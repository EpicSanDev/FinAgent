"""
Tests de Performance FinAgent

Ce module contient les tests de performance pour évaluer les performances,
la scalabilité et l'efficacité du système FinAgent sous différentes charges
et conditions d'utilisation.

Les tests de performance couvrent :
- Benchmarks de latence et débit
- Tests de charge (charge croissante)
- Tests de stress (limites système)
- Profiling de mémoire et CPU
- Performance des APIs externes
- Optimisation des algorithmes financiers

Organisation des tests de performance :
- test_latency_benchmarks.py : Benchmarks de latence des opérations critiques
- test_load_testing.py : Tests de charge avec montée progressive
- test_stress_testing.py : Tests de stress aux limites système
- test_memory_profiling.py : Profiling mémoire et détection fuites
- test_api_performance.py : Performance intégration APIs externes
- test_algorithm_optimization.py : Optimisation algorithmes financiers
- test_concurrent_performance.py : Performance en environnement concurrent

Marqueurs pytest utilisés :
- @pytest.mark.performance : Tous les tests de performance
- @pytest.mark.benchmark : Tests de benchmark spécifiques
- @pytest.mark.load : Tests de charge
- @pytest.mark.stress : Tests de stress
- @pytest.mark.memory : Tests de profiling mémoire
- @pytest.mark.slow : Tests nécessitant plus de temps
- @pytest.mark.cpu_intensive : Tests intensifs CPU
"""

# Import des composants de performance pour faciliter les imports
from .test_latency_benchmarks import *
from .test_load_testing import *
from .test_stress_testing import *
from .test_memory_profiling import *
from .test_api_performance import *
from .test_algorithm_optimization import *
from .test_concurrent_performance import *

__all__ = [
    # Benchmarks de latence
    "TestLatencyBenchmarks",
    "TestOperationLatency",
    "TestAPILatency",
    "TestCalculationLatency",
    
    # Tests de charge
    "TestLoadTesting",
    "TestGradualLoad",
    "TestSustainedLoad",
    "TestPeakLoad",
    
    # Tests de stress
    "TestStressTesting",
    "TestSystemLimits",
    "TestResourceExhaustion",
    "TestCrashRecovery",
    
    # Profiling mémoire
    "TestMemoryProfiling",
    "TestMemoryLeaks",
    "TestMemoryOptimization",
    "TestGarbageCollection",
    
    # Performance API
    "TestAPIPerformance",
    "TestOpenBBPerformance",
    "TestClaudePerformance",
    "TestRateLimitOptimization",
    
    # Optimisation algorithmes
    "TestAlgorithmOptimization",
    "TestPortfolioOptimization",
    "TestStrategyPerformance",
    "TestCalculationOptimization",
    
    # Performance concurrente
    "TestConcurrentPerformance",
    "TestParallelProcessing",
    "TestAsyncPerformance",
    "TestThreadSafety"
]