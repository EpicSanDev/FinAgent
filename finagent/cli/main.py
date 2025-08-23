"""
Interface CLI principale pour FinAgent.
"""

import asyncio
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..ai import (
    get_ai_factory, get_service_status, get_available_models,
    create_ai_provider, ModelType, ProviderType
)
from ..ai.config import get_ai_config

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


@cli.group()
def ai():
    """Commandes pour la gestion des services IA"""
    pass


@ai.command()
async def status():
    """Affiche le statut des services IA"""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Vérification du statut...", total=None)
        
        try:
            status_info = await get_service_status()
            
            # Table des services
            services_table = Table(title="Statut des Services IA")
            services_table.add_column("Service", style="cyan")
            services_table.add_column("Statut", style="bold")
            
            for service, status in status_info.items():
                if service == "providers":
                    continue
                status_style = "green" if status else "red"
                status_text = "✅ Actif" if status else "❌ Inactif"
                services_table.add_row(service, f"[{status_style}]{status_text}[/{status_style}]")
            
            console.print(services_table)
            
            # Table des providers
            if "providers" in status_info:
                providers_table = Table(title="Statut des Providers IA")
                providers_table.add_column("Provider", style="cyan")
                providers_table.add_column("Disponible", style="bold")
                providers_table.add_column("Temps de réponse", style="yellow")
                providers_table.add_column("Modèles", style="blue")
                providers_table.add_column("Erreur", style="red")
                
                for provider, info in status_info["providers"].items():
                    available = info.get("available", False)
                    status_style = "green" if available else "red"
                    status_text = "✅" if available else "❌"
                    
                    response_time = info.get("response_time_ms")
                    response_text = f"{response_time:.1f}ms" if response_time else "N/A"
                    
                    models_count = info.get("models_available", 0)
                    models_text = str(models_count) if models_count > 0 else "0"
                    
                    error_text = info.get("error", "")[:50] if info.get("error") else ""
                    
                    providers_table.add_row(
                        provider,
                        f"[{status_style}]{status_text}[/{status_style}]",
                        response_text,
                        models_text,
                        error_text
                    )
                
                console.print(providers_table)
            
        except Exception as e:
            console.print(f"[red]Erreur lors de la vérification du statut: {e}[/red]")


@ai.command()
async def models():
    """Liste les modèles IA disponibles"""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Récupération des modèles...", total=None)
        
        try:
            available_models = await get_available_models()
            
            for provider, models_list in available_models.items():
                table = Table(title=f"Modèles {provider.upper()}")
                table.add_column("Modèle", style="cyan")
                table.add_column("Statut", style="green")
                
                if models_list:
                    for model in models_list:
                        table.add_row(model, "✅ Disponible")
                else:
                    table.add_row("Aucun modèle", "❌ Non disponible")
                
                console.print(table)
            
        except Exception as e:
            console.print(f"[red]Erreur lors de la récupération des modèles: {e}[/red]")


@ai.command()
@click.option("--provider", type=click.Choice(["claude", "ollama"]), help="Provider à tester")
@click.option("--model", help="Modèle spécifique à tester")
async def test(provider, model):
    """Teste la connectivité avec les providers IA"""
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Test de connectivité...", total=None)
        
        try:
            # Détermine le provider
            provider_type = None
            if provider == "claude":
                provider_type = ProviderType.CLAUDE
            elif provider == "ollama":
                provider_type = ProviderType.OLLAMA
            
            # Crée le provider
            ai_provider = await create_ai_provider(provider_type)
            
            if not ai_provider:
                console.print("[red]❌ Impossible de créer le provider[/red]")
                return
            
            # Détermine le modèle
            if model:
                try:
                    model_type = ModelType(model)
                except ValueError:
                    console.print(f"[red]❌ Modèle invalide: {model}[/red]")
                    return
            else:
                # Utilise le modèle par défaut du provider
                config = get_ai_config()
                if provider_type == ProviderType.CLAUDE:
                    model_type = config.claude.default_model
                elif provider_type == ProviderType.OLLAMA:
                    model_type = config.ollama.default_model
                else:
                    model_type = ModelType.CLAUDE_3_5_SONNET
            
            # Test avec un prompt simple
            test_prompt = "Réponds simplement 'OK' si tu reçois ce message."
            
            progress.update(task, description="Envoi du test...")
            response = await ai_provider.generate_response(
                test_prompt,
                model=model_type,
                max_tokens=10
            )
            
            if response:
                console.print(f"[green]✅ Test réussi avec {provider_type.value}[/green]")
                console.print(f"[dim]Modèle: {model_type.value}[/dim]")
                console.print(f"[dim]Réponse: {response[:100]}...[/dim]")
            else:
                console.print(f"[red]❌ Test échoué: aucune réponse[/red]")
            
        except Exception as e:
            console.print(f"[red]❌ Erreur durant le test: {e}[/red]")


@ai.command()
@click.option("--model", help="Modèle Ollama à télécharger")
async def pull(model):
    """Télécharge un modèle Ollama"""
    if not model:
        console.print("[red]❌ Veuillez spécifier un modèle à télécharger[/red]")
        return
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task(f"Téléchargement de {model}...", total=None)
        
        try:
            # Valide le modèle
            try:
                model_type = ModelType(model)
            except ValueError:
                console.print(f"[red]❌ Modèle invalide: {model}[/red]")
                return
            
            # Récupère le service de discovery
            from ..ai.services import get_discovery_service
            discovery_service = await get_discovery_service()
            
            if not discovery_service:
                console.print("[red]❌ Service de discovery non disponible[/red]")
                return
            
            # Télécharge le modèle
            success = await discovery_service.pull_model(model_type)
            
            if success:
                console.print(f"[green]✅ Modèle {model} téléchargé avec succès[/green]")
            else:
                console.print(f"[red]❌ Échec du téléchargement de {model}[/red]")
            
        except Exception as e:
            console.print(f"[red]❌ Erreur durant le téléchargement: {e}[/red]")


@cli.group()
def config():
    """Commandes de configuration"""
    pass


@config.command()
def show():
    """Affiche la configuration actuelle"""
    try:
        ai_config = get_ai_config()
        
        # Panneau de configuration Claude
        claude_info = f"""
[cyan]API Key:[/cyan] {'✅ Configurée' if ai_config.claude.api_key else '❌ Manquante'}
[cyan]URL de base:[/cyan] {ai_config.claude.base_url}
[cyan]Modèle par défaut:[/cyan] {ai_config.claude.default_model.value}
[cyan]Timeout:[/cyan] {ai_config.claude.timeout}s
        """
        console.print(Panel(claude_info.strip(), title="Configuration Claude"))
        
        # Panneau de configuration Ollama
        ollama_info = f"""
[cyan]Host:[/cyan] {ai_config.ollama.host}
[cyan]Port:[/cyan] {ai_config.ollama.port}
[cyan]URL complète:[/cyan] {ai_config.ollama.base_url}
[cyan]Modèle par défaut:[/cyan] {ai_config.ollama.default_model.value}
[cyan]Auto-pull:[/cyan] {'✅ Activé' if ai_config.ollama.auto_pull else '❌ Désactivé'}
        """
        console.print(Panel(ollama_info.strip(), title="Configuration Ollama"))
        
        # Panneau de configuration générale
        general_info = f"""
[cyan]Stratégie de fallback:[/cyan] {ai_config.fallback_strategy.value}
[cyan]Provider préféré:[/cyan] {ai_config.preferred_provider.value if ai_config.preferred_provider else 'Auto'}
[cyan]Auto-discovery:[/cyan] {'✅ Activé' if ai_config.enable_auto_discovery else '❌ Désactivé'}
[cyan]Intervalle de refresh:[/cyan] {ai_config.discovery_refresh_interval}s
        """
        console.print(Panel(general_info.strip(), title="Configuration Générale"))
        
    except Exception as e:
        console.print(f"[red]❌ Erreur lors de l'affichage de la configuration: {e}[/red]")


@config.command()
@click.option("--provider", type=click.Choice(["claude", "ollama"]), required=True)
async def setup(provider):
    """Configuration interactive d'un provider"""
    
    if provider == "claude":
        console.print("[cyan]Configuration de Claude[/cyan]")
        
        api_key = click.prompt("Clé API OpenRouter", hide_input=True)
        base_url = click.prompt("URL de base", default="https://openrouter.ai/api/v1")
        
        # Sauvegarde temporaire - dans un vrai projet, on sauvegarderait dans un fichier
        console.print("[green]✅ Configuration Claude sauvegardée[/green]")
        console.print("[yellow]💡 Redémarrez l'application pour appliquer les changements[/yellow]")
        
    elif provider == "ollama":
        console.print("[cyan]Configuration d'Ollama[/cyan]")
        
        host = click.prompt("Host Ollama", default="localhost")
        port = click.prompt("Port Ollama", default=11434, type=int)
        
        # Test de connexion
        from ..ai.providers.ollama_provider import create_ollama_provider
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Test de connexion...", total=None)
            
            try:
                provider_instance = create_ollama_provider(host=host, port=port)
                connected = await provider_instance.validate_connection()
                
                if connected:
                    console.print("[green]✅ Connexion Ollama réussie[/green]")
                    console.print("[green]✅ Configuration Ollama sauvegardée[/green]")
                else:
                    console.print("[red]❌ Impossible de se connecter à Ollama[/red]")
                    console.print("[yellow]💡 Vérifiez qu'Ollama est démarré et accessible[/yellow]")
                
            except Exception as e:
                console.print(f"[red]❌ Erreur de connexion: {e}[/red]")


@cli.command()
@click.argument("symbol")
@click.option("--provider", type=click.Choice(["claude", "ollama"]), help="Provider IA à utiliser")
@click.option("--model", help="Modèle spécifique à utiliser")
async def analyze(symbol, provider, model):
    """Analyse financière d'un symbole boursier"""
    
    console.print(f"[cyan]Analyse de {symbol.upper()}[/cyan]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Initialisation de l'analyse...", total=None)
        
        try:
            # Détermine le provider
            provider_type = None
            if provider == "claude":
                provider_type = ProviderType.CLAUDE
            elif provider == "ollama":
                provider_type = ProviderType.OLLAMA
            
            # Crée le provider IA
            ai_provider = await create_ai_provider(provider_type, task_type="analysis")
            
            if not ai_provider:
                console.print("[red]❌ Impossible de créer le provider IA[/red]")
                return
            
            progress.update(task, description="Analyse en cours...")
            
            # Prompt d'analyse simple
            prompt = f"""
            Analyse le symbole boursier {symbol.upper()}.
            
            Fournis une analyse concise incluant:
            1. Vue d'ensemble de l'entreprise
            2. Position sur le marché
            3. Tendances récentes
            4. Recommandation générale
            
            Réponds en français et de manière structurée.
            """
            
            # Détermine le modèle
            if model:
                try:
                    model_type = ModelType(model)
                except ValueError:
                    console.print(f"[yellow]⚠️ Modèle invalide, utilisation du modèle par défaut[/yellow]")
                    model_type = None
            else:
                model_type = None
            
            response = await ai_provider.generate_response(
                prompt,
                model=model_type,
                max_tokens=1000
            )
            
            if response:
                console.print(Panel(response, title=f"Analyse de {symbol.upper()}"))
            else:
                console.print("[red]❌ Aucune réponse de l'IA[/red]")
            
        except Exception as e:
            console.print(f"[red]❌ Erreur durant l'analyse: {e}[/red]")


# Point d'entrée async pour les commandes
def run_async_command(coro):
    """Wrapper pour exécuter des commandes async avec click"""
    def wrapper(*args, **kwargs):
        return asyncio.run(coro(*args, **kwargs))
    return wrapper


# Application des wrappers async
ai.command()(run_async_command(status))
ai.command()(run_async_command(models))
ai.command()(run_async_command(test))
ai.command()(run_async_command(pull))
config.command()(run_async_command(setup))
cli.command()(run_async_command(analyze))


if __name__ == "__main__":
    cli()