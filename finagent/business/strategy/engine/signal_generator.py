"""
Générateur de signaux de trading.

Ce module transforme les résultats d'évaluation des règles en signaux
de trading structurés avec scoring de confiance et métadonnées.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
import uuid

from ..models.strategy_models import Strategy
from .rule_evaluator import EvaluationResult, EvaluationContext

logger = logging.getLogger(__name__)


class SignalType(str, Enum):
    """Types de signaux de trading."""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    REBALANCE = "rebalance"


class SignalConfidence(str, Enum):
    """Niveaux de confiance des signaux."""
    VERY_LOW = "very_low"     # 0.0 - 0.2
    LOW = "low"               # 0.2 - 0.4
    MEDIUM = "medium"         # 0.4 - 0.6
    HIGH = "high"             # 0.6 - 0.8
    VERY_HIGH = "very_high"   # 0.8 - 1.0


class SignalPriority(str, Enum):
    """Priorités des signaux."""
    CRITICAL = "critical"     # Stop-loss, urgence
    HIGH = "high"            # Signaux forts
    MEDIUM = "medium"        # Signaux normaux
    LOW = "low"              # Signaux faibles


@dataclass
class TradingSignal:
    """Signal de trading structuré."""
    signal_id: str
    strategy_id: str
    symbol: str
    signal_type: SignalType
    timestamp: datetime
    
    # Métriques de confiance
    confidence: float  # 0.0 - 1.0
    confidence_level: SignalConfidence
    priority: SignalPriority
    
    # Détails du signal
    price_target: Optional[float] = None
    quantity: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    
    # Justification
    triggered_conditions: List[str] = None
    reasoning: Optional[str] = None
    
    # Métadonnées
    validity_duration: Optional[timedelta] = None
    market_conditions: Optional[Dict[str, Any]] = None
    risk_metrics: Optional[Dict[str, float]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Initialisation post-creation."""
        if self.triggered_conditions is None:
            self.triggered_conditions = []
        
        if self.signal_id is None:
            self.signal_id = str(uuid.uuid4())
        
        if self.confidence_level is None:
            self.confidence_level = self._calculate_confidence_level()
        
        if self.priority is None:
            self.priority = self._calculate_priority()
    
    def _calculate_confidence_level(self) -> SignalConfidence:
        """Calcule le niveau de confiance basé sur le score."""
        if self.confidence >= 0.8:
            return SignalConfidence.VERY_HIGH
        elif self.confidence >= 0.6:
            return SignalConfidence.HIGH
        elif self.confidence >= 0.4:
            return SignalConfidence.MEDIUM
        elif self.confidence >= 0.2:
            return SignalConfidence.LOW
        else:
            return SignalConfidence.VERY_LOW
    
    def _calculate_priority(self) -> SignalPriority:
        """Calcule la priorité du signal."""
        if self.signal_type in [SignalType.STOP_LOSS, SignalType.TAKE_PROFIT]:
            return SignalPriority.CRITICAL
        elif self.confidence >= 0.7:
            return SignalPriority.HIGH
        elif self.confidence >= 0.5:
            return SignalPriority.MEDIUM
        else:
            return SignalPriority.LOW
    
    def is_valid(self) -> bool:
        """Vérifie si le signal est encore valide."""
        if self.validity_duration is None:
            return True
        
        expiry_time = self.timestamp + self.validity_duration
        return datetime.now() < expiry_time
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire."""
        return {
            'signal_id': self.signal_id,
            'strategy_id': self.strategy_id,
            'symbol': self.symbol,
            'signal_type': self.signal_type.value,
            'timestamp': self.timestamp.isoformat(),
            'confidence': float(self.confidence),
            'confidence_level': self.confidence_level.value,
            'priority': self.priority.value,
            'price_target': float(self.price_target) if self.price_target else None,
            'quantity': float(self.quantity) if self.quantity else None,
            'stop_loss': float(self.stop_loss) if self.stop_loss else None,
            'take_profit': float(self.take_profit) if self.take_profit else None,
            'triggered_conditions': self.triggered_conditions,
            'reasoning': self.reasoning,
            'validity_duration_seconds': self.validity_duration.total_seconds() if self.validity_duration else None,
            'market_conditions': self.market_conditions,
            'risk_metrics': self.risk_metrics,
            'metadata': self.metadata,
            'is_valid': self.is_valid()
        }


class SignalGenerationError(Exception):
    """Exception levée lors d'erreurs de génération de signaux."""
    
    def __init__(self, message: str, strategy_id: Optional[str] = None, error_code: Optional[str] = None):
        self.message = message
        self.strategy_id = strategy_id
        self.error_code = error_code
        super().__init__(self._format_message())
    
    def _format_message(self) -> str:
        """Formate le message d'erreur."""
        if self.strategy_id and self.error_code:
            return f"[{self.error_code}] Stratégie {self.strategy_id}: {self.message}"
        elif self.strategy_id:
            return f"Stratégie {self.strategy_id}: {self.message}"
        elif self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class SignalGenerator:
    """
    Générateur de signaux de trading.
    
    Responsabilités:
    - Transformer les évaluations en signaux structurés
    - Calculer les niveaux de confiance
    - Appliquer les filtres de qualité
    - Gérer les priorités et validités
    - Intégrer la gestion des risques
    """
    
    def __init__(self, 
                 market_data_provider=None,
                 risk_calculator=None,
                 min_confidence_threshold: float = 0.3,
                 default_signal_validity_minutes: int = 60):
        """
        Initialise le générateur de signaux.
        
        Args:
            market_data_provider: Fournisseur de données de marché
            risk_calculator: Calculateur de risques
            min_confidence_threshold: Seuil minimum de confiance
            default_signal_validity_minutes: Validité par défaut des signaux
        """
        self.logger = logging.getLogger(__name__)
        
        # Services externes
        self.market_data_provider = market_data_provider
        self.risk_calculator = risk_calculator
        
        # Configuration
        self.min_confidence_threshold = min_confidence_threshold
        self.default_signal_validity = timedelta(minutes=default_signal_validity_minutes)
        
        # Filtres de qualité
        self.quality_filters = {
            'min_volume_ratio': 0.5,     # Volume min vs moyenne
            'max_spread_pct': 0.02,      # Spread bid-ask max 2%
            'min_liquidity': 10000,      # Liquidité minimum
            'max_volatility': 0.1        # Volatilité max 10%
        }
        
        # Métriques
        self.generation_stats = {
            'total_signals_generated': 0,
            'signals_by_type': {},
            'signals_by_confidence': {},
            'filtered_signals': 0,
            'avg_confidence': 0.0
        }
    
    async def initialize(self) -> None:
        """Initialise le générateur."""
        self.logger.info("Initialisation du générateur de signaux")
        
        # Initialisation des services externes
        if self.market_data_provider:
            await self.market_data_provider.initialize()
        
        if self.risk_calculator:
            await self.risk_calculator.initialize()
        
        self.logger.info("Générateur de signaux initialisé")
    
    async def generate_signals(self, 
                             evaluation_result: EvaluationResult,
                             strategy: Strategy,
                             execution_context) -> List[TradingSignal]:
        """
        Génère des signaux de trading basés sur le résultat d'évaluation.
        
        Args:
            evaluation_result: Résultat de l'évaluation des règles
            strategy: Stratégie source
            execution_context: Contexte d'exécution
            
        Returns:
            List[TradingSignal]: Liste des signaux générés
        """
        try:
            signals = []
            
            # Vérification de la qualité de l'évaluation
            if not self._is_evaluation_valid(evaluation_result):
                self.logger.debug(f"Évaluation invalide pour {evaluation_result.symbol}")
                return signals
            
            # Génération des signaux d'achat
            if evaluation_result.buy_signal_triggered:
                buy_signal = await self._generate_buy_signal(
                    evaluation_result, strategy, execution_context
                )
                if buy_signal and self._passes_quality_filters(buy_signal, execution_context):
                    signals.append(buy_signal)
            
            # Génération des signaux de vente
            if evaluation_result.sell_signal_triggered:
                sell_signal = await self._generate_sell_signal(
                    evaluation_result, strategy, execution_context
                )
                if sell_signal and self._passes_quality_filters(sell_signal, execution_context):
                    signals.append(sell_signal)
            
            # Génération des signaux de gestion des risques
            risk_signals = await self._generate_risk_management_signals(
                evaluation_result, strategy, execution_context
            )
            for risk_signal in risk_signals:
                if self._passes_quality_filters(risk_signal, execution_context):
                    signals.append(risk_signal)
            
            # Mise à jour des statistiques
            self._update_generation_stats(signals)
            
            self.logger.debug(f"Générés {len(signals)} signaux pour {evaluation_result.symbol}")
            return signals
            
        except Exception as e:
            error_msg = f"Erreur génération signaux: {e}"
            self.logger.error(error_msg)
            raise SignalGenerationError(error_msg, strategy.strategy.name, "SIGNAL_GENERATION_FAILED")
    
    async def _generate_buy_signal(self, 
                                 evaluation_result: EvaluationResult,
                                 strategy: Strategy,
                                 execution_context) -> Optional[TradingSignal]:
        """Génère un signal d'achat."""
        try:
            # Calcul des paramètres du signal
            current_price = await self._get_current_price(evaluation_result.symbol)
            if current_price is None:
                return None
            
            # Calcul de la quantité basée sur la gestion des risques
            position_size = self._calculate_position_size(strategy, execution_context, current_price)
            
            # Calcul des niveaux de stop-loss et take-profit
            stop_loss_price = self._calculate_stop_loss_price(
                current_price, strategy.risk_management.stop_loss
            )
            take_profit_price = self._calculate_take_profit_price(
                current_price, strategy.risk_management.take_profit
            )
            
            # Génération du raisonnement
            reasoning = self._generate_signal_reasoning(
                evaluation_result.buy_conditions_details, "achat"
            )
            
            # Conditions déclenchées
            triggered_conditions = [
                detail.condition_id for detail in evaluation_result.buy_conditions_details
                if detail.is_met
            ]
            
            # Calcul des métriques de risque
            risk_metrics = await self._calculate_risk_metrics(
                evaluation_result.symbol, current_price, position_size, execution_context
            )
            
            signal = TradingSignal(
                signal_id=None,  # Sera généré automatiquement
                strategy_id=evaluation_result.strategy_id,
                symbol=evaluation_result.symbol,
                signal_type=SignalType.BUY,
                timestamp=evaluation_result.timestamp,
                confidence=evaluation_result.buy_confidence_score,
                confidence_level=None,  # Calculé automatiquement
                priority=None,  # Calculé automatiquement
                price_target=current_price,
                quantity=position_size,
                stop_loss=stop_loss_price,
                take_profit=take_profit_price,
                triggered_conditions=triggered_conditions,
                reasoning=reasoning,
                validity_duration=self._calculate_signal_validity(strategy),
                market_conditions=await self._get_market_conditions(evaluation_result.symbol),
                risk_metrics=risk_metrics,
                metadata={
                    'strategy_type': strategy.strategy.type.value,
                    'data_quality': evaluation_result.data_quality_score,
                    'evaluation_time_ms': evaluation_result.total_evaluation_time_ms
                }
            )
            
            return signal
            
        except Exception as e:
            self.logger.error(f"Erreur génération signal achat: {e}")
            return None
    
    async def _generate_sell_signal(self, 
                                  evaluation_result: EvaluationResult,
                                  strategy: Strategy,
                                  execution_context) -> Optional[TradingSignal]:
        """Génère un signal de vente."""
        try:
            # Logique similaire au signal d'achat mais pour la vente
            current_price = await self._get_current_price(evaluation_result.symbol)
            if current_price is None:
                return None
            
            # Pour un signal de vente, on peut vendre une position existante
            position_size = await self._get_current_position_size(
                evaluation_result.symbol, execution_context
            )
            
            if position_size <= 0:
                # Pas de position à vendre
                return None
            
            # Génération du raisonnement
            reasoning = self._generate_signal_reasoning(
                evaluation_result.sell_conditions_details, "vente"
            )
            
            # Conditions déclenchées
            triggered_conditions = [
                detail.condition_id for detail in evaluation_result.sell_conditions_details
                if detail.is_met
            ]
            
            # Calcul des métriques de risque
            risk_metrics = await self._calculate_risk_metrics(
                evaluation_result.symbol, current_price, -position_size, execution_context
            )
            
            signal = TradingSignal(
                signal_id=None,
                strategy_id=evaluation_result.strategy_id,
                symbol=evaluation_result.symbol,
                signal_type=SignalType.SELL,
                timestamp=evaluation_result.timestamp,
                confidence=evaluation_result.sell_confidence_score,
                confidence_level=None,
                priority=None,
                price_target=current_price,
                quantity=position_size,
                stop_loss=None,  # Pas de stop-loss pour une vente
                take_profit=None,  # Pas de take-profit pour une vente
                triggered_conditions=triggered_conditions,
                reasoning=reasoning,
                validity_duration=self._calculate_signal_validity(strategy),
                market_conditions=await self._get_market_conditions(evaluation_result.symbol),
                risk_metrics=risk_metrics,
                metadata={
                    'strategy_type': strategy.strategy.type.value,
                    'data_quality': evaluation_result.data_quality_score,
                    'evaluation_time_ms': evaluation_result.total_evaluation_time_ms
                }
            )
            
            return signal
            
        except Exception as e:
            self.logger.error(f"Erreur génération signal vente: {e}")
            return None
    
    async def _generate_risk_management_signals(self, 
                                              evaluation_result: EvaluationResult,
                                              strategy: Strategy,
                                              execution_context) -> List[TradingSignal]:
        """Génère des signaux de gestion des risques."""
        signals = []
        
        try:
            # Vérification des conditions de stop-loss
            for detail in evaluation_result.sell_conditions_details:
                if detail.indicator == 'stop_loss' and detail.is_met:
                    stop_loss_signal = await self._create_stop_loss_signal(
                        evaluation_result, strategy, execution_context, detail
                    )
                    if stop_loss_signal:
                        signals.append(stop_loss_signal)
                
                # Vérification des conditions de take-profit
                elif detail.indicator == 'take_profit' and detail.is_met:
                    take_profit_signal = await self._create_take_profit_signal(
                        evaluation_result, strategy, execution_context, detail
                    )
                    if take_profit_signal:
                        signals.append(take_profit_signal)
            
            return signals
            
        except Exception as e:
            self.logger.error(f"Erreur génération signaux risque: {e}")
            return signals
    
    def _is_evaluation_valid(self, evaluation_result: EvaluationResult) -> bool:
        """Vérifie si l'évaluation est valide pour générer des signaux."""
        # Vérification du statut d'évaluation
        if evaluation_result.status.value not in ['success', 'partial_success']:
            return False
        
        # Vérification de la qualité des données
        if evaluation_result.data_quality_score < 0.3:
            return False
        
        # Vérification de la confiance minimale
        if (evaluation_result.buy_signal_triggered and 
            evaluation_result.buy_confidence_score < self.min_confidence_threshold):
            return False
        
        if (evaluation_result.sell_signal_triggered and 
            evaluation_result.sell_confidence_score < self.min_confidence_threshold):
            return False
        
        return True
    
    def _passes_quality_filters(self, signal: TradingSignal, execution_context) -> bool:
        """Vérifie si un signal passe les filtres de qualité."""
        try:
            # Filtre de confiance minimum
            if signal.confidence < self.min_confidence_threshold:
                self.generation_stats['filtered_signals'] += 1
                return False
            
            # Filtre de conditions de marché
            if signal.market_conditions:
                volume_ratio = signal.market_conditions.get('volume_ratio', 1.0)
                if volume_ratio < self.quality_filters['min_volume_ratio']:
                    self.generation_stats['filtered_signals'] += 1
                    return False
                
                spread_pct = signal.market_conditions.get('spread_pct', 0.0)
                if spread_pct > self.quality_filters['max_spread_pct']:
                    self.generation_stats['filtered_signals'] += 1
                    return False
            
            return True
            
        except Exception as e:
            self.logger.warning(f"Erreur filtres qualité: {e}")
            return False
    
    async def _get_current_price(self, symbol: str) -> Optional[float]:
        """Récupère le prix actuel d'un symbole."""
        try:
            if self.market_data_provider:
                price_data = await self.market_data_provider.get_current_price(symbol)
                return price_data.get('price')
            else:
                # Mode dégradé - retourne None
                return None
        except Exception as e:
            self.logger.warning(f"Erreur récupération prix {symbol}: {e}")
            return None
    
    def _calculate_position_size(self, strategy: Strategy, execution_context, current_price: float) -> float:
        """Calcule la taille de position basée sur la stratégie."""
        try:
            # Position size basée sur la configuration de la stratégie
            position_size_pct = float(strategy.risk_management.position_sizing.value)
            
            # Capital disponible (simplifié)
            available_capital = execution_context.portfolio_state.get('available_capital', 100000)
            
            # Calcul de la taille de position
            position_value = available_capital * position_size_pct
            quantity = position_value / current_price
            
            return round(quantity, 2)
            
        except Exception as e:
            self.logger.warning(f"Erreur calcul taille position: {e}")
            return 0.0
    
    def _calculate_stop_loss_price(self, current_price: float, stop_loss_config) -> Optional[float]:
        """Calcule le prix de stop-loss."""
        if not stop_loss_config:
            return None
        
        try:
            stop_loss_pct = float(stop_loss_config.value)
            stop_loss_price = current_price * (1 - stop_loss_pct)
            return round(stop_loss_price, 2)
        except Exception as e:
            self.logger.warning(f"Erreur calcul stop-loss: {e}")
            return None
    
    def _calculate_take_profit_price(self, current_price: float, take_profit_config) -> Optional[float]:
        """Calcule le prix de take-profit."""
        if not take_profit_config:
            return None
        
        try:
            take_profit_pct = float(take_profit_config.value)
            take_profit_price = current_price * (1 + take_profit_pct)
            return round(take_profit_price, 2)
        except Exception as e:
            self.logger.warning(f"Erreur calcul take-profit: {e}")
            return None
    
    def _generate_signal_reasoning(self, conditions_details: List, action: str) -> str:
        """Génère le raisonnement du signal."""
        triggered_conditions = [d for d in conditions_details if d.is_met]
        
        if not triggered_conditions:
            return f"Signal de {action} généré"
        
        reasoning_parts = [f"Signal de {action} déclenché par:"]
        
        for detail in triggered_conditions[:3]:  # Limite à 3 conditions principales
            condition_desc = f"- {detail.indicator} {detail.operator} {detail.threshold}"
            if detail.actual_value is not None:
                condition_desc += f" (valeur actuelle: {detail.actual_value})"
            reasoning_parts.append(condition_desc)
        
        if len(triggered_conditions) > 3:
            reasoning_parts.append(f"- ... et {len(triggered_conditions) - 3} autres conditions")
        
        return "\n".join(reasoning_parts)
    
    def _calculate_signal_validity(self, strategy: Strategy) -> timedelta:
        """Calcule la durée de validité du signal."""
        # Basé sur l'horizon temporel de la stratégie
        time_horizon = strategy.settings.time_horizon if strategy.settings else None
        
        if time_horizon == 'short':
            return timedelta(minutes=30)
        elif time_horizon == 'medium':
            return timedelta(hours=4)
        elif time_horizon == 'long':
            return timedelta(hours=24)
        else:
            return self.default_signal_validity
    
    async def _get_market_conditions(self, symbol: str) -> Dict[str, Any]:
        """Récupère les conditions de marché."""
        try:
            if self.market_data_provider:
                return await self.market_data_provider.get_market_conditions(symbol)
            else:
                return {}
        except Exception as e:
            self.logger.warning(f"Erreur conditions marché {symbol}: {e}")
            return {}
    
    async def _calculate_risk_metrics(self, symbol: str, price: float, 
                                    quantity: float, execution_context) -> Dict[str, float]:
        """Calcule les métriques de risque."""
        try:
            if self.risk_calculator:
                return await self.risk_calculator.calculate_position_risk(
                    symbol, price, quantity, execution_context.portfolio_state
                )
            else:
                # Métriques de base
                position_value = abs(price * quantity)
                portfolio_value = execution_context.portfolio_state.get('total_value', 100000)
                
                return {
                    'position_value': position_value,
                    'portfolio_exposure': position_value / portfolio_value if portfolio_value > 0 else 0,
                    'estimated_risk': min(0.1, position_value / portfolio_value * 0.2)
                }
        except Exception as e:
            self.logger.warning(f"Erreur calcul risque: {e}")
            return {}
    
    async def _get_current_position_size(self, symbol: str, execution_context) -> float:
        """Récupère la taille de position actuelle."""
        try:
            portfolio_state = execution_context.portfolio_state
            positions = portfolio_state.get('positions', {})
            position = positions.get(symbol, {})
            return position.get('quantity', 0.0)
        except Exception as e:
            self.logger.warning(f"Erreur récupération position {symbol}: {e}")
            return 0.0
    
    async def _create_stop_loss_signal(self, evaluation_result, strategy, execution_context, detail) -> Optional[TradingSignal]:
        """Crée un signal de stop-loss."""
        try:
            current_price = await self._get_current_price(evaluation_result.symbol)
            position_size = await self._get_current_position_size(evaluation_result.symbol, execution_context)
            
            if not current_price or position_size <= 0:
                return None
            
            return TradingSignal(
                signal_id=None,
                strategy_id=evaluation_result.strategy_id,
                symbol=evaluation_result.symbol,
                signal_type=SignalType.STOP_LOSS,
                timestamp=evaluation_result.timestamp,
                confidence=min(1.0, detail.confidence * 1.2),  # Boost confiance pour stop-loss
                confidence_level=None,
                priority=SignalPriority.CRITICAL,
                price_target=current_price,
                quantity=position_size,
                triggered_conditions=[detail.condition_id],
                reasoning=f"Stop-loss déclenché: {detail.indicator} = {detail.actual_value}",
                validity_duration=timedelta(minutes=5),  # Très courte validité
                metadata={'trigger_type': 'stop_loss', 'urgency': 'high'}
            )
        except Exception as e:
            self.logger.error(f"Erreur création signal stop-loss: {e}")
            return None
    
    async def _create_take_profit_signal(self, evaluation_result, strategy, execution_context, detail) -> Optional[TradingSignal]:
        """Crée un signal de take-profit."""
        try:
            current_price = await self._get_current_price(evaluation_result.symbol)
            position_size = await self._get_current_position_size(evaluation_result.symbol, execution_context)
            
            if not current_price or position_size <= 0:
                return None
            
            return TradingSignal(
                signal_id=None,
                strategy_id=evaluation_result.strategy_id,
                symbol=evaluation_result.symbol,
                signal_type=SignalType.TAKE_PROFIT,
                timestamp=evaluation_result.timestamp,
                confidence=detail.confidence,
                confidence_level=None,
                priority=SignalPriority.HIGH,
                price_target=current_price,
                quantity=position_size,
                triggered_conditions=[detail.condition_id],
                reasoning=f"Take-profit déclenché: {detail.indicator} = {detail.actual_value}",
                validity_duration=timedelta(minutes=15),
                metadata={'trigger_type': 'take_profit'}
            )
        except Exception as e:
            self.logger.error(f"Erreur création signal take-profit: {e}")
            return None
    
    def _update_generation_stats(self, signals: List[TradingSignal]) -> None:
        """Met à jour les statistiques de génération."""
        self.generation_stats['total_signals_generated'] += len(signals)
        
        # Statistiques par type
        for signal in signals:
            signal_type = signal.signal_type.value
            self.generation_stats['signals_by_type'][signal_type] = (
                self.generation_stats['signals_by_type'].get(signal_type, 0) + 1
            )
            
            # Statistiques par niveau de confiance
            confidence_level = signal.confidence_level.value
            self.generation_stats['signals_by_confidence'][confidence_level] = (
                self.generation_stats['signals_by_confidence'].get(confidence_level, 0) + 1
            )
        
        # Confiance moyenne
        if signals:
            total_confidence = sum(s.confidence for s in signals)
            current_avg = self.generation_stats['avg_confidence']
            total_signals = self.generation_stats['total_signals_generated']
            
            new_avg = ((current_avg * (total_signals - len(signals))) + total_confidence) / total_signals
            self.generation_stats['avg_confidence'] = new_avg
    
    def get_generation_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de génération."""
        return {
            **self.generation_stats,
            'min_confidence_threshold': self.min_confidence_threshold,
            'default_validity_minutes': self.default_signal_validity.total_seconds() / 60,
            'quality_filters': self.quality_filters
        }
    
    def reset_stats(self) -> None:
        """Remet à zéro les statistiques."""
        self.generation_stats = {
            'total_signals_generated': 0,
            'signals_by_type': {},
            'signals_by_confidence': {},
            'filtered_signals': 0,
            'avg_confidence': 0.0
        }
        self.logger.info("Statistiques de génération remises à zéro")