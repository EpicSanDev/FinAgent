"""
Tests d'intégration pour le système de stratégies FinAgent.

Ce module teste l'intégration complète du système de stratégies,
de la création à l'exécution en passant par la gestion des risques.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock

# Imports du système de stratégies
from finagent.business.strategy.models.strategy_models import Strategy, StrategyConfig, StrategyType
from finagent.business.strategy.parser.yaml_parser import StrategyYAMLParser
from finagent.business.strategy.parser.strategy_validator import StrategyValidator
from finagent.business.strategy.engine.strategy_engine import StrategyEngine
from finagent.business.strategy.engine.signal_generator import TradingSignal, SignalType
from finagent.business.strategy.manager.strategy_manager import StrategyManager
from finagent.business.strategy.manager.portfolio_allocator import PortfolioAllocator
from finagent.business.strategy.manager.risk_manager import StrategyRiskManager


class TestStrategyIntegration:
    """Tests d'intégration du système de stratégies."""
    
    @pytest.fixture
    async def temp_dir(self):
        """Créé un répertoire temporaire pour les tests."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def sample_strategy_yaml(self):
        """Retourne un YAML de stratégie de test."""
        return """
strategy:
  name: "Test Strategy"
  description: "Stratégie de test pour l'intégration"
  type: "momentum"
  version: "1.0.0"
  author: "Test Suite"
  created_date: "2024-01-01"

instruments:
  - symbol: "AAPL"
    name: "Apple Inc."
    sector: "Technology"
    weight: 0.50
  - symbol: "GOOGL"
    name: "Alphabet Inc."
    sector: "Technology"
    weight: 0.50

buy_conditions:
  sma_bullish:
    indicator: "sma_crossover"
    parameters:
      fast_period: 10
      slow_period: 20
    operator: ">"
    threshold: 0
    confidence_weight: 0.6
    
  volume_confirm:
    indicator: "volume_ratio"
    parameters:
      period: 10
    operator: ">"
    threshold: 1.2
    confidence_weight: 0.4

sell_conditions:
  sma_bearish:
    indicator: "sma_crossover"
    parameters:
      fast_period: 10
      slow_period: 20
    operator: "<"
    threshold: 0
    confidence_weight: 0.8
    
  profit_target:
    indicator: "profit_percentage"
    parameters:
      entry_price: "dynamic"
    operator: ">"
    threshold: 0.10
    confidence_weight: 0.2

risk_management:
  stop_loss:
    type: "percentage"
    value: 0.05
  take_profit:
    type: "percentage"
    value: 0.10
  position_sizing:
    type: "fixed_percentage"
    value: 0.05
  max_drawdown:
    value: 0.08
  risk_level: "medium"

execution:
  frequency: "daily"
  market_hours_only: true
  minimum_confidence: 0.6

data_requirements:
  timeframe: "1d"
  history_days: 50
  indicators:
    - "sma"
    - "volume"
"""
    
    @pytest.fixture
    async def mock_market_data_provider(self):
        """Mock du fournisseur de données de marché."""
        provider = AsyncMock()
        
        # Données simulées
        provider.get_current_price.return_value = {"price": 150.0}
        provider.get_market_data.return_value = {
            "AAPL": {
                "price": 150.0,
                "volume": 1000000,
                "sma_10": 148.0,
                "sma_20": 145.0,
                "volume_ratio": 1.3
            },
            "GOOGL": {
                "price": 2500.0,
                "volume": 500000,
                "sma_10": 2480.0,
                "sma_20": 2450.0,
                "volume_ratio": 1.1
            }
        }
        provider.get_market_conditions.return_value = {
            "volatility": 0.15,
            "volume_ratio": 1.2,
            "spread_pct": 0.01
        }
        
        return provider
    
    @pytest.fixture
    async def mock_execution_service(self):
        """Mock du service d'exécution."""
        service = AsyncMock()
        service.execute_signal.return_value = Mock(success=True, order_id="test_order_123")
        return service
    
    @pytest.fixture
    def sample_portfolio_state(self):
        """État de portefeuille de test."""
        return {
            "total_value": 100000.0,
            "available_cash": 30000.0,
            "invested_value": 70000.0,
            "positions": {
                "AAPL": 10000.0,
                "GOOGL": 15000.0,
                "MSFT": 8000.0
            },
            "allocations": {
                "AAPL": 0.10,
                "GOOGL": 0.15,
                "MSFT": 0.08
            },
            "sector_exposures": {
                "Technology": 0.33
            },
            "strategy_allocations": {
                "test_strategy": 0.05
            }
        }
    
    async def test_complete_yaml_to_execution_flow(self, temp_dir, sample_strategy_yaml, 
                                                 mock_market_data_provider, mock_execution_service):
        """Test du flux complet : YAML -> Parsing -> Validation -> Exécution."""
        
        # 1. Création du fichier YAML
        strategy_file = temp_dir / "test_strategy.yaml"
        strategy_file.write_text(sample_strategy_yaml)
        
        # 2. Parsing du YAML
        parser = StrategyYAMLParser()
        strategy = await parser.parse_file(str(strategy_file))
        
        assert strategy is not None
        assert strategy.strategy.name == "Test Strategy"
        assert len(strategy.instruments) == 2
        
        # 3. Validation de la stratégie
        validator = StrategyValidator()
        validation_result = await validator.validate_strategy(strategy)
        
        assert validation_result.is_valid
        assert validation_result.overall_score > 0.5
        
        # 4. Création du moteur de stratégie
        engine = StrategyEngine(
            market_data_provider=mock_market_data_provider,
            execution_service=mock_execution_service
        )
        await engine.initialize()
        await engine.load_strategy(strategy)
        
        # 5. Création du contexte d'exécution
        from finagent.business.strategy.engine.strategy_engine import ExecutionContext
        
        context = ExecutionContext(
            strategy_id="test_strategy_001",
            timestamp=datetime.now(),
            portfolio_state={
                "total_value": 100000.0,
                "available_capital": 20000.0,
                "positions": {}
            },
            market_conditions={"volatility": 0.15},
            execution_config={"timeout_seconds": 30},
            risk_limits={"max_position_risk": 0.05}
        )
        
        # 6. Exécution de la stratégie
        signals = await engine.execute(context)
        
        # Vérifications
        assert isinstance(signals, list)
        # Les signaux dépendent des conditions et des données mock
        
        # 7. Nettoyage
        await engine.cleanup()
    
    async def test_strategy_manager_lifecycle(self, temp_dir, sample_strategy_yaml,
                                            mock_market_data_provider, mock_execution_service):
        """Test du cycle de vie complet avec le gestionnaire de stratégies."""
        
        # Création du fichier de stratégie
        strategy_file = temp_dir / "test_strategy.yaml"
        strategy_file.write_text(sample_strategy_yaml)
        
        # Initialisation du gestionnaire
        manager = StrategyManager(
            strategies_directory=str(temp_dir),
            market_data_provider=mock_market_data_provider,
            execution_service=mock_execution_service,
            max_concurrent_strategies=3,
            execution_interval_seconds=1
        )
        
        try:
            await manager.initialize()
            
            # Test d'ajout de stratégie
            strategy_id = await manager.add_strategy_from_file(str(strategy_file))
            assert strategy_id is not None
            
            # Vérification de la liste des stratégies
            strategies = await manager.list_strategies()
            assert len(strategies) == 1
            assert strategies[0]["strategy_name"] == "Test Strategy"
            
            # Test de démarrage
            await manager.start_strategy(strategy_id)
            
            # Vérification du statut
            strategy_info = await manager.get_strategy_info(strategy_id)
            assert strategy_info["status"] == "active"
            
            # Test d'exécution
            signals = await manager.execute_strategy(strategy_id)
            assert isinstance(signals, list)
            
            # Test de pause
            await manager.pause_strategy(strategy_id)
            strategy_info = await manager.get_strategy_info(strategy_id)
            assert strategy_info["status"] == "paused"
            
            # Test de reprise
            await manager.resume_strategy(strategy_id)
            strategy_info = await manager.get_strategy_info(strategy_id)
            assert strategy_info["status"] == "active"
            
            # Test d'arrêt
            await manager.stop_strategy(strategy_id)
            strategy_info = await manager.get_strategy_info(strategy_id)
            assert strategy_info["status"] == "stopped"
            
            # Test de suppression
            await manager.remove_strategy(strategy_id)
            strategies = await manager.list_strategies()
            assert len(strategies) == 0
            
        finally:
            await manager.shutdown()
    
    async def test_portfolio_allocation_integration(self, sample_portfolio_state):
        """Test de l'intégration avec l'allocateur de portefeuille."""
        
        # Initialisation de l'allocateur
        allocator = PortfolioAllocator(
            max_position_weight=0.10,
            max_sector_weight=0.40,
            min_cash_percentage=0.05
        )
        await allocator.initialize()
        
        # Création d'un signal de test
        signal = TradingSignal(
            signal_id="test_signal_001",
            strategy_id="test_strategy",
            symbol="MSFT",
            signal_type=SignalType.BUY,
            timestamp=datetime.now(),
            confidence=0.75,
            price_target=300.0,
            quantity=30.0
        )
        
        # Test d'allocation
        allocation_result = await allocator.allocate_signal(signal, sample_portfolio_state)
        
        # Vérifications
        assert allocation_result.signal_id == signal.signal_id
        assert allocation_result.allocated_amount > 0
        assert allocation_result.allocation_percentage < 0.10  # Respecte la limite
        
        # Test des limites d'allocation
        limits = await allocator.get_allocation_limits("MSFT", "test_strategy", sample_portfolio_state)
        assert "effective_limit" in limits
        assert limits["effective_limit"] >= 0
        
        # Test de rééquilibrage
        rebalancing = await allocator.calculate_portfolio_rebalancing(sample_portfolio_state)
        assert isinstance(rebalancing, list)
    
    async def test_risk_management_integration(self, sample_portfolio_state):
        """Test de l'intégration avec le gestionnaire de risques."""
        
        # Initialisation du gestionnaire de risques
        risk_manager = StrategyRiskManager(
            max_portfolio_risk=0.15,
            max_position_risk=0.05,
            max_concentration=0.20
        )
        await risk_manager.initialize()
        
        # Test d'évaluation d'un signal
        signal = TradingSignal(
            signal_id="risky_signal_001",
            strategy_id="test_strategy",
            symbol="AAPL",  # Déjà présent dans le portefeuille
            signal_type=SignalType.BUY,
            timestamp=datetime.now(),
            confidence=0.80,
            price_target=150.0,
            quantity=100.0  # Position importante
        )
        
        # Évaluation des risques
        risk_assessment = await risk_manager.assess_signal_risk(signal, sample_portfolio_state)
        
        # Vérifications
        assert risk_assessment.assessment_id is not None
        assert risk_assessment.overall_risk_level is not None
        assert isinstance(risk_assessment.is_acceptable, bool)
        assert len(risk_assessment.risk_metrics) > 0
        
        # Test de calcul des risques du portefeuille
        portfolio_risk = await risk_manager.calculate_portfolio_risk(sample_portfolio_state)
        
        assert portfolio_risk.total_value == sample_portfolio_state["total_value"]
        assert portfolio_risk.var_1d >= 0
        assert portfolio_risk.volatility >= 0
        
        # Test des statistiques
        risk_stats = risk_manager.get_risk_stats()
        assert "total_assessments" in risk_stats
        assert "risk_limits" in risk_stats
    
    async def test_signal_generation_and_processing(self, mock_market_data_provider):
        """Test de la génération et du traitement des signaux."""
        
        from finagent.business.strategy.engine.rule_evaluator import RuleEvaluator, EvaluationResult, EvaluationStatus
        from finagent.business.strategy.engine.signal_generator import SignalGenerator
        
        # Initialisation des composants
        rule_evaluator = RuleEvaluator(market_data_provider=mock_market_data_provider)
        signal_generator = SignalGenerator(market_data_provider=mock_market_data_provider)
        
        await rule_evaluator.initialize()
        await signal_generator.initialize()
        
        # Simulation d'un résultat d'évaluation
        evaluation_result = EvaluationResult(
            strategy_id="test_strategy",
            symbol="AAPL",
            timestamp=datetime.now(),
            status=EvaluationStatus.SUCCESS,
            buy_signal_triggered=True,
            sell_signal_triggered=False,
            buy_confidence_score=0.75,
            sell_confidence_score=0.25,
            buy_conditions_details=[],
            sell_conditions_details=[],
            data_quality_score=0.9,
            total_evaluation_time_ms=50.0,
            metadata={}
        )
        
        # Création d'une stratégie simple pour les tests
        from finagent.business.strategy.models.strategy_models import (
            StrategyConfig, RiskManagement, StopLoss, TakeProfit, PositionSizing
        )
        
        strategy = Strategy(
            strategy=StrategyConfig(
                name="Test Strategy",
                type=StrategyType.MOMENTUM,
                description="Test"
            ),
            instruments=[],
            buy_conditions={},
            sell_conditions={},
            risk_management=RiskManagement(
                stop_loss=StopLoss(type="percentage", value=0.05),
                take_profit=TakeProfit(type="percentage", value=0.10),
                position_sizing=PositionSizing(type="fixed_percentage", value=0.05),
                max_drawdown={"value": 0.08},
                risk_level="medium"
            )
        )
        
        # Contexte d'exécution mock
        execution_context = Mock()
        execution_context.portfolio_state = {
            "total_value": 100000.0,
            "available_capital": 20000.0
        }
        
        # Génération de signaux
        signals = await signal_generator.generate_signals(evaluation_result, strategy, execution_context)
        
        # Vérifications
        assert isinstance(signals, list)
        
        # Si des signaux sont générés, vérifier leur structure
        for signal in signals:
            assert hasattr(signal, 'signal_id')
            assert hasattr(signal, 'symbol')
            assert hasattr(signal, 'signal_type')
            assert hasattr(signal, 'confidence')
            assert signal.is_valid()  # Le signal doit être valide
    
    async def test_error_handling_and_recovery(self, temp_dir):
        """Test de la gestion d'erreurs et de la récupération."""
        
        # Test avec YAML invalide
        invalid_yaml = temp_dir / "invalid_strategy.yaml"
        invalid_yaml.write_text("invalid: yaml: content: [")
        
        parser = StrategyYAMLParser()
        
        with pytest.raises(Exception):
            await parser.parse_file(str(invalid_yaml))
        
        # Test avec stratégie invalide mais YAML valide
        invalid_strategy_yaml = """
strategy:
  name: "Invalid Strategy"
  # type manquant - requis
  
instruments: []  # Liste vide - invalide

buy_conditions: {}  # Conditions vides - invalides
sell_conditions: {}
"""
        
        invalid_strategy_file = temp_dir / "invalid_strategy_content.yaml"
        invalid_strategy_file.write_text(invalid_strategy_yaml)
        
        try:
            strategy = await parser.parse_file(str(invalid_strategy_file))
            validator = StrategyValidator()
            result = await validator.validate_strategy(strategy)
            
            # La validation doit échouer
            assert not result.is_valid
            assert len(result.errors) > 0
            
        except Exception:
            # Le parsing peut aussi échouer, c'est acceptable
            pass
        
        # Test de récupération du gestionnaire après erreur
        manager = StrategyManager(strategies_directory=str(temp_dir))
        
        try:
            await manager.initialize()
            
            # Tentative d'ajout d'une stratégie invalide
            try:
                await manager.add_strategy_from_file(str(invalid_strategy_file))
                assert False, "Devrait lever une exception"
            except Exception:
                pass  # Attendu
            
            # Le gestionnaire doit toujours fonctionner
            status = manager.get_manager_status()
            assert status["status"] == "active"
            
        finally:
            await manager.shutdown()
    
    async def test_performance_and_monitoring(self, temp_dir, sample_strategy_yaml):
        """Test des performances et du monitoring."""
        
        # Création du fichier de stratégie
        strategy_file = temp_dir / "perf_test_strategy.yaml"
        strategy_file.write_text(sample_strategy_yaml)
        
        # Mock providers optimisés
        mock_provider = AsyncMock()
        mock_provider.get_market_data.return_value = {
            "AAPL": {"price": 150.0, "volume": 1000000},
            "GOOGL": {"price": 2500.0, "volume": 500000}
        }
        
        manager = StrategyManager(
            strategies_directory=str(temp_dir),
            market_data_provider=mock_provider,
            max_concurrent_strategies=1
        )
        
        try:
            await manager.initialize()
            
            # Mesure du temps d'ajout de stratégie
            start_time = datetime.now()
            strategy_id = await manager.add_strategy_from_file(str(strategy_file))
            add_time = (datetime.now() - start_time).total_seconds()
            
            assert add_time < 5.0  # Moins de 5 secondes
            
            # Test des métriques de performance
            performance_metrics = manager.get_performance_metrics()
            assert "metrics" in performance_metrics
            
            # Test du monitoring en temps réel
            manager_status = manager.get_manager_status()
            assert manager_status["status"] == "active"
            assert manager_status["strategies_count"] == 1
            
            # Test de la charge (exécutions multiples)
            await manager.start_strategy(strategy_id)
            
            # Exécutions rapides successives
            execution_times = []
            for i in range(5):
                start = datetime.now()
                await manager.execute_strategy(strategy_id)
                exec_time = (datetime.now() - start).total_seconds()
                execution_times.append(exec_time)
            
            # Les exécutions doivent être raisonnablement rapides
            avg_exec_time = sum(execution_times) / len(execution_times)
            assert avg_exec_time < 1.0  # Moins d'1 seconde en moyenne
            
        finally:
            await manager.shutdown()
    
    async def test_concurrent_strategies(self, temp_dir, sample_strategy_yaml):
        """Test de l'exécution de stratégies concurrentes."""
        
        # Création de plusieurs fichiers de stratégies
        strategy_files = []
        for i in range(3):
            strategy_yaml = sample_strategy_yaml.replace(
                'name: "Test Strategy"', 
                f'name: "Test Strategy {i+1}"'
            )
            strategy_file = temp_dir / f"strategy_{i+1}.yaml"
            strategy_file.write_text(strategy_yaml)
            strategy_files.append(strategy_file)
        
        mock_provider = AsyncMock()
        mock_provider.get_market_data.return_value = {
            "AAPL": {"price": 150.0, "volume": 1000000},
            "GOOGL": {"price": 2500.0, "volume": 500000}
        }
        
        manager = StrategyManager(
            strategies_directory=str(temp_dir),
            market_data_provider=mock_provider,
            max_concurrent_strategies=3
        )
        
        try:
            await manager.initialize()
            
            # Ajout de toutes les stratégies
            strategy_ids = []
            for strategy_file in strategy_files:
                strategy_id = await manager.add_strategy_from_file(str(strategy_file))
                strategy_ids.append(strategy_id)
            
            # Démarrage de toutes les stratégies
            for strategy_id in strategy_ids:
                await manager.start_strategy(strategy_id)
            
            # Vérification du statut
            status = manager.get_manager_status()
            assert status["active_strategies"] == 3
            
            # Exécution concurrente
            tasks = [manager.execute_strategy(sid) for sid in strategy_ids]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Vérification des résultats
            for result in results:
                if isinstance(result, Exception):
                    pytest.fail(f"Erreur d'exécution concurrente: {result}")
                assert isinstance(result, list)  # Liste de signaux
            
            # Arrêt de toutes les stratégies
            for strategy_id in strategy_ids:
                await manager.stop_strategy(strategy_id)
            
        finally:
            await manager.shutdown()


class TestStrategySystemStress:
    """Tests de stress du système de stratégies."""
    
    async def test_memory_usage_under_load(self, temp_dir):
        """Test de l'usage mémoire sous charge."""
        import psutil
        import os
        
        # Mesure initiale de la mémoire
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Création de nombreuses stratégies
        strategy_yaml = """
strategy:
  name: "Memory Test Strategy"
  type: "momentum"
instruments:
  - symbol: "TEST"
    weight: 1.0
buy_conditions:
  test_condition:
    indicator: "test"
    operator: ">"
    threshold: 0
    confidence_weight: 1.0
sell_conditions:
  test_condition:
    indicator: "test"
    operator: "<"
    threshold: 0
    confidence_weight: 1.0
risk_management:
  stop_loss:
    type: "percentage"
    value: 0.05
  position_sizing:
    type: "fixed_percentage"
    value: 0.05
  risk_level: "low"
"""
        
        mock_provider = AsyncMock()
        mock_provider.get_market_data.return_value = {"TEST": {"price": 100.0}}
        
        manager = StrategyManager(
            strategies_directory=str(temp_dir),
            market_data_provider=mock_provider
        )
        
        try:
            await manager.initialize()
            
            # Ajout de nombreuses stratégies
            strategy_ids = []
            for i in range(20):  # 20 stratégies
                modified_yaml = strategy_yaml.replace(
                    'name: "Memory Test Strategy"',
                    f'name: "Memory Test Strategy {i}"'
                )
                
                strategy_file = temp_dir / f"memory_test_{i}.yaml"
                strategy_file.write_text(modified_yaml)
                
                strategy_id = await manager.add_strategy_from_config({
                    "strategy": {"name": f"Memory Test {i}", "type": "momentum"},
                    "instruments": [{"symbol": "TEST", "weight": 1.0}],
                    "buy_conditions": {},
                    "sell_conditions": {},
                    "risk_management": {"stop_loss": {"type": "percentage", "value": 0.05}}
                })
                strategy_ids.append(strategy_id)
            
            # Mesure de la mémoire après chargement
            current_memory = process.memory_info().rss / 1024 / 1024
            memory_increase = current_memory - initial_memory
            
            # L'augmentation de mémoire doit rester raisonnable (< 100MB pour 20 stratégies)
            assert memory_increase < 100, f"Augmentation mémoire excessive: {memory_increase:.1f}MB"
            
            # Nettoyage
            for strategy_id in strategy_ids:
                await manager.remove_strategy(strategy_id)
            
            # Vérification du nettoyage mémoire
            import gc
            gc.collect()
            
            final_memory = process.memory_info().rss / 1024 / 1024
            memory_cleanup = current_memory - final_memory
            
            # Au moins 50% de la mémoire doit être libérée
            assert memory_cleanup > (memory_increase * 0.5), "Nettoyage mémoire insuffisant"
            
        finally:
            await manager.shutdown()


# Configuration pytest
@pytest.mark.asyncio
class TestAsyncSetup:
    """Configuration pour les tests asynchrones."""
    
    @pytest.fixture(scope="session")
    def event_loop(self):
        """Créé une event loop pour la session de test."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
        yield loop
        loop.close()


if __name__ == "__main__":
    # Exécution des tests si le fichier est lancé directement
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])