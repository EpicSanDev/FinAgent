"""
Module des formatters pour la CLI FinAgent.

Ce module expose tous les formatters spécialisés pour
le formatage élégant des sorties CLI.
"""

from .base_formatter import BaseFormatter
from .market_formatter import MarketFormatter
from .analysis_formatter import AnalysisFormatter
from .portfolio_formatter import PortfolioFormatter
from .decision_formatter import DecisionFormatter

__all__ = [
    "BaseFormatter",
    "MarketFormatter", 
    "AnalysisFormatter",
    "PortfolioFormatter",
    "DecisionFormatter",
]

# Factory pour créer le bon formatter selon le type de données
def create_formatter(data_type: str, **kwargs) -> BaseFormatter:
    """
    Factory pour créer le formatter approprié selon le type de données.
    
    Args:
        data_type: Type de données à formater
        **kwargs: Arguments pour l'initialisation du formatter
        
    Returns:
        Instance du formatter approprié
        
    Raises:
        ValueError: Si le type de données n'est pas supporté
    """
    formatters = {
        "market": MarketFormatter,
        "analysis": AnalysisFormatter,
        "portfolio": PortfolioFormatter,
        "decision": DecisionFormatter,
    }
    
    if data_type not in formatters:
        raise ValueError(f"Type de formatter non supporté: {data_type}")
    
    return formatters[data_type](**kwargs)