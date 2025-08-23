"""
Configuration pour les services AI avec support multi-providers.
"""

import os
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum

from .models.base import ModelType, ProviderType


class FallbackStrategy(str, Enum):
    """Stratégies de fallback entre providers."""
    NONE = "none"  # Pas de fallback
    CLAUDE_TO_OLLAMA = "claude_to_ollama"  # Claude puis Ollama
    OLLAMA_TO_CLAUDE = "ollama_to_claude"  # Ollama puis Claude
    AUTO = "auto"  # Sélection automatique basée sur disponibilité


@dataclass
class ClaudeConfig:
    """Configuration pour Claude via OpenRouter."""
    api_key: str = field(default_factory=lambda: os.getenv("OPENROUTER_API_KEY", ""))
    base_url: str = "https://openrouter.ai/api/v1"
    default_model: ModelType = ModelType.CLAUDE_3_5_SONNET
    max_tokens: int = 4000
    temperature: float = 0.7
    timeout: int = 60
    max_retries: int = 3
    retry_delay: float = 1.0
    
    def validate(self) -> bool:
        """Valide la configuration Claude."""
        return bool(self.api_key and self.base_url)


@dataclass
class OllamaConfig:
    """Configuration pour Ollama local."""
    host: str = "localhost"
    port: int = 11434
    default_model: ModelType = ModelType.LLAMA3_1_8B
    timeout: int = 120
    max_retries: int = 3
    retry_delay: float = 2.0
    auto_pull: bool = True
    stream: bool = False
    
    @property
    def base_url(self) -> str:
        """URL de base pour Ollama."""
        return f"http://{self.host}:{self.port}"
    
    def validate(self) -> bool:
        """Valide la configuration Ollama."""
        return bool(self.host and 1 <= self.port <= 65535)


@dataclass
class ProviderPriority:
    """Priorité et configuration d'un provider."""
    provider_type: ProviderType
    priority: int = 100  # Plus bas = priorité plus haute
    enabled: bool = True
    fallback_enabled: bool = True
    models: List[ModelType] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.models:
            # Modèles par défaut selon le provider
            if self.provider_type == ProviderType.CLAUDE:
                self.models = [
                    ModelType.CLAUDE_3_5_SONNET,
                    ModelType.CLAUDE_3_5_HAIKU,
                    ModelType.CLAUDE_3_OPUS
                ]
            elif self.provider_type == ProviderType.OLLAMA:
                self.models = [
                    ModelType.LLAMA3_1_8B,
                    ModelType.MISTRAL_7B,
                    ModelType.GEMMA_7B,
                    ModelType.CODELLAMA_7B
                ]


@dataclass
class AIConfig:
    """Configuration complète pour les services AI."""
    # Configurations des providers
    claude: ClaudeConfig = field(default_factory=ClaudeConfig)
    ollama: OllamaConfig = field(default_factory=OllamaConfig)
    
    # Stratégie de fallback
    fallback_strategy: FallbackStrategy = FallbackStrategy.AUTO
    
    # Priorités des providers
    provider_priorities: List[ProviderPriority] = field(default_factory=list)
    
    # Provider préféré par défaut
    preferred_provider: Optional[ProviderType] = None
    
    # Modèle par défaut global
    default_model: Optional[ModelType] = None
    
    # Options globales
    enable_auto_discovery: bool = True
    discovery_refresh_interval: int = 300  # 5 minutes
    
    # Mapping tâche -> modèles recommandés
    task_model_mapping: Dict[str, List[ModelType]] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialisation post-création."""
        if not self.provider_priorities:
            self.provider_priorities = [
                ProviderPriority(
                    provider_type=ProviderType.CLAUDE,
                    priority=10,
                    enabled=self.claude.validate()
                ),
                ProviderPriority(
                    provider_type=ProviderType.OLLAMA,
                    priority=20,
                    enabled=True  # Toujours activé, sera vérifié à l'exécution
                )
            ]
        
        # Mapping par défaut des tâches
        if not self.task_model_mapping:
            self.task_model_mapping = {
                "coding": [
                    ModelType.CLAUDE_3_5_SONNET,
                    ModelType.CODELLAMA_7B,
                    ModelType.CODELLAMA_13B,
                    ModelType.LLAMA3_1_8B
                ],
                "analysis": [
                    ModelType.CLAUDE_3_5_SONNET,
                    ModelType.CLAUDE_3_OPUS,
                    ModelType.LLAMA3_1_8B,
                    ModelType.MISTRAL_7B
                ],
                "conversation": [
                    ModelType.CLAUDE_3_5_HAIKU,
                    ModelType.LLAMA3_1_8B,
                    ModelType.GEMMA_7B,
                    ModelType.MISTRAL_7B
                ],
                "translation": [
                    ModelType.CLAUDE_3_5_SONNET,
                    ModelType.LLAMA3_1_8B,
                    ModelType.MISTRAL_7B
                ],
                "summarization": [
                    ModelType.CLAUDE_3_5_HAIKU,
                    ModelType.LLAMA3_1_8B,
                    ModelType.MISTRAL_7B,
                    ModelType.GEMMA_7B
                ]
            }
    
    def get_provider_config(self, provider_type: ProviderType) -> Union[ClaudeConfig, OllamaConfig, None]:
        """Retourne la configuration d'un provider."""
        if provider_type == ProviderType.CLAUDE:
            return self.claude
        elif provider_type == ProviderType.OLLAMA:
            return self.ollama
        return None
    
    def get_enabled_providers(self) -> List[ProviderType]:
        """Retourne la liste des providers activés."""
        return [
            priority.provider_type 
            for priority in self.provider_priorities
            if priority.enabled
        ]
    
    def get_providers_by_priority(self) -> List[ProviderType]:
        """Retourne les providers triés par priorité."""
        enabled_priorities = [p for p in self.provider_priorities if p.enabled]
        enabled_priorities.sort(key=lambda x: x.priority)
        return [p.provider_type for p in enabled_priorities]
    
    def get_fallback_providers(self, primary_provider: ProviderType) -> List[ProviderType]:
        """Retourne les providers de fallback pour un provider primaire."""
        if self.fallback_strategy == FallbackStrategy.NONE:
            return []
        
        all_providers = self.get_providers_by_priority()
        
        if self.fallback_strategy == FallbackStrategy.CLAUDE_TO_OLLAMA:
            if primary_provider == ProviderType.CLAUDE:
                return [ProviderType.OLLAMA] if ProviderType.OLLAMA in all_providers else []
            return []
        
        elif self.fallback_strategy == FallbackStrategy.OLLAMA_TO_CLAUDE:
            if primary_provider == ProviderType.OLLAMA:
                return [ProviderType.CLAUDE] if ProviderType.CLAUDE in all_providers else []
            return []
        
        elif self.fallback_strategy == FallbackStrategy.AUTO:
            # Retourne tous les autres providers disponibles
            return [p for p in all_providers if p != primary_provider]
        
        return []
    
    def get_recommended_models_for_task(self, task_type: str) -> List[ModelType]:
        """Retourne les modèles recommandés pour une tâche."""
        return self.task_model_mapping.get(task_type, [])
    
    def validate(self) -> Dict[str, Any]:
        """Valide la configuration et retourne un rapport."""
        validation_report = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "providers": {}
        }
        
        # Valide Claude
        claude_valid = self.claude.validate()
        validation_report["providers"]["claude"] = {
            "valid": claude_valid,
            "available": claude_valid
        }
        
        if not claude_valid:
            validation_report["warnings"].append(
                "Configuration Claude invalide - API key manquante"
            )
        
        # Valide Ollama
        ollama_valid = self.ollama.validate()
        validation_report["providers"]["ollama"] = {
            "valid": ollama_valid,
            "available": False  # Sera vérifié à l'exécution
        }
        
        if not ollama_valid:
            validation_report["errors"].append(
                "Configuration Ollama invalide - host/port incorrects"
            )
            validation_report["valid"] = False
        
        # Vérifie qu'au moins un provider est configuré
        if not claude_valid and not ollama_valid:
            validation_report["errors"].append(
                "Aucun provider AI configuré correctement"
            )
            validation_report["valid"] = False
        
        return validation_report


def create_ai_config_from_env() -> AIConfig:
    """Crée une configuration AI à partir des variables d'environnement."""
    claude_config = ClaudeConfig(
        api_key=os.getenv("OPENROUTER_API_KEY", ""),
        base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        default_model=ModelType(os.getenv("CLAUDE_DEFAULT_MODEL", ModelType.CLAUDE_3_5_SONNET.value)),
        max_tokens=int(os.getenv("CLAUDE_MAX_TOKENS", "4000")),
        temperature=float(os.getenv("CLAUDE_TEMPERATURE", "0.7")),
        timeout=int(os.getenv("CLAUDE_TIMEOUT", "60"))
    )
    
    ollama_config = OllamaConfig(
        host=os.getenv("OLLAMA_HOST", "localhost"),
        port=int(os.getenv("OLLAMA_PORT", "11434")),
        default_model=ModelType(os.getenv("OLLAMA_DEFAULT_MODEL", ModelType.LLAMA3_1_8B.value)),
        timeout=int(os.getenv("OLLAMA_TIMEOUT", "120")),
        auto_pull=os.getenv("OLLAMA_AUTO_PULL", "true").lower() == "true"
    )
    
    fallback_strategy = FallbackStrategy(
        os.getenv("AI_FALLBACK_STRATEGY", FallbackStrategy.AUTO.value)
    )
    
    preferred_provider = None
    if pref_env := os.getenv("AI_PREFERRED_PROVIDER"):
        try:
            preferred_provider = ProviderType(pref_env)
        except ValueError:
            pass
    
    return AIConfig(
        claude=claude_config,
        ollama=ollama_config,
        fallback_strategy=fallback_strategy,
        preferred_provider=preferred_provider,
        enable_auto_discovery=os.getenv("AI_ENABLE_AUTO_DISCOVERY", "true").lower() == "true",
        discovery_refresh_interval=int(os.getenv("AI_DISCOVERY_REFRESH_INTERVAL", "300"))
    )


# Instance globale de configuration
_ai_config: Optional[AIConfig] = None


def get_ai_config() -> AIConfig:
    """Retourne l'instance globale de configuration AI."""
    global _ai_config
    if _ai_config is None:
        _ai_config = create_ai_config_from_env()
    return _ai_config


def set_ai_config(config: AIConfig):
    """Définit l'instance globale de configuration AI."""
    global _ai_config
    _ai_config = config