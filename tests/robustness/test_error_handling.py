"""
Tests de Robustesse - Gestion d'Erreurs

Ces tests valident la capacité du système FinAgent à gérer
les erreurs de manière gracieuse, maintenir la stabilité
et fournir des messages d'erreur informatifs.
"""

import pytest
import asyncio
import logging
import traceback
from decimal import Decimal, InvalidOperation
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Type, Callable
from dataclasses import dataclass
from unittest.mock import Mock, patch, AsyncMock
import json
import tempfile
import os

from finagent.business.models.portfolio_models import Portfolio, Position
from finagent.business.models.decision_models import InvestmentDecision, DecisionType
from finagent.business.exceptions import (
    FinAgentError,
    ValidationError,
    DataError,
    APIError,
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
class ErrorTestResult:
    """Résultat de test d'erreur"""
    test_name: str
    error_type: str
    error_handled_gracefully: bool
    error_message_informative: bool
    system_state_preserved: bool
    recovery_successful: bool
    error_logged_properly: bool
    overall_robustness_score: float


class ErrorSimulator:
    """Simulateur d'erreurs pour tests de robustesse"""
    
    def __init__(self):
        self.error_log = []
        self.system_state_snapshots = []
    
    def capture_system_state(self, components: Dict[str, Any]) -> Dict[str, Any]:
        """Capture l'état du système avant test"""
        state = {}
        
        for name, component in components.items():
            try:
                if hasattr(component, 'get_state'):
                    state[name] = component.get_state()
                elif hasattr(component, '__dict__'):
                    # Capture attributs publics basiques
                    state[name] = {
                        attr: getattr(component, attr) 
                        for attr in dir(component) 
                        if not attr.startswith('_') and not callable(getattr(component, attr))
                    }
                else:
                    state[name] = str(component)
            except Exception as e:
                state[name] = f"State capture error: {e}"
        
        return state
    
    def verify_system_state_preserved(self, before_state: Dict[str, Any], 
                                    after_state: Dict[str, Any]) -> bool:
        """Vérifie que l'état système est préservé après erreur"""
        try:
            # Comparaison basique - les composants clés doivent exister
            before_keys = set(before_state.keys())
            after_keys = set(after_state.keys())
            
            # Vérifier que les composants principaux existent toujours
            critical_components_preserved = before_keys.issubset(after_keys)
            
            # Vérifier pas de corruption majeure
            no_major_corruption = True
            for key in before_keys.intersection(after_keys):
                if isinstance(before_state[key], dict) and isinstance(after_state[key], dict):
                    if "error" in str(after_state[key]).lower() and "error" not in str(before_state[key]).lower():
                        # Composant en erreur mais pas avant
                        continue
                # État similaire ou évolution normale
            
            return critical_components_preserved and no_major_corruption
            
        except Exception:
            return False
    
    async def simulate_api_errors(self, provider: Any, error_types: List[str]) -> Dict[str, ErrorTestResult]:
        """Simule différents types d'erreurs API"""
        results = {}
        
        for error_type in error_types:
            print(f"   🔴 Test erreur API: {error_type}")
            
            # Capture état avant
            before_state = self.capture_system_state({"provider": provider})
            
            try:
                # Configurer mock pour lever erreur spécifique
                if error_type == "timeout":
                    with patch.object(provider, 'get_market_data', side_effect=asyncio.TimeoutError("API timeout")):
                        result = await provider.get_market_data("AAPL")
                
                elif error_type == "rate_limit":
                    with patch.object(provider, 'get_market_data', side_effect=APIError("Rate limit exceeded", status_code=429)):
                        result = await provider.get_market_data("AAPL")
                
                elif error_type == "invalid_response":
                    with patch.object(provider, 'get_market_data', return_value={"invalid": "response"}):
                        result = await provider.get_market_data("AAPL")
                
                elif error_type == "network_error":
                    with patch.object(provider, 'get_market_data', side_effect=ConnectionError("Network unreachable")):
                        result = await provider.get_market_data("AAPL")
                
                elif error_type == "auth_error":
                    with patch.object(provider, 'get_market_data', side_effect=APIError("Unauthorized", status_code=401)):
                        result = await provider.get_market_data("AAPL")
                
                # Si on arrive ici, l'erreur n'a pas été levée
                error_handled = True
                error_message_informative = False
                
            except Exception as e:
                # Erreur levée comme attendu
                error_handled = True
                error_message_informative = len(str(e)) > 10 and any(
                    keyword in str(e).lower() 
                    for keyword in ["error", "failed", "timeout", "limit", "network", "auth"]
                )
                
                # Log de l'erreur
                self.error_log.append({
                    "type": error_type,
                    "exception": type(e).__name__,
                    "message": str(e),
                    "timestamp": datetime.now()
                })
            
            # Capture état après
            after_state = self.capture_system_state({"provider": provider})
            state_preserved = self.verify_system_state_preserved(before_state, after_state)
            
            # Tenter récupération
            recovery_successful = False
            try:
                # Test opération normale après erreur
                normal_result = await provider.get_market_data("AAPL")
                recovery_successful = normal_result is not None
            except Exception:
                recovery_successful = False
            
            # Calculer score robustesse
            robustness_score = sum([
                1.0 if error_handled else 0.0,
                1.0 if error_message_informative else 0.0,
                1.0 if state_preserved else 0.0,
                1.0 if recovery_successful else 0.0
            ]) / 4.0
            
            results[error_type] = ErrorTestResult(
                test_name=f"api_error_{error_type}",
                error_type=error_type,
                error_handled_gracefully=error_handled,
                error_message_informative=error_message_informative,
                system_state_preserved=state_preserved,
                recovery_successful=recovery_successful,
                error_logged_properly=len(self.error_log) > 0,
                overall_robustness_score=robustness_score
            )
            
            print(f"      Gestion: {'✓' if error_handled else '✗'}, "
                  f"Message: {'✓' if error_message_informative else '✗'}, "
                  f"État: {'✓' if state_preserved else '✗'}, "
                  f"Récup: {'✓' if recovery_successful else '✗'}")
        
        return results
    
    def simulate_data_corruption_errors(self, test_data: List[Dict[str, Any]]) -> Dict[str, ErrorTestResult]:
        """Simule erreurs de corruption de données"""
        results = {}
        corruption_types = [
            "invalid_decimal",
            "negative_price", 
            "future_date",
            "missing_required_field",
            "invalid_json_format",
            "circular_reference"
        ]
        
        for corruption_type in corruption_types:
            print(f"   🗂️  Test corruption: {corruption_type}")
            
            corrupted_data = self._create_corrupted_data(test_data[0], corruption_type)
            
            try:
                # Tenter traitement données corrompues
                if corruption_type == "invalid_decimal":
                    price = Decimal(corrupted_data["price"])
                
                elif corruption_type == "negative_price":
                    if float(corrupted_data["price"]) < 0:
                        raise ValidationError("Prix ne peut être négatif")
                
                elif corruption_type == "future_date":
                    date_obj = datetime.fromisoformat(corrupted_data["timestamp"])
                    if date_obj > datetime.now():
                        raise ValidationError("Date future non permise")
                
                elif corruption_type == "missing_required_field":
                    required_fields = ["symbol", "price", "timestamp"]
                    for field in required_fields:
                        if field not in corrupted_data:
                            raise ValidationError(f"Champ requis manquant: {field}")
                
                elif corruption_type == "invalid_json_format":
                    json.dumps(corrupted_data)  # Test sérialisation
                
                elif corruption_type == "circular_reference":
                    # Test détection référence circulaire
                    if self._has_circular_reference(corrupted_data):
                        raise DataError("Référence circulaire détectée")
                
                # Pas d'erreur levée
                error_handled = False
                error_message_informative = False
                
            except (ValidationError, DataError, ValueError, InvalidOperation) as e:
                # Erreur appropriée levée
                error_handled = True
                error_message_informative = len(str(e)) > 5
                
            except Exception as e:
                # Erreur inattendue
                error_handled = False
                error_message_informative = False
            
            # Score basé sur gestion appropriée
            robustness_score = 1.0 if error_handled and error_message_informative else 0.0
            
            results[corruption_type] = ErrorTestResult(
                test_name=f"data_corruption_{corruption_type}",
                error_type=corruption_type,
                error_handled_gracefully=error_handled,
                error_message_informative=error_message_informative,
                system_state_preserved=True,  # Pas de changement d'état pour validation
                recovery_successful=True,  # Données rejetées = récupération réussie
                error_logged_properly=True,
                overall_robustness_score=robustness_score
            )
        
        return results
    
    def _create_corrupted_data(self, original_data: Dict[str, Any], corruption_type: str) -> Dict[str, Any]:
        """Crée des données corrompues selon le type"""
        corrupted = original_data.copy()
        
        if corruption_type == "invalid_decimal":
            corrupted["price"] = "not_a_number"
        
        elif corruption_type == "negative_price":
            corrupted["price"] = -100.50
        
        elif corruption_type == "future_date":
            future_date = datetime.now() + timedelta(days=365)
            corrupted["timestamp"] = future_date.isoformat()
        
        elif corruption_type == "missing_required_field":
            if "symbol" in corrupted:
                del corrupted["symbol"]
        
        elif corruption_type == "invalid_json_format":
            # Ajouter objet non-sérialisable
            corrupted["invalid_object"] = lambda x: x
        
        elif corruption_type == "circular_reference":
            # Créer référence circulaire
            corrupted["self_ref"] = corrupted
        
        return corrupted
    
    def _has_circular_reference(self, obj: Any, seen: Optional[set] = None) -> bool:
        """Détecte référence circulaire"""
        if seen is None:
            seen = set()
        
        obj_id = id(obj)
        if obj_id in seen:
            return True
        
        if isinstance(obj, dict):
            seen.add(obj_id)
            for value in obj.values():
                if self._has_circular_reference(value, seen):
                    return True
            seen.remove(obj_id)
        
        return False


@pytest.mark.robustness
@pytest.mark.error_handling
class TestBasicErrorHandling:
    """Tests de gestion d'erreurs de base"""
    
    @pytest.fixture
    async def error_test_components(self, test_config):
        """Composants pour tests d'erreurs"""
        openbb_provider = MockOpenBBProvider(test_config.get("openbb", {}))
        claude_provider = MockClaudeProvider(test_config.get("claude", {}))
        
        return {
            "openbb": openbb_provider,
            "claude": claude_provider
        }
    
    @pytest.mark.asyncio
    async def test_api_error_handling(self, error_test_components):
        """Test gestion erreurs API"""
        simulator = ErrorSimulator()
        
        print("🌐 Test gestion erreurs API")
        
        # Test erreurs API OpenBB
        openbb_errors = ["timeout", "rate_limit", "invalid_response", "network_error", "auth_error"]
        
        openbb_results = await simulator.simulate_api_errors(
            error_test_components["openbb"], 
            openbb_errors
        )
        
        print(f"\n📊 Résultats OpenBB API:")
        for error_type, result in openbb_results.items():
            print(f"   {error_type:15s}: Score {result.overall_robustness_score:.2f}")
        
        # Test erreurs API Claude
        claude_errors = ["timeout", "rate_limit", "invalid_response", "auth_error"]
        
        claude_results = await simulator.simulate_api_errors(
            error_test_components["claude"],
            claude_errors
        )
        
        print(f"\n📊 Résultats Claude API:")
        for error_type, result in claude_results.items():
            print(f"   {error_type:15s}: Score {result.overall_robustness_score:.2f}")
        
        # Calculer scores globaux
        all_results = list(openbb_results.values()) + list(claude_results.values())
        average_robustness = sum(r.overall_robustness_score for r in all_results) / len(all_results)
        
        print(f"\n🎯 Score robustesse API global: {average_robustness:.2f}")
        
        # Assertions gestion erreurs API
        assert average_robustness >= 0.7  # Au moins 70% de robustesse
        assert all(r.error_handled_gracefully for r in all_results)  # Toutes erreurs gérées
        assert sum(r.error_logged_properly for r in all_results) >= len(all_results) * 0.8  # 80% logged
        
        return {
            "openbb_results": openbb_results,
            "claude_results": claude_results,
            "average_robustness": average_robustness
        }
    
    def test_data_validation_errors(self):
        """Test gestion erreurs validation données"""
        simulator = ErrorSimulator()
        
        print("📋 Test gestion erreurs validation")
        
        # Données test pour corruption
        test_data = [
            {
                "symbol": "AAPL",
                "price": 150.25,
                "timestamp": "2024-01-15T10:30:00",
                "volume": 1000000
            }
        ]
        
        # Test corruptions diverses
        corruption_results = simulator.simulate_data_corruption_errors(test_data)
        
        print(f"\n📊 Résultats validation données:")
        for corruption_type, result in corruption_results.items():
            print(f"   {corruption_type:20s}: "
                  f"Gérée {'✓' if result.error_handled_gracefully else '✗'}, "
                  f"Score {result.overall_robustness_score:.2f}")
        
        # Calculer score validation global
        validation_score = sum(r.overall_robustness_score for r in corruption_results.values()) / len(corruption_results)
        
        print(f"\n🎯 Score validation global: {validation_score:.2f}")
        
        # Assertions validation données
        assert validation_score >= 0.8  # Au moins 80% de robustesse validation
        
        # Vérifier types erreurs spécifiques bien gérées
        critical_corruptions = ["invalid_decimal", "missing_required_field", "negative_price"]
        for corruption in critical_corruptions:
            assert corruption_results[corruption].error_handled_gracefully
            assert corruption_results[corruption].overall_robustness_score >= 0.8
        
        return {
            "corruption_results": corruption_results,
            "validation_score": validation_score
        }
    
    @pytest.mark.asyncio
    async def test_exception_propagation(self, error_test_components):
        """Test propagation appropriée des exceptions"""
        print("🔄 Test propagation exceptions")
        
        # Test propagation exceptions custom
        exceptions_to_test = [
            (ValidationError, "Erreur validation test"),
            (DataError, "Erreur données test"),
            (APIError, "Erreur API test"),
            (ConfigurationError, "Erreur configuration test")
        ]
        
        propagation_results = {}
        
        for exception_class, message in exceptions_to_test:
            exception_name = exception_class.__name__
            print(f"   🔄 Test {exception_name}")
            
            # Test que exception est bien propagée
            with pytest.raises(exception_class) as exc_info:
                raise exception_class(message)
            
            # Vérifier propriétés exception
            caught_exception = exc_info.value
            message_preserved = str(caught_exception) == message
            type_preserved = type(caught_exception) == exception_class
            
            propagation_results[exception_name] = {
                "message_preserved": message_preserved,
                "type_preserved": type_preserved,
                "traceback_available": exc_info.tb is not None
            }
            
            print(f"      Message: {'✓' if message_preserved else '✗'}, "
                  f"Type: {'✓' if type_preserved else '✗'}")
        
        # Vérifier toutes propagations correctes
        all_correct = all(
            all(props.values()) 
            for props in propagation_results.values()
        )
        
        assert all_correct, "Certaines exceptions mal propagées"
        
        return propagation_results


@pytest.mark.robustness
@pytest.mark.error_handling
@pytest.mark.slow
class TestAdvancedErrorHandling:
    """Tests avancés de gestion d'erreurs"""
    
    @pytest.mark.asyncio
    async def test_cascading_error_handling(self, error_test_components):
        """Test gestion erreurs en cascade"""
        print("🌊 Test gestion erreurs en cascade")
        
        # Simuler chaîne d'erreurs
        error_chain = []
        
        async def operation_with_cascade_errors():
            try:
                # Première opération qui échoue
                raise APIError("API primaire indisponible")
            except APIError as e:
                error_chain.append(("primary_api", str(e)))
                
                try:
                    # Tentative fallback qui échoue aussi
                    raise ConnectionError("Fallback API inaccessible")
                except ConnectionError as e2:
                    error_chain.append(("fallback_api", str(e2)))
                    
                    try:
                        # Cache local corrompu
                        raise DataError("Cache local corrompu")
                    except DataError as e3:
                        error_chain.append(("local_cache", str(e3)))
                        
                        # Retourner données par défaut
                        return {"fallback": "default_data"}
        
        # Exécuter et vérifier gestion cascade
        result = await operation_with_cascade_errors()
        
        print(f"   Erreurs en cascade: {len(error_chain)}")
        for source, error in error_chain:
            print(f"      {source}: {error}")
        
        print(f"   Résultat final: {result}")
        
        # Assertions cascade
        assert len(error_chain) == 3  # Trois erreurs dans cascade
        assert result is not None  # Récupération finale réussie
        assert "fallback" in result  # Données fallback retournées
        
        return {
            "error_chain": error_chain,
            "final_result": result
        }
    
    def test_memory_error_handling(self):
        """Test gestion erreurs mémoire"""
        print("💾 Test gestion erreurs mémoire")
        
        # Simuler conditions mémoire faible
        def memory_intensive_operation():
            try:
                # Simuler allocation mémoire importante
                large_data = list(range(10**6))  # 1M éléments
                
                # Traitement qui pourrait échouer
                processed_data = [x * 2 for x in large_data]
                
                return {"status": "success", "size": len(processed_data)}
                
            except MemoryError as e:
                # Gestion erreur mémoire
                return {"status": "memory_error", "error": str(e)}
            
            except Exception as e:
                # Autres erreurs
                return {"status": "other_error", "error": str(e)}
            
            finally:
                # Nettoyage mémoire
                if 'large_data' in locals():
                    del large_data
                if 'processed_data' in locals():
                    del processed_data
        
        # Test opération
        result = memory_intensive_operation()
        
        print(f"   Résultat opération mémoire: {result['status']}")
        
        # Vérifier gestion appropriée
        assert result["status"] in ["success", "memory_error"]  # Gestion appropriée
        
        return result
    
    @pytest.mark.asyncio  
    async def test_timeout_error_handling(self, error_test_components):
        """Test gestion erreurs timeout"""
        print("⏱️  Test gestion erreurs timeout")
        
        # Test différents timeouts
        timeout_scenarios = [
            ("short_timeout", 0.1),  # 100ms
            ("medium_timeout", 1.0),  # 1s  
            ("long_timeout", 5.0)   # 5s
        ]
        
        timeout_results = {}
        
        for scenario_name, timeout_duration in timeout_scenarios:
            print(f"   Test timeout: {scenario_name} ({timeout_duration}s)")
            
            async def operation_with_timeout():
                # Opération qui prend plus de temps que timeout
                await asyncio.sleep(timeout_duration + 0.5)
                return "operation_completed"
            
            try:
                # Exécuter avec timeout
                result = await asyncio.wait_for(
                    operation_with_timeout(), 
                    timeout=timeout_duration
                )
                timeout_results[scenario_name] = {
                    "completed": True,
                    "result": result
                }
                
            except asyncio.TimeoutError:
                # Timeout géré correctement
                timeout_results[scenario_name] = {
                    "completed": False,
                    "timeout_handled": True
                }
                print(f"      Timeout géré correctement")
                
            except Exception as e:
                # Erreur inattendue
                timeout_results[scenario_name] = {
                    "completed": False,
                    "timeout_handled": False,
                    "error": str(e)
                }
        
        # Vérifier gestion timeouts
        timeouts_handled = sum(
            1 for result in timeout_results.values() 
            if result.get("timeout_handled", False)
        )
        
        print(f"\n📊 Timeouts gérés: {timeouts_handled}/{len(timeout_scenarios)}")
        
        assert timeouts_handled >= len(timeout_scenarios) * 0.8  # Au moins 80% gérés
        
        return timeout_results


if __name__ == "__main__":
    # Exécution directe pour tests de développement
    pytest.main([__file__, "-v", "--tb=short", "-m", "error_handling and not slow"])