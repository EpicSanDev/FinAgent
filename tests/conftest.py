"""
Configuration globale pytest pour FinAgent.

Ce module contient toutes les fixtures globales et la configuration
des tests pour l'ensemble de la suite de tests FinAgent.
"""

import asyncio
import os
import sys
import tempfile
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Dict, Any, AsyncGenerator, Generator
from unittest.mock import Mock, AsyncMock
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient
from freezegun import freeze_time

# Ajout du répertoire racine au path pour les imports
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from finagent.core.errors.exceptions import (
    FinAgentException,
    APIConnectionError,
    DataValidationError,
    ConfigurationError
)
from finagent.ai.models.base import (
    AIRequest,
    AIResponse, 
    ModelType,
    ConfidenceLevel
)


# ============================================================================
# CONFIGURATION GLOBALE
# ============================================================================

def pytest_configure(config):
    """Configuration globale pytest."""
    # Définir les variables d'environnement pour les tests
    os.environ.setdefault("FINAGENT_TEST_MODE", "true")
    os.environ.setdefault("FINAGENT_LOG_LEVEL", "ERROR")
    os.environ.setdefault("FINAGENT_DB_URL", "sqlite:///:memory:")
    
    # Désactiver les appels API réels en mode test
    os.environ.setdefault("FINAGENT_DISABLE_EXTERNAL_APIS", "true")


def pytest_collection_modifyitems(config, items):
    """Modifier les éléments de collection de tests."""
    # Marquer automatiquement les tests selon leurs noms
    for item in items:
        # Tests lents
        if "slow" in item.nodeid or "integration" in item.nodeid:
            item.add_marker(pytest.mark.slow)
            
        # Tests d'API
        if "api" in item.nodeid or "openbb" in item.nodeid or "claude" in item.nodeid:
            item.add_marker(pytest.mark.api)
            
        # Tests CLI
        if "cli" in item.nodeid:
            item.add_marker(pytest.mark.cli)


# ============================================================================
# FIXTURES DE BASE
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Fixture pour loop d'événements asyncio partagé."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir():
    """Répertoire temporaire pour les tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def mock_config():
    """Configuration mock pour les tests."""
    return {
        "openbb": {
            "api_key": "test_openbb_key",
            "base_url": "https://api.test.openbb.co"
        },
        "claude": {
            "api_key": "test_claude_key", 
            "base_url": "https://api.test.openrouter.ai"
        },
        "database": {
            "url": "sqlite:///:memory:"
        },
        "logging": {
            "level": "ERROR"
        }
    }


@pytest.fixture
def mock_datetime():
    """DateTime fixe pour les tests."""
    fixed_time = datetime(2024, 1, 15, 10, 30, 0)
    with freeze_time(fixed_time):
        yield fixed_time


# ============================================================================
# FIXTURES DONNÉES FINANCIÈRES
# ============================================================================

@pytest.fixture
def sample_stock_data():
    """Données d'actions échantillon."""
    return {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "price": Decimal("150.25"),
        "change": Decimal("2.50"),
        "change_percent": Decimal("1.69"),
        "volume": 45_000_000,
        "market_cap": 2_500_000_000_000,
        "pe_ratio": Decimal("25.3"),
        "dividend_yield": Decimal("0.5"),
        "52_week_high": Decimal("175.00"),
        "52_week_low": Decimal("120.00")
    }


@pytest.fixture
def sample_market_indicators():
    """Indicateurs de marché échantillon."""
    return {
        "rsi": Decimal("65.4"),
        "macd": Decimal("1.23"),
        "macd_signal": Decimal("1.15"),
        "bb_upper": Decimal("155.00"),
        "bb_middle": Decimal("150.00"),
        "bb_lower": Decimal("145.00"),
        "sma_20": Decimal("148.50"),
        "sma_50": Decimal("145.25"),
        "volume_sma": 42_000_000
    }


@pytest.fixture
def sample_news_data():
    """Données de news échantillon."""
    return [
        {
            "title": "Apple Reports Strong Q4 Earnings",
            "content": "Apple Inc. reported strong quarterly earnings...",
            "published_at": datetime.now() - timedelta(hours=2),
            "source": "Financial Times",
            "sentiment": "positive",
            "relevance": 0.95
        },
        {
            "title": "Tech Stocks Rally Continues",
            "content": "Technology stocks continue to show strength...",
            "published_at": datetime.now() - timedelta(hours=6),
            "source": "Reuters", 
            "sentiment": "neutral",
            "relevance": 0.75
        }
    ]


# ============================================================================
# FIXTURES IA ET PROVIDERS
# ============================================================================

@pytest.fixture
def mock_ai_request():
    """Requête IA mock."""
    return AIRequest(
        prompt="Analyze AAPL stock performance",
        model_type=ModelType.CLAUDE_3_SONNET,
        temperature=0.3,
        max_tokens=2000
    )


@pytest.fixture
def mock_ai_response():
    """Réponse IA mock."""
    return AIResponse(
        request_id=uuid4(),
        content="Apple stock shows strong fundamentals with positive outlook...",
        model_used=ModelType.CLAUDE_3_SONNET,
        tokens_used=250,
        processing_time=1.5,
        confidence=ConfidenceLevel.HIGH
    )


@pytest.fixture
def mock_claude_provider():
    """Provider Claude mock."""
    provider = AsyncMock()
    provider.send_request.return_value = AIResponse(
        request_id=uuid4(),
        content="Mock AI analysis response",
        model_used=ModelType.CLAUDE_3_SONNET,
        tokens_used=200,
        processing_time=1.0,
        confidence=ConfidenceLevel.MEDIUM
    )
    provider.validate_connection.return_value = True
    provider.get_available_models.return_value = [
        ModelType.CLAUDE_3_SONNET,
        ModelType.CLAUDE_3_HAIKU
    ]
    return provider


@pytest.fixture
def mock_openbb_provider():
    """Provider OpenBB mock."""
    provider = AsyncMock()
    
    # Mock des données de marché
    provider.get_stock_data.return_value = {
        "symbol": "AAPL",
        "price": 150.25,
        "change": 2.50,
        "volume": 45000000
    }
    
    # Mock des indicateurs techniques
    provider.get_technical_indicators.return_value = {
        "rsi": 65.4,
        "macd": 1.23,
        "sma_20": 148.50
    }
    
    # Mock des news
    provider.get_news.return_value = [
        {
            "title": "Apple Reports Earnings",
            "published_at": datetime.now(),
            "sentiment": "positive"
        }
    ]
    
    return provider


# ============================================================================
# FIXTURES HTTP ET RÉSEAU
# ============================================================================

@pytest.fixture
async def http_client():
    """Client HTTP async pour les tests."""
    async with AsyncClient() as client:
        yield client


@pytest.fixture
def mock_http_responses():
    """Réponses HTTP mock."""
    return {
        "openbb_stock": {
            "status_code": 200,
            "json": {
                "symbol": "AAPL",
                "price": 150.25,
                "change": 2.50
            }
        },
        "claude_analysis": {
            "status_code": 200, 
            "json": {
                "choices": [{
                    "message": {
                        "content": "Stock analysis response"
                    }
                }]
            }
        }
    }


# ============================================================================
# FIXTURES STRATÉGIES ET DÉCISIONS
# ============================================================================

@pytest.fixture
def sample_strategy_config():
    """Configuration de stratégie échantillon."""
    return {
        "name": "Test Momentum Strategy",
        "type": "technical",
        "risk_tolerance": "medium",
        "time_horizon": "medium",
        "rules": [
            {
                "name": "RSI Oversold",
                "conditions": [
                    {
                        "indicator": "rsi",
                        "operator": "<",
                        "value": 30
                    }
                ],
                "action": "buy",
                "weight": 0.7
            }
        ]
    }


@pytest.fixture
def sample_portfolio():
    """Portfolio échantillon."""
    return {
        "id": uuid4(),
        "name": "Test Portfolio",
        "cash": Decimal("10000.00"),
        "total_value": Decimal("15000.00"),
        "positions": [
            {
                "symbol": "AAPL",
                "quantity": 20,
                "average_cost": Decimal("140.00"),
                "current_price": Decimal("150.25")
            }
        ]
    }


# ============================================================================
# FIXTURES CLI
# ============================================================================

@pytest.fixture
def cli_runner():
    """Runner pour tester les commandes CLI."""
    from click.testing import CliRunner
    return CliRunner()


@pytest.fixture
def mock_cli_context():
    """Contexte CLI mock."""
    return {
        "config": None,
        "verbose": False,
        "debug": False
    }


# ============================================================================
# FIXTURES EXCEPTIONS ET ERREURS
# ============================================================================

@pytest.fixture
def sample_exceptions():
    """Exceptions échantillon pour tests."""
    return {
        "api_error": APIConnectionError(
            "Failed to connect to OpenBB API",
            error_code="API_001"
        ),
        "validation_error": DataValidationError(
            "Invalid stock symbol format",
            error_code="VAL_001"
        ),
        "config_error": ConfigurationError(
            "Missing API key configuration",
            error_code="CFG_001"
        )
    }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_mock_response(status_code: int = 200, json_data: Dict[str, Any] = None):
    """Crée une réponse HTTP mock."""
    response = Mock()
    response.status_code = status_code
    response.json.return_value = json_data or {}
    return response


def assert_valid_uuid(uuid_string: str):
    """Vérifie qu'une chaîne est un UUID valide."""
    from uuid import UUID
    try:
        UUID(uuid_string)
        return True
    except ValueError:
        return False


# ============================================================================
# FIXTURES SPÉCIALISÉES PAR MODULE
# ============================================================================

# Ces fixtures seront importées par les modules spécifiques selon leurs besoins
# Voir tests/utils/test_fixtures.py pour plus de détails