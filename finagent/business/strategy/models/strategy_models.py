"""
Modèles Pydantic pour les configurations de stratégies.

Ce module définit tous les modèles de données nécessaires pour valider
et structurer les fichiers de configuration de stratégies YAML.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field, field_validator, model_validator


class StrategyType(str, Enum):
    """Types de stratégies supportées."""
    TECHNICAL = "technical"
    FUNDAMENTAL = "fundamental"
    SENTIMENT = "sentiment"
    HYBRID = "hybrid"


class RiskTolerance(str, Enum):
    """Niveaux de tolérance au risque."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TimeHorizon(str, Enum):
    """Horizons temporels d'investissement."""
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"


class MarketCap(str, Enum):
    """Tailles de capitalisation boursière."""
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


class PositionSizingMethod(str, Enum):
    """Méthodes de dimensionnement des positions."""
    FIXED_PERCENTAGE = "fixed_percentage"
    VOLATILITY_BASED = "volatility_based"
    KELLY = "kelly"


class StopLossType(str, Enum):
    """Types de stop-loss."""
    PERCENTAGE = "percentage"
    ATR_BASED = "atr_based"
    TECHNICAL = "technical"


class StrategyStatus(str, Enum):
    """Statuts possibles d'une stratégie."""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"
    ARCHIVED = "archived"


class RiskLevel(str, Enum):
    """Niveaux de risque."""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class StrategySettings(BaseModel):
    """Paramètres généraux de la stratégie."""
    risk_tolerance: RiskTolerance = Field(
        default=RiskTolerance.MEDIUM,
        description="Niveau de tolérance au risque"
    )
    time_horizon: TimeHorizon = Field(
        default=TimeHorizon.MEDIUM,
        description="Horizon temporel d'investissement"
    )
    max_positions: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Nombre maximum de positions simultanées"
    )
    position_size: Decimal = Field(
        default=Decimal("0.1"),
        ge=Decimal("0.01"),
        le=Decimal("1.0"),
        description="Taille de position par défaut (en fraction du capital)"
    )

    @field_validator('position_size', mode='before')
    def validate_position_size(cls, v):
        if isinstance(v, (int, float)):
            return Decimal(str(v))
        return v


class Instrument(BaseModel):
    """Instrument financier."""
    symbol: str = Field(description="Symbole de l'instrument")
    name: str = Field(description="Nom de l'instrument")
    sector: Optional[str] = Field(default=None, description="Secteur d'activité")
    weight: Optional[float] = Field(default=None, description="Poids dans le portefeuille")


class StrategyUniverse(BaseModel):
    """Définition de l'univers d'investissement."""
    instruments: Optional[List[Instrument]] = Field(
        default=None,
        description="Liste des instruments spécifiques"
    )
    watchlist: Optional[List[str]] = Field(
        default=None,
        description="Liste des symboles à surveiller"
    )
    sectors: Optional[List[str]] = Field(
        default=None,
        description="Secteurs d'activité ciblés"
    )
    market_cap: Optional[MarketCap] = Field(
        default=None,
        description="Taille de capitalisation ciblée"
    )
    exclude_symbols: Optional[List[str]] = Field(
        default=None,
        description="Symboles à exclure"
    )
    min_price: Optional[Decimal] = Field(
        default=None,
        ge=Decimal("0.01"),
        description="Prix minimum pour inclusion"
    )
    min_volume: Optional[int] = Field(
        default=None,
        ge=1000,
        description="Volume minimum pour inclusion"
    )

    @field_validator('watchlist', 'exclude_symbols', mode='after')
    def validate_symbols(cls, v):
        if v is not None:
            # Convertir en majuscules et valider le format
            return [symbol.upper().strip() for symbol in v if symbol.strip()]
        return v


class TechnicalAnalysis(BaseModel):
    """Configuration de l'analyse technique."""
    type: str = Field(description="Type d'indicateur technique")
    weight: Decimal = Field(
        default=Decimal("1.0"),
        ge=Decimal("0.0"),
        le=Decimal("1.0"),
        description="Poids de l'indicateur dans l'analyse"
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Paramètres spécifiques à l'indicateur"
    )

    @field_validator('weight', mode='before')
    def validate_weight(cls, v):
        if isinstance(v, (int, float)):
            return Decimal(str(v))
        return v


class FundamentalAnalysis(BaseModel):
    """Configuration de l'analyse fondamentale."""
    type: str = Field(description="Type d'indicateur fondamental")
    weight: Decimal = Field(
        default=Decimal("1.0"),
        ge=Decimal("0.0"),
        le=Decimal("1.0"),
        description="Poids de l'indicateur dans l'analyse"
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Paramètres spécifiques à l'indicateur"
    )

    @field_validator('weight', mode='before')
    def validate_weight(cls, v):
        if isinstance(v, (int, float)):
            return Decimal(str(v))
        return v


class SentimentAnalysis(BaseModel):
    """Configuration de l'analyse de sentiment."""
    type: str = Field(description="Type d'indicateur de sentiment")
    weight: Decimal = Field(
        default=Decimal("1.0"),
        ge=Decimal("0.0"),
        le=Decimal("1.0"),
        description="Poids de l'indicateur dans l'analyse"
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Paramètres spécifiques à l'indicateur"
    )

    @field_validator('weight', mode='before')
    def validate_weight(cls, v):
        if isinstance(v, (int, float)):
            return Decimal(str(v))
        return v


class StrategyAnalysis(BaseModel):
    """Configuration de l'analyse de la stratégie."""
    technical: Optional[List[TechnicalAnalysis]] = Field(
        default=None,
        description="Indicateurs d'analyse technique"
    )
    fundamental: Optional[List[FundamentalAnalysis]] = Field(
        default=None,
        description="Indicateurs d'analyse fondamentale"
    )
    sentiment: Optional[List[SentimentAnalysis]] = Field(
        default=None,
        description="Indicateurs d'analyse de sentiment"
    )

    @model_validator(mode='before')
    def validate_at_least_one_analysis(cls, data):
        """Valide qu'au moins un type d'analyse est défini."""
        technical = data.get('technical')
        fundamental = data.get('fundamental')
        sentiment = data.get('sentiment')
        
        if not any([technical, fundamental, sentiment]):
            raise ValueError("Au moins un type d'analyse doit être défini")
        
        return data

    @field_validator('technical', 'fundamental', 'sentiment', mode='after')
    def validate_analysis_weights(cls, v):
        """Valide que la somme des poids ne dépasse pas 1.0."""
        if v is not None and len(v) > 0:
            total_weight = sum(item.weight for item in v)
            if total_weight > Decimal("1.0"):
                raise ValueError(f"La somme des poids ({total_weight}) ne peut pas dépasser 1.0")
        return v


class PositionSizing(BaseModel):
    """Configuration du dimensionnement des positions."""
    method: PositionSizingMethod = Field(
        default=PositionSizingMethod.FIXED_PERCENTAGE,
        description="Méthode de dimensionnement"
    )
    value: Decimal = Field(
        description="Valeur du paramètre de dimensionnement"
    )

    @field_validator('value', mode='before')
    def validate_value(cls, v):
        if isinstance(v, (int, float)):
            return Decimal(str(v))
        return v


class StopLoss(BaseModel):
    """Configuration du stop-loss."""
    type: StopLossType = Field(
        default=StopLossType.PERCENTAGE,
        description="Type de stop-loss"
    )
    value: Decimal = Field(
        description="Valeur du stop-loss"
    )

    @field_validator('value', mode='before')
    def validate_value(cls, v):
        if isinstance(v, (int, float)):
            return Decimal(str(v))
        return v


class TakeProfit(BaseModel):
    """Configuration du take-profit."""
    type: StopLossType = Field(
        default=StopLossType.PERCENTAGE,
        description="Type de take-profit"
    )
    value: Decimal = Field(
        description="Valeur du take-profit"
    )

    @field_validator('value', mode='before')
    def validate_value(cls, v):
        if isinstance(v, (int, float)):
            return Decimal(str(v))
        return v


class StrategyRiskManagement(BaseModel):
    """Configuration de la gestion des risques."""
    position_sizing: PositionSizing = Field(
        description="Configuration du dimensionnement des positions"
    )
    stop_loss: Optional[StopLoss] = Field(
        default=None,
        description="Configuration du stop-loss"
    )
    take_profit: Optional[TakeProfit] = Field(
        default=None,
        description="Configuration du take-profit"
    )
    max_drawdown: Optional[Decimal] = Field(
        default=None,
        ge=Decimal("0.01"),
        le=Decimal("1.0"),
        description="Drawdown maximum autorisé"
    )
    max_correlation: Optional[Decimal] = Field(
        default=None,
        ge=Decimal("0.0"),
        le=Decimal("1.0"),
        description="Corrélation maximum entre positions"
    )

    @field_validator('max_drawdown', 'max_correlation', mode='before')
    def validate_decimal_fields(cls, v):
        if v is not None and isinstance(v, (int, float)):
            return Decimal(str(v))
        return v


class StrategyBacktesting(BaseModel):
    """Configuration du backtesting."""
    start_date: str = Field(
        description="Date de début du backtest (YYYY-MM-DD)"
    )
    end_date: str = Field(
        description="Date de fin du backtest (YYYY-MM-DD)"
    )
    initial_capital: Decimal = Field(
        default=Decimal("100000"),
        ge=Decimal("1000"),
        description="Capital initial"
    )
    commission: Decimal = Field(
        default=Decimal("0.001"),
        ge=Decimal("0.0"),
        le=Decimal("0.1"),
        description="Commission par transaction"
    )
    slippage: Optional[Decimal] = Field(
        default=Decimal("0.0005"),
        ge=Decimal("0.0"),
        le=Decimal("0.1"),
        description="Slippage par transaction"
    )
    benchmark: Optional[str] = Field(
        default="SPY",
        description="Symbole de référence pour comparaison"
    )

    @field_validator('initial_capital', 'commission', 'slippage', mode='before')
    def validate_decimal_fields(cls, v):
        if v is not None and isinstance(v, (int, float)):
            return Decimal(str(v))
        return v

    @field_validator('start_date', 'end_date', mode='after')
    def validate_dates(cls, v):
        """Valide le format des dates."""
        try:
            datetime.strptime(v, '%Y-%m-%d')
        except ValueError:
            raise ValueError(f"Format de date invalide: {v}. Utilisez YYYY-MM-DD")
        return v

    @model_validator(mode='before')
    def validate_date_order(cls, data):
        """Valide que la date de fin est postérieure à la date de début."""
        start = data.get('start_date')
        end = data.get('end_date')
        
        if start and end:
            start_dt = datetime.strptime(start, '%Y-%m-%d')
            end_dt = datetime.strptime(end, '%Y-%m-%d')
            
            if end_dt <= start_dt:
                raise ValueError("La date de fin doit être postérieure à la date de début")
        
        return data


class StrategyAlerts(BaseModel):
    """Configuration des alertes et notifications."""
    buy_signals: bool = Field(
        default=True,
        description="Activer les alertes pour les signaux d'achat"
    )
    sell_signals: bool = Field(
        default=True,
        description="Activer les alertes pour les signaux de vente"
    )
    risk_warnings: bool = Field(
        default=True,
        description="Activer les alertes de risque"
    )
    performance_updates: bool = Field(
        default=False,
        description="Activer les mises à jour de performance"
    )
    email_notifications: bool = Field(
        default=False,
        description="Activer les notifications par email"
    )


class StrategyConfig(BaseModel):
    """Configuration complète d'une stratégie."""
    name: str = Field(
        min_length=1,
        max_length=100,
        description="Nom de la stratégie"
    )
    version: str = Field(
        default="1.0",
        pattern=r"^\d+\.\d+(\.\d+)?$",
        description="Version de la stratégie"
    )
    author: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Auteur de la stratégie"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Description de la stratégie"
    )
    type: StrategyType = Field(
        description="Type de stratégie"
    )
    template: Optional[str] = Field(
        default=None,
        description="Template de base utilisé"
    )
    created_at: Optional[datetime] = Field(
        default_factory=datetime.now,
        description="Date de création"
    )
    updated_at: Optional[datetime] = Field(
        default_factory=datetime.now,
        description="Date de dernière modification"
    )


class Strategy(BaseModel):
    """Modèle complet d'une stratégie de trading."""
    strategy: StrategyConfig = Field(
        description="Configuration de base de la stratégie"
    )
    settings: Optional[StrategySettings] = Field(
        default_factory=StrategySettings,
        description="Paramètres généraux"
    )
    universe: Optional[StrategyUniverse] = Field(
        default=None,
        description="Univers d'investissement"
    )
    analysis: StrategyAnalysis = Field(
        description="Configuration de l'analyse"
    )
    rules: Dict[str, Any] = Field(
        description="Règles de trading (défini dans rule_models)"
    )
    risk_management: StrategyRiskManagement = Field(
        description="Gestion des risques"
    )
    backtesting: Optional[StrategyBacktesting] = Field(
        default=None,
        description="Configuration du backtesting"
    )
    alerts: Optional[StrategyAlerts] = Field(
        default_factory=StrategyAlerts,
        description="Configuration des alertes"
    )

    class Config:
        """Configuration Pydantic."""
        validate_assignment = True
        arbitrary_types_allowed = True
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }

    @model_validator(mode='before')
    def validate_strategy_consistency(cls, data):
        """Valide la cohérence globale de la stratégie."""
        settings = data.get('settings')
        risk_mgmt = data.get('risk_management')
        
        if settings and risk_mgmt:
            # Vérifier que position_size * max_positions <= 1.0
            total_exposure = settings.position_size * settings.max_positions
            if total_exposure > Decimal("1.0"):
                raise ValueError(
                    f"L'exposition totale ({total_exposure}) ne peut pas dépasser 100% du capital"
                )
        
        return data

    def dict(self, **kwargs) -> Dict[str, Any]:
        """Convertit en dictionnaire avec encodage des types spéciaux."""
        data = super().dict(**kwargs)
        return self._encode_decimals_and_dates(data)

    def _encode_decimals_and_dates(self, obj: Any) -> Any:
        """Encode récursivement les Decimal et datetime en strings."""
        if isinstance(obj, dict):
            return {k: self._encode_decimals_and_dates(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._encode_decimals_and_dates(item) for item in obj]
        elif isinstance(obj, Decimal):
            return str(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        else:
            return obj
class StrategyPerformance(BaseModel):
    """Métriques de performance d'une stratégie."""
    total_return: Optional[Decimal] = Field(
        default=None,
        description="Rendement total"
    )
    annual_return: Optional[Decimal] = Field(
        default=None,
        description="Rendement annualisé"
    )
    volatility: Optional[Decimal] = Field(
        default=None,
        description="Volatilité annualisée"
    )
    sharpe_ratio: Optional[Decimal] = Field(
        default=None,
        description="Ratio de Sharpe"
    )
    max_drawdown: Optional[Decimal] = Field(
        default=None,
        description="Perte maximale"
    )
    win_rate: Optional[Decimal] = Field(
        default=None,
        description="Taux de réussite"
    )
    trades_count: Optional[int] = Field(
        default=None,
        description="Nombre de trades"
    )
    last_updated: Optional[datetime] = Field(
        default=None,
        description="Dernière mise à jour"
    )

    @field_validator('total_return', 'annual_return', 'volatility', 'sharpe_ratio', 'max_drawdown', 'win_rate', mode='before')
    def validate_decimal_fields(cls, v):
        if v is not None and isinstance(v, (int, float)):
            return Decimal(str(v))
        return v

    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat() if v else None
        }