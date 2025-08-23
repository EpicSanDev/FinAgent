"""
Gestionnaire de positions - Gestion détaillée des positions individuelles.
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Any
from uuid import UUID

from finagent.business.models.portfolio_models import (
    Position,
    Transaction,
    TransactionType,
    PositionType,
    PositionStatus
)
from finagent.data.providers.openbb_provider import OpenBBProvider

logger = logging.getLogger(__name__)


class PositionManager:
    """
    Gestionnaire de positions individuelles.
    
    Responsabilités :
    - Création et fermeture de positions
    - Calcul des coûts moyens (FIFO, LIFO, Average)
    - Suivi du P&L réalisé et non réalisé
    - Gestion des lots (parcels) pour optimisation fiscale
    - Mise à jour des prix et valorisation
    """
    
    def __init__(
        self,
        openbb_provider: OpenBBProvider,
        cost_method: str = "average"  # "fifo", "lifo", "average"
    ):
        """
        Initialise le gestionnaire de positions.
        
        Args:
            openbb_provider: Provider de données financières
            cost_method: Méthode de calcul des coûts
        """
        self.openbb_provider = openbb_provider
        self.cost_method = cost_method
        
        # Cache des informations de titres
        self._security_info_cache: Dict[str, Dict[str, Any]] = {}
        
        logger.info(f"Gestionnaire de positions initialisé (méthode: {cost_method})")
    
    async def create_position(
        self, 
        symbol: str, 
        initial_transaction: Transaction
    ) -> Position:
        """
        Crée une nouvelle position à partir d'une transaction.
        
        Args:
            symbol: Symbole du titre
            initial_transaction: Transaction initiale d'achat
            
        Returns:
            Position: Nouvelle position créée
        """
        logger.info(f"Création position pour {symbol}")
        
        try:
            # Récupérer les informations du titre
            security_info = await self._get_security_info(symbol)
            
            # Créer la position
            position = Position(
                symbol=symbol,
                position_type=PositionType.LONG,  # Par défaut
                quantity=initial_transaction.quantity,
                available_quantity=initial_transaction.quantity,
                average_cost=initial_transaction.price,
                total_cost=initial_transaction.total_amount,
                current_price=initial_transaction.price,
                market_value=initial_transaction.quantity * initial_transaction.price,
                unrealized_pnl=Decimal("0"),
                weight=0.0,  # Sera calculé par le PortfolioManager
                sector=security_info.get('sector'),
                industry=security_info.get('industry'),
                transactions=[initial_transaction.id]
            )
            
            logger.info(f"Position créée pour {symbol}: {position.quantity} @ {position.average_cost}")
            return position
            
        except Exception as e:
            logger.error(f"Erreur création position pour {symbol}: {e}")
            raise
    
    async def add_to_position(
        self, 
        position: Position, 
        transaction: Transaction
    ) -> Position:
        """
        Ajoute à une position existante.
        
        Args:
            position: Position existante
            transaction: Transaction d'achat supplémentaire
            
        Returns:
            Position: Position mise à jour
        """
        logger.info(f"Ajout à la position {position.symbol}: {transaction.quantity}")
        
        try:
            # Vérifier que c'est une transaction d'achat
            if transaction.transaction_type != TransactionType.BUY:
                raise ValueError("Seules les transactions d'achat peuvent être ajoutées")
            
            # Calculer le nouveau coût moyen selon la méthode
            new_quantity = position.quantity + transaction.quantity
            
            if self.cost_method == "average":
                # Coût moyen pondéré
                new_total_cost = position.total_cost + transaction.total_amount
                new_average_cost = new_total_cost / new_quantity
            elif self.cost_method == "fifo":
                # FIFO - garder le coût séparément par lot
                new_total_cost = position.total_cost + transaction.total_amount
                new_average_cost = new_total_cost / new_quantity
            elif self.cost_method == "lifo":
                # LIFO - garder le coût séparément par lot
                new_total_cost = position.total_cost + transaction.total_amount
                new_average_cost = new_total_cost / new_quantity
            else:
                raise ValueError(f"Méthode de coût non supportée: {self.cost_method}")
            
            # Mettre à jour la position
            position.quantity = new_quantity
            position.available_quantity = new_quantity
            position.average_cost = new_average_cost
            position.total_cost = new_total_cost
            position.market_value = new_quantity * position.current_price
            position.unrealized_pnl = position.market_value - position.total_cost
            position.total_pnl = position.unrealized_pnl + position.realized_pnl
            position.transactions.append(transaction.id)
            position.last_updated = datetime.now()
            
            logger.info(f"Position {position.symbol} mise à jour: {position.quantity} @ {position.average_cost}")
            return position
            
        except Exception as e:
            logger.error(f"Erreur ajout à la position {position.symbol}: {e}")
            raise
    
    async def reduce_position(
        self, 
        position: Position, 
        transaction: Transaction
    ) -> Position:
        """
        Réduit une position existante (vente).
        
        Args:
            position: Position existante
            transaction: Transaction de vente
            
        Returns:
            Position: Position mise à jour
        """
        logger.info(f"Réduction position {position.symbol}: {transaction.quantity}")
        
        try:
            # Vérifier que c'est une transaction de vente
            if transaction.transaction_type != TransactionType.SELL:
                raise ValueError("Seules les transactions de vente peuvent réduire une position")
            
            # Vérifier qu'on a assez de quantité
            if transaction.quantity > position.available_quantity:
                raise ValueError(f"Quantité insuffisante: {transaction.quantity} > {position.available_quantity}")
            
            # Calculer le P&L réalisé selon la méthode
            cost_basis = await self._calculate_cost_basis(position, transaction.quantity)
            realized_pnl = transaction.total_amount - cost_basis
            
            # Mettre à jour la position
            position.quantity -= transaction.quantity
            position.available_quantity -= transaction.quantity
            position.total_cost -= cost_basis
            position.realized_pnl += realized_pnl
            
            # Recalculer le coût moyen si nécessaire
            if position.quantity > 0:
                position.average_cost = position.total_cost / position.quantity
                position.market_value = position.quantity * position.current_price
                position.unrealized_pnl = position.market_value - position.total_cost
            else:
                # Position fermée
                position.average_cost = Decimal("0")
                position.market_value = Decimal("0")
                position.unrealized_pnl = Decimal("0")
                position.status = PositionStatus.CLOSED
            
            position.total_pnl = position.unrealized_pnl + position.realized_pnl
            position.transactions.append(transaction.id)
            position.last_updated = datetime.now()
            
            logger.info(f"Position {position.symbol} réduite: {position.quantity} restant, P&L réalisé: {realized_pnl}")
            return position
            
        except Exception as e:
            logger.error(f"Erreur réduction position {position.symbol}: {e}")
            raise
    
    async def update_position_price(
        self, 
        position: Position, 
        new_price: Decimal
    ) -> Position:
        """
        Met à jour le prix d'une position et recalcule les métriques.
        
        Args:
            position: Position à mettre à jour
            new_price: Nouveau prix du marché
            
        Returns:
            Position: Position mise à jour
        """
        try:
            # Mettre à jour le prix et les métriques
            position.current_price = new_price
            position.market_value = position.quantity * new_price
            position.unrealized_pnl = position.market_value - position.total_cost
            position.total_pnl = position.unrealized_pnl + position.realized_pnl
            position.last_updated = datetime.now()
            
            return position
            
        except Exception as e:
            logger.error(f"Erreur mise à jour prix position {position.symbol}: {e}")
            raise
    
    async def close_position(
        self, 
        position: Position, 
        closing_transaction: Transaction
    ) -> Position:
        """
        Ferme complètement une position.
        
        Args:
            position: Position à fermer
            closing_transaction: Transaction de fermeture
            
        Returns:
            Position: Position fermée
        """
        logger.info(f"Fermeture position {position.symbol}")
        
        try:
            # Vérifier que la transaction ferme toute la position
            if closing_transaction.quantity != position.quantity:
                raise ValueError("La transaction ne ferme pas toute la position")
            
            # Réduire la position à zéro
            await self.reduce_position(position, closing_transaction)
            
            # Marquer comme fermée
            position.status = PositionStatus.CLOSED
            
            logger.info(f"Position {position.symbol} fermée, P&L total: {position.total_pnl}")
            return position
            
        except Exception as e:
            logger.error(f"Erreur fermeture position {position.symbol}: {e}")
            raise
    
    async def calculate_position_metrics(self, position: Position) -> Dict[str, Any]:
        """
        Calcule les métriques détaillées d'une position.
        
        Args:
            position: Position à analyser
            
        Returns:
            Dict: Métriques de la position
        """
        try:
            metrics = {
                'symbol': position.symbol,
                'quantity': float(position.quantity),
                'market_value': float(position.market_value),
                'total_cost': float(position.total_cost),
                'average_cost': float(position.average_cost),
                'current_price': float(position.current_price),
                'unrealized_pnl': float(position.unrealized_pnl),
                'realized_pnl': float(position.realized_pnl),
                'total_pnl': float(position.total_pnl),
                'return_percentage': position.return_percentage,
                'weight': position.weight,
                'is_profitable': position.is_profitable,
                'days_held': (datetime.now() - position.opened_at).days,
                'sector': position.sector,
                'industry': position.industry
            }
            
            # Métriques additionnelles
            if position.market_value > 0:
                metrics['price_change'] = float(
                    (position.current_price - position.average_cost) / position.average_cost * 100
                )
            else:
                metrics['price_change'] = 0.0
            
            # Distance des niveaux de support/résistance (si disponible)
            security_info = await self._get_security_info(position.symbol)
            if 'support_level' in security_info:
                support_distance = float(
                    (position.current_price - security_info['support_level']) / position.current_price * 100
                )
                metrics['support_distance_pct'] = support_distance
            
            if 'resistance_level' in security_info:
                resistance_distance = float(
                    (security_info['resistance_level'] - position.current_price) / position.current_price * 100
                )
                metrics['resistance_distance_pct'] = resistance_distance
            
            return metrics
            
        except Exception as e:
            logger.error(f"Erreur calcul métriques position {position.symbol}: {e}")
            return {}
    
    async def get_position_risk_metrics(self, position: Position) -> Dict[str, Any]:
        """
        Calcule les métriques de risque d'une position.
        
        Args:
            position: Position à analyser
            
        Returns:
            Dict: Métriques de risque
        """
        try:
            # Récupérer les données historiques pour le calcul de volatilité
            historical_data = await self.openbb_provider.get_historical_data(
                position.symbol, period="3m", interval="1d"
            )
            
            risk_metrics = {
                'symbol': position.symbol,
                'position_size': float(position.market_value),
                'concentration_risk': position.weight,
                'sector': position.sector
            }
            
            if historical_data and len(historical_data) > 20:
                import pandas as pd
                import numpy as np
                
                df = pd.DataFrame(historical_data)
                returns = df['close'].pct_change().dropna()
                
                # Volatilité
                volatility = float(returns.std() * np.sqrt(252))
                risk_metrics['volatility'] = volatility
                
                # VaR de la position (95%)
                var_95 = float(np.percentile(returns, 5))
                position_var = position.market_value * abs(var_95)
                risk_metrics['position_var_95'] = float(position_var)
                
                # Maximum drawdown
                cumulative = (1 + returns).cumprod()
                running_max = cumulative.cummax()
                drawdown = (cumulative - running_max) / running_max
                max_drawdown = float(abs(drawdown.min()))
                risk_metrics['max_drawdown'] = max_drawdown
                
                # Beta (si possible avec un benchmark)
                risk_metrics['estimated_beta'] = min(2.0, max(0.5, volatility / 0.16))  # Estimation simple
            
            return risk_metrics
            
        except Exception as e:
            logger.error(f"Erreur calcul métriques risque position {position.symbol}: {e}")
            return {'symbol': position.symbol, 'error': str(e)}
    
    async def _calculate_cost_basis(
        self, 
        position: Position, 
        quantity_sold: Decimal
    ) -> Decimal:
        """
        Calcule le coût de base pour une vente selon la méthode choisie.
        
        Args:
            position: Position concernée
            quantity_sold: Quantité vendue
            
        Returns:
            Decimal: Coût de base
        """
        try:
            if self.cost_method == "average":
                # Coût moyen
                return position.average_cost * quantity_sold
            
            elif self.cost_method == "fifo":
                # FIFO - First In, First Out
                # Pour une implémentation simple, utiliser le coût moyen
                # En production, il faudrait tracker les lots individuels
                return position.average_cost * quantity_sold
            
            elif self.cost_method == "lifo":
                # LIFO - Last In, First Out
                # Pour une implémentation simple, utiliser le coût moyen
                # En production, il faudrait tracker les lots individuels
                return position.average_cost * quantity_sold
            
            else:
                # Par défaut, coût moyen
                return position.average_cost * quantity_sold
                
        except Exception as e:
            logger.error(f"Erreur calcul coût de base: {e}")
            return position.average_cost * quantity_sold
    
    async def _get_security_info(self, symbol: str) -> Dict[str, Any]:
        """
        Récupère les informations d'un titre avec cache.
        
        Args:
            symbol: Symbole du titre
            
        Returns:
            Dict: Informations du titre
        """
        try:
            # Vérifier le cache
            if symbol in self._security_info_cache:
                return self._security_info_cache[symbol]
            
            # Récupérer les informations
            company_info = await self.openbb_provider.get_company_info(symbol)
            
            security_info = {
                'sector': company_info.get('sector', 'Unknown'),
                'industry': company_info.get('industry', 'Unknown'),
                'market_cap': company_info.get('market_cap'),
                'pe_ratio': company_info.get('pe_ratio'),
                'dividend_yield': company_info.get('dividend_yield'),
                'beta': company_info.get('beta')
            }
            
            # Mettre en cache
            self._security_info_cache[symbol] = security_info
            
            return security_info
            
        except Exception as e:
            logger.warning(f"Erreur récupération info titre {symbol}: {e}")
            return {
                'sector': 'Unknown',
                'industry': 'Unknown'
            }
    
    def set_cost_method(self, method: str):
        """
        Change la méthode de calcul des coûts.
        
        Args:
            method: Nouvelle méthode ("average", "fifo", "lifo")
        """
        if method not in ["average", "fifo", "lifo"]:
            raise ValueError(f"Méthode non supportée: {method}")
        
        self.cost_method = method
        logger.info(f"Méthode de coût changée pour: {method}")
    
    async def split_position(
        self, 
        position: Position, 
        split_ratio: float,
        split_date: datetime = None
    ) -> Position:
        """
        Applique un split d'actions à une position.
        
        Args:
            position: Position concernée
            split_ratio: Ratio du split (ex: 2.0 pour 2:1)
            split_date: Date du split
            
        Returns:
            Position: Position ajustée
        """
        logger.info(f"Application split {split_ratio}:1 pour {position.symbol}")
        
        try:
            if split_date is None:
                split_date = datetime.now()
            
            # Ajuster les quantités
            position.quantity *= Decimal(str(split_ratio))
            position.available_quantity *= Decimal(str(split_ratio))
            
            # Ajuster les prix
            position.average_cost /= Decimal(str(split_ratio))
            position.current_price /= Decimal(str(split_ratio))
            
            # La valeur de marché et les P&L restent inchangés
            position.market_value = position.quantity * position.current_price
            position.last_updated = datetime.now()
            
            logger.info(f"Split appliqué: {position.quantity} @ {position.average_cost}")
            return position
            
        except Exception as e:
            logger.error(f"Erreur application split pour {position.symbol}: {e}")
            raise
    
    async def apply_dividend(
        self, 
        position: Position, 
        dividend_per_share: Decimal,
        dividend_date: datetime = None
    ) -> Decimal:
        """
        Applique un dividende à une position.
        
        Args:
            position: Position concernée
            dividend_per_share: Dividende par action
            dividend_date: Date du dividende
            
        Returns:
            Decimal: Montant total du dividende
        """
        logger.info(f"Application dividende {dividend_per_share} pour {position.symbol}")
        
        try:
            if dividend_date is None:
                dividend_date = datetime.now()
            
            # Calculer le dividende total
            total_dividend = position.quantity * dividend_per_share
            
            # Ajouter au P&L réalisé
            position.realized_pnl += total_dividend
            position.total_pnl += total_dividend
            position.last_updated = datetime.now()
            
            logger.info(f"Dividende appliqué: {total_dividend}")
            return total_dividend
            
        except Exception as e:
            logger.error(f"Erreur application dividende pour {position.symbol}: {e}")
            raise