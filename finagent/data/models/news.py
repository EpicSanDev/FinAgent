"""
Modèles pour les nouvelles financières.

Ce module définit les structures de données pour les nouvelles,
analyses et événements financiers.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from enum import Enum
from decimal import Decimal

from pydantic import BaseModel, Field, validator, HttpUrl
import arrow

from .base import BaseFinancialModel, Symbol, DataQuality


class NewsCategory(str, Enum):
    """Catégories de nouvelles financières."""
    
    EARNINGS = "earnings"  # Résultats financiers
    MERGER = "merger"  # Fusions & acquisitions
    DIVIDEND = "dividend"  # Dividendes
    ANALYST = "analyst"  # Recommandations d'analystes
    GENERAL = "general"  # Nouvelles générales
    REGULATORY = "regulatory"  # Réglementaire
    MARKET = "market"  # Marché général
    TECHNOLOGY = "technology"  # Technologie
    ESG = "esg"  # Environnement, Social, Gouvernance
    CRYPTO = "crypto"  # Cryptomonnaies
    COMMODITIES = "commodities"  # Matières premières
    FOREX = "forex"  # Devises
    POLITICS = "politics"  # Politique/Géopolitique


class SentimentScore(str, Enum):
    """Score de sentiment des nouvelles."""
    
    VERY_POSITIVE = "very_positive"  # 0.8 - 1.0
    POSITIVE = "positive"  # 0.4 - 0.8
    NEUTRAL = "neutral"  # -0.4 - 0.4
    NEGATIVE = "negative"  # -0.8 - -0.4
    VERY_NEGATIVE = "very_negative"  # -1.0 - -0.8


class NewsSource(BaseModel):
    """
    Modèle pour une source de nouvelles.
    """
    
    name: str = Field(
        ...,
        description="Nom de la source",
        min_length=1,
        max_length=100
    )
    url: Optional[HttpUrl] = Field(
        None,
        description="URL de la source"
    )
    credibility_score: float = Field(
        1.0,
        description="Score de crédibilité (0-1)",
        ge=0.0,
        le=1.0
    )
    bias_score: float = Field(
        0.0,
        description="Score de biais (-1 à 1, 0=neutre)",
        ge=-1.0,
        le=1.0
    )
    category: Optional[str] = Field(
        None,
        description="Catégorie de la source (média, blog, officiel)"
    )

    def __str__(self) -> str:
        """Représentation textuelle de la source."""
        return self.name

    def __hash__(self) -> int:
        """Hash basé sur le nom pour utilisation dans des sets."""
        return hash(self.name)


class NewsArticle(BaseFinancialModel):
    """
    Modèle pour un article de nouvelles financières.
    """
    
    title: str = Field(
        ...,
        description="Titre de l'article",
        min_length=1,
        max_length=500
    )
    summary: Optional[str] = Field(
        None,
        description="Résumé de l'article",
        max_length=2000
    )
    content: Optional[str] = Field(
        None,
        description="Contenu complet de l'article"
    )
    url: Optional[HttpUrl] = Field(
        None,
        description="URL de l'article"
    )
    published_at: datetime = Field(
        ...,
        description="Date de publication"
    )
    source: NewsSource = Field(
        ...,
        description="Source de l'article"
    )
    author: Optional[str] = Field(
        None,
        description="Auteur de l'article",
        max_length=100
    )
    category: NewsCategory = Field(
        NewsCategory.GENERAL,
        description="Catégorie de la nouvelle"
    )
    symbols: List[Symbol] = Field(
        default_factory=list,
        description="Symboles mentionnés dans l'article"
    )
    sentiment_score: Optional[float] = Field(
        None,
        description="Score de sentiment (-1 à 1)",
        ge=-1.0,
        le=1.0
    )
    sentiment: Optional[SentimentScore] = Field(
        None,
        description="Sentiment catégorisé"
    )
    impact_score: Optional[float] = Field(
        None,
        description="Score d'impact estimé (0-1)",
        ge=0.0,
        le=1.0
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Tags/mots-clés"
    )
    language: str = Field(
        "en",
        description="Langue de l'article (code ISO)"
    )
    quality: Optional[DataQuality] = Field(
        None,
        description="Qualité des données de l'article"
    )

    @validator('sentiment', always=True)
    def set_sentiment_from_score(cls, v: Optional[SentimentScore], values: Dict[str, Any]) -> Optional[SentimentScore]:
        """Détermine automatiquement le sentiment selon le score."""
        if v is not None:
            return v
        
        score = values.get('sentiment_score')
        if score is None:
            return None
        
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

    @property
    def is_relevant_for_symbol(self) -> bool:
        """Indique si l'article mentionne des symboles spécifiques."""
        return len(self.symbols) > 0

    @property
    def is_high_impact(self) -> bool:
        """Indique si l'article a un impact élevé."""
        return self.impact_score is not None and self.impact_score > 0.7

    @property
    def is_recent(self, hours: int = 24) -> bool:
        """Indique si l'article est récent."""
        now = arrow.utcnow()
        published = arrow.get(self.published_at)
        return (now - published).total_seconds() < (hours * 3600)

    @property
    def word_count(self) -> int:
        """Compte approximatif des mots dans le contenu."""
        if self.content:
            return len(self.content.split())
        elif self.summary:
            return len(self.summary.split())
        else:
            return len(self.title.split())

    def add_symbol(self, symbol: Symbol) -> None:
        """Ajoute un symbole mentionné dans l'article."""
        if symbol not in self.symbols:
            self.symbols.append(symbol)

    def add_tag(self, tag: str) -> None:
        """Ajoute un tag à l'article."""
        if tag not in self.tags:
            self.tags.append(tag)

    def __str__(self) -> str:
        """Représentation textuelle de l'article."""
        symbols_str = ", ".join([s.symbol for s in self.symbols]) if self.symbols else "N/A"
        return f"{self.title} [{symbols_str}] ({self.source.name})"


class MarketEvent(BaseFinancialModel):
    """
    Modèle pour un événement de marché.
    
    Représente des événements spécifiques comme earnings, splits, etc.
    """
    
    event_type: str = Field(
        ...,
        description="Type d'événement (earnings, split, dividend, etc.)",
        min_length=1
    )
    symbol: Symbol = Field(
        ...,
        description="Symbole concerné"
    )
    event_date: datetime = Field(
        ...,
        description="Date de l'événement"
    )
    description: str = Field(
        ...,
        description="Description de l'événement",
        min_length=1
    )
    expected_impact: Optional[str] = Field(
        None,
        description="Impact attendu (HIGH, MEDIUM, LOW)"
    )
    consensus_estimate: Optional[Decimal] = Field(
        None,
        description="Estimation consensus (pour earnings)"
    )
    actual_value: Optional[Decimal] = Field(
        None,
        description="Valeur réelle (après l'événement)"
    )
    surprise_percent: Optional[Decimal] = Field(
        None,
        description="Pourcentage de surprise vs consensus"
    )
    is_confirmed: bool = Field(
        False,
        description="Événement confirmé ou estimé"
    )
    related_articles: List[str] = Field(
        default_factory=list,
        description="IDs des articles liés"
    )

    @validator('surprise_percent', always=True)
    def calculate_surprise(cls, v: Optional[Decimal], values: Dict[str, Any]) -> Optional[Decimal]:
        """Calcule automatiquement le pourcentage de surprise."""
        if v is not None:
            return v
        
        actual = values.get('actual_value')
        consensus = values.get('consensus_estimate')
        
        if actual is not None and consensus is not None and consensus != 0:
            return ((actual - consensus) / consensus) * 100
        
        return None

    @property
    def is_past_event(self) -> bool:
        """Indique si l'événement est passé."""
        return arrow.get(self.event_date) < arrow.utcnow()

    @property
    def days_until_event(self) -> int:
        """Nombre de jours jusqu'à l'événement."""
        if self.is_past_event:
            return 0
        
        now = arrow.utcnow()
        event = arrow.get(self.event_date)
        return (event - now).days

    @property
    def surprise_level(self) -> Optional[str]:
        """Niveau de surprise basé sur le pourcentage."""
        if self.surprise_percent is None:
            return None
        
        abs_surprise = abs(self.surprise_percent)
        if abs_surprise > 20:
            return "TRÈS_ÉLEVÉE"
        elif abs_surprise > 10:
            return "ÉLEVÉE"
        elif abs_surprise > 5:
            return "MODÉRÉE"
        else:
            return "FAIBLE"

    def __str__(self) -> str:
        """Représentation textuelle de l'événement."""
        date_str = arrow.get(self.event_date).format('YYYY-MM-DD')
        return f"{self.event_type.upper()} {self.symbol.symbol} on {date_str}"


class SentimentAnalysis(BaseModel):
    """
    Modèle pour l'analyse de sentiment agrégée.
    """
    
    symbol: Symbol = Field(
        ...,
        description="Symbole analysé"
    )
    timestamp: datetime = Field(
        default_factory=lambda: arrow.utcnow().datetime,
        description="Timestamp de l'analyse"
    )
    period_hours: int = Field(
        24,
        description="Période d'analyse en heures",
        gt=0
    )
    total_articles: int = Field(
        ...,
        description="Nombre total d'articles analysés",
        ge=0
    )
    average_sentiment: float = Field(
        ...,
        description="Sentiment moyen (-1 à 1)",
        ge=-1.0,
        le=1.0
    )
    sentiment_distribution: Dict[str, int] = Field(
        default_factory=dict,
        description="Distribution des sentiments"
    )
    weighted_sentiment: Optional[float] = Field(
        None,
        description="Sentiment pondéré par impact",
        ge=-1.0,
        le=1.0
    )
    confidence_score: float = Field(
        ...,
        description="Score de confiance de l'analyse",
        ge=0.0,
        le=1.0
    )
    trending_topics: List[str] = Field(
        default_factory=list,
        description="Sujets tendance pour ce symbole"
    )

    @property
    def overall_sentiment(self) -> SentimentScore:
        """Sentiment global catégorisé."""
        score = self.weighted_sentiment or self.average_sentiment
        
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

    @property
    def is_high_confidence(self) -> bool:
        """Indique si l'analyse a une haute confiance."""
        return self.confidence_score > 0.8 and self.total_articles >= 5

    def __str__(self) -> str:
        """Représentation textuelle de l'analyse."""
        return f"Sentiment {self.symbol.symbol}: {self.overall_sentiment} ({self.total_articles} articles)"


class NewsCollection(BaseModel):
    """
    Collection de nouvelles pour un ou plusieurs symboles.
    """
    
    articles: List[NewsArticle] = Field(
        default_factory=list,
        description="Liste des articles"
    )
    events: List[MarketEvent] = Field(
        default_factory=list,
        description="Liste des événements"
    )
    symbols: List[Symbol] = Field(
        default_factory=list,
        description="Symboles couverts"
    )
    start_date: Optional[datetime] = Field(
        None,
        description="Date de début de la collection"
    )
    end_date: Optional[datetime] = Field(
        None,
        description="Date de fin de la collection"
    )
    
    def add_article(self, article: NewsArticle) -> None:
        """Ajoute un article à la collection."""
        self.articles.append(article)
        
        # Met à jour les symboles et dates
        for symbol in article.symbols:
            if symbol not in self.symbols:
                self.symbols.append(symbol)
        
        if not self.start_date or article.published_at < self.start_date:
            self.start_date = article.published_at
        if not self.end_date or article.published_at > self.end_date:
            self.end_date = article.published_at

    def add_event(self, event: MarketEvent) -> None:
        """Ajoute un événement à la collection."""
        self.events.append(event)
        
        if event.symbol not in self.symbols:
            self.symbols.append(event.symbol)

    def get_articles_for_symbol(self, symbol: str) -> List[NewsArticle]:
        """Récupère tous les articles pour un symbole."""
        return [
            article for article in self.articles
            if any(s.symbol == symbol.upper() for s in article.symbols)
        ]

    def get_recent_articles(self, hours: int = 24) -> List[NewsArticle]:
        """Récupère les articles récents."""
        cutoff = arrow.utcnow().shift(hours=-hours).datetime
        return [
            article for article in self.articles
            if article.published_at >= cutoff
        ]

    def get_high_impact_articles(self) -> List[NewsArticle]:
        """Récupère les articles à fort impact."""
        return [
            article for article in self.articles
            if article.is_high_impact
        ]

    def analyze_sentiment_for_symbol(self, symbol: str, hours: int = 24) -> Optional[SentimentAnalysis]:
        """Analyse le sentiment pour un symbole."""
        articles = self.get_articles_for_symbol(symbol)
        recent_articles = [
            article for article in articles
            if article.is_recent(hours)
        ]
        
        if not recent_articles:
            return None
        
        # Calcule les métriques de sentiment
        sentiments = [
            article.sentiment_score for article in recent_articles
            if article.sentiment_score is not None
        ]
        
        if not sentiments:
            return None
        
        symbol_obj = next((s for s in self.symbols if s.symbol == symbol.upper()), None)
        if not symbol_obj:
            return None
        
        avg_sentiment = sum(sentiments) / len(sentiments)
        confidence = min(1.0, len(sentiments) / 10)  # Plus d'articles = plus de confiance
        
        return SentimentAnalysis(
            symbol=symbol_obj,
            period_hours=hours,
            total_articles=len(recent_articles),
            average_sentiment=avg_sentiment,
            confidence_score=confidence
        )

    def __len__(self) -> int:
        """Retourne le nombre total d'articles et événements."""
        return len(self.articles) + len(self.events)

    def __str__(self) -> str:
        """Représentation textuelle de la collection."""
        return f"NewsCollection: {len(self.articles)} articles, {len(self.events)} events"