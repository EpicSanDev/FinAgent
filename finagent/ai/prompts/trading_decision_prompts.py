"""
Prompts pour les décisions de trading.
"""

from typing import Any, Dict, List, Optional
from decimal import Decimal

from ..models import (
    TradingContext,
    RiskParameters,
    AnalysisResult,
    DecisionType,
    PositionSizing,
    ConfidenceLevel
)


class TradingDecisionPrompts:
    """Générateur de prompts pour les décisions de trading."""
    
    @staticmethod
    def create_buy_decision_prompt(
        trading_context: TradingContext,
        analysis_result: AnalysisResult,
        risk_parameters: RiskParameters,
        strategy_context: Optional[str] = None
    ) -> str:
        """Crée un prompt pour une décision d'achat."""
        
        symbol = trading_context.symbol
        current_price = trading_context.current_price
        available_cash = trading_context.available_cash
        portfolio_value = trading_context.portfolio_value
        
        prompt = f"""Tu es un trader professionnel expert. Évalue une opportunité d'ACHAT pour {symbol}.

CONTEXTE DE TRADING:
- Symbole: {symbol}
- Prix actuel: {current_price}$
- Liquidités disponibles: {available_cash:,.2f}$
- Valeur du portefeuille: {portfolio_value:,.2f}$
- Position actuelle: {trading_context.current_position or 0} actions
"""
        
        if trading_context.average_cost:
            prompt += f"- Prix moyen d'acquisition: {trading_context.average_cost}$\n"
            if trading_context.position_pnl:
                prompt += f"- P&L position actuelle: {trading_context.position_pnl:+,.2f}$\n"
        
        prompt += f"""
ANALYSE TECHNIQUE/FONDAMENTALE:
- Tendance globale: {analysis_result.overall_trend.value}
- Niveau de confiance: {analysis_result.confidence.value}
- Score bullish: {analysis_result.bullish_score:.3f}
- Score bearish: {analysis_result.bearish_score:.3f}
- Niveau de risque: {analysis_result.risk_level.value}
"""
        
        if analysis_result.technical_score:
            prompt += f"- Score technique: {analysis_result.technical_score:.3f}\n"
        if analysis_result.fundamental_score:
            prompt += f"- Score fondamental: {analysis_result.fundamental_score:.3f}\n"
        if analysis_result.sentiment_score:
            prompt += f"- Score sentiment: {analysis_result.sentiment_score:+.3f}\n"
        
        if analysis_result.support_levels:
            prompt += f"- Supports: {', '.join([f'{s}$' for s in analysis_result.support_levels[:3]])}\n"
        if analysis_result.resistance_levels:
            prompt += f"- Résistances: {', '.join([f'{r}$' for r in analysis_result.resistance_levels[:3]])}\n"
        
        if analysis_result.target_price_bull:
            prompt += f"- Prix cible haussier: {analysis_result.target_price_bull}$\n"
        if analysis_result.stop_loss_level:
            prompt += f"- Stop loss suggéré: {analysis_result.stop_loss_level}$\n"
        
        prompt += f"""
PARAMÈTRES DE RISQUE:
- Méthode de sizing: {risk_parameters.position_sizing_method.value}
- Poids max par position: {risk_parameters.max_position_weight * 100:.1f}%
- Risque par trade: {risk_parameters.risk_per_trade * 100:.1f}%
- Stop loss: {risk_parameters.stop_loss_percent * 100 if risk_parameters.stop_loss_percent else 'N/A'}%
- Take profit: {risk_parameters.take_profit_percent * 100 if risk_parameters.take_profit_percent else 'N/A'}%
"""
        
        if strategy_context:
            prompt += f"\nSTRATÉGIE: {strategy_context}\n"
        
        if analysis_result.key_drivers:
            prompt += "\nCATALYSEURS POSITIFS:\n"
            for driver in analysis_result.key_drivers[:5]:
                prompt += f"- {driver}\n"
        
        if analysis_result.risk_factors:
            prompt += "\nRISQUES IDENTIFIÉS:\n"
            for risk in analysis_result.risk_factors[:5]:
                prompt += f"- {risk}\n"
        
        prompt += f"""
CONSIGNES DE DÉCISION:
1. Détermine si c'est le bon moment pour ACHETER
2. Calcule la taille de position optimale
3. Définis les niveaux de stop-loss et take-profit
4. Évalue le ratio risque/récompense
5. Identifie les conditions d'invalidation
6. Détermine le niveau d'urgence d'exécution

CRITÈRES D'ÉVALUATION:
- Le signal d'achat est-il clair et confirmé ?
- Le timing d'entrée est-il optimal ?
- Le ratio risque/récompense est-il favorable (>2:1) ?
- La taille de position respecte-t-elle les règles de gestion du risque ?
- Y a-t-il des catalyseurs imminents ?

RÉPONSE ATTENDUE:
- Décision: BUY, STRONG_BUY, ou HOLD avec justification
- Niveau de confiance: VERY_LOW à VERY_HIGH
- Quantité recommandée (nombre d'actions)
- Prix limite d'achat (si différent du marché)
- Stop-loss recommandé
- Take-profit recommandé
- Ratio risque/récompense calculé
- Timing d'exécution optimal
- Conditions d'invalidation de la décision

Justifie chaque recommandation de manière précise et professionnelle en français."""
        
        return prompt
    
    @staticmethod
    def create_sell_decision_prompt(
        trading_context: TradingContext,
        analysis_result: AnalysisResult,
        risk_parameters: RiskParameters,
        hold_period_days: Optional[int] = None
    ) -> str:
        """Crée un prompt pour une décision de vente."""
        
        symbol = trading_context.symbol
        current_price = trading_context.current_price
        current_position = trading_context.current_position or 0
        average_cost = trading_context.average_cost
        
        prompt = f"""Tu es un trader professionnel expert. Évalue une opportunité de VENTE pour {symbol}.

POSITION ACTUELLE:
- Symbole: {symbol}
- Prix actuel: {current_price}$
- Position: {current_position} actions
- Valeur position: {current_position * current_price:,.2f}$
"""
        
        if average_cost:
            pnl = (current_price - average_cost) * current_position
            pnl_percent = (current_price - average_cost) / average_cost * 100
            prompt += f"- Prix d'acquisition moyen: {average_cost}$\n"
            prompt += f"- P&L: {pnl:+,.2f}$ ({pnl_percent:+.2f}%)\n"
        
        if hold_period_days:
            prompt += f"- Période de détention: {hold_period_days} jours\n"
        
        prompt += f"""
ANALYSE ACTUELLE:
- Tendance globale: {analysis_result.overall_trend.value}
- Niveau de confiance: {analysis_result.confidence.value}
- Score bullish: {analysis_result.bullish_score:.3f}
- Score bearish: {analysis_result.bearish_score:.3f}
- Niveau de risque: {analysis_result.risk_level.value}
"""
        
        if analysis_result.target_price_bear:
            prompt += f"- Prix cible baissier: {analysis_result.target_price_bear}$\n"
        
        if analysis_result.support_levels:
            nearest_support = min(analysis_result.support_levels, key=lambda x: abs(x - current_price))
            prompt += f"- Support le plus proche: {nearest_support}$\n"
        
        if analysis_result.resistance_levels:
            nearest_resistance = min(analysis_result.resistance_levels, key=lambda x: abs(x - current_price))
            prompt += f"- Résistance la plus proche: {nearest_resistance}$\n"
        
        prompt += f"""
GESTION DU RISQUE:
- Stop loss: {risk_parameters.stop_loss_percent * 100 if risk_parameters.stop_loss_percent else 'N/A'}%
- Take profit: {risk_parameters.take_profit_percent * 100 if risk_parameters.take_profit_percent else 'N/A'}%
- Trailing stop: {risk_parameters.trailing_stop_percent * 100 if risk_parameters.trailing_stop_percent else 'N/A'}%
"""
        
        if analysis_result.risk_factors:
            prompt += "\nRISQUES ACTUELS:\n"
            for risk in analysis_result.risk_factors[:5]:
                prompt += f"- {risk}\n"
        
        if analysis_result.opportunities:
            prompt += "\nOPPORTUNITÉS RESTANTES:\n"
            for opp in analysis_result.opportunities[:3]:
                prompt += f"- {opp}\n"
        
        prompt += f"""
CONSIGNES DE DÉCISION:
1. Évalue s'il faut VENDRE maintenant
2. Détermine la quantité à vendre (partielle ou totale)
3. Choisis le type d'ordre optimal
4. Évalue si les objectifs de profit sont atteints
5. Vérifie si les conditions de stop-loss sont remplies
6. Analyse l'évolution du momentum

CRITÈRES D'ÉVALUATION:
- Les objectifs de profit sont-ils atteints ?
- Le momentum se détériore-t-il ?
- Y a-t-il des signaux de retournement ?
- Le niveau de risque a-t-il augmenté ?
- Des catalyseurs négatifs sont-ils imminents ?

TYPES DE VENTE À CONSIDÉRER:
- Prise de profit (take-profit)
- Stop-loss défensif
- Vente sur détérioration technique
- Réduction de position (vente partielle)
- Sortie complète

RÉPONSE ATTENDUE:
- Décision: SELL, STRONG_SELL, ou HOLD avec justification
- Niveau de confiance: VERY_LOW à VERY_HIGH
- Quantité à vendre (% de la position)
- Type d'ordre recommandé
- Prix limite de vente (si applicable)
- Timing d'exécution optimal
- Justification de la sortie
- Impact sur le portefeuille

Analyse objective et détaillée en français."""
        
        return prompt
    
    @staticmethod
    def create_hold_decision_prompt(
        trading_context: TradingContext,
        analysis_result: AnalysisResult,
        market_conditions: Optional[str] = None
    ) -> str:
        """Crée un prompt pour une décision de conservation."""
        
        symbol = trading_context.symbol
        current_price = trading_context.current_price
        
        prompt = f"""Tu es un trader professionnel expert. Évalue si tu dois CONSERVER la position sur {symbol}.

SITUATION ACTUELLE:
- Symbole: {symbol}
- Prix actuel: {current_price}$
- Position: {trading_context.current_position or 0} actions
- Conditions de marché: {market_conditions or 'Non spécifiées'}
"""
        
        if trading_context.position_pnl:
            prompt += f"- P&L position: {trading_context.position_pnl:+,.2f}$\n"
        
        prompt += f"""
ANALYSE TECHNIQUE/FONDAMENTALE:
- Tendance: {analysis_result.overall_trend.value}
- Confiance: {analysis_result.confidence.value}
- Score bullish: {analysis_result.bullish_score:.3f}
- Score bearish: {analysis_result.bearish_score:.3f}
- Risque: {analysis_result.risk_level.value}
"""
        
        if analysis_result.key_drivers:
            prompt += "\nFACTEURS POSITIFS:\n"
            for driver in analysis_result.key_drivers[:3]:
                prompt += f"- {driver}\n"
        
        if analysis_result.risk_factors:
            prompt += "\nFACTEURS DE RISQUE:\n"
            for risk in analysis_result.risk_factors[:3]:
                prompt += f"- {risk}\n"
        
        prompt += f"""
CONSIGNES:
1. Évalue si la thèse d'investissement reste valide
2. Détermine si les conditions de marché soutiennent la position
3. Analyse si des ajustements sont nécessaires
4. Vérifie si de nouveaux catalyseurs émergent
5. Évalue l'opportunité cost vs autres investissements

QUESTIONS CLÉS:
- La tendance reste-t-elle favorable ?
- Les fondamentaux se sont-ils détériorés ?
- Le niveau de risque est-il acceptable ?
- Y a-t-il de meilleures opportunités ailleurs ?
- Le timing de sortie est-il prématuré ?

RÉPONSE ATTENDUE:
- Décision: HOLD avec justification claire
- Actions de monitoring recommandées
- Niveaux à surveiller (support/résistance)
- Catalyseurs à attendre
- Conditions de réévaluation
- Ajustements stratégiques éventuels

Analyse nuancée et professionnelle en français."""
        
        return prompt
    
    @staticmethod
    def create_portfolio_rebalancing_prompt(
        portfolio_positions: List[Dict[str, Any]],
        target_allocation: Dict[str, float],
        risk_metrics: Dict[str, float],
        market_outlook: Optional[str] = None
    ) -> str:
        """Crée un prompt pour le rééquilibrage de portefeuille."""
        
        prompt = f"""Tu es un gestionnaire de portefeuille expert. Analyse le besoin de rééquilibrage du portefeuille.

POSITIONS ACTUELLES:
"""
        
        total_value = sum(pos.get('value', 0) for pos in portfolio_positions)
        
        for pos in portfolio_positions:
            symbol = pos.get('symbol', 'N/A')
            value = pos.get('value', 0)
            allocation = (value / total_value * 100) if total_value > 0 else 0
            pnl = pos.get('pnl', 0)
            prompt += f"- {symbol}: {value:,.2f}$ ({allocation:.1f}%) - P&L: {pnl:+,.2f}$\n"
        
        prompt += f"\nVALEUR TOTALE: {total_value:,.2f}$\n"
        
        prompt += "\nALLOCATION CIBLE:\n"
        for asset, target in target_allocation.items():
            prompt += f"- {asset}: {target * 100:.1f}%\n"
        
        prompt += "\nMÉTRIQUES DE RISQUE:\n"
        for metric, value in risk_metrics.items():
            prompt += f"- {metric}: {value:.3f}\n"
        
        if market_outlook:
            prompt += f"\nPERSPECTIVE DE MARCHÉ: {market_outlook}\n"
        
        prompt += f"""
CONSIGNES DE RÉÉQUILIBRAGE:
1. Compare l'allocation actuelle vs cible
2. Identifie les écarts significatifs (>5%)
3. Propose des ajustements pour optimiser le risque
4. Considère les coûts de transaction
5. Évalue l'impact fiscal potentiel
6. Prends en compte les conditions de marché

FACTEURS À CONSIDÉRER:
- Dérive de l'allocation due aux performances
- Changement des conditions de marché
- Nouveaux objectifs de risque
- Opportunités de prise de profit
- Optimisation fiscale

RÉPONSE ATTENDUE:
- Nécessité de rééquilibrage (OUI/NON)
- Actions spécifiques recommandées
- Ordre de priorité des ajustements
- Impact estimé sur le risque
- Timing optimal pour l'exécution
- Coûts estimés de rééquilibrage

Recommandations précises et actionables en français."""
        
        return prompt
    
    @staticmethod
    def create_risk_management_prompt(
        portfolio_risk: Dict[str, Any],
        position_risks: List[Dict[str, Any]],
        market_stress_scenarios: Optional[Dict[str, float]] = None,
        risk_limits: Optional[Dict[str, float]] = None
    ) -> str:
        """Crée un prompt pour la gestion des risques."""
        
        prompt = """Tu es un expert en gestion des risques financiers. Évalue et recommande des actions de gestion du risque.

RISQUE DE PORTEFEUILLE:
"""
        
        for metric, value in portfolio_risk.items():
            prompt += f"- {metric}: {value}\n"
        
        prompt += "\nRISQUES PAR POSITION:\n"
        for pos_risk in position_risks:
            symbol = pos_risk.get('symbol', 'N/A')
            risk_score = pos_risk.get('risk_score', 'N/A')
            contribution = pos_risk.get('risk_contribution', 'N/A')
            prompt += f"- {symbol}: Score {risk_score}, Contribution {contribution}\n"
        
        if market_stress_scenarios:
            prompt += "\nSCÉNARIOS DE STRESS:\n"
            for scenario, impact in market_stress_scenarios.items():
                prompt += f"- {scenario}: {impact:+.2f}%\n"
        
        if risk_limits:
            prompt += "\nLIMITES DE RISQUE:\n"
            for limit, value in risk_limits.items():
                prompt += f"- {limit}: {value}\n"
        
        prompt += f"""
CONSIGNES:
1. Identifie les concentrations de risque excessives
2. Évalue si les limites de risque sont respectées
3. Propose des actions de mitigation
4. Recommande des ajustements de position
5. Suggère des stratégies de couverture si nécessaire

ACTIONS DE GESTION POSSIBLES:
- Réduction de positions à haut risque
- Diversification sectorielle/géographique
- Mise en place de couvertures (hedging)
- Ajustement des stops-loss
- Réduction de l'exposition globale

RÉPONSE ATTENDUE:
- Évaluation du niveau de risque global
- Principales sources de risque
- Actions correctives prioritaires
- Recommandations de couverture
- Limites à ajuster si nécessaire
- Plan de contingence si détérioration

Analyse rigoureuse et recommandations concrètes en français."""
        
        return prompt