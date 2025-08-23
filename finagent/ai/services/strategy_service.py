"""
Service d'interprétation et d'adaptation des stratégies par IA.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

import structlog

from ..models import (
    AIRequest,
    AIResponse,
    AIProvider,
    ModelType,
    MarketContext,
    TechnicalIndicators,
    FundamentalMetrics,
    AnalysisResult,
    TradingContext,
    RiskParameters,
    DecisionRequest,
    TradingDecision,
    ConfidenceLevel,
    AIError,
)
from ..prompts import (
    PromptManager,
    PromptContext,
    PromptType,
)

logger = structlog.get_logger(__name__)


class StrategyService:
    """Service d'interprétation et d'adaptation des stratégies de trading par IA."""
    
    def __init__(
        self,
        ai_provider: AIProvider,
        prompt_manager: PromptManager,
        default_model: ModelType = ModelType.CLAUDE_3_5_SONNET
    ):
        self.ai_provider = ai_provider
        self.prompt_manager = prompt_manager
        self.default_model = default_model
        
        self.logger = logger.bind(service="strategy")
        
        # Cache des stratégies analysées
        self._strategy_cache: Dict[str, Dict[str, Any]] = {}
    
    async def interpret_strategy(
        self,
        strategy_name: str,
        strategy_config: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Interprète une stratégie de trading avec l'aide de l'IA."""
        
        self.logger.info(
            "Interprétation stratégie",
            strategy_name=strategy_name,
            config_keys=list(strategy_config.keys())
        )
        
        try:
            # Vérification du cache
            cache_key = self._generate_cache_key(strategy_name, strategy_config)
            if cache_key in self._strategy_cache:
                self.logger.debug("Stratégie trouvée en cache", strategy_name=strategy_name)
                return self._strategy_cache[cache_key]
            
            # Génération du prompt d'interprétation
            prompt = self._create_strategy_interpretation_prompt(
                strategy_name,
                strategy_config,
                user_preferences
            )
            
            # Requête à l'IA
            ai_request = AIRequest(
                model_type=ModelType.CLAUDE_3_5_SONNET,  # Modèle avancé pour stratégies
                prompt=prompt,
                temperature=0.3,  # Créativité modérée
                max_tokens=4000
            )
            
            ai_response = await self.ai_provider.send_request(ai_request)
            
            # Parsing de l'interprétation
            interpretation = await self._parse_strategy_interpretation(
                strategy_name,
                strategy_config,
                ai_response
            )
            
            # Mise en cache
            self._strategy_cache[cache_key] = interpretation
            
            self.logger.info(
                "Stratégie interprétée",
                strategy_name=strategy_name,
                approach=interpretation.get('approach'),
                tokens_used=ai_response.tokens_used
            )
            
            return interpretation
            
        except Exception as e:
            self.logger.error(
                "Erreur interprétation stratégie",
                strategy_name=strategy_name,
                error=str(e)
            )
            raise AIError(f"Erreur lors de l'interprétation de la stratégie: {str(e)}")
    
    async def adapt_strategy_to_market(
        self,
        strategy_interpretation: Dict[str, Any],
        market_context: MarketContext,
        current_analysis: AnalysisResult,
        market_regime: Optional[str] = None
    ) -> Dict[str, Any]:
        """Adapte une stratégie aux conditions de marché actuelles."""
        
        symbol = market_context.symbol
        
        self.logger.info(
            "Adaptation stratégie au marché",
            strategy=strategy_interpretation.get('name'),
            symbol=symbol,
            market_regime=market_regime
        )
        
        try:
            # Génération du prompt d'adaptation
            prompt = self._create_strategy_adaptation_prompt(
                strategy_interpretation,
                market_context,
                current_analysis,
                market_regime
            )
            
            # Requête à l'IA
            ai_request = AIRequest(
                model_type=ModelType.CLAUDE_3_5_SONNET,
                prompt=prompt,
                temperature=0.4,  # Plus de créativité pour adaptation
                max_tokens=3500
            )
            
            ai_response = await self.ai_provider.send_request(ai_request)
            
            # Parsing de l'adaptation
            adapted_strategy = await self._parse_strategy_adaptation(
                strategy_interpretation,
                market_context,
                ai_response
            )
            
            self.logger.info(
                "Stratégie adaptée",
                symbol=symbol,
                adaptations=len(adapted_strategy.get('adaptations', [])),
                confidence=adapted_strategy.get('confidence')
            )
            
            return adapted_strategy
            
        except Exception as e:
            self.logger.error(
                "Erreur adaptation stratégie",
                strategy=strategy_interpretation.get('name'),
                symbol=symbol,
                error=str(e)
            )
            raise AIError(f"Erreur lors de l'adaptation de la stratégie: {str(e)}")
    
    async def generate_custom_strategy(
        self,
        user_goals: Dict[str, Any],
        risk_profile: Dict[str, Any],
        market_preferences: Dict[str, Any],
        example_strategies: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Génère une stratégie personnalisée basée sur les préférences utilisateur."""
        
        self.logger.info(
            "Génération stratégie personnalisée",
            goals=list(user_goals.keys()),
            risk_level=risk_profile.get('level')
        )
        
        try:
            # Génération du prompt de création
            prompt = self._create_strategy_generation_prompt(
                user_goals,
                risk_profile,
                market_preferences,
                example_strategies
            )
            
            # Requête à l'IA avec le modèle le plus avancé
            ai_request = AIRequest(
                model_type=ModelType.CLAUDE_3_OPUS,  # Le plus créatif pour génération
                prompt=prompt,
                temperature=0.6,  # Créativité élevée
                max_tokens=5000
            )
            
            ai_response = await self.ai_provider.send_request(ai_request)
            
            # Parsing de la stratégie générée
            custom_strategy = await self._parse_generated_strategy(
                user_goals,
                risk_profile,
                ai_response
            )
            
            self.logger.info(
                "Stratégie personnalisée générée",
                strategy_name=custom_strategy.get('name'),
                components=len(custom_strategy.get('components', [])),
                tokens_used=ai_response.tokens_used
            )
            
            return custom_strategy
            
        except Exception as e:
            self.logger.error(
                "Erreur génération stratégie personnalisée",
                error=str(e)
            )
            raise AIError(f"Erreur lors de la génération de la stratégie: {str(e)}")
    
    async def validate_strategy_consistency(
        self,
        strategy: Dict[str, Any],
        risk_parameters: RiskParameters,
        user_constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Valide la cohérence d'une stratégie avec les paramètres de risque."""
        
        self.logger.info(
            "Validation cohérence stratégie",
            strategy_name=strategy.get('name')
        )
        
        try:
            # Génération du prompt de validation
            prompt = self._create_strategy_validation_prompt(
                strategy,
                risk_parameters,
                user_constraints
            )
            
            # Requête à l'IA
            ai_request = AIRequest(
                model_type=ModelType.CLAUDE_3_SONNET,
                prompt=prompt,
                temperature=0.2,  # Faible pour validation rigoureuse
                max_tokens=2500
            )
            
            ai_response = await self.ai_provider.send_request(ai_request)
            
            # Parsing de la validation
            validation_result = await self._parse_strategy_validation(
                strategy,
                ai_response
            )
            
            self.logger.info(
                "Validation terminée",
                strategy_name=strategy.get('name'),
                is_consistent=validation_result.get('is_consistent'),
                issues=len(validation_result.get('issues', []))
            )
            
            return validation_result
            
        except Exception as e:
            self.logger.error(
                "Erreur validation stratégie",
                strategy_name=strategy.get('name'),
                error=str(e)
            )
            raise AIError(f"Erreur lors de la validation de la stratégie: {str(e)}")
    
    async def optimize_strategy_parameters(
        self,
        strategy: Dict[str, Any],
        historical_performance: List[Dict[str, Any]],
        market_conditions: List[str],
        target_metrics: Dict[str, float]
    ) -> Dict[str, Any]:
        """Optimise les paramètres d'une stratégie basé sur les performances historiques."""
        
        self.logger.info(
            "Optimisation paramètres stratégie",
            strategy_name=strategy.get('name'),
            performance_periods=len(historical_performance)
        )
        
        try:
            # Génération du prompt d'optimisation
            prompt = self._create_strategy_optimization_prompt(
                strategy,
                historical_performance,
                market_conditions,
                target_metrics
            )
            
            # Requête à l'IA
            ai_request = AIRequest(
                model_type=ModelType.CLAUDE_3_5_SONNET,
                prompt=prompt,
                temperature=0.4,
                max_tokens=4000
            )
            
            ai_response = await self.ai_provider.send_request(ai_request)
            
            # Parsing de l'optimisation
            optimization_result = await self._parse_strategy_optimization(
                strategy,
                ai_response
            )
            
            self.logger.info(
                "Optimisation terminée",
                strategy_name=strategy.get('name'),
                optimizations=len(optimization_result.get('parameter_changes', [])),
                expected_improvement=optimization_result.get('expected_improvement')
            )
            
            return optimization_result
            
        except Exception as e:
            self.logger.error(
                "Erreur optimisation stratégie",
                strategy_name=strategy.get('name'),
                error=str(e)
            )
            raise AIError(f"Erreur lors de l'optimisation de la stratégie: {str(e)}")
    
    async def explain_strategy_decision(
        self,
        strategy: Dict[str, Any],
        trading_decision: TradingDecision,
        market_context: MarketContext,
        analysis_result: AnalysisResult
    ) -> str:
        """Explique comment la stratégie a mené à une décision de trading."""
        
        symbol = market_context.symbol
        
        self.logger.info(
            "Explication décision stratégique",
            strategy_name=strategy.get('name'),
            symbol=symbol,
            decision=trading_decision.action.value
        )
        
        try:
            # Génération du prompt d'explication
            prompt = self._create_decision_explanation_prompt(
                strategy,
                trading_decision,
                market_context,
                analysis_result
            )
            
            # Requête à l'IA
            ai_request = AIRequest(
                model_type=ModelType.CLAUDE_3_SONNET,
                prompt=prompt,
                temperature=0.3,
                max_tokens=2000
            )
            
            ai_response = await self.ai_provider.send_request(ai_request)
            
            explanation = ai_response.content.strip()
            
            self.logger.info(
                "Explication générée",
                strategy_name=strategy.get('name'),
                symbol=symbol,
                explanation_length=len(explanation)
            )
            
            return explanation
            
        except Exception as e:
            self.logger.error(
                "Erreur explication décision",
                strategy_name=strategy.get('name'),
                symbol=symbol,
                error=str(e)
            )
            return f"Erreur lors de l'explication: {str(e)}"
    
    def _generate_cache_key(self, strategy_name: str, strategy_config: Dict[str, Any]) -> str:
        """Génère une clé de cache pour une stratégie."""
        import hashlib
        import json
        
        config_str = json.dumps(strategy_config, sort_keys=True)
        cache_input = f"{strategy_name}:{config_str}"
        return hashlib.md5(cache_input.encode()).hexdigest()
    
    def _create_strategy_interpretation_prompt(
        self,
        strategy_name: str,
        strategy_config: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> str:
        """Crée un prompt pour l'interprétation de stratégie."""
        
        prompt = f"""Tu es un expert en stratégies de trading. Interprète cette stratégie de trading nommée "{strategy_name}".

CONFIGURATION DE LA STRATÉGIE:
"""
        
        for key, value in strategy_config.items():
            prompt += f"- {key}: {value}\n"
        
        if user_preferences:
            prompt += "\nPRÉFÉRENCES UTILISATEUR:\n"
            for key, value in user_preferences.items():
                prompt += f"- {key}: {value}\n"
        
        prompt += f"""
CONSIGNES D'INTERPRÉTATION:
1. Identifie le type de stratégie (technique, fondamentale, hybride)
2. Détermine l'approche principale (momentum, mean reversion, breakout, etc.)
3. Analyse les indicateurs et critères utilisés
4. Évalue l'horizon temporel de la stratégie
5. Identifie les forces et faiblesses
6. Détermine les conditions de marché optimales
7. Évalue la complexité d'implémentation

RÉPONSE ATTENDUE:
- Type de stratégie
- Approche principale
- Indicateurs clés utilisés
- Horizon temporel optimal
- Conditions de marché favorables
- Forces de la stratégie
- Faiblesses et limitations
- Niveau de complexité
- Recommandations d'amélioration

Analyse détaillée et professionnelle en français."""
        
        return prompt
    
    def _create_strategy_adaptation_prompt(
        self,
        strategy: Dict[str, Any],
        market_context: MarketContext,
        analysis: AnalysisResult,
        market_regime: Optional[str]
    ) -> str:
        """Crée un prompt pour l'adaptation de stratégie."""
        
        symbol = market_context.symbol
        current_price = market_context.current_price
        
        prompt = f"""Tu es un expert en adaptation de stratégies de trading. Adapte cette stratégie aux conditions de marché actuelles pour {symbol}.

STRATÉGIE ACTUELLE:
- Nom: {strategy.get('name', 'Non spécifié')}
- Type: {strategy.get('type', 'Non spécifié')}
- Approche: {strategy.get('approach', 'Non spécifiée')}

CONTEXTE DE MARCHÉ:
- Symbole: {symbol}
- Prix actuel: {current_price}$
- Tendance: {analysis.overall_trend.value}
- Confiance: {analysis.confidence.value}
- Niveau de risque: {analysis.risk_level.value}
"""
        
        if market_regime:
            prompt += f"- Régime de marché: {market_regime}\n"
        
        if analysis.key_drivers:
            prompt += "\nCATALYSEURS ACTUELS:\n"
            for driver in analysis.key_drivers[:3]:
                prompt += f"- {driver}\n"
        
        if analysis.risk_factors:
            prompt += "\nRISQUES ACTUELS:\n"
            for risk in analysis.risk_factors[:3]:
                prompt += f"- {risk}\n"
        
        prompt += f"""
CONSIGNES D'ADAPTATION:
1. Évalue si la stratégie est appropriée pour ces conditions
2. Identifie les ajustements nécessaires aux paramètres
3. Recommande des modifications aux critères d'entrée/sortie
4. Adapte la gestion du risque aux conditions actuelles
5. Propose des améliorations temporaires si nécessaire
6. Évalue l'impact des adaptations sur la performance

RÉPONSE ATTENDUE:
- Évaluation de l'adéquation actuelle
- Adaptations recommandées (paramètres, critères)
- Modifications de la gestion du risque
- Ajustements temporels si nécessaire
- Niveau de confiance dans les adaptations
- Impact estimé sur la performance
- Conditions de réévaluation

Analyse pratique et actionnable en français."""
        
        return prompt
    
    def _create_strategy_generation_prompt(
        self,
        user_goals: Dict[str, Any],
        risk_profile: Dict[str, Any],
        market_preferences: Dict[str, Any],
        example_strategies: Optional[List[Dict[str, Any]]]
    ) -> str:
        """Crée un prompt pour la génération de stratégie personnalisée."""
        
        prompt = """Tu es un expert en création de stratégies de trading personnalisées. Génère une stratégie adaptée aux besoins spécifiques de cet utilisateur.

OBJECTIFS UTILISATEUR:
"""
        
        for goal, value in user_goals.items():
            prompt += f"- {goal}: {value}\n"
        
        prompt += "\nPROFIL DE RISQUE:\n"
        for risk_param, value in risk_profile.items():
            prompt += f"- {risk_param}: {value}\n"
        
        prompt += "\nPRÉFÉRENCES DE MARCHÉ:\n"
        for pref, value in market_preferences.items():
            prompt += f"- {pref}: {value}\n"
        
        if example_strategies:
            prompt += "\nSTRATÉGIES DE RÉFÉRENCE:\n"
            for i, strategy in enumerate(example_strategies[:3], 1):
                prompt += f"{i}. {strategy.get('name', 'Stratégie')}: {strategy.get('description', 'N/A')}\n"
        
        prompt += f"""
CONSIGNES DE CRÉATION:
1. Conçois une stratégie cohérente avec les objectifs
2. Respecte strictement le profil de risque
3. Intègre les préférences de marché
4. Définis des critères d'entrée et de sortie clairs
5. Établis des règles de gestion du risque
6. Prévois des mécanismes d'adaptation
7. Assure la simplicité d'exécution

RÉPONSE ATTENDUE:
- Nom de la stratégie
- Description et philosophie
- Type et approche principale
- Critères d'entrée détaillés
- Critères de sortie détaillés
- Règles de gestion du risque
- Paramètres configurables
- Conditions d'adaptation
- Métriques de performance à suivre
- Instructions d'implémentation

Stratégie complète et professionnelle en français."""
        
        return prompt
    
    def _create_strategy_validation_prompt(
        self,
        strategy: Dict[str, Any],
        risk_parameters: RiskParameters,
        user_constraints: Optional[Dict[str, Any]]
    ) -> str:
        """Crée un prompt pour la validation de stratégie."""
        
        prompt = f"""Tu es un expert en validation de stratégies de trading. Valide la cohérence de cette stratégie avec les paramètres de risque.

STRATÉGIE À VALIDER:
- Nom: {strategy.get('name', 'Non spécifié')}
- Type: {strategy.get('type', 'Non spécifié')}
- Approche: {strategy.get('approach', 'Non spécifiée')}

PARAMÈTRES DE RISQUE:
- Méthode de sizing: {risk_parameters.position_sizing_method.value}
- Poids max par position: {risk_parameters.max_position_weight * 100:.1f}%
- Risque par trade: {risk_parameters.risk_per_trade * 100:.1f}%
"""
        
        if risk_parameters.stop_loss_percent:
            prompt += f"- Stop loss: {risk_parameters.stop_loss_percent * 100:.1f}%\n"
        
        if risk_parameters.take_profit_percent:
            prompt += f"- Take profit: {risk_parameters.take_profit_percent * 100:.1f}%\n"
        
        if user_constraints:
            prompt += "\nCONTRAINTES UTILISATEUR:\n"
            for constraint, value in user_constraints.items():
                prompt += f"- {constraint}: {value}\n"
        
        prompt += f"""
CONSIGNES DE VALIDATION:
1. Vérifie la cohérence entre stratégie et paramètres de risque
2. Identifie les conflits potentiels
3. Évalue la faisabilité d'implémentation
4. Contrôle le respect des contraintes utilisateur
5. Analyse les risques non couverts
6. Vérifie la logique des critères d'entrée/sortie

RÉPONSE ATTENDUE:
- Cohérence globale (OUI/NON)
- Points de cohérence identifiés
- Conflits et incohérences trouvés
- Recommandations de correction
- Risques non adressés
- Score de validation (0-10)
- Actions correctives prioritaires

Validation rigoureuse et détaillée en français."""
        
        return prompt
    
    def _create_strategy_optimization_prompt(
        self,
        strategy: Dict[str, Any],
        performance_history: List[Dict[str, Any]],
        market_conditions: List[str],
        target_metrics: Dict[str, float]
    ) -> str:
        """Crée un prompt pour l'optimisation de stratégie."""
        
        prompt = f"""Tu es un expert en optimisation de stratégies de trading. Optimise cette stratégie basée sur les performances historiques.

STRATÉGIE ACTUELLE:
- Nom: {strategy.get('name', 'Non spécifié')}
- Type: {strategy.get('type', 'Non spécifié')}

PERFORMANCE HISTORIQUE:
"""
        
        for i, perf in enumerate(performance_history[-5:], 1):  # 5 dernières performances
            prompt += f"Période {i}: Rendement {perf.get('return', 0):.2%}, "
            prompt += f"Sharpe {perf.get('sharpe', 0):.2f}, "
            prompt += f"Max DD {perf.get('max_drawdown', 0):.2%}\n"
        
        prompt += "\nCONDITIONS DE MARCHÉ OBSERVÉES:\n"
        for condition in market_conditions[-10:]:  # 10 dernières conditions
            prompt += f"- {condition}\n"
        
        prompt += "\nOBJECTIFS D'OPTIMISATION:\n"
        for metric, target in target_metrics.items():
            prompt += f"- {metric}: {target:.2%} minimum\n"
        
        prompt += f"""
CONSIGNES D'OPTIMISATION:
1. Analyse les performances dans différentes conditions
2. Identifie les paramètres sous-optimaux
3. Propose des ajustements spécifiques
4. Évalue l'impact des changements proposés
5. Maintient la cohérence de la stratégie
6. Considère les objectifs de performance

RÉPONSE ATTENDUE:
- Analyse des performances actuelles
- Paramètres à optimiser (avec valeurs actuelles et proposées)
- Justification des changements
- Impact estimé sur les métriques cibles
- Risques des modifications
- Plan d'implémentation des changements
- Méthode de validation des améliorations

Optimisation rigoureuse et justifiée en français."""
        
        return prompt
    
    def _create_decision_explanation_prompt(
        self,
        strategy: Dict[str, Any],
        decision: TradingDecision,
        market_context: MarketContext,
        analysis: AnalysisResult
    ) -> str:
        """Crée un prompt pour l'explication d'une décision."""
        
        symbol = market_context.symbol
        
        prompt = f"""Tu es un expert en explication de décisions de trading. Explique comment cette stratégie a mené à la décision prise.

STRATÉGIE UTILISÉE:
- Nom: {strategy.get('name', 'Non spécifié')}
- Approche: {strategy.get('approach', 'Non spécifiée')}

CONTEXTE DE MARCHÉ:
- Symbole: {symbol}
- Prix: {market_context.current_price}$
- Tendance: {analysis.overall_trend.value}

DÉCISION PRISE:
- Action: {decision.action.value}
- Confiance: {decision.confidence.value}
- Quantité: {decision.recommended_quantity or 'Non spécifiée'}
"""
        
        if decision.reasoning:
            prompt += f"- Raisonnement IA: {decision.reasoning}\n"
        
        prompt += f"""
CONSIGNES D'EXPLICATION:
1. Explique le lien entre stratégie et analyse de marché
2. Détaille les critères qui ont déclenché la décision
3. Justifie le niveau de confiance
4. Explique la logique de taille de position
5. Mentionne les facteurs de risque considérés

Explication claire et pédagogique en français, maximum 200 mots."""
        
        return prompt
    
    # Méthodes de parsing (simplifiées pour l'exemple)
    
    async def _parse_strategy_interpretation(
        self,
        strategy_name: str,
        strategy_config: Dict[str, Any],
        ai_response: AIResponse
    ) -> Dict[str, Any]:
        """Parse l'interprétation de stratégie."""
        
        content = ai_response.content
        
        return {
            'name': strategy_name,
            'original_config': strategy_config,
            'type': self._extract_strategy_type(content),
            'approach': self._extract_approach(content),
            'complexity': self._extract_complexity(content),
            'time_horizon': self._extract_time_horizon(content),
            'market_conditions': self._extract_favorable_conditions(content),
            'strengths': self._extract_strengths(content),
            'weaknesses': self._extract_weaknesses(content),
            'interpretation': content,
            'timestamp': datetime.utcnow()
        }
    
    async def _parse_strategy_adaptation(
        self,
        strategy: Dict[str, Any],
        market_context: MarketContext,
        ai_response: AIResponse
    ) -> Dict[str, Any]:
        """Parse l'adaptation de stratégie."""
        
        content = ai_response.content
        
        return {
            'original_strategy': strategy,
            'market_context': market_context.symbol,
            'adaptations': self._extract_adaptations(content),
            'parameter_changes': self._extract_parameter_changes(content),
            'risk_adjustments': self._extract_risk_adjustments(content),
            'confidence': self._extract_adaptation_confidence(content),
            'adapted_strategy': content,
            'timestamp': datetime.utcnow()
        }
    
    async def _parse_generated_strategy(
        self,
        user_goals: Dict[str, Any],
        risk_profile: Dict[str, Any],
        ai_response: AIResponse
    ) -> Dict[str, Any]:
        """Parse une stratégie générée."""
        
        content = ai_response.content
        
        return {
            'name': self._extract_strategy_name(content),
            'description': self._extract_description(content),
            'type': self._extract_strategy_type(content),
            'approach': self._extract_approach(content),
            'entry_criteria': self._extract_entry_criteria(content),
            'exit_criteria': self._extract_exit_criteria(content),
            'risk_management': self._extract_risk_rules(content),
            'parameters': self._extract_parameters(content),
            'user_goals': user_goals,
            'risk_profile': risk_profile,
            'full_strategy': content,
            'generated_at': datetime.utcnow()
        }
    
    async def _parse_strategy_validation(
        self,
        strategy: Dict[str, Any],
        ai_response: AIResponse
    ) -> Dict[str, Any]:
        """Parse la validation de stratégie."""
        
        content = ai_response.content
        
        return {
            'strategy_name': strategy.get('name'),
            'is_consistent': self._extract_consistency(content),
            'validation_score': self._extract_validation_score(content),
            'coherent_points': self._extract_coherent_points(content),
            'issues': self._extract_issues(content),
            'recommendations': self._extract_recommendations(content),
            'validation_report': content,
            'validated_at': datetime.utcnow()
        }
    
    async def _parse_strategy_optimization(
        self,
        strategy: Dict[str, Any],
        ai_response: AIResponse
    ) -> Dict[str, Any]:
        """Parse l'optimisation de stratégie."""
        
        content = ai_response.content
        
        return {
            'strategy_name': strategy.get('name'),
            'parameter_changes': self._extract_parameter_optimizations(content),
            'expected_improvement': self._extract_expected_improvement(content),
            'implementation_plan': self._extract_implementation_plan(content),
            'risks': self._extract_optimization_risks(content),
            'validation_method': self._extract_validation_method(content),
            'optimization_report': content,
            'optimized_at': datetime.utcnow()
        }
    
    # Méthodes d'extraction simplifiées (en pratique, utiliser des techniques NLP plus sophistiquées)
    
    def _extract_strategy_type(self, content: str) -> str:
        """Extrait le type de stratégie."""
        content_lower = content.lower()
        
        if 'technique' in content_lower:
            return 'technical'
        elif 'fondamental' in content_lower:
            return 'fundamental'
        elif 'hybride' in content_lower:
            return 'hybrid'
        else:
            return 'unknown'
    
    def _extract_approach(self, content: str) -> str:
        """Extrait l'approche principale."""
        content_lower = content.lower()
        
        approaches = {
            'momentum': ['momentum', 'élan'],
            'mean_reversion': ['retour à la moyenne', 'mean reversion'],
            'breakout': ['breakout', 'cassure'],
            'trend_following': ['suivi de tendance', 'trend following'],
            'contrarian': ['contrarian', 'contraire']
        }
        
        for approach, keywords in approaches.items():
            if any(keyword in content_lower for keyword in keywords):
                return approach
        
        return 'unknown'
    
    def _extract_complexity(self, content: str) -> str:
        """Extrait le niveau de complexité."""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ['simple', 'facile', 'basique']):
            return 'simple'
        elif any(word in content_lower for word in ['complexe', 'avancé', 'sophistiqué']):
            return 'complex'
        else:
            return 'moderate'
    
    def _extract_time_horizon(self, content: str) -> str:
        """Extrait l'horizon temporel."""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ['court terme', 'scalping', 'intraday']):
            return 'short_term'
        elif any(word in content_lower for word in ['long terme', 'investissement']):
            return 'long_term'
        else:
            return 'medium_term'
    
    def _extract_favorable_conditions(self, content: str) -> List[str]:
        """Extrait les conditions de marché favorables."""
        conditions = []
        
        if 'tendance' in content.lower():
            conditions.append('trending_market')
        if 'volatile' in content.lower():
            conditions.append('volatile_market')
        if 'latéral' in content.lower():
            conditions.append('sideways_market')
        
        return conditions
    
    def _extract_strengths(self, content: str) -> List[str]:
        """Extrait les forces de la stratégie."""
        return self._extract_list_items(content, ['force', 'avantage', 'point fort'])
    
    def _extract_weaknesses(self, content: str) -> List[str]:
        """Extrait les faiblesses de la stratégie."""
        return self._extract_list_items(content, ['faiblesse', 'inconvénient', 'limitation'])
    
    def _extract_list_items(self, content: str, keywords: List[str]) -> List[str]:
        """Extrait des éléments de liste basés sur des mots-clés."""
        items = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in keywords):
                if line.startswith('-') or line.startswith('•'):
                    item = line[1:].strip()
                    if item and len(item) > 5:
                        items.append(item)
        
        return items[:5]  # Max 5 éléments
    
    def _extract_adaptations(self, content: str) -> List[str]:
        """Extrait les adaptations recommandées."""
        return self._extract_list_items(content, ['adaptation', 'ajustement', 'modification'])
    
    def _extract_parameter_changes(self, content: str) -> Dict[str, str]:
        """Extrait les changements de paramètres."""
        # Implémentation simplifiée
        return {'example_param': 'new_value'}
    
    def _extract_risk_adjustments(self, content: str) -> List[str]:
        """Extrait les ajustements de risque."""
        return self._extract_list_items(content, ['risque', 'stop', 'limite'])
    
    def _extract_adaptation_confidence(self, content: str) -> str:
        """Extrait le niveau de confiance de l'adaptation."""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ['très confiant', 'très élevé']):
            return 'very_high'
        elif any(word in content_lower for word in ['confiant', 'élevé']):
            return 'high'
        elif any(word in content_lower for word in ['faible', 'incertain']):
            return 'low'
        else:
            return 'medium'
    
    def _extract_strategy_name(self, content: str) -> str:
        """Extrait le nom de la stratégie."""
        lines = content.split('\n')
        for line in lines:
            if 'nom' in line.lower() and ':' in line:
                return line.split(':')[1].strip()
        return 'Stratégie Personnalisée'
    
    def _extract_description(self, content: str) -> str:
        """Extrait la description."""
        lines = content.split('\n')
        for line in lines:
            if 'description' in line.lower() and ':' in line:
                return line.split(':')[1].strip()
        return 'Description non disponible'
    
    def _extract_entry_criteria(self, content: str) -> List[str]:
        """Extrait les critères d'entrée."""
        return self._extract_list_items(content, ['entrée', 'achat', 'signal'])
    
    def _extract_exit_criteria(self, content: str) -> List[str]:
        """Extrait les critères de sortie."""
        return self._extract_list_items(content, ['sortie', 'vente', 'clôture'])
    
    def _extract_risk_rules(self, content: str) -> List[str]:
        """Extrait les règles de gestion du risque."""
        return self._extract_list_items(content, ['risque', 'stop', 'limite', 'protection'])
    
    def _extract_parameters(self, content: str) -> Dict[str, Any]:
        """Extrait les paramètres configurables."""
        # Implémentation simplifiée
        return {}
    
    def _extract_consistency(self, content: str) -> bool:
        """Extrait si la stratégie est cohérente."""
        content_lower = content.lower()
        return 'oui' in content_lower and 'cohérent' in content_lower
    
    def _extract_validation_score(self, content: str) -> Optional[float]:
        """Extrait le score de validation."""
        import re
        
        match = re.search(r'score.*?(\d+(?:\.\d+)?)', content.lower())
        if match:
            try:
                return float(match.group(1))
            except:
                pass
        return None
    
    def _extract_coherent_points(self, content: str) -> List[str]:
        """Extrait les points cohérents."""
        return self._extract_list_items(content, ['cohérent', 'correct', 'approprié'])
    
    def _extract_issues(self, content: str) -> List[str]:
        """Extrait les problèmes identifiés."""
        return self._extract_list_items(content, ['problème', 'conflit', 'incohérence'])
    
    def _extract_recommendations(self, content: str) -> List[str]:
        """Extrait les recommandations."""
        return self._extract_list_items(content, ['recommandation', 'suggestion', 'conseil'])
    
    def _extract_parameter_optimizations(self, content: str) -> List[Dict[str, Any]]:
        """Extrait les optimisations de paramètres."""
        # Implémentation simplifiée
        return []
    
    def _extract_expected_improvement(self, content: str) -> Optional[float]:
        """Extrait l'amélioration attendue."""
        import re
        
        match = re.search(r'amélioration.*?(\d+(?:\.\d+)?)%', content.lower())
        if match:
            try:
                return float(match.group(1)) / 100
            except:
                pass
        return None
    
    def _extract_implementation_plan(self, content: str) -> List[str]:
        """Extrait le plan d'implémentation."""
        return self._extract_list_items(content, ['implémentation', 'étape', 'plan'])
    
    def _extract_optimization_risks(self, content: str) -> List[str]:
        """Extrait les risques de l'optimisation."""
        return self._extract_list_items(content, ['risque', 'danger', 'précaution'])
    
    def _extract_validation_method(self, content: str) -> str:
        """Extrait la méthode de validation."""
        content_lower = content.lower()
        
        if 'backtest' in content_lower:
            return 'backtesting'
        elif 'simulation' in content_lower:
            return 'simulation'
        elif 'paper trading' in content_lower:
            return 'paper_trading'
        else:
            return 'manual_review'