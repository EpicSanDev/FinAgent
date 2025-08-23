"""
Test manuel d'intégration du système de stratégies FinAgent.

Ce script permet de tester manuellement le système complet
pour valider son bon fonctionnement.
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime

# Ajout du répertoire parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from finagent.business.strategy.parser.yaml_parser import StrategyYAMLParser
from finagent.business.strategy.parser.strategy_validator import StrategyValidator
from finagent.business.strategy.engine.strategy_engine import StrategyEngine, ExecutionContext, ExecutionMode
from finagent.business.strategy.manager.strategy_manager import StrategyManager


class MockMarketDataProvider:
    """Fournisseur de données de marché simulé pour les tests."""
    
    def __init__(self):
        self.data = {}
    
    async def initialize(self):
        """Initialise le fournisseur de données."""
        pass
        
    async def connect(self):
        """Connecte au fournisseur de données."""
        pass
    
    async def get_current_price(self, symbol: str) -> dict:
        """Retourne un prix simulé."""
        prices = {
            "AAPL": 150.0,
            "GOOGL": 2500.0,
            "MSFT": 300.0,
            "AMZN": 3200.0,
            "TSLA": 800.0
        }
        return {"price": prices.get(symbol, 100.0)}
    
    async def get_market_data(self, symbols: list) -> dict:
        """Retourne des données de marché simulées."""
        data = {}
        for symbol in symbols:
            base_price = await self.get_current_price(symbol)
            data[symbol] = {
                "price": base_price["price"],
                "volume": 1000000,
                "sma_10": base_price["price"] * 0.98,
                "sma_20": base_price["price"] * 0.95,
                "volume_ratio": 1.2,
                "rsi": 60.0,
                "macd": 0.5,
                "bollinger_upper": base_price["price"] * 1.02,
                "bollinger_lower": base_price["price"] * 0.98
            }
        return data
    
    async def get_market_conditions(self) -> dict:
        """Retourne les conditions de marché simulées."""
        return {
            "volatility": 0.15,
            "volume_ratio": 1.2,
            "spread_pct": 0.01,
            "market_trend": "bullish"
        }


class MockExecutionService:
    """Service d'exécution simulé pour les tests."""
    
    def __init__(self):
        self.executed_signals = []
    
    async def execute_signal(self, signal):
        """Simule l'exécution d'un signal."""
        from finagent.business.strategy.engine.signal_generator import ExecutionResult
        
        self.executed_signals.append(signal)
        
        return ExecutionResult(
            signal_id=signal.signal_id,
            success=True,
            order_id=f"ORDER_{len(self.executed_signals):04d}",
            executed_price=signal.price_target * 0.999,  # Léger slippage
            executed_quantity=signal.quantity,
            execution_timestamp=datetime.now(),
            fees=signal.quantity * signal.price_target * 0.001,  # 0.1% de frais
            metadata={"simulated": True}
        )
    
    def get_executed_signals(self):
        """Retourne la liste des signaux exécutés."""
        return self.executed_signals.copy()


async def test_yaml_parsing():
    """Test du parsing d'un fichier YAML."""
    print("🔍 Test du parsing YAML...")
    
    # Utilisation d'un template existant
    template_path = Path(__file__).parent.parent / "templates" / "simple_test_strategy.yaml"
    
    if not template_path.exists():
        print(f"❌ Template non trouvé: {template_path}")
        return False
    
    try:
        parser = StrategyYAMLParser()
        strategy = parser.parse_file(str(template_path))
        
        print(f"✅ Stratégie parsée: {strategy.strategy.name}")
        print(f"   - Type: {strategy.strategy.type}")
        
        # Vérifier les instruments dans l'univers
        instruments_count = 0
        if strategy.universe and strategy.universe.instruments:
            instruments_count = len(strategy.universe.instruments)
        elif strategy.universe and strategy.universe.watchlist:
            instruments_count = len(strategy.universe.watchlist)
            
        print(f"   - Instruments: {instruments_count}")
        
        # Vérifier les règles
        buy_conditions_count = 0
        sell_conditions_count = 0
        if hasattr(strategy, 'rules') and strategy.rules:
            if hasattr(strategy.rules, 'buy_conditions') and strategy.rules.buy_conditions:
                buy_conditions_count = len(strategy.rules.buy_conditions)
            if hasattr(strategy.rules, 'sell_conditions') and strategy.rules.sell_conditions:
                sell_conditions_count = len(strategy.rules.sell_conditions)
            
        print(f"   - Conditions d'achat: {buy_conditions_count}")
        print(f"   - Conditions de vente: {sell_conditions_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur de parsing: {e}")
        return False


async def test_strategy_validation():
    """Test de la validation d'une stratégie."""
    print("\n🔍 Test de validation de stratégie...")
    
    template_path = Path(__file__).parent.parent / "templates" / "simple_test_strategy.yaml"
    
    try:
        parser = StrategyYAMLParser()
        strategy = parser.parse_file(str(template_path))
        
        validator = StrategyValidator()
        result = validator.validate_strategy(strategy)
        
        print(f"✅ Validation terminée:")
        print(f"   - Valide: {result.is_valid}")
        print(f"   - Erreurs: {len(result.errors)}")
        print(f"   - Avertissements: {len(result.warnings)}")
        print(f"   - Informations: {len(result.infos)}")
        
        if result.errors:
            print("   Erreurs détectées:")
            for error in result.errors[:3]:  # Limite à 3 erreurs
                print(f"     - {error}")
        
        if result.warnings:
            print("   Avertissements:")
            for warning in result.warnings[:3]:  # Limite à 3 avertissements
                print(f"     - {warning}")
        
        return result.is_valid
        
    except Exception as e:
        print(f"❌ Erreur de validation: {e}")
        return False


async def test_strategy_engine():
    """Test du moteur de stratégie."""
    print("\n🔍 Test du moteur de stratégie...")
    
    try:
        # Initialisation des mocks
        market_provider = MockMarketDataProvider()
        execution_service = MockExecutionService()
        
        # Création du moteur
        engine = StrategyEngine(
            data_provider=market_provider
        )
        await engine.initialize()
        
        # Chargement d'une stratégie
        template_path = Path(__file__).parent.parent / "templates" / "simple_test_strategy.yaml"
        parser = StrategyYAMLParser()
        strategy = parser.parse_file(str(template_path))
        
        strategy_id = await engine.load_strategy(strategy)
        
        # Création du contexte d'exécution
        context = ExecutionContext(
            strategy_id=strategy_id,
            symbol="AAPL",
            timestamp=datetime.now(),
            market_data={
                "AAPL": {
                    "price": 150.0,
                    "volume": 1000000,
                    "high": 152.0,
                    "low": 148.0
                }
            },
            portfolio_state={
                "total_value": 100000.0,
                "available_capital": 20000.0,
                "positions": {}
            },
            execution_mode=ExecutionMode.SIMULATION,
            metadata={"test": True},
            market_conditions={"volatility": 0.15},
            execution_config={"timeout_seconds": 30},
            risk_limits={"max_position_risk": 0.05}
        )
        
        # Exécution de la stratégie
        result = await engine.execute_strategy(strategy_id, context)
        
        print(f"✅ Moteur exécuté:")
        print(f"   - Succès: {result.error is None}")
        print(f"   - Temps d'exécution: {result.execution_time_ms:.2f}ms")
        if result.error:
            print(f"   - Erreur: {result.error}")
        if result.signals:
            print(f"   - Signaux générés: {len(result.signals)}")
            for i, signal in enumerate(result.signals[:3]):  # Limite à 3 signaux
                print(f"   - Signal {i+1}: {signal.symbol} ({signal.signal_type.value}) - Confiance: {signal.confidence:.2f}")
        else:
            print(f"   - Aucun signal généré")
        
        await engine.cleanup()
        return True
        
    except Exception as e:
        print(f"❌ Erreur du moteur: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_strategy_manager():
    """Test du gestionnaire de stratégies."""
    print("\n🔍 Test du gestionnaire de stratégies...")
    
    try:
        # Initialisation des mocks
        market_provider = MockMarketDataProvider()
        execution_service = MockExecutionService()
        
        # Répertoire des templates
        templates_dir = Path(__file__).parent.parent / "templates"
        
        # Création du gestionnaire
        manager = StrategyManager(
            strategies_directory=str(templates_dir),
            market_data_provider=market_provider,
            execution_service=execution_service,
            max_concurrent_strategies=3
        )
        
        await manager.initialize()
        
        # Test d'ajout de stratégie
        template_path = templates_dir / "simple_test_strategy.yaml"
        strategy_id = await manager.add_strategy_from_file(str(template_path))
        
        print(f"✅ Stratégie ajoutée: {strategy_id}")
        
        # Test de démarrage
        await manager.start_strategy(strategy_id)
        print("✅ Stratégie démarrée")
        
        # Test d'exécution
        signals = await manager.execute_strategy(strategy_id)
        print(f"✅ Exécution réussie: {len(signals)} signaux")
        
        # Test de statut
        status = manager.get_manager_status()
        print(f"✅ Statut du gestionnaire:")
        print(f"   - Statut: {status['status']}")
        print(f"   - Stratégies actives: {status['active_strategies']}")
        print(f"   - Stratégies totales: {status['strategies_count']}")
        
        # Test d'arrêt
        await manager.stop_strategy(strategy_id)
        print("✅ Stratégie arrêtée")
        
        # Nettoyage
        await manager.shutdown()
        print("✅ Gestionnaire fermé")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur du gestionnaire: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_portfolio_allocation():
    """Test de l'allocation de portefeuille."""
    print("\n🔍 Test de l'allocation de portefeuille...")
    
    try:
        from finagent.business.strategy.manager.portfolio_allocator import PortfolioAllocator
        from finagent.business.strategy.engine.signal_generator import TradingSignal, SignalType, SignalConfidence, SignalPriority
        
        # Initialisation de l'allocateur
        allocator = PortfolioAllocator(
            max_position_weight=0.10,
            max_sector_weight=0.40,
            min_cash_percentage=0.05
        )
        await allocator.initialize()
        
        # État du portefeuille de test
        portfolio_state = {
            "total_value": 100000.0,
            "available_cash": 20000.0,
            "invested_value": 80000.0,
            "positions": {
                "AAPL": 15000.0,
                "GOOGL": 20000.0,
                "MSFT": 10000.0
            },
            "allocations": {
                "AAPL": 0.15,
                "GOOGL": 0.20,
                "MSFT": 0.10
            },
            "sector_exposures": {
                "Technology": 0.45
            },
            "strategy_allocations": {}
        }
        
        # Signal de test
        signal = TradingSignal(
            signal_id="test_allocation_001",
            strategy_id="test_strategy",
            symbol="AMZN",
            signal_type=SignalType.BUY,
            timestamp=datetime.now(),
            confidence=0.75,
            confidence_level=SignalConfidence.HIGH,
            priority=SignalPriority.MEDIUM,
            price_target=3200.0,
            quantity=5.0
        )
        
        # Test d'allocation
        allocation_result = await allocator.allocate_signal(signal, portfolio_state)
        
        print(f"✅ Allocation calculée:")
        print(f"   - Signal: {allocation_result.signal_id}")
        print(f"   - Montant alloué: ${allocation_result.allocated_amount:.2f}")
        print(f"   - Pourcentage: {allocation_result.allocation_percentage:.2%}")
        print(f"   - Quantité ajustée: {allocation_result.adjusted_quantity:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur d'allocation: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_risk_management():
    """Test de la gestion des risques."""
    print("\n🔍 Test de la gestion des risques...")
    
    try:
        from finagent.business.strategy.manager.risk_manager import StrategyRiskManager
        from finagent.business.strategy.engine.signal_generator import TradingSignal, SignalType, SignalConfidence, SignalPriority
        
        # Initialisation du gestionnaire de risques
        risk_manager = StrategyRiskManager(
            max_portfolio_risk=0.15,
            max_position_risk=0.05,
            max_concentration=0.20
        )
        await risk_manager.initialize()
        
        # État du portefeuille de test
        portfolio_state = {
            "total_value": 100000.0,
            "available_cash": 20000.0,
            "positions": {
                "AAPL": 15000.0,
                "GOOGL": 20000.0
            },
            "allocations": {
                "AAPL": 0.15,
                "GOOGL": 0.20
            }
        }
        
        # Signal risqué de test
        signal = TradingSignal(
            signal_id="risky_signal_001",
            strategy_id="test_strategy",
            symbol="AAPL",  # Position existante
            signal_type=SignalType.BUY,
            timestamp=datetime.now(),
            confidence=0.80,
            confidence_level=SignalConfidence.HIGH,
            priority=SignalPriority.HIGH,
            price_target=150.0,
            quantity=200.0  # Position importante
        )
        
        # Évaluation du risque
        risk_assessment = await risk_manager.assess_signal_risk(signal, portfolio_state)
        
        print(f"✅ Évaluation des risques:")
        print(f"   - ID: {risk_assessment.assessment_id}")
        print(f"   - Niveau de risque: {risk_assessment.overall_risk_level}")
        print(f"   - Acceptable: {risk_assessment.is_acceptable}")
        print(f"   - Score de risque: {risk_assessment.risk_score:.3f}")
        print(f"   - Métriques: {len(risk_assessment.risk_metrics)}")
        
        # Calcul du risque du portefeuille
        portfolio_risk = await risk_manager.calculate_portfolio_risk(portfolio_state)
        
        print(f"✅ Risque du portefeuille:")
        print(f"   - VaR 1j: ${portfolio_risk.var_1d:.2f}")
        print(f"   - Volatilité: {portfolio_risk.volatility:.2%}")
        print(f"   - Sharpe ratio: {portfolio_risk.sharpe_ratio:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur de gestion des risques: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_integration_tests():
    """Lance tous les tests d'intégration."""
    print("🚀 Démarrage des tests d'intégration du système de stratégies FinAgent\n")
    
    tests = [
        ("Parsing YAML", test_yaml_parsing),
        ("Validation de stratégie", test_strategy_validation),
        ("Moteur de stratégie", test_strategy_engine),
        ("Gestionnaire de stratégies", test_strategy_manager),
        ("Allocation de portefeuille", test_portfolio_allocation),
        ("Gestion des risques", test_risk_management)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"🧪 {test_name}")
        print('='*60)
        
        try:
            result = await test_func()
            results.append((test_name, result))
            
            if result:
                print(f"\n✅ {test_name}: RÉUSSI")
            else:
                print(f"\n❌ {test_name}: ÉCHEC")
                
        except Exception as e:
            print(f"\n❌ {test_name}: ERREUR - {e}")
            results.append((test_name, False))
    
    # Résumé des résultats
    print(f"\n\n{'='*60}")
    print("📊 RÉSUMÉ DES TESTS")
    print('='*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ RÉUSSI" if result else "❌ ÉCHEC"
        print(f"{test_name:<30} {status}")
    
    print(f"\n🎯 Résultat global: {passed}/{total} tests réussis ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 Tous les tests d'intégration ont réussi !")
        print("Le système de stratégies FinAgent est prêt à l'emploi.")
    else:
        print(f"\n⚠️  {total-passed} test(s) ont échoué.")
        print("Vérifiez les erreurs ci-dessus avant de continuer.")
    
    return passed == total


if __name__ == "__main__":
    # Exécution des tests
    success = asyncio.run(run_integration_tests())
    sys.exit(0 if success else 1)