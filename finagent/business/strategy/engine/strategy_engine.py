"""
Moteur principal d'exécution des stratégies de trading.

Ce module contient le moteur central qui orchestrate l'exécution des stratégies,
coordonne l'évaluation des règles et la génération de signaux.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, AsyncGenerator
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from ..models.strategy_models import Strategy
from ..parser.rule_compiler import CompiledRule, RuleCompiler
from .rule_evaluator import RuleEvaluator, EvaluationContext
from .signal_generator import SignalGenerator, TradingSignal

logger = logging.getLogger(__name__)


class EngineState(str, Enum):
    """États du moteur de stratégie."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"


class ExecutionMode(str, Enum):
    """Modes d'exécution."""
    SIMULATION = "simulation"
    PAPER_TRADING = "paper_trading"
    LIVE_TRADING = "live_trading"
    BACKTEST = "backtest"


@dataclass
class ExecutionContext:
    """Contexte d'exécution d'une stratégie."""
    strategy_id: str
    symbol: str
    timestamp: datetime
    market_data: Dict[str, Any]
    portfolio_state: Dict[str, Any]
    execution_mode: ExecutionMode
    metadata: Dict[str, Any]
    market_conditions: Optional[Dict[str, Any]] = None
    execution_config: Optional[Dict[str, Any]] = None
    risk_limits: Optional[Dict[str, Any]] = None


@dataclass
class ExecutionResult:
    """Résultat d'exécution d'une stratégie."""
    strategy_id: str
    symbol: str
    timestamp: datetime
    signals: List[TradingSignal]
    performance_metrics: Dict[str, float]
    execution_time_ms: float
    error: Optional[str] = None
    metadata: Dict[str, Any] = None


class EngineError(Exception):
    """Exception levée par le moteur de stratégie."""
    
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


class StrategyEngine:
    """
    Moteur principal d'exécution des stratégies de trading.
    
    Responsabilités:
    - Charger et compiler les stratégies
    - Orchestrer l'exécution en temps réel
    - Coordonner l'évaluation des règles
    - Gérer les performances et la surveillance
    - Intégrer avec les sources de données
    """
    
    def __init__(self, 
                 data_provider=None,
                 portfolio_manager=None,
                 risk_manager=None,
                 execution_mode: ExecutionMode = ExecutionMode.SIMULATION):
        """
        Initialise le moteur de stratégie.
        
        Args:
            data_provider: Fournisseur de données de marché
            portfolio_manager: Gestionnaire de portefeuille
            risk_manager: Gestionnaire de risques
            execution_mode: Mode d'exécution
        """
        self.logger = logging.getLogger(__name__)
        
        # Composants externes
        self.data_provider = data_provider
        self.portfolio_manager = portfolio_manager
        self.risk_manager = risk_manager
        
        # Configuration
        self.execution_mode = execution_mode
        self.state = EngineState.STOPPED
        
        # Composants internes
        self.rule_compiler = RuleCompiler()
        self.rule_evaluator = RuleEvaluator()
        self.signal_generator = SignalGenerator()
        
        # Stratégies actives
        self.active_strategies: Dict[str, Dict[str, Any]] = {}
        self.compiled_rules: Dict[str, CompiledRule] = {}
        
        # Métriques et surveillance
        self.performance_metrics: Dict[str, Dict[str, float]] = {}
        self.execution_stats: Dict[str, Any] = {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'avg_execution_time_ms': 0.0,
            'last_execution': None
        }
        
        # Configuration des timeouts
        self.execution_timeout = 30.0  # secondes
        self.evaluation_timeout = 10.0  # secondes
    
    async def initialize(self) -> None:
        """Initialise le moteur de stratégie."""
        await self.start()
    
    async def start(self) -> None:
        """Démarre le moteur de stratégie."""
        if self.state != EngineState.STOPPED:
            raise EngineError(f"Impossible de démarrer: état actuel {self.state}")
        
        try:
            self.state = EngineState.STARTING
            self.logger.info("Démarrage du moteur de stratégie...")
            
            # Initialisation des composants
            await self._initialize_components()
            
            # Validation de la configuration
            await self._validate_configuration()
            
            self.state = EngineState.RUNNING
            self.logger.info("Moteur de stratégie démarré avec succès")
            
        except Exception as e:
            self.state = EngineState.ERROR
            error_msg = f"Échec du démarrage du moteur: {e}"
            self.logger.error(error_msg)
            raise EngineError(error_msg, error_code="ENGINE_START_FAILED")
    
    async def stop(self) -> None:
        """Arrête le moteur de stratégie."""
        if self.state == EngineState.STOPPED:
            return
        
        try:
            self.logger.info("Arrêt du moteur de stratégie...")
            
            # Arrêt gracieux des stratégies actives
            await self._stop_active_strategies()
            
            # Sauvegarde des métriques
            await self._save_performance_metrics()
            
            self.state = EngineState.STOPPED
            self.logger.info("Moteur de stratégie arrêté")
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'arrêt: {e}")
            self.state = EngineState.ERROR
    
    async def load_strategy(self, strategy: Strategy, strategy_id: Optional[str] = None) -> str:
        """
        Charge et compile une stratégie.
        
        Args:
            strategy: Stratégie à charger
            strategy_id: Identifiant optionnel de la stratégie
            
        Returns:
            str: Identifiant de la stratégie chargée
            
        Raises:
            EngineError: Si le chargement échoue
        """
        if strategy_id is None:
            strategy_id = f"strategy_{len(self.active_strategies) + 1}"
        
        try:
            self.logger.info(f"Chargement de la stratégie {strategy_id}")
            
            # Compilation des règles
            compiled_rule = self.rule_compiler.compile(strategy.rules, strategy_id)
            self.compiled_rules[strategy_id] = compiled_rule
            
            # Stockage de la stratégie
            self.active_strategies[strategy_id] = {
                'strategy': strategy,
                'compiled_rule': compiled_rule,
                'loaded_at': datetime.now(),
                'execution_count': 0,
                'last_execution': None,
                'status': 'loaded'
            }
            
            # Initialisation des métriques
            self.performance_metrics[strategy_id] = {
                'total_signals': 0,
                'buy_signals': 0,
                'sell_signals': 0,
                'avg_confidence': 0.0,
                'success_rate': 0.0,
                'avg_execution_time_ms': 0.0
            }
            
            self.logger.info(f"Stratégie {strategy_id} chargée avec succès")
            return strategy_id
            
        except Exception as e:
            error_msg = f"Échec du chargement de la stratégie: {e}"
            self.logger.error(error_msg)
            raise EngineError(error_msg, strategy_id, "STRATEGY_LOAD_FAILED")
    
    async def unload_strategy(self, strategy_id: str) -> None:
        """
        Décharge une stratégie.
        
        Args:
            strategy_id: Identifiant de la stratégie
        """
        if strategy_id not in self.active_strategies:
            raise EngineError(f"Stratégie {strategy_id} non trouvée", strategy_id)
        
        try:
            self.logger.info(f"Déchargement de la stratégie {strategy_id}")
            
            # Suppression des références
            del self.active_strategies[strategy_id]
            del self.compiled_rules[strategy_id]
            
            # Conservation des métriques pour historique
            # (ne supprime pas performance_metrics)
            
            self.logger.info(f"Stratégie {strategy_id} déchargée")
            
        except Exception as e:
            error_msg = f"Erreur lors du déchargement: {e}"
            self.logger.error(error_msg)
            raise EngineError(error_msg, strategy_id, "STRATEGY_UNLOAD_FAILED")
    
    async def execute_strategy(self, strategy_id: str, execution_context: ExecutionContext) -> ExecutionResult:
        """
        Exécute une stratégie pour un contexte donné.
        
        Args:
            strategy_id: Identifiant de la stratégie
            execution_context: Contexte d'exécution
            
        Returns:
            ExecutionResult: Résultat de l'exécution
        """
        if self.state != EngineState.RUNNING:
            raise EngineError(f"Moteur non en marche: {self.state}")
        
        if strategy_id not in self.active_strategies:
            raise EngineError(f"Stratégie {strategy_id} non trouvée", strategy_id)
        
        start_time = datetime.now()
        
        try:
            strategy_data = self.active_strategies[strategy_id]
            strategy = strategy_data['strategy']
            compiled_rule = strategy_data['compiled_rule']
            
            # Mise à jour des statistiques
            strategy_data['execution_count'] += 1
            strategy_data['last_execution'] = start_time
            self.execution_stats['total_executions'] += 1
            
            # Vérification des risques (si activée)
            if self.risk_manager:
                risk_check = await self._check_risk_limits(strategy_id, execution_context)
                if not risk_check['allowed']:
                    return ExecutionResult(
                        strategy_id=strategy_id,
                        symbol=execution_context.symbol,
                        timestamp=start_time,
                        signals=[],
                        performance_metrics={},
                        execution_time_ms=0.0,
                        error=f"Exécution bloquée par gestion des risques: {risk_check['reason']}"
                    )
            
            # Évaluation des règles
            evaluation_context = EvaluationContext(
                strategy_id=strategy_id,
                symbol=execution_context.symbol,
                market_data=execution_context.market_data,
                portfolio_state=execution_context.portfolio_state,
                timestamp=execution_context.timestamp
            )
            
            evaluation_result = await asyncio.wait_for(
                self.rule_evaluator.evaluate(compiled_rule, evaluation_context),
                timeout=self.evaluation_timeout
            )
            
            # Génération des signaux
            signals = await self.signal_generator.generate_signals(
                evaluation_result, strategy, execution_context
            )
            
            # Calcul des métriques de performance
            performance_metrics = self._calculate_performance_metrics(
                strategy_id, signals, evaluation_result
            )
            
            # Calcul du temps d'exécution
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Mise à jour des statistiques
            self._update_execution_stats(strategy_id, execution_time, True)
            
            result = ExecutionResult(
                strategy_id=strategy_id,
                symbol=execution_context.symbol,
                timestamp=start_time,
                signals=signals,
                performance_metrics=performance_metrics,
                execution_time_ms=execution_time,
                metadata={
                    'evaluation_result': evaluation_result.dict() if hasattr(evaluation_result, 'dict') else {},
                    'strategy_config': strategy.strategy.dict()
                }
            )
            
            self.logger.debug(f"Stratégie {strategy_id} exécutée en {execution_time:.2f}ms")
            return result
            
        except asyncio.TimeoutError:
            self._update_execution_stats(strategy_id, 0.0, False)
            error_msg = f"Timeout lors de l'exécution (>{self.execution_timeout}s)"
            self.logger.error(error_msg)
            raise EngineError(error_msg, strategy_id, "EXECUTION_TIMEOUT")
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            self._update_execution_stats(strategy_id, execution_time, False)
            error_msg = f"Erreur lors de l'exécution: {e}"
            self.logger.error(error_msg)
            raise EngineError(error_msg, strategy_id, "EXECUTION_FAILED")
    
    async def execute_all_strategies(self, market_data: Dict[str, Any], 
                                   symbols: List[str]) -> List[ExecutionResult]:
        """
        Exécute toutes les stratégies actives pour les symboles donnés.
        
        Args:
            market_data: Données de marché
            symbols: Liste des symboles à traiter
            
        Returns:
            List[ExecutionResult]: Résultats d'exécution
        """
        results = []
        
        for symbol in symbols:
            for strategy_id in self.active_strategies.keys():
                try:
                    # Vérification de l'univers de la stratégie
                    strategy = self.active_strategies[strategy_id]['strategy']
                    if not self._symbol_in_strategy_universe(symbol, strategy):
                        continue
                    
                    # Contexte d'exécution
                    execution_context = ExecutionContext(
                        strategy_id=strategy_id,
                        symbol=symbol,
                        timestamp=datetime.now(),
                        market_data=market_data.get(symbol, {}),
                        portfolio_state=await self._get_portfolio_state(symbol) if self.portfolio_manager else {},
                        execution_mode=self.execution_mode,
                        metadata={}
                    )
                    
                    # Exécution
                    result = await self.execute_strategy(strategy_id, execution_context)
                    results.append(result)
                    
                except Exception as e:
                    self.logger.error(f"Erreur lors de l'exécution de {strategy_id} pour {symbol}: {e}")
                    # Continue avec les autres stratégies
        
        return results
    
    async def get_engine_status(self) -> Dict[str, Any]:
        """Retourne le statut du moteur."""
        return {
            'state': self.state.value,
            'execution_mode': self.execution_mode.value,
            'active_strategies_count': len(self.active_strategies),
            'active_strategies': list(self.active_strategies.keys()),
            'execution_stats': self.execution_stats,
            'performance_summary': self._get_performance_summary(),
            'uptime_seconds': self._get_uptime_seconds(),
            'memory_usage': self._get_memory_usage()
        }
    
    async def _initialize_components(self) -> None:
        """Initialise les composants du moteur."""
        # Initialisation des évaluateurs
        await self.rule_evaluator.initialize()
        await self.signal_generator.initialize()
        
        # Configuration du data provider
        if self.data_provider:
            await self.data_provider.connect()
    
    async def _validate_configuration(self) -> None:
        """Valide la configuration du moteur."""
        if not self.data_provider:
            self.logger.warning("Aucun fournisseur de données configuré")
        
        if not self.portfolio_manager and self.execution_mode != ExecutionMode.SIMULATION:
            raise EngineError("Gestionnaire de portefeuille requis pour ce mode d'exécution")
    
    async def _stop_active_strategies(self) -> None:
        """Arrête toutes les stratégies actives."""
        for strategy_id in list(self.active_strategies.keys()):
            try:
                await self.unload_strategy(strategy_id)
            except Exception as e:
                self.logger.error(f"Erreur lors de l'arrêt de {strategy_id}: {e}")
    
    async def _save_performance_metrics(self) -> None:
        """Sauvegarde les métriques de performance."""
        # Implementation dépendante du système de persistance
        self.logger.info("Métriques de performance sauvegardées")
    
    async def _check_risk_limits(self, strategy_id: str, context: ExecutionContext) -> Dict[str, Any]:
        """Vérifie les limites de risque."""
        if not self.risk_manager:
            return {'allowed': True}
        
        # Placeholder - implémentation dépendante du risk manager
        return {'allowed': True, 'reason': None}
    
    async def _get_portfolio_state(self, symbol: str) -> Dict[str, Any]:
        """Récupère l'état du portefeuille pour un symbole."""
        if not self.portfolio_manager:
            return {}
        
        # Placeholder - implémentation dépendante du portfolio manager
        return {
            'position': 0,
            'avg_cost': 0.0,
            'unrealized_pnl': 0.0
        }
    
    def _symbol_in_strategy_universe(self, symbol: str, strategy: Strategy) -> bool:
        """Vérifie si un symbole fait partie de l'univers de la stratégie."""
        if not strategy.universe or not strategy.universe.watchlist:
            return True  # Pas de restriction
        
        return symbol.upper() in [s.upper() for s in strategy.universe.watchlist]
    
    def _calculate_performance_metrics(self, strategy_id: str, signals: List[TradingSignal], 
                                     evaluation_result) -> Dict[str, float]:
        """Calcule les métriques de performance."""
        metrics = {}
        
        if signals:
            metrics['signal_count'] = len(signals)
            metrics['avg_confidence'] = sum(s.confidence for s in signals) / len(signals)
            metrics['buy_signals'] = len([s for s in signals if s.signal_type == 'buy'])
            metrics['sell_signals'] = len([s for s in signals if s.signal_type == 'sell'])
        else:
            metrics.update({
                'signal_count': 0,
                'avg_confidence': 0.0,
                'buy_signals': 0,
                'sell_signals': 0
            })
        
        # Mise à jour des métriques cumulées
        if strategy_id in self.performance_metrics:
            cum_metrics = self.performance_metrics[strategy_id]
            cum_metrics['total_signals'] += metrics['signal_count']
            cum_metrics['buy_signals'] += metrics['buy_signals']
            cum_metrics['sell_signals'] += metrics['sell_signals']
        
        return metrics
    
    def _update_execution_stats(self, strategy_id: str, execution_time_ms: float, success: bool) -> None:
        """Met à jour les statistiques d'exécution."""
        if success:
            self.execution_stats['successful_executions'] += 1
        else:
            self.execution_stats['failed_executions'] += 1
        
        # Mise à jour du temps d'exécution moyen
        total_exec = self.execution_stats['total_executions']
        current_avg = self.execution_stats['avg_execution_time_ms']
        new_avg = ((current_avg * (total_exec - 1)) + execution_time_ms) / total_exec
        self.execution_stats['avg_execution_time_ms'] = new_avg
        
        self.execution_stats['last_execution'] = datetime.now().isoformat()
    
    def _get_performance_summary(self) -> Dict[str, float]:
        """Génère un résumé des performances."""
        if not self.performance_metrics:
            return {}
        
        total_signals = sum(m.get('total_signals', 0) for m in self.performance_metrics.values())
        total_buy = sum(m.get('buy_signals', 0) for m in self.performance_metrics.values())
        total_sell = sum(m.get('sell_signals', 0) for m in self.performance_metrics.values())
        
        return {
            'total_signals_generated': total_signals,
            'total_buy_signals': total_buy,
            'total_sell_signals': total_sell,
            'active_strategies': len(self.active_strategies),
            'success_rate': (self.execution_stats['successful_executions'] / 
                           max(1, self.execution_stats['total_executions'])) * 100
        }
    
    def _get_uptime_seconds(self) -> float:
        """Calcule le temps de fonctionnement."""
        # Implémentation simplifiée
        return 0.0
    
    def _get_memory_usage(self) -> Dict[str, float]:
        """Calcule l'utilisation mémoire."""
        # Implémentation simplifiée
        return {'strategies_mb': len(self.active_strategies) * 0.1}
    
    async def cleanup(self) -> None:
        """Nettoie les ressources du moteur."""
        try:
            self.logger.info("Nettoyage du moteur de stratégie...")
            
            # Arrêt de toutes les stratégies actives
            await self._stop_active_strategies()
            
            # Nettoyage des composants
            if hasattr(self.rule_evaluator, 'cleanup'):
                await self.rule_evaluator.cleanup()
            
            if hasattr(self.signal_generator, 'cleanup'):
                await self.signal_generator.cleanup()
            
            # Déconnexion du data provider
            if self.data_provider and hasattr(self.data_provider, 'disconnect'):
                await self.data_provider.disconnect()
            
            # Sauvegarde finale des métriques
            await self._save_performance_metrics()
            
            # Nettoyage des structures de données
            self.active_strategies.clear()
            self.compiled_rules.clear()
            self.performance_metrics.clear()
            
            self.state = EngineState.STOPPED
            self.logger.info("Nettoyage du moteur terminé")
            
        except Exception as e:
            self.logger.error(f"Erreur lors du nettoyage: {e}")
            raise EngineError(f"Échec du nettoyage: {e}")