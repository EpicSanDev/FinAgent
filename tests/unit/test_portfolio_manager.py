"""
Tests unitaires pour le gestionnaire de portefeuille FinAgent.

Ce module teste toutes les fonctionnalités de gestion de portefeuille,
incluant l'allocation d'actifs, le rééquilibrage, la gestion des risques
et le suivi de performance.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, patch, AsyncMock
import uuid

from finagent.core.portfolio.portfolio_manager import (
    PortfolioManager, AllocationEngine, RiskManager, PerformanceTracker
)
from finagent.core.models.portfolio_models import (
    Portfolio, Position, Transaction, TransactionType,
    PortfolioMetrics, RiskMetrics, PerformanceMetrics
)
from finagent.core.models.decision_models import (
    InvestmentDecision, DecisionType, ConfidenceLevel
)
from finagent.core.exceptions import (
    PortfolioError, InsufficientFundsError, PositionNotFoundError,
    RiskLimitExceededError, InvalidAllocationError
)
from tests.utils import (
    PortfolioFactory, TransactionFactory, PositionFactory,
    create_test_portfolio, assert_decimal_equals, assert_valid_uuid
)


class TestPortfolioManager:
    """Tests pour le gestionnaire de portefeuille principal."""
    
    @pytest.fixture
    def portfolio_manager(self):
        """Gestionnaire de portefeuille configuré."""
        config = {
            "max_positions": 20,
            "min_cash_reserve": 0.05,
            "rebalance_threshold": 0.05,
            "risk_limit": 0.20,
            "commission_rate": 0.001
        }
        return PortfolioManager(config)
    
    @pytest.fixture
    def sample_portfolio_data(self):
        """Données de portefeuille échantillon."""
        return {
            "id": str(uuid.uuid4()),
            "name": "Test Portfolio",
            "initial_value": Decimal("100000.00"),
            "cash_balance": Decimal("15000.00"),
            "positions": [
                {
                    "symbol": "AAPL",
                    "quantity": Decimal("50"),
                    "avg_cost": Decimal("150.00"),
                    "current_price": Decimal("155.25"),
                    "market_value": Decimal("7762.50")
                },
                {
                    "symbol": "GOOGL",
                    "quantity": Decimal("10"),
                    "avg_cost": Decimal("2700.00"),
                    "current_price": Decimal("2750.80"),
                    "market_value": Decimal("27508.00")
                },
                {
                    "symbol": "MSFT",
                    "quantity": Decimal("40"),
                    "avg_cost": Decimal("320.00"),
                    "current_price": Decimal("335.50"),
                    "market_value": Decimal("13420.00")
                }
            ],
            "total_value": Decimal("63690.50"),
            "target_allocation": {
                "AAPL": Decimal("0.25"),
                "GOOGL": Decimal("0.30"),
                "MSFT": Decimal("0.20"),
                "cash": Decimal("0.25")
            }
        }
    
    @pytest.mark.asyncio
    async def test_create_portfolio(self, portfolio_manager):
        """Test création d'un portefeuille."""
        portfolio_config = {
            "name": "New Portfolio",
            "initial_cash": Decimal("50000.00"),
            "strategy": "balanced",
            "risk_tolerance": "medium"
        }
        
        portfolio_id = await portfolio_manager.create_portfolio(portfolio_config)
        
        assert_valid_uuid(portfolio_id)
        
        portfolio = await portfolio_manager.get_portfolio(portfolio_id)
        assert portfolio["name"] == "New Portfolio"
        assert portfolio["cash_balance"] == Decimal("50000.00")
        assert portfolio["total_value"] == Decimal("50000.00")
        assert len(portfolio["positions"]) == 0
    
    @pytest.mark.asyncio
    async def test_add_position(self, portfolio_manager, sample_portfolio_data):
        """Test ajout d'une position."""
        portfolio_id = str(uuid.uuid4())
        await portfolio_manager.load_portfolio(portfolio_id, sample_portfolio_data)
        
        new_position = {
            "symbol": "TSLA",
            "quantity": Decimal("20"),
            "price": Decimal("200.00"),
            "transaction_type": TransactionType.BUY
        }
        
        result = await portfolio_manager.add_position(portfolio_id, new_position)
        
        assert result["success"] is True
        assert "transaction_id" in result
        
        # Vérifier que la position a été ajoutée
        updated_portfolio = await portfolio_manager.get_portfolio(portfolio_id)
        tsla_position = next(
            (p for p in updated_portfolio["positions"] if p["symbol"] == "TSLA"),
            None
        )
        
        assert tsla_position is not None
        assert tsla_position["quantity"] == Decimal("20")
        assert tsla_position["avg_cost"] == Decimal("200.00")
    
    @pytest.mark.asyncio
    async def test_remove_position(self, portfolio_manager, sample_portfolio_data):
        """Test suppression d'une position."""
        portfolio_id = str(uuid.uuid4())
        await portfolio_manager.load_portfolio(portfolio_id, sample_portfolio_data)
        
        # Vendre une partie de la position AAPL
        sell_order = {
            "symbol": "AAPL",
            "quantity": Decimal("20"),  # Vendre 20 sur 50
            "price": Decimal("160.00"),
            "transaction_type": TransactionType.SELL
        }
        
        result = await portfolio_manager.remove_position(portfolio_id, sell_order)
        
        assert result["success"] is True
        
        # Vérifier que la position a été réduite
        updated_portfolio = await portfolio_manager.get_portfolio(portfolio_id)
        aapl_position = next(
            (p for p in updated_portfolio["positions"] if p["symbol"] == "AAPL"),
            None
        )
        
        assert aapl_position["quantity"] == Decimal("30")  # 50 - 20
    
    @pytest.mark.asyncio
    async def test_insufficient_funds_error(self, portfolio_manager, sample_portfolio_data):
        """Test erreur fonds insuffisants."""
        portfolio_id = str(uuid.uuid4())
        await portfolio_manager.load_portfolio(portfolio_id, sample_portfolio_data)
        
        # Essayer d'acheter pour plus que le cash disponible
        large_order = {
            "symbol": "EXPENSIVE",
            "quantity": Decimal("100"),
            "price": Decimal("1000.00"),  # 100k$ > 15k$ cash disponible
            "transaction_type": TransactionType.BUY
        }
        
        with pytest.raises(InsufficientFundsError):
            await portfolio_manager.add_position(portfolio_id, large_order)
    
    @pytest.mark.asyncio
    async def test_position_not_found_error(self, portfolio_manager, sample_portfolio_data):
        """Test erreur position non trouvée."""
        portfolio_id = str(uuid.uuid4())
        await portfolio_manager.load_portfolio(portfolio_id, sample_portfolio_data)
        
        # Essayer de vendre une position inexistante
        invalid_sell = {
            "symbol": "NONEXISTENT",
            "quantity": Decimal("10"),
            "price": Decimal("100.00"),
            "transaction_type": TransactionType.SELL
        }
        
        with pytest.raises(PositionNotFoundError):
            await portfolio_manager.remove_position(portfolio_id, invalid_sell)
    
    @pytest.mark.asyncio
    async def test_calculate_portfolio_value(self, portfolio_manager, sample_portfolio_data):
        """Test calcul de la valeur du portefeuille."""
        portfolio_id = str(uuid.uuid4())
        await portfolio_manager.load_portfolio(portfolio_id, sample_portfolio_data)
        
        # Mettre à jour les prix
        price_updates = {
            "AAPL": Decimal("160.00"),
            "GOOGL": Decimal("2800.00"),
            "MSFT": Decimal("340.00")
        }
        
        total_value = await portfolio_manager.calculate_portfolio_value(
            portfolio_id, price_updates
        )
        
        # Calculer valeur attendue
        expected_aapl = Decimal("50") * Decimal("160.00")  # 8000
        expected_googl = Decimal("10") * Decimal("2800.00")  # 28000
        expected_msft = Decimal("40") * Decimal("340.00")  # 13600
        expected_cash = sample_portfolio_data["cash_balance"]  # 15000
        expected_total = expected_aapl + expected_googl + expected_msft + expected_cash
        
        assert_decimal_equals(total_value, expected_total)
    
    @pytest.mark.asyncio
    async def test_portfolio_metrics_calculation(self, portfolio_manager, sample_portfolio_data):
        """Test calcul des métriques de portefeuille."""
        portfolio_id = str(uuid.uuid4())
        await portfolio_manager.load_portfolio(portfolio_id, sample_portfolio_data)
        
        metrics = await portfolio_manager.calculate_metrics(portfolio_id)
        
        assert "total_return" in metrics
        assert "volatility" in metrics
        assert "sharpe_ratio" in metrics
        assert "max_drawdown" in metrics
        assert "beta" in metrics
        assert "alpha" in metrics
        
        # Vérifier plages raisonnables
        assert -1 <= metrics["total_return"] <= 2
        assert 0 <= metrics["volatility"] <= 1
        assert -5 <= metrics["sharpe_ratio"] <= 5


class TestAllocationEngine:
    """Tests pour le moteur d'allocation."""
    
    @pytest.fixture
    def allocation_engine(self):
        """Moteur d'allocation configuré."""
        return AllocationEngine()
    
    @pytest.fixture
    def target_allocation(self):
        """Allocation cible échantillon."""
        return {
            "AAPL": Decimal("0.25"),
            "GOOGL": Decimal("0.20"),
            "MSFT": Decimal("0.15"),
            "TSLA": Decimal("0.10"),
            "AMZN": Decimal("0.15"),
            "cash": Decimal("0.15")
        }
    
    @pytest.fixture
    def current_portfolio(self):
        """Portefeuille actuel pour allocation."""
        return {
            "total_value": Decimal("100000.00"),
            "cash_balance": Decimal("5000.00"),
            "positions": [
                {"symbol": "AAPL", "market_value": Decimal("35000.00")},  # 35%
                {"symbol": "GOOGL", "market_value": Decimal("15000.00")},  # 15%
                {"symbol": "MSFT", "market_value": Decimal("20000.00")},  # 20%
                {"symbol": "TSLA", "market_value": Decimal("25000.00")}   # 25%
            ]
        }
    
    def test_calculate_allocation_drift(self, allocation_engine, target_allocation, current_portfolio):
        """Test calcul de dérive d'allocation."""
        drift = allocation_engine.calculate_allocation_drift(
            current_portfolio, target_allocation
        )
        
        assert "AAPL" in drift
        assert "GOOGL" in drift
        assert "MSFT" in drift
        assert "TSLA" in drift
        assert "AMZN" in drift
        assert "cash" in drift
        
        # AAPL: 35% actuel vs 25% cible = +10% de dérive
        assert_decimal_equals(drift["AAPL"], Decimal("0.10"))
        
        # GOOGL: 15% actuel vs 20% cible = -5% de dérive
        assert_decimal_equals(drift["GOOGL"], Decimal("-0.05"))
        
        # AMZN: 0% actuel vs 15% cible = -15% de dérive
        assert_decimal_equals(drift["AMZN"], Decimal("-0.15"))
    
    def test_generate_rebalancing_orders(self, allocation_engine, target_allocation, current_portfolio):
        """Test génération d'ordres de rééquilibrage."""
        rebalance_threshold = Decimal("0.05")  # 5%
        
        orders = allocation_engine.generate_rebalancing_orders(
            current_portfolio, target_allocation, rebalance_threshold
        )
        
        # Vérifier que seules les dérives > seuil génèrent des ordres
        significant_drifts = ["AAPL", "AMZN"]  # |dérive| > 5%
        
        for order in orders:
            assert order["symbol"] in significant_drifts
            assert order["action"] in ["buy", "sell"]
            assert order["quantity"] > 0
        
        # AAPL devrait avoir un ordre de vente (sur-pondéré)
        aapl_order = next((o for o in orders if o["symbol"] == "AAPL"), None)
        assert aapl_order is not None
        assert aapl_order["action"] == "sell"
        
        # AMZN devrait avoir un ordre d'achat (sous-pondéré)
        amzn_order = next((o for o in orders if o["symbol"] == "AMZN"), None)
        assert amzn_order is not None
        assert amzn_order["action"] == "buy"
    
    def test_optimize_allocation(self, allocation_engine):
        """Test optimisation d'allocation."""
        assets = ["AAPL", "GOOGL", "MSFT", "TSLA"]
        
        # Données historiques simulées
        historical_returns = {
            "AAPL": [0.02, 0.01, -0.01, 0.03, 0.00],
            "GOOGL": [0.01, 0.02, 0.00, -0.01, 0.02],
            "MSFT": [0.015, 0.005, 0.01, 0.02, 0.01],
            "TSLA": [0.05, -0.03, 0.02, -0.01, 0.04]
        }
        
        constraints = {
            "max_weight": 0.40,
            "min_weight": 0.05,
            "target_return": 0.12,
            "max_volatility": 0.20
        }
        
        optimized_allocation = allocation_engine.optimize_allocation(
            assets, historical_returns, constraints
        )
        
        # Vérifier contraintes
        total_weight = sum(optimized_allocation.values())
        assert abs(total_weight - 1.0) < 0.001  # Somme = 1
        
        for symbol, weight in optimized_allocation.items():
            assert constraints["min_weight"] <= weight <= constraints["max_weight"]
    
    def test_sector_allocation_limits(self, allocation_engine):
        """Test limites d'allocation sectorielle."""
        portfolio_allocation = {
            "AAPL": Decimal("0.25"),    # Technology
            "GOOGL": Decimal("0.20"),   # Technology
            "MSFT": Decimal("0.15"),    # Technology
            "JNJ": Decimal("0.10"),     # Healthcare
            "JPM": Decimal("0.15"),     # Financial
            "cash": Decimal("0.15")
        }
        
        sector_mapping = {
            "AAPL": "Technology",
            "GOOGL": "Technology",
            "MSFT": "Technology",
            "JNJ": "Healthcare",
            "JPM": "Financial"
        }
        
        sector_limits = {
            "Technology": Decimal("0.50"),  # 50% max
            "Healthcare": Decimal("0.30"),
            "Financial": Decimal("0.30")
        }
        
        violations = allocation_engine.check_sector_limits(
            portfolio_allocation, sector_mapping, sector_limits
        )
        
        # Technology: 25% + 20% + 15% = 60% > 50% limite
        assert "Technology" in violations
        assert violations["Technology"]["current"] == Decimal("0.60")
        assert violations["Technology"]["limit"] == Decimal("0.50")
        assert violations["Technology"]["excess"] == Decimal("0.10")


class TestRiskManager:
    """Tests pour le gestionnaire de risques."""
    
    @pytest.fixture
    def risk_manager(self):
        """Gestionnaire de risques configuré."""
        config = {
            "max_portfolio_var": 0.05,  # 5% VaR max
            "max_position_size": 0.20,  # 20% max par position
            "max_sector_concentration": 0.40,  # 40% max par secteur
            "max_correlation": 0.8,  # Corrélation max entre positions
            "stop_loss_threshold": 0.10  # 10% stop loss
        }
        return RiskManager(config)
    
    @pytest.fixture
    def portfolio_with_risks(self):
        """Portefeuille avec risques pour tests."""
        return {
            "total_value": Decimal("100000.00"),
            "positions": [
                {
                    "symbol": "AAPL",
                    "market_value": Decimal("25000.00"),
                    "beta": 1.20,
                    "volatility": 0.25,
                    "sector": "Technology"
                },
                {
                    "symbol": "GOOGL",
                    "market_value": Decimal("20000.00"),
                    "beta": 1.15,
                    "volatility": 0.30,
                    "sector": "Technology"
                },
                {
                    "symbol": "TSLA",
                    "market_value": Decimal("30000.00"),  # Position importante
                    "beta": 1.80,
                    "volatility": 0.45,
                    "sector": "Technology"
                }
            ]
        }
    
    def test_calculate_portfolio_var(self, risk_manager, portfolio_with_risks):
        """Test calcul VaR du portefeuille."""
        var_95 = risk_manager.calculate_portfolio_var(portfolio_with_risks, confidence=0.95)
        
        assert 0 < var_95 < 1  # VaR entre 0 et 100%
        assert isinstance(var_95, (float, Decimal))
    
    def test_check_position_size_limits(self, risk_manager, portfolio_with_risks):
        """Test vérification des limites de taille de position."""
        violations = risk_manager.check_position_size_limits(portfolio_with_risks)
        
        # TSLA = 30% > 20% limite
        assert len(violations) == 1
        assert violations[0]["symbol"] == "TSLA"
        assert violations[0]["current_weight"] == Decimal("0.30")
        assert violations[0]["limit"] == Decimal("0.20")
    
    def test_check_sector_concentration(self, risk_manager, portfolio_with_risks):
        """Test vérification de la concentration sectorielle."""
        violations = risk_manager.check_sector_concentration(portfolio_with_risks)
        
        # Technology: 25% + 20% + 30% = 75% > 40% limite
        assert len(violations) == 1
        assert violations[0]["sector"] == "Technology"
        assert violations[0]["concentration"] == Decimal("0.75")
        assert violations[0]["limit"] == Decimal("0.40")
    
    def test_calculate_correlation_risk(self, risk_manager):
        """Test calcul du risque de corrélation."""
        correlation_matrix = {
            ("AAPL", "GOOGL"): 0.85,  # Corrélation élevée
            ("AAPL", "TSLA"): 0.75,
            ("GOOGL", "TSLA"): 0.90   # Corrélation très élevée
        }
        
        portfolio_weights = {
            "AAPL": Decimal("0.30"),
            "GOOGL": Decimal("0.25"),
            "TSLA": Decimal("0.35")
        }
        
        high_correlations = risk_manager.find_high_correlations(
            correlation_matrix, portfolio_weights, threshold=0.8
        )
        
        # GOOGL-TSLA corrélation > 0.8
        assert len(high_correlations) >= 1
        googl_tsla_corr = next(
            (c for c in high_correlations 
             if set(c["assets"]) == {"GOOGL", "TSLA"}),
            None
        )
        assert googl_tsla_corr is not None
        assert googl_tsla_corr["correlation"] == 0.90
    
    def test_calculate_stop_loss_levels(self, risk_manager, portfolio_with_risks):
        """Test calcul des niveaux de stop loss."""
        current_prices = {
            "AAPL": Decimal("150.00"),
            "GOOGL": Decimal("2700.00"),
            "TSLA": Decimal("200.00")
        }
        
        stop_losses = risk_manager.calculate_stop_loss_levels(
            portfolio_with_risks, current_prices
        )
        
        for symbol, stop_level in stop_losses.items():
            current_price = current_prices[symbol]
            expected_stop = current_price * Decimal("0.90")  # 10% stop loss
            assert_decimal_equals(stop_level, expected_stop)
    
    def test_assess_overall_risk_score(self, risk_manager, portfolio_with_risks):
        """Test évaluation du score de risque global."""
        risk_assessment = risk_manager.assess_portfolio_risk(portfolio_with_risks)
        
        assert "overall_score" in risk_assessment
        assert "risk_factors" in risk_assessment
        assert "recommendations" in risk_assessment
        
        # Score entre 0 et 1
        assert 0 <= risk_assessment["overall_score"] <= 1
        
        # Facteurs de risque détectés
        risk_factors = risk_assessment["risk_factors"]
        assert "concentration_risk" in risk_factors
        assert "sector_risk" in risk_factors
        
        # Ce portefeuille devrait avoir un score de risque élevé
        assert risk_assessment["overall_score"] > 0.6


class TestPerformanceTracker:
    """Tests pour le suivi de performance."""
    
    @pytest.fixture
    def performance_tracker(self):
        """Tracker de performance configuré."""
        return PerformanceTracker()
    
    @pytest.fixture
    def historical_portfolio_values(self):
        """Valeurs historiques du portefeuille."""
        base_date = datetime.now() - timedelta(days=30)
        return [
            {
                "date": base_date + timedelta(days=i),
                "total_value": Decimal(str(100000 + i * 100 + (i % 5) * 500)),
                "cash_value": Decimal(str(10000 - i * 50)),
                "positions_value": Decimal(str(90000 + i * 150 + (i % 5) * 500))
            }
            for i in range(31)  # 31 jours de données
        ]
    
    @pytest.fixture
    def benchmark_returns(self):
        """Rendements de benchmark."""
        return [
            {"date": datetime.now() - timedelta(days=30-i), "return": 0.001 * (i % 3)}
            for i in range(31)
        ]
    
    def test_calculate_returns(self, performance_tracker, historical_portfolio_values):
        """Test calcul des rendements."""
        daily_returns = performance_tracker.calculate_daily_returns(historical_portfolio_values)
        
        assert len(daily_returns) == len(historical_portfolio_values) - 1  # N-1 rendements
        
        for return_data in daily_returns:
            assert "date" in return_data
            assert "daily_return" in return_data
            assert -1 <= return_data["daily_return"] <= 1  # Rendement raisonnable
    
    def test_calculate_volatility(self, performance_tracker, historical_portfolio_values):
        """Test calcul de la volatilité."""
        daily_returns = performance_tracker.calculate_daily_returns(historical_portfolio_values)
        returns_only = [r["daily_return"] for r in daily_returns]
        
        volatility = performance_tracker.calculate_volatility(returns_only)
        
        assert 0 <= volatility <= 2  # Volatilité raisonnable
        assert isinstance(volatility, (float, Decimal))
    
    def test_calculate_sharpe_ratio(self, performance_tracker, historical_portfolio_values):
        """Test calcul du ratio de Sharpe."""
        daily_returns = performance_tracker.calculate_daily_returns(historical_portfolio_values)
        returns_only = [r["daily_return"] for r in daily_returns]
        
        risk_free_rate = 0.02  # 2% annuel
        sharpe_ratio = performance_tracker.calculate_sharpe_ratio(
            returns_only, risk_free_rate
        )
        
        assert -5 <= sharpe_ratio <= 5  # Ratio raisonnable
        assert isinstance(sharpe_ratio, (float, Decimal))
    
    def test_calculate_max_drawdown(self, performance_tracker, historical_portfolio_values):
        """Test calcul du drawdown maximum."""
        max_drawdown = performance_tracker.calculate_max_drawdown(historical_portfolio_values)
        
        assert max_drawdown <= 0  # Drawdown toujours négatif ou zéro
        assert max_drawdown >= -1  # Ne peut pas perdre plus de 100%
    
    def test_calculate_alpha_beta(self, performance_tracker, historical_portfolio_values, benchmark_returns):
        """Test calcul alpha et beta."""
        portfolio_returns = performance_tracker.calculate_daily_returns(historical_portfolio_values)
        
        alpha, beta = performance_tracker.calculate_alpha_beta(
            portfolio_returns, benchmark_returns
        )
        
        assert -2 <= alpha <= 2  # Alpha raisonnable
        assert 0 <= beta <= 3  # Beta raisonnable
    
    def test_performance_attribution(self, performance_tracker):
        """Test attribution de performance."""
        position_returns = [
            {"symbol": "AAPL", "return": 0.05, "weight": 0.25, "sector": "Technology"},
            {"symbol": "GOOGL", "return": 0.03, "weight": 0.20, "sector": "Technology"},
            {"symbol": "JNJ", "return": 0.02, "weight": 0.15, "sector": "Healthcare"},
            {"symbol": "JPM", "return": 0.04, "weight": 0.15, "sector": "Financial"}
        ]
        
        attribution = performance_tracker.calculate_performance_attribution(position_returns)
        
        assert "sector_attribution" in attribution
        assert "security_selection" in attribution
        assert "total_return" in attribution
        
        # Vérifier attribution sectorielle
        sector_attr = attribution["sector_attribution"]
        assert "Technology" in sector_attr
        assert "Healthcare" in sector_attr
        assert "Financial" in sector_attr
    
    def test_rolling_performance_metrics(self, performance_tracker, historical_portfolio_values):
        """Test métriques de performance glissantes."""
        window_size = 7  # 7 jours
        
        rolling_metrics = performance_tracker.calculate_rolling_metrics(
            historical_portfolio_values, window_size
        )
        
        expected_length = len(historical_portfolio_values) - window_size + 1
        assert len(rolling_metrics) == expected_length
        
        for metric in rolling_metrics:
            assert "date" in metric
            assert "rolling_return" in metric
            assert "rolling_volatility" in metric
            assert "rolling_sharpe" in metric


class TestPortfolioOptimization:
    """Tests pour l'optimisation de portefeuille."""
    
    @pytest.fixture
    def portfolio_optimizer(self):
        """Optimiseur de portefeuille."""
        from finagent.core.portfolio.optimization import PortfolioOptimizer
        return PortfolioOptimizer()
    
    @pytest.fixture
    def asset_universe(self):
        """Univers d'actifs pour optimisation."""
        return {
            "AAPL": {
                "expected_return": 0.12,
                "volatility": 0.25,
                "sector": "Technology"
            },
            "GOOGL": {
                "expected_return": 0.10,
                "volatility": 0.30,
                "sector": "Technology"
            },
            "JNJ": {
                "expected_return": 0.08,
                "volatility": 0.15,
                "sector": "Healthcare"
            },
            "JPM": {
                "expected_return": 0.09,
                "volatility": 0.20,
                "sector": "Financial"
            }
        }
    
    def test_mean_variance_optimization(self, portfolio_optimizer, asset_universe):
        """Test optimisation moyenne-variance."""
        target_return = 0.10
        
        constraints = {
            "max_weight": 0.40,
            "min_weight": 0.05,
            "sector_limits": {"Technology": 0.50}
        }
        
        optimal_weights = portfolio_optimizer.optimize_mean_variance(
            asset_universe, target_return, constraints
        )
        
        # Vérifier contraintes
        total_weight = sum(optimal_weights.values())
        assert abs(total_weight - 1.0) < 0.001
        
        for symbol, weight in optimal_weights.items():
            assert constraints["min_weight"] <= weight <= constraints["max_weight"]
        
        # Vérifier limite sectorielle
        tech_weight = optimal_weights.get("AAPL", 0) + optimal_weights.get("GOOGL", 0)
        assert tech_weight <= constraints["sector_limits"]["Technology"]
    
    def test_risk_parity_optimization(self, portfolio_optimizer, asset_universe):
        """Test optimisation risk parity."""
        risk_parity_weights = portfolio_optimizer.optimize_risk_parity(asset_universe)
        
        # Vérifier que les poids somment à 1
        total_weight = sum(risk_parity_weights.values())
        assert abs(total_weight - 1.0) < 0.001
        
        # En risk parity, les actifs moins volatils devraient avoir plus de poids
        jnj_weight = risk_parity_weights["JNJ"]  # Volatilité 0.15
        googl_weight = risk_parity_weights["GOOGL"]  # Volatilité 0.30
        assert jnj_weight > googl_weight
    
    def test_black_litterman_optimization(self, portfolio_optimizer, asset_universe):
        """Test optimisation Black-Litterman."""
        # Vues de l'investisseur
        investor_views = {
            "AAPL": {"expected_return": 0.15, "confidence": 0.8},
            "JNJ": {"expected_return": 0.06, "confidence": 0.6}
        }
        
        market_cap_weights = {
            "AAPL": 0.30,
            "GOOGL": 0.25,
            "JNJ": 0.25,
            "JPM": 0.20
        }
        
        bl_weights = portfolio_optimizer.optimize_black_litterman(
            asset_universe, investor_views, market_cap_weights
        )
        
        # Les poids devraient être ajustés selon les vues
        total_weight = sum(bl_weights.values())
        assert abs(total_weight - 1.0) < 0.001
        
        # AAPL devrait avoir un poids plus élevé (vue optimiste)
        assert bl_weights["AAPL"] >= market_cap_weights["AAPL"]


# Fixtures globales pour tests de portefeuille
@pytest.fixture
def portfolio_test_scenarios():
    """Scénarios de test pour portefeuilles."""
    return {
        "conservative": {
            "allocation": {"stocks": 0.40, "bonds": 0.50, "cash": 0.10},
            "max_position": 0.10,
            "rebalance_threshold": 0.03
        },
        "balanced": {
            "allocation": {"stocks": 0.60, "bonds": 0.30, "cash": 0.10},
            "max_position": 0.15,
            "rebalance_threshold": 0.05
        },
        "aggressive": {
            "allocation": {"stocks": 0.85, "bonds": 0.10, "cash": 0.05},
            "max_position": 0.25,
            "rebalance_threshold": 0.10
        }
    }


@pytest.fixture
def market_stress_scenarios():
    """Scénarios de stress de marché."""
    return {
        "market_crash": {
            "equity_drop": -0.30,
            "bond_change": 0.05,
            "volatility_spike": 2.0
        },
        "interest_rate_shock": {
            "rate_change": 0.02,
            "bond_impact": -0.10,
            "growth_stock_impact": -0.15
        },
        "sector_rotation": {
            "tech_impact": -0.20,
            "value_impact": 0.10,
            "defensive_impact": 0.05
        }
    }