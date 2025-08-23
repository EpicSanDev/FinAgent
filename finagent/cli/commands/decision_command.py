"""
Commande de gestion des décisions de trading pour la CLI FinAgent.

Cette commande permet de créer, évaluer et suivre les décisions
de trading avec reasoning détaillé et historique.
"""

import asyncio
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timedelta
from enum import Enum

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from rich.prompt import Prompt, Confirm

from ..formatters import DecisionFormatter, AnalysisFormatter
from ..utils import (
    SYMBOL, PERCENTAGE, AMOUNT,
    with_progress, ValidationError,
    progress_manager, spinner_manager,
    cache_manager
)

# Imports des services (à adapter selon l'architecture finale)
# from finagent.business.decision.decision_engine import DecisionEngine
# from finagent.business.decision.reasoning_engine import ReasoningEngine
# from finagent.data.decision.decision_repository import DecisionRepository

console = Console()


class DecisionType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    REDUCE = "REDUCE"
    INCREASE = "INCREASE"


class ConfidenceLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"


@click.group()
def decision():
    """Commandes de gestion des décisions de trading."""
    pass


@decision.command()
@click.argument('symbol', type=SYMBOL, required=True)
@click.option(
    '--amount',
    type=AMOUNT,
    help='Montant à investir (requis pour BUY/INCREASE)'
)
@click.option(
    '--quantity',
    type=float,
    help='Quantité d\'actions (alternative au montant)'
)
@click.option(
    '--decision-type', '-t',
    type=click.Choice([t.value for t in DecisionType]),
    help='Type de décision (détecté automatiquement si non spécifié)'
)
@click.option(
    '--timeframe',
    type=click.Choice(['1d', '1w', '1m', '3m', '6m', '1y']),
    default='1m',
    help='Horizon temporel de la décision'
)
@click.option(
    '--risk-tolerance',
    type=click.Choice(['low', 'medium', 'high']),
    default='medium',
    help='Tolérance au risque'
)
@click.option(
    '--include-sentiment',
    is_flag=True,
    help='Inclure l\'analyse de sentiment'
)
@click.option(
    '--include-fundamental',
    is_flag=True,
    help='Inclure l\'analyse fondamentale'
)
@click.option(
    '--factors',
    multiple=True,
    type=click.Choice(['technical', 'fundamental', 'sentiment', 'macro', 'news']),
    default=['technical', 'sentiment'],
    help='Facteurs à considérer dans la décision'
)
@click.option(
    '--save-decision',
    is_flag=True,
    help='Sauvegarder la décision dans l\'historique'
)
@click.option(
    '--auto-execute',
    is_flag=True,
    help='Exécuter automatiquement si confiance élevée'
)
@click.pass_context
def analyze(ctx, symbol: str, amount: Optional[float], quantity: Optional[float],
           decision_type: Optional[str], timeframe: str, risk_tolerance: str,
           include_sentiment: bool, include_fundamental: bool, factors: tuple,
           save_decision: bool, auto_execute: bool):
    """
    Analyse un symbole et génère une recommandation de décision.
    
    SYMBOL: Symbole de l'action à analyser
    
    Exemples:
    \b
        finagent decision analyze AAPL --amount 5000
        finagent decision analyze MSFT --quantity 20 --timeframe 3m
        finagent decision analyze TSLA --include-fundamental --factors technical fundamental
    """
    try:
        verbose = ctx.obj.get('verbose', False) if ctx.obj else False
        
        if verbose:
            console.print(f"🤖 Analyse de décision pour {symbol}...", style="blue")
        
        # Validation des paramètres
        if decision_type in [DecisionType.BUY.value, DecisionType.INCREASE.value]:
            if not amount and not quantity:
                raise ValidationError("Montant ou quantité requis pour les décisions d'achat")
        
        # Génération de la décision
        decision_result = asyncio.run(_generate_trading_decision(
            symbol=symbol,
            amount=amount,
            quantity=quantity,
            decision_type=decision_type,
            timeframe=timeframe,
            risk_tolerance=risk_tolerance,
            include_sentiment=include_sentiment,
            include_fundamental=include_fundamental,
            factors=list(factors),
            verbose=verbose
        ))
        
        # Affichage de la décision
        _display_trading_decision(decision_result)
        
        # Sauvegarde si demandée
        if save_decision:
            asyncio.run(_save_decision_to_history(decision_result))
            console.print("✅ Décision sauvegardée dans l'historique", style="green")
        
        # Exécution automatique si conditions remplies
        if auto_execute and decision_result['confidence_level'] in ['HIGH', 'VERY_HIGH']:
            if Confirm.ask(f"Exécuter automatiquement la décision {decision_result['recommendation']} ?"):
                asyncio.run(_execute_trading_decision(decision_result))
                console.print("🚀 Décision exécutée avec succès", style="green")
    
    except ValidationError as e:
        console.print(f"❌ Erreur de validation: {e.message}", style="red")
        ctx.exit(1)
    
    except Exception as e:
        console.print(f"❌ Erreur lors de l'analyse: {e}", style="red")
        if verbose:
            console.print_exception()
        ctx.exit(1)


@decision.command()
@click.option(
    '--symbol', '-s',
    type=SYMBOL,
    help='Filtrer par symbole'
)
@click.option(
    '--decision-type', '-t',
    type=click.Choice([t.value for t in DecisionType]),
    help='Filtrer par type de décision'
)
@click.option(
    '--confidence', '-c',
    type=click.Choice([c.value for c in ConfidenceLevel]),
    help='Filtrer par niveau de confiance'
)
@click.option(
    '--days', '-d',
    type=int,
    default=30,
    help='Nombre de jours d\'historique'
)
@click.option(
    '--status',
    type=click.Choice(['pending', 'executed', 'cancelled', 'expired', 'all']),
    default='all',
    help='Filtrer par statut'
)
@click.option(
    '--format',
    type=click.Choice(['table', 'detailed', 'summary']),
    default='table',
    help='Format d\'affichage'
)
@click.option(
    '--export',
    type=click.Path(),
    help='Exporter l\'historique vers un fichier'
)
@click.pass_context
def history(ctx, symbol: Optional[str], decision_type: Optional[str],
           confidence: Optional[str], days: int, status: str, format: str,
           export: Optional[str]):
    """
    Affiche l'historique des décisions de trading.
    
    Exemples:
    \b
        finagent decision history
        finagent decision history --symbol AAPL --days 7
        finagent decision history --confidence HIGH --format detailed
        finagent decision history --export decisions.csv
    """
    try:
        verbose = ctx.obj.get('verbose', False) if ctx.obj else False
        
        if verbose:
            console.print("📊 Récupération de l'historique des décisions...", style="blue")
        
        # Récupération de l'historique
        history_data = asyncio.run(_get_decision_history(
            symbol=symbol,
            decision_type=decision_type,
            confidence=confidence,
            days=days,
            status=status,
            verbose=verbose
        ))
        
        if not history_data['decisions']:
            console.print("📭 Aucune décision trouvée pour les critères spécifiés", style="yellow")
            return
        
        # Affichage selon le format
        if format == 'summary':
            _display_decision_summary(history_data)
        elif format == 'detailed':
            _display_decision_detailed(history_data)
        else:
            _display_decision_table(history_data)
        
        # Export si demandé
        if export:
            _export_decision_history(history_data, export)
            console.print(f"✅ Historique exporté: {export}", style="green")
    
    except Exception as e:
        console.print(f"❌ Erreur lors de la récupération: {e}", style="red")
        if verbose:
            console.print_exception()
        ctx.exit(1)


@decision.command()
@click.argument('decision_id', required=True)
@click.option(
    '--reason',
    help='Raison de l\'annulation'
)
@click.option(
    '--force',
    is_flag=True,
    help='Forcer l\'annulation même si déjà exécutée'
)
@click.pass_context
def cancel(ctx, decision_id: str, reason: Optional[str], force: bool):
    """
    Annule une décision en attente.
    
    DECISION_ID: Identifiant de la décision à annuler
    
    Exemples:
    \b
        finagent decision cancel DEC_12345
        finagent decision cancel DEC_12345 --reason "Conditions de marché changées"
        finagent decision cancel DEC_12345 --force
    """
    try:
        verbose = ctx.obj.get('verbose', False) if ctx.obj else False
        
        if verbose:
            console.print(f"❌ Annulation de la décision {decision_id}...", style="blue")
        
        # Annulation de la décision
        cancel_result = asyncio.run(_cancel_trading_decision(
            decision_id=decision_id,
            reason=reason,
            force=force,
            verbose=verbose
        ))
        
        # Affichage du résultat
        _display_cancellation_result(cancel_result)
    
    except Exception as e:
        console.print(f"❌ Erreur lors de l'annulation: {e}", style="red")
        if verbose:
            console.print_exception()
        ctx.exit(1)


@decision.command()
@click.option(
    '--days', '-d',
    type=int,
    default=30,
    help='Période d\'analyse en jours'
)
@click.option(
    '--symbol', '-s',
    type=SYMBOL,
    help='Analyser un symbole spécifique'
)
@click.option(
    '--benchmark',
    type=SYMBOL,
    default='SPY',
    help='Benchmark pour la comparaison'
)
@click.option(
    '--include-costs',
    is_flag=True,
    help='Inclure les coûts de transaction'
)
@click.option(
    '--group-by',
    type=click.Choice(['symbol', 'decision_type', 'confidence', 'month']),
    default='symbol',
    help='Grouper les performances par critère'
)
@click.pass_context
def performance(ctx, days: int, symbol: Optional[str], benchmark: str,
               include_costs: bool, group_by: str):
    """
    Analyse les performances des décisions passées.
    
    Exemples:
    \b
        finagent decision performance
        finagent decision performance --days 90 --symbol AAPL
        finagent decision performance --include-costs --benchmark QQQ
    """
    try:
        verbose = ctx.obj.get('verbose', False) if ctx.obj else False
        
        if verbose:
            console.print("📊 Analyse des performances des décisions...", style="blue")
        
        # Analyse des performances
        performance_data = asyncio.run(_analyze_decision_performance(
            days=days,
            symbol=symbol,
            benchmark=benchmark,
            include_costs=include_costs,
            group_by=group_by,
            verbose=verbose
        ))
        
        # Affichage des résultats
        _display_performance_analysis(performance_data)
    
    except Exception as e:
        console.print(f"❌ Erreur lors de l'analyse: {e}", style="red")
        if verbose:
            console.print_exception()
        ctx.exit(1)


@decision.command()
@click.argument('symbol', type=SYMBOL, required=True)
@click.option(
    '--scenarios',
    multiple=True,
    type=click.Choice(['bull', 'bear', 'sideways', 'volatile', 'recession']),
    default=['bull', 'bear', 'sideways'],
    help='Scénarios de marché à simuler'
)
@click.option(
    '--timeframe',
    type=click.Choice(['1w', '1m', '3m', '6m', '1y']),
    default='3m',
    help='Horizon de simulation'
)
@click.option(
    '--monte-carlo-runs',
    type=int,
    default=1000,
    help='Nombre de simulations Monte Carlo'
)
@click.option(
    '--confidence-intervals',
    multiple=True,
    type=click.Choice(['90', '95', '99']),
    default=['95'],
    help='Intervalles de confiance à calculer'
)
@click.pass_context
def simulate(ctx, symbol: str, scenarios: tuple, timeframe: str,
            monte_carlo_runs: int, confidence_intervals: tuple):
    """
    Simule l'impact de différents scénarios sur une décision.
    
    SYMBOL: Symbole à simuler
    
    Exemples:
    \b
        finagent decision simulate AAPL
        finagent decision simulate TSLA --scenarios bull bear volatile
        finagent decision simulate MSFT --timeframe 6m --monte-carlo-runs 5000
    """
    try:
        verbose = ctx.obj.get('verbose', False) if ctx.obj else False
        
        if verbose:
            console.print(f"🎲 Simulation de scénarios pour {symbol}...", style="blue")
        
        # Simulation des scénarios
        simulation_result = asyncio.run(_simulate_decision_scenarios(
            symbol=symbol,
            scenarios=list(scenarios),
            timeframe=timeframe,
            monte_carlo_runs=monte_carlo_runs,
            confidence_intervals=[int(ci) for ci in confidence_intervals],
            verbose=verbose
        ))
        
        # Affichage des résultats
        _display_simulation_results(simulation_result)
    
    except Exception as e:
        console.print(f"❌ Erreur lors de la simulation: {e}", style="red")
        if verbose:
            console.print_exception()
        ctx.exit(1)


# === Fonctions d'implémentation ===

async def _generate_trading_decision(symbol: str, amount: Optional[float],
                                   quantity: Optional[float], decision_type: Optional[str],
                                   timeframe: str, risk_tolerance: str,
                                   include_sentiment: bool, include_fundamental: bool,
                                   factors: List[str], verbose: bool) -> Dict[str, Any]:
    """Génère une décision de trading basée sur l'analyse."""
    
    with progress_manager.progress_context() as progress:
        # Étape 1: Récupération des données de marché
        market_task = progress.add_task("📊 Récupération données marché", total=100)
        for i in range(100):
            await asyncio.sleep(0.01)
            progress.update(market_task, advance=1)
        
        # Étape 2: Analyse technique
        if 'technical' in factors:
            tech_task = progress.add_task("📈 Analyse technique", total=100)
            for i in range(100):
                await asyncio.sleep(0.015)
                progress.update(tech_task, advance=1)
        
        # Étape 3: Analyse fondamentale
        if 'fundamental' in factors or include_fundamental:
            fund_task = progress.add_task("📋 Analyse fondamentale", total=100)
            for i in range(100):
                await asyncio.sleep(0.02)
                progress.update(fund_task, advance=1)
        
        # Étape 4: Analyse de sentiment
        if 'sentiment' in factors or include_sentiment:
            sent_task = progress.add_task("😊 Analyse sentiment", total=100)
            for i in range(100):
                await asyncio.sleep(0.012)
                progress.update(sent_task, advance=1)
        
        # Étape 5: Génération de la recommandation
        decision_task = progress.add_task("🤖 Génération décision", total=100)
        for i in range(100):
            await asyncio.sleep(0.02)
            progress.update(decision_task, advance=1)
    
    # Simulation de décision basée sur des facteurs
    current_price = 157.45  # Prix simulé
    
    # Détermination automatique du type de décision si non spécifié
    if not decision_type:
        # Logique simplifiée pour la démo
        decision_type = DecisionType.BUY.value if hash(symbol) % 3 == 0 else DecisionType.HOLD.value
    
    # Calcul de la quantité si montant spécifié
    if amount and not quantity:
        quantity = amount / current_price
    elif quantity and not amount:
        amount = quantity * current_price
    
    return {
        "id": f"DEC_{hash(f'{symbol}{datetime.now()}') % 100000}",
        "symbol": symbol,
        "recommendation": decision_type,
        "confidence_level": ConfidenceLevel.HIGH.value,
        "confidence_score": 0.87,
        "current_price": current_price,
        "target_price": current_price * 1.12 if decision_type == DecisionType.BUY.value else None,
        "stop_loss": current_price * 0.95 if decision_type == DecisionType.BUY.value else None,
        "quantity": quantity,
        "amount": amount,
        "timeframe": timeframe,
        "risk_tolerance": risk_tolerance,
        "factors_analyzed": factors,
        "timestamp": datetime.now(),
        "reasoning": {
            "primary_factors": [
                {
                    "factor": "Technical Analysis",
                    "weight": 0.4,
                    "score": 0.85,
                    "rationale": "RSI indique une zone de survente, MACD montre une divergence haussière"
                },
                {
                    "factor": "Market Sentiment",
                    "weight": 0.3,
                    "score": 0.75,
                    "rationale": "Sentiment général positif, volume d'achat en hausse"
                },
                {
                    "factor": "Risk Assessment",
                    "weight": 0.3,
                    "score": 0.90,
                    "rationale": "Volatilité dans la normale, corrélation faible avec le marché"
                }
            ],
            "key_points": [
                f"Prix actuel de {current_price}$ proche du support technique",
                "Volume supérieur à la moyenne sur 5 jours",
                "Ratio P/E attractif par rapport au secteur",
                f"Objectif à 3 mois: {current_price * 1.12:.2f}$"
            ],
            "risks": [
                "Volatilité élevée du marché tech",
                "Résultats trimestriels dans 2 semaines",
                "Incertitude macro-économique"
            ],
            "catalysts": [
                "Lancement de nouveau produit prévu",
                "Guidance positive du management",
                "Amélioration des marges opérationnelles"
            ]
        },
        "execution_plan": {
            "entry_strategy": "Ordre limité à prix actuel",
            "position_sizing": f"{(quantity or 0):.2f} actions",
            "risk_management": "Stop-loss à 5%, take-profit à 12%",
            "monitoring": "Réévaluation hebdomadaire"
        },
        "status": "pending",
        "expires_at": datetime.now() + timedelta(days=7)
    }


async def _get_decision_history(symbol: Optional[str], decision_type: Optional[str],
                              confidence: Optional[str], days: int, status: str,
                              verbose: bool) -> Dict[str, Any]:
    """Récupère l'historique des décisions."""
    
    with spinner_manager.spinner_context("📊 Chargement de l'historique..."):
        await asyncio.sleep(1.2)
    
    # Simulation d'historique de décisions
    decisions = [
        {
            "id": "DEC_12345",
            "symbol": "AAPL",
            "recommendation": "BUY",
            "confidence_level": "HIGH",
            "confidence_score": 0.89,
            "amount": 5000.00,
            "quantity": 31.75,
            "entry_price": 157.45,
            "current_price": 165.20,
            "created_at": datetime.now() - timedelta(days=5),
            "status": "executed",
            "performance": 0.049,  # +4.9%
            "reasoning_summary": "Signal technique fort + sentiment positif"
        },
        {
            "id": "DEC_12346",
            "symbol": "MSFT",
            "recommendation": "HOLD",
            "confidence_level": "MEDIUM",
            "confidence_score": 0.65,
            "amount": None,
            "quantity": 50,
            "entry_price": 315.80,
            "current_price": 318.45,
            "created_at": datetime.now() - timedelta(days=12),
            "status": "executed",
            "performance": 0.008,  # +0.8%
            "reasoning_summary": "Consolidation attendue, pas de catalyseur immédiat"
        },
        {
            "id": "DEC_12347",
            "symbol": "TSLA",
            "recommendation": "SELL",
            "confidence_level": "HIGH",
            "confidence_score": 0.82,
            "amount": 8500.00,
            "quantity": 42.5,
            "entry_price": 200.00,
            "current_price": 195.30,
            "created_at": datetime.now() - timedelta(days=8),
            "status": "executed",
            "performance": -0.024,  # -2.4%
            "reasoning_summary": "Surévaluation technique, momentum négatif"
        },
        {
            "id": "DEC_12348",
            "symbol": "GOOGL",
            "recommendation": "BUY",
            "confidence_level": "VERY_HIGH",
            "confidence_score": 0.93,
            "amount": 10000.00,
            "quantity": 75.2,
            "entry_price": 133.00,
            "current_price": 133.00,
            "created_at": datetime.now() - timedelta(hours=2),
            "status": "pending",
            "performance": None,
            "reasoning_summary": "Opportunité d'achat exceptionnelle après correction"
        }
    ]
    
    # Application des filtres
    filtered_decisions = decisions
    
    if symbol:
        filtered_decisions = [d for d in filtered_decisions if d['symbol'] == symbol]
    
    if decision_type:
        filtered_decisions = [d for d in filtered_decisions if d['recommendation'] == decision_type]
    
    if confidence:
        filtered_decisions = [d for d in filtered_decisions if d['confidence_level'] == confidence]
    
    if status != 'all':
        filtered_decisions = [d for d in filtered_decisions if d['status'] == status]
    
    # Filtrage par date
    cutoff_date = datetime.now() - timedelta(days=days)
    filtered_decisions = [d for d in filtered_decisions if d['created_at'] >= cutoff_date]
    
    return {
        "decisions": filtered_decisions,
        "total_count": len(filtered_decisions),
        "filters": {
            "symbol": symbol,
            "decision_type": decision_type,
            "confidence": confidence,
            "days": days,
            "status": status
        },
        "summary": {
            "executed": len([d for d in filtered_decisions if d['status'] == 'executed']),
            "pending": len([d for d in filtered_decisions if d['status'] == 'pending']),
            "cancelled": len([d for d in filtered_decisions if d['status'] == 'cancelled']),
            "avg_performance": sum(d['performance'] for d in filtered_decisions if d['performance']) / 
                            len([d for d in filtered_decisions if d['performance']]) if 
                            any(d['performance'] for d in filtered_decisions) else 0
        }
    }


async def _cancel_trading_decision(decision_id: str, reason: Optional[str],
                                 force: bool, verbose: bool) -> Dict[str, Any]:
    """Annule une décision de trading."""
    
    with spinner_manager.spinner_context("❌ Annulation en cours..."):
        await asyncio.sleep(1)
    
    return {
        "decision_id": decision_id,
        "status": "cancelled",
        "reason": reason or "Annulation manuelle",
        "cancelled_at": datetime.now(),
        "was_executed": False,
        "cancellation_successful": True
    }


async def _analyze_decision_performance(days: int, symbol: Optional[str],
                                      benchmark: str, include_costs: bool,
                                      group_by: str, verbose: bool) -> Dict[str, Any]:
    """Analyse les performances des décisions."""
    
    with progress_manager.progress_context() as progress:
        # Récupération des données
        data_task = progress.add_task("📊 Récupération des décisions", total=100)
        for i in range(100):
            await asyncio.sleep(0.01)
            progress.update(data_task, advance=1)
        
        # Calcul des performances
        perf_task = progress.add_task("📈 Calcul des performances", total=100)
        for i in range(100):
            await asyncio.sleep(0.015)
            progress.update(perf_task, advance=1)
        
        # Comparaison avec benchmark
        bench_task = progress.add_task(f"⚖️  Comparaison avec {benchmark}", total=100)
        for i in range(100):
            await asyncio.sleep(0.01)
            progress.update(bench_task, advance=1)
    
    # Simulation de données de performance
    return {
        "period_days": days,
        "symbol_filter": symbol,
        "benchmark": benchmark,
        "include_costs": include_costs,
        "group_by": group_by,
        "overall_performance": {
            "total_decisions": 47,
            "executed_decisions": 42,
            "avg_return": 0.068,
            "win_rate": 0.74,
            "total_return": 0.187,
            "benchmark_return": 0.134,
            "excess_return": 0.053,
            "sharpe_ratio": 1.23,
            "max_drawdown": -0.056
        },
        "by_decision_type": {
            "BUY": {"count": 18, "avg_return": 0.089, "win_rate": 0.78},
            "SELL": {"count": 12, "avg_return": 0.045, "win_rate": 0.67},
            "HOLD": {"count": 12, "avg_return": 0.023, "win_rate": 0.75}
        },
        "by_confidence_level": {
            "VERY_HIGH": {"count": 8, "avg_return": 0.125, "win_rate": 0.88},
            "HIGH": {"count": 19, "avg_return": 0.078, "win_rate": 0.79},
            "MEDIUM": {"count": 15, "avg_return": 0.034, "win_rate": 0.60}
        },
        "monthly_performance": [
            {"month": "2024-01", "return": 0.045, "decisions": 8},
            {"month": "2024-02", "return": -0.012, "decisions": 6},
            {"month": "2024-03", "return": 0.089, "decisions": 12},
            {"month": "2024-04", "return": 0.067, "decisions": 9},
            {"month": "2024-05", "return": 0.123, "decisions": 7}
        ]
    }


async def _simulate_decision_scenarios(symbol: str, scenarios: List[str],
                                     timeframe: str, monte_carlo_runs: int,
                                     confidence_intervals: List[int],
                                     verbose: bool) -> Dict[str, Any]:
    """Simule différents scénarios de marché."""
    
    with progress_manager.progress_context() as progress:
        # Initialisation
        init_task = progress.add_task("🎲 Initialisation simulation", total=100)
        for i in range(100):
            await asyncio.sleep(0.005)
            progress.update(init_task, advance=1)
        
        # Simulation pour chaque scénario
        for scenario in scenarios:
            scenario_task = progress.add_task(f"📊 Scénario {scenario}", total=monte_carlo_runs)
            for i in range(monte_carlo_runs):
                await asyncio.sleep(0.001)
                progress.update(scenario_task, advance=1)
    
    # Simulation de résultats
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "monte_carlo_runs": monte_carlo_runs,
        "scenarios": scenarios,
        "confidence_intervals": confidence_intervals,
        "scenario_results": {
            "bull": {
                "probability": 0.35,
                "expected_return": 0.187,
                "volatility": 0.165,
                "confidence_intervals": {
                    90: {"lower": 0.089, "upper": 0.298},
                    95: {"lower": 0.067, "upper": 0.334},
                    99: {"lower": 0.023, "upper": 0.412}
                }
            },
            "bear": {
                "probability": 0.25,
                "expected_return": -0.134,
                "volatility": 0.245,
                "confidence_intervals": {
                    90: {"lower": -0.267, "upper": -0.045},
                    95: {"lower": -0.298, "upper": -0.012},
                    99: {"lower": -0.356, "upper": 0.034}
                }
            },
            "sideways": {
                "probability": 0.40,
                "expected_return": 0.023,
                "volatility": 0.089,
                "confidence_intervals": {
                    90: {"lower": -0.034, "upper": 0.089},
                    95: {"lower": -0.045, "upper": 0.103},
                    99: {"lower": -0.067, "upper": 0.134}
                }
            }
        },
        "risk_metrics": {
            "var_95": -0.089,
            "cvar_95": -0.134,
            "probability_of_loss": 0.32,
            "expected_shortfall": -0.067
        },
        "optimal_strategy": {
            "recommended_action": "BUY",
            "position_size": 0.75,  # 75% de la position prévue
            "stop_loss": 0.08,
            "take_profit": 0.15
        }
    }


async def _save_decision_to_history(decision_result: Dict[str, Any]) -> None:
    """Sauvegarde une décision dans l'historique."""
    with spinner_manager.spinner_context("💾 Sauvegarde en cours..."):
        await asyncio.sleep(0.5)


async def _execute_trading_decision(decision_result: Dict[str, Any]) -> None:
    """Exécute une décision de trading."""
    with spinner_manager.spinner_context("🚀 Exécution en cours..."):
        await asyncio.sleep(1.5)


# === Fonctions d'affichage ===

def _display_trading_decision(decision_result: Dict[str, Any]) -> None:
    """Affiche une décision de trading."""
    formatter = DecisionFormatter()
    
    # Panel principal de la décision
    decision_panel = formatter.format_trading_decision(decision_result)
    console.print(decision_panel)
    
    # Arbre de raisonnement
    reasoning_tree = formatter.format_reasoning_tree(decision_result['reasoning'])
    console.print("\n")
    console.print(reasoning_tree)


def _display_decision_table(history_data: Dict[str, Any]) -> None:
    """Affiche l'historique sous forme de tableau."""
    table = Table(title="📊 Historique des Décisions", show_header=True)
    
    table.add_column("ID", style="dim", no_wrap=True)
    table.add_column("Symbole", style="cyan bold")
    table.add_column("Décision", justify="center")
    table.add_column("Confiance", justify="center")
    table.add_column("Montant", justify="right")
    table.add_column("Performance", justify="right")
    table.add_column("Statut", justify="center")
    table.add_column("Date", style="dim")
    
    for decision in history_data['decisions']:
        # Formatage des valeurs
        decision_emoji = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡", "REDUCE": "🟠", "INCREASE": "🔵"}
        decision_display = f"{decision_emoji.get(decision['recommendation'], '⚪')} {decision['recommendation']}"
        
        confidence_emoji = {"VERY_HIGH": "🔥", "HIGH": "🟢", "MEDIUM": "🟡", "LOW": "🔴"}
        confidence_display = f"{confidence_emoji.get(decision['confidence_level'], '⚪')} {decision['confidence_level']}"
        
        amount_display = f"${decision['amount']:,.0f}" if decision['amount'] else "-"
        
        if decision['performance'] is not None:
            perf_color = "green" if decision['performance'] > 0 else "red" if decision['performance'] < 0 else "white"
            performance_display = f"[{perf_color}]{decision['performance']:+.1%}[/{perf_color}]"
        else:
            performance_display = "-"
        
        status_emoji = {"executed": "✅", "pending": "⏳", "cancelled": "❌", "expired": "⏰"}
        status_display = f"{status_emoji.get(decision['status'], '⚪')} {decision['status']}"
        
        date_display = decision['created_at'].strftime('%d/%m %H:%M')
        
        table.add_row(
            decision['id'][-5:],  # Derniers 5 caractères
            decision['symbol'],
            decision_display,
            confidence_display,
            amount_display,
            performance_display,
            status_display,
            date_display
        )
    
    console.print(table)
    
    # Résumé
    summary = history_data['summary']
    console.print(f"\n📊 [bold]Résumé:[/bold] {summary['executed']} exécutées, {summary['pending']} en attente")
    if summary['avg_performance']:
        perf_color = "green" if summary['avg_performance'] > 0 else "red"
        console.print(f"📈 Performance moyenne: [{perf_color}]{summary['avg_performance']:+.1%}[/{perf_color}]")


def _display_decision_detailed(history_data: Dict[str, Any]) -> None:
    """Affiche l'historique détaillé."""
    for decision in history_data['decisions']:
        console.print(Panel.fit(
            f"🆔 [bold]{decision['id']}[/bold] - {decision['symbol']}\n"
            f"📊 Décision: [cyan]{decision['recommendation']}[/cyan] | "
            f"Confiance: [yellow]{decision['confidence_level']}[/yellow] ({decision['confidence_score']:.1%})\n"
            f"💰 Montant: ${decision['amount']:,.0f} | Quantité: {decision['quantity']:.2f}\n"
            f"💹 Prix d'entrée: ${decision['entry_price']:.2f} | Prix actuel: ${decision['current_price']:.2f}\n"
            f"📈 Performance: {decision['performance']:+.1%}\n" if decision['performance'] else ""
            f"🧠 Raisonnement: {decision['reasoning_summary']}\n"
            f"📅 Créée: {decision['created_at'].strftime('%d/%m/%Y à %H:%M')} | "
            f"Statut: {decision['status']}",
            border_style="blue"
        ))
        console.print()


def _display_decision_summary(history_data: Dict[str, Any]) -> None:
    """Affiche un résumé de l'historique."""
    summary = history_data['summary']
    
    console.print(Panel.fit(
        f"📊 [bold]Résumé des Décisions[/bold]\n\n"
        f"📈 Total: {history_data['total_count']} décisions\n"
        f"✅ Exécutées: {summary['executed']}\n"
        f"⏳ En attente: {summary['pending']}\n"
        f"❌ Annulées: {summary['cancelled']}\n"
        f"📊 Performance moyenne: {summary['avg_performance']:+.1%}" if summary['avg_performance'] else "",
        title="📋 Historique",
        border_style="blue"
    ))


def _display_cancellation_result(cancel_result: Dict[str, Any]) -> None:
    """Affiche le résultat d'annulation."""
    if cancel_result['cancellation_successful']:
        console.print(Panel.fit(
            f"✅ [green]Décision annulée avec succès[/green]\n\n"
            f"🆔 ID: {cancel_result['decision_id']}\n"
            f"📝 Raison: {cancel_result['reason']}\n"
            f"🕒 Annulée le: {cancel_result['cancelled_at'].strftime('%d/%m/%Y à %H:%M')}",
            title="❌ Annulation",
            border_style="red"
        ))
    else:
        console.print(f"❌ [red]Échec de l'annulation de la décision {cancel_result['decision_id']}[/red]")


def _display_performance_analysis(performance_data: Dict[str, Any]) -> None:
    """Affiche l'analyse de performance."""
    overall = performance_data['overall_performance']
    
    # Panel principal
    console.print(Panel.fit(
        f"📊 [bold]Performance Globale[/bold]\n\n"
        f"📈 Rendement total: [green]{overall['total_return']:+.1%}[/green]\n"
        f"⚖️  Benchmark ({performance_data['benchmark']}): {overall['benchmark_return']:+.1%}\n"
        f"🎯 Excès de rendement: [cyan]{overall['excess_return']:+.1%}[/cyan]\n"
        f"🏆 Taux de réussite: {overall['win_rate']:.1%}\n"
        f"📊 Ratio de Sharpe: {overall['sharpe_ratio']:.2f}\n"
        f"📉 Drawdown max: {overall['max_drawdown']:.1%}",
        title="📈 Performance des Décisions",
        border_style="green"
    ))
    
    # Tableau par type de décision
    console.print("\n📊 [bold]Performance par Type de Décision:[/bold]")
    type_table = Table(show_header=True)
    type_table.add_column("Type", style="cyan")
    type_table.add_column("Nombre", justify="right")
    type_table.add_column("Rendement Moyen", justify="right")
    type_table.add_column("Taux de Réussite", justify="right")
    
    for decision_type, stats in performance_data['by_decision_type'].items():
        type_table.add_row(
            decision_type,
            str(stats['count']),
            f"{stats['avg_return']:+.1%}",
            f"{stats['win_rate']:.1%}"
        )
    
    console.print(type_table)


def _display_simulation_results(simulation_result: Dict[str, Any]) -> None:
    """Affiche les résultats de simulation."""
    console.print(Panel.fit(
        f"🎲 [bold]Simulation de Scénarios - {simulation_result['symbol']}[/bold]\n\n"
        f"⏰ Horizon: {simulation_result['timeframe']}\n"
        f"🔄 Simulations: {simulation_result['monte_carlo_runs']:,}\n"
        f"📊 Scénarios: {', '.join(simulation_result['scenarios'])}",
        title="🎯 Simulation Monte Carlo",
        border_style="blue"
    ))
    
    # Tableau des scénarios
    console.print("\n📊 [bold]Résultats par Scénario:[/bold]")
    scenario_table = Table(show_header=True)
    scenario_table.add_column("Scénario", style="cyan")
    scenario_table.add_column("Probabilité", justify="right")
    scenario_table.add_column("Rendement Attendu", justify="right")
    scenario_table.add_column("Volatilité", justify="right")
    scenario_table.add_column("IC 95% (Min)", justify="right")
    scenario_table.add_column("IC 95% (Max)", justify="right")
    
    for scenario, results in simulation_result['scenario_results'].items():
        ci_95 = results['confidence_intervals'].get(95, {})
        scenario_table.add_row(
            scenario.capitalize(),
            f"{results['probability']:.1%}",
            f"{results['expected_return']:+.1%}",
            f"{results['volatility']:.1%}",
            f"{ci_95.get('lower', 0):+.1%}",
            f"{ci_95.get('upper', 0):+.1%}"
        )
    
    console.print(scenario_table)
    
    # Recommandation optimale
    optimal = simulation_result['optimal_strategy']
    console.print(f"\n🎯 [bold]Stratégie Optimale:[/bold]")
    console.print(f"📊 Action: [cyan]{optimal['recommended_action']}[/cyan]")
    console.print(f"📏 Taille de position: {optimal['position_size']:.1%}")
    console.print(f"🛑 Stop-loss: {optimal['stop_loss']:.1%}")
    console.print(f"🎯 Take-profit: {optimal['take_profit']:.1%}")


def _export_decision_history(history_data: Dict[str, Any], filepath: str) -> None:
    """Exporte l'historique des décisions."""
    import csv
    from pathlib import Path
    
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # En-têtes
        writer.writerow([
            'ID', 'Symbole', 'Décision', 'Confiance', 'Score', 'Montant', 'Quantité',
            'Prix Entrée', 'Prix Actuel', 'Performance', 'Statut', 'Date Création', 'Raisonnement'
        ])
        
        # Données
        for decision in history_data['decisions']:
            writer.writerow([
                decision['id'],
                decision['symbol'],
                decision['recommendation'],
                decision['confidence_level'],
                decision['confidence_score'],
                decision['amount'] or '',
                decision['quantity'],
                decision['entry_price'],
                decision['current_price'],
                decision['performance'] or '',
                decision['status'],
                decision['created_at'].isoformat(),
                decision['reasoning_summary']
            ])