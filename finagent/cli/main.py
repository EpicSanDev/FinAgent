"""
CLI principal pour FinAgent.

Point d'entrée principal pour l'interface en ligne de commande
de FinAgent avec toutes les commandes développées.
"""

import click
from rich.console import Console

# Import des commandes développées
from .commands.analyze_command import analyze
from .commands.portfolio_command import portfolio
from .commands.strategy_command import strategy
from .commands.decision_command import decision
from .commands.config_command import config

from finagent import __version__
from finagent.core.errors.exceptions import FinAgentException

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="finagent")
@click.option(
    "--config", 
    "-c",
    type=click.Path(exists=True),
    help="Chemin vers le fichier de configuration"
)
@click.option("--verbose", "-v", is_flag=True, help="Mode verbose")
@click.option("--debug", is_flag=True, help="Mode debug")
@click.option("--interactive", is_flag=True, help="Mode interactif (REPL)")
@click.option("--wizard", is_flag=True, help="Assistant de configuration")
@click.option("--menu", is_flag=True, help="Système de menus")
@click.pass_context
def cli(ctx, config, verbose, debug, interactive, wizard, menu):
    """
    🤖 FinAgent - Agent IA pour analyse d'actions financières
    
    Analysez vos investissements avec Claude AI et les données OpenBB.
    """
    # Configuration du contexte global
    ctx.ensure_object(dict)
    ctx.obj['config'] = config
    ctx.obj['verbose'] = verbose
    ctx.obj['debug'] = debug
    
    if verbose:
        console.print("🔍 Mode verbose activé", style="yellow")
    if debug:
        console.print("🐛 Mode debug activé", style="yellow")
    
    # Gestion des modes interactifs
    if wizard:
        try:
            from .interactive import run_wizard_sync
            console.print("🚀 Lancement de l'assistant de configuration...", style="cyan")
            run_wizard_sync()
        except ImportError:
            console.print("❌ Interface wizard non disponible (dépendances manquantes)", style="red")
            console.print("💡 Installez: pip install prompt-toolkit", style="yellow")
        return
    
    if menu:
        try:
            from .interactive import run_menu_system_sync
            console.print("📋 Lancement du système de menus...", style="cyan")
            run_menu_system_sync()
        except ImportError:
            console.print("❌ Interface menu non disponible (dépendances manquantes)", style="red")
            console.print("💡 Installez: pip install prompt-toolkit", style="yellow")
        return
    
    if interactive:
        try:
            from .interactive import run_repl_sync
            console.print("🎯 Lancement du REPL interactif...", style="cyan")
            run_repl_sync()
        except ImportError:
            console.print("❌ Interface REPL non disponible (dépendances manquantes)", style="red")
            console.print("💡 Installez: pip install prompt-toolkit", style="yellow")
        return


# Ajout des commandes développées
cli.add_command(analyze)
cli.add_command(portfolio)
cli.add_command(strategy)
cli.add_command(decision)
cli.add_command(config)


@cli.command()
def version():
    """Affiche la version de FinAgent."""
    console.print("🤖 [bold cyan]FinAgent v1.0.0[/bold cyan]", style="cyan")
    console.print("Agent IA pour l'analyse financière", style="dim")
    console.print("\n📦 [yellow]Modules disponibles :[/yellow]")
    console.print("• 📊 Analyse de marché et d'actions")
    console.print("• 💼 Gestion de portefeuilles")
    console.print("• 📋 Stratégies d'investissement")
    console.print("• 🎯 Décisions de trading")
    console.print("• ⚙️  Configuration et paramètres")
    console.print("\n🎯 [yellow]Interfaces disponibles :[/yellow]")
    console.print("• [cyan]--interactive[/cyan] : REPL avec auto-complétion")
    console.print("• [cyan]--wizard[/cyan] : Assistant de configuration")
    console.print("• [cyan]--menu[/cyan] : Navigation par menus")


if __name__ == "__main__":
    try:
        cli()
    except FinAgentException as e:
        console.print(f"❌ Erreur FinAgent: {e.message}", style="red")
        if e.error_code:
            console.print(f"Code d'erreur: {e.error_code}", style="dim")
    except Exception as e:
        console.print(f"💥 Erreur inattendue: {e}", style="red bold")
        raise