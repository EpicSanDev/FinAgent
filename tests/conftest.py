"""
Configuration commune pour les tests FinAgent.

Ce fichier contient les fixtures et configurations partagées
pour tous les tests du projet.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from typing import Dict, Any, List
import tempfile
import os

from finagent.ai.models.base import ModelType, ProviderType
from finagent.ai.config import AIConfig, OllamaConfig, ClaudeConfig, FallbackStrategy
from finagent.ai.providers.ollama_provider import OllamaProvider, OllamaModelInfo
from finagent.ai.services.model_discovery_service import ModelDiscoveryService


@pytest.fixture(scope="session")
def event_loop():
    """Event loop pour les tests asyncio."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_config_dir():
    """Répertoire temporaire pour les configurations de test."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def sample_ollama_config():
    """Configuration Ollama de test."""
    return OllamaConfig(
        host="localhost",
        port=11434,
        timeout=30,
        auto_pull=True,
        max_retries=3,
        retry_delay=1.0
    )


@pytest.fixture
def sample_claude_config():
    """Configuration Claude de test."""
    return ClaudeConfig(
        api_key="test-api-key",
        base_url="https://api.anthropic.com",
        timeout=60,
        max_retries=3,
        retry_delay=2.0
    )


@pytest.fixture
def sample_ai_config(sample_ollama_config, sample_claude_config):
    """Configuration AI complète de test."""
    return AIConfig(
        ollama=sample_ollama_config,
        claude=sample_claude_config,
        preferred_provider=ProviderType.OLLAMA,
        fallback_strategy=FallbackStrategy.AUTO,
        enable_auto_discovery=True,
        discovery_refresh_interval=300
    )


@pytest.fixture
def mock_ollama_models_response():
    """Réponse mockée pour la liste des modèles Ollama."""
    return {
        "models": [
            {
                "name": "llama3.1:8b",
                "size": 4600000000,
                "digest": "sha256:abc123",
                "details": {
                    "format": "gguf",
                    "family": "llama",
                    "families": ["llama"],
                    "parameter_size": "8B",
                    "quantization_level": "Q4_0"
                },
                "modified_at": "2024-01-01T00:00:00Z"
            },
            {
                "name": "mistral:7b",
                "size": 3800000000,
                "digest": "sha256:def456",
                "details": {
                    "format": "gguf",
                    "family": "mistral",
                    "families": ["mistral"],
                    "parameter_size": "7B",
                    "quantization_level": "Q4_0"
                },
                "modified_at": "2024-01-01T00:00:00Z"
            },
            {
                "name": "codellama:7b",
                "size": 3900000000,
                "digest": "sha256:ghi789",
                "details": {
                    "format": "gguf",
                    "family": "llama",
                    "families": ["llama"],
                    "parameter_size": "7B",
                    "quantization_level": "Q4_0"
                },
                "modified_at": "2024-01-01T00:00:00Z"
            }
        ]
    }


@pytest.fixture
def mock_ollama_generate_response():
    """Réponse mockée pour la génération Ollama."""
    return {
        "model": "llama3.1:8b",
        "created_at": "2024-01-01T00:00:00Z",
        "response": "Ceci est une réponse de test générée par le modèle Ollama. L'analyse financière demandée nécessite une approche méthodique.",
        "done": True,
        "context": [123, 456, 789],
        "total_duration": 1500000000,
        "load_duration": 300000000,
        "prompt_eval_count": 25,
        "prompt_eval_duration": 200000000,
        "eval_count": 35,
        "eval_duration": 800000000
    }


@pytest.fixture
def mock_claude_response():
    """Réponse mockée pour Claude."""
    return {
        "id": "msg_test123",
        "type": "message",
        "role": "assistant",
        "content": [
            {
                "type": "text",
                "text": "Ceci est une réponse de test de Claude. L'analyse financière sera détaillée et précise."
            }
        ],
        "model": "claude-3-sonnet-20240229",
        "stop_reason": "end_turn",
        "stop_sequence": None,
        "usage": {
            "input_tokens": 25,
            "output_tokens": 35
        }
    }


@pytest.fixture
def sample_model_infos():
    """Liste d'informations de modèles pour les tests."""
    return [
        OllamaModelInfo(
            name="llama3.1:8b",
            size_bytes=4600000000,
            digest="sha256:abc123",
            details={
                "format": "gguf",
                "family": "llama",
                "parameter_size": "8B",
                "quantization_level": "Q4_0"
            }
        ),
        OllamaModelInfo(
            name="mistral:7b",
            size_bytes=3800000000,
            digest="sha256:def456",
            details={
                "format": "gguf",
                "family": "mistral",
                "parameter_size": "7B",
                "quantization_level": "Q4_0"
            }
        )
    ]


@pytest.fixture
def mock_ollama_provider(sample_ollama_config, sample_model_infos):
    """Provider Ollama mocké pour les tests."""
    provider = AsyncMock(spec=OllamaProvider)
    provider.config = sample_ollama_config
    provider.base_url = f"http://{sample_ollama_config.host}:{sample_ollama_config.port}"
    
    # Configuration des méthodes mockées
    provider.validate_connection.return_value = True
    provider.get_available_models_info.return_value = sample_model_infos
    provider.pull_model.return_value = True
    provider.generate_response.return_value = "Réponse de test Ollama"
    
    return provider


@pytest.fixture
def mock_model_discovery_service(mock_ollama_provider):
    """Service de discovery mocké."""
    service = AsyncMock(spec=ModelDiscoveryService)
    service.provider = mock_ollama_provider
    
    # Modèles disponibles mockés
    service.get_available_models.return_value = [
        ModelType.LLAMA3_1_8B,
        ModelType.MISTRAL_7B,
        ModelType.CODELLAMA_7B
    ]
    
    # Recommandations mockées
    service.get_recommended_models_for_task.return_value = [
        ModelType.LLAMA3_1_8B,
        ModelType.MISTRAL_7B
    ]
    
    service.pull_model.return_value = True
    service.refresh_models.return_value = {}
    
    return service


@pytest.fixture
def mock_http_session():
    """Session HTTP mockée pour les tests."""
    session = AsyncMock()
    
    # Configuration des réponses par défaut
    response = AsyncMock()
    response.status = 200
    response.json.return_value = {"status": "ok"}
    response.text.return_value = "OK"
    
    session.get.return_value.__aenter__.return_value = response
    session.post.return_value.__aenter__.return_value = response
    session.put.return_value.__aenter__.return_value = response
    session.delete.return_value.__aenter__.return_value = response
    
    return session


@pytest.fixture
def sample_financial_data():
    """Données financières de test."""
    return {
        "symbol": "AAPL",
        "price": 150.25,
        "change": 2.50,
        "change_percent": 1.69,
        "volume": 50000000,
        "market_cap": 2500000000000,
        "pe_ratio": 25.5,
        "dividend_yield": 0.6,
        "analysis": {
            "trend": "bullish",
            "support": 145.00,
            "resistance": 155.00,
            "recommendation": "buy"
        }
    }


@pytest.fixture
def sample_prompts():
    """Prompts de test pour différentes tâches."""
    return {
        "analysis": """
        Analyse l'action Apple (AAPL) en considérant :
        1. Performance récente
        2. Tendances du marché
        3. Position concurrentielle
        4. Recommandation d'investissement
        """,
        "portfolio": """
        Optimise ce portefeuille de 50,000€ :
        - Actions tech: 40%
        - Obligations: 30%
        - Cash: 30%
        Profil: investisseur modéré, horizon 10 ans.
        """,
        "coding": """
        Écris une fonction Python qui calcule :
        1. Moyenne mobile simple (SMA)
        2. RSI (Relative Strength Index)
        3. Bandes de Bollinger
        """,
        "summary": """
        Résume les points clés de l'actualité financière
        de cette semaine en 5 points maximum.
        """
    }


# Marks personnalisés pour les tests
def pytest_configure(config):
    """Configuration des marks personnalisés."""
    config.addinivalue_line(
        "markers", "unit: Tests unitaires rapides"
    )
    config.addinivalue_line(
        "markers", "integration: Tests d'intégration"
    )
    config.addinivalue_line(
        "markers", "ollama: Tests spécifiques à Ollama"
    )
    config.addinivalue_line(
        "markers", "claude: Tests spécifiques à Claude"
    )
    config.addinivalue_line(
        "markers", "slow: Tests lents nécessitant plus de temps"
    )
    config.addinivalue_line(
        "markers", "network: Tests nécessitant une connexion réseau"
    )


# Helpers pour les tests
class TestHelpers:
    """Méthodes utilitaires pour les tests."""
    
    @staticmethod
    def create_mock_response(status: int = 200, json_data: Dict[str, Any] = None, text: str = None):
        """Crée une réponse HTTP mockée."""
        response = AsyncMock()
        response.status = status
        
        if json_data:
            response.json.return_value = json_data
        if text:
            response.text.return_value = text
            
        return response
    
    @staticmethod
    def assert_model_info_valid(model_info: OllamaModelInfo):
        """Valide qu'une info de modèle est correcte."""
        assert model_info.name
        assert model_info.size_bytes > 0
        assert model_info.digest
        assert isinstance(model_info.details, dict)
    
    @staticmethod
    def assert_ai_response_valid(response: str):
        """Valide qu'une réponse AI est correcte."""
        assert isinstance(response, str)
        assert len(response) > 0
        assert response.strip() != ""


@pytest.fixture
def test_helpers():
    """Fixture pour accéder aux helpers de test."""
    return TestHelpers


# Configuration des timeouts pour les tests asyncio
@pytest.fixture(autouse=True)
def setup_test_timeout():
    """Configure un timeout par défaut pour les tests asyncio."""
    import pytest_asyncio
    pytest_asyncio.timeout = 30  # 30 secondes par test


# Variables d'environnement pour les tests
@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """Configure l'environnement pour les tests."""
    # Variables d'environnement de test
    test_env = {
        "OLLAMA_HOST": "localhost",
        "OLLAMA_PORT": "11434",
        "OLLAMA_DEFAULT_MODEL": "llama3.1:8b",
        "OLLAMA_AUTO_PULL": "true",
        "AI_PREFERRED_PROVIDER": "ollama",
        "AI_FALLBACK_STRATEGY": "auto",
        "AI_ENABLE_AUTO_DISCOVERY": "true",
        "LOG_LEVEL": "DEBUG",
        "TESTING": "true"
    }
    
    for key, value in test_env.items():
        monkeypatch.setenv(key, value)


# Nettoyage après les tests
@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Nettoyage automatique après chaque test."""
    yield
    
    # Nettoyage des ressources si nécessaire
    # (connexions, fichiers temporaires, etc.)
    pass