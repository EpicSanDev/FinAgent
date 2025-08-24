"""
Test d'intégration pour le système de données financières OpenBB.

Ce module démontre l'utilisation complète de l'intégration OpenBB
avec tous les services et composants.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

import arrow

from .models.base import Symbol, TimeFrame
from .models.technical_indicators import IndicatorType
from .models.news import NewsCategory

from .validators import BaseValidator
from .cache import MemoryCache, MultiLevelCacheManager, CacheStrategy
from .providers.openbb_provider import OpenBBProvider
from .services.market_data_service import MarketDataService
from .services.technical_indicators_service import TechnicalIndicatorsService
from .services.news_service import NewsService


# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FinancialDataManager:
    """
    Gestionnaire principal pour toutes les données financières.
    
    Orchestrer l'accès aux données de marché, indicateurs techniques,
    et nouvelles financières via une interface unifiée.
    """
    
    def __init__(self, enable_cache: bool = True):
        """
        Initialise le gestionnaire de données financières.
        
        Args:
            enable_cache: Active le système de cache
        """
        self.enable_cache = enable_cache
        
        # Configuration du cache
        if enable_cache:
            self.memory_cache = MemoryCache(
                max_size=1000,
                default_ttl=3600
            )
            self.cache_manager = MultiLevelCacheManager(
                l1_cache=self.memory_cache,
                strategy=CacheStrategy.READ_THROUGH
            )
        else:
            self.cache_manager = None
        
        # Initialisation des services
        self.provider = OpenBBProvider(cache_manager=self.cache_manager)
        self.market_service = MarketDataService(
            provider=self.provider,
            cache_manager=self.cache_manager
        )
        self.indicators_service = TechnicalIndicatorsService(
            provider=self.provider,
            cache_manager=self.cache_manager
        )
        self.news_service = NewsService(
            provider=self.provider,
            cache_manager=self.cache_manager
        )
    
    async def comprehensive_analysis(
        self,
        symbol: str,
        timeframe: TimeFrame = TimeFrame.DAY_1,
        lookback_days: int = 30
    ) -> Dict[str, Any]:
        """
        Effectue une analyse complète d'un symbole.
        
        Args:
            symbol: Symbole financier à analyser
            timeframe: Timeframe pour l'analyse
            lookback_days: Nombre de jours d'historique
            
        Returns:
            Dictionnaire avec toutes les données analysées
        """
        symbol = BaseValidator.normalize_symbol(symbol)
        logger.info(f"Démarrage analyse complète pour {symbol}")
        
        end_date = arrow.utcnow().datetime
        start_date = end_date - timedelta(days=lookback_days)
        
        try:
            # 1. Données de marché historiques
            logger.info("Récupération données de marché...")
            market_data = await self.market_service.get_historical_data(
                symbol=symbol,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date
            )
            
            # 2. Cotation en temps réel
            logger.info("Récupération cotation temps réel...")
            current_quote = await self.market_service.get_quote(symbol)
            
            # 3. Indicateurs techniques
            logger.info("Calcul indicateurs techniques...")
            
            # Configuration des indicateurs à calculer
            indicators_config = [
                {'type': 'sma', 'period': 20},
                {'type': 'sma', 'period': 50},
                {'type': 'ema', 'period': 12},
                {'type': 'rsi', 'period': 14},
                {'type': 'macd', 'fast': 12, 'slow': 26, 'signal': 9},
                {'type': 'bollinger', 'period': 20, 'std_multiplier': 2.0},
                {'type': 'stochastic', 'k_period': 14, 'd_period': 3}
            ]
            
            indicators_collection = await self.indicators_service.calculate_indicator_collection(
                symbol=symbol,
                timeframe=timeframe,
                indicators=indicators_config,
                end_date=end_date,
                lookback_days=lookback_days
            )
            
            # 4. Nouvelles et sentiment
            logger.info("Analyse nouvelles et sentiment...")
            news_collection = await self.news_service.get_company_news(
                symbol=symbol,
                limit=50,
                start_date=start_date
            )
            
            sentiment_analysis = await self.news_service.analyze_sentiment_for_symbol(
                symbol=symbol,
                hours=24
            )
            
            # 5. Compilation des résultats
            analysis_result = {
                'symbol': symbol,
                'timeframe': timeframe,
                'analysis_date': end_date,
                'lookback_days': lookback_days,
                
                # Données de marché
                'market_data': {
                    'total_points': len(market_data.data),
                    'latest_price': float(market_data.data[-1].close) if market_data.data else None,
                    'price_change_period': self._calculate_price_change(market_data),
                    'volume_average': self._calculate_average_volume(market_data),
                    'high_low_range': self._calculate_high_low_range(market_data)
                },
                
                # Cotation actuelle
                'current_quote': {
                    'bid': float(current_quote.bid) if current_quote.bid else None,
                    'ask': float(current_quote.ask) if current_quote.ask else None,
                    'last_price': float(current_quote.last_price) if current_quote.last_price else None,
                    'volume': int(current_quote.volume) if current_quote.volume else None
                },
                
                # Indicateurs techniques
                'technical_indicators': self._format_indicators(indicators_collection),
                
                # Sentiment et nouvelles
                'news_sentiment': {
                    'total_articles': len(news_collection.articles),
                    'recent_articles': len(news_collection.get_recent_articles(24)),
                    'high_impact_articles': len(news_collection.get_high_impact_articles()),
                    'sentiment_analysis': sentiment_analysis.dict() if sentiment_analysis else None
                },
                
                # Synthèse
                'synthesis': self._generate_synthesis(
                    market_data, indicators_collection, sentiment_analysis
                )
            }
            
            logger.info(f"Analyse complète terminée pour {symbol}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Erreur analyse complète {symbol}: {e}")
            raise
    
    async def portfolio_analysis(
        self,
        symbols: List[str],
        timeframe: TimeFrame = TimeFrame.DAY_1
    ) -> Dict[str, Any]:
        """
        Analyse un portefeuille de symboles.
        
        Args:
            symbols: Liste des symboles du portefeuille
            timeframe: Timeframe pour l'analyse
            
        Returns:
            Analyse agrégée du portefeuille
        """
        symbols = [BaseValidator.normalize_symbol(s) for s in symbols]
        logger.info(f"Analyse portefeuille: {symbols}")
        
        try:
            # Analyse en parallèle de tous les symboles
            tasks = [
                self.comprehensive_analysis(symbol, timeframe, lookback_days=30)
                for symbol in symbols
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Compilation des résultats
            successful_analyses = []
            failed_symbols = []
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    failed_symbols.append(symbols[i])
                    logger.error(f"Échec analyse {symbols[i]}: {result}")
                else:
                    successful_analyses.append(result)
            
            # Agrégation des métriques
            portfolio_metrics = self._calculate_portfolio_metrics(successful_analyses)
            
            return {
                'portfolio_symbols': symbols,
                'successful_analyses': len(successful_analyses),
                'failed_analyses': len(failed_symbols),
                'failed_symbols': failed_symbols,
                'timeframe': timeframe,
                'analysis_date': arrow.utcnow().datetime,
                'portfolio_metrics': portfolio_metrics,
                'individual_analyses': successful_analyses
            }
            
        except Exception as e:
            logger.error(f"Erreur analyse portefeuille: {e}")
            raise
    
    async def market_overview(self) -> Dict[str, Any]:
        """
        Génère un aperçu du marché général.
        
        Returns:
            Aperçu du marché avec tendances et nouvelles
        """
        logger.info("Génération aperçu du marché")
        
        try:
            # Symboles représentatifs du marché
            market_symbols = ['SPY', 'QQQ', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
            
            # Nouvelles générales du marché
            market_news = await self.news_service.get_market_news(
                limit=100,
                include_sentiment=True
            )
            
            # Actions tendance
            trending_stocks = await self.news_service.get_trending_stocks(
                hours=24,
                min_mentions=3,
                limit=10
            )
            
            # Analyse des indices principaux
            indices_analysis = await self.portfolio_analysis(
                symbols=['SPY', 'QQQ', 'IWM'],  # S&P 500, NASDAQ, Russell 2000
                timeframe=TimeFrame.DAY_1
            )
            
            return {
                'overview_date': arrow.utcnow().datetime,
                'market_news': {
                    'total_articles': len(market_news.articles),
                    'recent_articles': len(market_news.get_recent_articles(6)),
                    'high_impact_articles': len(market_news.get_high_impact_articles())
                },
                'trending_stocks': trending_stocks,
                'major_indices': indices_analysis,
                'market_sentiment': self._calculate_market_sentiment(market_news)
            }
            
        except Exception as e:
            logger.error(f"Erreur aperçu du marché: {e}")
            raise
    
    # Méthodes utilitaires privées
    
    def _calculate_price_change(self, market_data) -> Dict[str, float]:
        """Calcule le changement de prix sur la période."""
        if len(market_data.data) < 2:
            return {'change': 0.0, 'change_percent': 0.0}
        
        first_price = float(market_data.data[0].close)
        last_price = float(market_data.data[-1].close)
        
        change = last_price - first_price
        change_percent = (change / first_price) * 100 if first_price != 0 else 0.0
        
        return {
            'change': change,
            'change_percent': change_percent,
            'first_price': first_price,
            'last_price': last_price
        }
    
    def _calculate_average_volume(self, market_data) -> int:
        """Calcule le volume moyen."""
        if not market_data.data:
            return 0
        
        volumes = [int(point.volume or 0) for point in market_data.data]
        return sum(volumes) // len(volumes) if volumes else 0
    
    def _calculate_high_low_range(self, market_data) -> Dict[str, float]:
        """Calcule la fourchette haut-bas."""
        if not market_data.data:
            return {'high': 0.0, 'low': 0.0, 'range_percent': 0.0}
        
        highs = [float(point.high) for point in market_data.data]
        lows = [float(point.low) for point in market_data.data]
        
        period_high = max(highs)
        period_low = min(lows)
        range_percent = ((period_high - period_low) / period_low) * 100 if period_low != 0 else 0.0
        
        return {
            'high': period_high,
            'low': period_low,
            'range_percent': range_percent
        }
    
    def _format_indicators(self, indicators_collection) -> Dict[str, Any]:
        """Formate les indicateurs techniques pour l'affichage."""
        formatted = {}
        
        for name, indicator in indicators_collection.indicators.items():
            if hasattr(indicator, 'value'):
                # Indicateur simple (SMA, EMA, RSI)
                formatted[name] = {
                    'value': float(indicator.value),
                    'type': indicator.indicator_type,
                    'period': indicator.period
                }
                
                # Ajout de propriétés spéciales
                if hasattr(indicator, 'signal'):
                    formatted[name]['signal'] = indicator.signal
                if hasattr(indicator, 'is_overbought'):
                    formatted[name]['overbought'] = indicator.is_overbought
                if hasattr(indicator, 'is_oversold'):
                    formatted[name]['oversold'] = indicator.is_oversold
                    
            elif hasattr(indicator, 'macd_line'):
                # MACD
                formatted[name] = {
                    'macd_line': float(indicator.macd_line),
                    'signal_line': float(indicator.signal_line),
                    'histogram': float(indicator.histogram),
                    'bullish_crossover': indicator.is_bullish_crossover
                }
                
            elif hasattr(indicator, 'upper_band'):
                # Bollinger Bands
                formatted[name] = {
                    'upper_band': float(indicator.upper_band),
                    'middle_band': float(indicator.middle_band),
                    'lower_band': float(indicator.lower_band),
                    'bandwidth_percent': float(indicator.bandwidth_percent)
                }
                
            elif hasattr(indicator, 'k_percent'):
                # Stochastic
                formatted[name] = {
                    'k_percent': float(indicator.k_percent),
                    'd_percent': float(indicator.d_percent),
                    'signal': indicator.signal,
                    'overbought': indicator.is_overbought,
                    'oversold': indicator.is_oversold
                }
        
        return formatted
    
    def _generate_synthesis(self, market_data, indicators_collection, sentiment_analysis) -> Dict[str, str]:
        """Génère une synthèse de l'analyse."""
        synthesis = {
            'trend': 'NEUTRE',
            'momentum': 'NEUTRE',
            'sentiment': 'NEUTRE',
            'overall': 'NEUTRE'
        }
        
        # Analyse de la tendance (basée sur les moyennes mobiles)
        sma_20 = indicators_collection.get_indicator('SMA_20')
        sma_50 = indicators_collection.get_indicator('SMA_50')
        
        if sma_20 and sma_50:
            if sma_20.value > sma_50.value:
                synthesis['trend'] = 'HAUSSIER'
            elif sma_20.value < sma_50.value:
                synthesis['trend'] = 'BAISSIER'
        
        # Analyse du momentum (RSI)
        rsi = indicators_collection.get_indicator('RSI_14')
        if rsi:
            if rsi.is_overbought:
                synthesis['momentum'] = 'SURACHETÉ'
            elif rsi.is_oversold:
                synthesis['momentum'] = 'SURVENDU'
        
        # Sentiment
        if sentiment_analysis:
            synthesis['sentiment'] = sentiment_analysis.overall_sentiment
        
        # Synthèse globale
        positive_signals = sum(1 for signal in synthesis.values() if 'HAUSSIER' in signal or 'POSITIF' in signal)
        negative_signals = sum(1 for signal in synthesis.values() if 'BAISSIER' in signal or 'NÉGATIF' in signal)
        
        if positive_signals > negative_signals:
            synthesis['overall'] = 'POSITIF'
        elif negative_signals > positive_signals:
            synthesis['overall'] = 'NÉGATIF'
        
        return synthesis
    
    def _calculate_portfolio_metrics(self, analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calcule les métriques agrégées du portefeuille."""
        if not analyses:
            return {}
        
        # Performance moyenne
        changes = [a['market_data']['price_change_period']['change_percent'] for a in analyses]
        avg_performance = sum(changes) / len(changes) if changes else 0.0
        
        # Répartition des tendances
        trends = [a['synthesis']['trend'] for a in analyses]
        trend_distribution = {
            'HAUSSIER': trends.count('HAUSSIER'),
            'BAISSIER': trends.count('BAISSIER'),
            'NEUTRE': trends.count('NEUTRE')
        }
        
        # Sentiment global
        sentiments = []
        for analysis in analyses:
            if analysis['news_sentiment']['sentiment_analysis']:
                sentiments.append(analysis['news_sentiment']['sentiment_analysis']['average_sentiment'])
        
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0.0
        
        return {
            'average_performance_percent': avg_performance,
            'trend_distribution': trend_distribution,
            'average_sentiment': avg_sentiment,
            'total_symbols_analyzed': len(analyses)
        }
    
    def _calculate_market_sentiment(self, market_news) -> Dict[str, Any]:
        """Calcule le sentiment général du marché."""
        recent_articles = market_news.get_recent_articles(24)
        
        if not recent_articles:
            return {'sentiment': 'NEUTRE', 'confidence': 0.0}
        
        sentiments = [a.sentiment_score for a in recent_articles if a.sentiment_score is not None]
        
        if not sentiments:
            return {'sentiment': 'NEUTRE', 'confidence': 0.0}
        
        avg_sentiment = sum(sentiments) / len(sentiments)
        confidence = min(1.0, len(sentiments) / 20)
        
        if avg_sentiment > 0.3:
            sentiment_label = 'POSITIF'
        elif avg_sentiment < -0.3:
            sentiment_label = 'NÉGATIF'
        else:
            sentiment_label = 'NEUTRE'
        
        return {
            'sentiment': sentiment_label,
            'score': avg_sentiment,
            'confidence': confidence,
            'articles_analyzed': len(sentiments)
        }
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Retourne le statut de santé de tout le système."""
        health_data = {
            'overall_status': 'healthy',
            'timestamp': arrow.utcnow().datetime,
            'services': {}
        }
        
        # Statut des services
        try:
            health_data['services']['market_data'] = await self.market_service.get_health_status()
        except Exception as e:
            health_data['services']['market_data'] = {'status': 'error', 'error': str(e)}
        
        try:
            health_data['services']['technical_indicators'] = await self.indicators_service.get_health_status()
        except Exception as e:
            health_data['services']['technical_indicators'] = {'status': 'error', 'error': str(e)}
        
        try:
            health_data['services']['news'] = await self.news_service.get_health_status()
        except Exception as e:
            health_data['services']['news'] = {'status': 'error', 'error': str(e)}
        
        # Cache status
        if self.cache_manager:
            health_data['cache'] = {
                'enabled': True,
                'memory_cache_size': len(self.memory_cache._cache) if hasattr(self.memory_cache, '_cache') else 0
            }
        else:
            health_data['cache'] = {'enabled': False}
        
        return health_data
    
    async def close(self):
        """Ferme tous les services et libère les ressources."""
        logger.info("Fermeture du gestionnaire de données financières")
        
        await self.market_service.close()
        await self.indicators_service.close()
        await self.news_service.close()
        
        if self.cache_manager:
            await self.cache_manager.close()


# Fonction de démonstration
async def demo_integration():
    """
    Démonstration complète de l'intégration OpenBB.
    """
    logger.info("=== DÉMONSTRATION INTÉGRATION OPENBB ===")
    
    # Initialisation du gestionnaire
    manager = FinancialDataManager(enable_cache=True)
    
    try:
        # Test 1: Analyse complète d'un symbole
        logger.info("\n1. Analyse complète AAPL...")
        aapl_analysis = await manager.comprehensive_analysis(
            symbol="AAPL",
            timeframe=TimeFrame.DAY_1,
            lookback_days=30
        )
        logger.info(f"✅ Analyse AAPL terminée: {aapl_analysis['market_data']['total_points']} points de données")
        
        # Test 2: Analyse de portefeuille
        logger.info("\n2. Analyse portefeuille FAANG...")
        portfolio_symbols = ['AAPL', 'GOOGL', 'AMZN', 'META', 'NFLX']
        portfolio_analysis = await manager.portfolio_analysis(
            symbols=portfolio_symbols,
            timeframe=TimeFrame.DAY_1
        )
        logger.info(f"✅ Portefeuille analysé: {portfolio_analysis['successful_analyses']}/{len(portfolio_symbols)} symboles")
        
        # Test 3: Aperçu du marché
        logger.info("\n3. Aperçu du marché...")
        market_overview = await manager.market_overview()
        logger.info(f"✅ Aperçu du marché: {market_overview['market_news']['total_articles']} nouvelles")
        
        # Test 4: Statut de santé du système
        logger.info("\n4. Vérification santé système...")
        health_status = await manager.get_system_health()
        logger.info(f"✅ Système: {health_status['overall_status']}")
        
        logger.info("\n=== DÉMONSTRATION TERMINÉE AVEC SUCCÈS ===")
        
        return {
            'aapl_analysis': aapl_analysis,
            'portfolio_analysis': portfolio_analysis,
            'market_overview': market_overview,
            'health_status': health_status
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur durant la démonstration: {e}")
        raise
    
    finally:
        await manager.close()


if __name__ == "__main__":
    # Exécution de la démonstration
    asyncio.run(demo_integration())