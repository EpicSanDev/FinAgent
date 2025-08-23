"""
Modèles de données pour le système de décision de trading.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator


class SignalType(str, Enum):
    """Types de signaux de trading."""
    TECHNICAL = "technical"
    FUNDAMENTAL = "fundamental"
    SENTIMENT = "sentiment"
    STRATEGY = "strategy"
    AI_ANALYSIS = "ai_analysis"


class SignalStrength(str, Enum):
    """Force du signal."""
    VERY_WEAK = "very_weak"
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    VERY_STRONG = "very_strong"


class DecisionAction(str, Enum):
    """Actions de décision possibles."""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    REDUCE = "reduce"
    INCREASE = "increase"


class ConfidenceLevel(str, Enum):
    """Niveaux de confiance."""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class DecisionSignal(BaseModel):
    """Signal individuel pour la prise de décision."""
    
    id: UUID = Field(default_factory=uuid4)
    symbol: str = Field(..., description="Symbole du titre")
    signal_type: SignalType = Field(..., description="Type de signal")
    strength: SignalStrength = Field(..., description="Force du signal")
    direction: DecisionAction = Field(..., description="Direction recommandée")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confiance [0-1]")
    weight: float = Field(default=1.0, ge=0.0, le=1.0, description="Poids du signal")
    
    # Métadonnées
    source: str = Field(..., description="Source du signal")
    timestamp: datetime = Field(default_factory=datetime.now)
    expiry: Optional[datetime] = Field(None, description="Expiration du signal")
    
    # Données contextuelles
    price_target: Optional[Decimal] = Field(None, description="Prix cible")
    stop_loss: Optional[Decimal] = Field(None, description="Stop loss")
    timeframe: str = Field(default="1D", description="Timeframe du signal")
    
    # Justification
    reason: str = Field(..., description="Raison du signal")
    supporting_data: Dict[str, Any] = Field(default_factory=dict, description="Données de support")
    
    @validator('confidence')
    def validate_confidence(cls, v):
        """Valide le niveau de confiance."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("La confiance doit être entre 0 et 1")
        return v
    
    @property
    def is_expired(self) -> bool:
        """Vérifie si le signal a expiré."""
        if self.expiry is None:
            return False
        return datetime.now() > self.expiry
    
    @property
    def strength_value(self) -> float:
        """Convertit la force en valeur numérique."""
        strength_map = {
            SignalStrength.VERY_WEAK: 0.2,
            SignalStrength.WEAK: 0.4,
            SignalStrength.MODERATE: 0.6,
            SignalStrength.STRONG: 0.8,
            SignalStrength.VERY_STRONG: 1.0
        }
        return strength_map[self.strength]


class MarketAnalysis(BaseModel):
    """Analyse de marché pour un symbole."""
    
    symbol: str = Field(..., description="Symbole analysé")
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # Analyse technique
    technical_indicators: Dict[str, float] = Field(default_factory=dict)
    support_levels: List[Decimal] = Field(default_factory=list)
    resistance_levels: List[Decimal] = Field(default_factory=list)
    trend_direction: str = Field(..., description="Direction de la tendance")
    volatility: float = Field(..., ge=0.0, description="Volatilité")
    
    # Analyse fondamentale
    pe_ratio: Optional[float] = Field(None, description="P/E ratio")
    market_cap: Optional[Decimal] = Field(None, description="Capitalisation")
    dividend_yield: Optional[float] = Field(None, description="Rendement dividende")
    
    # Sentiment de marché
    sentiment_score: float = Field(..., ge=-1.0, le=1.0, description="Score sentiment [-1,1]")
    news_sentiment: Optional[str] = Field(None, description="Sentiment des news")
    social_sentiment: Optional[str] = Field(None, description="Sentiment social")
    
    # Volumes et liquidité
    avg_volume: Decimal = Field(..., description="Volume moyen")
    volume_trend: str = Field(..., description="Tendance du volume")
    liquidity_score: float = Field(..., ge=0.0, le=1.0, description="Score de liquidité")


class RiskAssessment(BaseModel):
    """Évaluation des risques pour une décision."""
    
    symbol: str = Field(..., description="Symbole évalué")
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # Métriques de risque
    var_1d: Optional[Decimal] = Field(None, description="VaR 1 jour")
    var_5d: Optional[Decimal] = Field(None, description="VaR 5 jours")
    beta: Optional[float] = Field(None, description="Beta vs marché")
    sharpe_ratio: Optional[float] = Field(None, description="Ratio de Sharpe")
    max_drawdown: Optional[float] = Field(None, description="Drawdown maximum")
    
    # Risques spécifiques
    sector_risk: float = Field(..., ge=0.0, le=1.0, description="Risque sectoriel")
    concentration_risk: float = Field(..., ge=0.0, le=1.0, description="Risque de concentration")
    liquidity_risk: float = Field(..., ge=0.0, le=1.0, description="Risque de liquidité")
    credit_risk: Optional[float] = Field(None, ge=0.0, le=1.0, description="Risque de crédit")
    
    # Score global
    overall_risk_score: float = Field(..., ge=0.0, le=1.0, description="Score de risque global")
    risk_level: str = Field(..., description="Niveau de risque")
    
    # Recommandations
    max_position_size: float = Field(..., ge=0.0, le=1.0, description="Taille max de position")
    recommended_stop_loss: Optional[Decimal] = Field(None, description="Stop loss recommandé")


class SignalAggregation(BaseModel):
    """Agrégation de signaux multiples."""
    
    symbol: str = Field(..., description="Symbole")
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # Signaux source
    signals: List[DecisionSignal] = Field(..., description="Signaux individuels")
    
    # Résultat agrégé
    aggregated_action: DecisionAction = Field(..., description="Action agrégée")
    aggregated_confidence: float = Field(..., ge=0.0, le=1.0, description="Confiance agrégée")
    consensus_strength: float = Field(..., ge=0.0, le=1.0, description="Force du consensus")
    
    # Détails d'agrégation
    buy_signals: int = Field(..., description="Nombre de signaux BUY")
    sell_signals: int = Field(..., description="Nombre de signaux SELL")
    hold_signals: int = Field(..., description="Nombre de signaux HOLD")
    
    # Poids et scores
    weighted_score: float = Field(..., description="Score pondéré")
    signal_weights: Dict[str, float] = Field(default_factory=dict)
    
    @validator('signals')
    def validate_signals_symbol(cls, v, values):
        """Valide que tous les signaux concernent le même symbole."""
        if 'symbol' in values:
            symbol = values['symbol']
            for signal in v:
                if signal.symbol != symbol:
                    raise ValueError(f"Signal pour {signal.symbol} ne correspond pas au symbole {symbol}")
        return v
    
    @property
    def active_signals(self) -> List[DecisionSignal]:
        """Retourne les signaux non expirés."""
        return [signal for signal in self.signals if not signal.is_expired]
    
    @property
    def signal_distribution(self) -> Dict[str, float]:
        """Distribution des types de signaux."""
        if not self.signals:
            return {}
        
        type_counts = {}
        for signal in self.signals:
            type_counts[signal.signal_type] = type_counts.get(signal.signal_type, 0) + 1
        
        total = len(self.signals)
        return {k: v / total for k, v in type_counts.items()}


class DecisionContext(BaseModel):
    """Contexte pour la prise de décision."""
    
    symbol: str = Field(..., description="Symbole")
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # Prix et données de marché
    current_price: Decimal = Field(..., description="Prix actuel")
    previous_close: Decimal = Field(..., description="Clôture précédente")
    day_high: Decimal = Field(..., description="Haut du jour")
    day_low: Decimal = Field(..., description="Bas du jour")
    volume: Decimal = Field(..., description="Volume")
    
    # Contexte de portefeuille
    current_position: Optional[Decimal] = Field(None, description="Position actuelle")
    available_cash: Decimal = Field(..., description="Cash disponible")
    portfolio_value: Decimal = Field(..., description="Valeur du portefeuille")
    position_weight: float = Field(default=0.0, ge=0.0, le=1.0, description="Poids dans le portefeuille")
    
    # Contraintes
    max_position_size: float = Field(default=0.1, ge=0.0, le=1.0, description="Taille max de position")
    min_trade_amount: Decimal = Field(default=Decimal("100"), description="Montant min de trade")
    
    # Données contextuelles
    market_analysis: Optional[MarketAnalysis] = Field(None, description="Analyse de marché")
    risk_assessment: Optional[RiskAssessment] = Field(None, description="Évaluation des risques")
    signal_aggregation: Optional[SignalAggregation] = Field(None, description="Agrégation de signaux")
    
    # Métadonnées de stratégie
    active_strategies: List[str] = Field(default_factory=list, description="Stratégies actives")
    strategy_context: Dict[str, Any] = Field(default_factory=dict, description="Contexte stratégique")


class DecisionResult(BaseModel):
    """Résultat d'une décision de trading."""
    
    id: UUID = Field(default_factory=uuid4)
    symbol: str = Field(..., description="Symbole")
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # Décision principale
    action: DecisionAction = Field(..., description="Action recommandée")
    confidence: ConfidenceLevel = Field(..., description="Niveau de confiance")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Score de confiance numérique")
    
    # Détails de l'ordre
    quantity: Optional[Decimal] = Field(None, description="Quantité recommandée")
    price_target: Optional[Decimal] = Field(None, description="Prix cible")
    stop_loss: Optional[Decimal] = Field(None, description="Stop loss")
    take_profit: Optional[Decimal] = Field(None, description="Take profit")
    
    # Justification
    primary_reason: str = Field(..., description="Raison principale")
    supporting_factors: List[str] = Field(default_factory=list, description="Facteurs de support")
    risk_factors: List[str] = Field(default_factory=list, description="Facteurs de risque")
    
    # Métriques de décision
    expected_return: Optional[float] = Field(None, description="Rendement attendu")
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Score de risque")
    reward_risk_ratio: Optional[float] = Field(None, description="Ratio reward/risk")
    
    # Impact sur le portefeuille
    portfolio_impact: Dict[str, float] = Field(default_factory=dict, description="Impact sur le portefeuille")
    new_allocation: Optional[float] = Field(None, description="Nouvelle allocation")
    
    # Signaux utilisés
    signals_used: List[UUID] = Field(default_factory=list, description="IDs des signaux utilisés")
    signals_summary: Dict[str, int] = Field(default_factory=dict, description="Résumé des signaux")
    
    # Contexte de décision
    decision_context: Dict[str, Any] = Field(default_factory=dict, description="Contexte de la décision")
    market_conditions: str = Field(..., description="Conditions de marché")
    
    @validator('confidence_score')
    def validate_confidence_score(cls, v):
        """Valide le score de confiance."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Le score de confiance doit être entre 0 et 1")
        return v
    
    @property
    def is_actionable(self) -> bool:
        """Indique si la décision est actionnable."""
        return (
            self.action in [DecisionAction.BUY, DecisionAction.SELL] and
            self.confidence_score >= 0.6 and
            self.quantity is not None and
            self.quantity > 0
        )
    
    @property
    def execution_priority(self) -> int:
        """Priorité d'exécution (1=haute, 5=basse)."""
        if self.confidence_score >= 0.9:
            return 1
        elif self.confidence_score >= 0.8:
            return 2
        elif self.confidence_score >= 0.7:
            return 3
        elif self.confidence_score >= 0.6:
            return 4
        else:
            return 5