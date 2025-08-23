"""
Modèles pour l'analyse financière par IA.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import Field, validator

from .base import BaseAIModel, ConfidenceLevel


class AnalysisType(str, Enum):
    """Types d'analyse financière."""
    TECHNICAL = "technical"
    FUNDAMENTAL = "fundamental"
    SENTIMENT = "sentiment"
    RISK = "risk"
    MARKET_OVERVIEW = "market_overview"
    SECTOR_ANALYSIS = "sector_analysis"


class TrendDirection(str, Enum):
    """Direction de la tendance."""
    STRONG_BULLISH = "strong_bullish"
    BULLISH = "bullish"
    NEUTRAL = "neutral"
    BEARISH = "bearish"
    STRONG_BEARISH = "strong_bearish"


class MarketSentiment(str, Enum):
    """Sentiment du marché."""
    EXTREMELY_FEARFUL = "extremely_fearful"
    FEARFUL = "fearful"
    NEUTRAL = "neutral"
    GREEDY = "greedy"
    EXTREMELY_GREEDY = "extremely_greedy"


class RiskLevel(str, Enum):
    """Niveau de risque."""
    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


class MarketContext(BaseAIModel):
    """Contexte du marché pour l'analyse."""
    
    symbol: str = Field(min_length=1, max_length=10)
    current_price: Decimal = Field(gt=0)
    market_cap: Optional[Decimal] = None
    volume_24h: Optional[Decimal] = None
    
    # Données techniques
    price_change_24h: Optional[Decimal] = None
    price_change_7d: Optional[Decimal] = None
    price_change_30d: Optional[Decimal] = None
    
    # Indicateurs techniques
    rsi: Optional[float] = Field(None, ge=0, le=100)
    macd: Optional[float] = None
    moving_avg_50: Optional[Decimal] = None
    moving_avg_200: Optional[Decimal] = None
    bollinger_upper: Optional[Decimal] = None
    bollinger_lower: Optional[Decimal] = None
    
    # Données fondamentales
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    debt_to_equity: Optional[float] = None
    roe: Optional[float] = None
    revenue_growth: Optional[float] = None
    
    # Sentiment et nouvelles
    news_sentiment: Optional[MarketSentiment] = None
    social_sentiment: Optional[MarketSentiment] = None
    analyst_rating: Optional[str] = None
    
    # Contexte temporel
    analysis_timestamp: datetime = Field(default_factory=datetime.utcnow)
    market_session: Optional[str] = None  # "pre_market", "regular", "after_hours"
    
    @validator('symbol')
    def validate_symbol(cls, v):
        """Valide le symbole."""
        return v.upper().strip()


class TechnicalIndicators(BaseAIModel):
    """Indicateurs techniques détaillés."""
    
    # Momentum
    rsi: Optional[float] = Field(None, ge=0, le=100)
    stoch_k: Optional[float] = Field(None, ge=0, le=100)
    stoch_d: Optional[float] = Field(None, ge=0, le=100)
    williams_r: Optional[float] = Field(None, ge=-100, le=0)
    
    # Trend
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_histogram: Optional[float] = None
    adx: Optional[float] = Field(None, ge=0, le=100)
    
    # Volatility
    bollinger_upper: Optional[Decimal] = None
    bollinger_middle: Optional[Decimal] = None
    bollinger_lower: Optional[Decimal] = None
    atr: Optional[float] = Field(None, ge=0)
    
    # Volume
    volume_sma: Optional[Decimal] = None
    volume_ratio: Optional[float] = None
    
    # Moving Averages
    sma_20: Optional[Decimal] = None
    sma_50: Optional[Decimal] = None
    sma_200: Optional[Decimal] = None
    ema_12: Optional[Decimal] = None
    ema_26: Optional[Decimal] = None


class FundamentalMetrics(BaseAIModel):
    """Métriques fondamentales."""
    
    # Valorisation
    pe_ratio: Optional[float] = None
    pe_forward: Optional[float] = None
    pb_ratio: Optional[float] = None
    ps_ratio: Optional[float] = None
    pcf_ratio: Optional[float] = None
    
    # Profitabilité
    roe: Optional[float] = None
    roa: Optional[float] = None
    gross_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    net_margin: Optional[float] = None
    
    # Croissance
    revenue_growth_yoy: Optional[float] = None
    earnings_growth_yoy: Optional[float] = None
    revenue_growth_qoq: Optional[float] = None
    earnings_growth_qoq: Optional[float] = None
    
    # Solidité financière
    debt_to_equity: Optional[float] = None
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None
    interest_coverage: Optional[float] = None
    
    # Dividendes
    dividend_yield: Optional[float] = None
    payout_ratio: Optional[float] = None
    dividend_growth: Optional[float] = None


class SentimentData(BaseAIModel):
    """Données de sentiment."""
    
    # Sentiment des nouvelles
    news_sentiment: MarketSentiment
    news_score: float = Field(ge=-1.0, le=1.0)
    news_count: int = Field(ge=0)
    
    # Sentiment des analystes
    analyst_sentiment: Optional[MarketSentiment] = None
    analyst_upgrades: int = Field(default=0, ge=0)
    analyst_downgrades: int = Field(default=0, ge=0)
    analyst_target_price: Optional[Decimal] = None
    
    # Sentiment social/retail
    social_sentiment: Optional[MarketSentiment] = None
    social_mentions: int = Field(default=0, ge=0)
    social_score: Optional[float] = Field(None, ge=-1.0, le=1.0)
    
    # Indicateurs de marché
    fear_greed_index: Optional[int] = Field(None, ge=0, le=100)
    vix_level: Optional[float] = None
    put_call_ratio: Optional[float] = None


class AnalysisRequest(BaseAIModel):
    """Requête d'analyse financière."""
    
    request_id: UUID = Field(default_factory=uuid4)
    analysis_type: AnalysisType
    market_context: MarketContext
    technical_indicators: Optional[TechnicalIndicators] = None
    fundamental_metrics: Optional[FundamentalMetrics] = None
    sentiment_data: Optional[SentimentData] = None
    
    # Paramètres d'analyse
    time_horizon: str = Field(default="1d")  # "1h", "1d", "1w", "1m", "3m", "1y"
    include_risk_analysis: bool = Field(default=True)
    include_sector_comparison: bool = Field(default=False)
    custom_context: Optional[str] = None
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AnalysisResult(BaseAIModel):
    """Résultat d'analyse financière."""
    
    request_id: UUID
    analysis_id: UUID = Field(default_factory=uuid4)
    analysis_type: AnalysisType
    symbol: str
    
    # Résultats principaux
    overall_trend: TrendDirection
    confidence: ConfidenceLevel
    risk_level: RiskLevel
    
    # Analyses détaillées
    technical_analysis: Optional[str] = None
    fundamental_analysis: Optional[str] = None
    sentiment_analysis: Optional[str] = None
    risk_analysis: Optional[str] = None
    
    # Scores et métriques
    bullish_score: float = Field(ge=0.0, le=1.0)
    bearish_score: float = Field(ge=0.0, le=1.0)
    technical_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    fundamental_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    sentiment_score: Optional[float] = Field(None, ge=-1.0, le=1.0)
    
    # Niveaux de support et résistance
    support_levels: List[Decimal] = Field(default_factory=list)
    resistance_levels: List[Decimal] = Field(default_factory=list)
    
    # Prix cibles
    target_price_bull: Optional[Decimal] = None
    target_price_bear: Optional[Decimal] = None
    stop_loss_level: Optional[Decimal] = None
    
    # Facteurs clés
    key_drivers: List[str] = Field(default_factory=list)
    risk_factors: List[str] = Field(default_factory=list)
    opportunities: List[str] = Field(default_factory=list)
    
    # Métadonnées
    processing_time: float = Field(default=0.0, ge=0.0)
    model_used: str
    tokens_used: int = Field(default=0, ge=0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('bullish_score', 'bearish_score')
    def validate_scores_sum(cls, v, values):
        """Valide que les scores bullish + bearish <= 1.0."""
        if 'bullish_score' in values:
            total = v + values['bullish_score']
            if total > 1.0:
                raise ValueError("La somme des scores bullish et bearish ne peut pas dépasser 1.0")
        return v


class MarketOverview(BaseAIModel):
    """Vue d'ensemble du marché."""
    
    overview_id: UUID = Field(default_factory=uuid4)
    market_session: str
    overall_sentiment: MarketSentiment
    volatility_level: RiskLevel
    
    # Indices principaux
    sp500_change: Optional[float] = None
    nasdaq_change: Optional[float] = None
    dow_change: Optional[float] = None
    vix_level: Optional[float] = None
    
    # Secteurs leaders et perdants
    leading_sectors: List[str] = Field(default_factory=list)
    lagging_sectors: List[str] = Field(default_factory=list)
    
    # Événements importants
    key_events: List[str] = Field(default_factory=list)
    economic_releases: List[str] = Field(default_factory=list)
    
    # Analyse générale
    market_summary: str
    outlook: str
    key_themes: List[str] = Field(default_factory=list)
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)