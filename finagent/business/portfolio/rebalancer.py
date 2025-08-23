"""
Rééquilibreur de portefeuille - Analyse et recommandations de rééquilibrage.
"""

import asyncio
import logging
import numpy as np
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID

from finagent.business.models.portfolio_models import (
    Portfolio,
    Position,
    RebalanceRecommendation,
    RebalanceType
)
from finagent.data.providers.openbb_provider import OpenBBProvider

logger = logging.getLogger(__name__)


class Rebalancer:
    """
    Gestionnaire de rééquilibrage du portefeuille.
    
    Analyse :
    - Déviations par rapport aux allocations cibles
    - Dérive du portefeuille dans le temps
    - Opportunités de rééquilibrage
    - Coûts de transaction vs bénéfices
    - Optimisation fiscale
    """
    
    def __init__(
        self,
        openbb_provider: OpenBBProvider,
        transaction_cost_rate: float = 0.001,  # 0.1%
        tax_rate: float = 0.28  # 28% gains en capital
    ):
        """
        Initialise le rééquilibreur.
        
        Args:
            openbb_provider: Provider de données financières
            transaction_cost_rate: Taux de frais de transaction
            tax_rate: Taux d'imposition sur les gains en capital
        """
        self.openbb_provider = openbb_provider
        self.transaction_cost_rate = transaction_cost_rate
        self.tax_rate = tax_rate
        
        # Seuils de rééquilibrage
        self.default_thresholds = {
            'minor': 0.02,      # 2% - rééquilibrage mineur
            'moderate': 0.05,   # 5% - rééquilibrage modéré
            'major': 0.10       # 10% - rééquilibrage majeur
        }
        
        # Configuration
        self.min_trade_amount = Decimal("100")
        self.max_turnover = 0.25  # 25% max du portefeuille
        
        logger.info("Rééquilibreur initialisé")
    
    async def analyze_portfolio(self, portfolio: Portfolio) -> Optional[RebalanceRecommendation]:
        """
        Analyse un portefeuille et génère des recommandations de rééquilibrage.
        
        Args:
            portfolio: Portefeuille à analyser
            
        Returns:
            RebalanceRecommendation: Recommandations ou None si pas nécessaire
        """
        logger.info(f"Analyse rééquilibrage pour portefeuille {portfolio.id}")
        
        try:
            # Vérifier s'il y a des allocations cibles
            if not portfolio.target_allocation:
                logger.info("Pas d'allocation cible définie")
                return None
            
            # Calculer les déviations actuelles
            deviations = await self._calculate_deviations(portfolio)
            
            # Vérifier si un rééquilibrage est nécessaire
            max_deviation = max(abs(dev) for dev in deviations.values()) if deviations else 0
            
            if max_deviation < portfolio.rebalance_threshold:
                logger.info(f"Déviation max {max_deviation:.3f} sous le seuil {portfolio.rebalance_threshold}")
                return None
            
            # Déterminer le type de rééquilibrage
            rebalance_type = self._determine_rebalance_type(max_deviation)
            
            # Générer les actions de rééquilibrage
            actions = await self._generate_rebalance_actions(portfolio, deviations)
            
            if not actions:
                logger.info("Aucune action de rééquilibrage nécessaire")
                return None
            
            # Calculer les coûts et bénéfices
            cost_analysis = await self._analyze_rebalance_costs(portfolio, actions)
            
            # Vérifier si le rééquilibrage est rentable
            if not self._is_rebalance_worthwhile(cost_analysis, max_deviation):
                logger.info("Rééquilibrage non rentable")
                return None
            
            # Optimiser les actions pour minimiser les coûts
            optimized_actions = await self._optimize_rebalance_actions(portfolio, actions)
            
            # Déterminer la priorité et l'urgence
            priority, urgency = self._assess_urgency(max_deviation, portfolio)
            
            # Créer la recommandation
            recommendation = RebalanceRecommendation(
                portfolio_id=portfolio.id,
                rebalance_type=rebalance_type,
                current_allocations=self._get_current_allocations(portfolio),
                target_allocations=portfolio.target_allocation,
                deviations=deviations,
                actions=optimized_actions,
                estimated_cost=cost_analysis['total_cost'],
                expected_improvement=self._calculate_expected_improvement(max_deviation),
                priority=priority,
                urgency_score=urgency,
                reason=self._generate_rebalance_reason(max_deviation, deviations),
                risk_impact=self._assess_risk_impact(portfolio, optimized_actions),
                max_turnover=self.max_turnover,
                min_trade_size=self.min_trade_amount
            )
            
            logger.info(f"Recommandation générée: {len(optimized_actions)} actions, coût {cost_analysis['total_cost']}")
            return recommendation
            
        except Exception as e:
            logger.error(f"Erreur analyse rééquilibrage: {e}")
            return None
    
    async def _calculate_deviations(self, portfolio: Portfolio) -> Dict[str, float]:
        """Calcule les déviations par rapport aux allocations cibles."""
        
        deviations = {}
        current_allocations = self._get_current_allocations(portfolio)
        
        # Déviations pour les positions existantes et cibles
        all_symbols = set(current_allocations.keys()) | set(portfolio.target_allocation.keys())
        
        for symbol in all_symbols:
            current_weight = current_allocations.get(symbol, 0.0)
            target_weight = portfolio.target_allocation.get(symbol, 0.0)
            deviation = current_weight - target_weight
            
            # Ignorer les très petites déviations
            if abs(deviation) >= 0.005:  # 0.5%
                deviations[symbol] = deviation
        
        return deviations
    
    def _get_current_allocations(self, portfolio: Portfolio) -> Dict[str, float]:
        """Récupère les allocations actuelles du portefeuille."""
        
        current_allocations = {}
        
        for symbol, position in portfolio.active_positions.items():
            current_allocations[symbol] = position.weight
        
        return current_allocations
    
    def _determine_rebalance_type(self, max_deviation: float) -> RebalanceType:
        """Détermine le type de rééquilibrage nécessaire."""
        
        if max_deviation >= self.default_thresholds['major']:
            return RebalanceType.RISK_DRIVEN
        elif max_deviation >= self.default_thresholds['moderate']:
            return RebalanceType.THRESHOLD
        else:
            return RebalanceType.AUTOMATIC
    
    async def _generate_rebalance_actions(
        self, 
        portfolio: Portfolio, 
        deviations: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """Génère les actions de rééquilibrage nécessaires."""
        
        actions = []
        
        try:
            # Séparer les sur-pondérations (à vendre) et sous-pondérations (à acheter)
            to_sell = {k: v for k, v in deviations.items() if v > 0}
            to_buy = {k: -v for k, v in deviations.items() if v < 0}
            
            # Générer les ordres de vente
            for symbol, over_weight in to_sell.items():
                if symbol in portfolio.positions:
                    position = portfolio.positions[symbol]
                    
                    # Calculer la quantité à vendre
                    target_value = portfolio.target_allocation.get(symbol, 0.0) * portfolio.total_value
                    current_value = position.market_value
                    value_to_sell = current_value - target_value
                    
                    if value_to_sell > self.min_trade_amount:
                        quantity_to_sell = value_to_sell / position.current_price
                        
                        # Éviter de vendre plus que disponible
                        quantity_to_sell = min(quantity_to_sell, position.available_quantity)
                        
                        if quantity_to_sell > 0:
                            actions.append({
                                'symbol': symbol,
                                'action': 'SELL',
                                'quantity': float(quantity_to_sell),
                                'amount': float(value_to_sell),
                                'current_price': float(position.current_price),
                                'reason': f'Réduction sur-pondération de {over_weight:.2%}'
                            })
            
            # Générer les ordres d'achat
            for symbol, under_weight in to_buy.items():
                target_value = portfolio.target_allocation.get(symbol, 0.0) * portfolio.total_value
                current_value = 0.0
                
                if symbol in portfolio.positions:
                    current_value = portfolio.positions[symbol].market_value
                
                value_to_buy = target_value - current_value
                
                if value_to_buy > self.min_trade_amount:
                    # Récupérer le prix actuel
                    try:
                        quote = await self.openbb_provider.get_quote(symbol)
                        current_price = Decimal(str(quote.get('price', 0)))
                        
                        if current_price > 0:
                            quantity_to_buy = value_to_buy / current_price
                            
                            actions.append({
                                'symbol': symbol,
                                'action': 'BUY',
                                'quantity': float(quantity_to_buy),
                                'amount': float(value_to_buy),
                                'current_price': float(current_price),
                                'reason': f'Augmentation sous-pondération de {under_weight:.2%}'
                            })
                    except Exception as e:
                        logger.warning(f"Erreur récupération prix pour {symbol}: {e}")
                        continue
            
            return actions
            
        except Exception as e:
            logger.error(f"Erreur génération actions rééquilibrage: {e}")
            return []
    
    async def _analyze_rebalance_costs(
        self, 
        portfolio: Portfolio, 
        actions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyse les coûts du rééquilibrage."""
        
        try:
            total_transaction_value = sum(action['amount'] for action in actions)
            transaction_costs = total_transaction_value * self.transaction_cost_rate
            
            # Coûts fiscaux (gains en capital)
            tax_costs = 0.0
            
            for action in actions:
                if action['action'] == 'SELL' and action['symbol'] in portfolio.positions:
                    position = portfolio.positions[action['symbol']]
                    
                    # Calculer le gain en capital
                    sell_quantity = Decimal(str(action['quantity']))
                    cost_basis = position.average_cost * sell_quantity
                    proceeds = Decimal(str(action['amount']))
                    
                    if proceeds > cost_basis:
                        capital_gain = proceeds - cost_basis
                        tax_costs += float(capital_gain) * self.tax_rate
            
            # Impact de marché (estimation)
            market_impact = total_transaction_value * 0.0005  # 0.05% estimation
            
            total_cost = transaction_costs + tax_costs + market_impact
            
            return {
                'total_cost': Decimal(str(total_cost)),
                'transaction_costs': transaction_costs,
                'tax_costs': tax_costs,
                'market_impact': market_impact,
                'total_transaction_value': total_transaction_value
            }
            
        except Exception as e:
            logger.error(f"Erreur analyse coûts rééquilibrage: {e}")
            return {
                'total_cost': Decimal("0"),
                'transaction_costs': 0.0,
                'tax_costs': 0.0,
                'market_impact': 0.0,
                'total_transaction_value': 0.0
            }
    
    def _is_rebalance_worthwhile(
        self, 
        cost_analysis: Dict[str, Any], 
        max_deviation: float
    ) -> bool:
        """Détermine si le rééquilibrage vaut la peine selon les coûts."""
        
        try:
            total_cost_pct = float(cost_analysis['total_cost']) / float(cost_analysis['total_transaction_value'])
            
            # Seuils de rentabilité selon la déviation
            if max_deviation >= 0.10:  # 10%+
                return total_cost_pct < 0.02  # Acceptable jusqu'à 2% de coûts
            elif max_deviation >= 0.05:  # 5-10%
                return total_cost_pct < 0.01  # Acceptable jusqu'à 1% de coûts
            else:  # < 5%
                return total_cost_pct < 0.005  # Acceptable jusqu'à 0.5% de coûts
                
        except Exception as e:
            logger.error(f"Erreur évaluation rentabilité: {e}")
            return False
    
    async def _optimize_rebalance_actions(
        self, 
        portfolio: Portfolio, 
        actions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Optimise les actions de rééquilibrage pour minimiser les coûts."""
        
        try:
            optimized_actions = []
            
            # Grouper par action (vente/achat)
            sells = [a for a in actions if a['action'] == 'SELL']
            buys = [a for a in actions if a['action'] == 'BUY']
            
            # Optimiser les ventes (prioriser les positions avec gains limités)
            optimized_sells = await self._optimize_sell_orders(portfolio, sells)
            
            # Optimiser les achats (prioriser selon la liquidité)
            optimized_buys = await self._optimize_buy_orders(buys)
            
            # Équilibrer les montants (cash flow neutre)
            balanced_actions = self._balance_cash_flows(optimized_sells, optimized_buys)
            
            return balanced_actions
            
        except Exception as e:
            logger.error(f"Erreur optimisation actions: {e}")
            return actions
    
    async def _optimize_sell_orders(
        self, 
        portfolio: Portfolio, 
        sell_actions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Optimise les ordres de vente pour minimiser l'impact fiscal."""
        
        optimized_sells = []
        
        for action in sell_actions:
            symbol = action['symbol']
            if symbol not in portfolio.positions:
                continue
            
            position = portfolio.positions[symbol]
            
            # Calculer l'impact fiscal
            sell_quantity = Decimal(str(action['quantity']))
            cost_basis = position.average_cost * sell_quantity
            proceeds = Decimal(str(action['amount']))
            
            # Prioriser les ventes avec faible impact fiscal
            if proceeds > cost_basis:
                capital_gain = proceeds - cost_basis
                tax_impact = float(capital_gain) * self.tax_rate
                action['tax_impact'] = tax_impact
                action['tax_efficiency'] = action['amount'] / (action['amount'] + tax_impact)
            else:
                action['tax_impact'] = 0.0
                action['tax_efficiency'] = 1.0
            
            optimized_sells.append(action)
        
        # Trier par efficacité fiscale (plus efficace en premier)
        optimized_sells.sort(key=lambda x: x['tax_efficiency'], reverse=True)
        
        return optimized_sells
    
    async def _optimize_buy_orders(self, buy_actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Optimise les ordres d'achat selon la liquidité et les coûts."""
        
        optimized_buys = []
        
        for action in buy_actions:
            # Évaluer la liquidité (simulation)
            symbol = action['symbol']
            
            try:
                # Récupérer les données de volume
                volume_data = await self.openbb_provider.get_historical_data(
                    symbol, period="1mo", interval="1d"
                )
                
                if volume_data:
                    import pandas as pd
                    df = pd.DataFrame(volume_data)
                    avg_volume = df['volume'].mean() if 'volume' in df.columns else 0
                    
                    # Score de liquidité
                    trade_volume = action['quantity']
                    liquidity_ratio = trade_volume / avg_volume if avg_volume > 0 else 1.0
                    
                    # Impact de marché estimé
                    if liquidity_ratio < 0.01:  # < 1% du volume quotidien
                        market_impact = 0.0005
                    elif liquidity_ratio < 0.05:  # < 5%
                        market_impact = 0.001
                    else:  # > 5%
                        market_impact = 0.002
                    
                    action['liquidity_score'] = 1.0 / (1.0 + liquidity_ratio)
                    action['market_impact'] = market_impact
                else:
                    action['liquidity_score'] = 0.5
                    action['market_impact'] = 0.001
                    
            except Exception as e:
                logger.warning(f"Erreur évaluation liquidité {symbol}: {e}")
                action['liquidity_score'] = 0.5
                action['market_impact'] = 0.001
            
            optimized_buys.append(action)
        
        # Trier par score de liquidité (plus liquide en premier)
        optimized_buys.sort(key=lambda x: x['liquidity_score'], reverse=True)
        
        return optimized_buys
    
    def _balance_cash_flows(
        self, 
        sells: List[Dict[str, Any]], 
        buys: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Équilibre les flux de trésorerie pour être cash-neutre."""
        
        total_sells = sum(action['amount'] for action in sells)
        total_buys = sum(action['amount'] for action in buys)
        
        balanced_actions = []
        
        # Ajouter toutes les ventes
        balanced_actions.extend(sells)
        
        # Ajuster les achats pour équilibrer
        if total_buys > 0:
            adjustment_factor = total_sells / total_buys
            
            for buy_action in buys:
                # Ajuster le montant et la quantité
                buy_action['amount'] *= adjustment_factor
                buy_action['quantity'] *= adjustment_factor
                balanced_actions.append(buy_action)
        
        return balanced_actions
    
    def _assess_urgency(self, max_deviation: float, portfolio: Portfolio) -> Tuple[int, float]:
        """Évalue la priorité et l'urgence du rééquilibrage."""
        
        # Priorité (1=haute, 5=basse)
        if max_deviation >= 0.15:  # 15%+
            priority = 1
            urgency = 0.9
        elif max_deviation >= 0.10:  # 10-15%
            priority = 2
            urgency = 0.7
        elif max_deviation >= 0.07:  # 7-10%
            priority = 3
            urgency = 0.5
        elif max_deviation >= 0.05:  # 5-7%
            priority = 4
            urgency = 0.3
        else:  # < 5%
            priority = 5
            urgency = 0.1
        
        # Ajuster selon le temps depuis le dernier rééquilibrage
        if portfolio.last_rebalance:
            days_since = (datetime.now() - portfolio.last_rebalance).days
            if days_since > 90:  # > 3 mois
                urgency = min(1.0, urgency + 0.2)
                priority = max(1, priority - 1)
        
        return priority, urgency
    
    def _calculate_expected_improvement(self, max_deviation: float) -> float:
        """Calcule l'amélioration attendue du rééquilibrage."""
        
        # Estimation simple basée sur la réduction de la déviation
        # En pratique, cela devrait être basé sur des métriques de risque
        return min(0.5, max_deviation * 2)  # Max 50% d'amélioration
    
    def _generate_rebalance_reason(
        self, 
        max_deviation: float, 
        deviations: Dict[str, float]
    ) -> str:
        """Génère une raison textuelle pour le rééquilibrage."""
        
        # Trouver la plus grande déviation
        max_symbol = max(deviations.keys(), key=lambda k: abs(deviations[k]))
        max_dev = deviations[max_symbol]
        
        if max_dev > 0:
            return f"Sur-pondération de {max_symbol} ({max_dev:.1%}), déviation max: {max_deviation:.1%}"
        else:
            return f"Sous-pondération de {max_symbol} ({abs(max_dev):.1%}), déviation max: {max_deviation:.1%}"
    
    def _assess_risk_impact(
        self, 
        portfolio: Portfolio, 
        actions: List[Dict[str, Any]]
    ) -> str:
        """Évalue l'impact sur le risque du portefeuille."""
        
        # Analyse simplifiée
        total_transaction_value = sum(action['amount'] for action in actions)
        turnover = total_transaction_value / float(portfolio.total_value)
        
        if turnover > 0.20:  # > 20%
            return "Impact élevé sur le risque - turnover important"
        elif turnover > 0.10:  # > 10%
            return "Impact modéré sur le risque"
        else:
            return "Impact faible sur le risque"
    
    async def execute_rebalance(
        self, 
        portfolio: Portfolio, 
        recommendation: RebalanceRecommendation
    ) -> Dict[str, Any]:
        """
        Exécute un plan de rééquilibrage.
        
        Args:
            portfolio: Portefeuille à rééquilibrer
            recommendation: Plan de rééquilibrage
            
        Returns:
            Dict: Résultat de l'exécution
        """
        logger.info(f"Exécution rééquilibrage pour portefeuille {portfolio.id}")
        
        try:
            executed_actions = []
            failed_actions = []
            total_cost = Decimal("0")
            
            # Exécuter les actions dans l'ordre optimal
            execution_order = recommendation.execution_order
            
            for action in execution_order:
                try:
                    # Simuler l'exécution (en production: intégration avec broker)
                    result = await self._simulate_trade_execution(action)
                    
                    if result['success']:
                        executed_actions.append({
                            'action': action,
                            'result': result
                        })
                        total_cost += Decimal(str(result.get('cost', 0)))
                    else:
                        failed_actions.append({
                            'action': action,
                            'error': result.get('error', 'Unknown error')
                        })
                        
                except Exception as e:
                    logger.error(f"Erreur exécution action {action}: {e}")
                    failed_actions.append({
                        'action': action,
                        'error': str(e)
                    })
            
            # Mettre à jour la date de dernier rééquilibrage
            portfolio.last_rebalance = datetime.now()
            
            execution_result = {
                'success': len(failed_actions) == 0,
                'executed_count': len(executed_actions),
                'failed_count': len(failed_actions),
                'total_cost': total_cost,
                'executed_actions': executed_actions,
                'failed_actions': failed_actions,
                'execution_time': datetime.now()
            }
            
            logger.info(f"Rééquilibrage terminé: {len(executed_actions)} succès, {len(failed_actions)} échecs")
            return execution_result
            
        except Exception as e:
            logger.error(f"Erreur exécution rééquilibrage: {e}")
            return {
                'success': False,
                'error': str(e),
                'execution_time': datetime.now()
            }
    
    async def _simulate_trade_execution(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Simule l'exécution d'un trade."""
        
        try:
            # Récupérer le prix actuel pour vérification
            quote = await self.openbb_provider.get_quote(action['symbol'])
            current_price = quote.get('price', action['current_price'])
            
            # Calculer le slippage (simulation)
            price_diff = abs(current_price - action['current_price']) / action['current_price']
            slippage = min(0.002, price_diff)  # Max 0.2% slippage
            
            # Calculer les coûts
            transaction_value = action['amount']
            transaction_cost = transaction_value * self.transaction_cost_rate
            slippage_cost = transaction_value * slippage
            total_cost = transaction_cost + slippage_cost
            
            # Simulation du succès (95% de réussite)
            import random
            success = random.random() > 0.05
            
            if success:
                return {
                    'success': True,
                    'executed_price': current_price,
                    'executed_quantity': action['quantity'],
                    'cost': total_cost,
                    'slippage': slippage
                }
            else:
                return {
                    'success': False,
                    'error': 'Échec simulation execution'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def set_rebalance_thresholds(self, thresholds: Dict[str, float]):
        """Met à jour les seuils de rééquilibrage."""
        
        self.default_thresholds.update(thresholds)
        logger.info(f"Seuils de rééquilibrage mis à jour: {self.default_thresholds}")
    
    def set_transaction_costs(self, transaction_cost_rate: float, tax_rate: float):
        """Met à jour les coûts de transaction."""
        
        self.transaction_cost_rate = transaction_cost_rate
        self.tax_rate = tax_rate
        logger.info(f"Coûts mis à jour: transaction {transaction_cost_rate:.3%}, taxe {tax_rate:.1%}")