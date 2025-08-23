"""
Factory pour créer et gérer les providers AI avec auto-détection.
"""

import asyncio
from typing import Dict, List, Optional, Type, Union, Any
from datetime import datetime, timedelta

import structlog

from .models.base import ModelType, ProviderType, AIProvider
from .providers.claude_provider import ClaudeProvider
from .providers.ollama_provider import OllamaProvider, create_ollama_provider
from .services.model_discovery_service import (
    ModelDiscoveryService, 
    initialize_discovery_service,
    get_discovery_service
)
from .config import (
    AIConfig,
    ClaudeConfig, 
    OllamaConfig,
    FallbackStrategy,
    get_ai_config
)

logger = structlog.get_logger(__name__)


class ProviderHealthStatus:
    """Statut de santé d'un provider."""
    
    def __init__(self, provider_type: ProviderType):
        self.provider_type = provider_type
        self.is_available = False
        self.last_check = None
        self.error_message = None
        self.response_time_ms = None
        self.models_available = 0
        
    def update_status(self, available: bool, error: str = None, response_time: float = None):
        """Met à jour le statut."""
        self.is_available = available
        self.last_check = datetime.utcnow()
        self.error_message = error
        self.response_time_ms = response_time
    
    def is_healthy(self, max_age_minutes: int = 5) -> bool:
        """Vérifie si le statut est encore valide."""
        if not self.last_check:
            return False
        
        age = datetime.utcnow() - self.last_check
        return age.total_seconds() < (max_age_minutes * 60)


class AIProviderFactory:
    """Factory pour créer et gérer les providers AI."""
    
    def __init__(self, config: Optional[AIConfig] = None):
        self.config = config or get_ai_config()
        self.logger = logger.bind(component="ai_factory")
        
        # Cache des providers créés
        self._providers: Dict[ProviderType, AIProvider] = {}
        self._provider_health: Dict[ProviderType, ProviderHealthStatus] = {}
        
        # Service de discovery
        self._discovery_service: Optional[ModelDiscoveryService] = None
        
        # Lock pour éviter les créations concurrentes
        self._creation_lock = asyncio.Lock()
        
        # Cache des validations
        self._validation_cache: Dict[ProviderType, bool] = {}
        self._cache_expiry: Dict[ProviderType, datetime] = {}
    
    async def initialize(self) -> bool:
        """Initialise la factory et les services."""
        try:
            self.logger.info("Initialisation AI Factory")
            
            # Valide la configuration
            validation = self.config.validate()
            if not validation["valid"]:
                self.logger.error("Configuration AI invalide", errors=validation["errors"])
                return False
            
            # Initialise le service de discovery si activé
            if self.config.enable_auto_discovery:
                success = await initialize_discovery_service(
                    ollama_config=self.config.ollama,
                    auto_refresh_interval=self.config.discovery_refresh_interval
                )
                if success:
                    self._discovery_service = await get_discovery_service()
                    self.logger.info("Service de discovery initialisé")
                else:
                    self.logger.warning("Échec initialisation service discovery")
            
            # Initialise le monitoring de santé des providers
            await self._initialize_health_monitoring()
            
            self.logger.info("AI Factory initialisée avec succès")
            return True
            
        except Exception as e:
            self.logger.error("Erreur initialisation AI Factory", error=str(e))
            return False
    
    async def _initialize_health_monitoring(self):
        """Initialise le monitoring de santé des providers."""
        for provider_type in self.config.get_enabled_providers():
            self._provider_health[provider_type] = ProviderHealthStatus(provider_type)
            
            # Check initial de santé
            await self._check_provider_health(provider_type)
    
    async def _check_provider_health(self, provider_type: ProviderType) -> bool:
        """Vérifie la santé d'un provider."""
        try:
            start_time = datetime.utcnow()
            
            if provider_type == ProviderType.CLAUDE:
                # Test simple de connectivité Claude
                provider = await self._create_claude_provider()
                if provider:
                    # Teste avec un prompt minimal
                    response = await provider.generate_response(
                        "Test", 
                        model=self.config.claude.default_model,
                        max_tokens=1
                    )
                    available = bool(response)
                else:
                    available = False
            
            elif provider_type == ProviderType.OLLAMA:
                # Test de connectivité Ollama
                provider = await self._create_ollama_provider()
                available = provider is not None and await provider.validate_connection()
            
            else:
                available = False
            
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            health_status = self._provider_health.get(provider_type)
            if health_status:
                health_status.update_status(available, response_time=response_time)
                
                if self._discovery_service and provider_type == ProviderType.OLLAMA:
                    # Met à jour le nombre de modèles disponibles
                    available_models = self._discovery_service.get_available_models()
                    health_status.models_available = len(available_models)
            
            self.logger.debug(
                "Santé provider vérifiée", 
                provider=provider_type.value,
                available=available,
                response_time_ms=response_time
            )
            
            return available
            
        except Exception as e:
            health_status = self._provider_health.get(provider_type)
            if health_status:
                health_status.update_status(False, error=str(e))
            
            self.logger.warning(
                "Erreur vérification santé provider",
                provider=provider_type.value,
                error=str(e)
            )
            return False
    
    async def _create_claude_provider(self) -> Optional[ClaudeProvider]:
        """Crée un provider Claude."""
        try:
            if not self.config.claude.validate():
                return None
            
            # Utilise l'implémentation existante de ClaudeProvider
            # (nous assumons qu'elle existe déjà dans le projet)
            provider = ClaudeProvider(
                api_key=self.config.claude.api_key,
                base_url=self.config.claude.base_url,
                default_model=self.config.claude.default_model,
                max_tokens=self.config.claude.max_tokens,
                temperature=self.config.claude.temperature,
                timeout=self.config.claude.timeout
            )
            
            return provider
            
        except Exception as e:
            self.logger.error("Erreur création Claude provider", error=str(e))
            return None
    
    async def _create_ollama_provider(self) -> Optional[OllamaProvider]:
        """Crée un provider Ollama."""
        try:
            if not self.config.ollama.validate():
                return None
            
            provider = create_ollama_provider(
                host=self.config.ollama.host,
                port=self.config.ollama.port,
                timeout=self.config.ollama.timeout
            )
            
            # Test de connexion
            if not await provider.validate_connection():
                return None
            
            return provider
            
        except Exception as e:
            self.logger.error("Erreur création Ollama provider", error=str(e))
            return None
    
    async def get_provider(
        self, 
        provider_type: Optional[ProviderType] = None,
        force_refresh: bool = False
    ) -> Optional[AIProvider]:
        """Retourne un provider AI."""
        async with self._creation_lock:
            try:
                # Détermine le provider à utiliser
                if provider_type is None:
                    provider_type = await self._select_best_provider()
                
                if provider_type is None:
                    self.logger.error("Aucun provider disponible")
                    return None
                
                # Vérifie le cache
                if not force_refresh and provider_type in self._providers:
                    provider = self._providers[provider_type]
                    
                    # Vérifie si le provider est encore valide
                    if await self._is_provider_valid(provider_type):
                        return provider
                    else:
                        # Supprime du cache
                        del self._providers[provider_type]
                
                # Crée un nouveau provider
                provider = await self._create_provider(provider_type)
                
                if provider:
                    self._providers[provider_type] = provider
                    self.logger.info("Provider créé", provider=provider_type.value)
                    return provider
                else:
                    self.logger.error("Échec création provider", provider=provider_type.value)
                    return None
                
            except Exception as e:
                self.logger.error("Erreur récupération provider", error=str(e))
                return None
    
    async def _create_provider(self, provider_type: ProviderType) -> Optional[AIProvider]:
        """Crée un provider spécifique."""
        if provider_type == ProviderType.CLAUDE:
            return await self._create_claude_provider()
        elif provider_type == ProviderType.OLLAMA:
            return await self._create_ollama_provider()
        else:
            self.logger.error("Type de provider non supporté", type=provider_type.value)
            return None
    
    async def _select_best_provider(self) -> Optional[ProviderType]:
        """Sélectionne le meilleur provider disponible."""
        try:
            # Si un provider préféré est configuré, l'essayer en premier
            if self.config.preferred_provider:
                if await self._is_provider_available(self.config.preferred_provider):
                    return self.config.preferred_provider
            
            # Utilise l'ordre de priorité configuré
            for provider_type in self.config.get_providers_by_priority():
                if await self._is_provider_available(provider_type):
                    return provider_type
            
            self.logger.warning("Aucun provider disponible")
            return None
            
        except Exception as e:
            self.logger.error("Erreur sélection provider", error=str(e))
            return None
    
    async def _is_provider_available(self, provider_type: ProviderType) -> bool:
        """Vérifie si un provider est disponible."""
        # Vérifie le cache de validation
        cache_key = provider_type
        if (cache_key in self._validation_cache and 
            cache_key in self._cache_expiry and
            datetime.utcnow() < self._cache_expiry[cache_key]):
            return self._validation_cache[cache_key]
        
        # Vérifie la santé du provider
        health_status = self._provider_health.get(provider_type)
        if health_status and health_status.is_healthy():
            available = health_status.is_available
        else:
            # Re-vérifie la santé
            available = await self._check_provider_health(provider_type)
        
        # Met en cache le résultat
        self._validation_cache[cache_key] = available
        self._cache_expiry[cache_key] = datetime.utcnow() + timedelta(minutes=5)
        
        return available
    
    async def _is_provider_valid(self, provider_type: ProviderType) -> bool:
        """Vérifie si un provider en cache est encore valide."""
        return await self._is_provider_available(provider_type)
    
    async def get_provider_with_fallback(
        self,
        primary_provider: Optional[ProviderType] = None,
        task_type: Optional[str] = None
    ) -> Optional[AIProvider]:
        """Retourne un provider avec fallback automatique."""
        try:
            # Détermine le provider primaire
            if primary_provider is None:
                primary_provider = await self._select_best_provider()
            
            if primary_provider is None:
                return None
            
            # Essaie le provider primaire
            provider = await self.get_provider(primary_provider)
            if provider:
                return provider
            
            # Essaie les providers de fallback
            fallback_providers = self.config.get_fallback_providers(primary_provider)
            
            for fallback_provider in fallback_providers:
                self.logger.info(
                    "Tentative fallback provider",
                    primary=primary_provider.value,
                    fallback=fallback_provider.value
                )
                
                provider = await self.get_provider(fallback_provider)
                if provider:
                    return provider
            
            self.logger.error("Aucun provider disponible après fallback")
            return None
            
        except Exception as e:
            self.logger.error("Erreur provider avec fallback", error=str(e))
            return None
    
    async def get_recommended_provider_for_task(self, task_type: str) -> Optional[ProviderType]:
        """Recommande un provider pour une tâche spécifique."""
        try:
            # Récupère les modèles recommandés pour la tâche
            recommended_models = self.config.get_recommended_models_for_task(task_type)
            
            if not recommended_models:
                return await self._select_best_provider()
            
            # Trouve le premier provider disponible avec un modèle recommandé
            for model_type in recommended_models:
                for provider_type in self.config.get_providers_by_priority():
                    if await self._is_provider_available(provider_type):
                        # Vérifie si le provider supporte ce modèle
                        if await self._provider_supports_model(provider_type, model_type):
                            return provider_type
            
            # Fallback sur le meilleur provider disponible
            return await self._select_best_provider()
            
        except Exception as e:
            self.logger.error("Erreur recommandation provider", task=task_type, error=str(e))
            return await self._select_best_provider()
    
    async def _provider_supports_model(self, provider_type: ProviderType, model_type: ModelType) -> bool:
        """Vérifie si un provider supporte un modèle."""
        try:
            if provider_type == ProviderType.CLAUDE:
                from .models.base import ModelUtils
                return ModelUtils.is_claude_model(model_type)
            
            elif provider_type == ProviderType.OLLAMA:
                from .models.base import ModelUtils
                if not ModelUtils.is_ollama_model(model_type):
                    return False
                
                # Vérifie si le modèle est disponible via le service de discovery
                if self._discovery_service:
                    return self._discovery_service.is_model_available(model_type)
                
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(
                "Erreur vérification support modèle",
                provider=provider_type.value,
                model=model_type.value,
                error=str(e)
            )
            return False
    
    def get_provider_health_status(self) -> Dict[str, Any]:
        """Retourne le statut de santé de tous les providers."""
        health_report = {}
        
        for provider_type, health_status in self._provider_health.items():
            health_report[provider_type.value] = {
                "available": health_status.is_available,
                "last_check": health_status.last_check.isoformat() if health_status.last_check else None,
                "response_time_ms": health_status.response_time_ms,
                "models_available": health_status.models_available,
                "error": health_status.error_message,
                "healthy": health_status.is_healthy()
            }
        
        return health_report
    
    async def refresh_all_providers(self):
        """Rafraîchit tous les providers et leur statut."""
        self.logger.info("Rafraîchissement de tous les providers")
        
        # Vide les caches
        self._validation_cache.clear()
        self._cache_expiry.clear()
        
        # Re-vérifie la santé de tous les providers
        for provider_type in self.config.get_enabled_providers():
            await self._check_provider_health(provider_type)
        
        # Rafraîchit le service de discovery
        if self._discovery_service:
            await self._discovery_service.refresh_models()
    
    async def shutdown(self):
        """Arrête la factory et libère les ressources."""
        self.logger.info("Arrêt AI Factory")
        
        # Ferme tous les providers
        for provider in self._providers.values():
            if hasattr(provider, 'close'):
                try:
                    await provider.close()
                except:
                    pass
        
        # Arrête le service de discovery
        if self._discovery_service:
            await self._discovery_service.shutdown()
        
        self._providers.clear()
        self._provider_health.clear()


# Instance globale de la factory
_ai_factory: Optional[AIProviderFactory] = None


async def get_ai_factory() -> AIProviderFactory:
    """Retourne l'instance globale de la factory."""
    global _ai_factory
    
    if _ai_factory is None:
        _ai_factory = AIProviderFactory()
        await _ai_factory.initialize()
    
    return _ai_factory


async def create_ai_provider(
    provider_type: Optional[ProviderType] = None,
    task_type: Optional[str] = None,
    with_fallback: bool = True
) -> Optional[AIProvider]:
    """Fonction utilitaire pour créer un provider AI."""
    factory = await get_ai_factory()
    
    if with_fallback:
        return await factory.get_provider_with_fallback(provider_type, task_type)
    else:
        return await factory.get_provider(provider_type)


async def shutdown_ai_factory():
    """Arrête la factory globale."""
    global _ai_factory
    
    if _ai_factory:
        await _ai_factory.shutdown()
        _ai_factory = None