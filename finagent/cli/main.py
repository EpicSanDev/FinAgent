"""
Interface CLI principale pour FinAgent.
"""

import click
from rich.console import Console

# Import des groupes de commandes
from .commands.ai_commands import ai_group
from .commands.config_commands import config_group
from .commands.analyze_command import analyze

console = Console()


@click.group()
@click.option("--config", "-c", help="Chemin vers le fichier de configuration")
@click.option("--verbose", "-v", is_flag=True, help="Mode verbose")
@click.option("--debug", is_flag=True, help="Mode debug")
@click.pass_context
def cli(ctx, config, verbose, debug):
    """🤖 FinAgent - Agent IA pour analyse financière"""
    ctx.ensure_object(dict)
    ctx.obj["config"] = config
    ctx.obj["verbose"] = verbose
    ctx.obj["debug"] = debug


# Ajout des groupes de commandes
cli.add_command(ai_group, name="ai")
cli.add_command(config_group, name="config")
cli.add_command(analyze, name="analyze")


if __name__ == "__main__":
    cli()