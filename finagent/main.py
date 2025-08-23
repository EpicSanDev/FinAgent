"""
Point d'entrée principal de FinAgent

Ce module contient la fonction main() qui initialise l'application,
configure les services essentiels et lance l'interface CLI.
"""

import sys
import asyncio
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.traceback import install

# Imports locaux (à implémenter)
# from finagent.core.logging.logger import setup_logging
# from finagent.core.errors.error_handler import setup_error_handling
# from finagent.config.settings import Settings
# from finagent.cli.main import cli
# from finagent.core.dependency_injection.container import setup_container

# Installation des tracebacks riches pour le développement
install(show_locals=True)

# Console pour les sorties
console = Console()


def print_welcome():
    """Affiche le message de bienvenue."""
    from finagent import WELCOME_MESSAGE
    console.print(WELCOME_MESSAGE, style="cyan")


def check_requirements() -> bool:
    """
    Vérifie que tous les prérequis sont installés.
    
    Returns:
        bool: True si tous les prérequis sont satisfaits
    """
    try:
        # Vérification des imports critiques
        import pandas  # noqa: F401
        import openbb  # noqa: F401
        import openai  # noqa: F401
        import sqlalchemy  # noqa: F401
        
        console.print("✅ Toutes les dépendances sont installées", style="green")
        return True
        
    except ImportError as e:
        console.print(f"❌ Dépendance manquante: {e}", style="red")
        console.print("💡 Exécutez: poetry install ou pip install -r requirements.txt", style="yellow")
        return False


def setup_data_directories():
    """Crée les répertoires de données nécessaires."""
    data_dirs = [
        "data/cache",
        "data/logs", 
        "data/backups",
        "data/exports",
        "data/strategies"
    ]
    
    for dir_path in data_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    console.print("📁 Répertoires de données initialisés", style="green")


def initialize_app() -> bool:
    """
    Initialise l'application FinAgent.
    
    Returns:
        bool: True si l'initialisation réussit
    """
    try:
        # TODO: Implémenter l'initialisation complète
        # 1. Charger la configuration
        # settings = Settings()
        
        # 2. Configurer le logging
        # setup_logging(settings.logging)
        
        # 3. Configurer la gestion d'erreurs  
        # setup_error_handling()
        
        # 4. Initialiser le conteneur DI
        # setup_container()
        
        # 5. Vérifier la connectivité aux APIs
        # await verify_api_connections()
        
        console.print("🚀 FinAgent initialisé avec succès", style="green")
        return True
        
    except Exception as e:
        console.print(f"❌ Erreur lors de l'initialisation: {e}", style="red")
        return False


@click.command()
@click.option(
    "--config", 
    "-c",
    type=click.Path(exists=True),
    default="config.yaml",
    help="Chemin vers le fichier de configuration"
)
@click.option(
    "--verbose", 
    "-v",
    is_flag=True,
    help="Active le mode verbose"
)
@click.option(
    "--debug",
    is_flag=True,
    help="Active le mode debug"
)
@click.version_option()
def main(config: Optional[str], verbose: bool, debug: bool):
    """
    🤖 FinAgent - Agent IA pour analyse d'actions financières
    
    Analysez vos investissements avec l'intelligence artificielle Claude
    et les données financières de qualité institutionnelle d'OpenBB.
    """
    
    # Affichage du message de bienvenue
    if not debug:
        print_welcome()
    
    # Configuration du mode verbose
    if verbose:
        console.print("🔍 Mode verbose activé", style="yellow")
    
    if debug:
        console.print("🐛 Mode debug activé", style="yellow")
        
    # Vérification des prérequis
    console.print("🔍 Vérification des prérequis...", style="blue")
    if not check_requirements():
        sys.exit(1)
    
    # Configuration des répertoires
    setup_data_directories()
    
    # Initialisation de l'application
    console.print("⚙️  Initialisation de FinAgent...", style="blue")
    if not initialize_app():
        sys.exit(1)
    
    # TODO: Lancement de l'interface CLI principale
    console.print("💡 Interface CLI en cours de développement...", style="yellow")
    console.print("🎯 Commandes à venir:", style="cyan")
    console.print("   • finagent analyze --symbol AAPL", style="dim")
    console.print("   • finagent strategy create --template momentum", style="dim")
    console.print("   • finagent portfolio status", style="dim")
    console.print("   • finagent config setup", style="dim")
    
    # Pour le moment, juste confirmer que l'app démarre
    console.print("✅ FinAgent démarré avec succès!", style="green bold")


def cli_entry_point():
    """
    Point d'entrée pour le script console défini dans pyproject.toml.
    Cette fonction sera appelée quand on execute 'finagent' en ligne de commande.
    """
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n👋 Au revoir!", style="yellow")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n💥 Erreur inattendue: {e}", style="red bold")
        if "--debug" in sys.argv:
            raise
        sys.exit(1)


if __name__ == "__main__":
    cli_entry_point()