"""
Commandes CLI pour la gestion IA.
"""

import asyncio
import click
from rich.console import Console
from rich.table import Table

from ...ai import (
    get_ai_config,
    get_service_status,
    get_available_models,
    initialize_ai_system,
    shutdown_ai_system
)

console = Console()


@click.group()
def ai_group():
    """Commandes pour la gestion de l'intelligence artificielle."""
    pass


@ai_group.command()
def status():
    """Affiche le statut des services IA."""
    try:
        status_data = asyncio.run(get_service_status())
        
        table = Table(title="📊 Statut des Services IA")
        table.add_column("Service", style="cyan")
        table.add_column("Statut", style="green")
        table.add_column("Details", style="yellow")
        
        # Services principaux
        for service, is_active in status_data.items():
            if service != "providers":
                status_text = "✅ Actif" if is_active else "❌ Inactif"
                table.add_row(service.replace("_", " ").title(), status_text, "")
        
        # Providers
        if "providers" in status_data:
            for provider, info in status_data["providers"].items():
                status_text = "✅ Disponible" if info.get("available", False) else "❌ Indisponible"
                error_info = info.get("error", "")
                table.add_row(f"Provider {provider.title()}", status_text, error_info)
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]❌ Erreur lors de la vérification du statut: {e}[/red]")


@ai_group.command()
def models():
    """Liste les modèles IA disponibles."""
    try:
        models_data = asyncio.run(get_available_models())
        
        table = Table(title="🤖 Modèles IA Disponibles")
        table.add_column("Provider", style="cyan")
        table.add_column("Modèles", style="green")
        
        for provider, model_list in models_data.items():
            models_text = "\n".join(model_list) if model_list else "Aucun modèle disponible"
            table.add_row(provider.title(), models_text)
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]❌ Erreur lors de la récupération des modèles: {e}[/red]")


@ai_group.command()
def test():
    """Teste la connectivité avec les providers IA."""
    try:
        console.print("🔗 Test de connectivité en cours...", style="blue")
        
        # Test simple de connexion
        status_data = asyncio.run(get_service_status())
        
        if "providers" in status_data:
            table = Table(title="🔍 Test de Connectivité")
            table.add_column("Provider", style="cyan")
            table.add_column("Statut", style="bold")
            table.add_column("Temps de réponse", style="yellow")
            
            for provider, info in status_data["providers"].items():
                available = info.get("available", False)
                status_style = "green" if available else "red"
                status_text = "✅ Connecté" if available else "❌ Déconnecté"
                
                response_time = info.get("response_time_ms")
                response_text = f"{response_time:.1f}ms" if response_time else "N/A"
                
                table.add_row(
                    provider.title(),
                    f"[{status_style}]{status_text}[/{status_style}]",
                    response_text
                )
            
            console.print(table)
        else:
            console.print("[red]❌ Aucun provider disponible[/red]")
            
    except Exception as e:
        console.print(f"[red]❌ Erreur lors du test: {e}[/red]")


@ai_group.command()
def config():
    """Affiche la configuration IA actuelle."""
    try:
        ai_config = get_ai_config()
        validation = ai_config.validate()
        
        table = Table(title="⚙️ Configuration IA")
        table.add_column("Paramètre", style="cyan")
        table.add_column("Valeur", style="green")
        
        table.add_row("Provider préféré", str(ai_config.preferred_provider or "Auto"))
        table.add_row("Stratégie de fallback", ai_config.fallback_strategy.value)
        table.add_row("Auto-discovery", "✅ Activé" if ai_config.enable_auto_discovery else "❌ Désactivé")
        table.add_row("Configuration valide", "✅ Oui" if validation["valid"] else "❌ Non")
        
        console.print(table)
        
        if validation["errors"]:
            console.print("\n[red]❌ Erreurs de configuration:[/red]")
            for error in validation["errors"]:
                console.print(f"  • {error}")
        
        if validation["warnings"]:
            console.print("\n[yellow]⚠️ Avertissements:[/yellow]")
            for warning in validation["warnings"]:
                console.print(f"  • {warning}")
                
    except Exception as e:
        console.print(f"[red]❌ Erreur lors de la lecture de la configuration: {e}[/red]")


@ai_group.command()
def init():
    """Initialise les services IA."""
    try:
        console.print("🚀 Initialisation des services IA...")
        initialize_ai_system()
        console.print("[green]✅ Services IA initialisés avec succès![/green]")
        
    except Exception as e:
        console.print(f"[red]❌ Erreur lors de l'initialisation: {e}[/red]")


@ai_group.command()
def shutdown():
    """Arrête les services IA."""
    try:
        console.print("🛑 Arrêt des services IA...")
        shutdown_ai_system()
        console.print("[green]✅ Services IA arrêtés avec succès![/green]")
        
    except Exception as e:
        console.print(f"[red]❌ Erreur lors de l'arrêt: {e}[/red]")


if __name__ == "__main__":
    ai_group()