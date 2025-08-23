"""
Module de gestion des stratégies de trading.

Ce module contient les composants de haut niveau pour orchestrer
les stratégies de trading, gérer l'allocation de portefeuille
et contrôler les risques.
"""

from .strategy_manager import (
    StrategyManager,
    StrategyInstance,
    ManagerMetrics,
    ManagerStatus,
    StrategyManagerError
)

from .portfolio_allocator import (
    PortfolioAllocator,
    AllocationResult,
    PositionAllocation,
    AllocationMethod,
    AllocationStatus,
    AllocationConstraint,
    PortfolioState,
    AllocationError
)

from .risk_manager import (
    StrategyRiskManager,
    RiskAssessment,
    RiskMetric,
    RiskLimit,
    PortfolioRisk,
    RiskLevel,
    RiskType,
    RiskManagerError
)

__all__ = [
    # Strategy Manager
    'StrategyManager',
    'StrategyInstance',
    'ManagerMetrics',
    'ManagerStatus',
    'StrategyManagerError',
    
    # Portfolio Allocator
    'PortfolioAllocator',
    'AllocationResult',
    'PositionAllocation',
    'AllocationMethod',
    'AllocationStatus',
    'AllocationConstraint',
    'PortfolioState',
    'AllocationError',
    
    # Risk Manager
    'StrategyRiskManager',
    'RiskAssessment',
    'RiskMetric',
    'RiskLimit',
    'PortfolioRisk',
    'RiskLevel',
    'RiskType',
    'RiskManagerError'
]