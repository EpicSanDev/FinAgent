"""
Allocateur de portefeuille pour les stratégies de trading.

Ce module gère l'allocation du capital entre les différentes stratégies
et positions, en optimisant la diversification et en respectant les
contraintes de risque.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from decimal import Decimal
import math

from ..engine.signal_generator import TradingSignal, SignalType, SignalPriority

logger = logging.getLogger(__name__)


class AllocationMethod(str, Enum):
    """Méthodes d'allocation de portefeuille."""
    EQUAL_WEIGHT = "equal_weight"           # Poids égaux
    RISK_PARITY = "risk_parity"            # Parité de risque
    MARKET_CAP = "market_cap"              # Pondération par capitalisation
    VOLATILITY_TARGET = "volatility_target" # Ciblage de volatilité
    KELLY_CRITERION = "kelly_criterion"     # Critère de Kelly
    CUSTOM = "custom"                       # Allocation personnalisée


class AllocationStatus(str, Enum):
    """Statuts d'allocation."""
    APPROVED = "approved"
    REJECTED = "rejected"
    PENDING = "pending"
    PARTIAL = "partial"


@dataclass
class AllocationConstraint:
    """Contrainte d'allocation."""
    constraint_type: str  # max_position, max_sector, min_cash, etc.
    value: float
    currency: Optional[str] = None
    is_percentage: bool = True
    description: Optional[str] = None


@dataclass
class PositionAllocation:
    """Allocation pour une position spécifique."""
    symbol: str
    target_weight: float
    current_weight: float
    target_value: float
    current_value: float
    adjustment_needed: float
    adjustment_percentage: float
    priority: int = 1  # 1 = haute priorité
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire."""
        return {
            'symbol': self.symbol,
            'target_weight': self.target_weight,
            'current_weight': self.current_weight,
            'target_value': self.target_value,
            'current_value': self.current_value,
            'adjustment_needed': self.adjustment_needed,
            'adjustment_percentage': self.adjustment_percentage,
            'priority': self.priority
        }


@dataclass
class AllocationResult:
    """Résultat d'une allocation."""
    signal_id: str
    strategy_id: str
    status: AllocationStatus
    allocated_amount: float
    allocation_percentage: float
    adjusted_quantity: float = 0.0  # Quantité ajustée selon les contraintes
    position_allocations: List[PositionAllocation] = field(default_factory=list)
    constraints_respected: List[str] = field(default_factory=list)
    constraints_violated: List[str] = field(default_factory=list)
    rejection_reason: Optional[str] = None
    confidence_impact: float = 1.0  # Facteur d'impact sur la confiance
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_approved(self) -> bool:
        """Vérifie si l'allocation est approuvée."""
        return self.status == AllocationStatus.APPROVED
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire."""
        return {
            'signal_id': self.signal_id,
            'strategy_id': self.strategy_id,
            'status': self.status.value,
            'allocated_amount': self.allocated_amount,
            'allocation_percentage': self.allocation_percentage,
            'position_allocations': [pa.to_dict() for pa in self.position_allocations],
            'constraints_respected': self.constraints_respected,
            'constraints_violated': self.constraints_violated,
            'rejection_reason': self.rejection_reason,
            'confidence_impact': self.confidence_impact,
            'is_approved': self.is_approved,
            'metadata': self.metadata
        }


@dataclass
class PortfolioState:
    """État du portefeuille."""
    total_value: float
    available_cash: float
    invested_value: float
    positions: Dict[str, float]  # symbol -> value
    allocations: Dict[str, float]  # symbol -> weight
    sector_exposures: Dict[str, float]  # sector -> weight
    strategy_allocations: Dict[str, float]  # strategy_id -> weight
    last_update: datetime
    
    @property
    def cash_percentage(self) -> float:
        """Pourcentage de cash."""
        return self.available_cash / self.total_value if self.total_value > 0 else 0
    
    @property
    def invested_percentage(self) -> float:
        """Pourcentage investi."""
        return self.invested_value / self.total_value if self.total_value > 0 else 0


class AllocationError(Exception):
    """Exception levée lors d'erreurs d'allocation."""
    
    def __init__(self, message: str, signal_id: Optional[str] = None, error_code: Optional[str] = None):
        self.message = message
        self.signal_id = signal_id
        self.error_code = error_code
        super().__init__(self._format_message())
    
    def _format_message(self) -> str:
        """Formate le message d'erreur."""
        if self.signal_id and self.error_code:
            return f"[{self.error_code}] Signal {self.signal_id}: {self.message}"
        elif self.signal_id:
            return f"Signal {self.signal_id}: {self.message}"
        elif self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class PortfolioAllocator:
    """
    Allocateur de portefeuille pour les stratégies de trading.
    
    Responsabilités:
    - Allocation du capital entre positions
    - Respect des contraintes de risque
    - Optimisation de la diversification
    - Rééquilibrage automatique
    - Gestion des limites par secteur/stratégie
    """
    
    def __init__(self,
                 default_allocation_method: AllocationMethod = AllocationMethod.RISK_PARITY,
                 max_position_weight: float = 0.10,  # 10% max par position
                 max_sector_weight: float = 0.25,    # 25% max par secteur
                 min_cash_percentage: float = 0.05,  # 5% min en cash
                 max_strategy_weight: float = 0.30,  # 30% max par stratégie
                 rebalance_threshold: float = 0.05): # Seuil de rééquilibrage 5%
        """
        Initialise l'allocateur de portefeuille.
        
        Args:
            default_allocation_method: Méthode d'allocation par défaut
            max_position_weight: Poids maximum par position
            max_sector_weight: Poids maximum par secteur
            min_cash_percentage: Pourcentage minimum en cash
            max_strategy_weight: Poids maximum par stratégie
            rebalance_threshold: Seuil de rééquilibrage
        """
        self.logger = logging.getLogger(__name__)
        
        # Configuration d'allocation
        self.default_allocation_method = default_allocation_method
        self.max_position_weight = max_position_weight
        self.max_sector_weight = max_sector_weight
        self.min_cash_percentage = min_cash_percentage
        self.max_strategy_weight = max_strategy_weight
        self.rebalance_threshold = rebalance_threshold
        
        # Contraintes configurables
        self.constraints: List[AllocationConstraint] = []
        self._setup_default_constraints()
        
        # Cache et données
        self._sector_mappings: Dict[str, str] = {}  # symbol -> sector
        self._volatility_cache: Dict[str, Tuple[float, datetime]] = {}
        self._correlation_matrix: Dict[Tuple[str, str], float] = {}
        
        # Métriques d'allocation
        self.allocation_stats = {
            'total_allocations': 0,
            'approved_allocations': 0,
            'rejected_allocations': 0,
            'average_allocation_size': 0.0,
            'constraints_violations': {},
            'allocation_methods_used': {}
        }
        
        self.logger.info("Allocateur de portefeuille initialisé")
    
    async def initialize(self) -> None:
        """Initialise l'allocateur."""
        self.logger.info("Initialisation de l'allocateur de portefeuille")
        
        # Chargement des mappings secteurs
        await self._load_sector_mappings()
        
        # Initialisation des données de marché
        await self._initialize_market_data()
        
        self.logger.info("Allocateur de portefeuille initialisé")
    
    async def allocate_signal(self, signal: TradingSignal, portfolio_state: Dict[str, Any]) -> AllocationResult:
        """
        Alloue un signal de trading dans le portefeuille.
        
        Args:
            signal: Signal de trading à allouer
            portfolio_state: État actuel du portefeuille
            
        Returns:
            AllocationResult: Résultat de l'allocation
        """
        try:
            self.logger.debug(f"Allocation signal {signal.signal_id} pour {signal.symbol}")
            
            # Conversion de l'état du portefeuille
            portfolio = self._convert_portfolio_state(portfolio_state)
            
            # Vérification des contraintes préliminaires
            constraint_check = self._check_preliminary_constraints(signal, portfolio)
            if not constraint_check['passed']:
                return AllocationResult(
                    signal_id=signal.signal_id,
                    strategy_id=signal.strategy_id,
                    status=AllocationStatus.REJECTED,
                    allocated_amount=0.0,
                    allocation_percentage=0.0,
                    rejection_reason=constraint_check['reason']
                )
            
            # Calcul de l'allocation selon la méthode configurée
            allocation_amount = await self._calculate_allocation_amount(signal, portfolio)
            
            # Vérification des contraintes détaillées
            constraint_result = await self._check_detailed_constraints(
                signal, portfolio, allocation_amount
            )
            
            if not constraint_result['passed']:
                # Tentative d'ajustement de l'allocation
                adjusted_amount = await self._adjust_allocation_for_constraints(
                    signal, portfolio, allocation_amount, constraint_result['violations']
                )
                
                if adjusted_amount <= 0:
                    return AllocationResult(
                        signal_id=signal.signal_id,
                        strategy_id=signal.strategy_id,
                        status=AllocationStatus.REJECTED,
                        allocated_amount=0.0,
                        allocation_percentage=0.0,
                        rejection_reason=constraint_result['reason'],
                        constraints_violated=constraint_result['violations']
                    )
                
                allocation_amount = adjusted_amount
            
            # Calcul des ajustements de portefeuille nécessaires
            position_allocations = await self._calculate_position_adjustments(
                signal, portfolio, allocation_amount
            )
            
            # Calcul de l'impact sur la confiance
            confidence_impact = self._calculate_confidence_impact(
                signal, portfolio, allocation_amount
            )
            
            # Création du résultat
            result = AllocationResult(
                signal_id=signal.signal_id,
                strategy_id=signal.strategy_id,
                status=AllocationStatus.APPROVED,
                allocated_amount=allocation_amount,
                allocation_percentage=allocation_amount / portfolio.total_value,
                position_allocations=position_allocations,
                constraints_respected=constraint_result.get('respected', []),
                constraints_violated=constraint_result.get('violations', []),
                confidence_impact=confidence_impact,
                metadata={
                    'allocation_method': self.default_allocation_method.value,
                    'portfolio_value': portfolio.total_value,
                    'cash_percentage': portfolio.cash_percentage,
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            # Mise à jour des statistiques
            self._update_allocation_stats(result)
            
            self.logger.debug(f"Allocation approuvée: {allocation_amount:.2f} ({result.allocation_percentage:.2%})")
            return result
            
        except Exception as e:
            error_msg = f"Erreur allocation signal: {e}"
            self.logger.error(error_msg)
            
            return AllocationResult(
                signal_id=signal.signal_id,
                strategy_id=signal.strategy_id,
                status=AllocationStatus.REJECTED,
                allocated_amount=0.0,
                allocation_percentage=0.0,
                rejection_reason=error_msg
            )
    
    async def calculate_portfolio_rebalancing(self, portfolio_state: Dict[str, Any]) -> List[PositionAllocation]:
        """
        Calcule les ajustements nécessaires pour rééquilibrer le portefeuille.
        
        Args:
            portfolio_state: État actuel du portefeuille
            
        Returns:
            List[PositionAllocation]: Liste des ajustements nécessaires
        """
        try:
            portfolio = self._convert_portfolio_state(portfolio_state)
            rebalancing_needed = []
            
            # Calcul des poids cibles selon la méthode d'allocation
            target_weights = await self._calculate_target_weights(portfolio)
            
            for symbol, target_weight in target_weights.items():
                current_weight = portfolio.allocations.get(symbol, 0.0)
                current_value = portfolio.positions.get(symbol, 0.0)
                target_value = target_weight * portfolio.total_value
                
                # Vérification si un rééquilibrage est nécessaire
                weight_diff = abs(target_weight - current_weight)
                if weight_diff > self.rebalance_threshold:
                    adjustment_needed = target_value - current_value
                    
                    allocation = PositionAllocation(
                        symbol=symbol,
                        target_weight=target_weight,
                        current_weight=current_weight,
                        target_value=target_value,
                        current_value=current_value,
                        adjustment_needed=adjustment_needed,
                        adjustment_percentage=adjustment_needed / current_value if current_value > 0 else 0,
                        priority=self._calculate_rebalancing_priority(weight_diff)
                    )
                    
                    rebalancing_needed.append(allocation)
            
            # Tri par priorité
            rebalancing_needed.sort(key=lambda x: x.priority, reverse=True)
            
            self.logger.info(f"Rééquilibrage nécessaire pour {len(rebalancing_needed)} positions")
            return rebalancing_needed
            
        except Exception as e:
            self.logger.error(f"Erreur calcul rééquilibrage: {e}")
            return []
    
    async def get_allocation_limits(self, symbol: str, strategy_id: str, portfolio_state: Dict[str, Any]) -> Dict[str, float]:
        """
        Retourne les limites d'allocation pour un symbole et une stratégie.
        
        Args:
            symbol: Symbole financier
            strategy_id: ID de la stratégie
            portfolio_state: État du portefeuille
            
        Returns:
            Dict[str, float]: Limites d'allocation
        """
        try:
            portfolio = self._convert_portfolio_state(portfolio_state)
            
            # Limite par position
            current_position_weight = portfolio.allocations.get(symbol, 0.0)
            max_additional_position = max(0, self.max_position_weight - current_position_weight)
            
            # Limite par secteur
            sector = self._get_symbol_sector(symbol)
            current_sector_weight = portfolio.sector_exposures.get(sector, 0.0)
            max_additional_sector = max(0, self.max_sector_weight - current_sector_weight)
            
            # Limite par stratégie
            current_strategy_weight = portfolio.strategy_allocations.get(strategy_id, 0.0)
            max_additional_strategy = max(0, self.max_strategy_weight - current_strategy_weight)
            
            # Limite de cash disponible
            max_cash_allocation = portfolio.available_cash / portfolio.total_value
            
            # Limite effective (minimum des contraintes)
            effective_limit = min(
                max_additional_position,
                max_additional_sector,
                max_additional_strategy,
                max_cash_allocation
            )
            
            return {
                'max_position_weight': self.max_position_weight,
                'current_position_weight': current_position_weight,
                'max_additional_position': max_additional_position,
                'max_sector_weight': self.max_sector_weight,
                'current_sector_weight': current_sector_weight,
                'max_additional_sector': max_additional_sector,
                'max_strategy_weight': self.max_strategy_weight,
                'current_strategy_weight': current_strategy_weight,
                'max_additional_strategy': max_additional_strategy,
                'max_cash_allocation': max_cash_allocation,
                'effective_limit': effective_limit,
                'sector': sector
            }
            
        except Exception as e:
            self.logger.error(f"Erreur calcul limites allocation: {e}")
            return {'effective_limit': 0.0}
    
    def add_constraint(self, constraint: AllocationConstraint) -> None:
        """Ajoute une contrainte d'allocation."""
        self.constraints.append(constraint)
        self.logger.info(f"Contrainte ajoutée: {constraint.constraint_type}")
    
    def remove_constraint(self, constraint_type: str) -> None:
        """Supprime une contrainte d'allocation."""
        self.constraints = [c for c in self.constraints if c.constraint_type != constraint_type]
        self.logger.info(f"Contrainte supprimée: {constraint_type}")
    
    def get_allocation_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques d'allocation."""
        return {
            **self.allocation_stats,
            'success_rate': (
                self.allocation_stats['approved_allocations'] / 
                max(self.allocation_stats['total_allocations'], 1)
            ),
            'constraints': [
                {
                    'type': c.constraint_type,
                    'value': c.value,
                    'is_percentage': c.is_percentage,
                    'description': c.description
                }
                for c in self.constraints
            ]
        }
    
    # Méthodes privées d'implémentation
    
    def _setup_default_constraints(self) -> None:
        """Configure les contraintes par défaut."""
        default_constraints = [
            AllocationConstraint(
                constraint_type="max_position_weight",
                value=self.max_position_weight,
                is_percentage=True,
                description="Poids maximum par position"
            ),
            AllocationConstraint(
                constraint_type="max_sector_weight",
                value=self.max_sector_weight,
                is_percentage=True,
                description="Poids maximum par secteur"
            ),
            AllocationConstraint(
                constraint_type="min_cash_percentage",
                value=self.min_cash_percentage,
                is_percentage=True,
                description="Pourcentage minimum en cash"
            ),
            AllocationConstraint(
                constraint_type="max_strategy_weight",
                value=self.max_strategy_weight,
                is_percentage=True,
                description="Poids maximum par stratégie"
            )
        ]
        
        self.constraints.extend(default_constraints)
    
    async def _load_sector_mappings(self) -> None:
        """Charge les mappings symbole -> secteur."""
        # Implémentation simplifiée - à adapter selon la source de données
        self._sector_mappings = {
            'AAPL': 'Technology',
            'GOOGL': 'Technology',
            'MSFT': 'Technology',
            'AMZN': 'Consumer Discretionary',
            'TSLA': 'Consumer Discretionary',
            'JPM': 'Financials',
            'BAC': 'Financials',
            'XOM': 'Energy',
            'CVX': 'Energy',
            'JNJ': 'Healthcare',
            'PFE': 'Healthcare'
        }
    
    async def _initialize_market_data(self) -> None:
        """Initialise les données de marché nécessaires."""
        # Initialisation des données de volatilité, corrélations, etc.
        # Implémentation à adapter selon le fournisseur de données
        pass
    
    def _convert_portfolio_state(self, portfolio_state: Dict[str, Any]) -> PortfolioState:
        """Convertit l'état du portefeuille en objet PortfolioState."""
        return PortfolioState(
            total_value=portfolio_state.get('total_value', 0.0),
            available_cash=portfolio_state.get('available_cash', 0.0),
            invested_value=portfolio_state.get('invested_value', 0.0),
            positions=portfolio_state.get('positions', {}),
            allocations=portfolio_state.get('allocations', {}),
            sector_exposures=portfolio_state.get('sector_exposures', {}),
            strategy_allocations=portfolio_state.get('strategy_allocations', {}),
            last_update=datetime.now()
        )
    
    def _check_preliminary_constraints(self, signal: TradingSignal, portfolio: PortfolioState) -> Dict[str, Any]:
        """Vérifie les contraintes préliminaires."""
        # Vérification du cash minimum
        if portfolio.cash_percentage < self.min_cash_percentage:
            return {
                'passed': False,
                'reason': f"Cash insuffisant: {portfolio.cash_percentage:.2%} < {self.min_cash_percentage:.2%}"
            }
        
        # Vérification de la validité du signal
        if not signal.is_valid():
            return {
                'passed': False,
                'reason': "Signal expiré ou invalide"
            }
        
        # Vérification de la confiance minimum
        if signal.confidence < 0.3:  # Seuil configurable
            return {
                'passed': False,
                'reason': f"Confiance trop faible: {signal.confidence:.2%}"
            }
        
        return {'passed': True}
    
    async def _calculate_allocation_amount(self, signal: TradingSignal, portfolio: PortfolioState) -> float:
        """Calcule le montant à allouer selon la méthode configurée."""
        if self.default_allocation_method == AllocationMethod.EQUAL_WEIGHT:
            return await self._calculate_equal_weight_allocation(signal, portfolio)
        
        elif self.default_allocation_method == AllocationMethod.RISK_PARITY:
            return await self._calculate_risk_parity_allocation(signal, portfolio)
        
        elif self.default_allocation_method == AllocationMethod.VOLATILITY_TARGET:
            return await self._calculate_volatility_target_allocation(signal, portfolio)
        
        elif self.default_allocation_method == AllocationMethod.KELLY_CRITERION:
            return await self._calculate_kelly_allocation(signal, portfolio)
        
        else:
            # Méthode par défaut basée sur la confiance
            base_allocation = portfolio.total_value * 0.05  # 5% par défaut
            confidence_multiplier = signal.confidence
            return base_allocation * confidence_multiplier
    
    async def _calculate_equal_weight_allocation(self, signal: TradingSignal, portfolio: PortfolioState) -> float:
        """Calcule l'allocation à poids égaux."""
        # Allocation basée sur un nombre cible de positions
        target_positions = 20  # Configurable
        target_weight = 1.0 / target_positions
        return portfolio.total_value * target_weight
    
    async def _calculate_risk_parity_allocation(self, signal: TradingSignal, portfolio: PortfolioState) -> float:
        """Calcule l'allocation basée sur la parité de risque."""
        # Récupération de la volatilité du symbole
        volatility = await self._get_symbol_volatility(signal.symbol)
        
        if volatility <= 0:
            return portfolio.total_value * 0.02  # Allocation minimale
        
        # Allocation inversement proportionnelle à la volatilité
        target_volatility = 0.15  # 15% de volatilité cible
        risk_budget = target_volatility / volatility
        
        # Limitation à des valeurs raisonnables
        risk_budget = min(risk_budget, 0.10)  # Maximum 10%
        risk_budget = max(risk_budget, 0.01)  # Minimum 1%
        
        return portfolio.total_value * risk_budget
    
    async def _calculate_volatility_target_allocation(self, signal: TradingSignal, portfolio: PortfolioState) -> float:
        """Calcule l'allocation pour cibler une volatilité spécifique."""
        target_volatility = 0.12  # 12% de volatilité cible
        symbol_volatility = await self._get_symbol_volatility(signal.symbol)
        
        if symbol_volatility <= 0:
            return portfolio.total_value * 0.02
        
        # Calcul de l'allocation pour atteindre la volatilité cible
        allocation_ratio = target_volatility / symbol_volatility
        allocation_ratio = min(allocation_ratio, 0.15)  # Maximum 15%
        
        return portfolio.total_value * allocation_ratio
    
    async def _calculate_kelly_allocation(self, signal: TradingSignal, portfolio: PortfolioState) -> float:
        """Calcule l'allocation selon le critère de Kelly."""
        # Paramètres simplifiés pour le critère de Kelly
        win_probability = signal.confidence
        average_win = 0.08  # 8% de gain moyen
        average_loss = 0.04  # 4% de perte moyenne
        
        if win_probability <= 0.5:
            return portfolio.total_value * 0.01  # Allocation minimale
        
        # Formule de Kelly: f = (bp - q) / b
        # où b = ratio gain/perte, p = probabilité de gain, q = probabilité de perte
        b = average_win / average_loss
        p = win_probability
        q = 1 - win_probability
        
        kelly_fraction = (b * p - q) / b
        
        # Limitation pour éviter un surlevier
        kelly_fraction = min(kelly_fraction, 0.10)  # Maximum 10%
        kelly_fraction = max(kelly_fraction, 0.01)  # Minimum 1%
        
        return portfolio.total_value * kelly_fraction
    
    async def _check_detailed_constraints(self, signal: TradingSignal, portfolio: PortfolioState, allocation_amount: float) -> Dict[str, Any]:
        """Vérifie les contraintes détaillées."""
        violations = []
        respected = []
        
        allocation_percentage = allocation_amount / portfolio.total_value
        
        # Vérification des contraintes personnalisées
        for constraint in self.constraints:
            constraint_check = self._check_single_constraint(
                constraint, signal, portfolio, allocation_amount, allocation_percentage
            )
            
            if constraint_check['violated']:
                violations.append(constraint.constraint_type)
            else:
                respected.append(constraint.constraint_type)
        
        return {
            'passed': len(violations) == 0,
            'violations': violations,
            'respected': respected,
            'reason': f"Contraintes violées: {', '.join(violations)}" if violations else None
        }
    
    def _check_single_constraint(self, constraint: AllocationConstraint, signal: TradingSignal, 
                                portfolio: PortfolioState, allocation_amount: float, 
                                allocation_percentage: float) -> Dict[str, Any]:
        """Vérifie une contrainte spécifique."""
        if constraint.constraint_type == "max_position_weight":
            current_weight = portfolio.allocations.get(signal.symbol, 0.0)
            new_weight = current_weight + allocation_percentage
            return {'violated': new_weight > constraint.value}
        
        elif constraint.constraint_type == "max_sector_weight":
            sector = self._get_symbol_sector(signal.symbol)
            current_sector_weight = portfolio.sector_exposures.get(sector, 0.0)
            new_sector_weight = current_sector_weight + allocation_percentage
            return {'violated': new_sector_weight > constraint.value}
        
        elif constraint.constraint_type == "min_cash_percentage":
            new_cash = portfolio.available_cash - allocation_amount
            new_cash_percentage = new_cash / portfolio.total_value
            return {'violated': new_cash_percentage < constraint.value}
        
        elif constraint.constraint_type == "max_strategy_weight":
            current_strategy_weight = portfolio.strategy_allocations.get(signal.strategy_id, 0.0)
            new_strategy_weight = current_strategy_weight + allocation_percentage
            return {'violated': new_strategy_weight > constraint.value}
        
        return {'violated': False}
    
    async def _adjust_allocation_for_constraints(self, signal: TradingSignal, portfolio: PortfolioState, 
                                               allocation_amount: float, violations: List[str]) -> float:
        """Ajuste l'allocation pour respecter les contraintes."""
        adjusted_amount = allocation_amount
        
        for violation in violations:
            if violation == "max_position_weight":
                current_weight = portfolio.allocations.get(signal.symbol, 0.0)
                max_additional = max(0, self.max_position_weight - current_weight)
                max_amount = max_additional * portfolio.total_value
                adjusted_amount = min(adjusted_amount, max_amount)
            
            elif violation == "max_sector_weight":
                sector = self._get_symbol_sector(signal.symbol)
                current_sector_weight = portfolio.sector_exposures.get(sector, 0.0)
                max_additional = max(0, self.max_sector_weight - current_sector_weight)
                max_amount = max_additional * portfolio.total_value
                adjusted_amount = min(adjusted_amount, max_amount)
            
            elif violation == "min_cash_percentage":
                min_cash_required = self.min_cash_percentage * portfolio.total_value
                max_amount = portfolio.available_cash - min_cash_required
                adjusted_amount = min(adjusted_amount, max(0, max_amount))
            
            elif violation == "max_strategy_weight":
                current_strategy_weight = portfolio.strategy_allocations.get(signal.strategy_id, 0.0)
                max_additional = max(0, self.max_strategy_weight - current_strategy_weight)
                max_amount = max_additional * portfolio.total_value
                adjusted_amount = min(adjusted_amount, max_amount)
        
        return max(0, adjusted_amount)
    
    async def _calculate_position_adjustments(self, signal: TradingSignal, portfolio: PortfolioState, 
                                            allocation_amount: float) -> List[PositionAllocation]:
        """Calcule les ajustements de position nécessaires."""
        adjustments = []
        
        # Ajustement pour la nouvelle position
        current_value = portfolio.positions.get(signal.symbol, 0.0)
        current_weight = portfolio.allocations.get(signal.symbol, 0.0)
        
        if signal.signal_type == SignalType.BUY:
            new_value = current_value + allocation_amount
        elif signal.signal_type == SignalType.SELL:
            new_value = max(0, current_value - allocation_amount)
        else:
            new_value = current_value
        
        new_weight = new_value / portfolio.total_value
        
        adjustment = PositionAllocation(
            symbol=signal.symbol,
            target_weight=new_weight,
            current_weight=current_weight,
            target_value=new_value,
            current_value=current_value,
            adjustment_needed=new_value - current_value,
            adjustment_percentage=(new_value - current_value) / current_value if current_value > 0 else 0,
            priority=self._get_signal_priority_score(signal)
        )
        
        adjustments.append(adjustment)
        
        return adjustments
    
    def _calculate_confidence_impact(self, signal: TradingSignal, portfolio: PortfolioState, 
                                   allocation_amount: float) -> float:
        """Calcule l'impact sur la confiance basé sur l'allocation."""
        # Facteur basé sur la taille de l'allocation relative
        allocation_percentage = allocation_amount / portfolio.total_value
        
        if allocation_percentage < 0.01:  # Moins de 1%
            return 0.8  # Réduction de confiance pour allocation trop petite
        elif allocation_percentage > 0.10:  # Plus de 10%
            return 0.9  # Légère réduction pour allocation importante
        else:
            return 1.0  # Pas d'impact
    
    async def _calculate_target_weights(self, portfolio: PortfolioState) -> Dict[str, float]:
        """Calcule les poids cibles pour le rééquilibrage."""
        # Implémentation simplifiée basée sur la méthode d'allocation par défaut
        symbols = list(portfolio.positions.keys())
        
        if self.default_allocation_method == AllocationMethod.EQUAL_WEIGHT:
            target_weight = 1.0 / len(symbols) if symbols else 0.0
            return {symbol: target_weight for symbol in symbols}
        
        elif self.default_allocation_method == AllocationMethod.RISK_PARITY:
            # Calcul basé sur la volatilité inverse
            volatilities = {}
            for symbol in symbols:
                volatilities[symbol] = await self._get_symbol_volatility(symbol)
            
            # Calcul des poids inversement proportionnels à la volatilité
            total_inv_vol = sum(1.0 / max(vol, 0.01) for vol in volatilities.values())
            
            return {
                symbol: (1.0 / max(volatilities[symbol], 0.01)) / total_inv_vol
                for symbol in symbols
            }
        
        else:
            # Maintien des poids actuels par défaut
            return portfolio.allocations.copy()
    
    def _calculate_rebalancing_priority(self, weight_diff: float) -> int:
        """Calcule la priorité de rééquilibrage."""
        if weight_diff > 0.10:  # Plus de 10% d'écart
            return 5  # Priorité maximale
        elif weight_diff > 0.07:
            return 4
        elif weight_diff > 0.05:
            return 3
        elif weight_diff > 0.03:
            return 2
        else:
            return 1
    
    def _get_symbol_sector(self, symbol: str) -> str:
        """Retourne le secteur d'un symbole."""
        return self._sector_mappings.get(symbol, 'Unknown')
    
    async def _get_symbol_volatility(self, symbol: str) -> float:
        """Récupère la volatilité d'un symbole."""
        # Vérification du cache
        if symbol in self._volatility_cache:
            volatility, timestamp = self._volatility_cache[symbol]
            if datetime.now() - timestamp < timedelta(hours=1):
                return volatility
        
        # Calcul ou récupération de la volatilité
        # Implémentation simplifiée - à adapter selon le fournisseur de données
        default_volatilities = {
            'AAPL': 0.25, 'GOOGL': 0.28, 'MSFT': 0.23,
            'AMZN': 0.35, 'TSLA': 0.55, 'JPM': 0.30,
            'BAC': 0.35, 'XOM': 0.40, 'CVX': 0.38,
            'JNJ': 0.18, 'PFE': 0.20
        }
        
        volatility = default_volatilities.get(symbol, 0.25)  # 25% par défaut
        
        # Mise en cache
        self._volatility_cache[symbol] = (volatility, datetime.now())
        
        return volatility
    
    def _get_signal_priority_score(self, signal: TradingSignal) -> int:
        """Calcule le score de priorité d'un signal."""
        base_score = 1
        
        # Ajustement basé sur le type de signal
        if signal.signal_type == SignalType.STOP_LOSS:
            base_score += 4  # Haute priorité pour stop-loss
        elif signal.signal_type == SignalType.TAKE_PROFIT:
            base_score += 3
        elif signal.priority == SignalPriority.CRITICAL:
            base_score += 4
        elif signal.priority == SignalPriority.HIGH:
            base_score += 2
        
        # Ajustement basé sur la confiance
        if signal.confidence >= 0.8:
            base_score += 2
        elif signal.confidence >= 0.6:
            base_score += 1
        
        return min(base_score, 5)  # Score maximum de 5
    
    def _update_allocation_stats(self, result: AllocationResult) -> None:
        """Met à jour les statistiques d'allocation."""
        self.allocation_stats['total_allocations'] += 1
        
        if result.is_approved:
            self.allocation_stats['approved_allocations'] += 1
            
            # Mise à jour de la taille moyenne d'allocation
            current_avg = self.allocation_stats['average_allocation_size']
            total_approved = self.allocation_stats['approved_allocations']
            
            new_avg = ((current_avg * (total_approved - 1)) + result.allocated_amount) / total_approved
            self.allocation_stats['average_allocation_size'] = new_avg
        else:
            self.allocation_stats['rejected_allocations'] += 1
        
        # Statistiques des violations de contraintes
        for violation in result.constraints_violated:
            self.allocation_stats['constraints_violations'][violation] = (
                self.allocation_stats['constraints_violations'].get(violation, 0) + 1
            )
        
        # Statistiques des méthodes d'allocation
        method = result.metadata.get('allocation_method', 'unknown')
        self.allocation_stats['allocation_methods_used'][method] = (
            self.allocation_stats['allocation_methods_used'].get(method, 0) + 1
        )