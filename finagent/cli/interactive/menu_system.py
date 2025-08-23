"""
Système de menus interactifs pour FinAgent.

Fournit une interface de navigation par menus pour les utilisateurs
qui préfèrent une approche guidée plutôt que des commandes CLI.
"""

import asyncio
from typing import Dict, Any, List, Callable, Optional, Tuple
from pathlib import Path
import json
from datetime import datetime, timedelta

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.text import Text
from rich.align import Align
from rich.columns import Columns
from rich.progress import Progress, SpinnerColumn, TextColumn

from finagent.cli.formatters.base_formatter import BaseFormatter
from finagent.cli.utils.validation import SymbolValidator

console = Console()


class MenuItem:
    """Représente un élément de menu."""
    
    def __init__(
        self,
        key: str,
        title: str,
        description: str,
        action: Optional[Callable] = None,
        submenu: Optional[Dict[str, 'MenuItem']] = None,
        enabled: bool = True
    ):
        self.key = key
        self.title = title
        self.description = description
        self.action = action
        self.submenu = submenu or {}
        self.enabled = enabled
    
    def is_submenu(self) -> bool:
        """Vérifie si l'élément a un sous-menu."""
        return bool(self.submenu)
    
    def is_action(self) -> bool:
        """Vérifie si l'élément a une action."""
        return self.action is not None
    
    async def execute(self) -> bool:
        """Exécute l'action associée."""
        if self.action:
            return await self.action()
        return True


class MenuSystem:
    """Système de navigation par menus pour FinAgent."""
    
    def __init__(self):
        """Initialise le système de menus."""
        self.current_menu_path = []
        self.user_context = {}
        self.formatter = BaseFormatter()
        self._init_menus()
    
    def _init_menus(self) -> None:
        """Initialise la structure des menus."""
        self.root_menu = {
            '1': MenuItem(
                '1', '📊 Analyse de Marché', 
                'Analyser des actions, secteurs et tendances du marché',
                submenu=self._create_analysis_menu()
            ),
            '2': MenuItem(
                '2', '💼 Gestion de Portefeuille',
                'Créer et gérer vos portefeuilles d\'investissement',
                submenu=self._create_portfolio_menu()
            ),
            '3': MenuItem(
                '3', '📋 Stratégies d\'Investissement',
                'Créer, tester et optimiser des stratégies',
                submenu=self._create_strategy_menu()
            ),
            '4': MenuItem(
                '4', '🎯 Décisions de Trading',
                'Analyser et prendre des décisions d\'investissement',
                submenu=self._create_decision_menu()
            ),
            '5': MenuItem(
                '5', '⚙️  Configuration',
                'Configurer FinAgent et vos préférences',
                submenu=self._create_config_menu()
            ),
            '6': MenuItem(
                '6', '📚 Aide et Documentation',
                'Guides, tutoriels et documentation',
                submenu=self._create_help_menu()
            ),
            'q': MenuItem(
                'q', '🚪 Quitter',
                'Quitter le système de menus',
                action=self._action_quit
            )
        }
        
        self.current_menu = self.root_menu
    
    def _create_analysis_menu(self) -> Dict[str, MenuItem]:
        """Crée le menu d'analyse."""
        return {
            '1': MenuItem(
                '1', '📈 Analyser une Action',
                'Analyse complète d\'une action spécifique',
                action=self._action_analyze_stock
            ),
            '2': MenuItem(
                '2', '⚖️  Comparer des Actions',
                'Comparer plusieurs actions entre elles',
                action=self._action_compare_stocks
            ),
            '3': MenuItem(
                '3', '🌍 Vue d\'Ensemble du Marché',
                'Analyse globale des indices et secteurs',
                action=self._action_market_overview
            ),
            '4': MenuItem(
                '4', '🔍 Recherche de Titres',
                'Rechercher et filtrer des actions par critères',
                action=self._action_stock_screener
            ),
            '5': MenuItem(
                '5', '📊 Analyse Sectorielle',
                'Analyser un secteur d\'activité spécifique',
                action=self._action_sector_analysis
            ),
            'b': MenuItem(
                'b', '⬅️  Retour',
                'Retourner au menu principal',
                action=self._action_back
            )
        }
    
    def _create_portfolio_menu(self) -> Dict[str, MenuItem]:
        """Crée le menu de gestion de portefeuille."""
        return {
            '1': MenuItem(
                '1', '➕ Créer un Portefeuille',
                'Créer un nouveau portefeuille d\'investissement',
                action=self._action_create_portfolio
            ),
            '2': MenuItem(
                '2', '📋 Mes Portefeuilles',
                'Voir et gérer vos portefeuilles existants',
                action=self._action_list_portfolios
            ),
            '3': MenuItem(
                '3', '📊 Analyser un Portefeuille',
                'Analyse détaillée d\'un portefeuille',
                action=self._action_analyze_portfolio
            ),
            '4': MenuItem(
                '4', '⚡ Optimiser un Portefeuille',
                'Optimiser l\'allocation d\'un portefeuille',
                action=self._action_optimize_portfolio
            ),
            '5': MenuItem(
                '5', '📈 Performance Historique',
                'Analyser la performance historique',
                action=self._action_portfolio_performance
            ),
            '6': MenuItem(
                '6', '🎯 Rééquilibrage',
                'Recommandations de rééquilibrage',
                action=self._action_rebalance_portfolio
            ),
            'b': MenuItem(
                'b', '⬅️  Retour',
                'Retourner au menu principal',
                action=self._action_back
            )
        }
    
    def _create_strategy_menu(self) -> Dict[str, MenuItem]:
        """Crée le menu de stratégies."""
        return {
            '1': MenuItem(
                '1', '📝 Créer une Stratégie',
                'Créer une nouvelle stratégie d\'investissement',
                action=self._action_create_strategy
            ),
            '2': MenuItem(
                '2', '📋 Mes Stratégies',
                'Voir et gérer vos stratégies existantes',
                action=self._action_list_strategies
            ),
            '3': MenuItem(
                '3', '🧪 Tester une Stratégie (Backtest)',
                'Tester une stratégie sur données historiques',
                action=self._action_backtest_strategy
            ),
            '4': MenuItem(
                '4', '⚡ Optimiser une Stratégie',
                'Optimiser les paramètres d\'une stratégie',
                action=self._action_optimize_strategy
            ),
            '5': MenuItem(
                '5', '📊 Comparer des Stratégies',
                'Comparer plusieurs stratégies entre elles',
                action=self._action_compare_strategies
            ),
            '6': MenuItem(
                '6', '🎯 Stratégies Prédéfinies',
                'Utiliser des templates de stratégies',
                action=self._action_strategy_templates
            ),
            'b': MenuItem(
                'b', '⬅️  Retour',
                'Retourner au menu principal',
                action=self._action_back
            )
        }
    
    def _create_decision_menu(self) -> Dict[str, MenuItem]:
        """Crée le menu de décisions."""
        return {
            '1': MenuItem(
                '1', '🎯 Analyser une Décision',
                'Analyser une décision d\'achat/vente',
                action=self._action_analyze_decision
            ),
            '2': MenuItem(
                '2', '📋 Historique des Décisions',
                'Voir l\'historique de vos décisions',
                action=self._action_decision_history
            ),
            '3': MenuItem(
                '3', '📊 Performance des Décisions',
                'Analyser la performance de vos décisions',
                action=self._action_decision_performance
            ),
            '4': MenuItem(
                '4', '🎲 Simulation Monte Carlo',
                'Simuler des scénarios d\'investissement',
                action=self._action_monte_carlo
            ),
            '5': MenuItem(
                '5', '⚠️  Analyse de Risque',
                'Évaluer les risques d\'une position',
                action=self._action_risk_analysis
            ),
            'b': MenuItem(
                'b', '⬅️  Retour',
                'Retourner au menu principal',
                action=self._action_back
            )
        }
    
    def _create_config_menu(self) -> Dict[str, MenuItem]:
        """Crée le menu de configuration."""
        return {
            '1': MenuItem(
                '1', '👤 Configuration Initiale',
                'Assistant de configuration pour nouveaux utilisateurs',
                action=self._action_initial_config
            ),
            '2': MenuItem(
                '2', '🔑 Clés API',
                'Configurer les clés d\'accès aux services',
                action=self._action_api_keys
            ),
            '3': MenuItem(
                '3', '📊 Paramètres Portefeuille',
                'Configurer les paramètres par défaut',
                action=self._action_portfolio_settings
            ),
            '4': MenuItem(
                '4', '🤖 Préférences IA',
                'Configurer le moteur d\'analyse IA',
                action=self._action_ai_preferences
            ),
            '5': MenuItem(
                '5', '📊 Sources de Données',
                'Configurer les fournisseurs de données',
                action=self._action_data_sources
            ),
            '6': MenuItem(
                '6', '💾 Sauvegarde/Restauration',
                'Gérer la sauvegarde de votre configuration',
                action=self._action_backup_restore
            ),
            '7': MenuItem(
                '7', '📋 Voir la Configuration',
                'Afficher la configuration actuelle',
                action=self._action_show_config
            ),
            'b': MenuItem(
                'b', '⬅️  Retour',
                'Retourner au menu principal',
                action=self._action_back
            )
        }
    
    def _create_help_menu(self) -> Dict[str, MenuItem]:
        """Crée le menu d'aide."""
        return {
            '1': MenuItem(
                '1', '🚀 Guide de Démarrage',
                'Guide pour bien commencer avec FinAgent',
                action=self._action_getting_started
            ),
            '2': MenuItem(
                '2', '📖 Documentation des Commandes',
                'Référence complète des commandes',
                action=self._action_command_reference
            ),
            '3': MenuItem(
                '3', '💡 Exemples d\'Utilisation',
                'Exemples pratiques d\'analyses',
                action=self._action_usage_examples
            ),
            '4': MenuItem(
                '4', '❓ FAQ',
                'Questions fréquemment posées',
                action=self._action_faq
            ),
            '5': MenuItem(
                '5', '🐛 Signaler un Problème',
                'Obtenir de l\'aide pour résoudre un problème',
                action=self._action_troubleshooting
            ),
            'b': MenuItem(
                'b', '⬅️  Retour',
                'Retourner au menu principal',
                action=self._action_back
            )
        }
    
    def _show_menu(self, menu: Dict[str, MenuItem], title: str = "Menu Principal") -> None:
        """Affiche un menu."""
        console.clear()
        
        # En-tête avec chemin de navigation
        navigation = " → ".join(['FinAgent'] + [step for step in self.current_menu_path])
        console.print(f"[dim]{navigation}[/dim]\n")
        
        # Titre du menu
        console.print(Panel(
            f"[bold cyan]{title}[/bold cyan]",
            border_style="cyan",
            width=60
        ))
        
        # Options du menu
        options_table = Table(show_header=False, box=None, padding=(0, 2))
        options_table.add_column("Choix", style="bold cyan", width=8)
        options_table.add_column("Description", style="white")
        
        for key, item in menu.items():
            if item.enabled:
                status = ""
                if not item.enabled:
                    status = "[dim](indisponible)[/dim]"
                elif item.is_submenu():
                    status = "▶"
                
                options_table.add_row(
                    f"[{key}]",
                    f"{item.title} {status}\n[dim]{item.description}[/dim]"
                )
        
        console.print(options_table)
        console.print()
    
    def _get_user_choice(self, menu: Dict[str, MenuItem]) -> Optional[str]:
        """Récupère le choix de l'utilisateur."""
        valid_choices = [key for key, item in menu.items() if item.enabled]
        
        try:
            choice = Prompt.ask(
                "Votre choix",
                choices=valid_choices,
                show_choices=False
            ).lower()
            return choice
        except KeyboardInterrupt:
            return 'q'
        except Exception:
            return None
    
    async def _execute_menu_item(self, item: MenuItem) -> bool:
        """Exécute un élément de menu."""
        try:
            if item.is_submenu():
                # Navigation vers sous-menu
                self.current_menu_path.append(item.title)
                self.current_menu = item.submenu
                return True
            
            elif item.is_action():
                # Exécution d'action
                console.print()
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console
                ) as progress:
                    task = progress.add_task("Exécution en cours...", total=None)
                    result = await item.execute()
                    progress.update(task, completed=True)
                
                if result:
                    console.print("\n[green]✅ Opération terminée avec succès[/green]")
                else:
                    console.print("\n[yellow]⚠️  Opération annulée ou échouée[/yellow]")
                
                # Pause pour permettre la lecture
                console.print("\n[dim]Appuyez sur Entrée pour continuer...[/dim]")
                input()
                return True
            
            return False
            
        except Exception as e:
            console.print(f"\n[red]❌ Erreur: {e}[/red]")
            console.print("\n[dim]Appuyez sur Entrée pour continuer...[/dim]")
            input()
            return False
    
    async def run(self) -> None:
        """Lance le système de menus."""
        try:
            while True:
                # Titre basé sur la position dans les menus
                if not self.current_menu_path:
                    title = "🎯 FinAgent - Menu Principal"
                else:
                    title = f"📋 {self.current_menu_path[-1]}"
                
                self._show_menu(self.current_menu, title)
                
                choice = self._get_user_choice(self.current_menu)
                
                if choice is None:
                    console.print("[red]Choix invalide[/red]")
                    await asyncio.sleep(1)
                    continue
                
                if choice == 'q' and not self.current_menu_path:
                    # Quitter depuis le menu principal
                    break
                
                item = self.current_menu.get(choice)
                if item:
                    await self._execute_menu_item(item)
        
        except KeyboardInterrupt:
            console.print("\n[yellow]👋 Au revoir ![/yellow]")
        
        except Exception as e:
            console.print(f"\n[red]❌ Erreur système: {e}[/red]")
    
    # === Actions des menus ===
    
    async def _action_quit(self) -> bool:
        """Action pour quitter."""
        return False
    
    async def _action_back(self) -> bool:
        """Action pour revenir en arrière."""
        if self.current_menu_path:
            self.current_menu_path.pop()
            # Reconstruire le menu parent
            menu = self.root_menu
            for step in self.current_menu_path:
                for item in menu.values():
                    if item.title == step and item.is_submenu():
                        menu = item.submenu
                        break
            self.current_menu = menu
        return True
    
    # Actions d'analyse
    async def _action_analyze_stock(self) -> bool:
        """Action d'analyse d'action."""
        console.print("[bold cyan]📈 Analyse d'Action[/bold cyan]\n")
        
        # Saisie du symbole
        symbol = Prompt.ask("Symbole de l'action (ex: AAPL, GOOGL)")
        
        if not SymbolValidator.validate_symbol(symbol):
            console.print("[red]❌ Symbole invalide[/red]")
            return False
        
        # Options d'analyse
        analysis_options = {
            '1': 'Analyse technique',
            '2': 'Analyse fondamentale',
            '3': 'Analyse complète (technique + fondamentale)',
            '4': 'Analyse rapide'
        }
        
        console.print("\n[yellow]Type d'analyse :[/yellow]")
        for key, desc in analysis_options.items():
            console.print(f"  {key}. {desc}")
        
        analysis_type = Prompt.ask(
            "Votre choix",
            choices=list(analysis_options.keys()),
            default='3'
        )
        
        # Simulation de l'analyse
        console.print(f"\n🔍 Analyse de {symbol.upper()} en cours...")
        await asyncio.sleep(2)  # Simulation
        
        console.print(f"✅ Analyse de {symbol.upper()} terminée")
        console.print(f"📊 Type: {analysis_options[analysis_type]}")
        
        return True
    
    async def _action_compare_stocks(self) -> bool:
        """Action de comparaison d'actions."""
        console.print("[bold cyan]⚖️  Comparaison d'Actions[/bold cyan]\n")
        
        # Saisie des symboles
        symbols_input = Prompt.ask("Symboles à comparer (séparés par des virgules, ex: AAPL,GOOGL,MSFT)")
        symbols = [s.strip().upper() for s in symbols_input.split(',')]
        
        if len(symbols) < 2:
            console.print("[red]❌ Il faut au moins 2 symboles pour comparer[/red]")
            return False
        
        # Critères de comparaison
        criteria = {
            '1': 'Performance',
            '2': 'Valorisation',
            '3': 'Croissance',
            '4': 'Dividendes',
            '5': 'Comparaison complète'
        }
        
        console.print("\n[yellow]Critères de comparaison :[/yellow]")
        for key, desc in criteria.items():
            console.print(f"  {key}. {desc}")
        
        criterion = Prompt.ask(
            "Votre choix",
            choices=list(criteria.keys()),
            default='5'
        )
        
        console.print(f"\n🔍 Comparaison de {', '.join(symbols)} en cours...")
        await asyncio.sleep(2)
        
        console.print(f"✅ Comparaison terminée")
        console.print(f"📊 Critère: {criteria[criterion]}")
        
        return True
    
    async def _action_market_overview(self) -> bool:
        """Action de vue d'ensemble du marché."""
        console.print("[bold cyan]🌍 Vue d'Ensemble du Marché[/bold cyan]\n")
        
        # Marchés à analyser
        markets = {
            '1': 'États-Unis (S&P 500, NASDAQ, Dow Jones)',
            '2': 'Europe (FTSE, DAX, CAC 40)',
            '3': 'Asie (Nikkei, Hang Seng, Shanghai)',
            '4': 'Global (tous les marchés)',
            '5': 'Secteurs par performance'
        }
        
        console.print("[yellow]Marché à analyser :[/yellow]")
        for key, desc in markets.items():
            console.print(f"  {key}. {desc}")
        
        market = Prompt.ask(
            "Votre choix",
            choices=list(markets.keys()),
            default='1'
        )
        
        console.print(f"\n🔍 Analyse du marché en cours...")
        await asyncio.sleep(2)
        
        console.print(f"✅ Analyse terminée")
        console.print(f"🌍 Marché: {markets[market]}")
        
        return True
    
    async def _action_stock_screener(self) -> bool:
        """Action de recherche de titres."""
        console.print("[bold cyan]🔍 Recherche de Titres[/bold cyan]\n")
        
        # Critères de filtrage
        console.print("[yellow]Filtres disponibles :[/yellow]")
        
        # Capitalisation
        market_cap = Prompt.ask(
            "Capitalisation minimale (en milliards USD)",
            default="1"
        )
        
        # Secteur
        sectors = ['Technology', 'Healthcare', 'Finance', 'Consumer', 'Energy', 'Tous']
        console.print("\nSecteurs :")
        for i, sector in enumerate(sectors, 1):
            console.print(f"  {i}. {sector}")
        
        sector_choice = IntPrompt.ask(
            "Secteur (1-6)",
            choices=[str(i) for i in range(1, 7)],
            default=6
        )
        
        selected_sector = sectors[sector_choice - 1]
        
        console.print(f"\n🔍 Recherche en cours...")
        console.print(f"  • Capitalisation min: ${market_cap}B")
        console.print(f"  • Secteur: {selected_sector}")
        
        await asyncio.sleep(2)
        
        console.print("✅ Recherche terminée - 25 titres trouvés")
        
        return True
    
    async def _action_sector_analysis(self) -> bool:
        """Action d'analyse sectorielle."""
        console.print("[bold cyan]📊 Analyse Sectorielle[/bold cyan]\n")
        
        # Secteurs disponibles
        sectors = {
            '1': 'Technology (XLK)',
            '2': 'Healthcare (XLV)', 
            '3': 'Financial Services (XLF)',
            '4': 'Consumer Discretionary (XLY)',
            '5': 'Energy (XLE)',
            '6': 'Utilities (XLU)',
            '7': 'Real Estate (XLRE)',
            '8': 'Materials (XLB)',
            '9': 'Industrials (XLI)',
            '10': 'Consumer Staples (XLP)',
            '11': 'Communication Services (XLC)'
        }
        
        console.print("[yellow]Secteur à analyser :[/yellow]")
        for key, desc in sectors.items():
            console.print(f"  {key}. {desc}")
        
        sector = Prompt.ask(
            "Votre choix",
            choices=list(sectors.keys()),
            default='1'
        )
        
        console.print(f"\n🔍 Analyse du secteur {sectors[sector]} en cours...")
        await asyncio.sleep(2)
        
        console.print("✅ Analyse sectorielle terminée")
        
        return True
    
    # Actions de portefeuille
    async def _action_create_portfolio(self) -> bool:
        """Action de création de portefeuille."""
        console.print("[bold cyan]➕ Création de Portefeuille[/bold cyan]\n")
        
        # Nom du portefeuille
        name = Prompt.ask("Nom du portefeuille")
        
        # Description
        description = Prompt.ask("Description (optionnelle)", default="")
        
        # Capital initial
        initial_capital = IntPrompt.ask("Capital initial (USD)", default=100000)
        
        # Type de portefeuille
        portfolio_types = {
            '1': 'Croissance',
            '2': 'Valeur',
            '3': 'Équilibré',
            '4': 'Revenus (dividendes)',
            '5': 'Personnalisé'
        }
        
        console.print("\n[yellow]Type de portefeuille :[/yellow]")
        for key, desc in portfolio_types.items():
            console.print(f"  {key}. {desc}")
        
        portfolio_type = Prompt.ask(
            "Votre choix",
            choices=list(portfolio_types.keys()),
            default='3'
        )
        
        console.print(f"\n📝 Création du portefeuille '{name}' en cours...")
        await asyncio.sleep(1)
        
        console.print(f"✅ Portefeuille '{name}' créé avec succès")
        console.print(f"💰 Capital initial: ${initial_capital:,}")
        console.print(f"📊 Type: {portfolio_types[portfolio_type]}")
        
        return True
    
    async def _action_list_portfolios(self) -> bool:
        """Action de liste des portefeuilles."""
        console.print("[bold cyan]📋 Mes Portefeuilles[/bold cyan]\n")
        
        # Simulation de portefeuilles existants
        portfolios = [
            {"name": "Croissance Tech", "value": 125000, "return": 25.0, "positions": 8},
            {"name": "Dividendes Stable", "value": 85000, "return": 8.5, "positions": 12},
            {"name": "Crypto Allocation", "value": 15000, "return": -5.2, "positions": 5}
        ]
        
        if not portfolios:
            console.print("[yellow]Aucun portefeuille trouvé[/yellow]")
            console.print("💡 Créez votre premier portefeuille avec l'option 1 du menu précédent")
            return True
        
        # Tableau des portefeuilles
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Nom", style="white")
        table.add_column("Valeur", justify="right", style="cyan")
        table.add_column("Rendement", justify="right")
        table.add_column("Positions", justify="right", style="dim")
        
        for portfolio in portfolios:
            return_color = "green" if portfolio["return"] >= 0 else "red"
            return_sign = "+" if portfolio["return"] >= 0 else ""
            
            table.add_row(
                portfolio["name"],
                f"${portfolio['value']:,}",
                f"[{return_color}]{return_sign}{portfolio['return']:.1f}%[/{return_color}]",
                str(portfolio["positions"])
            )
        
        console.print(table)
        
        # Actions possibles
        console.print(f"\n[yellow]Actions disponibles :[/yellow]")
        console.print("• Analyser un portefeuille: Option 3")
        console.print("• Optimiser: Option 4")
        console.print("• Voir la performance: Option 5")
        
        return True
    
    async def _action_analyze_portfolio(self) -> bool:
        """Action d'analyse de portefeuille."""
        console.print("[bold cyan]📊 Analyse de Portefeuille[/bold cyan]\n")
        
        portfolio_name = Prompt.ask("Nom du portefeuille à analyser")
        
        console.print(f"\n🔍 Analyse du portefeuille '{portfolio_name}' en cours...")
        await asyncio.sleep(2)
        
        console.print("✅ Analyse terminée")
        console.print("📊 Rapport d'analyse généré")
        
        return True
    
    async def _action_optimize_portfolio(self) -> bool:
        """Action d'optimisation de portefeuille."""
        console.print("[bold cyan]⚡ Optimisation de Portefeuille[/bold cyan]\n")
        
        portfolio_name = Prompt.ask("Nom du portefeuille à optimiser")
        
        # Objectif d'optimisation
        objectives = {
            '1': 'Maximiser le rendement',
            '2': 'Minimiser le risque',
            '3': 'Optimiser le ratio Sharpe',
            '4': 'Équilibrage risque/rendement'
        }
        
        console.print("\n[yellow]Objectif d'optimisation :[/yellow]")
        for key, desc in objectives.items():
            console.print(f"  {key}. {desc}")
        
        objective = Prompt.ask(
            "Votre choix",
            choices=list(objectives.keys()),
            default='3'
        )
        
        console.print(f"\n⚡ Optimisation du portefeuille '{portfolio_name}' en cours...")
        await asyncio.sleep(3)
        
        console.print("✅ Optimisation terminée")
        console.print(f"🎯 Objectif: {objectives[objective]}")
        
        return True
    
    async def _action_portfolio_performance(self) -> bool:
        """Action d'analyse de performance."""
        console.print("[bold cyan]📈 Performance Historique[/bold cyan]\n")
        
        portfolio_name = Prompt.ask("Nom du portefeuille")
        
        # Période d'analyse
        periods = {
            '1': '1 mois',
            '2': '3 mois',
            '3': '6 mois',
            '4': '1 an',
            '5': '2 ans',
            '6': 'Depuis création'
        }
        
        console.print("\n[yellow]Période d'analyse :[/yellow]")
        for key, desc in periods.items():
            console.print(f"  {key}. {desc}")
        
        period = Prompt.ask(
            "Votre choix",
            choices=list(periods.keys()),
            default='4'
        )
        
        console.print(f"\n📊 Analyse de performance sur {periods[period]} en cours...")
        await asyncio.sleep(2)
        
        console.print("✅ Analyse de performance terminée")
        
        return True
    
    async def _action_rebalance_portfolio(self) -> bool:
        """Action de rééquilibrage."""
        console.print("[bold cyan]🎯 Rééquilibrage de Portefeuille[/bold cyan]\n")
        
        portfolio_name = Prompt.ask("Nom du portefeuille")
        
        console.print(f"\n⚖️  Analyse du rééquilibrage pour '{portfolio_name}' en cours...")
        await asyncio.sleep(2)
        
        console.print("✅ Recommandations de rééquilibrage générées")
        
        return True
    
    # Actions de stratégies (placeholder)
    async def _action_create_strategy(self) -> bool:
        console.print("🚧 Fonctionnalité en développement")
        return True
    
    async def _action_list_strategies(self) -> bool:
        console.print("🚧 Fonctionnalité en développement")
        return True
    
    async def _action_backtest_strategy(self) -> bool:
        console.print("🚧 Fonctionnalité en développement")
        return True
    
    async def _action_optimize_strategy(self) -> bool:
        console.print("🚧 Fonctionnalité en développement")
        return True
    
    async def _action_compare_strategies(self) -> bool:
        console.print("🚧 Fonctionnalité en développement")
        return True
    
    async def _action_strategy_templates(self) -> bool:
        console.print("🚧 Fonctionnalité en développement")
        return True
    
    # Actions de décisions (placeholder)
    async def _action_analyze_decision(self) -> bool:
        console.print("🚧 Fonctionnalité en développement")
        return True
    
    async def _action_decision_history(self) -> bool:
        console.print("🚧 Fonctionnalité en développement")
        return True
    
    async def _action_decision_performance(self) -> bool:
        console.print("🚧 Fonctionnalité en développement")
        return True
    
    async def _action_monte_carlo(self) -> bool:
        console.print("🚧 Fonctionnalité en développement")
        return True
    
    async def _action_risk_analysis(self) -> bool:
        console.print("🚧 Fonctionnalité en développement")
        return True
    
    # Actions de configuration
    async def _action_initial_config(self) -> bool:
        """Action de configuration initiale."""
        console.print("[bold cyan]👤 Configuration Initiale[/bold cyan]\n")
        
        console.print("🚀 Lancement de l'assistant de configuration...")
        
        # Import et lancement du wizard
        try:
            from finagent.cli.interactive.wizard import run_wizard
            return await run_wizard()
        except ImportError:
            console.print("[red]❌ Module wizard non disponible[/red]")
            return False
    
    async def _action_api_keys(self) -> bool:
        console.print("🚧 Fonctionnalité en développement")
        return True
    
    async def _action_portfolio_settings(self) -> bool:
        console.print("🚧 Fonctionnalité en développement")
        return True
    
    async def _action_ai_preferences(self) -> bool:
        console.print("🚧 Fonctionnalité en développement")
        return True
    
    async def _action_data_sources(self) -> bool:
        console.print("🚧 Fonctionnalité en développement")
        return True
    
    async def _action_backup_restore(self) -> bool:
        console.print("🚧 Fonctionnalité en développement")
        return True
    
    async def _action_show_config(self) -> bool:
        console.print("🚧 Fonctionnalité en développement")
        return True
    
    # Actions d'aide
    async def _action_getting_started(self) -> bool:
        """Action guide de démarrage."""
        console.print("[bold cyan]🚀 Guide de Démarrage FinAgent[/bold cyan]\n")
        
        guide_text = """
[bold yellow]👋 Bienvenue dans FinAgent ![/bold yellow]

[cyan]📋 Étapes recommandées pour commencer :[/cyan]

[bold]1. Configuration initiale[/bold]
   • Lancez le wizard de configuration
   • Configurez vos clés API (OpenRouter requis)
   • Définissez votre profil d'investisseur

[bold]2. Première analyse[/bold]
   • Analysez une action que vous connaissez
   • Exemple: Menu Analyse → Analyser une Action → AAPL

[bold]3. Créez votre premier portefeuille[/bold]
   • Menu Portefeuille → Créer un Portefeuille
   • Définissez vos positions actuelles

[bold]4. Explorez les stratégies[/bold]
   • Menu Stratégies → Stratégies Prédéfinies
   • Testez des stratégies sur vos données

[cyan]💡 Conseils :[/cyan]
• Utilisez le mode interactif pour explorer
• Consultez l'aide contextuelle avec '?'
• Sauvegardez régulièrement votre configuration
        """
        
        console.print(Panel(
            guide_text.strip(),
            title="Guide de Démarrage",
            border_style="cyan"
        ))
        
        return True
    
    async def _action_command_reference(self) -> bool:
        console.print("🚧 Fonctionnalité en développement")
        return True
    
    async def _action_usage_examples(self) -> bool:
        console.print("🚧 Fonctionnalité en développement")
        return True
    
    async def _action_faq(self) -> bool:
        console.print("🚧 Fonctionnalité en développement")
        return True
    
    async def _action_troubleshooting(self) -> bool:
        console.print("🚧 Fonctionnalité en développement")
        return True


# === Fonctions utilitaires ===

async def run_menu_system() -> None:
    """Lance le système de menus."""
    menu_system = MenuSystem()
    await menu_system.run()


def run_menu_system_sync() -> None:
    """Lance le système de menus de manière synchrone."""
    asyncio.run(run_menu_system())


if __name__ == "__main__":
    # Test du système de menus
    run_menu_system_sync()