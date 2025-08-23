"""
Module des commandes CLI de FinAgent.

Ce module expose toutes les commandes principales de l'interface CLI
pour une utilisation facile dans l'application principale.
"""

from .analyze_command import analyze
from .portfolio_command import portfolio
from .strategy_command import strategy
from .decision_command import decision
from .config_command import config

# Export des commandes principales
__all__ = [
    'analyze',
    'portfolio', 
    'strategy',
    'decision',
    'config'
]

# Métadonnées du module
COMMANDS = {
    'analyze': {
        'function': analyze,
        'description': 'Commandes d\'analyse d\'actions et de marchés',
        'category': 'analysis'
    },
    'portfolio': {
        'function': portfolio,
        'description': 'Commandes de gestion de portefeuilles d\'investissement',
        'category': 'portfolio'
    },
    'strategy': {
        'function': strategy,
        'description': 'Commandes de gestion des stratégies d\'investissement',
        'category': 'strategy'
    },
    'decision': {
        'function': decision,
        'description': 'Commandes de gestion des décisions de trading',
        'category': 'decision'
    },
    'config': {
        'function': config,
        'description': 'Commandes de gestion de la configuration',
        'category': 'system'
    }
}

def get_command_list():
    """Retourne la liste des commandes disponibles."""
    return list(COMMANDS.keys())

def get_command_info(command_name: str):
    """Retourne les informations d'une commande spécifique."""
    return COMMANDS.get(command_name)

def get_commands_by_category(category: str):
    """Retourne les commandes d'une catégorie spécifique."""
    return {
        name: info for name, info in COMMANDS.items() 
        if info['category'] == category
    }