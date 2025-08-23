"""
Tests de Performance - Performance des Algorithmes

Ces tests évaluent les performances des algorithmes core de FinAgent :
évaluation de stratégies, calculs de risques, optimisation de portefeuille,
et algorithmes de décision financière.
"""

import pytest
import asyncio
import time
import statistics
import math
import numpy as np
from decimal import Decimal
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple, Callable
from dataclasses import dataclass
import random

from finagent.business.models.portfolio_models import Portfolio, Position
from finagent.business.models.decision_models import InvestmentDecision, DecisionType
from finagent.business.strategy.engine.strategy_engine import StrategyEngine
from finagent.business.portfolio.portfolio_manager import PortfolioManager
from finagent.business.decision.risk_evaluator import RiskEvaluator

# Import des utilitaires de test
from tests.utils import (
    create_test_portfolio,
    create_test_strategy,
    MockOpenBBProvider,
    MockClaudeProvider,
    benchmark_performance
)


@dataclass
class AlgorithmPerformanceResult:
    """Résultat de performance algorithme"""
    algorithm_name: str
    input_size: int
    execution_time_ms: float
    operations_per_second: float
    memory_usage_mb: float
    complexity_analysis: str
    scaling_factor: float
    accuracy_metrics: Optional[Dict[str, float]] = None


@dataclass
class ComplexityBenchmark:
    """Benchmark de complexité algorithmique"""
    algorithm: str
    input_sizes: List[int]
    execution_times: List[float]
    theoretical_complexity: str
    measured_complexity: str
    scaling_efficiency: float


class AlgorithmBenchmarker:
    """Benchmarker pour algorithmes FinAgent"""
    
    def __init__(self, components: Dict[str, Any]):
        self.components = components
        self.results = []
    
    @benchmark_performance
    async def benchmark_algorithm(self, algorithm_func: Callable, 
                                input_data: Any, 
                                algorithm_name: str) -> AlgorithmPerformanceResult:
        """Benchmark un algorithme spécifique"""
        import psutil
        
        # Mesure mémoire avant
        process = psutil.Process()
        memory_before = process.memory_info().rss / (1024 * 1024)
        
        # Mesure temps d'exécution
        start_time = time.perf_counter()
        
        if asyncio.iscoroutinefunction(algorithm_func):
            result = await algorithm_func(input_data)
        else:
            result = algorithm_func(input_data)
        
        end_time = time.perf_counter()
        
        # Mesure mémoire après
        memory_after = process.memory_info().rss / (1024 * 1024)
        
        execution_time = (end_time - start_time) * 1000  # ms
        memory_usage = memory_after - memory_before
        
        # Estimer taille d'entrée
        input_size = self._estimate_input_size(input_data)
        operations_per_second = (input_size / execution_time) * 1000 if execution_time > 0 else 0
        
        return AlgorithmPerformanceResult(
            algorithm_name=algorithm_name,
            input_size=input_size,
            execution_time_ms=execution_time,
            operations_per_second=operations_per_second,
            memory_usage_mb=memory_usage,
            complexity_analysis="O(n)",  # Sera raffiné par analyse
            scaling_factor=1.0
        )
    
    def _estimate_input_size(self, input_data: Any) -> int:
        """Estime la taille d'entrée d'un algorithme"""
        if isinstance(input_data, Portfolio):
            return len(input_data.positions)
        elif isinstance(input_data, list):
            return len(input_data)
        elif isinstance(input_data, dict):
            return len(input_data)
        elif hasattr(input_data, '__len__'):
            return len(input_data)
        else:
            return 1
    
    async def complexity_analysis(self, algorithm_func: Callable,
                                input_generator: Callable,
                                sizes: List[int],
                                algorithm_name: str) -> ComplexityBenchmark:
        """Analyse la complexité d'un algorithme"""
        execution_times = []
        
        print(f"   🔬 Analyse complexité: {algorithm_name}")
        
        for size in sizes:
            input_data = input_generator(size)
            
            # Moyenner sur plusieurs exécutions pour réduire le bruit
            runs = 3
            run_times = []
            
            for _ in range(runs):
                start_time = time.perf_counter()
                
                if asyncio.iscoroutinefunction(algorithm_func):
                    await algorithm_func(input_data)
                else:
                    algorithm_func(input_data)
                
                end_time = time.perf_counter()
                run_times.append((end_time - start_time) * 1000)
            
            avg_time = statistics.mean(run_times)
            execution_times.append(avg_time)
            
            print(f"      Taille {size:4d}: {avg_time:8.2f}ms")
        
        # Analyse de la complexité mesurée
        measured_complexity = self._analyze_complexity_pattern(sizes, execution_times)
        scaling_efficiency = self._calculate_scaling_efficiency(sizes, execution_times)
        
        return ComplexityBenchmark(
            algorithm=algorithm_name,
            input_sizes=sizes,
            execution_times=execution_times,
            theoretical_complexity="To be determined",
            measured_complexity=measured_complexity,
            scaling_efficiency=scaling_efficiency
        )
    
    def _analyze_complexity_pattern(self, sizes: List[int], times: List[float]) -> str:
        """Analyse le pattern de complexité à partir des mesures"""
        if len(sizes) < 3:
            return "Insufficient data"
        
        # Calculer ratios de croissance
        size_ratios = [sizes[i] / sizes[i-1] for i in range(1, len(sizes))]
        time_ratios = [times[i] / times[i-1] for i in range(1, len(times))]
        
        avg_size_ratio = statistics.mean(size_ratios)
        avg_time_ratio = statistics.mean(time_ratios)
        
        # Classifier la complexité
        if avg_time_ratio <= avg_size_ratio * 1.1:
            return "O(n) - Linear"
        elif avg_time_ratio <= (avg_size_ratio ** 1.5) * 1.1:
            return "O(n log n) - Linearithmic" 
        elif avg_time_ratio <= (avg_size_ratio ** 2) * 1.1:
            return "O(n²) - Quadratic"
        else:
            return "O(n³+) - Polynomial or worse"
    
    def _calculate_scaling_efficiency(self, sizes: List[int], times: List[float]) -> float:
        """Calcule l'efficacité de scaling"""
        if len(sizes) < 2:
            return 1.0
        
        # Efficacité = croissance idéale / croissance réelle
        size_growth = sizes[-1] / sizes[0]
        time_growth = times[-1] / times[0]
        
        return size_growth / time_growth if time_growth > 0 else 0.0


@pytest.mark.performance
@pytest.mark.algorithm
class TestCoreAlgorithmPerformance:
    """Tests de performance algorithmes core"""
    
    @pytest.fixture
    async def algorithm_test_components(self, test_config):
        """Composants pour tests algorithmes"""
        openbb_provider = MockOpenBBProvider(test_config.get("openbb", {}))
        claude_provider = MockClaudeProvider(test_config.get("claude", {}))
        
        strategy_engine = StrategyEngine(test_config.get("strategy", {}))
        portfolio_manager = PortfolioManager(test_config.get("portfolio", {}))
        risk_evaluator = RiskEvaluator(test_config.get("risk", {}))
        
        return {
            "openbb": openbb_provider,
            "claude": claude_provider,
            "strategy_engine": strategy_engine,
            "portfolio_manager": portfolio_manager,
            "risk_evaluator": risk_evaluator
        }
    
    @pytest.mark.asyncio
    async def test_portfolio_valuation_performance(self, algorithm_test_components):
        """Test performance calcul valeur portefeuille"""
        benchmarker = AlgorithmBenchmarker(algorithm_test_components)
        
        print("💰 Test performance évaluation portefeuille")
        
        # Générateur de portfolios de tailles variables
        def generate_portfolio(num_positions: int) -> Portfolio:
            portfolio = create_test_portfolio(initial_capital=Decimal("1000000.00"))
            
            for i in range(num_positions):
                position = Position(
                    symbol=f"STOCK{i:04d}",
                    quantity=random.randint(10, 1000),
                    average_price=Decimal(str(random.uniform(10, 500))),
                    current_price=Decimal(str(random.uniform(8, 520))),
                    last_updated=datetime.now()
                )
                portfolio.positions.append(position)
            
            return portfolio
        
        # Test complexité avec différentes tailles
        sizes = [10, 25, 50, 100, 250, 500, 1000]
        
        complexity_result = await benchmarker.complexity_analysis(
            algorithm_func=algorithm_test_components["portfolio_manager"].calculate_value,
            input_generator=generate_portfolio,
            sizes=sizes,
            algorithm_name="portfolio_valuation"
        )
        
        print(f"\n📊 Résultats évaluation portefeuille:")
        print(f"   Complexité mesurée: {complexity_result.measured_complexity}")
        print(f"   Efficacité scaling: {complexity_result.scaling_efficiency:.2f}")
        print(f"   Temps max (1000 pos): {complexity_result.execution_times[-1]:.1f}ms")
        
        # Assertions performance
        assert complexity_result.execution_times[-1] < 100.0  # Moins de 100ms pour 1000 positions
        assert complexity_result.scaling_efficiency > 0.5  # Efficacité raisonnable
        assert "Linear" in complexity_result.measured_complexity or "log" in complexity_result.measured_complexity  # Complexité acceptable
        
        return complexity_result
    
    @pytest.mark.asyncio
    async def test_risk_calculation_performance(self, algorithm_test_components):
        """Test performance calculs de risque"""
        benchmarker = AlgorithmBenchmarker(algorithm_test_components)
        
        print("⚠️  Test performance calculs de risque")
        
        # Générateur de portfolios pour calculs de risque
        def generate_risk_portfolio(num_positions: int) -> Portfolio:
            portfolio = create_test_portfolio(initial_capital=Decimal("5000000.00"))
            
            # Créer positions avec historique de prix pour calculs de risque
            for i in range(num_positions):
                position = Position(
                    symbol=f"RISK{i:04d}",
                    quantity=random.randint(100, 1000),
                    average_price=Decimal(str(random.uniform(50, 300))),
                    current_price=Decimal(str(random.uniform(45, 320))),
                    last_updated=datetime.now()
                )
                portfolio.positions.append(position)
            
            return portfolio
        
        # Test différentes tailles pour calculs de risque
        sizes = [5, 10, 20, 50, 100, 200]
        
        complexity_result = await benchmarker.complexity_analysis(
            algorithm_func=algorithm_test_components["portfolio_manager"].calculate_risk_metrics,
            input_generator=generate_risk_portfolio,
            sizes=sizes,
            algorithm_name="risk_calculation"
        )
        
        # Test spécifique VaR et autres métriques complexes
        large_portfolio = generate_risk_portfolio(100)
        
        var_result = await benchmarker.benchmark_algorithm(
            algorithm_func=algorithm_test_components["portfolio_manager"].calculate_value_at_risk,
            input_data=large_portfolio,
            algorithm_name="value_at_risk"
        )
        
        sharpe_result = await benchmarker.benchmark_algorithm(
            algorithm_func=algorithm_test_components["portfolio_manager"].calculate_sharpe_ratio,
            input_data=large_portfolio,
            algorithm_name="sharpe_ratio"
        )
        
        print(f"\n📊 Résultats calculs de risque:")
        print(f"   Complexité globale: {complexity_result.measured_complexity}")
        print(f"   VaR (100 pos): {var_result.execution_time_ms:.1f}ms")
        print(f"   Sharpe ratio (100 pos): {sharpe_result.execution_time_ms:.1f}ms")
        print(f"   Efficacité scaling: {complexity_result.scaling_efficiency:.2f}")
        
        # Assertions risque
        assert complexity_result.execution_times[-1] < 500.0  # Moins de 500ms pour calculs complexes
        assert var_result.execution_time_ms < 100.0  # VaR rapide
        assert sharpe_result.execution_time_ms < 50.0  # Sharpe très rapide
        
        return {
            "complexity": complexity_result,
            "var_performance": var_result,
            "sharpe_performance": sharpe_result
        }
    
    @pytest.mark.asyncio
    async def test_strategy_evaluation_performance(self, algorithm_test_components):
        """Test performance évaluation de stratégies"""
        benchmarker = AlgorithmBenchmarker(algorithm_test_components)
        
        print("🎯 Test performance évaluation stratégies")
        
        # Générateur de données de marché complexes
        def generate_market_data(num_indicators: int) -> Dict[str, Any]:
            market_data = {
                "symbol": "TEST",
                "price": random.uniform(100, 200),
                "volume": random.randint(1000000, 50000000),
                "market_cap": random.uniform(1e9, 1e12)
            }
            
            # Ajouter indicateurs techniques
            technical_indicators = {}
            indicator_types = ["MA", "EMA", "RSI", "MACD", "BB", "STOCH", "ADX", "CCI"]
            
            for i in range(num_indicators):
                indicator_name = f"{random.choice(indicator_types)}_{i}"
                technical_indicators[indicator_name] = random.uniform(-100, 100)
            
            return {
                "market_data": market_data,
                "technical_indicators": technical_indicators,
                "strategy": create_test_strategy("complex")
            }
        
        # Test avec complexité croissante des stratégies
        sizes = [5, 10, 20, 50, 100, 200]  # Nombre d'indicateurs
        
        async def evaluate_strategy_with_data(data: Dict[str, Any]):
            return await algorithm_test_components["strategy_engine"].evaluate_symbol(
                symbol=data["market_data"]["symbol"],
                market_data=data["market_data"],
                technical_indicators=data["technical_indicators"],
                strategy_config=data["strategy"]
            )
        
        complexity_result = await benchmarker.complexity_analysis(
            algorithm_func=evaluate_strategy_with_data,
            input_generator=generate_market_data,
            sizes=sizes,
            algorithm_name="strategy_evaluation"
        )
        
        # Test stratégies spécifiques
        strategy_types = ["momentum", "mean_reversion", "breakout", "balanced"]
        strategy_results = {}
        
        for strategy_type in strategy_types:
            strategy = create_test_strategy(strategy_type)
            market_data = generate_market_data(50)
            market_data["strategy"] = strategy
            
            result = await benchmarker.benchmark_algorithm(
                algorithm_func=evaluate_strategy_with_data,
                input_data=market_data,
                algorithm_name=f"strategy_{strategy_type}"
            )
            
            strategy_results[strategy_type] = result
        
        print(f"\n📊 Résultats évaluation stratégies:")
        print(f"   Complexité: {complexity_result.measured_complexity}")
        print(f"   Temps max (200 indicateurs): {complexity_result.execution_times[-1]:.1f}ms")
        
        for strategy_type, result in strategy_results.items():
            print(f"   {strategy_type:15s}: {result.execution_time_ms:6.1f}ms")
        
        # Assertions stratégies
        assert complexity_result.execution_times[-1] < 200.0  # Moins de 200ms même complexe
        assert all(r.execution_time_ms < 100.0 for r in strategy_results.values())  # Chaque stratégie < 100ms
        
        return {
            "complexity": complexity_result,
            "strategy_results": strategy_results
        }


@pytest.mark.performance
@pytest.mark.algorithm
@pytest.mark.slow
class TestOptimizationAlgorithms:
    """Tests de performance algorithmes d'optimisation"""
    
    @pytest.mark.asyncio
    async def test_portfolio_optimization_performance(self, algorithm_test_components):
        """Test performance optimisation de portefeuille"""
        benchmarker = AlgorithmBenchmarker(algorithm_test_components)
        
        print("⚖️  Test performance optimisation portefeuille")
        
        # Générateur de données d'optimisation
        def generate_optimization_data(num_assets: int) -> Dict[str, Any]:
            # Matrice de corrélation aléatoire
            correlation_matrix = np.random.rand(num_assets, num_assets)
            correlation_matrix = (correlation_matrix + correlation_matrix.T) / 2  # Symétrique
            np.fill_diagonal(correlation_matrix, 1.0)  # Diagonale = 1
            
            # Rendements attendus et volatilités
            expected_returns = [random.uniform(0.05, 0.15) for _ in range(num_assets)]
            volatilities = [random.uniform(0.10, 0.30) for _ in range(num_assets)]
            
            # Portfolio actuel
            current_weights = [random.uniform(0.01, 0.20) for _ in range(num_assets)]
            total_weight = sum(current_weights)
            current_weights = [w / total_weight for w in current_weights]
            
            return {
                "num_assets": num_assets,
                "correlation_matrix": correlation_matrix,
                "expected_returns": expected_returns,
                "volatilities": volatilities,
                "current_weights": current_weights,
                "target_return": 0.10,
                "risk_tolerance": 0.20
            }
        
        # Algorithme d'optimisation simplifié (simulation)
        def portfolio_optimization(data: Dict[str, Any]) -> Dict[str, float]:
            num_assets = data["num_assets"]
            
            # Simulation d'algorithme d'optimisation (complexité O(n³))
            # En réalité utiliserait des méthodes comme mean-variance optimization
            
            # Simulation calculs matriciels
            correlation_matrix = data["correlation_matrix"]
            
            # Opérations coûteuses simulées
            for i in range(num_assets):
                for j in range(num_assets):
                    for k in range(min(10, num_assets)):  # Limiter pour éviter explosion temps
                        _ = correlation_matrix[i][j] * data["expected_returns"][k]
            
            # Résultat optimisé simulé
            optimized_weights = [random.uniform(0.05, 0.25) for _ in range(num_assets)]
            total = sum(optimized_weights)
            optimized_weights = [w / total for w in optimized_weights]
            
            return {
                "optimized_weights": optimized_weights,
                "expected_return": sum(w * r for w, r in zip(optimized_weights, data["expected_returns"])),
                "expected_risk": random.uniform(0.15, 0.25)
            }
        
        # Test complexité optimisation
        sizes = [5, 10, 15, 20, 30, 40, 50]
        
        complexity_result = await benchmarker.complexity_analysis(
            algorithm_func=portfolio_optimization,
            input_generator=generate_optimization_data,
            sizes=sizes,
            algorithm_name="portfolio_optimization"
        )
        
        # Test algorithmes spécifiques
        large_optimization = generate_optimization_data(30)
        
        mean_variance_result = await benchmarker.benchmark_algorithm(
            algorithm_func=portfolio_optimization,
            input_data=large_optimization,
            algorithm_name="mean_variance_optimization"
        )
        
        print(f"\n📊 Résultats optimisation portefeuille:")
        print(f"   Complexité: {complexity_result.measured_complexity}")
        print(f"   Temps optimisation (50 actifs): {complexity_result.execution_times[-1]:.1f}ms")
        print(f"   Mean-Variance (30 actifs): {mean_variance_result.execution_time_ms:.1f}ms")
        print(f"   Efficacité scaling: {complexity_result.scaling_efficiency:.2f}")
        
        # Assertions optimisation
        assert complexity_result.execution_times[-1] < 1000.0  # Moins de 1s pour 50 actifs
        assert mean_variance_result.execution_time_ms < 500.0  # Moins de 500ms pour 30 actifs
        
        return {
            "complexity": complexity_result,
            "mean_variance": mean_variance_result
        }
    
    @pytest.mark.asyncio
    async def test_rebalancing_algorithm_performance(self, algorithm_test_components):
        """Test performance algorithmes de rebalancing"""
        benchmarker = AlgorithmBenchmarker(algorithm_test_components)
        
        print("🔄 Test performance algorithmes rebalancing")
        
        # Générateur de portfolios pour rebalancing
        def generate_rebalancing_portfolio(num_positions: int) -> Portfolio:
            portfolio = create_test_portfolio(initial_capital=Decimal("10000000.00"))
            
            # Créer positions déséquilibrées nécessitant rebalancing
            for i in range(num_positions):
                # Poids inégaux pour forcer rebalancing
                weight = random.uniform(0.01, 0.15) if i < num_positions // 2 else random.uniform(0.001, 0.05)
                value = float(portfolio.cash) * weight
                
                price = random.uniform(50, 300)
                quantity = int(value / price)
                
                position = Position(
                    symbol=f"REBAL{i:04d}",
                    quantity=quantity,
                    average_price=Decimal(str(price)),
                    current_price=Decimal(str(price * random.uniform(0.9, 1.1))),
                    last_updated=datetime.now()
                )
                portfolio.positions.append(position)
            
            return portfolio
        
        # Test complexité rebalancing
        sizes = [10, 20, 30, 50, 75, 100]
        
        complexity_result = await benchmarker.complexity_analysis(
            algorithm_func=algorithm_test_components["portfolio_manager"].generate_rebalancing_recommendations,
            input_generator=generate_rebalancing_portfolio,
            sizes=sizes,
            algorithm_name="rebalancing_algorithm"
        )
        
        # Test avec contraintes spécifiques
        large_portfolio = generate_rebalancing_portfolio(50)
        
        # Différents types de rebalancing
        threshold_rebalancing = await benchmarker.benchmark_algorithm(
            algorithm_func=algorithm_test_components["portfolio_manager"].generate_rebalancing_recommendations,
            input_data=large_portfolio,
            algorithm_name="threshold_rebalancing"
        )
        
        print(f"\n📊 Résultats rebalancing:")
        print(f"   Complexité: {complexity_result.measured_complexity}")
        print(f"   Temps rebalancing (100 pos): {complexity_result.execution_times[-1]:.1f}ms")
        print(f"   Rebalancing seuil (50 pos): {threshold_rebalancing.execution_time_ms:.1f}ms")
        
        # Assertions rebalancing
        assert complexity_result.execution_times[-1] < 300.0  # Moins de 300ms pour 100 positions
        assert threshold_rebalancing.execution_time_ms < 150.0  # Moins de 150ms pour 50 positions
        
        return {
            "complexity": complexity_result,
            "threshold_rebalancing": threshold_rebalancing
        }


@pytest.mark.performance
@pytest.mark.algorithm
@pytest.mark.slowest
class TestAdvancedAlgorithmPerformance:
    """Tests de performance algorithmes avancés"""
    
    @pytest.mark.asyncio
    async def test_monte_carlo_simulation_performance(self, algorithm_test_components):
        """Test performance simulations Monte Carlo"""
        benchmarker = AlgorithmBenchmarker(algorithm_test_components)
        
        print("🎲 Test performance simulations Monte Carlo")
        
        # Simulation Monte Carlo pour analyse de risque
        def monte_carlo_simulation(num_simulations: int) -> Dict[str, Any]:
            portfolio_values = []
            
            # Paramètres simulation
            initial_value = 1000000.0
            daily_return_mean = 0.0008  # 0.08% par jour
            daily_return_std = 0.015    # 1.5% volatilité
            time_horizon = 252  # 1 an
            
            for _ in range(num_simulations):
                value = initial_value
                
                for day in range(time_horizon):
                    daily_return = random.gauss(daily_return_mean, daily_return_std)
                    value *= (1 + daily_return)
                
                portfolio_values.append(value)
            
            # Calculs statistiques
            portfolio_values.sort()
            var_95 = portfolio_values[int(0.05 * num_simulations)]
            var_99 = portfolio_values[int(0.01 * num_simulations)]
            
            return {
                "simulations": num_simulations,
                "final_values": portfolio_values,
                "var_95": var_95,
                "var_99": var_99,
                "expected_value": statistics.mean(portfolio_values)
            }
        
        # Test différents nombres de simulations
        simulation_sizes = [100, 500, 1000, 5000, 10000]
        
        complexity_result = await benchmarker.complexity_analysis(
            algorithm_func=monte_carlo_simulation,
            input_generator=lambda size: size,
            sizes=simulation_sizes,
            algorithm_name="monte_carlo_simulation"
        )
        
        print(f"\n📊 Résultats Monte Carlo:")
        print(f"   Complexité: {complexity_result.measured_complexity}")
        print(f"   Temps 10k simulations: {complexity_result.execution_times[-1]:.1f}ms")
        print(f"   Efficacité: {complexity_result.scaling_efficiency:.3f}")
        
        # Test de précision vs performance
        precision_tests = [1000, 5000, 10000]
        precision_results = {}
        
        base_result = monte_carlo_simulation(10000)  # Référence
        
        for size in precision_tests:
            start_time = time.perf_counter()
            result = monte_carlo_simulation(size)
            end_time = time.perf_counter()
            
            # Calculer erreur relative
            var_error = abs(result["var_95"] - base_result["var_95"]) / base_result["var_95"]
            
            precision_results[size] = {
                "execution_time": (end_time - start_time) * 1000,
                "var_error": var_error,
                "precision_ratio": 1.0 / var_error if var_error > 0 else float('inf')
            }
        
        print(f"\n   Analyse précision vs performance:")
        for size, result in precision_results.items():
            efficiency = result["precision_ratio"] / result["execution_time"]
            print(f"   {size:5d} sim: {result['execution_time']:6.1f}ms, "
                  f"erreur {result['var_error']:.3f}, "
                  f"efficacité {efficiency:.2f}")
        
        # Assertions Monte Carlo
        assert complexity_result.execution_times[-1] < 2000.0  # Moins de 2s pour 10k simulations
        assert complexity_result.scaling_efficiency > 0.8  # Bonne efficacité linéaire
        
        return {
            "complexity": complexity_result,
            "precision_analysis": precision_results
        }
    
    @pytest.mark.asyncio
    async def test_machine_learning_performance(self, algorithm_test_components):
        """Test performance algorithmes ML simplifiés"""
        benchmarker = AlgorithmBenchmarker(algorithm_test_components)
        
        print("🤖 Test performance algorithmes ML")
        
        # Simulation d'entraînement modèle ML simple
        def train_prediction_model(data_size: int) -> Dict[str, Any]:
            # Générer données d'entraînement (prix historiques)
            features = []
            targets = []
            
            for i in range(data_size):
                # Features: prix passés, volumes, indicateurs
                feature_vector = [
                    random.uniform(90, 110),   # Prix J-1
                    random.uniform(85, 115),   # Prix J-2
                    random.uniform(80, 120),   # Prix J-3
                    random.uniform(1e6, 10e6), # Volume
                    random.uniform(20, 80),    # RSI
                    random.uniform(-2, 2),     # MACD
                ]
                features.append(feature_vector)
                
                # Target: mouvement prix futur
                target = random.choice([0, 1])  # Binaire: hausse/baisse
                targets.append(target)
            
            # Simulation entraînement (régression logistique simple)
            weights = [random.uniform(-1, 1) for _ in range(len(features[0]))]
            
            # Simulation itérations d'optimisation
            learning_rate = 0.01
            epochs = min(100, data_size // 10)  # Adaptatif
            
            for epoch in range(epochs):
                for i in range(len(features)):
                    # Simulation gradient descent
                    prediction = sum(w * f for w, f in zip(weights, features[i]))
                    error = targets[i] - (1 if prediction > 0 else 0)
                    
                    # Update weights (simulation)
                    for j in range(len(weights)):
                        weights[j] += learning_rate * error * features[i][j] * 0.001
            
            # Évaluation sur données test
            accuracy = random.uniform(0.6, 0.8)  # Simulation
            
            return {
                "model_weights": weights,
                "training_accuracy": accuracy,
                "data_size": data_size,
                "epochs": epochs
            }
        
        # Test complexité ML
        data_sizes = [100, 500, 1000, 2000, 5000]
        
        complexity_result = await benchmarker.complexity_analysis(
            algorithm_func=train_prediction_model,
            input_generator=lambda size: size,
            sizes=data_sizes,
            algorithm_name="ml_training"
        )
        
        # Test inférence vs entraînement
        large_model = train_prediction_model(2000)
        
        def predict_single(features: List[float]) -> float:
            return sum(w * f for w, f in zip(large_model["model_weights"], features))
        
        # Test performance inférence
        inference_features = [random.uniform(50, 150) for _ in range(6)]
        
        inference_result = await benchmarker.benchmark_algorithm(
            algorithm_func=predict_single,
            input_data=inference_features,
            algorithm_name="ml_inference"
        )
        
        print(f"\n📊 Résultats ML:")
        print(f"   Complexité entraînement: {complexity_result.measured_complexity}")
        print(f"   Temps entraînement (5k): {complexity_result.execution_times[-1]:.1f}ms")
        print(f"   Temps inférence: {inference_result.execution_time_ms:.3f}ms")
        print(f"   Ratio entraînement/inférence: {complexity_result.execution_times[-1] / inference_result.execution_time_ms:.0f}x")
        
        # Assertions ML
        assert complexity_result.execution_times[-1] < 5000.0  # Moins de 5s entraînement
        assert inference_result.execution_time_ms < 1.0  # Moins de 1ms inférence
        
        return {
            "training_complexity": complexity_result,
            "inference_performance": inference_result,
            "model_size": len(large_model["model_weights"])
        }


if __name__ == "__main__":
    # Exécution directe pour tests de développement
    pytest.main([__file__, "-v", "--tb=short", "-m", "algorithm and not slowest"])