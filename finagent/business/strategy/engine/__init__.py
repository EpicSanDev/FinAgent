"""
Moteur d'exécution pour les stratégies de trading.

Ce module contient le moteur principal d'exécution des stratégies,
l'évaluateur de règles et le générateur de signaux.
"""

from .strategy_engine import (
    StrategyEngine,
    EngineError,
    ExecutionContext,
    ExecutionResult
)

from .rule_evaluator import (
    RuleEvaluator,
    EvaluationContext,
    EvaluationResult,
    EvaluationError
)

from .signal_generator import (
    SignalGenerator,
    TradingSignal,
    SignalType,
    SignalConfidence,
    SignalGenerationError
)

__all__ = [
    # Strategy Engine
    "StrategyEngine",
    "EngineError",
    "ExecutionContext", 
    "ExecutionResult",
    
    # Rule Evaluator
    "RuleEvaluator",
    "EvaluationContext",
    "EvaluationResult",
    "EvaluationError",
    
    # Signal Generator
    "SignalGenerator",
    "TradingSignal",
    "SignalType",
    "SignalConfidence",
    "SignalGenerationError"
]