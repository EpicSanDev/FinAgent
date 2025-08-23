"""
Évaluateur de règles pour les stratégies de trading.

Ce module contient la logique d'évaluation des règles compilées
en utilisant les données de marché en temps réel.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from ..parser.rule_compiler import CompiledRule, CompiledCondition
from ..models.condition_models import IndicatorCalculationResult

logger = logging.getLogger(__name__)


class EvaluationStatus(str, Enum):
    """Statuts d'évaluation."""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    INSUFFICIENT_DATA = "insufficient_data"


@dataclass
class EvaluationContext:
    """Contexte d'évaluation des règles."""
    strategy_id: str
    symbol: str
    timestamp: datetime
    market_data: Dict[str, Any]
    portfolio_state: Dict[str, Any]
    indicators_cache: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ConditionEvaluationDetail:
    """Détail de l'évaluation d'une condition."""
    condition_id: str
    indicator: str
    operator: str
    threshold: Any
    actual_value: Any
    is_met: bool
    confidence: float
    evaluation_time_ms: float
    error: Optional[str] = None


@dataclass
class EvaluationResult:
    """Résultat de l'évaluation des règles."""
    strategy_id: str
    symbol: str
    timestamp: datetime
    
    # Résultats des conditions d'achat
    buy_signal_triggered: bool
    buy_confidence_score: float
    buy_conditions_details: List[ConditionEvaluationDetail]
    
    # Résultats des conditions de vente
    sell_signal_triggered: bool
    sell_confidence_score: float
    sell_conditions_details: List[ConditionEvaluationDetail]
    
    # Métadonnées d'évaluation
    status: EvaluationStatus
    total_evaluation_time_ms: float
    data_quality_score: float
    errors: List[str]
    
    def dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire."""
        return {
            'strategy_id': self.strategy_id,
            'symbol': self.symbol,
            'timestamp': self.timestamp.isoformat(),
            'buy_signal_triggered': self.buy_signal_triggered,
            'buy_confidence_score': float(self.buy_confidence_score),
            'sell_signal_triggered': self.sell_signal_triggered,
            'sell_confidence_score': float(self.sell_confidence_score),
            'status': self.status.value,
            'total_evaluation_time_ms': self.total_evaluation_time_ms,
            'data_quality_score': self.data_quality_score,
            'errors': self.errors,
            'buy_conditions_count': len(self.buy_conditions_details),
            'sell_conditions_count': len(self.sell_conditions_details)
        }


class EvaluationError(Exception):
    """Exception levée lors d'erreurs d'évaluation."""
    
    def __init__(self, message: str, condition_id: Optional[str] = None, error_code: Optional[str] = None):
        self.message = message
        self.condition_id = condition_id
        self.error_code = error_code
        super().__init__(self._format_message())
    
    def _format_message(self) -> str:
        """Formate le message d'erreur."""
        if self.condition_id and self.error_code:
            return f"[{self.error_code}] Condition {self.condition_id}: {self.message}"
        elif self.condition_id:
            return f"Condition {self.condition_id}: {self.message}"
        elif self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class RuleEvaluator:
    """
    Évaluateur de règles compilées pour les stratégies de trading.
    
    Responsabilités:
    - Évaluer les conditions compilées avec les données de marché
    - Calculer les scores de confiance
    - Gérer la cache des indicateurs
    - Surveiller les performances d'évaluation
    """
    
    def __init__(self, 
                 indicators_service=None,
                 cache_ttl_seconds: int = 300,
                 max_evaluation_time_ms: float = 5000.0):
        """
        Initialise l'évaluateur de règles.
        
        Args:
            indicators_service: Service de calcul d'indicateurs
            cache_ttl_seconds: TTL du cache des indicateurs
            max_evaluation_time_ms: Temps maximum d'évaluation
        """
        self.logger = logging.getLogger(__name__)
        
        # Services externes
        self.indicators_service = indicators_service
        
        # Configuration
        self.cache_ttl_seconds = cache_ttl_seconds
        self.max_evaluation_time_ms = max_evaluation_time_ms
        
        # Cache des indicateurs
        self.indicators_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_timestamps: Dict[str, datetime] = {}
        
        # Métriques de performance
        self.evaluation_stats = {
            'total_evaluations': 0,
            'successful_evaluations': 0,
            'failed_evaluations': 0,
            'avg_evaluation_time_ms': 0.0,
            'cache_hit_rate': 0.0,
            'cache_hits': 0,
            'cache_misses': 0
        }
        
        # Seuils de qualité des données
        self.data_quality_thresholds = {
            'min_price_data_points': 20,
            'max_data_age_minutes': 60,
            'min_volume_threshold': 1000
        }
    
    async def initialize(self) -> None:
        """Initialise l'évaluateur."""
        self.logger.info("Initialisation de l'évaluateur de règles")
        
        # Initialisation du service d'indicateurs si disponible
        if self.indicators_service:
            await self.indicators_service.initialize()
        
        self.logger.info("Évaluateur de règles initialisé")
    
    async def evaluate(self, compiled_rule: CompiledRule, context: EvaluationContext) -> EvaluationResult:
        """
        Évalue une règle compilée avec le contexte donné.
        
        Args:
            compiled_rule: Règle compilée à évaluer
            context: Contexte d'évaluation
            
        Returns:
            EvaluationResult: Résultat de l'évaluation
        """
        start_time = datetime.now()
        errors = []
        
        try:
            self.logger.debug(f"Évaluation de la règle {compiled_rule.rule_id} pour {context.symbol}")
            
            # Validation des données
            data_quality_score = self._assess_data_quality(context.market_data)
            if data_quality_score < 0.5:
                self.logger.warning(f"Qualité des données faible: {data_quality_score}")
            
            # Préparation du cache d'indicateurs
            await self._prepare_indicators_cache(context)
            
            # Évaluation des conditions d'achat
            buy_signal, buy_confidence, buy_details = await self._evaluate_conditions(
                compiled_rule.buy_conditions, compiled_rule.buy_operator, context, "buy"
            )
            
            # Évaluation des conditions de vente
            sell_signal, sell_confidence, sell_details = await self._evaluate_conditions(
                compiled_rule.sell_conditions, compiled_rule.sell_operator, context, "sell"
            )
            
            # Calcul du temps d'évaluation
            evaluation_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Détermination du statut
            status = self._determine_evaluation_status(
                buy_details, sell_details, evaluation_time, errors
            )
            
            # Mise à jour des statistiques
            self._update_evaluation_stats(evaluation_time, status == EvaluationStatus.SUCCESS)
            
            result = EvaluationResult(
                strategy_id=context.strategy_id,
                symbol=context.symbol,
                timestamp=context.timestamp,
                buy_signal_triggered=buy_signal,
                buy_confidence_score=buy_confidence,
                buy_conditions_details=buy_details,
                sell_signal_triggered=sell_signal,
                sell_confidence_score=sell_confidence,
                sell_conditions_details=sell_details,
                status=status,
                total_evaluation_time_ms=evaluation_time,
                data_quality_score=data_quality_score,
                errors=errors
            )
            
            self.logger.debug(
                f"Évaluation terminée en {evaluation_time:.2f}ms - "
                f"Achat: {buy_signal} ({buy_confidence:.3f}), "
                f"Vente: {sell_signal} ({sell_confidence:.3f})"
            )
            
            return result
            
        except Exception as e:
            evaluation_time = (datetime.now() - start_time).total_seconds() * 1000
            self._update_evaluation_stats(evaluation_time, False)
            
            error_msg = f"Erreur lors de l'évaluation: {e}"
            self.logger.error(error_msg)
            errors.append(error_msg)
            
            # Retourne un résultat d'erreur
            return EvaluationResult(
                strategy_id=context.strategy_id,
                symbol=context.symbol,
                timestamp=context.timestamp,
                buy_signal_triggered=False,
                buy_confidence_score=0.0,
                buy_conditions_details=[],
                sell_signal_triggered=False,
                sell_confidence_score=0.0,
                sell_conditions_details=[],
                status=EvaluationStatus.FAILED,
                total_evaluation_time_ms=evaluation_time,
                data_quality_score=0.0,
                errors=errors
            )
    
    async def _evaluate_conditions(self, 
                                 conditions: List[CompiledCondition],
                                 operator: str,
                                 context: EvaluationContext,
                                 condition_type: str) -> Tuple[bool, float, List[ConditionEvaluationDetail]]:
        """
        Évalue une liste de conditions avec un opérateur logique.
        
        Args:
            conditions: Conditions à évaluer
            operator: Opérateur logique (AND, OR, NOT)
            context: Contexte d'évaluation
            condition_type: Type de condition (buy/sell)
            
        Returns:
            Tuple: (signal_triggered, confidence_score, details)
        """
        if not conditions:
            return False, 0.0, []
        
        details = []
        evaluation_results = []
        weights = []
        
        # Évaluation de chaque condition
        for condition in conditions:
            try:
                start_time = datetime.now()
                
                # Préparation des données pour l'évaluateur
                market_data_with_cache = {
                    **context.market_data,
                    'indicators_cache': context.indicators_cache or {},
                    'portfolio_state': context.portfolio_state
                }
                
                # Évaluation de la condition
                is_met = condition.evaluator(market_data_with_cache)
                
                # Calcul du temps d'évaluation
                eval_time = (datetime.now() - start_time).total_seconds() * 1000
                
                # Récupération des détails pour le logging
                metadata = condition.metadata
                actual_value = self._get_indicator_current_value(
                    metadata.get('indicator', ''), context
                )
                
                # Calcul de la confiance basé sur la qualité des données et la force du signal
                confidence = self._calculate_condition_confidence(
                    is_met, actual_value, metadata.get('value'), context
                )
                
                detail = ConditionEvaluationDetail(
                    condition_id=condition.condition_id,
                    indicator=metadata.get('indicator', 'unknown'),
                    operator=metadata.get('operator', 'unknown'),
                    threshold=metadata.get('value'),
                    actual_value=actual_value,
                    is_met=is_met,
                    confidence=confidence,
                    evaluation_time_ms=eval_time
                )
                
                details.append(detail)
                evaluation_results.append(is_met)
                weights.append(float(condition.weight))
                
            except Exception as e:
                error_msg = f"Erreur évaluation condition {condition.condition_id}: {e}"
                self.logger.warning(error_msg)
                
                detail = ConditionEvaluationDetail(
                    condition_id=condition.condition_id,
                    indicator=condition.metadata.get('indicator', 'unknown'),
                    operator=condition.metadata.get('operator', 'unknown'),
                    threshold=condition.metadata.get('value'),
                    actual_value=None,
                    is_met=False,
                    confidence=0.0,
                    evaluation_time_ms=0.0,
                    error=error_msg
                )
                
                details.append(detail)
                evaluation_results.append(False)
                weights.append(float(condition.weight))
        
        # Application de l'opérateur logique
        if operator.upper() == "AND":
            signal_triggered = all(evaluation_results)
        elif operator.upper() == "OR":
            signal_triggered = any(evaluation_results)
        elif operator.upper() == "NOT":
            signal_triggered = not evaluation_results[0] if evaluation_results else False
        else:
            signal_triggered = False
        
        # Calcul du score de confiance pondéré
        if weights and sum(weights) > 0:
            # Confiance pondérée basée sur les résultats individuels
            weighted_confidences = [
                detail.confidence * weight 
                for detail, weight in zip(details, weights)
            ]
            confidence_score = sum(weighted_confidences) / sum(weights)
        else:
            confidence_score = 0.0
        
        return signal_triggered, confidence_score, details
    
    async def _prepare_indicators_cache(self, context: EvaluationContext) -> None:
        """Prépare le cache des indicateurs."""
        cache_key = f"{context.symbol}_{context.timestamp.strftime('%Y%m%d_%H%M')}"
        
        # Vérification du cache existant
        if cache_key in self.indicators_cache:
            cache_age = (datetime.now() - self.cache_timestamps[cache_key]).total_seconds()
            if cache_age < self.cache_ttl_seconds:
                context.indicators_cache = self.indicators_cache[cache_key]
                self.evaluation_stats['cache_hits'] += 1
                return
        
        # Cache miss - calcul des indicateurs
        self.evaluation_stats['cache_misses'] += 1
        
        if self.indicators_service:
            try:
                # Calcul des indicateurs via le service
                indicators = await self.indicators_service.calculate_all_indicators(
                    context.symbol, context.market_data
                )
                
                # Mise en cache
                self.indicators_cache[cache_key] = indicators
                self.cache_timestamps[cache_key] = datetime.now()
                context.indicators_cache = indicators
                
                # Nettoyage du cache ancien
                await self._cleanup_old_cache_entries()
                
            except Exception as e:
                self.logger.warning(f"Erreur calcul indicateurs: {e}")
                context.indicators_cache = {}
        else:
            # Mode dégradé sans service d'indicateurs
            context.indicators_cache = self._calculate_basic_indicators(context.market_data)
    
    def _assess_data_quality(self, market_data: Dict[str, Any]) -> float:
        """Évalue la qualité des données de marché."""
        quality_score = 1.0
        
        # Vérification de la présence des données de prix
        prices = market_data.get('prices', {})
        if not prices:
            return 0.0
        
        # Vérification du nombre de points de données
        for timeframe, data in prices.items():
            if isinstance(data, list):
                if len(data) < self.data_quality_thresholds['min_price_data_points']:
                    quality_score *= 0.7
        
        # Vérification de l'âge des données
        current_price = market_data.get('current_price')
        if current_price and 'timestamp' in current_price:
            try:
                price_timestamp = datetime.fromisoformat(current_price['timestamp'])
                age_minutes = (datetime.now() - price_timestamp).total_seconds() / 60
                if age_minutes > self.data_quality_thresholds['max_data_age_minutes']:
                    quality_score *= 0.8
            except Exception:
                quality_score *= 0.9
        
        # Vérification du volume
        volume = market_data.get('volume', 0)
        if volume < self.data_quality_thresholds['min_volume_threshold']:
            quality_score *= 0.9
        
        return max(0.0, min(1.0, quality_score))
    
    def _get_indicator_current_value(self, indicator_name: str, context: EvaluationContext) -> Optional[float]:
        """Récupère la valeur actuelle d'un indicateur."""
        try:
            # Recherche dans le cache d'indicateurs
            if context.indicators_cache and indicator_name in context.indicators_cache:
                return context.indicators_cache[indicator_name]
            
            # Recherche dans les données de marché
            if indicator_name in ['price', 'close']:
                prices = context.market_data.get('prices', {}).get('1d', [])
                if prices:
                    return prices[-1].get('close')
            
            elif indicator_name == 'volume':
                prices = context.market_data.get('prices', {}).get('1d', [])
                if prices:
                    return prices[-1].get('volume')
            
            # Autres indicateurs
            market_indicators = context.market_data.get('indicators', {})
            return market_indicators.get(indicator_name)
            
        except Exception as e:
            self.logger.debug(f"Erreur récupération valeur {indicator_name}: {e}")
            return None
    
    def _calculate_condition_confidence(self, is_met: bool, actual_value: Any, 
                                      threshold_value: Any, context: EvaluationContext) -> float:
        """Calcule la confiance d'une condition."""
        base_confidence = 1.0 if is_met else 0.0
        
        # Ajustement basé sur la force du signal
        if actual_value is not None and threshold_value is not None:
            try:
                if isinstance(actual_value, (int, float)) and isinstance(threshold_value, (int, float)):
                    # Calcul de la distance relative au seuil
                    if threshold_value != 0:
                        distance_ratio = abs(actual_value - threshold_value) / abs(threshold_value)
                        # Plus la valeur est éloignée du seuil, plus la confiance est élevée
                        signal_strength = min(1.0, distance_ratio)
                        base_confidence *= (0.5 + 0.5 * signal_strength)
            except Exception:
                pass
        
        # Ajustement basé sur la qualité des données
        data_quality = self._assess_data_quality(context.market_data)
        base_confidence *= data_quality
        
        return max(0.0, min(1.0, base_confidence))
    
    def _determine_evaluation_status(self, buy_details: List[ConditionEvaluationDetail],
                                   sell_details: List[ConditionEvaluationDetail],
                                   evaluation_time_ms: float,
                                   errors: List[str]) -> EvaluationStatus:
        """Détermine le statut de l'évaluation."""
        if errors:
            return EvaluationStatus.FAILED
        
        if evaluation_time_ms > self.max_evaluation_time_ms:
            return EvaluationStatus.TIMEOUT
        
        # Vérification des erreurs dans les détails
        total_conditions = len(buy_details) + len(sell_details)
        failed_conditions = len([d for d in buy_details + sell_details if d.error])
        
        if total_conditions == 0:
            return EvaluationStatus.INSUFFICIENT_DATA
        
        if failed_conditions == 0:
            return EvaluationStatus.SUCCESS
        elif failed_conditions < total_conditions:
            return EvaluationStatus.PARTIAL_SUCCESS
        else:
            return EvaluationStatus.FAILED
    
    def _calculate_basic_indicators(self, market_data: Dict[str, Any]) -> Dict[str, float]:
        """Calcule des indicateurs de base sans service externe."""
        indicators = {}
        
        prices = market_data.get('prices', {}).get('1d', [])
        if prices and len(prices) >= 14:
            # RSI simplifié
            gains = []
            losses = []
            
            for i in range(1, min(15, len(prices))):
                change = prices[i]['close'] - prices[i-1]['close']
                if change > 0:
                    gains.append(change)
                    losses.append(0)
                else:
                    gains.append(0)
                    losses.append(abs(change))
            
            if gains and losses:
                avg_gain = sum(gains) / len(gains)
                avg_loss = sum(losses) / len(losses)
                
                if avg_loss > 0:
                    rs = avg_gain / avg_loss
                    rsi = 100 - (100 / (1 + rs))
                    indicators['rsi'] = rsi
            
            # SMA 20
            if len(prices) >= 20:
                sma_20 = sum(p['close'] for p in prices[-20:]) / 20
                indicators['sma_20'] = sma_20
            
            # Prix actuel
            indicators['price'] = prices[-1]['close']
            indicators['volume'] = prices[-1].get('volume', 0)
        
        return indicators
    
    async def _cleanup_old_cache_entries(self) -> None:
        """Nettoie les entrées anciennes du cache."""
        current_time = datetime.now()
        keys_to_remove = []
        
        for key, timestamp in self.cache_timestamps.items():
            age_seconds = (current_time - timestamp).total_seconds()
            if age_seconds > self.cache_ttl_seconds:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            self.indicators_cache.pop(key, None)
            self.cache_timestamps.pop(key, None)
    
    def _update_evaluation_stats(self, evaluation_time_ms: float, success: bool) -> None:
        """Met à jour les statistiques d'évaluation."""
        self.evaluation_stats['total_evaluations'] += 1
        
        if success:
            self.evaluation_stats['successful_evaluations'] += 1
        else:
            self.evaluation_stats['failed_evaluations'] += 1
        
        # Mise à jour du temps moyen
        total_evals = self.evaluation_stats['total_evaluations']
        current_avg = self.evaluation_stats['avg_evaluation_time_ms']
        new_avg = ((current_avg * (total_evals - 1)) + evaluation_time_ms) / total_evals
        self.evaluation_stats['avg_evaluation_time_ms'] = new_avg
        
        # Calcul du taux de cache hit
        total_cache_ops = self.evaluation_stats['cache_hits'] + self.evaluation_stats['cache_misses']
        if total_cache_ops > 0:
            self.evaluation_stats['cache_hit_rate'] = (
                self.evaluation_stats['cache_hits'] / total_cache_ops
            ) * 100
    
    def get_evaluation_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques d'évaluation."""
        return {
            **self.evaluation_stats,
            'cache_size': len(self.indicators_cache),
            'cache_ttl_seconds': self.cache_ttl_seconds,
            'max_evaluation_time_ms': self.max_evaluation_time_ms
        }
    
    def clear_cache(self) -> None:
        """Vide le cache des indicateurs."""
        self.indicators_cache.clear()
        self.cache_timestamps.clear()
        self.logger.info("Cache des indicateurs vidé")