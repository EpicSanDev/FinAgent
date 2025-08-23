"""
Provider Ollama pour l'intégration IA locale.
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

import httpx
import structlog
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

from ..models import (
    AIRequest,
    AIResponse,
    AIProvider,
    ModelType,
    ProviderType,
    ModelUtils,
    TokenUsage,
    RateLimitInfo,
    AIError,
    RateLimitError,
    ModelNotAvailableError,
    InvalidRequestError,
    ProviderError,
)

logger = structlog.get_logger(__name__)


class OllamaConfig:
    """Configuration pour Ollama."""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 11434,
        base_url: Optional[str] = None,
        timeout: int = 120,
        max_retries: int = 3,
        stream: bool = False,
        keep_alive: Optional[str] = "5m"
    ):
        self.host = host
        self.port = port
        self.base_url = base_url or f"http://{host}:{port}"
        self.timeout = timeout
        self.max_retries = max_retries
        self.stream = stream
        self.keep_alive = keep_alive
        
        # Assurer que l'URL se termine correctement
        self.base_url = self.base_url.rstrip('/')


class OllamaModelInfo:
    """Informations sur un modèle Ollama."""
    
    def __init__(self, data: Dict[str, Any]):
        self.name: str = data.get("name", "")
        self.modified_at: str = data.get("modified_at", "")
        self.size: int = data.get("size", 0)
        self.digest: str = data.get("digest", "")
        self.details: Dict[str, Any] = data.get("details", {})
        
    @property
    def size_gb(self) -> float:
        """Taille du modèle en GB."""
        return self.size / (1024 ** 3)
    
    @property
    def parameter_count(self) -> Optional[str]:
        """Nombre de paramètres du modèle."""
        return self.details.get("parameter_size")
    
    @property
    def quantization(self) -> Optional[str]:
        """Type de quantization."""
        return self.details.get("quantization_level")


class OllamaRateLimiter:
    """Gestionnaire de rate limiting pour Ollama (basique car local)."""
    
    def __init__(self, max_concurrent: int = 3):
        self.max_concurrent = max_concurrent
        self.active_requests = 0
        self._lock = asyncio.Lock()
    
    async def can_make_request(self) -> bool:
        """Vérifie si on peut faire une requête."""
        async with self._lock:
            return self.active_requests < self.max_concurrent
    
    async def acquire(self):
        """Acquiert un slot pour une requête."""
        async with self._lock:
            self.active_requests += 1
    
    async def release(self):
        """Libère un slot après une requête."""
        async with self._lock:
            self.active_requests = max(0, self.active_requests - 1)
    
    def get_rate_limit_info(self) -> RateLimitInfo:
        """Retourne les informations de rate limiting."""
        return RateLimitInfo(
            requests_per_minute=self.max_concurrent * 20,  # Estimation
            tokens_per_minute=100000,  # Pas de limite réelle pour local
            current_requests=self.active_requests,
            current_tokens=0,
            reset_time=datetime.utcnow()
        )


class OllamaProvider(AIProvider):
    """Provider pour Ollama local."""
    
    def __init__(self, config: OllamaConfig):
        self.config = config
        self.rate_limiter = OllamaRateLimiter()
        self.logger = logger.bind(provider="ollama")
        self._available_models: Optional[List[OllamaModelInfo]] = None
        self._models_cache_time: Optional[float] = None
        self._cache_ttl = 300  # 5 minutes
        
        # Client HTTP avec configuration appropriée
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.config.timeout),
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
        )
    
    def get_provider_type(self) -> ProviderType:
        """Retourne le type du provider."""
        return ProviderType.OLLAMA
    
    async def validate_connection(self) -> bool:
        """Valide la connexion au serveur Ollama."""
        try:
            response = await self.client.get(f"{self.config.base_url}/api/tags")
            if response.status_code == 200:
                self.logger.info("Connexion Ollama validée", url=self.config.base_url)
                return True
            else:
                self.logger.warning(
                    "Connexion Ollama échoué",
                    status_code=response.status_code,
                    url=self.config.base_url
                )
                return False
        except Exception as e:
            self.logger.error(
                "Erreur validation connexion Ollama",
                error=str(e),
                url=self.config.base_url
            )
            return False
    
    async def _refresh_available_models(self) -> List[OllamaModelInfo]:
        """Récupère la liste des modèles disponibles depuis Ollama."""
        try:
            response = await self.client.get(f"{self.config.base_url}/api/tags")
            if response.status_code == 200:
                data = response.json()
                models = [OllamaModelInfo(model_data) for model_data in data.get("models", [])]
                self._available_models = models
                self._models_cache_time = time.time()
                
                self.logger.info(
                    "Modèles Ollama récupérés",
                    count=len(models),
                    models=[m.name for m in models]
                )
                return models
            else:
                raise ProviderError(f"Erreur récupération modèles: {response.status_code}")
        except Exception as e:
            self.logger.error("Erreur refresh modèles Ollama", error=str(e))
            raise ProviderError(f"Impossible de récupérer les modèles Ollama: {e}")
    
    async def get_available_models_info(self) -> List[OllamaModelInfo]:
        """Retourne les informations détaillées des modèles disponibles."""
        # Vérifie le cache
        if (self._available_models is None or 
            self._models_cache_time is None or 
            time.time() - self._models_cache_time > self._cache_ttl):
            await self._refresh_available_models()
        
        return self._available_models or []
    
    def get_available_models(self) -> List[ModelType]:
        """Retourne la liste des modèles disponibles en tant que ModelType."""
        # Version synchrone pour l'interface
        # En pratique, cette méthode devrait être appelée après un refresh async
        if self._available_models:
            available_names = [model.name for model in self._available_models]
            return [
                model_type for model_type in ModelType
                if ModelUtils.is_ollama_model(model_type) and 
                model_type.value in available_names
            ]
        return []
    
    async def is_model_available(self, model: ModelType) -> bool:
        """Vérifie si un modèle spécifique est disponible."""
        if not ModelUtils.is_ollama_model(model):
            return False
        
        available_models = await self.get_available_models_info()
        return any(m.name == model.value for m in available_models)
    
    async def pull_model(self, model_name: str) -> bool:
        """Télécharge un modèle si pas disponible."""
        try:
            self.logger.info("Téléchargement modèle Ollama", model=model_name)
            
            payload = {"name": model_name}
            response = await self.client.post(
                f"{self.config.base_url}/api/pull",
                json=payload,
                timeout=httpx.Timeout(600)  # 10 minutes pour le téléchargement
            )
            
            if response.status_code == 200:
                # Invalide le cache des modèles
                self._available_models = None
                self.logger.info("Modèle téléchargé avec succès", model=model_name)
                return True
            else:
                self.logger.error(
                    "Erreur téléchargement modèle",
                    model=model_name,
                    status_code=response.status_code
                )
                return False
        except Exception as e:
            self.logger.error(
                "Exception téléchargement modèle",
                model=model_name,
                error=str(e)
            )
            return False
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
        before_sleep=before_sleep_log(logger, structlog.INFO)
    )
    async def send_request(self, request: AIRequest) -> AIResponse:
        """Envoie une requête à Ollama et retourne la réponse."""
        start_time = time.time()
        
        # Vérifie si on peut faire la requête
        if not await self.rate_limiter.can_make_request():
            raise RateLimitError("Trop de requêtes simultanées vers Ollama")
        
        await self.rate_limiter.acquire()
        
        try:
            # Vérifie que le modèle est disponible
            if not await self.is_model_available(request.model_type):
                # Tente de télécharger le modèle
                if not await self.pull_model(request.model_type.value):
                    raise ModelNotAvailableError(
                        f"Modèle {request.model_type.value} non disponible et téléchargement échoué"
                    )
            
            # Prépare la requête Ollama
            payload = {
                "model": request.model_type.value,
                "prompt": request.prompt,
                "options": {
                    "temperature": request.temperature,
                    "num_predict": request.max_tokens,
                },
                "stream": self.config.stream,
                "keep_alive": self.config.keep_alive
            }
            
            # Ajoute le contexte si fourni
            if request.context:
                # Ollama peut utiliser le contexte dans le prompt ou comme système
                if "system" in request.context:
                    payload["system"] = request.context["system"]
                
                # Ajoute d'autres informations de contexte au prompt
                context_info = []
                for key, value in request.context.items():
                    if key != "system" and value:
                        context_info.append(f"{key}: {value}")
                
                if context_info:
                    payload["prompt"] = f"Context: {'; '.join(context_info)}\n\n{request.prompt}"
            
            self.logger.debug(
                "Envoi requête Ollama",
                model=request.model_type.value,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
            
            # Envoie la requête
            response = await self.client.post(
                f"{self.config.base_url}/api/generate",
                json=payload
            )
            
            processing_time = time.time() - start_time
            
            if response.status_code != 200:
                raise ProviderError(
                    f"Erreur Ollama: {response.status_code} - {response.text}"
                )
            
            # Parse la réponse
            response_data = response.json()
            content = response_data.get("response", "")
            
            # Estime l'utilisation des tokens (approximatif)
            prompt_tokens = len(request.prompt.split()) * 1.3  # Approximation
            completion_tokens = len(content.split()) * 1.3
            total_tokens = prompt_tokens + completion_tokens
            
            tokens_used = TokenUsage(
                prompt_tokens=int(prompt_tokens),
                completion_tokens=int(completion_tokens),
                total_tokens=int(total_tokens),
                estimated_cost=0.0  # Ollama est gratuit
            )
            
            # Crée la réponse
            ai_response = AIResponse(
                request_id=request.request_id,
                content=content,
                model_used=request.model_type,
                tokens_used=int(total_tokens),
                processing_time=processing_time,
                metadata={
                    "ollama_response": response_data,
                    "model_info": response_data.get("model", {}),
                    "done": response_data.get("done", True),
                    "rate_limit_info": self.rate_limiter.get_rate_limit_info().model_dump()
                }
            )
            
            self.logger.info(
                "Requête Ollama terminée",
                model=request.model_type.value,
                tokens=int(total_tokens),
                duration=processing_time
            )
            
            return ai_response
            
        except httpx.TimeoutException:
            raise ProviderError(f"Timeout lors de la requête vers Ollama après {self.config.timeout}s")
        except httpx.ConnectError:
            raise ProviderError(f"Impossible de se connecter à Ollama sur {self.config.base_url}")
        except json.JSONDecodeError:
            raise ProviderError("Réponse Ollama invalide (JSON malformé)")
        except Exception as e:
            self.logger.error("Erreur inattendue Ollama", error=str(e))
            raise ProviderError(f"Erreur inattendue: {e}")
        finally:
            await self.rate_limiter.release()
    
    async def close(self):
        """Ferme les connexions du provider."""
        await self.client.aclose()
        self.logger.info("Provider Ollama fermé")


# Factory function pour créer un provider Ollama
def create_ollama_provider(
    host: str = "localhost",
    port: int = 11434,
    timeout: int = 120,
    **kwargs
) -> OllamaProvider:
    """
    Crée une instance du provider Ollama.
    
    Args:
        host: Host du serveur Ollama
        port: Port du serveur Ollama
        timeout: Timeout en secondes
        **kwargs: Arguments supplémentaires pour OllamaConfig
    
    Returns:
        Instance configurée du provider Ollama
    """
    config = OllamaConfig(
        host=host,
        port=port,
        timeout=timeout,
        **kwargs
    )
    return OllamaProvider(config)