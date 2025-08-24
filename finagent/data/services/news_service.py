"""
Service pour les nouvelles financières.

Ce module fournit une interface de haut niveau pour récupérer,
analyser et gérer les nouvelles financières avec analyse de sentiment.
"""

import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from decimal import Decimal
from collections import defaultdict, Counter

import arrow
from textblob import TextBlob

from ..models.base import Symbol
from ..validators.base import ValidationError
from ..models.news import (
    NewsArticle, NewsCollection, MarketEvent, SentimentAnalysis,
    NewsCategory, SentimentScore, NewsSource
)
from ..providers.openbb_provider import OpenBBProvider, OpenBBError
from ..cache import MultiLevelCacheManager, CacheKeys, CacheTags
from ..validators import BaseValidator

logger = logging.getLogger(__name__)


class NewsAnalysisError(Exception):
    """Erreur lors de l'analyse des nouvelles."""
    pass


class SentimentAnalyzer:
    """
    Analyseur de sentiment pour les nouvelles financières.
    
    Utilise TextBlob et des règles spécialisées pour l'analyse financière.
    """
    
    # Mots-clés positifs et négatifs pour l'analyse financière
    POSITIVE_KEYWORDS = {
        'growth', 'profit', 'revenue', 'earnings', 'beat', 'exceed', 'strong',
        'bullish', 'buy', 'upgrade', 'outperform', 'gains', 'rally', 'surge',
        'croissance', 'profit', 'bénéfice', 'dépasser', 'fort', 'haussier'
    }
    
    NEGATIVE_KEYWORDS = {
        'loss', 'decline', 'fall', 'drop', 'weak', 'bearish', 'sell', 'downgrade',
        'underperform', 'miss', 'disappoint', 'crash', 'plunge', 'collapse',
        'perte', 'baisse', 'chute', 'faible', 'baissier', 'décevoir', 'effondrement'
    }
    
    @classmethod
    def analyze_sentiment(cls, text: str) -> Tuple[float, float]:
        """
        Analyse le sentiment d'un texte.
        
        Args:
            text: Texte à analyser
            
        Returns:
            Tuple (sentiment_score, confidence) où:
            - sentiment_score: Score entre -1 (très négatif) et 1 (très positif)
            - confidence: Confiance dans l'analyse (0-1)
        """
        if not text or not text.strip():
            return 0.0, 0.0
        
        try:
            # Analyse avec TextBlob
            blob = TextBlob(text.lower())
            base_sentiment = blob.sentiment.polarity
            
            # Analyse avec mots-clés financiers
            words = set(re.findall(r'\b\w+\b', text.lower()))
            
            positive_count = len(words.intersection(cls.POSITIVE_KEYWORDS))
            negative_count = len(words.intersection(cls.NEGATIVE_KEYWORDS))
            
            # Score pondéré
            keyword_sentiment = 0.0
            if positive_count > 0 or negative_count > 0:
                keyword_sentiment = (positive_count - negative_count) / (positive_count + negative_count)
            
            # Combinaison des scores (60% TextBlob, 40% mots-clés)
            final_sentiment = 0.6 * base_sentiment + 0.4 * keyword_sentiment
            
            # Calcul de la confiance
            total_keywords = positive_count + negative_count
            confidence = min(1.0, 0.3 + 0.1 * total_keywords + abs(final_sentiment) * 0.3)
            
            return float(final_sentiment), float(confidence)
            
        except Exception as e:
            logger.error(f"Erreur analyse sentiment: {e}")
            return 0.0, 0.0
    
    @classmethod
    def categorize_sentiment(cls, score: float) -> SentimentScore:
        """Catégorise un score de sentiment."""
        if score >= 0.8:
            return SentimentScore.VERY_POSITIVE
        elif score >= 0.4:
            return SentimentScore.POSITIVE
        elif score <= -0.8:
            return SentimentScore.VERY_NEGATIVE
        elif score <= -0.4:
            return SentimentScore.NEGATIVE
        else:
            return SentimentScore.NEUTRAL


class NewsService:
    """
    Service pour la gestion des nouvelles financières.
    
    Fournit une interface unifiée pour récupérer et analyser
    les nouvelles avec sentiment analysis automatique.
    """
    
    def __init__(
        self,
        provider: OpenBBProvider,
        cache_manager: Optional[MultiLevelCacheManager] = None,
        enable_sentiment_analysis: bool = True
    ):
        """
        Initialise le service de nouvelles.
        
        Args:
            provider: Provider OpenBB pour récupérer les données
            cache_manager: Gestionnaire de cache (optionnel)
            enable_sentiment_analysis: Active l'analyse de sentiment
        """
        self.provider = provider
        self.cache_manager = cache_manager
        self.enable_sentiment_analysis = enable_sentiment_analysis
        self.sentiment_analyzer = SentimentAnalyzer()
        
        # Métriques
        self.cache_hits = 0
        self.cache_misses = 0
        self.articles_processed = 0
        self.sentiment_analyses = 0
        self.errors_count = 0
    
    async def get_company_news(
        self,
        symbol: str,
        limit: int = 50,
        start_date: Optional[datetime] = None,
        include_sentiment: bool = True
    ) -> NewsCollection:
        """
        Récupère les nouvelles d'une entreprise avec analyse de sentiment.
        
        Args:
            symbol: Symbole de l'entreprise
            limit: Nombre maximum d'articles
            start_date: Date de début (optionnelle)
            include_sentiment: Inclure l'analyse de sentiment
            
        Returns:
            Collection de nouvelles avec sentiment
        """
        symbol = BaseValidator.normalize_symbol(symbol)
        
        try:
            logger.info(f"Récupération nouvelles avec sentiment: {symbol}")
            
            # Utilise le provider pour récupérer les nouvelles de base
            news_collection = await self.provider.get_company_news(
                symbol=symbol,
                limit=limit,
                start_date=start_date
            )
            
            # Ajoute l'analyse de sentiment si demandée
            if include_sentiment and self.enable_sentiment_analysis:
                await self._add_sentiment_analysis(news_collection)
            
            self.articles_processed += len(news_collection.articles)
            logger.info(f"Traité {len(news_collection.articles)} articles pour {symbol}")
            
            return news_collection
            
        except Exception as e:
            self.errors_count += 1
            logger.error(f"Erreur récupération nouvelles {symbol}: {e}")
            if isinstance(e, (ValidationError, OpenBBError)):
                raise
            raise NewsAnalysisError(f"Erreur récupération nouvelles: {e}")
    
    async def get_multi_symbol_news(
        self,
        symbols: List[str],
        limit_per_symbol: int = 20,
        start_date: Optional[datetime] = None,
        include_sentiment: bool = True
    ) -> NewsCollection:
        """
        Récupère les nouvelles pour plusieurs symboles en parallèle.
        
        Args:
            symbols: Liste des symboles
            limit_per_symbol: Limite d'articles par symbole
            start_date: Date de début
            include_sentiment: Inclure l'analyse de sentiment
            
        Returns:
            Collection agrégée de nouvelles
        """
        symbols = [BaseValidator.normalize_symbol(s) for s in symbols]
        logger.info(f"Récupération nouvelles multi-symboles: {symbols}")
        
        # Récupération en parallèle
        tasks = [
            self.get_company_news(symbol, limit_per_symbol, start_date, include_sentiment)
            for symbol in symbols
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Agrégation des résultats
        combined_collection = NewsCollection()
        successful = 0
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Erreur symbole {symbols[i]}: {result}")
                continue
            
            # Fusion des collections
            for article in result.articles:
                combined_collection.add_article(article)
            
            for event in result.events:
                combined_collection.add_event(event)
            
            successful += 1
        
        logger.info(f"Multi-symboles: {successful}/{len(symbols)} récupérés avec succès")
        return combined_collection
    
    async def get_market_news(
        self,
        limit: int = 100,
        start_date: Optional[datetime] = None,
        categories: Optional[List[NewsCategory]] = None,
        include_sentiment: bool = True
    ) -> NewsCollection:
        """
        Récupère les nouvelles générales du marché.
        
        Args:
            limit: Nombre maximum d'articles
            start_date: Date de début
            categories: Catégories de nouvelles à inclure
            include_sentiment: Inclure l'analyse de sentiment
            
        Returns:
            Collection de nouvelles du marché
        """
        # Cache des nouvelles générales du marché
        cache_key = f"market_news_{limit}_{start_date.strftime('%Y%m%d') if start_date else 'all'}"
        if self.cache_manager:
            cached = await self.cache_manager.get(cache_key)
            if cached:
                self.cache_hits += 1
                return cached
        
        try:
            self.cache_misses += 1
            logger.info("Récupération nouvelles générales du marché")
            
            # Pour les nouvelles générales, on utilise des symboles populaires
            # comme proxy pour obtenir un aperçu du marché
            market_symbols = ['SPY', 'QQQ', 'AAPL', 'MSFT', 'GOOGL', 'TSLA']
            
            news_collection = await self.get_multi_symbol_news(
                symbols=market_symbols,
                limit_per_symbol=limit // len(market_symbols),
                start_date=start_date,
                include_sentiment=include_sentiment
            )
            
            # Filtrage par catégories si spécifiées
            if categories:
                filtered_articles = [
                    article for article in news_collection.articles
                    if article.category in categories
                ]
                news_collection.articles = filtered_articles
            
            # Cache (15 minutes pour les nouvelles générales)
            if self.cache_manager:
                tags = [CacheTags.NEWS, CacheTags.MARKET_DATA]
                await self.cache_manager.set(cache_key, news_collection, 900, tags)
            
            return news_collection
            
        except Exception as e:
            self.errors_count += 1
            logger.error(f"Erreur récupération nouvelles marché: {e}")
            raise NewsAnalysisError(f"Erreur nouvelles marché: {e}")
    
    async def analyze_sentiment_for_symbol(
        self,
        symbol: str,
        hours: int = 24,
        min_articles: int = 3
    ) -> Optional[SentimentAnalysis]:
        """
        Analyse le sentiment agrégé pour un symbole.
        
        Args:
            symbol: Symbole à analyser
            hours: Période d'analyse en heures
            min_articles: Nombre minimum d'articles requis
            
        Returns:
            Analyse de sentiment ou None si insuffisant
        """
        symbol = BaseValidator.normalize_symbol(symbol)
        
        cache_key = f"sentiment_{symbol}_{hours}h"
        if self.cache_manager:
            cached = await self.cache_manager.get(cache_key)
            if cached:
                self.cache_hits += 1
                return cached
        
        try:
            self.cache_misses += 1
            logger.info(f"Analyse sentiment {symbol} sur {hours}h")
            
            # Récupère les nouvelles récentes
            start_date = arrow.utcnow().shift(hours=-hours).datetime
            news_collection = await self.get_company_news(
                symbol=symbol,
                start_date=start_date,
                include_sentiment=True
            )
            
            if len(news_collection.articles) < min_articles:
                logger.warning(f"Pas assez d'articles pour {symbol}: {len(news_collection.articles)} < {min_articles}")
                return None
            
            # Analyse de sentiment agrégée
            sentiment_analysis = await self._create_sentiment_analysis(
                news_collection, symbol, hours
            )
            
            # Cache (30 minutes)
            if self.cache_manager:
                tags = [CacheTags.symbol(symbol), CacheTags.NEWS]
                await self.cache_manager.set(cache_key, sentiment_analysis, 1800, tags)
            
            self.sentiment_analyses += 1
            return sentiment_analysis
            
        except Exception as e:
            self.errors_count += 1
            logger.error(f"Erreur analyse sentiment {symbol}: {e}")
            raise NewsAnalysisError(f"Erreur analyse sentiment: {e}")
    
    async def get_trending_stocks(
        self,
        hours: int = 24,
        min_mentions: int = 5,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Identifie les actions tendance basées sur les mentions dans les nouvelles.
        
        Args:
            hours: Période d'analyse
            min_mentions: Nombre minimum de mentions
            limit: Nombre maximum de résultats
            
        Returns:
            Liste des actions tendance avec métriques
        """
        cache_key = f"trending_{hours}h_{min_mentions}_{limit}"
        if self.cache_manager:
            cached = await self.cache_manager.get(cache_key)
            if cached:
                self.cache_hits += 1
                return cached
        
        try:
            self.cache_misses += 1
            logger.info(f"Identification actions tendance sur {hours}h")
            
            # Récupère les nouvelles générales du marché
            start_date = arrow.utcnow().shift(hours=-hours).datetime
            market_news = await self.get_market_news(
                start_date=start_date,
                include_sentiment=True
            )
            
            # Compte les mentions et analyse les sentiments
            symbol_stats = defaultdict(lambda: {
                'mentions': 0,
                'sentiments': [],
                'articles': [],
                'avg_sentiment': 0.0,
                'trend_score': 0.0
            })
            
            for article in market_news.articles:
                for symbol in article.symbols:
                    stats = symbol_stats[symbol.symbol]
                    stats['mentions'] += 1
                    stats['articles'].append(article)
                    
                    if article.sentiment_score is not None:
                        stats['sentiments'].append(article.sentiment_score)
            
            # Calcule les métriques
            trending = []
            for symbol, stats in symbol_stats.items():
                if stats['mentions'] < min_mentions:
                    continue
                
                # Sentiment moyen
                if stats['sentiments']:
                    stats['avg_sentiment'] = sum(stats['sentiments']) / len(stats['sentiments'])
                
                # Score de tendance (combine mentions et sentiment)
                mention_score = min(1.0, stats['mentions'] / 20)  # Normalise sur 20 mentions
                sentiment_score = (stats['avg_sentiment'] + 1) / 2  # Normalise 0-1
                stats['trend_score'] = 0.7 * mention_score + 0.3 * sentiment_score
                
                trending.append({
                    'symbol': symbol,
                    'mentions': stats['mentions'],
                    'avg_sentiment': stats['avg_sentiment'],
                    'sentiment_label': SentimentAnalyzer.categorize_sentiment(stats['avg_sentiment']),
                    'trend_score': stats['trend_score'],
                    'recent_articles': len([a for a in stats['articles'] if a.is_recent(6)])
                })
            
            # Trie par score de tendance
            trending.sort(key=lambda x: x['trend_score'], reverse=True)
            result = trending[:limit]
            
            # Cache (20 minutes)
            if self.cache_manager:
                tags = [CacheTags.NEWS, CacheTags.TRENDING]
                await self.cache_manager.set(cache_key, result, 1200, tags)
            
            logger.info(f"Identifié {len(result)} actions tendance")
            return result
            
        except Exception as e:
            self.errors_count += 1
            logger.error(f"Erreur identification tendances: {e}")
            raise NewsAnalysisError(f"Erreur tendances: {e}")
    
    async def get_earnings_calendar(
        self,
        days_ahead: int = 7,
        symbols: Optional[List[str]] = None
    ) -> List[MarketEvent]:
        """
        Récupère le calendrier des résultats financiers.
        
        Args:
            days_ahead: Nombre de jours à l'avance
            symbols: Symboles spécifiques (optionnel)
            
        Returns:
            Liste des événements earnings
        """
        cache_key = f"earnings_calendar_{days_ahead}_{','.join(symbols) if symbols else 'all'}"
        if self.cache_manager:
            cached = await self.cache_manager.get(cache_key)
            if cached:
                self.cache_hits += 1
                return cached
        
        try:
            self.cache_misses += 1
            logger.info(f"Récupération calendrier earnings ({days_ahead} jours)")
            
            # Pour cette implémentation, on simule un calendrier d'earnings
            # Dans une vraie implémentation, on utiliserait l'API OpenBB
            # ou une autre source de données d'earnings
            
            events = []
            # Cette partie devrait être remplacée par un vrai appel API
            # events = await self._fetch_earnings_calendar(days_ahead, symbols)
            
            # Cache (4 heures)
            if self.cache_manager:
                tags = [CacheTags.NEWS, CacheTags.EARNINGS]
                await self.cache_manager.set(cache_key, events, 14400, tags)
            
            return events
            
        except Exception as e:
            self.errors_count += 1
            logger.error(f"Erreur calendrier earnings: {e}")
            raise NewsAnalysisError(f"Erreur calendrier earnings: {e}")
    
    async def search_news(
        self,
        query: str,
        limit: int = 50,
        start_date: Optional[datetime] = None,
        symbols: Optional[List[str]] = None,
        categories: Optional[List[NewsCategory]] = None
    ) -> NewsCollection:
        """
        Recherche des nouvelles par mots-clés.
        
        Args:
            query: Requête de recherche
            limit: Nombre maximum de résultats
            start_date: Date de début
            symbols: Filtrer par symboles
            categories: Filtrer par catégories
            
        Returns:
            Collection de nouvelles filtrées
        """
        if not query or len(query.strip()) < 2:
            raise ValidationError("Requête de recherche trop courte")
        
        try:
            logger.info(f"Recherche nouvelles: '{query}'")
            
            # Si des symboles sont spécifiés, recherche dans leurs nouvelles
            if symbols:
                news_collection = await self.get_multi_symbol_news(
                    symbols=symbols,
                    limit_per_symbol=limit // len(symbols),
                    start_date=start_date,
                    include_sentiment=True
                )
            else:
                # Sinon, recherche dans les nouvelles générales
                news_collection = await self.get_market_news(
                    limit=limit,
                    start_date=start_date,
                    include_sentiment=True
                )
            
            # Filtrage par mots-clés
            query_words = set(query.lower().split())
            filtered_articles = []
            
            for article in news_collection.articles:
                # Recherche dans titre, résumé et contenu
                text_to_search = f"{article.title} {article.summary or ''} {article.content or ''}".lower()
                
                if any(word in text_to_search for word in query_words):
                    # Filtrage par catégories si spécifié
                    if categories and article.category not in categories:
                        continue
                    
                    filtered_articles.append(article)
            
            # Crée une nouvelle collection avec les résultats filtrés
            result_collection = NewsCollection()
            for article in filtered_articles:
                result_collection.add_article(article)
            
            logger.info(f"Recherche '{query}': {len(filtered_articles)} résultats")
            return result_collection
            
        except Exception as e:
            self.errors_count += 1
            logger.error(f"Erreur recherche nouvelles '{query}': {e}")
            raise NewsAnalysisError(f"Erreur recherche: {e}")
    
    # Méthodes privées
    
    async def _add_sentiment_analysis(self, news_collection: NewsCollection) -> None:
        """Ajoute l'analyse de sentiment aux articles d'une collection."""
        if not self.enable_sentiment_analysis:
            return
        
        for article in news_collection.articles:
            if article.sentiment_score is None:
                # Analyse le sentiment du titre + résumé
                text_to_analyze = f"{article.title}. {article.summary or ''}"
                sentiment_score, confidence = self.sentiment_analyzer.analyze_sentiment(text_to_analyze)
                
                article.sentiment_score = sentiment_score
                article.sentiment = SentimentAnalyzer.categorize_sentiment(sentiment_score)
                
                # Calcule un score d'impact basé sur la source et le sentiment
                if article.impact_score is None:
                    impact_score = self._calculate_impact_score(article, confidence)
                    article.impact_score = impact_score
    
    def _calculate_impact_score(self, article: NewsArticle, sentiment_confidence: float) -> float:
        """Calcule un score d'impact pour un article."""
        base_score = 0.5
        
        # Facteur source (crédibilité)
        source_factor = article.source.credibility_score
        
        # Facteur sentiment (plus c'est extrême, plus c'est impactant)
        sentiment_factor = abs(article.sentiment_score or 0) if article.sentiment_score else 0
        
        # Facteur confiance
        confidence_factor = sentiment_confidence
        
        # Facteur catégorie (earnings sont plus impactants)
        category_factor = 1.2 if article.category == NewsCategory.EARNINGS else 1.0
        
        # Facteur symboles (plus de symboles = plus d'impact potentiel)
        symbols_factor = min(1.5, 1.0 + 0.1 * len(article.symbols))
        
        impact_score = (
            base_score * source_factor * (1 + sentiment_factor) * 
            confidence_factor * category_factor * symbols_factor
        )
        
        return min(1.0, impact_score)
    
    async def _create_sentiment_analysis(
        self,
        news_collection: NewsCollection,
        symbol: str,
        hours: int
    ) -> SentimentAnalysis:
        """Crée une analyse de sentiment agrégée."""
        articles = news_collection.get_articles_for_symbol(symbol)
        recent_articles = [a for a in articles if a.is_recent(hours)]
        
        if not recent_articles:
            raise NewsAnalysisError("Aucun article récent pour l'analyse")
        
        # Calcule les métriques
        sentiments = [a.sentiment_score for a in recent_articles if a.sentiment_score is not None]
        
        if not sentiments:
            raise NewsAnalysisError("Aucun score de sentiment disponible")
        
        avg_sentiment = sum(sentiments) / len(sentiments)
        
        # Sentiment pondéré par l'impact
        weighted_sentiments = [
            a.sentiment_score * (a.impact_score or 0.5)
            for a in recent_articles
            if a.sentiment_score is not None
        ]
        
        weighted_sentiment = sum(weighted_sentiments) / len(weighted_sentiments) if weighted_sentiments else avg_sentiment
        
        # Distribution des sentiments
        sentiment_distribution = Counter()
        for article in recent_articles:
            if article.sentiment:
                sentiment_distribution[article.sentiment] += 1
        
        # Score de confiance
        confidence = min(1.0, len(sentiments) / 10 + abs(avg_sentiment) * 0.3)
        
        # Sujets tendance (tags les plus fréquents)
        all_tags = []
        for article in recent_articles:
            all_tags.extend(article.tags)
        
        trending_topics = [tag for tag, _ in Counter(all_tags).most_common(5)]
        
        return SentimentAnalysis(
            symbol=Symbol(symbol=symbol),
            period_hours=hours,
            total_articles=len(recent_articles),
            average_sentiment=avg_sentiment,
            sentiment_distribution=dict(sentiment_distribution),
            weighted_sentiment=weighted_sentiment,
            confidence_score=confidence,
            trending_topics=trending_topics
        )
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Retourne le statut de santé du service."""
        return {
            'service': 'NewsService',
            'status': 'healthy',
            'metrics': {
                'cache_hits': self.cache_hits,
                'cache_misses': self.cache_misses,
                'hit_rate': self.cache_hits / max(1, self.cache_hits + self.cache_misses),
                'articles_processed': self.articles_processed,
                'sentiment_analyses': self.sentiment_analyses,
                'errors_count': self.errors_count,
                'sentiment_analysis_enabled': self.enable_sentiment_analysis
            },
            'provider_status': await self.provider.get_health_status()
        }
    
    async def close(self):
        """Ferme le service et libère les ressources."""
        logger.info("Fermeture du service de nouvelles")
        # Pas de ressources particulières à libérer pour ce service