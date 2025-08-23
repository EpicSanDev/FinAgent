"""
Moteur de décision principal - Orchestration de la prise de décision de trading.
"""

import asyncio
import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Any
from uuid import UUID

from finagent.ai.services.analysis_service import AnalysisService
from finagent.ai.services.decision_service import DecisionService
from finagent.business.models.decision_models import (
    DecisionContext,
    DecisionResult,
    DecisionAction,
    ConfidenceLevel,
    SignalAggregation,
    MarketAnalysis,
    RiskAssessment
)
from finagent.business.models.portfolio_models import Portfolio, Position
from finagent.business.strategy.manager.strategy_manager import StrategyManager
from finagent.data.providers.openbb_provider import OpenBBProvider
from finagent.infrastructure.config import settings

logger = logging.getLogger(__name__)


class DecisionEngine:
    """
    Moteur de décision principal pour le trading automatisé.
    
    Ce composant orchestre :
    - L'analyse de marché via OpenBB
    - L'analyse IA via Claude
    - L'évaluation des stratégies utilisateur
    - L'agrégation des signaux
    - La prise de décision finale
    """
    
    def __init__(
        self,
        analysis_service: AnalysisService,
        decision_service: DecisionService,
        strategy_manager: StrategyManager,
        openbb_provider: OpenBBProvider,
        market_analyzer: Optional['MarketAnalyzer'] = None,
        signal_aggregator: Optional['SignalAggregator'] = None,
        risk_evaluator: Optional['RiskEvaluator'] = None
    ):
        """
        Initialise le moteur de décision.
        
        Args:
            analysis_service: Service d'analyse financière IA
            decision_service: Service de décision trading IA
            strategy_manager: Gestionnaire de stratégies utilisateur
            openbb_provider: Provider de données financières
            market_analyzer: Analyseur de marché (optionnel)
            signal_aggregator: Agrégateur de signaux (optionnel)
            risk_evaluator: Évaluateur de risque (optionnel)
        """
        self.analysis_service = analysis_service
        self.decision_service = decision_service
        self.strategy_manager = strategy_manager
        self.openbb_provider = openbb_provider
        
        # Composants optionnels (injection de dépendance)
        self.market_analyzer = market_analyzer
        self.signal_aggregator = signal_aggregator
        self.risk_evaluator = risk_evaluator
        
        # Configuration
        self.max_concurrent_analyses = settings.ai.max_concurrent_requests or 3
        self.decision_timeout = 30  # secondes
        
        logger.info("Moteur de décision initialisé")
    
    async def make_decision(
        self,
        symbol: str,
        portfolio: Portfolio,
        context: Optional[Dict[str, Any]] = None
    ) -> DecisionResult:
        """
        Prend une décision de trading pour un symbole donné.
        
        Args:
            symbol: Symbole du titre à analyser
            portfolio: Portefeuille actuel
            context: Contexte additionnel pour la décision
            
        Returns:
            DecisionResult: Décision de trading complète
        """
        logger.info(f"Démarrage de la prise de décision pour {symbol}")
        
        try:
            # 1. Construire le contexte de décision
            decision_context = await self._build_decision_context(
                symbol, portfolio, context
            )
            
            # 2. Collecter toutes les analyses en parallèle
            analysis_tasks = [
                self._get_market_data(symbol),
                self._analyze_market_conditions(symbol, decision_context),
                self._evaluate_strategies(symbol, decision_context),
                self._assess_risks(symbol, decision_context)
            ]
            
            market_data, market_analysis, strategy_signals, risk_assessment = \
                await asyncio.gather(*analysis_tasks, return_exceptions=True)
            
            # 3. Vérifier les erreurs
            if isinstance(market_data, Exception):
                logger.error(f"Erreur récupération données marché: {market_data}")
                market_data = None
            
            if isinstance(market_analysis, Exception):
                logger.error(f"Erreur analyse marché: {market_analysis}")
                market_analysis = None
                
            if isinstance(strategy_signals, Exception):
                logger.error(f"Erreur évaluation stratégies: {strategy_signals}")
                strategy_signals = []
                
            if isinstance(risk_assessment, Exception):
                logger.error(f"Erreur évaluation risques: {risk_assessment}")
                risk_assessment = None
            
            # 4. Mettre à jour le contexte avec les données collectées
            decision_context = await self._update_context_with_analysis(
                decision_context, market_data, market_analysis, risk_assessment
            )
            
            # 5. Agréger les signaux
            signal_aggregation = await self._aggregate_signals(
                symbol, strategy_signals, market_analysis, risk_assessment
            )
            
            # 6. Prendre la décision finale via l'IA
            final_decision = await self._make_final_decision(
                symbol, decision_context, signal_aggregation
            )
            
            # 7. Valider et ajuster la décision
            validated_decision = await self._validate_and_adjust_decision(
                final_decision, decision_context, portfolio
            )
            
            logger.info(f"Décision prise pour {symbol}: {validated_decision.action}")
            return validated_decision
            
        except Exception as e:
            logger.error(f"Erreur lors de la prise de décision pour {symbol}: {e}")
            
            # Décision de fallback en cas d'erreur
            return DecisionResult(
                symbol=symbol,
                action=DecisionAction.HOLD,
                confidence=ConfidenceLevel.VERY_LOW,
                confidence_score=0.1,
                primary_reason=f"Erreur lors de l'analyse: {str(e)}",
                risk_score=1.0,
                market_conditions="Indéterminé"
            )
    
    async def make_batch_decisions(
        self,
        symbols: List[str],
        portfolio: Portfolio,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, DecisionResult]:
        """
        Prend des décisions pour plusieurs symboles en parallèle.
        
        Args:
            symbols: Liste des symboles à analyser
            portfolio: Portefeuille actuel
            context: Contexte additionnel
            
        Returns:
            Dict[str, DecisionResult]: Décisions par symbole
        """
        logger.info(f"Prise de décisions par lot pour {len(symbols)} symboles")
        
        # Limiter la concurrence
        semaphore = asyncio.Semaphore(self.max_concurrent_analyses)
        
        async def make_single_decision(symbol: str) -> tuple[str, DecisionResult]:
            async with semaphore:
                decision = await self.make_decision(symbol, portfolio, context)
                return symbol, decision
        
        # Exécuter toutes les décisions en parallèle
        tasks = [make_single_decision(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Traiter les résultats
        decisions = {}
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Erreur dans la prise de décision par lot: {result}")
                continue
            
            symbol, decision = result
            decisions[symbol] = decision
        
        logger.info(f"Décisions par lot terminées: {len(decisions)} succès")
        return decisions
    
    async def _build_decision_context(
        self,
        symbol: str,
        portfolio: Portfolio,
        context: Optional[Dict[str, Any]] = None
    ) -> DecisionContext:
        """Construit le contexte de décision initial."""
        
        # Récupérer les données de prix de base
        try:
            price_data = await self.openbb_provider.get_quote(symbol)
            current_price = Decimal(str(price_data.get('price', 0)))
            previous_close = Decimal(str(price_data.get('previous_close', current_price)))
            day_high = Decimal(str(price_data.get('day_high', current_price)))
            day_low = Decimal(str(price_data.get('day_low', current_price)))
            volume = Decimal(str(price_data.get('volume', 0)))
        except Exception as e:
            logger.warning(f"Erreur récupération prix pour {symbol}: {e}")
            current_price = Decimal("0")
            previous_close = Decimal("0")
            day_high = Decimal("0")
            day_low = Decimal("0")
            volume = Decimal("0")
        
        # Récupérer la position actuelle
        current_position = None
        position_weight = 0.0
        if symbol in portfolio.positions:
            pos = portfolio.positions[symbol]
            current_position = pos.quantity
            position_weight = pos.weight
        
        # Stratégies actives
        active_strategies = await self.strategy_manager.get_active_strategy_names()
        
        return DecisionContext(
            symbol=symbol,
            current_price=current_price,
            previous_close=previous_close,
            day_high=day_high,
            day_low=day_low,
            volume=volume,
            current_position=current_position,
            available_cash=portfolio.available_cash,
            portfolio_value=portfolio.total_value,
            position_weight=position_weight,
            active_strategies=active_strategies,
            strategy_context=context or {}
        )
    
    async def _get_market_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Récupère les données de marché complètes."""
        try:
            # Données de base
            quote = await self.openbb_provider.get_quote(symbol)
            
            # Données historiques pour l'analyse technique
            historical = await self.openbb_provider.get_historical_data(
                symbol, period="1y", interval="1d"
            )
            
            # Informations fondamentales
            company_info = await self.openbb_provider.get_company_info(symbol)
            
            return {
                'quote': quote,
                'historical': historical,
                'company_info': company_info
            }
        except Exception as e:
            logger.error(f"Erreur récupération données marché pour {symbol}: {e}")
            return None
    
    async def _analyze_market_conditions(
        self, 
        symbol: str, 
        context: DecisionContext
    ) -> Optional[MarketAnalysis]:
        """Analyse les conditions de marché via l'IA."""
        try:
            if self.market_analyzer:
                return await self.market_analyzer.analyze_market(symbol, context)
            
            # Fallback avec le service d'analyse
            analysis = await self.analysis_service.analyze_market_conditions(
                symbol=symbol,
                timeframe="1D",
                context={
                    'current_price': float(context.current_price),
                    'volume': float(context.volume),
                    'portfolio_weight': context.position_weight
                }
            )
            
            # Convertir en MarketAnalysis
            return MarketAnalysis(
                symbol=symbol,
                technical_indicators=analysis.technical_indicators,
                trend_direction=analysis.trend_analysis.get('direction', 'neutral'),
                volatility=analysis.volatility_metrics.get('current', 0.0),
                sentiment_score=analysis.sentiment_analysis.get('overall_score', 0.0),
                avg_volume=context.volume,
                volume_trend=analysis.volume_analysis.get('trend', 'stable'),
                liquidity_score=0.8  # Valeur par défaut
            )
            
        except Exception as e:
            logger.error(f"Erreur analyse conditions marché pour {symbol}: {e}")
            return None
    
    async def _evaluate_strategies(
        self, 
        symbol: str, 
        context: DecisionContext
    ) -> List[Any]:
        """Évalue les stratégies utilisateur pour générer des signaux."""
        try:
            signals = []
            
            for strategy_name in context.active_strategies:
                try:
                    # Récupérer la stratégie
                    strategy = await self.strategy_manager.get_strategy(strategy_name)
                    if not strategy:
                        continue
                    
                    # Évaluer la stratégie
                    evaluation = await self.strategy_manager.evaluate_strategy_for_symbol(
                        strategy_name, symbol
                    )
                    
                    if evaluation and evaluation.action != "HOLD":
                        signals.append(evaluation)
                        
                except Exception as e:
                    logger.warning(f"Erreur évaluation stratégie {strategy_name}: {e}")
                    continue
            
            return signals
            
        except Exception as e:
            logger.error(f"Erreur évaluation stratégies pour {symbol}: {e}")
            return []
    
    async def _assess_risks(
        self, 
        symbol: str, 
        context: DecisionContext
    ) -> Optional[RiskAssessment]:
        """Évalue les risques associés au symbole."""
        try:
            if self.risk_evaluator:
                return await self.risk_evaluator.assess_risk(symbol, context)
            
            # Évaluation de base des risques
            return RiskAssessment(
                symbol=symbol,
                sector_risk=0.5,  # Valeur par défaut
                concentration_risk=context.position_weight,
                liquidity_risk=0.3,  # Valeur par défaut
                overall_risk_score=0.5,
                risk_level="Modéré",
                max_position_size=0.1
            )
            
        except Exception as e:
            logger.error(f"Erreur évaluation risques pour {symbol}: {e}")
            return None
    
    async def _update_context_with_analysis(
        self,
        context: DecisionContext,
        market_data: Optional[Dict[str, Any]],
        market_analysis: Optional[MarketAnalysis],
        risk_assessment: Optional[RiskAssessment]
    ) -> DecisionContext:
        """Met à jour le contexte avec les analyses effectuées."""
        
        # Mettre à jour les contraintes de risque
        if risk_assessment:
            context.max_position_size = risk_assessment.max_position_size
            
        # Ajouter les analyses au contexte
        context.market_analysis = market_analysis
        context.risk_assessment = risk_assessment
        
        # Ajouter les données de marché au contexte stratégique
        if market_data:
            context.strategy_context.update({
                'market_data': market_data,
                'has_market_analysis': market_analysis is not None,
                'has_risk_assessment': risk_assessment is not None
            })
        
        return context
    
    async def _aggregate_signals(
        self,
        symbol: str,
        strategy_signals: List[Any],
        market_analysis: Optional[MarketAnalysis],
        risk_assessment: Optional[RiskAssessment]
    ) -> Optional[SignalAggregation]:
        """Agrège tous les signaux disponibles."""
        try:
            if self.signal_aggregator:
                return await self.signal_aggregator.aggregate_signals(
                    symbol, strategy_signals, market_analysis, risk_assessment
                )
            
            # Agrégation simple par défaut
            if not strategy_signals:
                return None
            
            # Compter les signaux
            buy_count = sum(1 for s in strategy_signals if s.action == "BUY")
            sell_count = sum(1 for s in strategy_signals if s.action == "SELL")
            hold_count = len(strategy_signals) - buy_count - sell_count
            
            # Déterminer l'action agrégée
            if buy_count > sell_count:
                aggregated_action = DecisionAction.BUY
                confidence = buy_count / len(strategy_signals)
            elif sell_count > buy_count:
                aggregated_action = DecisionAction.SELL
                confidence = sell_count / len(strategy_signals)
            else:
                aggregated_action = DecisionAction.HOLD
                confidence = 0.5
            
            return SignalAggregation(
                symbol=symbol,
                signals=[],  # Conversion nécessaire
                aggregated_action=aggregated_action,
                aggregated_confidence=confidence,
                consensus_strength=confidence,
                buy_signals=buy_count,
                sell_signals=sell_count,
                hold_signals=hold_count,
                weighted_score=confidence
            )
            
        except Exception as e:
            logger.error(f"Erreur agrégation signaux pour {symbol}: {e}")
            return None
    
    async def _make_final_decision(
        self,
        symbol: str,
        context: DecisionContext,
        signal_aggregation: Optional[SignalAggregation]
    ) -> DecisionResult:
        """Prend la décision finale via l'IA."""
        try:
            # Préparer le contexte pour l'IA
            decision_context = {
                'symbol': symbol,
                'current_price': float(context.current_price),
                'position_weight': context.position_weight,
                'available_cash': float(context.available_cash),
                'portfolio_value': float(context.portfolio_value),
                'market_analysis': context.market_analysis.dict() if context.market_analysis else None,
                'risk_assessment': context.risk_assessment.dict() if context.risk_assessment else None,
                'signal_aggregation': signal_aggregation.dict() if signal_aggregation else None
            }
            
            # Utiliser le service de décision IA
            ai_decision = await self.decision_service.make_trading_decision(
                symbol=symbol,
                current_price=float(context.current_price),
                position_size=context.position_weight,
                portfolio_context=decision_context
            )
            
            # Convertir en DecisionResult
            return DecisionResult(
                symbol=symbol,
                action=DecisionAction(ai_decision.action.lower()),
                confidence=ConfidenceLevel.MEDIUM,  # À mapper selon le score
                confidence_score=ai_decision.confidence,
                primary_reason=ai_decision.reasoning,
                supporting_factors=ai_decision.supporting_factors,
                risk_factors=ai_decision.risk_factors,
                expected_return=ai_decision.expected_return,
                risk_score=ai_decision.risk_assessment.overall_score,
                quantity=Decimal(str(ai_decision.position_size)) if ai_decision.position_size else None,
                price_target=Decimal(str(ai_decision.target_price)) if ai_decision.target_price else None,
                stop_loss=Decimal(str(ai_decision.stop_loss)) if ai_decision.stop_loss else None,
                market_conditions=decision_context.get('market_conditions', 'Normal')
            )
            
        except Exception as e:
            logger.error(f"Erreur décision finale IA pour {symbol}: {e}")
            
            # Décision de fallback
            return DecisionResult(
                symbol=symbol,
                action=DecisionAction.HOLD,
                confidence=ConfidenceLevel.LOW,
                confidence_score=0.3,
                primary_reason="Décision par défaut due à une erreur",
                risk_score=0.8,
                market_conditions="Indéterminé"
            )
    
    async def _validate_and_adjust_decision(
        self,
        decision: DecisionResult,
        context: DecisionContext,
        portfolio: Portfolio
    ) -> DecisionResult:
        """Valide et ajuste la décision selon les contraintes."""
        try:
            # Vérifier les contraintes de position
            if decision.action == DecisionAction.BUY and decision.quantity:
                # Calculer la nouvelle allocation
                trade_value = decision.quantity * context.current_price
                new_weight = (context.position_weight * portfolio.total_value + trade_value) / portfolio.total_value
                
                # Limiter selon la taille max de position
                max_weight = context.max_position_size
                if new_weight > max_weight:
                    # Ajuster la quantité
                    max_trade_value = (max_weight * portfolio.total_value) - (context.position_weight * portfolio.total_value)
                    if max_trade_value > 0:
                        decision.quantity = max_trade_value / context.current_price
                    else:
                        decision.action = DecisionAction.HOLD
                        decision.quantity = None
                        decision.primary_reason += " - Limite de position atteinte"
                
                # Vérifier le cash disponible
                required_cash = decision.quantity * context.current_price if decision.quantity else Decimal("0")
                if required_cash > context.available_cash:
                    if context.available_cash > context.min_trade_amount:
                        decision.quantity = context.available_cash / context.current_price
                    else:
                        decision.action = DecisionAction.HOLD
                        decision.quantity = None
                        decision.primary_reason += " - Cash insuffisant"
            
            # Vérifier la taille minimale de trade
            if decision.quantity and decision.quantity * context.current_price < context.min_trade_amount:
                decision.action = DecisionAction.HOLD
                decision.quantity = None
                decision.primary_reason += " - Montant de trade trop faible"
            
            # Ajuster le niveau de confiance si modifié
            if decision.action == DecisionAction.HOLD and "limite" in decision.primary_reason.lower():
                decision.confidence_score = min(decision.confidence_score, 0.6)
                decision.confidence = ConfidenceLevel.MEDIUM
            
            return decision
            
        except Exception as e:
            logger.error(f"Erreur validation décision pour {decision.symbol}: {e}")
            return decision