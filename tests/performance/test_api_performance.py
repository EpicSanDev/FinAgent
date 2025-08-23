"""
Tests de Performance - Performance des APIs

Ces tests évaluent les performances des intégrations API externes
(OpenBB, Claude/OpenRouter), mesurent les latences, timeouts,
et optimisent les stratégies de cache et retry.
"""

import pytest
import asyncio
import time
import statistics
import aiohttp
from decimal import Decimal
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from unittest.mock import AsyncMock, patch
import random

from finagent.ai.providers.claude_provider import ClaudeProvider
from finagent.business.models.portfolio_models import Portfolio, Position
from finagent.business.models.decision_models import InvestmentDecision, DecisionType

# Import des utilitaires de test
from tests.utils import (
    create_test_portfolio,
    create_test_strategy,
    MockOpenBBProvider,
    MockClaudeProvider,
    benchmark_performance
)


@dataclass
class APIPerformanceMetrics:
    """Métriques de performance API"""
    endpoint: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    min_latency_ms: float
    max_latency_ms: float
    throughput_rps: float  # requests per second
    error_rate: float
    timeout_count: int
    cache_hit_rate: Optional[float] = None


@dataclass
class APILoadTestResult:
    """Résultat de test de charge API"""
    test_name: str
    concurrent_requests: int
    duration_seconds: float
    metrics: APIPerformanceMetrics
    system_metrics: Dict[str, float]
    degradation_points: List[Tuple[int, float]]  # (concurrent_level, latency)


class APIPerformanceTester:
    """Testeur de performance API"""
    
    def __init__(self, openbb_provider, claude_provider):
        self.openbb_provider = openbb_provider
        self.claude_provider = claude_provider
        self.request_logs = []
        self.cache_stats = {"hits": 0, "misses": 0}
    
    def log_request(self, endpoint: str, start_time: float, end_time: float, 
                   success: bool, error: Optional[str] = None):
        """Log une requête API"""
        latency = (end_time - start_time) * 1000  # ms
        
        self.request_logs.append({
            "endpoint": endpoint,
            "timestamp": start_time,
            "latency_ms": latency,
            "success": success,
            "error": error
        })
    
    async def test_openbb_endpoint_performance(self, endpoint: str, 
                                             requests_count: int,
                                             concurrent_limit: int = 10) -> APIPerformanceMetrics:
        """Test performance d'un endpoint OpenBB"""
        print(f"   🔄 Test endpoint OpenBB: {endpoint}")
        
        symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "NVDA", "META", "AMZN", "NFLX"]
        semaphore = asyncio.Semaphore(concurrent_limit)
        
        async def single_request(symbol: str):
            async with semaphore:
                start_time = time.perf_counter()
                try:
                    if endpoint == "current_price":
                        result = await self.openbb_provider.get_current_price(symbol)
                    elif endpoint == "historical_data":
                        end_date = datetime.now()
                        start_date = end_date - timedelta(days=30)
                        result = await self.openbb_provider.get_historical_data(
                            symbol, start_date, end_date
                        )
                    elif endpoint == "company_info":
                        result = await self.openbb_provider.get_company_info(symbol)
                    elif endpoint == "financial_metrics":
                        result = await self.openbb_provider.get_financial_metrics(symbol)
                    else:
                        raise ValueError(f"Endpoint inconnu: {endpoint}")
                    
                    end_time = time.perf_counter()
                    self.log_request(endpoint, start_time, end_time, True)
                    return result
                    
                except Exception as e:
                    end_time = time.perf_counter()
                    self.log_request(endpoint, start_time, end_time, False, str(e))
                    return None
        
        # Lancer les requêtes
        start_time = time.perf_counter()
        
        tasks = [
            single_request(random.choice(symbols))
            for _ in range(requests_count)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.perf_counter()
        
        # Analyser résultats
        endpoint_logs = [log for log in self.request_logs if log["endpoint"] == endpoint]
        
        successful_logs = [log for log in endpoint_logs if log["success"]]
        failed_logs = [log for log in endpoint_logs if not log["success"]]
        
        if successful_logs:
            latencies = [log["latency_ms"] for log in successful_logs]
            avg_latency = statistics.mean(latencies)
            p95_latency = statistics.quantiles(latencies, n=20)[18] if len(latencies) > 20 else max(latencies)
            p99_latency = statistics.quantiles(latencies, n=100)[98] if len(latencies) > 100 else max(latencies)
            min_latency = min(latencies)
            max_latency = max(latencies)
        else:
            avg_latency = p95_latency = p99_latency = min_latency = max_latency = 0
        
        total_duration = end_time - start_time
        throughput = len(successful_logs) / total_duration if total_duration > 0 else 0
        error_rate = len(failed_logs) / len(endpoint_logs) if endpoint_logs else 0
        
        return APIPerformanceMetrics(
            endpoint=endpoint,
            total_requests=len(endpoint_logs),
            successful_requests=len(successful_logs),
            failed_requests=len(failed_logs),
            avg_latency_ms=avg_latency,
            p95_latency_ms=p95_latency,
            p99_latency_ms=p99_latency,
            min_latency_ms=min_latency,
            max_latency_ms=max_latency,
            throughput_rps=throughput,
            error_rate=error_rate,
            timeout_count=len([log for log in failed_logs if "timeout" in log.get("error", "").lower()])
        )
    
    async def test_claude_endpoint_performance(self, analysis_type: str,
                                             requests_count: int,
                                             concurrent_limit: int = 5) -> APIPerformanceMetrics:
        """Test performance des endpoints Claude"""
        print(f"   🤖 Test endpoint Claude: {analysis_type}")
        
        semaphore = asyncio.Semaphore(concurrent_limit)
        
        async def single_analysis():
            async with semaphore:
                start_time = time.perf_counter()
                try:
                    if analysis_type == "portfolio_analysis":
                        portfolio = create_test_portfolio(initial_capital=Decimal("100000.00"))
                        # Ajouter quelques positions
                        for i in range(5):
                            position = Position(
                                symbol=f"TEST{i:02d}",
                                quantity=random.randint(10, 100),
                                average_price=Decimal(str(random.uniform(50, 200))),
                                current_price=Decimal(str(random.uniform(45, 210))),
                                last_updated=datetime.now()
                            )
                            portfolio.positions.append(position)
                        
                        result = await self.claude_provider.analyze_portfolio(portfolio)
                        
                    elif analysis_type == "market_sentiment":
                        result = await self.claude_provider.analyze_market_sentiment(
                            ["positive news", "market rally", "growth stocks"]
                        )
                        
                    elif analysis_type == "investment_recommendation":
                        market_data = {
                            "symbol": "AAPL",
                            "price": 150.0,
                            "volume": 50000000,
                            "market_cap": 2500000000000
                        }
                        result = await self.claude_provider.generate_investment_recommendation(market_data)
                        
                    else:
                        raise ValueError(f"Type d'analyse inconnu: {analysis_type}")
                    
                    end_time = time.perf_counter()
                    self.log_request(analysis_type, start_time, end_time, True)
                    return result
                    
                except Exception as e:
                    end_time = time.perf_counter()
                    self.log_request(analysis_type, start_time, end_time, False, str(e))
                    return None
        
        # Lancer les analyses
        start_time = time.perf_counter()
        
        tasks = [single_analysis() for _ in range(requests_count)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.perf_counter()
        
        # Analyser résultats
        analysis_logs = [log for log in self.request_logs if log["endpoint"] == analysis_type]
        
        successful_logs = [log for log in analysis_logs if log["success"]]
        failed_logs = [log for log in analysis_logs if not log["success"]]
        
        if successful_logs:
            latencies = [log["latency_ms"] for log in successful_logs]
            avg_latency = statistics.mean(latencies)
            p95_latency = statistics.quantiles(latencies, n=20)[18] if len(latencies) > 20 else max(latencies)
            p99_latency = statistics.quantiles(latencies, n=100)[98] if len(latencies) > 100 else max(latencies)
            min_latency = min(latencies)
            max_latency = max(latencies)
        else:
            avg_latency = p95_latency = p99_latency = min_latency = max_latency = 0
        
        total_duration = end_time - start_time
        throughput = len(successful_logs) / total_duration if total_duration > 0 else 0
        error_rate = len(failed_logs) / len(analysis_logs) if analysis_logs else 0
        
        return APIPerformanceMetrics(
            endpoint=analysis_type,
            total_requests=len(analysis_logs),
            successful_requests=len(successful_logs),
            failed_requests=len(failed_logs),
            avg_latency_ms=avg_latency,
            p95_latency_ms=p95_latency,
            p99_latency_ms=p99_latency,
            min_latency_ms=min_latency,
            max_latency_ms=max_latency,
            throughput_rps=throughput,
            error_rate=error_rate,
            timeout_count=len([log for log in failed_logs if "timeout" in log.get("error", "").lower()])
        )


@pytest.mark.performance
@pytest.mark.api
class TestBasicAPIPerformance:
    """Tests de performance API de base"""
    
    @pytest.fixture
    async def api_test_components(self, test_config):
        """Composants pour tests API"""
        # Utiliser des mocks configurés pour performance réaliste
        openbb_provider = MockOpenBBProvider(test_config.get("openbb", {}))
        claude_provider = MockClaudeProvider(test_config.get("claude", {}))
        
        # Configurer latences réalistes
        openbb_provider.set_latency_simulation(min_ms=50, max_ms=200)
        claude_provider.set_latency_simulation(min_ms=500, max_ms=2000)
        
        return {
            "openbb": openbb_provider,
            "claude": claude_provider
        }
    
    @pytest.mark.asyncio
    async def test_openbb_endpoints_baseline(self, api_test_components):
        """Test baseline performance endpoints OpenBB"""
        tester = APIPerformanceTester(
            api_test_components["openbb"],
            api_test_components["claude"]
        )
        
        print("📊 Test baseline performance OpenBB")
        
        endpoints = ["current_price", "historical_data", "company_info", "financial_metrics"]
        requests_per_endpoint = 20
        
        endpoint_results = {}
        
        for endpoint in endpoints:
            metrics = await tester.test_openbb_endpoint_performance(
                endpoint=endpoint,
                requests_count=requests_per_endpoint,
                concurrent_limit=5
            )
            
            endpoint_results[endpoint] = metrics
            
            print(f"      {endpoint:20s}: {metrics.avg_latency_ms:6.1f}ms avg, "
                  f"{metrics.throughput_rps:5.1f} req/s, "
                  f"{metrics.error_rate:.1%} erreurs")
        
        # Analyse comparative
        fastest_endpoint = min(endpoint_results.values(), key=lambda x: x.avg_latency_ms)
        slowest_endpoint = max(endpoint_results.values(), key=lambda x: x.avg_latency_ms)
        
        avg_throughput = statistics.mean(m.throughput_rps for m in endpoint_results.values())
        total_error_rate = statistics.mean(m.error_rate for m in endpoint_results.values())
        
        print(f"\n📊 Résumé OpenBB:")
        print(f"   Endpoint le plus rapide: {fastest_endpoint.endpoint} ({fastest_endpoint.avg_latency_ms:.1f}ms)")
        print(f"   Endpoint le plus lent: {slowest_endpoint.endpoint} ({slowest_endpoint.avg_latency_ms:.1f}ms)")
        print(f"   Débit moyen: {avg_throughput:.1f} req/s")
        print(f"   Taux d'erreur moyen: {total_error_rate:.1%}")
        
        # Assertions baseline
        for endpoint, metrics in endpoint_results.items():
            assert metrics.error_rate <= 0.05  # Max 5% erreurs
            assert metrics.avg_latency_ms <= 500.0  # Max 500ms moyenne
            assert metrics.throughput_rps >= 1.0  # Min 1 req/s
        
        return endpoint_results
    
    @pytest.mark.asyncio
    async def test_claude_analysis_baseline(self, api_test_components):
        """Test baseline performance analyses Claude"""
        tester = APIPerformanceTester(
            api_test_components["openbb"],
            api_test_components["claude"]
        )
        
        print("🤖 Test baseline performance Claude")
        
        analysis_types = ["portfolio_analysis", "market_sentiment", "investment_recommendation"]
        requests_per_type = 10  # Moins de requêtes pour Claude (plus lent)
        
        analysis_results = {}
        
        for analysis_type in analysis_types:
            metrics = await tester.test_claude_endpoint_performance(
                analysis_type=analysis_type,
                requests_count=requests_per_type,
                concurrent_limit=3  # Limite plus basse pour Claude
            )
            
            analysis_results[analysis_type] = metrics
            
            print(f"      {analysis_type:25s}: {metrics.avg_latency_ms:6.1f}ms avg, "
                  f"{metrics.throughput_rps:5.2f} req/s, "
                  f"{metrics.error_rate:.1%} erreurs")
        
        # Analyse comparative
        fastest_analysis = min(analysis_results.values(), key=lambda x: x.avg_latency_ms)
        slowest_analysis = max(analysis_results.values(), key=lambda x: x.avg_latency_ms)
        
        avg_throughput = statistics.mean(m.throughput_rps for m in analysis_results.values())
        total_error_rate = statistics.mean(m.error_rate for m in analysis_results.values())
        
        print(f"\n📊 Résumé Claude:")
        print(f"   Analyse la plus rapide: {fastest_analysis.endpoint} ({fastest_analysis.avg_latency_ms:.1f}ms)")
        print(f"   Analyse la plus lente: {slowest_analysis.endpoint} ({slowest_analysis.avg_latency_ms:.1f}ms)")
        print(f"   Débit moyen: {avg_throughput:.2f} req/s")
        print(f"   Taux d'erreur moyen: {total_error_rate:.1%}")
        
        # Assertions baseline Claude
        for analysis_type, metrics in analysis_results.items():
            assert metrics.error_rate <= 0.10  # Max 10% erreurs pour Claude
            assert metrics.avg_latency_ms <= 3000.0  # Max 3s moyenne
            assert metrics.throughput_rps >= 0.1  # Min 0.1 req/s
        
        return analysis_results


@pytest.mark.performance
@pytest.mark.api
@pytest.mark.slow
class TestAPILoadTesting:
    """Tests de charge API"""
    
    @pytest.mark.asyncio
    async def test_openbb_concurrent_load(self, api_test_components):
        """Test charge concurrente OpenBB"""
        tester = APIPerformanceTester(
            api_test_components["openbb"],
            api_test_components["claude"]
        )
        
        print("📈 Test charge concurrente OpenBB")
        
        # Test montée progressive de concurrence
        concurrent_levels = [1, 2, 5, 10, 15, 20, 30]
        requests_per_level = 50
        endpoint = "current_price"
        
        load_results = []
        
        for concurrent_limit in concurrent_levels:
            print(f"   🔄 Test {concurrent_limit} requêtes concurrentes")
            
            # Reset logs pour ce niveau
            tester.request_logs.clear()
            
            start_time = time.perf_counter()
            
            metrics = await tester.test_openbb_endpoint_performance(
                endpoint=endpoint,
                requests_count=requests_per_level,
                concurrent_limit=concurrent_limit
            )
            
            end_time = time.perf_counter()
            total_duration = end_time - start_time
            
            load_result = APILoadTestResult(
                test_name=f"openbb_concurrent_{concurrent_limit}",
                concurrent_requests=concurrent_limit,
                duration_seconds=total_duration,
                metrics=metrics,
                system_metrics={
                    "concurrent_level": concurrent_limit,
                    "requests_per_second": requests_per_level / total_duration
                },
                degradation_points=[]
            )
            
            load_results.append(load_result)
            
            print(f"      Latence: {metrics.avg_latency_ms:6.1f}ms (P95: {metrics.p95_latency_ms:6.1f}ms)")
            print(f"      Débit: {metrics.throughput_rps:6.1f} req/s")
            print(f"      Erreurs: {metrics.error_rate:.1%}")
        
        # Analyser dégradation performance
        baseline_latency = load_results[0].metrics.avg_latency_ms
        
        print(f"\n📊 Analyse dégradation concurrence:")
        print(f"   Latence baseline (1 concurrent): {baseline_latency:.1f}ms")
        
        for result in load_results[1:]:
            latency_ratio = result.metrics.avg_latency_ms / baseline_latency
            throughput_efficiency = result.metrics.throughput_rps / result.concurrent_requests
            
            print(f"   {result.concurrent_requests:2d} concurrent: "
                  f"Latence x{latency_ratio:.2f}, "
                  f"Efficacité {throughput_efficiency:.2f} req/s/thread")
            
            # Détecter points de dégradation significative
            if latency_ratio > 2.0:  # Latence > 2x baseline
                result.degradation_points.append((result.concurrent_requests, latency_ratio))
        
        # Assertions charge
        assert load_results[-1].metrics.error_rate <= 0.15  # Max 15% erreurs même en charge
        assert max(r.metrics.avg_latency_ms for r in load_results) <= 1000.0  # Max 1s latence
        
        return load_results
    
    @pytest.mark.asyncio
    async def test_mixed_api_load(self, api_test_components):
        """Test charge mixte OpenBB + Claude"""
        tester = APIPerformanceTester(
            api_test_components["openbb"],
            api_test_components["claude"]
        )
        
        print("🔀 Test charge mixte APIs")
        
        # Simulation charge réaliste mixte
        total_duration = 30  # 30 secondes
        openbb_requests_rate = 2  # 2 req/s OpenBB
        claude_requests_rate = 0.5  # 0.5 req/s Claude
        
        print(f"   Simulation {total_duration}s: OpenBB {openbb_requests_rate} req/s, Claude {claude_requests_rate} req/s")
        
        start_time = time.perf_counter()
        end_time = start_time + total_duration
        
        openbb_tasks = []
        claude_tasks = []
        
        # Générateur de tâches OpenBB
        async def generate_openbb_requests():
            while time.perf_counter() < end_time:
                task = tester.test_openbb_endpoint_performance(
                    endpoint=random.choice(["current_price", "company_info"]),
                    requests_count=1,
                    concurrent_limit=1
                )
                openbb_tasks.append(task)
                await asyncio.sleep(1.0 / openbb_requests_rate)
        
        # Générateur de tâches Claude
        async def generate_claude_requests():
            while time.perf_counter() < end_time:
                task = tester.test_claude_endpoint_performance(
                    analysis_type=random.choice(["portfolio_analysis", "market_sentiment"]),
                    requests_count=1,
                    concurrent_limit=1
                )
                claude_tasks.append(task)
                await asyncio.sleep(1.0 / claude_requests_rate)
        
        # Lancer générateurs en parallèle
        generators = await asyncio.gather(
            generate_openbb_requests(),
            generate_claude_requests(),
            return_exceptions=True
        )
        
        # Attendre completion de toutes les requêtes
        if openbb_tasks:
            openbb_results = await asyncio.gather(*openbb_tasks, return_exceptions=True)
        if claude_tasks:
            claude_results = await asyncio.gather(*claude_tasks, return_exceptions=True)
        
        # Analyser logs mixtes
        total_requests = len(tester.request_logs)
        openbb_logs = [log for log in tester.request_logs if log["endpoint"] in ["current_price", "company_info"]]
        claude_logs = [log for log in tester.request_logs if log["endpoint"] in ["portfolio_analysis", "market_sentiment"]]
        
        openbb_success_rate = len([log for log in openbb_logs if log["success"]]) / len(openbb_logs) if openbb_logs else 0
        claude_success_rate = len([log for log in claude_logs if log["success"]]) / len(claude_logs) if claude_logs else 0
        
        openbb_avg_latency = statistics.mean([log["latency_ms"] for log in openbb_logs if log["success"]]) if openbb_logs else 0
        claude_avg_latency = statistics.mean([log["latency_ms"] for log in claude_logs if log["success"]]) if claude_logs else 0
        
        actual_duration = time.perf_counter() - start_time
        
        print(f"\n📊 Résultats charge mixte:")
        print(f"   Durée: {actual_duration:.1f}s")
        print(f"   Requêtes totales: {total_requests}")
        print(f"   OpenBB: {len(openbb_logs)} req, {openbb_success_rate:.1%} succès, {openbb_avg_latency:.1f}ms avg")
        print(f"   Claude: {len(claude_logs)} req, {claude_success_rate:.1%} succès, {claude_avg_latency:.1f}ms avg")
        
        # Assertions charge mixte
        assert openbb_success_rate >= 0.90  # 90% succès OpenBB
        assert claude_success_rate >= 0.85  # 85% succès Claude
        assert total_requests >= total_duration * (openbb_requests_rate + claude_requests_rate) * 0.8  # 80% du taux attendu
        
        return {
            "duration": actual_duration,
            "total_requests": total_requests,
            "openbb_metrics": {
                "requests": len(openbb_logs),
                "success_rate": openbb_success_rate,
                "avg_latency": openbb_avg_latency
            },
            "claude_metrics": {
                "requests": len(claude_logs),
                "success_rate": claude_success_rate,
                "avg_latency": claude_avg_latency
            }
        }


@pytest.mark.performance
@pytest.mark.api
@pytest.mark.slowest
class TestAPIOptimization:
    """Tests d'optimisation API"""
    
    @pytest.mark.asyncio
    async def test_caching_effectiveness(self, api_test_components):
        """Test efficacité du cache API"""
        # Simuler un cache simple
        cache = {}
        cache_hits = 0
        cache_misses = 0
        
        class CachedOpenBBProvider:
            def __init__(self, base_provider):
                self.base_provider = base_provider
            
            async def get_current_price(self, symbol: str):
                nonlocal cache_hits, cache_misses
                
                cache_key = f"price_{symbol}"
                if cache_key in cache:
                    cache_hits += 1
                    return cache[cache_key]
                else:
                    cache_misses += 1
                    result = await self.base_provider.get_current_price(symbol)
                    cache[cache_key] = result
                    return result
        
        cached_provider = CachedOpenBBProvider(api_test_components["openbb"])
        
        print("💾 Test efficacité cache API")
        
        # Phase 1: Requêtes sans cache (cache miss)
        print("   Phase 1: Population cache")
        
        symbols = ["AAPL", "GOOGL", "MSFT", "TSLA"]
        
        phase1_start = time.perf_counter()
        for symbol in symbols:
            await cached_provider.get_current_price(symbol)
        phase1_end = time.perf_counter()
        
        phase1_duration = (phase1_end - phase1_start) * 1000
        phase1_cache_misses = cache_misses
        
        print(f"      Durée: {phase1_duration:.1f}ms")
        print(f"      Cache misses: {phase1_cache_misses}")
        
        # Phase 2: Requêtes avec cache (cache hit)
        print("   Phase 2: Utilisation cache")
        
        phase2_start = time.perf_counter()
        for symbol in symbols * 3:  # Répéter 3x les mêmes symboles
            await cached_provider.get_current_price(symbol)
        phase2_end = time.perf_counter()
        
        phase2_duration = (phase2_end - phase2_start) * 1000
        phase2_cache_hits = cache_hits
        
        print(f"      Durée: {phase2_duration:.1f}ms")
        print(f"      Cache hits: {phase2_cache_hits}")
        
        # Calcul efficacité cache
        cache_hit_rate = cache_hits / (cache_hits + cache_misses)
        speedup_factor = phase1_duration / phase2_duration if phase2_duration > 0 else 0
        
        print(f"\n📊 Efficacité cache:")
        print(f"   Taux cache hit: {cache_hit_rate:.1%}")
        print(f"   Accélération: {speedup_factor:.1f}x")
        print(f"   Réduction latence: {((phase1_duration - phase2_duration) / phase1_duration * 100):.1f}%")
        
        # Assertions cache
        assert cache_hit_rate >= 0.70  # Au moins 70% cache hits
        assert speedup_factor >= 2.0  # Au moins 2x plus rapide avec cache
        
        return {
            "cache_hit_rate": cache_hit_rate,
            "speedup_factor": speedup_factor,
            "cache_hits": cache_hits,
            "cache_misses": cache_misses
        }
    
    @pytest.mark.asyncio
    async def test_retry_strategy_performance(self, api_test_components):
        """Test performance stratégies de retry"""
        print("🔄 Test performance stratégies retry")
        
        # Simuler provider avec échecs intermittents
        class UnreliableProvider:
            def __init__(self, base_provider, failure_rate=0.3):
                self.base_provider = base_provider
                self.failure_rate = failure_rate
                self.call_count = 0
            
            async def get_current_price(self, symbol: str):
                self.call_count += 1
                if random.random() < self.failure_rate:
                    raise Exception("Simulated API failure")
                return await self.base_provider.get_current_price(symbol)
        
        # Stratégies de retry
        async def no_retry_strategy(provider, symbol):
            return await provider.get_current_price(symbol)
        
        async def simple_retry_strategy(provider, symbol, max_retries=3):
            for attempt in range(max_retries + 1):
                try:
                    return await provider.get_current_price(symbol)
                except Exception as e:
                    if attempt == max_retries:
                        raise e
                    await asyncio.sleep(0.1 * (2 ** attempt))  # Backoff exponentiel
        
        async def circuit_breaker_strategy(provider, symbol, failure_threshold=5):
            # Simulation simple d'un circuit breaker
            if hasattr(circuit_breaker_strategy, 'failures'):
                if circuit_breaker_strategy.failures >= failure_threshold:
                    raise Exception("Circuit breaker open")
            else:
                circuit_breaker_strategy.failures = 0
            
            try:
                result = await provider.get_current_price(symbol)
                circuit_breaker_strategy.failures = 0  # Reset sur succès
                return result
            except Exception as e:
                circuit_breaker_strategy.failures += 1
                raise e
        
        strategies = {
            "no_retry": no_retry_strategy,
            "simple_retry": simple_retry_strategy,
            "circuit_breaker": circuit_breaker_strategy
        }
        
        strategy_results = {}
        
        for strategy_name, strategy_func in strategies.items():
            print(f"   🔄 Test stratégie: {strategy_name}")
            
            unreliable_provider = UnreliableProvider(api_test_components["openbb"], failure_rate=0.3)
            
            # Test 20 requêtes
            successes = 0
            failures = 0
            total_attempts = 0
            latencies = []
            
            for i in range(20):
                start_time = time.perf_counter()
                try:
                    if strategy_name == "simple_retry":
                        await strategy_func(unreliable_provider, f"TEST{i:02d}", max_retries=3)
                    else:
                        await strategy_func(unreliable_provider, f"TEST{i:02d}")
                    successes += 1
                except Exception:
                    failures += 1
                
                end_time = time.perf_counter()
                latencies.append((end_time - start_time) * 1000)
                total_attempts = unreliable_provider.call_count
            
            success_rate = successes / (successes + failures)
            avg_latency = statistics.mean(latencies)
            avg_attempts_per_request = total_attempts / 20
            
            strategy_results[strategy_name] = {
                "success_rate": success_rate,
                "avg_latency_ms": avg_latency,
                "avg_attempts_per_request": avg_attempts_per_request,
                "total_attempts": total_attempts
            }
            
            print(f"      Succès: {success_rate:.1%}")
            print(f"      Latence moyenne: {avg_latency:.1f}ms")
            print(f"      Tentatives/requête: {avg_attempts_per_request:.1f}")
        
        # Comparer stratégies
        best_success = max(strategy_results.values(), key=lambda x: x["success_rate"])
        best_latency = min(strategy_results.values(), key=lambda x: x["avg_latency_ms"])
        
        print(f"\n📊 Comparaison stratégies retry:")
        for strategy, result in strategy_results.items():
            efficiency = result["success_rate"] / result["avg_attempts_per_request"]
            print(f"   {strategy:15s}: {result['success_rate']:.1%} succès, "
                  f"{result['avg_latency_ms']:6.1f}ms, "
                  f"efficacité {efficiency:.2f}")
        
        return strategy_results


if __name__ == "__main__":
    # Exécution directe pour tests de développement
    pytest.main([__file__, "-v", "--tb=short", "-m", "api and not slowest"])