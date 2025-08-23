"""
Utilitaires de gestion du cache pour la CLI FinAgent.

Ce module fournit des outils pour gérer le cache de données,
optimiser les performances et nettoyer l'espace disque.
"""

import os
import json
import pickle
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import track

console = Console()


class CacheType(str, Enum):
    """Types de cache disponibles."""
    MARKET_DATA = "market_data"
    ANALYSIS_RESULTS = "analysis_results"
    STRATEGY_BACKTEST = "strategy_backtest"
    AI_RESPONSES = "ai_responses"
    USER_PREFERENCES = "user_preferences"


@dataclass
class CacheEntry:
    """Entrée de cache avec métadonnées."""
    key: str
    data: Any
    cache_type: CacheType
    created_at: datetime
    expires_at: Optional[datetime]
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    size_bytes: int = 0
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.last_accessed is None:
            self.last_accessed = self.created_at


@dataclass
class CacheStats:
    """Statistiques du cache."""
    total_entries: int
    total_size_bytes: int
    cache_hit_rate: float
    oldest_entry: Optional[datetime]
    newest_entry: Optional[datetime]
    entries_by_type: Dict[str, int]
    size_by_type: Dict[str, int]


class CacheManager:
    """Gestionnaire principal du cache."""
    
    def __init__(self, cache_dir: Union[str, Path] = "data/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Répertoires par type de cache
        self.cache_dirs = {
            cache_type: self.cache_dir / cache_type.value
            for cache_type in CacheType
        }
        
        # Création des répertoires
        for cache_dir in self.cache_dirs.values():
            cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Fichier de métadonnées
        self.metadata_file = self.cache_dir / "metadata.json"
        self.metadata = self._load_metadata()
        
        # Statistiques
        self.hit_count = 0
        self.miss_count = 0
    
    def _load_metadata(self) -> Dict[str, Dict]:
        """Charge les métadonnées du cache."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                console.print("⚠️  Erreur lors du chargement des métadonnées du cache", style="yellow")
        
        return {
            "entries": {},
            "stats": {
                "hit_count": 0,
                "miss_count": 0,
                "created_at": datetime.now().isoformat()
            }
        }
    
    def _save_metadata(self) -> None:
        """Sauvegarde les métadonnées du cache."""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2, default=str)
        except IOError as e:
            console.print(f"⚠️  Erreur lors de la sauvegarde des métadonnées: {e}", style="yellow")
    
    def _generate_cache_key(self, 
                           key: str, 
                           cache_type: CacheType,
                           additional_params: Optional[Dict] = None) -> str:
        """
        Génère une clé de cache unique.
        
        Args:
            key: Clé de base
            cache_type: Type de cache
            additional_params: Paramètres supplémentaires pour la clé
            
        Returns:
            Clé de cache hashée
        """
        key_data = {
            "key": key,
            "type": cache_type.value,
            "params": additional_params or {}
        }
        
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_cache_file_path(self, cache_key: str, cache_type: CacheType) -> Path:
        """Retourne le chemin du fichier de cache."""
        return self.cache_dirs[cache_type] / f"{cache_key}.cache"
    
    def get(self, 
            key: str,
            cache_type: CacheType,
            additional_params: Optional[Dict] = None) -> Optional[Any]:
        """
        Récupère une valeur du cache.
        
        Args:
            key: Clé de recherche
            cache_type: Type de cache
            additional_params: Paramètres supplémentaires
            
        Returns:
            Valeur en cache ou None si non trouvée/expirée
        """
        cache_key = self._generate_cache_key(key, cache_type, additional_params)
        cache_file = self._get_cache_file_path(cache_key, cache_type)
        
        if not cache_file.exists():
            self.miss_count += 1
            return None
        
        try:
            # Chargement des données
            with open(cache_file, 'rb') as f:
                cache_entry = pickle.load(f)
            
            # Vérification de l'expiration
            if cache_entry.expires_at and datetime.now() > cache_entry.expires_at:
                self._remove_cache_file(cache_key, cache_type)
                self.miss_count += 1
                return None
            
            # Mise à jour des statistiques d'accès
            cache_entry.access_count += 1
            cache_entry.last_accessed = datetime.now()
            
            # Sauvegarde des métadonnées mises à jour
            self.metadata["entries"][cache_key] = {
                "access_count": cache_entry.access_count,
                "last_accessed": cache_entry.last_accessed.isoformat(),
                "cache_type": cache_type.value
            }
            
            self.hit_count += 1
            return cache_entry.data
            
        except (pickle.PickleError, IOError) as e:
            console.print(f"⚠️  Erreur lors de la lecture du cache: {e}", style="yellow")
            self._remove_cache_file(cache_key, cache_type)
            self.miss_count += 1
            return None
    
    def set(self,
            key: str,
            data: Any,
            cache_type: CacheType,
            ttl_seconds: Optional[int] = None,
            additional_params: Optional[Dict] = None,
            tags: Optional[List[str]] = None) -> bool:
        """
        Stocke une valeur dans le cache.
        
        Args:
            key: Clé de stockage
            data: Données à stocker
            cache_type: Type de cache
            ttl_seconds: Durée de vie en secondes (optionnel)
            additional_params: Paramètres supplémentaires
            tags: Tags pour catégoriser l'entrée
            
        Returns:
            True si le stockage a réussi
        """
        cache_key = self._generate_cache_key(key, cache_type, additional_params)
        cache_file = self._get_cache_file_path(cache_key, cache_type)
        
        # Calcul de l'expiration
        expires_at = None
        if ttl_seconds:
            expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
        
        # Création de l'entrée de cache
        cache_entry = CacheEntry(
            key=cache_key,
            data=data,
            cache_type=cache_type,
            created_at=datetime.now(),
            expires_at=expires_at,
            tags=tags or []
        )
        
        try:
            # Sauvegarde des données
            with open(cache_file, 'wb') as f:
                pickle.dump(cache_entry, f)
            
            # Calcul de la taille
            cache_entry.size_bytes = cache_file.stat().st_size
            
            # Mise à jour des métadonnées
            self.metadata["entries"][cache_key] = {
                "key": key,
                "cache_type": cache_type.value,
                "created_at": cache_entry.created_at.isoformat(),
                "expires_at": expires_at.isoformat() if expires_at else None,
                "size_bytes": cache_entry.size_bytes,
                "tags": cache_entry.tags,
                "access_count": 0,
                "last_accessed": cache_entry.created_at.isoformat()
            }
            
            self._save_metadata()
            return True
            
        except (pickle.PickleError, IOError) as e:
            console.print(f"❌ Erreur lors de l'écriture du cache: {e}", style="red")
            return False
    
    def delete(self, 
               key: str,
               cache_type: CacheType,
               additional_params: Optional[Dict] = None) -> bool:
        """
        Supprime une entrée du cache.
        
        Args:
            key: Clé à supprimer
            cache_type: Type de cache
            additional_params: Paramètres supplémentaires
            
        Returns:
            True si la suppression a réussi
        """
        cache_key = self._generate_cache_key(key, cache_type, additional_params)
        return self._remove_cache_file(cache_key, cache_type)
    
    def _remove_cache_file(self, cache_key: str, cache_type: CacheType) -> bool:
        """Supprime un fichier de cache et ses métadonnées."""
        cache_file = self._get_cache_file_path(cache_key, cache_type)
        
        success = True
        if cache_file.exists():
            try:
                cache_file.unlink()
            except OSError:
                success = False
        
        # Suppression des métadonnées
        if cache_key in self.metadata["entries"]:
            del self.metadata["entries"][cache_key]
            self._save_metadata()
        
        return success
    
    def clear_by_type(self, cache_type: CacheType) -> int:
        """
        Vide tout le cache d'un type donné.
        
        Args:
            cache_type: Type de cache à vider
            
        Returns:
            Nombre d'entrées supprimées
        """
        cache_dir = self.cache_dirs[cache_type]
        removed_count = 0
        
        if cache_dir.exists():
            for cache_file in cache_dir.glob("*.cache"):
                try:
                    cache_file.unlink()
                    removed_count += 1
                except OSError:
                    pass
        
        # Nettoyage des métadonnées
        keys_to_remove = [
            key for key, meta in self.metadata["entries"].items()
            if meta.get("cache_type") == cache_type.value
        ]
        
        for key in keys_to_remove:
            del self.metadata["entries"][key]
        
        self._save_metadata()
        return removed_count
    
    def clear_expired(self) -> int:
        """
        Supprime toutes les entrées expirées.
        
        Returns:
            Nombre d'entrées supprimées
        """
        now = datetime.now()
        removed_count = 0
        keys_to_remove = []
        
        for cache_key, meta in self.metadata["entries"].items():
            expires_at_str = meta.get("expires_at")
            if expires_at_str:
                try:
                    expires_at = datetime.fromisoformat(expires_at_str)
                    if now > expires_at:
                        cache_type = CacheType(meta["cache_type"])
                        if self._remove_cache_file(cache_key, cache_type):
                            removed_count += 1
                        keys_to_remove.append(cache_key)
                except (ValueError, KeyError):
                    keys_to_remove.append(cache_key)
        
        # Nettoyage des métadonnées
        for key in keys_to_remove:
            if key in self.metadata["entries"]:
                del self.metadata["entries"][key]
        
        self._save_metadata()
        return removed_count
    
    def clear_by_tags(self, tags: List[str]) -> int:
        """
        Supprime les entrées ayant certains tags.
        
        Args:
            tags: Liste des tags à rechercher
            
        Returns:
            Nombre d'entrées supprimées
        """
        removed_count = 0
        keys_to_remove = []
        
        for cache_key, meta in self.metadata["entries"].items():
            entry_tags = meta.get("tags", [])
            if any(tag in entry_tags for tag in tags):
                cache_type = CacheType(meta["cache_type"])
                if self._remove_cache_file(cache_key, cache_type):
                    removed_count += 1
                keys_to_remove.append(cache_key)
        
        # Nettoyage des métadonnées
        for key in keys_to_remove:
            if key in self.metadata["entries"]:
                del self.metadata["entries"][key]
        
        self._save_metadata()
        return removed_count
    
    def get_stats(self) -> CacheStats:
        """
        Retourne les statistiques du cache.
        
        Returns:
            Statistiques détaillées
        """
        total_entries = len(self.metadata["entries"])
        total_size = 0
        entries_by_type = {}
        size_by_type = {}
        oldest_entry = None
        newest_entry = None
        
        for meta in self.metadata["entries"].values():
            cache_type = meta.get("cache_type", "unknown")
            size_bytes = meta.get("size_bytes", 0)
            created_at_str = meta.get("created_at")
            
            # Comptage par type
            entries_by_type[cache_type] = entries_by_type.get(cache_type, 0) + 1
            size_by_type[cache_type] = size_by_type.get(cache_type, 0) + size_bytes
            total_size += size_bytes
            
            # Dates
            if created_at_str:
                try:
                    created_at = datetime.fromisoformat(created_at_str)
                    if oldest_entry is None or created_at < oldest_entry:
                        oldest_entry = created_at
                    if newest_entry is None or created_at > newest_entry:
                        newest_entry = created_at
                except ValueError:
                    pass
        
        # Calcul du taux de réussite
        total_requests = self.hit_count + self.miss_count
        hit_rate = self.hit_count / total_requests if total_requests > 0 else 0.0
        
        return CacheStats(
            total_entries=total_entries,
            total_size_bytes=total_size,
            cache_hit_rate=hit_rate,
            oldest_entry=oldest_entry,
            newest_entry=newest_entry,
            entries_by_type=entries_by_type,
            size_by_type=size_by_type
        )
    
    def cleanup_old_entries(self, days_old: int = 30) -> int:
        """
        Supprime les entrées plus anciennes que X jours.
        
        Args:
            days_old: Nombre de jours d'ancienneté
            
        Returns:
            Nombre d'entrées supprimées
        """
        cutoff_date = datetime.now() - timedelta(days=days_old)
        removed_count = 0
        keys_to_remove = []
        
        for cache_key, meta in self.metadata["entries"].items():
            last_accessed_str = meta.get("last_accessed") or meta.get("created_at")
            if last_accessed_str:
                try:
                    last_accessed = datetime.fromisoformat(last_accessed_str)
                    if last_accessed < cutoff_date:
                        cache_type = CacheType(meta["cache_type"])
                        if self._remove_cache_file(cache_key, cache_type):
                            removed_count += 1
                        keys_to_remove.append(cache_key)
                except (ValueError, KeyError):
                    keys_to_remove.append(cache_key)
        
        # Nettoyage des métadonnées
        for key in keys_to_remove:
            if key in self.metadata["entries"]:
                del self.metadata["entries"][key]
        
        self._save_metadata()
        return removed_count


def format_size(size_bytes: int) -> str:
    """Formate une taille en bytes de manière lisible."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def create_cache_stats_table(stats: CacheStats) -> Table:
    """
    Crée un tableau des statistiques de cache.
    
    Args:
        stats: Statistiques du cache
        
    Returns:
        Table formatée
    """
    table = Table(title="📊 Statistiques du Cache", show_header=True, header_style="bold cyan")
    
    table.add_column("Métrique", style="cyan", no_wrap=True)
    table.add_column("Valeur", justify="right")
    
    # Statistiques générales
    table.add_row("Nombre total d'entrées", str(stats.total_entries))
    table.add_row("Taille totale", format_size(stats.total_size_bytes))
    table.add_row("Taux de réussite", f"{stats.cache_hit_rate:.1%}")
    
    if stats.oldest_entry:
        table.add_row("Entrée la plus ancienne", stats.oldest_entry.strftime("%Y-%m-%d %H:%M"))
    
    if stats.newest_entry:
        table.add_row("Entrée la plus récente", stats.newest_entry.strftime("%Y-%m-%d %H:%M"))
    
    # Séparateur
    table.add_row("─" * 20, "─" * 15)
    
    # Répartition par type
    for cache_type, count in stats.entries_by_type.items():
        size = stats.size_by_type.get(cache_type, 0)
        table.add_row(
            f"{cache_type.replace('_', ' ').title()}",
            f"{count} entrées ({format_size(size)})"
        )
    
    return table


def create_cache_commands_panel() -> Panel:
    """Crée un panel avec les commandes de cache disponibles."""
    content = """
🧹 Commandes de nettoyage disponibles:

• finagent cache clear --type market_data
  Vide le cache des données de marché

• finagent cache clear --expired
  Supprime les entrées expirées

• finagent cache clear --older-than 30
  Supprime les entrées de plus de 30 jours

• finagent cache clear --tags analysis,temp
  Supprime les entrées avec certains tags

• finagent cache stats
  Affiche les statistiques détaillées

• finagent cache optimize
  Optimise et compacte le cache
    """
    
    return Panel(
        content,
        title="💡 Aide - Gestion du Cache",
        border_style="blue"
    )


# Instance globale du gestionnaire de cache
cache_manager = CacheManager()