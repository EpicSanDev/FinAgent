"""
Modèles de base pour l'intégration IA.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ConfigDict


class BaseAIModel(BaseModel):
    """Modèle de base pour tous les modèles IA."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        use_enum_values=True,
        frozen=False,
        protected_namespaces=()
    )


class ModelType(str, Enum):
    """Types de modèles Claude disponibles."""
    CLAUDE_3_SONNET = "claude-3-sonnet-20240229"
    CLAUDE_3_HAIKU = "claude-3-haiku-20240307" 
    CLAUDE_3_OPUS = "claude-3-opus-20240229"
    CLAUDE_3_5_SONNET = "claude-3-5-sonnet-20241022"


class ConfidenceLevel(str, Enum):
    """Niveaux de confiance pour les décisions IA."""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class ResponseFormat(str, Enum):
    """Formats de réponse disponibles."""
    TEXT = "text"
    JSON = "json"
    STRUCTURED = "structured"


class AIRequest(BaseAIModel):
    """Requête vers l'IA."""
    
    request_id: UUID = Field(default_factory=uuid4)
    model_type: ModelType = Field(default=ModelType.CLAUDE_3_SONNET)
    prompt: str = Field(min_length=1)
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)
    temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4000, gt=0, le=8192)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    
class AIResponse(BaseAIModel):
    """Réponse de l'IA."""
    
    request_id: UUID
    response_id: UUID = Field(default_factory=uuid4)
    content: str
    model_used: ModelType
    tokens_used: int = Field(default=0, ge=0)
    processing_time: float = Field(default=0.0, ge=0.0)
    confidence: Optional[ConfidenceLevel] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    error: Optional[str] = None


class AIProvider(ABC):
    """Interface abstraite pour les providers IA."""
    
    @abstractmethod
    async def send_request(self, request: AIRequest) -> AIResponse:
        """Envoie une requête à l'IA et retourne la réponse."""
        pass
        
    @abstractmethod
    async def validate_connection(self) -> bool:
        """Valide la connexion au provider IA."""
        pass
        
    @abstractmethod
    def get_available_models(self) -> List[ModelType]:
        """Retourne la liste des modèles disponibles."""
        pass


class TokenUsage(BaseAIModel):
    """Utilisation des tokens pour une requête."""
    
    prompt_tokens: int = Field(ge=0)
    completion_tokens: int = Field(ge=0)
    total_tokens: int = Field(ge=0)
    estimated_cost: float = Field(default=0.0, ge=0.0)
    
    def __post_init__(self):
        """Calcule le total des tokens."""
        self.total_tokens = self.prompt_tokens + self.completion_tokens


class RateLimitInfo(BaseAIModel):
    """Informations sur les limites de taux."""
    
    requests_per_minute: int = Field(gt=0)
    tokens_per_minute: int = Field(gt=0)
    current_requests: int = Field(default=0, ge=0)
    current_tokens: int = Field(default=0, ge=0)
    reset_time: datetime
    
    @property
    def requests_remaining(self) -> int:
        """Nombre de requêtes restantes."""
        return max(0, self.requests_per_minute - self.current_requests)
    
    @property
    def tokens_remaining(self) -> int:
        """Nombre de tokens restants."""
        return max(0, self.tokens_per_minute - self.current_tokens)
    
    @property
    def is_rate_limited(self) -> bool:
        """Vérifie si on a atteint les limites."""
        return self.current_requests >= self.requests_per_minute or \
               self.current_tokens >= self.tokens_per_minute


class AIError(Exception):
    """Exception de base pour les erreurs IA."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class RateLimitError(AIError):
    """Erreur de limite de taux dépassée."""
    pass


class ModelNotAvailableError(AIError):
    """Erreur de modèle non disponible."""
    pass


class InvalidRequestError(AIError):
    """Erreur de requête invalide."""
    pass


class ProviderError(AIError):
    """Erreur du provider IA."""
    pass