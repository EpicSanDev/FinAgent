"""
Module des validators pour les données financières.

Ce module regroupe tous les validators utilisés pour valider
et nettoyer les données financières dans le système.
"""

# Validators de base
from .base import (
    ValidationError,
    BaseValidator,
    validate_symbol_param,
    validate_timeframe_param,
    validate_date_range_params
)

# Validators de données de marché
from .market_data import (
    MarketDataValidator,
    QuoteValidator
)

# Validators d'indicateurs techniques
from .technical_indicators import (
    IndicatorValidator
)

# Exports publics
__all__ = [
    # Base
    "ValidationError",
    "BaseValidator",
    "validate_symbol_param",
    "validate_timeframe_param", 
    "validate_date_range_params",
    
    # Market Data
    "MarketDataValidator",
    "QuoteValidator",
    
    # Technical Indicators
    "IndicatorValidator"
]

# Version du module validators
__version__ = "1.0.0"

# Fonctions utilitaires pour validation rapide
def validate_symbol(symbol: str) -> str:
    """
    Fonction utilitaire pour valider un symbole.
    
    Args:
        symbol: Symbole à valider
        
    Returns:
        Symbole normalisé
        
    Raises:
        ValidationError: Si le symbole est invalide
    """
    return BaseValidator.normalize_symbol(symbol)

def validate_symbols(symbols: list[str]) -> list[str]:
    """
    Fonction utilitaire pour valider une liste de symboles.
    
    Args:
        symbols: Liste de symboles
        
    Returns:
        Liste de symboles normalisés
        
    Raises:
        ValidationError: Si un symbole est invalide
    """
    return BaseValidator.validate_symbols_list(symbols)

def validate_timeframe(timeframe: str) -> str:
    """
    Fonction utilitaire pour valider un timeframe.
    
    Args:
        timeframe: Timeframe à valider
        
    Returns:
        Timeframe validé
        
    Raises:
        ValidationError: Si le timeframe est invalide
    """
    return BaseValidator.normalize_timeframe(timeframe).value

def validate_period(period: int, min_period: int = 1, max_period: int = 1000) -> int:
    """
    Fonction utilitaire pour valider une période.
    
    Args:
        period: Période à valider
        min_period: Période minimale
        max_period: Période maximale
        
    Returns:
        Période validée
        
    Raises:
        ValidationError: Si la période est invalide
    """
    return BaseValidator.validate_period(period, min_period, max_period)

def validate_positive_number(value, field_name: str = "value"):
    """
    Fonction utilitaire pour valider un nombre positif.
    
    Args:
        value: Valeur à valider
        field_name: Nom du champ pour les erreurs
        
    Returns:
        Valeur validée en Decimal
        
    Raises:
        ValidationError: Si la valeur est invalide
    """
    return BaseValidator.validate_positive_number(value, field_name)

# Dictionnaire des validators par type de données
VALIDATORS_BY_TYPE = {
    'symbol': BaseValidator.normalize_symbol,
    'timeframe': BaseValidator.normalize_timeframe,
    'period': BaseValidator.validate_period,
    'positive_number': BaseValidator.validate_positive_number,
    'percentage': BaseValidator.validate_percentage,
    'currency': BaseValidator.validate_currency,
    'symbols_list': BaseValidator.validate_symbols_list,
    'url': BaseValidator.validate_url,
    'text': BaseValidator.clean_text
}

def get_validator(data_type: str):
    """
    Retourne le validator approprié pour un type de données.
    
    Args:
        data_type: Type de données
        
    Returns:
        Fonction de validation ou None
    """
    return VALIDATORS_BY_TYPE.get(data_type)

def list_available_validators() -> list[str]:
    """
    Liste tous les validators disponibles.
    
    Returns:
        Liste des types de données supportés
    """
    return list(VALIDATORS_BY_TYPE.keys())

# Configuration de validation par défaut
DEFAULT_VALIDATION_CONFIG = {
    'symbol': {
        'required': True,
        'normalize': True,
        'max_length': 10
    },
    'timeframe': {
        'required': True,
        'normalize': True,
        'allowed_values': ['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w', '1M']
    },
    'period': {
        'required': True,
        'min_value': 1,
        'max_value': 1000,
        'default': 14
    },
    'symbols_list': {
        'max_symbols': 50,
        'remove_duplicates': True,
        'normalize': True
    }
}

def get_validation_config(data_type: str) -> dict:
    """
    Retourne la configuration de validation pour un type de données.
    
    Args:
        data_type: Type de données
        
    Returns:
        Configuration de validation
    """
    return DEFAULT_VALIDATION_CONFIG.get(data_type, {})

# Fonctions de validation composite
def validate_ohlcv_data(open_price, high_price, low_price, close_price, volume=None):
    """
    Valide des données OHLCV complètes.
    
    Args:
        open_price: Prix d'ouverture
        high_price: Prix le plus haut
        low_price: Prix le plus bas
        close_price: Prix de fermeture
        volume: Volume (optionnel)
        
    Returns:
        Dictionnaire des données validées
        
    Raises:
        ValidationError: Si les données sont invalides
    """
    return MarketDataValidator.validate_ohlcv_data(
        open_price, high_price, low_price, close_price, volume
    )

def validate_indicator_params(indicator_type: str, **params):
    """
    Valide les paramètres d'un indicateur technique.
    
    Args:
        indicator_type: Type d'indicateur
        **params: Paramètres de l'indicateur
        
    Returns:
        Paramètres validés
        
    Raises:
        ValidationError: Si les paramètres sont invalides
    """
    from ..models.technical_indicators import IndicatorType
    
    try:
        ind_type = IndicatorType(indicator_type.lower())
    except ValueError:
        raise ValidationError(f"Type d'indicateur invalide: {indicator_type}")
    
    # Validation selon le type d'indicateur
    if ind_type == IndicatorType.RSI:
        return IndicatorValidator.validate_rsi_parameters(
            params.get('period', 14)
        )
    elif ind_type == IndicatorType.MACD:
        return IndicatorValidator.validate_macd_parameters(
            params.get('fast_period', 12),
            params.get('slow_period', 26),
            params.get('signal_period', 9)
        )
    elif ind_type == IndicatorType.BOLLINGER:
        return IndicatorValidator.validate_bollinger_parameters(
            params.get('period', 20),
            params.get('std_multiplier', 2.0)
        )
    elif ind_type == IndicatorType.STOCH:
        return IndicatorValidator.validate_stochastic_parameters(
            params.get('k_period', 14),
            params.get('d_period', 3),
            params.get('smooth_k', 1)
        )
    else:
        # Validation générique pour autres indicateurs
        period = params.get('period')
        if period is not None:
            return {
                'period': IndicatorValidator.validate_indicator_period(ind_type, period)
            }
        return params

# Cache des résultats de validation pour éviter les re-validations
_validation_cache = {}

def cached_validate(cache_key: str, validator_func, *args, **kwargs):
    """
    Validation avec cache pour éviter les re-validations.
    
    Args:
        cache_key: Clé de cache
        validator_func: Fonction de validation
        *args: Arguments positionnels
        **kwargs: Arguments nommés
        
    Returns:
        Résultat de la validation (depuis le cache ou calculé)
    """
    if cache_key in _validation_cache:
        return _validation_cache[cache_key]
    
    result = validator_func(*args, **kwargs)
    _validation_cache[cache_key] = result
    return result

def clear_validation_cache():
    """Vide le cache de validation."""
    global _validation_cache
    _validation_cache.clear()

def get_cache_stats() -> dict:
    """
    Retourne les statistiques du cache de validation.
    
    Returns:
        Statistiques du cache
    """
    return {
        'cache_size': len(_validation_cache),
        'cache_keys': list(_validation_cache.keys())
    }