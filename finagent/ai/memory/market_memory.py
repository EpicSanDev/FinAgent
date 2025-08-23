"""
Gestionnaire de mémoire des données de marché.
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
    MarketMemory, MemorySearchQuery, MemorySearchResult, 
    MemoryEntry, MemoryType, MemoryPersistenceConfig, MemoryRetentionPolicy
)
from ...core.errors.exceptions import FinAgentError

logger = structlog.get_logger(__name__)


class MarketMemoryError(FinAgentError):
    """Erreur liée à la mémoire des données de marché."""
    pass


class MarketMemoryManager:
    """
    Gestionnaire de mémoire pour les données de marché.
    
    Stocke et indexe les données de marché historiques pour permettre
    une analyse contextuelle et des prédictions basées sur l'historique.
    """
    
    def __init__(
        self,
        persistence_config: Optional[MemoryPersistenceConfig] = None,
        retention_policy: Optional[MemoryRetentionPolicy] = None
    ):
        """
        Initialise le gestionnaire de mémoire des données de marché.
        
        Args:
            persistence_config: Configuration de persistence
            retention_policy: Politique de rétention
        """
        self.persistence_config = persistence_config or MemoryPersistenceConfig()
        self.retention_policy = retention_policy or MemoryRetentionPolicy()
        
        # Cache en mémoire organisé par symbole et date
        self._market_cache: Dict[str, Dict[str, MarketMemory]] = {}  # symbol -> date -> data
        self._cache_size_limit = 1000
        self._cache_entry_count = 0
        
        # Index pour recherche rapide
        self._symbol_index: Dict[str, List[str]] = {}  # symbol -> list of memory_ids
        self._date_index: Dict[str, List[str]] = {}    # date -> list of memory_ids
        
        # Base de données SQLite pour persistence
        self.db_path: Optional[Path] = None
        if self.persistence_config.enabled:
            storage_dir = Path(self.persistence_config.storage_path)
            storage_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = storage_dir / "market_data.db"
        
        logger.info(
            "Gestionnaire de mémoire des données de marché initialisé",
            persistence_enabled=self.persistence_config.enabled,
            db_path=str(self.db_path) if self.db_path else None
        )
    
    async def start(self) -> None:
        """Démarre le gestionnaire de mémoire."""
        try:
            if self.persistence_config.enabled and self.db_path:
                await self._init_database()
            
            logger.info("Gestionnaire de mémoire des données de marché démarré")
            
        except Exception as e:
            logger.error("Erreur lors du démarrage", error=str(e))
            raise MarketMemoryError(f"Impossible de démarrer: {e}")
    
    async def stop(self) -> None:
        """Arrête le gestionnaire de mémoire."""
        try:
            self._market_cache.clear()
            self._symbol_index.clear()
            self._date_index.clear()
            self._cache_entry_count = 0
            
            logger.info("Gestionnaire de mémoire des données de marché arrêté")
            
        except Exception as e:
            logger.error("Erreur lors de l'arrêt", error=str(e))
    
    async def store_market_data(
        self,
        market_data: MarketMemory
    ) -> str:
        """
        Stocke des données de marché.
        
        Args:
            market_data: Données de marché à stocker
            
        Returns:
            ID des données stockées
        """
        try:
            # Organiser le cache par symbole et date
            symbol = market_data.symbol
            date_key = market_data.timestamp.strftime("%Y-%m-%d")
            
            if symbol not in self._market_cache:
                self._market_cache[symbol] = {}
            
            # Ajouter au cache si possible
            if self._cache_entry_count < self._cache_size_limit:
                self._market_cache[symbol][date_key] = market_data
                self._cache_entry_count += 1
                
                # Mettre à jour les index
                self._update_symbol_index(symbol, market_data.memory_id)
                self._update_date_index(date_key, market_data.memory_id)
            
            # Sauvegarder en base si persistence activée
            if self.persistence_config.enabled and self.db_path:
                await self._save_market_data_to_db(market_data)
            
            logger.debug(
                "Données de marché stockées",
                memory_id=market_data.memory_id,
                symbol=market_data.symbol,
                timestamp=market_data.timestamp
            )
            
            return market_data.memory_id
            
        except Exception as e:
            logger.error(
                "Erreur lors du stockage des données de marché",
                memory_id=market_data.memory_id,
                symbol=market_data.symbol,
                error=str(e)
            )
            raise MarketMemoryError(f"Impossible de stocker les données de marché: {e}")
    
    async def get_market_data(
        self,
        memory_id: str
    ) -> Optional[MarketMemory]:
        """
        Récupère des données de marché par ID.
        
        Args:
            memory_id: ID des données de marché
            
        Returns:
            Données de marché ou None si non trouvées
        """
        try:
            # Rechercher dans le cache
            for symbol_cache in self._market_cache.values():
                for market_data in symbol_cache.values():
                    if market_data.memory_id == memory_id:
                        logger.debug("Données de marché récupérées depuis le cache", memory_id=memory_id)
                        return market_data
            
            # Charger depuis la base si persistence activée
            if self.persistence_config.enabled and self.db_path:
                market_data = await self._load_market_data_from_db(memory_id)
                if market_data:
                    # Ajouter au cache si possible
                    if self._cache_entry_count < self._cache_size_limit:
                        symbol = market_data.symbol
                        date_key = market_data.timestamp.strftime("%Y-%m-%d")
                        
                        if symbol not in self._market_cache:
                            self._market_cache[symbol] = {}
                        
                        self._market_cache[symbol][date_key] = market_data
                        self._cache_entry_count += 1
                        
                        self._update_symbol_index(symbol, memory_id)
                        self._update_date_index(date_key, memory_id)
                
                return market_data
            
            return None
            
        except Exception as e:
            logger.error(
                "Erreur lors de la récupération des données de marché",
                memory_id=memory_id,
                error=str(e)
            )
            return None
    
    async def get_market_data_by_symbol(
        self,
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[MarketMemory]:
        """
        Récupère les données de marché pour un symbole donné.
        
        Args:
            symbol: Symbole financier
            start_date: Date de début (optionnelle)
            end_date: Date de fin (optionnelle)
            limit: Limite du nombre de résultats
            
        Returns:
            Liste des données de marché
        """
        try:
            results = []
            
            # Rechercher dans le cache
            if symbol in self._market_cache:
                for date_key, market_data in self._market_cache[symbol].items():
                    # Filtrer par dates si spécifiées
                    if start_date and market_data.timestamp < start_date:
                        continue
                    if end_date and market_data.timestamp > end_date:
                        continue
                    
                    results.append(market_data)
            
            # Rechercher en base si persistence activée
            if self.persistence_config.enabled and self.db_path:
                db_results = await self._load_market_data_by_symbol_from_db(
                    symbol, start_date, end_date, limit
                )
                
                # Éviter les doublons avec le cache
                cache_ids = {data.memory_id for data in results}
                for data in db_results:
                    if data.memory_id not in cache_ids:
                        results.append(data)
            
            # Trier par timestamp
            results.sort(key=lambda x: x.timestamp, reverse=True)
            
            # Appliquer la limite
            if limit:
                results = results[:limit]
            
            logger.debug(
                "Données de marché récupérées par symbole",
                symbol=symbol,
                count=len(results)
            )
            
            return results
            
        except Exception as e:
            logger.error(
                "Erreur lors de la récupération par symbole",
                symbol=symbol,
                error=str(e)
            )
            return []
    
    async def search_market_data(
        self,
        query: MemorySearchQuery
    ) -> List[MemorySearchResult]:
        """
        Recherche dans les données de marché.
        
        Args:
            query: Requête de recherche
            
        Returns:
            Liste des résultats
        """
        try:
            results = []
            
            # Rechercher dans le cache
            for symbol, symbol_cache in self._market_cache.items():
                for market_data in symbol_cache.values():
                    if self._matches_query(market_data, query):
                        score = self._calculate_relevance_score(market_data, query)
                        
                        memory_entry = MemoryEntry(
                            id=market_data.memory_id,
                            memory_type=MemoryType.MARKET_DATA,
                            content=market_data,
                            metadata={
                                "symbol": market_data.symbol,
                                "price": market_data.price,
                                "volume": market_data.volume,
                                "market_cap": getattr(market_data, 'market_cap', None)
                            },
                            created_at=market_data.timestamp
                        )
                        
                        results.append(MemorySearchResult(
                            memory_entry=memory_entry,
                            relevance_score=score,
                            match_highlights=self._get_match_highlights(market_data, query)
                        ))
            
            # Rechercher en base si persistence activée
            if self.persistence_config.enabled and self.db_path:
                db_results = await self._search_market_data_in_db(query)
                
                # Éviter les doublons avec le cache
                cache_ids = {result.memory_entry.id for result in results}
                for result in db_results:
                    if result.memory_entry.id not in cache_ids:
                        results.append(result)
            
            # Trier par score de pertinence
            results.sort(key=lambda r: -r.relevance_score)
            
            # Appliquer la limite
            if query.limit:
                results = results[:query.limit]
            
            logger.debug(
                "Recherche de données de marché effectuée",
                query_text=query.text_query,
                results_count=len(results)
            )
            
            return results
            
        except Exception as e:
            logger.error("Erreur lors de la recherche", error=str(e))
            return []
    
    async def delete_market_data(
        self,
        memory_id: str
    ) -> bool:
        """
        Supprime des données de marché.
        
        Args:
            memory_id: ID des données de marché
            
        Returns:
            True si supprimées avec succès
        """
        try:
            # Supprimer du cache
            deleted_from_cache = False
            for symbol, symbol_cache in self._market_cache.items():
                for date_key, market_data in list(symbol_cache.items()):
                    if market_data.memory_id == memory_id:
                        del symbol_cache[date_key]
                        self._cache_entry_count -= 1
                        deleted_from_cache = True
                        
                        # Mettre à jour les index
                        self._remove_from_symbol_index(symbol, memory_id)
                        self._remove_from_date_index(date_key, memory_id)
                        break
                
                if deleted_from_cache:
                    break
            
            # Supprimer de la base si persistence activée
            if self.persistence_config.enabled and self.db_path:
                await self._delete_market_data_from_db(memory_id)
            
            logger.debug("Données de marché supprimées", memory_id=memory_id)
            return True
            
        except Exception as e:
            logger.error(
                "Erreur lors de la suppression",
                memory_id=memory_id,
                error=str(e)
            )
            return False
    
    async def cleanup_expired(self) -> int:
        """
        Nettoie les données de marché expirées.
        
        Returns:
            Nombre d'entrées supprimées
        """
        try:
            deleted_count = 0
            cutoff_time = datetime.utcnow() - timedelta(
                days=self.retention_policy.market_data_retention_days
            )
            
            # Nettoyer le cache
            for symbol, symbol_cache in list(self._market_cache.items()):
                expired_dates = []
                for date_key, market_data in symbol_cache.items():
                    if market_data.timestamp < cutoff_time:
                        expired_dates.append(date_key)
                        deleted_count += 1
                        
                        # Mettre à jour les index
                        self._remove_from_symbol_index(symbol, market_data.memory_id)
                        self._remove_from_date_index(date_key, market_data.memory_id)
                
                for date_key in expired_dates:
                    del symbol_cache[date_key]
                    self._cache_entry_count -= 1
                
                # Supprimer le symbole s'il n'a plus de données
                if not symbol_cache:
                    del self._market_cache[symbol]
            
            # Nettoyer la base si persistence activée
            if self.persistence_config.enabled and self.db_path:
                db_deleted = await self._cleanup_expired_market_data_in_db(cutoff_time)
                deleted_count += db_deleted
            
            logger.info("Nettoyage des données de marché expirées", deleted_count=deleted_count)
            return deleted_count
            
        except Exception as e:
            logger.error("Erreur lors du nettoyage", error=str(e))
            return 0
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Retourne les statistiques des données de marché.
        
        Returns:
            Dictionnaire des statistiques
        """
        try:
            cache_count = self._cache_entry_count
            db_count = 0
            
            if self.persistence_config.enabled and self.db_path:
                db_count = await self._get_db_market_data_count()
            
            unique_symbols = len(self._market_cache)
            
            return {
                "count": max(cache_count, db_count),
                "cache_count": cache_count,
                "db_count": db_count,
                "unique_symbols": unique_symbols,
                "cache_limit": self._cache_size_limit
            }
            
        except Exception as e:
            logger.error("Erreur lors de la récupération des stats", error=str(e))
            return {"count": 0}
    
    def _update_symbol_index(self, symbol: str, memory_id: str) -> None:
        """Met à jour l'index par symbole."""
        if symbol not in self._symbol_index:
            self._symbol_index[symbol] = []
        if memory_id not in self._symbol_index[symbol]:
            self._symbol_index[symbol].append(memory_id)
    
    def _update_date_index(self, date_key: str, memory_id: str) -> None:
        """Met à jour l'index par date."""
        if date_key not in self._date_index:
            self._date_index[date_key] = []
        if memory_id not in self._date_index[date_key]:
            self._date_index[date_key].append(memory_id)
    
    def _remove_from_symbol_index(self, symbol: str, memory_id: str) -> None:
        """Supprime un élément de l'index par symbole."""
        if symbol in self._symbol_index and memory_id in self._symbol_index[symbol]:
            self._symbol_index[symbol].remove(memory_id)
            if not self._symbol_index[symbol]:
                del self._symbol_index[symbol]
    
    def _remove_from_date_index(self, date_key: str, memory_id: str) -> None:
        """Supprime un élément de l'index par date."""
        if date_key in self._date_index and memory_id in self._date_index[date_key]:
            self._date_index[date_key].remove(memory_id)
            if not self._date_index[date_key]:
                del self._date_index[date_key]
    
    def _matches_query(
        self,
        market_data: MarketMemory,
        query: MemorySearchQuery
    ) -> bool:
        """Vérifie si des données de marché correspondent à la requête."""
        # Vérifier la plage de dates
        if query.start_date and market_data.timestamp < query.start_date:
            return False
        if query.end_date and market_data.timestamp > query.end_date:
            return False
        
        # Vérifier le texte de recherche
        if query.text_query:
            text_lower = query.text_query.lower()
            if text_lower not in market_data.symbol.lower():
                return False
        
        # Vérifier les métadonnées
        if query.metadata_filters:
            for key, value in query.metadata_filters.items():
                if key == "symbol" and value.upper() != market_data.symbol.upper():
                    return False
                elif key == "min_price" and market_data.price < float(value):
                    return False
                elif key == "max_price" and market_data.price > float(value):
                    return False
                elif key == "min_volume" and market_data.volume < float(value):
                    return False
        
        return True
    
    def _calculate_relevance_score(
        self,
        market_data: MarketMemory,
        query: MemorySearchQuery
    ) -> float:
        """Calcule le score de pertinence."""
        score = 0.0
        
        if query.text_query:
            text_lower = query.text_query.lower()
            
            # Score basé sur la correspondance exacte du symbole
            if text_lower == market_data.symbol.lower():
                score += 1.0
            elif text_lower in market_data.symbol.lower():
                score += 0.7
        
        # Score basé sur la fraîcheur des données
        age_days = (datetime.utcnow() - market_data.timestamp).days
        if age_days < 1:
            score += 0.3
        elif age_days < 7:
            score += 0.2
        elif age_days < 30:
            score += 0.1
        
        # Score basé sur le volume (données plus volumineuses = plus importantes)
        if market_data.volume > 1000000:
            score += 0.2
        elif market_data.volume > 100000:
            score += 0.1
        
        return min(score, 1.0)
    
    def _get_match_highlights(
        self,
        market_data: MarketMemory,
        query: MemorySearchQuery
    ) -> List[str]:
        """Génère les surlignages de correspondance."""
        highlights = []
        
        if query.text_query:
            highlights.append(f"Symbol: {market_data.symbol}")
        
        highlights.append(f"Price: ${market_data.price:.2f}")
        highlights.append(f"Volume: {market_data.volume:,.0f}")
        
        if hasattr(market_data, 'market_cap') and market_data.market_cap:
            highlights.append(f"Market Cap: ${market_data.market_cap:,.0f}")
        
        return highlights[:3]  # Limiter à 3 highlights
    
    async def _init_database(self) -> None:
        """Initialise la base de données SQLite."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS market_data (
                    id TEXT PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    price REAL NOT NULL,
                    volume REAL NOT NULL,
                    market_cap REAL,
                    indicators TEXT,
                    sentiment_score REAL,
                    metadata TEXT
                )
            """)
            
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_market_data_symbol 
                ON market_data(symbol)
            """)
            
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_market_data_timestamp 
                ON market_data(timestamp)
            """)
            
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_market_data_symbol_timestamp 
                ON market_data(symbol, timestamp)
            """)
            
            await db.commit()
    
    async def _save_market_data_to_db(
        self,
        market_data: MarketMemory
    ) -> None:
        """Sauvegarde des données de marché en base."""
        indicators_json = json.dumps(market_data.indicators) if market_data.indicators else None
        metadata_json = json.dumps(market_data.metadata) if market_data.metadata else None
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO market_data 
                (id, symbol, timestamp, price, volume, market_cap, indicators, sentiment_score, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                market_data.memory_id,
                market_data.symbol,
                market_data.timestamp.timestamp(),
                market_data.price,
                market_data.volume,
                getattr(market_data, 'market_cap', None),
                indicators_json,
                getattr(market_data, 'sentiment_score', None),
                metadata_json
            ))
            await db.commit()
    
    async def _load_market_data_from_db(
        self,
        memory_id: str
    ) -> Optional[MarketMemory]:
        """Charge des données de marché depuis la base."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT symbol, timestamp, price, volume, market_cap, indicators, sentiment_score, metadata
                FROM market_data WHERE id = ?
            """, (memory_id,)) as cursor:
                row = await cursor.fetchone()
                
                if not row:
                    return None
                
                symbol, timestamp, price, volume, market_cap, indicators_json, sentiment_score, metadata_json = row
                
                indicators = json.loads(indicators_json) if indicators_json else {}
                metadata = json.loads(metadata_json) if metadata_json else {}
                
                return MarketMemory(
                    memory_id=memory_id,
                    symbol=symbol,
                    timestamp=datetime.fromtimestamp(timestamp),
                    price=price,
                    volume=volume,
                    market_cap=market_cap,
                    indicators=indicators,
                    sentiment_score=sentiment_score,
                    metadata=metadata
                )
    
    async def _load_market_data_by_symbol_from_db(
        self,
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[MarketMemory]:
        """Charge les données de marché par symbole depuis la base."""
        results = []
        
        sql = "SELECT id, symbol, timestamp, price, volume, market_cap, indicators, sentiment_score, metadata FROM market_data WHERE symbol = ?"
        params = [symbol]
        
        if start_date:
            sql += " AND timestamp >= ?"
            params.append(start_date.timestamp())
        
        if end_date:
            sql += " AND timestamp <= ?"
            params.append(end_date.timestamp())
        
        sql += " ORDER BY timestamp DESC"
        
        if limit:
            sql += " LIMIT ?"
            params.append(limit)
        
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(sql, params) as cursor:
                async for row in cursor:
                    memory_id, symbol, timestamp, price, volume, market_cap, indicators_json, sentiment_score, metadata_json = row
                    
                    indicators = json.loads(indicators_json) if indicators_json else {}
                    metadata = json.loads(metadata_json) if metadata_json else {}
                    
                    market_data = MarketMemory(
                        memory_id=memory_id,
                        symbol=symbol,
                        timestamp=datetime.fromtimestamp(timestamp),
                        price=price,
                        volume=volume,
                        market_cap=market_cap,
                        indicators=indicators,
                        sentiment_score=sentiment_score,
                        metadata=metadata
                    )
                    
                    results.append(market_data)
        
        return results
    
    async def _search_market_data_in_db(
        self,
        query: MemorySearchQuery
    ) -> List[MemorySearchResult]:
        """Recherche des données de marché en base."""
        results = []
        
        sql = "SELECT id, symbol, timestamp, price, volume, market_cap, indicators, sentiment_score, metadata FROM market_data WHERE 1=1"
        params = []
        
        if query.text_query:
            sql += " AND symbol LIKE ?"
            params.append(f"%{query.text_query}%")
        
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
                    memory_id, symbol, timestamp, price, volume, market_cap, indicators_json, sentiment_score, metadata_json = row
                    
                    indicators = json.loads(indicators_json) if indicators_json else {}
                    metadata = json.loads(metadata_json) if metadata_json else {}
                    
                    market_data = MarketMemory(
                        memory_id=memory_id,
                        symbol=symbol,
                        timestamp=datetime.fromtimestamp(timestamp),
                        price=price,
                        volume=volume,
                        market_cap=market_cap,
                        indicators=indicators,
                        sentiment_score=sentiment_score,
                        metadata=metadata
                    )
                    
                    score = self._calculate_relevance_score(market_data, query)
                    
                    memory_entry = MemoryEntry(
                        id=memory_id,
                        memory_type=MemoryType.MARKET_DATA,
                        content=market_data,
                        metadata={
                            "symbol": symbol,
                            "price": price,
                            "volume": volume,
                            "market_cap": market_cap
                        },
                        created_at=datetime.fromtimestamp(timestamp)
                    )
                    
                    results.append(MemorySearchResult(
                        memory_entry=memory_entry,
                        relevance_score=score,
                        match_highlights=self._get_match_highlights(market_data, query)
                    ))
        
        return results
    
    async def _delete_market_data_from_db(
        self,
        memory_id: str
    ) -> None:
        """Supprime des données de marché de la base."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM market_data WHERE id = ?", (memory_id,))
            await db.commit()
    
    async def _cleanup_expired_market_data_in_db(
        self,
        cutoff_time: datetime
    ) -> int:
        """Nettoie les données de marché expirées en base."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "DELETE FROM market_data WHERE timestamp < ?",
                (cutoff_time.timestamp(),)
            )
            await db.commit()
            return cursor.rowcount
    
    async def _get_db_market_data_count(self) -> int:
        """Retourne le nombre de données de marché en base."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT COUNT(*) FROM market_data") as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0