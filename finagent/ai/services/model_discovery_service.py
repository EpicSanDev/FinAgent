"""
Service de découverte automatique des modèles Ollama.
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass
from enum import Enum

import structlog

from ..models import ModelType, ProviderType, ModelUtils
from ..providers.ollama_provider import OllamaProvider, OllamaModelInfo, OllamaConfig

logger = structlog.get_logger(__name__)


class ModelStatus(str, Enum):
    """Statut d'un modèle."""
    AVAILABLE = "available"
    DOWNLOADING = "downloading"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


@dataclass
class ModelDiscoveryInfo:
    """Informations sur un modèle découvert."""
    model_type: ModelType
    status: ModelStatus
    size_gb: Optional[float] = None
    parameter_count: Optional[str] = None
    last_used: Optional[datetime] = None
    download_progress: Optional[float] = None
    error_message: Optional[str] = None
    
    @property
    def is_available(self) -> bool:
        """Vérifie si le modèle est disponible."""
        return self.status == ModelStatus.AVAILABLE
    
    @property
    def size_category(self) -> str:
        """Catégorie de taille du modèle."""
        return ModelUtils.get_model_size_category(self.model_type)


class ModelDiscoveryService:
    """Service de découverte automatique des modèles Ollama."""
    
    def __init__(
        self,
        ollama_provider: Optional[OllamaProvider] = None,
        auto_refresh_interval: int = 300,  # 5 minutes
        auto_pull_popular: bool = False
    ):
        self.ollama_provider = ollama_provider
        self.auto_refresh_interval = auto_refresh_interval
        self.auto_pull_popular = auto_pull_popular
        self.logger = logger.bind(service="model_discovery")
        
        # Cache des modèles découverts
        self._discovered_models: Dict[ModelType, ModelDiscoveryInfo] = {}
        self._last_refresh: Optional[datetime] = None
        self._refresh_lock = asyncio.Lock()
        self._auto_refresh_task: Optional[asyncio.Task] = None
        
        # Modèles populaires à télécharger automatiquement
        self.popular_models = [
            ModelType.LLAMA3_1_8B,
            ModelType.MISTRAL_7B,
            ModelType.GEMMA_7B,
            ModelType.CODELLAMA_7B
        ]
    
    async def initialize(self, ollama_config: Optional[OllamaConfig] = None) -> bool:
        """Initialise le service de découverte."""
        try:
            # Crée le provider Ollama si pas fourni
            if not self.ollama_provider:
                config = ollama_config or OllamaConfig()
                from ..providers.ollama_provider import create_ollama_provider
                self.ollama_provider = create_ollama_provider(
                    host=config.host,
                    port=config.port,
                    timeout=config.timeout
                )
            
            # Vérifie la connexion Ollama
            if not await self.ollama_provider.validate_connection():
                self.logger.warning("Ollama non disponible, discovery désactivé")
                return False
            
            # Premier scan des modèles
            await self.refresh_models()
            
            # Démarre le refresh automatique
            if self.auto_refresh_interval > 0:
                self._auto_refresh_task = asyncio.create_task(self._auto_refresh_loop())
            
            self.logger.info("Service de découverte initialisé")
            return True
            
        except Exception as e:
            self.logger.error("Erreur initialisation discovery service", error=str(e))
            return False
    
    async def _auto_refresh_loop(self):
        """Boucle de refresh automatique des modèles."""
        while True:
            try:
                await asyncio.sleep(self.auto_refresh_interval)
                await self.refresh_models()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("Erreur dans auto-refresh loop", error=str(e))
                await asyncio.sleep(60)  # Attendre 1 minute avant de réessayer
    
    async def refresh_models(self) -> Dict[ModelType, ModelDiscoveryInfo]:
        """Rafraîchit la liste des modèles disponibles."""
        async with self._refresh_lock:
            try:
                if not self.ollama_provider:
                    return self._discovered_models
                
                self.logger.debug("Début refresh des modèles")
                
                # Récupère les modèles installés
                available_models = await self.ollama_provider.get_available_models_info()
                available_names = {model.name for model in available_models}
                
                # Met à jour les modèles connus
                for model_type in ModelType:
                    if not ModelUtils.is_ollama_model(model_type):
                        continue
                    
                    model_name = model_type.value
                    
                    if model_name in available_names:
                        # Modèle disponible
                        model_info = next(m for m in available_models if m.name == model_name)
                        
                        discovery_info = ModelDiscoveryInfo(
                            model_type=model_type,
                            status=ModelStatus.AVAILABLE,
                            size_gb=model_info.size_gb,
                            parameter_count=model_info.parameter_count
                        )
                        
                        # Conserve les infos existantes si disponibles
                        if model_type in self._discovered_models:
                            existing = self._discovered_models[model_type]
                            discovery_info.last_used = existing.last_used
                        
                        self._discovered_models[model_type] = discovery_info
                    
                    else:
                        # Modèle non disponible
                        if model_type not in self._discovered_models:
                            self._discovered_models[model_type] = ModelDiscoveryInfo(
                                model_type=model_type,
                                status=ModelStatus.UNAVAILABLE
                            )
                        elif self._discovered_models[model_type].status == ModelStatus.AVAILABLE:
                            # Modèle était disponible mais plus maintenant
                            self._discovered_models[model_type].status = ModelStatus.UNAVAILABLE
                
                self._last_refresh = datetime.utcnow()
                
                self.logger.info(
                    "Refresh modèles terminé",
                    available=len([m for m in self._discovered_models.values() if m.is_available]),
                    total=len(self._discovered_models)
                )
                
                # Auto-pull des modèles populaires si activé
                if self.auto_pull_popular:
                    await self._auto_pull_popular_models()
                
                return self._discovered_models.copy()
                
            except Exception as e:
                self.logger.error("Erreur refresh modèles", error=str(e))
                return self._discovered_models
    
    async def _auto_pull_popular_models(self):
        """Télécharge automatiquement les modèles populaires manquants."""
        try:
            for model_type in self.popular_models:
                discovery_info = self._discovered_models.get(model_type)
                
                if (discovery_info and 
                    discovery_info.status == ModelStatus.UNAVAILABLE and 
                    discovery_info.error_message is None):
                    
                    self.logger.info("Auto-pull modèle populaire", model=model_type.value)
                    success = await self.pull_model(model_type)
                    
                    if success:
                        self.logger.info("Modèle populaire téléchargé", model=model_type.value)
                    else:
                        self.logger.warning("Échec téléchargement modèle populaire", model=model_type.value)
        
        except Exception as e:
            self.logger.error("Erreur auto-pull modèles populaires", error=str(e))
    
    async def pull_model(self, model_type: ModelType) -> bool:
        """Télécharge un modèle spécifique."""
        if not self.ollama_provider or not ModelUtils.is_ollama_model(model_type):
            return False
        
        try:
            # Met à jour le statut
            if model_type in self._discovered_models:
                self._discovered_models[model_type].status = ModelStatus.DOWNLOADING
                self._discovered_models[model_type].download_progress = 0.0
            
            self.logger.info("Début téléchargement modèle", model=model_type.value)
            
            success = await self.ollama_provider.pull_model(model_type.value)
            
            if success:
                # Refresh pour mettre à jour les infos
                await self.refresh_models()
                return True
            else:
                # Marque comme erreur
                if model_type in self._discovered_models:
                    self._discovered_models[model_type].status = ModelStatus.ERROR
                    self._discovered_models[model_type].error_message = "Échec téléchargement"
                return False
        
        except Exception as e:
            self.logger.error("Erreur téléchargement modèle", model=model_type.value, error=str(e))
            if model_type in self._discovered_models:
                self._discovered_models[model_type].status = ModelStatus.ERROR
                self._discovered_models[model_type].error_message = str(e)
            return False
    
    def get_available_models(self) -> List[ModelType]:
        """Retourne la liste des modèles disponibles."""
        return [
            model_type for model_type, info in self._discovered_models.items()
            if info.is_available
        ]
    
    def get_recommended_models_for_task(self, task_type: str) -> List[ModelType]:
        """Recommande des modèles disponibles pour une tâche."""
        recommended = ModelUtils.get_recommended_models_for_task(task_type)
        available = self.get_available_models()
        
        # Retourne les modèles recommandés qui sont disponibles
        return [model for model in recommended if model in available]
    
    def get_model_info(self, model_type: ModelType) -> Optional[ModelDiscoveryInfo]:
        """Retourne les informations sur un modèle."""
        return self._discovered_models.get(model_type)
    
    def is_model_available(self, model_type: ModelType) -> bool:
        """Vérifie si un modèle est disponible."""
        info = self.get_model_info(model_type)
        return info is not None and info.is_available
    
    def get_models_by_size_category(self, size_category: str) -> List[ModelType]:
        """Retourne les modèles disponibles par catégorie de taille."""
        return [
            model_type for model_type, info in self._discovered_models.items()
            if info.is_available and info.size_category == size_category
        ]
    
    def get_models_summary(self) -> Dict[str, Any]:
        """Retourne un résumé des modèles découverts."""
        available = [info for info in self._discovered_models.values() if info.is_available]
        downloading = [info for info in self._discovered_models.values() if info.status == ModelStatus.DOWNLOADING]
        
        total_size = sum(info.size_gb for info in available if info.size_gb)
        
        return {
            "total_models": len(self._discovered_models),
            "available_models": len(available),
            "downloading_models": len(downloading),
            "total_size_gb": round(total_size, 2),
            "last_refresh": self._last_refresh.isoformat() if self._last_refresh else None,
            "popular_models_available": [
                model.value for model in self.popular_models 
                if self.is_model_available(model)
            ]
        }
    
    async def shutdown(self):
        """Arrête le service de découverte."""
        if self._auto_refresh_task:
            self._auto_refresh_task.cancel()
            try:
                await self._auto_refresh_task
            except asyncio.CancelledError:
                pass
        
        if self.ollama_provider:
            await self.ollama_provider.close()
        
        self.logger.info("Service de découverte arrêté")


# Instance globale du service (singleton)
_discovery_service: Optional[ModelDiscoveryService] = None


async def get_discovery_service() -> Optional[ModelDiscoveryService]:
    """Retourne l'instance globale du service de découverte."""
    return _discovery_service


async def initialize_discovery_service(
    ollama_config: Optional[OllamaConfig] = None,
    **kwargs
) -> bool:
    """Initialise le service de découverte global."""
    global _discovery_service
    
    if _discovery_service is None:
        _discovery_service = ModelDiscoveryService(**kwargs)
    
    return await _discovery_service.initialize(ollama_config)


async def shutdown_discovery_service():
    """Arrête le service de découverte global."""
    global _discovery_service
    
    if _discovery_service:
        await _discovery_service.shutdown()
        _discovery_service = None