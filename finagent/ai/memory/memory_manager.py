"""
Gestionnaire principal du système de mémoire IA.
"""

import asyncio
import structlog
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
from pathlib import Path

from ..models.memory import (
    MemoryType, MemoryEntry, ConversationMemory, MarketMemory, 
    DecisionMemory, MemorySearchQuery, MemorySearchResult,
    MemoryPersistenceConfig, MemoryRetentionPolicy
)
from .conversation_memory import ConversationMemoryManager
from .market_memory import MarketMemoryManager  
from .decision_memory import DecisionMemoryManager
from ...core.errors.exceptions import FinAgentError

logger = structlog.get_logger(__name__)


class MemoryError(FinAgentError):
    """Erreur liée au système de mémoire."""
    pass


class MemoryManager:
    """
    Gestionnaire principal du système de mémoire IA.
    
    Coordonne les différents types de mémoire et fournit une interface unifiée
    pour stocker, récupérer et rechercher dans les mémoires.
    """
    
    def __init__(
        self,
        persistence_config: Optional[MemoryPersistenceConfig] = None,
        retention_policy: Optional[MemoryRetentionPolicy] = None
    ):
        """
        Initialise le gestionnaire de mémoire.
        
        Args:
            persistence_config: Configuration de persistence
            retention_policy: Politique de rétention des données
        """
        self.persistence_config = persistence_config or MemoryPersistenceConfig()
        self.retention_policy = retention_policy or MemoryRetentionPolicy()
        
        # Initialiser les gestionnaires de mémoire spécialisés
        self.conversation_manager = ConversationMemoryManager(
            persistence_config=self.persistence_config,
            retention_policy=self.retention_policy
        )
        
        self.market_manager = MarketMemoryManager(
            persistence_config=self.persistence_config,
            retention_policy=self.retention_policy
        )
        
        self.decision_manager = DecisionMemoryManager(
            persistence_config=self.persistence_config,
            retention_policy=self.retention_policy
        )
        
        # Cache en mémoire pour accès rapide
        self._memory_cache: Dict[str, MemoryEntry] = {}
        self._cache_size_limit = 1000
        
        # Tâche de nettoyage périodique
        self._cleanup_task: Optional[asyncio.Task] = None
        
        logger.info(
            "Gestionnaire de mémoire initialisé",
            persistence_enabled=self.persistence_config.enabled,
            retention_days=self.retention_policy.default_retention_days
        )
    
    async def start(self) -> None:
        """Démarre le gestionnaire de mémoire."""
        try:
            # Démarrer les gestionnaires spécialisés
            await self.conversation_manager.start()
            await self.market_manager.start()
            await self.decision_manager.start()
            
            # Démarrer la tâche de nettoyage périodique
            if self.retention_policy.auto_cleanup_enabled:
                self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            
            logger.info("Gestionnaire de mémoire démarré")
            
        except Exception as e:
            logger.error("Erreur lors du démarrage du gestionnaire de mémoire", error=str(e))
            raise MemoryError(f"Impossible de démarrer le gestionnaire de mémoire: {e}")
    
    async def stop(self) -> None:
        """Arrête le gestionnaire de mémoire."""
        try:
            # Arrêter la tâche de nettoyage
            if self._cleanup_task:
                self._cleanup_task.cancel()
                try:
                    await self._cleanup_task
                except asyncio.CancelledError:
                    pass
            
            # Arrêter les gestionnaires spécialisés
            await self.conversation_manager.stop()
            await self.market_manager.stop() 
            await self.decision_manager.stop()
            
            # Vider le cache
            self._memory_cache.clear()
            
            logger.info("Gestionnaire de mémoire arrêté")
            
        except Exception as e:
            logger.error("Erreur lors de l'arrêt du gestionnaire de mémoire", error=str(e))
    
    async def store_memory(
        self,
        memory_type: MemoryType,
        content: Union[ConversationMemory, MarketMemory, DecisionMemory],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Stocke une entrée mémoire.
        
        Args:
            memory_type: Type de mémoire
            content: Contenu à stocker
            metadata: Métadonnées optionnelles
            
        Returns:
            ID de l'entrée mémoire stockée
        """
        try:
            # Déléguer au gestionnaire approprié
            if memory_type == MemoryType.CONVERSATION:
                memory_id = await self.conversation_manager.store_conversation(content)
            elif memory_type == MemoryType.MARKET_DATA:
                memory_id = await self.market_manager.store_market_data(content)
            elif memory_type == MemoryType.DECISION:
                memory_id = await self.decision_manager.store_decision(content)
            else:
                raise MemoryError(f"Type de mémoire non supporté: {memory_type}")
            
            # Créer l'entrée mémoire unifiée
            entry = MemoryEntry(
                id=memory_id,
                memory_type=memory_type,
                content=content,
                metadata=metadata or {},
                created_at=datetime.utcnow()
            )
            
            # Ajouter au cache si possible
            if len(self._memory_cache) < self._cache_size_limit:
                self._memory_cache[memory_id] = entry
            
            logger.debug(
                "Mémoire stockée",
                memory_id=memory_id,
                memory_type=memory_type.value
            )
            
            return memory_id
            
        except Exception as e:
            logger.error(
                "Erreur lors du stockage de la mémoire",
                memory_type=memory_type.value,
                error=str(e)
            )
            raise MemoryError(f"Impossible de stocker la mémoire: {e}")
    
    async def retrieve_memory(
        self,
        memory_id: str,
        memory_type: Optional[MemoryType] = None
    ) -> Optional[MemoryEntry]:
        """
        Récupère une entrée mémoire par son ID.
        
        Args:
            memory_id: ID de l'entrée mémoire
            memory_type: Type de mémoire (optionnel, pour optimisation)
            
        Returns:
            Entrée mémoire ou None si non trouvée
        """
        try:
            # Vérifier le cache d'abord
            if memory_id in self._memory_cache:
                logger.debug("Mémoire récupérée depuis le cache", memory_id=memory_id)
                return self._memory_cache[memory_id]
            
            # Essayer de récupérer depuis les gestionnaires spécialisés
            entry = None
            
            if memory_type == MemoryType.CONVERSATION:
                content = await self.conversation_manager.get_conversation(memory_id)
                if content:
                    entry = MemoryEntry(
                        id=memory_id,
                        memory_type=MemoryType.CONVERSATION,
                        content=content,
                        metadata={},
                        created_at=content.timestamp
                    )
            elif memory_type == MemoryType.MARKET_DATA:
                content = await self.market_manager.get_market_data(memory_id)
                if content:
                    entry = MemoryEntry(
                        id=memory_id,
                        memory_type=MemoryType.MARKET_DATA,
                        content=content,
                        metadata={},
                        created_at=content.timestamp
                    )
            elif memory_type == MemoryType.DECISION:
                content = await self.decision_manager.get_decision(memory_id)
                if content:
                    entry = MemoryEntry(
                        id=memory_id,
                        memory_type=MemoryType.DECISION,
                        content=content,
                        metadata={},
                        created_at=content.timestamp
                    )
            else:
                # Rechercher dans tous les gestionnaires
                for manager_type, manager in [
                    (MemoryType.CONVERSATION, self.conversation_manager),
                    (MemoryType.MARKET_DATA, self.market_manager),
                    (MemoryType.DECISION, self.decision_manager)
                ]:
                    try:
                        if manager_type == MemoryType.CONVERSATION:
                            content = await manager.get_conversation(memory_id)
                        elif manager_type == MemoryType.MARKET_DATA:
                            content = await manager.get_market_data(memory_id)
                        else:
                            content = await manager.get_decision(memory_id)
                        
                        if content:
                            entry = MemoryEntry(
                                id=memory_id,
                                memory_type=manager_type,
                                content=content,
                                metadata={},
                                created_at=getattr(content, 'timestamp', datetime.utcnow())
                            )
                            break
                    except:
                        continue
            
            # Mettre en cache si trouvé
            if entry and len(self._memory_cache) < self._cache_size_limit:
                self._memory_cache[memory_id] = entry
            
            logger.debug(
                "Mémoire récupérée",
                memory_id=memory_id,
                found=entry is not None
            )
            
            return entry
            
        except Exception as e:
            logger.error(
                "Erreur lors de la récupération de la mémoire",
                memory_id=memory_id,
                error=str(e)
            )
            return None
    
    async def search_memories(
        self,
        query: MemorySearchQuery
    ) -> List[MemorySearchResult]:
        """
        Recherche dans les mémoires selon les critères spécifiés.
        
        Args:
            query: Requête de recherche
            
        Returns:
            Liste des résultats de recherche
        """
        try:
            results = []
            
            # Rechercher dans chaque type de mémoire selon les filtres
            if not query.memory_types or MemoryType.CONVERSATION in query.memory_types:
                conversation_results = await self.conversation_manager.search_conversations(query)
                results.extend(conversation_results)
            
            if not query.memory_types or MemoryType.MARKET_DATA in query.memory_types:
                market_results = await self.market_manager.search_market_data(query)
                results.extend(market_results)
            
            if not query.memory_types or MemoryType.DECISION in query.memory_types:
                decision_results = await self.decision_manager.search_decisions(query)
                results.extend(decision_results)
            
            # Trier par score de pertinence puis par date
            results.sort(key=lambda r: (-r.relevance_score, -r.memory_entry.created_at.timestamp()))
            
            # Appliquer la limite
            if query.limit:
                results = results[:query.limit]
            
            logger.debug(
                "Recherche de mémoires effectuée",
                query_text=query.text_query,
                results_count=len(results)
            )
            
            return results
            
        except Exception as e:
            logger.error(
                "Erreur lors de la recherche de mémoires",
                query=query.dict(),
                error=str(e)
            )
            return []
    
    async def delete_memory(
        self,
        memory_id: str,
        memory_type: Optional[MemoryType] = None
    ) -> bool:
        """
        Supprime une entrée mémoire.
        
        Args:
            memory_id: ID de l'entrée mémoire
            memory_type: Type de mémoire (optionnel)
            
        Returns:
            True si supprimé avec succès
        """
        try:
            deleted = False
            
            # Supprimer du cache
            if memory_id in self._memory_cache:
                del self._memory_cache[memory_id]
            
            # Supprimer des gestionnaires appropriés
            if memory_type == MemoryType.CONVERSATION:
                deleted = await self.conversation_manager.delete_conversation(memory_id)
            elif memory_type == MemoryType.MARKET_DATA:
                deleted = await self.market_manager.delete_market_data(memory_id)
            elif memory_type == MemoryType.DECISION:
                deleted = await self.decision_manager.delete_decision(memory_id)
            else:
                # Essayer tous les gestionnaires
                for manager in [self.conversation_manager, self.market_manager, self.decision_manager]:
                    try:
                        if hasattr(manager, 'delete_conversation'):
                            result = await manager.delete_conversation(memory_id)
                        elif hasattr(manager, 'delete_market_data'):
                            result = await manager.delete_market_data(memory_id)
                        else:
                            result = await manager.delete_decision(memory_id)
                        
                        if result:
                            deleted = True
                            break
                    except:
                        continue
            
            logger.debug(
                "Suppression de mémoire",
                memory_id=memory_id,
                deleted=deleted
            )
            
            return deleted
            
        except Exception as e:
            logger.error(
                "Erreur lors de la suppression de mémoire",
                memory_id=memory_id,
                error=str(e)
            )
            return False
    
    async def cleanup_expired_memories(self) -> int:
        """
        Nettoie les mémoires expirées selon la politique de rétention.
        
        Returns:
            Nombre d'entrées supprimées
        """
        try:
            total_deleted = 0
            
            # Nettoyer chaque gestionnaire
            conversation_deleted = await self.conversation_manager.cleanup_expired()
            market_deleted = await self.market_manager.cleanup_expired()
            decision_deleted = await self.decision_manager.cleanup_expired()
            
            total_deleted = conversation_deleted + market_deleted + decision_deleted
            
            # Nettoyer le cache des entrées expirées
            expired_cache_keys = []
            cutoff_time = datetime.utcnow() - timedelta(
                days=self.retention_policy.default_retention_days
            )
            
            for key, entry in self._memory_cache.items():
                if entry.created_at < cutoff_time:
                    expired_cache_keys.append(key)
            
            for key in expired_cache_keys:
                del self._memory_cache[key]
            
            logger.info(
                "Nettoyage des mémoires expirées terminé",
                total_deleted=total_deleted,
                cache_entries_removed=len(expired_cache_keys)
            )
            
            return total_deleted
            
        except Exception as e:
            logger.error("Erreur lors du nettoyage des mémoires", error=str(e))
            return 0
    
    async def get_memory_stats(self) -> Dict[str, Any]:
        """
        Retourne les statistiques du système de mémoire.
        
        Returns:
            Dictionnaire des statistiques
        """
        try:
            conversation_stats = await self.conversation_manager.get_stats()
            market_stats = await self.market_manager.get_stats()
            decision_stats = await self.decision_manager.get_stats()
            
            return {
                "cache_size": len(self._memory_cache),
                "cache_limit": self._cache_size_limit,
                "conversation_memories": conversation_stats,
                "market_memories": market_stats,
                "decision_memories": decision_stats,
                "total_memories": (
                    conversation_stats.get("count", 0) +
                    market_stats.get("count", 0) +
                    decision_stats.get("count", 0)
                ),
                "persistence_enabled": self.persistence_config.enabled,
                "retention_policy": {
                    "default_days": self.retention_policy.default_retention_days,
                    "auto_cleanup": self.retention_policy.auto_cleanup_enabled
                }
            }
            
        except Exception as e:
            logger.error("Erreur lors de la récupération des stats", error=str(e))
            return {}
    
    async def _cleanup_loop(self) -> None:
        """Boucle de nettoyage périodique."""
        while True:
            try:
                await asyncio.sleep(self.retention_policy.cleanup_interval_hours * 3600)
                await self.cleanup_expired_memories()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Erreur dans la boucle de nettoyage", error=str(e))
                await asyncio.sleep(300)  # Attendre 5 minutes avant de réessayer