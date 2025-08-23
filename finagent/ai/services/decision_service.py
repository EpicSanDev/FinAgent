"""
Service de prise de décision de trading par IA.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional
from decimal import Decimal

import structlog

from ..models import (
    AIRequest,
    AIResponse,
    AIProvider,
    ModelType,
    DecisionRequest,
    TradingDecision,
    DecisionType,
    OrderType,
    TimeInForce,
    ConfidenceLevel,
    RiskLevel,
    TradingContext,
    RiskParameters,
    AnalysisResult,
    PortfolioImpact,
    DecisionHistory,
    AIError,
)
from ..prompts import (
    PromptManager,
    PromptContext,
    PromptType,
)

logger = structlog.get_logger(__name__)


class DecisionService:
    """Service de prise de décision de trading utilisant l'IA."""
    
    def __init__(
        self,
        ai_provider: AIProvider,
        prompt_manager: PromptManager,
        default_model: ModelType = ModelType.CLAUDE_3_5_SONNET
    ):
        self.ai_provider = ai_provider
        self.prompt_manager = prompt_manager
        self.default_model = default_model
        
        self.logger = logger.bind(service="decision")
    
    async def make_trading_decision(self, request: DecisionRequest) -> TradingDecision:
        """Prend une décision de trading basée sur l'analyse."""
        
        symbol = request.trading_context.symbol
        current_price = request.trading_context.current_price
        
        self.logger.info(
            "Prise de décision trading",
            symbol=symbol,
            current_price=float(current_price),
            trend=request.analysis_result.overall_trend.value,
            request_id=str(request.request_id)
        )
        
        try:
            # Pré-analyse pour déterminer le type de décision probable
            likely_decision = self._predict_decision_type(request)
            
            # Sélection du modèle et du prompt approprié
            model = self._select_decision_model(likely_decision, request.aggressive_mode)
            prompt_type = self._get_decision_prompt_type(likely_decision)
            
            # Génération du prompt contextualisé
            prompt_context = self._create_decision_prompt_context(request)
            prompt = self.prompt_manager.generate_prompt(prompt_type, prompt_context)
            
            # Requête à l'IA
            ai_request = AIRequest(
                model_type=model,
                prompt=prompt,
                context=self._create_decision_ai_context(request),
                temperature=0.2,  # Très faible pour décisions critiques
                max_tokens=3000
            )
            
            ai_response = await self.ai_provider.send_request(ai_request)
            
            # Parsing et structuration de la décision
            decision = await self._parse_decision_response(
                request,
                ai_response,
                model
            )
            
            # Validation et ajustements de sécurité
            decision = await self._validate_and_adjust_decision(decision, request)
            
            self.logger.info(
                "Décision prise",
                symbol=symbol,
                action=decision.action.value,
                confidence=decision.confidence.value,
                quantity=float(decision.recommended_quantity) if decision.recommended_quantity else None,
                tokens_used=ai_response.tokens_used
            )
            
            return decision
            
        except Exception as e:
            self.logger.error(
                "Erreur prise de décision",
                symbol=symbol,
                error=str(e),
                request_id=str(request.request_id)
            )
            raise AIError(f"Erreur lors de la prise de décision: {str(e)}")
    
    async def evaluate_buy_opportunity(
        self,
        trading_context: TradingContext,
        analysis_result: AnalysisResult,
        risk_parameters: RiskParameters,
        strategy_context: Optional[str] = None
    ) -> TradingDecision:
        """Évalue spécifiquement une opportunité d'achat."""
        
        request = DecisionRequest(
            trading_context=trading_context,
            analysis_result=analysis_result,
            risk_parameters=risk_parameters,
            strategy_name=strategy_context
        )
        
        # Force l'évaluation d'achat
        prompt_context = self._create_decision_prompt_context(request)
        prompt = self.prompt_manager.generate_prompt(PromptType.BUY_DECISION, prompt_context)
        
        ai_request = AIRequest(
            model_type=ModelType.CLAUDE_3_5_SONNET,
            prompt=prompt,
            temperature=0.2,
            max_tokens=3000
        )
        
        ai_response = await self.ai_provider.send_request(ai_request)
        
        return await self._parse_decision_response(request, ai_response, ModelType.CLAUDE_3_5_SONNET)
    
    async def evaluate_sell_opportunity(
        self,
        trading_context: TradingContext,
        analysis_result: AnalysisResult,
        risk_parameters: RiskParameters,
        hold_period_days: Optional[int] = None
    ) -> TradingDecision:
        """Évalue spécifiquement une opportunité de vente."""
        
        request = DecisionRequest(
            trading_context=trading_context,
            analysis_result=analysis_result,
            risk_parameters=risk_parameters,
            custom_notes=f"Période de détention: {hold_period_days} jours" if hold_period_days else None
        )
        
        # Ajoute la période de détention au contexte
        prompt_context = self._create_decision_prompt_context(request)
        if hold_period_days:
            prompt_context.custom_context["hold_period_days"] = hold_period_days
        
        prompt = self.prompt_manager.generate_prompt(PromptType.SELL_DECISION, prompt_context)
        
        ai_request = AIRequest(
            model_type=ModelType.CLAUDE_3_5_SONNET,
            prompt=prompt,
            temperature=0.2,
            max_tokens=3000
        )
        
        ai_response = await self.ai_provider.send_request(ai_request)
        
        return await self._parse_decision_response(request, ai_response, ModelType.CLAUDE_3_5_SONNET)
    
    async def evaluate_hold_decision(
        self,
        trading_context: TradingContext,
        analysis_result: AnalysisResult,
        market_conditions: Optional[str] = None
    ) -> TradingDecision:
        """Évalue la décision de conserver une position."""
        
        # Utilise des paramètres de risque par défaut pour l'évaluation
        risk_parameters = RiskParameters()
        
        request = DecisionRequest(
            trading_context=trading_context,
            analysis_result=analysis_result,
            risk_parameters=risk_parameters,
            market_conditions=market_conditions
        )
        
        prompt_context = self._create_decision_prompt_context(request)
        prompt = self.prompt_manager.generate_prompt(PromptType.HOLD_DECISION, prompt_context)
        
        ai_request = AIRequest(
            model_type=ModelType.CLAUDE_3_SONNET,  # Sonnet suffisant pour hold
            prompt=prompt,
            temperature=0.3,
            max_tokens=2000
        )
        
        ai_response = await self.ai_provider.send_request(ai_request)
        
        return await self._parse_decision_response(request, ai_response, ModelType.CLAUDE_3_SONNET)
    
    async def calculate_position_size(
        self,
        decision: TradingDecision,
        trading_context: TradingContext,
        risk_parameters: RiskParameters
    ) -> Decimal:
        """Calcule la taille de position optimale."""
        
        if decision.action in [DecisionType.HOLD]:
            return Decimal('0')
        
        current_price = trading_context.current_price
        available_cash = trading_context.available_cash
        portfolio_value = trading_context.portfolio_value
        
        # Méthode de sizing selon les paramètres
        if risk_parameters.position_sizing_method.value == "fixed_amount":
            # Montant fixe défini par l'utilisateur
            target_amount = min(available_cash, Decimal('10000'))  # Default 10k max
            return target_amount / current_price
        
        elif risk_parameters.position_sizing_method.value == "percentage_of_portfolio":
            # Pourcentage du portefeuille
            target_allocation = min(risk_parameters.max_position_weight, 0.1)  # Max 10%
            target_amount = portfolio_value * Decimal(str(target_allocation))
            target_amount = min(target_amount, available_cash)
            return target_amount / current_price
        
        elif risk_parameters.position_sizing_method.value == "risk_based":
            # Basé sur le risque par trade
            if not decision.stop_loss_price:
                # Utilise un stop loss par défaut à 5%
                stop_loss_price = current_price * Decimal('0.95')
            else:
                stop_loss_price = decision.stop_loss_price
            
            risk_per_share = current_price - stop_loss_price
            if risk_per_share <= 0:
                return Decimal('0')
            
            max_loss = portfolio_value * Decimal(str(risk_parameters.risk_per_trade))
            max_shares = max_loss / risk_per_share
            
            # Limite par la liquidité disponible
            max_shares_by_cash = available_cash / current_price
            return min(max_shares, max_shares_by_cash)
        
        else:
            # Par défaut: 5% du portefeuille
            target_amount = portfolio_value * Decimal('0.05')
            target_amount = min(target_amount, available_cash)
            return target_amount / current_price
    
    async def assess_portfolio_impact(
        self,
        decision: TradingDecision,
        trading_context: TradingContext,
        current_positions: List[Dict[str, Any]]
    ) -> PortfolioImpact:
        """Évalue l'impact d'une décision sur le portefeuille."""
        
        symbol = decision.symbol
        current_price = trading_context.current_price
        quantity = decision.recommended_quantity or Decimal('0')
        
        # Calcule les nouvelles positions
        if decision.action in [DecisionType.BUY, DecisionType.STRONG_BUY]:
            trade_value = quantity * current_price
            new_cash = trading_context.available_cash - trade_value
            new_position_value = (trading_context.current_position or Decimal('0') + quantity) * current_price
        elif decision.action in [DecisionType.SELL, DecisionType.STRONG_SELL]:
            trade_value = quantity * current_price
            new_cash = trading_context.available_cash + trade_value
            new_position_value = max(Decimal('0'), (trading_context.current_position or Decimal('0') - quantity)) * current_price
        else:  # HOLD
            new_cash = trading_context.available_cash
            new_position_value = (trading_context.current_position or Decimal('0')) * current_price
        
        new_total_value = new_cash + new_position_value
        
        # Calcule la concentration de risque
        position_weight = float(new_position_value / new_total_value) if new_total_value > 0 else 0
        concentration_risk = position_weight if position_weight > 0.1 else 0  # Risque si >10%
        
        # Alertes de risque
        risk_warnings = []
        if concentration_risk > 0.2:
            risk_warnings.append(f"Concentration excessive sur {symbol}: {concentration_risk:.1%}")
        if new_cash < 0:
            risk_warnings.append("Liquidités insuffisantes")
        if position_weight > 0.15:
            risk_warnings.append(f"Position importante: {position_weight:.1%} du portefeuille")
        
        return PortfolioImpact(
            decision_id=decision.decision_id,
            new_cash_position=new_cash,
            new_position_value=new_position_value,
            new_total_value=new_total_value,
            concentration_risk=concentration_risk,
            risk_warnings=risk_warnings
        )
    
    def _predict_decision_type(self, request: DecisionRequest) -> DecisionType:
        """Prédit le type de décision probable basé sur l'analyse."""
        
        analysis = request.analysis_result
        context = request.trading_context
        
        # Si pas de position, ne peut que acheter ou rester en attente
        if not context.current_position or context.current_position == 0:
            if analysis.overall_trend.value in ["strong_bullish", "bullish"] and analysis.confidence.value in ["high", "very_high"]:
                return DecisionType.BUY
            else:
                return DecisionType.HOLD
        
        # Si position existante, peut acheter plus, vendre ou conserver
        if analysis.overall_trend.value == "strong_bearish":
            return DecisionType.SELL
        elif analysis.overall_trend.value == "bearish":
            return DecisionType.SELL
        elif analysis.overall_trend.value == "strong_bullish":
            return DecisionType.BUY
        elif analysis.overall_trend.value == "bullish":
            return DecisionType.BUY
        else:
            return DecisionType.HOLD
    
    def _select_decision_model(self, decision_type: DecisionType, aggressive_mode: bool) -> ModelType:
        """Sélectionne le modèle selon le type de décision."""
        
        # Pour les décisions critiques (achat/vente), utilise les meilleurs modèles
        if decision_type in [DecisionType.BUY, DecisionType.SELL, DecisionType.STRONG_BUY, DecisionType.STRONG_SELL]:
            return ModelType.CLAUDE_3_5_SONNET if aggressive_mode else ModelType.CLAUDE_3_SONNET
        else:
            return ModelType.CLAUDE_3_SONNET  # Sonnet suffisant pour HOLD
    
    def _get_decision_prompt_type(self, decision_type: DecisionType) -> PromptType:
        """Détermine le type de prompt selon la décision."""
        
        if decision_type in [DecisionType.BUY, DecisionType.STRONG_BUY]:
            return PromptType.BUY_DECISION
        elif decision_type in [DecisionType.SELL, DecisionType.STRONG_SELL]:
            return PromptType.SELL_DECISION
        else:
            return PromptType.HOLD_DECISION
    
    def _create_decision_prompt_context(self, request: DecisionRequest) -> PromptContext:
        """Crée le contexte pour les prompts de décision."""
        
        return PromptContext(
            trading_context=request.trading_context,
            analysis_result=request.analysis_result,
            risk_parameters=request.risk_parameters,
            strategy_name=request.strategy_name,
            time_horizon=request.time_horizon,
            aggressive_mode=request.aggressive_mode,
            market_conditions=request.market_conditions,
            custom_context={
                "news_embargo": request.news_embargo,
                "earnings_period": request.earnings_period,
                "custom_notes": request.custom_notes,
                "override_rules": request.override_rules,
            }
        )
    
    def _create_decision_ai_context(self, request: DecisionRequest) -> Dict[str, Any]:
        """Crée le contexte pour la requête IA."""
        
        return {
            "decision_type": "trading",
            "symbol": request.trading_context.symbol,
            "strategy": request.strategy_name,
            "time_horizon": request.time_horizon,
            "aggressive_mode": request.aggressive_mode,
            "market_conditions": request.market_conditions,
        }
    
    async def _parse_decision_response(
        self,
        request: DecisionRequest,
        ai_response: AIResponse,
        model_used: ModelType
    ) -> TradingDecision:
        """Parse et structure la réponse de décision."""
        
        content = ai_response.content
        context = request.trading_context
        
        # Extraction des informations de la réponse
        action = self._extract_decision_action(content)
        confidence = self._extract_confidence_level(content)
        urgency = self._extract_urgency(content)
        
        # Extraction des paramètres d'exécution
        order_type = self._extract_order_type(content)
        time_in_force = self._extract_time_in_force(content)
        
        # Extraction des quantités et prix
        recommended_quantity = self._extract_quantity(content, context)
        limit_price = self._extract_limit_price(content, context.current_price)
        
        # Extraction de la gestion du risque
        stop_loss_price = self._extract_stop_loss(content, context.current_price)
        take_profit_price = self._extract_take_profit(content, context.current_price)
        
        # Extraction des justifications
        reasoning = self._extract_reasoning(content)
        key_factors = self._extract_key_factors(content)
        risk_assessment = self._extract_risk_assessment(content)
        
        # Extraction des scores
        technical_score = self._extract_score_from_content(content, "technique")
        fundamental_score = self._extract_score_from_content(content, "fondamental")
        sentiment_score = self._extract_sentiment_score(content)
        
        # Extraction du ratio risque/récompense
        risk_reward_ratio = self._extract_risk_reward_ratio(content)
        expected_return = self._extract_expected_return(content)
        
        return TradingDecision(
            request_id=request.request_id,
            symbol=context.symbol,
            action=action,
            confidence=confidence,
            urgency=urgency,
            order_type=order_type,
            time_in_force=time_in_force,
            recommended_quantity=recommended_quantity,
            limit_price=limit_price,
            stop_loss_price=stop_loss_price,
            take_profit_price=take_profit_price,
            reasoning=reasoning,
            key_factors=key_factors,
            risk_assessment=risk_assessment,
            expected_return=expected_return,
            risk_reward_ratio=risk_reward_ratio,
            technical_score=technical_score,
            fundamental_score=fundamental_score,
            sentiment_score=sentiment_score,
            risk_score=request.analysis_result.risk_level,
            model_used=model_used.value,
            processing_time=ai_response.processing_time,
            tokens_used=ai_response.tokens_used
        )
    
    async def _validate_and_adjust_decision(
        self,
        decision: TradingDecision,
        request: DecisionRequest
    ) -> TradingDecision:
        """Valide et ajuste la décision pour la sécurité."""
        
        context = request.trading_context
        risk_params = request.risk_parameters
        
        # Validation de la quantité
        if decision.recommended_quantity:
            # Limite par la liquidité disponible
            if decision.action in [DecisionType.BUY, DecisionType.STRONG_BUY]:
                max_affordable = context.available_cash / context.current_price
                decision.recommended_quantity = min(decision.recommended_quantity, max_affordable)
            
            # Limite par la position existante pour les ventes
            elif decision.action in [DecisionType.SELL, DecisionType.STRONG_SELL]:
                current_position = context.current_position or Decimal('0')
                decision.recommended_quantity = min(decision.recommended_quantity, current_position)
            
            # Assure une quantité minimum
            if decision.recommended_quantity < Decimal('1'):
                decision.recommended_quantity = Decimal('0')
                decision.action = DecisionType.HOLD
        
        # Validation du stop loss (pas trop proche du prix actuel)
        if decision.stop_loss_price:
            min_stop_distance = context.current_price * Decimal('0.02')  # 2% minimum
            if decision.action in [DecisionType.BUY, DecisionType.STRONG_BUY]:
                if decision.stop_loss_price > context.current_price - min_stop_distance:
                    decision.stop_loss_price = context.current_price - min_stop_distance
            elif decision.action in [DecisionType.SELL, DecisionType.STRONG_SELL]:
                if decision.stop_loss_price < context.current_price + min_stop_distance:
                    decision.stop_loss_price = context.current_price + min_stop_distance
        
        # Validation du take profit
        if decision.take_profit_price:
            min_profit_distance = context.current_price * Decimal('0.05')  # 5% minimum
            if decision.action in [DecisionType.BUY, DecisionType.STRONG_BUY]:
                if decision.take_profit_price < context.current_price + min_profit_distance:
                    decision.take_profit_price = context.current_price + min_profit_distance
        
        # Ajustement si confiance trop faible
        if decision.confidence in [ConfidenceLevel.VERY_LOW, ConfidenceLevel.LOW]:
            if decision.action in [DecisionType.STRONG_BUY, DecisionType.STRONG_SELL]:
                # Downgrade vers action normale
                decision.action = DecisionType.BUY if decision.action == DecisionType.STRONG_BUY else DecisionType.SELL
            
            # Réduit la taille de position
            if decision.recommended_quantity:
                decision.recommended_quantity *= Decimal('0.5')
        
        return decision
    
    # Méthodes d'extraction simplifiées (en pratique, utiliser des techniques NLP plus sophistiquées)
    
    def _extract_decision_action(self, content: str) -> DecisionType:
        """Extrait l'action de trading du contenu."""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ["strong buy", "achat fort", "fortement acheter"]):
            return DecisionType.STRONG_BUY
        elif any(word in content_lower for word in ["buy", "acheter", "achat"]):
            return DecisionType.BUY
        elif any(word in content_lower for word in ["strong sell", "vente forte", "fortement vendre"]):
            return DecisionType.STRONG_SELL
        elif any(word in content_lower for word in ["sell", "vendre", "vente"]):
            return DecisionType.SELL
        else:
            return DecisionType.HOLD
    
    def _extract_confidence_level(self, content: str) -> ConfidenceLevel:
        """Extrait le niveau de confiance."""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ["très élevé", "very high", "très haute"]):
            return ConfidenceLevel.VERY_HIGH
        elif any(word in content_lower for word in ["élevé", "high", "haute"]):
            return ConfidenceLevel.HIGH
        elif any(word in content_lower for word in ["faible", "low", "basse"]):
            return ConfidenceLevel.LOW
        elif any(word in content_lower for word in ["très faible", "very low"]):
            return ConfidenceLevel.VERY_LOW
        else:
            return ConfidenceLevel.MEDIUM
    
    def _extract_urgency(self, content: str) -> str:
        """Extrait le niveau d'urgence."""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ["immédiat", "immediate", "urgent"]):
            return "immediate"
        elif any(word in content_lower for word in ["élevé", "high"]):
            return "high"
        elif any(word in content_lower for word in ["faible", "low"]):
            return "low"
        else:
            return "normal"
    
    def _extract_order_type(self, content: str) -> OrderType:
        """Extrait le type d'ordre."""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ["limit", "limite"]):
            return OrderType.LIMIT
        elif any(word in content_lower for word in ["stop", "stop loss"]):
            return OrderType.STOP_LOSS
        else:
            return OrderType.MARKET
    
    def _extract_time_in_force(self, content: str) -> TimeInForce:
        """Extrait la durée de validité."""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ["gtc", "good till cancelled"]):
            return TimeInForce.GTC
        elif any(word in content_lower for word in ["ioc", "immediate or cancel"]):
            return TimeInForce.IOC
        else:
            return TimeInForce.DAY
    
    def _extract_quantity(self, content: str, context: TradingContext) -> Optional[Decimal]:
        """Extrait la quantité recommandée."""
        import re
        
        # Cherche des patterns de quantité
        patterns = [
            r"(\d+(?:\.\d+)?)\s*actions?",
            r"(\d+(?:\.\d+)?)\s*shares?",
            r"quantité.*?(\d+(?:\.\d+)?)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content.lower())
            if match:
                try:
                    return Decimal(match.group(1))
                except:
                    continue
        
        return None
    
    def _extract_limit_price(self, content: str, current_price: Decimal) -> Optional[Decimal]:
        """Extrait le prix limite."""
        import re
        
        patterns = [
            rf"limite.*?(\d+(?:\.\d+)?)\$?",
            rf"prix.*?(\d+(?:\.\d+)?)\$?",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content.lower())
            if match:
                try:
                    price = Decimal(match.group(1))
                    # Valide que le prix est raisonnable
                    if current_price * Decimal('0.5') <= price <= current_price * Decimal('1.5'):
                        return price
                except:
                    continue
        
        return None
    
    def _extract_stop_loss(self, content: str, current_price: Decimal) -> Optional[Decimal]:
        """Extrait le stop loss."""
        import re
        
        patterns = [
            rf"stop.*?loss.*?(\d+(?:\.\d+)?)\$?",
            rf"stop.*?(\d+(?:\.\d+)?)\$?",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content.lower())
            if match:
                try:
                    price = Decimal(match.group(1))
                    # Valide que le prix est dans une fourchette raisonnable
                    if current_price * Decimal('0.7') <= price <= current_price * Decimal('1.3'):
                        return price
                except:
                    continue
        
        return None
    
    def _extract_take_profit(self, content: str, current_price: Decimal) -> Optional[Decimal]:
        """Extrait le take profit."""
        import re
        
        patterns = [
            rf"take.*?profit.*?(\d+(?:\.\d+)?)\$?",
            rf"objectif.*?(\d+(?:\.\d+)?)\$?",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content.lower())
            if match:
                try:
                    price = Decimal(match.group(1))
                    if price > current_price:
                        return price
                except:
                    continue
        
        return None
    
    def _extract_reasoning(self, content: str) -> str:
        """Extrait le raisonnement principal."""
        # Cherche la section de justification
        lines = content.split('\n')
        reasoning_lines = []
        
        capture = False
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in ["justification", "raisonnement", "analyse"]):
                capture = True
                continue
            elif capture and line:
                if line.startswith('-') or line.startswith('•'):
                    reasoning_lines.append(line[1:].strip())
                else:
                    reasoning_lines.append(line)
                    
                if len(reasoning_lines) >= 3:  # Limite à 3 lignes principales
                    break
        
        return ". ".join(reasoning_lines) if reasoning_lines else content[:200] + "..."
    
    def _extract_key_factors(self, content: str) -> List[str]:
        """Extrait les facteurs clés."""
        import re
        
        factors = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if (line.startswith('-') or line.startswith('•')) and len(line) > 10:
                factor = line[1:].strip()
                if any(keyword in factor.lower() for keyword in ["facteur", "raison", "signal", "indicateur"]):
                    factors.append(factor)
        
        return factors[:5]  # Max 5 facteurs
    
    def _extract_risk_assessment(self, content: str) -> str:
        """Extrait l'évaluation du risque."""
        lines = content.split('\n')
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ["risque", "risk"]):
                return line.strip()
        
        return "Évaluation du risque non spécifiée"
    
    def _extract_score_from_content(self, content: str, score_type: str) -> Optional[float]:
        """Extrait un score spécifique du contenu."""
        import re
        
        pattern = rf"{score_type}.*?(\d+(?:\.\d+)?)"
        match = re.search(pattern, content.lower())
        if match:
            try:
                score = float(match.group(1))
                return min(1.0, score / 100 if score > 1 else score)
            except:
                pass
        
        return None
    
    def _extract_sentiment_score(self, content: str) -> Optional[float]:
        """Extrait le score de sentiment."""
        import re
        
        patterns = [
            r"sentiment.*?([+-]?\d+(?:\.\d+)?)",
            r"sentiment.*?score.*?([+-]?\d+(?:\.\d+)?)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content.lower())
            if match:
                try:
                    score = float(match.group(1))
                    return max(-1.0, min(1.0, score))
                except:
                    continue
        
        return None
    
    def _extract_risk_reward_ratio(self, content: str) -> Optional[float]:
        """Extrait le ratio risque/récompense."""
        import re
        
        patterns = [
            r"ratio.*?(\d+(?:\.\d+)?):1",
            r"risque.*?récompense.*?(\d+(?:\.\d+)?)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content.lower())
            if match:
                try:
                    return float(match.group(1))
                except:
                    continue
        
        return None
    
    def _extract_expected_return(self, content: str) -> Optional[float]:
        """Extrait le rendement attendu."""
        import re
        
        patterns = [
            r"rendement.*?(\d+(?:\.\d+)?)%",
            r"retour.*?(\d+(?:\.\d+)?)%",
            r"gain.*?(\d+(?:\.\d+)?)%",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content.lower())
            if match:
                try:
                    return float(match.group(1)) / 100
                except:
                    continue
        
        return None