"""
Service de données de marché.

Ce module fournit une interface de haut niveau pour accéder
aux données de marché via OpenBB avec gestion automatique
du cache, validation et optimisations.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from decimal import Decimal

import arrow

from ..models.base import Symbol, TimeFrame
from ..models.market_data import OHLCV, QuoteData, Price, MarketDataCollection
from ..providers import OpenBBProvider, OpenBBError, DataNotFoundError
from ..validators import BaseValidator, ValidationError
from ..cache import MultiLevelCacheManager, CacheKeys, CacheTags

logger = logging.getLogger(__name__)


class MarketDataServiceError(Exception):
    """Exception du service de données de marché."""
    
    def __init__(self, message: str, symbol: str = "", cause: Optional[Exception] = None):
        self.message = message
        self.symbol = symbol
        self.cause = cause
        super().__init__(message)


class MarketDataService:
    """
    Service principal pour l'accès aux données de marché.
    
    Fournit une interface simplifiée pour récupérer des données
    de marché avec gestion automatique du cache, retry et validation.
    """
    
    def __init__(
        self,
        provider: OpenBBProvider,
        cache_manager: Optional[MultiLevelCacheManager] = None,
        default_limit: int = 100
    ):
        """
        Initialise le service de données de marché.
        
        Args:
            provider: Provider OpenBB
            cache_manager: Gestionnaire de cache (optionnel)
            default_limit: Limite par défaut de données
        """
        self.provider = provider
        self.cache_manager = cache_manager
        self.default_limit = default_limit
        
        # Métriques du service
        self.requests_count = 0
        self.cache_hits = 0
        self.errors_count = 0
        
        logger.info("Service de données de marché initialisé")

    async def get_current_price(self, symbol: str) -> Price:
        """
        Récupère le prix actuel d'un symbole.
        
        Args:
            symbol: Symbole financier
            
        Returns:
            Prix actuel
            
        Raises:
            ValidationError: Si le symbole est invalide
            MarketDataServiceError: En cas d'erreur du service
        """
        try:
            symbol = BaseValidator.normalize_symbol(symbol)
            self.requests_count += 1
            
            logger.debug(f"Récupération prix actuel: {symbol}")
            
            quote = await self.provider.get_quote(symbol)
            
            logger.debug(f"Prix actuel {symbol}: {quote.last_price}")
            return quote.last_price
            
        except ValidationError:
            raise
        except OpenBBError as e:
            self.errors_count += 1
            raise MarketDataServiceError(
                f"Erreur lors de la récupération du prix pour {symbol}: {e.message}",
                symbol=symbol,
                cause=e
            )
        except Exception as e:
            self.errors_count += 1
            raise MarketDataServiceError(
                f"Erreur inattendue lors de la récupération du prix pour {symbol}: {e}",
                symbol=symbol,
                cause=e
            )

    async def get_quote(self, symbol: str) -> QuoteData:
        """
        Récupère la cotation complète d'un symbole.
        
        Args:
            symbol: Symbole financier
            
        Returns:
            Données de cotation complètes
        """
        try:
            symbol = BaseValidator.normalize_symbol(symbol)
            self.requests_count += 1
            
            logger.debug(f"Récupération cotation: {symbol}")
            
            quote = await self.provider.get_quote(symbol)
            
            logger.debug(f"Cotation {symbol}: {quote}")
            return quote
            
        except ValidationError:
            raise
        except OpenBBError as e:
            self.errors_count += 1
            raise MarketDataServiceError(
                f"Erreur lors de la récupération de la cotation pour {symbol}: {e.message}",
                symbol=symbol,
                cause=e
            )
        except Exception as e:
            self.errors_count += 1
            raise MarketDataServiceError(
                f"Erreur inattendue lors de la récupération de la cotation pour {symbol}: {e}",
                symbol=symbol,
                cause=e
            )

    async def get_historical_data(
        self,
        symbol: str,
        timeframe: TimeFrame = TimeFrame.DAY_1,
        days_back: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> MarketDataCollection:
        """
        Récupère les données historiques d'un symbole.
        
        Args:
            symbol: Symbole financier
            timeframe: Timeframe des données
            days_back: Nombre de jours en arrière (alternative aux dates)
            start_date: Date de début
            end_date: Date de fin
            limit: Limite de données
            
        Returns:
            Collection de données historiques
        """
        try:
            symbol = BaseValidator.normalize_symbol(symbol)
            timeframe = BaseValidator.normalize_timeframe(timeframe)
            self.requests_count += 1
            
            # Calcul des dates si days_back spécifié
            if days_back is not None:
                end_date = arrow.utcnow().datetime
                start_date = end_date - timedelta(days=days_back)
            
            # Validation des dates
            if start_date and end_date:
                if not BaseValidator.is_valid_date_range(start_date, end_date):
                    raise ValidationError("Plage de dates invalide")
            
            # Limite par défaut
            if limit is None:
                limit = self.default_limit
            
            logger.info(f"Récupération données historiques: {symbol} {timeframe.value}")
            
            collection = await self.provider.get_historical_data(
                symbol=symbol,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date,
                limit=limit
            )
            
            logger.info(f"Récupéré {len(collection.data)} points pour {symbol}")
            return collection
            
        except ValidationError:
            raise
        except OpenBBError as e:
            self.errors_count += 1
            raise MarketDataServiceError(
                f"Erreur lors de la récupération des données historiques pour {symbol}: {e.message}",
                symbol=symbol,
                cause=e
            )
        except Exception as e:
            self.errors_count += 1
            raise MarketDataServiceError(
                f"Erreur inattendue lors de la récupération des données historiques pour {symbol}: {e}",
                symbol=symbol,
                cause=e
            )

    async def get_intraday_data(
        self,
        symbol: str,
        timeframe: TimeFrame = TimeFrame.MINUTE_5,
        hours_back: int = 6
    ) -> MarketDataCollection:
        """
        Récupère les données intraday d'un symbole.
        
        Args:
            symbol: Symbole financier
            timeframe: Timeframe intraday
            hours_back: Nombre d'heures en arrière
            
        Returns:
            Collection de données intraday
        """
        try:
            symbol = BaseValidator.normalize_symbol(symbol)
            timeframe = BaseValidator.normalize_timeframe(timeframe)
            
            # Validation du timeframe intraday
            intraday_timeframes = [
                TimeFrame.MINUTE_1, TimeFrame.MINUTE_5, 
                TimeFrame.MINUTE_15, TimeFrame.MINUTE_30,
                TimeFrame.HOUR_1, TimeFrame.HOUR_4
            ]
            
            if timeframe not in intraday_timeframes:
                raise ValidationError(f"Timeframe {timeframe.value} n'est pas intraday")
            
            # Calcul des dates
            end_date = arrow.utcnow().datetime
            start_date = end_date - timedelta(hours=hours_back)
            
            logger.info(f"Récupération données intraday: {symbol} {timeframe.value} ({hours_back}h)")
            
            return await self.get_historical_data(
                symbol=symbol,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date
            )
            
        except ValidationError:
            raise
        except MarketDataServiceError:
            raise
        except Exception as e:
            self.errors_count += 1
            raise MarketDataServiceError(
                f"Erreur lors de la récupération des données intraday pour {symbol}: {e}",
                symbol=symbol,
                cause=e
            )

    async def get_multiple_quotes(self, symbols: List[str]) -> Dict[str, QuoteData]:
        """
        Récupère les cotations de plusieurs symboles en parallèle.
        
        Args:
            symbols: Liste de symboles
            
        Returns:
            Dictionnaire symbole -> cotation
        """
        try:
            symbols = BaseValidator.validate_symbols_list(symbols)
            
            logger.info(f"Récupération cotations multiples: {len(symbols)} symboles")
            
            # Exécution en parallèle
            tasks = [self.get_quote(symbol) for symbol in symbols]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Traitement des résultats
            quotes = {}
            errors = {}
            
            for symbol, result in zip(symbols, results):
                if isinstance(result, Exception):
                    errors[symbol] = result
                    logger.warning(f"Erreur pour {symbol}: {result}")
                else:
                    quotes[symbol] = result
            
            logger.info(f"Récupéré {len(quotes)} cotations, {len(errors)} erreurs")
            
            if errors and not quotes:
                # Toutes les requêtes ont échoué
                raise MarketDataServiceError(f"Échec de toutes les cotations: {list(errors.keys())}")
            
            return quotes
            
        except ValidationError:
            raise
        except MarketDataServiceError:
            raise
        except Exception as e:
            self.errors_count += 1
            raise MarketDataServiceError(f"Erreur lors de la récupération multiple: {e}", cause=e)

    async def get_multiple_historical_data(
        self,
        symbols: List[str],
        timeframe: TimeFrame = TimeFrame.DAY_1,
        days_back: int = 30
    ) -> Dict[str, MarketDataCollection]:
        """
        Récupère les données historiques de plusieurs symboles.
        
        Args:
            symbols: Liste de symboles
            timeframe: Timeframe des données
            days_back: Nombre de jours en arrière
            
        Returns:
            Dictionnaire symbole -> collection de données
        """
        try:
            symbols = BaseValidator.validate_symbols_list(symbols)
            timeframe = BaseValidator.normalize_timeframe(timeframe)
            
            logger.info(f"Récupération données historiques multiples: {len(symbols)} symboles")
            
            # Exécution en parallèle avec limitation de concurrence
            semaphore = asyncio.Semaphore(5)  # Max 5 requêtes simultanées
            
            async def get_data_with_semaphore(symbol):
                async with semaphore:
                    return await self.get_historical_data(
                        symbol=symbol,
                        timeframe=timeframe,
                        days_back=days_back
                    )
            
            tasks = [get_data_with_semaphore(symbol) for symbol in symbols]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Traitement des résultats
            data_collections = {}
            errors = {}
            
            for symbol, result in zip(symbols, results):
                if isinstance(result, Exception):
                    errors[symbol] = result
                    logger.warning(f"Erreur données historiques pour {symbol}: {result}")
                else:
                    data_collections[symbol] = result
            
            logger.info(f"Récupéré données pour {len(data_collections)} symboles, {len(errors)} erreurs")
            
            return data_collections
            
        except ValidationError:
            raise
        except MarketDataServiceError:
            raise
        except Exception as e:
            self.errors_count += 1
            raise MarketDataServiceError(f"Erreur lors de la récupération multiple: {e}", cause=e)

    async def search_symbols(self, query: str, limit: int = 10) -> List[Symbol]:
        """
        Recherche des symboles financiers.
        
        Args:
            query: Terme de recherche
            limit: Nombre maximum de résultats
            
        Returns:
            Liste des symboles trouvés
        """
        try:
            if not query or len(query.strip()) < 1:
                raise ValidationError("Query de recherche requise")
            
            if limit <= 0 or limit > 100:
                raise ValidationError("Limite doit être entre 1 et 100")
            
            logger.debug(f"Recherche symboles: '{query}'")
            
            symbols = await self.provider.search_symbols(query.strip(), limit)
            
            logger.debug(f"Trouvé {len(symbols)} symboles pour '{query}'")
            return symbols
            
        except ValidationError:
            raise
        except OpenBBError as e:
            self.errors_count += 1
            raise MarketDataServiceError(
                f"Erreur lors de la recherche '{query}': {e.message}",
                cause=e
            )
        except Exception as e:
            self.errors_count += 1
            raise MarketDataServiceError(f"Erreur inattendue lors de la recherche '{query}': {e}", cause=e)

    async def get_price_change(
        self,
        symbol: str,
        timeframe: TimeFrame = TimeFrame.DAY_1,
        periods: int = 1
    ) -> Dict[str, Decimal]:
        """
        Calcule les variations de prix sur une période.
        
        Args:
            symbol: Symbole financier
            timeframe: Timeframe de référence
            periods: Nombre de périodes pour calculer la variation
            
        Returns:
            Dictionnaire avec les métriques de variation
        """
        try:
            symbol = BaseValidator.normalize_symbol(symbol)
            timeframe = BaseValidator.normalize_timeframe(timeframe)
            
            if periods <= 0:
                raise ValidationError("Nombre de périodes doit être positif")
            
            logger.debug(f"Calcul variation prix: {symbol} sur {periods} {timeframe.value}")
            
            # Récupération des données récentes
            collection = await self.get_historical_data(
                symbol=symbol,
                timeframe=timeframe,
                limit=periods + 1
            )
            
            if len(collection.data) < 2:
                raise MarketDataServiceError(f"Pas assez de données pour calculer la variation de {symbol}")
            
            # Calcul des variations
            latest = collection.data[-1]
            previous = collection.data[-(periods + 1)]
            
            change_absolute = latest.close - previous.close
            change_percent = (change_absolute / previous.close) * 100
            
            # Variation intraday
            intraday_change = latest.close - latest.open
            intraday_percent = (intraday_change / latest.open) * 100
            
            return {
                'current_price': latest.close,
                'previous_price': previous.close,
                'change_absolute': change_absolute,
                'change_percent': change_percent,
                'intraday_change': intraday_change,
                'intraday_percent': intraday_percent,
                'high': latest.high,
                'low': latest.low,
                'volume': latest.volume or 0
            }
            
        except ValidationError:
            raise
        except MarketDataServiceError:
            raise
        except Exception as e:
            self.errors_count += 1
            raise MarketDataServiceError(
                f"Erreur lors du calcul de variation pour {symbol}: {e}",
                symbol=symbol,
                cause=e
            )

    async def invalidate_cache(self, symbol: str) -> int:
        """
        Invalide le cache pour un symbole donné.
        
        Args:
            symbol: Symbole à invalider
            
        Returns:
            Nombre d'entrées supprimées du cache
        """
        try:
            symbol = BaseValidator.normalize_symbol(symbol)
            
            if self.cache_manager:
                deleted_count = await self.cache_manager.invalidate_by_tag(CacheTags.symbol(symbol))
                logger.info(f"Cache invalidé pour {symbol}: {deleted_count} entrées")
                return deleted_count
            
            return 0
            
        except Exception as e:
            logger.error(f"Erreur lors de l'invalidation du cache pour {symbol}: {e}")
            return 0

    async def get_market_status(self, symbol: str) -> Dict[str, Any]:
        """
        Récupère le statut du marché pour un symbole.
        
        Args:
            symbol: Symbole financier
            
        Returns:
            Information sur le statut du marché
        """
        try:
            symbol = BaseValidator.normalize_symbol(symbol)
            
            # Récupération de la cotation pour obtenir le statut
            quote = await self.get_quote(symbol)
            
            # Analyse du timestamp pour déterminer si le marché est ouvert
            now = arrow.utcnow()
            quote_time = arrow.get(quote.created_at)
            age_minutes = (now - quote_time).total_seconds() / 60
            
            # Si les données sont très récentes (< 5 min), marché probablement ouvert
            is_likely_open = age_minutes < 5
            
            return {
                'symbol': symbol,
                'market_status': quote.market_status.value,
                'last_update': quote.created_at.isoformat(),
                'age_minutes': age_minutes,
                'is_likely_open': is_likely_open,
                'last_price': float(quote.last_price.value)
            }
            
        except Exception as e:
            self.errors_count += 1
            raise MarketDataServiceError(
                f"Erreur lors de la récupération du statut de marché pour {symbol}: {e}",
                symbol=symbol,
                cause=e
            )

    def get_statistics(self) -> Dict[str, Any]:
        """
        Retourne les statistiques du service.
        
        Returns:
            Dictionnaire avec les métriques du service
        """
        success_rate = ((self.requests_count - self.errors_count) / 
                       self.requests_count) if self.requests_count > 0 else 0
        
        cache_hit_rate = self.cache_hits / self.requests_count if self.requests_count > 0 else 0
        
        return {
            'requests_count': self.requests_count,
            'errors_count': self.errors_count,
            'success_rate': success_rate,
            'cache_hits': self.cache_hits,
            'cache_hit_rate': cache_hit_rate,
            'provider_stats': self.provider.get_statistics()
        }

    async def health_check(self) -> Dict[str, Any]:
        """
        Vérifie l'état de santé du service.
        
        Returns:
            Rapport de santé du service
        """
        health_status = {
            'status': 'unknown',
            'timestamp': arrow.utcnow().isoformat(),
            'service_stats': self.get_statistics()
        }
        
        try:
            # Test basique avec un symbole fiable
            test_symbol = "AAPL"
            price = await self.get_current_price(test_symbol)
            
            if price and price.value > 0:
                health_status['status'] = 'healthy'
                health_status['test_result'] = {
                    'symbol': test_symbol,
                    'price': float(price.value),
                    'timestamp': price.timestamp.isoformat()
                }
            else:
                health_status['status'] = 'degraded'
                
        except Exception as e:
            health_status['status'] = 'unhealthy'
            health_status['error'] = str(e)
        
        # Ajout du statut du provider
        try:
            provider_health = await self.provider.health_check()
            health_status['provider_health'] = provider_health
        except Exception as e:
            health_status['provider_error'] = str(e)
        
        return health_status

    async def close(self) -> None:
        """Ferme le service et nettoie les ressources."""
        logger.info("Fermeture du service de données de marché")
        
        # Affichage des statistiques finales
        stats = self.get_statistics()
        logger.info(f"Statistiques finales du service: {stats}")
        
        # Fermeture du provider
        if self.provider:
            await self.provider.close()