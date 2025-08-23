"""
Module d'interface interactive pour FinAgent CLI.

Ce module fournit des interfaces utilisateur avancées pour interagir
avec FinAgent de manière intuitive et guidée.

Composants principaux:
- REPL: Interface de ligne de commande interactive avec auto-complétion
- Wizard: Assistant de configuration guidé pour nouveaux utilisateurs  
- Menu System: Navigation par menus pour utilisateurs non-techniques

Usage:
    # REPL interactif
    from finagent.cli.interactive import run_repl
    await run_repl()
    
    # Assistant de configuration
    from finagent.cli.interactive import run_wizard
    await run_wizard()
    
    # Système de menus
    from finagent.cli.interactive import run_menu_system
    await run_menu_system()
"""

from .repl import FinAgentREPL, run_repl, run_repl_sync
from .wizard import FinAgentWizard, run_wizard, run_wizard_sync
from .menu_system import MenuSystem, run_menu_system, run_menu_system_sync

__all__ = [
    # Classes principales
    'FinAgentREPL',
    'FinAgentWizard', 
    'MenuSystem',
    
    # Fonctions async
    'run_repl',
    'run_wizard',
    'run_menu_system',
    
    # Fonctions sync
    'run_repl_sync',
    'run_wizard_sync',
    'run_menu_system_sync'
]

# Métadonnées du module
__version__ = "1.0.0"
__author__ = "FinAgent Team"
__description__ = "Interface interactive avancée pour FinAgent CLI"

# Configuration par défaut
DEFAULT_CONFIG = {
    'repl': {
        'auto_complete': True,
        'history_enabled': True,
        'vi_mode': False,
        'mouse_support': True,
        'enable_shortcuts': True,
        'show_help_panel': True,
        'theme': 'auto'
    },
    'wizard': {
        'skip_welcome': False,
        'auto_save': True,
        'verbose_mode': False,
        'show_progress': True
    },
    'menu_system': {
        'clear_screen': True,
        'show_navigation': True,
        'enable_shortcuts': True,
        'confirm_actions': True
    }
}


def get_default_config() -> dict:
    """
    Retourne la configuration par défaut pour les interfaces interactives.
    
    Returns:
        dict: Configuration par défaut
    """
    return DEFAULT_CONFIG.copy()


def get_interface_info() -> dict:
    """
    Retourne les informations sur les interfaces disponibles.
    
    Returns:
        dict: Informations sur chaque interface
    """
    return {
        'repl': {
            'name': 'REPL Interactif',
            'description': 'Interface de ligne de commande avec auto-complétion',
            'features': [
                'Auto-complétion intelligente',
                'Historique des commandes',
                'Raccourcis clavier',
                'Aide contextuelle',
                'Thèmes personnalisables'
            ],
            'target_users': 'Utilisateurs techniques familiers avec CLI',
            'complexity': 'Intermédiaire à Avancé'
        },
        'wizard': {
            'name': 'Assistant de Configuration',
            'description': 'Guide pas-à-pas pour configurer FinAgent',
            'features': [
                'Configuration guidée',
                'Recommandations personnalisées',
                'Validation automatique',
                'Sauvegarde sécurisée',
                'Récapitulatif complet'
            ],
            'target_users': 'Nouveaux utilisateurs, première configuration',
            'complexity': 'Débutant'
        },
        'menu_system': {
            'name': 'Système de Menus',
            'description': 'Navigation par menus pour accès simplifié',
            'features': [
                'Navigation intuitive',
                'Actions guidées',
                'Descriptions détaillées',
                'Retour facile',
                'Interface visuelle'
            ],
            'target_users': 'Utilisateurs non-techniques, exploration',
            'complexity': 'Débutant à Intermédiaire'
        }
    }


# Fonctions de commodité pour le choix d'interface

def recommend_interface(user_experience: str = 'beginner') -> str:
    """
    Recommande une interface basée sur l'expérience utilisateur.
    
    Args:
        user_experience: Niveau d'expérience ('beginner', 'intermediate', 'advanced')
        
    Returns:
        str: Interface recommandée ('wizard', 'menu_system', 'repl')
    """
    recommendations = {
        'beginner': 'wizard',      # Configuration initiale guidée
        'intermediate': 'menu_system',  # Navigation par menus
        'advanced': 'repl',        # Interface CLI avancée
        'expert': 'repl'           # Interface CLI avancée
    }
    
    return recommendations.get(user_experience, 'menu_system')


def get_interface_shortcuts() -> dict:
    """
    Retourne les raccourcis clavier pour chaque interface.
    
    Returns:
        dict: Raccourcis par interface
    """
    return {
        'repl': {
            'Ctrl+C': 'Interrompre la commande en cours',
            'Ctrl+D': 'Quitter le REPL', 
            'Tab': 'Auto-complétion',
            'Ctrl+R': 'Recherche dans l\'historique',
            'Ctrl+L': 'Effacer l\'écran',
            'Ctrl+A': 'Début de ligne',
            'Ctrl+E': 'Fin de ligne',
            '?': 'Aide contextuelle',
            'help': 'Afficher toutes les commandes'
        },
        'wizard': {
            'Enter': 'Valider la saisie',
            'Ctrl+C': 'Annuler la configuration',
            'Tab': 'Complétion automatique des choix'
        },
        'menu_system': {
            '1-9': 'Sélectionner un élément de menu',
            'b': 'Retour au menu précédent',
            'q': 'Quitter (depuis le menu principal)',
            'Enter': 'Valider le choix',
            'Ctrl+C': 'Quitter immédiatement'
        }
    }


def print_interface_help():
    """Affiche l'aide pour choisir une interface."""
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    
    console = Console()
    
    # Titre
    console.print(Panel(
        "[bold cyan]🎯 Interfaces Interactives FinAgent[/bold cyan]\n\n"
        "Choisissez l'interface qui correspond le mieux à vos besoins :",
        title="Guide des Interfaces",
        border_style="cyan"
    ))
    
    # Tableau des interfaces
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Interface", style="white", width=15)
    table.add_column("Description", style="cyan", width=30)
    table.add_column("Utilisateurs Cibles", style="yellow", width=25)
    table.add_column("Complexité", style="green", width=15)
    
    interfaces = get_interface_info()
    
    for key, info in interfaces.items():
        complexity_color = {
            'Débutant': 'green',
            'Débutant à Intermédiaire': 'yellow', 
            'Intermédiaire à Avancé': 'orange',
            'Avancé': 'red'
        }.get(info['complexity'], 'white')
        
        table.add_row(
            f"[bold]{info['name']}[/bold]",
            info['description'],
            info['target_users'],
            f"[{complexity_color}]{info['complexity']}[/{complexity_color}]"
        )
    
    console.print(table)
    
    # Instructions d'utilisation
    console.print("\n[bold yellow]💡 Comment utiliser :[/bold yellow]")
    console.print("• [cyan]finagent --wizard[/cyan] : Assistant de configuration")
    console.print("• [cyan]finagent --menu[/cyan] : Système de menus")
    console.print("• [cyan]finagent --interactive[/cyan] : REPL interactif")
    console.print("• [cyan]finagent --help[/cyan] : Aide complète des commandes")


if __name__ == "__main__":
    # Affichage des informations sur les interfaces
    print_interface_help()