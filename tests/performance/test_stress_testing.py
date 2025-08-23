"""
Tests de Performance - Tests de Stress

Ces tests poussent le système FinAgent au-delà de ses limites normales
pour identifier les points de rupture, tester la récupération d'erreurs
et valider la stabilité sous contraintes extrêmes.
"""

import pytest
import asyncio
import time
import statistics
import psutil
import resource
import gc
import threading
from decimal import Decimal
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
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
class StressTestResult:
    """Résultat de test de stress"""
    test_type: str
    peak_load: int
    duration: float
    breaking_point: Optional[int]
    max_throughput: float
    degradation_threshold: float
    recovery_time: float
    error_rate: float
    memory_peak_mb: float
    cpu_peak_percent: float
    system_stable: bool


class StressTestRunner:
    """Runner pour les tests de stress"""
    
    def __init__(self, components: Dict[str, Any]):
        self.components = components
        self.active_tasks = []
        self.error_count = 0
        self.max_memory = 0
        self.max_cpu = 0
        self.breaking_point = None
        
    def monitor_system(self) -> Dict[str, float]:
        """Monitoring système continu"""
        process = psutil.Process()
        memory_mb = process.memory_info().rss / (1024 * 1024)
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        self.max_memory = max(self.max_memory, memory_mb)
        self.max_cpu = max(self.max_cpu, cpu_percent)
        
        return {
            "memory_mb": memory_mb,
            "cpu_percent": cpu_percent,
            "open_files": process.num_fds() if hasattr(process, 'num_fds') else 0,
            "threads": process.num_threads()
        }
    
    async def stress_operation(self, operation_id: int, complexity: str = "normal") -> Dict[str, Any]:
        """Opération stressante selon le niveau de complexité"""
        start_time = time.perf_counter()
        
        try:
            if complexity == "light":
                # Opération légère
                portfolio = create_test_portfolio(initial_capital=Decimal("1000.00"))
                await self.components["portfolio_manager"].calculate_value(portfolio)
            
            elif complexity == "normal":
                # Opération normale
                portfolio = create_test_portfolio(initial_capital=Decimal("100000.00"))
                strategy = create_test_strategy("balanced")
                
                market_data = await self.components["openbb"].get_current_price("AAPL")
                await self.components["strategy_engine"].evaluate_symbol(
                    symbol="AAPL",
                    market_data=market_data,
                    technical_indicators={"RSI": random.uniform(20, 80)},
                    strategy_config=strategy
                )
            
            elif complexity == "heavy":
                # Opération lourde
                portfolio = create_test_portfolio(initial_capital=Decimal("1000000.00"))
                
                # Ajouter plusieurs positions
                for i in range(10):
                    position = Position(
                        symbol=f"STOCK{i:02d}",
                        quantity=random.randint(10, 100),
                        average_price=Decimal(str(random.uniform(50, 200))),
                        current_price=Decimal(str(random.uniform(45, 210))),
                        last_updated=datetime.now()
                    )
                    portfolio.positions.append(position)
                
                # Analyse complète
                await self.components["portfolio_manager"].analyze_portfolio(portfolio)
                await self.components["portfolio_manager"].calculate_risk_metrics(portfolio)
                await self.components["portfolio_manager"].generate_rebalancing_recommendations(portfolio)
            
            elif complexity == "extreme":
                # Opération extrême
                portfolio = create_test_portfolio(initial_capital=Decimal("10000000.00"))
                
                # Créer portfolio complexe
                for i in range(50):
                    position = Position(
                        symbol=f"COMPLEX{i:03d}",
                        quantity=random.randint(100, 1000),
                        average_price=Decimal(str(random.uniform(10, 500))),
                        current_price=Decimal(str(random.uniform(8, 520))),
                        last_updated=datetime.now()
                    )
                    portfolio.positions.append(position)
                
                # Analyses multiples simultanées
                tasks = [
                    self.components["portfolio_manager"].analyze_portfolio(portfolio),
                    self.components["portfolio_manager"].calculate_risk_metrics(portfolio),
                    self.components["portfolio_manager"].calculate_performance_metrics(portfolio),
                    self.components["portfolio_manager"].generate_rebalancing_recommendations(portfolio)
                ]
                await asyncio.gather(*tasks)
            
            end_time = time.perf_counter()
            duration = (end_time - start_time) * 1000
            
            return {
                "operation_id": operation_id,
                "complexity": complexity,
                "duration": duration,
                "success": True,
                "error": None
            }
            
        except Exception as e:
            end_time = time.perf_counter()
            duration = (end_time - start_time) * 1000
            self.error_count += 1
            
            return {
                "operation_id": operation_id,
                "complexity": complexity,
                "duration": duration,
                "success": False,
                "error": str(e)
            }
    
    async def ramp_up_stress_test(self, max_concurrent: int, ramp_duration: float) -> List[Dict]:
        """Test de montée progressive jusqu'au point de rupture"""
        results = []
        current_load = 1
        step_duration = ramp_duration / max_concurrent
        
        print(f"🚀 Montée progressive: 1 → {max_concurrent} sur {ramp_duration}s")
        
        while current_load <= max_concurrent:
            step_start = time.perf_counter()
            
            # Lancer opérations pour ce niveau
            tasks = [
                self.stress_operation(i, complexity="normal")
                for i in range(current_load)
            ]
            
            step_results = await asyncio.gather(*tasks, return_exceptions=True)
            step_end = time.perf_counter()
            
            # Analyser résultats de ce step
            successful = [r for r in step_results if not isinstance(r, Exception) and r.get("success", False)]
            failed = [r for r in step_results if isinstance(r, Exception) or not r.get("success", True)]
            
            success_rate = len(successful) / current_load if current_load > 0 else 0
            avg_duration = statistics.mean(r["duration"] for r in successful) if successful else 0
            step_duration_actual = (step_end - step_start) * 1000
            
            system_metrics = self.monitor_system()
            
            step_result = {
                "load_level": current_load,
                "success_rate": success_rate,
                "avg_duration": avg_duration,
                "step_duration": step_duration_actual,
                "failed_count": len(failed),
                "system_metrics": system_metrics
            }
            
            results.append(step_result)
            
            print(f"   {current_load:3d} concurrent: "
                  f"Succès {success_rate:.1%}, "
                  f"Durée {avg_duration:.1f}ms, "
                  f"CPU {system_metrics['cpu_percent']:.1f}%")
            
            # Détecter point de rupture
            if success_rate < 0.5:  # Moins de 50% de succès
                self.breaking_point = current_load
                print(f"   ⚠️  Point de rupture détecté: {current_load} concurrent")
                break
            
            current_load += 1
            await asyncio.sleep(step_duration / 1000)  # Pause entre steps
        
        return results


@pytest.mark.performance
@pytest.mark.stress
class TestBasicStress:
    """Tests de stress de base"""
    
    @pytest.fixture
    async def stress_test_components(self, test_config):
        """Composants optimisés pour tests de stress"""
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
    async def test_concurrent_user_stress(self, stress_test_components):
        """Test de stress par utilisateurs concurrents croissants"""
        runner = StressTestRunner(stress_test_components)
        
        print("👥 Test stress utilisateurs concurrents")
        
        max_users = 50
        ramp_results = await runner.ramp_up_stress_test(
            max_concurrent=max_users,
            ramp_duration=30.0  # 30 secondes
        )
        
        # Analyser progression
        peak_load = max(r["load_level"] for r in ramp_results)
        peak_throughput = max(r["load_level"] / (r["step_duration"] / 1000) for r in ramp_results)
        degradation_start = None
        
        for i, result in enumerate(ramp_results):
            if result["success_rate"] < 0.95 and degradation_start is None:
                degradation_start = result["load_level"]
        
        stress_result = StressTestResult(
            test_type="concurrent_users",
            peak_load=peak_load,
            duration=sum(r["step_duration"] for r in ramp_results),
            breaking_point=runner.breaking_point,
            max_throughput=peak_throughput,
            degradation_threshold=degradation_start or peak_load,
            recovery_time=0.0,  # Pas applicable ici
            error_rate=runner.error_count / sum(r["load_level"] for r in ramp_results),
            memory_peak_mb=runner.max_memory,
            cpu_peak_percent=runner.max_cpu,
            system_stable=runner.breaking_point is None
        )
        
        print(f"\n📊 Résultats stress utilisateurs:")
        print(f"   Charge max supportée: {stress_result.peak_load}")
        print(f"   Point de rupture: {stress_result.breaking_point or 'Non atteint'}")
        print(f"   Seuil dégradation: {stress_result.degradation_threshold}")
        print(f"   Débit max: {stress_result.max_throughput:.1f} ops/sec")
        print(f"   Mémoire pic: {stress_result.memory_peak_mb:.1f} MB")
        print(f"   CPU pic: {stress_result.cpu_peak_percent:.1f}%")
        
        # Assertions
        assert stress_result.degradation_threshold >= 10  # Supporte au moins 10 users
        assert stress_result.memory_peak_mb < 1000  # Moins de 1GB
        assert stress_result.cpu_peak_percent < 100  # CPU pas saturé
        
        return stress_result
    
    @pytest.mark.asyncio
    async def test_operation_complexity_stress(self, stress_test_components):
        """Test de stress par complexité d'opérations"""
        runner = StressTestRunner(stress_test_components)
        
        print("⚙️  Test stress complexité opérations")
        
        complexities = ["light", "normal", "heavy", "extreme"]
        complexity_results = {}
        
        for complexity in complexities:
            print(f"\n   🔄 Test complexité '{complexity}'")
            
            concurrent_ops = 20
            operations_per_level = 5
            
            complexity_start = time.perf_counter()
            
            tasks = [
                runner.stress_operation(i, complexity=complexity)
                for i in range(concurrent_ops)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            complexity_end = time.perf_counter()
            complexity_duration = (complexity_end - complexity_start) * 1000
            
            successful = [r for r in results if not isinstance(r, Exception) and r.get("success", False)]
            failed = [r for r in results if isinstance(r, Exception) or not r.get("success", True)]
            
            success_rate = len(successful) / concurrent_ops
            avg_duration = statistics.mean(r["duration"] for r in successful) if successful else 0
            p95_duration = statistics.quantiles([r["duration"] for r in successful], n=20)[18] if len(successful) > 20 else avg_duration
            
            system_metrics = runner.monitor_system()
            
            complexity_results[complexity] = {
                "concurrent_ops": concurrent_ops,
                "success_rate": success_rate,
                "avg_duration": avg_duration,
                "p95_duration": p95_duration,
                "total_duration": complexity_duration,
                "failed_count": len(failed),
                "throughput": len(successful) / (complexity_duration / 1000),
                "system_metrics": system_metrics
            }
            
            print(f"      Succès: {success_rate:.1%}")
            print(f"      Durée moy: {avg_duration:.1f}ms (P95: {p95_duration:.1f}ms)")
            print(f"      Débit: {complexity_results[complexity]['throughput']:.1f} ops/sec")
            
            await asyncio.sleep(1.0)  # Pause entre complexités
        
        # Analyser progression de complexité
        print(f"\n📊 Progression complexité:")
        for complexity in complexities:
            result = complexity_results[complexity]
            print(f"   {complexity:8s}: {result['avg_duration']:6.1f}ms, "
                  f"Succès {result['success_rate']:.1%}, "
                  f"Débit {result['throughput']:5.1f} ops/sec")
        
        # Vérifications par complexité
        assert complexity_results["light"]["success_rate"] >= 0.98  # 98% pour opérations légères
        assert complexity_results["normal"]["success_rate"] >= 0.95  # 95% pour opérations normales
        assert complexity_results["heavy"]["success_rate"] >= 0.90  # 90% pour opérations lourdes
        assert complexity_results["extreme"]["success_rate"] >= 0.80  # 80% pour opérations extrêmes
        
        return complexity_results


@pytest.mark.performance
@pytest.mark.stress
@pytest.mark.slow
class TestExtremStress:
    """Tests de stress extrêmes"""
    
    @pytest.mark.asyncio
    async def test_memory_stress(self, stress_test_components):
        """Test de stress mémoire"""
        runner = StressTestRunner(stress_test_components)
        
        print("🧠 Test stress mémoire")
        
        # Créer de nombreux portfolios volumineux simultanément
        memory_start = psutil.Process().memory_info().rss / (1024 * 1024)
        
        large_portfolios = []
        operations = []
        
        try:
            for i in range(100):  # 100 portfolios volumineux
                portfolio = create_test_portfolio(initial_capital=Decimal("5000000.00"))
                
                # Ajouter nombreuses positions
                for j in range(100):  # 100 positions par portfolio
                    position = Position(
                        symbol=f"MEM{i:03d}_{j:03d}",
                        quantity=random.randint(100, 1000),
                        average_price=Decimal(str(random.uniform(10, 200))),
                        current_price=Decimal(str(random.uniform(8, 220))),
                        last_updated=datetime.now()
                    )
                    portfolio.positions.append(position)
                
                large_portfolios.append(portfolio)
                
                # Opération sur ce portfolio
                operations.append(
                    runner.components["portfolio_manager"].analyze_portfolio(portfolio)
                )
                
                # Monitoring mémoire
                current_memory = psutil.Process().memory_info().rss / (1024 * 1024)
                if i % 10 == 0:
                    print(f"   Portfolio {i:3d}: {current_memory - memory_start:6.1f} MB utilisés")
                
                # Arrêter si mémoire excessive
                if current_memory > memory_start + 2000:  # +2GB max
                    print(f"   ⚠️  Limite mémoire atteinte: {i} portfolios")
                    break
            
            # Exécuter toutes les opérations
            print(f"   🔄 Exécution {len(operations)} analyses simultanées...")
            
            start_time = time.perf_counter()
            results = await asyncio.gather(*operations, return_exceptions=True)
            end_time = time.perf_counter()
            
            # Analyser résultats
            successful = [r for r in results if not isinstance(r, Exception)]
            failed = [r for r in results if isinstance(r, Exception)]
            
            memory_end = psutil.Process().memory_info().rss / (1024 * 1024)
            memory_used = memory_end - memory_start
            duration = (end_time - start_time) * 1000
            
            print(f"\n📊 Résultats stress mémoire:")
            print(f"   Portfolios créés: {len(large_portfolios)}")
            print(f"   Opérations réussies: {len(successful)}")
            print(f"   Opérations échouées: {len(failed)}")
            print(f"   Mémoire utilisée: {memory_used:.1f} MB")
            print(f"   Durée totale: {duration:.1f}ms")
            print(f"   Taux succès: {len(successful) / len(operations):.1%}")
            
            # Nettoyage forcé
            large_portfolios.clear()
            operations.clear()
            gc.collect()
            
            memory_after_gc = psutil.Process().memory_info().rss / (1024 * 1024)
            memory_recovered = memory_end - memory_after_gc
            
            print(f"   Mémoire récupérée après GC: {memory_recovered:.1f} MB")
            
            # Assertions
            assert len(successful) / len(operations) >= 0.80  # 80% succès minimum
            assert memory_used < 3000  # Moins de 3GB utilisés
            assert memory_recovered > memory_used * 0.5  # Au moins 50% récupéré
            
            return {
                "portfolios_created": len(large_portfolios),
                "operations_successful": len(successful),
                "memory_used_mb": memory_used,
                "memory_recovered_mb": memory_recovered,
                "success_rate": len(successful) / len(operations),
                "duration_ms": duration
            }
            
        except Exception as e:
            print(f"   ❌ Erreur stress mémoire: {e}")
            raise
        
        finally:
            # Nettoyage de sécurité
            large_portfolios.clear()
            operations.clear()
            gc.collect()
    
    @pytest.mark.asyncio
    async def test_sustained_extreme_load(self, stress_test_components):
        """Test de charge extrême soutenue"""
        runner = StressTestRunner(stress_test_components)
        
        print("⚡ Test charge extrême soutenue")
        
        test_duration = 60  # 60 secondes
        extreme_load = 30  # 30 opérations simultanées
        batch_interval = 2.0  # Nouveau batch toutes les 2 secondes
        
        timeline_results = []
        start_time = time.perf_counter()
        batch_count = 0
        
        print(f"   Charge {extreme_load} ops simultanées pendant {test_duration}s")
        
        while (time.perf_counter() - start_time) < test_duration:
            batch_start = time.perf_counter()
            batch_count += 1
            
            # Créer batch d'opérations extrêmes
            tasks = [
                runner.stress_operation(i, complexity="extreme")
                for i in range(extreme_load)
            ]
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            batch_end = time.perf_counter()
            
            # Analyser ce batch
            successful = [r for r in batch_results if not isinstance(r, Exception) and r.get("success", False)]
            failed = [r for r in batch_results if isinstance(r, Exception) or not r.get("success", True)]
            
            batch_duration = (batch_end - batch_start) * 1000
            elapsed_time = batch_end - start_time
            
            success_rate = len(successful) / extreme_load
            avg_duration = statistics.mean(r["duration"] for r in successful) if successful else 0
            throughput = len(successful) / (batch_duration / 1000) if batch_duration > 0 else 0
            
            system_metrics = runner.monitor_system()
            
            batch_result = {
                "batch": batch_count,
                "elapsed_time": elapsed_time,
                "success_rate": success_rate,
                "avg_duration": avg_duration,
                "throughput": throughput,
                "failed_count": len(failed),
                "system_metrics": system_metrics
            }
            
            timeline_results.append(batch_result)
            
            # Affichage périodique
            if batch_count % 5 == 0:
                print(f"   {elapsed_time:5.1f}s: Succès {success_rate:.1%}, "
                      f"Débit {throughput:.1f} ops/sec, "
                      f"CPU {system_metrics['cpu_percent']:.1f}%")
            
            # Vérifier stabilité système
            if system_metrics['cpu_percent'] > 95 or system_metrics['memory_mb'] > 2000:
                print(f"   ⚠️  Système sous stress extrême - CPU {system_metrics['cpu_percent']:.1f}%")
            
            # Pause avant prochain batch
            sleep_time = max(0, batch_interval - (batch_end - batch_start))
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
        
        # Analyser performance sur la durée
        total_operations = sum(r["success_rate"] * extreme_load for r in timeline_results)
        avg_success_rate = statistics.mean(r["success_rate"] for r in timeline_results)
        avg_throughput = statistics.mean(r["throughput"] for r in timeline_results)
        throughput_stability = statistics.stdev(r["throughput"] for r in timeline_results) / avg_throughput if avg_throughput > 0 else 0
        
        final_system = runner.monitor_system()
        
        print(f"\n📊 Résultats charge extrême soutenue:")
        print(f"   Durée: {test_duration}s")
        print(f"   Batches exécutés: {batch_count}")
        print(f"   Opérations totales: {total_operations:.0f}")
        print(f"   Taux succès moyen: {avg_success_rate:.1%}")
        print(f"   Débit moyen: {avg_throughput:.1f} ops/sec")
        print(f"   Stabilité débit: {(1 - throughput_stability):.1%}")
        print(f"   Mémoire finale: {final_system['memory_mb']:.1f} MB")
        print(f"   CPU max: {runner.max_cpu:.1f}%")
        
        # Analyser dégradation dans le temps
        first_half = timeline_results[:len(timeline_results)//2]
        second_half = timeline_results[len(timeline_results)//2:]
        
        first_half_success = statistics.mean(r["success_rate"] for r in first_half)
        second_half_success = statistics.mean(r["success_rate"] for r in second_half)
        
        performance_degradation = (first_half_success - second_half_success) / first_half_success if first_half_success > 0 else 0
        
        print(f"   Dégradation performance: {performance_degradation:.1%}")
        
        # Assertions
        assert avg_success_rate >= 0.70  # 70% succès minimum sous charge extrême
        assert performance_degradation <= 0.20  # Max 20% dégradation
        assert throughput_stability <= 0.30  # Variabilité < 30%
        assert final_system['memory_mb'] < 2000  # Mémoire contrôlée
        
        return {
            "total_operations": total_operations,
            "avg_success_rate": avg_success_rate,
            "avg_throughput": avg_throughput,
            "throughput_stability": throughput_stability,
            "performance_degradation": performance_degradation,
            "timeline": timeline_results,
            "system_metrics": final_system
        }
    
    @pytest.mark.asyncio
    async def test_recovery_after_stress(self, stress_test_components):
        """Test de récupération après stress"""
        runner = StressTestRunner(stress_test_components)
        
        print("🔄 Test récupération après stress")
        
        # Phase 1: Baseline normal
        print("   Phase 1: Mesure baseline normale")
        
        baseline_tasks = [
            runner.stress_operation(i, complexity="normal")
            for i in range(10)
        ]
        baseline_results = await asyncio.gather(*baseline_tasks)
        baseline_success = len([r for r in baseline_results if r.get("success", False)]) / len(baseline_tasks)
        baseline_avg_duration = statistics.mean(r["duration"] for r in baseline_results if r.get("success", False))
        
        print(f"      Baseline: {baseline_success:.1%} succès, {baseline_avg_duration:.1f}ms")
        
        # Phase 2: Stress intense
        print("   Phase 2: Application stress intense")
        
        stress_tasks = [
            runner.stress_operation(i, complexity="extreme")
            for i in range(50)
        ]
        stress_start = time.perf_counter()
        stress_results = await asyncio.gather(*stress_tasks, return_exceptions=True)
        stress_end = time.perf_counter()
        
        stress_successful = [r for r in stress_results if not isinstance(r, Exception) and r.get("success", False)]
        stress_success_rate = len(stress_successful) / len(stress_tasks)
        stress_duration = (stress_end - stress_start) * 1000
        
        print(f"      Stress: {stress_success_rate:.1%} succès, {stress_duration:.1f}ms total")
        
        # Phase 3: Mesures de récupération
        print("   Phase 3: Mesure récupération")
        
        recovery_measurements = []
        recovery_intervals = [0, 5, 10, 30]  # secondes après stress
        
        for interval in recovery_intervals:
            if interval > 0:
                await asyncio.sleep(interval)
            
            recovery_start = time.perf_counter()
            recovery_tasks = [
                runner.stress_operation(i, complexity="normal")
                for i in range(10)
            ]
            recovery_results = await asyncio.gather(*recovery_tasks)
            recovery_end = time.perf_counter()
            
            recovery_successful = [r for r in recovery_results if r.get("success", False)]
            recovery_success_rate = len(recovery_successful) / len(recovery_tasks)
            recovery_avg_duration = statistics.mean(r["duration"] for r in recovery_successful) if recovery_successful else float('inf')
            recovery_system = runner.monitor_system()
            
            recovery_measurement = {
                "interval": interval,
                "success_rate": recovery_success_rate,
                "avg_duration": recovery_avg_duration,
                "vs_baseline_success": recovery_success_rate / baseline_success if baseline_success > 0 else 0,
                "vs_baseline_duration": recovery_avg_duration / baseline_avg_duration if baseline_avg_duration > 0 else float('inf'),
                "system_metrics": recovery_system
            }
            
            recovery_measurements.append(recovery_measurement)
            
            print(f"      +{interval:2d}s: Succès {recovery_success_rate:.1%} "
                  f"({recovery_measurement['vs_baseline_success']:.2f}x baseline), "
                  f"Durée {recovery_avg_duration:.1f}ms "
                  f"({recovery_measurement['vs_baseline_duration']:.2f}x baseline)")
        
        # Analyser récupération
        final_recovery = recovery_measurements[-1]
        full_recovery_time = None
        
        for measurement in recovery_measurements:
            if (measurement["vs_baseline_success"] >= 0.95 and 
                measurement["vs_baseline_duration"] <= 1.2):
                full_recovery_time = measurement["interval"]
                break
        
        print(f"\n📊 Analyse récupération:")
        print(f"   Récupération complète: {full_recovery_time}s" if full_recovery_time is not None else "   Récupération incomplète")
        print(f"   Performance finale: {final_recovery['vs_baseline_success']:.2f}x baseline")
        print(f"   Latence finale: {final_recovery['vs_baseline_duration']:.2f}x baseline")
        
        # Assertions récupération
        assert final_recovery["success_rate"] >= 0.90  # 90% succès après récupération
        assert final_recovery["vs_baseline_success"] >= 0.85  # 85% de la baseline
        assert full_recovery_time is not None and full_recovery_time <= 30  # Récupération en 30s max
        
        return {
            "baseline_success": baseline_success,
            "stress_success_rate": stress_success_rate,
            "recovery_measurements": recovery_measurements,
            "full_recovery_time": full_recovery_time,
            "final_recovery_ratio": final_recovery["vs_baseline_success"]
        }


@pytest.mark.performance
@pytest.mark.stress
@pytest.mark.slowest
class TestCatastrophicStress:
    """Tests de stress catastrophiques"""
    
    @pytest.mark.asyncio
    async def test_system_breaking_point(self, stress_test_components):
        """Test pour trouver le point de rupture du système"""
        runner = StressTestRunner(stress_test_components)
        
        print("💥 Test point de rupture système")
        
        # Augmentation agressive jusqu'à rupture
        current_load = 10
        max_attempts = 200
        breaking_point = None
        last_successful_load = 0
        
        while current_load <= max_attempts:
            print(f"   🔄 Test charge {current_load}")
            
            try:
                # Test avec timeout court
                tasks = [
                    runner.stress_operation(i, complexity="extreme")
                    for i in range(current_load)
                ]
                
                # Timeout agressif
                results = await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=30.0  # 30 secondes max
                )
                
                successful = [r for r in results if not isinstance(r, Exception) and r.get("success", False)]
                success_rate = len(successful) / current_load
                
                system_metrics = runner.monitor_system()
                
                print(f"      Succès: {success_rate:.1%}, "
                      f"CPU: {system_metrics['cpu_percent']:.1f}%, "
                      f"RAM: {system_metrics['memory_mb']:.1f}MB")
                
                # Critères de rupture
                if (success_rate < 0.30 or  # Moins de 30% de succès
                    system_metrics['cpu_percent'] > 98 or  # CPU saturé
                    system_metrics['memory_mb'] > 3000):  # Mémoire excessive
                    
                    breaking_point = current_load
                    print(f"   💥 Point de rupture détecté: {current_load}")
                    break
                
                if success_rate >= 0.50:
                    last_successful_load = current_load
                
                # Augmentation adaptative
                if success_rate > 0.80:
                    current_load += 20  # Augmentation rapide si OK
                elif success_rate > 0.50:
                    current_load += 10  # Augmentation modérée
                else:
                    current_load += 5   # Augmentation prudente
                
            except asyncio.TimeoutError:
                breaking_point = current_load
                print(f"   ⏰ Timeout atteint à {current_load} - considéré comme point de rupture")
                break
            
            except Exception as e:
                breaking_point = current_load
                print(f"   ❌ Exception à {current_load}: {e}")
                break
            
            # Pause pour stabilisation
            await asyncio.sleep(2.0)
        
        print(f"\n📊 Point de rupture système:")
        print(f"   Dernière charge réussie: {last_successful_load}")
        print(f"   Point de rupture: {breaking_point}")
        print(f"   Marge opérationnelle: {last_successful_load}x charge normale")
        
        # Assertions
        assert last_successful_load >= 20  # Au moins 20x charge normale
        assert breaking_point is not None  # Point de rupture identifié
        assert breaking_point > last_successful_load  # Logique cohérente
        
        return {
            "last_successful_load": last_successful_load,
            "breaking_point": breaking_point,
            "operational_margin": last_successful_load
        }


if __name__ == "__main__":
    # Exécution directe pour tests de développement
    pytest.main([__file__, "-v", "--tb=short", "-m", "stress and not slowest"])