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
    """Types de modèles AI disponibles (Claude et Ollama)."""
    # Modèles Claude via OpenRouter
    CLAUDE_3_SONNET = "claude-3-sonnet-20240229"
    CLAUDE_3_HAIKU = "claude-3-haiku-20240307"
    CLAUDE_3_OPUS = "claude-3-opus-20240229"
    CLAUDE_3_5_SONNET = "claude-3-5-sonnet-20241022"
    CLAUDE_3_5_HAIKU = "claude-3-5-haiku-20241022"
    
    # Modèles Ollama locaux - Llama famille
    LLAMA2_7B = "llama2:7b"
    LLAMA2_13B = "llama2:13b"
    LLAMA2_70B = "llama2:70b"
    LLAMA3_8B = "llama3:8b"
    LLAMA3_70B = "llama3:70b"
    LLAMA3_1_8B = "llama3.1:8b"
    LLAMA3_1_70B = "llama3.1:70b"
    
    # Modèles Ollama - Mistral famille
    MISTRAL_7B = "mistral:7b"
    MISTRAL_INSTRUCT = "mistral:7b-instruct"
    MIXTRAL_8X7B = "mixtral:8x7b"
    MIXTRAL_8X22B = "mixtral:8x22b"
    
    # Modèles Ollama - Code spécialisés
    CODELLAMA_7B = "codellama:7b"
    CODELLAMA_13B = "codellama:13b"
    CODELLAMA_34B = "codellama:34b"
    CODELLAMA_INSTRUCT = "codellama:7b-instruct"
    
    # Modèles Ollama - Autres
    GEMMA_2B = "gemma:2b"
    GEMMA_7B = "gemma:7b"
    PHI3_MINI = "phi3:mini"
    PHI3_MEDIUM = "phi3:medium"
    QWEN2_7B = "qwen2:7b"
    QWEN2_72B = "qwen2:72b"
    
    # Modèles spécialisés finance (customs)
    FINLLAMA_7B = "finllama:7b"
    FINMISTRAL_7B = "finmistral:7b"


class ProviderType(str, Enum):
    """Types de providers AI disponibles."""
    CLAUDE = "claude"
    OLLAMA = "ollama"
    OPENAI = "openai"


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
    
    @abstractmethod
    def get_provider_type(self) -> ProviderType:
        """Retourne le type du provider."""
        pass


class ModelUtils:
    """Utilitaires pour la gestion des modèles."""
    
    @staticmethod
    def get_provider_for_model(model: ModelType) -> ProviderType:
        """Détermine le provider approprié pour un modèle donné."""
        if model.value.startswith(("claude-", "anthropic/")):
            return ProviderType.CLAUDE
        elif model.value.startswith(("gpt-", "openai/")):
            return ProviderType.OPENAI
        else:
            # Tous les autres modèles sont considérés comme Ollama
            return ProviderType.OLLAMA
    
    @staticmethod
    def is_ollama_model(model: ModelType) -> bool:
        """Vérifie si un modèle est un modèle Ollama."""
        return ModelUtils.get_provider_for_model(model) == ProviderType.OLLAMA
    
    @staticmethod
    def is_claude_model(model: ModelType) -> bool:
        """Vérifie si un modèle est un modèle Claude."""
        return ModelUtils.get_provider_for_model(model) == ProviderType.CLAUDE
    
    @staticmethod
    def get_model_size_category(model: ModelType) -> str:
        """Catégorise la taille du modèle."""
        model_str = model.value.lower()
        if any(size in model_str for size in ["2b", "mini"]):
            return "small"
        elif any(size in model_str for size in ["7b", "8b"]):
            return "medium"
        elif any(size in model_str for size in ["13b", "22b"]):
            return "large"
        elif any(size in model_str for size in ["34b", "70b", "72b"]):
            return "xlarge"
        else:
            return "unknown"
    
    @staticmethod
    def get_recommended_models_for_task(task_type: str) -> List[ModelType]:
        """Recommande des modèles selon le type de tâche."""
        recommendations = {
            "analysis": [
                ModelType.LLAMA3_1_8B,
                ModelType.MISTRAL_7B,
                ModelType.CLAUDE_3_SONNET
            ],
            "decision": [
                ModelType.LLAMA3_1_70B,
                ModelType.MIXTRAL_8X7B,
                ModelType.CLAUDE_3_5_SONNET
            ],
            "sentiment": [
                ModelType.GEMMA_7B,
                ModelType.MISTRAL_INSTRUCT,
                ModelType.CLAUDE_3_HAIKU
            ],
            "strategy": [
                ModelType.CODELLAMA_13B,
                ModelType.LLAMA3_1_70B,
                ModelType.CLAUDE_3_OPUS
            ],
            "code": [
                ModelType.CODELLAMA_INSTRUCT,
                ModelType.CODELLAMA_34B,
                ModelType.CLAUDE_3_5_SONNET
            ]
        }
        return recommendations.get(task_type, [ModelType.LLAMA3_1_8B])


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