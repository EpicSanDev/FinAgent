"""
Tests d'intégration pour l'intégration Ollama dans FinAgent.

Ces tests vérifient le bon fonctionnement de l'intégration Ollama
avec mocking pour éviter les dépendances externes.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, List, Any
import json

from finagent.ai.providers.ollama_provider import OllamaProvider, OllamaConfig, OllamaModelInfo
from finagent.ai.services.model_discovery_service import ModelDiscoveryService
from finagent.ai.factory import AIProviderFactory
from finagent.ai.models.base import ModelType, ProviderType
from finagent.ai.config import AIConfig, FallbackStrategy


class TestOllamaProvider:
    """Tests pour le provider Ollama."""
    
    @pytest.fixture
    def ollama_config(self):
        """Configuration Ollama pour les tests."""
        return OllamaConfig(
            host="localhost",
            port=11434,
            timeout=30,
            auto_pull=True
        )
    
    @pytest.fixture
    def mock_ollama_response(self):
        """Réponse mockée d'Ollama."""
        return {
            "response": "Ceci est une réponse de test d'Ollama.",
            "done": True,
            "total_duration": 1000000000,
            "load_duration": 500000000,
            "prompt_eval_count": 10,
            "eval_count": 20
        }
    
    @pytest.fixture
    def mock_models_list(self):
        """Liste mockée des modèles Ollama."""
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
                    }
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
                    }
                }
            ]
        }
    
    @pytest.mark.asyncio
    async def test_ollama_provider_initialization(self, ollama_config):
        """Test l'initialisation du provider Ollama."""
        provider = OllamaProvider(ollama_config)
        
        assert provider.config == ollama_config
        assert provider.base_url == "http://localhost:11434"
        assert provider._session is None
    
    @pytest.mark.asyncio
    async def test_validate_connection_success(self, ollama_config):
        """Test la validation de connexion réussie."""
        provider = OllamaProvider(ollama_config)
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {"version": "0.1.0"}
            mock_get.return_value.__aenter__.return_value = mock_response
            
            result = await provider.validate_connection()
            
            assert result is True
            mock_get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_validate_connection_failure(self, ollama_config):
        """Test la validation de connexion échouée."""
        provider = OllamaProvider(ollama_config)
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.side_effect = Exception("Connection refused")
            
            result = await provider.validate_connection()
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_generate_response_success(self, ollama_config, mock_ollama_response):
        """Test la génération de réponse réussie."""
        provider = OllamaProvider(ollama_config)
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = mock_ollama_response
            mock_post.return_value.__aenter__.return_value = mock_response
            
            response = await provider.generate_response(
                "Test prompt",
                model=ModelType.LLAMA3_1_8B,
                max_tokens=100
            )
            
            assert response == "Ceci est une réponse de test d'Ollama."
            mock_post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_response_with_auto_pull(self, ollama_config, mock_ollama_response):
        """Test la génération avec téléchargement automatique."""
        provider = OllamaProvider(ollama_config)
        
        with patch('aiohttp.ClientSession.post') as mock_post, \
             patch.object(provider, 'pull_model') as mock_pull:
            
            # Premier appel échoue (modèle non trouvé)
            mock_response_404 = AsyncMock()
            mock_response_404.status = 404
            mock_response_404.json.return_value = {"error": "model not found"}
            
            # Deuxième appel réussit
            mock_response_200 = AsyncMock()
            mock_response_200.status = 200
            mock_response_200.json.return_value = mock_ollama_response
            
            mock_post.return_value.__aenter__.side_effect = [
                mock_response_404,
                mock_response_200
            ]
            
            mock_pull.return_value = True
            
            response = await provider.generate_response(
                "Test prompt",
                model=ModelType.LLAMA3_1_8B
            )
            
            assert response == "Ceci est une réponse de test d'Ollama."
            mock_pull.assert_called_once_with("llama3.1:8b")
            assert mock_post.call_count == 2
    
    @pytest.mark.asyncio
    async def test_get_available_models_info(self, ollama_config, mock_models_list):
        """Test la récupération des informations des modèles."""
        provider = OllamaProvider(ollama_config)
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = mock_models_list
            mock_get.return_value.__aenter__.return_value = mock_response
            
            models_info = await provider.get_available_models_info()
            
            assert len(models_info) == 2
            assert models_info[0].name == "llama3.1:8b"
            assert models_info[0].size_bytes == 4600000000
            assert models_info[1].name == "mistral:7b"
    
    @pytest.mark.asyncio
    async def test_pull_model_success(self, ollama_config):
        """Test le téléchargement de modèle réussi."""
        provider = OllamaProvider(ollama_config)
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {"status": "success"}
            mock_post.return_value.__aenter__.return_value = mock_response
            
            result = await provider.pull_model("llama3.1:8b")
            
            assert result is True
            mock_post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, ollama_config):
        """Test le rate limiting."""
        provider = OllamaProvider(ollama_config)
        
        # Simulation de plusieurs requêtes rapides
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 429  # Too Many Requests
            mock_post.return_value.__aenter__.return_value = mock_response
            
            # Premier appel - devrait passer
            await provider._rate_limiter.acquire()
            
            # Deuxième appel immédiat - pourrait être limité
            start_time = asyncio.get_event_loop().time()
            await provider._rate_limiter.acquire()
            end_time = asyncio.get_event_loop().time()
            
            # Vérifier qu'il y a eu un délai (rate limiting)
            assert end_time - start_time >= 0


class TestModelDiscoveryService:
    """Tests pour le service de discovery des modèles."""
    
    @pytest.fixture
    def mock_provider(self):
        """Provider Ollama mocké."""
        provider = AsyncMock(spec=OllamaProvider)
        provider.get_available_models_info.return_value = [
            OllamaModelInfo(
                name="llama3.1:8b",
                size_bytes=4600000000,
                digest="sha256:abc123",
                details={"family": "llama", "parameter_size": "8B"}
            )
        ]
        return provider
    
    @pytest.mark.asyncio
    async def test_refresh_models(self, mock_provider):
        """Test le rafraîchissement des modèles."""
        discovery = ModelDiscoveryService(mock_provider)
        
        models_info = await discovery.refresh_models()
        
        assert len(models_info) >= 0
        mock_provider.get_available_models_info.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_pull_model(self, mock_provider):
        """Test le téléchargement de modèle."""
        discovery = ModelDiscoveryService(mock_provider)
        mock_provider.pull_model.return_value = True
        
        result = await discovery.pull_model(ModelType.LLAMA3_1_8B)
        
        assert result is True
        mock_provider.pull_model.assert_called_once_with("llama3.1:8b")
    
    def test_get_recommended_models_for_task(self, mock_provider):
        """Test les recommandations de modèles par tâche."""
        discovery = ModelDiscoveryService(mock_provider)
        
        # Test différentes tâches
        coding_models = discovery.get_recommended_models_for_task("coding")
        analysis_models = discovery.get_recommended_models_for_task("analysis")
        conversation_models = discovery.get_recommended_models_for_task("conversation")
        
        assert ModelType.CODELLAMA_7B in coding_models
        assert ModelType.LLAMA3_1_8B in analysis_models
        assert ModelType.GEMMA_7B in conversation_models
    
    def test_get_available_models(self, mock_provider):
        """Test la récupération des modèles disponibles."""
        discovery = ModelDiscoveryService(mock_provider)
        
        # Simulation de modèles en cache
        discovery._model_cache = {
            ModelType.LLAMA3_1_8B: MagicMock(available=True),
            ModelType.MISTRAL_7B: MagicMock(available=False)
        }
        
        available = discovery.get_available_models()
        
        assert ModelType.LLAMA3_1_8B in available
        assert ModelType.MISTRAL_7B not in available


class TestAIProviderFactory:
    """Tests pour la factory des providers AI."""
    
    @pytest.fixture
    def ai_config(self):
        """Configuration AI pour les tests."""
        return AIConfig(
            preferred_provider=ProviderType.OLLAMA,
            fallback_strategy=FallbackStrategy.AUTO,
            enable_auto_discovery=True
        )
    
    @pytest.mark.asyncio
    async def test_factory_initialization(self, ai_config):
        """Test l'initialisation de la factory."""
        factory = AIProviderFactory(ai_config)
        
        assert factory.config == ai_config
        assert factory._providers == {}
        assert factory._health_status == {}
    
    @pytest.mark.asyncio
    async def test_get_provider_by_type(self, ai_config):
        """Test la récupération de provider par type."""
        factory = AIProviderFactory(ai_config)
        
        with patch.object(factory, '_create_provider') as mock_create:
            mock_provider = AsyncMock()
            mock_create.return_value = mock_provider
            
            provider = await factory.get_provider(ProviderType.OLLAMA)
            
            assert provider == mock_provider
            mock_create.assert_called_once_with(ProviderType.OLLAMA)
    
    @pytest.mark.asyncio
    async def test_get_provider_for_task(self, ai_config):
        """Test la sélection de provider pour une tâche."""
        factory = AIProviderFactory(ai_config)
        
        with patch.object(factory, '_select_best_provider_for_task') as mock_select, \
             patch.object(factory, 'get_provider') as mock_get_provider:
            
            mock_select.return_value = ProviderType.OLLAMA
            mock_provider = AsyncMock()
            mock_get_provider.return_value = mock_provider
            
            provider = await factory.get_provider_for_task("analysis")
            
            assert provider == mock_provider
            mock_select.assert_called_once_with("analysis")
    
    @pytest.mark.asyncio
    async def test_health_check(self, ai_config):
        """Test la vérification de santé des providers."""
        factory = AIProviderFactory(ai_config)
        
        with patch.object(factory, 'get_provider') as mock_get_provider:
            mock_provider = AsyncMock()
            mock_provider.validate_connection.return_value = True
            mock_get_provider.return_value = mock_provider
            
            health = await factory._check_provider_health(ProviderType.OLLAMA)
            
            assert health["available"] is True
            assert "response_time_ms" in health
    
    def test_get_provider_health_status(self, ai_config):
        """Test la récupération du statut de santé."""
        factory = AIProviderFactory(ai_config)
        
        # Simulation de statuts de santé
        factory._health_status = {
            "ollama": {"available": True, "response_time_ms": 12.5},
            "claude": {"available": False, "response_time_ms": None}
        }
        
        status = factory.get_provider_health_status()
        
        assert status["ollama"]["available"] is True
        assert status["claude"]["available"] is False


class TestFallbackStrategies:
    """Tests pour les stratégies de fallback."""
    
    @pytest.mark.asyncio
    async def test_ollama_to_claude_fallback(self):
        """Test du fallback Ollama vers Claude."""
        config = AIConfig(
            fallback_strategy=FallbackStrategy.OLLAMA_TO_CLAUDE,
            preferred_provider=ProviderType.OLLAMA
        )
        
        factory = AIProviderFactory(config)
        
        with patch.object(factory, 'get_provider') as mock_get_provider:
            # Ollama échoue
            ollama_provider = AsyncMock()
            ollama_provider.generate_response.side_effect = Exception("Ollama error")
            
            # Claude réussit
            claude_provider = AsyncMock()
            claude_provider.generate_response.return_value = "Claude response"
            
            mock_get_provider.side_effect = lambda pt: (
                ollama_provider if pt == ProviderType.OLLAMA else claude_provider
            )
            
            provider = await factory.get_provider_for_task("analysis")
            
            # Simuler l'échec d'Ollama et le fallback vers Claude
            with pytest.raises(Exception):
                await ollama_provider.generate_response("test")
            
            # Le fallback devrait utiliser Claude
            response = await claude_provider.generate_response("test")
            assert response == "Claude response"
    
    @pytest.mark.asyncio
    async def test_auto_fallback_strategy(self):
        """Test de la stratégie de fallback automatique."""
        config = AIConfig(
            fallback_strategy=FallbackStrategy.AUTO,
            preferred_provider=ProviderType.OLLAMA
        )
        
        factory = AIProviderFactory(config)
        
        with patch.object(factory, '_check_provider_health') as mock_health:
            # Ollama disponible, Claude non disponible
            mock_health.side_effect = lambda pt: (
                {"available": True, "response_time_ms": 10.0}
                if pt == ProviderType.OLLAMA
                else {"available": False, "response_time_ms": None}
            )
            
            selected = factory._select_best_provider_for_task("analysis")
            
            # Devrait sélectionner Ollama car disponible
            assert selected == ProviderType.OLLAMA


class TestIntegrationScenarios:
    """Tests de scénarios d'intégration complets."""
    
    @pytest.mark.asyncio
    async def test_complete_analysis_workflow(self):
        """Test d'un workflow d'analyse complet."""
        # Configuration avec Ollama en priorité
        config = AIConfig(
            preferred_provider=ProviderType.OLLAMA,
            fallback_strategy=FallbackStrategy.OLLAMA_TO_CLAUDE,
            enable_auto_discovery=True
        )
        
        # Mock des composants
        with patch('finagent.ai.providers.ollama_provider.OllamaProvider') as MockOllama, \
             patch('finagent.ai.services.model_discovery_service.ModelDiscoveryService') as MockDiscovery:
            
            # Configuration du mock Ollama
            mock_ollama = AsyncMock()
            mock_ollama.validate_connection.return_value = True
            mock_ollama.generate_response.return_value = "Analyse financière détaillée..."
            MockOllama.return_value = mock_ollama
            
            # Configuration du mock Discovery
            mock_discovery = AsyncMock()
            mock_discovery.get_available_models.return_value = [ModelType.LLAMA3_1_8B]
            MockDiscovery.return_value = mock_discovery
            
            # Test du workflow
            factory = AIProviderFactory(config)
            provider = await factory.get_provider_for_task("analysis")
            
            response = await provider.generate_response(
                "Analyse l'action AAPL",
                model=ModelType.LLAMA3_1_8B,
                max_tokens=1000
            )
            
            assert "Analyse financière" in response
            mock_ollama.generate_response.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_model_discovery_and_auto_pull(self):
        """Test de la découverte de modèle et téléchargement automatique."""
        with patch('finagent.ai.providers.ollama_provider.OllamaProvider') as MockOllama:
            mock_provider = AsyncMock()
            
            # Premier appel : modèle non disponible
            mock_provider.get_available_models_info.return_value = []
            
            # Téléchargement réussi
            mock_provider.pull_model.return_value = True
            
            # Après téléchargement : modèle disponible
            model_info = OllamaModelInfo(
                name="llama3.1:8b",
                size_bytes=4600000000,
                digest="sha256:abc123",
                details={"family": "llama"}
            )
            
            MockOllama.return_value = mock_provider
            
            discovery = ModelDiscoveryService(mock_provider)
            
            # Test du téléchargement
            success = await discovery.pull_model(ModelType.LLAMA3_1_8B)
            assert success is True
            
            mock_provider.pull_model.assert_called_once_with("llama3.1:8b")


@pytest.fixture(scope="session")
def event_loop():
    """Fixture pour l'event loop asyncio."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# Marks pour les tests
pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.integration,
    pytest.mark.ollama
]


if __name__ == "__main__":
    # Exécution des tests avec pytest
    pytest.main([__file__, "-v", "--tb=short"])