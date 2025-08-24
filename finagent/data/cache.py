"""
Système de cache multi-niveaux pour les données financières.

Ce module fournit un système de cache robuste avec support de TTL,
tags, et invalidation intelligente.
"""

import asyncio
import json
import pickle
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Union
from abc import ABC, abstractmethod
import hashlib
import logging

logger = logging.getLogger(__name__)


class CacheKeys:
    """Générateur de clés de cache standardisées."""
    
    @staticmethod
    def market_data(symbol: str, timeframe: str) -> str:
        """Génère une clé pour les données de marché."""
        return f"market_data:{symbol}:{timeframe}"
    
    @staticmethod
    def quote(symbol: str) -> str:
        """Génère une clé pour une cotation."""
        return f"quote:{symbol}"
    
    @staticmethod
    def news(symbol: str, hours: int = 24) -> str:
        """Génère une clé pour les nouvelles."""
        return f"news:{symbol}:{hours}h"
    
    @staticmethod
    def technical_indicators(symbol: str, timeframe: str, indicators: str) -> str:
        """Génère une clé pour les indicateurs techniques."""
        return f"indicators:{symbol}:{timeframe}:{indicators}"
    
    @staticmethod
    def company_info(symbol: str) -> str:
        """Génère une clé pour les informations d'entreprise."""
        return f"company_info:{symbol}"
    
    @staticmethod
    def historical_data(symbol: str, start: str, end: str, timeframe: str) -> str:
        """Génère une clé pour les données historiques."""
        return f"historical:{symbol}:{start}:{end}:{timeframe}"


class CacheTags:
    """Générateur de tags pour l'invalidation du cache."""
    
    # Tags de base
    REAL_TIME = "real_time"
    HISTORICAL = "historical"
    NEWS = "news"
    INDICATORS = "indicators"
    COMPANY = "company"
    
    @staticmethod
    def symbol(symbol: str) -> str:
        """Tag pour un symbole spécifique."""
        return f"symbol:{symbol}"
    
    @staticmethod
    def timeframe(timeframe: str) -> str:
        """Tag pour un timeframe spécifique."""
        return f"timeframe:{timeframe}"
    
    @staticmethod
    def date(date: str) -> str:
        """Tag pour une date spécifique."""
        return f"date:{date}"
    
    @staticmethod
    def source(source: str) -> str:
        """Tag pour une source de données."""
        return f"source:{source}"


class CacheItem:
    """Élément de cache avec métadonnées."""
    
    def __init__(self, data: Any, ttl: int, tags: Optional[List[str]] = None):
        self.data = data
        self.created_at = time.time()
        self.ttl = ttl
        self.tags = set(tags or [])
        self.access_count = 0
        self.last_accessed = self.created_at
    
    @property
    def is_expired(self) -> bool:
        """Vérifie si l'élément a expiré."""
        return time.time() - self.created_at > self.ttl
    
    @property
    def age_seconds(self) -> int:
        """Âge de l'élément en secondes."""
        return int(time.time() - self.created_at)
    
    def access(self) -> Any:
        """Marque l'accès à l'élément et retourne les données."""
        self.access_count += 1
        self.last_accessed = time.time()
        return self.data
    
    def has_tag(self, tag: str) -> bool:
        """Vérifie si l'élément a un tag spécifique."""
        return tag in self.tags


class BaseCacheBackend(ABC):
    """Interface de base pour les backends de cache."""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Récupère une valeur du cache."""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Stocke une valeur dans le cache."""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Supprime une clé du cache."""
        pass
    
    @abstractmethod
    async def clear(self) -> int:
        """Vide complètement le cache."""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Vérifie si une clé existe."""
        pass


class MemoryCacheBackend(BaseCacheBackend):
    """Backend de cache en mémoire simple."""
    
    def __init__(self, max_size: int = 1000):
        self.cache: Dict[str, CacheItem] = {}
        self.max_size = max_size
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        """Récupère une valeur du cache."""
        async with self._lock:
            item = self.cache.get(key)
            if item is None:
                return None
            
            if item.is_expired:
                del self.cache[key]
                return None
            
            return item.access()
    
    async def set(self, key: str, value: Any, ttl: int = 3600, tags: Optional[List[str]] = None) -> bool:
        """Stocke une valeur dans le cache."""
        async with self._lock:
            # Éviction si nécessaire
            if len(self.cache) >= self.max_size:
                await self._evict_lru()
            
            self.cache[key] = CacheItem(value, ttl, tags)
            return True
    
    async def delete(self, key: str) -> bool:
        """Supprime une clé du cache."""
        async with self._lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False
    
    async def clear(self) -> int:
        """Vide complètement le cache."""
        async with self._lock:
            count = len(self.cache)
            self.cache.clear()
            return count
    
    async def exists(self, key: str) -> bool:
        """Vérifie si une clé existe."""
        async with self._lock:
            item = self.cache.get(key)
            if item is None:
                return False
            
            if item.is_expired:
                del self.cache[key]
                return False
            
            return True
    
    async def invalidate_by_tag(self, tag: str) -> int:
        """Invalide tous les éléments avec un tag spécifique."""
        async with self._lock:
            keys_to_delete = []
            for key, item in self.cache.items():
                if item.has_tag(tag):
                    keys_to_delete.append(key)
            
            for key in keys_to_delete:
                del self.cache[key]
            
            return len(keys_to_delete)
    
    async def _evict_lru(self) -> None:
        """Évince l'élément le moins récemment utilisé."""
        if not self.cache:
            return
        
        # Trouve l'élément le moins récemment accédé
        lru_key = min(self.cache.keys(), 
                     key=lambda k: self.cache[k].last_accessed)
        del self.cache[lru_key]
    
    async def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du cache."""
        async with self._lock:
            total_items = len(self.cache)
            expired_items = sum(1 for item in self.cache.values() if item.is_expired)
            total_accesses = sum(item.access_count for item in self.cache.values())
            
            return {
                'total_items': total_items,
                'expired_items': expired_items,
                'active_items': total_items - expired_items,
                'total_accesses': total_accesses,
                'max_size': self.max_size,
                'utilization': total_items / self.max_size if self.max_size > 0 else 0
            }


class MultiLevelCacheManager:
    """Gestionnaire de cache multi-niveaux."""
    
    def __init__(self, 
                 l1_backend: Optional[BaseCacheBackend] = None,
                 l2_backend: Optional[BaseCacheBackend] = None,
                 default_ttl: int = 3600):
        """
        Initialise le gestionnaire de cache.
        
        Args:
            l1_backend: Cache L1 (rapide, petite taille)
            l2_backend: Cache L2 (plus lent, plus grande taille)
            default_ttl: TTL par défaut en secondes
        """
        self.l1_backend = l1_backend or MemoryCacheBackend(max_size=500)
        self.l2_backend = l2_backend
        self.default_ttl = default_ttl
        
        # Statistiques
        self.hits_l1 = 0
        self.hits_l2 = 0
        self.misses = 0
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Récupère une valeur du cache (multi-niveaux).
        
        Args:
            key: Clé à rechercher
            
        Returns:
            Valeur trouvée ou None
        """
        # Essayer L1 d'abord
        value = await self.l1_backend.get(key)
        if value is not None:
            self.hits_l1 += 1
            return value
        
        # Essayer L2 si disponible
        if self.l2_backend:
            value = await self.l2_backend.get(key)
            if value is not None:
                self.hits_l2 += 1
                # Remonter en L1 pour les accès futurs
                await self.l1_backend.set(key, value)
                return value
        
        self.misses += 1
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None, 
                  tags: Optional[List[str]] = None) -> bool:
        """
        Stocke une valeur dans le cache.
        
        Args:
            key: Clé de stockage
            value: Valeur à stocker
            ttl: TTL en secondes (utilise default_ttl si None)
            tags: Tags pour l'invalidation
            
        Returns:
            True si stocké avec succès
        """
        actual_ttl = ttl or self.default_ttl
        
        # Stocker en L1
        success_l1 = await self.l1_backend.set(key, value, actual_ttl, tags)
        
        # Stocker en L2 si disponible
        success_l2 = True
        if self.l2_backend:
            success_l2 = await self.l2_backend.set(key, value, actual_ttl, tags)
        
        return success_l1 and success_l2
    
    async def delete(self, key: str) -> bool:
        """
        Supprime une clé des deux niveaux.
        
        Args:
            key: Clé à supprimer
            
        Returns:
            True si supprimé d'au moins un niveau
        """
        deleted_l1 = await self.l1_backend.delete(key)
        deleted_l2 = False
        
        if self.l2_backend:
            deleted_l2 = await self.l2_backend.delete(key)
        
        return deleted_l1 or deleted_l2
    
    async def clear(self) -> int:
        """
        Vide tous les niveaux de cache.
        
        Returns:
            Nombre total d'éléments supprimés
        """
        count_l1 = await self.l1_backend.clear()
        count_l2 = 0
        
        if self.l2_backend:
            count_l2 = await self.l2_backend.clear()
        
        return count_l1 + count_l2
    
    async def invalidate_by_tag(self, tag: str) -> int:
        """
        Invalide tous les éléments avec un tag spécifique.
        
        Args:
            tag: Tag à invalider
            
        Returns:
            Nombre d'éléments invalidés
        """
        count = 0
        
        # Invalider L1
        if hasattr(self.l1_backend, 'invalidate_by_tag'):
            count += await self.l1_backend.invalidate_by_tag(tag)
        
        # Invalider L2
        if self.l2_backend and hasattr(self.l2_backend, 'invalidate_by_tag'):
            count += await self.l2_backend.invalidate_by_tag(tag)
        
        return count
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Retourne les statistiques globales du cache.
        
        Returns:
            Dictionnaire avec les statistiques
        """
        total_requests = self.hits_l1 + self.hits_l2 + self.misses
        hit_rate = (self.hits_l1 + self.hits_l2) / total_requests if total_requests > 0 else 0
        
        stats = {
            'requests': {
                'total': total_requests,
                'hits_l1': self.hits_l1,
                'hits_l2': self.hits_l2,
                'misses': self.misses,
                'hit_rate': hit_rate,
                'l1_hit_rate': self.hits_l1 / total_requests if total_requests > 0 else 0,
                'l2_hit_rate': self.hits_l2 / total_requests if total_requests > 0 else 0
            }
        }
        
        # Ajouter les stats L1
        if hasattr(self.l1_backend, 'get_stats'):
            stats['l1'] = await self.l1_backend.get_stats()
        
        # Ajouter les stats L2
        if self.l2_backend and hasattr(self.l2_backend, 'get_stats'):
            stats['l2'] = await self.l2_backend.get_stats()
        
        return stats
    
    async def health_check(self) -> Dict[str, bool]:
        """
        Vérifie l'état de santé des backends de cache.
        
        Returns:
            État de santé de chaque niveau
        """
        health = {}
        
        # Test L1
        try:
            test_key = "__health_check__"
            await self.l1_backend.set(test_key, "test", 1)
            value = await self.l1_backend.get(test_key)
            await self.l1_backend.delete(test_key)
            health['l1'] = value == "test"
        except Exception as e:
            logger.error(f"Erreur health check L1: {e}")
            health['l1'] = False
        
        # Test L2
        if self.l2_backend:
            try:
                test_key = "__health_check__"
                await self.l2_backend.set(test_key, "test", 1)
                value = await self.l2_backend.get(test_key)
                await self.l2_backend.delete(test_key)
                health['l2'] = value == "test"
            except Exception as e:
                logger.error(f"Erreur health check L2: {e}")
                health['l2'] = False
        else:
            health['l2'] = None  # Pas configuré
        
        return health