"""
Mocks pour providers externes de FinAgent.

Ce module contient tous les mocks pour simuler les APIs externes
(OpenBB, Claude/OpenRouter) et autres services tiers.
"""

import asyncio
import json
import random
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Optional, Union
from unittest.mock import Mock, AsyncMock, MagicMock
from uuid import uuid4

import httpx
from faker import Faker

from finagent.ai.models.base import (
    AIRequest, AIResponse, ModelType, ConfidenceLevel, 
    TokenUsage, RateLimitInfo, RateLimitError
)
from finagent.core.errors.exceptions import (
    APIConnectionError, DataValidationError, FinAgentException
)

fake = Faker()


# ============================================================================
# MOCK OPENBB PROVIDER
# ============================================================================

class MockOpenBBProvider:
    """Mock complet du provider OpenBB."""
    
    def __init__(self, simulate_errors: bool = False, error_rate: float = 0.05):
        self.simulate_errors = simulate_errors
        self.error_rate = error_rate
        self.call_count = 0
        self.rate_limit_calls = 0
        
    def _should_simulate_error(self) -> bool:
        """Détermine si on doit simuler une erreur."""
        return self.simulate_errors and random.random() < self.error_rate
    
    def _increment_calls(self):
        """Incrémente les compteurs d'appels."""
        self.call_count += 1
        self.rate_limit_calls += 1
        
        # Simule rate limiting après 100 appels
        if self.rate_limit_calls > 100:
            self.rate_limit_calls = 0
            raise APIConnectionError(
                "Rate limit exceeded", 
                error_code="RATE_LIMIT_001"
            )
    
    async def get_stock_data(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """Mock pour récupération de données d'actions."""
        self._increment_calls()
        
        if self._should_simulate_error():
            raise APIConnectionError(f"Failed to fetch data for {symbol}")
            
        # Simule un délai réseau
        await asyncio.sleep(random.uniform(0.1, 0.5))
        
        base_price = random.uniform(50, 500)
        change = random.uniform(-10, 10)
        
        return {
            "symbol": symbol,
            "name": f"{symbol} Corporation",
            "price": round(base_price, 2),
            "change": round(change, 2),
            "change_percent": round((change / base_price) * 100, 2),
            "volume": random.randint(1_000_000, 100_000_000),
            "market_cap": random.randint(1_000_000_000, 3_000_000_000_000),
            "pe_ratio": round(random.uniform(10, 50), 1),
            "dividend_yield": round(random.uniform(0, 5), 2),
            "52_week_high": round(base_price * 1.2, 2),
            "52_week_low": round(base_price * 0.8, 2),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def get_technical_indicators(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """Mock pour indicateurs techniques."""
        self._increment_calls()
        
        if self._should_simulate_error():
            raise APIConnectionError(f"Failed to fetch indicators for {symbol}")
            
        await asyncio.sleep(random.uniform(0.2, 0.8))
        
        return {
            "symbol": symbol,
            "rsi": round(random.uniform(20, 80), 1),
            "macd": round(random.uniform(-2, 2), 3),
            "macd_signal": round(random.uniform(-2, 2), 3),
            "bb_upper": round(random.uniform(150, 200), 2),
            "bb_middle": round(random.uniform(140, 160), 2),
            "bb_lower": round(random.uniform(130, 150), 2),
            "sma_20": round(random.uniform(140, 160), 2),
            "sma_50": round(random.uniform(135, 155), 2),
            "sma_200": round(random.uniform(130, 150), 2),
            "ema_12": round(random.uniform(145, 165), 2),
            "ema_26": round(random.uniform(140, 160), 2),
            "volume_sma": random.randint(30_000_000, 80_000_000),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def get_news(self, symbol: str, limit: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """Mock pour news financières."""
        self._increment_calls()
        
        if self._should_simulate_error():
            raise APIConnectionError(f"Failed to fetch news for {symbol}")
            
        await asyncio.sleep(random.uniform(0.3, 1.0))
        
        sentiments = ["positive", "negative", "neutral"]
        sources = ["Reuters", "Bloomberg", "Financial Times", "Wall Street Journal"]
        
        news = []
        for i in range(min(limit, random.randint(3, 8))):
            news.append({
                "title": fake.sentence(nb_words=8)[:-1],
                "content": fake.text(max_nb_chars=500),
                "published_at": (datetime.utcnow() - timedelta(hours=random.randint(1, 48))).isoformat(),
                "source": random.choice(sources),
                "sentiment": random.choice(sentiments),
                "relevance": round(random.uniform(0.3, 1.0), 2),
                "url": fake.url(),
                "symbol": symbol
            })
        
        return news
    
    async def get_historical_data(self, symbol: str, period: str = "1y", **kwargs) -> List[Dict[str, Any]]:
        """Mock pour données historiques."""
        self._increment_calls()
        
        if self._should_simulate_error():
            raise APIConnectionError(f"Failed to fetch historical data for {symbol}")
            
        await asyncio.sleep(random.uniform(0.5, 1.5))
        
        # Génère des données historiques simulées
        periods = {"1d": 1, "1w": 7, "1m": 30, "3m": 90, "1y": 365}
        days = periods.get(period, 30)
        
        base_price = random.uniform(100, 300)
        data = []
        
        for i in range(days):
            date = datetime.utcnow() - timedelta(days=days-i-1)
            price_change = random.uniform(-0.05, 0.05)
            base_price *= (1 + price_change)
            
            data.append({
                "date": date.strftime("%Y-%m-%d"),
                "open": round(base_price * random.uniform(0.98, 1.02), 2),
                "high": round(base_price * random.uniform(1.00, 1.05), 2),
                "low": round(base_price * random.uniform(0.95, 1.00), 2),
                "close": round(base_price, 2),
                "volume": random.randint(10_000_000, 150_000_000)
            })
        
        return data
    
    async def validate_connection(self) -> bool:
        """Mock pour validation de connexion."""
        if self._should_simulate_error():
            return False
        return True
    
    def get_rate_limit_info(self) -> RateLimitInfo:
        """Mock pour informations de rate limiting."""
        return RateLimitInfo(
            requests_per_minute=100,
            tokens_per_minute=1000000,
            current_requests=self.rate_limit_calls,
            current_tokens=self.rate_limit_calls * 100,
            reset_time=datetime.utcnow() + timedelta(minutes=1)
        )


# ============================================================================
# MOCK CLAUDE PROVIDER
# ============================================================================

class MockClaudeProvider:
    """Mock complet du provider Claude/OpenRouter."""
    
    def __init__(self, simulate_errors: bool = False, error_rate: float = 0.03):
        self.simulate_errors = simulate_errors
        self.error_rate = error_rate
        self.call_count = 0
        self.total_tokens_used = 0
        
        # Templates de réponses par type d'analyse
        self.response_templates = {
            "stock_analysis": [
                "Based on the technical analysis, {symbol} shows {sentiment} signals with RSI at {rsi}...",
                "The fundamental analysis of {symbol} indicates {outlook} prospects based on recent earnings...",
                "Market sentiment for {symbol} appears {sentiment} with strong volume indicators..."
            ],
            "decision": [
                "Recommendation: {action} {symbol}. Confidence: {confidence}. Risk level: {risk}...",
                "Analysis suggests {action} position in {symbol} with {confidence} confidence...",
                "Market conditions favor a {action} strategy for {symbol}..."
            ],
            "risk_assessment": [
                "Risk assessment for {symbol}: {risk_level} risk with volatility at {volatility}...",
                "Portfolio risk analysis shows {risk_level} exposure with correlation factors...",
                "Current market conditions present {risk_level} risk for this position..."
            ]
        }
    
    def _should_simulate_error(self) -> bool:
        """Détermine si on doit simuler une erreur."""
        return self.simulate_errors and random.random() < self.error_rate
    
    def _generate_contextual_response(self, prompt: str, context: Dict[str, Any]) -> str:
        """Génère une réponse contextuelle basée sur le prompt."""
        prompt_lower = prompt.lower()
        
        # Détermine le type d'analyse
        if "analyze" in prompt_lower or "analysis" in prompt_lower:
            template_type = "stock_analysis"
        elif "decision" in prompt_lower or "recommend" in prompt_lower:
            template_type = "decision"
        elif "risk" in prompt_lower:
            template_type = "risk_assessment"
        else:
            template_type = "stock_analysis"
        
        # Sélectionne un template aléatoire
        template = random.choice(self.response_templates[template_type])
        
        # Remplace les placeholders avec des valeurs du contexte ou des valeurs par défaut
        replacements = {
            "symbol": context.get("symbol", "UNKNOWN"),
            "sentiment": random.choice(["bullish", "bearish", "neutral"]),
            "rsi": context.get("rsi", random.randint(20, 80)),
            "outlook": random.choice(["positive", "negative", "mixed"]),
            "action": random.choice(["BUY", "SELL", "HOLD"]),
            "confidence": random.choice(["HIGH", "MEDIUM", "LOW"]),
            "risk": random.choice(["LOW", "MEDIUM", "HIGH"]),
            "risk_level": random.choice(["low", "moderate", "high"]),
            "volatility": f"{random.uniform(0.1, 0.5):.2f}"
        }
        
        response = template
        for key, value in replacements.items():
            response = response.replace(f"{{{key}}}", str(value))
        
        # Ajoute du contenu additionnel
        additional_content = [
            " Technical indicators suggest continued momentum.",
            " Market fundamentals support this assessment.",
            " Consider portfolio diversification in current market conditions.",
            " Monitor key resistance/support levels closely.",
            " Recent earnings reports align with this analysis."
        ]
        
        response += random.choice(additional_content)
        response += f" Analysis generated at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC."
        
        return response
    
    async def send_request(self, request: AIRequest) -> AIResponse:
        """Mock pour envoi de requête vers Claude."""
        self.call_count += 1
        
        if self._should_simulate_error():
            if random.random() < 0.5:
                raise RateLimitError("Rate limit exceeded for Claude API")
            else:
                raise APIConnectionError("Failed to connect to Claude API")
        
        # Simule le temps de traitement
        processing_time = random.uniform(0.5, 3.0)
        await asyncio.sleep(processing_time)
        
        # Génère une réponse contextuelle
        content = self._generate_contextual_response(request.prompt, request.context)
        
        # Calcule l'utilisation des tokens
        prompt_tokens = len(request.prompt.split()) + len(str(request.context).split())
        completion_tokens = len(content.split())
        total_tokens = prompt_tokens + completion_tokens
        
        self.total_tokens_used += total_tokens
        
        return AIResponse(
            request_id=request.request_id,
            content=content,
            model_used=request.model_type,
            tokens_used=total_tokens,
            processing_time=processing_time,
            confidence=random.choice(list(ConfidenceLevel)),
            metadata={
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "model_version": "mock-1.0",
                "temperature": request.temperature
            }
        )
    
    async def validate_connection(self) -> bool:
        """Mock pour validation de connexion."""
        if self._should_simulate_error():
            return False
        
        # Simule une vérification de connexion
        await asyncio.sleep(0.1)
        return True
    
    def get_available_models(self) -> List[ModelType]:
        """Mock pour modèles disponibles."""
        return [
            ModelType.CLAUDE_3_SONNET,
            ModelType.CLAUDE_3_HAIKU,
            ModelType.CLAUDE_3_5_SONNET
        ]
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Mock pour statistiques d'utilisation."""
        return {
            "total_requests": self.call_count,
            "total_tokens": self.total_tokens_used,
            "average_tokens_per_request": self.total_tokens_used / max(self.call_count, 1),
            "estimated_cost": self.total_tokens_used * 0.0001
        }


# ============================================================================
# MOCK HTTP RESPONSES
# ============================================================================

class MockHTTPResponse:
    """Mock pour réponses HTTP."""
    
    def __init__(self, status_code: int = 200, json_data: Dict[str, Any] = None, 
                 text_data: str = None, headers: Dict[str, str] = None):
        self.status_code = status_code
        self._json_data = json_data or {}
        self._text_data = text_data or json.dumps(self._json_data)
        self.headers = headers or {"Content-Type": "application/json"}
    
    def json(self) -> Dict[str, Any]:
        """Retourne les données JSON."""
        return self._json_data
    
    @property
    def text(self) -> str:
        """Retourne le texte de la réponse."""
        return self._text_data
    
    def raise_for_status(self):
        """Simule la vérification du statut HTTP."""
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                f"HTTP {self.status_code}", 
                request=Mock(), 
                response=self
            )


def create_mock_http_client(responses: Dict[str, MockHTTPResponse]) -> Mock:
    """Crée un client HTTP mock avec des réponses prédéfinies."""
    client = AsyncMock()
    
    async def mock_request(method: str, url: str, **kwargs):
        # Trouve la réponse correspondante basée sur l'URL
        for pattern, response in responses.items():
            if pattern in url:
                return response
        
        # Réponse par défaut
        return MockHTTPResponse(404, {"error": "Not found"})
    
    client.request = mock_request
    client.get = lambda url, **kwargs: mock_request("GET", url, **kwargs)
    client.post = lambda url, **kwargs: mock_request("POST", url, **kwargs)
    
    return client


# ============================================================================
# FACTORIES DE MOCKS
# ============================================================================

def create_openbb_mock(simulate_errors: bool = False) -> MockOpenBBProvider:
    """Factory pour créer un mock OpenBB."""
    return MockOpenBBProvider(simulate_errors=simulate_errors)


def create_claude_mock(simulate_errors: bool = False) -> MockClaudeProvider:
    """Factory pour créer un mock Claude."""
    return MockClaudeProvider(simulate_errors=simulate_errors)


def create_database_mock() -> Mock:
    """Factory pour créer un mock de base de données."""
    db_mock = AsyncMock()
    
    # Mock des opérations de base
    db_mock.execute.return_value = Mock(rowcount=1)
    db_mock.fetch_one.return_value = {"id": 1, "name": "test"}
    db_mock.fetch_all.return_value = [{"id": 1, "name": "test1"}, {"id": 2, "name": "test2"}]
    
    # Mock des transactions
    db_mock.begin.return_value.__aenter__.return_value = db_mock
    db_mock.begin.return_value.__aexit__.return_value = None
    
    return db_mock


def create_cache_mock() -> Mock:
    """Factory pour créer un mock de cache."""
    cache_mock = AsyncMock()
    cache_data = {}
    
    async def mock_get(key: str):
        return cache_data.get(key)
    
    async def mock_set(key: str, value: Any, timeout: int = None):
        cache_data[key] = value
        return True
    
    async def mock_delete(key: str):
        return cache_data.pop(key, None) is not None
    
    cache_mock.get = mock_get
    cache_mock.set = mock_set
    cache_mock.delete = mock_delete
    cache_mock.clear = lambda: cache_data.clear()
    
    return cache_mock