"""
Tests de Performance - Benchmarks de Latence

Ces tests mesurent la latence des opérations critiques de FinAgent
pour identifier les goulots d'étranglement et optimiser les performances.
"""

import pytest
import asyncio
import time
import statistics
from decimal import Decimal
from datetime import datetime, timedelta
from typing import List, Dict, Any, Callable
from dataclasses import dataclass

from finagent.business.models.portfolio_models import Portfolio, Position
from finagent.business.models.decision_models import InvestmentDecision, DecisionType
from finagent.business.strategy.engine.strategy_engine import StrategyEngine
from finagent.business.portfolio.portfolio_manager import PortfolioManager

# Import des utilitaires de test
from tests.utils import (
    create_test_portfolio,
    create_test_strategy,
    MockOpenBBProvider,
    MockClaudeProvider,
    benchmark_performance,
    StockDataFactory
)


@dataclass
class LatencyResult:
    """Résultat de mesure de latence"""
    operation: str
    min_latency: float
    max_latency: float
    avg_latency: float
    median_latency: float
    p95_latency: float
    p99_latency: float
    iterations: int
    total_time: float


def measure_latency(operation_name: str, iterations: int = 100):
    """Décorateur pour mesurer la latence d'une opération"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            latencies = []
            start_total = time.perf_counter()
            
            for _ in range(iterations):
                start = time.perf_counter()
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                end = time.perf_counter()
                latencies.append((end - start) * 1000)  # Convertir en ms
            
            end_total = time.perf_counter()
            total_time = (end_total - start_total) * 1000
            
            # Calculer statistiques
            latency_result = LatencyResult(
                operation=operation_name,
                min_latency=min(latencies),
                max_latency=max(latencies),
                avg_latency=statistics.mean(latencies),
                median_latency=statistics.median(latencies),
                p95_latency=statistics.quantiles(latencies, n=20)[18],  # 95e percentile
                p99_latency=statistics.quantiles(latencies, n=100)[98], # 99e percentile
                iterations=iterations,
                total_time=total_time
            )
            
            return result, latency_result
        return wrapper
    return decorator


@pytest.mark.performance
@pytest.mark.benchmark
class TestLatencyBenchmarks:
    """Tests de benchmarks de latence générale"""
    
    @pytest.fixture
    async def performance_components(self, test_config):
        """Composants optimisés pour tests de performance"""
        # Providers avec cache activé pour performance
        openbb_provider = MockOpenBBProvider(test_config.get("openbb", {}))
        claude_provider = MockClaudeProvider(test_config.get("claude", {}))
        
        # Configuration optimisée
        perf_config = {
            "cache_enabled": True,
            "batch_size": 100,
            "timeout": 1.0
        }
        
        strategy_engine = StrategyEngine({**test_config.get("strategy", {}), **perf_config})
        portfolio_manager = PortfolioManager({**test_config.get("portfolio", {}), **perf_config})
        
        return {
            "openbb": openbb_provider,
            "claude": claude_provider,
            "strategy_engine": strategy_engine,
            "portfolio_manager": portfolio_manager
        }
    
    @pytest.fixture
    def large_portfolio(self):
        """Portfolio large pour tests de performance"""
        return create_test_portfolio(
            initial_capital=Decimal("1000000.00"),
            positions=[
                (f"STOCK{i:03d}", 100 + i, Decimal(f"{100 + i * 5}.00"))
                for i in range(50)  # 50 positions
            ]
        )


@pytest.mark.performance
@pytest.mark.benchmark
class TestOperationLatency:
    """Tests de latence des opérations critiques"""
    
    @pytest.mark.asyncio
    async def test_portfolio_analysis_latency(self, performance_components, large_portfolio):
        """Benchmark de latence pour l'analyse de portefeuille"""
        portfolio_manager = performance_components["portfolio_manager"]
        
        @measure_latency("portfolio_analysis", iterations=50)
        async def analyze_portfolio():
            return await portfolio_manager.analyze_portfolio(large_portfolio)
        
        result, latency = await analyze_portfolio()
        
        # Assertions de performance
        assert latency.avg_latency < 100.0  # Moins de 100ms en moyenne
        assert latency.p95_latency < 200.0  # 95% sous 200ms
        assert latency.p99_latency < 500.0  # 99% sous 500ms
        
        print(f"📊 Benchmark Analyse Portfolio:")
        print(f"   Moyenne: {latency.avg_latency:.2f}ms")
        print(f"   Médiane: {latency.median_latency:.2f}ms")
        print(f"   P95: {latency.p95_latency:.2f}ms")
        print(f"   P99: {latency.p99_latency:.2f}ms")
        print(f"   Min/Max: {latency.min_latency:.2f}/{latency.max_latency:.2f}ms")
        
        assert result is not None
        return latency
    
    @pytest.mark.asyncio
    async def test_strategy_evaluation_latency(self, performance_components):
        """Benchmark de latence pour l'évaluation de stratégies"""
        strategy_engine = performance_components["strategy_engine"]
        
        # Données de test
        market_data = {"price": 150.00, "volume": 1000000}
        technical_indicators = {"RSI": 65, "MACD": {"signal": "bullish"}}
        strategy_config = create_test_strategy("momentum")
        
        @measure_latency("strategy_evaluation", iterations=100)
        async def evaluate_strategy():
            return await strategy_engine.evaluate_symbol(
                symbol="AAPL",
                market_data=market_data,
                technical_indicators=technical_indicators,
                strategy_config=strategy_config
            )
        
        result, latency = await evaluate_strategy()
        
        # Assertions de performance
        assert latency.avg_latency < 50.0   # Moins de 50ms en moyenne
        assert latency.p95_latency < 100.0  # 95% sous 100ms
        assert latency.p99_latency < 200.0  # 99% sous 200ms
        
        print(f"📊 Benchmark Évaluation Stratégie:")
        print(f"   Moyenne: {latency.avg_latency:.2f}ms")
        print(f"   P95: {latency.p95_latency:.2f}ms")
        print(f"   P99: {latency.p99_latency:.2f}ms")
        
        assert result is not None
        return latency
    
    @pytest.mark.asyncio
    async def test_decision_generation_latency(self, performance_components, large_portfolio):
        """Benchmark de latence pour la génération de décisions"""
        portfolio_manager = performance_components["portfolio_manager"]
        
        # Décision de test
        test_decision = InvestmentDecision(
            symbol="NEWSTOCK",
            decision_type=DecisionType.BUY,
            quantity=100,
            target_price=Decimal("200.00"),
            confidence=Decimal("0.8"),
            reasoning="Test de latence",
            max_allocation=Decimal("0.05"),
            created_at=datetime.now()
        )
        
        @measure_latency("decision_validation", iterations=100)
        async def validate_decision():
            return await portfolio_manager.can_execute_decision(
                decision=test_decision,
                portfolio=large_portfolio
            )
        
        result, latency = await validate_decision()
        
        # Assertions de performance
        assert latency.avg_latency < 30.0   # Moins de 30ms en moyenne
        assert latency.p95_latency < 60.0   # 95% sous 60ms
        assert latency.p99_latency < 120.0  # 99% sous 120ms
        
        print(f"📊 Benchmark Validation Décision:")
        print(f"   Moyenne: {latency.avg_latency:.2f}ms")
        print(f"   P95: {latency.p95_latency:.2f}ms")
        print(f"   P99: {latency.p99_latency:.2f}ms")
        
        assert result is not None
        return latency
    
    @pytest.mark.asyncio
    async def test_risk_calculation_latency(self, performance_components, large_portfolio):
        """Benchmark de latence pour les calculs de risque"""
        portfolio_manager = performance_components["portfolio_manager"]
        
        @measure_latency("risk_calculation", iterations=50)
        async def calculate_risk():
            return await portfolio_manager.calculate_risk_metrics(large_portfolio)
        
        result, latency = await calculate_risk()
        
        # Assertions de performance
        assert latency.avg_latency < 150.0  # Moins de 150ms en moyenne
        assert latency.p95_latency < 300.0  # 95% sous 300ms
        assert latency.p99_latency < 600.0  # 99% sous 600ms
        
        print(f"📊 Benchmark Calcul Risque:")
        print(f"   Moyenne: {latency.avg_latency:.2f}ms")
        print(f"   P95: {latency.p95_latency:.2f}ms")
        print(f"   P99: {latency.p99_latency:.2f}ms")
        
        assert result is not None
        return latency


@pytest.mark.performance
@pytest.mark.benchmark
class TestAPILatency:
    """Tests de latence des APIs"""
    
    @pytest.mark.asyncio
    async def test_openbb_api_latency(self, performance_components):
        """Benchmark de latence pour les appels OpenBB"""
        openbb_provider = performance_components["openbb"]
        
        @measure_latency("openbb_current_price", iterations=50)
        async def get_current_price():
            return await openbb_provider.get_current_price("AAPL")
        
        result, latency = await get_current_price()
        
        # Assertions pour API mockée (plus rapide)
        assert latency.avg_latency < 10.0   # Moins de 10ms en moyenne (mock)
        assert latency.p95_latency < 20.0   # 95% sous 20ms
        assert latency.p99_latency < 50.0   # 99% sous 50ms
        
        print(f"📊 Benchmark OpenBB API (mock):")
        print(f"   Moyenne: {latency.avg_latency:.2f}ms")
        print(f"   P95: {latency.p95_latency:.2f}ms")
        print(f"   P99: {latency.p99_latency:.2f}ms")
        
        assert result is not None
        return latency
    
    @pytest.mark.asyncio
    async def test_claude_api_latency(self, performance_components):
        """Benchmark de latence pour les appels Claude"""
        claude_provider = performance_components["claude"]
        
        @measure_latency("claude_completion", iterations=20)  # Moins d'itérations pour IA
        async def generate_completion():
            return await claude_provider.generate_completion(
                "Analysez brièvement AAPL. Réponse en 2 phrases maximum."
            )
        
        result, latency = await generate_completion()
        
        # Assertions pour API mockée IA (simulation plus réaliste)
        assert latency.avg_latency < 100.0  # Moins de 100ms en moyenne (mock)
        assert latency.p95_latency < 200.0  # 95% sous 200ms
        assert latency.p99_latency < 500.0  # 99% sous 500ms
        
        print(f"📊 Benchmark Claude API (mock):")
        print(f"   Moyenne: {latency.avg_latency:.2f}ms")
        print(f"   P95: {latency.p95_latency:.2f}ms")
        print(f"   P99: {latency.p99_latency:.2f}ms")
        
        assert result is not None
        return latency


@pytest.mark.performance
@pytest.mark.benchmark
class TestCalculationLatency:
    """Tests de latence des calculs financiers"""
    
    @pytest.mark.asyncio
    async def test_portfolio_value_calculation_latency(self, large_portfolio):
        """Benchmark de calcul de valeur de portefeuille"""
        
        @measure_latency("portfolio_value_calculation", iterations=1000)
        def calculate_portfolio_value():
            return large_portfolio.total_value
        
        result, latency = await calculate_portfolio_value()
        
        # Calcul simple doit être très rapide
        assert latency.avg_latency < 1.0    # Moins de 1ms en moyenne
        assert latency.p95_latency < 2.0    # 95% sous 2ms
        assert latency.p99_latency < 5.0    # 99% sous 5ms
        
        print(f"📊 Benchmark Calcul Valeur Portfolio:")
        print(f"   Moyenne: {latency.avg_latency:.3f}ms")
        print(f"   P95: {latency.p95_latency:.3f}ms")
        print(f"   P99: {latency.p99_latency:.3f}ms")
        
        assert result > 0
        return latency
    
    @pytest.mark.asyncio
    async def test_allocation_calculation_latency(self, performance_components, large_portfolio):
        """Benchmark de calcul d'allocation"""
        portfolio_manager = performance_components["portfolio_manager"]
        
        @measure_latency("allocation_calculation", iterations=100)
        async def calculate_allocation():
            return await portfolio_manager.get_current_allocation(large_portfolio)
        
        result, latency = await calculate_allocation()
        
        # Calcul d'allocation doit être rapide
        assert latency.avg_latency < 20.0   # Moins de 20ms en moyenne
        assert latency.p95_latency < 40.0   # 95% sous 40ms
        assert latency.p99_latency < 80.0   # 99% sous 80ms
        
        print(f"📊 Benchmark Calcul Allocation:")
        print(f"   Moyenne: {latency.avg_latency:.2f}ms")
        print(f"   P95: {latency.p95_latency:.2f}ms")
        print(f"   P99: {latency.p99_latency:.2f}ms")
        
        assert result is not None
        assert isinstance(result, dict)
        return latency
    
    @pytest.mark.asyncio
    async def test_rebalancing_orders_latency(self, performance_components, large_portfolio):
        """Benchmark de génération d'ordres de rééquilibrage"""
        portfolio_manager = performance_components["portfolio_manager"]
        
        # Allocation cible pour le test
        target_allocation = {
            position.symbol: Decimal("0.02")  # 2% par position (50 positions = 100%)
            for position in large_portfolio.positions
        }
        
        @measure_latency("rebalancing_orders", iterations=20)
        async def generate_rebalancing():
            return await portfolio_manager.generate_rebalancing_orders(
                portfolio=large_portfolio,
                target_allocation=target_allocation
            )
        
        result, latency = await generate_rebalancing()
        
        # Génération ordres complexe mais doit rester raisonnable
        assert latency.avg_latency < 200.0  # Moins de 200ms en moyenne
        assert latency.p95_latency < 400.0  # 95% sous 400ms
        assert latency.p99_latency < 800.0  # 99% sous 800ms
        
        print(f"📊 Benchmark Génération Ordres Rééquilibrage:")
        print(f"   Moyenne: {latency.avg_latency:.2f}ms")
        print(f"   P95: {latency.p95_latency:.2f}ms")
        print(f"   P99: {latency.p99_latency:.2f}ms")
        
        assert result is not None
        return latency


@pytest.mark.performance
@pytest.mark.benchmark
@pytest.mark.slow
class TestBatchOperationLatency:
    """Tests de latence pour les opérations en lot"""
    
    @pytest.mark.asyncio
    async def test_batch_symbol_analysis_latency(self, performance_components):
        """Benchmark d'analyse de symboles en lot"""
        strategy_engine = performance_components["strategy_engine"]
        openbb_provider = performance_components["openbb"]
        
        symbols = [f"STOCK{i:03d}" for i in range(20)]  # 20 symboles
        strategy_config = create_test_strategy("momentum")
        
        @measure_latency("batch_symbol_analysis", iterations=10)
        async def analyze_batch():
            results = []
            for symbol in symbols:
                market_data = await openbb_provider.get_current_price(symbol)
                technical_data = await openbb_provider.get_technical_indicators(
                    symbol, indicators=["RSI", "MACD"]
                )
                
                evaluation = await strategy_engine.evaluate_symbol(
                    symbol=symbol,
                    market_data=market_data,
                    technical_indicators=technical_data,
                    strategy_config=strategy_config
                )
                results.append(evaluation)
            
            return results
        
        result, latency = await analyze_batch()
        
        # Analyse en lot de 20 symboles
        assert latency.avg_latency < 2000.0  # Moins de 2s en moyenne
        assert latency.p95_latency < 4000.0  # 95% sous 4s
        assert latency.p99_latency < 8000.0  # 99% sous 8s
        
        # Calculer latence par symbole
        avg_per_symbol = latency.avg_latency / len(symbols)
        
        print(f"📊 Benchmark Analyse Lot (20 symboles):")
        print(f"   Moyenne totale: {latency.avg_latency:.0f}ms")
        print(f"   Moyenne par symbole: {avg_per_symbol:.1f}ms")
        print(f"   P95: {latency.p95_latency:.0f}ms")
        print(f"   P99: {latency.p99_latency:.0f}ms")
        
        assert len(result) == len(symbols)
        return latency
    
    @pytest.mark.asyncio
    async def test_parallel_vs_sequential_latency(self, performance_components):
        """Comparaison latence traitement parallèle vs séquentiel"""
        strategy_engine = performance_components["strategy_engine"]
        openbb_provider = performance_components["openbb"]
        
        symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]
        strategy_config = create_test_strategy("balanced")
        
        # Test séquentiel
        @measure_latency("sequential_processing", iterations=10)
        async def process_sequential():
            results = []
            for symbol in symbols:
                market_data = await openbb_provider.get_current_price(symbol)
                evaluation = await strategy_engine.evaluate_symbol(
                    symbol=symbol,
                    market_data=market_data,
                    technical_indicators={"RSI": 50},
                    strategy_config=strategy_config
                )
                results.append(evaluation)
            return results
        
        # Test parallèle
        @measure_latency("parallel_processing", iterations=10)
        async def process_parallel():
            async def analyze_symbol(symbol):
                market_data = await openbb_provider.get_current_price(symbol)
                return await strategy_engine.evaluate_symbol(
                    symbol=symbol,
                    market_data=market_data,
                    technical_indicators={"RSI": 50},
                    strategy_config=strategy_config
                )
            
            tasks = [analyze_symbol(symbol) for symbol in symbols]
            return await asyncio.gather(*tasks)
        
        # Exécuter les deux tests
        seq_result, seq_latency = await process_sequential()
        par_result, par_latency = await process_parallel()
        
        # Le parallèle devrait être plus rapide
        speedup = seq_latency.avg_latency / par_latency.avg_latency
        
        print(f"📊 Comparaison Séquentiel vs Parallèle:")
        print(f"   Séquentiel: {seq_latency.avg_latency:.1f}ms")
        print(f"   Parallèle: {par_latency.avg_latency:.1f}ms")
        print(f"   Accélération: {speedup:.2f}x")
        
        # Vérifier que le parallèle est plus efficace
        assert speedup > 1.0  # Au moins une amélioration
        assert par_latency.avg_latency < seq_latency.avg_latency
        
        assert len(seq_result) == len(symbols)
        assert len(par_result) == len(symbols)
        
        return {
            "sequential": seq_latency,
            "parallel": par_latency,
            "speedup": speedup
        }


if __name__ == "__main__":
    # Exécution directe pour tests de développement
    pytest.main([__file__, "-v", "--tb=short", "-m", "benchmark"])