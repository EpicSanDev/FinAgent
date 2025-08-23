"""
Commande de gestion des stratégies pour la CLI FinAgent.

Cette commande permet de créer, tester et gérer des stratégies
d'investissement en YAML avec backtesting et optimisation.
"""

import asyncio
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timedelta
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from rich.prompt import Prompt, Confirm

from ..formatters import AnalysisFormatter, DecisionFormatter
from ..utils import (
    SYMBOL, PERCENTAGE, AMOUNT, TIMEFRAME,
    with_progress, ValidationError,
    progress_manager, spinner_manager,
    cache_manager
)

# Imports des services (à adapter selon l'architecture finale)
# from finagent.business.strategy.strategy_engine import StrategyEngine
# from finagent.business.strategy.strategy_validator import StrategyValidator
# from finagent.business.backtest.backtest_engine import BacktestEngine

console = Console()


@click.group()
def strategy():
    """Commandes de gestion des stratégies d'investissement."""
    pass


@strategy.command()
@click.argument('name', required=True)
@click.option(
    '--template', '-t',
    type=click.Choice(['basic', 'momentum', 'mean_reversion', 'pairs_trading', 'custom']),
    default='basic',
    help='Template de stratégie à utiliser'
)
@click.option(
    '--description', '-d',
    help='Description de la stratégie'
)
@click.option(
    '--risk-level',
    type=click.Choice(['low', 'medium', 'high']),
    default='medium',
    help='Niveau de risque de la stratégie'
)
@click.option(
    '--timeframe',
    type=TIMEFRAME,
    default='1d',
    help='Timeframe principal de la stratégie'
)
@click.option(
    '--output', '-o',
    type=click.Path(),
    help='Fichier de sortie (par défaut: strategies/{name}.yaml)'
)
@click.option(
    '--interactive', '-i',
    is_flag=True,
    help='Mode interactif pour créer la stratégie'
)
@click.pass_context
def create(ctx, name: str, template: str, description: str, risk_level: str,
          timeframe: str, output: Optional[str], interactive: bool):
    """
    Crée une nouvelle stratégie d'investissement.
    
    NAME: Nom de la stratégie à créer
    
    Exemples:
    \b
        finagent strategy create "Ma Stratégie RSI" --template momentum
        finagent strategy create "Arbitrage Pairs" --template pairs_trading
        finagent strategy create "Stratégie Custom" --interactive
    """
    try:
        verbose = ctx.obj.get('verbose', False) if ctx.obj else False
        
        if verbose:
            console.print(f"📝 Création de la stratégie '{name}'...", style="blue")
        
        # Validation du nom
        if len(name) < 3:
            raise ValidationError("Le nom de la stratégie doit contenir au moins 3 caractères")
        
        # Mode interactif
        if interactive:
            strategy_config = _interactive_strategy_creation(name, template)
        else:
            strategy_config = _create_strategy_from_template(
                name, template, description, risk_level, timeframe
            )
        
        # Détermination du fichier de sortie
        if not output:
            output = f"strategies/{name.lower().replace(' ', '_')}.yaml"
        
        # Création de la stratégie
        strategy_result = asyncio.run(_create_strategy_file(
            name=name,
            config=strategy_config,
            output_path=output,
            verbose=verbose
        ))
        
        # Affichage du résultat
        _display_strategy_creation_result(strategy_result, output)
    
    except ValidationError as e:
        console.print(f"❌ Erreur de validation: {e.message}", style="red")
        ctx.exit(1)
    
    except Exception as e:
        console.print(f"❌ Erreur lors de la création: {e}", style="red")
        if verbose:
            console.print_exception()
        ctx.exit(1)


@strategy.command()
@click.argument('strategy_file', type=click.Path(exists=True), required=True)
@click.option(
    '--fix/--no-fix',
    default=False,
    help='Corriger automatiquement les erreurs simples'
)
@click.option(
    '--detailed', '-d',
    is_flag=True,
    help='Validation détaillée avec suggestions'
)
@click.pass_context
def validate(ctx, strategy_file: str, fix: bool, detailed: bool):
    """
    Valide une stratégie YAML.
    
    STRATEGY_FILE: Chemin vers le fichier de stratégie
    
    Exemples:
    \b
        finagent strategy validate strategies/ma_strategy.yaml
        finagent strategy validate strategies/rsi_strategy.yaml --detailed
        finagent strategy validate strategies/pairs.yaml --fix
    """
    try:
        verbose = ctx.obj.get('verbose', False) if ctx.obj else False
        
        if verbose:
            console.print(f"🔍 Validation de '{strategy_file}'...", style="blue")
        
        # Validation de la stratégie
        validation_result = asyncio.run(_validate_strategy_file(
            strategy_file=strategy_file,
            fix_errors=fix,
            detailed=detailed,
            verbose=verbose
        ))
        
        # Affichage des résultats
        _display_validation_result(validation_result, strategy_file)
        
        # Application des corrections si demandées
        if fix and validation_result.get('fixes_applied'):
            console.print(f"✅ {len(validation_result['fixes_applied'])} corrections appliquées", style="green")
    
    except Exception as e:
        console.print(f"❌ Erreur lors de la validation: {e}", style="red")
        if verbose:
            console.print_exception()
        ctx.exit(1)


@strategy.command()
@click.argument('strategy_file', type=click.Path(exists=True), required=True)
@click.option(
    '--symbol', '-s',
    type=SYMBOL,
    help='Symbole spécifique à tester (sinon utilise ceux de la stratégie)'
)
@click.option(
    '--start-date',
    type=click.DateTime(formats=['%Y-%m-%d']),
    help='Date de début du test (par défaut: 1 an)'
)
@click.option(
    '--end-date',
    type=click.DateTime(formats=['%Y-%m-%d']),
    help='Date de fin du test (par défaut: aujourd\'hui)'
)
@click.option(
    '--initial-capital',
    type=AMOUNT,
    default=100000.0,
    help='Capital initial pour le backtest'
)
@click.option(
    '--benchmark',
    type=SYMBOL,
    default='SPY',
    help='Benchmark pour la comparaison'
)
@click.option(
    '--commission',
    type=PERCENTAGE,
    default=0.001,
    help='Frais de transaction (en pourcentage)'
)
@click.option(
    '--slippage',
    type=PERCENTAGE,
    default=0.0005,
    help='Slippage estimé (en pourcentage)'
)
@click.option(
    '--save-results',
    type=click.Path(),
    help='Sauvegarder les résultats détaillés'
)
@click.option(
    '--plot/--no-plot',
    default=True,
    help='Générer des graphiques de performance'
)
@click.pass_context
def backtest(ctx, strategy_file: str, symbol: Optional[str], start_date: Optional[datetime],
            end_date: Optional[datetime], initial_capital: float, benchmark: str,
            commission: float, slippage: float, save_results: Optional[str], plot: bool):
    """
    Effectue un backtest d'une stratégie.
    
    STRATEGY_FILE: Chemin vers le fichier de stratégie
    
    Exemples:
    \b
        finagent strategy backtest strategies/rsi_strategy.yaml
        finagent strategy backtest strategies/ma_cross.yaml --symbol AAPL
        finagent strategy backtest strategies/momentum.yaml --start-date 2020-01-01
    """
    try:
        verbose = ctx.obj.get('verbose', False) if ctx.obj else False
        
        if verbose:
            console.print(f"📊 Backtest de '{strategy_file}'...", style="blue")
        
        # Dates par défaut
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=365)
        
        # Exécution du backtest
        backtest_result = asyncio.run(_run_strategy_backtest(
            strategy_file=strategy_file,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            benchmark=benchmark,
            commission=commission,
            slippage=slippage,
            verbose=verbose
        ))
        
        # Affichage des résultats
        _display_backtest_result(backtest_result)
        
        # Sauvegarde si demandée
        if save_results:
            _save_backtest_results(backtest_result, save_results)
            console.print(f"✅ Résultats sauvegardés: {save_results}", style="green")
        
        # Génération de graphiques
        if plot:
            _generate_backtest_plots(backtest_result)
    
    except Exception as e:
        console.print(f"❌ Erreur lors du backtest: {e}", style="red")
        if verbose:
            console.print_exception()
        ctx.exit(1)


@strategy.command()
@click.argument('strategy_file', type=click.Path(exists=True), required=True)
@click.option(
    '--parameters', '-p',
    multiple=True,
    help='Paramètres à optimiser (format: param_name:min:max:step)'
)
@click.option(
    '--objective',
    type=click.Choice(['total_return', 'sharpe_ratio', 'calmar_ratio', 'sortino_ratio']),
    default='sharpe_ratio',
    help='Objectif d\'optimisation'
)
@click.option(
    '--method',
    type=click.Choice(['grid_search', 'random_search', 'bayesian', 'genetic']),
    default='grid_search',
    help='Méthode d\'optimisation'
)
@click.option(
    '--iterations',
    type=int,
    default=100,
    help='Nombre d\'itérations (pour random/bayesian/genetic)'
)
@click.option(
    '--start-date',
    type=click.DateTime(formats=['%Y-%m-%d']),
    help='Date de début de l\'optimisation'
)
@click.option(
    '--end-date',
    type=click.DateTime(formats=['%Y-%m-%d']),
    help='Date de fin de l\'optimisation'
)
@click.option(
    '--save-best',
    type=click.Path(),
    help='Sauvegarder la meilleure stratégie optimisée'
)
@click.pass_context
def optimize(ctx, strategy_file: str, parameters: tuple, objective: str,
            method: str, iterations: int, start_date: Optional[datetime],
            end_date: Optional[datetime], save_best: Optional[str]):
    """
    Optimise les paramètres d'une stratégie.
    
    STRATEGY_FILE: Chemin vers le fichier de stratégie
    
    Exemples:
    \b
        finagent strategy optimize strategies/rsi.yaml -p "rsi_period:10:30:2"
        finagent strategy optimize strategies/ma.yaml -p "fast_ma:5:20:1" -p "slow_ma:20:50:5"
        finagent strategy optimize strategies/bollinger.yaml --method bayesian --iterations 200
    """
    try:
        verbose = ctx.obj.get('verbose', False) if ctx.obj else False
        
        if verbose:
            console.print(f"⚙️  Optimisation de '{strategy_file}'...", style="blue")
        
        # Validation des paramètres
        if not parameters:
            raise ValidationError("Au moins un paramètre à optimiser doit être spécifié")
        
        # Parsing des paramètres
        parsed_params = _parse_optimization_parameters(parameters)
        
        # Dates par défaut
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=365)
        
        # Optimisation
        optimization_result = asyncio.run(_optimize_strategy_parameters(
            strategy_file=strategy_file,
            parameters=parsed_params,
            objective=objective,
            method=method,
            iterations=iterations,
            start_date=start_date,
            end_date=end_date,
            verbose=verbose
        ))
        
        # Affichage des résultats
        _display_optimization_result(optimization_result)
        
        # Sauvegarde de la meilleure stratégie
        if save_best:
            _save_optimized_strategy(optimization_result, save_best)
            console.print(f"✅ Meilleure stratégie sauvegardée: {save_best}", style="green")
    
    except ValidationError as e:
        console.print(f"❌ Erreur de validation: {e.message}", style="red")
        ctx.exit(1)
    
    except Exception as e:
        console.print(f"❌ Erreur lors de l'optimisation: {e}", style="red")
        if verbose:
            console.print_exception()
        ctx.exit(1)


@strategy.command()
@click.option(
    '--directory', '-d',
    type=click.Path(exists=True),
    default='strategies',
    help='Répertoire des stratégies'
)
@click.option(
    '--format',
    type=click.Choice(['table', 'list', 'detailed']),
    default='table',
    help='Format d\'affichage'
)
@click.option(
    '--filter-risk',
    type=click.Choice(['low', 'medium', 'high']),
    help='Filtrer par niveau de risque'
)
@click.option(
    '--filter-timeframe',
    type=TIMEFRAME,
    help='Filtrer par timeframe'
)
@click.pass_context
def list(ctx, directory: str, format: str, filter_risk: Optional[str],
         filter_timeframe: Optional[str]):
    """
    Liste toutes les stratégies disponibles.
    
    Exemples:
    \b
        finagent strategy list
        finagent strategy list --format detailed
        finagent strategy list --filter-risk low --filter-timeframe 1d
    """
    try:
        verbose = ctx.obj.get('verbose', False) if ctx.obj else False
        
        if verbose:
            console.print(f"📋 Recherche des stratégies dans '{directory}'...", style="blue")
        
        # Récupération des stratégies
        strategies = asyncio.run(_list_available_strategies(
            directory=directory,
            filter_risk=filter_risk,
            filter_timeframe=filter_timeframe,
            verbose=verbose
        ))
        
        if not strategies:
            console.print("📭 Aucune stratégie trouvée", style="yellow")
            console.print(f"💡 Vérifiez le répertoire '{directory}' ou créez une nouvelle stratégie")
            return
        
        # Affichage selon le format
        if format == 'list':
            for strategy in strategies:
                console.print(f"• {strategy['name']}")
        elif format == 'detailed':
            _display_strategies_detailed(strategies)
        else:
            _display_strategies_table(strategies)
    
    except Exception as e:
        console.print(f"❌ Erreur lors de la récupération: {e}", style="red")
        if verbose:
            console.print_exception()
        ctx.exit(1)


@strategy.command()
@click.argument('strategy_file', type=click.Path(exists=True), required=True)
@click.pass_context
def show(ctx, strategy_file: str):
    """
    Affiche le contenu détaillé d'une stratégie.
    
    STRATEGY_FILE: Chemin vers le fichier de stratégie
    
    Exemples:
    \b
        finagent strategy show strategies/rsi_strategy.yaml
        finagent strategy show strategies/momentum.yaml
    """
    try:
        verbose = ctx.obj.get('verbose', False) if ctx.obj else False
        
        # Chargement et affichage de la stratégie
        strategy_content = asyncio.run(_load_strategy_content(
            strategy_file=strategy_file,
            verbose=verbose
        ))
        
        _display_strategy_content(strategy_content, strategy_file)
    
    except Exception as e:
        console.print(f"❌ Erreur lors du chargement: {e}", style="red")
        if verbose:
            console.print_exception()
        ctx.exit(1)


# === Fonctions d'implémentation ===

def _interactive_strategy_creation(name: str, template: str) -> Dict[str, Any]:
    """Crée une stratégie en mode interactif."""
    console.print(Panel.fit(
        f"🤖 [bold blue]Assistant de Création de Stratégie[/bold blue]\n\n"
        f"Nom: [cyan]{name}[/cyan]\n"
        f"Template: [yellow]{template}[/yellow]",
        title="📝 Création Interactive",
        border_style="blue"
    ))
    
    # Collecte des informations de base
    description = Prompt.ask("📝 Description de la stratégie", default=f"Stratégie {name}")
    risk_level = Prompt.ask(
        "⚖️  Niveau de risque",
        choices=['low', 'medium', 'high'],
        default='medium'
    )
    timeframe = Prompt.ask("⏰ Timeframe principal", default='1d')
    
    # Configuration spécifique selon le template
    if template == 'momentum':
        lookback_period = int(Prompt.ask("📊 Période de lookback", default="20"))
        threshold = float(Prompt.ask("🎯 Seuil de momentum (%)", default="5.0"))
    elif template == 'mean_reversion':
        ma_period = int(Prompt.ask("📈 Période moyenne mobile", default="50"))
        deviation_threshold = float(Prompt.ask("📏 Seuil d'écart (%)", default="2.0"))
    elif template == 'pairs_trading':
        pair_symbol = Prompt.ask("👥 Symbole de la paire", default="SPY")
        correlation_threshold = float(Prompt.ask("🔗 Seuil de corrélation", default="0.8"))
    
    # Paramètres de gestion du risque
    stop_loss = float(Prompt.ask("🛑 Stop Loss (%)", default="5.0"))
    take_profit = float(Prompt.ask("🎯 Take Profit (%)", default="10.0"))
    
    return {
        "name": name,
        "description": description,
        "risk_level": risk_level,
        "timeframe": timeframe,
        "template": template,
        "parameters": {
            "stop_loss": stop_loss / 100,
            "take_profit": take_profit / 100
        }
    }


def _create_strategy_from_template(name: str, template: str, description: str,
                                 risk_level: str, timeframe: str) -> Dict[str, Any]:
    """Crée une stratégie à partir d'un template."""
    base_config = {
        "name": name,
        "description": description or f"Stratégie {name} basée sur {template}",
        "risk_level": risk_level,
        "timeframe": timeframe,
        "template": template,
        "created_at": datetime.now().isoformat(),
        "version": "1.0.0"
    }
    
    # Configuration spécifique par template
    if template == 'basic':
        base_config.update({
            "signals": {
                "entry": {
                    "conditions": ["price > sma_20", "volume > volume_avg"],
                    "logic": "AND"
                },
                "exit": {
                    "conditions": ["price < sma_20", "stop_loss", "take_profit"],
                    "logic": "OR"
                }
            },
            "parameters": {
                "sma_period": 20,
                "volume_period": 10,
                "stop_loss": 0.05,
                "take_profit": 0.10
            }
        })
    
    elif template == 'momentum':
        base_config.update({
            "signals": {
                "entry": {
                    "conditions": ["rsi > 70", "price_change_5d > 0.05"],
                    "logic": "AND"
                },
                "exit": {
                    "conditions": ["rsi < 30", "stop_loss", "take_profit"],
                    "logic": "OR"
                }
            },
            "parameters": {
                "rsi_period": 14,
                "momentum_period": 5,
                "momentum_threshold": 0.05,
                "stop_loss": 0.08,
                "take_profit": 0.15
            }
        })
    
    elif template == 'mean_reversion':
        base_config.update({
            "signals": {
                "entry": {
                    "conditions": ["price < bollinger_lower", "rsi < 30"],
                    "logic": "AND"
                },
                "exit": {
                    "conditions": ["price > bollinger_upper", "rsi > 70", "stop_loss"],
                    "logic": "OR"
                }
            },
            "parameters": {
                "bollinger_period": 20,
                "bollinger_std": 2.0,
                "rsi_period": 14,
                "stop_loss": 0.10
            }
        })
    
    return base_config


async def _create_strategy_file(name: str, config: Dict[str, Any],
                              output_path: str, verbose: bool) -> Dict[str, Any]:
    """Crée le fichier de stratégie."""
    
    with spinner_manager.spinner_context("📝 Création du fichier de stratégie..."):
        await asyncio.sleep(1)
        
        # Création du répertoire si nécessaire
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Conversion en YAML et sauvegarde
        import yaml
        with open(output_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False, indent=2)
    
    return {
        "name": name,
        "config": config,
        "output_path": output_path,
        "file_size": Path(output_path).stat().st_size,
        "created_at": datetime.now()
    }


async def _validate_strategy_file(strategy_file: str, fix_errors: bool,
                                detailed: bool, verbose: bool) -> Dict[str, Any]:
    """Valide un fichier de stratégie."""
    
    with progress_manager.progress_context() as progress:
        # Étape 1: Lecture du fichier
        read_task = progress.add_task("📖 Lecture du fichier", total=100)
        for i in range(100):
            await asyncio.sleep(0.01)
            progress.update(read_task, advance=1)
        
        # Étape 2: Validation de la syntaxe YAML
        yaml_task = progress.add_task("🔍 Validation YAML", total=100)
        for i in range(100):
            await asyncio.sleep(0.005)
            progress.update(yaml_task, advance=1)
        
        # Étape 3: Validation de la structure
        struct_task = progress.add_task("🏗️  Validation structure", total=100)
        for i in range(100):
            await asyncio.sleep(0.01)
            progress.update(struct_task, advance=1)
        
        # Étape 4: Validation logique
        logic_task = progress.add_task("🧠 Validation logique", total=100)
        for i in range(100):
            await asyncio.sleep(0.015)
            progress.update(logic_task, advance=1)
    
    # Simulation de résultats de validation
    errors = []
    warnings = []
    suggestions = []
    
    # Quelques erreurs/warnings simulés
    if "test" in strategy_file.lower():
        warnings.append({
            "type": "warning",
            "message": "Le nom de fichier contient 'test' - considérez un nom plus descriptif",
            "line": None,
            "fixable": False
        })
    
    if detailed:
        suggestions.extend([
            "Considérez ajouter plus de conditions de sortie",
            "Vous pourriez inclure une validation de volume",
            "Pensez à définir des niveaux de position sizing"
        ])
    
    return {
        "file": strategy_file,
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "suggestions": suggestions if detailed else [],
        "fixes_applied": [] if not fix_errors else ["Format YAML normalisé"],
        "validation_date": datetime.now()
    }


async def _run_strategy_backtest(strategy_file: str, symbol: Optional[str],
                               start_date: datetime, end_date: datetime,
                               initial_capital: float, benchmark: str,
                               commission: float, slippage: float,
                               verbose: bool) -> Dict[str, Any]:
    """Exécute le backtest d'une stratégie."""
    
    with progress_manager.progress_context() as progress:
        # Étape 1: Chargement de la stratégie
        load_task = progress.add_task("📖 Chargement stratégie", total=100)
        for i in range(100):
            await asyncio.sleep(0.01)
            progress.update(load_task, advance=1)
        
        # Étape 2: Récupération des données historiques
        data_task = progress.add_task("📊 Récupération données", total=100)
        for i in range(100):
            await asyncio.sleep(0.02)
            progress.update(data_task, advance=1)
        
        # Étape 3: Exécution du backtest
        backtest_task = progress.add_task("🔄 Exécution backtest", total=100)
        for i in range(100):
            await asyncio.sleep(0.03)
            progress.update(backtest_task, advance=1)
        
        # Étape 4: Calcul des métriques
        metrics_task = progress.add_task("📈 Calcul métriques", total=100)
        for i in range(100):
            await asyncio.sleep(0.02)
            progress.update(metrics_task, advance=1)
    
    # Simulation de résultats de backtest
    total_days = (end_date - start_date).days
    
    return {
        "strategy_file": strategy_file,
        "symbol": symbol or "AAPL",  # Symbole par défaut
        "period": {
            "start_date": start_date,
            "end_date": end_date,
            "total_days": total_days
        },
        "capital": {
            "initial": initial_capital,
            "final": initial_capital * 1.187,  # +18.7% simulé
            "peak": initial_capital * 1.243,
            "trough": initial_capital * 0.912
        },
        "performance": {
            "total_return": 0.187,
            "annualized_return": 0.156,
            "volatility": 0.184,
            "sharpe_ratio": 1.23,
            "sortino_ratio": 1.67,
            "calmar_ratio": 1.95,
            "max_drawdown": -0.088,
            "win_rate": 0.64,
            "profit_factor": 1.85
        },
        "benchmark_comparison": {
            "benchmark": benchmark,
            "benchmark_return": 0.134,
            "excess_return": 0.053,
            "tracking_error": 0.045,
            "information_ratio": 1.18,
            "beta": 1.05,
            "alpha": 0.021
        },
        "trade_statistics": {
            "total_trades": 47,
            "winning_trades": 30,
            "losing_trades": 17,
            "avg_win": 0.034,
            "avg_loss": -0.019,
            "largest_win": 0.087,
            "largest_loss": -0.054
        },
        "costs": {
            "total_commission": initial_capital * commission * 47,  # 47 trades
            "total_slippage": initial_capital * slippage * 47,
            "total_costs": initial_capital * (commission + slippage) * 47
        }
    }


async def _optimize_strategy_parameters(strategy_file: str, parameters: Dict[str, Dict],
                                      objective: str, method: str, iterations: int,
                                      start_date: datetime, end_date: datetime,
                                      verbose: bool) -> Dict[str, Any]:
    """Optimise les paramètres d'une stratégie."""
    
    with progress_manager.progress_context() as progress:
        # Initialisation
        init_task = progress.add_task("⚙️  Initialisation optimisation", total=100)
        for i in range(100):
            await asyncio.sleep(0.01)
            progress.update(init_task, advance=1)
        
        # Optimisation des paramètres
        optim_task = progress.add_task(f"🔄 Optimisation ({method})", total=iterations)
        for i in range(iterations):
            await asyncio.sleep(0.05)  # Simulation d'une itération
            progress.update(optim_task, advance=1)
        
        # Évaluation finale
        eval_task = progress.add_task("📊 Évaluation résultats", total=100)
        for i in range(100):
            await asyncio.sleep(0.01)
            progress.update(eval_task, advance=1)
    
    # Simulation de résultats d'optimisation
    return {
        "strategy_file": strategy_file,
        "method": method,
        "objective": objective,
        "iterations": iterations,
        "best_parameters": {
            "rsi_period": 16,  # exemple
            "sma_period": 22,
            "stop_loss": 0.065,
            "take_profit": 0.125
        },
        "best_performance": {
            objective: 1.67,  # valeur optimisée
            "total_return": 0.234,
            "max_drawdown": -0.067,
            "win_rate": 0.68
        },
        "optimization_history": [
            {"iteration": 1, objective: 1.23},
            {"iteration": 25, objective: 1.45},
            {"iteration": 50, objective: 1.58},
            {"iteration": 75, objective: 1.64},
            {"iteration": 100, objective: 1.67}
        ],
        "parameter_sensitivity": {
            "rsi_period": {"min": 1.12, "max": 1.67, "optimal": 16},
            "sma_period": {"min": 1.05, "max": 1.58, "optimal": 22}
        }
    }


async def _list_available_strategies(directory: str, filter_risk: Optional[str],
                                   filter_timeframe: Optional[str],
                                   verbose: bool) -> List[Dict[str, Any]]:
    """Liste les stratégies disponibles."""
    
    with spinner_manager.spinner_context("📋 Recherche des stratégies..."):
        await asyncio.sleep(0.8)
    
    # Simulation de stratégies disponibles
    strategies = [
        {
            "name": "RSI Momentum",
            "file": "strategies/rsi_momentum.yaml",
            "description": "Stratégie basée sur RSI avec momentum",
            "risk_level": "medium",
            "timeframe": "1d",
            "created_at": datetime.now() - timedelta(days=30),
            "last_backtest": datetime.now() - timedelta(days=7),
            "performance": {"sharpe": 1.23, "return": 0.187}
        },
        {
            "name": "MA Cross",
            "file": "strategies/ma_cross.yaml",
            "description": "Croisement de moyennes mobiles",
            "risk_level": "low",
            "timeframe": "1d",
            "created_at": datetime.now() - timedelta(days=45),
            "last_backtest": datetime.now() - timedelta(days=3),
            "performance": {"sharpe": 1.05, "return": 0.134}
        },
        {
            "name": "Pairs Trading",
            "file": "strategies/pairs_trading.yaml",
            "description": "Arbitrage de paires corrélées",
            "risk_level": "high",
            "timeframe": "1h",
            "created_at": datetime.now() - timedelta(days=15),
            "last_backtest": datetime.now() - timedelta(days=1),
            "performance": {"sharpe": 1.78, "return": 0.256}
        }
    ]
    
    # Application des filtres
    if filter_risk:
        strategies = [s for s in strategies if s['risk_level'] == filter_risk]
    
    if filter_timeframe:
        strategies = [s for s in strategies if s['timeframe'] == filter_timeframe]
    
    return strategies


async def _load_strategy_content(strategy_file: str, verbose: bool) -> Dict[str, Any]:
    """Charge le contenu d'une stratégie."""
    
    with spinner_manager.spinner_context("📖 Chargement de la stratégie..."):
        await asyncio.sleep(0.5)
    
    # Simulation de contenu de stratégie
    return {
        "name": "RSI Momentum Strategy",
        "description": "Stratégie basée sur l'indicateur RSI avec confirmation de momentum",
        "version": "1.2.0",
        "risk_level": "medium",
        "timeframe": "1d",
        "symbols": ["AAPL", "MSFT", "GOOGL"],
        "signals": {
            "entry": {
                "conditions": ["rsi > 70", "volume > volume_avg * 1.5"],
                "logic": "AND"
            },
            "exit": {
                "conditions": ["rsi < 30", "stop_loss", "take_profit"],
                "logic": "OR"
            }
        },
        "parameters": {
            "rsi_period": 14,
            "volume_period": 20,
            "stop_loss": 0.05,
            "take_profit": 0.10
        },
        "risk_management": {
            "max_position_size": 0.1,
            "max_portfolio_risk": 0.02,
            "diversification_limit": 5
        },
        "file_path": strategy_file,
        "raw_content": "# Contenu YAML simulé..."
    }


def _parse_optimization_parameters(parameters: tuple) -> Dict[str, Dict]:
    """Parse les paramètres d'optimisation."""
    parsed = {}
    
    for param in parameters:
        try:
            name, min_val, max_val, step = param.split(':')
            parsed[name] = {
                'min': float(min_val),
                'max': float(max_val),
                'step': float(step)
            }
        except ValueError:
            raise ValidationError(f"Format invalide pour le paramètre: {param}. Utilisez format:min:max:step")
    
    return parsed


# === Fonctions d'affichage ===

def _display_strategy_creation_result(strategy_result: Dict[str, Any], output_path: str) -> None:
    """Affiche le résultat de création de stratégie."""
    console.print(Panel.fit(
        f"✅ [green]Stratégie créée avec succès![/green]\n\n"
        f"📝 [bold]{strategy_result['name']}[/bold]\n"
        f"📁 Fichier: {output_path}\n"
        f"📏 Taille: {strategy_result['file_size']} octets\n"
        f"🕒 Créée le: {strategy_result['created_at'].strftime('%d/%m/%Y à %H:%M')}\n\n"
        f"💡 [dim]Utilisez 'finagent strategy validate {output_path}' pour valider[/dim]",
        title="📝 Nouvelle Stratégie",
        border_style="green"
    ))


def _display_validation_result(validation_result: Dict[str, Any], strategy_file: str) -> None:
    """Affiche les résultats de validation."""
    if validation_result['valid']:
        console.print(f"✅ [green]Stratégie '{strategy_file}' valide![/green]")
    else:
        console.print(f"❌ [red]Erreurs détectées dans '{strategy_file}'[/red]")
    
    # Erreurs
    if validation_result['errors']:
        console.print("\n🚨 [red bold]Erreurs:[/red bold]")
        for error in validation_result['errors']:
            console.print(f"  • {error['message']}")
    
    # Warnings
    if validation_result['warnings']:
        console.print("\n⚠️  [yellow bold]Avertissements:[/yellow bold]")
        for warning in validation_result['warnings']:
            console.print(f"  • {warning['message']}")
    
    # Suggestions
    if validation_result['suggestions']:
        console.print("\n💡 [blue bold]Suggestions:[/blue bold]")
        for suggestion in validation_result['suggestions']:
            console.print(f"  • {suggestion}")


def _display_backtest_result(backtest_result: Dict[str, Any]) -> None:
    """Affiche les résultats de backtest."""
    formatter = AnalysisFormatter()
    
    # Panel principal avec résumé
    console.print(Panel.fit(
        f"📊 [bold]Résultats du Backtest[/bold]\n\n"
        f"🎯 Symbole: [cyan]{backtest_result['symbol']}[/cyan]\n"
        f"📅 Période: {backtest_result['period']['start_date'].strftime('%d/%m/%Y')} → "
        f"{backtest_result['period']['end_date'].strftime('%d/%m/%Y')}\n"
        f"💰 Capital: ${backtest_result['capital']['initial']:,.0f} → "
        f"${backtest_result['capital']['final']:,.0f}\n"
        f"📈 Rendement Total: [green]{backtest_result['performance']['total_return']:.1%}[/green]\n"
        f"📊 Ratio de Sharpe: [cyan]{backtest_result['performance']['sharpe_ratio']:.2f}[/cyan]",
        title="🔬 Backtest",
        border_style="blue"
    ))
    
    # Tableau des métriques de performance
    table = Table(title="📈 Métriques de Performance", show_header=True)
    table.add_column("Métrique", style="cyan")
    table.add_column("Valeur", justify="right")
    table.add_column("Benchmark", justify="right")
    
    perf = backtest_result['performance']
    bench = backtest_result['benchmark_comparison']
    
    metrics = [
        ("Rendement Total", f"{perf['total_return']:.1%}", f"{bench['benchmark_return']:.1%}"),
        ("Rendement Annualisé", f"{perf['annualized_return']:.1%}", "-"),
        ("Volatilité", f"{perf['volatility']:.1%}", "-"),
        ("Ratio de Sharpe", f"{perf['sharpe_ratio']:.2f}", "-"),
        ("Drawdown Max", f"{perf['max_drawdown']:.1%}", "-"),
        ("Taux de Gain", f"{perf['win_rate']:.1%}", "-")
    ]
    
    for metric, value, benchmark in metrics:
        table.add_row(metric, value, benchmark)
    
    console.print()
    console.print(table)


def _display_optimization_result(optimization_result: Dict[str, Any]) -> None:
    """Affiche les résultats d'optimisation."""
    console.print(Panel.fit(
        f"⚙️  [bold]Optimisation Terminée[/bold]\n\n"
        f"🎯 Objectif: {optimization_result['objective']}\n"
        f"🔄 Méthode: {optimization_result['method']}\n"
        f"📊 Itérations: {optimization_result['iterations']}\n"
        f"🏆 Meilleur Score: [green]{optimization_result['best_performance'][optimization_result['objective']]:.2f}[/green]",
        title="⚙️  Optimisation",
        border_style="green"
    ))
    
    # Tableau des meilleurs paramètres
    table = Table(title="🏆 Meilleurs Paramètres", show_header=True)
    table.add_column("Paramètre", style="cyan")
    table.add_column("Valeur Optimale", justify="right")
    
    for param, value in optimization_result['best_parameters'].items():
        if isinstance(value, float):
            formatted_value = f"{value:.3f}"
        else:
            formatted_value = str(value)
        table.add_row(param, formatted_value)
    
    console.print()
    console.print(table)


def _display_strategies_table(strategies: List[Dict[str, Any]]) -> None:
    """Affiche la liste des stratégies sous forme de tableau."""
    table = Table(title="📋 Stratégies Disponibles", show_header=True)
    
    table.add_column("Nom", style="cyan bold")
    table.add_column("Risque", justify="center")
    table.add_column("Timeframe", justify="center")
    table.add_column("Sharpe", justify="right")
    table.add_column("Rendement", justify="right")
    table.add_column("Dernier Test", style="dim")
    
    for strategy in strategies:
        # Emoji pour le niveau de risque
        risk_emoji = {"low": "🟢", "medium": "🟡", "high": "🔴"}
        risk_display = f"{risk_emoji.get(strategy['risk_level'], '⚪')} {strategy['risk_level']}"
        
        # Formatage des performances
        sharpe = f"{strategy['performance']['sharpe']:.2f}"
        return_pct = f"{strategy['performance']['return']:.1%}"
        
        # Date du dernier test
        last_test = strategy['last_backtest'].strftime('%d/%m/%Y')
        
        table.add_row(
            strategy['name'],
            risk_display,
            strategy['timeframe'],
            sharpe,
            return_pct,
            last_test
        )
    
    console.print(table)


def _display_strategies_detailed(strategies: List[Dict[str, Any]]) -> None:
    """Affiche la liste détaillée des stratégies."""
    for strategy in strategies:
        console.print(Panel.fit(
            f"📝 [bold]{strategy['name']}[/bold]\n"
            f"📄 {strategy['description']}\n"
            f"📁 {strategy['file']}\n"
            f"⚖️  Risque: {strategy['risk_level']} | "
            f"⏰ Timeframe: {strategy['timeframe']}\n"
            f"📊 Sharpe: {strategy['performance']['sharpe']:.2f} | "
            f"📈 Rendement: {strategy['performance']['return']:.1%}\n"
            f"🕒 Créée: {strategy['created_at'].strftime('%d/%m/%Y')} | "
            f"🔬 Dernier test: {strategy['last_backtest'].strftime('%d/%m/%Y')}",
            border_style="blue"
        ))
        console.print()


def _display_strategy_content(strategy_content: Dict[str, Any], strategy_file: str) -> None:
    """Affiche le contenu détaillé d'une stratégie."""
    # Informations générales
    console.print(Panel.fit(
        f"📝 [bold]{strategy_content['name']}[/bold]\n"
        f"📄 {strategy_content['description']}\n"
        f"🏷️  Version: {strategy_content['version']}\n"
        f"⚖️  Risque: {strategy_content['risk_level']} | "
        f"⏰ Timeframe: {strategy_content['timeframe']}\n"
        f"🎯 Symboles: {', '.join(strategy_content['symbols'])}",
        title=f"📊 {Path(strategy_file).stem}",
        border_style="blue"
    ))
    
    # Paramètres
    console.print("\n📊 [bold]Paramètres:[/bold]")
    params_table = Table(show_header=True)
    params_table.add_column("Paramètre", style="cyan")
    params_table.add_column("Valeur", justify="right")
    
    for param, value in strategy_content['parameters'].items():
        params_table.add_row(param, str(value))
    
    console.print(params_table)
    
    # Signaux (optionnel)
    if strategy_content.get('signals'):
        console.print("\n🚦 [bold]Signaux:[/bold]")
        signals = strategy_content['signals']
        
        console.print(f"  📈 [green]Entrée:[/green] {' AND '.join(signals['entry']['conditions'])}")
        console.print(f"  📉 [red]Sortie:[/red] {' OR '.join(signals['exit']['conditions'])}")


def _save_backtest_results(backtest_result: Dict[str, Any], filepath: str) -> None:
    """Sauvegarde les résultats de backtest."""
    import json
    
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'w') as f:
        json.dump(backtest_result, f, indent=2, default=str)


def _save_optimized_strategy(optimization_result: Dict[str, Any], filepath: str) -> None:
    """Sauvegarde la stratégie optimisée."""
    import yaml
    
    # Créer une nouvelle stratégie avec les paramètres optimisés
    optimized_strategy = {
        "name": f"Optimized Strategy",
        "description": f"Stratégie optimisée avec {optimization_result['method']}",
        "version": "1.0.0-optimized",
        "optimization_info": {
            "method": optimization_result['method'],
            "objective": optimization_result['objective'],
            "optimization_date": datetime.now().isoformat()
        },
        "parameters": optimization_result['best_parameters'],
        "performance": optimization_result['best_performance']
    }
    
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'w') as f:
        yaml.dump(optimized_strategy, f, default_flow_style=False, indent=2)


def _generate_backtest_plots(backtest_result: Dict[str, Any]) -> None:
    """Génère les graphiques de backtest."""
    console.print("\n📊 [yellow]Génération de graphiques non encore implémentée[/yellow]")
    console.print("💡 Les résultats sont disponibles dans le tableau ci-dessus")