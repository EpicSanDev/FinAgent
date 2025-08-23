"""
Gestionnaire principal des stratégies de trading.

Ce module orchestre l'ensemble du système de stratégies, gérant le cycle de vie
des stratégies, l'allocation de portefeuille et l'intégration avec les systèmes
externes.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json
import uuid
from contextlib import asynccontextmanager

from ..models.strategy_models import Strategy, StrategyStatus, StrategyPerformance
from ..parser.yaml_parser import StrategyYAMLParser
from ..parser.strategy_validator import StrategyValidator
from ..engine.strategy_engine import StrategyEngine, ExecutionContext, ExecutionMode
from ..engine.signal_generator import TradingSignal, SignalType, SignalPriority
from .portfolio_allocator import PortfolioAllocator, AllocationResult
from .risk_manager import StrategyRiskManager, RiskAssessment

logger = logging.getLogger(__name__)


class ManagerStatus(str, Enum):
    """États du gestionnaire de stratégies."""
    INACTIVE = "inactive"
    INITIALIZING = "initializing"
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"
    SHUTTING_DOWN = "shutting_down"


@dataclass
class StrategyInstance:
    """Instance d'une stratégie en cours d'exécution."""
    strategy_id: str
    strategy: Strategy
    engine: StrategyEngine
    status: StrategyStatus
    created_at: datetime
    last_execution: Optional[datetime] = None
    execution_count: int = 0
    error_count: int = 0
    last_error: Optional[str] = None
    performance: Optional[StrategyPerformance] = None
    active_signals: List[TradingSignal] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire."""
        return {
            'strategy_id': self.strategy_id,
            'strategy_name': self.strategy.strategy.name,
            'strategy_type': self.strategy.strategy.type.value,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'last_execution': self.last_execution.isoformat() if self.last_execution else None,
            'execution_count': self.execution_count,
            'error_count': self.error_count,
            'last_error': self.last_error,
            'performance': self.performance.dict() if self.performance else None,
            'active_signals_count': len(self.active_signals),
            'metadata': self.metadata
        }


@dataclass
class ManagerMetrics:
    """Métriques du gestionnaire de stratégies."""
    total_strategies: int = 0
    active_strategies: int = 0
    paused_strategies: int = 0
    error_strategies: int = 0
    total_signals_generated: int = 0
    signals_executed: int = 0
    average_execution_time_ms: float = 0.0
    success_rate: float = 0.0
    portfolio_value: float = 0.0
    total_pnl: float = 0.0
    risk_metrics: Dict[str, float] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.now)


class StrategyManagerError(Exception):
    """Exception levée par le gestionnaire de stratégies."""
    
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


class StrategyManager:
    """
    Gestionnaire principal des stratégies de trading.
    
    Responsabilités:
    - Gestion du cycle de vie des stratégies
    - Orchestration des exécutions
    - Allocation de portefeuille
    - Gestion des risques
    - Surveillance et métriques
    - Intégration avec systèmes externes
    """
    
    def __init__(self,
                 strategies_directory: str = "strategies",
                 market_data_provider=None,
                 execution_service=None,
                 portfolio_service=None,
                 risk_service=None,
                 max_concurrent_strategies: int = 10,
                 execution_interval_seconds: int = 60,
                 enable_auto_allocation: bool = True):
        """
        Initialise le gestionnaire de stratégies.
        
        Args:
            strategies_directory: Répertoire des fichiers de stratégies
            market_data_provider: Fournisseur de données de marché
            execution_service: Service d'exécution des ordres
            portfolio_service: Service de gestion de portefeuille
            risk_service: Service de gestion des risques
            max_concurrent_strategies: Nombre max de stratégies simultanées
            execution_interval_seconds: Intervalle d'exécution en secondes
            enable_auto_allocation: Active l'allocation automatique
        """
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.strategies_directory = Path(strategies_directory)
        self.max_concurrent_strategies = max_concurrent_strategies
        self.execution_interval = timedelta(seconds=execution_interval_seconds)
        self.enable_auto_allocation = enable_auto_allocation
        
        # Services externes
        self.market_data_provider = market_data_provider
        self.execution_service = execution_service
        self.portfolio_service = portfolio_service
        self.risk_service = risk_service
        
        # Composants internes
        self.yaml_parser = StrategyYAMLParser()
        self.validator = StrategyValidator()
        self.portfolio_allocator = PortfolioAllocator()
        self.risk_manager = StrategyRiskManager()
        
        # État du gestionnaire
        self.status = ManagerStatus.INACTIVE
        self.strategy_instances: Dict[str, StrategyInstance] = {}
        self.execution_queue: asyncio.Queue = asyncio.Queue()
        self.signal_queue: asyncio.Queue = asyncio.Queue()
        
        # Tâches en arrière-plan
        self._execution_task: Optional[asyncio.Task] = None
        self._signal_processing_task: Optional[asyncio.Task] = None
        self._monitoring_task: Optional[asyncio.Task] = None
        
        # Métriques et surveillance
        self.metrics = ManagerMetrics()
        self.performance_history: List[Dict[str, Any]] = []
        
        # Configuration avancée
        self.execution_config = {
            'batch_size': 5,
            'timeout_seconds': 30,
            'retry_attempts': 3,
            'error_threshold': 0.1
        }
        
        # Cache et optimisations
        self._portfolio_cache = {}
        self._market_cache = {}
        self._cache_ttl = timedelta(minutes=5)
        
        self.logger.info("Gestionnaire de stratégies initialisé")
    
    async def initialize(self) -> None:
        """Initialise le gestionnaire et ses composants."""
        try:
            self.status = ManagerStatus.INITIALIZING
            self.logger.info("Initialisation du gestionnaire de stratégies")
            
            # Création du répertoire des stratégies
            self.strategies_directory.mkdir(parents=True, exist_ok=True)
            
            # Initialisation des composants
            await self._initialize_components()
            
            # Chargement des stratégies existantes
            await self._load_existing_strategies()
            
            # Démarrage des tâches d'arrière-plan
            await self._start_background_tasks()
            
            self.status = ManagerStatus.ACTIVE
            self.logger.info("Gestionnaire de stratégies initialisé avec succès")
            
        except Exception as e:
            self.status = ManagerStatus.ERROR
            error_msg = f"Erreur initialisation gestionnaire: {e}"
            self.logger.error(error_msg)
            raise StrategyManagerError(error_msg, error_code="MANAGER_INIT_FAILED")
    
    async def shutdown(self) -> None:
        """Arrête le gestionnaire proprement."""
        try:
            self.status = ManagerStatus.SHUTTING_DOWN
            self.logger.info("Arrêt du gestionnaire de stratégies")
            
            # Arrêt des tâches d'arrière-plan
            await self._stop_background_tasks()
            
            # Arrêt des stratégies actives
            await self._stop_all_strategies()
            
            # Sauvegarde de l'état
            await self._save_manager_state()
            
            self.status = ManagerStatus.INACTIVE
            self.logger.info("Gestionnaire de stratégies arrêté")
            
        except Exception as e:
            self.logger.error(f"Erreur arrêt gestionnaire: {e}")
            raise StrategyManagerError(f"Erreur arrêt gestionnaire: {e}", error_code="MANAGER_SHUTDOWN_FAILED")
    
    async def add_strategy_from_file(self, file_path: str) -> str:
        """
        Ajoute une stratégie depuis un fichier YAML.
        
        Args:
            file_path: Chemin vers le fichier de stratégie
            
        Returns:
            str: ID de la stratégie créée
        """
        try:
            # Chargement et validation de la stratégie
            strategy = self.yaml_parser.parse_file(file_path)
            validation_result = self.validator.validate_strategy(strategy)
            
            if not validation_result.is_valid:
                error_msg = f"Stratégie invalide: {validation_result.get_error_summary()}"
                raise StrategyManagerError(error_msg, error_code="INVALID_STRATEGY")
            
            # Création de l'instance de stratégie
            strategy_id = await self._create_strategy_instance(strategy)
            
            self.logger.info(f"Stratégie {strategy.strategy.name} ajoutée avec ID {strategy_id}")
            return strategy_id
            
        except Exception as e:
            error_msg = f"Erreur ajout stratégie depuis fichier {file_path}: {e}"
            self.logger.error(error_msg)
            raise StrategyManagerError(error_msg, error_code="STRATEGY_ADD_FAILED")
    
    async def add_strategy_from_config(self, strategy_config: Dict[str, Any]) -> str:
        """
        Ajoute une stratégie depuis une configuration.
        
        Args:
            strategy_config: Configuration de la stratégie
            
        Returns:
            str: ID de la stratégie créée
        """
        try:
            # Parsing de la configuration
            strategy = await self.yaml_parser.parse_config(strategy_config)
            validation_result = self.validator.validate_strategy(strategy)
            
            if not validation_result.is_valid:
                error_msg = f"Stratégie invalide: {validation_result.get_error_summary()}"
                raise StrategyManagerError(error_msg, error_code="INVALID_STRATEGY")
            
            # Création de l'instance de stratégie
            strategy_id = await self._create_strategy_instance(strategy)
            
            self.logger.info(f"Stratégie {strategy.strategy.name} ajoutée avec ID {strategy_id}")
            return strategy_id
            
        except Exception as e:
            error_msg = f"Erreur ajout stratégie depuis config: {e}"
            self.logger.error(error_msg)
            raise StrategyManagerError(error_msg, error_code="STRATEGY_ADD_FAILED")
    
    async def start_strategy(self, strategy_id: str) -> None:
        """Démarre une stratégie."""
        try:
            if strategy_id not in self.strategy_instances:
                raise StrategyManagerError(f"Stratégie {strategy_id} non trouvée", 
                                         strategy_id, "STRATEGY_NOT_FOUND")
            
            instance = self.strategy_instances[strategy_id]
            
            if instance.status == StrategyStatus.ACTIVE:
                self.logger.warning(f"Stratégie {strategy_id} déjà active")
                return
            
            # Vérification des limites
            active_count = len([i for i in self.strategy_instances.values() 
                              if i.status == StrategyStatus.ACTIVE])
            
            if active_count >= self.max_concurrent_strategies:
                raise StrategyManagerError(
                    f"Limite de stratégies simultanées atteinte ({self.max_concurrent_strategies})",
                    strategy_id, "MAX_STRATEGIES_REACHED"
                )
            
            # Évaluation des risques
            risk_assessment = await self.risk_manager.assess_strategy_risk(
                instance.strategy, self._get_current_portfolio_state()
            )
            
            if not risk_assessment.is_acceptable:
                raise StrategyManagerError(
                    f"Risque inacceptable: {risk_assessment.rejection_reason}",
                    strategy_id, "RISK_REJECTED"
                )
            
            # Démarrage de la stratégie
            await instance.engine.start()
            instance.status = StrategyStatus.ACTIVE
            instance.metadata['started_at'] = datetime.now().isoformat()
            instance.metadata['risk_assessment'] = risk_assessment.to_dict()
            
            # Ajout à la queue d'exécution
            await self.execution_queue.put(strategy_id)
            
            # Mise à jour des métriques
            self._update_metrics()
            
            self.logger.info(f"Stratégie {strategy_id} démarrée")
            
        except Exception as e:
            self.logger.error(f"Erreur démarrage stratégie {strategy_id}: {e}")
            if strategy_id in self.strategy_instances:
                self.strategy_instances[strategy_id].status = StrategyStatus.ERROR
                self.strategy_instances[strategy_id].last_error = str(e)
            raise
    
    async def stop_strategy(self, strategy_id: str) -> None:
        """Arrête une stratégie."""
        try:
            if strategy_id not in self.strategy_instances:
                raise StrategyManagerError(f"Stratégie {strategy_id} non trouvée", 
                                         strategy_id, "STRATEGY_NOT_FOUND")
            
            instance = self.strategy_instances[strategy_id]
            
            if instance.status not in [StrategyStatus.ACTIVE, StrategyStatus.PAUSED]:
                self.logger.warning(f"Stratégie {strategy_id} non active")
                return
            
            # Arrêt de la stratégie
            await instance.engine.stop()
            instance.status = StrategyStatus.STOPPED
            instance.metadata['stopped_at'] = datetime.now().isoformat()
            
            # Traitement des signaux actifs
            await self._process_active_signals(strategy_id)
            
            # Mise à jour des métriques
            self._update_metrics()
            
            self.logger.info(f"Stratégie {strategy_id} arrêtée")
            
        except Exception as e:
            self.logger.error(f"Erreur arrêt stratégie {strategy_id}: {e}")
            raise StrategyManagerError(f"Erreur arrêt stratégie: {e}", strategy_id, "STRATEGY_STOP_FAILED")
    
    async def pause_strategy(self, strategy_id: str) -> None:
        """Met en pause une stratégie."""
        try:
            if strategy_id not in self.strategy_instances:
                raise StrategyManagerError(f"Stratégie {strategy_id} non trouvée", 
                                         strategy_id, "STRATEGY_NOT_FOUND")
            
            instance = self.strategy_instances[strategy_id]
            
            if instance.status != StrategyStatus.ACTIVE:
                raise StrategyManagerError(f"Stratégie {strategy_id} non active", 
                                         strategy_id, "STRATEGY_NOT_ACTIVE")
            
            await instance.engine.pause()
            instance.status = StrategyStatus.PAUSED
            instance.metadata['paused_at'] = datetime.now().isoformat()
            
            self._update_metrics()
            self.logger.info(f"Stratégie {strategy_id} mise en pause")
            
        except Exception as e:
            self.logger.error(f"Erreur pause stratégie {strategy_id}: {e}")
            raise StrategyManagerError(f"Erreur pause stratégie: {e}", strategy_id, "STRATEGY_PAUSE_FAILED")
    
    async def resume_strategy(self, strategy_id: str) -> None:
        """Reprend une stratégie en pause."""
        try:
            if strategy_id not in self.strategy_instances:
                raise StrategyManagerError(f"Stratégie {strategy_id} non trouvée", 
                                         strategy_id, "STRATEGY_NOT_FOUND")
            
            instance = self.strategy_instances[strategy_id]
            
            if instance.status != StrategyStatus.PAUSED:
                raise StrategyManagerError(f"Stratégie {strategy_id} non en pause", 
                                         strategy_id, "STRATEGY_NOT_PAUSED")
            
            await instance.engine.resume()
            instance.status = StrategyStatus.ACTIVE
            instance.metadata['resumed_at'] = datetime.now().isoformat()
            
            # Remise en queue d'exécution
            await self.execution_queue.put(strategy_id)
            
            self._update_metrics()
            self.logger.info(f"Stratégie {strategy_id} reprise")
            
        except Exception as e:
            self.logger.error(f"Erreur reprise stratégie {strategy_id}: {e}")
            raise StrategyManagerError(f"Erreur reprise stratégie: {e}", strategy_id, "STRATEGY_RESUME_FAILED")
    
    async def remove_strategy(self, strategy_id: str) -> None:
        """Supprime une stratégie."""
        try:
            if strategy_id not in self.strategy_instances:
                raise StrategyManagerError(f"Stratégie {strategy_id} non trouvée", 
                                         strategy_id, "STRATEGY_NOT_FOUND")
            
            # Arrêt de la stratégie si active
            instance = self.strategy_instances[strategy_id]
            if instance.status in [StrategyStatus.ACTIVE, StrategyStatus.PAUSED]:
                await self.stop_strategy(strategy_id)
            
            # Nettoyage des ressources
            await instance.engine.cleanup()
            
            # Suppression de l'instance
            del self.strategy_instances[strategy_id]
            
            self._update_metrics()
            self.logger.info(f"Stratégie {strategy_id} supprimée")
            
        except Exception as e:
            self.logger.error(f"Erreur suppression stratégie {strategy_id}: {e}")
            raise StrategyManagerError(f"Erreur suppression stratégie: {e}", strategy_id, "STRATEGY_REMOVE_FAILED")
    
    async def execute_strategy(self, strategy_id: str) -> List[TradingSignal]:
        """Exécute une stratégie et retourne les signaux générés."""
        try:
            if strategy_id not in self.strategy_instances:
                raise StrategyManagerError(f"Stratégie {strategy_id} non trouvée", 
                                         strategy_id, "STRATEGY_NOT_FOUND")
            
            instance = self.strategy_instances[strategy_id]
            
            if instance.status != StrategyStatus.ACTIVE:
                return []
            
            # Création du contexte d'exécution
            execution_context = await self._create_execution_context(strategy_id)
            
            # Exécution de la stratégie
            start_time = datetime.now()
            result = await instance.engine.execute_strategy(strategy_id, execution_context)
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Extraction des signaux du résultat
            signals = result.signals
            
            # Mise à jour de l'instance
            instance.last_execution = start_time
            instance.execution_count += 1
            instance.active_signals.extend(signals)
            
            # Traitement des signaux
            for signal in signals:
                await self.signal_queue.put(signal)
            
            # Mise à jour des métriques
            self.metrics.total_signals_generated += len(signals)
            self._update_execution_time_metric(execution_time)
            
            self.logger.debug(f"Stratégie {strategy_id} exécutée: {len(signals)} signaux générés")
            return signals
            
        except Exception as e:
            self.logger.error(f"Erreur exécution stratégie {strategy_id}: {e}")
            
            if strategy_id in self.strategy_instances:
                instance = self.strategy_instances[strategy_id]
                instance.error_count += 1
                instance.last_error = str(e)
                
                # Arrêt automatique si trop d'erreurs
                error_rate = instance.error_count / max(instance.execution_count, 1)
                if error_rate > self.execution_config['error_threshold']:
                    self.logger.warning(f"Taux d'erreur élevé pour {strategy_id}, arrêt automatique")
                    await self.stop_strategy(strategy_id)
            
            raise StrategyManagerError(f"Erreur exécution stratégie: {e}", strategy_id, "STRATEGY_EXECUTION_FAILED")
    
    async def get_strategy_info(self, strategy_id: str) -> Dict[str, Any]:
        """Retourne les informations d'une stratégie."""
        if strategy_id not in self.strategy_instances:
            raise StrategyManagerError(f"Stratégie {strategy_id} non trouvée", 
                                     strategy_id, "STRATEGY_NOT_FOUND")
        
        instance = self.strategy_instances[strategy_id]
        return instance.to_dict()
    
    async def list_strategies(self) -> List[Dict[str, Any]]:
        """Liste toutes les stratégies."""
        return [instance.to_dict() for instance in self.strategy_instances.values()]
    
    async def get_active_signals(self, strategy_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retourne les signaux actifs."""
        all_signals = []
        
        for sid, instance in self.strategy_instances.items():
            if strategy_id is None or sid == strategy_id:
                for signal in instance.active_signals:
                    if signal.is_valid():
                        all_signals.append(signal.to_dict())
        
        return all_signals
    
    def get_manager_status(self) -> Dict[str, Any]:
        """Retourne le statut du gestionnaire."""
        return {
            'status': self.status.value,
            'strategies_count': len(self.strategy_instances),
            'active_strategies': len([i for i in self.strategy_instances.values() 
                                    if i.status == StrategyStatus.ACTIVE]),
            'metrics': self.metrics.__dict__,
            'execution_config': self.execution_config,
            'queue_sizes': {
                'execution_queue': self.execution_queue.qsize(),
                'signal_queue': self.signal_queue.qsize()
            }
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Retourne les métriques de performance."""
        return {
            'metrics': self.metrics.__dict__,
            'performance_history': self.performance_history[-100:],  # Dernières 100 entrées
            'strategy_performances': {
                sid: instance.performance.dict() if instance.performance else None
                for sid, instance in self.strategy_instances.items()
            }
        }
    
    # Méthodes privées d'implémentation
    
    async def _initialize_components(self) -> None:
        """Initialise les composants internes."""
        await self.portfolio_allocator.initialize()
        await self.risk_manager.initialize()
        
        if self.market_data_provider:
            await self.market_data_provider.initialize()
        
        if self.portfolio_service:
            await self.portfolio_service.initialize()
    
    async def _load_existing_strategies(self) -> None:
        """Charge les stratégies existantes depuis le répertoire."""
        if not self.strategies_directory.exists():
            return
        
        yaml_files = list(self.strategies_directory.glob("*.yaml")) + \
                    list(self.strategies_directory.glob("*.yml"))
        
        for yaml_file in yaml_files:
            try:
                await self.add_strategy_from_file(str(yaml_file))
            except Exception as e:
                self.logger.warning(f"Impossible de charger {yaml_file}: {e}")
    
    async def _start_background_tasks(self) -> None:
        """Démarre les tâches d'arrière-plan."""
        self._execution_task = asyncio.create_task(self._execution_loop())
        self._signal_processing_task = asyncio.create_task(self._signal_processing_loop())
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
    
    async def _stop_background_tasks(self) -> None:
        """Arrête les tâches d'arrière-plan."""
        tasks = [self._execution_task, self._signal_processing_task, self._monitoring_task]
        
        for task in tasks:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
    
    async def _stop_all_strategies(self) -> None:
        """Arrête toutes les stratégies."""
        for strategy_id in list(self.strategy_instances.keys()):
            try:
                await self.stop_strategy(strategy_id)
            except Exception as e:
                self.logger.error(f"Erreur arrêt stratégie {strategy_id}: {e}")
    
    async def _create_strategy_instance(self, strategy: Strategy) -> str:
        """Crée une instance de stratégie."""
        strategy_id = str(uuid.uuid4())
        
        # Création du moteur de stratégie
        engine = StrategyEngine(
            data_provider=self.market_data_provider
        )
        await engine.initialize()
        await engine.load_strategy(strategy, strategy_id)
        
        # Création de l'instance
        instance = StrategyInstance(
            strategy_id=strategy_id,
            strategy=strategy,
            engine=engine,
            status=StrategyStatus.ACTIVE,
            created_at=datetime.now()
        )
        
        self.strategy_instances[strategy_id] = instance
        self._update_metrics()
        
        return strategy_id
    
    async def _create_execution_context(self, strategy_id: str) -> ExecutionContext:
        """Crée le contexte d'exécution pour une stratégie."""
        portfolio_state = await self._get_portfolio_state()
        market_conditions = await self._get_market_conditions()
        
        return ExecutionContext(
            strategy_id=strategy_id,
            symbol="AAPL",  # Symbole par défaut pour les tests
            timestamp=datetime.now(),
            market_data={"price": 150.0, "volume": 1000000},  # Données de marché fictives
            portfolio_state=portfolio_state,
            execution_mode=ExecutionMode.SIMULATION,
            metadata={"test_mode": True},
            market_conditions=market_conditions,
            execution_config=self.execution_config,
            risk_limits=await self._get_risk_limits(strategy_id)
        )
    
    async def _execution_loop(self) -> None:
        """Boucle d'exécution des stratégies."""
        while self.status == ManagerStatus.ACTIVE:
            try:
                # Traitement par batch
                strategy_ids = []
                for _ in range(self.execution_config['batch_size']):
                    try:
                        strategy_id = await asyncio.wait_for(
                            self.execution_queue.get(), 
                            timeout=1.0
                        )
                        strategy_ids.append(strategy_id)
                    except asyncio.TimeoutError:
                        break
                
                if strategy_ids:
                    # Exécution en parallèle
                    tasks = [self.execute_strategy(sid) for sid in strategy_ids]
                    await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Remise en queue pour la prochaine exécution
                    for strategy_id in strategy_ids:
                        if (strategy_id in self.strategy_instances and 
                            self.strategy_instances[strategy_id].status == StrategyStatus.ACTIVE):
                            await asyncio.sleep(self.execution_interval.total_seconds())
                            await self.execution_queue.put(strategy_id)
                
                await asyncio.sleep(1)  # Pause courte
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Erreur boucle d'exécution: {e}")
                await asyncio.sleep(5)  # Pause en cas d'erreur
    
    async def _signal_processing_loop(self) -> None:
        """Boucle de traitement des signaux."""
        while self.status == ManagerStatus.ACTIVE:
            try:
                signal = await asyncio.wait_for(self.signal_queue.get(), timeout=1.0)
                await self._process_signal(signal)
                
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Erreur traitement signal: {e}")
    
    async def _monitoring_loop(self) -> None:
        """Boucle de surveillance et maintenance."""
        while self.status == ManagerStatus.ACTIVE:
            try:
                # Nettoyage des signaux expirés
                await self._cleanup_expired_signals()
                
                # Mise à jour des performances
                await self._update_performance_metrics()
                
                # Vérification de l'état des stratégies
                await self._check_strategy_health()
                
                # Sauvegarde périodique
                await self._save_manager_state()
                
                await asyncio.sleep(60)  # Surveillance toutes les minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Erreur surveillance: {e}")
                await asyncio.sleep(30)
    
    async def _process_signal(self, signal: TradingSignal) -> None:
        """Traite un signal de trading."""
        try:
            # Allocation de portefeuille si activée
            if self.enable_auto_allocation:
                allocation_result = await self.portfolio_allocator.allocate_signal(
                    signal, self._get_current_portfolio_state()
                )
                
                if not allocation_result.is_approved:
                    self.logger.info(f"Signal {signal.signal_id} rejeté par l'allocateur: {allocation_result.rejection_reason}")
                    return
            
            # Gestion des risques
            risk_assessment = await self.risk_manager.assess_signal_risk(
                signal, self._get_current_portfolio_state()
            )
            
            if not risk_assessment.is_acceptable:
                self.logger.info(f"Signal {signal.signal_id} rejeté par le gestionnaire de risques: {risk_assessment.rejection_reason}")
                return
            
            # Exécution du signal
            if self.execution_service:
                execution_result = await self.execution_service.execute_signal(signal)
                
                if execution_result.success:
                    self.metrics.signals_executed += 1
                    self.logger.info(f"Signal {signal.signal_id} exécuté avec succès")
                else:
                    self.logger.warning(f"Échec exécution signal {signal.signal_id}: {execution_result.error}")
            
        except Exception as e:
            self.logger.error(f"Erreur traitement signal {signal.signal_id}: {e}")
    
    def _get_current_portfolio_state(self) -> Dict[str, Any]:
        """Retourne l'état actuel du portefeuille."""
        # Implémentation simplifiée - à adapter selon le service de portefeuille
        return {
            'total_value': 100000,
            'available_capital': 50000,
            'positions': {},
            'allocations': {}
        }
    
    async def _get_portfolio_state(self) -> Dict[str, Any]:
        """Récupère l'état du portefeuille avec cache."""
        cache_key = 'portfolio_state'
        
        if cache_key in self._portfolio_cache:
            cached_data, timestamp = self._portfolio_cache[cache_key]
            if datetime.now() - timestamp < self._cache_ttl:
                return cached_data
        
        # Récupération depuis le service
        if self.portfolio_service:
            portfolio_state = await self.portfolio_service.get_portfolio_state()
        else:
            portfolio_state = self._get_current_portfolio_state()
        
        # Mise en cache
        self._portfolio_cache[cache_key] = (portfolio_state, datetime.now())
        return portfolio_state
    
    async def _get_market_conditions(self) -> Dict[str, Any]:
        """Récupère les conditions de marché."""
        if self.market_data_provider:
            return await self.market_data_provider.get_market_conditions()
        return {}
    
    async def _get_risk_limits(self, strategy_id: str) -> Dict[str, Any]:
        """Récupère les limites de risque pour une stratégie."""
        if self.risk_service:
            return await self.risk_service.get_strategy_limits(strategy_id)
        return {}
    
    async def _process_active_signals(self, strategy_id: str) -> None:
        """Traite les signaux actifs d'une stratégie arrêtée."""
        instance = self.strategy_instances[strategy_id]
        
        for signal in instance.active_signals[:]:
            if signal.signal_type in [SignalType.STOP_LOSS, SignalType.TAKE_PROFIT]:
                # Traitement immédiat des signaux critiques
                await self._process_signal(signal)
            
            instance.active_signals.remove(signal)
    
    async def _cleanup_expired_signals(self) -> None:
        """Nettoie les signaux expirés."""
        for instance in self.strategy_instances.values():
            instance.active_signals = [s for s in instance.active_signals if s.is_valid()]
    
    async def _update_performance_metrics(self) -> None:
        """Met à jour les métriques de performance."""
        # Calcul des performances par stratégie
        for instance in self.strategy_instances.values():
            if instance.performance:
                # Mise à jour des performances (implémentation simplifiée)
                pass
        
        # Sauvegarde de l'historique
        performance_snapshot = {
            'timestamp': datetime.now().isoformat(),
            'metrics': self.metrics.__dict__.copy()
        }
        
        self.performance_history.append(performance_snapshot)
        
        # Limitation de l'historique
        if len(self.performance_history) > 1000:
            self.performance_history = self.performance_history[-1000:]
    
    async def _check_strategy_health(self) -> None:
        """Vérifie la santé des stratégies."""
        for strategy_id, instance in self.strategy_instances.items():
            try:
                # Vérification du taux d'erreur
                if instance.execution_count > 0:
                    error_rate = instance.error_count / instance.execution_count
                    
                    if error_rate > self.execution_config['error_threshold']:
                        self.logger.warning(f"Taux d'erreur élevé pour {strategy_id}: {error_rate:.2%}")
                        
                        if instance.status == StrategyStatus.ACTIVE:
                            await self.pause_strategy(strategy_id)
                
                # Vérification de l'activité récente
                if instance.status == StrategyStatus.ACTIVE and instance.last_execution:
                    time_since_execution = datetime.now() - instance.last_execution
                    max_idle_time = self.execution_interval * 3
                    
                    if time_since_execution > max_idle_time:
                        self.logger.warning(f"Stratégie {strategy_id} inactive depuis {time_since_execution}")
                        # Remise en queue si nécessaire
                        await self.execution_queue.put(strategy_id)
                
            except Exception as e:
                self.logger.error(f"Erreur vérification santé {strategy_id}: {e}")
    
    async def _save_manager_state(self) -> None:
        """Sauvegarde l'état du gestionnaire."""
        try:
            state = {
                'status': self.status.value,
                'strategies': {
                    sid: instance.to_dict() 
                    for sid, instance in self.strategy_instances.items()
                },
                'metrics': self.metrics.__dict__,
                'timestamp': datetime.now().isoformat()
            }
            
            state_file = self.strategies_directory / 'manager_state.json'
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2, default=str)
                
        except Exception as e:
            self.logger.warning(f"Erreur sauvegarde état: {e}")
    
    def _update_metrics(self) -> None:
        """Met à jour les métriques du gestionnaire."""
        self.metrics.total_strategies = len(self.strategy_instances)
        self.metrics.active_strategies = len([
            i for i in self.strategy_instances.values() 
            if i.status == StrategyStatus.ACTIVE
        ])
        self.metrics.paused_strategies = len([
            i for i in self.strategy_instances.values() 
            if i.status == StrategyStatus.PAUSED
        ])
        self.metrics.error_strategies = len([
            i for i in self.strategy_instances.values() 
            if i.status == StrategyStatus.ERROR
        ])
        self.metrics.last_updated = datetime.now()
    
    def _update_execution_time_metric(self, execution_time_ms: float) -> None:
        """Met à jour la métrique de temps d'exécution."""
        current_avg = self.metrics.average_execution_time_ms
        total_executions = sum(i.execution_count for i in self.strategy_instances.values())
        
        if total_executions > 0:
            self.metrics.average_execution_time_ms = (
                (current_avg * (total_executions - 1) + execution_time_ms) / total_executions
            )
    
    @asynccontextmanager
    async def strategy_context(self, strategy_id: str):
        """Context manager pour les opérations sur une stratégie."""
        if strategy_id not in self.strategy_instances:
            raise StrategyManagerError(f"Stratégie {strategy_id} non trouvée", 
                                     strategy_id, "STRATEGY_NOT_FOUND")
        
        instance = self.strategy_instances[strategy_id]
        
        try:
            yield instance
        except Exception as e:
            instance.error_count += 1
            instance.last_error = str(e)
            self.logger.error(f"Erreur dans contexte stratégie {strategy_id}: {e}")
            raise