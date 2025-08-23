"""
Module des utilitaires pour la CLI FinAgent.

Ce module expose tous les utilitaires nécessaires pour
le bon fonctionnement de l'interface en ligne de commande.
"""

from .validation import (
    ValidationError,
    validate_symbol,
    validate_amount,
    validate_percentage,
    validate_date,
    validate_timeframe,
    validate_file_path,
    validate_strategy_name,
    validate_portfolio_name,
    format_validation_error,
    interactive_validation,
    SymbolParamType,
    AmountParamType,
    PercentageParamType,
    TimeframeParamType,
    SYMBOL,
    AMOUNT,
    POSITIVE_AMOUNT,
    PERCENTAGE,
    TIMEFRAME,
)

from .progress import (
    ProgressManager,
    SpinnerManager,
    StepProgress,
    BatchProgress,
    with_progress,
    with_spinner,
    async_progress_wrapper,
    create_status_panel,
    progress_manager,
    spinner_manager,
)

from .cache_utils import (
    CacheType,
    CacheEntry,
    CacheStats,
    CacheManager,
    cache_manager,
    format_size,
    create_cache_stats_table,
    create_cache_commands_panel,
)

__all__ = [
    # Validation
    "ValidationError",
    "validate_symbol",
    "validate_amount", 
    "validate_percentage",
    "validate_date",
    "validate_timeframe",
    "validate_file_path",
    "validate_strategy_name",
    "validate_portfolio_name",
    "format_validation_error",
    "interactive_validation",
    "SymbolParamType",
    "AmountParamType",
    "PercentageParamType", 
    "TimeframeParamType",
    "SYMBOL",
    "AMOUNT",
    "POSITIVE_AMOUNT",
    "PERCENTAGE",
    "TIMEFRAME",
    
    # Progress
    "ProgressManager",
    "SpinnerManager",
    "StepProgress",
    "BatchProgress",
    "with_progress",
    "with_spinner",
    "async_progress_wrapper",
    "create_status_panel",
    "progress_manager",
    "spinner_manager",
    
    # Cache
    "CacheType",
    "CacheEntry",
    "CacheStats",
    "CacheManager",
    "cache_manager",
    "format_size",
    "create_cache_stats_table",
    "create_cache_commands_panel",
]