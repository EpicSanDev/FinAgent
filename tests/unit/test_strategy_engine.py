"""
Tests unitaires pour le moteur de stratégies FinAgent.

Ce module teste le moteur de stratégies, incluant le chargement de stratégies YAML,
l'évaluation de règles, la génération de signaux et la gestion des décisions.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, patch, AsyncMock
import yaml
import tempfile
import os

from finagent.business.strategy.engine.strategy_engine import (
    StrategyEngine, StrategyLoader, RuleEvaluator, SignalGenerator
)
from finagent.business.strategy.models.strategy_models import (
    StrategyType, RiskTolerance, TimeHorizon, PositionSizingMethod
)
from finagent.core.models.decision_models import DecisionType, ConfidenceLevel
from finagent.core.exceptions import (
    StrategyLoadError, RuleEvaluationError, InvalidStrategyError
)
from tests.utils import (
    StockDataFactory, create_test_strategy, create_test_market_data,
    assert_valid_uuid, assert_decimal_equals
)


class TestStrategyLoader:
    """Tests pour le chargeur de stratégies."""
    
    @pytest.fixture
    def sample_strategy_yaml(self):
        """Stratégie YAML échantillon."""
        return """
metadata:
  name: "Momentum Strategy"
  description: "Strategy based on momentum indicators"
  version: "1.0.0"
  author: "FinAgent"
  created_at: "2024-01-01T00:00:00Z"
  updated_at: "2024-01-01T00:00:00Z"

strategy:
  type: "technical"
  risk_tolerance: "medium"
  time_horizon: "short"
  target_return: 0.15
  max_drawdown: 0.10
  rebalance_frequency: "weekly"

portfolio:
  max_positions: 10
  position_sizing: "fixed_percentage"
  max_position_size: 0.20
  min_position_size: 0.02
  cash_reserve: 0.05

risk_management:
  stop_loss: 0.08
  take_profit: 0.20
  trailing_stop: true
  max_correlation: 0.7
  sector_concentration_limit: 0.3

rules:
  - name: "RSI Oversold"
    description: "Buy when RSI is below 30"
    conditions:
      - indicator: "rsi"
        operator: "<"
        value: 30
        timeframe: "1d"
    action: "buy"
    weight: 0.8
    priority: 1
    
  - name: "RSI Overbought"
    description: "Sell when RSI is above 70"
    conditions:
      - indicator: "rsi"
        operator: ">"
        value: 70
        timeframe: "1d"
    action: "sell"
    weight: 0.7
    priority: 2
    
  - name: "Volume Confirmation"
    description: "Confirm with volume"
    conditions:
      - indicator: "volume"
        operator: ">"
        value: 1000000
    action: "confirm"
    weight: 0.5
    priority: 3
"""
    
    @pytest.fixture
    def strategy_loader(self):
        """Chargeur de stratégies configuré."""
        return StrategyLoader()
    
    def test_load_strategy_from_string(self, strategy_loader, sample_strategy_yaml):
        """Test chargement stratégie depuis chaîne YAML."""
        strategy = strategy_loader.load_from_string(sample_strategy_yaml)
        
        # Vérification métadonnées
        assert strategy["metadata"]["name"] == "Momentum Strategy"
        assert strategy["metadata"]["version"] == "1.0.0"
        
        # Vérification configuration stratégie
        assert strategy["strategy"]["type"] == "technical"
        assert strategy["strategy"]["risk_tolerance"] == "medium"
        assert strategy["strategy"]["target_return"] == 0.15
        
        # Vérification règles
        assert len(strategy["rules"]) == 3
        assert strategy["rules"][0]["name"] == "RSI Oversold"
        assert strategy["rules"][0]["action"] == "buy"
    
    def test_load_strategy_from_file(self, strategy_loader, sample_strategy_yaml):
        """Test chargement stratégie depuis fichier."""
        # Créer fichier temporaire
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(sample_strategy_yaml)
            temp_file = f.name
        
        try:
            strategy = strategy_loader.load_from_file(temp_file)
            
            assert strategy["metadata"]["name"] == "Momentum Strategy"
            assert len(strategy["rules"]) == 3
        finally:
            os.unlink(temp_file)
    
    def test_validate_strategy_structure(self, strategy_loader, sample_strategy_yaml):
        """Test validation de la structure de stratégie."""
        strategy = strategy_loader.load_from_string(sample_strategy_yaml)
        
        # Validation réussie
        is_valid, errors = strategy_loader.validate_strategy(strategy)
        assert is_valid is True
        assert len(errors) == 0
    
    def test_invalid_strategy_validation(self, strategy_loader):
        """Test validation stratégie invalide."""
        invalid_strategy = {
            "metadata": {
                "name": ""  # Nom vide
            },
            "strategy": {
                "type": "invalid_type",  # Type invalide
                "target_return": -0.5  # Rendement négatif
            },
            "rules": []  # Pas de règles
        }
        
        is_valid, errors = strategy_loader.validate_strategy(invalid_strategy)
        assert is_valid is False
        assert len(errors) > 0
        
        # Vérifier types d'erreurs
        error_messages = [error["message"] for error in errors]
        assert any("name" in msg.lower() for msg in error_messages)
        assert any("type" in msg.lower() for msg in error_messages)
    
    def test_load_multiple_strategies(self, strategy_loader, sample_strategy_yaml):
        """Test chargement de plusieurs stratégies."""
        # Créer variation de la stratégie
        conservative_yaml = sample_strategy_yaml.replace(
            'risk_tolerance: "medium"', 'risk_tolerance: "low"'
        ).replace(
            'name: "Momentum Strategy"', 'name: "Conservative Strategy"'
        )
        
        strategies = [
            strategy_loader.load_from_string(sample_strategy_yaml),
            strategy_loader.load_from_string(conservative_yaml)
        ]
        
        assert len(strategies) == 2
        assert strategies[0]["metadata"]["name"] == "Momentum Strategy"
        assert strategies[1]["metadata"]["name"] == "Conservative Strategy"
        assert strategies[0]["strategy"]["risk_tolerance"] == "medium"
        assert strategies[1]["strategy"]["risk_tolerance"] == "low"


class TestRuleEvaluator:
    """Tests pour l'évaluateur de règles."""
    
    @pytest.fixture
    def rule_evaluator(self):
        """Évaluateur de règles configuré."""
        return RuleEvaluator()
    
    @pytest.fixture
    def sample_market_data(self):
        """Données de marché échantillon."""
        return {
            "AAPL": {
                "price": 150.25,
                "volume": 2500000,
                "rsi": 35.2,
                "macd": 0.5,
                "sma_20": 148.50,
                "sma_50": 145.80,
                "pe_ratio": 28.5,
                "market_cap": 2500000000000,
                "timestamp": datetime.now()
            },
            "GOOGL": {
                "price": 2750.80,
                "volume": 1200000,
                "rsi": 72.8,
                "macd": -0.3,
                "sma_20": 2720.00,
                "sma_50": 2680.00,
                "pe_ratio": 22.1,
                "market_cap": 1800000000000,
                "timestamp": datetime.now()
            }
        }
    
    @pytest.fixture
    def sample_rules(self):
        """Règles échantillon."""
        return [
            {
                "name": "RSI Oversold",
                "conditions": [
                    {"indicator": "rsi", "operator": "<", "value": 40}
                ],
                "action": "buy",
                "weight": 0.8,
                "priority": 1
            },
            {
                "name": "RSI Overbought",
                "conditions": [
                    {"indicator": "rsi", "operator": ">", "value": 70}
                ],
                "action": "sell",
                "weight": 0.7,
                "priority": 2
            },
            {
                "name": "Volume and RSI",
                "conditions": [
                    {"indicator": "rsi", "operator": "<", "value": 50},
                    {"indicator": "volume", "operator": ">", "value": 2000000}
                ],
                "action": "buy",
                "weight": 0.6,
                "priority": 3,
                "condition_logic": "AND"
            }
        ]
    
    def test_evaluate_single_condition(self, rule_evaluator, sample_market_data):
        """Test évaluation d'une condition unique."""
        symbol = "AAPL"
        market_data = sample_market_data[symbol]
        
        # Condition vraie
        condition_true = {"indicator": "rsi", "operator": "<", "value": 40}
        result_true = rule_evaluator.evaluate_condition(condition_true, market_data)
        assert result_true is True  # RSI=35.2 < 40
        
        # Condition fausse
        condition_false = {"indicator": "rsi", "operator": ">", "value": 40}
        result_false = rule_evaluator.evaluate_condition(condition_false, market_data)
        assert result_false is False  # RSI=35.2 > 40 est faux
    
    def test_evaluate_multiple_conditions_and(self, rule_evaluator, sample_market_data):
        """Test évaluation de conditions multiples avec AND."""
        symbol = "AAPL"
        market_data = sample_market_data[symbol]
        
        conditions = [
            {"indicator": "rsi", "operator": "<", "value": 40},  # True: 35.2 < 40
            {"indicator": "volume", "operator": ">", "value": 2000000}  # True: 2500000 > 2000000
        ]
        
        result = rule_evaluator.evaluate_conditions(conditions, market_data, logic="AND")
        assert result is True  # Toutes les conditions sont vraies
        
        # Test avec une condition fausse
        conditions_mixed = [
            {"indicator": "rsi", "operator": "<", "value": 40},  # True
            {"indicator": "volume", "operator": "<", "value": 1000000}  # False
        ]
        
        result_mixed = rule_evaluator.evaluate_conditions(conditions_mixed, market_data, logic="AND")
        assert result_mixed is False  # Une condition fausse
    
    def test_evaluate_multiple_conditions_or(self, rule_evaluator, sample_market_data):
        """Test évaluation de conditions multiples avec OR."""
        symbol = "AAPL"
        market_data = sample_market_data[symbol]
        
        conditions = [
            {"indicator": "rsi", "operator": ">", "value": 80},  # False: 35.2 > 80
            {"indicator": "volume", "operator": ">", "value": 2000000}  # True: 2500000 > 2000000
        ]
        
        result = rule_evaluator.evaluate_conditions(conditions, market_data, logic="OR")
        assert result is True  # Au moins une condition vraie
        
        # Test avec toutes conditions fausses
        conditions_false = [
            {"indicator": "rsi", "operator": ">", "value": 80},  # False
            {"indicator": "volume", "operator": "<", "value": 1000000}  # False
        ]
        
        result_false = rule_evaluator.evaluate_conditions(conditions_false, market_data, logic="OR")
        assert result_false is False  # Toutes les conditions fausses
    
    def test_evaluate_rule(self, rule_evaluator, sample_market_data, sample_rules):
        """Test évaluation de règle complète."""
        symbol = "AAPL"
        market_data = sample_market_data[symbol]
        
        # Règle RSI Oversold - devrait être vraie pour AAPL (RSI=35.2)
        rule_oversold = sample_rules[0]
        result = rule_evaluator.evaluate_rule(rule_oversold, symbol, market_data)
        
        assert result["triggered"] is True
        assert result["action"] == "buy"
        assert result["weight"] == 0.8
        assert result["rule_name"] == "RSI Oversold"
        
        # Règle RSI Overbought - devrait être fausse pour AAPL
        rule_overbought = sample_rules[1]
        result_false = rule_evaluator.evaluate_rule(rule_overbought, symbol, market_data)
        
        assert result_false["triggered"] is False
    
    def test_evaluate_all_rules(self, rule_evaluator, sample_market_data, sample_rules):
        """Test évaluation de toutes les règles."""
        symbol = "AAPL"
        market_data = sample_market_data[symbol]
        
        results = rule_evaluator.evaluate_all_rules(sample_rules, symbol, market_data)
        
        # Vérifier que toutes les règles ont été évaluées
        assert len(results) == len(sample_rules)
        
        # Vérifier résultats spécifiques
        oversold_result = next(r for r in results if r["rule_name"] == "RSI Oversold")
        assert oversold_result["triggered"] is True
        
        overbought_result = next(r for r in results if r["rule_name"] == "RSI Overbought")
        assert overbought_result["triggered"] is False
        
        volume_rsi_result = next(r for r in results if r["rule_name"] == "Volume and RSI")
        assert volume_rsi_result["triggered"] is True  # RSI < 50 AND volume > 2M
    
    def test_operator_validation(self, rule_evaluator):
        """Test validation des opérateurs."""
        test_data = {"indicator_value": 50}
        
        operators_test_cases = [
            ({"indicator": "indicator_value", "operator": ">", "value": 40}, True),
            ({"indicator": "indicator_value", "operator": "<", "value": 40}, False),
            ({"indicator": "indicator_value", "operator": ">=", "value": 50}, True),
            ({"indicator": "indicator_value", "operator": "<=", "value": 50}, True),
            ({"indicator": "indicator_value", "operator": "==", "value": 50}, True),
            ({"indicator": "indicator_value", "operator": "!=", "value": 40}, True)
        ]
        
        for condition, expected_result in operators_test_cases:
            result = rule_evaluator.evaluate_condition(condition, test_data)
            assert result == expected_result
    
    def test_missing_indicator_handling(self, rule_evaluator):
        """Test gestion d'indicateur manquant."""
        market_data = {"price": 100, "volume": 1000000}
        condition = {"indicator": "missing_indicator", "operator": ">", "value": 50}
        
        # Devrait gérer gracieusement l'indicateur manquant
        result = rule_evaluator.evaluate_condition(condition, market_data)
        assert result is False  # Par défaut, condition non satisfaite si indicateur manquant


class TestSignalGenerator:
    """Tests pour le générateur de signaux."""
    
    @pytest.fixture
    def signal_generator(self):
        """Générateur de signaux configuré."""
        return SignalGenerator()
    
    @pytest.fixture
    def sample_rule_results(self):
        """Résultats de règles échantillon."""
        return [
            {
                "rule_name": "RSI Oversold",
                "triggered": True,
                "action": "buy",
                "weight": 0.8,
                "confidence": 0.9,
                "priority": 1
            },
            {
                "rule_name": "Volume Confirmation",
                "triggered": True,
                "action": "buy",
                "weight": 0.5,
                "confidence": 0.7,
                "priority": 3
            },
            {
                "rule_name": "RSI Overbought",
                "triggered": False,
                "action": "sell",
                "weight": 0.7,
                "confidence": 0.8,
                "priority": 2
            }
        ]
    
    def test_generate_signal_single_action(self, signal_generator, sample_rule_results):
        """Test génération de signal avec action unique."""
        symbol = "AAPL"
        
        signal = signal_generator.generate_signal(symbol, sample_rule_results)
        
        assert signal["symbol"] == symbol
        assert signal["action"] == "buy"  # Action dominante
        assert signal["confidence"] > 0
        assert signal["strength"] > 0
        assert "triggered_rules" in signal
        assert len(signal["triggered_rules"]) == 2  # 2 règles déclenchées
    
    def test_signal_strength_calculation(self, signal_generator):
        """Test calcul de la force du signal."""
        rule_results = [
            {"triggered": True, "action": "buy", "weight": 0.8, "confidence": 0.9},
            {"triggered": True, "action": "buy", "weight": 0.6, "confidence": 0.8},
            {"triggered": True, "action": "buy", "weight": 0.4, "confidence": 0.7}
        ]
        
        signal = signal_generator.generate_signal("TEST", rule_results)
        
        # Force = moyenne pondérée des poids × confiances
        expected_strength = (0.8 * 0.9 + 0.6 * 0.8 + 0.4 * 0.7) / 3
        assert abs(signal["strength"] - expected_strength) < 0.01
    
    def test_conflicting_signals_resolution(self, signal_generator):
        """Test résolution de signaux conflictuels."""
        conflicting_results = [
            {"triggered": True, "action": "buy", "weight": 0.8, "confidence": 0.9, "priority": 1},
            {"triggered": True, "action": "sell", "weight": 0.6, "confidence": 0.7, "priority": 2},
            {"triggered": True, "action": "buy", "weight": 0.5, "confidence": 0.8, "priority": 3}
        ]
        
        signal = signal_generator.generate_signal("CONFLICT", conflicting_results)
        
        # L'action avec le poids total le plus élevé devrait dominer
        assert signal["action"] == "buy"  # 0.8 + 0.5 = 1.3 > 0.6
        assert "conflicting_signals" in signal
        assert signal["conflicting_signals"] is True
    
    def test_no_triggered_rules(self, signal_generator):
        """Test aucune règle déclenchée."""
        no_triggers = [
            {"triggered": False, "action": "buy", "weight": 0.8},
            {"triggered": False, "action": "sell", "weight": 0.7}
        ]
        
        signal = signal_generator.generate_signal("NO_SIGNAL", no_triggers)
        
        assert signal["action"] == "hold"
        assert signal["strength"] == 0
        assert signal["confidence"] == 0
        assert len(signal["triggered_rules"]) == 0
    
    def test_signal_metadata(self, signal_generator, sample_rule_results):
        """Test métadonnées du signal."""
        signal = signal_generator.generate_signal("META", sample_rule_results)
        
        assert "timestamp" in signal
        assert "signal_id" in signal
        assert isinstance(signal["timestamp"], datetime)
        assert_valid_uuid(signal["signal_id"])
        
        # Métadonnées additionnelles
        assert "rule_count" in signal
        assert "triggered_rule_count" in signal
        assert signal["rule_count"] == len(sample_rule_results)
        assert signal["triggered_rule_count"] == 2


class TestStrategyEngine:
    """Tests pour le moteur de stratégies principal."""
    
    @pytest.fixture
    def strategy_engine(self):
        """Moteur de stratégies configuré."""
        return StrategyEngine()
    
    @pytest.fixture
    def complete_strategy(self):
        """Stratégie complète pour tests."""
        return {
            "metadata": {
                "name": "Test Strategy",
                "version": "1.0.0"
            },
            "strategy": {
                "type": "technical",
                "risk_tolerance": "medium",
                "time_horizon": "short"
            },
            "portfolio": {
                "max_positions": 10,
                "position_sizing": "fixed_percentage",
                "max_position_size": 0.20
            },
            "risk_management": {
                "stop_loss": 0.08,
                "take_profit": 0.20
            },
            "rules": [
                {
                    "name": "RSI Entry",
                    "conditions": [
                        {"indicator": "rsi", "operator": "<", "value": 35}
                    ],
                    "action": "buy",
                    "weight": 0.8,
                    "priority": 1
                },
                {
                    "name": "RSI Exit",
                    "conditions": [
                        {"indicator": "rsi", "operator": ">", "value": 65}
                    ],
                    "action": "sell",
                    "weight": 0.7,
                    "priority": 2
                }
            ]
        }
    
    @pytest.fixture
    def portfolio_context(self):
        """Contexte de portefeuille pour tests."""
        return {
            "total_value": 100000,
            "cash_balance": 10000,
            "positions": [
                {"symbol": "AAPL", "quantity": 50, "value": 7500},
                {"symbol": "GOOGL", "quantity": 3, "value": 8250}
            ],
            "risk_metrics": {
                "portfolio_beta": 1.15,
                "var_95": 0.023
            }
        }
    
    @pytest.mark.asyncio
    async def test_load_strategy(self, strategy_engine, complete_strategy):
        """Test chargement de stratégie dans le moteur."""
        strategy_id = await strategy_engine.load_strategy(complete_strategy)
        
        assert_valid_uuid(strategy_id)
        assert strategy_id in strategy_engine.loaded_strategies
        
        loaded_strategy = strategy_engine.get_strategy(strategy_id)
        assert loaded_strategy["metadata"]["name"] == "Test Strategy"
    
    @pytest.mark.asyncio
    async def test_analyze_symbol(self, strategy_engine, complete_strategy):
        """Test analyse d'un symbole."""
        strategy_id = await strategy_engine.load_strategy(complete_strategy)
        
        market_data = {
            "AAPL": {
                "price": 150.25,
                "rsi": 32.5,  # Déclenchera la règle d'achat
                "volume": 2500000,
                "timestamp": datetime.now()
            }
        }
        
        analysis = await strategy_engine.analyze_symbol(
            strategy_id, "AAPL", market_data["AAPL"]
        )
        
        assert analysis["symbol"] == "AAPL"
        assert analysis["strategy_id"] == strategy_id
        assert "signal" in analysis
        assert "rule_results" in analysis
        assert analysis["signal"]["action"] == "buy"  # RSI < 35
    
    @pytest.mark.asyncio
    async def test_analyze_portfolio(self, strategy_engine, complete_strategy, portfolio_context):
        """Test analyse de portefeuille."""
        strategy_id = await strategy_engine.load_strategy(complete_strategy)
        
        market_data = {
            "AAPL": {"price": 150.25, "rsi": 70.0},  # Vendre
            "GOOGL": {"price": 2750.80, "rsi": 30.0},  # Acheter
            "MSFT": {"price": 340.50, "rsi": 45.0}  # Hold
        }
        
        portfolio_analysis = await strategy_engine.analyze_portfolio(
            strategy_id, portfolio_context, market_data
        )
        
        assert "strategy_id" in portfolio_analysis
        assert "timestamp" in portfolio_analysis
        assert "symbol_analyses" in portfolio_analysis
        assert "portfolio_recommendations" in portfolio_analysis
        
        # Vérifier analyses par symbole
        symbol_analyses = portfolio_analysis["symbol_analyses"]
        assert len(symbol_analyses) == len(market_data)
        
        aapl_analysis = next(a for a in symbol_analyses if a["symbol"] == "AAPL")
        assert aapl_analysis["signal"]["action"] == "sell"
        
        googl_analysis = next(a for a in symbol_analyses if a["symbol"] == "GOOGL")
        assert googl_analysis["signal"]["action"] == "buy"
    
    @pytest.mark.asyncio
    async def test_generate_decisions(self, strategy_engine, complete_strategy, portfolio_context):
        """Test génération de décisions."""
        strategy_id = await strategy_engine.load_strategy(complete_strategy)
        
        signals = [
            {
                "symbol": "AAPL",
                "action": "sell",
                "strength": 0.8,
                "confidence": 0.9,
                "current_price": 150.25
            },
            {
                "symbol": "TSLA",
                "action": "buy",
                "strength": 0.7,
                "confidence": 0.8,
                "current_price": 200.00
            }
        ]
        
        decisions = await strategy_engine.generate_decisions(
            strategy_id, signals, portfolio_context
        )
        
        assert len(decisions) <= len(signals)  # Peut filtrer certains signaux
        
        for decision in decisions:
            assert "decision_id" in decision
            assert "symbol" in decision
            assert "decision_type" in decision
            assert "quantity" in decision
            assert "confidence" in decision
            assert decision["strategy_id"] == strategy_id
    
    @pytest.mark.asyncio
    async def test_position_sizing(self, strategy_engine, complete_strategy, portfolio_context):
        """Test dimensionnement des positions."""
        strategy_id = await strategy_engine.load_strategy(complete_strategy)
        
        buy_signal = {
            "symbol": "MSFT",
            "action": "buy",
            "strength": 0.8,
            "confidence": 0.9,
            "current_price": 340.50
        }
        
        position_size = await strategy_engine.calculate_position_size(
            strategy_id, buy_signal, portfolio_context
        )
        
        # Vérifier que la taille respecte les limites
        max_position_value = portfolio_context["total_value"] * 0.20  # 20% max
        calculated_value = position_size["quantity"] * buy_signal["current_price"]
        
        assert calculated_value <= max_position_value
        assert position_size["quantity"] > 0
        assert "reasoning" in position_size
    
    @pytest.mark.asyncio
    async def test_risk_management_integration(self, strategy_engine, complete_strategy):
        """Test intégration de la gestion des risques."""
        strategy_id = await strategy_engine.load_strategy(complete_strategy)
        
        high_risk_signal = {
            "symbol": "VOLATILE_STOCK",
            "action": "buy",
            "strength": 0.9,
            "confidence": 0.7,
            "current_price": 50.00,
            "volatility": 0.8  # Très volatile
        }
        
        portfolio_high_concentration = {
            "total_value": 100000,
            "positions": [
                {"symbol": "TECH1", "value": 25000, "sector": "Technology"},
                {"symbol": "TECH2", "value": 20000, "sector": "Technology"},
                {"symbol": "TECH3", "value": 15000, "sector": "Technology"}
            ]
        }
        
        risk_assessment = await strategy_engine.assess_risk(
            strategy_id, high_risk_signal, portfolio_high_concentration
        )
        
        assert "risk_score" in risk_assessment
        assert "risk_factors" in risk_assessment
        assert "recommendations" in risk_assessment
        assert 0 <= risk_assessment["risk_score"] <= 1
    
    @pytest.mark.asyncio
    async def test_strategy_performance_tracking(self, strategy_engine, complete_strategy):
        """Test suivi de performance des stratégies."""
        strategy_id = await strategy_engine.load_strategy(complete_strategy)
        
        # Simuler quelques décisions historiques
        historical_decisions = [
            {
                "symbol": "AAPL",
                "decision_type": "buy",
                "timestamp": datetime.now() - timedelta(days=5),
                "price": 145.00,
                "outcome": "profitable"
            },
            {
                "symbol": "GOOGL",
                "decision_type": "sell",
                "timestamp": datetime.now() - timedelta(days=3),
                "price": 2700.00,
                "outcome": "loss"
            }
        ]
        
        await strategy_engine.update_performance_metrics(strategy_id, historical_decisions)
        
        performance = await strategy_engine.get_strategy_performance(strategy_id)
        
        assert "total_decisions" in performance
        assert "win_rate" in performance
        assert "average_return" in performance
        assert "sharpe_ratio" in performance
        assert performance["total_decisions"] == len(historical_decisions)


class TestStrategyBacktesting:
    """Tests pour le backtesting de stratégies."""
    
    @pytest.fixture
    def strategy_engine(self):
        """Moteur de stratégies pour backtesting."""
        return StrategyEngine()
    
    @pytest.fixture
    def historical_data(self):
        """Données historiques pour backtesting."""
        dates = [datetime.now() - timedelta(days=i) for i in range(30, 0, -1)]
        
        return {
            "AAPL": [
                {
                    "date": date,
                    "price": 150 + (i % 10 - 5),
                    "rsi": 30 + (i % 40),
                    "volume": 2000000 + (i % 1000000)
                }
                for i, date in enumerate(dates)
            ]
        }
    
    @pytest.mark.asyncio
    async def test_backtest_strategy(self, strategy_engine, complete_strategy, historical_data):
        """Test backtesting d'une stratégie."""
        strategy_id = await strategy_engine.load_strategy(complete_strategy)
        
        backtest_config = {
            "start_date": datetime.now() - timedelta(days=30),
            "end_date": datetime.now(),
            "initial_capital": 100000,
            "commission": 0.001,
            "slippage": 0.0005
        }
        
        backtest_results = await strategy_engine.backtest_strategy(
            strategy_id, historical_data, backtest_config
        )
        
        assert "strategy_id" in backtest_results
        assert "period" in backtest_results
        assert "performance_metrics" in backtest_results
        assert "trades" in backtest_results
        assert "equity_curve" in backtest_results
        
        # Vérifier métriques de performance
        metrics = backtest_results["performance_metrics"]
        assert "total_return" in metrics
        assert "sharpe_ratio" in metrics
        assert "max_drawdown" in metrics
        assert "win_rate" in metrics
    
    @pytest.mark.asyncio
    async def test_compare_strategies(self, strategy_engine, complete_strategy):
        """Test comparaison de stratégies."""
        strategy_id_1 = await strategy_engine.load_strategy(complete_strategy)
        
        # Créer une stratégie variant
        conservative_strategy = complete_strategy.copy()
        conservative_strategy["metadata"]["name"] = "Conservative Strategy"
        conservative_strategy["rules"][0]["conditions"][0]["value"] = 25  # RSI plus conservateur
        
        strategy_id_2 = await strategy_engine.load_strategy(conservative_strategy)
        
        comparison = await strategy_engine.compare_strategies(
            [strategy_id_1, strategy_id_2],
            period_days=30
        )
        
        assert "strategies" in comparison
        assert "comparison_metrics" in comparison
        assert len(comparison["strategies"]) == 2
        
        # Vérifier métriques de comparaison
        comp_metrics = comparison["comparison_metrics"]
        assert "returns_correlation" in comp_metrics
        assert "risk_adjusted_performance" in comp_metrics


# Fixtures globales pour tests de stratégies
@pytest.fixture
def strategy_test_data():
    """Données de test pour stratégies."""
    return {
        "symbols": ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN"],
        "timeframes": ["1m", "5m", "15m", "1h", "1d", "1w"],
        "indicators": ["rsi", "macd", "sma", "ema", "bollinger", "volume"],
        "actions": ["buy", "sell", "hold", "reduce", "increase"]
    }


@pytest.fixture
def strategy_performance_benchmarks():
    """Benchmarks de performance pour stratégies."""
    return {
        "minimum_sharpe": 0.5,
        "maximum_drawdown": 0.15,
        "minimum_win_rate": 0.45,
        "minimum_profit_factor": 1.2
    }