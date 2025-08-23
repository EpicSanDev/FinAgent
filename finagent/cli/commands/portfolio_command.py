"""
Commande de gestion de portefeuilles pour la CLI FinAgent.

Cette commande permet de créer, gérer et analyser des portefeuilles
d'investissement avec calculs de performance et optimisation.
"""

import asyncio
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm

from ..formatters import PortfolioFormatter, AnalysisFormatter
from ..utils import (
    SYMBOL, PERCENTAGE, AMOUNT,
    with_progress, ValidationError,
    progress_manager, spinner_manager,
    cache_manager
)

# Imports des services (à adapter selon l'architecture finale)
# from finagent.business.portfolio.portfolio_manager import PortfolioManager
# from finagent.business.portfolio.optimizer import PortfolioOptimizer
# from finagent.data.portfolio.portfolio_repository import PortfolioRepository

console = Console()


@click.group()
def portfolio():
    """Commandes de gestion de portefeuilles d'investissement."""
    pass


@portfolio.command()
@click.argument('name', required=True)
@click.option(
    '--description', '-d',
    help='Description du portefeuille'
)
@click.option(
    '--initial-balance', '-b',
    type=AMOUNT,
    default=10000.0,
    help='Solde initial du portefeuille'
)
@click.option(
    '--currency',
    type=click.Choice(['USD', 'EUR', 'GBP', 'CAD']),
    default='USD',
    help='Devise du portefeuille'
)
@click.option(
    '--risk-profile',
    type=click.Choice(['conservative', 'moderate', 'aggressive']),
    default='moderate',
    help='Profil de risque'
)
@click.option(
    '--benchmark',
    type=SYMBOL,
    default='SPY',
    help='Indice de référence pour la comparaison'
)
@click.pass_context
def create(ctx, name: str, description: str, initial_balance: float,
          currency: str, risk_profile: str, benchmark: str):
    """
    Crée un nouveau portefeuille d'investissement.
    
    NAME: Nom unique du portefeuille
    
    Exemples:
    \b
        finagent portfolio create "Mon Portfolio Tech" --initial-balance 50000
        finagent portfolio create "Retraite" --risk-profile conservative
        finagent portfolio create "Trading" --risk-profile aggressive --currency EUR
    """
    try:
        verbose = ctx.obj.get('verbose', False) if ctx.obj else False
        
        if verbose:
            console.print(f"📊 Création du portefeuille '{name}'...", style="blue")
        
        # Validation du nom
        if len(name) < 3:
            raise ValidationError("Le nom du portefeuille doit contenir au moins 3 caractères")
        
        # Création du portefeuille
        portfolio_data = asyncio.run(_create_portfolio(
            name=name,
            description=description,
            initial_balance=initial_balance,
            currency=currency,
            risk_profile=risk_profile,
            benchmark=benchmark,
            verbose=verbose
        ))
        
        # Affichage du résultat
        _display_portfolio_creation_result(portfolio_data)
    
    except ValidationError as e:
        console.print(f"❌ Erreur de validation: {e.message}", style="red")
        ctx.exit(1)
    
    except Exception as e:
        console.print(f"❌ Erreur lors de la création: {e}", style="red")
        if verbose:
            console.print_exception()
        ctx.exit(1)


@portfolio.command()
@click.argument('portfolio_name', required=True)
@click.argument('symbol', type=SYMBOL, required=True)
@click.option(
    '--quantity', '-q',
    type=float,
    help='Quantité d\'actions (requis si pas de montant)'
)
@click.option(
    '--amount', '-a',
    type=AMOUNT,
    help='Montant à investir (requis si pas de quantité)'
)
@click.option(
    '--price', '-p',
    type=AMOUNT,
    help='Prix par action (utilise le prix actuel si non spécifié)'
)
@click.option(
    '--order-type',
    type=click.Choice(['market', 'limit', 'stop']),
    default='market',
    help='Type d\'ordre'
)
@click.option(
    '--validate/--no-validate',
    default=True,
    help='Valider l\'ordre avant exécution'
)
@click.pass_context
def add(ctx, portfolio_name: str, symbol: str, quantity: Optional[float],
        amount: Optional[float], price: Optional[float], order_type: str,
        validate: bool):
    """
    Ajoute une position à un portefeuille.
    
    PORTFOLIO_NAME: Nom du portefeuille
    SYMBOL: Symbole de l'action à acheter
    
    Exemples:
    \b
        finagent portfolio add "Mon Portfolio" AAPL --quantity 10
        finagent portfolio add "Mon Portfolio" MSFT --amount 5000
        finagent portfolio add "Trading" TSLA --quantity 5 --price 200.00
    """
    try:
        verbose = ctx.obj.get('verbose', False) if ctx.obj else False
        
        # Validation des paramètres
        if not quantity and not amount:
            raise ValidationError("Vous devez spécifier soit --quantity soit --amount")
        
        if quantity and amount:
            raise ValidationError("Vous ne pouvez pas spécifier à la fois --quantity et --amount")
        
        if verbose:
            console.print(f"💰 Ajout de {symbol} au portefeuille '{portfolio_name}'...", style="blue")
        
        # Exécution de l'ajout
        add_result = asyncio.run(_add_position_to_portfolio(
            portfolio_name=portfolio_name,
            symbol=symbol,
            quantity=quantity,
            amount=amount,
            price=price,
            order_type=order_type,
            validate=validate,
            verbose=verbose
        ))
        
        # Affichage du résultat
        _display_add_position_result(add_result)
    
    except ValidationError as e:
        console.print(f"❌ Erreur de validation: {e.message}", style="red")
        ctx.exit(1)
    
    except Exception as e:
        console.print(f"❌ Erreur lors de l'ajout: {e}", style="red")
        if verbose:
            console.print_exception()
        ctx.exit(1)


@portfolio.command()
@click.argument('portfolio_name', required=True)
@click.option(
    '--detailed', '-d',
    is_flag=True,
    help='Affichage détaillé avec métriques avancées'
)
@click.option(
    '--period',
    type=click.Choice(['1d', '1w', '1m', '3m', '6m', '1y', 'ytd', 'all']),
    default='1m',
    help='Période d\'analyse de performance'
)
@click.option(
    '--include-benchmark',
    is_flag=True,
    help='Inclure la comparaison avec le benchmark'
)
@click.option(
    '--group-by',
    type=click.Choice(['sector', 'country', 'market_cap', 'none']),
    default='none',
    help='Grouper les positions par critère'
)
@click.option(
    '--format',
    type=click.Choice(['table', 'chart', 'json']),
    default='table',
    help='Format d\'affichage'
)
@click.pass_context
def show(ctx, portfolio_name: str, detailed: bool, period: str,
         include_benchmark: bool, group_by: str, format: str):
    """
    Affiche le contenu et les performances d'un portefeuille.
    
    PORTFOLIO_NAME: Nom du portefeuille à afficher
    
    Exemples:
    \b
        finagent portfolio show "Mon Portfolio"
        finagent portfolio show "Trading" --detailed --period 1y
        finagent portfolio show "Retraite" --include-benchmark --group-by sector
    """
    try:
        verbose = ctx.obj.get('verbose', False) if ctx.obj else False
        
        if verbose:
            console.print(f"📊 Récupération du portefeuille '{portfolio_name}'...", style="blue")
        
        # Récupération des données du portefeuille
        portfolio_data = asyncio.run(_get_portfolio_data(
            portfolio_name=portfolio_name,
            period=period,
            include_benchmark=include_benchmark,
            detailed=detailed,
            verbose=verbose
        ))
        
        # Affichage selon le format demandé
        if format == 'json':
            import json
            console.print_json(json.dumps(portfolio_data, default=str, indent=2))
        elif format == 'chart':
            _display_portfolio_chart(portfolio_data)
        else:
            _display_portfolio_table(portfolio_data, detailed, group_by)
    
    except Exception as e:
        console.print(f"❌ Erreur lors de l'affichage: {e}", style="red")
        if verbose:
            console.print_exception()
        ctx.exit(1)


@portfolio.command()
@click.option(
    '--format',
    type=click.Choice(['table', 'simple']),
    default='table',
    help='Format d\'affichage'
)
@click.pass_context
def list(ctx, format: str):
    """
    Liste tous les portefeuilles existants.
    
    Exemples:
    \b
        finagent portfolio list
        finagent portfolio list --format simple
    """
    try:
        verbose = ctx.obj.get('verbose', False) if ctx.obj else False
        
        # Récupération de la liste des portefeuilles
        portfolios = asyncio.run(_list_portfolios(verbose))
        
        if not portfolios:
            console.print("📭 Aucun portefeuille trouvé", style="yellow")
            console.print("💡 Utilisez 'finagent portfolio create' pour créer votre premier portefeuille")
            return
        
        # Affichage de la liste
        if format == 'simple':
            for p in portfolios:
                console.print(f"• {p['name']}")
        else:
            _display_portfolios_table(portfolios)
    
    except Exception as e:
        console.print(f"❌ Erreur lors de la récupération: {e}", style="red")
        if verbose:
            console.print_exception()
        ctx.exit(1)


@portfolio.command()
@click.argument('portfolio_name', required=True)
@click.option(
    '--method',
    type=click.Choice(['mean_variance', 'min_variance', 'max_sharpe', 'risk_parity']),
    default='max_sharpe',
    help='Méthode d\'optimisation'
)
@click.option(
    '--target-return',
    type=PERCENTAGE,
    help='Rendement cible (pour mean_variance)'
)
@click.option(
    '--max-weight',
    type=PERCENTAGE,
    default=0.3,
    help='Poids maximum par position'
)
@click.option(
    '--min-weight',
    type=PERCENTAGE,
    default=0.01,
    help='Poids minimum par position'
)
@click.option(
    '--period',
    type=click.Choice(['1y', '2y', '3y', '5y']),
    default='2y',
    help='Période historique pour l\'optimisation'
)
@click.option(
    '--apply/--no-apply',
    default=False,
    help='Appliquer automatiquement l\'optimisation'
)
@click.pass_context
def optimize(ctx, portfolio_name: str, method: str, target_return: Optional[float],
            max_weight: float, min_weight: float, period: str, apply: bool):
    """
    Optimise l'allocation d'un portefeuille.
    
    PORTFOLIO_NAME: Nom du portefeuille à optimiser
    
    Exemples:
    \b
        finagent portfolio optimize "Mon Portfolio" --method max_sharpe
        finagent portfolio optimize "Retraite" --method min_variance --apply
        finagent portfolio optimize "Trading" --method mean_variance --target-return 0.12
    """
    try:
        verbose = ctx.obj.get('verbose', False) if ctx.obj else False
        
        if verbose:
            console.print(f"⚙️  Optimisation du portefeuille '{portfolio_name}'...", style="blue")
        
        # Validation des paramètres
        if method == 'mean_variance' and target_return is None:
            raise ValidationError("Le rendement cible est requis pour la méthode mean_variance")
        
        # Exécution de l'optimisation
        optimization_result = asyncio.run(_optimize_portfolio(
            portfolio_name=portfolio_name,
            method=method,
            target_return=target_return,
            max_weight=max_weight,
            min_weight=min_weight,
            period=period,
            verbose=verbose
        ))
        
        # Affichage des résultats
        _display_optimization_result(optimization_result)
        
        # Application si demandée
        if apply:
            if Confirm.ask("Voulez-vous appliquer cette optimisation ?"):
                asyncio.run(_apply_optimization(portfolio_name, optimization_result))
                console.print("✅ Optimisation appliquée avec succès", style="green")
        
    except ValidationError as e:
        console.print(f"❌ Erreur de validation: {e.message}", style="red")
        ctx.exit(1)
    
    except Exception as e:
        console.print(f"❌ Erreur lors de l'optimisation: {e}", style="red")
        if verbose:
            console.print_exception()
        ctx.exit(1)


@portfolio.command()
@click.argument('portfolio_name', required=True)
@click.option(
    '--period',
    type=click.Choice(['1d', '1w', '1m', '3m', '6m', '1y', 'ytd', 'all']),
    default='1y',
    help='Période d\'analyse'
)
@click.option(
    '--include-benchmark',
    is_flag=True,
    help='Inclure la comparaison avec le benchmark'
)
@click.option(
    '--metrics',
    multiple=True,
    type=click.Choice(['returns', 'volatility', 'sharpe', 'sortino', 'calmar', 'max_drawdown', 'var', 'all']),
    default=['returns', 'volatility', 'sharpe'],
    help='Métriques de performance à calculer'
)
@click.option(
    '--save-report',
    type=click.Path(),
    help='Sauvegarder le rapport de performance'
)
@click.pass_context
def performance(ctx, portfolio_name: str, period: str, include_benchmark: bool,
               metrics: tuple, save_report: Optional[str]):
    """
    Analyse les performances d'un portefeuille.
    
    PORTFOLIO_NAME: Nom du portefeuille à analyser
    
    Exemples:
    \b
        finagent portfolio performance "Mon Portfolio"
        finagent portfolio performance "Trading" --period 6m --include-benchmark
        finagent portfolio performance "Retraite" --metrics all --save-report rapport.pdf
    """
    try:
        verbose = ctx.obj.get('verbose', False) if ctx.obj else False
        
        if verbose:
            console.print(f"📈 Analyse des performances de '{portfolio_name}'...", style="blue")
        
        # Analyse de performance
        performance_data = asyncio.run(_analyze_portfolio_performance(
            portfolio_name=portfolio_name,
            period=period,
            include_benchmark=include_benchmark,
            metrics=list(metrics),
            verbose=verbose
        ))
        
        # Affichage des résultats
        _display_performance_analysis(performance_data)
        
        # Sauvegarde si demandée
        if save_report:
            _save_performance_report(performance_data, save_report)
            console.print(f"✅ Rapport sauvegardé: {save_report}", style="green")
    
    except Exception as e:
        console.print(f"❌ Erreur lors de l'analyse: {e}", style="red")
        if verbose:
            console.print_exception()
        ctx.exit(1)


# === Fonctions d'implémentation ===

async def _create_portfolio(name: str, description: str, initial_balance: float,
                          currency: str, risk_profile: str, benchmark: str,
                          verbose: bool) -> Dict[str, Any]:
    """Crée un nouveau portefeuille."""
    
    with spinner_manager.spinner_context("📊 Création du portefeuille..."):
        await asyncio.sleep(1)  # Simulation
    
    # Simulation de la création (en réalité, appel au PortfolioManager)
    portfolio_data = {
        "id": f"portfolio_{hash(name) % 10000}",
        "name": name,
        "description": description or f"Portefeuille d'investissement {name}",
        "initial_balance": initial_balance,
        "current_balance": initial_balance,
        "currency": currency,
        "risk_profile": risk_profile,
        "benchmark": benchmark,
        "created_at": datetime.now(),
        "positions": [],
        "total_value": initial_balance,
        "cash": initial_balance,
        "performance": {
            "total_return": 0.0,
            "total_return_percent": 0.0,
            "daily_return": 0.0,
            "volatility": 0.0
        }
    }
    
    return portfolio_data


async def _add_position_to_portfolio(portfolio_name: str, symbol: str,
                                    quantity: Optional[float], amount: Optional[float],
                                    price: Optional[float], order_type: str,
                                    validate: bool, verbose: bool) -> Dict[str, Any]:
    """Ajoute une position à un portefeuille."""
    
    with progress_manager.progress_context() as progress:
        # Étape 1: Récupération du prix actuel
        price_task = progress.add_task("💰 Récupération du prix actuel", total=100)
        for i in range(100):
            await asyncio.sleep(0.01)
            progress.update(price_task, advance=1)
        
        current_price = price or float(f"{150 + (hash(symbol) % 100):.2f}")  # Prix simulé
        
        # Étape 2: Calcul de la quantité/montant
        calc_task = progress.add_task("🧮 Calcul de l'ordre", total=100)
        for i in range(100):
            await asyncio.sleep(0.005)
            progress.update(calc_task, advance=1)
        
        if amount and not quantity:
            calculated_quantity = amount / current_price
        else:
            calculated_quantity = quantity
            amount = quantity * current_price
        
        # Étape 3: Validation (si demandée)
        if validate:
            validation_task = progress.add_task("✅ Validation de l'ordre", total=100)
            for i in range(100):
                await asyncio.sleep(0.01)
                progress.update(validation_task, advance=1)
        
        # Étape 4: Exécution de l'ordre
        execution_task = progress.add_task("🚀 Exécution de l'ordre", total=100)
        for i in range(100):
            await asyncio.sleep(0.01)
            progress.update(execution_task, advance=1)
    
    return {
        "portfolio_name": portfolio_name,
        "symbol": symbol,
        "quantity": calculated_quantity,
        "amount": amount,
        "price": current_price,
        "order_type": order_type,
        "execution_time": datetime.now(),
        "status": "EXECUTED",
        "fees": amount * 0.001,  # 0.1% de frais simulés
        "order_id": f"ORD_{hash(f'{portfolio_name}{symbol}') % 100000}"
    }


async def _get_portfolio_data(portfolio_name: str, period: str,
                            include_benchmark: bool, detailed: bool,
                            verbose: bool) -> Dict[str, Any]:
    """Récupère les données complètes d'un portefeuille."""
    
    with spinner_manager.spinner_context("📊 Chargement du portefeuille..."):
        await asyncio.sleep(1.5)
    
    # Simulation de données de portefeuille
    positions = [
        {
            "symbol": "AAPL",
            "quantity": 25,
            "avg_price": 150.00,
            "current_price": 157.45,
            "market_value": 3936.25,
            "cost_basis": 3750.00,
            "unrealized_pnl": 186.25,
            "unrealized_pnl_percent": 4.97,
            "weight": 0.35,
            "sector": "Technology"
        },
        {
            "symbol": "MSFT",
            "quantity": 15,
            "avg_price": 300.00,
            "current_price": 315.80,
            "market_value": 4737.00,
            "cost_basis": 4500.00,
            "unrealized_pnl": 237.00,
            "unrealized_pnl_percent": 5.27,
            "weight": 0.42,
            "sector": "Technology"
        },
        {
            "symbol": "JNJ",
            "quantity": 30,
            "avg_price": 160.00,
            "current_price": 165.20,
            "market_value": 4956.00,
            "cost_basis": 4800.00,
            "unrealized_pnl": 156.00,
            "unrealized_pnl_percent": 3.25,
            "weight": 0.23,
            "sector": "Healthcare"
        }
    ]
    
    total_value = sum(p["market_value"] for p in positions)
    total_cost = sum(p["cost_basis"] for p in positions)
    
    return {
        "name": portfolio_name,
        "currency": "USD",
        "risk_profile": "moderate",
        "benchmark": "SPY",
        "created_at": datetime.now() - timedelta(days=180),
        "last_updated": datetime.now(),
        "positions": positions,
        "summary": {
            "total_value": total_value,
            "total_cost": total_cost,
            "cash": 1500.00,
            "total_pnl": total_value - total_cost,
            "total_pnl_percent": ((total_value - total_cost) / total_cost) * 100,
            "position_count": len(positions),
            "diversification_score": 0.75
        },
        "performance": {
            "1d": {"return": 0.012, "benchmark": 0.008},
            "1w": {"return": 0.034, "benchmark": 0.021},
            "1m": {"return": 0.087, "benchmark": 0.054},
            "3m": {"return": 0.156, "benchmark": 0.123},
            "ytd": {"return": 0.234, "benchmark": 0.187},
            "1y": {"return": 0.187, "benchmark": 0.156}
        },
        "risk_metrics": {
            "volatility": 0.18,
            "sharpe_ratio": 1.23,
            "max_drawdown": -0.08,
            "beta": 1.05,
            "var_95": -0.025
        }
    }


async def _list_portfolios(verbose: bool) -> List[Dict[str, Any]]:
    """Liste tous les portefeuilles."""
    
    with spinner_manager.spinner_context("📋 Récupération des portefeuilles..."):
        await asyncio.sleep(0.5)
    
    # Simulation de portefeuilles existants
    return [
        {
            "name": "Mon Portfolio Tech",
            "value": 45230.50,
            "currency": "USD",
            "return_1d": 1.23,
            "return_ytd": 18.45,
            "position_count": 8,
            "created_at": datetime.now() - timedelta(days=120)
        },
        {
            "name": "Retraite",
            "value": 123450.75,
            "currency": "USD", 
            "return_1d": 0.45,
            "return_ytd": 8.92,
            "position_count": 15,
            "created_at": datetime.now() - timedelta(days=365)
        },
        {
            "name": "Trading Actif",
            "value": 23780.20,
            "currency": "EUR",
            "return_1d": -0.78,
            "return_ytd": 25.60,
            "position_count": 5,
            "created_at": datetime.now() - timedelta(days=45)
        }
    ]


async def _optimize_portfolio(portfolio_name: str, method: str,
                            target_return: Optional[float], max_weight: float,
                            min_weight: float, period: str,
                            verbose: bool) -> Dict[str, Any]:
    """Optimise l'allocation d'un portefeuille."""
    
    with progress_manager.progress_context() as progress:
        # Étape 1: Récupération des données historiques
        data_task = progress.add_task("📊 Récupération données historiques", total=100)
        for i in range(100):
            await asyncio.sleep(0.02)
            progress.update(data_task, advance=1)
        
        # Étape 2: Calcul des rendements et covariances
        calc_task = progress.add_task("🧮 Calcul matrices de covariance", total=100)
        for i in range(100):
            await asyncio.sleep(0.015)
            progress.update(calc_task, advance=1)
        
        # Étape 3: Optimisation
        optim_task = progress.add_task(f"⚙️  Optimisation {method}", total=100)
        for i in range(100):
            await asyncio.sleep(0.025)
            progress.update(optim_task, advance=1)
    
    # Simulation de résultats d'optimisation
    current_weights = {"AAPL": 0.35, "MSFT": 0.42, "JNJ": 0.23}
    optimized_weights = {"AAPL": 0.28, "MSFT": 0.45, "JNJ": 0.27}
    
    return {
        "method": method,
        "period": period,
        "target_return": target_return,
        "constraints": {
            "max_weight": max_weight,
            "min_weight": min_weight
        },
        "current_allocation": current_weights,
        "optimized_allocation": optimized_weights,
        "expected_metrics": {
            "expected_return": 0.125,
            "volatility": 0.165,
            "sharpe_ratio": 1.45
        },
        "improvement": {
            "return_improvement": 0.018,
            "risk_reduction": -0.015,
            "sharpe_improvement": 0.22
        },
        "rebalancing_trades": [
            {"symbol": "AAPL", "action": "SELL", "amount": 1250.00},
            {"symbol": "MSFT", "action": "BUY", "amount": 850.00},
            {"symbol": "JNJ", "action": "BUY", "amount": 400.00}
        ]
    }


async def _analyze_portfolio_performance(portfolio_name: str, period: str,
                                       include_benchmark: bool, metrics: List[str],
                                       verbose: bool) -> Dict[str, Any]:
    """Analyse les performances d'un portefeuille."""
    
    with progress_manager.progress_context() as progress:
        # Récupération des données
        data_task = progress.add_task("📊 Récupération historique", total=100)
        for i in range(100):
            await asyncio.sleep(0.01)
            progress.update(data_task, advance=1)
        
        # Calcul des métriques
        for metric in metrics:
            metric_task = progress.add_task(f"📈 Calcul {metric}", total=100)
            for i in range(100):
                await asyncio.sleep(0.005)
                progress.update(metric_task, advance=1)
    
    # Simulation de données de performance
    return {
        "portfolio_name": portfolio_name,
        "period": period,
        "analysis_date": datetime.now(),
        "metrics": {
            "total_return": 0.187,
            "annualized_return": 0.156,
            "volatility": 0.18,
            "sharpe_ratio": 1.23,
            "sortino_ratio": 1.67,
            "calmar_ratio": 1.95,
            "max_drawdown": -0.082,
            "var_95": -0.025,
            "cvar_95": -0.038,
            "beta": 1.05,
            "alpha": 0.023,
            "tracking_error": 0.045
        },
        "benchmark_comparison": {
            "benchmark": "SPY",
            "portfolio_return": 0.187,
            "benchmark_return": 0.156,
            "excess_return": 0.031,
            "information_ratio": 0.69
        } if include_benchmark else None,
        "monthly_returns": [
            {"month": "2024-01", "return": 0.045},
            {"month": "2024-02", "return": -0.012},
            {"month": "2024-03", "return": 0.028},
            {"month": "2024-04", "return": 0.018},
            {"month": "2024-05", "return": 0.035},
            {"month": "2024-06", "return": -0.008}
        ]
    }


# === Fonctions d'affichage ===

def _display_portfolio_creation_result(portfolio_data: Dict[str, Any]) -> None:
    """Affiche le résultat de création de portefeuille."""
    console.print(Panel.fit(
        f"✅ [green]Portefeuille créé avec succès![/green]\n\n"
        f"📊 [bold]{portfolio_data['name']}[/bold]\n"
        f"💰 Solde initial: {portfolio_data['initial_balance']:,.2f} {portfolio_data['currency']}\n"
        f"⚖️  Profil de risque: {portfolio_data['risk_profile'].title()}\n"
        f"📈 Benchmark: {portfolio_data['benchmark']}\n"
        f"🕒 Créé le: {portfolio_data['created_at'].strftime('%d/%m/%Y à %H:%M')}",
        title="💼 Nouveau Portefeuille",
        border_style="green"
    ))


def _display_add_position_result(add_result: Dict[str, Any]) -> None:
    """Affiche le résultat d'ajout de position."""
    fees_percent = (add_result['fees'] / add_result['amount']) * 100
    
    console.print(Panel.fit(
        f"✅ [green]Position ajoutée avec succès![/green]\n\n"
        f"📊 Portefeuille: [bold]{add_result['portfolio_name']}[/bold]\n"
        f"🎯 Symbole: [cyan]{add_result['symbol']}[/cyan]\n"
        f"📈 Quantité: {add_result['quantity']:.2f}\n"
        f"💰 Prix: ${add_result['price']:.2f}\n"
        f"💵 Montant total: ${add_result['amount']:,.2f}\n"
        f"💸 Frais: ${add_result['fees']:.2f} ({fees_percent:.2f}%)\n"
        f"🆔 Ordre: {add_result['order_id']}\n"
        f"🕒 Exécuté le: {add_result['execution_time'].strftime('%d/%m/%Y à %H:%M:%S')}",
        title="💰 Ordre Exécuté",
        border_style="green"
    ))


def _display_portfolio_table(portfolio_data: Dict[str, Any], detailed: bool, group_by: str) -> None:
    """Affiche le portefeuille sous forme de tableau."""
    formatter = PortfolioFormatter()
    
    # Résumé du portefeuille
    summary_panel = formatter.format_portfolio_summary(portfolio_data)
    console.print(summary_panel)
    console.print()
    
    # Positions
    positions_table = formatter.format_positions_table({
        "positions": portfolio_data["positions"],
        "detailed": detailed,
        "group_by": group_by
    })
    console.print(positions_table)
    
    if detailed:
        console.print()
        # Métriques de risque
        risk_panel = formatter.format_risk_metrics(portfolio_data.get("risk_metrics", {}))
        console.print(risk_panel)


def _display_portfolios_table(portfolios: List[Dict[str, Any]]) -> None:
    """Affiche la liste des portefeuilles."""
    table = Table(title="📊 Mes Portefeuilles", show_header=True)
    
    table.add_column("Nom", style="cyan bold", no_wrap=True)
    table.add_column("Valeur", justify="right")
    table.add_column("Perf. 1J", justify="right")
    table.add_column("Perf. YTD", justify="right")
    table.add_column("Positions", justify="center")
    table.add_column("Créé le", style="dim")
    
    for portfolio in portfolios:
        # Formatage des valeurs
        value = f"{portfolio['value']:,.2f} {portfolio['currency']}"
        perf_1d = f"{portfolio['return_1d']:+.2f}%"
        perf_ytd = f"{portfolio['return_ytd']:+.2f}%"
        positions = f"{portfolio['position_count']}"
        created = portfolio['created_at'].strftime('%d/%m/%Y')
        
        # Couleurs selon la performance
        perf_1d_style = "green" if portfolio['return_1d'] > 0 else "red" if portfolio['return_1d'] < 0 else "white"
        perf_ytd_style = "green" if portfolio['return_ytd'] > 0 else "red" if portfolio['return_ytd'] < 0 else "white"
        
        table.add_row(
            portfolio['name'],
            value,
            f"[{perf_1d_style}]{perf_1d}[/{perf_1d_style}]",
            f"[{perf_ytd_style}]{perf_ytd}[/{perf_ytd_style}]",
            positions,
            created
        )
    
    console.print(table)


def _display_optimization_result(optimization_result: Dict[str, Any]) -> None:
    """Affiche les résultats d'optimisation."""
    formatter = PortfolioFormatter()
    
    # Résultats d'optimisation
    optimization_panel = formatter.format_optimization_result(optimization_result)
    console.print(optimization_panel)


def _display_performance_analysis(performance_data: Dict[str, Any]) -> None:
    """Affiche l'analyse de performance."""
    formatter = PortfolioFormatter()
    
    # Métriques de performance
    performance_panel = formatter.format_performance_analysis(performance_data)
    console.print(performance_panel)


def _display_portfolio_chart(portfolio_data: Dict[str, Any]) -> None:
    """Affiche le graphique du portefeuille."""
    console.print("📊 [yellow]Mode graphique non encore implémenté[/yellow]")
    console.print("💡 Utilisez --format table pour l'instant")


def _save_performance_report(performance_data: Dict[str, Any], filepath: str) -> None:
    """Sauvegarde le rapport de performance."""
    # Simulation de sauvegarde
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'w') as f:
        f.write("Rapport de Performance FinAgent\n")
        f.write("==============================\n\n")
        f.write(f"Portefeuille: {performance_data['portfolio_name']}\n")
        f.write(f"Période: {performance_data['period']}\n")
        f.write(f"Date d'analyse: {performance_data['analysis_date']}\n\n")
        
        f.write("Métriques de Performance:\n")
        for metric, value in performance_data['metrics'].items():
            if isinstance(value, float):
                f.write(f"  {metric}: {value:.2%}\n")
            else:
                f.write(f"  {metric}: {value}\n")


async def _apply_optimization(portfolio_name: str, optimization_result: Dict[str, Any]) -> None:
    """Applique les recommandations d'optimisation."""
    with spinner_manager.spinner_context("🔄 Application de l'optimisation..."):
        await asyncio.sleep(2)  # Simulation