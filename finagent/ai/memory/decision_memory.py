"""
Gestionnaire de mémoire des décisions de trading.
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
    DecisionMemory, MemorySearchQuery, MemorySearchResult, 
    MemoryEntry, MemoryType, MemoryPersistenceConfig, MemoryRetentionPolicy
)
from ..models.trading_decision import DecisionType
from ..models.base import ConfidenceLevel
from ...core.errors.exceptions import FinAgentError

logger = structlog.get_logger(__name__)


class DecisionMemoryError(FinAgentError):
    """Erreur liée à la mémoire des décisions."""
    pass


class DecisionMemoryManager:
    """
    Gestionnaire de mémoire pour les décisions de trading.
    
    Stocke et indexe les décisions de trading pour permettre l'analyse
    des performances, l'apprentissage et l'amélioration des stratégies.
    """
    
    def __init__(
        self,
        persistence_config: Optional[MemoryPersistenceConfig] = None,
        retention_policy: Optional[MemoryRetentionPolicy] = None
    ):
        """
        Initialise le gestionnaire de mémoire des décisions.
        
        Args:
            persistence_config: Configuration de persistence
            retention_policy: Politique de rétention
        """
        self.persistence_config = persistence_config or MemoryPersistenceConfig()
        self.retention_policy = retention_policy or MemoryRetentionPolicy()
        
        # Cache en mémoire organisé par symbole et action
        self._decision_cache: Dict[str, Dict[str, List[DecisionMemory]]] = {}  # symbol -> action -> decisions
        self._cache_size_limit = 1000
        self._cache_entry_count = 0
        
        # Index pour recherche rapide
        self._symbol_index: Dict[str, List[str]] = {}  # symbol -> list of memory_ids
        self._action_index: Dict[str, List[str]] = {}  # action -> list of memory_ids
        self._performance_index: Dict[str, List[str]] = {}  # performance_range -> list of memory_ids
        
        # Base de données SQLite pour persistence
        self.db_path: Optional[Path] = None
        if self.persistence_config.enabled:
            storage_dir = Path(self.persistence_config.storage_path)
            storage_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = storage_dir / "trading_decisions.db"
        
        logger.info(
            "Gestionnaire de mémoire des décisions initialisé",
            persistence_enabled=self.persistence_config.enabled,
            db_path=str(self.db_path) if self.db_path else None
        )
    
    async def start(self) -> None:
        """Démarre le gestionnaire de mémoire."""
        try:
            if self.persistence_config.enabled and self.db_path:
                await self._init_database()
            
            logger.info("Gestionnaire de mémoire des décisions démarré")
            
        except Exception as e:
            logger.error("Erreur lors du démarrage", error=str(e))
            raise DecisionMemoryError(f"Impossible de démarrer: {e}")
    
    async def stop(self) -> None:
        """Arrête le gestionnaire de mémoire."""
        try:
            self._decision_cache.clear()
            self._symbol_index.clear()
            self._action_index.clear()
            self._performance_index.clear()
            self._cache_entry_count = 0
            
            logger.info("Gestionnaire de mémoire des décisions arrêté")
            
        except Exception as e:
            logger.error("Erreur lors de l'arrêt", error=str(e))
    
    async def store_decision(
        self,
        decision: DecisionMemory
    ) -> str:
        """
        Stocke une décision de trading.
        
        Args:
            decision: Décision à stocker
            
        Returns:
            ID de la décision stockée
        """
        try:
            # Organiser le cache par symbole et action
            symbol = decision.symbol
            action = decision.action.value
            
            if symbol not in self._decision_cache:
                self._decision_cache[symbol] = {}
            if action not in self._decision_cache[symbol]:
                self._decision_cache[symbol][action] = []
            
            # Ajouter au cache si possible
            if self._cache_entry_count < self._cache_size_limit:
                self._decision_cache[symbol][action].append(decision)
                self._cache_entry_count += 1
                
                # Mettre à jour les index
                self._update_symbol_index(symbol, decision.decision_id)
                self._update_action_index(action, decision.decision_id)
                
                if decision.actual_outcome is not None:
                    performance_range = self._get_performance_range(decision.actual_outcome)
                    self._update_performance_index(performance_range, decision.decision_id)
            
            # Sauvegarder en base si persistence activée
            if self.persistence_config.enabled and self.db_path:
                await self._save_decision_to_db(decision)
            
            logger.debug(
                "Décision stockée",
                decision_id=decision.decision_id,
                symbol=decision.symbol,
                action=decision.action.value,
                confidence=decision.confidence.value
            )
            
            return decision.decision_id
            
        except Exception as e:
            logger.error(
                "Erreur lors du stockage de la décision",
                decision_id=decision.decision_id,
                symbol=decision.symbol,
                error=str(e)
            )
            raise DecisionMemoryError(f"Impossible de stocker la décision: {e}")
    
    async def get_decision(
        self,
        decision_id: str
    ) -> Optional[DecisionMemory]:
        """
        Récupère une décision par son ID.
        
        Args:
            decision_id: ID de la décision
            
        Returns:
            Décision ou None si non trouvée
        """
        try:
            # Rechercher dans le cache
            for symbol_cache in self._decision_cache.values():
                for action_decisions in symbol_cache.values():
                    for decision in action_decisions:
                        if decision.decision_id == decision_id:
                            logger.debug("Décision récupérée depuis le cache", decision_id=decision_id)
                            return decision
            
            # Charger depuis la base si persistence activée
            if self.persistence_config.enabled and self.db_path:
                decision = await self._load_decision_from_db(decision_id)
                if decision:
                    # Ajouter au cache si possible
                    if self._cache_entry_count < self._cache_size_limit:
                        symbol = decision.symbol
                        action = decision.action.value
                        
                        if symbol not in self._decision_cache:
                            self._decision_cache[symbol] = {}
                        if action not in self._decision_cache[symbol]:
                            self._decision_cache[symbol][action] = []
                        
                        self._decision_cache[symbol][action].append(decision)
                        self._cache_entry_count += 1
                        
                        self._update_symbol_index(symbol, decision_id)
                        self._update_action_index(action, decision_id)
                        
                        if decision.actual_outcome is not None:
                            performance_range = self._get_performance_range(decision.actual_outcome)
                            self._update_performance_index(performance_range, decision_id)
                
                return decision
            
            return None
            
        except Exception as e:
            logger.error(
                "Erreur lors de la récupération de la décision",
                decision_id=decision_id,
                error=str(e)
            )
            return None
    
    async def get_decisions_by_symbol(
        self,
        symbol: str,
        action: Optional[DecisionType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[DecisionMemory]:
        """
        Récupère les décisions pour un symbole donné.
        
        Args:
            symbol: Symbole financier
            action: Action de trading (optionnelle)
            start_date: Date de début (optionnelle)
            end_date: Date de fin (optionnelle)
            limit: Limite du nombre de résultats
            
        Returns:
            Liste des décisions
        """
        try:
            results = []
            
            # Rechercher dans le cache
            if symbol in self._decision_cache:
                if action:
                    action_key = action.value
                    if action_key in self._decision_cache[symbol]:
                        for decision in self._decision_cache[symbol][action_key]:
                            if self._matches_date_range(decision, start_date, end_date):
                                results.append(decision)
                else:
                    for action_decisions in self._decision_cache[symbol].values():
                        for decision in action_decisions:
                            if self._matches_date_range(decision, start_date, end_date):
                                results.append(decision)
            
            # Rechercher en base si persistence activée
            if self.persistence_config.enabled and self.db_path:
                db_results = await self._load_decisions_by_symbol_from_db(
                    symbol, action, start_date, end_date, limit
                )
                
                # Éviter les doublons avec le cache
                cache_ids = {decision.decision_id for decision in results}
                for decision in db_results:
                    if decision.decision_id not in cache_ids:
                        results.append(decision)
            
            # Trier par timestamp
            results.sort(key=lambda x: x.timestamp, reverse=True)
            
            # Appliquer la limite
            if limit:
                results = results[:limit]
            
            logger.debug(
                "Décisions récupérées par symbole",
                symbol=symbol,
                action=action.value if action else "ALL",
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
    
    async def get_performance_analysis(
        self,
        symbol: Optional[str] = None,
        action: Optional[DecisionType] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Analyse les performances des décisions.
        
        Args:
            symbol: Symbole à analyser (optionnel)
            action: Action à analyser (optionnelle)
            days: Nombre de jours à analyser
            
        Returns:
            Analyse des performances
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            decisions = []
            
            # Collecter les décisions avec résultats
            if symbol:
                decisions = await self.get_decisions_by_symbol(
                    symbol, action, start_date=cutoff_date
                )
            else:
                # Récupérer toutes les décisions récentes
                for symbol_cache in self._decision_cache.values():
                    for action_decisions in symbol_cache.values():
                        for decision in action_decisions:
                            if (decision.timestamp >= cutoff_date and 
                                decision.actual_outcome is not None):
                                if not action or decision.action == action:
                                    decisions.append(decision)
            
            # Filtrer les décisions avec résultats
            decisions_with_outcomes = [
                d for d in decisions if d.actual_outcome is not None
            ]
            
            if not decisions_with_outcomes:
                return {
                    "total_decisions": 0,
                    "decisions_with_outcomes": 0,
                    "success_rate": 0.0,
                    "average_return": 0.0,
                    "total_return": 0.0,
                    "best_decision": None,
                    "worst_decision": None,
                    "by_action": {},
                    "by_confidence": {}
                }
            
            # Calculer les métriques
            successful_decisions = [d for d in decisions_with_outcomes if d.actual_outcome > 0]
            success_rate = len(successful_decisions) / len(decisions_with_outcomes)
            
            returns = [d.actual_outcome for d in decisions_with_outcomes]
            average_return = sum(returns) / len(returns)
            total_return = sum(returns)
            
            best_decision = max(decisions_with_outcomes, key=lambda d: d.actual_outcome)
            worst_decision = min(decisions_with_outcomes, key=lambda d: d.actual_outcome)
            
            # Analyse par action
            by_action = {}
            for action_type in DecisionType:
                action_decisions = [d for d in decisions_with_outcomes if DecisionType(d.action) == action_type]
                if action_decisions:
                    action_returns = [d.actual_outcome for d in action_decisions]
                    by_action[action_type.value] = {
                        "count": len(action_decisions),
                        "success_rate": len([d for d in action_decisions if d.actual_outcome > 0]) / len(action_decisions),
                        "average_return": sum(action_returns) / len(action_returns),
                        "total_return": sum(action_returns)
                    }
            
            # Analyse par niveau de confiance
            by_confidence = {}
            for confidence_level in ConfidenceLevel:
                conf_decisions = [d for d in decisions_with_outcomes if ConfidenceLevel(d.confidence) == confidence_level]
                if conf_decisions:
                    conf_returns = [d.actual_outcome for d in conf_decisions]
                    by_confidence[confidence_level.value] = {
                        "count": len(conf_decisions),
                        "success_rate": len([d for d in conf_decisions if d.actual_outcome > 0]) / len(conf_decisions),
                        "average_return": sum(conf_returns) / len(conf_returns),
                        "total_return": sum(conf_returns)
                    }
            
            return {
                "total_decisions": len(decisions),
                "decisions_with_outcomes": len(decisions_with_outcomes),
                "success_rate": success_rate,
                "average_return": average_return,
                "total_return": total_return,
                "best_decision": {
                    "id": best_decision.decision_id,
                    "symbol": best_decision.symbol,
                    "action": best_decision.action.value,
                    "return": best_decision.actual_outcome
                },
                "worst_decision": {
                    "id": worst_decision.decision_id,
                    "symbol": worst_decision.symbol,
                    "action": worst_decision.action.value,
                    "return": worst_decision.actual_outcome
                },
                "by_action": by_action,
                "by_confidence": by_confidence
            }
            
        except Exception as e:
            logger.error("Erreur lors de l'analyse des performances", error=str(e))
            return {}
    
    async def search_decisions(
        self,
        query: MemorySearchQuery
    ) -> List[MemorySearchResult]:
        """
        Recherche dans les décisions.
        
        Args:
            query: Requête de recherche
            
        Returns:
            Liste des résultats
        """
        try:
            results = []
            
            # Rechercher dans le cache
            for symbol, symbol_cache in self._decision_cache.items():
                for action_decisions in symbol_cache.values():
                    for decision in action_decisions:
                        if self._matches_query(decision, query):
                            score = self._calculate_relevance_score(decision, query)
                            
                            memory_entry = MemoryEntry(
                                id=decision.decision_id,
                                memory_type=MemoryType.DECISION,
                                content=decision,
                                metadata={
                                    "symbol": decision.symbol,
                                    "action": decision.action.value,
                                    "confidence": decision.confidence.value,
                                    "expected_return": decision.expected_return,
                                    "actual_outcome": decision.actual_outcome
                                },
                                created_at=decision.timestamp
                            )
                            
                            results.append(MemorySearchResult(
                                memory_entry=memory_entry,
                                relevance_score=score,
                                match_highlights=self._get_match_highlights(decision, query)
                            ))
            
            # Rechercher en base si persistence activée
            if self.persistence_config.enabled and self.db_path:
                db_results = await self._search_decisions_in_db(query)
                
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
                "Recherche de décisions effectuée",
                query_text=query.text_query,
                results_count=len(results)
            )
            
            return results
            
        except Exception as e:
            logger.error("Erreur lors de la recherche", error=str(e))
            return []
    
    async def update_decision_outcome(
        self,
        decision_id: str,
        actual_outcome: float
    ) -> bool:
        """
        Met à jour le résultat réel d'une décision.
        
        Args:
            decision_id: ID de la décision
            actual_outcome: Résultat réel
            
        Returns:
            True si mis à jour avec succès
        """
        try:
            decision = await self.get_decision(decision_id)
            if not decision:
                logger.warning("Décision non trouvée pour mise à jour", decision_id=decision_id)
                return False
            
            # Mettre à jour la décision
            decision.actual_outcome = actual_outcome
            decision.updated_at = datetime.utcnow()
            
            # Mettre à jour les index de performance
            performance_range = self._get_performance_range(actual_outcome)
            self._update_performance_index(performance_range, decision_id)
            
            # Sauvegarder en base si persistence activée
            if self.persistence_config.enabled and self.db_path:
                await self._save_decision_to_db(decision)
            
            logger.debug(
                "Résultat de décision mis à jour",
                decision_id=decision_id,
                actual_outcome=actual_outcome
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Erreur lors de la mise à jour du résultat",
                decision_id=decision_id,
                error=str(e)
            )
            return False
    
    async def delete_decision(
        self,
        decision_id: str
    ) -> bool:
        """
        Supprime une décision.
        
        Args:
            decision_id: ID de la décision
            
        Returns:
            True si supprimée avec succès
        """
        try:
            # Supprimer du cache
            deleted_from_cache = False
            for symbol, symbol_cache in self._decision_cache.items():
                for action, action_decisions in symbol_cache.items():
                    for i, decision in enumerate(action_decisions):
                        if decision.decision_id == decision_id:
                            del action_decisions[i]
                            self._cache_entry_count -= 1
                            deleted_from_cache = True
                            
                            # Mettre à jour les index
                            self._remove_from_symbol_index(symbol, decision_id)
                            self._remove_from_action_index(action, decision_id)
                            
                            if decision.actual_outcome is not None:
                                performance_range = self._get_performance_range(decision.actual_outcome)
                                self._remove_from_performance_index(performance_range, decision_id)
                            
                            break
                    
                    if deleted_from_cache:
                        break
                
                if deleted_from_cache:
                    break
            
            # Supprimer de la base si persistence activée
            if self.persistence_config.enabled and self.db_path:
                await self._delete_decision_from_db(decision_id)
            
            logger.debug("Décision supprimée", decision_id=decision_id)
            return True
            
        except Exception as e:
            logger.error(
                "Erreur lors de la suppression",
                decision_id=decision_id,
                error=str(e)
            )
            return False
    
    async def cleanup_expired(self) -> int:
        """
        Nettoie les décisions expirées.
        
        Returns:
            Nombre de décisions supprimées
        """
        try:
            deleted_count = 0
            cutoff_time = datetime.utcnow() - timedelta(
                days=self.retention_policy.decision_retention_days
            )
            
            # Nettoyer le cache
            for symbol, symbol_cache in list(self._decision_cache.items()):
                for action, action_decisions in list(symbol_cache.items()):
                    expired_indices = []
                    for i, decision in enumerate(action_decisions):
                        if decision.timestamp < cutoff_time:
                            expired_indices.append(i)
                            deleted_count += 1
                            
                            # Mettre à jour les index
                            self._remove_from_symbol_index(symbol, decision.decision_id)
                            self._remove_from_action_index(action, decision.decision_id)
                            
                            if decision.actual_outcome is not None:
                                performance_range = self._get_performance_range(decision.actual_outcome)
                                self._remove_from_performance_index(performance_range, decision.decision_id)
                    
                    # Supprimer en ordre inverse pour maintenir les indices
                    for i in reversed(expired_indices):
                        del action_decisions[i]
                        self._cache_entry_count -= 1
                    
                    # Supprimer l'action si elle n'a plus de décisions
                    if not action_decisions:
                        del symbol_cache[action]
                
                # Supprimer le symbole s'il n'a plus d'actions
                if not symbol_cache:
                    del self._decision_cache[symbol]
            
            # Nettoyer la base si persistence activée
            if self.persistence_config.enabled and self.db_path:
                db_deleted = await self._cleanup_expired_decisions_in_db(cutoff_time)
                deleted_count += db_deleted
            
            logger.info("Nettoyage des décisions expirées", deleted_count=deleted_count)
            return deleted_count
            
        except Exception as e:
            logger.error("Erreur lors du nettoyage", error=str(e))
            return 0
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Retourne les statistiques des décisions.
        
        Returns:
            Dictionnaire des statistiques
        """
        try:
            cache_count = self._cache_entry_count
            db_count = 0
            
            if self.persistence_config.enabled and self.db_path:
                db_count = await self._get_db_decision_count()
            
            unique_symbols = len(self._decision_cache)
            
            # Compter par action
            action_counts = {}
            for symbol_cache in self._decision_cache.values():
                for action, decisions in symbol_cache.items():
                    action_counts[action] = action_counts.get(action, 0) + len(decisions)
            
            # Compter les décisions avec résultats
            decisions_with_outcomes = 0
            for symbol_cache in self._decision_cache.values():
                for decisions in symbol_cache.values():
                    for decision in decisions:
                        if decision.actual_outcome is not None:
                            decisions_with_outcomes += 1
            
            return {
                "count": max(cache_count, db_count),
                "cache_count": cache_count,
                "db_count": db_count,
                "unique_symbols": unique_symbols,
                "decisions_with_outcomes": decisions_with_outcomes,
                "by_action": action_counts,
                "cache_limit": self._cache_size_limit
            }
            
        except Exception as e:
            logger.error("Erreur lors de la récupération des stats", error=str(e))
            return {"count": 0}
    
    def _matches_date_range(
        self,
        decision: DecisionMemory,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> bool:
        """Vérifie si une décision correspond à la plage de dates."""
        if start_date and decision.timestamp < start_date:
            return False
        if end_date and decision.timestamp > end_date:
            return False
        return True
    
    def _get_performance_range(self, outcome: float) -> str:
        """Détermine la plage de performance."""
        if outcome >= 0.1:
            return "excellent"
        elif outcome >= 0.05:
            return "good"
        elif outcome >= 0:
            return "neutral"
        elif outcome >= -0.05:
            return "poor"
        else:
            return "bad"
    
    def _update_symbol_index(self, symbol: str, decision_id: str) -> None:
        """Met à jour l'index par symbole."""
        if symbol not in self._symbol_index:
            self._symbol_index[symbol] = []
        if decision_id not in self._symbol_index[symbol]:
            self._symbol_index[symbol].append(decision_id)
    
    def _update_action_index(self, action: str, decision_id: str) -> None:
        """Met à jour l'index par action."""
        if action not in self._action_index:
            self._action_index[action] = []
        if decision_id not in self._action_index[action]:
            self._action_index[action].append(decision_id)
    
    def _update_performance_index(self, performance_range: str, decision_id: str) -> None:
        """Met à jour l'index par performance."""
        if performance_range not in self._performance_index:
            self._performance_index[performance_range] = []
        if decision_id not in self._performance_index[performance_range]:
            self._performance_index[performance_range].append(decision_id)
    
    def _remove_from_symbol_index(self, symbol: str, decision_id: str) -> None:
        """Supprime un élément de l'index par symbole."""
        if symbol in self._symbol_index and decision_id in self._symbol_index[symbol]:
            self._symbol_index[symbol].remove(decision_id)
            if not self._symbol_index[symbol]:
                del self._symbol_index[symbol]
    
    def _remove_from_action_index(self, action: str, decision_id: str) -> None:
        """Supprime un élément de l'index par action."""
        if action in self._action_index and decision_id in self._action_index[action]:
            self._action_index[action].remove(decision_id)
            if not self._action_index[action]:
                del self._action_index[action]
    
    def _remove_from_performance_index(self, performance_range: str, decision_id: str) -> None:
        """Supprime un élément de l'index par performance."""
        if performance_range in self._performance_index and decision_id in self._performance_index[performance_range]:
            self._performance_index[performance_range].remove(decision_id)
            if not self._performance_index[performance_range]:
                del self._performance_index[performance_range]
    
    def _matches_query(
        self,
        decision: DecisionMemory,
        query: MemorySearchQuery
    ) -> bool:
        """Vérifie si une décision correspond à la requête."""
        # Vérifier la plage de dates
        if query.start_date and decision.timestamp < query.start_date:
            return False
        if query.end_date and decision.timestamp > query.end_date:
            return False
        
        # Vérifier le texte de recherche
        if query.text_query:
            text_lower = query.text_query.lower()
            if (text_lower not in decision.symbol.lower() and
                text_lower not in decision.reasoning.lower() and
                text_lower not in decision.action.value.lower()):
                return False
        
        # Vérifier les métadonnées
        if query.metadata_filters:
            for key, value in query.metadata_filters.items():
                if key == "symbol" and value.upper() != decision.symbol.upper():
                    return False
                elif key == "action" and value.lower() != decision.action.value.lower():
                    return False
                elif key == "confidence" and value.lower() != decision.confidence.value.lower():
                    return False
                elif key == "min_expected_return" and decision.expected_return < float(value):
                    return False
                elif key == "profitable_only" and value.lower() == "true":
                    if decision.actual_outcome is None or decision.actual_outcome <= 0:
                        return False
        
        return True
    
    def _calculate_relevance_score(
        self,
        decision: DecisionMemory,
        query: MemorySearchQuery
    ) -> float:
        """Calcule le score de pertinence."""
        score = 0.0
        
        if query.text_query:
            text_lower = query.text_query.lower()
            
            # Score basé sur la correspondance exacte du symbole
            if text_lower == decision.symbol.lower():
                score += 1.0
            elif text_lower in decision.symbol.lower():
                score += 0.7
            
            # Score basé sur l'action
            if text_lower == decision.action.value.lower():
                score += 0.6
            elif text_lower in decision.action.value.lower():
                score += 0.4
            
            # Score basé sur le raisonnement
            if text_lower in decision.reasoning.lower():
                score += 0.3
        
        # Score basé sur la fraîcheur
        age_days = (datetime.utcnow() - decision.timestamp).days
        if age_days < 1:
            score += 0.3
        elif age_days < 7:
            score += 0.2
        elif age_days < 30:
            score += 0.1
        
        # Score basé sur la performance (si disponible)
        if decision.actual_outcome is not None:
            if decision.actual_outcome > 0:
                score += 0.2
            elif decision.actual_outcome > -0.05:
                score += 0.1
        
        # Score basé sur le niveau de confiance
        confidence_scores = {
            ConfidenceLevel.VERY_HIGH: 0.3,
            ConfidenceLevel.HIGH: 0.2,
            ConfidenceLevel.MEDIUM: 0.1,
            ConfidenceLevel.LOW: 0.05,
            ConfidenceLevel.VERY_LOW: 0.0
        }
        score += confidence_scores.get(decision.confidence, 0.0)
        
        return min(score, 1.0)
    
    def _get_match_highlights(
        self,
        decision: DecisionMemory,
        query: MemorySearchQuery
    ) -> List[str]:
        """Génère les surlignages de correspondance."""
        highlights = []
        
        highlights.append(f"Symbol: {decision.symbol}")
        highlights.append(f"Action: {decision.action.value}")
        highlights.append(f"Confidence: {decision.confidence.value}")
        
        if decision.actual_outcome is not None:
            highlights.append(f"Outcome: {decision.actual_outcome:.2%}")
        else:
            highlights.append(f"Expected: {decision.expected_return:.2%}")
        
        if query.text_query and query.text_query.lower() in decision.reasoning.lower():
            highlights.append(f"Reasoning: {decision.reasoning[:100]}...")
        
        return highlights[:4]  # Limiter à 4 highlights
    
    # Méthodes de base de données (similaires aux autres gestionnaires)
    async def _init_database(self) -> None:
        """Initialise la base de données SQLite."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS trading_decisions (
                    id TEXT PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    action TEXT NOT NULL,
                    confidence TEXT NOT NULL,
                    reasoning TEXT NOT NULL,
                    expected_return REAL NOT NULL,
                    actual_outcome REAL,
                    risk_assessment TEXT,
                    metadata TEXT
                )
            """)
            
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_decisions_symbol 
                ON trading_decisions(symbol)
            """)
            
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_decisions_timestamp 
                ON trading_decisions(timestamp)
            """)
            
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_decisions_action 
                ON trading_decisions(action)
            """)
            
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_decisions_performance 
                ON trading_decisions(actual_outcome)
            """)
            
            await db.commit()
    
    async def _save_decision_to_db(self, decision: DecisionMemory) -> None:
        """Sauvegarde une décision en base."""
        risk_assessment_json = json.dumps(decision.risk_assessment) if decision.risk_assessment else None
        metadata_json = json.dumps(decision.metadata) if decision.metadata else None
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO trading_decisions 
                (id, symbol, timestamp, updated_at, action, confidence, reasoning, 
                 expected_return, actual_outcome, risk_assessment, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                decision.decision_id,
                decision.symbol,
                decision.timestamp.timestamp(),
                decision.updated_at.timestamp(),
                decision.action.value,
                decision.confidence.value,
                decision.reasoning,
                decision.expected_return,
                decision.actual_outcome,
                risk_assessment_json,
                metadata_json
            ))
            await db.commit()
    
    async def _load_decision_from_db(self, decision_id: str) -> Optional[DecisionMemory]:
        """Charge une décision depuis la base."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT symbol, timestamp, updated_at, action, confidence, reasoning,
                       expected_return, actual_outcome, risk_assessment, metadata
                FROM trading_decisions WHERE id = ?
            """, (decision_id,)) as cursor:
                row = await cursor.fetchone()
                
                if not row:
                    return None
                
                (symbol, timestamp, updated_at, action, confidence, reasoning,
                 expected_return, actual_outcome, risk_assessment_json, metadata_json) = row
                
                risk_assessment = json.loads(risk_assessment_json) if risk_assessment_json else {}
                metadata = json.loads(metadata_json) if metadata_json else {}
                
                return DecisionMemory(
                    decision_id=decision_id,
                    symbol=symbol,
                    timestamp=datetime.fromtimestamp(timestamp),
                    updated_at=datetime.fromtimestamp(updated_at),
                    action=action,
                    confidence=confidence,
                    reasoning=reasoning,
                    expected_return=expected_return,
                    actual_outcome=actual_outcome,
                    risk_assessment=risk_assessment,
                    metadata=metadata
                )
    
    async def _load_decisions_by_symbol_from_db(
        self,
        symbol: str,
        action: Optional[DecisionType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[DecisionMemory]:
        """Charge les décisions par symbole depuis la base."""
        results = []
        
        sql = """SELECT id, symbol, timestamp, updated_at, action, confidence, reasoning,
                        expected_return, actual_outcome, risk_assessment, metadata
                 FROM trading_decisions WHERE symbol = ?"""
        params = [symbol]
        
        if action:
            sql += " AND action = ?"
            params.append(action.value)
        
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
                    (decision_id, symbol, timestamp, updated_at, action_str, confidence_str, reasoning,
                     expected_return, actual_outcome, risk_assessment_json, metadata_json) = row
                    
                    risk_assessment = json.loads(risk_assessment_json) if risk_assessment_json else {}
                    metadata = json.loads(metadata_json) if metadata_json else {}
                    
                    decision = DecisionMemory(
                        decision_id=decision_id,
                        symbol=symbol,
                        timestamp=datetime.fromtimestamp(timestamp),
                        updated_at=datetime.fromtimestamp(updated_at),
                        action=action_str,
                        confidence=confidence_str,
                        reasoning=reasoning,
                        expected_return=expected_return,
                        actual_outcome=actual_outcome,
                        risk_assessment=risk_assessment,
                        metadata=metadata
                    )
                    
                    results.append(decision)
        
        return results
    
    async def _search_decisions_in_db(self, query: MemorySearchQuery) -> List[MemorySearchResult]:
        """Recherche des décisions en base."""
        results = []
        
        sql = """SELECT id, symbol, timestamp, updated_at, action, confidence, reasoning,
                        expected_return, actual_outcome, risk_assessment, metadata
                 FROM trading_decisions WHERE 1=1"""
        params = []
        
        if query.text_query:
            sql += " AND (symbol LIKE ? OR reasoning LIKE ? OR action LIKE ?)"
            params.extend([f"%{query.text_query}%"] * 3)
        
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
                    (decision_id, symbol, timestamp, updated_at, action_str, confidence_str, reasoning,
                     expected_return, actual_outcome, risk_assessment_json, metadata_json) = row
                    
                    risk_assessment = json.loads(risk_assessment_json) if risk_assessment_json else {}
                    metadata = json.loads(metadata_json) if metadata_json else {}
                    
                    decision = DecisionMemory(
                        decision_id=decision_id,
                        symbol=symbol,
                        timestamp=datetime.fromtimestamp(timestamp),
                        updated_at=datetime.fromtimestamp(updated_at),
                        action=action_str,
                        confidence=confidence_str,
                        reasoning=reasoning,
                        expected_return=expected_return,
                        actual_outcome=actual_outcome,
                        risk_assessment=risk_assessment,
                        metadata=metadata
                    )
                    
                    score = self._calculate_relevance_score(decision, query)
                    
                    memory_entry = MemoryEntry(
                        id=decision_id,
                        memory_type=MemoryType.DECISION,
                        content=decision,
                        metadata={
                            "symbol": symbol,
                            "action": action_str,
                            "confidence": confidence_str,
                            "expected_return": expected_return,
                            "actual_outcome": actual_outcome
                        },
                        created_at=datetime.fromtimestamp(timestamp)
                    )
                    
                    results.append(MemorySearchResult(
                        memory_entry=memory_entry,
                        relevance_score=score,
                        match_highlights=self._get_match_highlights(decision, query)
                    ))
        
        return results
    
    async def _delete_decision_from_db(self, decision_id: str) -> None:
        """Supprime une décision de la base."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM trading_decisions WHERE id = ?", (decision_id,))
            await db.commit()
    
    async def _cleanup_expired_decisions_in_db(self, cutoff_time: datetime) -> int:
        """Nettoie les décisions expirées en base."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "DELETE FROM trading_decisions WHERE timestamp < ?",
                (cutoff_time.timestamp(),)
            )
            await db.commit()
            return cursor.rowcount
    
    async def _get_db_decision_count(self) -> int:
        """Retourne le nombre de décisions en base."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT COUNT(*) FROM trading_decisions") as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0