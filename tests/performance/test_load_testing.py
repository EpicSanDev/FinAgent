"""
Tests de Performance - Tests de Charge

Ces tests évaluent la capacité du système FinAgent à gérer une charge
croissante d'utilisateurs et d'opérations, mesurant la dégradation
des performances et identifiant les seuils de saturation.
"""

import pytest
import asyncio
import time
import statistics
import psutil
import threading
from decimal import Decimal
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

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
class LoadTestResult:
    """Résultat de test de charge"""
    concurrent_users: int
    operations_per_user: int
    total_operations: int
    duration: float
    throughput: float  # opérations/seconde
    avg_response_time: float
    p95_response_time: float
    p99_response_time: float
    success_rate: float
    error_count: int
    cpu_usage: float
    memory_usage: float


class LoadTestRunner:
    """Runner pour les tests de charge"""
    
    def __init__(self, components: Dict[str, Any]):
        self.components = components
        self.results = []
        self.errors = []
    
    async def run_user_simulation(self, user_id: int, operations: int) -> Dict[str, Any]:
        """Simule l'activité d'un utilisateur"""
        start_time = time.perf_counter()
        operation_times = []
        operations_completed = 0
        errors = []
        
        try:
            # Créer portefeuille utilisateur
            portfolio = create_test_portfolio(
                initial_capital=Decimal("100000.00")
            )
            portfolio.id = f"load-test-user-{user_id}"
            
            for op in range(operations):
                op_start = time.perf_counter()
                
                try:
                    # Rotation entre différents types d'opérations
                    if op % 4 == 0:
                        # Analyse de portefeuille
                        await self.components["portfolio_manager"].analyze_portfolio(portfolio)
                    elif op % 4 == 1:
                        # Évaluation de stratégie
                        market_data = await self.components["openbb"].get_current_price("AAPL")
                        await self.components["strategy_engine"].evaluate_symbol(
                            symbol="AAPL",
                            market_data=market_data,
                            technical_indicators={"RSI": 50},
                            strategy_config=create_test_strategy("momentum")
                        )
                    elif op % 4 == 2:
                        # Calcul de risques
                        await self.components["portfolio_manager"].calculate_risk_metrics(portfolio)
                    else:
                        # Validation décision
                        decision = InvestmentDecision(
                            symbol="TEST",
                            decision_type=DecisionType.BUY,
                            quantity=10,
                            target_price=Decimal("100.00"),
                            confidence=Decimal("0.7"),
                            reasoning="Load test",
                            created_at=datetime.now()
                        )
                        await self.components["portfolio_manager"].can_execute_decision(
                            decision=decision,
                            portfolio=portfolio
                        )
                    
                    operations_completed += 1
                    
                except Exception as e:
                    errors.append(str(e))
                
                op_end = time.perf_counter()
                operation_times.append((op_end - op_start) * 1000)  # ms
                
                # Petite pause pour simuler temps de réflexion utilisateur
                await asyncio.sleep(0.01)
        
        except Exception as e:
            errors.append(f"User simulation error: {e}")
        
        end_time = time.perf_counter()
        total_time = (end_time - start_time) * 1000
        
        return {
            "user_id": user_id,
            "operations_completed": operations_completed,
            "total_time": total_time,
            "operation_times": operation_times,
            "errors": errors,
            "success_rate": operations_completed / operations if operations > 0 else 0
        }
    
    def get_system_metrics(self) -> Dict[str, float]:
        """Récupère les métriques système"""
        return {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": psutil.virtual_memory().percent,
            "memory_available": psutil.virtual_memory().available / (1024**3)  # GB
        }


@pytest.mark.performance
@pytest.mark.load
class TestLoadTesting:
    """Tests de charge de base"""
    
    @pytest.fixture
    async def load_test_components(self, test_config):
        """Composants optimisés pour tests de charge"""
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
    async def test_baseline_single_user_load(self, load_test_components):
        """Test de charge baseline avec un utilisateur unique"""
        runner = LoadTestRunner(load_test_components)
        
        print("📊 Test de charge baseline (1 utilisateur)")
        
        # Mesurer performance système avant
        initial_metrics = runner.get_system_metrics()
        
        # Simuler utilisateur unique avec beaucoup d'opérations
        start_time = time.perf_counter()
        result = await runner.run_user_simulation(user_id=1, operations=100)
        end_time = time.perf_counter()
        
        # Mesurer performance système après
        final_metrics = runner.get_system_metrics()
        
        duration = (end_time - start_time) * 1000
        throughput = result["operations_completed"] / (duration / 1000)
        
        load_result = LoadTestResult(
            concurrent_users=1,
            operations_per_user=100,
            total_operations=result["operations_completed"],
            duration=duration,
            throughput=throughput,
            avg_response_time=statistics.mean(result["operation_times"]) if result["operation_times"] else 0,
            p95_response_time=statistics.quantiles(result["operation_times"], n=20)[18] if len(result["operation_times"]) > 20 else 0,
            p99_response_time=statistics.quantiles(result["operation_times"], n=100)[98] if len(result["operation_times"]) > 100 else 0,
            success_rate=result["success_rate"],
            error_count=len(result["errors"]),
            cpu_usage=final_metrics["cpu_percent"],
            memory_usage=final_metrics["memory_percent"]
        )
        
        print(f"   ✅ Baseline établie:")
        print(f"      Opérations: {load_result.total_operations}")
        print(f"      Débit: {load_result.throughput:.1f} ops/sec")
        print(f"      Temps réponse moyen: {load_result.avg_response_time:.1f}ms")
        print(f"      Taux de succès: {load_result.success_rate:.1%}")
        print(f"      CPU: {load_result.cpu_usage:.1f}%")
        print(f"      Mémoire: {load_result.memory_usage:.1f}%")
        
        # Assertions baseline
        assert load_result.success_rate >= 0.95  # 95% succès minimum
        assert load_result.avg_response_time < 100.0  # Moins de 100ms en moyenne
        assert load_result.throughput > 5.0  # Au moins 5 ops/sec
        
        return load_result


@pytest.mark.performance
@pytest.mark.load
class TestGradualLoad:
    """Tests de charge progressive"""
    
    @pytest.mark.asyncio
    async def test_gradual_load_increase(self, load_test_components):
        """Test de montée progressive de charge"""
        runner = LoadTestRunner(load_test_components)
        
        print("📈 Test de charge progressive")
        
        # Différents niveaux de charge à tester
        load_levels = [1, 2, 5, 10, 15, 20]
        operations_per_user = 20
        load_results = []
        
        for concurrent_users in load_levels:
            print(f"\n   🔄 Test avec {concurrent_users} utilisateurs simultanés")
            
            # Mesurer métriques système avant
            initial_metrics = runner.get_system_metrics()
            start_time = time.perf_counter()
            
            # Lancer utilisateurs simultanés
            tasks = [
                runner.run_user_simulation(user_id=i, operations=operations_per_user)
                for i in range(concurrent_users)
            ]
            
            user_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            end_time = time.perf_counter()
            final_metrics = runner.get_system_metrics()
            
            # Analyser résultats
            successful_results = [r for r in user_results if not isinstance(r, Exception)]
            total_operations = sum(r["operations_completed"] for r in successful_results)
            total_errors = sum(len(r["errors"]) for r in successful_results)
            
            all_operation_times = []
            for r in successful_results:
                all_operation_times.extend(r["operation_times"])
            
            duration = (end_time - start_time) * 1000
            throughput = total_operations / (duration / 1000) if duration > 0 else 0
            success_rate = len(successful_results) / concurrent_users
            
            load_result = LoadTestResult(
                concurrent_users=concurrent_users,
                operations_per_user=operations_per_user,
                total_operations=total_operations,
                duration=duration,
                throughput=throughput,
                avg_response_time=statistics.mean(all_operation_times) if all_operation_times else 0,
                p95_response_time=statistics.quantiles(all_operation_times, n=20)[18] if len(all_operation_times) > 20 else 0,
                p99_response_time=statistics.quantiles(all_operation_times, n=100)[98] if len(all_operation_times) > 100 else 0,
                success_rate=success_rate,
                error_count=total_errors,
                cpu_usage=final_metrics["cpu_percent"],
                memory_usage=final_metrics["memory_percent"]
            )
            
            load_results.append(load_result)
            
            print(f"      Opérations: {load_result.total_operations}")
            print(f"      Débit: {load_result.throughput:.1f} ops/sec")
            print(f"      Temps réponse: {load_result.avg_response_time:.1f}ms (P95: {load_result.p95_response_time:.1f}ms)")
            print(f"      Succès: {load_result.success_rate:.1%}")
            print(f"      CPU: {load_result.cpu_usage:.1f}% | RAM: {load_result.memory_usage:.1f}%")
            
            # Pause entre niveaux pour stabilisation
            await asyncio.sleep(1.0)
        
        # Analyser évolution des performances
        print(f"\n📊 Analyse évolution performances:")
        baseline = load_results[0]  # 1 utilisateur
        
        for result in load_results[1:]:  # 2+ utilisateurs
            throughput_scaling = result.throughput / baseline.throughput
            response_degradation = result.avg_response_time / baseline.avg_response_time
            
            print(f"   {result.concurrent_users:2d} users: "
                  f"Débit x{throughput_scaling:.2f}, "
                  f"Latence x{response_degradation:.2f}, "
                  f"Succès {result.success_rate:.1%}")
            
            # Vérifications de dégradation acceptable
            if result.concurrent_users <= 10:
                assert result.success_rate >= 0.90  # 90% succès jusqu'à 10 users
                assert response_degradation <= 3.0   # Max 3x latence baseline
            elif result.concurrent_users <= 20:
                assert result.success_rate >= 0.80  # 80% succès jusqu'à 20 users
                assert response_degradation <= 5.0   # Max 5x latence baseline
        
        return load_results
    
    @pytest.mark.asyncio
    async def test_sustained_load(self, load_test_components):
        """Test de charge soutenue sur durée prolongée"""
        runner = LoadTestRunner(load_test_components)
        
        print("⏱️  Test de charge soutenue (60 secondes)")
        
        concurrent_users = 5
        test_duration = 60  # secondes
        operations_per_batch = 10
        
        results_timeline = []
        start_time = time.perf_counter()
        
        while (time.perf_counter() - start_time) < test_duration:
            batch_start = time.perf_counter()
            
            # Lancer batch d'utilisateurs
            tasks = [
                runner.run_user_simulation(user_id=i, operations=operations_per_batch)
                for i in range(concurrent_users)
            ]
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            batch_end = time.perf_counter()
            
            # Analyser ce batch
            successful = [r for r in batch_results if not isinstance(r, Exception)]
            total_ops = sum(r["operations_completed"] for r in successful)
            batch_duration = (batch_end - batch_start) * 1000
            
            batch_metrics = {
                "elapsed_time": (batch_end - start_time),
                "operations": total_ops,
                "duration": batch_duration,
                "throughput": total_ops / (batch_duration / 1000) if batch_duration > 0 else 0,
                "success_rate": len(successful) / concurrent_users,
                "system_metrics": runner.get_system_metrics()
            }
            
            results_timeline.append(batch_metrics)
            
            # Affichage progression
            if len(results_timeline) % 5 == 0:
                elapsed = batch_metrics["elapsed_time"]
                throughput = batch_metrics["throughput"]
                cpu = batch_metrics["system_metrics"]["cpu_percent"]
                print(f"   {elapsed:5.1f}s: {throughput:6.1f} ops/sec, CPU {cpu:5.1f}%")
            
            # Pause courte entre batchs
            await asyncio.sleep(0.5)
        
        # Analyser stabilité sur la durée
        throughputs = [r["throughput"] for r in results_timeline]
        cpu_usages = [r["system_metrics"]["cpu_percent"] for r in results_timeline]
        success_rates = [r["success_rate"] for r in results_timeline]
        
        avg_throughput = statistics.mean(throughputs)
        throughput_stddev = statistics.stdev(throughputs) if len(throughputs) > 1 else 0
        avg_success_rate = statistics.mean(success_rates)
        max_cpu = max(cpu_usages)
        
        print(f"\n📊 Résultats charge soutenue:")
        print(f"   Durée: {test_duration}s")
        print(f"   Débit moyen: {avg_throughput:.1f} ± {throughput_stddev:.1f} ops/sec")
        print(f"   Taux succès moyen: {avg_success_rate:.1%}")
        print(f"   CPU max: {max_cpu:.1f}%")
        print(f"   Stabilité: {((avg_throughput - throughput_stddev) / avg_throughput):.1%}")
        
        # Assertions stabilité
        assert avg_success_rate >= 0.85  # 85% succès en moyenne
        assert throughput_stddev / avg_throughput <= 0.20  # Variabilité < 20%
        assert max_cpu <= 80.0  # CPU < 80%
        
        return {
            "timeline": results_timeline,
            "avg_throughput": avg_throughput,
            "throughput_stability": throughput_stddev / avg_throughput,
            "avg_success_rate": avg_success_rate,
            "max_cpu": max_cpu
        }


@pytest.mark.performance
@pytest.mark.load
@pytest.mark.slow
class TestPeakLoad:
    """Tests de charge pic"""
    
    @pytest.mark.asyncio
    async def test_peak_load_handling(self, load_test_components):
        """Test de gestion de charge pic soudaine"""
        runner = LoadTestRunner(load_test_components)
        
        print("🚀 Test de charge pic soudaine")
        
        # Phase 1: Charge normale
        normal_users = 5
        peak_users = 25
        operations_per_user = 15
        
        print(f"   Phase 1: Charge normale ({normal_users} users)")
        
        normal_start = time.perf_counter()
        normal_tasks = [
            runner.run_user_simulation(user_id=i, operations=operations_per_user)
            for i in range(normal_users)
        ]
        normal_results = await asyncio.gather(*normal_tasks)
        normal_end = time.perf_counter()
        
        normal_duration = (normal_end - normal_start) * 1000
        normal_ops = sum(r["operations_completed"] for r in normal_results)
        normal_throughput = normal_ops / (normal_duration / 1000)
        
        print(f"      Débit normal: {normal_throughput:.1f} ops/sec")
        
        # Pause courte
        await asyncio.sleep(2.0)
        
        # Phase 2: Charge pic soudaine
        print(f"   Phase 2: Charge pic soudaine ({peak_users} users)")
        
        peak_start = time.perf_counter()
        peak_tasks = [
            runner.run_user_simulation(user_id=i, operations=operations_per_user)
            for i in range(peak_users)
        ]
        peak_results = await asyncio.gather(*peak_tasks, return_exceptions=True)
        peak_end = time.perf_counter()
        
        # Analyser résultats pic
        successful_peak = [r for r in peak_results if not isinstance(r, Exception)]
        failed_peak = [r for r in peak_results if isinstance(r, Exception)]
        
        peak_duration = (peak_end - peak_start) * 1000
        peak_ops = sum(r["operations_completed"] for r in successful_peak)
        peak_throughput = peak_ops / (peak_duration / 1000) if peak_duration > 0 else 0
        peak_success_rate = len(successful_peak) / peak_users
        
        # Métriques système pendant pic
        peak_system = runner.get_system_metrics()
        
        print(f"      Débit pic: {peak_throughput:.1f} ops/sec")
        print(f"      Taux succès pic: {peak_success_rate:.1%}")
        print(f"      Échecs: {len(failed_peak)}")
        print(f"      CPU pic: {peak_system['cpu_percent']:.1f}%")
        print(f"      RAM pic: {peak_system['memory_percent']:.1f}%")
        
        # Phase 3: Retour à la normale
        print(f"   Phase 3: Retour normal ({normal_users} users)")
        
        await asyncio.sleep(2.0)  # Laisser système récupérer
        
        recovery_start = time.perf_counter()
        recovery_tasks = [
            runner.run_user_simulation(user_id=i, operations=operations_per_user)
            for i in range(normal_users)
        ]
        recovery_results = await asyncio.gather(*recovery_tasks)
        recovery_end = time.perf_counter()
        
        recovery_duration = (recovery_end - recovery_start) * 1000
        recovery_ops = sum(r["operations_completed"] for r in recovery_results)
        recovery_throughput = recovery_ops / (recovery_duration / 1000)
        recovery_system = runner.get_system_metrics()
        
        print(f"      Débit récupération: {recovery_throughput:.1f} ops/sec")
        print(f"      CPU récupération: {recovery_system['cpu_percent']:.1f}%")
        
        # Analyser capacité de récupération
        throughput_recovery = recovery_throughput / normal_throughput
        
        print(f"\n📊 Analyse charge pic:")
        print(f"   Dégradation pic: {(normal_throughput / peak_throughput):.2f}x")
        print(f"   Récupération: {throughput_recovery:.2f}x du normal")
        print(f"   Résilience: {peak_success_rate:.1%} succès pendant pic")
        
        # Assertions résilience
        assert peak_success_rate >= 0.70  # 70% succès minimum pendant pic
        assert throughput_recovery >= 0.90  # Récupération 90% du débit normal
        assert peak_system['cpu_percent'] <= 95.0  # CPU < 95% même en pic
        
        return {
            "normal_throughput": normal_throughput,
            "peak_throughput": peak_throughput,
            "peak_success_rate": peak_success_rate,
            "recovery_throughput": recovery_throughput,
            "throughput_recovery": throughput_recovery,
            "peak_cpu": peak_system['cpu_percent'],
            "failed_requests": len(failed_peak)
        }
    
    @pytest.mark.asyncio
    async def test_load_distribution_patterns(self, load_test_components):
        """Test de différents patterns de distribution de charge"""
        runner = LoadTestRunner(load_test_components)
        
        print("📊 Test patterns de distribution de charge")
        
        patterns = {
            "uniform": [5, 5, 5, 5, 5],           # Charge uniforme
            "ramp_up": [1, 3, 5, 7, 10],          # Montée progressive
            "spike": [2, 2, 15, 2, 2],            # Pic soudain
            "wave": [3, 6, 9, 6, 3],              # Vague
            "random": [4, 8, 3, 9, 2]             # Aléatoire
        }
        
        pattern_results = {}
        
        for pattern_name, user_counts in patterns.items():
            print(f"\n   📈 Pattern '{pattern_name}': {user_counts}")
            
            phase_results = []
            pattern_start = time.perf_counter()
            
            for phase, user_count in enumerate(user_counts):
                phase_start = time.perf_counter()
                
                tasks = [
                    runner.run_user_simulation(user_id=i, operations=10)
                    for i in range(user_count)
                ]
                
                phase_user_results = await asyncio.gather(*tasks, return_exceptions=True)
                phase_end = time.perf_counter()
                
                successful = [r for r in phase_user_results if not isinstance(r, Exception)]
                total_ops = sum(r["operations_completed"] for r in successful)
                phase_duration = (phase_end - phase_start) * 1000
                throughput = total_ops / (phase_duration / 1000) if phase_duration > 0 else 0
                
                phase_results.append({
                    "phase": phase,
                    "users": user_count,
                    "operations": total_ops,
                    "throughput": throughput,
                    "success_rate": len(successful) / user_count if user_count > 0 else 1
                })
                
                await asyncio.sleep(0.5)  # Pause entre phases
            
            pattern_end = time.perf_counter()
            pattern_duration = (pattern_end - pattern_start) * 1000
            
            # Analyser pattern
            total_operations = sum(p["operations"] for p in phase_results)
            avg_throughput = statistics.mean(p["throughput"] for p in phase_results)
            min_success_rate = min(p["success_rate"] for p in phase_results)
            throughput_variance = statistics.variance(p["throughput"] for p in phase_results)
            
            pattern_results[pattern_name] = {
                "phases": phase_results,
                "total_operations": total_operations,
                "avg_throughput": avg_throughput,
                "min_success_rate": min_success_rate,
                "throughput_variance": throughput_variance,
                "total_duration": pattern_duration
            }
            
            print(f"      Débit moyen: {avg_throughput:.1f} ops/sec")
            print(f"      Succès min: {min_success_rate:.1%}")
            print(f"      Variance: {throughput_variance:.1f}")
        
        # Comparer patterns
        print(f"\n📊 Comparaison patterns:")
        best_throughput = max(pattern_results.values(), key=lambda x: x["avg_throughput"])
        most_stable = min(pattern_results.values(), key=lambda x: x["throughput_variance"])
        
        for name, result in pattern_results.items():
            stability = "Stable" if result["throughput_variance"] < 10 else "Variable"
            print(f"   {name:8s}: {result['avg_throughput']:6.1f} ops/sec, "
                  f"Succès {result['min_success_rate']:.1%}, {stability}")
        
        # Assertions
        for pattern_name, result in pattern_results.items():
            assert result["min_success_rate"] >= 0.75  # 75% succès minimum
            assert result["avg_throughput"] > 0  # Débit positif
        
        return pattern_results


if __name__ == "__main__":
    # Exécution directe pour tests de développement
    pytest.main([__file__, "-v", "--tb=short", "-m", "load and not slow"])