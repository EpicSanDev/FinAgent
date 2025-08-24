"""
Service pour les indicateurs techniques.

Ce module fournit une interface de haut niveau pour calculer
et récupérer les indicateurs techniques avec cache automatique.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Tuple
from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor

import arrow
import pandas as pd
import numpy as np

from ..models.base import Symbol, TimeFrame
from ..validators.base import ValidationError
from ..models.market_data import MarketDataCollection
from ..models.technical_indicators import (
    BaseIndicator, SimpleIndicator, MovingAverage, RSI, MACD,
    BollingerBands, Stochastic, IndicatorType, IndicatorCollection
)
from ..providers.openbb_provider import OpenBBProvider, OpenBBError
from ..cache import MultiLevelCacheManager, CacheKeys, CacheTags
from ..validators import BaseValidator

logger = logging.getLogger(__name__)


class IndicatorCalculationError(Exception):
    """Erreur lors du calcul d'un indicateur."""
    pass


class InsufficientDataError(Exception):
    """Données insuffisantes pour calculer l'indicateur."""
    pass


class TechnicalIndicatorsService:
    """
    Service pour calculer et gérer les indicateurs techniques.
    
    Fournit une interface unifiée pour calculer tous types d'indicateurs
    avec cache automatique et optimisations de performance.
    """
    
    def __init__(
        self,
        provider: OpenBBProvider,
        cache_manager: Optional[MultiLevelCacheManager] = None,
        max_workers: int = 4
    ):
        """
        Initialise le service d'indicateurs techniques.
        
        Args:
            provider: Provider OpenBB pour récupérer les données
            cache_manager: Gestionnaire de cache (optionnel)
            max_workers: Nombre max de workers pour calculs parallèles
        """
        self.provider = provider
        self.cache_manager = cache_manager
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # Métriques
        self.cache_hits = 0
        self.cache_misses = 0
        self.calculations_count = 0
        self.errors_count = 0
    
    async def calculate_moving_average(
        self,
        symbol: str,
        timeframe: TimeFrame,
        ma_type: IndicatorType,
        period: int,
        end_date: Optional[datetime] = None,
        lookback_days: int = 100
    ) -> MovingAverage:
        """
        Calcule une moyenne mobile.
        
        Args:
            symbol: Symbole financier
            timeframe: Timeframe des données
            ma_type: Type de moyenne (SMA, EMA, WMA)
            period: Période de calcul
            end_date: Date de fin (par défaut: maintenant)
            lookback_days: Jours de données historiques à récupérer
            
        Returns:
            Indicateur de moyenne mobile
            
        Raises:
            ValidationError: Si les paramètres sont invalides
            InsufficientDataError: Si pas assez de données
            IndicatorCalculationError: En cas d'erreur de calcul
        """
        # Validation
        symbol = BaseValidator.normalize_symbol(symbol)
        if period <= 0:
            raise ValidationError("La période doit être positive")
        if ma_type not in [IndicatorType.SMA, IndicatorType.EMA, IndicatorType.WMA]:
            raise ValidationError(f"Type MA invalide: {ma_type}")
        
        # Vérification cache
        cache_key = CacheKeys.indicator(
            symbol, timeframe, f"{ma_type}_{period}"
        )
        if self.cache_manager:
            cached = await self.cache_manager.get(cache_key)
            if cached:
                self.cache_hits += 1
                return cached
        
        try:
            self.cache_misses += 1
            logger.info(f"Calcul {ma_type.upper()}({period}) pour {symbol}")
            
            # Récupération des données
            end_date = end_date or arrow.utcnow().datetime
            start_date = end_date - timedelta(days=lookback_days)
            
            market_data = await self.provider.get_historical_data(
                symbol=symbol,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date
            )
            
            if len(market_data.data) < period:
                raise InsufficientDataError(
                    f"Besoin de {period} points, seulement {len(market_data.data)} disponibles"
                )
            
            # Conversion en DataFrame pour calculs
            df = market_data.to_dataframe()
            if df.empty:
                raise InsufficientDataError("Aucune donnée disponible")
            
            # Calcul selon le type
            if ma_type == IndicatorType.SMA:
                ma_value = self._calculate_sma(df['close'], period)
            elif ma_type == IndicatorType.EMA:
                ma_value = self._calculate_ema(df['close'], period)
            elif ma_type == IndicatorType.WMA:
                ma_value = self._calculate_wma(df['close'], period)
            else:
                raise IndicatorCalculationError(f"Type MA non supporté: {ma_type}")
            
            # Création de l'indicateur
            ma = MovingAverage(
                symbol=Symbol(symbol=symbol),
                timestamp=df.index[-1],
                timeframe=timeframe,
                indicator_type=ma_type,
                period=period,
                value=Decimal(str(ma_value))
            )
            
            # Mise en cache
            if self.cache_manager:
                ttl = self._get_indicator_cache_ttl(timeframe)
                tags = [
                    CacheTags.symbol(symbol),
                    CacheTags.timeframe(str(timeframe)),
                    CacheTags.TECHNICAL_INDICATORS
                ]
                await self.cache_manager.set(cache_key, ma, ttl, tags)
            
            self.calculations_count += 1
            logger.debug(f"{ma_type.upper()}({period}) = {ma_value:.2f}")
            return ma
            
        except Exception as e:
            self.errors_count += 1
            logger.error(f"Erreur calcul {ma_type}({period}) pour {symbol}: {e}")
            if isinstance(e, (ValidationError, InsufficientDataError, IndicatorCalculationError)):
                raise
            raise IndicatorCalculationError(f"Erreur calcul moyenne mobile: {e}")
    
    async def calculate_rsi(
        self,
        symbol: str,
        timeframe: TimeFrame,
        period: int = 14,
        end_date: Optional[datetime] = None,
        lookback_days: int = 100
    ) -> RSI:
        """
        Calcule le RSI (Relative Strength Index).
        
        Args:
            symbol: Symbole financier
            timeframe: Timeframe des données
            period: Période de calcul (défaut: 14)
            end_date: Date de fin
            lookback_days: Jours de données historiques
            
        Returns:
            Indicateur RSI
        """
        symbol = BaseValidator.normalize_symbol(symbol)
        if period <= 1:
            raise ValidationError("Période RSI doit être > 1")
        
        cache_key = CacheKeys.indicator(symbol, timeframe, f"rsi_{period}")
        if self.cache_manager:
            cached = await self.cache_manager.get(cache_key)
            if cached:
                self.cache_hits += 1
                return cached
        
        try:
            self.cache_misses += 1
            logger.info(f"Calcul RSI({period}) pour {symbol}")
            
            # Récupération des données
            end_date = end_date or arrow.utcnow().datetime
            start_date = end_date - timedelta(days=lookback_days)
            
            market_data = await self.provider.get_historical_data(
                symbol=symbol,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date
            )
            
            if len(market_data.data) < period + 1:
                raise InsufficientDataError(
                    f"Besoin de {period + 1} points pour RSI, seulement {len(market_data.data)} disponibles"
                )
            
            df = market_data.to_dataframe()
            rsi_value = await self._calculate_rsi_async(df['close'], period)
            
            rsi = RSI(
                symbol=Symbol(symbol=symbol),
                timestamp=df.index[-1],
                timeframe=timeframe,
                period=period,
                value=Decimal(str(rsi_value))
            )
            
            # Cache
            if self.cache_manager:
                ttl = self._get_indicator_cache_ttl(timeframe)
                tags = [CacheTags.symbol(symbol), CacheTags.TECHNICAL_INDICATORS]
                await self.cache_manager.set(cache_key, rsi, ttl, tags)
            
            self.calculations_count += 1
            logger.debug(f"RSI({period}) = {rsi_value:.2f}")
            return rsi
            
        except Exception as e:
            self.errors_count += 1
            logger.error(f"Erreur calcul RSI pour {symbol}: {e}")
            if isinstance(e, (ValidationError, InsufficientDataError)):
                raise
            raise IndicatorCalculationError(f"Erreur calcul RSI: {e}")
    
    async def calculate_macd(
        self,
        symbol: str,
        timeframe: TimeFrame,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
        end_date: Optional[datetime] = None,
        lookback_days: int = 100
    ) -> MACD:
        """
        Calcule le MACD (Moving Average Convergence Divergence).
        
        Args:
            symbol: Symbole financier
            timeframe: Timeframe des données
            fast_period: Période EMA rapide (défaut: 12)
            slow_period: Période EMA lente (défaut: 26)
            signal_period: Période EMA signal (défaut: 9)
            end_date: Date de fin
            lookback_days: Jours de données historiques
            
        Returns:
            Indicateur MACD
        """
        symbol = BaseValidator.normalize_symbol(symbol)
        if fast_period >= slow_period:
            raise ValidationError("Période rapide doit être < période lente")
        
        cache_key = CacheKeys.indicator(
            symbol, timeframe, f"macd_{fast_period}_{slow_period}_{signal_period}"
        )
        if self.cache_manager:
            cached = await self.cache_manager.get(cache_key)
            if cached:
                self.cache_hits += 1
                return cached
        
        try:
            self.cache_misses += 1
            logger.info(f"Calcul MACD({fast_period},{slow_period},{signal_period}) pour {symbol}")
            
            # Récupération des données
            end_date = end_date or arrow.utcnow().datetime
            start_date = end_date - timedelta(days=lookback_days)
            
            market_data = await self.provider.get_historical_data(
                symbol=symbol,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date
            )
            
            min_required = max(slow_period, signal_period) + 10
            if len(market_data.data) < min_required:
                raise InsufficientDataError(
                    f"Besoin de {min_required} points pour MACD"
                )
            
            df = market_data.to_dataframe()
            macd_data = await self._calculate_macd_async(
                df['close'], fast_period, slow_period, signal_period
            )
            
            macd = MACD(
                symbol=Symbol(symbol=symbol),
                timestamp=df.index[-1],
                timeframe=timeframe,
                period=slow_period,  # Période de référence
                macd_line=Decimal(str(macd_data['macd'])),
                signal_line=Decimal(str(macd_data['signal'])),
                histogram=Decimal(str(macd_data['histogram'])),
                fast_period=fast_period,
                slow_period=slow_period,
                signal_period=signal_period
            )
            
            # Cache
            if self.cache_manager:
                ttl = self._get_indicator_cache_ttl(timeframe)
                tags = [CacheTags.symbol(symbol), CacheTags.TECHNICAL_INDICATORS]
                await self.cache_manager.set(cache_key, macd, ttl, tags)
            
            self.calculations_count += 1
            logger.debug(f"MACD = {macd_data['macd']:.4f}")
            return macd
            
        except Exception as e:
            self.errors_count += 1
            logger.error(f"Erreur calcul MACD pour {symbol}: {e}")
            if isinstance(e, (ValidationError, InsufficientDataError)):
                raise
            raise IndicatorCalculationError(f"Erreur calcul MACD: {e}")
    
    async def calculate_bollinger_bands(
        self,
        symbol: str,
        timeframe: TimeFrame,
        period: int = 20,
        std_multiplier: float = 2.0,
        end_date: Optional[datetime] = None,
        lookback_days: int = 100
    ) -> BollingerBands:
        """
        Calcule les Bandes de Bollinger.
        
        Args:
            symbol: Symbole financier
            timeframe: Timeframe des données
            period: Période SMA (défaut: 20)
            std_multiplier: Multiplicateur d'écart-type (défaut: 2.0)
            end_date: Date de fin
            lookback_days: Jours de données historiques
            
        Returns:
            Indicateur Bollinger Bands
        """
        symbol = BaseValidator.normalize_symbol(symbol)
        if period <= 1:
            raise ValidationError("Période doit être > 1")
        if std_multiplier <= 0:
            raise ValidationError("Multiplicateur doit être > 0")
        
        cache_key = CacheKeys.indicator(
            symbol, timeframe, f"bollinger_{period}_{std_multiplier}"
        )
        if self.cache_manager:
            cached = await self.cache_manager.get(cache_key)
            if cached:
                self.cache_hits += 1
                return cached
        
        try:
            self.cache_misses += 1
            logger.info(f"Calcul Bollinger({period},{std_multiplier}) pour {symbol}")
            
            # Récupération des données
            end_date = end_date or arrow.utcnow().datetime
            start_date = end_date - timedelta(days=lookback_days)
            
            market_data = await self.provider.get_historical_data(
                symbol=symbol,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date
            )
            
            if len(market_data.data) < period:
                raise InsufficientDataError(
                    f"Besoin de {period} points pour Bollinger"
                )
            
            df = market_data.to_dataframe()
            bb_data = await self._calculate_bollinger_async(
                df['close'], period, std_multiplier
            )
            
            bollinger = BollingerBands(
                symbol=Symbol(symbol=symbol),
                timestamp=df.index[-1],
                timeframe=timeframe,
                period=period,
                middle_band=Decimal(str(bb_data['middle'])),
                upper_band=Decimal(str(bb_data['upper'])),
                lower_band=Decimal(str(bb_data['lower'])),
                std_dev=Decimal(str(bb_data['std_dev'])),
                std_multiplier=Decimal(str(std_multiplier))
            )
            
            # Cache
            if self.cache_manager:
                ttl = self._get_indicator_cache_ttl(timeframe)
                tags = [CacheTags.symbol(symbol), CacheTags.TECHNICAL_INDICATORS]
                await self.cache_manager.set(cache_key, bollinger, ttl, tags)
            
            self.calculations_count += 1
            logger.debug(f"Bollinger Upper:{bb_data['upper']:.2f} Lower:{bb_data['lower']:.2f}")
            return bollinger
            
        except Exception as e:
            self.errors_count += 1
            logger.error(f"Erreur calcul Bollinger pour {symbol}: {e}")
            if isinstance(e, (ValidationError, InsufficientDataError)):
                raise
            raise IndicatorCalculationError(f"Erreur calcul Bollinger: {e}")
    
    async def calculate_stochastic(
        self,
        symbol: str,
        timeframe: TimeFrame,
        k_period: int = 14,
        d_period: int = 3,
        end_date: Optional[datetime] = None,
        lookback_days: int = 100
    ) -> Stochastic:
        """
        Calcule l'oscillateur Stochastique.
        
        Args:
            symbol: Symbole financier
            timeframe: Timeframe des données
            k_period: Période pour %K (défaut: 14)
            d_period: Période pour %D (défaut: 3)
            end_date: Date de fin
            lookback_days: Jours de données historiques
            
        Returns:
            Indicateur Stochastic
        """
        symbol = BaseValidator.normalize_symbol(symbol)
        if k_period <= 0 or d_period <= 0:
            raise ValidationError("Périodes doivent être > 0")
        
        cache_key = CacheKeys.indicator(
            symbol, timeframe, f"stoch_{k_period}_{d_period}"
        )
        if self.cache_manager:
            cached = await self.cache_manager.get(cache_key)
            if cached:
                self.cache_hits += 1
                return cached
        
        try:
            self.cache_misses += 1
            logger.info(f"Calcul Stochastic({k_period},{d_period}) pour {symbol}")
            
            # Récupération des données
            end_date = end_date or arrow.utcnow().datetime
            start_date = end_date - timedelta(days=lookback_days)
            
            market_data = await self.provider.get_historical_data(
                symbol=symbol,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date
            )
            
            min_required = k_period + d_period
            if len(market_data.data) < min_required:
                raise InsufficientDataError(
                    f"Besoin de {min_required} points pour Stochastic"
                )
            
            df = market_data.to_dataframe()
            stoch_data = await self._calculate_stochastic_async(
                df['high'], df['low'], df['close'], k_period, d_period
            )
            
            stochastic = Stochastic(
                symbol=Symbol(symbol=symbol),
                timestamp=df.index[-1],
                timeframe=timeframe,
                period=k_period,
                k_percent=Decimal(str(stoch_data['k'])),
                d_percent=Decimal(str(stoch_data['d'])),
                k_period=k_period,
                d_period=d_period
            )
            
            # Cache
            if self.cache_manager:
                ttl = self._get_indicator_cache_ttl(timeframe)
                tags = [CacheTags.symbol(symbol), CacheTags.TECHNICAL_INDICATORS]
                await self.cache_manager.set(cache_key, stochastic, ttl, tags)
            
            self.calculations_count += 1
            logger.debug(f"Stochastic %K:{stoch_data['k']:.1f} %D:{stoch_data['d']:.1f}")
            return stochastic
            
        except Exception as e:
            self.errors_count += 1
            logger.error(f"Erreur calcul Stochastic pour {symbol}: {e}")
            if isinstance(e, (ValidationError, InsufficientDataError)):
                raise
            raise IndicatorCalculationError(f"Erreur calcul Stochastic: {e}")
    
    async def calculate_indicator_collection(
        self,
        symbol: str,
        timeframe: TimeFrame,
        indicators: List[Dict[str, Any]],
        end_date: Optional[datetime] = None,
        lookback_days: int = 100
    ) -> IndicatorCollection:
        """
        Calcule une collection d'indicateurs en parallèle.
        
        Args:
            symbol: Symbole financier
            timeframe: Timeframe des données
            indicators: Liste des config d'indicateurs à calculer
            end_date: Date de fin
            lookback_days: Jours de données historiques
            
        Returns:
            Collection d'indicateurs
            
        Example:
            indicators = [
                {'type': 'sma', 'period': 20},
                {'type': 'rsi', 'period': 14},
                {'type': 'macd', 'fast': 12, 'slow': 26, 'signal': 9}
            ]
        """
        symbol = BaseValidator.normalize_symbol(symbol)
        
        logger.info(f"Calcul collection de {len(indicators)} indicateurs pour {symbol}")
        
        collection = IndicatorCollection(
            symbol=Symbol(symbol=symbol),
            timeframe=timeframe,
            timestamp=end_date or arrow.utcnow().datetime
        )
        
        # Calculs en parallèle
        tasks = []
        for i, config in enumerate(indicators):
            task_name = f"{config.get('type', 'unknown')}_{i}"
            task = self._calculate_single_indicator(
                symbol, timeframe, config, end_date, lookback_days, task_name
            )
            tasks.append(task)
        
        # Attendre tous les calculs
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Traiter les résultats
        successful = 0
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Erreur indicateur {i}: {result}")
                continue
            
            indicator_name, indicator = result
            collection.add_indicator(indicator_name, indicator)
            successful += 1
        
        logger.info(f"Collection calculée: {successful}/{len(indicators)} indicateurs")
        return collection
    
    async def _calculate_single_indicator(
        self,
        symbol: str,
        timeframe: TimeFrame,
        config: Dict[str, Any],
        end_date: Optional[datetime],
        lookback_days: int,
        task_name: str
    ) -> Tuple[str, BaseIndicator]:
        """Calcule un seul indicateur selon la configuration."""
        indicator_type = config.get('type', '').lower()
        
        try:
            if indicator_type == 'sma':
                indicator = await self.calculate_moving_average(
                    symbol, timeframe, IndicatorType.SMA,
                    config.get('period', 20), end_date, lookback_days
                )
                return f"SMA_{config.get('period', 20)}", indicator
                
            elif indicator_type == 'ema':
                indicator = await self.calculate_moving_average(
                    symbol, timeframe, IndicatorType.EMA,
                    config.get('period', 20), end_date, lookback_days
                )
                return f"EMA_{config.get('period', 20)}", indicator
                
            elif indicator_type == 'rsi':
                indicator = await self.calculate_rsi(
                    symbol, timeframe, config.get('period', 14),
                    end_date, lookback_days
                )
                return f"RSI_{config.get('period', 14)}", indicator
                
            elif indicator_type == 'macd':
                indicator = await self.calculate_macd(
                    symbol, timeframe,
                    config.get('fast', 12),
                    config.get('slow', 26),
                    config.get('signal', 9),
                    end_date, lookback_days
                )
                return "MACD", indicator
                
            elif indicator_type == 'bollinger':
                indicator = await self.calculate_bollinger_bands(
                    symbol, timeframe,
                    config.get('period', 20),
                    config.get('std_multiplier', 2.0),
                    end_date, lookback_days
                )
                return "BOLLINGER", indicator
                
            elif indicator_type == 'stochastic':
                indicator = await self.calculate_stochastic(
                    symbol, timeframe,
                    config.get('k_period', 14),
                    config.get('d_period', 3),
                    end_date, lookback_days
                )
                return "STOCHASTIC", indicator
                
            else:
                raise IndicatorCalculationError(f"Type d'indicateur non supporté: {indicator_type}")
                
        except Exception as e:
            logger.error(f"Erreur calcul {task_name}: {e}")
            raise
    
    # Méthodes de calcul async
    
    async def _calculate_rsi_async(self, prices: pd.Series, period: int) -> float:
        """Calcule le RSI de manière asynchrone."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, self._calculate_rsi, prices, period
        )
    
    async def _calculate_macd_async(
        self, prices: pd.Series, fast: int, slow: int, signal: int
    ) -> Dict[str, float]:
        """Calcule le MACD de manière asynchrone."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, self._calculate_macd, prices, fast, slow, signal
        )
    
    async def _calculate_bollinger_async(
        self, prices: pd.Series, period: int, std_mult: float
    ) -> Dict[str, float]:
        """Calcule les Bollinger Bands de manière asynchrone."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, self._calculate_bollinger, prices, period, std_mult
        )
    
    async def _calculate_stochastic_async(
        self, high: pd.Series, low: pd.Series, close: pd.Series,
        k_period: int, d_period: int
    ) -> Dict[str, float]:
        """Calcule le Stochastic de manière asynchrone."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, self._calculate_stochastic, high, low, close, k_period, d_period
        )
    
    # Méthodes de calcul synchrones
    
    def _calculate_sma(self, prices: pd.Series, period: int) -> float:
        """Calcule la Simple Moving Average."""
        if len(prices) < period:
            raise InsufficientDataError(f"Besoin de {period} valeurs pour SMA")
        return float(prices.tail(period).mean())
    
    def _calculate_ema(self, prices: pd.Series, period: int) -> float:
        """Calcule l'Exponential Moving Average."""
        if len(prices) < period:
            raise InsufficientDataError(f"Besoin de {period} valeurs pour EMA")
        return float(prices.ewm(span=period).mean().iloc[-1])
    
    def _calculate_wma(self, prices: pd.Series, period: int) -> float:
        """Calcule la Weighted Moving Average."""
        if len(prices) < period:
            raise InsufficientDataError(f"Besoin de {period} valeurs pour WMA")
        
        weights = np.arange(1, period + 1)
        values = prices.tail(period).values
        return float(np.sum(weights * values) / np.sum(weights))
    
    def _calculate_rsi(self, prices: pd.Series, period: int) -> float:
        """Calcule le RSI."""
        if len(prices) < period + 1:
            raise InsufficientDataError(f"Besoin de {period + 1} valeurs pour RSI")
        
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return float(rsi.iloc[-1])
    
    def _calculate_macd(
        self, prices: pd.Series, fast: int, slow: int, signal: int
    ) -> Dict[str, float]:
        """Calcule le MACD."""
        if len(prices) < slow:
            raise InsufficientDataError(f"Besoin de {slow} valeurs pour MACD")
        
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line
        
        return {
            'macd': float(macd_line.iloc[-1]),
            'signal': float(signal_line.iloc[-1]),
            'histogram': float(histogram.iloc[-1])
        }
    
    def _calculate_bollinger(
        self, prices: pd.Series, period: int, std_mult: float
    ) -> Dict[str, float]:
        """Calcule les Bandes de Bollinger."""
        if len(prices) < period:
            raise InsufficientDataError(f"Besoin de {period} valeurs pour Bollinger")
        
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        
        upper = sma + (std * std_mult)
        lower = sma - (std * std_mult)
        
        return {
            'upper': float(upper.iloc[-1]),
            'middle': float(sma.iloc[-1]),
            'lower': float(lower.iloc[-1]),
            'std_dev': float(std.iloc[-1])
        }
    
    def _calculate_stochastic(
        self, high: pd.Series, low: pd.Series, close: pd.Series,
        k_period: int, d_period: int
    ) -> Dict[str, float]:
        """Calcule l'oscillateur Stochastique."""
        if len(close) < k_period:
            raise InsufficientDataError(f"Besoin de {k_period} valeurs pour Stochastic")
        
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()
        
        k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        d_percent = k_percent.rolling(window=d_period).mean()
        
        return {
            'k': float(k_percent.iloc[-1]),
            'd': float(d_percent.iloc[-1])
        }
    
    def _get_indicator_cache_ttl(self, timeframe: TimeFrame) -> int:
        """Retourne le TTL de cache approprié pour les indicateurs."""
        ttl_mapping = {
            TimeFrame.MINUTE_1: 60,       # 1 minute
            TimeFrame.MINUTE_5: 300,      # 5 minutes
            TimeFrame.MINUTE_15: 900,     # 15 minutes
            TimeFrame.MINUTE_30: 1800,    # 30 minutes
            TimeFrame.HOUR_1: 3600,       # 1 heure
            TimeFrame.HOUR_4: 14400,      # 4 heures
            TimeFrame.DAY_1: 86400,       # 24 heures
            TimeFrame.WEEK_1: 604800,     # 7 jours
            TimeFrame.MONTH_1: 2592000    # 30 jours
        }
        return ttl_mapping.get(timeframe, 3600)
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Retourne le statut de santé du service."""
        return {
            'service': 'TechnicalIndicatorsService',
            'status': 'healthy',
            'metrics': {
                'cache_hits': self.cache_hits,
                'cache_misses': self.cache_misses,
                'hit_rate': self.cache_hits / max(1, self.cache_hits + self.cache_misses),
                'calculations_count': self.calculations_count,
                'errors_count': self.errors_count,
                'max_workers': self.max_workers
            },
            'provider_status': await self.provider.get_health_status()
        }
    
    async def close(self):
        """Ferme le service et libère les ressources."""
        logger.info("Fermeture du service d'indicateurs techniques")
        if hasattr(self.executor, 'shutdown'):
            self.executor.shutdown(wait=True)