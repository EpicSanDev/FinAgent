"""
Évaluateur de risque - Calcul des métriques de risque et recommandations.
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any, Tuple
from scipy import stats

from finagent.business.models.decision_models import RiskAssessment, DecisionContext
from finagent.business.models.portfolio_models import Portfolio, Position
from finagent.data.providers.openbb_provider import OpenBBProvider
from finagent.infrastructure.config import settings

logger = logging.getLogger(__name__)


class RiskEvaluator:
    """
    Évaluateur de risque avancé pour l'analyse des risques de trading.
    
    Calcule :
    - VaR (Value at Risk) et CVaR
    - Beta et corrélations
    - Ratio de Sharpe et Sortino
    - Maximum Drawdown
    - Métriques de concentration et liquidité
    - Recommandations de position sizing
    """
    
    def __init__(
        self,
        openbb_provider: OpenBBProvider,
        benchmark_symbol: str = "SPY"
    ):
        """
        Initialise l'évaluateur de risque.
        
        Args:
            openbb_provider: Provider de données financières
            benchmark_symbol: Symbole de référence pour le beta
        """
        self.openbb_provider = openbb_provider
        self.benchmark_symbol = benchmark_symbol
        
        # Configuration des calculs
        self.var_confidence_levels = [0.95, 0.99]
        self.var_periods = [1, 5, 22]  # 1 jour, 1 semaine, 1 mois
        self.lookback_days = 252  # 1 an
        self.risk_free_rate = 0.02  # 2% annuel
        
        # Seuils de risque
        self.risk_thresholds = {
            'low': 0.3,
            'moderate': 0.6,
            'high': 0.8
        }
        
        # Cache pour les données de benchmark
        self._benchmark_cache = {}
        self._cache_expiry = None
        
        logger.info("Évaluateur de risque initialisé")
    
    async def assess_risk(
        self, 
        symbol: str, 
        context: DecisionContext,
        portfolio: Optional[Portfolio] = None
    ) -> RiskAssessment:
        """
        Évalue le risque complet pour un symbole.
        
        Args:
            symbol: Symbole à évaluer
            context: Contexte de décision
            portfolio: Portefeuille pour l'évaluation de concentration
            
        Returns:
            RiskAssessment: Évaluation complète des risques
        """
        logger.info(f"Évaluation des risques pour {symbol}")
        
        try:
            # Collecter les données en parallèle
            tasks = [
                self._get_price_data(symbol),
                self._get_benchmark_data(),
                self._get_sector_info(symbol)
            ]
            
            price_data, benchmark_data, sector_info = \
                await asyncio.gather(*tasks, return_exceptions=True)
            
            # Vérifier les erreurs
            if isinstance(price_data, Exception):
                logger.error(f"Erreur données prix: {price_data}")
                price_data = None
                
            if isinstance(benchmark_data, Exception):
                logger.error(f"Erreur données benchmark: {benchmark_data}")
                benchmark_data = None
                
            if isinstance(sector_info, Exception):
                logger.error(f"Erreur info secteur: {sector_info}")
                sector_info = {}
            
            # Calculer les métriques de risque
            var_metrics = {}
            beta_value = None
            sharpe_ratio = None
            max_drawdown = None
            
            if price_data is not None and len(price_data) > 30:
                # Calculer VaR
                var_metrics = await self._calculate_var_metrics(price_data)
                
                # Calculer Beta
                if benchmark_data is not None:
                    beta_value = await self._calculate_beta(price_data, benchmark_data)
                
                # Calculer Sharpe ratio
                sharpe_ratio = await self._calculate_sharpe_ratio(price_data)
                
                # Calculer Maximum Drawdown
                max_drawdown = await self._calculate_max_drawdown(price_data)
            
            # Évaluer les risques spécifiques
            sector_risk = await self._assess_sector_risk(sector_info)
            concentration_risk = await self._assess_concentration_risk(symbol, context, portfolio)
            liquidity_risk = await self._assess_liquidity_risk(symbol, price_data)
            credit_risk = await self._assess_credit_risk(symbol, sector_info)
            
            # Calculer le score de risque global
            overall_risk_score = await self._calculate_overall_risk_score(
                var_metrics, beta_value, sector_risk, concentration_risk, 
                liquidity_risk, credit_risk
            )
            
            # Déterminer le niveau de risque
            risk_level = self._determine_risk_level(overall_risk_score)
            
            # Calculer la taille de position recommandée
            max_position_size = await self._calculate_max_position_size(
                overall_risk_score, context, var_metrics
            )
            
            # Calculer le stop loss recommandé
            recommended_stop_loss = await self._calculate_recommended_stop_loss(
                context.current_price, var_metrics, max_drawdown
            )
            
            # Construire l'évaluation finale
            risk_assessment = RiskAssessment(
                symbol=symbol,
                var_1d=Decimal(str(var_metrics.get('var_1d', 0))),
                var_5d=Decimal(str(var_metrics.get('var_5d', 0))),
                beta=beta_value,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown,
                sector_risk=sector_risk,
                concentration_risk=concentration_risk,
                liquidity_risk=liquidity_risk,
                credit_risk=credit_risk,
                overall_risk_score=overall_risk_score,
                risk_level=risk_level,
                max_position_size=max_position_size,
                recommended_stop_loss=recommended_stop_loss
            )
            
            logger.info(f"Évaluation risque terminée pour {symbol}: {risk_level}")
            return risk_assessment
            
        except Exception as e:
            logger.error(f"Erreur évaluation risque pour {symbol}: {e}")
            
            # Évaluation par défaut en cas d'erreur
            return RiskAssessment(
                symbol=symbol,
                sector_risk=0.5,
                concentration_risk=context.position_weight,
                liquidity_risk=0.5,
                overall_risk_score=0.7,
                risk_level="Modéré",
                max_position_size=0.05
            )
    
    async def _get_price_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """Récupère les données de prix historiques."""
        try:
            data = await self.openbb_provider.get_historical_data(
                symbol, period="1y", interval="1d"
            )
            
            if data and len(data) > 0:
                df = pd.DataFrame(data)
                df['date'] = pd.to_datetime(df.get('date', df.index))
                df = df.set_index('date')
                
                # Calculer les rendements
                df['returns'] = df['close'].pct_change()
                df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
                
                return df.dropna()
            
            return None
            
        except Exception as e:
            logger.error(f"Erreur récupération données prix pour {symbol}: {e}")
            return None
    
    async def _get_benchmark_data(self) -> Optional[pd.DataFrame]:
        """Récupère les données du benchmark avec cache."""
        try:
            # Vérifier le cache
            now = datetime.now()
            if (self._benchmark_cache and self._cache_expiry and 
                now < self._cache_expiry):
                return self._benchmark_cache.get('data')
            
            # Récupérer de nouvelles données
            data = await self.openbb_provider.get_historical_data(
                self.benchmark_symbol, period="1y", interval="1d"
            )
            
            if data and len(data) > 0:
                df = pd.DataFrame(data)
                df['date'] = pd.to_datetime(df.get('date', df.index))
                df = df.set_index('date')
                df['returns'] = df['close'].pct_change()
                df = df.dropna()
                
                # Mettre à jour le cache
                self._benchmark_cache = {'data': df}
                self._cache_expiry = now + timedelta(hours=4)
                
                return df
            
            return None
            
        except Exception as e:
            logger.error(f"Erreur récupération données benchmark: {e}")
            return None
    
    async def _get_sector_info(self, symbol: str) -> Dict[str, Any]:
        """Récupère les informations sectorielles."""
        try:
            company_info = await self.openbb_provider.get_company_info(symbol)
            return {
                'sector': company_info.get('sector', 'Unknown'),
                'industry': company_info.get('industry', 'Unknown'),
                'market_cap': company_info.get('market_cap', 0),
                'beta': company_info.get('beta'),
            }
        except Exception as e:
            logger.error(f"Erreur info secteur pour {symbol}: {e}")
            return {}
    
    async def _calculate_var_metrics(self, price_data: pd.DataFrame) -> Dict[str, float]:
        """Calcule les métriques Value at Risk."""
        try:
            metrics = {}
            returns = price_data['returns'].dropna()
            
            if len(returns) < 30:
                return metrics
            
            # VaR historique pour différentes périodes
            for period in self.var_periods:
                for confidence in self.var_confidence_levels:
                    # VaR historique
                    var_hist = np.percentile(returns, (1 - confidence) * 100)
                    
                    # VaR paramétrique (normal)
                    mean_return = returns.mean()
                    std_return = returns.std()
                    var_param = stats.norm.ppf(1 - confidence, mean_return, std_return)
                    
                    # Prendre le plus conservateur
                    var_value = min(var_hist, var_param) * np.sqrt(period)
                    
                    key = f'var_{period}d_{int(confidence*100)}'
                    metrics[key] = float(var_value)
            
            # CVaR (Expected Shortfall)
            for period in [1, 5]:
                var_95 = metrics.get(f'var_{period}d_95', 0)
                tail_returns = returns[returns <= var_95 / np.sqrt(period)]
                if len(tail_returns) > 0:
                    cvar = tail_returns.mean() * np.sqrt(period)
                    metrics[f'cvar_{period}d'] = float(cvar)
            
            # Simplifier les clés principales
            metrics['var_1d'] = metrics.get('var_1d_95', 0)
            metrics['var_5d'] = metrics.get('var_5d_95', 0)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Erreur calcul VaR: {e}")
            return {}
    
    async def _calculate_beta(
        self, 
        price_data: pd.DataFrame, 
        benchmark_data: pd.DataFrame
    ) -> Optional[float]:
        """Calcule le beta par rapport au benchmark."""
        try:
            # Aligner les dates
            combined = pd.merge(
                price_data[['returns']], 
                benchmark_data[['returns']], 
                left_index=True, 
                right_index=True, 
                suffixes=('_stock', '_market')
            ).dropna()
            
            if len(combined) < 60:  # Minimum 2 mois de données
                return None
            
            # Calculer beta via régression linéaire
            stock_returns = combined['returns_stock']
            market_returns = combined['returns_market']
            
            covariance = np.cov(stock_returns, market_returns)[0][1]
            market_variance = np.var(market_returns)
            
            if market_variance == 0:
                return None
            
            beta = covariance / market_variance
            return float(beta)
            
        except Exception as e:
            logger.error(f"Erreur calcul beta: {e}")
            return None
    
    async def _calculate_sharpe_ratio(self, price_data: pd.DataFrame) -> Optional[float]:
        """Calcule le ratio de Sharpe."""
        try:
            returns = price_data['returns'].dropna()
            
            if len(returns) < 30:
                return None
            
            # Rendement annualisé
            mean_return = returns.mean() * 252
            
            # Volatilité annualisée
            volatility = returns.std() * np.sqrt(252)
            
            if volatility == 0:
                return None
            
            # Ratio de Sharpe
            sharpe = (mean_return - self.risk_free_rate) / volatility
            return float(sharpe)
            
        except Exception as e:
            logger.error(f"Erreur calcul Sharpe: {e}")
            return None
    
    async def _calculate_max_drawdown(self, price_data: pd.DataFrame) -> Optional[float]:
        """Calcule le maximum drawdown."""
        try:
            prices = price_data['close']
            
            # Calculer les pics cumulés
            cumulative_max = prices.cummax()
            
            # Calculer les drawdowns
            drawdowns = (prices - cumulative_max) / cumulative_max
            
            # Maximum drawdown
            max_dd = drawdowns.min()
            return float(abs(max_dd))
            
        except Exception as e:
            logger.error(f"Erreur calcul max drawdown: {e}")
            return None
    
    async def _assess_sector_risk(self, sector_info: Dict[str, Any]) -> float:
        """Évalue le risque sectoriel."""
        try:
            sector = sector_info.get('sector', '').lower()
            
            # Secteurs à haut risque
            high_risk_sectors = {
                'technology', 'biotechnology', 'cryptocurrency',
                'energy', 'mining', 'real estate', 'financial'
            }
            
            # Secteurs à faible risque
            low_risk_sectors = {
                'utilities', 'consumer staples', 'healthcare',
                'telecommunications', 'consumer defensive'
            }
            
            if any(hrs in sector for hrs in high_risk_sectors):
                return 0.8
            elif any(lrs in sector for lrs in low_risk_sectors):
                return 0.3
            else:
                return 0.5  # Risque modéré par défaut
                
        except Exception as e:
            logger.error(f"Erreur évaluation risque sectoriel: {e}")
            return 0.5
    
    async def _assess_concentration_risk(
        self, 
        symbol: str, 
        context: DecisionContext,
        portfolio: Optional[Portfolio]
    ) -> float:
        """Évalue le risque de concentration."""
        try:
            # Poids actuel dans le portefeuille
            current_weight = context.position_weight
            
            # Risque basé sur la concentration
            if current_weight > 0.2:  # Plus de 20%
                return min(1.0, current_weight * 2)
            elif current_weight > 0.1:  # Plus de 10%
                return current_weight * 1.5
            else:
                return current_weight
                
        except Exception as e:
            logger.error(f"Erreur évaluation risque concentration: {e}")
            return 0.3
    
    async def _assess_liquidity_risk(
        self, 
        symbol: str, 
        price_data: Optional[pd.DataFrame]
    ) -> float:
        """Évalue le risque de liquidité."""
        try:
            if price_data is None or len(price_data) < 20:
                return 0.8  # Risque élevé si pas de données
            
            # Analyser les volumes
            volumes = price_data['volume']
            avg_volume = volumes.mean()
            volume_std = volumes.std()
            
            # Score de liquidité basé sur le volume
            if avg_volume > 1000000:  # Volume élevé
                base_risk = 0.2
            elif avg_volume > 100000:  # Volume modéré
                base_risk = 0.4
            else:  # Volume faible
                base_risk = 0.8
            
            # Ajuster selon la volatilité du volume
            if volume_std > 0 and avg_volume > 0:
                volume_cv = volume_std / avg_volume
                if volume_cv > 1.0:  # Très volatile
                    base_risk += 0.2
                elif volume_cv > 0.5:  # Modérément volatile
                    base_risk += 0.1
            
            return min(1.0, base_risk)
            
        except Exception as e:
            logger.error(f"Erreur évaluation risque liquidité: {e}")
            return 0.6
    
    async def _assess_credit_risk(
        self, 
        symbol: str, 
        sector_info: Dict[str, Any]
    ) -> Optional[float]:
        """Évalue le risque de crédit (pour les obligations/secteurs sensibles)."""
        try:
            sector = sector_info.get('sector', '').lower()
            market_cap = sector_info.get('market_cap', 0)
            
            # Secteurs sensibles au crédit
            credit_sensitive_sectors = {
                'financial', 'banking', 'real estate', 'utilities'
            }
            
            if any(css in sector for css in credit_sensitive_sectors):
                # Risque basé sur la taille de l'entreprise
                if market_cap > 50_000_000_000:  # Large cap
                    return 0.3
                elif market_cap > 10_000_000_000:  # Mid cap
                    return 0.5
                else:  # Small cap
                    return 0.7
            
            return None  # Pas applicable
            
        except Exception as e:
            logger.error(f"Erreur évaluation risque crédit: {e}")
            return None
    
    async def _calculate_overall_risk_score(
        self,
        var_metrics: Dict[str, float],
        beta: Optional[float],
        sector_risk: float,
        concentration_risk: float,
        liquidity_risk: float,
        credit_risk: Optional[float]
    ) -> float:
        """Calcule le score de risque global."""
        try:
            risk_components = []
            weights = []
            
            # VaR (30% du poids)
            if var_metrics.get('var_1d'):
                var_risk = min(1.0, abs(var_metrics['var_1d']) * 20)  # Normaliser
                risk_components.append(var_risk)
                weights.append(0.3)
            
            # Beta (20% du poids)
            if beta is not None:
                beta_risk = min(1.0, abs(beta - 1.0) * 0.5 + 0.3)
                risk_components.append(beta_risk)
                weights.append(0.2)
            
            # Risque sectoriel (20% du poids)
            risk_components.append(sector_risk)
            weights.append(0.2)
            
            # Risque de concentration (15% du poids)
            risk_components.append(concentration_risk)
            weights.append(0.15)
            
            # Risque de liquidité (10% du poids)
            risk_components.append(liquidity_risk)
            weights.append(0.1)
            
            # Risque de crédit (5% du poids si applicable)
            if credit_risk is not None:
                risk_components.append(credit_risk)
                weights.append(0.05)
            
            # Normaliser les poids
            total_weight = sum(weights)
            weights = [w / total_weight for w in weights]
            
            # Calculer le score pondéré
            overall_score = sum(risk * weight for risk, weight in zip(risk_components, weights))
            
            return min(1.0, max(0.0, overall_score))
            
        except Exception as e:
            logger.error(f"Erreur calcul score risque global: {e}")
            return 0.6
    
    def _determine_risk_level(self, risk_score: float) -> str:
        """Détermine le niveau de risque textuel."""
        if risk_score <= self.risk_thresholds['low']:
            return "Faible"
        elif risk_score <= self.risk_thresholds['moderate']:
            return "Modéré"
        elif risk_score <= self.risk_thresholds['high']:
            return "Élevé"
        else:
            return "Très Élevé"
    
    async def _calculate_max_position_size(
        self,
        risk_score: float,
        context: DecisionContext,
        var_metrics: Dict[str, float]
    ) -> float:
        """Calcule la taille de position maximale recommandée."""
        try:
            # Taille de base selon le niveau de risque
            base_sizes = {
                "Faible": 0.15,
                "Modéré": 0.10,
                "Élevé": 0.05,
                "Très Élevé": 0.02
            }
            
            risk_level = self._determine_risk_level(risk_score)
            base_size = base_sizes.get(risk_level, 0.05)
            
            # Ajustement selon le VaR
            if var_metrics.get('var_1d'):
                var_1d = abs(var_metrics['var_1d'])
                if var_1d > 0.05:  # 5% VaR journalier
                    base_size *= 0.5
                elif var_1d > 0.03:  # 3% VaR journalier
                    base_size *= 0.7
            
            # Ajustement selon la concentration actuelle
            if context.position_weight > 0.05:
                base_size *= 0.8
            
            return min(0.2, max(0.01, base_size))
            
        except Exception as e:
            logger.error(f"Erreur calcul taille position max: {e}")
            return 0.05
    
    async def _calculate_recommended_stop_loss(
        self,
        current_price: Decimal,
        var_metrics: Dict[str, float],
        max_drawdown: Optional[float]
    ) -> Optional[Decimal]:
        """Calcule le stop loss recommandé."""
        try:
            price = float(current_price)
            
            # Basé sur le VaR 5 jours
            var_5d = var_metrics.get('var_5d')
            if var_5d:
                var_stop = price * (1 + var_5d * 2)  # 2x VaR comme marge
            else:
                var_stop = None
            
            # Basé sur le maximum drawdown historique
            if max_drawdown:
                dd_stop = price * (1 - max_drawdown * 0.5)  # 50% du max DD
            else:
                dd_stop = None
            
            # Stop loss par défaut (10%)
            default_stop = price * 0.9
            
            # Prendre le plus conservateur
            stops = [s for s in [var_stop, dd_stop, default_stop] if s is not None]
            
            if stops:
                recommended_stop = max(stops)  # Le moins restrictif
                return Decimal(str(recommended_stop))
            
            return None
            
        except Exception as e:
            logger.error(f"Erreur calcul stop loss recommandé: {e}")
            return None