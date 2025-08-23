"""
Configuration et initialisation du système IA.
"""

import os
import structlog
from typing import Dict, Any, Optional
from pathlib import Path

from .providers.claude_provider import ClaudeProvider
from .services.analysis_service import AnalysisService
from .services.decision_service import DecisionService
from .services.sentiment_service import SentimentService
from .services.strategy_service import StrategyService
from .prompts.prompt_manager import PromptManager
from .memory.memory_manager import MemoryManager
from .models.memory import MemoryPersistenceConfig, MemoryRetentionPolicy
from ..core.config import Config
from ..core.errors.exceptions import FinAgentError

logger = structlog.get_logger(__name__)


class AIConfigError(FinAgentError):
    """Erreur de configuration IA."""
    pass


class AIConfig:
    """
    Configuration centralisée du système IA.
    
    Coordonne l'initialisation et la configuration de tous les composants IA:
    - Provider Claude via OpenRouter
    - Services d'analyse
    - Gestionnaire de prompts
    - Système de mémoire
    """
    
    def __init__(self, config: Config):
        """
        Initialise la configuration IA.
        
        Args:
            config: Configuration principale de l'application
        """
        self.config = config
        self.ai_config = config.get("ai", {})
        
        # Composants IA
        self.provider: Optional[ClaudeProvider] = None
        self.prompt_manager: Optional[PromptManager] = None
        self.memory_manager: Optional[MemoryManager] = None
        
        # Services IA
        self.analysis_service: Optional[AnalysisService] = None
        self.decision_service: Optional[DecisionService] = None
        self.sentiment_service: Optional[SentimentService] = None
        self.strategy_service: Optional[StrategyService] = None
        
        self._initialized = False
        
        logger.info("Configuration IA initialisée")
    
    async def initialize(self) -> None:
        """Initialise tous les composants IA."""
        try:
            if self._initialized:
                logger.warning("Système IA déjà initialisé")
                return
            
            # Valider la configuration
            self._validate_config()
            
            # Initialiser les composants dans l'ordre de dépendance
            await self._initialize_provider()
            await self._initialize_memory_manager()
            await self._initialize_prompt_manager()
            await self._initialize_services()
            
            self._initialized = True
            logger.info("Système IA initialisé avec succès")
            
        except Exception as e:
            logger.error("Erreur lors de l'initialisation du système IA", error=str(e))
            raise AIConfigError(f"Impossible d'initialiser le système IA: {e}")
    
    async def shutdown(self) -> None:
        """Arrête tous les composants IA."""
        try:
            if not self._initialized:
                return
            
            # Arrêter les services
            if self.analysis_service:
                await self.analysis_service.stop()
            if self.decision_service:
                await self.decision_service.stop()
            if self.sentiment_service:
                await self.sentiment_service.stop()
            if self.strategy_service:
                await self.strategy_service.stop()
            
            # Arrêter le gestionnaire de mémoire
            if self.memory_manager:
                await self.memory_manager.stop()
            
            # Arrêter le provider
            if self.provider:
                await self.provider.close()
            
            self._initialized = False
            logger.info("Système IA arrêté")
            
        except Exception as e:
            logger.error("Erreur lors de l'arrêt du système IA", error=str(e))
    
    def get_analysis_service(self) -> AnalysisService:
        """Retourne le service d'analyse."""
        if not self._initialized or not self.analysis_service:
            raise AIConfigError("Service d'analyse non initialisé")
        return self.analysis_service
    
    def get_decision_service(self) -> DecisionService:
        """Retourne le service de décision."""
        if not self._initialized or not self.decision_service:
            raise AIConfigError("Service de décision non initialisé")
        return self.decision_service
    
    def get_sentiment_service(self) -> SentimentService:
        """Retourne le service de sentiment."""
        if not self._initialized or not self.sentiment_service:
            raise AIConfigError("Service de sentiment non initialisé")
        return self.sentiment_service
    
    def get_strategy_service(self) -> StrategyService:
        """Retourne le service de stratégie."""
        if not self._initialized or not self.strategy_service:
            raise AIConfigError("Service de stratégie non initialisé")
        return self.strategy_service
    
    def get_memory_manager(self) -> MemoryManager:
        """Retourne le gestionnaire de mémoire."""
        if not self._initialized or not self.memory_manager:
            raise AIConfigError("Gestionnaire de mémoire non initialisé")
        return self.memory_manager
    
    def get_provider(self) -> ClaudeProvider:
        """Retourne le provider Claude."""
        if not self._initialized or not self.provider:
            raise AIConfigError("Provider Claude non initialisé")
        return self.provider
    
    def _validate_config(self) -> None:
        """Valide la configuration IA."""
        # Vérifier que l'IA est activée
        if not self.ai_config.get("provider", {}).get("enabled", False):
            raise AIConfigError("Le système IA n'est pas activé")
        
        # Vérifier la clé API OpenRouter
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise AIConfigError(
                "Clé API OpenRouter manquante. "
                "Définissez la variable d'environnement OPENROUTER_API_KEY"
            )
        
        # Vérifier la configuration Claude
        claude_config = self.ai_config.get("claude", {})
        if not claude_config:
            raise AIConfigError("Configuration Claude manquante")
        
        # Vérifier les modèles
        models = claude_config.get("models", {})
        if not models.get("default"):
            raise AIConfigError("Modèle Claude par défaut manquant")
        
        logger.debug("Configuration IA validée")
    
    async def _initialize_provider(self) -> None:
        """Initialise le provider Claude."""
        try:
            # Configuration du provider
            claude_config = self.ai_config.get("claude", {})
            rate_limiting_config = self.ai_config.get("rate_limiting", {})
            retry_config = self.ai_config.get("retry", {})
            circuit_breaker_config = self.ai_config.get("circuit_breaker", {})
            
            # Configuration OpenRouter
            openrouter_config = self.config.get("apis", {}).get("openrouter", {})
            
            self.provider = ClaudeProvider(
                api_key=os.getenv("OPENROUTER_API_KEY"),
                base_url=openrouter_config.get("base_url", "https://openrouter.ai/api/v1"),
                default_model=claude_config.get("models", {}).get("default"),
                default_temperature=claude_config.get("temperature", 0.1),
                default_max_tokens=claude_config.get("max_tokens", 4000),
                timeout=openrouter_config.get("timeout", 30),
                rate_limits_per_minute=rate_limiting_config.get("requests_per_minute", 50),
                max_retries=retry_config.get("max_attempts", 3),
                circuit_breaker_enabled=circuit_breaker_config.get("enabled", True),
                circuit_breaker_failure_threshold=circuit_breaker_config.get("failure_threshold", 5)
            )
            
            await self.provider.initialize()
            logger.info("Provider Claude initialisé")
            
        except Exception as e:
            logger.error("Erreur lors de l'initialisation du provider", error=str(e))
            raise AIConfigError(f"Impossible d'initialiser le provider Claude: {e}")
    
    async def _initialize_memory_manager(self) -> None:
        """Initialise le gestionnaire de mémoire."""
        try:
            memory_config = self.ai_config.get("memory", {})
            
            # Configuration de persistence
            persistence_config = MemoryPersistenceConfig(
                enabled=memory_config.get("persistence", {}).get("enabled", True),
                storage_path=memory_config.get("persistence", {}).get("storage_path", "./data/ai_memory")
            )
            
            # Politique de rétention
            retention_config = memory_config.get("retention", {})
            retention_policy = MemoryRetentionPolicy(
                default_retention_days=retention_config.get("default_retention_days", 90),
                conversation_retention_days=retention_config.get("conversation_retention_days", 30),
                market_data_retention_days=retention_config.get("market_data_retention_days", 180),
                decision_retention_days=retention_config.get("decision_retention_days", 365),
                auto_cleanup_enabled=retention_config.get("auto_cleanup_enabled", True),
                cleanup_interval_hours=retention_config.get("cleanup_interval_hours", 24)
            )
            
            self.memory_manager = MemoryManager(
                persistence_config=persistence_config,
                retention_policy=retention_policy
            )
            
            await self.memory_manager.start()
            logger.info("Gestionnaire de mémoire initialisé")
            
        except Exception as e:
            logger.error("Erreur lors de l'initialisation du gestionnaire de mémoire", error=str(e))
            raise AIConfigError(f"Impossible d'initialiser le gestionnaire de mémoire: {e}")
    
    async def _initialize_prompt_manager(self) -> None:
        """Initialise le gestionnaire de prompts."""
        try:
            prompts_config = self.ai_config.get("prompts", {})
            
            # Répertoire des templates de prompts
            templates_dir = prompts_config.get("directory", "./finagent/ai/prompts/templates")
            templates_path = Path(templates_dir)
            
            # Créer le répertoire s'il n'existe pas
            templates_path.mkdir(parents=True, exist_ok=True)
            
            self.prompt_manager = PromptManager(
                templates_directory=templates_path,
                default_context_length=prompts_config.get("context_length", 2000),
                include_history=prompts_config.get("include_history", True)
            )
            
            logger.info("Gestionnaire de prompts initialisé")
            
        except Exception as e:
            logger.error("Erreur lors de l'initialisation du gestionnaire de prompts", error=str(e))
            raise AIConfigError(f"Impossible d'initialiser le gestionnaire de prompts: {e}")
    
    async def _initialize_services(self) -> None:
        """Initialise tous les services IA."""
        try:
            claude_config = self.ai_config.get("claude", {})
            service_configs = claude_config.get("service_configs", {})
            
            # Service d'analyse
            analysis_config = service_configs.get("analysis", {})
            self.analysis_service = AnalysisService(
                provider=self.provider,
                prompt_manager=self.prompt_manager,
                memory_manager=self.memory_manager,
                default_model=analysis_config.get("model"),
                default_temperature=analysis_config.get("temperature", 0.1),
                default_max_tokens=analysis_config.get("max_tokens", 3000)
            )
            
            # Service de décision
            decision_config = service_configs.get("decision", {})
            self.decision_service = DecisionService(
                provider=self.provider,
                prompt_manager=self.prompt_manager,
                memory_manager=self.memory_manager,
                default_model=decision_config.get("model"),
                default_temperature=decision_config.get("temperature", 0.05),
                default_max_tokens=decision_config.get("max_tokens", 2000)
            )
            
            # Service de sentiment
            sentiment_config = service_configs.get("sentiment", {})
            self.sentiment_service = SentimentService(
                provider=self.provider,
                prompt_manager=self.prompt_manager,
                memory_manager=self.memory_manager,
                default_model=sentiment_config.get("model"),
                default_temperature=sentiment_config.get("temperature", 0.2),
                default_max_tokens=sentiment_config.get("max_tokens", 1000)
            )
            
            # Service de stratégie
            strategy_config = service_configs.get("strategy", {})
            self.strategy_service = StrategyService(
                provider=self.provider,
                prompt_manager=self.prompt_manager,
                memory_manager=self.memory_manager,
                default_model=strategy_config.get("model"),
                default_temperature=strategy_config.get("temperature", 0.1),
                default_max_tokens=strategy_config.get("max_tokens", 4000)
            )
            
            logger.info("Services IA initialisés")
            
        except Exception as e:
            logger.error("Erreur lors de l'initialisation des services", error=str(e))
            raise AIConfigError(f"Impossible d'initialiser les services IA: {e}")
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Retourne un résumé de la configuration IA."""
        claude_config = self.ai_config.get("claude", {})
        memory_config = self.ai_config.get("memory", {})
        
        return {
            "provider": {
                "type": "claude",
                "enabled": self.ai_config.get("provider", {}).get("enabled", False),
                "default_model": claude_config.get("models", {}).get("default"),
                "temperature": claude_config.get("temperature", 0.1),
                "max_tokens": claude_config.get("max_tokens", 4000)
            },
            "memory": {
                "enabled": memory_config.get("enabled", True),
                "persistence": memory_config.get("persistence", {}).get("enabled", True),
                "retention_days": memory_config.get("retention", {}).get("default_retention_days", 90)
            },
            "services": {
                "analysis": self.analysis_service is not None,
                "decision": self.decision_service is not None,
                "sentiment": self.sentiment_service is not None,
                "strategy": self.strategy_service is not None
            },
            "initialized": self._initialized
        }


# Instance globale de configuration IA
_ai_config_instance: Optional[AIConfig] = None


def get_ai_config() -> Optional[AIConfig]:
    """Retourne l'instance de configuration IA."""
    return _ai_config_instance


def initialize_ai_config(config: Config) -> AIConfig:
    """
    Initialise la configuration IA globale.
    
    Args:
        config: Configuration principale de l'application
        
    Returns:
        Instance de configuration IA
    """
    global _ai_config_instance
    
    if _ai_config_instance is None:
        _ai_config_instance = AIConfig(config)
    
    return _ai_config_instance


async def initialize_ai_system(config: Config) -> AIConfig:
    """
    Initialise complètement le système IA.
    
    Args:
        config: Configuration principale de l'application
        
    Returns:
        Instance de configuration IA initialisée
    """
    ai_config = initialize_ai_config(config)
    await ai_config.initialize()
    return ai_config


async def shutdown_ai_system() -> None:
    """Arrête le système IA."""
    global _ai_config_instance
    
    if _ai_config_instance:
        await _ai_config_instance.shutdown()
        _ai_config_instance = None