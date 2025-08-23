"""
Commandes CLI pour la gestion de la configuration.
"""

import click
from rich.console import Console
from rich.table import Table

from ...core.config import get_config

console = Console()


@click.group()
def config_group():
    """Commandes pour la gestion de la configuration."""
    pass


@config_group.command()
def show():
    """Affiche la configuration actuelle."""
    try:
        config = get_config()
        
        table = Table(title="⚙️ Configuration FinAgent")
        table.add_column("Paramètre", style="cyan")
        table.add_column("Valeur", style="green")
        
        # Configuration générale
        table.add_row("Environnement", getattr(config, 'environment', 'development'))
        table.add_row("Niveau de log", getattr(config, 'log_level', 'INFO'))
        table.add_row("Répertoire de données", getattr(config, 'data_dir', './data'))
        
        # Configuration de cache
        if hasattr(config, 'cache'):
            table.add_row("Cache TTL", str(getattr(config.cache, 'ttl', 300)))
            table.add_row("Cache max size", str(getattr(config.cache, 'maxsize', 1000)))
        
        # Configuration trading
        if hasattr(config, 'trading'):
            table.add_row("Position par défaut", f"${getattr(config.trading, 'default_position_size', 1000)}")
            table.add_row("Limite de risque", f"{getattr(config.trading, 'default_risk_limit', 2.0)}%")
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]❌ Erreur lors de la lecture de la configuration: {e}[/red]")


@config_group.command()
@click.option('--key', required=True, help='Clé de configuration à modifier')
@click.option('--value', required=True, help='Nouvelle valeur')
def set(key: str, value: str):
    """Modifie une valeur de configuration."""
    try:
        console.print(f"[yellow]⚠️ Modification de configuration non implémentée pour: {key}={value}[/yellow]")
        console.print("Modifiez directement le fichier .env ou config.yaml")
        
    except Exception as e:
        console.print(f"[red]❌ Erreur lors de la modification: {e}[/red]")


@config_group.command()
def validate():
    """Valide la configuration actuelle."""
    try:
        config = get_config()
        
        console.print("✅ Configuration valide!")
        console.print(f"Fichier de configuration: {getattr(config, '_config_file', 'config.yaml')}")
        
    except Exception as e:
        console.print(f"[red]❌ Configuration invalide: {e}[/red]")


if __name__ == "__main__":
    config_group()