#!/usr/bin/env python3
"""
Script d'installation et configuration Ollama pour FinAgent.

Ce script automatise l'installation d'Ollama et le téléchargement des modèles recommandés.
"""

import asyncio
import os
import sys
import platform
import subprocess
import time
from pathlib import Path
from typing import List, Optional

import requests
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel
from rich.table import Table

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from finagent.ai.providers.ollama_provider import create_ollama_provider
from finagent.ai.models.base import ModelType

console = Console()


class OllamaInstaller:
    """Installateur automatique pour Ollama."""
    
    def __init__(self):
        self.console = console
        self.system = platform.system().lower()
        self.architecture = platform.machine().lower()
        
        # Modèles recommandés par taille
        self.recommended_models = {
            "small": [
                ModelType.GEMMA_2B,
                ModelType.PHI3_MINI,
            ],
            "medium": [
                ModelType.LLAMA3_1_8B,
                ModelType.MISTRAL_7B,
                ModelType.GEMMA_7B,
                ModelType.CODELLAMA_7B,
            ],
            "large": [
                ModelType.LLAMA3_1_70B,
                ModelType.CODELLAMA_13B,
                ModelType.MISTRAL_22B,
            ]
        }
    
    def check_system_requirements(self) -> bool:
        """Vérifie les prérequis système."""
        console.print("[cyan]Vérification des prérequis système...[/cyan]")
        
        # Vérification de l'OS
        if self.system not in ["linux", "darwin", "windows"]:
            console.print(f"[red]❌ Système d'exploitation non supporté: {self.system}[/red]")
            return False
        
        console.print(f"[green]✅ Système: {platform.system()} {platform.release()}[/green]")
        
        # Vérification de l'architecture
        if "arm" in self.architecture or "aarch64" in self.architecture:
            console.print(f"[green]✅ Architecture: {self.architecture} (optimisé pour ARM)[/green]")
        elif "x86_64" in self.architecture or "amd64" in self.architecture:
            console.print(f"[green]✅ Architecture: {self.architecture}[/green]")
        else:
            console.print(f"[yellow]⚠️ Architecture: {self.architecture} (non testée)[/yellow]")
        
        # Vérification de la RAM
        try:
            import psutil
            memory_gb = psutil.virtual_memory().total / (1024**3)
            console.print(f"[green]✅ RAM: {memory_gb:.1f} GB[/green]")
            
            if memory_gb < 4:
                console.print("[yellow]⚠️ RAM faible - recommandé: au moins 8GB pour de bonnes performances[/yellow]")
            elif memory_gb < 8:
                console.print("[yellow]💡 Pour les gros modèles (70B+), 16GB+ de RAM recommandés[/yellow]")
        except ImportError:
            console.print("[yellow]⚠️ Impossible de vérifier la RAM (psutil non installé)[/yellow]")
        
        return True
    
    def is_ollama_installed(self) -> bool:
        """Vérifie si Ollama est déjà installé."""
        try:
            result = subprocess.run(["ollama", "--version"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                version = result.stdout.strip()
                console.print(f"[green]✅ Ollama déjà installé: {version}[/green]")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        console.print("[yellow]📦 Ollama non trouvé - installation requise[/yellow]")
        return False
    
    def install_ollama(self) -> bool:
        """Installe Ollama selon le système d'exploitation."""
        console.print("[cyan]Installation d'Ollama...[/cyan]")
        
        try:
            if self.system == "linux" or self.system == "darwin":
                # Installation via script curl pour Linux/macOS
                console.print("Téléchargement et exécution du script d'installation...")
                
                # Télécharge le script d'installation
                response = requests.get("https://ollama.ai/install.sh", timeout=30)
                response.raise_for_status()
                
                # Exécute le script
                process = subprocess.Popen(
                    ["sh"],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                stdout, stderr = process.communicate(input=response.text)
                
                if process.returncode == 0:
                    console.print("[green]✅ Ollama installé avec succès[/green]")
                    return True
                else:
                    console.print(f"[red]❌ Erreur d'installation: {stderr}[/red]")
                    return False
            
            elif self.system == "windows":
                console.print("[yellow]Installation manuelle requise pour Windows:[/yellow]")
                console.print("1. Visitez https://ollama.ai/download")
                console.print("2. Téléchargez l'installateur Windows")
                console.print("3. Exécutez l'installateur")
                console.print("4. Redémarrez ce script après l'installation")
                return False
            
        except Exception as e:
            console.print(f"[red]❌ Erreur lors de l'installation: {e}[/red]")
            return False
        
        return False
    
    def start_ollama_service(self) -> bool:
        """Démarre le service Ollama."""
        console.print("[cyan]Démarrage du service Ollama...[/cyan]")
        
        try:
            # Vérifie si le service est déjà en cours
            result = subprocess.run(
                ["curl", "-s", "http://localhost:11434/api/version"],
                capture_output=True, timeout=5
            )
            
            if result.returncode == 0:
                console.print("[green]✅ Service Ollama déjà en cours[/green]")
                return True
            
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        try:
            # Démarre Ollama en arrière-plan
            if self.system == "windows":
                subprocess.Popen(["ollama", "serve"], creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Attend que le service soit prêt
            console.print("Attente du démarrage du service...")
            for i in range(30):  # 30 secondes max
                try:
                    result = subprocess.run(
                        ["curl", "-s", "http://localhost:11434/api/version"],
                        capture_output=True, timeout=2
                    )
                    if result.returncode == 0:
                        console.print("[green]✅ Service Ollama démarré[/green]")
                        return True
                except:
                    pass
                
                time.sleep(1)
            
            console.print("[red]❌ Timeout - impossible de démarrer le service[/red]")
            return False
            
        except Exception as e:
            console.print(f"[red]❌ Erreur lors du démarrage: {e}[/red]")
            return False
    
    async def test_ollama_connection(self) -> bool:
        """Teste la connexion à Ollama."""
        console.print("[cyan]Test de connexion à Ollama...[/cyan]")
        
        try:
            provider = create_ollama_provider()
            connected = await provider.validate_connection()
            
            if connected:
                console.print("[green]✅ Connexion Ollama réussie[/green]")
                
                # Affiche les modèles déjà installés
                models = await provider.get_available_models_info()
                if models:
                    console.print(f"[blue]📦 {len(models)} modèle(s) déjà installé(s)[/blue]")
                    for model in models[:3]:  # Affiche les 3 premiers
                        console.print(f"   • {model.name} ({model.size_gb:.1f}GB)")
                    if len(models) > 3:
                        console.print(f"   • ... et {len(models) - 3} autre(s)")
                
                return True
            else:
                console.print("[red]❌ Impossible de se connecter à Ollama[/red]")
                return False
                
        except Exception as e:
            console.print(f"[red]❌ Erreur de connexion: {e}[/red]")
            return False
    
    def select_models_to_install(self) -> List[ModelType]:
        """Interface interactive pour sélectionner les modèles à installer."""
        console.print("\n[cyan]Sélection des modèles à installer[/cyan]")
        
        # Affiche les options de taille
        table = Table(title="Catégories de modèles")
        table.add_column("Taille", style="cyan")
        table.add_column("Modèles", style="white")
        table.add_column("RAM requise", style="yellow")
        table.add_column("Description", style="dim")
        
        table.add_row(
            "Small", 
            "Gemma 2B, Phi3 Mini", 
            "4-6 GB",
            "Rapides, bonne qualité générale"
        )
        table.add_row(
            "Medium", 
            "Llama 3.1 8B, Mistral 7B", 
            "8-12 GB",
            "Équilibre performance/qualité"
        )
        table.add_row(
            "Large", 
            "Llama 3.1 70B, CodeLlama 13B", 
            "16+ GB",
            "Haute qualité, plus lents"
        )
        
        console.print(table)
        
        while True:
            choice = console.input("\n[yellow]Choisissez une catégorie (small/medium/large/custom/skip): [/yellow]").lower().strip()
            
            if choice == "skip":
                return []
            elif choice in ["small", "medium", "large"]:
                selected_models = self.recommended_models[choice]
                console.print(f"[green]Sélection: {len(selected_models)} modèles de taille {choice}[/green]")
                return selected_models
            elif choice == "custom":
                return self._select_custom_models()
            else:
                console.print("[red]Choix invalide. Utilisez: small, medium, large, custom, ou skip[/red]")
    
    def _select_custom_models(self) -> List[ModelType]:
        """Sélection personnalisée de modèles."""
        console.print("\n[cyan]Sélection personnalisée de modèles[/cyan]")
        
        all_models = []
        for category_models in self.recommended_models.values():
            all_models.extend(category_models)
        
        # Supprime les doublons
        unique_models = list(set(all_models))
        unique_models.sort(key=lambda x: x.value)
        
        console.print("Modèles disponibles:")
        for i, model in enumerate(unique_models, 1):
            console.print(f"  {i:2d}. {model.value}")
        
        selected = []
        while True:
            choice = console.input("\n[yellow]Entrez les numéros des modèles (ex: 1,3,5) ou 'done': [/yellow]").strip()
            
            if choice.lower() == "done":
                break
            
            try:
                indices = [int(x.strip()) - 1 for x in choice.split(",")]
                for idx in indices:
                    if 0 <= idx < len(unique_models):
                        model = unique_models[idx]
                        if model not in selected:
                            selected.append(model)
                            console.print(f"[green]✅ Ajouté: {model.value}[/green]")
                        else:
                            console.print(f"[yellow]⚠️ Déjà sélectionné: {model.value}[/yellow]")
                    else:
                        console.print(f"[red]❌ Index invalide: {idx + 1}[/red]")
            except ValueError:
                console.print("[red]❌ Format invalide. Utilisez des numéros séparés par des virgules.[/red]")
        
        return selected
    
    async def install_models(self, models: List[ModelType]) -> bool:
        """Installe les modèles sélectionnés."""
        if not models:
            console.print("[yellow]Aucun modèle à installer[/yellow]")
            return True
        
        console.print(f"\n[cyan]Installation de {len(models)} modèle(s)...[/cyan]")
        
        provider = create_ollama_provider()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            
            overall_task = progress.add_task("Installation globale", total=len(models))
            
            for i, model in enumerate(models, 1):
                model_task = progress.add_task(f"Installation {model.value}", total=100)
                
                try:
                    console.print(f"\n[blue]📥 Installation de {model.value} ({i}/{len(models)})[/blue]")
                    
                    # Simule le progrès (Ollama ne fournit pas de callback de progrès)
                    for j in range(0, 101, 10):
                        progress.update(model_task, completed=j)
                        await asyncio.sleep(0.1)
                    
                    success = await provider.pull_model(model.value)
                    
                    if success:
                        progress.update(model_task, completed=100)
                        progress.update(overall_task, advance=1)
                        console.print(f"[green]✅ {model.value} installé avec succès[/green]")
                    else:
                        console.print(f"[red]❌ Échec de l'installation de {model.value}[/red]")
                        
                except Exception as e:
                    console.print(f"[red]❌ Erreur lors de l'installation de {model.value}: {e}[/red]")
        
        console.print("\n[green]🎉 Installation des modèles terminée[/green]")
        return True
    
    async def run_setup(self):
        """Exécute le processus complet d'installation."""
        console.print(Panel.fit("🤖 Configuration Ollama pour FinAgent", style="cyan bold"))
        
        # 1. Vérification des prérequis
        if not self.check_system_requirements():
            return False
        
        # 2. Vérification/Installation d'Ollama
        if not self.is_ollama_installed():
            if not self.install_ollama():
                return False
        
        # 3. Démarrage du service
        if not self.start_ollama_service():
            return False
        
        # 4. Test de connexion
        if not await self.test_ollama_connection():
            return False
        
        # 5. Sélection et installation des modèles
        models_to_install = self.select_models_to_install()
        if models_to_install:
            await self.install_models(models_to_install)
        
        # 6. Configuration finale
        console.print("\n[green]🎉 Configuration Ollama terminée avec succès![/green]")
        console.print("\n[cyan]Prochaines étapes:[/cyan]")
        console.print("1. [white]Configurez vos variables d'environnement dans .env[/white]")
        console.print("2. [white]Testez la configuration: finagent ai status[/white]")
        console.print("3. [white]Analysez une action: finagent analyze AAPL --provider ollama[/white]")
        
        return True


async def main():
    """Point d'entrée principal."""
    try:
        installer = OllamaInstaller()
        success = await installer.run_setup()
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        console.print("\n[yellow]👋 Installation interrompue par l'utilisateur[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]💥 Erreur inattendue: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())