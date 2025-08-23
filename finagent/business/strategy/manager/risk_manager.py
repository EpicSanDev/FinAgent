"""
Gestionnaire de risques pour les stratégies de trading.

Ce module évalue et gère les risques associés aux stratégies et signaux
de trading, en appliquant des limites et des contrôles de risque.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from decimal import Decimal
import math
import numpy as np

from ..models.strategy_models import Strategy, RiskLevel
from ..engine.signal_generator import TradingSignal, SignalType

logger = logging.getLogger(__name__)


class RiskLevel(str, Enum):
    """Niveaux de risque."""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"
    CRITICAL = "critical"


class RiskType(str, Enum):
    """Types de risques."""
    MARKET = "market"                    # Risque de marché
    CONCENTRATION = "concentration"      # Risque de concentration
    LIQUIDITY = "liquidity"             # Risque de liquidité
    VOLATILITY = "volatility"           # Risque de volatilité
    CORRELATION = "correlation"         # Risque de corrélation
    DRAWDOWN = "drawdown"               # Risque de drawdown
    LEVERAGE = "leverage"               # Risque de leverage
    OPERATIONAL = "operational"         # Risque opérationnel


@dataclass
class RiskMetric:
    """Métrique de risque."""
    metric_name: str
    current_value: float
    limit_value: float
    risk_level: RiskLevel
    is_breached: bool
    breach_severity: float  # 0-1, 1 étant le plus sévère
    description: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire."""
        return {
            'metric_name': self.metric_name,
            'current_value': self.current_value,
            'limit_value': self.limit_value,
            'risk_level': self.risk_level.value,
            'is_breached': self.is_breached,
            'breach_severity': self.breach_severity,
            'description': self.description
        }


@dataclass
class RiskAssessment:
    """Évaluation complète des risques."""
    assessment_id: str
    timestamp: datetime
    overall_risk_level: RiskLevel
    is_acceptable: bool
    risk_score: float = 0.0             # Score de risque global (0-1)
    risk_metrics: List[RiskMetric] = field(default_factory=list)
    rejection_reason: Optional[str] = None
    recommendations: List[str] = field(default_factory=list)
    confidence_adjustment: float = 1.0  # Facteur d'ajustement de confiance
    risk_budget_usage: float = 0.0      # Usage du budget de risque (0-1)
    expected_risk: float = 0.0          # Risque attendu
    max_loss_estimate: float = 0.0      # Estimation de perte maximale
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire."""
        return {
            'assessment_id': self.assessment_id,
            'timestamp': self.timestamp.isoformat(),
            'overall_risk_level': self.overall_risk_level.value,
            'is_acceptable': self.is_acceptable,
            'risk_metrics': [rm.to_dict() for rm in self.risk_metrics],
            'rejection_reason': self.rejection_reason,
            'recommendations': self.recommendations,
            'confidence_adjustment': self.confidence_adjustment,
            'risk_budget_usage': self.risk_budget_usage,
            'expected_risk': self.expected_risk,
            'max_loss_estimate': self.max_loss_estimate,
            'metadata': self.metadata
        }


@dataclass
class RiskLimit:
    """Limite de risque."""
    limit_type: str
    limit_value: float
    current_value: float = 0.0
    is_percentage: bool = True
    is_hard_limit: bool = True  # True = limite stricte, False = limite souple
    breach_action: str = "reject"  # reject, warn, reduce
    description: Optional[str] = None


@dataclass
class PortfolioRisk:
    """Risque du portefeuille."""
    total_value: float
    var_1d: float           # Value at Risk 1 jour
    var_1w: float           # Value at Risk 1 semaine
    var_1m: float           # Value at Risk 1 mois
    expected_shortfall: float  # Expected Shortfall
    max_drawdown: float     # Drawdown maximum
    volatility: float       # Volatilité du portefeuille
    sharpe_ratio: float     # Ratio de Sharpe
    beta: float             # Beta du marché
    correlation_risk: float # Risque de corrélation
    concentration_risk: float # Risque de concentration
    liquidity_risk: float   # Risque de liquidité


class RiskManagerError(Exception):
    """Exception levée par le gestionnaire de risques."""
    
    def __init__(self, message: str, risk_type: Optional[str] = None, error_code: Optional[str] = None):
        self.message = message
        self.risk_type = risk_type
        self.error_code = error_code
        super().__init__(self._format_message())
    
    def _format_message(self) -> str:
        """Formate le message d'erreur."""
        if self.risk_type and self.error_code:
            return f"[{self.error_code}] Risque {self.risk_type}: {self.message}"
        elif self.risk_type:
            return f"Risque {self.risk_type}: {self.message}"
        elif self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class StrategyRiskManager:
    """
    Gestionnaire de risques pour les stratégies de trading.
    
    Responsabilités:
    - Évaluation des risques des stratégies et signaux
    - Application des limites de risque
    - Calcul des métriques VaR, Expected Shortfall
    - Gestion du budget de risque
    - Surveillance des corrélations et concentrations
    - Recommandations de gestion des risques
    """
    
    def __init__(self,
                 max_portfolio_risk: float = 0.15,      # VaR max 15%
                 max_position_risk: float = 0.05,       # Risque max par position 5%
                 max_strategy_risk: float = 0.10,       # Risque max par stratégie 10%
                 max_correlation: float = 0.70,         # Corrélation max 70%
                 max_concentration: float = 0.20,       # Concentration max 20%
                 confidence_level: float = 0.95,        # Niveau de confiance VaR
                 lookback_days: int = 252):             # Période de calcul 1 an
        """
        Initialise le gestionnaire de risques.
        
        Args:
            max_portfolio_risk: Risque maximum du portefeuille (VaR)
            max_position_risk: Risque maximum par position
            max_strategy_risk: Risque maximum par stratégie
            max_correlation: Corrélation maximum autorisée
            max_concentration: Concentration maximum autorisée
            confidence_level: Niveau de confiance pour VaR
            lookback_days: Période de calcul historique
        """
        self.logger = logging.getLogger(__name__)
        
        # Configuration des limites de risque
        self.max_portfolio_risk = max_portfolio_risk
        self.max_position_risk = max_position_risk
        self.max_strategy_risk = max_strategy_risk
        self.max_correlation = max_correlation
        self.max_concentration = max_concentration
        self.confidence_level = confidence_level
        self.lookback_days = lookback_days
        
        # Limites de risque configurables
        self.risk_limits: Dict[str, RiskLimit] = {}
        self._setup_default_limits()
        
        # Cache des données de risque
        self._volatility_cache: Dict[str, Tuple[float, datetime]] = {}
        self._correlation_cache: Dict[Tuple[str, str], Tuple[float, datetime]] = {}
        self._var_cache: Dict[str, Tuple[float, datetime]] = {}
        
        # Historique des évaluations
        self.risk_assessments: List[RiskAssessment] = []
        
        # Métriques de surveillance
        self.risk_stats = {
            'total_assessments': 0,
            'rejected_signals': 0,
            'rejected_strategies': 0,
            'risk_breaches': {},
            'average_risk_level': 0.0,
            'portfolio_risk_utilization': 0.0
        }
        
        self.logger.info("Gestionnaire de risques initialisé")
    
    async def initialize(self) -> None:
        """Initialise le gestionnaire de risques."""
        self.logger.info("Initialisation du gestionnaire de risques")
        
        # Chargement des données historiques
        await self._load_historical_data()
        
        # Initialisation des modèles de risque
        await self._initialize_risk_models()
        
        self.logger.info("Gestionnaire de risques initialisé")
    
    async def assess_strategy_risk(self, strategy: Strategy, portfolio_state: Dict[str, Any]) -> RiskAssessment:
        """
        Évalue les risques d'une stratégie.
        
        Args:
            strategy: Stratégie à évaluer
            portfolio_state: État actuel du portefeuille
            
        Returns:
            RiskAssessment: Évaluation des risques
        """
        try:
            assessment_id = f"strategy_{strategy.strategy.name}_{datetime.now().isoformat()}"
            
            # Calcul des métriques de risque
            risk_metrics = await self._calculate_strategy_risk_metrics(strategy, portfolio_state)
            
            # Évaluation du niveau de risque global
            overall_risk_level = self._calculate_overall_risk_level(risk_metrics)
            
            # Vérification de l'acceptabilité
            is_acceptable, rejection_reason = self._evaluate_risk_acceptability(risk_metrics)
            
            # Génération des recommandations
            recommendations = self._generate_risk_recommendations(risk_metrics, strategy)
            
            # Calcul des ajustements
            confidence_adjustment = self._calculate_confidence_adjustment(risk_metrics)
            risk_budget_usage = self._calculate_risk_budget_usage(risk_metrics, portfolio_state)
            
            # Création de l'évaluation
            assessment = RiskAssessment(
                assessment_id=assessment_id,
                timestamp=datetime.now(),
                overall_risk_level=overall_risk_level,
                is_acceptable=is_acceptable,
                risk_metrics=risk_metrics,
                rejection_reason=rejection_reason,
                recommendations=recommendations,
                confidence_adjustment=confidence_adjustment,
                risk_budget_usage=risk_budget_usage,
                expected_risk=self._calculate_expected_risk(risk_metrics),
                max_loss_estimate=self._calculate_max_loss_estimate(risk_metrics, portfolio_state),
                metadata={
                    'strategy_name': strategy.strategy.name,
                    'strategy_type': strategy.strategy.type.value,
                    'assessment_type': 'strategy'
                }
            )
            
            # Mise à jour des statistiques
            self._update_risk_stats(assessment)
            
            # Sauvegarde de l'évaluation
            self.risk_assessments.append(assessment)
            self._cleanup_old_assessments()
            
            self.logger.debug(f"Évaluation stratégie {strategy.strategy.name}: {overall_risk_level.value}")
            return assessment
            
        except Exception as e:
            error_msg = f"Erreur évaluation risque stratégie: {e}"
            self.logger.error(error_msg)
            raise RiskManagerError(error_msg, "strategy", "RISK_ASSESSMENT_FAILED")
    
    async def assess_signal_risk(self, signal: TradingSignal, portfolio_state: Dict[str, Any]) -> RiskAssessment:
        """
        Évalue les risques d'un signal de trading.
        
        Args:
            signal: Signal à évaluer
            portfolio_state: État actuel du portefeuille
            
        Returns:
            RiskAssessment: Évaluation des risques
        """
        try:
            assessment_id = f"signal_{signal.signal_id}"
            
            # Calcul des métriques de risque
            risk_metrics = await self._calculate_signal_risk_metrics(signal, portfolio_state)
            
            # Évaluation du niveau de risque global
            overall_risk_level = self._calculate_overall_risk_level(risk_metrics)
            
            # Vérification de l'acceptabilité
            is_acceptable, rejection_reason = self._evaluate_risk_acceptability(risk_metrics)
            
            # Génération des recommandations
            recommendations = self._generate_signal_recommendations(risk_metrics, signal)
            
            # Calcul des ajustements
            confidence_adjustment = self._calculate_confidence_adjustment(risk_metrics)
            risk_budget_usage = self._calculate_risk_budget_usage(risk_metrics, portfolio_state)
            
            # Création de l'évaluation
            assessment = RiskAssessment(
                assessment_id=assessment_id,
                timestamp=datetime.now(),
                overall_risk_level=overall_risk_level,
                is_acceptable=is_acceptable,
                risk_metrics=risk_metrics,
                rejection_reason=rejection_reason,
                recommendations=recommendations,
                confidence_adjustment=confidence_adjustment,
                risk_budget_usage=risk_budget_usage,
                expected_risk=self._calculate_expected_risk(risk_metrics),
                max_loss_estimate=self._calculate_max_loss_estimate(risk_metrics, portfolio_state),
                metadata={
                    'signal_id': signal.signal_id,
                    'signal_type': signal.signal_type.value,
                    'symbol': signal.symbol,
                    'assessment_type': 'signal'
                }
            )
            
            # Mise à jour des statistiques
            self._update_risk_stats(assessment)
            
            self.logger.debug(f"Évaluation signal {signal.signal_id}: {overall_risk_level.value}")
            return assessment
            
        except Exception as e:
            error_msg = f"Erreur évaluation risque signal: {e}"
            self.logger.error(error_msg)
            raise RiskManagerError(error_msg, "signal", "RISK_ASSESSMENT_FAILED")
    
    async def calculate_portfolio_risk(self, portfolio_state: Dict[str, Any]) -> PortfolioRisk:
        """
        Calcule les métriques de risque du portefeuille.
        
        Args:
            portfolio_state: État du portefeuille
            
        Returns:
            PortfolioRisk: Métriques de risque du portefeuille
        """
        try:
            positions = portfolio_state.get('positions', {})
            total_value = portfolio_state.get('total_value', 0.0)
            
            if not positions or total_value <= 0:
                return PortfolioRisk(
                    total_value=total_value,
                    var_1d=0.0, var_1w=0.0, var_1m=0.0,
                    expected_shortfall=0.0, max_drawdown=0.0,
                    volatility=0.0, sharpe_ratio=0.0, beta=0.0,
                    correlation_risk=0.0, concentration_risk=0.0, liquidity_risk=0.0
                )
            
            # Calcul des VaR
            var_1d = await self._calculate_portfolio_var(positions, total_value, 1)
            var_1w = await self._calculate_portfolio_var(positions, total_value, 7)
            var_1m = await self._calculate_portfolio_var(positions, total_value, 30)
            
            # Calcul de l'Expected Shortfall
            expected_shortfall = await self._calculate_expected_shortfall(positions, total_value)
            
            # Calcul des autres métriques
            volatility = await self._calculate_portfolio_volatility(positions, total_value)
            max_drawdown = await self._calculate_max_drawdown(positions)
            sharpe_ratio = await self._calculate_sharpe_ratio(positions, total_value)
            beta = await self._calculate_portfolio_beta(positions, total_value)
            
            # Calcul des risques spécifiques
            correlation_risk = await self._calculate_correlation_risk(positions)
            concentration_risk = self._calculate_concentration_risk(positions, total_value)
            liquidity_risk = await self._calculate_liquidity_risk(positions)
            
            return PortfolioRisk(
                total_value=total_value,
                var_1d=var_1d,
                var_1w=var_1w,
                var_1m=var_1m,
                expected_shortfall=expected_shortfall,
                max_drawdown=max_drawdown,
                volatility=volatility,
                sharpe_ratio=sharpe_ratio,
                beta=beta,
                correlation_risk=correlation_risk,
                concentration_risk=concentration_risk,
                liquidity_risk=liquidity_risk
            )
            
        except Exception as e:
            self.logger.error(f"Erreur calcul risque portefeuille: {e}")
            raise RiskManagerError(f"Erreur calcul risque portefeuille: {e}", "portfolio", "PORTFOLIO_RISK_CALC_FAILED")
    
    def add_risk_limit(self, limit: RiskLimit) -> None:
        """Ajoute une limite de risque."""
        self.risk_limits[limit.limit_type] = limit
        self.logger.info(f"Limite de risque ajoutée: {limit.limit_type}")
    
    def remove_risk_limit(self, limit_type: str) -> None:
        """Supprime une limite de risque."""
        if limit_type in self.risk_limits:
            del self.risk_limits[limit_type]
            self.logger.info(f"Limite de risque supprimée: {limit_type}")
    
    def get_risk_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de risque."""
        return {
            **self.risk_stats,
            'risk_limits': {
                limit_type: {
                    'limit_value': limit.limit_value,
                    'current_value': limit.current_value,
                    'is_percentage': limit.is_percentage,
                    'is_hard_limit': limit.is_hard_limit,
                    'description': limit.description
                }
                for limit_type, limit in self.risk_limits.items()
            },
            'cache_stats': {
                'volatility_cache_size': len(self._volatility_cache),
                'correlation_cache_size': len(self._correlation_cache),
                'var_cache_size': len(self._var_cache)
            }
        }
    
    # Méthodes privées d'implémentation
    
    def _setup_default_limits(self) -> None:
        """Configure les limites de risque par défaut."""
        default_limits = [
            RiskLimit(
                limit_type="max_portfolio_var",
                limit_value=self.max_portfolio_risk,
                is_percentage=True,
                description="VaR maximum du portefeuille"
            ),
            RiskLimit(
                limit_type="max_position_risk",
                limit_value=self.max_position_risk,
                is_percentage=True,
                description="Risque maximum par position"
            ),
            RiskLimit(
                limit_type="max_strategy_risk",
                limit_value=self.max_strategy_risk,
                is_percentage=True,
                description="Risque maximum par stratégie"
            ),
            RiskLimit(
                limit_type="max_correlation",
                limit_value=self.max_correlation,
                is_percentage=False,
                description="Corrélation maximum"
            ),
            RiskLimit(
                limit_type="max_concentration",
                limit_value=self.max_concentration,
                is_percentage=True,
                description="Concentration maximum"
            )
        ]
        
        for limit in default_limits:
            self.risk_limits[limit.limit_type] = limit
    
    async def _load_historical_data(self) -> None:
        """Charge les données historiques nécessaires."""
        # Implémentation du chargement des données historiques
        # À adapter selon le fournisseur de données
        pass
    
    async def _initialize_risk_models(self) -> None:
        """Initialise les modèles de risque."""
        # Initialisation des modèles VaR, corrélations, etc.
        pass
    
    async def _calculate_strategy_risk_metrics(self, strategy: Strategy, portfolio_state: Dict[str, Any]) -> List[RiskMetric]:
        """Calcule les métriques de risque d'une stratégie."""
        metrics = []
        
        # Risque de concentration par stratégie
        strategy_exposure = self._calculate_strategy_exposure(strategy, portfolio_state)
        concentration_metric = RiskMetric(
            metric_name="strategy_concentration",
            current_value=strategy_exposure,
            limit_value=self.max_strategy_risk,
            risk_level=self._get_risk_level_from_usage(strategy_exposure / self.max_strategy_risk),
            is_breached=strategy_exposure > self.max_strategy_risk,
            breach_severity=max(0, (strategy_exposure - self.max_strategy_risk) / self.max_strategy_risk),
            description="Concentration de la stratégie dans le portefeuille"
        )
        metrics.append(concentration_metric)
        
        # Risque de volatilité des instruments de la stratégie
        volatility_risk = await self._calculate_strategy_volatility_risk(strategy, portfolio_state)
        volatility_metric = RiskMetric(
            metric_name="strategy_volatility",
            current_value=volatility_risk,
            limit_value=0.30,  # 30% de volatilité max
            risk_level=self._get_risk_level_from_usage(volatility_risk / 0.30),
            is_breached=volatility_risk > 0.30,
            breach_severity=max(0, (volatility_risk - 0.30) / 0.30),
            description="Volatilité des instruments de la stratégie"
        )
        metrics.append(volatility_metric)
        
        # Risque de drawdown basé sur l'historique de la stratégie
        drawdown_risk = await self._calculate_strategy_drawdown_risk(strategy)
        drawdown_metric = RiskMetric(
            metric_name="strategy_drawdown",
            current_value=drawdown_risk,
            limit_value=0.20,  # 20% de drawdown max
            risk_level=self._get_risk_level_from_usage(drawdown_risk / 0.20),
            is_breached=drawdown_risk > 0.20,
            breach_severity=max(0, (drawdown_risk - 0.20) / 0.20),
            description="Risque de drawdown de la stratégie"
        )
        metrics.append(drawdown_metric)
        
        return metrics
    
    async def _calculate_signal_risk_metrics(self, signal: TradingSignal, portfolio_state: Dict[str, Any]) -> List[RiskMetric]:
        """Calcule les métriques de risque d'un signal."""
        metrics = []
        
        # Risque de position
        position_risk = self._calculate_position_risk(signal, portfolio_state)
        position_metric = RiskMetric(
            metric_name="position_risk",
            current_value=position_risk,
            limit_value=self.max_position_risk,
            risk_level=self._get_risk_level_from_usage(position_risk / self.max_position_risk),
            is_breached=position_risk > self.max_position_risk,
            breach_severity=max(0, (position_risk - self.max_position_risk) / self.max_position_risk),
            description="Risque de la position"
        )
        metrics.append(position_metric)
        
        # Risque de liquidité
        liquidity_risk = await self._calculate_signal_liquidity_risk(signal)
        liquidity_metric = RiskMetric(
            metric_name="liquidity_risk",
            current_value=liquidity_risk,
            limit_value=0.15,  # 15% de risque de liquidité max
            risk_level=self._get_risk_level_from_usage(liquidity_risk / 0.15),
            is_breached=liquidity_risk > 0.15,
            breach_severity=max(0, (liquidity_risk - 0.15) / 0.15),
            description="Risque de liquidité du signal"
        )
        metrics.append(liquidity_metric)
        
        # Risque de corrélation
        correlation_risk = await self._calculate_signal_correlation_risk(signal, portfolio_state)
        correlation_metric = RiskMetric(
            metric_name="correlation_risk",
            current_value=correlation_risk,
            limit_value=self.max_correlation,
            risk_level=self._get_risk_level_from_usage(correlation_risk / self.max_correlation),
            is_breached=correlation_risk > self.max_correlation,
            breach_severity=max(0, (correlation_risk - self.max_correlation) / self.max_correlation),
            description="Risque de corrélation avec le portefeuille"
        )
        metrics.append(correlation_metric)
        
        return metrics
    
    def _calculate_overall_risk_level(self, risk_metrics: List[RiskMetric]) -> RiskLevel:
        """Calcule le niveau de risque global."""
        if not risk_metrics:
            return RiskLevel.LOW
        
        # Recherche du niveau de risque le plus élevé
        max_risk_level = RiskLevel.VERY_LOW
        critical_breaches = 0
        high_breaches = 0
        
        for metric in risk_metrics:
            if metric.is_breached:
                if metric.breach_severity >= 0.5:
                    critical_breaches += 1
                elif metric.breach_severity >= 0.2:
                    high_breaches += 1
            
            # Mise à jour du niveau maximum
            risk_levels_order = [RiskLevel.VERY_LOW, RiskLevel.LOW, RiskLevel.MEDIUM, 
                               RiskLevel.HIGH, RiskLevel.VERY_HIGH, RiskLevel.CRITICAL]
            
            current_index = risk_levels_order.index(max_risk_level)
            metric_index = risk_levels_order.index(metric.risk_level)
            
            if metric_index > current_index:
                max_risk_level = metric.risk_level
        
        # Ajustement basé sur les violations
        if critical_breaches >= 2:
            return RiskLevel.CRITICAL
        elif critical_breaches >= 1 or high_breaches >= 3:
            return RiskLevel.VERY_HIGH
        elif high_breaches >= 2:
            return RiskLevel.HIGH
        
        return max_risk_level
    
    def _evaluate_risk_acceptability(self, risk_metrics: List[RiskMetric]) -> Tuple[bool, Optional[str]]:
        """Évalue si le risque est acceptable."""
        critical_breaches = []
        high_breaches = []
        
        for metric in risk_metrics:
            if metric.is_breached:
                if metric.breach_severity >= 0.5:
                    critical_breaches.append(metric.metric_name)
                elif metric.breach_severity >= 0.2:
                    high_breaches.append(metric.metric_name)
        
        # Rejet si violations critiques
        if critical_breaches:
            reason = f"Violations critiques: {', '.join(critical_breaches)}"
            return False, reason
        
        # Rejet si trop de violations importantes
        if len(high_breaches) >= 3:
            reason = f"Trop de violations importantes: {', '.join(high_breaches)}"
            return False, reason
        
        return True, None
    
    def _generate_risk_recommendations(self, risk_metrics: List[RiskMetric], strategy: Strategy) -> List[str]:
        """Génère des recommandations de gestion des risques."""
        recommendations = []
        
        for metric in risk_metrics:
            if metric.is_breached:
                if metric.metric_name == "strategy_concentration":
                    recommendations.append("Réduire l'exposition à cette stratégie")
                elif metric.metric_name == "strategy_volatility":
                    recommendations.append("Considérer des instruments moins volatils")
                elif metric.metric_name == "strategy_drawdown":
                    recommendations.append("Réviser les paramètres de stop-loss")
                elif metric.metric_name == "position_risk":
                    recommendations.append("Réduire la taille de position")
                elif metric.metric_name == "liquidity_risk":
                    recommendations.append("Éviter les instruments illiquides")
                elif metric.metric_name == "correlation_risk":
                    recommendations.append("Diversifier avec des actifs non corrélés")
        
        # Recommandations générales basées sur le niveau de risque global
        overall_risk = self._calculate_overall_risk_level(risk_metrics)
        
        if overall_risk in [RiskLevel.VERY_HIGH, RiskLevel.CRITICAL]:
            recommendations.append("Suspendre temporairement les nouvelles positions")
            recommendations.append("Réviser la stratégie de gestion des risques")
        elif overall_risk == RiskLevel.HIGH:
            recommendations.append("Surveiller étroitement les positions")
            recommendations.append("Considérer une réduction de l'exposition")
        
        return list(set(recommendations))  # Suppression des doublons
    
    def _generate_signal_recommendations(self, risk_metrics: List[RiskMetric], signal: TradingSignal) -> List[str]:
        """Génère des recommandations spécifiques aux signaux."""
        recommendations = []
        
        for metric in risk_metrics:
            if metric.is_breached:
                if metric.metric_name == "position_risk":
                    recommendations.append(f"Réduire la quantité de {signal.symbol}")
                elif metric.metric_name == "liquidity_risk":
                    recommendations.append(f"Étaler l'exécution de {signal.symbol}")
                elif metric.metric_name == "correlation_risk":
                    recommendations.append(f"Reporter l'exécution si forte corrélation")
        
        return recommendations
    
    def _calculate_confidence_adjustment(self, risk_metrics: List[RiskMetric]) -> float:
        """Calcule l'ajustement de confiance basé sur le risque."""
        if not risk_metrics:
            return 1.0
        
        # Réduction de confiance basée sur les violations
        adjustment = 1.0
        
        for metric in risk_metrics:
            if metric.is_breached:
                # Réduction proportionnelle à la sévérité
                reduction = metric.breach_severity * 0.3  # Maximum 30% de réduction
                adjustment *= (1.0 - reduction)
        
        return max(0.1, adjustment)  # Minimum 10% de confiance conservée
    
    def _calculate_risk_budget_usage(self, risk_metrics: List[RiskMetric], portfolio_state: Dict[str, Any]) -> float:
        """Calcule l'usage du budget de risque."""
        total_usage = 0.0
        count = 0
        
        for metric in risk_metrics:
            if metric.limit_value > 0:
                usage = metric.current_value / metric.limit_value
                total_usage += min(usage, 1.0)  # Plafonné à 100%
                count += 1
        
        return total_usage / count if count > 0 else 0.0
    
    def _calculate_expected_risk(self, risk_metrics: List[RiskMetric]) -> float:
        """Calcule le risque attendu."""
        if not risk_metrics:
            return 0.0
        
        # Moyenne pondérée des risques
        total_risk = sum(metric.current_value for metric in risk_metrics)
        return total_risk / len(risk_metrics)
    
    def _calculate_max_loss_estimate(self, risk_metrics: List[RiskMetric], portfolio_state: Dict[str, Any]) -> float:
        """Estime la perte maximale."""
        portfolio_value = portfolio_state.get('total_value', 0.0)
        
        # Estimation basée sur le VaR et les métriques de risque
        max_risk = max((metric.current_value for metric in risk_metrics), default=0.05)
        
        return portfolio_value * max_risk
    
    def _get_risk_level_from_usage(self, usage_ratio: float) -> RiskLevel:
        """Détermine le niveau de risque basé sur le ratio d'usage."""
        if usage_ratio >= 1.5:
            return RiskLevel.CRITICAL
        elif usage_ratio >= 1.2:
            return RiskLevel.VERY_HIGH
        elif usage_ratio >= 1.0:
            return RiskLevel.HIGH
        elif usage_ratio >= 0.8:
            return RiskLevel.MEDIUM
        elif usage_ratio >= 0.5:
            return RiskLevel.LOW
        else:
            return RiskLevel.VERY_LOW
    
    def _calculate_strategy_exposure(self, strategy: Strategy, portfolio_state: Dict[str, Any]) -> float:
        """Calcule l'exposition d'une stratégie."""
        # Implémentation simplifiée
        strategy_allocations = portfolio_state.get('strategy_allocations', {})
        return strategy_allocations.get(strategy.strategy.name, 0.0)
    
    async def _calculate_strategy_volatility_risk(self, strategy: Strategy, portfolio_state: Dict[str, Any]) -> float:
        """Calcule le risque de volatilité d'une stratégie."""
        # Volatilité moyenne des instruments de la stratégie
        # Implémentation simplifiée
        return 0.20  # 20% de volatilité par défaut
    
    async def _calculate_strategy_drawdown_risk(self, strategy: Strategy) -> float:
        """Calcule le risque de drawdown d'une stratégie."""
        # Basé sur l'historique de performance de la stratégie
        # Implémentation simplifiée
        return 0.15  # 15% de drawdown par défaut
    
    def _calculate_position_risk(self, signal: TradingSignal, portfolio_state: Dict[str, Any]) -> float:
        """Calcule le risque d'une position."""
        if signal.quantity and signal.price_target:
            position_value = abs(signal.quantity * signal.price_target)
            portfolio_value = portfolio_state.get('total_value', 1.0)
            return position_value / portfolio_value
        return 0.0
    
    async def _calculate_signal_liquidity_risk(self, signal: TradingSignal) -> float:
        """Calcule le risque de liquidité d'un signal."""
        # Basé sur le volume, spread, taille de position
        # Implémentation simplifiée
        return 0.05  # 5% de risque de liquidité par défaut
    
    async def _calculate_signal_correlation_risk(self, signal: TradingSignal, portfolio_state: Dict[str, Any]) -> float:
        """Calcule le risque de corrélation d'un signal."""
        # Corrélation avec les positions existantes
        # Implémentation simplifiée
        return 0.60  # 60% de corrélation par défaut
    
    async def _calculate_portfolio_var(self, positions: Dict[str, float], total_value: float, days: int) -> float:
        """Calcule le VaR du portefeuille."""
        # Implémentation simplifiée du calcul VaR
        # En pratique, utiliserait des données historiques ou Monte Carlo
        
        if not positions or total_value <= 0:
            return 0.0
        
        # VaR basé sur la volatilité moyenne et la diversification
        avg_volatility = 0.20  # 20% de volatilité moyenne
        diversification_factor = 0.8  # Réduction due à la diversification
        time_factor = math.sqrt(days / 252)  # Ajustement temporel
        
        var = total_value * avg_volatility * diversification_factor * time_factor * 1.65  # 95% de confiance
        
        return var
    
    async def _calculate_expected_shortfall(self, positions: Dict[str, float], total_value: float) -> float:
        """Calcule l'Expected Shortfall."""
        var_1d = await self._calculate_portfolio_var(positions, total_value, 1)
        # ES typiquement 1.3x le VaR pour une distribution normale
        return var_1d * 1.3
    
    async def _calculate_portfolio_volatility(self, positions: Dict[str, float], total_value: float) -> float:
        """Calcule la volatilité du portefeuille."""
        # Implémentation simplifiée
        if not positions:
            return 0.0
        
        # Volatilité moyenne pondérée
        weighted_volatility = 0.0
        for symbol, value in positions.items():
            weight = value / total_value
            symbol_volatility = await self._get_symbol_volatility(symbol)
            weighted_volatility += weight * symbol_volatility
        
        # Ajustement pour diversification
        return weighted_volatility * 0.8
    
    async def _calculate_max_drawdown(self, positions: Dict[str, float]) -> float:
        """Calcule le drawdown maximum."""
        # Implémentation simplifiée basée sur l'historique
        return 0.18  # 18% par défaut
    
    async def _calculate_sharpe_ratio(self, positions: Dict[str, float], total_value: float) -> float:
        """Calcule le ratio de Sharpe."""
        # Implémentation simplifiée
        return 1.2  # Ratio de Sharpe par défaut
    
    async def _calculate_portfolio_beta(self, positions: Dict[str, float], total_value: float) -> float:
        """Calcule le beta du portefeuille."""
        # Beta par rapport au marché
        return 1.0  # Beta neutre par défaut
    
    async def _calculate_correlation_risk(self, positions: Dict[str, float]) -> float:
        """Calcule le risque de corrélation."""
        # Corrélation moyenne entre les positions
        return 0.65  # 65% de corrélation moyenne par défaut
    
    def _calculate_concentration_risk(self, positions: Dict[str, float], total_value: float) -> float:
        """Calcule le risque de concentration."""
        if not positions or total_value <= 0:
            return 0.0
        
        # Index de Herfindahl-Hirschman
        hhi = sum((value / total_value) ** 2 for value in positions.values())
        
        # Normalisation (1/n pour portefeuille équipondéré)
        n = len(positions)
        min_hhi = 1.0 / n if n > 0 else 1.0
        normalized_hhi = (hhi - min_hhi) / (1.0 - min_hhi) if n > 1 else 0.0
        
        return normalized_hhi
    
    async def _calculate_liquidity_risk(self, positions: Dict[str, float]) -> float:
        """Calcule le risque de liquidité."""
        # Basé sur la liquidité moyenne des positions
        return 0.08  # 8% par défaut
    
    async def _get_symbol_volatility(self, symbol: str) -> float:
        """Récupère la volatilité d'un symbole."""
        # Vérification du cache
        if symbol in self._volatility_cache:
            volatility, timestamp = self._volatility_cache[symbol]
            if datetime.now() - timestamp < timedelta(hours=1):
                return volatility
        
        # Volatilités par défaut
        default_volatilities = {
            'AAPL': 0.25, 'GOOGL': 0.28, 'MSFT': 0.23,
            'AMZN': 0.35, 'TSLA': 0.55, 'JPM': 0.30,
            'BAC': 0.35, 'XOM': 0.40, 'CVX': 0.38,
            'JNJ': 0.18, 'PFE': 0.20
        }
        
        volatility = default_volatilities.get(symbol, 0.25)
        
        # Mise en cache
        self._volatility_cache[symbol] = (volatility, datetime.now())
        
        return volatility
    
    def _update_risk_stats(self, assessment: RiskAssessment) -> None:
        """Met à jour les statistiques de risque."""
        self.risk_stats['total_assessments'] += 1
        
        if not assessment.is_acceptable:
            if assessment.metadata.get('assessment_type') == 'signal':
                self.risk_stats['rejected_signals'] += 1
            elif assessment.metadata.get('assessment_type') == 'strategy':
                self.risk_stats['rejected_strategies'] += 1
        
        # Mise à jour des violations de contraintes
        for metric in assessment.risk_metrics:
            if metric.is_breached:
                metric_name = metric.metric_name
                self.risk_stats['risk_breaches'][metric_name] = (
                    self.risk_stats['risk_breaches'].get(metric_name, 0) + 1
                )
        
        # Mise à jour du niveau de risque moyen
        risk_level_scores = {
            RiskLevel.VERY_LOW: 1, RiskLevel.LOW: 2, RiskLevel.MEDIUM: 3,
            RiskLevel.HIGH: 4, RiskLevel.VERY_HIGH: 5, RiskLevel.CRITICAL: 6
        }
        
        current_score = risk_level_scores.get(assessment.overall_risk_level, 3)
        total_assessments = self.risk_stats['total_assessments']
        current_avg = self.risk_stats['average_risk_level']
        
        new_avg = ((current_avg * (total_assessments - 1)) + current_score) / total_assessments
        self.risk_stats['average_risk_level'] = new_avg
        
        # Mise à jour de l'utilisation du budget de risque
        self.risk_stats['portfolio_risk_utilization'] = assessment.risk_budget_usage
    
    def _cleanup_old_assessments(self) -> None:
        """Nettoie les anciennes évaluations."""
        # Garde seulement les 1000 dernières évaluations
        if len(self.risk_assessments) > 1000:
            self.risk_assessments = self.risk_assessments[-1000:]