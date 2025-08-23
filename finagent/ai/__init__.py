"""
Module IA pour l'agent financier.

Ce module fournit une intelligence artificielle complète pour l'analyse financière,
la prise de décision de trading, l'analyse de sentiment et l'interprétation de stratégies.
Il utilise Claude via OpenRouter pour alimenter tous les services d'IA.
"""

from .config import (
    AIConfig, AIConfigError, 
    get_ai_config, initialize_ai_config, 
    initialize_ai_system, shutdown_ai_system
)

from .providers.claude_provider import ClaudeProvider

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
    ModelType, ResponseFormat
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
    # Configuration et initialisation
    "AIConfig",
    "AIConfigError", 
    "get_ai_config",
    "initialize_ai_config",
    "initialize_ai_system",
    "shutdown_ai_system",
    
    # Provider
    "ClaudeProvider",
    
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
    "ResponseFormat",
    
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


def get_available_models() -> list[str]:
    """
    Retourne la liste des modèles IA disponibles.
    
    Returns:
        Liste des modèles disponibles
    """
    return [
        "anthropic/claude-3.5-sonnet-20241022",
        "anthropic/claude-3-sonnet-20240229", 
        "anthropic/claude-3-haiku-20240307",
        "anthropic/claude-3-opus-20240229"
    ]


def get_service_status() -> dict[str, bool]:
    """
    Retourne le statut des services IA.
    
    Returns:
        Dictionnaire du statut de chaque service
    """
    ai_config = get_ai_config()
    
    if not ai_config or not ai_config._initialized:
        return {
            "analysis_service": False,
            "decision_service": False,
            "sentiment_service": False,
            "strategy_service": False,
            "memory_manager": False,
            "provider": False
        }
    
    return {
        "analysis_service": ai_config.analysis_service is not None,
        "decision_service": ai_config.decision_service is not None,
        "sentiment_service": ai_config.sentiment_service is not None,
        "strategy_service": ai_config.strategy_service is not None,
        "memory_manager": ai_config.memory_manager is not None,
        "provider": ai_config.provider is not None
    }