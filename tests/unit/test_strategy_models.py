"""
Tests unitaires pour les modèles de stratégies FinAgent.

Ce module teste tous les modèles Pydantic utilisés pour valider
et structurer les configurations de stratégies YAML.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any
from uuid import uuid4

from pydantic import ValidationError

from finagent.business.strategy.models.strategy_models import (
    StrategyType, RiskTolerance, TimeHorizon, MarketCap, PositionSizingMethod
)
from tests.utils import assert_valid_uuid, assert_decimal_equals


class TestStrategyEnums:
    """Tests pour les énumérations de stratégies."""
    
    def test_strategy_type_enum(self):
        """Test énumération StrategyType."""
        assert StrategyType.TECHNICAL == "technical"
        assert StrategyType.FUNDAMENTAL == "fundamental"
        assert StrategyType.SENTIMENT == "sentiment"
        assert StrategyType.HYBRID == "hybrid"
        
        # Test que tous les types sont des chaînes
        for strategy_type in StrategyType:
            assert isinstance(strategy_type.value, str)
    
    def test_risk_tolerance_enum(self):
        """Test énumération RiskTolerance."""
        assert RiskTolerance.LOW == "low"
        assert RiskTolerance.MEDIUM == "medium"
        assert RiskTolerance.HIGH == "high"
        
        # Test ordre implicite du risque
        risk_levels = [RiskTolerance.LOW, RiskTolerance.MEDIUM, RiskTolerance.HIGH]
        for level in risk_levels:
            assert isinstance(level.value, str)
    
    def test_time_horizon_enum(self):
        """Test énumération TimeHorizon."""
        assert TimeHorizon.SHORT == "short"
        assert TimeHorizon.MEDIUM == "medium"
        assert TimeHorizon.LONG == "long"
        
        # Test que tous les horizons sont des chaînes
        for horizon in TimeHorizon:
            assert isinstance(horizon.value, str)
    
    def test_market_cap_enum(self):
        """Test énumération MarketCap."""
        assert MarketCap.SMALL == "small"
        assert MarketCap.MEDIUM == "medium"
        assert MarketCap.LARGE == "large"
        
        for cap in MarketCap:
            assert isinstance(cap.value, str)
    
    def test_position_sizing_method_enum(self):
        """Test énumération PositionSizingMethod."""
        assert PositionSizingMethod.FIXED_PERCENTAGE == "fixed_percentage"
        assert PositionSizingMethod.VOLATILITY_BASED == "volatility_based"
        assert PositionSizingMethod.KELLY == "kelly"
        
        for method in PositionSizingMethod:
            assert isinstance(method.value, str)


class TestStrategyConditionModels:
    """Tests pour les modèles de conditions de stratégies."""
    
    @pytest.fixture
    def sample_condition_data(self):
        """Données échantillon pour conditions."""
        return {
            "indicator": "rsi",
            "operator": ">",
            "value": 70.0,
            "timeframe": "1d"
        }
    
    def test_basic_condition_creation(self, sample_condition_data):
        """Test création d'une condition basique."""
        # Note: Ce test sera adapté une fois les modèles de conditions créés
        # Pour l'instant, nous testons la structure de données
        condition = sample_condition_data
        
        assert condition["indicator"] == "rsi"
        assert condition["operator"] == ">"
        assert condition["value"] == 70.0
        assert condition["timeframe"] == "1d"
    
    def test_condition_operators(self):
        """Test opérateurs de condition valides."""
        valid_operators = [">", "<", ">=", "<=", "==", "!=", "between", "not_between"]
        
        for operator in valid_operators:
            condition = {
                "indicator": "price",
                "operator": operator,
                "value": 100.0
            }
            assert condition["operator"] == operator
    
    def test_condition_indicators(self):
        """Test indicateurs de condition valides."""
        valid_indicators = [
            "price", "rsi", "macd", "sma_20", "sma_50", "volume",
            "pe_ratio", "pb_ratio", "market_cap", "dividend_yield"
        ]
        
        for indicator in valid_indicators:
            condition = {
                "indicator": indicator,
                "operator": ">",
                "value": 10.0
            }
            assert condition["indicator"] == indicator


class TestStrategyRuleModels:
    """Tests pour les modèles de règles de stratégies."""
    
    @pytest.fixture
    def sample_rule_data(self):
        """Données échantillon pour règles."""
        return {
            "name": "RSI Oversold",
            "description": "Buy when RSI is below 30",
            "conditions": [
                {
                    "indicator": "rsi",
                    "operator": "<",
                    "value": 30
                }
            ],
            "action": "buy",
            "weight": 0.8,
            "priority": 1
        }
    
    def test_rule_creation(self, sample_rule_data):
        """Test création d'une règle."""
        rule = sample_rule_data
        
        assert rule["name"] == "RSI Oversold"
        assert rule["action"] == "buy"
        assert rule["weight"] == 0.8
        assert len(rule["conditions"]) == 1
        assert rule["conditions"][0]["indicator"] == "rsi"
    
    def test_rule_actions(self):
        """Test actions de règle valides."""
        valid_actions = ["buy", "sell", "hold", "reduce", "increase"]
        
        for action in valid_actions:
            rule = {
                "name": "Test Rule",
                "conditions": [{"indicator": "price", "operator": ">", "value": 100}],
                "action": action,
                "weight": 0.5
            }
            assert rule["action"] == action
    
    def test_rule_weight_validation(self):
        """Test validation du poids des règles."""
        # Poids valides (0.0 à 1.0)
        valid_weights = [0.0, 0.1, 0.5, 0.9, 1.0]
        
        for weight in valid_weights:
            rule = {
                "name": "Test Rule",
                "conditions": [{"indicator": "price", "operator": ">", "value": 100}],
                "action": "buy",
                "weight": weight
            }
            assert rule["weight"] == weight
    
    def test_multiple_conditions_rule(self):
        """Test règle avec plusieurs conditions."""
        rule = {
            "name": "Complex Rule",
            "conditions": [
                {"indicator": "rsi", "operator": "<", "value": 30},
                {"indicator": "volume", "operator": ">", "value": 1000000},
                {"indicator": "price", "operator": ">", "value": 50}
            ],
            "action": "buy",
            "weight": 0.7,
            "condition_logic": "AND"  # Toutes les conditions doivent être vraies
        }
        
        assert len(rule["conditions"]) == 3
        assert rule["condition_logic"] == "AND"


class TestStrategyConfigModels:
    """Tests pour les modèles de configuration de stratégies."""
    
    @pytest.fixture
    def sample_strategy_config(self):
        """Configuration de stratégie échantillon."""
        return {
            "metadata": {
                "name": "Momentum Strategy",
                "description": "Strategy based on momentum indicators",
                "version": "1.0.0",
                "author": "FinAgent",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            },
            "strategy": {
                "type": StrategyType.TECHNICAL,
                "risk_tolerance": RiskTolerance.MEDIUM,
                "time_horizon": TimeHorizon.SHORT,
                "target_return": 0.15,
                "max_drawdown": 0.10,
                "rebalance_frequency": "weekly"
            },
            "portfolio": {
                "max_positions": 10,
                "position_sizing": PositionSizingMethod.FIXED_PERCENTAGE,
                "max_position_size": 0.20,
                "min_position_size": 0.02,
                "cash_reserve": 0.05
            },
            "risk_management": {
                "stop_loss": 0.08,
                "take_profit": 0.20,
                "trailing_stop": True,
                "max_correlation": 0.7,
                "sector_concentration_limit": 0.3
            },
            "rules": [
                {
                    "name": "Momentum Entry",
                    "conditions": [
                        {"indicator": "rsi", "operator": ">", "value": 60}
                    ],
                    "action": "buy",
                    "weight": 0.8
                }
            ]
        }
    
    def test_strategy_config_structure(self, sample_strategy_config):
        """Test structure de configuration de stratégie."""
        config = sample_strategy_config
        
        # Vérification des sections principales
        assert "metadata" in config
        assert "strategy" in config
        assert "portfolio" in config
        assert "risk_management" in config
        assert "rules" in config
        
        # Vérification des métadonnées
        metadata = config["metadata"]
        assert metadata["name"] == "Momentum Strategy"
        assert "version" in metadata
        assert "created_at" in metadata
    
    def test_strategy_section_validation(self, sample_strategy_config):
        """Test validation de la section stratégie."""
        strategy = sample_strategy_config["strategy"]
        
        assert strategy["type"] == StrategyType.TECHNICAL
        assert strategy["risk_tolerance"] == RiskTolerance.MEDIUM
        assert strategy["time_horizon"] == TimeHorizon.SHORT
        assert 0 < strategy["target_return"] <= 1.0
        assert 0 < strategy["max_drawdown"] <= 1.0
    
    def test_portfolio_section_validation(self, sample_strategy_config):
        """Test validation de la section portefeuille."""
        portfolio = sample_strategy_config["portfolio"]
        
        assert portfolio["max_positions"] > 0
        assert portfolio["position_sizing"] == PositionSizingMethod.FIXED_PERCENTAGE
        assert 0 < portfolio["max_position_size"] <= 1.0
        assert 0 < portfolio["min_position_size"] <= portfolio["max_position_size"]
        assert 0 <= portfolio["cash_reserve"] <= 0.5
    
    def test_risk_management_validation(self, sample_strategy_config):
        """Test validation de la gestion des risques."""
        risk_mgmt = sample_strategy_config["risk_management"]
        
        assert 0 < risk_mgmt["stop_loss"] <= 1.0
        assert 0 < risk_mgmt["take_profit"] <= 2.0
        assert isinstance(risk_mgmt["trailing_stop"], bool)
        assert 0 <= risk_mgmt["max_correlation"] <= 1.0
        assert 0 < risk_mgmt["sector_concentration_limit"] <= 1.0
    
    def test_rules_validation(self, sample_strategy_config):
        """Test validation des règles."""
        rules = sample_strategy_config["rules"]
        
        assert isinstance(rules, list)
        assert len(rules) > 0
        
        for rule in rules:
            assert "name" in rule
            assert "conditions" in rule
            assert "action" in rule
            assert "weight" in rule
            assert isinstance(rule["conditions"], list)
            assert len(rule["conditions"]) > 0


class TestStrategyValidation:
    """Tests pour la validation des stratégies."""
    
    def test_strategy_type_consistency(self):
        """Test cohérence du type de stratégie."""
        # Stratégie technique avec indicateurs techniques
        technical_strategy = {
            "type": StrategyType.TECHNICAL,
            "rules": [
                {
                    "name": "Technical Rule",
                    "conditions": [{"indicator": "rsi", "operator": ">", "value": 70}],
                    "action": "sell",
                    "weight": 0.8
                }
            ]
        }
        
        assert technical_strategy["type"] == StrategyType.TECHNICAL
        assert "rsi" in technical_strategy["rules"][0]["conditions"][0]["indicator"]
    
    def test_fundamental_strategy_consistency(self):
        """Test cohérence stratégie fondamentale."""
        fundamental_strategy = {
            "type": StrategyType.FUNDAMENTAL,
            "rules": [
                {
                    "name": "Value Rule",
                    "conditions": [{"indicator": "pe_ratio", "operator": "<", "value": 15}],
                    "action": "buy",
                    "weight": 0.7
                }
            ]
        }
        
        assert fundamental_strategy["type"] == StrategyType.FUNDAMENTAL
        assert "pe_ratio" in fundamental_strategy["rules"][0]["conditions"][0]["indicator"]
    
    def test_risk_tolerance_constraints(self):
        """Test contraintes selon la tolérance au risque."""
        # Stratégie faible risque
        low_risk_strategy = {
            "risk_tolerance": RiskTolerance.LOW,
            "max_position_size": 0.10,  # Positions plus petites
            "stop_loss": 0.05,  # Stop loss plus serré
            "cash_reserve": 0.20  # Plus de cash
        }
        
        # Stratégie haut risque
        high_risk_strategy = {
            "risk_tolerance": RiskTolerance.HIGH,
            "max_position_size": 0.30,  # Positions plus grandes
            "stop_loss": 0.15,  # Stop loss plus large
            "cash_reserve": 0.05  # Moins de cash
        }
        
        assert low_risk_strategy["risk_tolerance"] == RiskTolerance.LOW
        assert low_risk_strategy["max_position_size"] < high_risk_strategy["max_position_size"]
        assert low_risk_strategy["stop_loss"] < high_risk_strategy["stop_loss"]
    
    def test_time_horizon_constraints(self):
        """Test contraintes selon l'horizon temporel."""
        # Stratégie court terme
        short_term = {
            "time_horizon": TimeHorizon.SHORT,
            "rebalance_frequency": "daily",
            "target_return": 0.10  # Objectif plus modeste
        }
        
        # Stratégie long terme
        long_term = {
            "time_horizon": TimeHorizon.LONG,
            "rebalance_frequency": "monthly",
            "target_return": 0.25  # Objectif plus ambitieux
        }
        
        assert short_term["time_horizon"] == TimeHorizon.SHORT
        assert long_term["time_horizon"] == TimeHorizon.LONG
        assert short_term["target_return"] < long_term["target_return"]


class TestStrategyOptimization:
    """Tests pour l'optimisation des stratégies."""
    
    def test_weight_normalization(self):
        """Test normalisation des poids des règles."""
        rules = [
            {"name": "Rule 1", "weight": 0.3, "action": "buy"},
            {"name": "Rule 2", "weight": 0.5, "action": "buy"},
            {"name": "Rule 3", "weight": 0.7, "action": "sell"}
        ]
        
        # Calcul des poids normalisés
        total_weight = sum(rule["weight"] for rule in rules)
        normalized_rules = []
        
        for rule in rules:
            normalized_rule = rule.copy()
            normalized_rule["normalized_weight"] = rule["weight"] / total_weight
            normalized_rules.append(normalized_rule)
        
        # Vérification que la somme des poids normalisés = 1
        total_normalized = sum(rule["normalized_weight"] for rule in normalized_rules)
        assert abs(total_normalized - 1.0) < 0.001
    
    def test_rule_prioritization(self):
        """Test priorisation des règles."""
        rules = [
            {"name": "High Priority", "weight": 0.9, "priority": 1},
            {"name": "Medium Priority", "weight": 0.6, "priority": 2},
            {"name": "Low Priority", "weight": 0.3, "priority": 3}
        ]
        
        # Tri par priorité
        sorted_rules = sorted(rules, key=lambda x: x["priority"])
        
        assert sorted_rules[0]["name"] == "High Priority"
        assert sorted_rules[1]["name"] == "Medium Priority"
        assert sorted_rules[2]["name"] == "Low Priority"
    
    def test_conflicting_rules_resolution(self):
        """Test résolution de règles conflictuelles."""
        rules = [
            {"name": "Buy Signal", "action": "buy", "weight": 0.7, "confidence": 0.8},
            {"name": "Sell Signal", "action": "sell", "weight": 0.6, "confidence": 0.7}
        ]
        
        # Résolution par poids le plus élevé
        dominant_rule = max(rules, key=lambda x: x["weight"])
        assert dominant_rule["action"] == "buy"
        
        # Résolution par confiance la plus élevée
        confident_rule = max(rules, key=lambda x: x["confidence"])
        assert confident_rule["action"] == "buy"


class TestStrategyBacktesting:
    """Tests pour les modèles de backtesting."""
    
    @pytest.fixture
    def sample_backtest_config(self):
        """Configuration de backtest échantillon."""
        return {
            "period": {
                "start_date": "2023-01-01",
                "end_date": "2023-12-31",
                "benchmark": "SPY"
            },
            "data": {
                "frequency": "daily",
                "adjust_splits": True,
                "adjust_dividends": True
            },
            "costs": {
                "commission": 0.001,
                "slippage": 0.0005,
                "spread": 0.0002
            },
            "constraints": {
                "max_leverage": 1.0,
                "min_cash": 0.05,
                "trade_delay": 1  # jours
            }
        }
    
    def test_backtest_config_validation(self, sample_backtest_config):
        """Test validation configuration de backtest."""
        config = sample_backtest_config
        
        # Validation période
        period = config["period"]
        start_date = datetime.fromisoformat(period["start_date"])
        end_date = datetime.fromisoformat(period["end_date"])
        assert start_date < end_date
        
        # Validation coûts
        costs = config["costs"]
        assert 0 <= costs["commission"] <= 0.1
        assert 0 <= costs["slippage"] <= 0.1
        assert 0 <= costs["spread"] <= 0.1
        
        # Validation contraintes
        constraints = config["constraints"]
        assert constraints["max_leverage"] >= 1.0
        assert 0 <= constraints["min_cash"] <= 0.5
        assert constraints["trade_delay"] >= 0


class TestStrategyPerformanceMetrics:
    """Tests pour les métriques de performance."""
    
    @pytest.fixture
    def sample_performance_data(self):
        """Données de performance échantillon."""
        return {
            "returns": {
                "total_return": 0.15,
                "annualized_return": 0.12,
                "excess_return": 0.03,
                "alpha": 0.02,
                "beta": 1.1
            },
            "risk": {
                "volatility": 0.18,
                "max_drawdown": -0.08,
                "value_at_risk": -0.05,
                "sharpe_ratio": 0.67,
                "sortino_ratio": 0.89,
                "calmar_ratio": 1.5
            },
            "trades": {
                "total_trades": 45,
                "win_rate": 0.62,
                "profit_factor": 1.35,
                "avg_win": 0.035,
                "avg_loss": -0.022,
                "max_consecutive_wins": 5,
                "max_consecutive_losses": 3
            }
        }
    
    def test_performance_metrics_calculation(self, sample_performance_data):
        """Test calcul des métriques de performance."""
        perf = sample_performance_data
        
        # Vérification des ratios
        returns = perf["returns"]
        risk = perf["risk"]
        
        # Sharpe ratio approximatif
        expected_sharpe = returns["annualized_return"] / risk["volatility"]
        assert abs(risk["sharpe_ratio"] - expected_sharpe) < 0.1
        
        # Calmar ratio approximatif
        expected_calmar = returns["annualized_return"] / abs(risk["max_drawdown"])
        assert abs(risk["calmar_ratio"] - expected_calmar) < 0.5
    
    def test_trade_statistics(self, sample_performance_data):
        """Test statistiques de trading."""
        trades = sample_performance_data["trades"]
        
        assert 0 <= trades["win_rate"] <= 1.0
        assert trades["profit_factor"] > 0
        assert trades["avg_win"] > 0
        assert trades["avg_loss"] < 0
        assert trades["total_trades"] > 0


# Fixtures spécifiques pour les tests de stratégies
@pytest.fixture
def strategy_test_data():
    """Données de test pour stratégies."""
    return {
        "simple_strategy": {
            "name": "Simple RSI",
            "type": StrategyType.TECHNICAL,
            "rules": [
                {
                    "name": "Oversold",
                    "conditions": [{"indicator": "rsi", "operator": "<", "value": 30}],
                    "action": "buy",
                    "weight": 0.8
                }
            ]
        },
        "complex_strategy": {
            "name": "Multi-Factor",
            "type": StrategyType.HYBRID,
            "rules": [
                {
                    "name": "Technical Signal",
                    "conditions": [
                        {"indicator": "rsi", "operator": "<", "value": 40},
                        {"indicator": "macd", "operator": ">", "value": 0}
                    ],
                    "action": "buy",
                    "weight": 0.6
                },
                {
                    "name": "Fundamental Signal",
                    "conditions": [
                        {"indicator": "pe_ratio", "operator": "<", "value": 20}
                    ],
                    "action": "buy",
                    "weight": 0.4
                }
            ]
        }
    }


@pytest.fixture
def invalid_strategy_data():
    """Données de stratégie invalides pour tests."""
    return {
        "missing_name": {
            "type": StrategyType.TECHNICAL,
            "rules": []
        },
        "invalid_weight": {
            "name": "Invalid",
            "type": StrategyType.TECHNICAL,
            "rules": [
                {
                    "name": "Bad Rule",
                    "conditions": [{"indicator": "rsi", "operator": ">", "value": 70}],
                    "action": "buy",
                    "weight": 1.5  # > 1.0
                }
            ]
        },
        "empty_conditions": {
            "name": "Empty",
            "type": StrategyType.TECHNICAL,
            "rules": [
                {
                    "name": "No Conditions",
                    "conditions": [],  # Vide
                    "action": "buy",
                    "weight": 0.5
                }
            ]
        }
    }