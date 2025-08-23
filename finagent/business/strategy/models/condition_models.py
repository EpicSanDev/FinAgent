"""
Modèles Pydantic pour les conditions et indicateurs de trading.

Ce module définit les modèles spécifiques pour chaque type d'indicateur
technique, fondamental et de sentiment utilisé dans les stratégies.
"""

from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field, field_validator


class IndicatorType(str, Enum):
    """Types d'indicateurs supportés."""
    # Indicateurs techniques
    RSI = "rsi"
    MACD = "macd"
    STOCHASTIC = "stochastic"
    SMA = "sma"
    EMA = "ema"
    BOLLINGER_BANDS = "bollinger_bands"
    ATR = "atr"
    ADX = "adx"
    CCI = "cci"
    WILLIAMS_R = "williams_r"
    ROC = "roc"
    MFI = "mfi"
    OBV = "obv"
    VWAP = "vwap"
    VOLUME_PROFILE = "volume_profile"
    FIBONACCI = "fibonacci"
    SUPPORT_RESISTANCE = "support_resistance"
    
    # Indicateurs fondamentaux
    PE_RATIO = "pe_ratio"
    PEG_RATIO = "peg_ratio"
    PRICE_TO_BOOK = "price_to_book"
    PRICE_TO_SALES = "price_to_sales"
    DEBT_TO_EQUITY = "debt_to_equity"
    CURRENT_RATIO = "current_ratio"
    QUICK_RATIO = "quick_ratio"
    ROE = "roe"
    ROA = "roa"
    ROIC = "roic"
    REVENUE_GROWTH = "revenue_growth"
    EARNINGS_GROWTH = "earnings_growth"
    FREE_CASH_FLOW = "free_cash_flow"
    DIVIDEND_YIELD = "dividend_yield"
    
    # Indicateurs de sentiment
    NEWS_SENTIMENT = "news_sentiment"
    SOCIAL_SENTIMENT = "social_sentiment"
    VIX = "vix"
    PUT_CALL_RATIO = "put_call_ratio"
    INSIDER_TRADING = "insider_trading"
    ANALYST_RECOMMENDATIONS = "analyst_recommendations"


class ComparisonOperator(str, Enum):
    """Opérateurs de comparaison pour les conditions."""
    EQUAL = "equal"
    NOT_EQUAL = "not_equal"
    GREATER = "greater"
    GREATER_EQUAL = "greater_equal"
    LESS = "less"
    LESS_EQUAL = "less_equal"
    BETWEEN = "between"
    OUTSIDE = "outside"
    CROSSOVER_UP = "crossover_up"
    CROSSOVER_DOWN = "crossover_down"
    ABOVE_THRESHOLD = "above_threshold"
    BELOW_THRESHOLD = "below_threshold"


class TrendDirection(str, Enum):
    """Direction de tendance."""
    UP = "up"
    DOWN = "down"
    SIDEWAYS = "sideways"
    UNKNOWN = "unknown"


class VolatilityLevel(str, Enum):
    """Niveaux de volatilité."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"


class BaseCondition(BaseModel):
    """Condition de base pour l'évaluation des indicateurs."""
    indicator_type: IndicatorType = Field(
        description="Type d'indicateur"
    )
    operator: ComparisonOperator = Field(
        description="Opérateur de comparaison"
    )
    threshold: Optional[Union[float, int, List[Union[float, int]]]] = Field(
        default=None,
        description="Seuil de comparaison"
    )
    timeframe: str = Field(
        default="1d",
        description="Timeframe d'évaluation"
    )
    lookback_period: int = Field(
        default=1,
        ge=1,
        description="Période de lookback"
    )
    weight: Decimal = Field(
        default=Decimal("1.0"),
        ge=Decimal("0.0"),
        le=Decimal("1.0"),
        description="Poids dans l'évaluation"
    )

    @field_validator('weight', mode='before')
    def validate_weight(cls, v):
        if isinstance(v, (int, float)):
            return Decimal(str(v))
        return v


class TechnicalIndicator(BaseModel):
    """Configuration d'un indicateur technique."""
    type: IndicatorType = Field(
        description="Type d'indicateur technique"
    )
    parameters: Dict[str, Union[int, float, str]] = Field(
        description="Paramètres de l'indicateur"
    )
    timeframe: str = Field(
        default="1d",
        description="Timeframe pour le calcul"
    )

    class Config:
        """Configuration Pydantic."""
        validate_assignment = True


class RSIIndicator(TechnicalIndicator):
    """Indicateur RSI (Relative Strength Index)."""
    type: IndicatorType = Field(default=IndicatorType.RSI, )
    period: int = Field(
        default=14,
        ge=2,
        le=100,
        description="Période de calcul du RSI"
    )
    oversold_threshold: Decimal = Field(
        default=Decimal("30"),
        ge=Decimal("0"),
        le=Decimal("50"),
        description="Seuil de survente"
    )
    overbought_threshold: Decimal = Field(
        default=Decimal("70"),
        ge=Decimal("50"),
        le=Decimal("100"),
        description="Seuil de surachat"
    )

    @field_validator('oversold_threshold', 'overbought_threshold', mode='before')
    def validate_decimal_fields(cls, v):
        if isinstance(v, (int, float)):
            return Decimal(str(v))
        return v

    @field_validator('overbought_threshold', mode='after')
    def validate_thresholds(cls, v, info):
        oversold = info.data.get('oversold_threshold')
        if oversold and v <= oversold:
            raise ValueError("Le seuil de surachat doit être supérieur au seuil de survente")
        return v


class MACDIndicator(TechnicalIndicator):
    """Indicateur MACD (Moving Average Convergence Divergence)."""
    type: IndicatorType = Field(default=IndicatorType.MACD, )
    fast_period: int = Field(
        default=12,
        ge=1,
        description="Période de l'EMA rapide"
    )
    slow_period: int = Field(
        default=26,
        ge=1,
        description="Période de l'EMA lente"
    )
    signal_period: int = Field(
        default=9,
        ge=1,
        description="Période de la ligne de signal"
    )

    @field_validator('slow_period', mode='after')
    def validate_periods(cls, v, info):
        fast_period = info.data.get('fast_period')
        if fast_period and v <= fast_period:
            raise ValueError("La période lente doit être supérieure à la période rapide")
        return v


class MovingAverageIndicator(TechnicalIndicator):
    """Indicateur de moyenne mobile."""
    type: IndicatorType = Field(
        description="Type de moyenne mobile (SMA ou EMA)"
    )
    period: int = Field(
        default=20,
        ge=1,
        le=200,
        description="Période de la moyenne mobile"
    )
    source: str = Field(
        default="close",
        description="Source des données (open, high, low, close)"
    )


class BollingerBandsIndicator(TechnicalIndicator):
    """Indicateur Bollinger Bands."""
    type: IndicatorType = Field(default=IndicatorType.BOLLINGER_BANDS, )
    period: int = Field(
        default=20,
        ge=5,
        le=50,
        description="Période de la moyenne mobile"
    )
    std_deviation: Decimal = Field(
        default=Decimal("2.0"),
        ge=Decimal("0.5"),
        le=Decimal("3.0"),
        description="Nombre d'écarts-types"
    )

    @field_validator('std_deviation', mode='before')
    def validate_std_deviation(cls, v):
        if isinstance(v, (int, float)):
            return Decimal(str(v))
        return v


class VolumeIndicator(TechnicalIndicator):
    """Indicateur de volume."""
    type: IndicatorType = Field(
        description="Type d'indicateur de volume"
    )
    analysis_type: str = Field(
        default="surge",
        description="Type d'analyse (surge, average, profile)"
    )
    threshold_multiplier: Decimal = Field(
        default=Decimal("1.5"),
        ge=Decimal("0.1"),
        description="Multiplicateur pour la comparaison"
    )

    @field_validator('threshold_multiplier', mode='before')
    def validate_multiplier(cls, v):
        if isinstance(v, (int, float)):
            return Decimal(str(v))
        return v


class FundamentalIndicator(BaseModel):
    """Configuration d'un indicateur fondamental."""
    type: IndicatorType = Field(
        description="Type d'indicateur fondamental"
    )
    period: str = Field(
        default="ttm",
        description="Période (quarterly, annual, ttm)"
    )
    comparison_method: str = Field(
        default="absolute",
        description="Méthode de comparaison (absolute, relative, peer)"
    )

    class Config:
        """Configuration Pydantic."""
        validate_assignment = True


class ValuationIndicator(FundamentalIndicator):
    """Indicateur de valorisation."""
    min_value: Optional[Decimal] = Field(
        default=None,
        description="Valeur minimum acceptable"
    )
    max_value: Optional[Decimal] = Field(
        default=None,
        description="Valeur maximum acceptable"
    )
    sector_adjustment: bool = Field(
        default=False,
        description="Ajustement selon le secteur"
    )

    @field_validator('min_value', 'max_value', mode='before')
    def validate_decimal_fields(cls, v):
        if v is not None and isinstance(v, (int, float)):
            return Decimal(str(v))
        return v


class GrowthIndicator(FundamentalIndicator):
    """Indicateur de croissance."""
    min_growth_rate: Decimal = Field(
        description="Taux de croissance minimum"
    )
    consistency_periods: int = Field(
        default=4,
        ge=1,
        description="Nombre de périodes pour vérifier la consistance"
    )
    compound_growth: bool = Field(
        default=True,
        description="Utiliser le taux de croissance composé"
    )

    @field_validator('min_growth_rate', mode='before')
    def validate_growth_rate(cls, v):
        if isinstance(v, (int, float)):
            return Decimal(str(v))
        return v


class SentimentIndicator(BaseModel):
    """Configuration d'un indicateur de sentiment."""
    type: IndicatorType = Field(
        description="Type d'indicateur de sentiment"
    )
    source: Optional[str] = Field(
        default=None,
        description="Source des données de sentiment"
    )
    confidence_threshold: Decimal = Field(
        default=Decimal("0.6"),
        ge=Decimal("0.0"),
        le=Decimal("1.0"),
        description="Seuil de confiance"
    )
    time_window: str = Field(
        default="1d",
        description="Fenêtre temporelle d'analyse"
    )

    @field_validator('confidence_threshold', mode='before')
    def validate_confidence(cls, v):
        if isinstance(v, (int, float)):
            return Decimal(str(v))
        return v

    class Config:
        """Configuration Pydantic."""
        validate_assignment = True


class NewsSentimentIndicator(SentimentIndicator):
    """Indicateur de sentiment des actualités."""
    type: IndicatorType = Field(default=IndicatorType.NEWS_SENTIMENT, )
    sources: List[str] = Field(
        default=["reuters", "bloomberg", "yahoo"],
        description="Sources d'actualités"
    )
    keywords: Optional[List[str]] = Field(
        default=None,
        description="Mots-clés à surveiller"
    )
    language: str = Field(
        default="en",
        description="Langue des actualités"
    )


class SocialSentimentIndicator(SentimentIndicator):
    """Indicateur de sentiment des réseaux sociaux."""
    type: IndicatorType = Field(default=IndicatorType.SOCIAL_SENTIMENT, )
    platforms: List[str] = Field(
        default=["twitter", "reddit"],
        description="Plateformes de réseaux sociaux"
    )
    hashtags: Optional[List[str]] = Field(
        default=None,
        description="Hashtags à surveiller"
    )
    influencer_weight: Decimal = Field(
        default=Decimal("1.5"),
        ge=Decimal("1.0"),
        description="Poids des influenceurs"
    )

    @field_validator('influencer_weight', mode='before')
    def validate_influencer_weight(cls, v):
        if isinstance(v, (int, float)):
            return Decimal(str(v))
        return v


class MarketConditionIndicator(BaseModel):
    """Indicateur de condition de marché."""
    trend_direction: Optional[TrendDirection] = Field(
        default=None,
        description="Direction de tendance attendue"
    )
    volatility_level: Optional[VolatilityLevel] = Field(
        default=None,
        description="Niveau de volatilité attendu"
    )
    market_regime: Optional[str] = Field(
        default=None,
        description="Régime de marché (bull, bear, sideways)"
    )
    correlation_threshold: Optional[Decimal] = Field(
        default=None,
        ge=Decimal("0.0"),
        le=Decimal("1.0"),
        description="Seuil de corrélation avec le marché"
    )

    @field_validator('correlation_threshold', mode='before')
    def validate_correlation(cls, v):
        if v is not None and isinstance(v, (int, float)):
            return Decimal(str(v))
        return v


class RiskMetricIndicator(BaseModel):
    """Indicateur de métrique de risque."""
    metric_type: str = Field(
        description="Type de métrique (var, cvar, sharpe, sortino)"
    )
    lookback_period: int = Field(
        default=252,
        ge=20,
        description="Période de lookback en jours"
    )
    confidence_level: Decimal = Field(
        default=Decimal("0.95"),
        ge=Decimal("0.90"),
        le=Decimal("0.99"),
        description="Niveau de confiance"
    )
    benchmark: Optional[str] = Field(
        default="SPY",
        description="Benchmark pour comparaison"
    )

    @field_validator('confidence_level', mode='before')
    def validate_confidence_level(cls, v):
        if isinstance(v, (int, float)):
            return Decimal(str(v))
        return v


class ConditionEvaluationResult(BaseModel):
    """Résultat de l'évaluation d'une condition."""
    condition_id: str = Field(
        description="Identifiant unique de la condition"
    )
    is_met: bool = Field(
        description="La condition est-elle remplie"
    )
    score: Decimal = Field(
        ge=Decimal("0.0"),
        le=Decimal("1.0"),
        description="Score de la condition"
    )
    confidence: Decimal = Field(
        ge=Decimal("0.0"),
        le=Decimal("1.0"),
        description="Niveau de confiance"
    )
    value: Optional[Union[float, int, str]] = Field(
        default=None,
        description="Valeur actuelle de l'indicateur"
    )
    threshold: Optional[Union[float, int, str]] = Field(
        default=None,
        description="Seuil de comparaison"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Métadonnées additionnelles"
    )

    @field_validator('score', 'confidence', mode='before')
    def validate_decimal_fields(cls, v):
        if isinstance(v, (int, float)):
            return Decimal(str(v))
        return v

    class Config:
        """Configuration Pydantic."""
        json_encoders = {
            Decimal: str
        }


class IndicatorCalculationResult(BaseModel):
    """Résultat du calcul d'un indicateur."""
    indicator_type: IndicatorType = Field(
        description="Type d'indicateur"
    )
    symbol: str = Field(
        description="Symbole financier"
    )
    timestamp: str = Field(
        description="Timestamp du calcul (ISO format)"
    )
    value: Union[float, int, Dict[str, Union[float, int]]] = Field(
        description="Valeur calculée de l'indicateur"
    )
    confidence: Decimal = Field(
        ge=Decimal("0.0"),
        le=Decimal("1.0"),
        description="Confiance dans le calcul"
    )
    parameters: Dict[str, Any] = Field(
        description="Paramètres utilisés pour le calcul"
    )
    data_quality: Optional[str] = Field(
        default=None,
        description="Qualité des données source"
    )

    @field_validator('confidence', mode='before')
    def validate_confidence(cls, v):
        if isinstance(v, (int, float)):
            return Decimal(str(v))
        return v

    class Config:
        """Configuration Pydantic."""
        json_encoders = {
            Decimal: str
        }