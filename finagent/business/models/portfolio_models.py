"""
Modèles de données pour la gestion de portefeuille.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator


class PositionType(str, Enum):
    """Types de positions."""
    LONG = "long"
    SHORT = "short"


class TransactionType(str, Enum):
    """Types de transactions."""
    BUY = "buy"
    SELL = "sell"
    DIVIDEND = "dividend"
    SPLIT = "split"
    MERGER = "merger"
    SPIN_OFF = "spin_off"


class TransactionStatus(str, Enum):
    """Status des transactions."""
    PENDING = "pending"
    EXECUTED = "executed"
    CANCELLED = "cancelled"
    FAILED = "failed"
    PARTIAL = "partial"


class PositionStatus(str, Enum):
    """Status des positions."""
    ACTIVE = "active"
    CLOSED = "closed"
    SUSPENDED = "suspended"


class RebalanceType(str, Enum):
    """Types de rééquilibrage."""
    AUTOMATIC = "automatic"
    MANUAL = "manual"
    THRESHOLD = "threshold"
    PERIODIC = "periodic"
    RISK_DRIVEN = "risk_driven"


class Transaction(BaseModel):
    """Transaction individuelle."""
    
    id: UUID = Field(default_factory=uuid4)
    symbol: str = Field(..., description="Symbole du titre")
    transaction_type: TransactionType = Field(..., description="Type de transaction")
    status: TransactionStatus = Field(default=TransactionStatus.PENDING)
    
    # Détails de la transaction
    quantity: Decimal = Field(..., description="Quantité")
    price: Decimal = Field(..., description="Prix d'exécution")
    fees: Decimal = Field(default=Decimal("0"), description="Frais de transaction")
    total_amount: Decimal = Field(..., description="Montant total")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    executed_at: Optional[datetime] = Field(None, description="Date d'exécution")
    
    # Métadonnées
    order_id: Optional[str] = Field(None, description="ID de l'ordre")
    broker: Optional[str] = Field(None, description="Courtier")
    exchange: Optional[str] = Field(None, description="Bourse")
    
    # Contexte
    decision_id: Optional[UUID] = Field(None, description="ID de la décision source")
    strategy_name: Optional[str] = Field(None, description="Stratégie source")
    notes: Optional[str] = Field(None, description="Notes")
    
    @validator('quantity')
    def validate_quantity(cls, v):
        """Valide la quantité."""
        if v <= 0:
            raise ValueError("La quantité doit être positive")
        return v
    
    @validator('price')
    def validate_price(cls, v):
        """Valide le prix."""
        if v <= 0:
            raise ValueError("Le prix doit être positif")
        return v
    
    @property
    def net_amount(self) -> Decimal:
        """Montant net après frais."""
        if self.transaction_type == TransactionType.BUY:
            return self.total_amount + self.fees
        else:
            return self.total_amount - self.fees


class Position(BaseModel):
    """Position dans le portefeuille."""
    
    id: UUID = Field(default_factory=uuid4)
    symbol: str = Field(..., description="Symbole du titre")
    position_type: PositionType = Field(default=PositionType.LONG)
    status: PositionStatus = Field(default=PositionStatus.ACTIVE)
    
    # Quantités
    quantity: Decimal = Field(..., description="Quantité détenue")
    available_quantity: Decimal = Field(..., description="Quantité disponible")
    locked_quantity: Decimal = Field(default=Decimal("0"), description="Quantité bloquée")
    
    # Prix et coûts
    average_cost: Decimal = Field(..., description="Prix moyen d'acquisition")
    total_cost: Decimal = Field(..., description="Coût total")
    current_price: Decimal = Field(..., description="Prix actuel")
    market_value: Decimal = Field(..., description="Valeur de marché")
    
    # Performance
    unrealized_pnl: Decimal = Field(..., description="P&L non réalisé")
    realized_pnl: Decimal = Field(default=Decimal("0"), description="P&L réalisé")
    total_pnl: Decimal = Field(..., description="P&L total")
    
    # Pourcentages
    weight: float = Field(..., ge=0.0, le=1.0, description="Poids dans le portefeuille")
    allocation_target: Optional[float] = Field(None, ge=0.0, le=1.0, description="Allocation cible")
    
    # Métadonnées
    opened_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
    sector: Optional[str] = Field(None, description="Secteur")
    industry: Optional[str] = Field(None, description="Industrie")
    
    # Transactions liées
    transactions: List[UUID] = Field(default_factory=list, description="IDs des transactions")
    
    @validator('quantity')
    def validate_quantity(cls, v):
        """Valide la quantité."""
        if v < 0:
            raise ValueError("La quantité ne peut pas être négative")
        return v
    
    @validator('weight')
    def validate_weight(cls, v):
        """Valide le poids."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Le poids doit être entre 0 et 1")
        return v
    
    @property
    def return_percentage(self) -> float:
        """Rendement en pourcentage."""
        if self.total_cost == 0:
            return 0.0
        return float((self.total_pnl / self.total_cost) * 100)
    
    @property
    def is_profitable(self) -> bool:
        """Indique si la position est profitable."""
        return self.total_pnl > 0
    
    @property
    def is_empty(self) -> bool:
        """Indique si la position est vide."""
        return self.quantity == 0


class Portfolio(BaseModel):
    """Portefeuille complet."""
    
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., description="Nom du portefeuille")
    description: Optional[str] = Field(None, description="Description")
    
    # Valeurs
    total_value: Decimal = Field(..., description="Valeur totale")
    cash_balance: Decimal = Field(..., description="Solde de trésorerie")
    invested_amount: Decimal = Field(..., description="Montant investi")
    available_cash: Decimal = Field(..., description="Trésorerie disponible")
    
    # Positions
    positions: Dict[str, Position] = Field(default_factory=dict, description="Positions par symbole")
    
    # Performance
    total_pnl: Decimal = Field(default=Decimal("0"), description="P&L total")
    unrealized_pnl: Decimal = Field(default=Decimal("0"), description="P&L non réalisé")
    realized_pnl: Decimal = Field(default=Decimal("0"), description="P&L réalisé")
    
    # Métriques de risque
    beta: Optional[float] = Field(None, description="Beta du portefeuille")
    volatility: Optional[float] = Field(None, description="Volatilité")
    sharpe_ratio: Optional[float] = Field(None, description="Ratio de Sharpe")
    max_drawdown: Optional[float] = Field(None, description="Drawdown maximum")
    
    # Allocations
    sector_allocation: Dict[str, float] = Field(default_factory=dict, description="Allocation par secteur")
    target_allocation: Dict[str, float] = Field(default_factory=dict, description="Allocation cible")
    
    # Métadonnées
    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
    last_rebalance: Optional[datetime] = Field(None, description="Dernier rééquilibrage")
    
    # Configuration
    risk_tolerance: float = Field(default=0.5, ge=0.0, le=1.0, description="Tolérance au risque")
    max_position_size: float = Field(default=0.1, ge=0.0, le=1.0, description="Taille max de position")
    rebalance_threshold: float = Field(default=0.05, ge=0.0, le=1.0, description="Seuil de rééquilibrage")
    
    @property
    def return_percentage(self) -> float:
        """Rendement total en pourcentage."""
        if self.invested_amount == 0:
            return 0.0
        return float((self.total_pnl / self.invested_amount) * 100)
    
    @property
    def active_positions(self) -> Dict[str, Position]:
        """Positions actives."""
        return {
            symbol: position for symbol, position in self.positions.items()
            if position.status == PositionStatus.ACTIVE and not position.is_empty
        }
    
    @property
    def position_count(self) -> int:
        """Nombre de positions actives."""
        return len(self.active_positions)
    
    @property
    def diversification_score(self) -> float:
        """Score de diversification basé sur le nombre de positions."""
        count = self.position_count
        if count == 0:
            return 0.0
        elif count == 1:
            return 0.2
        elif count <= 5:
            return 0.4
        elif count <= 10:
            return 0.6
        elif count <= 20:
            return 0.8
        else:
            return 1.0


class PortfolioMetrics(BaseModel):
    """Métriques détaillées du portefeuille."""
    
    portfolio_id: UUID = Field(..., description="ID du portefeuille")
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # Valeurs de base
    total_value: Decimal = Field(..., description="Valeur totale")
    net_worth: Decimal = Field(..., description="Valeur nette")
    cash_percentage: float = Field(..., description="Pourcentage de trésorerie")
    
    # Performance
    daily_return: float = Field(..., description="Rendement journalier")
    weekly_return: float = Field(..., description="Rendement hebdomadaire")
    monthly_return: float = Field(..., description="Rendement mensuel")
    yearly_return: float = Field(..., description="Rendement annuel")
    total_return: float = Field(..., description="Rendement total")
    
    # Métriques de risque
    volatility_1m: float = Field(..., description="Volatilité 1 mois")
    volatility_3m: float = Field(..., description="Volatilité 3 mois")
    volatility_1y: float = Field(..., description="Volatilité 1 an")
    
    beta_1m: Optional[float] = Field(None, description="Beta 1 mois")
    beta_3m: Optional[float] = Field(None, description="Beta 3 mois")
    beta_1y: Optional[float] = Field(None, description="Beta 1 an")
    
    sharpe_ratio_1m: Optional[float] = Field(None, description="Sharpe 1 mois")
    sharpe_ratio_3m: Optional[float] = Field(None, description="Sharpe 3 mois")
    sharpe_ratio_1y: Optional[float] = Field(None, description="Sharpe 1 an")
    
    # Drawdown
    current_drawdown: float = Field(..., description="Drawdown actuel")
    max_drawdown_1m: float = Field(..., description="Max drawdown 1 mois")
    max_drawdown_3m: float = Field(..., description="Max drawdown 3 mois")
    max_drawdown_1y: float = Field(..., description="Max drawdown 1 an")
    
    # Diversification
    position_count: int = Field(..., description="Nombre de positions")
    sector_count: int = Field(..., description="Nombre de secteurs")
    herfindahl_index: float = Field(..., description="Indice de Herfindahl")
    concentration_ratio: float = Field(..., description="Ratio de concentration")
    
    # Allocations
    top_positions: List[Dict[str, Any]] = Field(default_factory=list, description="Top positions")
    sector_weights: Dict[str, float] = Field(default_factory=dict, description="Poids par secteur")
    
    @property
    def risk_level(self) -> str:
        """Niveau de risque basé sur la volatilité."""
        if self.volatility_1m < 0.1:
            return "Faible"
        elif self.volatility_1m < 0.2:
            return "Modéré"
        elif self.volatility_1m < 0.3:
            return "Élevé"
        else:
            return "Très Élevé"


class PerformanceMetrics(BaseModel):
    """Métriques de performance détaillées."""
    
    portfolio_id: UUID = Field(..., description="ID du portefeuille")
    period_start: datetime = Field(..., description="Début de la période")
    period_end: datetime = Field(..., description="Fin de la période")
    
    # Rendements
    absolute_return: float = Field(..., description="Rendement absolu")
    relative_return: float = Field(..., description="Rendement relatif")
    annualized_return: float = Field(..., description="Rendement annualisé")
    
    # Benchmark
    benchmark_return: Optional[float] = Field(None, description="Rendement du benchmark")
    alpha: Optional[float] = Field(None, description="Alpha")
    tracking_error: Optional[float] = Field(None, description="Tracking error")
    information_ratio: Optional[float] = Field(None, description="Information ratio")
    
    # Ratios de performance
    sharpe_ratio: Optional[float] = Field(None, description="Ratio de Sharpe")
    sortino_ratio: Optional[float] = Field(None, description="Ratio de Sortino")
    calmar_ratio: Optional[float] = Field(None, description="Ratio de Calmar")
    omega_ratio: Optional[float] = Field(None, description="Ratio d'Omega")
    
    # Statistiques de risque
    volatility: float = Field(..., description="Volatilité")
    downside_deviation: float = Field(..., description="Déviation négative")
    var_95: float = Field(..., description="VaR 95%")
    cvar_95: float = Field(..., description="CVaR 95%")
    
    # Drawdown
    max_drawdown: float = Field(..., description="Drawdown maximum")
    avg_drawdown: float = Field(..., description="Drawdown moyen")
    recovery_time: Optional[int] = Field(None, description="Temps de récupération (jours)")
    
    # Win/Loss
    win_rate: float = Field(..., description="Taux de gain")
    profit_factor: float = Field(..., description="Facteur de profit")
    avg_win: float = Field(..., description="Gain moyen")
    avg_loss: float = Field(..., description="Perte moyenne")
    
    # Métadonnées
    trades_count: int = Field(..., description="Nombre de trades")
    profitable_trades: int = Field(..., description="Trades profitables")
    losing_trades: int = Field(..., description="Trades perdants")


class RebalanceRecommendation(BaseModel):
    """Recommandation de rééquilibrage."""
    
    id: UUID = Field(default_factory=uuid4)
    portfolio_id: UUID = Field(..., description="ID du portefeuille")
    rebalance_type: RebalanceType = Field(..., description="Type de rééquilibrage")
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # Analyse
    current_allocations: Dict[str, float] = Field(..., description="Allocations actuelles")
    target_allocations: Dict[str, float] = Field(..., description="Allocations cibles")
    deviations: Dict[str, float] = Field(..., description="Déviations")
    
    # Recommandations
    actions: List[Dict[str, Any]] = Field(..., description="Actions recommandées")
    estimated_cost: Decimal = Field(..., description="Coût estimé")
    expected_improvement: float = Field(..., description="Amélioration attendue")
    
    # Priorité et urgence
    priority: int = Field(..., ge=1, le=5, description="Priorité (1=haute, 5=basse)")
    urgency_score: float = Field(..., ge=0.0, le=1.0, description="Score d'urgence")
    
    # Justification
    reason: str = Field(..., description="Raison du rééquilibrage")
    risk_impact: str = Field(..., description="Impact sur le risque")
    
    # Contraintes
    max_turnover: float = Field(default=0.2, description="Turnover maximum")
    min_trade_size: Decimal = Field(default=Decimal("100"), description="Taille min de trade")
    
    @property
    def total_deviation(self) -> float:
        """Déviation totale absolue."""
        return sum(abs(dev) for dev in self.deviations.values())
    
    @property
    def requires_immediate_action(self) -> bool:
        """Indique si une action immédiate est requise."""
        return self.urgency_score >= 0.8 or self.priority <= 2
    
    @property
    def execution_order(self) -> List[Dict[str, Any]]:
        """Ordre d'exécution optimisé des actions."""
        # Trier par type d'action (SELL avant BUY) et par montant
        actions = sorted(
            self.actions,
            key=lambda x: (x.get('action') != 'SELL', -x.get('amount', 0))
        )
        return actions