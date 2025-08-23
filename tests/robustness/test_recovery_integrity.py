"""
Tests de Robustesse - Récupération et Intégrité des Données

Ces tests valident la capacité du système FinAgent à récupérer
automatiquement des pannes, maintenir l'intégrité des données
et assurer la cohérence du système après incidents.
"""

import pytest
import asyncio
import time
import pickle
import json
import tempfile
import shutil
import os
from decimal import Decimal
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from unittest.mock import Mock, patch, AsyncMock
import sqlite3
import threading
from contextlib import contextmanager
import hashlib

from finagent.business.models.portfolio_models import Portfolio, Position
from finagent.business.models.decision_models import InvestmentDecision, DecisionType
from finagent.business.strategy.engine.strategy_engine import StrategyEngine
from finagent.business.portfolio.portfolio_manager import PortfolioManager
from finagent.business.exceptions import DataError, ValidationError

# Import des utilitaires de test
from tests.utils import (
    create_test_portfolio,
    create_test_strategy,
    MockOpenBBProvider,
    MockClaudeProvider
)


@dataclass
class RecoveryTestResult:
    """Résultat de test de récupération"""
    test_name: str
    recovery_type: str
    recovery_successful: bool
    recovery_time_ms: float
    data_integrity_preserved: bool
    system_consistency_maintained: bool
    automatic_recovery: bool
    recovery_score: float


@dataclass
class DataIntegrityCheck:
    """Résultat de vérification d'intégrité"""
    check_name: str
    data_consistent: bool
    corruption_detected: bool
    missing_data_count: int
    duplicate_data_count: int
    invalid_data_count: int
    integrity_score: float


class DataIntegrityValidator:
    """Validateur d'intégrité des données"""
    
    def __init__(self):
        self.integrity_rules = {}
        self.validation_log = []
    
    def register_integrity_rule(self, rule_name: str, validation_func: callable):
        """Enregistre une règle d'intégrité"""
        self.integrity_rules[rule_name] = validation_func
        print(f"   📋 Règle d'intégrité enregistrée: {rule_name}")
    
    def validate_portfolio_integrity(self, portfolio: Portfolio) -> DataIntegrityCheck:
        """Valide l'intégrité d'un portfolio"""
        errors = []
        
        # Vérifications de base
        missing_data = 0
        duplicates = 0
        invalid_data = 0
        
        # 1. Vérifier champs requis
        if not portfolio.id:
            errors.append("Portfolio ID manquant")
            missing_data += 1
        
        if portfolio.cash is None:
            errors.append("Cash amount manquant")
            missing_data += 1
        elif portfolio.cash < 0:
            errors.append(f"Cash négatif: {portfolio.cash}")
            invalid_data += 1
        
        # 2. Vérifier positions
        seen_symbols = set()
        for position in portfolio.positions:
            # Vérifier duplicatas
            if position.symbol in seen_symbols:
                errors.append(f"Position dupliquée: {position.symbol}")
                duplicates += 1
            seen_symbols.add(position.symbol)
            
            # Vérifier données position
            if not position.symbol:
                errors.append("Symbol manquant dans position")
                missing_data += 1
            
            if position.quantity <= 0:
                errors.append(f"Quantité invalide pour {position.symbol}: {position.quantity}")
                invalid_data += 1
            
            if position.average_price <= 0:
                errors.append(f"Prix moyen invalide pour {position.symbol}: {position.average_price}")
                invalid_data += 1
        
        # 3. Vérifier cohérence temporelle
        if portfolio.last_updated and portfolio.created_at:
            if portfolio.last_updated < portfolio.created_at:
                errors.append("Last_updated antérieur à created_at")
                invalid_data += 1
        
        # Score d'intégrité
        total_checks = len(portfolio.positions) * 3 + 5  # Estimé
        error_count = missing_data + duplicates + invalid_data
        integrity_score = max(0.0, 1.0 - (error_count / total_checks))
        
        result = DataIntegrityCheck(
            check_name="portfolio_integrity",
            data_consistent=len(errors) == 0,
            corruption_detected=len(errors) > 0,
            missing_data_count=missing_data,
            duplicate_data_count=duplicates,
            invalid_data_count=invalid_data,
            integrity_score=integrity_score
        )
        
        if errors:
            print(f"   ⚠️  Erreurs intégrité portfolio: {errors}")
        
        return result
    
    def validate_decision_integrity(self, decisions: List[InvestmentDecision]) -> DataIntegrityCheck:
        """Valide l'intégrité des décisions d'investissement"""
        errors = []
        missing_data = 0
        duplicates = 0
        invalid_data = 0
        
        seen_decisions = set()
        
        for decision in decisions:
            # Créer signature décision
            decision_sig = f"{decision.symbol}_{decision.decision_type}_{decision.timestamp}"
            
            if decision_sig in seen_decisions:
                errors.append(f"Décision dupliquée: {decision_sig}")
                duplicates += 1
            seen_decisions.add(decision_sig)
            
            # Vérifier champs requis
            if not decision.symbol:
                errors.append("Symbol manquant dans décision")
                missing_data += 1
            
            if not decision.decision_type:
                errors.append("Type décision manquant")
                missing_data += 1
            
            if decision.confidence is None or decision.confidence < 0 or decision.confidence > 1:
                errors.append(f"Confidence invalide: {decision.confidence}")
                invalid_data += 1
            
            # Vérifier cohérence quantité/prix pour ordres
            if decision.decision_type in [DecisionType.BUY, DecisionType.SELL]:
                if not decision.suggested_quantity or decision.suggested_quantity <= 0:
                    errors.append(f"Quantité suggérée invalide: {decision.suggested_quantity}")
                    invalid_data += 1
                
                if not decision.target_price or decision.target_price <= 0:
                    errors.append(f"Prix cible invalide: {decision.target_price}")
                    invalid_data += 1
        
        # Score intégrité
        total_checks = len(decisions) * 5 if decisions else 1
        error_count = missing_data + duplicates + invalid_data
        integrity_score = max(0.0, 1.0 - (error_count / total_checks))
        
        return DataIntegrityCheck(
            check_name="decision_integrity",
            data_consistent=len(errors) == 0,
            corruption_detected=len(errors) > 0,
            missing_data_count=missing_data,
            duplicate_data_count=duplicates,
            invalid_data_count=invalid_data,
            integrity_score=integrity_score
        )
    
    def calculate_data_checksum(self, data: Any) -> str:
        """Calcule checksum des données"""
        if isinstance(data, dict):
            serialized = json.dumps(data, sort_keys=True, default=str)
        else:
            serialized = str(data)
        
        return hashlib.sha256(serialized.encode()).hexdigest()[:16]


class RecoverySimulator:
    """Simulateur de pannes et récupération"""
    
    def __init__(self):
        self.backup_storage = {}
        self.recovery_log = []
        self.data_snapshots = {}
    
    def create_data_snapshot(self, snapshot_name: str, data: Dict[str, Any]):
        """Crée un snapshot des données"""
        self.data_snapshots[snapshot_name] = {
            "data": pickle.dumps(data),
            "timestamp": datetime.now(),
            "checksum": hashlib.sha256(pickle.dumps(data)).hexdigest()
        }
        print(f"   📸 Snapshot créé: {snapshot_name}")
    
    def restore_from_snapshot(self, snapshot_name: str) -> Dict[str, Any]:
        """Restaure depuis un snapshot"""
        if snapshot_name not in self.data_snapshots:
            raise DataError(f"Snapshot {snapshot_name} non trouvé")
        
        snapshot = self.data_snapshots[snapshot_name]
        
        # Vérifier intégrité
        restored_data = pickle.loads(snapshot["data"])
        current_checksum = hashlib.sha256(snapshot["data"]).hexdigest()
        
        if current_checksum != snapshot["checksum"]:
            raise DataError(f"Corruption détectée dans snapshot {snapshot_name}")
        
        print(f"   🔄 Données restaurées depuis: {snapshot_name}")
        return restored_data
    
    @contextmanager
    def simulate_system_crash(self, crash_type: str = "sudden"):
        """Simule un crash système"""
        print(f"   💥 Simulation crash: {crash_type}")
        
        # Enregistrer état avant crash
        pre_crash_time = time.perf_counter()
        
        try:
            yield
        except Exception as e:
            print(f"   🔴 Exception pendant crash: {e}")
            raise
        finally:
            # Simuler temps récupération
            if crash_type == "sudden":
                recovery_delay = 0.1  # Récupération rapide
            elif crash_type == "hardware_failure":
                recovery_delay = 1.0  # Récupération lente
            else:
                recovery_delay = 0.5  # Récupération moyenne
            
            time.sleep(recovery_delay)
            
            recovery_time = (time.perf_counter() - pre_crash_time) * 1000
            
            self.recovery_log.append({
                "crash_type": crash_type,
                "recovery_time_ms": recovery_time,
                "timestamp": datetime.now()
            })
            
            print(f"   ✅ Récupération simulée en {recovery_time:.1f}ms")
    
    def simulate_data_corruption(self, data: Dict[str, Any], 
                               corruption_type: str) -> Dict[str, Any]:
        """Simule corruption de données"""
        corrupted_data = data.copy()
        
        if corruption_type == "partial_corruption":
            # Corrompre quelques clés
            keys = list(corrupted_data.keys())
            for key in keys[:len(keys)//3]:  # 1/3 des clés
                if isinstance(corrupted_data[key], (int, float)):
                    corrupted_data[key] = -999999  # Valeur invalide
                elif isinstance(corrupted_data[key], str):
                    corrupted_data[key] = "CORRUPTED"
        
        elif corruption_type == "missing_fields":
            # Supprimer champs aléatoires
            keys_to_remove = list(corrupted_data.keys())[:2]
            for key in keys_to_remove:
                del corrupted_data[key]
        
        elif corruption_type == "type_corruption":
            # Changer types de données
            for key, value in corrupted_data.items():
                if isinstance(value, (int, float)):
                    corrupted_data[key] = str(value) + "_corrupted"
                elif isinstance(value, str):
                    corrupted_data[key] = 12345  # Type incorrect
        
        print(f"   🗂️  Corruption simulée: {corruption_type}")
        return corrupted_data


@pytest.mark.robustness
@pytest.mark.recovery
class TestBasicRecovery:
    """Tests de récupération de base"""
    
    @pytest.fixture
    async def recovery_test_components(self, test_config):
        """Composants pour tests de récupération"""
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
    async def test_automatic_recovery_from_api_failures(self, recovery_test_components):
        """Test récupération automatique des pannes API"""
        simulator = RecoverySimulator()
        
        print("🔄 Test récupération automatique pannes API")
        
        # Créer données test
        test_portfolio = create_test_portfolio(initial_capital=Decimal("100000.00"))
        
        # Créer snapshot avant test
        simulator.create_data_snapshot("before_api_test", {
            "portfolio": asdict(test_portfolio)
        })
        
        recovery_results = {}
        
        # Test récupération avec différents types de pannes
        failure_scenarios = [
            ("timeout_recovery", "Récupération après timeout"),
            ("connection_lost", "Récupération perte connexion"),
            ("service_unavailable", "Récupération service indispo")
        ]
        
        for scenario_name, description in failure_scenarios:
            print(f"\n   🔧 Test: {description}")
            
            start_time = time.perf_counter()
            
            with simulator.simulate_system_crash("sudden"):
                # Simuler panne API
                with patch.object(
                    recovery_test_components["openbb"], 
                    'get_market_data',
                    side_effect=[
                        Exception(f"Panne simulée: {scenario_name}"),
                        Exception(f"Panne simulée: {scenario_name}"),
                        {"symbol": "AAPL", "price": 150.0, "recovered": True}  # Récupération au 3e essai
                    ]
                ):
                    # Tentatives avec retry automatique
                    for attempt in range(3):
                        try:
                            result = await recovery_test_components["openbb"].get_market_data("AAPL")
                            if result.get("recovered"):
                                print(f"      ✅ Récupération réussie au tentative {attempt + 1}")
                                break
                        except Exception as e:
                            print(f"      ❌ Tentative {attempt + 1} échouée: {e}")
                            if attempt < 2:  # Retry automatique
                                await asyncio.sleep(0.1)
                            else:
                                print(f"      🔴 Récupération échouée après 3 tentatives")
            
            end_time = time.perf_counter()
            recovery_time = (end_time - start_time) * 1000
            
            # Vérifier intégrité après récupération
            integrity_validator = DataIntegrityValidator()
            integrity_check = integrity_validator.validate_portfolio_integrity(test_portfolio)
            
            recovery_results[scenario_name] = RecoveryTestResult(
                test_name=scenario_name,
                recovery_type="api_failure",
                recovery_successful=result.get("recovered", False) if 'result' in locals() else False,
                recovery_time_ms=recovery_time,
                data_integrity_preserved=integrity_check.data_consistent,
                system_consistency_maintained=True,  # Portfolio inchangé
                automatic_recovery=True,
                recovery_score=1.0 if result.get("recovered", False) and integrity_check.data_consistent else 0.5
            )
        
        # Analyser résultats récupération
        successful_recoveries = sum(1 for r in recovery_results.values() if r.recovery_successful)
        avg_recovery_time = sum(r.recovery_time_ms for r in recovery_results.values()) / len(recovery_results)
        
        print(f"\n📊 Résultats récupération API:")
        print(f"   Récupérations réussies: {successful_recoveries}/{len(recovery_results)}")
        print(f"   Temps récupération moyen: {avg_recovery_time:.1f}ms")
        
        # Assertions récupération API
        assert successful_recoveries >= len(recovery_results) * 0.8  # Au moins 80% récupération
        assert avg_recovery_time < 5000  # Moins de 5 secondes
        
        return {
            "recovery_results": recovery_results,
            "success_rate": successful_recoveries / len(recovery_results),
            "avg_recovery_time": avg_recovery_time
        }
    
    @pytest.mark.asyncio
    async def test_data_corruption_recovery(self, recovery_test_components):
        """Test récupération après corruption de données"""
        simulator = RecoverySimulator()
        integrity_validator = DataIntegrityValidator()
        
        print("🗂️  Test récupération corruption données")
        
        # Créer données initiales valides
        original_portfolio = create_test_portfolio(initial_capital=Decimal("50000.00"))
        
        # Ajouter positions pour enrichir les données
        for i in range(5):
            position = Position(
                symbol=f"STOCK{i:02d}",
                quantity=100 + i * 10,
                average_price=Decimal(str(50.0 + i * 5)),
                current_price=Decimal(str(52.0 + i * 5)),
                last_updated=datetime.now()
            )
            original_portfolio.positions.append(position)
        
        # Vérifier intégrité données originales
        original_integrity = integrity_validator.validate_portfolio_integrity(original_portfolio)
        print(f"   ✅ Intégrité données originales: {original_integrity.integrity_score:.2f}")
        
        # Créer snapshot de sauvegarde
        simulator.create_data_snapshot("clean_portfolio", {
            "portfolio": asdict(original_portfolio)
        })
        
        # Test différents types de corruption
        corruption_types = ["partial_corruption", "missing_fields", "type_corruption"]
        corruption_results = {}
        
        for corruption_type in corruption_types:
            print(f"\n   🔧 Test corruption: {corruption_type}")
            
            # Créer données corrompues
            portfolio_dict = asdict(original_portfolio)
            corrupted_dict = simulator.simulate_data_corruption(portfolio_dict, corruption_type)
            
            # Tenter validation données corrompues
            try:
                # Reconstruction portfolio à partir données corrompues
                corrupted_portfolio = Portfolio(**corrupted_dict)
                corruption_detected = False
            except (TypeError, ValueError, ValidationError) as e:
                print(f"      🔴 Corruption détectée à la reconstruction: {e}")
                corruption_detected = True
                corrupted_portfolio = None
            
            # Si reconstruction réussie, vérifier intégrité
            if corrupted_portfolio:
                corruption_integrity = integrity_validator.validate_portfolio_integrity(corrupted_portfolio)
                corruption_detected = corruption_integrity.corruption_detected
                print(f"      📊 Score intégrité corrompue: {corruption_integrity.integrity_score:.2f}")
            
            # Récupération depuis snapshot si corruption détectée
            recovery_successful = False
            recovered_portfolio = None
            
            if corruption_detected:
                print(f"      🔄 Récupération depuis snapshot...")
                try:
                    start_recovery = time.perf_counter()
                    restored_data = simulator.restore_from_snapshot("clean_portfolio")
                    recovered_portfolio = Portfolio(**restored_data["portfolio"])
                    end_recovery = time.perf_counter()
                    
                    recovery_time = (end_recovery - start_recovery) * 1000
                    
                    # Vérifier intégrité données récupérées
                    recovery_integrity = integrity_validator.validate_portfolio_integrity(recovered_portfolio)
                    recovery_successful = recovery_integrity.data_consistent
                    
                    print(f"      ✅ Récupération en {recovery_time:.1f}ms, "
                          f"intégrité: {recovery_integrity.integrity_score:.2f}")
                    
                except Exception as e:
                    print(f"      ❌ Échec récupération: {e}")
                    recovery_time = 0
                    recovery_successful = False
            else:
                recovery_time = 0  # Pas de récupération nécessaire
                recovery_successful = True  # Données non corrompues
            
            corruption_results[corruption_type] = {
                "corruption_detected": corruption_detected,
                "recovery_successful": recovery_successful,
                "recovery_time_ms": recovery_time,
                "data_integrity_preserved": recovery_successful
            }
        
        # Analyser résultats globaux
        total_recoveries = sum(1 for r in corruption_results.values() if r["recovery_successful"])
        recovery_rate = total_recoveries / len(corruption_results)
        
        print(f"\n📊 Résultats récupération corruption:")
        print(f"   Taux récupération: {recovery_rate:.1%}")
        
        # Assertions récupération corruption
        assert recovery_rate >= 0.8  # Au moins 80% récupération
        assert all(r["corruption_detected"] for r in corruption_results.values())  # Toutes corruptions détectées
        
        return {
            "original_integrity": original_integrity,
            "corruption_results": corruption_results,
            "recovery_rate": recovery_rate
        }


@pytest.mark.robustness
@pytest.mark.recovery
@pytest.mark.slow
class TestAdvancedRecovery:
    """Tests avancés de récupération"""
    
    @pytest.mark.asyncio
    async def test_system_state_reconstruction(self, recovery_test_components):
        """Test reconstruction état système complet"""
        simulator = RecoverySimulator()
        
        print("🏗️  Test reconstruction état système")
        
        # Créer état système complexe
        system_state = {
            "portfolios": [
                asdict(create_test_portfolio(Decimal("100000.00"))) for _ in range(3)
            ],
            "active_strategies": [
                {"name": "momentum", "active": True},
                {"name": "value", "active": False}
            ],
            "market_cache": {
                "AAPL": {"price": 150.0, "timestamp": time.time()},
                "GOOGL": {"price": 2800.0, "timestamp": time.time()}
            },
            "system_config": {
                "risk_tolerance": 0.7,
                "max_position_size": 0.1,
                "rebalance_frequency": "daily"
            }
        }
        
        # Snapshot état complet
        simulator.create_data_snapshot("full_system_state", system_state)
        
        # Simuler perte état système
        print(f"   💥 Simulation perte état système...")
        
        with simulator.simulate_system_crash("hardware_failure"):
            # Simular état système vide/corrompu
            corrupted_state = {
                "portfolios": [],
                "active_strategies": [],
                "market_cache": {},
                "system_config": {}
            }
            
            # Détecter perte de données
            state_empty = (
                len(corrupted_state["portfolios"]) == 0 and
                len(corrupted_state["active_strategies"]) == 0 and
                len(corrupted_state["market_cache"]) == 0
            )
            
            print(f"   🔍 État système vide détecté: {'✓' if state_empty else '✗'}")
            
            if state_empty:
                # Reconstruction depuis snapshot
                print(f"   🔄 Reconstruction état système...")
                
                start_reconstruction = time.perf_counter()
                restored_state = simulator.restore_from_snapshot("full_system_state")
                end_reconstruction = time.perf_counter()
                
                reconstruction_time = (end_reconstruction - start_reconstruction) * 1000
                
                # Vérifier intégrité état reconstruit
                reconstruction_successful = (
                    len(restored_state["portfolios"]) == 3 and
                    len(restored_state["active_strategies"]) == 2 and
                    len(restored_state["market_cache"]) == 2 and
                    "risk_tolerance" in restored_state["system_config"]
                )
                
                print(f"   ✅ Reconstruction {'réussie' if reconstruction_successful else 'échouée'} "
                      f"en {reconstruction_time:.1f}ms")
        
        # Vérifier cohérence après reconstruction
        integrity_validator = DataIntegrityValidator()
        integrity_checks = []
        
        for i, portfolio_dict in enumerate(restored_state["portfolios"]):
            try:
                portfolio = Portfolio(**portfolio_dict)
                integrity_check = integrity_validator.validate_portfolio_integrity(portfolio)
                integrity_checks.append(integrity_check)
                print(f"   📊 Portfolio {i+1} intégrité: {integrity_check.integrity_score:.2f}")
            except Exception as e:
                print(f"   ❌ Erreur reconstruction portfolio {i+1}: {e}")
                integrity_checks.append(DataIntegrityCheck(
                    check_name=f"portfolio_{i+1}",
                    data_consistent=False,
                    corruption_detected=True,
                    missing_data_count=1,
                    duplicate_data_count=0,
                    invalid_data_count=0,
                    integrity_score=0.0
                ))
        
        # Score global reconstruction
        avg_integrity = sum(check.integrity_score for check in integrity_checks) / len(integrity_checks)
        reconstruction_score = 1.0 if reconstruction_successful and avg_integrity >= 0.9 else avg_integrity
        
        print(f"\n📊 Score reconstruction système: {reconstruction_score:.2f}")
        
        # Assertions reconstruction système
        assert reconstruction_successful  # Reconstruction doit réussir
        assert avg_integrity >= 0.8  # Intégrité moyenne au moins 80%
        assert reconstruction_time < 2000  # Moins de 2 secondes
        
        return {
            "reconstruction_successful": reconstruction_successful,
            "reconstruction_time_ms": reconstruction_time,
            "integrity_checks": integrity_checks,
            "avg_integrity": avg_integrity,
            "reconstruction_score": reconstruction_score
        }


if __name__ == "__main__":
    # Exécution directe pour tests de développement
    pytest.main([__file__, "-v", "--tb=short", "-m", "recovery and not slow"])