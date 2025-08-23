"""
Utilitaires de test pour FinAgent.

Ce package contient tous les utilitaires, fixtures, mocks et helpers
nécessaires pour les tests de FinAgent.
"""

# Import des principales classes et fonctions utilitaires
from .test_fixtures import (
    StockDataFactory,
    TechnicalIndicatorsFactory,
    NewsDataFactory,
    AIRequestFactory,
    AIResponseFactory,
    PortfolioFactory,
    DecisionResultFactory,
    create_test_portfolio_with_positions,
    create_test_market_scenario,
    create_test_strategy_execution
)

from .mock_providers import (
    MockOpenBBProvider,
    MockClaudeProvider,
    MockHTTPResponse,
    create_openbb_mock,
    create_claude_mock,
    create_mock_http_client,
    create_database_mock,
    create_cache_mock
)

from .test_data_generator import (
    FinancialDataGenerator,
    PortfolioDataGenerator,
    StrategyDataGenerator,
    generate_test_dataset
)

from .test_helpers import (
    # Assertions
    assert_valid_uuid,
    assert_decimal_equals,
    assert_datetime_close,
    assert_portfolio_valid,
    assert_stock_data_valid,
    
    # Context managers
    temporary_config_file,
    temporary_directory,
    mock_environment_variables,
    async_timer,
    capture_logs,
    performance_benchmark,
    
    # Créateurs d'objets échantillon
    create_sample_ai_request,
    create_sample_ai_response,
    create_sample_stock_data,
    create_sample_portfolio,
    create_sample_position,
    
    # Helpers asynchrones
    wait_for_condition,
    run_with_timeout,
    make_async_test,
    
    # Validation
    validate_json_schema,
    validate_decimal_precision,
    validate_date_range,
    
    # Mocking
    create_mock_async_context_manager,
    patch_async_method,
    create_mock_http_response,
    
    # Performance
    PerformanceTimer,
    
    # Données de test
    load_test_data,
    save_test_data,
    
    # Nettoyage
    cleanup_test_files,
    reset_singletons,
    
    # Décorateurs
    skip_if_no_api_key,
    retry_on_failure
)

__all__ = [
    # Factories
    "StockDataFactory",
    "TechnicalIndicatorsFactory", 
    "NewsDataFactory",
    "AIRequestFactory",
    "AIResponseFactory",
    "PortfolioFactory",
    "DecisionResultFactory",
    
    # Mock providers
    "MockOpenBBProvider",
    "MockClaudeProvider",
    "MockHTTPResponse",
    "create_openbb_mock",
    "create_claude_mock",
    "create_mock_http_client",
    "create_database_mock",
    "create_cache_mock",
    
    # Data generators
    "FinancialDataGenerator",
    "PortfolioDataGenerator",
    "StrategyDataGenerator",
    "generate_test_dataset",
    
    # Test helpers
    "assert_valid_uuid",
    "assert_decimal_equals",
    "assert_datetime_close",
    "assert_portfolio_valid",
    "assert_stock_data_valid",
    "temporary_config_file",
    "temporary_directory",
    "mock_environment_variables",
    "async_timer",
    "capture_logs",
    "performance_benchmark",
    "create_sample_ai_request",
    "create_sample_ai_response",
    "create_sample_stock_data",
    "create_sample_portfolio",
    "create_sample_position",
    "wait_for_condition",
    "run_with_timeout",
    "make_async_test",
    "validate_json_schema",
    "validate_decimal_precision",
    "validate_date_range",
    "create_mock_async_context_manager",
    "patch_async_method",
    "create_mock_http_response",
    "PerformanceTimer",
    "load_test_data",
    "save_test_data",
    "cleanup_test_files",
    "reset_singletons",
    "skip_if_no_api_key",
    "retry_on_failure",
    
    # Complex creators
    "create_test_portfolio_with_positions",
    "create_test_market_scenario",
    "create_test_strategy_execution"
]

# Métadonnées du package
__version__ = "1.0.0"
__author__ = "FinAgent Test Suite"
__description__ = "Utilitaires de test pour FinAgent"