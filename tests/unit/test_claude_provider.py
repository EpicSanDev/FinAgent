"""
Tests unitaires pour le provider Claude de FinAgent.

Ce module teste toutes les fonctionnalités du provider Claude,
incluant la génération de réponses IA, la gestion de tokens,
le rate limiting et l'intégration avec l'API OpenRouter.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, patch, AsyncMock
import json

from finagent.ai.providers.claude_provider import (
    ClaudeProvider, ClaudeConfig, AIModel, MessageRole,
    TokenUsage, RateLimitInfo, AIRequest, AIResponse
)
from finagent.core.exceptions import (
    AIProviderError, APIRateLimitError, TokenLimitExceededError,
    InvalidPromptError, ModelNotAvailableError
)
from tests.utils import (
    AIRequestFactory, MockClaudeProvider, assert_valid_uuid,
    create_test_ai_conversation, create_test_financial_context
)


class TestClaudeConfig:
    """Tests pour la configuration Claude."""
    
    @pytest.fixture
    def sample_config_data(self):
        """Configuration échantillon pour Claude."""
        return {
            "api_key": "sk-test-claude-key-123",
            "base_url": "https://openrouter.ai/api/v1",
            "model": "anthropic/claude-3-sonnet-20240229",
            "max_tokens": 4000,
            "temperature": 0.7,
            "timeout": 60,
            "max_retries": 3,
            "rate_limit_per_minute": 50,
            "rate_limit_per_hour": 1000,
            "enable_streaming": True,
            "enable_caching": True,
            "cache_ttl": 600,
            "system_prompt": "You are FinAgent, an AI financial advisor."
        }
    
    def test_claude_config_creation(self, sample_config_data):
        """Test création de la configuration Claude."""
        config = sample_config_data
        
        assert config["api_key"].startswith("sk-")
        assert config["base_url"] == "https://openrouter.ai/api/v1"
        assert config["model"] == "anthropic/claude-3-sonnet-20240229"
        assert config["max_tokens"] == 4000
        assert config["temperature"] == 0.7
        assert config["enable_streaming"] is True
    
    def test_config_validation(self, sample_config_data):
        """Test validation de la configuration."""
        config = sample_config_data
        
        # API key non vide
        assert len(config["api_key"]) > 0
        
        # URL valide
        assert config["base_url"].startswith("https://")
        
        # Max tokens raisonnable
        assert 1 <= config["max_tokens"] <= 32768
        
        # Temperature valide
        assert 0 <= config["temperature"] <= 1
        
        # Timeout positif
        assert config["timeout"] > 0
        
        # Rate limits raisonnables
        assert 1 <= config["rate_limit_per_minute"] <= 1000
        assert 1 <= config["rate_limit_per_hour"] <= 10000


class TestClaudeProviderInitialization:
    """Tests pour l'initialisation du provider Claude."""
    
    @pytest.fixture
    def mock_claude_config(self):
        """Configuration mock pour Claude."""
        return {
            "api_key": "sk-test-key",
            "base_url": "https://openrouter.ai/api/v1",
            "model": "anthropic/claude-3-sonnet-20240229",
            "max_tokens": 4000,
            "temperature": 0.7,
            "timeout": 60
        }
    
    def test_provider_initialization(self, mock_claude_config):
        """Test initialisation du provider."""
        provider = MockClaudeProvider(mock_claude_config)
        
        assert provider.config["api_key"] == "sk-test-key"
        assert provider.config["model"] == "anthropic/claude-3-sonnet-20240229"
        assert provider.config["max_tokens"] == 4000
        assert provider.is_initialized is True
    
    def test_provider_initialization_invalid_config(self):
        """Test initialisation avec configuration invalide."""
        invalid_configs = [
            {"api_key": ""},  # API key vide
            {"api_key": "sk-test", "max_tokens": -1},  # Max tokens négatif
            {"api_key": "sk-test", "temperature": 1.5},  # Temperature > 1
            {"api_key": "sk-test", "timeout": 0}  # Timeout zéro
        ]
        
        for config in invalid_configs:
            with pytest.raises(ValueError):
                MockClaudeProvider(config)
    
    @pytest.mark.asyncio
    async def test_provider_health_check(self, mock_claude_config):
        """Test vérification de santé du provider."""
        provider = MockClaudeProvider(mock_claude_config)
        
        health_status = await provider.health_check()
        
        assert health_status["status"] == "healthy"
        assert "model_available" in health_status
        assert "rate_limit_remaining" in health_status
        assert "last_request_time" in health_status


class TestAIRequestResponse:
    """Tests pour les requêtes et réponses IA."""
    
    @pytest.fixture
    def mock_provider(self):
        """Provider mock configuré."""
        config = {
            "api_key": "sk-test-key",
            "model": "anthropic/claude-3-sonnet-20240229",
            "max_tokens": 4000,
            "temperature": 0.7
        }
        return MockClaudeProvider(config)
    
    @pytest.fixture
    def sample_ai_request_data(self):
        """Requête IA échantillon."""
        return {
            "id": "req_123456",
            "prompt": "Analyze the financial performance of Apple Inc. (AAPL)",
            "context": {
                "symbol": "AAPL",
                "current_price": 150.25,
                "pe_ratio": 28.5,
                "market_cap": 2500000000000
            },
            "max_tokens": 2000,
            "temperature": 0.7,
            "system_prompt": "You are a financial analyst.",
            "conversation_history": []
        }
    
    @pytest.mark.asyncio
    async def test_simple_completion(self, mock_provider, sample_ai_request_data):
        """Test complétion simple."""
        request_data = sample_ai_request_data
        
        response = await mock_provider.generate_completion(
            prompt=request_data["prompt"],
            context=request_data["context"],
            max_tokens=request_data["max_tokens"],
            temperature=request_data["temperature"]
        )
        
        assert response["id"] is not None
        assert "content" in response
        assert "token_usage" in response
        assert "model" in response
        assert len(response["content"]) > 0
        assert response["model"] == mock_provider.config["model"]
    
    @pytest.mark.asyncio
    async def test_conversation_completion(self, mock_provider):
        """Test complétion avec historique de conversation."""
        conversation_history = [
            {"role": "user", "content": "What is the current market trend?"},
            {"role": "assistant", "content": "The market is showing bullish trends..."},
            {"role": "user", "content": "Should I invest in tech stocks?"}
        ]
        
        response = await mock_provider.generate_completion(
            prompt="Analyze tech sector opportunities",
            conversation_history=conversation_history,
            max_tokens=1500
        )
        
        assert response["id"] is not None
        assert "content" in response
        assert len(response["content"]) > 0
        # La réponse devrait tenir compte du contexte de la conversation
    
    @pytest.mark.asyncio
    async def test_financial_analysis_request(self, mock_provider):
        """Test requête d'analyse financière."""
        financial_context = {
            "company": "Apple Inc.",
            "symbol": "AAPL",
            "financial_data": {
                "revenue": 394328000000,
                "net_income": 99803000000,
                "total_assets": 352755000000,
                "current_ratio": 1.07,
                "debt_to_equity": 0.31
            },
            "market_data": {
                "current_price": 150.25,
                "pe_ratio": 28.5,
                "market_cap": 2500000000000,
                "52_week_high": 182.13,
                "52_week_low": 124.17
            }
        }
        
        prompt = """
        Analyze the financial health and investment potential of this company.
        Consider both fundamental and market factors.
        Provide a recommendation with risk assessment.
        """
        
        response = await mock_provider.generate_completion(
            prompt=prompt,
            context=financial_context,
            max_tokens=3000,
            temperature=0.3  # Plus conservateur pour analyse
        )
        
        assert response["id"] is not None
        assert "content" in response
        # Vérifier que la réponse contient des éléments d'analyse
        content = response["content"].lower()
        assert any(keyword in content for keyword in [
            "financial", "revenue", "profit", "ratio", "recommendation"
        ])
    
    @pytest.mark.asyncio
    async def test_investment_strategy_request(self, mock_provider):
        """Test requête de stratégie d'investissement."""
        strategy_context = {
            "investor_profile": {
                "risk_tolerance": "medium",
                "time_horizon": "long_term",
                "investment_goals": ["growth", "income"],
                "portfolio_size": 100000
            },
            "market_conditions": {
                "market_trend": "bullish",
                "volatility": "medium",
                "interest_rates": "rising"
            }
        }
        
        prompt = """
        Create a personalized investment strategy based on the investor profile
        and current market conditions. Include asset allocation recommendations.
        """
        
        response = await mock_provider.generate_completion(
            prompt=prompt,
            context=strategy_context,
            max_tokens=2500
        )
        
        assert response["id"] is not None
        assert "content" in response
        content = response["content"].lower()
        assert any(keyword in content for keyword in [
            "allocation", "portfolio", "diversification", "strategy"
        ])


class TestTokenManagement:
    """Tests pour la gestion des tokens."""
    
    @pytest.fixture
    def mock_provider(self):
        """Provider mock configuré."""
        config = {
            "api_key": "sk-test-key",
            "model": "anthropic/claude-3-sonnet-20240229",
            "max_tokens": 4000
        }
        return MockClaudeProvider(config)
    
    @pytest.mark.asyncio
    async def test_token_counting(self, mock_provider):
        """Test comptage de tokens."""
        prompt = "Analyze the financial performance of Microsoft Corporation."
        
        token_count = await mock_provider.count_tokens(prompt)
        
        assert token_count > 0
        assert isinstance(token_count, int)
        # Approximation: ~4 caractères par token en moyenne
        expected_range = (len(prompt) // 6, len(prompt) // 2)
        assert expected_range[0] <= token_count <= expected_range[1]
    
    @pytest.mark.asyncio
    async def test_token_usage_tracking(self, mock_provider):
        """Test suivi d'utilisation des tokens."""
        prompt = "What are the key financial ratios for investment analysis?"
        
        response = await mock_provider.generate_completion(prompt, max_tokens=500)
        
        token_usage = response["token_usage"]
        assert "prompt_tokens" in token_usage
        assert "completion_tokens" in token_usage
        assert "total_tokens" in token_usage
        
        assert token_usage["prompt_tokens"] > 0
        assert token_usage["completion_tokens"] > 0
        assert token_usage["total_tokens"] == (
            token_usage["prompt_tokens"] + token_usage["completion_tokens"]
        )
    
    @pytest.mark.asyncio
    async def test_token_limit_validation(self, mock_provider):
        """Test validation des limites de tokens."""
        # Prompt très long qui dépasse la limite
        long_prompt = "Analyze this company: " + "financial data " * 2000
        
        with pytest.raises(TokenLimitExceededError):
            await mock_provider.generate_completion(
                prompt=long_prompt,
                max_tokens=4000
            )
    
    @pytest.mark.asyncio
    async def test_context_window_management(self, mock_provider):
        """Test gestion de la fenêtre de contexte."""
        # Conversation très longue
        long_conversation = []
        for i in range(50):
            long_conversation.extend([
                {"role": "user", "content": f"Question {i}: " + "text " * 100},
                {"role": "assistant", "content": f"Answer {i}: " + "response " * 100}
            ])
        
        # Le provider devrait tronquer ou gérer la conversation
        response = await mock_provider.generate_completion(
            prompt="Summarize our discussion",
            conversation_history=long_conversation,
            max_tokens=1000
        )
        
        assert response["id"] is not None
        assert "content" in response


class TestRateLimiting:
    """Tests pour la limitation de taux."""
    
    @pytest.fixture
    def mock_provider_with_rate_limit(self):
        """Provider mock avec limitation de taux."""
        config = {
            "api_key": "sk-test-key",
            "model": "anthropic/claude-3-sonnet-20240229",
            "rate_limit_per_minute": 5,  # Limite basse pour test
            "rate_limit_per_hour": 100
        }
        return MockClaudeProvider(config)
    
    @pytest.mark.asyncio
    async def test_rate_limit_enforcement(self, mock_provider_with_rate_limit):
        """Test application de la limitation de taux."""
        prompts = [f"Analyze stock {i}" for i in range(10)]
        
        successful_requests = 0
        rate_limited_requests = 0
        
        for prompt in prompts:
            try:
                await mock_provider_with_rate_limit.generate_completion(prompt)
                successful_requests += 1
            except APIRateLimitError:
                rate_limited_requests += 1
        
        # Vérification que la limite est appliquée
        assert successful_requests <= 5  # Limite configurée
        assert rate_limited_requests > 0
    
    @pytest.mark.asyncio
    async def test_rate_limit_info(self, mock_provider_with_rate_limit):
        """Test informations de limitation de taux."""
        rate_limit_info = await mock_provider_with_rate_limit.get_rate_limit_info()
        
        assert "requests_remaining" in rate_limit_info
        assert "reset_time" in rate_limit_info
        assert "limit_per_minute" in rate_limit_info
        assert "limit_per_hour" in rate_limit_info
        
        assert rate_limit_info["requests_remaining"] >= 0
        assert rate_limit_info["limit_per_minute"] == 5
        assert isinstance(rate_limit_info["reset_time"], datetime)
    
    @pytest.mark.asyncio
    async def test_rate_limit_backoff(self, mock_provider_with_rate_limit):
        """Test backoff en cas de rate limiting."""
        # Atteindre la limite
        for i in range(5):
            await mock_provider_with_rate_limit.generate_completion(f"Query {i}")
        
        # La prochaine requête devrait déclencher un backoff
        start_time = datetime.now()
        
        try:
            await mock_provider_with_rate_limit.generate_completion("Final query")
        except APIRateLimitError:
            pass
        
        # Vérifier qu'un délai a été appliqué
        elapsed = datetime.now() - start_time
        assert elapsed.total_seconds() >= 1  # Au moins 1 seconde de backoff


class TestStreamingResponse:
    """Tests pour les réponses en streaming."""
    
    @pytest.fixture
    def mock_provider_with_streaming(self):
        """Provider mock avec streaming activé."""
        config = {
            "api_key": "sk-test-key",
            "model": "anthropic/claude-3-sonnet-20240229",
            "enable_streaming": True
        }
        return MockClaudeProvider(config)
    
    @pytest.mark.asyncio
    async def test_streaming_completion(self, mock_provider_with_streaming):
        """Test complétion en streaming."""
        prompt = "Explain portfolio diversification strategies"
        
        chunks = []
        async for chunk in mock_provider_with_streaming.generate_completion_stream(
            prompt=prompt,
            max_tokens=1000
        ):
            chunks.append(chunk)
        
        assert len(chunks) > 1  # Plusieurs chunks reçus
        
        # Assembler la réponse complète
        full_content = "".join(chunk.get("content", "") for chunk in chunks)
        assert len(full_content) > 0
        
        # Vérifier que le dernier chunk contient les métadonnées finales
        last_chunk = chunks[-1]
        assert last_chunk.get("finished", False) is True
        assert "token_usage" in last_chunk
    
    @pytest.mark.asyncio
    async def test_streaming_with_callback(self, mock_provider_with_streaming):
        """Test streaming avec callback."""
        prompt = "Analyze the risks of cryptocurrency investments"
        received_chunks = []
        
        def chunk_callback(chunk):
            received_chunks.append(chunk)
        
        response = await mock_provider_with_streaming.generate_completion_stream(
            prompt=prompt,
            max_tokens=800,
            chunk_callback=chunk_callback
        )
        
        assert len(received_chunks) > 0
        # Vérifier que tous les chunks ont été traités par le callback
        
    @pytest.mark.asyncio
    async def test_streaming_error_handling(self, mock_provider_with_streaming):
        """Test gestion d'erreurs en streaming."""
        # Simuler erreur pendant le streaming
        mock_provider_with_streaming.simulate_streaming_error = True
        
        with pytest.raises(AIProviderError):
            async for chunk in mock_provider_with_streaming.generate_completion_stream(
                prompt="Test error handling",
                max_tokens=500
            ):
                pass


class TestErrorHandling:
    """Tests pour la gestion d'erreurs."""
    
    @pytest.fixture
    def mock_provider(self):
        """Provider mock configuré."""
        config = {"api_key": "sk-test-key", "model": "anthropic/claude-3-sonnet-20240229"}
        return MockClaudeProvider(config)
    
    @pytest.mark.asyncio
    async def test_invalid_prompt_error(self, mock_provider):
        """Test erreur prompt invalide."""
        invalid_prompts = [
            "",  # Prompt vide
            None,  # Prompt None
            "x" * 100000  # Prompt trop long
        ]
        
        for prompt in invalid_prompts:
            with pytest.raises((InvalidPromptError, ValueError)):
                await mock_provider.generate_completion(prompt)
    
    @pytest.mark.asyncio
    async def test_model_not_available_error(self, mock_provider):
        """Test erreur modèle non disponible."""
        # Changer vers un modèle inexistant
        mock_provider.config["model"] = "non-existent-model"
        
        with pytest.raises(ModelNotAvailableError):
            await mock_provider.generate_completion("Test prompt")
    
    @pytest.mark.asyncio
    async def test_api_timeout_error(self, mock_provider):
        """Test erreur timeout API."""
        # Simuler timeout
        mock_provider.simulate_timeout = True
        
        with pytest.raises(AIProviderError):
            await mock_provider.generate_completion("Test prompt with timeout")
    
    @pytest.mark.asyncio
    async def test_api_authentication_error(self, mock_provider):
        """Test erreur d'authentification."""
        # API key invalide
        mock_provider.config["api_key"] = "invalid-key"
        
        with pytest.raises(AIProviderError):
            await mock_provider.generate_completion("Test authentication")
    
    @pytest.mark.asyncio
    async def test_network_error_retry(self, mock_provider):
        """Test retry en cas d'erreur réseau."""
        # Simuler erreur réseau temporaire
        mock_provider.simulate_network_error = True
        mock_provider.network_error_count = 2  # Échec 2 fois puis succès
        
        response = await mock_provider.generate_completion("Test retry mechanism")
        
        assert response is not None
        assert mock_provider.retry_count > 0


class TestSpecializedRequests:
    """Tests pour les requêtes spécialisées."""
    
    @pytest.fixture
    def mock_provider(self):
        """Provider mock configuré."""
        config = {
            "api_key": "sk-test-key",
            "model": "anthropic/claude-3-sonnet-20240229",
            "temperature": 0.3
        }
        return MockClaudeProvider(config)
    
    @pytest.mark.asyncio
    async def test_financial_document_analysis(self, mock_provider):
        """Test analyse de document financier."""
        document_content = """
        QUARTERLY EARNINGS REPORT
        Revenue: $10.5B (+15% YoY)
        Net Income: $2.1B (+22% YoY)
        EPS: $3.25 (vs $2.85 expected)
        Gross Margin: 42.3%
        Operating Margin: 18.7%
        """
        
        response = await mock_provider.analyze_financial_document(
            document_content=document_content,
            analysis_type="earnings_analysis"
        )
        
        assert response["id"] is not None
        assert "analysis" in response
        assert "key_metrics" in response
        assert "sentiment" in response
        
        # Vérifier que l'analyse contient les éléments clés
        analysis = response["analysis"].lower()
        assert any(keyword in analysis for keyword in [
            "revenue", "growth", "earnings", "margin"
        ])
    
    @pytest.mark.asyncio
    async def test_risk_assessment_request(self, mock_provider):
        """Test évaluation de risque."""
        investment_data = {
            "asset_type": "stock",
            "symbol": "TSLA",
            "current_price": 200.00,
            "volatility": 0.45,
            "beta": 1.8,
            "market_cap": 650000000000,
            "pe_ratio": 45.2,
            "debt_to_equity": 0.23
        }
        
        response = await mock_provider.assess_investment_risk(
            investment_data=investment_data,
            risk_factors=["market_risk", "company_specific", "sector_risk"]
        )
        
        assert response["id"] is not None
        assert "risk_score" in response
        assert "risk_factors" in response
        assert "recommendations" in response
        
        # Score de risque entre 0 et 1
        assert 0 <= response["risk_score"] <= 1
    
    @pytest.mark.asyncio
    async def test_portfolio_optimization_request(self, mock_provider):
        """Test optimisation de portefeuille."""
        portfolio_data = {
            "current_positions": [
                {"symbol": "AAPL", "weight": 0.25, "value": 25000},
                {"symbol": "GOOGL", "weight": 0.20, "value": 20000},
                {"symbol": "MSFT", "weight": 0.15, "value": 15000},
                {"symbol": "TSLA", "weight": 0.10, "value": 10000}
            ],
            "total_value": 100000,
            "target_return": 0.12,
            "risk_tolerance": "medium",
            "constraints": {
                "max_position_size": 0.30,
                "min_position_size": 0.05,
                "sector_limits": {"Technology": 0.60}
            }
        }
        
        response = await mock_provider.optimize_portfolio(
            portfolio_data=portfolio_data,
            optimization_objective="sharpe_ratio"
        )
        
        assert response["id"] is not None
        assert "optimized_weights" in response
        assert "expected_return" in response
        assert "expected_risk" in response
        assert "rebalancing_actions" in response
    
    @pytest.mark.asyncio
    async def test_market_sentiment_analysis(self, mock_provider):
        """Test analyse de sentiment de marché."""
        news_data = [
            {
                "headline": "Fed raises interest rates by 0.25%",
                "content": "The Federal Reserve announced a quarter-point rate hike...",
                "source": "Reuters",
                "timestamp": datetime.now().isoformat()
            },
            {
                "headline": "Tech stocks rally on strong earnings",
                "content": "Major technology companies reported better than expected...",
                "source": "Bloomberg",
                "timestamp": datetime.now().isoformat()
            }
        ]
        
        response = await mock_provider.analyze_market_sentiment(
            news_data=news_data,
            sentiment_aspects=["overall", "sector_specific", "policy_impact"]
        )
        
        assert response["id"] is not None
        assert "overall_sentiment" in response
        assert "sector_sentiments" in response
        assert "sentiment_score" in response
        
        # Score de sentiment entre -1 et 1
        assert -1 <= response["sentiment_score"] <= 1


class TestCaching:
    """Tests pour le système de cache."""
    
    @pytest.fixture
    def mock_provider_with_cache(self):
        """Provider mock avec cache activé."""
        config = {
            "api_key": "sk-test-key",
            "model": "anthropic/claude-3-sonnet-20240229",
            "enable_caching": True,
            "cache_ttl": 300
        }
        return MockClaudeProvider(config)
    
    @pytest.mark.asyncio
    async def test_cache_hit(self, mock_provider_with_cache):
        """Test cache hit."""
        prompt = "What are the main types of investment strategies?"
        
        # Premier appel - depuis API
        response1 = await mock_provider_with_cache.generate_completion(prompt)
        api_calls_after_first = mock_provider_with_cache.api_call_count
        
        # Deuxième appel - depuis cache
        response2 = await mock_provider_with_cache.generate_completion(prompt)
        api_calls_after_second = mock_provider_with_cache.api_call_count
        
        # Vérifications
        assert response1["content"] == response2["content"]
        assert api_calls_after_second == api_calls_after_first  # Pas d'appel API
        assert mock_provider_with_cache.cache_hits > 0
    
    @pytest.mark.asyncio
    async def test_cache_miss_different_prompts(self, mock_provider_with_cache):
        """Test cache miss avec prompts différents."""
        prompt1 = "Explain portfolio diversification"
        prompt2 = "Explain risk management in trading"
        
        response1 = await mock_provider_with_cache.generate_completion(prompt1)
        api_calls_first = mock_provider_with_cache.api_call_count
        
        response2 = await mock_provider_with_cache.generate_completion(prompt2)
        api_calls_second = mock_provider_with_cache.api_call_count
        
        # Différents prompts = pas de cache hit
        assert response1["content"] != response2["content"]
        assert api_calls_second > api_calls_first
    
    @pytest.mark.asyncio
    async def test_cache_invalidation(self, mock_provider_with_cache):
        """Test invalidation de cache."""
        prompt = "Analyze current market conditions"
        
        # Mise en cache
        await mock_provider_with_cache.generate_completion(prompt)
        
        # Invalidation
        mock_provider_with_cache.invalidate_cache(prompt)
        
        # Nouvel appel devrait faire un appel API
        api_calls_before = mock_provider_with_cache.api_call_count
        await mock_provider_with_cache.generate_completion(prompt)
        api_calls_after = mock_provider_with_cache.api_call_count
        
        assert api_calls_after > api_calls_before


# Fixtures globales pour les tests Claude
@pytest.fixture
def claude_test_prompts():
    """Prompts de test pour Claude."""
    return {
        "analysis": [
            "Analyze the financial performance of Apple Inc.",
            "What are the key risks in the cryptocurrency market?",
            "Explain the impact of inflation on stock valuations"
        ],
        "strategy": [
            "Create a conservative investment portfolio",
            "Develop a trading strategy for volatile markets",
            "Recommend asset allocation for retirement planning"
        ],
        "education": [
            "Explain options trading basics",
            "What is quantitative easing and its market effects?",
            "How do interest rates affect different asset classes?"
        ]
    }


@pytest.fixture
def claude_test_contexts():
    """Contextes de test pour Claude."""
    return {
        "market_data": {
            "sp500": 4200.15,
            "vix": 18.5,
            "10y_treasury": 4.25,
            "fed_rate": 5.25
        },
        "portfolio": {
            "total_value": 500000,
            "cash_percentage": 0.15,
            "equity_percentage": 0.70,
            "bond_percentage": 0.15
        },
        "risk_profile": {
            "age": 35,
            "income": 120000,
            "risk_tolerance": "moderate",
            "time_horizon": "long_term"
        }
    }


@pytest.fixture
def claude_mock_responses():
    """Réponses mock pour Claude."""
    return {
        "financial_analysis": {
            "content": "Based on the financial data provided, Apple Inc. shows strong fundamentals...",
            "token_usage": {"prompt_tokens": 150, "completion_tokens": 300, "total_tokens": 450}
        },
        "investment_advice": {
            "content": "Given your risk profile and investment horizon, I recommend...",
            "token_usage": {"prompt_tokens": 200, "completion_tokens": 400, "total_tokens": 600}
        },
        "risk_assessment": {
            "content": "The risk analysis reveals several key factors to consider...",
            "token_usage": {"prompt_tokens": 180, "completion_tokens": 350, "total_tokens": 530}
        }
    }