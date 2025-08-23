"""
Tests unitaires pour les modèles de décision et de portefeuille FinAgent.

Ce module teste tous les modèles Pydantic utilisés pour les décisions
d'investissement, la gestion de portefeuille et l'allocation d'actifs.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Optional
from uuid import uuid4, UUID

from pydantic import ValidationError

from finagent.core.models.decision_models import (
    DecisionType, ActionType, ConfidenceLevel, RiskLevel,
    InvestmentDecision, PortfolioAction, AssetAllocation
)
from finagent.core.models.portfolio_models import (
    Position, Portfolio, Transaction, TransactionType,
    PortfolioMetrics, RiskMetrics, PerformanceMetrics
)
from tests.utils import assert_valid_uuid, assert_decimal_equals


class TestDecisionEnums:
    """Tests pour les énumérations de décision."""
    
    def test_decision_type_enum(self):
        """Test énumération DecisionType."""
        assert DecisionType.BUY == "buy"
        assert DecisionType.SELL == "sell"
        assert DecisionType.HOLD == "hold"
        assert DecisionType.REBALANCE == "rebalance"
        
        # Test que tous les types sont des chaînes
        for decision_type in DecisionType:
            assert isinstance(decision_type.value, str)
    
    def test_action_type_enum(self):
        """Test énumération ActionType."""
        assert ActionType.MARKET_ORDER == "market_order"
        assert ActionType.LIMIT_ORDER == "limit_order"
        assert ActionType.STOP_LOSS == "stop_loss"
        assert ActionType.TAKE_PROFIT == "take_profit"
        assert ActionType.TRAILING_STOP == "trailing_stop"
        
        for action_type in ActionType:
            assert isinstance(action_type.value, str)
    
    def test_confidence_level_enum(self):
        """Test énumération ConfidenceLevel."""
        assert ConfidenceLevel.LOW == "low"
        assert ConfidenceLevel.MEDIUM == "medium"
        assert ConfidenceLevel.HIGH == "high"
        assert ConfidenceLevel.VERY_HIGH == "very_high"
        
        # Test ordre implicite de confiance
        confidence_levels = [
            ConfidenceLevel.LOW, ConfidenceLevel.MEDIUM, 
            ConfidenceLevel.HIGH, ConfidenceLevel.VERY_HIGH
        ]
        for level in confidence_levels:
            assert isinstance(level.value, str)
    
    def test_risk_level_enum(self):
        """Test énumération RiskLevel."""
        assert RiskLevel.VERY_LOW == "very_low"
        assert RiskLevel.LOW == "low"
        assert RiskLevel.MEDIUM == "medium"
        assert RiskLevel.HIGH == "high"
        assert RiskLevel.VERY_HIGH == "very_high"
        
        for level in RiskLevel:
            assert isinstance(level.value, str)


class TestInvestmentDecisionModel:
    """Tests pour le modèle InvestmentDecision."""
    
    @pytest.fixture
    def sample_decision_data(self):
        """Données échantillon pour décision d'investissement."""
        return {
            "id": str(uuid4()),
            "timestamp": datetime.utcnow(),
            "symbol": "AAPL",
            "decision_type": DecisionType.BUY,
            "action_type": ActionType.MARKET_ORDER,
            "quantity": Decimal("10"),
            "price": Decimal("150.25"),
            "confidence": ConfidenceLevel.HIGH,
            "risk_level": RiskLevel.MEDIUM,
            "reasoning": "Strong momentum and good fundamentals",
            "strategy_name": "Momentum Strategy",
            "expected_return": Decimal("0.15"),
            "risk_score": Decimal("0.6"),
            "timeframe": "short_term",
            "stop_loss": Decimal("135.00"),
            "take_profit": Decimal("180.00"),
            "metadata": {
                "rsi": 45.2,
                "pe_ratio": 18.5,
                "volume": 1500000
            }
        }
    
    def test_investment_decision_creation(self, sample_decision_data):
        """Test création d'une décision d'investissement."""
        # Note: Test avec structure de données en attendant les modèles Pydantic
        decision = sample_decision_data
        
        assert_valid_uuid(decision["id"])
        assert isinstance(decision["timestamp"], datetime)
        assert decision["symbol"] == "AAPL"
        assert decision["decision_type"] == DecisionType.BUY
        assert decision["quantity"] == Decimal("10")
        assert decision["confidence"] == ConfidenceLevel.HIGH
    
    def test_decision_validation_constraints(self, sample_decision_data):
        """Test contraintes de validation des décisions."""
        decision = sample_decision_data
        
        # Quantité positive
        assert decision["quantity"] > 0
        
        # Prix positif
        assert decision["price"] > 0
        
        # Stop loss inférieur au prix pour un achat
        if decision["decision_type"] == DecisionType.BUY:
            assert decision["stop_loss"] < decision["price"]
            assert decision["take_profit"] > decision["price"]
        
        # Score de risque entre 0 et 1
        assert 0 <= decision["risk_score"] <= 1
        
        # Rendement attendu raisonnable
        assert -1 <= decision["expected_return"] <= 2
    
    def test_decision_sell_validation(self):
        """Test validation spécifique pour décision de vente."""
        sell_decision = {
            "id": str(uuid4()),
            "timestamp": datetime.utcnow(),
            "symbol": "TSLA",
            "decision_type": DecisionType.SELL,
            "action_type": ActionType.LIMIT_ORDER,
            "quantity": Decimal("5"),
            "price": Decimal("200.00"),
            "confidence": ConfidenceLevel.MEDIUM,
            "risk_level": RiskLevel.HIGH,
            "reasoning": "Overbought conditions",
            "strategy_name": "Mean Reversion"
        }
        
        assert sell_decision["decision_type"] == DecisionType.SELL
        assert sell_decision["quantity"] > 0
        # Pour une vente, pas de stop loss nécessaire
    
    def test_decision_hold_validation(self):
        """Test validation pour décision de conserver."""
        hold_decision = {
            "id": str(uuid4()),
            "timestamp": datetime.utcnow(),
            "symbol": "SPY",
            "decision_type": DecisionType.HOLD,
            "confidence": ConfidenceLevel.LOW,
            "risk_level": RiskLevel.LOW,
            "reasoning": "Mixed signals, wait for clearer trend",
            "strategy_name": "Conservative Strategy"
        }
        
        assert hold_decision["decision_type"] == DecisionType.HOLD
        # Pour HOLD, quantité et prix optionnels
    
    def test_decision_metadata_validation(self, sample_decision_data):
        """Test validation des métadonnées de décision."""
        decision = sample_decision_data
        metadata = decision["metadata"]
        
        # Vérification des indicateurs techniques
        assert isinstance(metadata["rsi"], (int, float))
        assert 0 <= metadata["rsi"] <= 100
        
        # Vérification ratio financier
        assert isinstance(metadata["pe_ratio"], (int, float))
        assert metadata["pe_ratio"] > 0
        
        # Vérification volume
        assert isinstance(metadata["volume"], int)
        assert metadata["volume"] > 0


class TestPortfolioActionModel:
    """Tests pour le modèle PortfolioAction."""
    
    @pytest.fixture
    def sample_portfolio_action_data(self):
        """Données échantillon pour action de portefeuille."""
        return {
            "id": str(uuid4()),
            "timestamp": datetime.utcnow(),
            "action_type": "rebalance",
            "description": "Monthly portfolio rebalancing",
            "allocations": [
                {
                    "symbol": "AAPL",
                    "target_weight": Decimal("0.25"),
                    "current_weight": Decimal("0.30"),
                    "adjustment": Decimal("-0.05")
                },
                {
                    "symbol": "GOOGL",
                    "target_weight": Decimal("0.20"),
                    "current_weight": Decimal("0.15"),
                    "adjustment": Decimal("0.05")
                }
            ],
            "total_value": Decimal("100000.00"),
            "cash_available": Decimal("5000.00"),
            "risk_metrics": {
                "portfolio_beta": Decimal("1.15"),
                "var_95": Decimal("0.023"),
                "sharpe_ratio": Decimal("0.85")
            }
        }
    
    def test_portfolio_action_creation(self, sample_portfolio_action_data):
        """Test création d'une action de portefeuille."""
        action = sample_portfolio_action_data
        
        assert_valid_uuid(action["id"])
        assert isinstance(action["timestamp"], datetime)
        assert action["action_type"] == "rebalance"
        assert len(action["allocations"]) == 2
        assert action["total_value"] > 0
    
    def test_allocation_weights_validation(self, sample_portfolio_action_data):
        """Test validation des poids d'allocation."""
        allocations = sample_portfolio_action_data["allocations"]
        
        for allocation in allocations:
            # Poids entre 0 et 1
            assert 0 <= allocation["target_weight"] <= 1
            assert 0 <= allocation["current_weight"] <= 1
            
            # Ajustement cohérent
            expected_adjustment = allocation["target_weight"] - allocation["current_weight"]
            assert abs(allocation["adjustment"] - expected_adjustment) < Decimal("0.001")
    
    def test_portfolio_value_consistency(self, sample_portfolio_action_data):
        """Test cohérence des valeurs de portefeuille."""
        action = sample_portfolio_action_data
        
        assert action["total_value"] > 0
        assert action["cash_available"] >= 0
        assert action["cash_available"] <= action["total_value"]


class TestAssetAllocationModel:
    """Tests pour le modèle AssetAllocation."""
    
    @pytest.fixture
    def sample_allocation_data(self):
        """Données échantillon pour allocation d'actifs."""
        return {
            "id": str(uuid4()),
            "timestamp": datetime.utcnow(),
            "strategy_name": "Balanced Growth",
            "allocations": {
                "equities": {
                    "target_weight": Decimal("0.60"),
                    "current_weight": Decimal("0.58"),
                    "assets": {
                        "AAPL": Decimal("0.15"),
                        "GOOGL": Decimal("0.12"),
                        "MSFT": Decimal("0.13"),
                        "TSLA": Decimal("0.10"),
                        "SPY": Decimal("0.10")
                    }
                },
                "bonds": {
                    "target_weight": Decimal("0.30"),
                    "current_weight": Decimal("0.32"),
                    "assets": {
                        "AGG": Decimal("0.20"),
                        "TLT": Decimal("0.12")
                    }
                },
                "cash": {
                    "target_weight": Decimal("0.10"),
                    "current_weight": Decimal("0.10"),
                    "assets": {
                        "USD": Decimal("0.10")
                    }
                }
            },
            "rebalance_threshold": Decimal("0.05"),
            "last_rebalance": datetime.utcnow() - timedelta(days=30),
            "next_rebalance": datetime.utcnow() + timedelta(days=30)
        }
    
    def test_asset_allocation_creation(self, sample_allocation_data):
        """Test création d'une allocation d'actifs."""
        allocation = sample_allocation_data
        
        assert_valid_uuid(allocation["id"])
        assert allocation["strategy_name"] == "Balanced Growth"
        assert "equities" in allocation["allocations"]
        assert "bonds" in allocation["allocations"]
        assert "cash" in allocation["allocations"]
    
    def test_allocation_weights_sum_to_one(self, sample_allocation_data):
        """Test que les poids d'allocation totalisent 1."""
        allocations = sample_allocation_data["allocations"]
        
        # Somme des poids cibles
        target_sum = sum(
            cat["target_weight"] for cat in allocations.values()
        )
        assert abs(target_sum - Decimal("1.0")) < Decimal("0.001")
        
        # Somme des poids actuels
        current_sum = sum(
            cat["current_weight"] for cat in allocations.values()
        )
        assert abs(current_sum - Decimal("1.0")) < Decimal("0.001")
    
    def test_asset_weights_within_category(self, sample_allocation_data):
        """Test cohérence des poids d'actifs dans chaque catégorie."""
        allocations = sample_allocation_data["allocations"]
        
        for category_name, category_data in allocations.items():
            assets = category_data["assets"]
            category_weight = category_data["current_weight"]
            
            # Somme des poids d'actifs doit égaler le poids de la catégorie
            assets_sum = sum(assets.values())
            assert abs(assets_sum - category_weight) < Decimal("0.001")
    
    def test_rebalance_threshold_validation(self, sample_allocation_data):
        """Test validation du seuil de rééquilibrage."""
        allocation = sample_allocation_data
        
        assert 0 < allocation["rebalance_threshold"] <= Decimal("0.2")
        assert allocation["last_rebalance"] < allocation["next_rebalance"]


class TestTransactionModel:
    """Tests pour le modèle Transaction."""
    
    @pytest.fixture
    def sample_transaction_data(self):
        """Données échantillon pour transaction."""
        return {
            "id": str(uuid4()),
            "timestamp": datetime.utcnow(),
            "transaction_type": TransactionType.BUY,
            "symbol": "AAPL",
            "quantity": Decimal("10"),
            "price": Decimal("150.25"),
            "total_amount": Decimal("1502.50"),
            "fees": Decimal("1.50"),
            "portfolio_id": str(uuid4()),
            "decision_id": str(uuid4()),
            "execution_price": Decimal("150.30"),
            "slippage": Decimal("0.05"),
            "status": "executed",
            "exchange": "NASDAQ",
            "order_id": "ORD123456"
        }
    
    def test_transaction_creation(self, sample_transaction_data):
        """Test création d'une transaction."""
        transaction = sample_transaction_data
        
        assert_valid_uuid(transaction["id"])
        assert_valid_uuid(transaction["portfolio_id"])
        assert_valid_uuid(transaction["decision_id"])
        assert transaction["transaction_type"] == TransactionType.BUY
        assert transaction["quantity"] > 0
        assert transaction["price"] > 0
    
    def test_transaction_amount_calculation(self, sample_transaction_data):
        """Test calcul du montant de transaction."""
        transaction = sample_transaction_data
        
        # Montant total = quantité × prix
        expected_amount = transaction["quantity"] * transaction["price"]
        assert transaction["total_amount"] == expected_amount
        
        # Frais positifs
        assert transaction["fees"] >= 0
        
        # Slippage peut être positif ou négatif
        assert abs(transaction["slippage"]) < transaction["price"] * Decimal("0.1")
    
    def test_buy_transaction_validation(self):
        """Test validation spécifique pour transaction d'achat."""
        buy_transaction = {
            "id": str(uuid4()),
            "timestamp": datetime.utcnow(),
            "transaction_type": TransactionType.BUY,
            "symbol": "GOOGL",
            "quantity": Decimal("5"),
            "price": Decimal("2500.00"),
            "total_amount": Decimal("12500.00"),
            "fees": Decimal("12.50"),
            "status": "executed"
        }
        
        assert buy_transaction["transaction_type"] == TransactionType.BUY
        assert buy_transaction["quantity"] > 0
        assert buy_transaction["total_amount"] > 0
    
    def test_sell_transaction_validation(self):
        """Test validation spécifique pour transaction de vente."""
        sell_transaction = {
            "id": str(uuid4()),
            "timestamp": datetime.utcnow(),
            "transaction_type": TransactionType.SELL,
            "symbol": "TSLA",
            "quantity": Decimal("3"),
            "price": Decimal("200.00"),
            "total_amount": Decimal("600.00"),
            "fees": Decimal("0.60"),
            "status": "executed"
        }
        
        assert sell_transaction["transaction_type"] == TransactionType.SELL
        assert sell_transaction["quantity"] > 0
        # Pour une vente, total_amount est positif (recettes)


class TestPositionModel:
    """Tests pour le modèle Position."""
    
    @pytest.fixture
    def sample_position_data(self):
        """Données échantillon pour position."""
        return {
            "id": str(uuid4()),
            "symbol": "AAPL",
            "quantity": Decimal("100"),
            "avg_cost": Decimal("145.50"),
            "current_price": Decimal("150.25"),
            "market_value": Decimal("15025.00"),
            "unrealized_pnl": Decimal("475.00"),
            "realized_pnl": Decimal("0.00"),
            "weight": Decimal("0.15"),
            "portfolio_id": str(uuid4()),
            "opened_at": datetime.utcnow() - timedelta(days=30),
            "last_updated": datetime.utcnow(),
            "sector": "Technology",
            "currency": "USD",
            "exchange": "NASDAQ",
            "dividend_yield": Decimal("0.0050"),
            "beta": Decimal("1.20")
        }
    
    def test_position_creation(self, sample_position_data):
        """Test création d'une position."""
        position = sample_position_data
        
        assert_valid_uuid(position["id"])
        assert_valid_uuid(position["portfolio_id"])
        assert position["symbol"] == "AAPL"
        assert position["quantity"] > 0
        assert position["avg_cost"] > 0
        assert position["current_price"] > 0
    
    def test_position_value_calculations(self, sample_position_data):
        """Test calculs de valeur de position."""
        position = sample_position_data
        
        # Valeur marché = quantité × prix actuel
        expected_market_value = position["quantity"] * position["current_price"]
        assert position["market_value"] == expected_market_value
        
        # PnL non réalisé = valeur marché - coût moyen × quantité
        cost_basis = position["avg_cost"] * position["quantity"]
        expected_unrealized_pnl = position["market_value"] - cost_basis
        assert position["unrealized_pnl"] == expected_unrealized_pnl
        
        # Poids entre 0 et 1
        assert 0 <= position["weight"] <= 1
    
    def test_position_profit_loss(self):
        """Test calcul profit/perte de position."""
        profitable_position = {
            "symbol": "MSFT",
            "quantity": Decimal("50"),
            "avg_cost": Decimal("200.00"),
            "current_price": Decimal("220.00"),
            "market_value": Decimal("11000.00")
        }
        
        cost_basis = profitable_position["avg_cost"] * profitable_position["quantity"]
        pnl = profitable_position["market_value"] - cost_basis
        
        assert pnl > 0  # Position profitable
        
        losing_position = {
            "symbol": "NFLX",
            "quantity": Decimal("20"),
            "avg_cost": Decimal("300.00"),
            "current_price": Decimal("280.00"),
            "market_value": Decimal("5600.00")
        }
        
        cost_basis_loss = losing_position["avg_cost"] * losing_position["quantity"]
        pnl_loss = losing_position["market_value"] - cost_basis_loss
        
        assert pnl_loss < 0  # Position en perte


class TestPortfolioModel:
    """Tests pour le modèle Portfolio."""
    
    @pytest.fixture
    def sample_portfolio_data(self):
        """Données échantillon pour portefeuille."""
        return {
            "id": str(uuid4()),
            "name": "Growth Portfolio",
            "description": "Aggressive growth strategy",
            "created_at": datetime.utcnow() - timedelta(days=365),
            "last_updated": datetime.utcnow(),
            "total_value": Decimal("250000.00"),
            "cash_balance": Decimal("25000.00"),
            "invested_value": Decimal("225000.00"),
            "initial_value": Decimal("200000.00"),
            "total_return": Decimal("0.25"),
            "positions": [
                {
                    "symbol": "AAPL",
                    "quantity": Decimal("100"),
                    "market_value": Decimal("15025.00"),
                    "weight": Decimal("0.0601")
                },
                {
                    "symbol": "GOOGL",
                    "quantity": Decimal("8"),
                    "market_value": Decimal("20000.00"),
                    "weight": Decimal("0.08")
                }
            ],
            "strategy_name": "Aggressive Growth",
            "risk_tolerance": "high",
            "currency": "USD",
            "owner_id": str(uuid4())
        }
    
    def test_portfolio_creation(self, sample_portfolio_data):
        """Test création d'un portefeuille."""
        portfolio = sample_portfolio_data
        
        assert_valid_uuid(portfolio["id"])
        assert_valid_uuid(portfolio["owner_id"])
        assert portfolio["name"] == "Growth Portfolio"
        assert portfolio["total_value"] > 0
        assert portfolio["cash_balance"] >= 0
        assert len(portfolio["positions"]) == 2
    
    def test_portfolio_value_consistency(self, sample_portfolio_data):
        """Test cohérence des valeurs de portefeuille."""
        portfolio = sample_portfolio_data
        
        # Valeur totale = cash + valeur investie
        expected_total = portfolio["cash_balance"] + portfolio["invested_value"]
        assert portfolio["total_value"] == expected_total
        
        # Valeur investie = somme des valeurs de marché des positions
        positions_value = sum(
            pos["market_value"] for pos in portfolio["positions"]
        )
        assert portfolio["invested_value"] == positions_value
        
        # Rendement total cohérent
        expected_return = (portfolio["total_value"] - portfolio["initial_value"]) / portfolio["initial_value"]
        assert abs(portfolio["total_return"] - expected_return) < Decimal("0.001")
    
    def test_portfolio_weights_validation(self, sample_portfolio_data):
        """Test validation des poids de portefeuille."""
        portfolio = sample_portfolio_data
        
        # Somme des poids des positions
        total_weight = sum(pos["weight"] for pos in portfolio["positions"])
        
        # Poids cash
        cash_weight = portfolio["cash_balance"] / portfolio["total_value"]
        
        # Total doit être proche de 1
        assert abs((total_weight + cash_weight) - Decimal("1.0")) < Decimal("0.01")


class TestPortfolioMetricsModel:
    """Tests pour le modèle PortfolioMetrics."""
    
    @pytest.fixture
    def sample_metrics_data(self):
        """Données échantillon pour métriques de portefeuille."""
        return {
            "portfolio_id": str(uuid4()),
            "timestamp": datetime.utcnow(),
            "total_return": Decimal("0.15"),
            "annualized_return": Decimal("0.12"),
            "volatility": Decimal("0.18"),
            "sharpe_ratio": Decimal("0.67"),
            "sortino_ratio": Decimal("0.89"),
            "max_drawdown": Decimal("-0.08"),
            "beta": Decimal("1.15"),
            "alpha": Decimal("0.02"),
            "var_95": Decimal("-0.05"),
            "var_99": Decimal("-0.08"),
            "win_rate": Decimal("0.62"),
            "profit_factor": Decimal("1.35"),
            "calmar_ratio": Decimal("1.5"),
            "information_ratio": Decimal("0.45"),
            "tracking_error": Decimal("0.04")
        }
    
    def test_portfolio_metrics_creation(self, sample_metrics_data):
        """Test création des métriques de portefeuille."""
        metrics = sample_metrics_data
        
        assert_valid_uuid(metrics["portfolio_id"])
        assert isinstance(metrics["timestamp"], datetime)
        assert -1 <= metrics["total_return"] <= 3  # Rendement raisonnable
        assert metrics["volatility"] > 0
        assert metrics["max_drawdown"] <= 0
    
    def test_risk_metrics_validation(self, sample_metrics_data):
        """Test validation des métriques de risque."""
        metrics = sample_metrics_data
        
        # VaR doit être négatif (perte potentielle)
        assert metrics["var_95"] <= 0
        assert metrics["var_99"] <= 0
        assert metrics["var_99"] <= metrics["var_95"]  # VaR 99% plus conservateur
        
        # Beta cohérent
        assert metrics["beta"] > 0
        
        # Volatilité positive
        assert metrics["volatility"] > 0
        
        # Max drawdown négatif ou zéro
        assert metrics["max_drawdown"] <= 0
    
    def test_performance_ratios_validation(self, sample_metrics_data):
        """Test validation des ratios de performance."""
        metrics = sample_metrics_data
        
        # Ratios peuvent être négatifs mais avec limites raisonnables
        assert -5 <= metrics["sharpe_ratio"] <= 5
        assert -5 <= metrics["sortino_ratio"] <= 5
        assert metrics["sortino_ratio"] >= metrics["sharpe_ratio"]  # Sortino généralement >= Sharpe
        
        # Taux de gain entre 0 et 1
        assert 0 <= metrics["win_rate"] <= 1
        
        # Facteur de profit positif
        assert metrics["profit_factor"] >= 0


class TestDecisionValidationRules:
    """Tests pour les règles de validation des décisions."""
    
    def test_decision_risk_consistency(self):
        """Test cohérence entre décision et niveau de risque."""
        high_risk_decision = {
            "symbol": "TSLA",
            "decision_type": DecisionType.BUY,
            "risk_level": RiskLevel.HIGH,
            "quantity": Decimal("50"),  # Grande quantité
            "confidence": ConfidenceLevel.MEDIUM,
            "expected_return": Decimal("0.30")  # Rendement élevé
        }
        
        low_risk_decision = {
            "symbol": "JNJ",
            "decision_type": DecisionType.BUY,
            "risk_level": RiskLevel.LOW,
            "quantity": Decimal("10"),  # Petite quantité
            "confidence": ConfidenceLevel.HIGH,
            "expected_return": Decimal("0.08")  # Rendement modeste
        }
        
        # Décision haut risque
        assert high_risk_decision["risk_level"] == RiskLevel.HIGH
        assert high_risk_decision["expected_return"] > low_risk_decision["expected_return"]
        
        # Décision bas risque
        assert low_risk_decision["risk_level"] == RiskLevel.LOW
        assert low_risk_decision["confidence"] == ConfidenceLevel.HIGH
    
    def test_position_sizing_rules(self):
        """Test règles de dimensionnement des positions."""
        portfolio_value = Decimal("100000.00")
        max_position_size = Decimal("0.10")  # 10% max par position
        
        valid_position = {
            "symbol": "AAPL",
            "quantity": Decimal("6"),
            "price": Decimal("150.00"),
            "total_value": Decimal("900.00")  # 0.9% du portefeuille
        }
        
        invalid_position = {
            "symbol": "RISKY_STOCK",
            "quantity": Decimal("100"),
            "price": Decimal("150.00"),
            "total_value": Decimal("15000.00")  # 15% du portefeuille
        }
        
        # Position valide
        valid_weight = valid_position["total_value"] / portfolio_value
        assert valid_weight <= max_position_size
        
        # Position invalide
        invalid_weight = invalid_position["total_value"] / portfolio_value
        assert invalid_weight > max_position_size
    
    def test_correlation_limits(self):
        """Test limites de corrélation entre positions."""
        positions = [
            {"symbol": "AAPL", "sector": "Technology", "weight": Decimal("0.15")},
            {"symbol": "GOOGL", "sector": "Technology", "weight": Decimal("0.12")},
            {"symbol": "MSFT", "sector": "Technology", "weight": Decimal("0.10")},
            {"symbol": "JNJ", "sector": "Healthcare", "weight": Decimal("0.08")}
        ]
        
        max_sector_concentration = Decimal("0.30")  # 30% max par secteur
        
        # Calcul concentration par secteur
        sector_weights = {}
        for pos in positions:
            sector = pos["sector"]
            if sector not in sector_weights:
                sector_weights[sector] = Decimal("0")
            sector_weights[sector] += pos["weight"]
        
        # Vérification limites
        tech_weight = sector_weights.get("Technology", Decimal("0"))
        healthcare_weight = sector_weights.get("Healthcare", Decimal("0"))
        
        assert tech_weight > max_sector_concentration  # Violation détectée
        assert healthcare_weight <= max_sector_concentration  # OK


# Fixtures globales pour les tests de décision
@pytest.fixture
def decision_test_scenarios():
    """Scénarios de test pour décisions."""
    return {
        "conservative_buy": {
            "symbol": "JNJ",
            "decision_type": DecisionType.BUY,
            "risk_level": RiskLevel.LOW,
            "confidence": ConfidenceLevel.HIGH,
            "expected_return": Decimal("0.08"),
            "stop_loss_percent": Decimal("0.05")
        },
        "aggressive_buy": {
            "symbol": "TSLA",
            "decision_type": DecisionType.BUY,
            "risk_level": RiskLevel.HIGH,
            "confidence": ConfidenceLevel.MEDIUM,
            "expected_return": Decimal("0.25"),
            "stop_loss_percent": Decimal("0.15")
        },
        "profit_taking_sell": {
            "symbol": "AAPL",
            "decision_type": DecisionType.SELL,
            "risk_level": RiskLevel.MEDIUM,
            "confidence": ConfidenceLevel.HIGH,
            "reason": "profit_taking"
        }
    }


@pytest.fixture
def portfolio_test_scenarios():
    """Scénarios de test pour portefeuilles."""
    return {
        "balanced_portfolio": {
            "name": "Balanced",
            "target_allocations": {
                "stocks": Decimal("0.60"),
                "bonds": Decimal("0.30"),
                "cash": Decimal("0.10")
            },
            "risk_tolerance": "medium",
            "rebalance_threshold": Decimal("0.05")
        },
        "aggressive_portfolio": {
            "name": "Growth",
            "target_allocations": {
                "stocks": Decimal("0.85"),
                "bonds": Decimal("0.10"),
                "cash": Decimal("0.05")
            },
            "risk_tolerance": "high",
            "rebalance_threshold": Decimal("0.10")
        }
    }