"""
Suivi de performance - Calcul des métriques de performance et suivi historique.
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID

from finagent.business.models.portfolio_models import (
    Portfolio,
    PortfolioMetrics,
    PerformanceMetrics
)
from finagent.data.providers.openbb_provider import OpenBBProvider

logger = logging.getLogger(__name__)


class PerformanceTracker:
    """
    Suivi de performance du portefeuille.
    
    Calcule :
    - Rendements sur différentes périodes
    - Métriques de risque (volatilité, VaR, drawdown)
    - Ratios de performance (Sharpe, Sortino, Calmar)
    - Comparaison avec benchmarks
    - Attribution de performance
    """
    
    def __init__(
        self,
        openbb_provider: OpenBBProvider,
        benchmark_symbols: List[str] = None
    ):
        """
        Initialise le tracker de performance.
        
        Args:
            openbb_provider: Provider de données financières
            benchmark_symbols: Symboles de référence pour comparaison
        """
        self.openbb_provider = openbb_provider
        self.benchmark_symbols = benchmark_symbols or ["SPY", "QQQ", "IWM"]
        
        # Configuration
        self.risk_free_rate = 0.02  # 2% annuel
        
        # Cache pour l'historique des portefeuilles
        self._portfolio_history: Dict[UUID, List[Dict[str, Any]]] = {}
        self._benchmark_cache: Dict[str, pd.DataFrame] = {}
        
        logger.info("Tracker de performance initialisé")
    
    async def track_portfolio_snapshot(self, portfolio: Portfolio):
        """
        Enregistre un snapshot du portefeuille pour le suivi historique.
        
        Args:
            portfolio: Portefeuille à enregistrer
        """
        try:
            snapshot = {
                'timestamp': datetime.now(),
                'total_value': float(portfolio.total_value),
                'cash_balance': float(portfolio.cash_balance),
                'invested_amount': float(portfolio.invested_amount),
                'total_pnl': float(portfolio.total_pnl),
                'unrealized_pnl': float(portfolio.unrealized_pnl),
                'realized_pnl': float(portfolio.realized_pnl),
                'position_count': portfolio.position_count,
                'positions': {
                    symbol: {
                        'quantity': float(pos.quantity),
                        'market_value': float(pos.market_value),
                        'weight': pos.weight,
                        'pnl': float(pos.total_pnl)
                    }
                    for symbol, pos in portfolio.active_positions.items()
                }
            }
            
            if portfolio.id not in self._portfolio_history:
                self._portfolio_history[portfolio.id] = []
            
            self._portfolio_history[portfolio.id].append(snapshot)
            
            # Garder seulement les 2 dernières années
            cutoff_date = datetime.now() - timedelta(days=730)
            self._portfolio_history[portfolio.id] = [
                s for s in self._portfolio_history[portfolio.id]
                if s['timestamp'] > cutoff_date
            ]
            
            logger.debug(f"Snapshot enregistré pour portefeuille {portfolio.id}")
            
        except Exception as e:
            logger.error(f"Erreur enregistrement snapshot: {e}")
    
    async def calculate_metrics(self, portfolio: Portfolio) -> PortfolioMetrics:
        """
        Calcule les métriques complètes du portefeuille.
        
        Args:
            portfolio: Portefeuille à analyser
            
        Returns:
            PortfolioMetrics: Métriques calculées
        """
        logger.info(f"Calcul métriques pour portefeuille {portfolio.id}")
        
        try:
            # Récupérer l'historique
            history = self._portfolio_history.get(portfolio.id, [])
            
            # Calculs de base
            cash_percentage = float(portfolio.cash_balance / portfolio.total_value) if portfolio.total_value > 0 else 1.0
            
            # Rendements
            returns = await self._calculate_returns(history)
            
            # Volatilité
            volatility_metrics = await self._calculate_volatility(history)
            
            # Drawdown
            drawdown_metrics = await self._calculate_drawdown(history)
            
            # Diversification
            diversification_metrics = await self._calculate_diversification(portfolio)
            
            # Top positions
            top_positions = await self._get_top_positions(portfolio)
            
            return PortfolioMetrics(
                portfolio_id=portfolio.id,
                total_value=portfolio.total_value,
                net_worth=portfolio.total_value,
                cash_percentage=cash_percentage,
                daily_return=returns.get('daily', 0.0),
                weekly_return=returns.get('weekly', 0.0),
                monthly_return=returns.get('monthly', 0.0),
                yearly_return=returns.get('yearly', 0.0),
                total_return=portfolio.return_percentage,
                volatility_1m=volatility_metrics.get('1m', 0.0),
                volatility_3m=volatility_metrics.get('3m', 0.0),
                volatility_1y=volatility_metrics.get('1y', 0.0),
                current_drawdown=drawdown_metrics.get('current', 0.0),
                max_drawdown_1m=drawdown_metrics.get('1m', 0.0),
                max_drawdown_3m=drawdown_metrics.get('3m', 0.0),
                max_drawdown_1y=drawdown_metrics.get('1y', 0.0),
                position_count=portfolio.position_count,
                sector_count=len(portfolio.sector_allocation),
                herfindahl_index=diversification_metrics.get('herfindahl', 0.0),
                concentration_ratio=diversification_metrics.get('concentration', 0.0),
                top_positions=top_positions,
                sector_weights=portfolio.sector_allocation
            )
            
        except Exception as e:
            logger.error(f"Erreur calcul métriques portefeuille {portfolio.id}: {e}")
            
            # Métriques minimales en cas d'erreur
            return PortfolioMetrics(
                portfolio_id=portfolio.id,
                total_value=portfolio.total_value,
                net_worth=portfolio.total_value,
                cash_percentage=float(portfolio.cash_balance / portfolio.total_value) if portfolio.total_value > 0 else 1.0,
                daily_return=0.0,
                weekly_return=0.0,
                monthly_return=0.0,
                yearly_return=0.0,
                total_return=portfolio.return_percentage,
                volatility_1m=0.0,
                volatility_3m=0.0,
                volatility_1y=0.0,
                current_drawdown=0.0,
                max_drawdown_1m=0.0,
                max_drawdown_3m=0.0,
                max_drawdown_1y=0.0,
                position_count=portfolio.position_count,
                sector_count=len(portfolio.sector_allocation),
                herfindahl_index=0.0,
                concentration_ratio=0.0,
                sector_weights=portfolio.sector_allocation
            )
    
    async def calculate_performance_metrics(
        self,
        portfolio: Portfolio,
        period_start: datetime,
        period_end: datetime,
        benchmark_symbol: str = "SPY"
    ) -> PerformanceMetrics:
        """
        Calcule les métriques de performance détaillées pour une période.
        
        Args:
            portfolio: Portefeuille à analyser
            period_start: Début de la période
            period_end: Fin de la période
            benchmark_symbol: Symbole de référence
            
        Returns:
            PerformanceMetrics: Métriques de performance
        """
        logger.info(f"Calcul métriques performance pour {period_start} - {period_end}")
        
        try:
            # Récupérer l'historique pour la période
            history = self._portfolio_history.get(portfolio.id, [])
            period_history = [
                h for h in history
                if period_start <= h['timestamp'] <= period_end
            ]
            
            if len(period_history) < 2:
                logger.warning("Historique insuffisant pour calcul performance")
                return self._create_empty_performance_metrics(
                    portfolio.id, period_start, period_end
                )
            
            # Calculer les rendements du portefeuille
            portfolio_returns = await self._calculate_period_returns(period_history)
            
            # Récupérer les données du benchmark
            benchmark_data = await self._get_benchmark_data(
                benchmark_symbol, period_start, period_end
            )
            
            # Calculer les métriques
            absolute_return = portfolio_returns[-1] if portfolio_returns else 0.0
            annualized_return = await self._annualize_return(absolute_return, period_start, period_end)
            
            # Benchmark et alpha
            benchmark_return = None
            alpha = None
            tracking_error = None
            information_ratio = None
            
            if benchmark_data is not None and len(benchmark_data) > 0:
                benchmark_return = float((benchmark_data['close'].iloc[-1] / benchmark_data['close'].iloc[0]) - 1)
                alpha = absolute_return - benchmark_return
                
                # Tracking error et information ratio
                if len(portfolio_returns) > 1 and len(benchmark_data) >= len(portfolio_returns):
                    benchmark_returns = benchmark_data['close'].pct_change().dropna().tail(len(portfolio_returns) - 1)
                    portfolio_daily_returns = np.diff(portfolio_returns) / portfolio_returns[:-1]
                    
                    if len(benchmark_returns) == len(portfolio_daily_returns):
                        excess_returns = portfolio_daily_returns - benchmark_returns.values
                        tracking_error = float(np.std(excess_returns) * np.sqrt(252))
                        if tracking_error > 0:
                            information_ratio = float(np.mean(excess_returns) * 252 / tracking_error)
            
            # Ratios de performance
            ratios = await self._calculate_performance_ratios(portfolio_returns, period_start, period_end)
            
            # Statistiques de risque
            risk_stats = await self._calculate_risk_statistics(portfolio_returns)
            
            # Drawdown
            drawdown_stats = await self._calculate_detailed_drawdown(portfolio_returns)
            
            # Win/Loss statistics
            win_loss_stats = await self._calculate_win_loss_stats(period_history)
            
            return PerformanceMetrics(
                portfolio_id=portfolio.id,
                period_start=period_start,
                period_end=period_end,
                absolute_return=absolute_return,
                relative_return=absolute_return,  # Same for now
                annualized_return=annualized_return,
                benchmark_return=benchmark_return,
                alpha=alpha,
                tracking_error=tracking_error,
                information_ratio=information_ratio,
                sharpe_ratio=ratios.get('sharpe'),
                sortino_ratio=ratios.get('sortino'),
                calmar_ratio=ratios.get('calmar'),
                omega_ratio=ratios.get('omega'),
                volatility=risk_stats.get('volatility', 0.0),
                downside_deviation=risk_stats.get('downside_deviation', 0.0),
                var_95=risk_stats.get('var_95', 0.0),
                cvar_95=risk_stats.get('cvar_95', 0.0),
                max_drawdown=drawdown_stats.get('max_drawdown', 0.0),
                avg_drawdown=drawdown_stats.get('avg_drawdown', 0.0),
                recovery_time=drawdown_stats.get('recovery_time'),
                win_rate=win_loss_stats.get('win_rate', 0.0),
                profit_factor=win_loss_stats.get('profit_factor', 0.0),
                avg_win=win_loss_stats.get('avg_win', 0.0),
                avg_loss=win_loss_stats.get('avg_loss', 0.0),
                trades_count=win_loss_stats.get('trades_count', 0),
                profitable_trades=win_loss_stats.get('profitable_trades', 0),
                losing_trades=win_loss_stats.get('losing_trades', 0)
            )
            
        except Exception as e:
            logger.error(f"Erreur calcul métriques performance: {e}")
            return self._create_empty_performance_metrics(
                portfolio.id, period_start, period_end
            )
    
    async def _calculate_returns(self, history: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calcule les rendements sur différentes périodes."""
        
        if len(history) < 2:
            return {'daily': 0.0, 'weekly': 0.0, 'monthly': 0.0, 'yearly': 0.0}
        
        try:
            # Trier par timestamp
            sorted_history = sorted(history, key=lambda x: x['timestamp'])
            
            # Rendement journalier (si disponible)
            daily_return = 0.0
            if len(sorted_history) >= 2:
                latest = sorted_history[-1]
                previous = sorted_history[-2]
                if previous['total_value'] > 0:
                    daily_return = (latest['total_value'] - previous['total_value']) / previous['total_value']
            
            # Rendements sur périodes plus longues
            now = datetime.now()
            
            weekly_return = self._calculate_period_return(sorted_history, now - timedelta(weeks=1))
            monthly_return = self._calculate_period_return(sorted_history, now - timedelta(days=30))
            yearly_return = self._calculate_period_return(sorted_history, now - timedelta(days=365))
            
            return {
                'daily': daily_return,
                'weekly': weekly_return,
                'monthly': monthly_return,
                'yearly': yearly_return
            }
            
        except Exception as e:
            logger.error(f"Erreur calcul rendements: {e}")
            return {'daily': 0.0, 'weekly': 0.0, 'monthly': 0.0, 'yearly': 0.0}
    
    def _calculate_period_return(
        self, 
        sorted_history: List[Dict[str, Any]], 
        start_date: datetime
    ) -> float:
        """Calcule le rendement depuis une date donnée."""
        
        try:
            # Trouver le point de départ le plus proche
            start_point = None
            for point in sorted_history:
                if point['timestamp'] >= start_date:
                    start_point = point
                    break
            
            if start_point is None and sorted_history:
                start_point = sorted_history[0]
            
            if start_point and sorted_history:
                end_point = sorted_history[-1]
                if start_point['total_value'] > 0:
                    return (end_point['total_value'] - start_point['total_value']) / start_point['total_value']
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Erreur calcul rendement période: {e}")
            return 0.0
    
    async def _calculate_volatility(self, history: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calcule la volatilité sur différentes périodes."""
        
        if len(history) < 10:
            return {'1m': 0.0, '3m': 0.0, '1y': 0.0}
        
        try:
            # Convertir en DataFrame
            df = pd.DataFrame(history)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
            
            # Calculer les rendements journaliers
            df['returns'] = df['total_value'].pct_change()
            returns = df['returns'].dropna()
            
            if len(returns) < 5:
                return {'1m': 0.0, '3m': 0.0, '1y': 0.0}
            
            # Volatilité sur différentes périodes
            now = datetime.now()
            
            vol_1m = self._calculate_period_volatility(df, now - timedelta(days=30))
            vol_3m = self._calculate_period_volatility(df, now - timedelta(days=90))
            vol_1y = self._calculate_period_volatility(df, now - timedelta(days=365))
            
            return {'1m': vol_1m, '3m': vol_3m, '1y': vol_1y}
            
        except Exception as e:
            logger.error(f"Erreur calcul volatilité: {e}")
            return {'1m': 0.0, '3m': 0.0, '1y': 0.0}
    
    def _calculate_period_volatility(self, df: pd.DataFrame, start_date: datetime) -> float:
        """Calcule la volatilité pour une période donnée."""
        
        try:
            period_df = df[df['timestamp'] >= start_date]
            if len(period_df) < 5:
                return 0.0
            
            returns = period_df['returns'].dropna()
            if len(returns) < 2:
                return 0.0
            
            # Volatilité annualisée
            volatility = returns.std() * np.sqrt(252)
            return float(volatility)
            
        except Exception as e:
            logger.error(f"Erreur calcul volatilité période: {e}")
            return 0.0
    
    async def _calculate_drawdown(self, history: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calcule les métriques de drawdown."""
        
        if len(history) < 2:
            return {'current': 0.0, '1m': 0.0, '3m': 0.0, '1y': 0.0}
        
        try:
            # Convertir en DataFrame
            df = pd.DataFrame(history)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
            
            # Calculer les drawdowns
            df['cummax'] = df['total_value'].cummax()
            df['drawdown'] = (df['total_value'] - df['cummax']) / df['cummax']
            
            # Drawdown actuel
            current_drawdown = float(abs(df['drawdown'].iloc[-1]))
            
            # Drawdowns sur périodes
            now = datetime.now()
            
            dd_1m = self._calculate_period_max_drawdown(df, now - timedelta(days=30))
            dd_3m = self._calculate_period_max_drawdown(df, now - timedelta(days=90))
            dd_1y = self._calculate_period_max_drawdown(df, now - timedelta(days=365))
            
            return {
                'current': current_drawdown,
                '1m': dd_1m,
                '3m': dd_3m,
                '1y': dd_1y
            }
            
        except Exception as e:
            logger.error(f"Erreur calcul drawdown: {e}")
            return {'current': 0.0, '1m': 0.0, '3m': 0.0, '1y': 0.0}
    
    def _calculate_period_max_drawdown(self, df: pd.DataFrame, start_date: datetime) -> float:
        """Calcule le drawdown maximum pour une période."""
        
        try:
            period_df = df[df['timestamp'] >= start_date]
            if len(period_df) < 2:
                return 0.0
            
            max_drawdown = period_df['drawdown'].min()
            return float(abs(max_drawdown))
            
        except Exception as e:
            logger.error(f"Erreur calcul max drawdown période: {e}")
            return 0.0
    
    async def _calculate_diversification(self, portfolio: Portfolio) -> Dict[str, float]:
        """Calcule les métriques de diversification."""
        
        try:
            positions = portfolio.active_positions
            if not positions:
                return {'herfindahl': 0.0, 'concentration': 0.0}
            
            # Indice de Herfindahl (concentration)
            weights = [pos.weight for pos in positions.values()]
            herfindahl = sum(w**2 for w in weights)
            
            # Ratio de concentration (top 3 positions)
            sorted_weights = sorted(weights, reverse=True)
            concentration = sum(sorted_weights[:3])
            
            return {
                'herfindahl': float(herfindahl),
                'concentration': float(concentration)
            }
            
        except Exception as e:
            logger.error(f"Erreur calcul diversification: {e}")
            return {'herfindahl': 0.0, 'concentration': 0.0}
    
    async def _get_top_positions(self, portfolio: Portfolio) -> List[Dict[str, Any]]:
        """Récupère les top positions du portefeuille."""
        
        try:
            positions = list(portfolio.active_positions.values())
            positions.sort(key=lambda p: p.market_value, reverse=True)
            
            top_positions = []
            for pos in positions[:10]:  # Top 10
                top_positions.append({
                    'symbol': pos.symbol,
                    'market_value': float(pos.market_value),
                    'weight': pos.weight,
                    'pnl': float(pos.total_pnl),
                    'return_pct': pos.return_percentage
                })
            
            return top_positions
            
        except Exception as e:
            logger.error(f"Erreur récupération top positions: {e}")
            return []
    
    async def _calculate_period_returns(self, history: List[Dict[str, Any]]) -> List[float]:
        """Calcule les rendements cumulés pour une période."""
        
        if len(history) < 2:
            return [1.0]
        
        try:
            sorted_history = sorted(history, key=lambda x: x['timestamp'])
            base_value = sorted_history[0]['total_value']
            
            returns = []
            for point in sorted_history:
                if base_value > 0:
                    cumulative_return = point['total_value'] / base_value
                else:
                    cumulative_return = 1.0
                returns.append(cumulative_return)
            
            return returns
            
        except Exception as e:
            logger.error(f"Erreur calcul rendements période: {e}")
            return [1.0]
    
    async def _get_benchmark_data(
        self, 
        symbol: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> Optional[pd.DataFrame]:
        """Récupère les données du benchmark."""
        
        try:
            # Vérifier le cache
            cache_key = f"{symbol}_{start_date.date()}_{end_date.date()}"
            if cache_key in self._benchmark_cache:
                return self._benchmark_cache[cache_key]
            
            # Récupérer les données
            period_days = (end_date - start_date).days
            if period_days <= 30:
                period = "1mo"
            elif period_days <= 90:
                period = "3mo"
            elif period_days <= 365:
                period = "1y"
            else:
                period = "2y"
            
            data = await self.openbb_provider.get_historical_data(
                symbol, period=period, interval="1d"
            )
            
            if data:
                df = pd.DataFrame(data)
                df['date'] = pd.to_datetime(df.get('date', df.index))
                df = df.set_index('date')
                
                # Filtrer selon les dates
                df = df[(df.index >= start_date) & (df.index <= end_date)]
                
                # Mettre en cache
                self._benchmark_cache[cache_key] = df
                
                return df
            
            return None
            
        except Exception as e:
            logger.error(f"Erreur récupération données benchmark {symbol}: {e}")
            return None
    
    async def _annualize_return(
        self, 
        total_return: float, 
        start_date: datetime, 
        end_date: datetime
    ) -> float:
        """Annualise un rendement."""
        
        try:
            days = (end_date - start_date).days
            if days == 0:
                return 0.0
            
            years = days / 365.25
            if years == 0:
                return 0.0
            
            annualized = (1 + total_return) ** (1 / years) - 1
            return float(annualized)
            
        except Exception as e:
            logger.error(f"Erreur annualisation rendement: {e}")
            return 0.0
    
    async def _calculate_performance_ratios(
        self, 
        returns: List[float], 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, Optional[float]]:
        """Calcule les ratios de performance."""
        
        if len(returns) < 2:
            return {'sharpe': None, 'sortino': None, 'calmar': None, 'omega': None}
        
        try:
            # Convertir en rendements journaliers
            daily_returns = np.diff(returns) / np.array(returns[:-1])
            
            if len(daily_returns) == 0:
                return {'sharpe': None, 'sortino': None, 'calmar': None, 'omega': None}
            
            # Rendement moyen et volatilité
            mean_return = np.mean(daily_returns) * 252
            volatility = np.std(daily_returns) * np.sqrt(252)
            
            # Ratio de Sharpe
            sharpe = None
            if volatility > 0:
                sharpe = (mean_return - self.risk_free_rate) / volatility
            
            # Ratio de Sortino
            sortino = None
            negative_returns = daily_returns[daily_returns < 0]
            if len(negative_returns) > 0:
                downside_deviation = np.std(negative_returns) * np.sqrt(252)
                if downside_deviation > 0:
                    sortino = (mean_return - self.risk_free_rate) / downside_deviation
            
            # Autres ratios (simplifié)
            calmar = None
            omega = None
            
            return {
                'sharpe': float(sharpe) if sharpe is not None else None,
                'sortino': float(sortino) if sortino is not None else None,
                'calmar': calmar,
                'omega': omega
            }
            
        except Exception as e:
            logger.error(f"Erreur calcul ratios performance: {e}")
            return {'sharpe': None, 'sortino': None, 'calmar': None, 'omega': None}
    
    async def _calculate_risk_statistics(self, returns: List[float]) -> Dict[str, float]:
        """Calcule les statistiques de risque."""
        
        if len(returns) < 2:
            return {
                'volatility': 0.0, 'downside_deviation': 0.0,
                'var_95': 0.0, 'cvar_95': 0.0
            }
        
        try:
            daily_returns = np.diff(returns) / np.array(returns[:-1])
            
            # Volatilité
            volatility = np.std(daily_returns) * np.sqrt(252)
            
            # Déviation négative
            negative_returns = daily_returns[daily_returns < 0]
            downside_deviation = np.std(negative_returns) * np.sqrt(252) if len(negative_returns) > 0 else 0.0
            
            # VaR et CVaR
            var_95 = np.percentile(daily_returns, 5)
            cvar_95 = np.mean(daily_returns[daily_returns <= var_95]) if np.any(daily_returns <= var_95) else var_95
            
            return {
                'volatility': float(volatility),
                'downside_deviation': float(downside_deviation),
                'var_95': float(abs(var_95)),
                'cvar_95': float(abs(cvar_95))
            }
            
        except Exception as e:
            logger.error(f"Erreur calcul statistiques risque: {e}")
            return {
                'volatility': 0.0, 'downside_deviation': 0.0,
                'var_95': 0.0, 'cvar_95': 0.0
            }
    
    async def _calculate_detailed_drawdown(self, returns: List[float]) -> Dict[str, Any]:
        """Calcule les statistiques détaillées de drawdown."""
        
        if len(returns) < 2:
            return {'max_drawdown': 0.0, 'avg_drawdown': 0.0, 'recovery_time': None}
        
        try:
            # Calculer les drawdowns
            cummax = np.maximum.accumulate(returns)
            drawdowns = (np.array(returns) - cummax) / cummax
            
            max_drawdown = abs(np.min(drawdowns))
            avg_drawdown = abs(np.mean(drawdowns[drawdowns < 0])) if np.any(drawdowns < 0) else 0.0
            
            # Temps de récupération (simplifié)
            recovery_time = None
            
            return {
                'max_drawdown': float(max_drawdown),
                'avg_drawdown': float(avg_drawdown),
                'recovery_time': recovery_time
            }
            
        except Exception as e:
            logger.error(f"Erreur calcul drawdown détaillé: {e}")
            return {'max_drawdown': 0.0, 'avg_drawdown': 0.0, 'recovery_time': None}
    
    async def _calculate_win_loss_stats(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calcule les statistiques de gains/pertes."""
        
        if len(history) < 2:
            return {
                'win_rate': 0.0, 'profit_factor': 0.0,
                'avg_win': 0.0, 'avg_loss': 0.0,
                'trades_count': 0, 'profitable_trades': 0, 'losing_trades': 0
            }
        
        try:
            # Calculer les changements journaliers de P&L
            sorted_history = sorted(history, key=lambda x: x['timestamp'])
            pnl_changes = []
            
            for i in range(1, len(sorted_history)):
                prev_pnl = sorted_history[i-1]['total_pnl']
                curr_pnl = sorted_history[i]['total_pnl']
                change = curr_pnl - prev_pnl
                if abs(change) > 0.01:  # Ignorer les très petits changements
                    pnl_changes.append(change)
            
            if not pnl_changes:
                return {
                    'win_rate': 0.0, 'profit_factor': 0.0,
                    'avg_win': 0.0, 'avg_loss': 0.0,
                    'trades_count': 0, 'profitable_trades': 0, 'losing_trades': 0
                }
            
            # Séparer gains et pertes
            wins = [p for p in pnl_changes if p > 0]
            losses = [p for p in pnl_changes if p < 0]
            
            # Statistiques
            trades_count = len(pnl_changes)
            profitable_trades = len(wins)
            losing_trades = len(losses)
            win_rate = profitable_trades / trades_count if trades_count > 0 else 0.0
            
            avg_win = np.mean(wins) if wins else 0.0
            avg_loss = abs(np.mean(losses)) if losses else 0.0
            
            profit_factor = (sum(wins) / abs(sum(losses))) if losses and sum(losses) != 0 else 0.0
            
            return {
                'win_rate': float(win_rate),
                'profit_factor': float(profit_factor),
                'avg_win': float(avg_win),
                'avg_loss': float(avg_loss),
                'trades_count': trades_count,
                'profitable_trades': profitable_trades,
                'losing_trades': losing_trades
            }
            
        except Exception as e:
            logger.error(f"Erreur calcul statistiques win/loss: {e}")
            return {
                'win_rate': 0.0, 'profit_factor': 0.0,
                'avg_win': 0.0, 'avg_loss': 0.0,
                'trades_count': 0, 'profitable_trades': 0, 'losing_trades': 0
            }
    
    def _create_empty_performance_metrics(
        self,
        portfolio_id: UUID,
        period_start: datetime,
        period_end: datetime
    ) -> PerformanceMetrics:
        """Crée des métriques vides en cas d'erreur."""
        
        return PerformanceMetrics(
            portfolio_id=portfolio_id,
            period_start=period_start,
            period_end=period_end,
            absolute_return=0.0,
            relative_return=0.0,
            annualized_return=0.0,
            volatility=0.0,
            downside_deviation=0.0,
            var_95=0.0,
            cvar_95=0.0,
            max_drawdown=0.0,
            avg_drawdown=0.0,
            win_rate=0.0,
            profit_factor=0.0,
            avg_win=0.0,
            avg_loss=0.0,
            trades_count=0,
            profitable_trades=0,
            losing_trades=0
        )