"""
Gestionnaire de portefeuille principal - Orchestration de la gestion de portefeuille.
"""

import asyncio
import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

from finagent.business.models.portfolio_models import (
    Portfolio,
    Position,
    Transaction,
    TransactionType,
    TransactionStatus,
    PositionStatus,
    PortfolioMetrics,
    PerformanceMetrics,
    RebalanceRecommendation
)
from finagent.business.models.decision_models import DecisionResult, DecisionAction
from finagent.data.providers.openbb_provider import OpenBBProvider
from finagent.infrastructure.config import settings

logger = logging.getLogger(__name__)


class PortfolioManager:
    """
    Gestionnaire principal de portefeuille.
    
    Responsabilités :
    - Gestion du cycle de vie du portefeuille
    - Exécution des transactions
    - Mise à jour des positions
    - Calcul des métriques de performance
    - Coordination avec les autres composants
    """
    
    def __init__(
        self,
        openbb_provider: OpenBBProvider,
        position_manager: Optional['PositionManager'] = None,
        performance_tracker: Optional['PerformanceTracker'] = None,
        rebalancer: Optional['Rebalancer'] = None
    ):
        """
        Initialise le gestionnaire de portefeuille.
        
        Args:
            openbb_provider: Provider de données financières
            position_manager: Gestionnaire de positions (optionnel)
            performance_tracker: Suivi de performance (optionnel)
            rebalancer: Gestionnaire de rééquilibrage (optionnel)
        """
        self.openbb_provider = openbb_provider
        self.position_manager = position_manager
        self.performance_tracker = performance_tracker
        self.rebalancer = rebalancer
        
        # Configuration
        self.min_trade_amount = Decimal(str(settings.trading.min_trade_amount or "100"))
        self.max_position_size = settings.trading.max_position_size or 0.2
        self.transaction_fee = Decimal("0.001")  # 0.1% par défaut
        
        # Stockage des portefeuilles (en production: base de données)
        self._portfolios: Dict[UUID, Portfolio] = {}
        self._transactions: Dict[UUID, List[Transaction]] = {}
        
        logger.info("Gestionnaire de portefeuille initialisé")
    
    async def create_portfolio(
        self,
        name: str,
        initial_cash: Decimal,
        description: Optional[str] = None,
        risk_tolerance: float = 0.5,
        target_allocation: Optional[Dict[str, float]] = None
    ) -> Portfolio:
        """
        Crée un nouveau portefeuille.
        
        Args:
            name: Nom du portefeuille
            initial_cash: Trésorerie initiale
            description: Description optionnelle
            risk_tolerance: Tolérance au risque [0-1]
            target_allocation: Allocation cible par secteur/stratégie
            
        Returns:
            Portfolio: Nouveau portefeuille créé
        """
        logger.info(f"Création du portefeuille '{name}' avec {initial_cash} de cash initial")
        
        portfolio = Portfolio(
            name=name,
            description=description,
            total_value=initial_cash,
            cash_balance=initial_cash,
            invested_amount=Decimal("0"),
            available_cash=initial_cash,
            risk_tolerance=risk_tolerance,
            target_allocation=target_allocation or {}
        )
        
        # Stocker le portefeuille
        self._portfolios[portfolio.id] = portfolio
        self._transactions[portfolio.id] = []
        
        logger.info(f"Portefeuille {portfolio.id} créé avec succès")
        return portfolio
    
    async def get_portfolio(self, portfolio_id: UUID) -> Optional[Portfolio]:
        """Récupère un portefeuille par son ID."""
        return self._portfolios.get(portfolio_id)
    
    async def update_portfolio_prices(self, portfolio_id: UUID) -> Portfolio:
        """
        Met à jour les prix du marché pour toutes les positions du portefeuille.
        
        Args:
            portfolio_id: ID du portefeuille
            
        Returns:
            Portfolio: Portefeuille mis à jour
        """
        logger.info(f"Mise à jour des prix pour le portefeuille {portfolio_id}")
        
        portfolio = self._portfolios.get(portfolio_id)
        if not portfolio:
            raise ValueError(f"Portefeuille {portfolio_id} non trouvé")
        
        try:
            # Récupérer les prix pour toutes les positions
            symbols = list(portfolio.active_positions.keys())
            if not symbols:
                return portfolio
            
            # Obtenir les prix en parallèle
            price_tasks = [
                self.openbb_provider.get_quote(symbol) for symbol in symbols
            ]
            price_results = await asyncio.gather(*price_tasks, return_exceptions=True)
            
            # Mettre à jour chaque position
            total_market_value = Decimal("0")
            total_pnl = Decimal("0")
            
            for i, symbol in enumerate(symbols):
                price_result = price_results[i]
                
                if isinstance(price_result, Exception):
                    logger.warning(f"Erreur prix pour {symbol}: {price_result}")
                    continue
                
                current_price = Decimal(str(price_result.get('price', 0)))
                position = portfolio.positions[symbol]
                
                # Mettre à jour la position
                if self.position_manager:
                    updated_position = await self.position_manager.update_position_price(
                        position, current_price
                    )
                    portfolio.positions[symbol] = updated_position
                else:
                    # Mise à jour simple
                    position.current_price = current_price
                    position.market_value = position.quantity * current_price
                    position.unrealized_pnl = position.market_value - position.total_cost
                    position.total_pnl = position.unrealized_pnl + position.realized_pnl
                    position.last_updated = datetime.now()
                
                total_market_value += position.market_value
                total_pnl += position.total_pnl
            
            # Mettre à jour le portefeuille
            portfolio.invested_amount = total_market_value
            portfolio.total_value = portfolio.cash_balance + total_market_value
            portfolio.total_pnl = total_pnl
            portfolio.unrealized_pnl = sum(p.unrealized_pnl for p in portfolio.active_positions.values())
            portfolio.last_updated = datetime.now()
            
            # Recalculer les poids
            await self._update_position_weights(portfolio)
            
            logger.info(f"Prix mis à jour pour {len(symbols)} positions")
            return portfolio
            
        except Exception as e:
            logger.error(f"Erreur mise à jour prix portefeuille {portfolio_id}: {e}")
            raise
    
    async def execute_decision(
        self, 
        portfolio_id: UUID, 
        decision: DecisionResult
    ) -> Optional[Transaction]:
        """
        Exécute une décision de trading.
        
        Args:
            portfolio_id: ID du portefeuille
            decision: Décision à exécuter
            
        Returns:
            Transaction: Transaction créée ou None si non exécutable
        """
        logger.info(f"Exécution décision {decision.action} pour {decision.symbol}")
        
        portfolio = self._portfolios.get(portfolio_id)
        if not portfolio:
            raise ValueError(f"Portefeuille {portfolio_id} non trouvé")
        
        try:
            # Vérifier si la décision est exécutable
            if not decision.is_actionable:
                logger.info(f"Décision non exécutable pour {decision.symbol}")
                return None
            
            # Créer la transaction selon l'action
            transaction = None
            
            if decision.action == DecisionAction.BUY:
                transaction = await self._execute_buy_order(portfolio, decision)
            elif decision.action == DecisionAction.SELL:
                transaction = await self._execute_sell_order(portfolio, decision)
            elif decision.action in [DecisionAction.INCREASE, DecisionAction.REDUCE]:
                transaction = await self._execute_adjustment_order(portfolio, decision)
            
            if transaction:
                # Enregistrer la transaction
                self._transactions[portfolio_id].append(transaction)
                
                # Mettre à jour le portefeuille
                await self._apply_transaction_to_portfolio(portfolio, transaction)
                
                logger.info(f"Transaction {transaction.id} exécutée avec succès")
            
            return transaction
            
        except Exception as e:
            logger.error(f"Erreur exécution décision pour {decision.symbol}: {e}")
            raise
    
    async def _execute_buy_order(
        self, 
        portfolio: Portfolio, 
        decision: DecisionResult
    ) -> Optional[Transaction]:
        """Exécute un ordre d'achat."""
        
        if not decision.quantity or decision.quantity <= 0:
            logger.warning(f"Quantité invalide pour achat {decision.symbol}")
            return None
        
        current_price = decision.decision_context.get('current_price', decision.price_target)
        if not current_price:
            # Récupérer le prix actuel
            quote = await self.openbb_provider.get_quote(decision.symbol)
            current_price = Decimal(str(quote.get('price', 0)))
        
        total_cost = decision.quantity * current_price
        fees = total_cost * self.transaction_fee
        total_amount = total_cost + fees
        
        # Vérifier le cash disponible
        if total_amount > portfolio.available_cash:
            logger.warning(f"Cash insuffisant pour {decision.symbol}: {total_amount} > {portfolio.available_cash}")
            return None
        
        # Créer la transaction
        transaction = Transaction(
            symbol=decision.symbol,
            transaction_type=TransactionType.BUY,
            quantity=decision.quantity,
            price=current_price,
            fees=fees,
            total_amount=total_amount,
            executed_at=datetime.now(),
            status=TransactionStatus.EXECUTED,
            decision_id=decision.id
        )
        
        return transaction
    
    async def _execute_sell_order(
        self, 
        portfolio: Portfolio, 
        decision: DecisionResult
    ) -> Optional[Transaction]:
        """Exécute un ordre de vente."""
        
        # Vérifier que la position existe
        if decision.symbol not in portfolio.positions:
            logger.warning(f"Aucune position pour {decision.symbol}")
            return None
        
        position = portfolio.positions[decision.symbol]
        
        # Déterminer la quantité à vendre
        if decision.quantity and decision.quantity > 0:
            sell_quantity = min(decision.quantity, position.available_quantity)
        else:
            # Vendre toute la position
            sell_quantity = position.available_quantity
        
        if sell_quantity <= 0:
            logger.warning(f"Aucune quantité disponible pour vente {decision.symbol}")
            return None
        
        current_price = decision.decision_context.get('current_price', decision.price_target)
        if not current_price:
            quote = await self.openbb_provider.get_quote(decision.symbol)
            current_price = Decimal(str(quote.get('price', 0)))
        
        total_proceeds = sell_quantity * current_price
        fees = total_proceeds * self.transaction_fee
        net_proceeds = total_proceeds - fees
        
        # Créer la transaction
        transaction = Transaction(
            symbol=decision.symbol,
            transaction_type=TransactionType.SELL,
            quantity=sell_quantity,
            price=current_price,
            fees=fees,
            total_amount=net_proceeds,
            executed_at=datetime.now(),
            status=TransactionStatus.EXECUTED,
            decision_id=decision.id
        )
        
        return transaction
    
    async def _execute_adjustment_order(
        self, 
        portfolio: Portfolio, 
        decision: DecisionResult
    ) -> Optional[Transaction]:
        """Exécute un ordre d'ajustement (augmentation/réduction)."""
        
        if decision.action == DecisionAction.INCREASE:
            # Traiter comme un achat
            return await self._execute_buy_order(portfolio, decision)
        elif decision.action == DecisionAction.REDUCE:
            # Traiter comme une vente partielle
            return await self._execute_sell_order(portfolio, decision)
        
        return None
    
    async def _apply_transaction_to_portfolio(
        self, 
        portfolio: Portfolio, 
        transaction: Transaction
    ):
        """Applique une transaction au portefeuille."""
        
        symbol = transaction.symbol
        
        if transaction.transaction_type == TransactionType.BUY:
            # Mise à jour pour achat
            if symbol in portfolio.positions:
                # Position existante
                position = portfolio.positions[symbol]
                if self.position_manager:
                    await self.position_manager.add_to_position(position, transaction)
                else:
                    # Mise à jour simple
                    new_quantity = position.quantity + transaction.quantity
                    new_cost = position.total_cost + transaction.total_amount
                    position.quantity = new_quantity
                    position.available_quantity = new_quantity
                    position.total_cost = new_cost
                    position.average_cost = new_cost / new_quantity
                    position.transactions.append(transaction.id)
            else:
                # Nouvelle position
                if self.position_manager:
                    position = await self.position_manager.create_position(
                        symbol, transaction
                    )
                else:
                    # Création simple
                    position = Position(
                        symbol=symbol,
                        quantity=transaction.quantity,
                        available_quantity=transaction.quantity,
                        average_cost=transaction.price,
                        total_cost=transaction.total_amount,
                        current_price=transaction.price,
                        market_value=transaction.quantity * transaction.price,
                        unrealized_pnl=Decimal("0"),
                        weight=0.0,
                        transactions=[transaction.id]
                    )
                
                portfolio.positions[symbol] = position
            
            # Réduire le cash
            portfolio.cash_balance -= transaction.total_amount
            portfolio.available_cash -= transaction.total_amount
            
        elif transaction.transaction_type == TransactionType.SELL:
            # Mise à jour pour vente
            if symbol in portfolio.positions:
                position = portfolio.positions[symbol]
                if self.position_manager:
                    await self.position_manager.reduce_position(position, transaction)
                else:
                    # Mise à jour simple
                    position.quantity -= transaction.quantity
                    position.available_quantity -= transaction.quantity
                    
                    # Calculer le P&L réalisé
                    cost_basis = position.average_cost * transaction.quantity
                    realized_pnl = transaction.total_amount - cost_basis
                    position.realized_pnl += realized_pnl
                    position.total_cost -= cost_basis
                    position.transactions.append(transaction.id)
                    
                    # Fermer la position si vide
                    if position.quantity == 0:
                        position.status = PositionStatus.CLOSED
            
            # Augmenter le cash
            portfolio.cash_balance += transaction.total_amount
            portfolio.available_cash += transaction.total_amount
        
        # Mettre à jour les métriques du portefeuille
        await self._update_portfolio_metrics(portfolio)
    
    async def _update_portfolio_metrics(self, portfolio: Portfolio):
        """Met à jour les métriques du portefeuille."""
        
        # Valeurs totales
        total_market_value = sum(
            pos.market_value for pos in portfolio.active_positions.values()
        )
        portfolio.invested_amount = total_market_value
        portfolio.total_value = portfolio.cash_balance + total_market_value
        
        # P&L
        portfolio.unrealized_pnl = sum(
            pos.unrealized_pnl for pos in portfolio.active_positions.values()
        )
        portfolio.realized_pnl = sum(
            pos.realized_pnl for pos in portfolio.positions.values()
        )
        portfolio.total_pnl = portfolio.unrealized_pnl + portfolio.realized_pnl
        
        # Allocation par secteur (simplifiée)
        await self._update_sector_allocation(portfolio)
        
        # Poids des positions
        await self._update_position_weights(portfolio)
        
        portfolio.last_updated = datetime.now()
    
    async def _update_position_weights(self, portfolio: Portfolio):
        """Met à jour les poids des positions."""
        
        if portfolio.total_value == 0:
            return
        
        for position in portfolio.positions.values():
            position.weight = float(position.market_value / portfolio.total_value)
    
    async def _update_sector_allocation(self, portfolio: Portfolio):
        """Met à jour l'allocation par secteur."""
        
        sector_values = {}
        
        for position in portfolio.active_positions.values():
            sector = position.sector or "Unknown"
            sector_values[sector] = sector_values.get(sector, Decimal("0")) + position.market_value
        
        # Convertir en pourcentages
        if portfolio.total_value > 0:
            portfolio.sector_allocation = {
                sector: float(value / portfolio.total_value)
                for sector, value in sector_values.items()
            }
    
    async def get_portfolio_metrics(self, portfolio_id: UUID) -> Optional[PortfolioMetrics]:
        """Récupère les métriques détaillées du portefeuille."""
        
        portfolio = self._portfolios.get(portfolio_id)
        if not portfolio:
            return None
        
        try:
            if self.performance_tracker:
                return await self.performance_tracker.calculate_metrics(portfolio)
            
            # Métriques de base
            cash_percentage = float(portfolio.cash_balance / portfolio.total_value) if portfolio.total_value > 0 else 1.0
            
            return PortfolioMetrics(
                portfolio_id=portfolio_id,
                total_value=portfolio.total_value,
                net_worth=portfolio.total_value,
                cash_percentage=cash_percentage,
                daily_return=0.0,  # Nécessite historique
                weekly_return=0.0,
                monthly_return=0.0,
                yearly_return=0.0,
                total_return=portfolio.return_percentage,
                volatility_1m=0.0,
                volatility_3m=0.0,
                volatility_1y=0.0,
                current_drawdown=0.0,
                max_drawdown_1m=0.0,
                max_drawdown_3m=0.0,
                max_drawdown_1y=0.0,
                position_count=portfolio.position_count,
                sector_count=len(portfolio.sector_allocation),
                herfindahl_index=0.0,
                concentration_ratio=0.0,
                sector_weights=portfolio.sector_allocation
            )
            
        except Exception as e:
            logger.error(f"Erreur calcul métriques portefeuille {portfolio_id}: {e}")
            return None
    
    async def get_rebalance_recommendations(
        self, 
        portfolio_id: UUID
    ) -> Optional[RebalanceRecommendation]:
        """Obtient les recommandations de rééquilibrage."""
        
        portfolio = self._portfolios.get(portfolio_id)
        if not portfolio:
            return None
        
        try:
            if self.rebalancer:
                return await self.rebalancer.analyze_portfolio(portfolio)
            
            # Analyse simple de rééquilibrage
            deviations = {}
            for symbol, target_weight in portfolio.target_allocation.items():
                current_weight = 0.0
                if symbol in portfolio.positions:
                    current_weight = portfolio.positions[symbol].weight
                
                deviation = current_weight - target_weight
                if abs(deviation) > portfolio.rebalance_threshold:
                    deviations[symbol] = deviation
            
            if not deviations:
                return None
            
            # Créer une recommandation simple
            actions = []
            for symbol, deviation in deviations.items():
                if deviation > 0:
                    actions.append({
                        'symbol': symbol,
                        'action': 'SELL',
                        'amount': abs(deviation) * float(portfolio.total_value)
                    })
                else:
                    actions.append({
                        'symbol': symbol,
                        'action': 'BUY',
                        'amount': abs(deviation) * float(portfolio.total_value)
                    })
            
            return RebalanceRecommendation(
                portfolio_id=portfolio_id,
                rebalance_type="threshold",
                current_allocations={s: p.weight for s, p in portfolio.positions.items()},
                target_allocations=portfolio.target_allocation,
                deviations=deviations,
                actions=actions,
                estimated_cost=Decimal("0"),
                expected_improvement=0.1,
                priority=3,
                urgency_score=0.5,
                reason="Déviation des allocations cibles"
            )
            
        except Exception as e:
            logger.error(f"Erreur recommandations rééquilibrage pour {portfolio_id}: {e}")
            return None
    
    async def get_transaction_history(
        self, 
        portfolio_id: UUID,
        limit: Optional[int] = None
    ) -> List[Transaction]:
        """Récupère l'historique des transactions."""
        
        transactions = self._transactions.get(portfolio_id, [])
        
        # Trier par date (plus récent en premier)
        transactions.sort(key=lambda t: t.executed_at or t.created_at, reverse=True)
        
        if limit:
            transactions = transactions[:limit]
        
        return transactions
    
    async def list_portfolios(self) -> List[Portfolio]:
        """Liste tous les portefeuilles."""
        return list(self._portfolios.values())