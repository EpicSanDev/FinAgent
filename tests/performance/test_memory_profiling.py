"""
Tests de Performance - Profiling Mémoire

Ces tests analysent l'utilisation mémoire du système FinAgent,
détectent les fuites de mémoire, mesurent les allocations
et optimisent la gestion des ressources.
"""

import pytest
import asyncio
import time
import gc
import tracemalloc
import psutil
import sys
import threading
from decimal import Decimal
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import weakref
import random

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
class MemorySnapshot:
    """Instantané mémoire"""
    timestamp: float
    rss_mb: float  # Resident Set Size
    vms_mb: float  # Virtual Memory Size
    heap_mb: float  # Heap Python
    objects_count: int
    gc_stats: Dict[str, int]
    tracemalloc_stats: Optional[Dict[str, Any]] = None


@dataclass
class MemoryLeakResult:
    """Résultat de détection de fuite mémoire"""
    test_name: str
    iterations: int
    initial_memory: float
    final_memory: float
    peak_memory: float
    memory_growth: float
    growth_rate_mb_per_iteration: float
    leak_detected: bool
    gc_collections: int
    objects_not_freed: int


class MemoryProfiler:
    """Profiler mémoire pour les tests"""
    
    def __init__(self):
        self.snapshots: List[MemorySnapshot] = []
        self.tracemalloc_enabled = False
        self.baseline_memory = None
        
    def start_profiling(self, with_tracemalloc: bool = False):
        """Démarre le profiling mémoire"""
        if with_tracemalloc:
            tracemalloc.start()
            self.tracemalloc_enabled = True
        
        gc.collect()  # Nettoyage initial
        self.baseline_memory = self.take_snapshot()
        
    def stop_profiling(self):
        """Arrête le profiling mémoire"""
        if self.tracemalloc_enabled:
            tracemalloc.stop()
            self.tracemalloc_enabled = False
    
    def take_snapshot(self, label: str = "") -> MemorySnapshot:
        """Prend un instantané mémoire"""
        process = psutil.Process()
        memory_info = process.memory_info()
        
        # Statistiques objets Python
        objects_count = len(gc.get_objects())
        gc_stats = {
            f"generation_{i}": len(gc.get_stats()[i])
            for i in range(len(gc.get_stats()))
        }
        
        # Statistiques tracemalloc si activé
        tracemalloc_stats = None
        if self.tracemalloc_enabled:
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc_stats = {
                "current_mb": current / (1024 * 1024),
                "peak_mb": peak / (1024 * 1024),
                "trace_count": len(tracemalloc.get_traceback_limit())
            }
        
        snapshot = MemorySnapshot(
            timestamp=time.perf_counter(),
            rss_mb=memory_info.rss / (1024 * 1024),
            vms_mb=memory_info.vms / (1024 * 1024),
            heap_mb=tracemalloc_stats["current_mb"] if tracemalloc_stats else 0,
            objects_count=objects_count,
            gc_stats=gc_stats,
            tracemalloc_stats=tracemalloc_stats
        )
        
        self.snapshots.append(snapshot)
        return snapshot
    
    def analyze_memory_growth(self, window_size: int = 10) -> Dict[str, float]:
        """Analyse la croissance mémoire"""
        if len(self.snapshots) < window_size:
            return {"growth_rate": 0.0, "trend": "insufficient_data"}
        
        recent_snapshots = self.snapshots[-window_size:]
        
        # Calcul de la tendance
        memory_values = [s.rss_mb for s in recent_snapshots]
        time_values = [s.timestamp for s in recent_snapshots]
        
        # Régression linéaire simple
        n = len(memory_values)
        sum_x = sum(time_values)
        sum_y = sum(memory_values)
        sum_xy = sum(x * y for x, y in zip(time_values, memory_values))
        sum_x2 = sum(x * x for x in time_values)
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        
        return {
            "growth_rate": slope,  # MB/seconde
            "trend": "increasing" if slope > 0.1 else "stable" if slope > -0.1 else "decreasing",
            "current_memory": recent_snapshots[-1].rss_mb,
            "baseline_memory": self.baseline_memory.rss_mb if self.baseline_memory else 0
        }
    
    def detect_memory_leaks(self, tolerance_mb: float = 50.0) -> bool:
        """Détecte les fuites de mémoire"""
        if len(self.snapshots) < 2:
            return False
        
        initial = self.snapshots[0]
        final = self.snapshots[-1]
        
        # Force garbage collection
        gc.collect()
        current_snapshot = self.take_snapshot()
        
        memory_growth = current_snapshot.rss_mb - initial.rss_mb
        return memory_growth > tolerance_mb


@pytest.mark.performance
@pytest.mark.memory
class TestBasicMemoryProfiling:
    """Tests de profiling mémoire de base"""
    
    @pytest.fixture
    async def memory_test_components(self, test_config):
        """Composants pour tests mémoire"""
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
    async def test_memory_baseline_operations(self, memory_test_components):
        """Test baseline utilisation mémoire opérations standard"""
        profiler = MemoryProfiler()
        profiler.start_profiling(with_tracemalloc=True)
        
        print("📏 Test baseline mémoire opérations standard")
        
        operations = [
            "create_portfolio",
            "analyze_portfolio", 
            "calculate_risks",
            "evaluate_strategy",
            "generate_decision"
        ]
        
        operation_memory = {}
        
        for operation in operations:
            gc.collect()
            before_snapshot = profiler.take_snapshot()
            
            if operation == "create_portfolio":
                portfolio = create_test_portfolio(initial_capital=Decimal("100000.00"))
                # Ajouter quelques positions
                for i in range(10):
                    position = Position(
                        symbol=f"TEST{i:02d}",
                        quantity=random.randint(10, 100),
                        average_price=Decimal(str(random.uniform(50, 200))),
                        current_price=Decimal(str(random.uniform(45, 210))),
                        last_updated=datetime.now()
                    )
                    portfolio.positions.append(position)
            
            elif operation == "analyze_portfolio":
                await memory_test_components["portfolio_manager"].analyze_portfolio(portfolio)
            
            elif operation == "calculate_risks":
                await memory_test_components["portfolio_manager"].calculate_risk_metrics(portfolio)
            
            elif operation == "evaluate_strategy":
                strategy = create_test_strategy("momentum")
                market_data = await memory_test_components["openbb"].get_current_price("AAPL")
                await memory_test_components["strategy_engine"].evaluate_symbol(
                    symbol="AAPL",
                    market_data=market_data,
                    technical_indicators={"RSI": 50},
                    strategy_config=strategy
                )
            
            elif operation == "generate_decision":
                decision = InvestmentDecision(
                    symbol="TEST",
                    decision_type=DecisionType.BUY,
                    quantity=100,
                    target_price=Decimal("150.00"),
                    confidence=Decimal("0.8"),
                    reasoning="Test decision",
                    created_at=datetime.now()
                )
                await memory_test_components["portfolio_manager"].can_execute_decision(
                    decision=decision,
                    portfolio=portfolio
                )
            
            after_snapshot = profiler.take_snapshot()
            memory_used = after_snapshot.rss_mb - before_snapshot.rss_mb
            
            operation_memory[operation] = {
                "memory_used_mb": memory_used,
                "objects_created": after_snapshot.objects_count - before_snapshot.objects_count,
                "heap_growth_mb": (after_snapshot.heap_mb - before_snapshot.heap_mb) if after_snapshot.heap_mb and before_snapshot.heap_mb else 0
            }
            
            print(f"   {operation:20s}: {memory_used:6.1f} MB, "
                  f"{operation_memory[operation]['objects_created']:4d} objets")
        
        # Analyse baseline
        total_memory = sum(op["memory_used_mb"] for op in operation_memory.values())
        max_memory_op = max(operation_memory.items(), key=lambda x: x[1]["memory_used_mb"])
        
        print(f"\n📊 Résumé baseline mémoire:")
        print(f"   Mémoire totale utilisée: {total_memory:.1f} MB")
        print(f"   Opération la plus coûteuse: {max_memory_op[0]} ({max_memory_op[1]['memory_used_mb']:.1f} MB)")
        
        profiler.stop_profiling()
        
        # Assertions baseline
        assert total_memory < 100.0  # Moins de 100MB pour toutes les opérations
        assert max_memory_op[1]["memory_used_mb"] < 50.0  # Aucune opération > 50MB
        
        return operation_memory
    
    @pytest.mark.asyncio
    async def test_memory_portfolio_scaling(self, memory_test_components):
        """Test scaling mémoire avec taille de portefeuille"""
        profiler = MemoryProfiler()
        profiler.start_profiling(with_tracemalloc=True)
        
        print("📈 Test scaling mémoire vs taille portefeuille")
        
        portfolio_sizes = [10, 50, 100, 250, 500, 1000]
        scaling_results = {}
        
        for size in portfolio_sizes:
            gc.collect()
            before_snapshot = profiler.take_snapshot()
            
            # Créer portefeuille de taille spécifique
            portfolio = create_test_portfolio(initial_capital=Decimal("1000000.00"))
            
            for i in range(size):
                position = Position(
                    symbol=f"SCALE{i:04d}",
                    quantity=random.randint(10, 1000),
                    average_price=Decimal(str(random.uniform(10, 500))),
                    current_price=Decimal(str(random.uniform(8, 520))),
                    last_updated=datetime.now()
                )
                portfolio.positions.append(position)
            
            # Analyser le portefeuille
            start_time = time.perf_counter()
            await memory_test_components["portfolio_manager"].analyze_portfolio(portfolio)
            end_time = time.perf_counter()
            
            after_snapshot = profiler.take_snapshot()
            
            memory_used = after_snapshot.rss_mb - before_snapshot.rss_mb
            analysis_time = (end_time - start_time) * 1000
            
            scaling_results[size] = {
                "memory_mb": memory_used,
                "analysis_time_ms": analysis_time,
                "memory_per_position": memory_used / size,
                "objects_count": after_snapshot.objects_count - before_snapshot.objects_count
            }
            
            print(f"   {size:4d} positions: {memory_used:6.1f} MB "
                  f"({scaling_results[size]['memory_per_position']:.3f} MB/pos), "
                  f"{analysis_time:6.1f}ms")
            
            # Nettoyer pour mesure suivante
            del portfolio
            gc.collect()
        
        # Analyser scaling
        memory_values = [r["memory_mb"] for r in scaling_results.values()]
        size_values = list(portfolio_sizes)
        
        # Vérifier linéarité approximative
        memory_growth_ratio = memory_values[-1] / memory_values[0]
        size_growth_ratio = size_values[-1] / size_values[0]
        
        linearity_factor = memory_growth_ratio / size_growth_ratio
        
        print(f"\n📊 Analyse scaling mémoire:")
        print(f"   Croissance mémoire: {memory_growth_ratio:.1f}x")
        print(f"   Croissance taille: {size_growth_ratio:.1f}x")
        print(f"   Facteur linéarité: {linearity_factor:.2f}")
        print(f"   Mémoire par position (1000): {scaling_results[1000]['memory_per_position']:.3f} MB")
        
        profiler.stop_profiling()
        
        # Assertions scaling
        assert linearity_factor < 2.0  # Croissance pas plus du double de linéaire
        assert scaling_results[1000]["memory_per_position"] < 0.1  # Moins de 100KB par position
        assert max(memory_values) < 200.0  # Moins de 200MB même pour 1000 positions
        
        return scaling_results


@pytest.mark.performance
@pytest.mark.memory
@pytest.mark.slow
class TestMemoryLeakDetection:
    """Tests de détection de fuites mémoire"""
    
    @pytest.mark.asyncio
    async def test_portfolio_operations_leak_detection(self, memory_test_components):
        """Test détection fuites - opérations répétées sur portfolios"""
        profiler = MemoryProfiler()
        profiler.start_profiling(with_tracemalloc=True)
        
        print("🔍 Test détection fuites - opérations portfolios")
        
        iterations = 100
        leak_results = []
        
        initial_snapshot = profiler.take_snapshot()
        print(f"   Mémoire initiale: {initial_snapshot.rss_mb:.1f} MB")
        
        for i in range(iterations):
            # Créer et traiter un portefeuille
            portfolio = create_test_portfolio(initial_capital=Decimal("500000.00"))
            
            # Ajouter positions aléatoirement
            num_positions = random.randint(20, 50)
            for j in range(num_positions):
                position = Position(
                    symbol=f"LEAK{i:03d}_{j:02d}",
                    quantity=random.randint(10, 100),
                    average_price=Decimal(str(random.uniform(50, 200))),
                    current_price=Decimal(str(random.uniform(45, 210))),
                    last_updated=datetime.now()
                )
                portfolio.positions.append(position)
            
            # Opérations sur le portefeuille
            await memory_test_components["portfolio_manager"].analyze_portfolio(portfolio)
            await memory_test_components["portfolio_manager"].calculate_risk_metrics(portfolio)
            await memory_test_components["portfolio_manager"].calculate_value(portfolio)
            
            # Nettoyer explicitement
            del portfolio
            
            # Mesurer mémoire périodiquement
            if i % 20 == 0:
                gc.collect()
                current_snapshot = profiler.take_snapshot()
                
                memory_growth = current_snapshot.rss_mb - initial_snapshot.rss_mb
                growth_rate = memory_growth / (i + 1)
                
                leak_results.append({
                    "iteration": i,
                    "memory_mb": current_snapshot.rss_mb,
                    "growth_mb": memory_growth,
                    "growth_rate": growth_rate,
                    "objects_count": current_snapshot.objects_count
                })
                
                print(f"   Iteration {i:3d}: {current_snapshot.rss_mb:6.1f} MB "
                      f"(+{memory_growth:5.1f} MB, {growth_rate:.3f} MB/iter)")
        
        # Nettoyage final et mesure
        gc.collect()
        final_snapshot = profiler.take_snapshot()
        
        total_growth = final_snapshot.rss_mb - initial_snapshot.rss_mb
        avg_growth_rate = total_growth / iterations
        
        # Analyse de fuite
        leak_detected = profiler.detect_memory_leaks(tolerance_mb=20.0)
        
        result = MemoryLeakResult(
            test_name="portfolio_operations",
            iterations=iterations,
            initial_memory=initial_snapshot.rss_mb,
            final_memory=final_snapshot.rss_mb,
            peak_memory=max(r["memory_mb"] for r in leak_results),
            memory_growth=total_growth,
            growth_rate_mb_per_iteration=avg_growth_rate,
            leak_detected=leak_detected,
            gc_collections=len([r for r in leak_results if r["iteration"] % 20 == 0]),
            objects_not_freed=final_snapshot.objects_count - initial_snapshot.objects_count
        )
        
        print(f"\n📊 Résultats détection fuites:")
        print(f"   Croissance totale: {result.memory_growth:.1f} MB")
        print(f"   Taux croissance: {result.growth_rate_mb_per_iteration:.3f} MB/iter")
        print(f"   Pic mémoire: {result.peak_memory:.1f} MB")
        print(f"   Fuite détectée: {'OUI' if result.leak_detected else 'NON'}")
        print(f"   Objets non libérés: {result.objects_not_freed}")
        
        profiler.stop_profiling()
        
        # Assertions fuites
        assert result.growth_rate_mb_per_iteration < 0.5  # Moins de 500KB par itération
        assert not result.leak_detected  # Pas de fuite majeure détectée
        assert result.memory_growth < 50.0  # Moins de 50MB de croissance totale
        
        return result
    
    @pytest.mark.asyncio
    async def test_strategy_engine_leak_detection(self, memory_test_components):
        """Test détection fuites - moteur de stratégies"""
        profiler = MemoryProfiler()
        profiler.start_profiling(with_tracemalloc=True)
        
        print("🎯 Test détection fuites - moteur stratégies")
        
        iterations = 200
        strategies = ["momentum", "mean_reversion", "breakout", "balanced"]
        symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "NVDA"]
        
        initial_snapshot = profiler.take_snapshot()
        leak_measurements = []
        
        for i in range(iterations):
            # Sélection aléatoire
            strategy_type = random.choice(strategies)
            symbol = random.choice(symbols)
            
            # Créer stratégie et données
            strategy = create_test_strategy(strategy_type)
            market_data = await memory_test_components["openbb"].get_current_price(symbol)
            
            # Indicateurs techniques aléatoirement
            technical_indicators = {
                "RSI": random.uniform(20, 80),
                "MA_20": random.uniform(100, 200),
                "MA_50": random.uniform(90, 210),
                "MACD": random.uniform(-5, 5),
                "Volume": random.randint(1000000, 10000000)
            }
            
            # Évaluer stratégie
            await memory_test_components["strategy_engine"].evaluate_symbol(
                symbol=symbol,
                market_data=market_data,
                technical_indicators=technical_indicators,
                strategy_config=strategy
            )
            
            # Mesures périodiques
            if i % 50 == 0:
                gc.collect()
                current_snapshot = profiler.take_snapshot()
                
                memory_growth = current_snapshot.rss_mb - initial_snapshot.rss_mb
                
                leak_measurements.append({
                    "iteration": i,
                    "memory_mb": current_snapshot.rss_mb,
                    "growth_mb": memory_growth,
                    "heap_mb": current_snapshot.heap_mb,
                    "objects": current_snapshot.objects_count
                })
                
                print(f"   Iteration {i:3d}: {current_snapshot.rss_mb:6.1f} MB "
                      f"(+{memory_growth:5.1f} MB)")
        
        # Analyse finale
        gc.collect()
        final_snapshot = profiler.take_snapshot()
        
        total_growth = final_snapshot.rss_mb - initial_snapshot.rss_mb
        growth_rate = total_growth / iterations
        
        # Tendance mémoire sur les dernières mesures
        last_measurements = leak_measurements[-3:]
        if len(last_measurements) >= 2:
            memory_trend = (last_measurements[-1]["memory_mb"] - last_measurements[0]["memory_mb"]) / len(last_measurements)
        else:
            memory_trend = 0
        
        print(f"\n📊 Résultats détection fuites stratégies:")
        print(f"   Itérations: {iterations}")
        print(f"   Croissance totale: {total_growth:.1f} MB")
        print(f"   Taux croissance: {growth_rate:.4f} MB/iter")
        print(f"   Tendance récente: {memory_trend:.3f} MB/mesure")
        print(f"   Mémoire finale: {final_snapshot.rss_mb:.1f} MB")
        
        profiler.stop_profiling()
        
        # Assertions
        assert growth_rate < 0.1  # Moins de 100KB par itération
        assert abs(memory_trend) < 2.0  # Tendance stable
        assert total_growth < 30.0  # Moins de 30MB total
        
        return {
            "iterations": iterations,
            "total_growth": total_growth,
            "growth_rate": growth_rate,
            "memory_trend": memory_trend,
            "measurements": leak_measurements
        }


@pytest.mark.performance
@pytest.mark.memory
@pytest.mark.slowest
class TestAdvancedMemoryProfiling:
    """Tests de profiling mémoire avancés"""
    
    @pytest.mark.asyncio
    async def test_concurrent_memory_behavior(self, memory_test_components):
        """Test comportement mémoire sous concurrence"""
        profiler = MemoryProfiler()
        profiler.start_profiling(with_tracemalloc=True)
        
        print("🔀 Test comportement mémoire concurrent")
        
        concurrent_tasks = 20
        operations_per_task = 10
        
        initial_snapshot = profiler.take_snapshot()
        
        async def concurrent_portfolio_operations(task_id: int):
            """Opérations concurrentes sur portfolios"""
            task_memory_usage = []
            
            for i in range(operations_per_task):
                # Créer portefeuille
                portfolio = create_test_portfolio(initial_capital=Decimal("200000.00"))
                
                # Ajouter positions
                for j in range(20):
                    position = Position(
                        symbol=f"CONC{task_id:02d}_{i:02d}_{j:02d}",
                        quantity=random.randint(10, 100),
                        average_price=Decimal(str(random.uniform(50, 200))),
                        current_price=Decimal(str(random.uniform(45, 210))),
                        last_updated=datetime.now()
                    )
                    portfolio.positions.append(position)
                
                # Opérations
                await memory_test_components["portfolio_manager"].analyze_portfolio(portfolio)
                await memory_test_components["portfolio_manager"].calculate_risk_metrics(portfolio)
                
                # Mesurer mémoire locale
                current_memory = psutil.Process().memory_info().rss / (1024 * 1024)
                task_memory_usage.append(current_memory)
                
                del portfolio
            
            return {
                "task_id": task_id,
                "peak_memory": max(task_memory_usage),
                "avg_memory": sum(task_memory_usage) / len(task_memory_usage),
                "operations": operations_per_task
            }
        
        # Lancer tâches concurrentes
        print(f"   Lancement {concurrent_tasks} tâches concurrentes...")
        
        start_time = time.perf_counter()
        task_results = await asyncio.gather(*[
            concurrent_portfolio_operations(i) for i in range(concurrent_tasks)
        ])
        end_time = time.perf_counter()
        
        # Mesure finale
        gc.collect()
        final_snapshot = profiler.take_snapshot()
        
        total_duration = (end_time - start_time) * 1000
        total_operations = concurrent_tasks * operations_per_task
        memory_growth = final_snapshot.rss_mb - initial_snapshot.rss_mb
        
        # Analyse concurrence
        peak_memories = [r["peak_memory"] for r in task_results]
        avg_memories = [r["avg_memory"] for r in task_results]
        
        memory_variance = statistics.variance(peak_memories) if len(peak_memories) > 1 else 0
        
        print(f"\n📊 Résultats mémoire concurrente:")
        print(f"   Tâches: {concurrent_tasks}")
        print(f"   Opérations totales: {total_operations}")
        print(f"   Durée: {total_duration:.1f}ms")
        print(f"   Croissance mémoire: {memory_growth:.1f} MB")
        print(f"   Pic mémoire max: {max(peak_memories):.1f} MB")
        print(f"   Variance mémoire: {memory_variance:.1f}")
        
        profiler.stop_profiling()
        
        # Assertions concurrence
        assert memory_growth < 100.0  # Moins de 100MB de croissance
        assert memory_variance < 500.0  # Variance raisonnable
        assert max(peak_memories) < 800.0  # Pic mémoire contrôlé
        
        return {
            "concurrent_tasks": concurrent_tasks,
            "total_operations": total_operations,
            "memory_growth": memory_growth,
            "peak_memory": max(peak_memories),
            "memory_variance": memory_variance,
            "task_results": task_results
        }
    
    @pytest.mark.asyncio
    async def test_garbage_collection_efficiency(self, memory_test_components):
        """Test efficacité du garbage collection"""
        profiler = MemoryProfiler()
        profiler.start_profiling(with_tracemalloc=True)
        
        print("♻️  Test efficacité garbage collection")
        
        # Phase 1: Allocation massive
        print("   Phase 1: Allocation massive")
        
        allocation_snapshot = profiler.take_snapshot()
        large_objects = []
        
        for i in range(50):
            # Créer gros portfolios
            portfolio = create_test_portfolio(initial_capital=Decimal("10000000.00"))
            
            for j in range(200):  # 200 positions par portfolio
                position = Position(
                    symbol=f"GC{i:02d}_{j:03d}",
                    quantity=random.randint(100, 1000),
                    average_price=Decimal(str(random.uniform(10, 500))),
                    current_price=Decimal(str(random.uniform(8, 520))),
                    last_updated=datetime.now()
                )
                portfolio.positions.append(position)
            
            large_objects.append(portfolio)
        
        peak_allocation_snapshot = profiler.take_snapshot()
        allocation_memory = peak_allocation_snapshot.rss_mb - allocation_snapshot.rss_mb
        
        print(f"      Mémoire allouée: {allocation_memory:.1f} MB")
        print(f"      Objets créés: {len(large_objects)} portfolios")
        
        # Phase 2: Libération progressive avec mesures GC
        print("   Phase 2: Libération et GC")
        
        gc_measurements = []
        
        # Libérer par chunks et mesurer GC
        chunk_size = 10
        for chunk_start in range(0, len(large_objects), chunk_size):
            chunk_end = min(chunk_start + chunk_size, len(large_objects))
            
            # Supprimer chunk
            for i in range(chunk_start, chunk_end):
                large_objects[i] = None
            
            # Mesurer avant GC
            before_gc = profiler.take_snapshot()
            
            # Force GC
            gc_start = time.perf_counter()
            collected_gen0 = gc.collect(0)
            collected_gen1 = gc.collect(1) 
            collected_gen2 = gc.collect(2)
            gc_end = time.perf_counter()
            
            # Mesurer après GC
            after_gc = profiler.take_snapshot()
            
            gc_duration = (gc_end - gc_start) * 1000
            memory_freed = before_gc.rss_mb - after_gc.rss_mb
            
            gc_measurements.append({
                "chunk": chunk_start // chunk_size,
                "objects_freed": chunk_size,
                "memory_freed_mb": memory_freed,
                "gc_duration_ms": gc_duration,
                "collected": {
                    "gen0": collected_gen0,
                    "gen1": collected_gen1,
                    "gen2": collected_gen2
                },
                "memory_after_mb": after_gc.rss_mb
            })
            
            print(f"      Chunk {chunk_start//chunk_size:2d}: "
                  f"{memory_freed:5.1f} MB libérés, "
                  f"GC {gc_duration:4.1f}ms")
        
        # Nettoyage final
        large_objects.clear()
        gc.collect()
        final_snapshot = profiler.take_snapshot()
        
        # Analyse efficacité GC
        total_memory_freed = sum(m["memory_freed_mb"] for m in gc_measurements)
        total_gc_time = sum(m["gc_duration_ms"] for m in gc_measurements)
        avg_gc_efficiency = total_memory_freed / total_gc_time if total_gc_time > 0 else 0
        
        final_memory_recovered = peak_allocation_snapshot.rss_mb - final_snapshot.rss_mb
        recovery_percentage = (final_memory_recovered / allocation_memory) * 100
        
        print(f"\n📊 Efficacité garbage collection:")
        print(f"   Mémoire allouée: {allocation_memory:.1f} MB")
        print(f"   Mémoire libérée total: {total_memory_freed:.1f} MB")
        print(f"   Récupération finale: {final_memory_recovered:.1f} MB ({recovery_percentage:.1f}%)")
        print(f"   Temps GC total: {total_gc_time:.1f}ms")
        print(f"   Efficacité GC: {avg_gc_efficiency:.2f} MB/ms")
        
        profiler.stop_profiling()
        
        # Assertions GC
        assert recovery_percentage >= 80.0  # Au moins 80% récupéré
        assert avg_gc_efficiency > 0.1  # Efficacité raisonnable
        assert total_gc_time < 1000.0  # GC pas trop lent
        
        return {
            "allocation_memory": allocation_memory,
            "total_memory_freed": total_memory_freed,
            "recovery_percentage": recovery_percentage,
            "total_gc_time": total_gc_time,
            "gc_efficiency": avg_gc_efficiency,
            "gc_measurements": gc_measurements
        }


if __name__ == "__main__":
    # Exécution directe pour tests de développement
    pytest.main([__file__, "-v", "--tb=short", "-m", "memory and not slowest"])