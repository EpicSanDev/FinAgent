"""
Tests unitaires pour FinAgent.

Ce package contient tous les tests unitaires organisés par composant :

Modèles et données :
- test_data_models.py : Tests des modèles de données IA (AIRequest, AIResponse, etc.)
- test_strategy_models.py : Tests des modèles de stratégies YAML
- test_decision_models.py : Tests des modèles de décision et portefeuille

Providers et services :
- test_openbb_provider.py : Tests du provider OpenBB (données financières)
- test_claude_provider.py : Tests du provider Claude (IA conversationnelle)

Logique métier :
- test_strategy_engine.py : Tests du moteur de stratégies (YAML, règles, signaux)
- test_portfolio_manager.py : Tests du gestionnaire de portefeuille

Interface utilisateur :
- test_cli.py : Tests de l'interface ligne de commande

Pour exécuter tous les tests unitaires :
    pytest tests/unit/

Pour exécuter un module spécifique :
    pytest tests/unit/test_data_models.py

Pour exécuter avec couverture :
    pytest tests/unit/ --cov=finagent --cov-report=html
"""

# Import des principaux modules de test pour faciliter l'accès
from .test_data_models import *
from .test_strategy_models import *
from .test_decision_models import *
from .test_openbb_provider import *
from .test_claude_provider import *
from .test_strategy_engine import *
from .test_portfolio_manager import *
from .test_cli import *

__all__ = [
    # Modules de test
    'test_data_models',
    'test_strategy_models', 
    'test_decision_models',
    'test_openbb_provider',
    'test_claude_provider',
    'test_strategy_engine',
    'test_portfolio_manager',
    'test_cli'
]