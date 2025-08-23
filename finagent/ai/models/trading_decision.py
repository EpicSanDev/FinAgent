"""
Modèles pour les décisions de trading par IA.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import Field, validator

from .base import BaseAIModel, ConfidenceLevel
from .financial_analysis import AnalysisResult, RiskLevel


class DecisionType(str, Enum):
    """Types de décision de trading."""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    STRONG_BUY = "strong_buy"
    STRONG_SELL = "strong_sell"


class OrderType(str, Enum):
    """Types d'ordre."""
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    STOP_LIMIT = "stop_limit"
    TRAILING_STOP = "trailing_stop"


class TimeInForce(str, Enum):
    """Durée de validité de l'ordre."""
    DAY = "day"
    GTC = "gtc"  # Good Till Cancelled
    IOC = "ioc"  # Immediate Or Cancel
    FOK = "fok"  # Fill Or Kill


class PositionSizing(str, Enum):
    """Méthodes de sizing de position."""
    FIXED_AMOUNT = "fixed_amount"
    PERCENTAGE_OF_PORTFOLIO = "percentage_of_portfolio"
    RISK_BASED = "risk_based"
    KELLY_CRITERION = "kelly_criterion"
    VOLATILITY_ADJUSTED = "volatility_adjusted"


class TradingContext(BaseAIModel):
    """Contexte pour la prise de décision de trading."""
    
    # Symbole et données de base
    symbol: str = Field(min_length=1, max_length=10)
    current_price: Decimal = Field(gt=0)
    current_position: Optional[Decimal] = Field(default=None)  # Nombre d'actions détenues
    average_cost: Optional[Decimal] = Field(default=None)  # Prix moyen d'acquisition
    
    # Portfolio et liquidités
    available_cash: Decimal = Field(ge=0)
    portfolio_value: Decimal = Field(gt=0)
    position_value: Optional[Decimal] = Field(default=None)
    portfolio_allocation: Optional[float] = Field(None, ge=0, le=1.0)  # % du portfolio
    
    # Paramètres de risque
    max_position_size: Optional[Decimal] = Field(default=None, ge=0)
    max_loss_per_trade: Optional[Decimal] = Field(default=None, ge=0)
    max_portfolio_risk: Optional[float] = Field(None, ge=0, le=1.0)
    
    # Contraintes de trading
    min_trade_amount: Decimal = Field(default=Decimal("100"), gt=0)
    max_trade_amount: Optional[Decimal] = Field(default=None, gt=0)
    allow_short_selling: bool = Field(default=False)
    allow_margin_trading: bool = Field(default=False)
    
    # Timing et session
    market_session: str = Field(default="regular")  # "pre_market", "regular", "after_hours"
    time_until_close: Optional[int] = Field(default=None, ge=0)  # minutes
    
    # Données historiques de performance
    win_rate: Optional[float] = Field(None, ge=0, le=1.0)
    avg_win: Optional[Decimal] = None
    avg_loss: Optional[Decimal] = None
    sharpe_ratio: Optional[float] = None
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('symbol')
    def validate_symbol(cls, v):
        """Valide le symbole."""
        return v.upper().strip()
    
    @property
    def position_pnl(self) -> Optional[Decimal]:
        """Calcule le P&L de la position actuelle."""
        if self.current_position and self.average_cost:
            return (self.current_price - self.average_cost) * self.current_position
        return None
    
    @property
    def position_pnl_percent(self) -> Optional[float]:
        """Calcule le P&L en pourcentage."""
        if self.average_cost:
            return float((self.current_price - self.average_cost) / self.average_cost)
        return None


class RiskParameters(BaseAIModel):
    """Paramètres de gestion du risque."""
    
    # Stop loss et take profit
    stop_loss_percent: Optional[float] = Field(None, gt=0, le=0.5)  # % de perte max
    take_profit_percent: Optional[float] = Field(None, gt=0, le=2.0)  # % de gain cible
    trailing_stop_percent: Optional[float] = Field(None, gt=0, le=0.2)
    
    # Sizing de position
    position_sizing_method: PositionSizing = Field(default=PositionSizing.PERCENTAGE_OF_PORTFOLIO)
    max_position_weight: float = Field(default=0.05, gt=0, le=1.0)  # 5% max par défaut
    risk_per_trade: float = Field(default=0.02, gt=0, le=0.1)  # 2% de risque par trade
    
    # Volatilité et corrélation
    max_volatility: Optional[float] = Field(None, gt=0)
    max_correlation: Optional[float] = Field(None, ge=-1, le=1)
    
    # Limites temporelles
    max_holding_period: Optional[int] = Field(None, gt=0)  # jours
    min_holding_period: Optional[int] = Field(None, gt=0)  # jours
    
    # Gestion des drawdowns
    max_drawdown: float = Field(default=0.15, gt=0, le=0.5)  # 15% max
    daily_loss_limit: Optional[Decimal] = Field(default=None, gt=0)


class DecisionRequest(BaseAIModel):
    """Requête de décision de trading."""
    
    request_id: UUID = Field(default_factory=uuid4)
    trading_context: TradingContext
    analysis_result: AnalysisResult
    risk_parameters: RiskParameters
    
    # Stratégie et préférences
    strategy_name: Optional[str] = None
    time_horizon: str = Field(default="1d")  # "intraday", "1d", "1w", "1m", "long_term"
    aggressive_mode: bool = Field(default=False)
    
    # Contraintes externes
    news_embargo: bool = Field(default=False)  # Pas de trading pendant les news
    earnings_period: bool = Field(default=False)  # Période de résultats
    market_conditions: Optional[str] = None  # "bull", "bear", "sideways", "volatile"
    
    # Contexte additionnel
    custom_notes: Optional[str] = None
    override_rules: List[str] = Field(default_factory=list)
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TradingDecision(BaseAIModel):
    """Décision de trading générée par l'IA."""
    
    request_id: UUID
    decision_id: UUID = Field(default_factory=uuid4)
    symbol: str
    
    # Décision principale
    action: DecisionType
    confidence: ConfidenceLevel
    urgency: str = Field(default="normal")  # "low", "normal", "high", "immediate"
    
    # Paramètres d'exécution
    order_type: OrderType = Field(default=OrderType.MARKET)
    time_in_force: TimeInForce = Field(default=TimeInForce.DAY)
    
    # Quantités et prix
    recommended_quantity: Optional[Decimal] = Field(default=None, ge=0)
    recommended_amount: Optional[Decimal] = Field(default=None, ge=0)
    limit_price: Optional[Decimal] = Field(default=None, gt=0)
    
    # Gestion du risque
    stop_loss_price: Optional[Decimal] = Field(default=None, gt=0)
    take_profit_price: Optional[Decimal] = Field(default=None, gt=0)
    position_size_percent: Optional[float] = Field(None, gt=0, le=1.0)
    
    # Analyse et justification
    reasoning: str = Field(min_length=10)
    key_factors: List[str] = Field(default_factory=list)
    risk_assessment: str
    expected_return: Optional[float] = None  # % attendu
    risk_reward_ratio: Optional[float] = None
    
    # Scores et métriques
    technical_score: Optional[float] = Field(None, ge=0, le=1)
    fundamental_score: Optional[float] = Field(None, ge=0, le=1)
    sentiment_score: Optional[float] = Field(None, ge=-1, le=1)
    risk_score: RiskLevel
    
    # Timing
    optimal_entry_time: Optional[str] = None  # "immediate", "market_open", "after_news"
    max_wait_time: Optional[int] = Field(None, gt=0)  # minutes
    
    # Conditions d'invalidation
    invalidation_conditions: List[str] = Field(default_factory=list)
    expiry_time: Optional[datetime] = None
    
    # Suivi et monitoring
    monitoring_alerts: List[str] = Field(default_factory=list)
    review_triggers: List[str] = Field(default_factory=list)
    
    # Métadonnées
    model_used: str
    processing_time: float = Field(default=0.0, ge=0)
    tokens_used: int = Field(default=0, ge=0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('recommended_quantity', 'recommended_amount')
    def validate_quantity_or_amount(cls, v, values):
        """Valide qu'on a soit quantity soit amount."""
        if v is None:
            return v
        
        # Au moins un des deux doit être spécifié pour les actions BUY/SELL
        action = values.get('action')
        if action in [DecisionType.BUY, DecisionType.SELL, DecisionType.STRONG_BUY, DecisionType.STRONG_SELL]:
            other_field = 'recommended_amount' if 'recommended_quantity' in values else 'recommended_quantity'
            if other_field not in values or values[other_field] is None:
                if v is None:
                    raise ValueError("Quantité ou montant requis pour les actions d'achat/vente")
        
        return v


class DecisionHistory(BaseAIModel):
    """Historique d'une décision de trading."""
    
    decision_id: UUID
    symbol: str
    original_decision: TradingDecision
    
    # Exécution
    executed: bool = Field(default=False)
    execution_price: Optional[Decimal] = Field(default=None)
    execution_quantity: Optional[Decimal] = Field(default=None)
    execution_time: Optional[datetime] = None
    execution_fees: Optional[Decimal] = Field(default=None, ge=0)
    
    # Résultats
    closed: bool = Field(default=False)
    close_price: Optional[Decimal] = Field(default=None)
    close_time: Optional[datetime] = None
    realized_pnl: Optional[Decimal] = None
    realized_return: Optional[float] = None  # %
    
    # Performance vs prédictions
    actual_max_price: Optional[Decimal] = None
    actual_min_price: Optional[Decimal] = None
    max_favorable_excursion: Optional[Decimal] = None  # MFE
    max_adverse_excursion: Optional[Decimal] = None   # MAE
    
    # Événements pendant la position
    stop_loss_hit: bool = Field(default=False)
    take_profit_hit: bool = Field(default=False)
    manually_closed: bool = Field(default=False)
    
    # Évaluation de la décision
    decision_quality_score: Optional[float] = Field(None, ge=0, le=1)
    lessons_learned: List[str] = Field(default_factory=list)
    improvement_notes: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PortfolioImpact(BaseAIModel):
    """Impact d'une décision sur le portfolio."""
    
    decision_id: UUID
    
    # Impact sur l'allocation
    new_cash_position: Decimal = Field(ge=0)
    new_position_value: Decimal = Field(ge=0)
    new_total_value: Decimal = Field(gt=0)
    
    # Métriques de risque
    new_portfolio_beta: Optional[float] = None
    new_portfolio_volatility: Optional[float] = None
    concentration_risk: Optional[float] = Field(None, ge=0, le=1)
    correlation_risk: Optional[float] = None
    
    # Diversification
    sector_allocation: Dict[str, float] = Field(default_factory=dict)
    geographic_allocation: Dict[str, float] = Field(default_factory=dict)
    asset_class_allocation: Dict[str, float] = Field(default_factory=dict)
    
    # Alertes de risque
    risk_warnings: List[str] = Field(default_factory=list)
    compliance_issues: List[str] = Field(default_factory=list)
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)