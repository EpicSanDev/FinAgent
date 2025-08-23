"""
Tests de Performance - Performance en Concurrence

Ces tests évaluent les performances du système FinAgent sous charge
concurrente, testent les mécanismes de synchronisation, détectent
les race conditions et mesurent l'efficacité du parallélisme.
"""

import pytest
import asyncio
import time
import statistics
import threading
import multiprocessing
from decimal import Decimal
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple, Callable
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import random
import queue
import weakref

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
    benchmark_performance
)


@dataclass
class ConcurrencyTestResult:
    """Résultat de test de concurrence"""
    test_name: str
    concurrent_operations: int
    execution_time_ms: float
    operations_per_second: float
    success_rate: float
    race_conditions_detected: int
    deadlocks_detected: int
    thread_safety_score: float
    scalability_efficiency: float


@dataclass
class ParallelismMetrics:
    """Métriques de parallélisme"""
    sequential_time_ms: float
    parallel_time_ms: float
    speedup_factor: float
    efficiency: float
    overhead_percentage: float
    optimal_thread_count: int


class ConcurrencyTester:
    """Testeur de concurrence et parallélisme"""
    
    def __init__(self, components: Dict[str, Any]):
        self.components = components
        self.race_condition_counter = 0
        self.deadlock_counter = 0
        self.shared_state = {}
        self.operation_results = []
        self.lock = threading.Lock()
    
    def reset_counters(self):
        """Reset des compteurs de test"""
        self.race_condition_counter = 0
        self.deadlock_counter = 0
        self.shared_state.clear()
        self.operation_results.clear()
    
    async def concurrent_portfolio_operations(self, num_operations: int, 
                                            operation_type: str) -> ConcurrencyTestResult:
        """Test opérations concurrentes sur portfolios"""
        self.reset_counters()
        
        print(f"   🔄 Test {num_operations} opérations concurrentes: {operation_type}")
        
        # Créer portfolios pour test
        portfolios = []
        for i in range(min(10, num_operations)):  # Max 10 portfolios partagés
            portfolio = create_test_portfolio(initial_capital=Decimal("500000.00"))
            
            # Ajouter positions
            for j in range(20):
                position = Position(
                    symbol=f"CONC{i:02d}_{j:02d}",
                    quantity=random.randint(10, 100),
                    average_price=Decimal(str(random.uniform(50, 200))),
                    current_price=Decimal(str(random.uniform(45, 210))),
                    last_updated=datetime.now()
                )
                portfolio.positions.append(position)
            
            portfolios.append(portfolio)
        
        async def single_operation(operation_id: int) -> Dict[str, Any]:
            """Une opération concurrente"""
            start_time = time.perf_counter()
            
            try:
                portfolio = random.choice(portfolios)
                
                if operation_type == "read_only":
                    # Opérations lecture seule (should be thread-safe)
                    result = await self.components["portfolio_manager"].calculate_value(portfolio)
                    
                elif operation_type == "analysis":
                    # Analyses (should be thread-safe)
                    result = await self.components["portfolio_manager"].analyze_portfolio(portfolio)
                    
                elif operation_type == "risk_calculation":
                    # Calculs de risque
                    result = await self.components["portfolio_manager"].calculate_risk_metrics(portfolio)
                    
                elif operation_type == "concurrent_modification":
                    # Modifications concurrentes (test race conditions)
                    with self.lock:
                        current_cash = float(portfolio.cash)
                        
                        # Simulation temps traitement
                        await asyncio.sleep(0.001)
                        
                        # Modification
                        portfolio.cash = Decimal(str(current_cash * 1.01))
                        
                        # Vérifier cohérence
                        if portfolio.id not in self.shared_state:
                            self.shared_state[portfolio.id] = 0
                        self.shared_state[portfolio.id] += 1
                    
                    result = portfolio.cash
                
                else:
                    raise ValueError(f"Type d'opération inconnu: {operation_type}")
                
                end_time = time.perf_counter()
                duration = (end_time - start_time) * 1000
                
                return {
                    "operation_id": operation_id,
                    "success": True,
                    "duration": duration,
                    "result": result
                }
                
            except Exception as e:
                end_time = time.perf_counter()
                duration = (end_time - start_time) * 1000
                
                # Détecter types d'erreurs
                if "deadlock" in str(e).lower():
                    self.deadlock_counter += 1
                elif "race" in str(e).lower() or "concurrent" in str(e).lower():
                    self.race_condition_counter += 1
                
                return {
                    "operation_id": operation_id,
                    "success": False,
                    "duration": duration,
                    "error": str(e)
                }
        
        # Lancer opérations concurrentes
        start_time = time.perf_counter()
        
        tasks = [single_operation(i) for i in range(num_operations)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.perf_counter()
        
        # Analyser résultats
        successful_results = [r for r in results if not isinstance(r, Exception) and r.get("success", False)]
        failed_results = [r for r in results if isinstance(r, Exception) or not r.get("success", True)]
        
        total_time = (end_time - start_time) * 1000
        success_rate = len(successful_results) / num_operations
        operations_per_second = len(successful_results) / (total_time / 1000) if total_time > 0 else 0
        
        # Score thread safety
        thread_safety_score = 1.0 - (self.race_condition_counter + self.deadlock_counter) / num_operations
        
        # Efficacité scalabilité (estimation)
        expected_parallel_efficiency = 0.8  # 80% idéal
        actual_efficiency = operations_per_second / (num_operations / (total_time / 1000)) if total_time > 0 else 0
        scalability_efficiency = min(1.0, actual_efficiency / expected_parallel_efficiency)
        
        return ConcurrencyTestResult(
            test_name=f"concurrent_{operation_type}",
            concurrent_operations=num_operations,
            execution_time_ms=total_time,
            operations_per_second=operations_per_second,
            success_rate=success_rate,
            race_conditions_detected=self.race_condition_counter,
            deadlocks_detected=self.deadlock_counter,
            thread_safety_score=thread_safety_score,
            scalability_efficiency=scalability_efficiency
        )
    
    def measure_parallelism_efficiency(self, operation_func: Callable,
                                     input_data: List[Any],
                                     max_workers: int = None) -> ParallelismMetrics:
        """Mesure l'efficacité du parallélisme"""
        if max_workers is None:
            max_workers = multiprocessing.cpu_count()
        
        print(f"   📊 Analyse parallélisme avec {len(input_data)} tâches")
        
        # Test séquentiel
        sequential_start = time.perf_counter()
        sequential_results = []
        
        for data in input_data:
            try:
                result = operation_func(data)
                sequential_results.append(result)
            except Exception as e:
                sequential_results.append(f"Error: {e}")
        
        sequential_end = time.perf_counter()
        sequential_time = (sequential_end - sequential_start) * 1000
        
        print(f"      Séquentiel: {sequential_time:.1f}ms")
        
        # Test parallèle avec différents nombres de workers
        worker_results = {}
        
        for num_workers in [2, 4, max_workers]:
            parallel_start = time.perf_counter()
            
            with ThreadPoolExecutor(max_workers=num_workers) as executor:
                parallel_futures = [executor.submit(operation_func, data) for data in input_data]
                parallel_results = []
                
                for future in as_completed(parallel_futures):
                    try:
                        result = future.result()
                        parallel_results.append(result)
                    except Exception as e:
                        parallel_results.append(f"Error: {e}")
            
            parallel_end = time.perf_counter()
            parallel_time = (parallel_end - parallel_start) * 1000
            
            speedup = sequential_time / parallel_time if parallel_time > 0 else 0
            efficiency = speedup / num_workers
            overhead = ((parallel_time - sequential_time / num_workers) / sequential_time) * 100 if sequential_time > 0 else 0
            
            worker_results[num_workers] = {
                "parallel_time": parallel_time,
                "speedup": speedup,
                "efficiency": efficiency,
                "overhead": overhead
            }
            
            print(f"      {num_workers:2d} workers: {parallel_time:6.1f}ms, "
                  f"speedup {speedup:.2f}x, "
                  f"efficacité {efficiency:.2f}")
        
        # Trouver configuration optimale
        best_worker_config = max(worker_results.items(), 
                               key=lambda x: x[1]["efficiency"])
        optimal_workers = best_worker_config[0]
        best_metrics = best_worker_config[1]
        
        return ParallelismMetrics(
            sequential_time_ms=sequential_time,
            parallel_time_ms=best_metrics["parallel_time"],
            speedup_factor=best_metrics["speedup"],
            efficiency=best_metrics["efficiency"],
            overhead_percentage=best_metrics["overhead"],
            optimal_thread_count=optimal_workers
        )


@pytest.mark.performance
@pytest.mark.concurrent
class TestBasicConcurrency:
    """Tests de concurrence de base"""
    
    @pytest.fixture
    async def concurrency_test_components(self, test_config):
        """Composants pour tests de concurrence"""
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
    async def test_concurrent_read_operations(self, concurrency_test_components):
        """Test opérations lecture concurrentes"""
        tester = ConcurrencyTester(concurrency_test_components)
        
        print("📖 Test opérations lecture concurrentes")
        
        # Test différents niveaux de concurrence pour lectures
        concurrency_levels = [5, 10, 20, 50]
        read_results = {}
        
        for level in concurrency_levels:
            result = await tester.concurrent_portfolio_operations(
                num_operations=level,
                operation_type="read_only"
            )
            
            read_results[level] = result
            
            print(f"   {level:2d} concurrent: {result.operations_per_second:6.1f} ops/s, "
                  f"succès {result.success_rate:.1%}, "
                  f"thread safety {result.thread_safety_score:.2f}")
        
        # Analyser scaling des lectures
        baseline_throughput = read_results[5].operations_per_second
        
        print(f"\n📊 Scaling opérations lecture:")
        for level, result in read_results.items():
            scaling_factor = result.operations_per_second / baseline_throughput
            expected_scaling = level / 5  # Idéalement linéaire
            efficiency = scaling_factor / expected_scaling if expected_scaling > 0 else 0
            
            print(f"   {level:2d}x: Scaling {scaling_factor:.2f}x "
                  f"(attendu {expected_scaling:.1f}x), "
                  f"efficacité {efficiency:.2f}")
        
        # Assertions lectures concurrentes
        for result in read_results.values():
            assert result.success_rate >= 0.95  # 95% succès minimum
            assert result.race_conditions_detected == 0  # Pas de race conditions
            assert result.thread_safety_score >= 0.95  # Thread safety élevé
        
        return read_results
    
    @pytest.mark.asyncio
    async def test_concurrent_analysis_operations(self, concurrency_test_components):
        """Test analyses concurrentes"""
        tester = ConcurrencyTester(concurrency_test_components)
        
        print("🔍 Test analyses concurrentes")
        
        # Test analyses complexes concurrentes
        analysis_levels = [3, 5, 10, 15]
        analysis_results = {}
        
        for level in analysis_levels:
            result = await tester.concurrent_portfolio_operations(
                num_operations=level,
                operation_type="analysis"
            )
            
            analysis_results[level] = result
            
            print(f"   {level:2d} analyses: {result.operations_per_second:5.2f} ops/s, "
                  f"temps {result.execution_time_ms:6.1f}ms, "
                  f"succès {result.success_rate:.1%}")
        
        # Test analyses + calculs de risque mélangés
        mixed_result = await asyncio.gather(
            tester.concurrent_portfolio_operations(5, "analysis"),
            tester.concurrent_portfolio_operations(5, "risk_calculation"),
            return_exceptions=True
        )
        
        print(f"\n📊 Tests mixtes:")
        for i, result in enumerate(mixed_result):
            if not isinstance(result, Exception):
                operation_type = "analyses" if i == 0 else "risques"
                print(f"   {operation_type}: {result.operations_per_second:.2f} ops/s")
        
        # Assertions analyses
        for result in analysis_results.values():
            assert result.success_rate >= 0.90  # 90% succès pour analyses
            assert result.thread_safety_score >= 0.90  # Thread safety bon
        
        return {
            "analysis_results": analysis_results,
            "mixed_results": mixed_result
        }
    
    @pytest.mark.asyncio
    async def test_race_condition_detection(self, concurrency_test_components):
        """Test détection de race conditions"""
        tester = ConcurrencyTester(concurrency_test_components)
        
        print("⚡ Test détection race conditions")
        
        # Test modifications concurrentes (potentielles race conditions)
        race_condition_levels = [5, 10, 20]
        race_results = {}
        
        for level in race_condition_levels:
            result = await tester.concurrent_portfolio_operations(
                num_operations=level,
                operation_type="concurrent_modification"
            )
            
            race_results[level] = result
            
            print(f"   {level:2d} modifications: succès {result.success_rate:.1%}, "
                  f"race conditions {result.race_conditions_detected}, "
                  f"safety score {result.thread_safety_score:.2f}")
        
        # Analyser détection de race conditions
        total_race_conditions = sum(r.race_conditions_detected for r in race_results.values())
        total_operations = sum(r.concurrent_operations for r in race_results.values())
        
        race_condition_rate = total_race_conditions / total_operations if total_operations > 0 else 0
        
        print(f"\n📊 Analyse race conditions:")
        print(f"   Total opérations: {total_operations}")
        print(f"   Race conditions détectées: {total_race_conditions}")
        print(f"   Taux race conditions: {race_condition_rate:.3f}")
        
        # Vérifier que les protections fonctionnent
        # (avec les locks, on ne devrait pas avoir de race conditions)
        assert total_race_conditions <= total_operations * 0.05  # Max 5% de race conditions
        
        return {
            "race_results": race_results,
            "total_race_conditions": total_race_conditions,
            "race_condition_rate": race_condition_rate
        }


@pytest.mark.performance
@pytest.mark.concurrent
@pytest.mark.slow
class TestParallelismEfficiency:
    """Tests d'efficacité du parallélisme"""
    
    @pytest.mark.asyncio
    async def test_cpu_intensive_parallelism(self, concurrency_test_components):
        """Test parallélisme pour tâches CPU-intensives"""
        tester = ConcurrencyTester(concurrency_test_components)
        
        print("⚙️  Test parallélisme CPU-intensif")
        
        # Fonction CPU-intensive simulée (calculs financiers)
        def cpu_intensive_calculation(portfolio_data: Dict[str, Any]) -> Dict[str, float]:
            """Simulation calcul complexe (Monte Carlo simplifié)"""
            num_simulations = 1000
            results = []
            
            initial_value = portfolio_data["value"]
            volatility = portfolio_data["volatility"]
            
            for _ in range(num_simulations):
                # Simulation marche aléatoire
                value = initial_value
                for day in range(30):  # 30 jours
                    daily_change = random.gauss(0, volatility / math.sqrt(252))
                    value *= (1 + daily_change)
                results.append(value)
            
            return {
                "final_value": statistics.mean(results),
                "var_95": sorted(results)[int(0.05 * len(results))],
                "volatility": statistics.stdev(results) / initial_value
            }
        
        # Générer données test
        portfolio_data_list = []
        for i in range(20):
            portfolio_data_list.append({
                "portfolio_id": i,
                "value": random.uniform(500000, 2000000),
                "volatility": random.uniform(0.15, 0.35)
            })
        
        # Mesurer efficacité parallélisme
        parallelism_metrics = tester.measure_parallelism_efficiency(
            operation_func=cpu_intensive_calculation,
            input_data=portfolio_data_list,
            max_workers=8
        )
        
        print(f"\n📊 Efficacité parallélisme CPU:")
        print(f"   Temps séquentiel: {parallelism_metrics.sequential_time_ms:.1f}ms")
        print(f"   Temps parallèle: {parallelism_metrics.parallel_time_ms:.1f}ms")
        print(f"   Speedup: {parallelism_metrics.speedup_factor:.2f}x")
        print(f"   Efficacité: {parallelism_metrics.efficiency:.2f}")
        print(f"   Overhead: {parallelism_metrics.overhead_percentage:.1f}%")
        print(f"   Workers optimaux: {parallelism_metrics.optimal_thread_count}")
        
        # Assertions parallélisme CPU
        assert parallelism_metrics.speedup_factor > 1.5  # Au moins 1.5x speedup
        assert parallelism_metrics.efficiency > 0.4  # Au moins 40% d'efficacité
        assert parallelism_metrics.overhead_percentage < 50.0  # Overhead < 50%
        
        return parallelism_metrics
    
    @pytest.mark.asyncio
    async def test_io_intensive_parallelism(self, concurrency_test_components):
        """Test parallélisme pour tâches I/O-intensives"""
        tester = ConcurrencyTester(concurrency_test_components)
        
        print("💾 Test parallélisme I/O-intensif")
        
        # Simulation opération I/O (requête API)
        async def io_intensive_operation(symbol_data: Dict[str, Any]) -> Dict[str, Any]:
            """Simulation requête API avec latence"""
            symbol = symbol_data["symbol"]
            
            # Simulation latence réseau
            await asyncio.sleep(random.uniform(0.01, 0.05))  # 10-50ms
            
            # Simulation traitement données
            market_data = {
                "symbol": symbol,
                "price": random.uniform(50, 300),
                "volume": random.randint(1000000, 50000000),
                "timestamp": time.time()
            }
            
            # Simulation analyse
            await asyncio.sleep(random.uniform(0.001, 0.005))  # 1-5ms
            
            return {
                "symbol": symbol,
                "analysis": market_data,
                "recommendation": random.choice(["BUY", "SELL", "HOLD"])
            }
        
        # Test avec différents niveaux de concurrence async
        symbols = [{"symbol": f"STOCK{i:03d}"} for i in range(50)]
        concurrency_levels = [1, 5, 10, 20, 30]
        
        async_results = {}
        
        for concurrency in concurrency_levels:
            print(f"   Test {concurrency} requêtes concurrentes")
            
            # Limiter concurrence
            semaphore = asyncio.Semaphore(concurrency)
            
            async def limited_operation(symbol_data):
                async with semaphore:
                    return await io_intensive_operation(symbol_data)
            
            start_time = time.perf_counter()
            
            tasks = [limited_operation(symbol) for symbol in symbols[:30]]  # 30 symboles
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            end_time = time.perf_counter()
            
            successful = [r for r in results if not isinstance(r, Exception)]
            total_time = (end_time - start_time) * 1000
            throughput = len(successful) / (total_time / 1000)
            
            async_results[concurrency] = {
                "execution_time": total_time,
                "throughput": throughput,
                "success_rate": len(successful) / len(tasks)
            }
            
            print(f"      Temps: {total_time:6.1f}ms, "
                  f"Débit: {throughput:5.1f} ops/s")
        
        # Analyser efficacité async
        sequential_time = async_results[1]["execution_time"]
        best_async = max(async_results.values(), key=lambda x: x["throughput"])
        
        async_speedup = sequential_time / best_async["execution_time"]
        async_efficiency = best_async["throughput"] / async_results[1]["throughput"]
        
        print(f"\n📊 Efficacité parallélisme I/O:")
        print(f"   Speedup async: {async_speedup:.2f}x")
        print(f"   Amélioration débit: {async_efficiency:.2f}x")
        print(f"   Meilleur débit: {best_async['throughput']:.1f} ops/s")
        
        # Assertions I/O parallélisme
        assert async_speedup > 3.0  # Au moins 3x speedup pour I/O
        assert best_async["success_rate"] >= 0.95  # 95% succès
        assert async_efficiency > 5.0  # Au moins 5x amélioration débit
        
        return {
            "async_results": async_results,
            "async_speedup": async_speedup,
            "async_efficiency": async_efficiency
        }


@pytest.mark.performance
@pytest.mark.concurrent
@pytest.mark.slowest
class TestAdvancedConcurrency:
    """Tests de concurrence avancés"""
    
    @pytest.mark.asyncio
    async def test_mixed_workload_concurrency(self, concurrency_test_components):
        """Test concurrence charge mixte CPU+I/O"""
        tester = ConcurrencyTester(concurrency_test_components)
        
        print("🔀 Test concurrence charge mixte")
        
        # Simulation charge mixte réaliste
        async def mixed_workload_simulation(duration_seconds: int = 10):
            """Simulation charge mixte pendant durée donnée"""
            
            results = {
                "portfolio_analyses": 0,
                "api_calls": 0,
                "risk_calculations": 0,
                "strategy_evaluations": 0,
                "errors": 0
            }
            
            start_time = time.perf_counter()
            end_time = start_time + duration_seconds
            
            # Tâches concurrentes différents types
            active_tasks = []
            
            while time.perf_counter() < end_time:
                # Nettoyer tâches terminées
                active_tasks = [task for task in active_tasks if not task.done()]
                
                # Limiter nombre tâches actives
                if len(active_tasks) < 20:
                    # Choisir type opération aléatoirement
                    operation_type = random.choices(
                        ["portfolio", "api", "risk", "strategy"],
                        weights=[0.3, 0.4, 0.2, 0.1]  # Distribution réaliste
                    )[0]
                    
                    if operation_type == "portfolio":
                        task = asyncio.create_task(self._portfolio_analysis_task())
                        task.add_done_callback(lambda t: self._update_result(results, "portfolio_analyses", t))
                    
                    elif operation_type == "api":
                        task = asyncio.create_task(self._api_call_task())
                        task.add_done_callback(lambda t: self._update_result(results, "api_calls", t))
                    
                    elif operation_type == "risk":
                        task = asyncio.create_task(self._risk_calculation_task())
                        task.add_done_callback(lambda t: self._update_result(results, "risk_calculations", t))
                    
                    elif operation_type == "strategy":
                        task = asyncio.create_task(self._strategy_evaluation_task())
                        task.add_done_callback(lambda t: self._update_result(results, "strategy_evaluations", t))
                    
                    active_tasks.append(task)
                
                # Petite pause pour éviter surcharge
                await asyncio.sleep(0.01)
            
            # Attendre toutes les tâches restantes
            if active_tasks:
                await asyncio.gather(*active_tasks, return_exceptions=True)
            
            actual_duration = time.perf_counter() - start_time
            
            return {
                "duration": actual_duration,
                "results": results,
                "total_operations": sum(results.values()),
                "operations_per_second": sum(results.values()) / actual_duration
            }
        
        # Helper methods pour différents types de tâches
        async def _portfolio_analysis_task(self):
            portfolio = create_test_portfolio(initial_capital=Decimal("200000.00"))
            return await concurrency_test_components["portfolio_manager"].analyze_portfolio(portfolio)
        
        async def _api_call_task(self):
            await asyncio.sleep(random.uniform(0.02, 0.1))  # Simulation latence API
            return {"data": "api_response"}
        
        async def _risk_calculation_task(self):
            portfolio = create_test_portfolio(initial_capital=Decimal("300000.00"))
            return await concurrency_test_components["portfolio_manager"].calculate_risk_metrics(portfolio)
        
        async def _strategy_evaluation_task(self):
            strategy = create_test_strategy("momentum")
            market_data = {"symbol": "TEST", "price": 150.0}
            return await concurrency_test_components["strategy_engine"].evaluate_symbol(
                "TEST", market_data, {"RSI": 50}, strategy
            )
        
        def _update_result(self, results, key, task):
            try:
                task.result()  # Vérifier si tâche réussie
                results[key] += 1
            except Exception:
                results["errors"] += 1
        
        # Ajouter les méthodes à l'instance
        self._portfolio_analysis_task = _portfolio_analysis_task
        self._api_call_task = _api_call_task  
        self._risk_calculation_task = _risk_calculation_task
        self._strategy_evaluation_task = _strategy_evaluation_task
        self._update_result = _update_result
        
        # Exécuter simulation
        print(f"   Simulation 10 secondes charge mixte...")
        
        mixed_results = await mixed_workload_simulation(duration_seconds=10)
        
        print(f"\n📊 Résultats charge mixte:")
        print(f"   Durée: {mixed_results['duration']:.1f}s")
        print(f"   Opérations totales: {mixed_results['total_operations']}")
        print(f"   Débit global: {mixed_results['operations_per_second']:.1f} ops/s")
        
        for operation_type, count in mixed_results["results"].items():
            percentage = (count / mixed_results['total_operations']) * 100 if mixed_results['total_operations'] > 0 else 0
            print(f"   {operation_type:20s}: {count:3d} ({percentage:5.1f}%)")
        
        # Assertions charge mixte
        assert mixed_results["total_operations"] >= 50  # Au moins 50 opérations
        assert mixed_results["results"]["errors"] / mixed_results["total_operations"] <= 0.05  # Max 5% erreurs
        assert mixed_results["operations_per_second"] >= 5.0  # Au moins 5 ops/s
        
        return mixed_results


if __name__ == "__main__":
    # Exécution directe pour tests de développement
    pytest.main([__file__, "-v", "--tb=short", "-m", "concurrent and not slowest"])