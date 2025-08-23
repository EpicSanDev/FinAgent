"""
Modèles de données pour le système de stratégies.

Ce module contient tous les modèles Pydantic utilisés pour valider
et structurer les configurations de stratégies YAML.
"""

from .strategy_models import (
    Strategy,
    StrategyConfig,
    StrategySettings,
    StrategyUniverse,
    StrategyAnalysis,
    StrategyRiskManagement,
    StrategyBacktesting,
    StrategyAlerts,
    StrategyStatus,
    StrategyPerformance,
    StrategyType,
    RiskTolerance,
    TimeHorizon,
    MarketCap,
    RiskLevel
)

from .rule_models import (
    Rule,
    BuyConditions,
    SellConditions,
    FilterCondition,
    ConditionOperator,
    RuleOperator
)

from .condition_models import (
    BaseCondition,
    IndicatorType,
    ComparisonOperator,
    TechnicalIndicator,
    FundamentalIndicator,
    SentimentIndicator,
    RSIIndicator,
    MACDIndicator,
    MovingAverageIndicator,
    BollingerBandsIndicator,
    VolumeIndicator,
    ValuationIndicator,
    GrowthIndicator,
    NewsSentimentIndicator,
    SocialSentimentIndicator,
    MarketConditionIndicator,
    RiskMetricIndicator,
    ConditionEvaluationResult,
    IndicatorCalculationResult
)

__all__ = [
    # Strategy models
    "Strategy",
    "StrategyConfig",
    "StrategySettings",
    "StrategyUniverse",
    "StrategyAnalysis",
    "StrategyRiskManagement",
    "StrategyBacktesting",
    "StrategyAlerts",
    "StrategyStatus",
    "StrategyPerformance",
    "StrategyType",
    "RiskTolerance",
    "TimeHorizon",
    "MarketCap",
    "RiskLevel",
    
    # Rule models
    "Rule",
    "BuyConditions",
    "SellConditions", 
    "FilterCondition",
    "ConditionOperator",
    "RuleOperator",
    
    # Condition models
    "BaseCondition",
    "IndicatorType",
    "ComparisonOperator",
    "TechnicalIndicator",
    "FundamentalIndicator",
    "SentimentIndicator",
    "RSIIndicator",
    "MACDIndicator",
    "MovingAverageIndicator",
    "BollingerBandsIndicator",
    "VolumeIndicator",
    "ValuationIndicator",
    "GrowthIndicator",
    "NewsSentimentIndicator",
    "SocialSentimentIndicator",
    "MarketConditionIndicator",
    "RiskMetricIndicator",
    "ConditionEvaluationResult",
    "IndicatorCalculationResult"
]