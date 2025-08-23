"""
Modèles de données pour l'intégration IA.
"""

# Modèles de base
from .base import (
    BaseAIModel,
    ModelType,
    ProviderType,
    ConfidenceLevel,
    AIRequest,
    AIResponse,
    AIProvider,
    ModelUtils,
    TokenUsage,
    RateLimitInfo,
    AIError,
    RateLimitError,
    ModelNotAvailableError,
    InvalidRequestError,
    ProviderError,
)

# Modèles d'analyse financière
from .financial_analysis import (
    AnalysisType,
    TrendDirection,
    MarketSentiment,
    RiskLevel,
    MarketContext,
    TechnicalIndicators,
    FundamentalMetrics,
    SentimentData,
    AnalysisRequest,
    AnalysisResult,
    MarketOverview,
)

# Modèles de décision de trading
from .trading_decision import (
    DecisionType,
    OrderType,
    TimeInForce,
    PositionSizing,
    TradingContext,
    RiskParameters,
    DecisionRequest,
    TradingDecision,
    DecisionHistory,
    PortfolioImpact,
)

# Modèles de mémoire
from .memory import (
    MemoryType,
    MemoryImportance,
    MemoryStatus,
    ConversationTurn,
    ConversationMemory,
    MarketPattern,
    DecisionOutcome,
    UserPreference,
    MemoryEntry,
    MemoryQuery,
    MemorySearchResult,
)

__all__ = [
    # Base
    "BaseAIModel",
    "ModelType",
    "ConfidenceLevel",
    "AIRequest",
    "AIResponse",
    "AIProvider",
    "TokenUsage",
    "RateLimitInfo",
    "AIError",
    "RateLimitError",
    "ModelNotAvailableError",
    "InvalidRequestError",
    "ProviderError",
    
    # Financial Analysis
    "AnalysisType",
    "TrendDirection",
    "MarketSentiment",
    "RiskLevel",
    "MarketContext",
    "TechnicalIndicators",
    "FundamentalMetrics",
    "SentimentData",
    "AnalysisRequest",
    "AnalysisResult",
    "MarketOverview",
    
    # Trading Decision
    "DecisionType",
    "OrderType",
    "TimeInForce",
    "PositionSizing",
    "TradingContext",
    "RiskParameters",
    "DecisionRequest",
    "TradingDecision",
    "DecisionHistory",
    "PortfolioImpact",
    
    # Memory
    "MemoryType",
    "MemoryImportance",
    "MemoryStatus",
    "ConversationTurn",
    "ConversationMemory",
    "MarketPattern",
    "DecisionOutcome",
    "UserPreference",
    "MemoryEntry",
    "MemoryQuery",
    "MemorySearchResult",
]