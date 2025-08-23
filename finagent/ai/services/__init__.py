"""
Services AI pour FinAgent.

Ce module contient tous les services d'intelligence artificielle
pour l'analyse financière, la prise de décision, et autres tâches.
"""

from .analysis_service import AnalysisService
from .decision_service import DecisionService
from .sentiment_service import SentimentService
from .strategy_service import StrategyService
from .model_discovery_service import (
    ModelDiscoveryService, ModelDiscoveryInfo, ModelStatus,
    get_discovery_service, initialize_discovery_service,
    shutdown_discovery_service
)

# Fonctions utilitaires pour créer des services avec les nouveaux providers
from typing import Optional
from ..factory import get_ai_factory, create_ai_provider
from ..models.base import ProviderType, ModelType
from ..prompts.prompt_manager import PromptManager


async def create_analysis_service(
    provider_type: Optional[ProviderType] = None,
    model_type: Optional[ModelType] = None,
    task_type: str = "analysis"
) -> AnalysisService:
    """
    Crée un service d'analyse avec le provider approprié.
    
    Args:
        provider_type: Type de provider à utiliser (optionnel)
        model_type: Type de modèle à utiliser (optionnel)
        task_type: Type de tâche pour la sélection automatique
        
    Returns:
        Service d'analyse configuré
    """
    if provider_type:
        provider = await create_ai_provider(provider_type)
    else:
        provider = await create_ai_provider(task_type=task_type)
    
    prompt_manager = PromptManager()
    default_model = model_type or ModelType.CLAUDE_3_SONNET
    
    return AnalysisService(provider, prompt_manager, default_model)


async def create_decision_service(
    provider_type: Optional[ProviderType] = None,
    model_type: Optional[ModelType] = None,
    task_type: str = "decision"
) -> DecisionService:
    """
    Crée un service de décision avec le provider approprié.
    
    Args:
        provider_type: Type de provider à utiliser (optionnel)
        model_type: Type de modèle à utiliser (optionnel)
        task_type: Type de tâche pour la sélection automatique
        
    Returns:
        Service de décision configuré
    """
    if provider_type:
        provider = await create_ai_provider(provider_type)
    else:
        provider = await create_ai_provider(task_type=task_type)
    
    prompt_manager = PromptManager()
    default_model = model_type or ModelType.CLAUDE_3_5_SONNET
    
    return DecisionService(provider, prompt_manager, default_model)


async def create_sentiment_service(
    provider_type: Optional[ProviderType] = None,
    model_type: Optional[ModelType] = None,
    task_type: str = "sentiment"
) -> SentimentService:
    """
    Crée un service de sentiment avec le provider approprié.
    
    Args:
        provider_type: Type de provider à utiliser (optionnel)
        model_type: Type de modèle à utiliser (optionnel)
        task_type: Type de tâche pour la sélection automatique
        
    Returns:
        Service de sentiment configuré
    """
    if provider_type:
        provider = await create_ai_provider(provider_type)
    else:
        provider = await create_ai_provider(task_type=task_type)
    
    prompt_manager = PromptManager()
    default_model = model_type or ModelType.CLAUDE_3_HAIKU
    
    return SentimentService(provider, prompt_manager, default_model)


async def create_strategy_service(
    provider_type: Optional[ProviderType] = None,
    model_type: Optional[ModelType] = None,
    task_type: str = "strategy"
) -> StrategyService:
    """
    Crée un service de stratégie avec le provider approprié.
    
    Args:
        provider_type: Type de provider à utiliser (optionnel)
        model_type: Type de modèle à utiliser (optionnel)
        task_type: Type de tâche pour la sélection automatique
        
    Returns:
        Service de stratégie configuré
    """
    if provider_type:
        provider = await create_ai_provider(provider_type)
    else:
        provider = await create_ai_provider(task_type=task_type)
    
    prompt_manager = PromptManager()
    default_model = model_type or ModelType.CLAUDE_3_SONNET
    
    return StrategyService(provider, prompt_manager, default_model)


# Fonctions pour obtenir tous les services configurés
async def get_all_services(
    provider_type: Optional[ProviderType] = None
) -> dict[str, object]:
    """
    Crée tous les services AI avec le même provider.
    
    Args:
        provider_type: Type de provider à utiliser pour tous les services
        
    Returns:
        Dictionnaire des services créés
    """
    return {
        "analysis": await create_analysis_service(provider_type),
        "decision": await create_decision_service(provider_type),
        "sentiment": await create_sentiment_service(provider_type),
        "strategy": await create_strategy_service(provider_type),
        "discovery": await get_discovery_service()
    }


# Fonction de santé des services
async def get_services_health() -> dict[str, bool]:
    """
    Vérifie la santé de tous les services AI.
    
    Returns:
        Dictionnaire du statut de santé de chaque service
    """
    health = {}
    
    try:
        # Test du service d'analyse
        analysis_service = await create_analysis_service()
        health["analysis"] = analysis_service is not None
    except Exception:
        health["analysis"] = False
    
    try:
        # Test du service de décision
        decision_service = await create_decision_service()
        health["decision"] = decision_service is not None
    except Exception:
        health["decision"] = False
    
    try:
        # Test du service de sentiment
        sentiment_service = await create_sentiment_service()
        health["sentiment"] = sentiment_service is not None
    except Exception:
        health["sentiment"] = False
    
    try:
        # Test du service de stratégie
        strategy_service = await create_strategy_service()
        health["strategy"] = strategy_service is not None
    except Exception:
        health["strategy"] = False
    
    try:
        # Test du service de discovery
        discovery_service = await get_discovery_service()
        health["discovery"] = discovery_service is not None
    except Exception:
        health["discovery"] = False
    
    return health


__all__ = [
    # Services principaux
    "AnalysisService",
    "DecisionService", 
    "SentimentService",
    "StrategyService",
    
    # Service de discovery
    "ModelDiscoveryService",
    "ModelDiscoveryInfo",
    "ModelStatus",
    "get_discovery_service",
    "initialize_discovery_service",
    "shutdown_discovery_service",
    
    # Fonctions utilitaires
    "create_analysis_service",
    "create_decision_service",
    "create_sentiment_service",
    "create_strategy_service",
    "get_all_services",
    "get_services_health",
]