"""
Assistant de configuration (Wizard) pour FinAgent.

Fournit une interface guidée pour configurer FinAgent
étape par étape pour les nouveaux utilisateurs.
"""

import asyncio
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import json

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm, IntPrompt, FloatPrompt
from rich.text import Text
from rich.align import Align

console = Console()


class FinAgentWizard:
    """Assistant de configuration guidé pour FinAgent."""
    
    def __init__(self):
        """Initialise le wizard."""
        self.config = {}
        self.current_step = 0
        self.total_steps = 7
        self.user_selections = {}
        
        # Étapes du wizard
        self.steps = [
            {
                'name': 'welcome',
                'title': '🎉 Bienvenue dans FinAgent',
                'description': 'Introduction et vérification des prérequis'
            },
            {
                'name': 'user_profile',
                'title': '👤 Profil Utilisateur',
                'description': 'Définition de votre profil d\'investisseur'
            },
            {
                'name': 'api_keys',
                'title': '🔑 Clés API',
                'description': 'Configuration des accès aux services externes'
            },
            {
                'name': 'portfolio_settings',
                'title': '📊 Configuration Portefeuille',
                'description': 'Paramètres de gestion de portefeuille'
            },
            {
                'name': 'ai_preferences',
                'title': '🤖 Préférences IA',
                'description': 'Configuration du moteur d\'analyse IA'
            },
            {
                'name': 'data_sources',
                'title': '📊 Sources de Données',
                'description': 'Configuration des fournisseurs de données'
            },
            {
                'name': 'finalization',
                'title': '✅ Finalisation',
                'description': 'Validation et sauvegarde de la configuration'
            }
        ]
    
    def _show_progress(self) -> None:
        """Affiche la progression du wizard."""
        progress_text = f"Étape {self.current_step + 1}/{self.total_steps}"
        current_step = self.steps[self.current_step]
        
        # Barre de progression visuelle
        progress_bar = "█" * (self.current_step + 1) + "░" * (self.total_steps - self.current_step - 1)
        
        console.print(Panel(
            f"[bold blue]{current_step['title']}[/bold blue]\n"
            f"{current_step['description']}\n\n"
            f"[cyan]{progress_text}[/cyan] {progress_bar}",
            border_style="blue",
            width=60
        ))
        console.print()
    
    def _step_welcome(self) -> bool:
        """Étape 1: Bienvenue et introduction."""
        self._show_progress()
        
        welcome_text = """
[bold green]🚀 Bienvenue dans l'assistant de configuration FinAgent ![/bold green]

Cet assistant vous guidera dans la configuration initiale de FinAgent,
votre agent IA pour l'analyse financière et la gestion de portefeuilles.

[yellow]📋 Ce que nous allons configurer :[/yellow]
• 👤 Votre profil d'investisseur
• 🔑 Les clés API pour accéder aux données
• 📊 Les paramètres de portefeuille
• 🤖 Les préférences du moteur IA
• 📊 Les sources de données

[cyan]⏱️  Temps estimé : 5-10 minutes[/cyan]

[dim]💡 Vous pourrez modifier ces paramètres plus tard avec 'finagent config'[/dim]
        """
        
        console.print(Panel(
            welcome_text.strip(),
            title="🎯 Assistant FinAgent",
            border_style="green",
            expand=False
        ))
        
        if not Confirm.ask("\n🚀 Prêt à commencer la configuration ?", default=True):
            console.print("❌ Configuration annulée", style="yellow")
            return False
        
        return True
    
    def _step_user_profile(self) -> bool:
        """Étape 2: Profil utilisateur."""
        self._show_progress()
        
        console.print("[bold cyan]👤 Définissons votre profil d'investisseur[/bold cyan]\n")
        
        # Expérience en investissement
        experience_choices = {
            'beginner': 'Débutant (moins de 1 an)',
            'intermediate': 'Intermédiaire (1-5 ans)', 
            'advanced': 'Avancé (5+ ans)',
            'expert': 'Expert (professionnel)'
        }
        
        console.print("📈 [yellow]Quelle est votre expérience en investissement ?[/yellow]")
        for key, desc in experience_choices.items():
            console.print(f"  • {key}: {desc}")
        
        experience = Prompt.ask(
            "Votre choix",
            choices=list(experience_choices.keys()),
            default='intermediate'
        )
        
        # Tolérance au risque
        risk_choices = {
            'conservative': 'Conservateur - Préserver le capital',
            'moderate': 'Modéré - Équilibre risque/rendement',
            'aggressive': 'Agressif - Maximiser les rendements'
        }
        
        console.print("\n⚖️  [yellow]Quelle est votre tolérance au risque ?[/yellow]")
        for key, desc in risk_choices.items():
            console.print(f"  • {key}: {desc}")
        
        risk_tolerance = Prompt.ask(
            "Votre choix",
            choices=list(risk_choices.keys()),
            default='moderate'
        )
        
        # Horizon d'investissement
        horizon_choices = {
            'short': 'Court terme (< 2 ans)',
            'medium': 'Moyen terme (2-10 ans)',
            'long': 'Long terme (> 10 ans)'
        }
        
        console.print("\n⏰ [yellow]Quel est votre horizon d'investissement principal ?[/yellow]")
        for key, desc in horizon_choices.items():
            console.print(f"  • {key}: {desc}")
        
        investment_horizon = Prompt.ask(
            "Votre choix",
            choices=list(horizon_choices.keys()),
            default='medium'
        )
        
        # Capital initial indicatif
        console.print("\n💰 [yellow]Capital d'investissement approximatif (pour calibrer les recommandations) ?[/yellow]")
        capital_ranges = [
            "< 10 000 USD",
            "10 000 - 50 000 USD", 
            "50 000 - 250 000 USD",
            "250 000 - 1 000 000 USD",
            "> 1 000 000 USD",
            "Préfère ne pas préciser"
        ]
        
        for i, range_desc in enumerate(capital_ranges, 1):
            console.print(f"  {i}. {range_desc}")
        
        capital_choice = IntPrompt.ask(
            "Votre choix (1-6)",
            choices=[str(i) for i in range(1, 7)],
            default=2
        )
        
        # Sauvegarde du profil
        self.user_selections['profile'] = {
            'experience': experience,
            'risk_tolerance': risk_tolerance,
            'investment_horizon': investment_horizon,
            'capital_range': capital_ranges[capital_choice - 1]
        }
        
        # Configuration dérivée
        self.config['preferences'] = {
            'risk_tolerance': risk_tolerance,
            'default_currency': 'USD',
            'max_position_size': 0.05 if risk_tolerance == 'conservative' else 0.1 if risk_tolerance == 'moderate' else 0.2,
            'enable_notifications': True,
            'auto_save_decisions': experience in ['beginner', 'intermediate']
        }
        
        # Récapitulatif
        console.print(f"\n✅ [green]Profil configuré :[/green]")
        console.print(f"  • Expérience: {experience_choices[experience]}")
        console.print(f"  • Tolérance au risque: {risk_choices[risk_tolerance]}")
        console.print(f"  • Horizon: {horizon_choices[investment_horizon]}")
        
        return True
    
    def _step_api_keys(self) -> bool:
        """Étape 3: Configuration des clés API."""
        self._show_progress()
        
        console.print("[bold cyan]🔑 Configuration des clés API[/bold cyan]\n")
        
        api_info = {
            'openrouter': {
                'name': 'OpenRouter',
                'description': 'Accès aux modèles IA (Claude, GPT, etc.)',
                'required': True,
                'url': 'https://openrouter.ai/keys'
            },
            'openbb': {
                'name': 'OpenBB',
                'description': 'Données financières complètes',
                'required': False,
                'url': 'https://my.openbb.co/app/platform/credentials'
            },
            'alpha_vantage': {
                'name': 'Alpha Vantage',
                'description': 'Données de marché alternatives',
                'required': False,
                'url': 'https://www.alphavantage.co/support/#api-key'
            }
        }
        
        console.print("[yellow]💡 Les clés API permettent d'accéder aux données et services externes.[/yellow]")
        console.print("[dim]Vous pouvez les configurer plus tard avec 'finagent config set'[/dim]\n")
        
        api_keys = {}
        
        for api_key, info in api_info.items():
            required_text = "[red]REQUIS[/red]" if info['required'] else "[dim]Optionnel[/dim]"
            
            console.print(f"🔗 [bold]{info['name']}[/bold] - {required_text}")
            console.print(f"   {info['description']}")
            console.print(f"   📋 Obtenir: [blue]{info['url']}[/blue]")
            
            if info['required'] or Confirm.ask(f"   Configurer {info['name']} maintenant ?", default=False):
                api_key_value = Prompt.ask(
                    f"   Clé API {info['name']}",
                    password=True,
                    default=""
                )
                
                if api_key_value:
                    api_keys[api_key] = api_key_value
                    console.print(f"   ✅ [green]Clé {info['name']} configurée[/green]")
                elif info['required']:
                    console.print(f"   ⚠️  [yellow]Attention: {info['name']} est requis pour le fonctionnement optimal[/yellow]")
            
            console.print()
        
        self.config['api_keys'] = api_keys
        
        # Résumé
        configured_apis = [name for name in api_keys.keys()]
        if configured_apis:
            console.print(f"✅ [green]APIs configurées: {', '.join(configured_apis)}[/green]")
        else:
            console.print("⚠️  [yellow]Aucune clé API configurée - fonctionnalités limitées[/yellow]")
        
        return True
    
    def _step_portfolio_settings(self) -> bool:
        """Étape 4: Configuration du portefeuille."""
        self._show_progress()
        
        console.print("[bold cyan]📊 Configuration des paramètres de portefeuille[/bold cyan]\n")
        
        # Capital initial par défaut basé sur le profil
        risk_tolerance = self.user_selections['profile']['risk_tolerance']
        suggested_capital = {
            'conservative': 50000,
            'moderate': 100000,
            'aggressive': 250000
        }.get(risk_tolerance, 100000)
        
        # Capital initial
        initial_capital = FloatPrompt.ask(
            f"💰 Capital initial par défaut pour les backtests (USD)",
            default=suggested_capital
        )
        
        # Benchmark par défaut
        benchmark_choices = {
            'SPY': 'S&P 500 (marché US général)',
            'QQQ': 'NASDAQ 100 (tech US)',
            'VTI': 'Total Stock Market (marché US complet)',
            'VXUS': 'International (hors US)',
            'VT': 'Monde entier'
        }
        
        console.print("\n📈 [yellow]Benchmark par défaut pour les comparaisons :[/yellow]")
        for key, desc in benchmark_choices.items():
            console.print(f"  • {key}: {desc}")
        
        benchmark = Prompt.ask(
            "Votre choix",
            choices=list(benchmark_choices.keys()),
            default='SPY'
        )
        
        # Frais et coûts
        console.print("\n💸 [yellow]Configuration des frais de transaction[/yellow]")
        
        # Présets de frais selon le profil
        fee_presets = {
            'conservative': {'commission': 0.0, 'slippage': 0.0001},  # Broker gratuit
            'moderate': {'commission': 0.001, 'slippage': 0.0005},   # Frais moyens
            'aggressive': {'commission': 0.005, 'slippage': 0.001}   # Trading actif
        }
        
        preset_fees = fee_presets[risk_tolerance]
        
        commission_rate = FloatPrompt.ask(
            "Taux de commission par transaction (%)",
            default=preset_fees['commission'] * 100
        ) / 100
        
        slippage_rate = FloatPrompt.ask(
            "Slippage estimé (%)", 
            default=preset_fees['slippage'] * 100
        ) / 100
        
        # Configuration du portefeuille
        self.config['portfolio'] = {
            'initial_capital': initial_capital,
            'default_benchmark': benchmark,
            'commission_rate': commission_rate,
            'slippage_rate': slippage_rate
        }
        
        # Récapitulatif
        console.print(f"\n✅ [green]Portefeuille configuré :[/green]")
        console.print(f"  • Capital initial: ${initial_capital:,.0f}")
        console.print(f"  • Benchmark: {benchmark} ({benchmark_choices[benchmark]})")
        console.print(f"  • Commission: {commission_rate:.3%}")
        console.print(f"  • Slippage: {slippage_rate:.3%}")
        
        return True
    
    def _step_ai_preferences(self) -> bool:
        """Étape 5: Préférences IA."""
        self._show_progress()
        
        console.print("[bold cyan]🤖 Configuration du moteur d'analyse IA[/bold cyan]\n")
        
        # Modèle IA basé sur l'expérience
        experience = self.user_selections['profile']['experience']
        
        model_recommendations = {
            'beginner': 'claude-3-haiku',      # Plus simple et explicatif
            'intermediate': 'claude-3-sonnet', # Équilibré
            'advanced': 'claude-3-opus',       # Plus sophistiqué  
            'expert': 'claude-3-opus'          # Maximum de capacités
        }
        
        recommended_model = model_recommendations[experience]
        
        model_choices = {
            'claude-3-haiku': 'Claude 3 Haiku - Rapide et économique',
            'claude-3-sonnet': 'Claude 3 Sonnet - Équilibré (recommandé)',
            'claude-3-opus': 'Claude 3 Opus - Plus puissant et détaillé'
        }
        
        console.print(f"🧠 [yellow]Modèle IA recommandé pour votre profil ({experience}): {recommended_model}[/yellow]\n")
        for key, desc in model_choices.items():
            prefix = "👉 " if key == recommended_model else "   "
            console.print(f"{prefix}{key}: {desc}")
        
        model = Prompt.ask(
            "Modèle à utiliser",
            choices=list(model_choices.keys()),
            default=recommended_model
        )
        
        # Température (créativité)
        temp_recommendations = {
            'conservative': 0.1,  # Très factuel
            'moderate': 0.3,      # Équilibré
            'aggressive': 0.5     # Plus créatif
        }
        
        risk_tolerance = self.user_selections['profile']['risk_tolerance']
        recommended_temp = temp_recommendations[risk_tolerance]
        
        console.print(f"\n🌡️  [yellow]Température du modèle (créativité des analyses)[/yellow]")
        console.print("   • 0.0-0.2: Très factuel et conservateur")
        console.print("   • 0.3-0.5: Équilibré entre faits et interprétation")
        console.print("   • 0.6-1.0: Plus créatif et exploratoire")
        
        temperature = FloatPrompt.ask(
            f"Température (recommandé pour votre profil: {recommended_temp})",
            default=recommended_temp
        )
        
        # Seuil de confiance
        confidence_recommendations = {
            'beginner': 0.8,      # Seuil élevé pour plus de sécurité
            'intermediate': 0.7,  # Équilibré
            'advanced': 0.6,      # Plus flexible
            'expert': 0.5         # Très flexible
        }
        
        recommended_confidence = confidence_recommendations[experience]
        
        confidence_threshold = FloatPrompt.ask(
            f"Seuil de confiance minimum pour les recommandations (0-1, recommandé: {recommended_confidence})",
            default=recommended_confidence
        )
        
        # Options avancées
        enable_reasoning = Confirm.ask(
            "Activer l'explication détaillée du raisonnement ?",
            default=True
        )
        
        self.config['ai'] = {
            'model': model,
            'temperature': temperature,
            'confidence_threshold': confidence_threshold,
            'enable_reasoning': enable_reasoning,
            'max_tokens': 4000
        }
        
        # Récapitulatif
        console.print(f"\n✅ [green]IA configurée :[/green]")
        console.print(f"  • Modèle: {model}")
        console.print(f"  • Température: {temperature}")
        console.print(f"  • Seuil de confiance: {confidence_threshold}")
        console.print(f"  • Raisonnement détaillé: {'Oui' if enable_reasoning else 'Non'}")
        
        return True
    
    def _step_data_sources(self) -> bool:
        """Étape 6: Sources de données."""
        self._show_progress()
        
        console.print("[bold cyan]📊 Configuration des sources de données[/bold cyan]\n")
        
        # Fournisseur principal
        if 'openbb' in self.config.get('api_keys', {}):
            default_provider = 'openbb'
        else:
            default_provider = 'yahoo'  # Gratuit par défaut
        
        provider_choices = {
            'openbb': 'OpenBB Platform (recommandé si clé configurée)',
            'yahoo': 'Yahoo Finance (gratuit, limité)',
            'alpha_vantage': 'Alpha Vantage (si clé configurée)'
        }
        
        console.print("[yellow]📡 Fournisseur principal de données financières :[/yellow]")
        for key, desc in provider_choices.items():
            prefix = "👉 " if key == default_provider else "   "
            console.print(f"{prefix}{key}: {desc}")
        
        data_provider = Prompt.ask(
            "Votre choix",
            choices=list(provider_choices.keys()),
            default=default_provider
        )
        
        # Fréquence de mise à jour
        update_frequencies = {
            '1m': 'Temps réel (1 minute) - Pour trading actif',
            '5m': '5 minutes - Suivi fréquent',
            '1h': '1 heure - Suivi régulier (recommandé)',
            '1d': '1 jour - Suivi quotidien'
        }
        
        console.print(f"\n🔄 [yellow]Fréquence de mise à jour des données :[/yellow]")
        for key, desc in update_frequencies.items():
            console.print(f"  • {key}: {desc}")
        
        update_frequency = Prompt.ask(
            "Votre choix",
            choices=list(update_frequencies.keys()),
            default='1h'
        )
        
        # Période historique
        historical_years = IntPrompt.ask(
            "📅 Nombre d'années de données historiques à conserver",
            default=5
        )
        
        # Données temps réel
        enable_realtime = False
        if data_provider == 'openbb' and 'openbb' in self.config.get('api_keys', {}):
            enable_realtime = Confirm.ask(
                "Activer les données temps réel ?",
                default=False
            )
        
        self.config['data'] = {
            'data_provider': data_provider,
            'update_frequency': update_frequency,
            'historical_data_years': historical_years,
            'enable_realtime': enable_realtime
        }
        
        # Cache et performance
        cache_duration = {
            '1m': 300,    # 5 minutes
            '5m': 900,    # 15 minutes
            '1h': 3600,   # 1 heure
            '1d': 86400   # 1 jour
        }.get(update_frequency, 3600)
        
        self.config['preferences']['cache_duration'] = cache_duration
        
        # Récapitulatif
        console.print(f"\n✅ [green]Sources de données configurées :[/green]")
        console.print(f"  • Fournisseur: {data_provider}")
        console.print(f"  • Mise à jour: {update_frequency}")
        console.print(f"  • Historique: {historical_years} ans")
        console.print(f"  • Temps réel: {'Oui' if enable_realtime else 'Non'}")
        
        return True
    
    def _step_finalization(self) -> bool:
        """Étape 7: Finalisation et sauvegarde."""
        self._show_progress()
        
        console.print("[bold cyan]✅ Finalisation de la configuration[/bold cyan]\n")
        
        # Configuration CLI par défaut
        self.config['cli'] = {
            'theme': 'auto',
            'verbose': False,
            'show_progress': True,
            'auto_complete': True,
            'color_output': True
        }
        
        # Récapitulatif complet
        console.print("[bold yellow]📋 Récapitulatif de votre configuration :[/bold yellow]\n")
        
        profile = self.user_selections['profile']
        
        summary_table = Table(show_header=True, header_style="bold cyan")
        summary_table.add_column("Catégorie", style="cyan")
        summary_table.add_column("Paramètre", style="white")
        summary_table.add_column("Valeur", style="green")
        
        # Profil utilisateur
        summary_table.add_row("👤 Profil", "Expérience", profile['experience'].title())
        summary_table.add_row("", "Tolérance au risque", profile['risk_tolerance'].title())
        summary_table.add_row("", "Horizon d'investissement", profile['investment_horizon'].title())
        
        # APIs
        apis = list(self.config.get('api_keys', {}).keys())
        summary_table.add_row("🔑 APIs", "Configurées", ', '.join(apis) if apis else "Aucune")
        
        # Portefeuille
        portfolio = self.config['portfolio']
        summary_table.add_row("📊 Portefeuille", "Capital initial", f"${portfolio['initial_capital']:,.0f}")
        summary_table.add_row("", "Benchmark", portfolio['default_benchmark'])
        summary_table.add_row("", "Commission", f"{portfolio['commission_rate']:.3%}")
        
        # IA
        ai = self.config['ai']
        summary_table.add_row("🤖 IA", "Modèle", ai['model'])
        summary_table.add_row("", "Température", str(ai['temperature']))
        summary_table.add_row("", "Seuil confiance", str(ai['confidence_threshold']))
        
        # Données
        data = self.config['data']
        summary_table.add_row("📊 Données", "Fournisseur", data['data_provider'])
        summary_table.add_row("", "Fréquence", data['update_frequency'])
        summary_table.add_row("", "Historique", f"{data['historical_data_years']} ans")
        
        console.print(summary_table)
        
        # Validation finale
        console.print()
        if not Confirm.ask("💾 Sauvegarder cette configuration ?", default=True):
            console.print("❌ Configuration non sauvegardée", style="yellow")
            return False
        
        # Sauvegarde
        try:
            self._save_configuration()
            
            console.print(Panel(
                "✅ [bold green]Configuration sauvegardée avec succès ![/bold green]\n\n"
                "🎉 FinAgent est maintenant configuré et prêt à être utilisé.\n\n"
                "[yellow]Prochaines étapes :[/yellow]\n"
                "• Testez avec: [cyan]finagent analyze stock AAPL[/cyan]\n"
                "• Mode interactif: [cyan]finagent --interactive[/cyan]\n"
                "• Aide complète: [cyan]finagent --help[/cyan]\n\n"
                "[dim]💡 Vous pouvez modifier la configuration plus tard avec:[/dim]\n"
                "[dim]   finagent config show[/dim]\n"
                "[dim]   finagent config set section.key value[/dim]",
                title="🎯 Configuration Terminée",
                border_style="green"
            ))
            
            return True
            
        except Exception as e:
            console.print(f"❌ Erreur lors de la sauvegarde: {e}", style="red")
            return False
    
    def _save_configuration(self) -> None:
        """Sauvegarde la configuration finale."""
        config_dir = Path.home() / '.finagent'
        config_dir.mkdir(exist_ok=True)
        
        config_file = config_dir / 'config.json'
        
        with open(config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
        
        console.print(f"📁 Configuration sauvegardée: {config_file}", style="dim")
    
    async def run(self) -> bool:
        """Lance le wizard complet."""
        console.clear()
        
        try:
            # Exécution séquentielle des étapes
            step_methods = [
                self._step_welcome,
                self._step_user_profile,
                self._step_api_keys,
                self._step_portfolio_settings,
                self._step_ai_preferences,
                self._step_data_sources,
                self._step_finalization
            ]
            
            for i, step_method in enumerate(step_methods):
                self.current_step = i
                
                if not step_method():
                    console.print("\n❌ Configuration interrompue", style="yellow")
                    return False
                
                # Pause entre les étapes (sauf la dernière)
                if i < len(step_methods) - 1:
                    console.print()
                    if not Confirm.ask("➡️  Continuer vers l'étape suivante ?", default=True):
                        console.print("❌ Configuration interrompue", style="yellow")
                        return False
                    
                    console.clear()
            
            return True
            
        except KeyboardInterrupt:
            console.print("\n❌ Configuration interrompue par l'utilisateur", style="yellow")
            return False
        
        except Exception as e:
            console.print(f"\n❌ Erreur durant la configuration: {e}", style="red")
            return False


# === Fonctions utilitaires ===

async def run_wizard() -> bool:
    """Lance l'assistant de configuration."""
    wizard = FinAgentWizard()
    return await wizard.run()


def run_wizard_sync() -> bool:
    """Lance l'assistant de configuration de manière synchrone."""
    return asyncio.run(run_wizard())


if __name__ == "__main__":
    # Test du wizard
    success = run_wizard_sync()
    if success:
        console.print("🎉 Wizard terminé avec succès !", style="green")
    else:
        console.print("❌ Wizard interrompu", style="red")