"""
Gestionnaire de mémoire des conversations.
"""

import asyncio
import json
import structlog
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
import sqlite3
import aiosqlite

from ..models.memory import (
    ConversationMemory, ConversationMessage, MemorySearchQuery, 
    MemorySearchResult, MemoryEntry, MemoryType,
    MemoryPersistenceConfig, MemoryRetentionPolicy
)
from ...core.errors.exceptions import FinAgentError

logger = structlog.get_logger(__name__)


class ConversationMemoryError(FinAgentError):
    """Erreur liée à la mémoire des conversations."""
    pass


class ConversationMemoryManager:
    """
    Gestionnaire de mémoire pour les conversations avec l'IA.
    
    Stocke et indexe les conversations pour permettre un contexte persistant
    et une recherche dans l'historique des échanges.
    """
    
    def __init__(
        self,
        persistence_config: Optional[MemoryPersistenceConfig] = None,
        retention_policy: Optional[MemoryRetentionPolicy] = None
    ):
        """
        Initialise le gestionnaire de mémoire des conversations.
        
        Args:
            persistence_config: Configuration de persistence
            retention_policy: Politique de rétention
        """
        self.persistence_config = persistence_config or MemoryPersistenceConfig()
        self.retention_policy = retention_policy or MemoryRetentionPolicy()
        
        # Cache en mémoire pour accès rapide
        self._conversation_cache: Dict[str, ConversationMemory] = {}
        self._cache_size_limit = 500
        
        # Base de données SQLite pour persistence
        self.db_path: Optional[Path] = None
        if self.persistence_config.enabled:
            storage_dir = Path(self.persistence_config.storage_path)
            storage_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = storage_dir / "conversations.db"
        
        logger.info(
            "Gestionnaire de mémoire des conversations initialisé",
            persistence_enabled=self.persistence_config.enabled,
            db_path=str(self.db_path) if self.db_path else None
        )
    
    async def start(self) -> None:
        """Démarre le gestionnaire de mémoire."""
        try:
            if self.persistence_config.enabled and self.db_path:
                await self._init_database()
            
            logger.info("Gestionnaire de mémoire des conversations démarré")
            
        except Exception as e:
            logger.error("Erreur lors du démarrage", error=str(e))
            raise ConversationMemoryError(f"Impossible de démarrer: {e}")
    
    async def stop(self) -> None:
        """Arrête le gestionnaire de mémoire."""
        try:
            self._conversation_cache.clear()
            logger.info("Gestionnaire de mémoire des conversations arrêté")
            
        except Exception as e:
            logger.error("Erreur lors de l'arrêt", error=str(e))
    
    async def store_conversation(
        self,
        conversation: ConversationMemory
    ) -> str:
        """
        Stocke une conversation.
        
        Args:
            conversation: Conversation à stocker
            
        Returns:
            ID de la conversation stockée
        """
        try:
            # Ajouter au cache
            if len(self._conversation_cache) < self._cache_size_limit:
                self._conversation_cache[conversation.conversation_id] = conversation
            
            # Sauvegarder en base si persistence activée
            if self.persistence_config.enabled and self.db_path:
                await self._save_conversation_to_db(conversation)
            
            logger.debug(
                "Conversation stockée",
                conversation_id=conversation.conversation_id,
                messages_count=len(conversation.messages)
            )
            
            return conversation.conversation_id
            
        except Exception as e:
            logger.error(
                "Erreur lors du stockage de conversation",
                conversation_id=conversation.conversation_id,
                error=str(e)
            )
            raise ConversationMemoryError(f"Impossible de stocker la conversation: {e}")
    
    async def get_conversation(
        self,
        conversation_id: str
    ) -> Optional[ConversationMemory]:
        """
        Récupère une conversation par son ID.
        
        Args:
            conversation_id: ID de la conversation
            
        Returns:
            Conversation ou None si non trouvée
        """
        try:
            # Vérifier le cache d'abord
            if conversation_id in self._conversation_cache:
                logger.debug("Conversation récupérée depuis le cache", conversation_id=conversation_id)
                return self._conversation_cache[conversation_id]
            
            # Charger depuis la base si persistence activée
            if self.persistence_config.enabled and self.db_path:
                conversation = await self._load_conversation_from_db(conversation_id)
                if conversation and len(self._conversation_cache) < self._cache_size_limit:
                    self._conversation_cache[conversation_id] = conversation
                return conversation
            
            return None
            
        except Exception as e:
            logger.error(
                "Erreur lors de la récupération de conversation",
                conversation_id=conversation_id,
                error=str(e)
            )
            return None
    
    async def add_message_to_conversation(
        self,
        conversation_id: str,
        message: ConversationMessage
    ) -> bool:
        """
        Ajoute un message à une conversation existante.
        
        Args:
            conversation_id: ID de la conversation
            message: Message à ajouter
            
        Returns:
            True si ajouté avec succès
        """
        try:
            # Récupérer la conversation
            conversation = await self.get_conversation(conversation_id)
            if not conversation:
                logger.warning("Conversation non trouvée", conversation_id=conversation_id)
                return False
            
            # Ajouter le message
            conversation.messages.append(message)
            conversation.updated_at = datetime.utcnow()
            
            # Mettre à jour le cache
            self._conversation_cache[conversation_id] = conversation
            
            # Sauvegarder en base si persistence activée
            if self.persistence_config.enabled and self.db_path:
                await self._save_conversation_to_db(conversation)
            
            logger.debug(
                "Message ajouté à la conversation",
                conversation_id=conversation_id,
                message_role=message.role.value
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Erreur lors de l'ajout de message",
                conversation_id=conversation_id,
                error=str(e)
            )
            return False
    
    async def search_conversations(
        self,
        query: MemorySearchQuery
    ) -> List[MemorySearchResult]:
        """
        Recherche dans les conversations.
        
        Args:
            query: Requête de recherche
            
        Returns:
            Liste des résultats
        """
        try:
            results = []
            
            # Rechercher dans le cache
            for conversation in self._conversation_cache.values():
                if self._matches_query(conversation, query):
                    score = self._calculate_relevance_score(conversation, query)
                    
                    memory_entry = MemoryEntry(
                        id=conversation.conversation_id,
                        memory_type=MemoryType.CONVERSATION,
                        content=conversation,
                        metadata={
                            "message_count": len(conversation.messages),
                            "context": conversation.context
                        },
                        created_at=conversation.timestamp
                    )
                    
                    results.append(MemorySearchResult(
                        memory_entry=memory_entry,
                        relevance_score=score,
                        match_highlights=self._get_match_highlights(conversation, query)
                    ))
            
            # Rechercher en base si persistence activée
            if self.persistence_config.enabled and self.db_path:
                db_results = await self._search_conversations_in_db(query)
                
                # Éviter les doublons avec le cache
                cache_ids = {conv.conversation_id for conv in self._conversation_cache.values()}
                for result in db_results:
                    if result.memory_entry.id not in cache_ids:
                        results.append(result)
            
            # Trier par score de pertinence
            results.sort(key=lambda r: -r.relevance_score)
            
            # Appliquer la limite
            if query.limit:
                results = results[:query.limit]
            
            logger.debug(
                "Recherche de conversations effectuée",
                query_text=query.text_query,
                results_count=len(results)
            )
            
            return results
            
        except Exception as e:
            logger.error("Erreur lors de la recherche", error=str(e))
            return []
    
    async def delete_conversation(
        self,
        conversation_id: str
    ) -> bool:
        """
        Supprime une conversation.
        
        Args:
            conversation_id: ID de la conversation
            
        Returns:
            True si supprimée avec succès
        """
        try:
            # Supprimer du cache
            if conversation_id in self._conversation_cache:
                del self._conversation_cache[conversation_id]
            
            # Supprimer de la base si persistence activée
            if self.persistence_config.enabled and self.db_path:
                await self._delete_conversation_from_db(conversation_id)
            
            logger.debug("Conversation supprimée", conversation_id=conversation_id)
            return True
            
        except Exception as e:
            logger.error(
                "Erreur lors de la suppression",
                conversation_id=conversation_id,
                error=str(e)
            )
            return False
    
    async def cleanup_expired(self) -> int:
        """
        Nettoie les conversations expirées.
        
        Returns:
            Nombre de conversations supprimées
        """
        try:
            deleted_count = 0
            cutoff_time = datetime.utcnow() - timedelta(
                days=self.retention_policy.conversation_retention_days
            )
            
            # Nettoyer le cache
            expired_ids = []
            for conv_id, conversation in self._conversation_cache.items():
                if conversation.timestamp < cutoff_time:
                    expired_ids.append(conv_id)
            
            for conv_id in expired_ids:
                del self._conversation_cache[conv_id]
                deleted_count += 1
            
            # Nettoyer la base si persistence activée
            if self.persistence_config.enabled and self.db_path:
                db_deleted = await self._cleanup_expired_conversations_in_db(cutoff_time)
                deleted_count += db_deleted
            
            logger.info("Nettoyage des conversations expirées", deleted_count=deleted_count)
            return deleted_count
            
        except Exception as e:
            logger.error("Erreur lors du nettoyage", error=str(e))
            return 0
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Retourne les statistiques des conversations.
        
        Returns:
            Dictionnaire des statistiques
        """
        try:
            cache_count = len(self._conversation_cache)
            db_count = 0
            
            if self.persistence_config.enabled and self.db_path:
                db_count = await self._get_db_conversation_count()
            
            total_messages = sum(
                len(conv.messages) for conv in self._conversation_cache.values()
            )
            
            return {
                "count": max(cache_count, db_count),
                "cache_count": cache_count,
                "db_count": db_count,
                "total_messages": total_messages,
                "cache_limit": self._cache_size_limit
            }
            
        except Exception as e:
            logger.error("Erreur lors de la récupération des stats", error=str(e))
            return {"count": 0}
    
    def _matches_query(
        self,
        conversation: ConversationMemory,
        query: MemorySearchQuery
    ) -> bool:
        """Vérifie si une conversation correspond à la requête."""
        # Vérifier la plage de dates
        if query.start_date and conversation.timestamp < query.start_date:
            return False
        if query.end_date and conversation.timestamp > query.end_date:
            return False
        
        # Vérifier le texte de recherche
        if query.text_query:
            text_lower = query.text_query.lower()
            
            # Rechercher dans le contexte
            if text_lower in conversation.context.lower():
                return True
            
            # Rechercher dans les messages
            for message in conversation.messages:
                if text_lower in message.content.lower():
                    return True
        
        # Vérifier les métadonnées
        if query.metadata_filters:
            for key, value in query.metadata_filters.items():
                if key == "context" and value.lower() not in conversation.context.lower():
                    return False
        
        return True
    
    def _calculate_relevance_score(
        self,
        conversation: ConversationMemory,
        query: MemorySearchQuery
    ) -> float:
        """Calcule le score de pertinence."""
        score = 0.0
        
        if query.text_query:
            text_lower = query.text_query.lower()
            
            # Score basé sur le contexte
            if text_lower in conversation.context.lower():
                score += 0.5
            
            # Score basé sur les messages
            for message in conversation.messages:
                if text_lower in message.content.lower():
                    score += 0.3
            
            # Bonus pour les correspondances exactes
            if query.text_query in conversation.context:
                score += 0.2
        
        # Score basé sur la fraîcheur
        age_days = (datetime.utcnow() - conversation.timestamp).days
        if age_days < 7:
            score += 0.2
        elif age_days < 30:
            score += 0.1
        
        return min(score, 1.0)
    
    def _get_match_highlights(
        self,
        conversation: ConversationMemory,
        query: MemorySearchQuery
    ) -> List[str]:
        """Génère les surlignages de correspondance."""
        highlights = []
        
        if query.text_query:
            text_lower = query.text_query.lower()
            
            # Highlights dans le contexte
            if text_lower in conversation.context.lower():
                highlights.append(f"Context: {conversation.context}")
            
            # Highlights dans les messages
            for message in conversation.messages:
                if text_lower in message.content.lower():
                    highlights.append(f"{message.role.value}: {message.content[:100]}...")
        
        return highlights[:3]  # Limiter à 3 highlights
    
    async def _init_database(self) -> None:
        """Initialise la base de données SQLite."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    context TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    messages TEXT NOT NULL
                )
            """)
            
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversations_timestamp 
                ON conversations(timestamp)
            """)
            
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversations_context 
                ON conversations(context)
            """)
            
            await db.commit()
    
    async def _save_conversation_to_db(
        self,
        conversation: ConversationMemory
    ) -> None:
        """Sauvegarde une conversation en base."""
        messages_json = json.dumps([
            {
                "role": msg.role.value,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat()
            }
            for msg in conversation.messages
        ])
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO conversations 
                (id, context, timestamp, updated_at, messages)
                VALUES (?, ?, ?, ?, ?)
            """, (
                conversation.conversation_id,
                conversation.context,
                conversation.timestamp.timestamp(),
                conversation.updated_at.timestamp(),
                messages_json
            ))
            await db.commit()
    
    async def _load_conversation_from_db(
        self,
        conversation_id: str
    ) -> Optional[ConversationMemory]:
        """Charge une conversation depuis la base."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT context, timestamp, updated_at, messages
                FROM conversations WHERE id = ?
            """, (conversation_id,)) as cursor:
                row = await cursor.fetchone()
                
                if not row:
                    return None
                
                context, timestamp, updated_at, messages_json = row
                messages_data = json.loads(messages_json)
                
                messages = [
                    ConversationMessage(
                        role=msg["role"],
                        content=msg["content"],
                        timestamp=datetime.fromisoformat(msg["timestamp"])
                    )
                    for msg in messages_data
                ]
                
                return ConversationMemory(
                    conversation_id=conversation_id,
                    context=context,
                    messages=messages,
                    timestamp=datetime.fromtimestamp(timestamp),
                    updated_at=datetime.fromtimestamp(updated_at)
                )
    
    async def _search_conversations_in_db(
        self,
        query: MemorySearchQuery
    ) -> List[MemorySearchResult]:
        """Recherche des conversations en base."""
        results = []
        
        sql = "SELECT id, context, timestamp, updated_at, messages FROM conversations WHERE 1=1"
        params = []
        
        if query.text_query:
            sql += " AND (context LIKE ? OR messages LIKE ?)"
            params.extend([f"%{query.text_query}%", f"%{query.text_query}%"])
        
        if query.start_date:
            sql += " AND timestamp >= ?"
            params.append(query.start_date.timestamp())
        
        if query.end_date:
            sql += " AND timestamp <= ?"
            params.append(query.end_date.timestamp())
        
        sql += " ORDER BY timestamp DESC"
        
        if query.limit:
            sql += " LIMIT ?"
            params.append(query.limit)
        
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(sql, params) as cursor:
                async for row in cursor:
                    conv_id, context, timestamp, updated_at, messages_json = row
                    messages_data = json.loads(messages_json)
                    
                    messages = [
                        ConversationMessage(
                            role=msg["role"],
                            content=msg["content"],
                            timestamp=datetime.fromisoformat(msg["timestamp"])
                        )
                        for msg in messages_data
                    ]
                    
                    conversation = ConversationMemory(
                        conversation_id=conv_id,
                        context=context,
                        messages=messages,
                        timestamp=datetime.fromtimestamp(timestamp),
                        updated_at=datetime.fromtimestamp(updated_at)
                    )
                    
                    score = self._calculate_relevance_score(conversation, query)
                    
                    memory_entry = MemoryEntry(
                        id=conv_id,
                        memory_type=MemoryType.CONVERSATION,
                        content=conversation,
                        metadata={
                            "message_count": len(messages),
                            "context": context
                        },
                        created_at=datetime.fromtimestamp(timestamp)
                    )
                    
                    results.append(MemorySearchResult(
                        memory_entry=memory_entry,
                        relevance_score=score,
                        match_highlights=self._get_match_highlights(conversation, query)
                    ))
        
        return results
    
    async def _delete_conversation_from_db(
        self,
        conversation_id: str
    ) -> None:
        """Supprime une conversation de la base."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
            await db.commit()
    
    async def _cleanup_expired_conversations_in_db(
        self,
        cutoff_time: datetime
    ) -> int:
        """Nettoie les conversations expirées en base."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "DELETE FROM conversations WHERE timestamp < ?",
                (cutoff_time.timestamp(),)
            )
            await db.commit()
            return cursor.rowcount
    
    async def _get_db_conversation_count(self) -> int:
        """Retourne le nombre de conversations en base."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT COUNT(*) FROM conversations") as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0