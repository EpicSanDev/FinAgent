"""
Module de gestion de portefeuille.

Ce module contient tous les composants nécessaires pour la gestion complète
d'un portefeuille d'investissement :

- PortfolioManager : Gestionnaire principal du portefeuille
- PositionManager : Gestion détaillée des positions
- PerformanceTracker : Suivi et analyse des performances
- Rebalancer : Rééquilibrage automatique du portefeuille

Utilisation :
    from finagent.business.portfolio import (
        PortfolioManager,
        PositionManager,
        PerformanceTracker,
        Rebalancer
    )
"""

from .portfolio_manager import PortfolioManager
from .position_manager import PositionManager
from .performance_tracker import PerformanceTracker
from .rebalancer import Rebalancer

__all__ = [
    'PortfolioManager',
    'PositionManager', 
    'PerformanceTracker',
    'Rebalancer'
]

__version__ = '1.0.0'
__author__ = 'FinAgent Team'