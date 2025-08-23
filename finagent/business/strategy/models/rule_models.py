"""
Modèles Pydantic pour les règles de trading.

Ce module définit les modèles pour structurer les règles d'achat, de vente
et les filtres dans les stratégies de trading.
"""

from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field, field_validator, model_validator


class RuleOperator(str, Enum):
    """Opérateurs logiques pour combiner les conditions."""
    AND = "AND"
    OR = "OR"
    NOT = "NOT"


class ConditionOperator(str, Enum):
    """Opérateurs de comparaison pour les conditions."""
    EQUAL = "=="
    NOT_EQUAL = "!="
    GREATER = ">"
    GREATER_EQUAL = ">="
    LESS = "<"
    LESS_EQUAL = "<="
    ABOVE = "above"
    BELOW = "below"
    CROSSOVER_UP = "crossover_up"
    CROSSOVER_DOWN = "crossover_down"
    BETWEEN = "between"
    OUTSIDE = "outside"


class MarketCondition(str, Enum):
    """Types de conditions de marché."""
    TRENDING = "trending"
    RANGING = "ranging"
    VOLATILE = "volatile"
    BULLISH = "bullish"
    BEARISH = "bearish"


class SignalType(str, Enum):
    """Types de signaux de trading."""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"


class BaseCondition(BaseModel):
    """Condition de base pour une règle."""
    indicator: str = Field(
        description="Nom de l'indicateur à évaluer"
    )
    operator: ConditionOperator = Field(
        description="Opérateur de comparaison"
    )
    value: Optional[Union[float, int, str, List[Union[float, int]]]] = Field(
        default=None,
        description="Valeur de référence pour la comparaison"
    )
    timeframe: Optional[str] = Field(
        default="1d",
        description="Timeframe pour l'évaluation (1m, 5m, 1h, 1d, etc.)"
    )
    lookback: Optional[int] = Field(
        default=1,
        ge=1,
        description="Nombre de périodes à regarder en arrière"
    )
    weight: Optional[Decimal] = Field(
        default=Decimal("1.0"),
        ge=Decimal("0.0"),
        le=Decimal("1.0"),
        description="Poids de cette condition dans l'évaluation globale"
    )

    @field_validator('weight', mode='before')
    def validate_weight(cls, v):
        if v is not None and isinstance(v, (int, float)):
            return Decimal(str(v))
        return v

    @field_validator('value', mode='after')
    def validate_value_for_operator(cls, v, info):
        """Valide que la valeur est cohérente avec l'opérateur."""
        operator = info.data.get('operator')
        
        if operator in [ConditionOperator.BETWEEN, ConditionOperator.OUTSIDE]:
            if not isinstance(v, list) or len(v) != 2:
                raise ValueError(f"L'opérateur {operator} nécessite une liste de 2 valeurs")
        elif operator in [ConditionOperator.CROSSOVER_UP, ConditionOperator.CROSSOVER_DOWN]:
            # Pour les crossovers, la valeur peut être optionnelle
            pass
        elif v is None:
            raise ValueError(f"L'opérateur {operator} nécessite une valeur")
        
        return v


class TechnicalCondition(BaseCondition):
    """Condition basée sur un indicateur technique."""
    parameters: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Paramètres additionnels pour l'indicateur"
    )


class FundamentalCondition(BaseCondition):
    """Condition basée sur un indicateur fondamental."""
    period: Optional[str] = Field(
        default="ttm",  # Trailing Twelve Months
        description="Période pour les données fondamentales (quarterly, annual, ttm)"
    )


class SentimentCondition(BaseCondition):
    """Condition basée sur l'analyse de sentiment."""
    source: Optional[str] = Field(
        default=None,
        description="Source des données de sentiment"
    )
    confidence_threshold: Optional[Decimal] = Field(
        default=Decimal("0.7"),
        ge=Decimal("0.0"),
        le=Decimal("1.0"),
        description="Seuil de confiance minimum"
    )

    @field_validator('confidence_threshold', mode='before')
    def validate_confidence(cls, v):
        if v is not None and isinstance(v, (int, float)):
            return Decimal(str(v))
        return v


class VolumeCondition(BaseCondition):
    """Condition basée sur le volume."""
    analysis_type: str = Field(
        default="surge",
        description="Type d'analyse volume (surge, average, profile)"
    )
    multiplier: Optional[Decimal] = Field(
        default=Decimal("1.5"),
        ge=Decimal("0.1"),
        description="Multiplicateur pour comparaison avec moyenne"
    )

    @field_validator('multiplier', mode='before')
    def validate_multiplier(cls, v):
        if v is not None and isinstance(v, (int, float)):
            return Decimal(str(v))
        return v


class PriceCondition(BaseCondition):
    """Condition basée sur le prix."""
    price_type: str = Field(
        default="close",
        description="Type de prix (open, high, low, close, vwap)"
    )


class RiskCondition(BaseCondition):
    """Condition de gestion des risques."""
    risk_type: str = Field(
        description="Type de risque (stop_loss, take_profit, max_drawdown)"
    )
    percentage: Optional[Decimal] = Field(
        default=None,
        ge=Decimal("0.0"),
        le=Decimal("1.0"),
        description="Pourcentage pour stop-loss/take-profit"
    )

    @field_validator('percentage', mode='before')
    def validate_percentage(cls, v):
        if v is not None and isinstance(v, (int, float)):
            return Decimal(str(v))
        return v


class FilterCondition(BaseModel):
    """Filtre pour valider les conditions de marché."""
    type: str = Field(
        description="Type de filtre (market_condition, liquidity, volatility)"
    )
    condition: Optional[str] = Field(
        default=None,
        description="Condition spécifique du filtre"
    )
    parameters: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Paramètres du filtre"
    )


class ConditionGroup(BaseModel):
    """Groupe de conditions avec opérateur logique."""
    operator: RuleOperator = Field(
        description="Opérateur logique pour combiner les conditions"
    )
    conditions: List[Union[
        TechnicalCondition,
        FundamentalCondition,
        SentimentCondition,
        VolumeCondition,
        PriceCondition,
        RiskCondition,
        'ConditionGroup'  # Référence pour permettre l'imbrication
    ]] = Field(
        min_items=1,
        description="Liste des conditions à évaluer"
    )
    min_score: Optional[Decimal] = Field(
        default=None,
        ge=Decimal("0.0"),
        le=Decimal("1.0"),
        description="Score minimum requis pour valider le groupe"
    )

    @field_validator('min_score', mode='before')
    def validate_min_score(cls, v):
        if v is not None and isinstance(v, (int, float)):
            return Decimal(str(v))
        return v

    @field_validator('conditions', mode='after')
    def validate_conditions_for_operator(cls, v, info):
        """Valide le nombre de conditions selon l'opérateur."""
        operator = info.data.get('operator')
        
        if operator == RuleOperator.NOT and len(v) != 1:
            raise ValueError("L'opérateur NOT ne peut s'appliquer qu'à une seule condition")
        elif operator in [RuleOperator.AND, RuleOperator.OR] and len(v) < 2:
            raise ValueError(f"L'opérateur {operator} nécessite au moins 2 conditions")
        
        return v


# Mise à jour des modèles pour permettre la référence forward
ConditionGroup.model_rebuild()


class BuyConditions(BaseModel):
    """Conditions d'achat."""
    operator: RuleOperator = Field(
        default=RuleOperator.AND,
        description="Opérateur principal pour combiner les conditions"
    )
    conditions: List[Union[
        TechnicalCondition,
        FundamentalCondition,
        SentimentCondition,
        VolumeCondition,
        PriceCondition,
        ConditionGroup
    ]] = Field(
        min_items=1,
        description="Conditions d'achat"
    )
    min_score: Optional[Decimal] = Field(
        default=None,
        ge=Decimal("0.0"),
        le=Decimal("1.0"),
        description="Score minimum pour déclencher un achat"
    )
    cooldown_period: Optional[int] = Field(
        default=None,
        ge=0,
        description="Période de refroidissement en minutes après un signal"
    )

    @field_validator('min_score', mode='before')
    def validate_min_score(cls, v):
        if v is not None and isinstance(v, (int, float)):
            return Decimal(str(v))
        return v


class SellConditions(BaseModel):
    """Conditions de vente."""
    operator: RuleOperator = Field(
        default=RuleOperator.OR,
        description="Opérateur principal pour combiner les conditions"
    )
    conditions: List[Union[
        TechnicalCondition,
        FundamentalCondition,
        SentimentCondition,
        VolumeCondition,
        PriceCondition,
        RiskCondition,
        ConditionGroup
    ]] = Field(
        min_items=1,
        description="Conditions de vente"
    )
    min_score: Optional[Decimal] = Field(
        default=None,
        ge=Decimal("0.0"),
        le=Decimal("1.0"),
        description="Score minimum pour déclencher une vente"
    )
    priority: Optional[List[str]] = Field(
        default=None,
        description="Ordre de priorité des conditions de vente"
    )

    @field_validator('min_score', mode='before')
    def validate_min_score(cls, v):
        if v is not None and isinstance(v, (int, float)):
            return Decimal(str(v))
        return v


class ExitStrategy(BaseModel):
    """Stratégie de sortie de position."""
    type: str = Field(
        description="Type de sortie (full, partial, trailing)"
    )
    percentage: Optional[Decimal] = Field(
        default=Decimal("1.0"),
        ge=Decimal("0.0"),
        le=Decimal("1.0"),
        description="Pourcentage de la position à vendre"
    )
    conditions: Optional[List[Union[
        TechnicalCondition,
        RiskCondition
    ]]] = Field(
        default=None,
        description="Conditions spécifiques pour cette sortie"
    )

    @field_validator('percentage', mode='before')
    def validate_percentage(cls, v):
        if v is not None and isinstance(v, (int, float)):
            return Decimal(str(v))
        return v


class Rule(BaseModel):
    """Règle complète de trading."""
    buy_conditions: BuyConditions = Field(
        description="Conditions d'achat"
    )
    sell_conditions: SellConditions = Field(
        description="Conditions de vente"
    )
    filters: Optional[List[FilterCondition]] = Field(
        default=None,
        description="Filtres globaux à appliquer"
    )
    exit_strategy: Optional[ExitStrategy] = Field(
        default=None,
        description="Stratégie de sortie spécifique"
    )
    max_holding_period: Optional[int] = Field(
        default=None,
        ge=1,
        description="Période de détention maximale en jours"
    )
    rebalance_frequency: Optional[str] = Field(
        default="daily",
        description="Fréquence de réévaluation (hourly, daily, weekly)"
    )

    class Config:
        """Configuration Pydantic."""
        validate_assignment = True
        arbitrary_types_allowed = True


class SignalResult(BaseModel):
    """Résultat d'évaluation d'un signal."""
    signal_type: SignalType = Field(
        description="Type de signal généré"
    )
    confidence: Decimal = Field(
        ge=Decimal("0.0"),
        le=Decimal("1.0"),
        description="Niveau de confiance du signal"
    )
    score: Decimal = Field(
        ge=Decimal("0.0"),
        le=Decimal("1.0"),
        description="Score d'évaluation des conditions"
    )
    triggered_conditions: List[str] = Field(
        description="Conditions qui ont déclenché le signal"
    )
    symbol: str = Field(
        description="Symbole concerné par le signal"
    )
    timestamp: str = Field(
        description="Timestamp du signal (ISO format)"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Métadonnées additionnelles"
    )

    @field_validator('confidence', 'score', mode='before')
    def validate_decimal_fields(cls, v):
        if isinstance(v, (int, float)):
            return Decimal(str(v))
        return v

    class Config:
        """Configuration Pydantic."""
        json_encoders = {
            Decimal: str
        }