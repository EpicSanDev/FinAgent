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

# Imports locaux
from finagent.cli.main import cli
from finagent.ai import (
    get_ai_factory, 
    initialize_discovery_service,
    shutdown_ai_factory,
    shutdown_discovery_service
)
from finagent.ai.config import get_ai_config

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
        import ollama  # noqa: F401
        import anthropic  # noqa: F401
        
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


async def initialize_app() -> bool:
    """
    Initialise l'application FinAgent.
    
    Returns:
        bool: True si l'initialisation réussit
    """
    try:
        console.print("⚙️ Initialisation de la configuration AI...", style="blue")
        
        # 1. Charger et valider la configuration AI
        ai_config = get_ai_config()
        validation = ai_config.validate()
        
        if not validation["valid"]:
            console.print("⚠️ Configuration AI incomplète:", style="yellow")
            for error in validation["errors"]:
                console.print(f"   • {error}", style="red")
            for warning in validation["warnings"]:
                console.print(f"   • {warning}", style="yellow")
        
        # 2. Initialiser la factory AI
        console.print("🤖 Initialisation des services AI...", style="blue")
        factory = await get_ai_factory()
        
        if not factory:
            console.print("❌ Échec de l'initialisation de la factory AI", style="red")
            return False
        
        # 3. Initialiser le service de discovery Ollama
        if ai_config.enable_auto_discovery:
            console.print("🔍 Initialisation du service de discovery...", style="blue")
            discovery_success = await initialize_discovery_service(ai_config.ollama)
            
            if discovery_success:
                console.print("✅ Service de discovery initialisé", style="green")
            else:
                console.print("⚠️ Service de discovery non disponible (Ollama non accessible)", style="yellow")
        
        # 4. Vérification des providers
        console.print("🔗 Vérification des providers...", style="blue")
        health_status = factory.get_provider_health_status()
        
        available_providers = []
        for provider, status in health_status.items():
            if status.get("available", False):
                available_providers.append(provider)
                console.print(f"   ✅ {provider} disponible", style="green")
            else:
                error_msg = status.get("error", "Inconnu")
                console.print(f"   ❌ {provider} indisponible ({error_msg})", style="red")
        
        if not available_providers:
            console.print("❌ Aucun provider AI disponible", style="red")
            return False
        
        console.print(f"🚀 FinAgent initialisé avec {len(available_providers)} provider(s) disponible(s)", style="green")
        return True
        
    except Exception as e:
        console.print(f"❌ Erreur lors de l'initialisation: {e}", style="red")
        return False


async def shutdown_app():
    """Arrêt propre de l'application."""
    try:
        await shutdown_discovery_service()
        await shutdown_ai_factory()
    except Exception as e:
        console.print(f"⚠️ Erreur lors de l'arrêt: {e}", style="yellow")


async def run_simple_mode(config: Optional[str], verbose: bool, debug: bool):
    """Mode de démarrage simple (sans arguments CLI)."""
    
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
    console.print("⚙️ Initialisation de FinAgent...", style="blue")
    if not await initialize_app():
        sys.exit(1)
    
    # Lancement de l'interface CLI principale
    console.print("🎯 Commandes disponibles:", style="cyan")
    console.print("   • finagent ai status          - Statut des services IA", style="dim")
    console.print("   • finagent ai models          - Liste des modèles disponibles", style="dim")
    console.print("   • finagent ai test            - Test de connectivité", style="dim")
    console.print("   • finagent config show        - Afficher la configuration", style="dim")
    console.print("   • finagent config setup       - Configuration interactive", style="dim")
    console.print("   • finagent analyze SYMBOL     - Analyser un titre", style="dim")
    
    console.print("✅ FinAgent démarré avec succès!", style="green bold")
    
    # Arrêt propre des services
    await shutdown_app()


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
    
    Analysez vos investissements avec l'IA (Claude + Ollama) 
    et les données financières de qualité institutionnelle d'OpenBB.
    """
    # Exécute le mode simple avec async
    asyncio.run(run_simple_mode(config, verbose, debug))


def main_cli():
    """Point d'entrée pour l'interface CLI complète."""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n👋 Au revoir!", style="yellow")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n💥 Erreur inattendue: {e}", style="red bold")
        if "--debug" in sys.argv:
            raise
        sys.exit(1)


def cli_entry_point():
    """
    Point d'entrée pour le script console défini dans pyproject.toml.
    Cette fonction sera appelée quand on execute 'finagent' en ligne de commande.
    """
    # Si des arguments CLI sont fournis, utilise l'interface CLI complète
    if len(sys.argv) > 1:
        main_cli()
    else:
        # Sinon, utilise le mode de démarrage simple
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