"""
Analyseur de marché - Analyse technique et fondamentale avancée.
"""

import asyncio
import logging
import numpy as np
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd

from finagent.business.models.decision_models import MarketAnalysis, DecisionContext
from finagent.data.providers.openbb_provider import OpenBBProvider
from finagent.ai.services.analysis_service import AnalysisService
from finagent.infrastructure.config import settings

logger = logging.getLogger(__name__)


class MarketAnalyzer:
    """
    Analyseur de marché avancé combinant analyse technique et fondamentale.
    
    Fournit :
    - Indicateurs techniques (RSI, MACD, Bollinger, etc.)
    - Niveaux de support et résistance
    - Analyse de tendance et volatilité
    - Sentiment de marché
    - Métriques fondamentales
    """
    
    def __init__(
        self,
        openbb_provider: OpenBBProvider,
        analysis_service: AnalysisService
    ):
        """
        Initialise l'analyseur de marché.
        
        Args:
            openbb_provider: Provider de données financières
            analysis_service: Service d'analyse IA
        """
        self.openbb_provider = openbb_provider
        self.analysis_service = analysis_service
        
        # Configuration des indicateurs techniques
        self.rsi_period = 14
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9
        self.bb_period = 20
        self.bb_std = 2
        self.sma_periods = [20, 50, 200]
        self.ema_periods = [12, 26]
        
        logger.info("Analyseur de marché initialisé")
    
    async def analyze_market(
        self, 
        symbol: str, 
        context: DecisionContext
    ) -> MarketAnalysis:
        """
        Analyse complète du marché pour un symbole.
        
        Args:
            symbol: Symbole à analyser
            context: Contexte de décision
            
        Returns:
            MarketAnalysis: Analyse complète du marché
        """
        logger.info(f"Démarrage analyse marché pour {symbol}")
        
        try:
            # Collecter toutes les données en parallèle
            tasks = [
                self._get_historical_data(symbol),
                self._get_company_fundamentals(symbol),
                self._get_market_sentiment(symbol),
                self._get_volume_data(symbol)
            ]
            
            historical_data, fundamentals, sentiment, volume_data = \
                await asyncio.gather(*tasks, return_exceptions=True)
            
            # Vérifier les erreurs
            if isinstance(historical_data, Exception):
                logger.error(f"Erreur données historiques: {historical_data}")
                historical_data = None
                
            if isinstance(fundamentals, Exception):
                logger.error(f"Erreur données fondamentales: {fundamentals}")
                fundamentals = {}
                
            if isinstance(sentiment, Exception):
                logger.error(f"Erreur sentiment: {sentiment}")
                sentiment = {}
                
            if isinstance(volume_data, Exception):
                logger.error(f"Erreur données volume: {volume_data}")
                volume_data = {}
            
            # Effectuer les analyses
            technical_indicators = {}
            support_levels = []
            resistance_levels = []
            trend_direction = "neutral"
            volatility = 0.0
            
            if historical_data is not None and len(historical_data) > 0:
                # Analyse technique
                technical_indicators = await self._calculate_technical_indicators(historical_data)
                support_levels, resistance_levels = await self._identify_support_resistance(historical_data)
                trend_direction = await self._determine_trend_direction(historical_data, technical_indicators)
                volatility = await self._calculate_volatility(historical_data)
            
            # Construire l'analyse complète
            market_analysis = MarketAnalysis(
                symbol=symbol,
                technical_indicators=technical_indicators,
                support_levels=support_levels,
                resistance_levels=resistance_levels,
                trend_direction=trend_direction,
                volatility=volatility,
                pe_ratio=fundamentals.get('pe_ratio'),
                market_cap=Decimal(str(fundamentals.get('market_cap', 0))) if fundamentals.get('market_cap') else None,
                dividend_yield=fundamentals.get('dividend_yield'),
                sentiment_score=sentiment.get('overall_score', 0.0),
                news_sentiment=sentiment.get('news_sentiment'),
                social_sentiment=sentiment.get('social_sentiment'),
                avg_volume=Decimal(str(volume_data.get('avg_volume', context.volume))),
                volume_trend=volume_data.get('trend', 'stable'),
                liquidity_score=volume_data.get('liquidity_score', 0.8)
            )
            
            logger.info(f"Analyse marché terminée pour {symbol}")
            return market_analysis
            
        except Exception as e:
            logger.error(f"Erreur analyse marché pour {symbol}: {e}")
            
            # Analyse minimale en cas d'erreur
            return MarketAnalysis(
                symbol=symbol,
                trend_direction="neutral",
                volatility=0.2,
                sentiment_score=0.0,
                avg_volume=context.volume,
                volume_trend="stable",
                liquidity_score=0.5
            )
    
    async def _get_historical_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """Récupère les données historiques."""
        try:
            # 1 an de données journalières
            data = await self.openbb_provider.get_historical_data(
                symbol, period="1y", interval="1d"
            )
            
            if data and len(data) > 0:
                df = pd.DataFrame(data)
                # S'assurer que les colonnes nécessaires existent
                required_cols = ['open', 'high', 'low', 'close', 'volume']
                for col in required_cols:
                    if col not in df.columns:
                        logger.warning(f"Colonne manquante {col} pour {symbol}")
                        return None
                
                # Convertir en types numériques
                for col in ['open', 'high', 'low', 'close', 'volume']:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                
                # Supprimer les lignes avec des valeurs manquantes
                df = df.dropna()
                
                return df if len(df) > 20 else None  # Minimum 20 points
            
            return None
            
        except Exception as e:
            logger.error(f"Erreur récupération données historiques pour {symbol}: {e}")
            return None
    
    async def _get_company_fundamentals(self, symbol: str) -> Dict[str, Any]:
        """Récupère les données fondamentales."""
        try:
            company_info = await self.openbb_provider.get_company_info(symbol)
            
            fundamentals = {}
            if company_info:
                # Extraire les métriques fondamentales
                fundamentals['pe_ratio'] = company_info.get('pe_ratio')
                fundamentals['market_cap'] = company_info.get('market_cap')
                fundamentals['dividend_yield'] = company_info.get('dividend_yield')
                fundamentals['book_value'] = company_info.get('book_value')
                fundamentals['earnings_growth'] = company_info.get('earnings_growth')
                fundamentals['revenue_growth'] = company_info.get('revenue_growth')
                fundamentals['debt_to_equity'] = company_info.get('debt_to_equity')
                fundamentals['return_on_equity'] = company_info.get('return_on_equity')
                fundamentals['profit_margin'] = company_info.get('profit_margin')
            
            return fundamentals
            
        except Exception as e:
            logger.error(f"Erreur récupération fondamentaux pour {symbol}: {e}")
            return {}
    
    async def _get_market_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Analyse le sentiment de marché."""
        try:
            # Utiliser le service d'analyse IA pour le sentiment
            sentiment_analysis = await self.analysis_service.analyze_sentiment(
                symbol=symbol,
                timeframe="1D"
            )
            
            return {
                'overall_score': sentiment_analysis.overall_sentiment,
                'news_sentiment': sentiment_analysis.news_sentiment,
                'social_sentiment': sentiment_analysis.social_sentiment,
                'confidence': sentiment_analysis.confidence
            }
            
        except Exception as e:
            logger.error(f"Erreur analyse sentiment pour {symbol}: {e}")
            return {
                'overall_score': 0.0,
                'news_sentiment': 'neutral',
                'social_sentiment': 'neutral',
                'confidence': 0.5
            }
    
    async def _get_volume_data(self, symbol: str) -> Dict[str, Any]:
        """Analyse les données de volume."""
        try:
            # Récupérer les données de volume récentes
            volume_data = await self.openbb_provider.get_historical_data(
                symbol, period="3m", interval="1d"
            )
            
            if not volume_data or len(volume_data) < 20:
                return {'avg_volume': 0, 'trend': 'stable', 'liquidity_score': 0.5}
            
            df = pd.DataFrame(volume_data)
            volumes = pd.to_numeric(df['volume'], errors='coerce').dropna()
            
            if len(volumes) == 0:
                return {'avg_volume': 0, 'trend': 'stable', 'liquidity_score': 0.5}
            
            # Calculer la moyenne et la tendance
            avg_volume = volumes.mean()
            recent_volume = volumes.tail(10).mean()
            
            # Déterminer la tendance
            if recent_volume > avg_volume * 1.2:
                trend = 'increasing'
            elif recent_volume < avg_volume * 0.8:
                trend = 'decreasing'
            else:
                trend = 'stable'
            
            # Score de liquidité basé sur le volume
            liquidity_score = min(1.0, avg_volume / 1000000)  # Normaliser
            
            return {
                'avg_volume': float(avg_volume),
                'trend': trend,
                'liquidity_score': float(liquidity_score)
            }
            
        except Exception as e:
            logger.error(f"Erreur analyse volume pour {symbol}: {e}")
            return {'avg_volume': 0, 'trend': 'stable', 'liquidity_score': 0.5}
    
    async def _calculate_technical_indicators(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calcule les indicateurs techniques."""
        try:
            indicators = {}
            
            # RSI
            indicators['rsi'] = self._calculate_rsi(df['close'], self.rsi_period)
            
            # MACD
            macd_line, signal_line, histogram = self._calculate_macd(
                df['close'], self.macd_fast, self.macd_slow, self.macd_signal
            )
            indicators['macd'] = macd_line
            indicators['macd_signal'] = signal_line
            indicators['macd_histogram'] = histogram
            
            # Bollinger Bands
            upper, middle, lower = self._calculate_bollinger_bands(
                df['close'], self.bb_period, self.bb_std
            )
            indicators['bb_upper'] = upper
            indicators['bb_middle'] = middle
            indicators['bb_lower'] = lower
            indicators['bb_width'] = (upper - lower) / middle if middle != 0 else 0
            
            # Moyennes mobiles
            for period in self.sma_periods:
                indicators[f'sma_{period}'] = df['close'].rolling(window=period).mean().iloc[-1]
            
            for period in self.ema_periods:
                indicators[f'ema_{period}'] = df['close'].ewm(span=period).mean().iloc[-1]
            
            # Stochastic
            stoch_k, stoch_d = self._calculate_stochastic(df, 14, 3)
            indicators['stoch_k'] = stoch_k
            indicators['stoch_d'] = stoch_d
            
            # Average True Range (ATR)
            indicators['atr'] = self._calculate_atr(df, 14)
            
            # Williams %R
            indicators['williams_r'] = self._calculate_williams_r(df, 14)
            
            # Commodity Channel Index (CCI)
            indicators['cci'] = self._calculate_cci(df, 20)
            
            return indicators
            
        except Exception as e:
            logger.error(f"Erreur calcul indicateurs techniques: {e}")
            return {}
    
    def _calculate_rsi(self, prices: pd.Series, period: int) -> float:
        """Calcule le RSI."""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0
        except:
            return 50.0
    
    def _calculate_macd(
        self, 
        prices: pd.Series, 
        fast: int, 
        slow: int, 
        signal: int
    ) -> Tuple[float, float, float]:
        """Calcule le MACD."""
        try:
            exp1 = prices.ewm(span=fast).mean()
            exp2 = prices.ewm(span=slow).mean()
            macd_line = exp1 - exp2
            signal_line = macd_line.ewm(span=signal).mean()
            histogram = macd_line - signal_line
            
            return (
                float(macd_line.iloc[-1]) if not pd.isna(macd_line.iloc[-1]) else 0.0,
                float(signal_line.iloc[-1]) if not pd.isna(signal_line.iloc[-1]) else 0.0,
                float(histogram.iloc[-1]) if not pd.isna(histogram.iloc[-1]) else 0.0
            )
        except:
            return (0.0, 0.0, 0.0)
    
    def _calculate_bollinger_bands(
        self, 
        prices: pd.Series, 
        period: int, 
        std_dev: float
    ) -> Tuple[float, float, float]:
        """Calcule les Bollinger Bands."""
        try:
            sma = prices.rolling(window=period).mean()
            std = prices.rolling(window=period).std()
            upper = sma + (std * std_dev)
            lower = sma - (std * std_dev)
            
            return (
                float(upper.iloc[-1]) if not pd.isna(upper.iloc[-1]) else 0.0,
                float(sma.iloc[-1]) if not pd.isna(sma.iloc[-1]) else 0.0,
                float(lower.iloc[-1]) if not pd.isna(lower.iloc[-1]) else 0.0
            )
        except:
            return (0.0, 0.0, 0.0)
    
    def _calculate_stochastic(
        self, 
        df: pd.DataFrame, 
        k_period: int, 
        d_period: int
    ) -> Tuple[float, float]:
        """Calcule le Stochastic."""
        try:
            low_min = df['low'].rolling(window=k_period).min()
            high_max = df['high'].rolling(window=k_period).max()
            k_percent = 100 * ((df['close'] - low_min) / (high_max - low_min))
            d_percent = k_percent.rolling(window=d_period).mean()
            
            return (
                float(k_percent.iloc[-1]) if not pd.isna(k_percent.iloc[-1]) else 50.0,
                float(d_percent.iloc[-1]) if not pd.isna(d_percent.iloc[-1]) else 50.0
            )
        except:
            return (50.0, 50.0)
    
    def _calculate_atr(self, df: pd.DataFrame, period: int) -> float:
        """Calcule l'Average True Range."""
        try:
            high_low = df['high'] - df['low']
            high_close = np.abs(df['high'] - df['close'].shift())
            low_close = np.abs(df['low'] - df['close'].shift())
            
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = ranges.max(axis=1)
            atr = true_range.rolling(window=period).mean()
            
            return float(atr.iloc[-1]) if not pd.isna(atr.iloc[-1]) else 0.0
        except:
            return 0.0
    
    def _calculate_williams_r(self, df: pd.DataFrame, period: int) -> float:
        """Calcule Williams %R."""
        try:
            highest_high = df['high'].rolling(window=period).max()
            lowest_low = df['low'].rolling(window=period).min()
            williams_r = -100 * ((highest_high - df['close']) / (highest_high - lowest_low))
            
            return float(williams_r.iloc[-1]) if not pd.isna(williams_r.iloc[-1]) else -50.0
        except:
            return -50.0
    
    def _calculate_cci(self, df: pd.DataFrame, period: int) -> float:
        """Calcule le Commodity Channel Index."""
        try:
            typical_price = (df['high'] + df['low'] + df['close']) / 3
            sma = typical_price.rolling(window=period).mean()
            mad = typical_price.rolling(window=period).apply(lambda x: np.abs(x - x.mean()).mean())
            cci = (typical_price - sma) / (0.015 * mad)
            
            return float(cci.iloc[-1]) if not pd.isna(cci.iloc[-1]) else 0.0
        except:
            return 0.0
    
    async def _identify_support_resistance(
        self, 
        df: pd.DataFrame
    ) -> Tuple[List[Decimal], List[Decimal]]:
        """Identifie les niveaux de support et résistance."""
        try:
            # Utiliser les pivots pour identifier les niveaux
            highs = df['high'].values
            lows = df['low'].values
            closes = df['close'].values
            
            # Trouver les pics et creux locaux
            resistance_levels = []
            support_levels = []
            
            # Algorithme simple de détection de pivots
            window = 5
            for i in range(window, len(highs) - window):
                # Résistance (pic local)
                if all(highs[i] >= highs[i-j] for j in range(1, window+1)) and \
                   all(highs[i] >= highs[i+j] for j in range(1, window+1)):
                    resistance_levels.append(Decimal(str(highs[i])))
                
                # Support (creux local)
                if all(lows[i] <= lows[i-j] for j in range(1, window+1)) and \
                   all(lows[i] <= lows[i+j] for j in range(1, window+1)):
                    support_levels.append(Decimal(str(lows[i])))
            
            # Garder seulement les niveaux les plus significatifs
            current_price = Decimal(str(closes[-1]))
            
            # Filtrer et trier
            resistance_levels = sorted(set(r for r in resistance_levels if r > current_price))[:5]
            support_levels = sorted(set(s for s in support_levels if s < current_price), reverse=True)[:5]
            
            return support_levels, resistance_levels
            
        except Exception as e:
            logger.error(f"Erreur identification support/résistance: {e}")
            return [], []
    
    async def _determine_trend_direction(
        self, 
        df: pd.DataFrame, 
        indicators: Dict[str, float]
    ) -> str:
        """Détermine la direction de la tendance."""
        try:
            # Analyser plusieurs facteurs
            trend_signals = []
            
            # 1. Moyennes mobiles
            if 'sma_20' in indicators and 'sma_50' in indicators:
                if indicators['sma_20'] > indicators['sma_50']:
                    trend_signals.append('bullish')
                else:
                    trend_signals.append('bearish')
            
            # 2. Prix vs moyennes mobiles
            current_price = float(df['close'].iloc[-1])
            if 'sma_20' in indicators:
                if current_price > indicators['sma_20']:
                    trend_signals.append('bullish')
                else:
                    trend_signals.append('bearish')
            
            # 3. MACD
            if 'macd' in indicators and 'macd_signal' in indicators:
                if indicators['macd'] > indicators['macd_signal']:
                    trend_signals.append('bullish')
                else:
                    trend_signals.append('bearish')
            
            # 4. Pente des prix (régression linéaire simple)
            prices = df['close'].tail(20).values
            x = np.arange(len(prices))
            slope = np.polyfit(x, prices, 1)[0]
            if slope > 0:
                trend_signals.append('bullish')
            else:
                trend_signals.append('bearish')
            
            # Consensus
            bullish_count = trend_signals.count('bullish')
            bearish_count = trend_signals.count('bearish')
            
            if bullish_count > bearish_count:
                return 'bullish'
            elif bearish_count > bullish_count:
                return 'bearish'
            else:
                return 'neutral'
                
        except Exception as e:
            logger.error(f"Erreur détermination tendance: {e}")
            return 'neutral'
    
    async def _calculate_volatility(self, df: pd.DataFrame) -> float:
        """Calcule la volatilité."""
        try:
            # Volatilité basée sur les returns journaliers
            returns = df['close'].pct_change().dropna()
            volatility = returns.std() * np.sqrt(252)  # Annualisée
            
            return float(volatility) if not pd.isna(volatility) else 0.2
            
        except Exception as e:
            logger.error(f"Erreur calcul volatilité: {e}")
            return 0.2