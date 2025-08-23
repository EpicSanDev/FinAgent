"""
Tests d'Intégration FinAgent

Ce module contient les tests d'intégration qui valident les workflows complets
et l'interaction entre les différents composants du système FinAgent.

Les tests d'intégration couvrent :
- Workflows bout-en-bout complets
- Intégration entre composants (Strategy Engine + Portfolio Manager)
- APIs externes réelles (avec limitations de rate)
- Persistance et récupération de données
- Interface CLI avec données réelles
- Scénarios utilisateur typiques

Organisation des tests d'intégration :
- test_workflow_integration.py : Workflows complets analyse -> décision -> exécution
- test_api_integration.py : Intégration réelle avec OpenBB et Claude APIs
- test_cli_integration.py : Tests CLI bout-en-bout avec vraies données
- test_data_persistence.py : Tests de persistance et récupération données
- test_strategy_portfolio_integration.py : Intégration moteur + gestionnaire
- test_end_to_end_scenarios.py : Scénarios utilisateur complets

Marqueurs pytest utilisés :
- @pytest.mark.integration : Tous les tests d'intégration
- @pytest.mark.slow : Tests nécessitant plus de temps (APIs réelles)
- @pytest.mark.external_api : Tests utilisant des APIs externes
- @pytest.mark.cli : Tests de l'interface en ligne de commande
- @pytest.mark.persistence : Tests de persistance de données
"""

# Import des tests d'intégration pour faciliter les imports
from .test_workflow_integration import *
from .test_api_integration import *
from .test_cli_integration import *
from .test_data_persistence import *
from .test_strategy_portfolio_integration import *
from .test_end_to_end_scenarios import *

__all__ = [
    # Workflows
    "TestWorkflowIntegration",
    "TestCompleteAnalysisWorkflow", 
    "TestDecisionExecutionWorkflow",
    "TestPortfolioManagementWorkflow",
    
    # APIs
    "TestOpenBBIntegration",
    "TestClaudeIntegration", 
    "TestAPIErrorHandling",
    "TestRateLimitingIntegration",
    
    # CLI
    "TestCLIIntegration",
    "TestCLIWorkflows",
    "TestCLIConfiguration",
    
    # Persistance
    "TestDataPersistence",
    "TestPortfolioPersistence",
    "TestStrategyPersistence",
    
    # Stratégie + Portfolio
    "TestStrategyPortfolioIntegration",
    "TestSignalToExecutionFlow",
    
    # End-to-End
    "TestEndToEndScenarios",
    "TestRealUserWorkflows",
    "TestCompleteSystemIntegration"
]