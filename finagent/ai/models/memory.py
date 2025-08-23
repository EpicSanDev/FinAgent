"""
Modèles pour le système de mémoire IA.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING
from uuid import UUID, uuid4

from pydantic import Field, validator, ConfigDict

from .base import BaseAIModel

if TYPE_CHECKING:
    from .trading_decision import TradingAction, ConfidenceLevel


class MemoryType(str, Enum):
    """Types de mémoire IA."""
    CONVERSATION = "conversation"
    MARKET_PATTERN = "market_pattern"
    DECISION_OUTCOME = "decision_outcome"
    STRATEGY_PERFORMANCE = "strategy_performance"
    ERROR_LEARNING = "error_learning"
    USER_PREFERENCE = "user_preference"
    CONTEXTUAL = "contextual"


class MemoryImportance(str, Enum):
    """Importance des souvenirs."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MINIMAL = "minimal"


class MemoryStatus(str, Enum):
    """Statut des souvenirs."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"
    PENDING_VALIDATION = "pending_validation"


class ConversationTurn(BaseAIModel):
    """Tour de conversation dans la mémoire."""
    
    model_config = ConfigDict(protected_namespaces=())
    
    turn_id: UUID = Field(default_factory=uuid4)
    user_input: str
    ai_response: str
    context: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Métadonnées
    model_used: Optional[str] = None
    tokens_used: Optional[int] = Field(None, ge=0)
    processing_time: Optional[float] = Field(None, ge=0)
    
    # Classification
    intent: Optional[str] = None  # "analysis", "decision", "question", "command"
    sentiment: Optional[str] = None  # "positive", "negative", "neutral"
    success: bool = Field(default=True)
    
    @validator('user_input', 'ai_response')
    def validate_non_empty(cls, v):
        """Valide que les champs ne sont pas vides."""
        if not v or not v.strip():
            raise ValueError("Le champ ne peut pas être vide")
        return v.strip()


class ConversationMemory(BaseAIModel):
    """Mémoire de conversation complète."""
    
    model_config = ConfigDict(protected_namespaces=())
    
    conversation_id: UUID = Field(default_factory=uuid4)
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    
    # Conversations
    turns: List[ConversationTurn] = Field(default_factory=list)
    
    # Métadonnées de session
    started_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    total_turns: int = Field(default=0, ge=0)
    
    # Contexte persistant
    persistent_context: Dict[str, Any] = Field(default_factory=dict)
    user_preferences: Dict[str, Any] = Field(default_factory=dict)
    
    # Résumé de conversation
    summary: Optional[str] = None
    key_topics: List[str] = Field(default_factory=list)
    resolved_issues: List[str] = Field(default_factory=list)
    pending_actions: List[str] = Field(default_factory=list)
    
    def add_turn(self, user_input: str, ai_response: str, **kwargs) -> ConversationTurn:
        """Ajoute un tour de conversation."""
        turn = ConversationTurn(
            user_input=user_input,
            ai_response=ai_response,
            **kwargs
        )
        self.turns.append(turn)
        self.total_turns = len(self.turns)
        self.last_activity = datetime.utcnow()
        return turn
    
    def get_recent_context(self, max_turns: int = 5) -> List[ConversationTurn]:
        """Retourne le contexte récent."""
        return self.turns[-max_turns:] if self.turns else []
    
    def get_conversation_summary(self, max_length: int = 500) -> str:
        """Génère un résumé de la conversation."""
        if not self.turns:
            return "Aucune conversation"
        
        if self.summary and len(self.summary) <= max_length:
            return self.summary
        
        # Résumé basique si pas de résumé IA
        recent_topics = list(set(self.key_topics[-5:]))
        return f"Conversation de {self.total_turns} tours sur: {', '.join(recent_topics)}"


class MarketPattern(BaseAIModel):
    """Pattern de marché mémorisé."""
    
    pattern_id: UUID = Field(default_factory=uuid4)
    pattern_type: str  # "reversal", "continuation", "breakout", "consolidation"
    
    # Conditions du pattern
    market_conditions: Dict[str, Any] = Field(default_factory=dict)
    technical_setup: Dict[str, Any] = Field(default_factory=dict)
    fundamental_context: Dict[str, Any] = Field(default_factory=dict)
    
    # Résultats observés
    success_rate: float = Field(ge=0, le=1)
    average_return: float
    average_duration: Optional[int] = None  # jours
    max_drawdown: Optional[float] = None
    
    # Exemples historiques
    historical_examples: List[Dict[str, Any]] = Field(default_factory=list)
    successful_cases: int = Field(default=0, ge=0)
    failed_cases: int = Field(default=0, ge=0)
    
    # Contexte d'application
    applicable_symbols: List[str] = Field(default_factory=list)
    applicable_sectors: List[str] = Field(default_factory=list)
    market_cap_range: Optional[str] = None  # "small", "mid", "large", "mega"
    
    # Métadonnées
    confidence: float = Field(ge=0, le=1)
    importance: MemoryImportance
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_validated: datetime = Field(default_factory=datetime.utcnow)
    
    def update_performance(self, success: bool, return_pct: float, duration_days: Optional[int] = None):
        """Met à jour les statistiques de performance."""
        if success:
            self.successful_cases += 1
        else:
            self.failed_cases += 1
        
        total_cases = self.successful_cases + self.failed_cases
        self.success_rate = self.successful_cases / total_cases if total_cases > 0 else 0
        
        # Mise à jour de la moyenne mobile du rendement
        self.average_return = (self.average_return * (total_cases - 1) + return_pct) / total_cases
        
        if duration_days:
            if self.average_duration:
                self.average_duration = int((self.average_duration * (total_cases - 1) + duration_days) / total_cases)
            else:
                self.average_duration = duration_days


class DecisionOutcome(BaseAIModel):
    """Résultat d'une décision de trading."""
    
    outcome_id: UUID = Field(default_factory=uuid4)
    decision_id: UUID
    symbol: str
    
    # Décision originale
    original_action: str  # "buy", "sell", "hold"
    original_confidence: str
    original_reasoning: str
    
    # Contexte de la décision
    market_context: Dict[str, Any] = Field(default_factory=dict)
    decision_factors: List[str] = Field(default_factory=list)
    
    # Résultats réels
    executed: bool = Field(default=False)
    execution_price: Optional[float] = None
    actual_return: Optional[float] = None  # %
    holding_period: Optional[int] = None  # jours
    max_favorable_excursion: Optional[float] = None
    max_adverse_excursion: Optional[float] = None
    
    # Évaluation de la décision
    correct_direction: Optional[bool] = None
    correct_timing: Optional[bool] = None
    risk_management_effective: Optional[bool] = None
    
    # Apprentissages
    what_worked: List[str] = Field(default_factory=list)
    what_failed: List[str] = Field(default_factory=list)
    improvement_areas: List[str] = Field(default_factory=list)
    
    # Métadonnées
    importance: MemoryImportance = Field(default=MemoryImportance.MEDIUM)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    evaluated_at: Optional[datetime] = None


class UserPreference(BaseAIModel):
    """Préférences utilisateur mémorisées."""
    
    model_config = ConfigDict(protected_namespaces=())
    
    preference_id: UUID = Field(default_factory=uuid4)
    user_id: Optional[str] = None
    category: str  # "risk_tolerance", "time_horizon", "sectors", "strategies"
    
    # Valeurs de préférences
    preferences: Dict[str, Any] = Field(default_factory=dict)
    
    # Historique des changements
    previous_values: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Contexte d'apprentissage
    learned_from_behavior: bool = Field(default=False)
    explicit_user_input: bool = Field(default=False)
    confidence: float = Field(default=0.5, ge=0, le=1)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    def update_preference(self, key: str, value: Any, confidence: float = 1.0):
        """Met à jour une préférence."""
        # Sauvegarde l'ancienne valeur
        if key in self.preferences:
            self.previous_values.append({
                "key": key,
                "old_value": self.preferences[key],
                "timestamp": datetime.utcnow()
            })
        
        # Met à jour
        self.preferences[key] = value
        self.confidence = min(1.0, max(0.0, confidence))
        self.last_updated = datetime.utcnow()


class MemoryEntry(BaseAIModel):
    """Entrée générique de mémoire."""
    
    memory_id: UUID = Field(default_factory=uuid4)
    memory_type: MemoryType
    importance: MemoryImportance
    status: MemoryStatus = Field(default=MemoryStatus.ACTIVE)
    
    # Contenu
    title: str
    content: Union[ConversationMemory, MarketPattern, DecisionOutcome, UserPreference, Dict[str, Any]]
    tags: List[str] = Field(default_factory=list)
    
    # Relations
    related_memories: List[UUID] = Field(default_factory=list)
    superseded_by: Optional[UUID] = None
    supersedes: List[UUID] = Field(default_factory=list)
    
    # Métadonnées temporelles
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_accessed: datetime = Field(default_factory=datetime.utcnow)
    access_count: int = Field(default=0, ge=0)
    
    # Contexte d'utilisation
    applicable_symbols: List[str] = Field(default_factory=list)
    applicable_strategies: List[str] = Field(default_factory=list)
    applicable_conditions: Dict[str, Any] = Field(default_factory=dict)
    
    # Score de pertinence
    relevance_score: float = Field(default=1.0, ge=0, le=1)
    decay_rate: float = Field(default=0.95, ge=0, le=1)  # Décroissance temporelle
    
    def access(self):
        """Marque la mémoire comme accédée."""
        self.last_accessed = datetime.utcnow()
        self.access_count += 1
    
    def calculate_current_relevance(self) -> float:
        """Calcule la pertinence actuelle avec décroissance temporelle."""
        days_since_creation = (datetime.utcnow() - self.created_at).days
        decayed_relevance = self.relevance_score * (self.decay_rate ** days_since_creation)
        
        # Bonus pour l'importance et l'accès récent
        importance_bonus = {
            MemoryImportance.CRITICAL: 0.3,
            MemoryImportance.HIGH: 0.2,
            MemoryImportance.MEDIUM: 0.1,
            MemoryImportance.LOW: 0.05,
            MemoryImportance.MINIMAL: 0.0
        }.get(self.importance, 0.0)
        
        days_since_access = (datetime.utcnow() - self.last_accessed).days
        recency_bonus = max(0, 0.1 - (days_since_access * 0.01))
        
        return min(1.0, decayed_relevance + importance_bonus + recency_bonus)


class MemoryQuery(BaseAIModel):
    """Requête de recherche dans la mémoire."""
    
    query_id: UUID = Field(default_factory=uuid4)
    
    # Critères de recherche
    memory_types: Optional[List[MemoryType]] = None
    keywords: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    symbols: List[str] = Field(default_factory=list)
    
    # Filtres temporels
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    last_accessed_after: Optional[datetime] = None
    
    # Filtres de qualité
    min_importance: Optional[MemoryImportance] = None
    min_relevance: float = Field(default=0.1, ge=0, le=1)
    status_filter: List[MemoryStatus] = Field(default_factory=lambda: [MemoryStatus.ACTIVE])
    
    # Paramètres de retour
    max_results: int = Field(default=10, gt=0, le=100)
    sort_by: str = Field(default="relevance")  # "relevance", "created_at", "access_count"
    include_content: bool = Field(default=True)
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MemorySearchResult(BaseAIModel):
    """Résultat de recherche dans la mémoire."""
    
    query_id: UUID
    total_found: int = Field(ge=0)
    results: List[MemoryEntry] = Field(default_factory=list)
    search_time: float = Field(default=0.0, ge=0)
    
    # Métadonnées de recherche
    filters_applied: Dict[str, Any] = Field(default_factory=dict)
    relevance_scores: List[float] = Field(default_factory=list)
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MarketMemory(BaseAIModel):
    """Mémoire des données de marché."""
    
    memory_id: str = Field(default_factory=lambda: str(uuid4()))
    symbol: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Données de marché
    price: float = Field(gt=0)
    volume: float = Field(ge=0)
    market_cap: Optional[float] = Field(None, ge=0)
    
    # Indicateurs techniques
    indicators: Dict[str, Any] = Field(default_factory=dict)
    
    # Score de sentiment
    sentiment_score: Optional[float] = Field(None, ge=-1, le=1)
    
    # Métadonnées
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DecisionMemory(BaseAIModel):
    """Mémoire des décisions de trading."""
    
    decision_id: str = Field(default_factory=lambda: str(uuid4()))
    symbol: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Décision
    action: str  # Sera converti en TradingAction lors de l'utilisation
    confidence: str  # Sera converti en ConfidenceLevel lors de l'utilisation
    reasoning: str
    
    # Prédictions
    expected_return: float
    actual_outcome: Optional[float] = None
    
    # Évaluation des risques
    risk_assessment: Dict[str, Any] = Field(default_factory=dict)
    
    # Métadonnées
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConversationMessage(BaseAIModel):
    """Message dans une conversation."""
    
    role: str  # "user" ou "assistant"
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ConversationMemory(BaseAIModel):
    """Mémoire de conversation simplifiée."""
    
    conversation_id: str = Field(default_factory=lambda: str(uuid4()))
    context: str
    messages: List[ConversationMessage] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class MemorySearchQuery(BaseAIModel):
    """Requête de recherche dans la mémoire."""
    
    text_query: Optional[str] = None
    memory_types: Optional[List[MemoryType]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    metadata_filters: Dict[str, Any] = Field(default_factory=dict)
    limit: Optional[int] = Field(default=10, gt=0)


class MemorySearchResult(BaseAIModel):
    """Résultat de recherche dans la mémoire."""
    
    memory_entry: MemoryEntry
    relevance_score: float = Field(ge=0, le=1)
    match_highlights: List[str] = Field(default_factory=list)


class MemoryPersistenceConfig(BaseAIModel):
    """Configuration de persistence de la mémoire."""
    
    enabled: bool = Field(default=True)
    storage_path: str = Field(default="./data/ai_memory")


class MemoryRetentionPolicy(BaseAIModel):
    """Politique de rétention de la mémoire."""
    
    default_retention_days: int = Field(default=90, gt=0)
    conversation_retention_days: int = Field(default=30, gt=0)
    market_data_retention_days: int = Field(default=180, gt=0)
    decision_retention_days: int = Field(default=365, gt=0)
    auto_cleanup_enabled: bool = Field(default=True)
    cleanup_interval_hours: int = Field(default=24, gt=0)