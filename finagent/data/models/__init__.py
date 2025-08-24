"""
Module des modèles de données financières.

Ce module regroupe tous les modèles Pydantic utilisés pour
structurer et valider les données financières dans le système.
"""

# Modèles de base
from .base import (
    TimeFrame,
    MarketStatus,
    Currency,
    BaseFinancialModel,
    Symbol,
    DataQuality
)

# Modèles de données de marché
from .market_data import (
    Price,
    OHLCV,
    QuoteData,
    MarketDataCollection
)

# Modèles d'indicateurs techniques
from .technical_indicators import (
    IndicatorType,
    BaseIndicator,
    SimpleIndicator,
    MovingAverage,
    RSI,
    MACD,
    BollingerBands,
    Stochastic,
    IndicatorCollection
)

# Modèles de nouvelles financières
from .news import (
    NewsCategory,
    SentimentScore,
    NewsSource,
    NewsArticle,
    MarketEvent,
    SentimentAnalysis,
    NewsCollection
)

# Exports publics
__all__ = [
    # Base
    "TimeFrame",
    "MarketStatus", 
    "Currency",
    "BaseFinancialModel",
    "Symbol",
    "DataQuality",
    
    # Market Data
    "Price",
    "OHLCV",
    "QuoteData",
    "MarketDataCollection",
    
    # Technical Indicators
    "IndicatorType",
    "BaseIndicator",
    "SimpleIndicator",
    "MovingAverage",
    "RSI",
    "MACD",
    "BollingerBands",
    "Stochastic",
    "IndicatorCollection",
    
    # News
    "NewsCategory",
    "SentimentScore",
    "NewsSource",
    "NewsArticle",
    "MarketEvent",
    "SentimentAnalysis",
    "NewsCollection"
]

# Version du module models
__version__ = "1.0.0"

# Documentation des modèles principaux
MODEL_DESCRIPTIONS = {
    "OHLCV": "Modèle pour les données de prix (Open, High, Low, Close, Volume)",
    "Symbol": "Modèle pour un symbole financier avec métadonnées",
    "RSI": "Indicateur de force relative (Relative Strength Index)",
    "MACD": "Indicateur MACD (Moving Average Convergence Divergence)",
    "BollingerBands": "Bandes de Bollinger pour l'analyse de volatilité",
    "NewsArticle": "Article de nouvelles financières avec analyse de sentiment",
    "MarketEvent": "Événement de marché (earnings, dividendes, etc.)",
    "IndicatorCollection": "Collection d'indicateurs techniques pour un symbole",
    "NewsCollection": "Collection d'articles et événements financiers"
}

def get_model_info(model_name: str) -> str:
    """
    Retourne la description d'un modèle.
    
    Args:
        model_name: Nom du modèle
        
    Returns:
        Description du modèle ou message d'erreur
    """
    return MODEL_DESCRIPTIONS.get(model_name, f"Modèle '{model_name}' non trouvé")

def list_available_models() -> list[str]:
    """
    Liste tous les modèles disponibles.
    
    Returns:
        Liste des noms de modèles
    """
    return list(__all__)

def list_timeframes() -> list[str]:
    """
    Liste tous les timeframes supportés.
    
    Returns:
        Liste des timeframes
    """
    return [tf.value for tf in TimeFrame]

def list_currencies() -> list[str]:
    """
    Liste toutes les devises supportées.
    
    Returns:
        Liste des codes de devises
    """
    return [curr.value for curr in Currency]

def list_indicator_types() -> list[str]:
    """
    Liste tous les types d'indicateurs supportés.
    
    Returns:
        Liste des types d'indicateurs
    """
    return [ind.value for ind in IndicatorType]

def list_news_categories() -> list[str]:
    """
    Liste toutes les catégories de nouvelles supportées.
    
    Returns:
        Liste des catégories
    """
    return [cat.value for cat in NewsCategory]