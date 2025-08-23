"""
Provider Claude via OpenRouter pour l'intégration IA.
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import uuid4

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)
import structlog

from ..models import (
    AIRequest,
    AIResponse,
    AIProvider,
    ModelType,
    TokenUsage,
    RateLimitInfo,
    AIError,
    RateLimitError,
    ModelNotAvailableError,
    InvalidRequestError,
    ProviderError,
)

logger = structlog.get_logger(__name__)


class OpenRouterConfig:
    """Configuration pour OpenRouter."""
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://openrouter.ai/api/v1",
        site_url: Optional[str] = None,
        app_name: Optional[str] = None,
        timeout: int = 60,
        max_retries: int = 3,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.site_url = site_url
        self.app_name = app_name or "FinAgent"
        self.timeout = timeout
        self.max_retries = max_retries


class RateLimiter:
    """Gestionnaire de rate limiting."""
    
    def __init__(self, requests_per_minute: int = 60, tokens_per_minute: int = 100000):
        self.requests_per_minute = requests_per_minute
        self.tokens_per_minute = tokens_per_minute
        self.request_times: List[float] = []
        self.token_usage: List[tuple[float, int]] = []  # (timestamp, tokens)
        self._lock = asyncio.Lock()
    
    async def can_make_request(self, estimated_tokens: int = 1000) -> bool:
        """Vérifie si on peut faire une requête."""
        async with self._lock:
            now = time.time()
            minute_ago = now - 60
            
            # Nettoie les anciens records
            self.request_times = [t for t in self.request_times if t > minute_ago]
            self.token_usage = [(t, tokens) for t, tokens in self.token_usage if t > minute_ago]
            
            # Vérifie les limites
            current_requests = len(self.request_times)
            current_tokens = sum(tokens for _, tokens in self.token_usage)
            
            return (
                current_requests < self.requests_per_minute and
                current_tokens + estimated_tokens <= self.tokens_per_minute
            )
    
    async def record_request(self, tokens_used: int):
        """Enregistre une requête effectuée."""
        async with self._lock:
            now = time.time()
            self.request_times.append(now)
            self.token_usage.append((now, tokens_used))
    
    def get_rate_limit_info(self) -> RateLimitInfo:
        """Retourne les informations de rate limiting."""
        now = time.time()
        minute_ago = now - 60
        
        current_requests = len([t for t in self.request_times if t > minute_ago])
        current_tokens = sum(tokens for t, tokens in self.token_usage if t > minute_ago)
        
        return RateLimitInfo(
            requests_per_minute=self.requests_per_minute,
            tokens_per_minute=self.tokens_per_minute,
            current_requests=current_requests,
            current_tokens=current_tokens,
            reset_time=datetime.fromtimestamp(now + 60)
        )


class ClaudeProvider(AIProvider):
    """Provider pour Claude via OpenRouter."""
    
    # Mapping des modèles vers les identifiants OpenRouter
    MODEL_MAPPING = {
        ModelType.CLAUDE_3_SONNET: "anthropic/claude-3-sonnet",
        ModelType.CLAUDE_3_HAIKU: "anthropic/claude-3-haiku",
        ModelType.CLAUDE_3_OPUS: "anthropic/claude-3-opus",
        ModelType.CLAUDE_3_5_SONNET: "anthropic/claude-3.5-sonnet",
        ModelType.CLAUDE_3_5_HAIKU: "anthropic/claude-3.5-haiku",
    }
    
    # Coûts approximatifs par 1K tokens (input/output)
    MODEL_COSTS = {
        ModelType.CLAUDE_3_HAIKU: (0.00025, 0.00125),
        ModelType.CLAUDE_3_SONNET: (0.003, 0.015),
        ModelType.CLAUDE_3_5_SONNET: (0.003, 0.015),
        ModelType.CLAUDE_3_5_HAIKU: (0.0005, 0.0025),
        ModelType.CLAUDE_3_OPUS: (0.015, 0.075),
    }
    
    def __init__(self, config: OpenRouterConfig):
        self.config = config
        self.rate_limiter = RateLimiter()
        self._client: Optional[httpx.AsyncClient] = None
        self._last_health_check: Optional[datetime] = None
        
        self.logger = logger.bind(provider="claude", base_url=config.base_url)
    
    async def __aenter__(self):
        """Context manager entry."""
        await self._ensure_client()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def _ensure_client(self):
        """S'assure que le client HTTP est initialisé."""
        if not self._client:
            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": self.config.site_url or "https://finagent.local",
                "X-Title": self.config.app_name,
            }
            
            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                headers=headers,
                timeout=httpx.Timeout(self.config.timeout),
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
            )
    
    @retry(
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        before_sleep=before_sleep_log(logger.warning, log_level="WARNING")
    )
    async def send_request(self, request: AIRequest) -> AIResponse:
        """Envoie une requête à Claude via OpenRouter."""
        start_time = time.time()
        
        # Validation du modèle
        if request.model_type not in self.MODEL_MAPPING:
            raise ModelNotAvailableError(
                f"Modèle {request.model_type} non supporté",
                error_code="UNSUPPORTED_MODEL"
            )
        
        # Vérification du rate limiting
        estimated_tokens = len(request.prompt) // 4  # Estimation approximative
        if not await self.rate_limiter.can_make_request(estimated_tokens):
            rate_info = self.rate_limiter.get_rate_limit_info()
            raise RateLimitError(
                "Limite de taux dépassée",
                error_code="RATE_LIMIT_EXCEEDED",
                details={"rate_limit_info": rate_info.model_dump()}
            )
        
        await self._ensure_client()
        
        # Préparation de la requête
        openrouter_model = self.MODEL_MAPPING[request.model_type]
        payload = {
            "model": openrouter_model,
            "messages": [
                {"role": "user", "content": request.prompt}
            ],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "stream": False,
        }
        
        # Ajout du contexte si présent
        if request.context:
            # Ajoute le contexte comme message système si supporté
            system_content = self._format_context(request.context)
            if system_content:
                payload["messages"].insert(0, {
                    "role": "system", 
                    "content": system_content
                })
        
        try:
            self.logger.info(
                "Envoi requête Claude",
                model=openrouter_model,
                tokens_estimated=estimated_tokens,
                request_id=str(request.request_id)
            )
            
            response = await self._client.post(
                "/chat/completions",
                json=payload
            )
            response.raise_for_status()
            
            data = response.json()
            processing_time = time.time() - start_time
            
            # Extraction des informations de la réponse
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            tokens_used = usage.get("total_tokens", 0)
            
            # Enregistrement pour le rate limiting
            await self.rate_limiter.record_request(tokens_used)
            
            # Estimation du coût
            input_cost, output_cost = self.MODEL_COSTS.get(request.model_type, (0, 0))
            estimated_cost = (
                usage.get("prompt_tokens", 0) * input_cost / 1000 +
                usage.get("completion_tokens", 0) * output_cost / 1000
            )
            
            ai_response = AIResponse(
                request_id=request.request_id,
                content=content,
                model_used=request.model_type,
                tokens_used=tokens_used,
                processing_time=processing_time,
                metadata={
                    "usage": usage,
                    "estimated_cost": estimated_cost,
                    "openrouter_model": openrouter_model,
                    "rate_limit_info": self.rate_limiter.get_rate_limit_info().model_dump()
                }
            )
            
            self.logger.info(
                "Réponse Claude reçue",
                tokens_used=tokens_used,
                processing_time=processing_time,
                estimated_cost=estimated_cost,
                request_id=str(request.request_id)
            )
            
            return ai_response
            
        except httpx.HTTPStatusError as e:
            error_msg = f"Erreur HTTP {e.response.status_code}"
            error_details = {}
            
            try:
                error_data = e.response.json()
                error_msg = error_data.get("error", {}).get("message", error_msg)
                error_details = error_data
            except:
                pass
            
            self.logger.error(
                "Erreur HTTP Claude",
                status_code=e.response.status_code,
                error_msg=error_msg,
                request_id=str(request.request_id)
            )
            
            if e.response.status_code == 429:
                raise RateLimitError(
                    "Limite de taux OpenRouter dépassée",
                    error_code="OPENROUTER_RATE_LIMIT",
                    details=error_details
                )
            elif e.response.status_code in (400, 422):
                raise InvalidRequestError(
                    f"Requête invalide: {error_msg}",
                    error_code="INVALID_REQUEST",
                    details=error_details
                )
            else:
                raise ProviderError(
                    f"Erreur provider: {error_msg}",
                    error_code="PROVIDER_ERROR",
                    details=error_details
                )
                
        except httpx.RequestError as e:
            self.logger.error(
                "Erreur réseau Claude",
                error=str(e),
                request_id=str(request.request_id)
            )
            raise ProviderError(
                f"Erreur de connexion: {str(e)}",
                error_code="CONNECTION_ERROR"
            )
        except Exception as e:
            self.logger.error(
                "Erreur inattendue Claude",
                error=str(e),
                request_id=str(request.request_id)
            )
            raise ProviderError(
                f"Erreur inattendue: {str(e)}",
                error_code="UNEXPECTED_ERROR"
            )
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Formate le contexte en message système."""
        if not context:
            return ""
        
        parts = []
        
        # Contexte de marché
        if "market_data" in context:
            parts.append("Données de marché:")
            parts.append(json.dumps(context["market_data"], indent=2))
        
        # Stratégie
        if "strategy" in context:
            parts.append(f"Stratégie: {context['strategy']}")
        
        # Préférences utilisateur
        if "user_preferences" in context:
            parts.append("Préférences utilisateur:")
            parts.append(json.dumps(context["user_preferences"], indent=2))
        
        # Historique des décisions
        if "decision_history" in context:
            parts.append("Historique récent des décisions:")
            for decision in context["decision_history"][-3:]:  # 3 dernières
                parts.append(f"- {decision}")
        
        return "\n\n".join(parts) if parts else ""
    
    async def validate_connection(self) -> bool:
        """Valide la connexion à OpenRouter."""
        try:
            # Check health moins fréquent (cache 5 minutes)
            now = datetime.utcnow()
            if (self._last_health_check and 
                now - self._last_health_check < timedelta(minutes=5)):
                return True
            
            await self._ensure_client()
            
            # Test avec une requête simple
            test_request = AIRequest(
                model_type=ModelType.CLAUDE_3_HAIKU,  # Modèle le moins cher
                prompt="Test de connexion. Réponds simplement 'OK'.",
                max_tokens=10,
                temperature=0.1
            )
            
            response = await self.send_request(test_request)
            
            self._last_health_check = now
            self.logger.info("Validation connexion Claude réussie")
            
            return "OK" in response.content.upper()
            
        except Exception as e:
            self.logger.error("Échec validation connexion Claude", error=str(e))
            return False
    
    def get_available_models(self) -> List[ModelType]:
        """Retourne la liste des modèles Claude disponibles."""
        return list(self.MODEL_MAPPING.keys())
    
    def get_model_info(self, model_type: ModelType) -> Dict[str, Any]:
        """Retourne les informations sur un modèle."""
        if model_type not in self.MODEL_MAPPING:
            raise ModelNotAvailableError(f"Modèle {model_type} non supporté")
        
        input_cost, output_cost = self.MODEL_COSTS.get(model_type, (0, 0))
        
        return {
            "model_id": self.MODEL_MAPPING[model_type],
            "input_cost_per_1k": input_cost,
            "output_cost_per_1k": output_cost,
            "max_tokens": 8192 if model_type == ModelType.CLAUDE_3_OPUS else 4096,
            "context_window": 200000,  # Claude 3 a un large context
            "recommended_for": self._get_model_recommendations(model_type)
        }
    
    def _get_model_recommendations(self, model_type: ModelType) -> List[str]:
        """Retourne les recommandations d'usage pour un modèle."""
        recommendations = {
            ModelType.CLAUDE_3_HAIKU: [
                "Décisions rapides",
                "Analyses simples", 
                "Screening d'actions",
                "Réponses courtes"
            ],
            ModelType.CLAUDE_3_SONNET: [
                "Analyses financières détaillées",
                "Décisions de trading complexes",
                "Évaluation de risques",
                "Analyses de sentiment"
            ],
            ModelType.CLAUDE_3_5_SONNET: [
                "Analyses financières avancées",
                "Stratégies de trading",
                "Analyses sectorielles",
                "Recommandations personnalisées"
            ],
            ModelType.CLAUDE_3_OPUS: [
                "Analyses très complexes",
                "Recherche approfondie",
                "Modélisation financière",
                "Analyses multi-factorielles"
            ]
        }
        return recommendations.get(model_type, [])
    
    async def estimate_cost(self, prompt: str, model_type: ModelType) -> float:
        """Estime le coût d'une requête."""
        if model_type not in self.MODEL_COSTS:
            return 0.0
        
        # Estimation approximative des tokens
        prompt_tokens = len(prompt) // 4
        estimated_completion_tokens = min(prompt_tokens // 2, 1000)  # Estimation conservative
        
        input_cost, output_cost = self.MODEL_COSTS[model_type]
        
        return (
            prompt_tokens * input_cost / 1000 +
            estimated_completion_tokens * output_cost / 1000
        )
    
    def get_rate_limit_status(self) -> RateLimitInfo:
        """Retourne le statut actuel du rate limiting."""
        return self.rate_limiter.get_rate_limit_info()


# Factory function pour créer un provider Claude
def create_claude_provider(
    api_key: str,
    site_url: Optional[str] = None,
    app_name: str = "FinAgent",
    **kwargs
) -> ClaudeProvider:
    """Crée un provider Claude configuré."""
    config = OpenRouterConfig(
        api_key=api_key,
        site_url=site_url,
        app_name=app_name,
        **kwargs
    )
    return ClaudeProvider(config)