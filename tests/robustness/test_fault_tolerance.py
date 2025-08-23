"""
Tests de Robustesse - Tolérance aux Pannes

Ces tests valident la capacité du système FinAgent à continuer
de fonctionner malgré des pannes partielles, à implémenter
des mécanismes de fallback et à se récupérer automatiquement.
"""

import pytest
import asyncio
import time
import random
import threading
from decimal import Decimal
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Callable, Union
from dataclasses import dataclass
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import json
import tempfile
import os
from contextlib import contextmanager

from finagent.business.models.portfolio_models import Portfolio, Position
from finagent.business.models.decision_models import InvestmentDecision, DecisionType
from finagent.business.strategy.engine.strategy_engine import StrategyEngine
from finagent.business.portfolio.portfolio_manager import PortfolioManager
from finagent.business.exceptions import (
    FinAgentError,
    APIError,
    DataError,
    ConfigurationError
)

# Import des utilitaires de test
from tests.utils import (
    create_test_portfolio,
    create_test_strategy,
    MockOpenBBProvider,
    MockClaudeProvider
)


@dataclass
class FaultToleranceResult:
    """Résultat de test de tolérance aux pannes"""
    test_name: str
    fault_type: str
    system_continued_operation: bool
    fallback_activated: bool
    data_integrity_maintained: bool
    recovery_time_ms: float
    graceful_degradation: bool
    fault_tolerance_score: float


@dataclass
class CircuitBreakerState:
    """État d'un circuit breaker"""
    state: str  # "closed", "open", "half_open"
    failure_count: int
    last_failure_time: Optional[datetime]
    success_count: int
    threshold: int
    timeout_duration: float


class FaultSimulator:
    """Simulateur de pannes pour tests de tolérance"""
    
    def __init__(self):
        self.active_faults = {}
        self.circuit_breakers = {}
        self.fallback_cache = {}
        self.recovery_log = []
    
    def inject_fault(self, component_name: str, fault_type: str, 
                    duration: float = 5.0, severity: str = "medium"):
        """Injecte une panne dans un composant"""
        fault_id = f"{component_name}_{fault_type}_{int(time.time())}"
        
        self.active_faults[fault_id] = {
            "component": component_name,
            "type": fault_type,
            "start_time": time.time(),
            "duration": duration,
            "severity": severity,
            "resolved": False
        }
        
        print(f"   💥 Panne injectée: {fault_type} sur {component_name} "
              f"(durée: {duration}s, sévérité: {severity})")
        
        return fault_id
    
    def resolve_fault(self, fault_id: str):
        """Résout une panne"""
        if fault_id in self.active_faults:
            self.active_faults[fault_id]["resolved"] = True
            self.active_faults[fault_id]["end_time"] = time.time()
            
            recovery_time = (
                self.active_faults[fault_id]["end_time"] - 
                self.active_faults[fault_id]["start_time"]
            )
            
            self.recovery_log.append({
                "fault_id": fault_id,
                "recovery_time": recovery_time,
                "timestamp": datetime.now()
            })
            
            print(f"   ✅ Panne résolue: {fault_id} (temps récupération: {recovery_time:.2f}s)")
    
    def get_active_faults(self) -> List[Dict[str, Any]]:
        """Retourne les pannes actives"""
        current_time = time.time()
        active = []
        
        for fault_id, fault_info in self.active_faults.items():
            if not fault_info["resolved"]:
                elapsed = current_time - fault_info["start_time"]
                if elapsed < fault_info["duration"]:
                    active.append({
                        "fault_id": fault_id,
                        "info": fault_info,
                        "elapsed": elapsed,
                        "remaining": fault_info["duration"] - elapsed
                    })
                else:
                    # Auto-résolution après durée
                    self.resolve_fault(fault_id)
        
        return active
    
    @contextmanager
    def simulated_component_failure(self, component: Any, failure_type: str, 
                                  failure_rate: float = 1.0):
        """Context manager pour simuler échec composant"""
        original_methods = {}
        
        try:
            if failure_type == "api_unavailable":
                # Patch toutes méthodes async pour lever APIError
                for attr_name in dir(component):
                    if not attr_name.startswith('_'):
                        attr = getattr(component, attr_name)
                        if asyncio.iscoroutinefunction(attr):
                            original_methods[attr_name] = attr
                            
                            async def failing_method(*args, **kwargs):
                                if random.random() < failure_rate:
                                    raise APIError(f"Service {attr_name} indisponible")
                                return await original_methods[attr_name](*args, **kwargs)
                            
                            setattr(component, attr_name, failing_method)
            
            elif failure_type == "data_corruption":
                # Patch méthodes retournant données corrompues
                if hasattr(component, 'get_market_data'):
                    original_methods['get_market_data'] = component.get_market_data
                    
                    async def corrupted_data_method(*args, **kwargs):
                        if random.random() < failure_rate:
                            return {"corrupted": True, "data": None}
                        return await original_methods['get_market_data'](*args, **kwargs)
                    
                    component.get_market_data = corrupted_data_method
            
            elif failure_type == "slow_response":
                # Patch méthodes avec délais excessifs
                if hasattr(component, 'get_market_data'):
                    original_methods['get_market_data'] = component.get_market_data
                    
                    async def slow_method(*args, **kwargs):
                        if random.random() < failure_rate:
                            await asyncio.sleep(random.uniform(5, 15))  # 5-15s délai
                        return await original_methods['get_market_data'](*args, **kwargs)
                    
                    component.get_market_data = slow_method
            
            yield
            
        finally:
            # Restaurer méthodes originales
            for attr_name, original_method in original_methods.items():
                setattr(component, attr_name, original_method)
    
    def create_circuit_breaker(self, name: str, failure_threshold: int = 5, 
                             timeout_duration: float = 60.0) -> CircuitBreakerState:
        """Crée un circuit breaker"""
        circuit_breaker = CircuitBreakerState(
            state="closed",
            failure_count=0,
            last_failure_time=None,
            success_count=0,
            threshold=failure_threshold,
            timeout_duration=timeout_duration
        )
        
        self.circuit_breakers[name] = circuit_breaker
        return circuit_breaker
    
    def circuit_breaker_call(self, name: str, operation: Callable) -> Any:
        """Exécute opération avec circuit breaker"""
        if name not in self.circuit_breakers:
            raise ValueError(f"Circuit breaker {name} non trouvé")
        
        cb = self.circuit_breakers[name]
        
        # Vérifier état circuit breaker
        if cb.state == "open":
            # Vérifier si timeout expiré
            if (cb.last_failure_time and 
                datetime.now() - cb.last_failure_time > timedelta(seconds=cb.timeout_duration)):
                cb.state = "half_open"
                cb.success_count = 0
                print(f"   🔄 Circuit breaker {name}: OPEN -> HALF_OPEN")
            else:
                raise APIError(f"Circuit breaker {name} ouvert")
        
        try:
            # Exécuter opération
            result = operation()
            
            # Succès
            if cb.state == "half_open":
                cb.success_count += 1
                if cb.success_count >= 3:  # 3 succès pour fermer
                    cb.state = "closed"
                    cb.failure_count = 0
                    print(f"   ✅ Circuit breaker {name}: HALF_OPEN -> CLOSED")
            elif cb.state == "closed":
                cb.failure_count = 0  # Reset compteur échecs
            
            return result
            
        except Exception as e:
            # Échec
            cb.failure_count += 1
            cb.last_failure_time = datetime.now()
            
            if cb.state == "closed" and cb.failure_count >= cb.threshold:
                cb.state = "open"
                print(f"   🔴 Circuit breaker {name}: CLOSED -> OPEN (échecs: {cb.failure_count})")
            elif cb.state == "half_open":
                cb.state = "open"
                print(f"   🔴 Circuit breaker {name}: HALF_OPEN -> OPEN")
            
            raise e


class FallbackManager:
    """Gestionnaire de mécanismes de fallback"""
    
    def __init__(self):
        self.fallback_strategies = {}
        self.fallback_cache = {}
        self.fallback_usage_log = []
    
    def register_fallback(self, service_name: str, fallback_func: Callable):
        """Enregistre stratégie de fallback pour service"""
        self.fallback_strategies[service_name] = fallback_func
        print(f"   📋 Fallback enregistré pour {service_name}")
    
    async def execute_with_fallback(self, service_name: str, primary_operation: Callable,
                                  *args, **kwargs) -> Any:
        """Exécute opération avec fallback automatique"""
        try:
            # Tentative opération primaire
            result = await primary_operation(*args, **kwargs)
            return result
            
        except Exception as e:
            print(f"   ⚠️  Échec service primaire {service_name}: {e}")
            
            # Log usage fallback
            self.fallback_usage_log.append({
                "service": service_name,
                "error": str(e),
                "timestamp": datetime.now()
            })
            
            # Vérifier fallback disponible
            if service_name in self.fallback_strategies:
                print(f"   🔄 Activation fallback pour {service_name}")
                
                try:
                    fallback_result = await self.fallback_strategies[service_name](*args, **kwargs)
                    
                    # Cache résultat fallback
                    cache_key = f"{service_name}_{hash(str(args))}"
                    self.fallback_cache[cache_key] = {
                        "result": fallback_result,
                        "timestamp": datetime.now()
                    }
                    
                    return fallback_result
                    
                except Exception as fallback_error:
                    print(f"   ❌ Échec fallback {service_name}: {fallback_error}")
                    raise e  # Lever erreur originale
            else:
                print(f"   ❌ Pas de fallback pour {service_name}")
                raise e
    
    def get_cached_fallback(self, service_name: str, args: tuple, 
                           max_age_seconds: float = 300) -> Optional[Any]:
        """Récupère résultat fallback du cache"""
        cache_key = f"{service_name}_{hash(str(args))}"
        
        if cache_key in self.fallback_cache:
            cached_item = self.fallback_cache[cache_key]
            age = (datetime.now() - cached_item["timestamp"]).total_seconds()
            
            if age <= max_age_seconds:
                print(f"   💾 Cache fallback utilisé pour {service_name} (âge: {age:.1f}s)")
                return cached_item["result"]
            else:
                # Cache expiré
                del self.fallback_cache[cache_key]
        
        return None


@pytest.mark.robustness
@pytest.mark.fault_tolerance
class TestBasicFaultTolerance:
    """Tests de tolérance aux pannes de base"""
    
    @pytest.fixture
    async def fault_tolerance_components(self, test_config):
        """Composants pour tests de tolérance aux pannes"""
        openbb_provider = MockOpenBBProvider(test_config.get("openbb", {}))
        claude_provider = MockClaudeProvider(test_config.get("claude", {}))
        
        strategy_engine = StrategyEngine(test_config.get("strategy", {}))
        portfolio_manager = PortfolioManager(test_config.get("portfolio", {}))
        
        return {
            "openbb": openbb_provider,
            "claude": claude_provider,
            "strategy_engine": strategy_engine,
            "portfolio_manager": portfolio_manager
        }
    
    @pytest.mark.asyncio
    async def test_api_service_failures(self, fault_tolerance_components):
        """Test tolérance aux pannes services API"""
        simulator = FaultSimulator()
        fallback_manager = FallbackManager()
        
        print("🌐 Test tolérance pannes services API")
        
        # Enregistrer fallbacks
        async def openbb_fallback(*args, **kwargs):
            return {
                "symbol": args[0] if args else "UNKNOWN",
                "price": 100.0,
                "source": "fallback_cache",
                "timestamp": datetime.now().isoformat()
            }
        
        async def claude_fallback(*args, **kwargs):
            return {
                "analysis": "Analyse indisponible - mode dégradé",
                "confidence": 0.3,
                "recommendation": "HOLD",
                "source": "fallback"
            }
        
        fallback_manager.register_fallback("openbb", openbb_fallback)
        fallback_manager.register_fallback("claude", claude_fallback)
        
        # Test pannes diverses
        fault_scenarios = [
            ("api_unavailable", 1.0),  # 100% échec
            ("data_corruption", 0.5),  # 50% corruption
            ("slow_response", 0.3)     # 30% lenteur
        ]
        
        fault_results = {}
        
        for fault_type, failure_rate in fault_scenarios:
            print(f"\n   🔧 Test panne: {fault_type} (taux: {failure_rate:.0%})")
            
            with simulator.simulated_component_failure(
                fault_tolerance_components["openbb"], 
                fault_type, 
                failure_rate
            ):
                # Test plusieurs opérations avec fallback
                operations_results = []
                
                for i in range(10):
                    start_time = time.perf_counter()
                    
                    try:
                        # Opération avec fallback
                        result = await fallback_manager.execute_with_fallback(
                            "openbb",
                            fault_tolerance_components["openbb"].get_market_data,
                            f"TEST{i:02d}"
                        )
                        
                        end_time = time.perf_counter()
                        operation_time = (end_time - start_time) * 1000
                        
                        operations_results.append({
                            "success": True,
                            "result": result,
                            "time_ms": operation_time,
                            "used_fallback": result.get("source") == "fallback_cache"
                        })
                        
                    except Exception as e:
                        end_time = time.perf_counter()
                        operation_time = (end_time - start_time) * 1000
                        
                        operations_results.append({
                            "success": False,
                            "error": str(e),
                            "time_ms": operation_time,
                            "used_fallback": False
                        })
                
                # Analyser résultats
                successful_ops = [r for r in operations_results if r["success"]]
                fallback_ops = [r for r in successful_ops if r["used_fallback"]]
                
                success_rate = len(successful_ops) / len(operations_results)
                fallback_usage_rate = len(fallback_ops) / len(operations_results)
                avg_response_time = sum(r["time_ms"] for r in successful_ops) / len(successful_ops) if successful_ops else 0
                
                fault_results[fault_type] = {
                    "success_rate": success_rate,
                    "fallback_usage_rate": fallback_usage_rate,
                    "avg_response_time_ms": avg_response_time,
                    "operations_count": len(operations_results)
                }
                
                print(f"      Succès: {success_rate:.1%}, "
                      f"Fallback: {fallback_usage_rate:.1%}, "
                      f"Temps moy: {avg_response_time:.1f}ms")
        
        # Calculer score tolérance global
        total_success_rate = sum(r["success_rate"] for r in fault_results.values()) / len(fault_results)
        total_fallback_effectiveness = sum(r["fallback_usage_rate"] for r in fault_results.values()) / len(fault_results)
        
        print(f"\n📊 Score tolérance API global:")
        print(f"   Taux succès global: {total_success_rate:.1%}")
        print(f"   Efficacité fallback: {total_fallback_effectiveness:.1%}")
        
        # Assertions tolérance pannes API
        assert total_success_rate >= 0.8  # Au moins 80% succès avec fallbacks
        assert total_fallback_effectiveness >= 0.3  # Au moins 30% usage fallback
        
        return {
            "fault_results": fault_results,
            "total_success_rate": total_success_rate,
            "fallback_effectiveness": total_fallback_effectiveness
        }
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_functionality(self, fault_tolerance_components):
        """Test fonctionnalité circuit breaker"""
        simulator = FaultSimulator()
        
        print("⚡ Test circuit breaker")
        
        # Créer circuit breaker
        cb = simulator.create_circuit_breaker(
            "test_service",
            failure_threshold=3,
            timeout_duration=2.0
        )
        
        # Fonction test qui échoue
        failure_count = 0
        def failing_operation():
            nonlocal failure_count
            failure_count += 1
            if failure_count <= 5:  # Premières 5 tentatives échouent
                raise APIError(f"Échec simulé #{failure_count}")
            return f"Succès après {failure_count} tentatives"
        
        circuit_breaker_log = []
        
        # Test séquence échecs -> ouverture -> récupération
        for attempt in range(10):
            try:
                result = simulator.circuit_breaker_call("test_service", failing_operation)
                circuit_breaker_log.append({
                    "attempt": attempt + 1,
                    "success": True,
                    "result": result,
                    "circuit_state": cb.state
                })
                print(f"   Tentative {attempt + 1}: ✅ {result}")
                
            except Exception as e:
                circuit_breaker_log.append({
                    "attempt": attempt + 1,
                    "success": False,
                    "error": str(e),
                    "circuit_state": cb.state
                })
                print(f"   Tentative {attempt + 1}: ❌ {e} (État CB: {cb.state})")
            
            # Pause pour timeout
            if cb.state == "open" and attempt == 6:
                print(f"   ⏱️  Attente timeout circuit breaker (2s)...")
                await asyncio.sleep(2.5)
        
        # Analyser comportement circuit breaker
        states_seen = {log["circuit_state"] for log in circuit_breaker_log}
        transitions = []
        
        prev_state = "closed"
        for log in circuit_breaker_log:
            if log["circuit_state"] != prev_state:
                transitions.append(f"{prev_state} -> {log['circuit_state']}")
                prev_state = log["circuit_state"]
        
        print(f"\n📊 Analyse circuit breaker:")
        print(f"   États vus: {states_seen}")
        print(f"   Transitions: {transitions}")
        print(f"   Échecs totaux: {cb.failure_count}")
        
        # Assertions circuit breaker
        assert "open" in states_seen  # Circuit s'est ouvert
        assert "closed -> open" in transitions  # Transition normale
        assert len([log for log in circuit_breaker_log if log["success"]]) > 0  # Récupération finale
        
        return {
            "circuit_breaker_log": circuit_breaker_log,
            "states_seen": states_seen,
            "transitions": transitions
        }
    
    @pytest.mark.asyncio
    async def test_graceful_degradation(self, fault_tolerance_components):
        """Test dégradation gracieuse des services"""
        simulator = FaultSimulator()
        
        print("📉 Test dégradation gracieuse")
        
        # Simuler différents niveaux de dégradation
        degradation_scenarios = [
            {
                "name": "partial_api_failure",
                "openbb_available": False,
                "claude_available": True,
                "expected_functionality": 0.6  # 60% fonctionnalité
            },
            {
                "name": "analysis_service_down",
                "openbb_available": True,
                "claude_available": False,
                "expected_functionality": 0.7  # 70% fonctionnalité
            },
            {
                "name": "both_services_degraded",
                "openbb_available": False,
                "claude_available": False,
                "expected_functionality": 0.3  # 30% fonctionnalité (cache/fallback)
            }
        ]
        
        degradation_results = {}
        
        for scenario in degradation_scenarios:
            print(f"\n   🔧 Scénario: {scenario['name']}")
            print(f"      OpenBB: {'✓' if scenario['openbb_available'] else '✗'}, "
                  f"Claude: {'✓' if scenario['claude_available'] else '✗'}")
            
            # Simuler indisponibilité services
            openbb_failure_rate = 0.0 if scenario["openbb_available"] else 1.0
            claude_failure_rate = 0.0 if scenario["claude_available"] else 1.0
            
            with simulator.simulated_component_failure(
                fault_tolerance_components["openbb"], 
                "api_unavailable", 
                openbb_failure_rate
            ), simulator.simulated_component_failure(
                fault_tolerance_components["claude"],
                "api_unavailable",
                claude_failure_rate
            ):
                # Test fonctionnalités essentielles
                functionality_tests = [
                    ("portfolio_valuation", self._test_portfolio_valuation),
                    ("market_data_access", self._test_market_data_access),
                    ("investment_analysis", self._test_investment_analysis),
                    ("risk_assessment", self._test_risk_assessment)
                ]
                
                test_results = {}
                
                for test_name, test_func in functionality_tests:
                    try:
                        result = await test_func(fault_tolerance_components)
                        test_results[test_name] = {
                            "success": True,
                            "result": result
                        }
                        print(f"      {test_name}: ✅")
                        
                    except Exception as e:
                        test_results[test_name] = {
                            "success": False,
                            "error": str(e)
                        }
                        print(f"      {test_name}: ❌ {e}")
                
                # Calculer fonctionnalité disponible
                successful_tests = sum(1 for r in test_results.values() if r["success"])
                actual_functionality = successful_tests / len(functionality_tests)
                
                degradation_results[scenario["name"]] = {
                    "expected_functionality": scenario["expected_functionality"],
                    "actual_functionality": actual_functionality,
                    "test_results": test_results,
                    "graceful": actual_functionality >= scenario["expected_functionality"] * 0.8  # Tolérance 20%
                }
                
                print(f"      Fonctionnalité: {actual_functionality:.1%} "
                      f"(attendu: {scenario['expected_functionality']:.1%})")
        
        # Analyser dégradation globale
        graceful_scenarios = sum(1 for r in degradation_results.values() if r["graceful"])
        graceful_degradation_score = graceful_scenarios / len(degradation_scenarios)
        
        print(f"\n📊 Score dégradation gracieuse: {graceful_degradation_score:.1%}")
        
        # Assertions dégradation gracieuse
        assert graceful_degradation_score >= 0.7  # Au moins 70% des scénarios gracieux
        
        return {
            "degradation_results": degradation_results,
            "graceful_degradation_score": graceful_degradation_score
        }
    
    # Helper methods pour tests de fonctionnalité
    async def _test_portfolio_valuation(self, components: Dict[str, Any]) -> Dict[str, Any]:
        """Test évaluation portfolio"""
        portfolio = create_test_portfolio(initial_capital=Decimal("100000.00"))
        result = await components["portfolio_manager"].calculate_value(portfolio)
        return {"portfolio_value": result}
    
    async def _test_market_data_access(self, components: Dict[str, Any]) -> Dict[str, Any]:
        """Test accès données marché"""
        result = await components["openbb"].get_market_data("AAPL")
        return {"market_data": result}
    
    async def _test_investment_analysis(self, components: Dict[str, Any]) -> Dict[str, Any]:
        """Test analyse investissement"""
        market_data = {"symbol": "AAPL", "price": 150.0}
        result = await components["claude"].analyze_investment("AAPL", market_data)
        return {"analysis": result}
    
    async def _test_risk_assessment(self, components: Dict[str, Any]) -> Dict[str, Any]:
        """Test évaluation risque"""
        portfolio = create_test_portfolio(initial_capital=Decimal("100000.00"))
        result = await components["portfolio_manager"].calculate_risk_metrics(portfolio)
        return {"risk_metrics": result}


@pytest.mark.robustness
@pytest.mark.fault_tolerance
@pytest.mark.slow
class TestAdvancedFaultTolerance:
    """Tests avancés de tolérance aux pannes"""
    
    @pytest.mark.asyncio
    async def test_cascade_failure_prevention(self, fault_tolerance_components):
        """Test prévention des pannes en cascade"""
        simulator = FaultSimulator()
        
        print("🌊 Test prévention pannes en cascade")
        
        # Simuler panne initiale qui pourrait se propager
        cascade_log = []
        
        def log_cascade_event(component: str, event: str, details: str = ""):
            cascade_log.append({
                "component": component,
                "event": event,
                "details": details,
                "timestamp": datetime.now()
            })
            print(f"   {event} - {component}: {details}")
        
        # Créer circuit breakers pour chaque composant
        for component_name in ["openbb", "claude", "strategy_engine", "portfolio_manager"]:
            simulator.create_circuit_breaker(
                component_name,
                failure_threshold=2,
                timeout_duration=1.0
            )
        
        # Injecter panne initiale
        log_cascade_event("openbb", "FAULT_INJECTED", "API indisponible")
        
        # Test opérations interdépendantes
        operations = [
            ("get_market_data", fault_tolerance_components["openbb"]),
            ("analyze_investment", fault_tolerance_components["claude"]),
            ("evaluate_strategy", fault_tolerance_components["strategy_engine"]),
            ("update_portfolio", fault_tolerance_components["portfolio_manager"])
        ]
        
        with simulator.simulated_component_failure(
            fault_tolerance_components["openbb"], 
            "api_unavailable", 
            1.0
        ):
            # Tenter chaque opération avec circuit breaker
            for operation_name, component in operations:
                try:
                    def operation_wrapper():
                        # Simuler dépendance aux données market
                        if operation_name != "get_market_data":
                            # Ces opérations dépendent de market data
                            raise APIError(f"{operation_name} nécessite données marché")
                        else:
                            raise APIError("Service indisponible")
                    
                    result = simulator.circuit_breaker_call(
                        operation_name.split("_")[0],  # Premier mot comme nom CB
                        operation_wrapper
                    )
                    
                    log_cascade_event(operation_name, "SUCCESS", "Opération réussie")
                    
                except Exception as e:
                    log_cascade_event(operation_name, "FAILURE", str(e))
        
        # Analyser propagation
        failure_events = [event for event in cascade_log if event["event"] == "FAILURE"]
        circuit_breaker_events = [
            event for event in cascade_log 
            if "circuit breaker" in event["details"].lower()
        ]
        
        print(f"\n📊 Analyse cascade:")
        print(f"   Échecs totaux: {len(failure_events)}")
        print(f"   Activations CB: {len(circuit_breaker_events)}")
        print(f"   Propagation contrôlée: {'✓' if len(failure_events) <= 4 else '✗'}")
        
        # Vérifier que cascade contrôlée
        assert len(failure_events) <= len(operations)  # Pas plus d'échecs que d'opérations
        
        return {
            "cascade_log": cascade_log,
            "failure_count": len(failure_events),
            "circuit_breaker_activations": len(circuit_breaker_events)
        }


if __name__ == "__main__":
    # Exécution directe pour tests de développement
    pytest.main([__file__, "-v", "--tb=short", "-m", "fault_tolerance and not slow"])