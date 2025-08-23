"""
Module IA pour l'agent financier.

Ce module fournit une intelligence artificielle complète pour l'analyse financière,
la prise de décision de trading, l'analyse de sentiment et l'interprétation de stratégies.
Il supporte Claude via OpenRouter et Ollama local pour alimenter tous les services d'IA.
"""

# Configuration existante et nouvelle configuration multi-providers
from .config import (
    AIConfig as LegacyAIConfig, AIConfigError,
    get_ai_config as get_legacy_ai_config,
    initialize_ai_config,
    initialize_ai_system,
    shutdown_ai_system
)

# Nouvelle configuration multi-providers
from .config import (
    AIConfig, ClaudeConfig, OllamaConfig,
    FallbackStrategy, ProviderPriority,
    get_ai_config, set_ai_config, create_ai_config_from_env
)

# Providers
from .providers.claude_provider import ClaudeProvider
from .providers.ollama_provider import (
    OllamaProvider, OllamaConfig as OllamaProviderConfig,
    OllamaModelInfo, create_ollama_provider
)

# Factory et services
from .factory import (
    AIProviderFactory, ProviderHealthStatus,
    get_ai_factory, create_ai_provider, shutdown_ai_factory
)

from .services.analysis_service import AnalysisService
from .services.decision_service import DecisionService
from .services.sentiment_service import SentimentService
from .services.strategy_service import StrategyService

from .prompts.prompt_manager import PromptManager

from .memory.memory_manager import MemoryManager
from .memory.conversation_memory import ConversationMemoryManager
from .memory.market_memory import MarketMemoryManager
from .memory.decision_memory import DecisionMemoryManager

from .models.base import (
    BaseAIModel, AIProvider, AIRequest, AIResponse,
    ModelType, ProviderType, ResponseFormat, ModelUtils
)

# Services de discovery
from .services.model_discovery_service import (
    ModelDiscoveryService, ModelDiscoveryInfo, ModelStatus,
    get_discovery_service, initialize_discovery_service,
    shutdown_discovery_service
)

from .models.financial_analysis import (
    AnalysisRequest as FinancialAnalysisRequest,
    AnalysisResult as FinancialAnalysisResponse,
    TechnicalIndicators as TechnicalAnalysis,
    FundamentalMetrics as FundamentalAnalysis,
    RiskLevel as RiskAnalysis,
    TrendDirection as MarketTrend,
    SentimentData as AnalysisInsight,
    MarketOverview as AnalysisRecommendation
)

from .models.trading_decision import (
    DecisionRequest as TradingDecisionRequest,
    TradingDecision as TradingDecisionResponse,
    DecisionType as TradingAction, RiskParameters as StopLoss,
    PortfolioImpact as TakeProfit, PositionSizing
)

from .models.memory import (
    MemoryType, MemoryEntry, ConversationMemory,
    MarketMemory, DecisionMemory, MemorySearchQuery,
    MemorySearchResult, MemoryPersistenceConfig, MemoryRetentionPolicy
)

# Import des enums spécifiques depuis les bons modules
from .models.base import ConfidenceLevel
from .models.financial_analysis import RiskLevel

# Import RiskLevel et ConfidenceLevel from base pour éviter les conflits
from .models.base import ConfidenceLevel
from .models.financial_analysis import RiskLevel

__version__ = "0.1.0"

__all__ = [
    # Configuration existante (rétrocompatibilité)
    "LegacyAIConfig",
    "AIConfigError",
    "get_legacy_ai_config",
    "initialize_ai_config",
    "initialize_ai_system",
    "shutdown_ai_system",
    
    # Nouvelle configuration multi-providers
    "AIConfig",
    "ClaudeConfig",
    "OllamaConfig",
    "FallbackStrategy",
    "ProviderPriority",
    "get_ai_config",
    "set_ai_config",
    "create_ai_config_from_env",
    
    # Providers
    "ClaudeProvider",
    "OllamaProvider",
    "OllamaProviderConfig",
    "OllamaModelInfo",
    "create_ollama_provider",
    
    # Factory et gestion des providers
    "AIProviderFactory",
    "ProviderHealthStatus",
    "get_ai_factory",
    "create_ai_provider",
    "shutdown_ai_factory",
    
    # Services
    "AnalysisService",
    "DecisionService", 
    "SentimentService",
    "StrategyService",
    
    # Gestionnaires
    "PromptManager",
    "MemoryManager",
    "ConversationMemoryManager",
    "MarketMemoryManager", 
    "DecisionMemoryManager",
    
    # Modèles de base
    "BaseAIModel",
    "AIProvider",
    "AIRequest",
    "AIResponse",
    "ModelType",
    "ProviderType",
    "ResponseFormat",
    "ModelUtils",
    
    # Services de discovery
    "ModelDiscoveryService",
    "ModelDiscoveryInfo",
    "ModelStatus",
    "get_discovery_service",
    "initialize_discovery_service",
    "shutdown_discovery_service",
    
    # Modèles d'analyse financière
    "FinancialAnalysisRequest",
    "FinancialAnalysisResponse",
    "TechnicalAnalysis",
    "FundamentalAnalysis", 
    "RiskAnalysis",
    "MarketTrend",
    "AnalysisInsight",
    "AnalysisRecommendation",
    
    # Modèles de décision de trading
    "TradingDecisionRequest",
    "TradingDecisionResponse", 
    "TradingAction",
    "ConfidenceLevel",
    "RiskLevel",
    "PositionSizing",
    "StopLoss",
    "TakeProfit",
    
    # Modèles de mémoire
    "MemoryType",
    "MemoryEntry",
    "ConversationMemory",
    "MarketMemory",
    "DecisionMemory", 
    "MemorySearchQuery",
    "MemorySearchResult",
    "MemoryPersistenceConfig",
    "MemoryRetentionPolicy",
]


def get_version() -> str:
    """Retourne la version du module IA."""
    return __version__


async def get_available_models() -> dict[str, list[str]]:
    """
    Retourne la liste des modèles IA disponibles par provider.
    
    Returns:
        Dictionnaire des modèles disponibles par provider
    """
    models = {
        "claude": [
            "anthropic/claude-3.5-sonnet-20241022",
            "anthropic/claude-3-sonnet-20240229",
            "anthropic/claude-3-haiku-20240307",
            "anthropic/claude-3-opus-20240229"
        ],
        "ollama": []
    }
    
    # Récupère les modèles Ollama disponibles
    try:
        discovery_service = await get_discovery_service()
        if discovery_service:
            ollama_models = discovery_service.get_available_models()
            models["ollama"] = [model.value for model in ollama_models]
    except Exception:
        pass  # Service non disponible
    
    return models


async def get_service_status() -> dict[str, any]:
    """
    Retourne le statut des services IA incluant les nouveaux providers.
    
    Returns:
        Dictionnaire du statut de chaque service et provider
    """
    # Nouveau statut basé sur les providers modernes
    service_status = {
        "analysis_service": False,
        "decision_service": False,
        "sentiment_service": False,
        "strategy_service": False,
        "memory_manager": False,
        "legacy_provider": False
    }
    
    # Vérifier la disponibilité des services via les nouveaux providers
    try:
        factory = await get_ai_factory()
        provider_health = factory.get_provider_health_status()
        
        # Si au moins un provider est disponible, les services le sont aussi
        has_available_provider = any(
            status.get("available", False)
            for status in provider_health.values()
        )
        
        if has_available_provider:
            service_status = {
                "analysis_service": True,
                "decision_service": True,
                "sentiment_service": True,
                "strategy_service": True,
                "memory_manager": True,
                "legacy_provider": True
            }
    except Exception:
        # Fallback vers legacy config si nécessaire
        try:
            legacy_config = get_legacy_ai_config()
            if legacy_config and hasattr(legacy_config, '_initialized') and legacy_config._initialized:
                service_status = {
                    "analysis_service": legacy_config.analysis_service is not None,
                    "decision_service": legacy_config.decision_service is not None,
                    "sentiment_service": legacy_config.sentiment_service is not None,
                    "strategy_service": legacy_config.strategy_service is not None,
                    "memory_manager": legacy_config.memory_manager is not None,
                    "legacy_provider": legacy_config.provider is not None
                }
        except Exception:
            pass  # Garder les valeurs par défaut
    
    # Statut des nouveaux providers
    provider_status = {}
    try:
        factory = await get_ai_factory()
        provider_status = factory.get_provider_health_status()
    except Exception:
        provider_status = {
            "claude": {"available": False, "error": "Non initialisé"},
            "ollama": {"available": False, "error": "Non initialisé"}
        }
    
    # Statut du service de discovery
    discovery_status = False
    try:
        discovery_service = await get_discovery_service()
        discovery_status = discovery_service is not None
    except Exception:
        pass
    
    return {
        "services": service_status,
        "providers": provider_status,
        "discovery_service": discovery_status,
        "factory_initialized": provider_status != {}
    }