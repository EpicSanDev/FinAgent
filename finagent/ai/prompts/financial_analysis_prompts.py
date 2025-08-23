"""
Prompts pour l'analyse financière.
"""

from typing import Any, Dict, List, Optional
from decimal import Decimal
from datetime import datetime

from ..models import (
    MarketContext,
    TechnicalIndicators,
    FundamentalMetrics,
    SentimentData,
    AnalysisType,
    TrendDirection,
    RiskLevel
)


class FinancialAnalysisPrompts:
    """Générateur de prompts pour l'analyse financière."""
    
    @staticmethod
    def create_technical_analysis_prompt(
        market_context: MarketContext,
        technical_indicators: TechnicalIndicators,
        time_horizon: str = "1d"
    ) -> str:
        """Crée un prompt pour l'analyse technique."""
        
        symbol = market_context.symbol
        current_price = market_context.current_price
        
        prompt = f"""Tu es un analyste technique expert. Analyse l'action {symbol} actuellement à {current_price}$ pour un horizon de {time_horizon}.

DONNÉES DE MARCHÉ:
- Prix actuel: {current_price}$
- Volume 24h: {market_context.volume_24h or 'N/A'}
- Variation 24h: {market_context.price_change_24h or 'N/A'}%
- Variation 7j: {market_context.price_change_7d or 'N/A'}%
- Variation 30j: {market_context.price_change_30d or 'N/A'}%

INDICATEURS TECHNIQUES:
"""
        
        # Ajout des indicateurs de momentum
        if technical_indicators.rsi:
            prompt += f"- RSI: {technical_indicators.rsi:.1f}\n"
        
        if technical_indicators.stoch_k and technical_indicators.stoch_d:
            prompt += f"- Stochastique K: {technical_indicators.stoch_k:.1f}, D: {technical_indicators.stoch_d:.1f}\n"
        
        if technical_indicators.williams_r:
            prompt += f"- Williams %R: {technical_indicators.williams_r:.1f}\n"
        
        # Indicateurs de tendance
        if technical_indicators.macd and technical_indicators.macd_signal:
            prompt += f"- MACD: {technical_indicators.macd:.4f}, Signal: {technical_indicators.macd_signal:.4f}\n"
            if technical_indicators.macd_histogram:
                prompt += f"- MACD Histogramme: {technical_indicators.macd_histogram:.4f}\n"
        
        if technical_indicators.adx:
            prompt += f"- ADX: {technical_indicators.adx:.1f}\n"
        
        # Moyennes mobiles
        if market_context.moving_avg_50:
            prompt += f"- MM50: {market_context.moving_avg_50}$\n"
        if market_context.moving_avg_200:
            prompt += f"- MM200: {market_context.moving_avg_200}$\n"
        
        if technical_indicators.sma_20:
            prompt += f"- SMA20: {technical_indicators.sma_20}$\n"
        
        # Bandes de Bollinger
        if (technical_indicators.bollinger_upper and 
            technical_indicators.bollinger_lower and 
            technical_indicators.bollinger_middle):
            prompt += f"- Bollinger: Haute {technical_indicators.bollinger_upper}$, "
            prompt += f"Milieu {technical_indicators.bollinger_middle}$, "
            prompt += f"Basse {technical_indicators.bollinger_lower}$\n"
        
        # Volatilité
        if technical_indicators.atr:
            prompt += f"- ATR: {technical_indicators.atr:.3f}\n"
        
        # Volume
        if technical_indicators.volume_ratio:
            prompt += f"- Ratio de volume: {technical_indicators.volume_ratio:.2f}\n"
        
        prompt += f"""
CONSIGNES D'ANALYSE:
1. Évalue la tendance actuelle (haussière, baissière, latérale)
2. Identifie les niveaux de support et résistance clés
3. Analyse les signaux de momentum (surachat/survente)
4. Détermine la force de la tendance
5. Identifie les patterns graphiques potentiels
6. Évalue le volume et sa signification
7. Prédis les mouvements probables pour {time_horizon}

RÉPONSE ATTENDUE:
Fournis une analyse structurée avec:
- Direction de tendance: STRONG_BULLISH, BULLISH, NEUTRAL, BEARISH, STRONG_BEARISH
- Niveaux de support (3 maximum)
- Niveaux de résistance (3 maximum)
- Score technique (0.0 à 1.0)
- Facteurs clés de l'analyse
- Catalyseurs techniques potentiels
- Niveau de risque: VERY_LOW, LOW, MODERATE, HIGH, VERY_HIGH

Format ta réponse de manière claire et concise en français."""
        
        return prompt
    
    @staticmethod
    def create_fundamental_analysis_prompt(
        market_context: MarketContext,
        fundamental_metrics: FundamentalMetrics,
        sector_context: Optional[str] = None
    ) -> str:
        """Crée un prompt pour l'analyse fondamentale."""
        
        symbol = market_context.symbol
        current_price = market_context.current_price
        market_cap = market_context.market_cap
        
        prompt = f"""Tu es un analyste fondamental expert. Analyse l'action {symbol} d'un point de vue fondamental.

DONNÉES DE BASE:
- Symbole: {symbol}
- Prix actuel: {current_price}$
- Capitalisation: {market_cap or 'N/A'}$
- Secteur: {sector_context or 'N/A'}

MÉTRIQUES DE VALORISATION:
"""
        
        if fundamental_metrics.pe_ratio:
            prompt += f"- P/E: {fundamental_metrics.pe_ratio:.2f}\n"
        if fundamental_metrics.pe_forward:
            prompt += f"- P/E Forward: {fundamental_metrics.pe_forward:.2f}\n"
        if fundamental_metrics.pb_ratio:
            prompt += f"- P/B: {fundamental_metrics.pb_ratio:.2f}\n"
        if fundamental_metrics.ps_ratio:
            prompt += f"- P/S: {fundamental_metrics.ps_ratio:.2f}\n"
        if fundamental_metrics.pcf_ratio:
            prompt += f"- P/CF: {fundamental_metrics.pcf_ratio:.2f}\n"
        
        prompt += "\nMÉTRIQUES DE PROFITABILITÉ:\n"
        
        if fundamental_metrics.roe:
            prompt += f"- ROE: {fundamental_metrics.roe:.2f}%\n"
        if fundamental_metrics.roa:
            prompt += f"- ROA: {fundamental_metrics.roa:.2f}%\n"
        if fundamental_metrics.gross_margin:
            prompt += f"- Marge brute: {fundamental_metrics.gross_margin:.2f}%\n"
        if fundamental_metrics.operating_margin:
            prompt += f"- Marge opérationnelle: {fundamental_metrics.operating_margin:.2f}%\n"
        if fundamental_metrics.net_margin:
            prompt += f"- Marge nette: {fundamental_metrics.net_margin:.2f}%\n"
        
        prompt += "\nMÉTRIQUES DE CROISSANCE:\n"
        
        if fundamental_metrics.revenue_growth_yoy:
            prompt += f"- Croissance revenus (YoY): {fundamental_metrics.revenue_growth_yoy:.2f}%\n"
        if fundamental_metrics.earnings_growth_yoy:
            prompt += f"- Croissance bénéfices (YoY): {fundamental_metrics.earnings_growth_yoy:.2f}%\n"
        if fundamental_metrics.revenue_growth_qoq:
            prompt += f"- Croissance revenus (QoQ): {fundamental_metrics.revenue_growth_qoq:.2f}%\n"
        if fundamental_metrics.earnings_growth_qoq:
            prompt += f"- Croissance bénéfices (QoQ): {fundamental_metrics.earnings_growth_qoq:.2f}%\n"
        
        prompt += "\nSOLIDITÉ FINANCIÈRE:\n"
        
        if fundamental_metrics.debt_to_equity:
            prompt += f"- Ratio D/E: {fundamental_metrics.debt_to_equity:.2f}\n"
        if fundamental_metrics.current_ratio:
            prompt += f"- Ratio de liquidité: {fundamental_metrics.current_ratio:.2f}\n"
        if fundamental_metrics.quick_ratio:
            prompt += f"- Ratio de liquidité immédiate: {fundamental_metrics.quick_ratio:.2f}\n"
        if fundamental_metrics.interest_coverage:
            prompt += f"- Couverture des intérêts: {fundamental_metrics.interest_coverage:.2f}\n"
        
        if (fundamental_metrics.dividend_yield or 
            fundamental_metrics.payout_ratio or 
            fundamental_metrics.dividend_growth):
            prompt += "\nDIVIDENDES:\n"
            if fundamental_metrics.dividend_yield:
                prompt += f"- Rendement: {fundamental_metrics.dividend_yield:.2f}%\n"
            if fundamental_metrics.payout_ratio:
                prompt += f"- Taux de distribution: {fundamental_metrics.payout_ratio:.2f}%\n"
            if fundamental_metrics.dividend_growth:
                prompt += f"- Croissance dividende: {fundamental_metrics.dividend_growth:.2f}%\n"
        
        prompt += f"""
CONSIGNES D'ANALYSE:
1. Évalue la valorisation de l'entreprise (sous-évaluée, correcte, surévaluée)
2. Analyse la santé financière et la profitabilité
3. Évalue les perspectives de croissance
4. Compare aux pairs du secteur {sector_context or 'si applicable'}
5. Identifie les forces et faiblesses fondamentales
6. Détermine la qualité du management et du modèle économique
7. Évalue les risques fondamentaux

RÉPONSE ATTENDUE:
- Valorisation: sous-évaluée/correcte/surévaluée
- Score fondamental (0.0 à 1.0)
- Points forts (3 maximum)
- Points faibles (3 maximum)
- Catalyseurs fondamentaux
- Risques principaux
- Prix cible justifié

Format ta réponse de manière structurée et professionnelle en français."""
        
        return prompt
    
    @staticmethod
    def create_sentiment_analysis_prompt(
        market_context: MarketContext,
        sentiment_data: SentimentData,
        recent_news: Optional[List[str]] = None
    ) -> str:
        """Crée un prompt pour l'analyse de sentiment."""
        
        symbol = market_context.symbol
        
        prompt = f"""Tu es un expert en analyse de sentiment financier. Analyse le sentiment autour de l'action {symbol}.

DONNÉES DE SENTIMENT:

NOUVELLES:
- Sentiment général: {sentiment_data.news_sentiment.value}
- Score nouvelles: {sentiment_data.news_score:.3f} (-1 à +1)
- Nombre d'articles: {sentiment_data.news_count}
"""
        
        if sentiment_data.analyst_sentiment:
            prompt += f"""
ANALYSTES:
- Sentiment analystes: {sentiment_data.analyst_sentiment.value}
- Upgrades récents: {sentiment_data.analyst_upgrades}
- Downgrades récents: {sentiment_data.analyst_downgrades}
"""
            if sentiment_data.analyst_target_price:
                prompt += f"- Prix cible consensus: {sentiment_data.analyst_target_price}$\n"
        
        if sentiment_data.social_sentiment:
            prompt += f"""
SENTIMENT SOCIAL/RETAIL:
- Sentiment social: {sentiment_data.social_sentiment.value}
- Mentions: {sentiment_data.social_mentions}
"""
            if sentiment_data.social_score:
                prompt += f"- Score social: {sentiment_data.social_score:.3f}\n"
        
        if (sentiment_data.fear_greed_index or 
            sentiment_data.vix_level or 
            sentiment_data.put_call_ratio):
            prompt += "\nINDICATEURS DE MARCHÉ:\n"
            if sentiment_data.fear_greed_index:
                prompt += f"- Fear & Greed Index: {sentiment_data.fear_greed_index}/100\n"
            if sentiment_data.vix_level:
                prompt += f"- VIX: {sentiment_data.vix_level:.2f}\n"
            if sentiment_data.put_call_ratio:
                prompt += f"- Put/Call Ratio: {sentiment_data.put_call_ratio:.3f}\n"
        
        if recent_news:
            prompt += "\nNOUVELLES RÉCENTES:\n"
            for i, news in enumerate(recent_news[:5], 1):
                prompt += f"{i}. {news}\n"
        
        prompt += f"""
CONSIGNES D'ANALYSE:
1. Évalue le sentiment global (très négatif à très positif)
2. Analyse la cohérence entre les différentes sources
3. Identifie les catalyseurs de sentiment
4. Détermine l'impact probable sur le prix
5. Évalue la durabilité du sentiment actuel
6. Compare au sentiment historique si possible
7. Identifie les risques de retournement

RÉPONSE ATTENDUE:
- Sentiment global: EXTREMELY_FEARFUL, FEARFUL, NEUTRAL, GREEDY, EXTREMELY_GREEDY
- Score de sentiment (-1.0 à +1.0)
- Facteurs positifs principaux
- Facteurs négatifs principaux
- Catalyseurs de changement de sentiment
- Impact probable sur le prix (court terme)
- Signaux d'alerte à surveiller

Analyse précise et nuancée en français."""
        
        return prompt
    
    @staticmethod
    def create_risk_analysis_prompt(
        market_context: MarketContext,
        volatility_data: Optional[Dict[str, float]] = None,
        correlation_data: Optional[Dict[str, float]] = None,
        market_conditions: Optional[str] = None
    ) -> str:
        """Crée un prompt pour l'analyse de risque."""
        
        symbol = market_context.symbol
        current_price = market_context.current_price
        
        prompt = f"""Tu es un expert en gestion des risques financiers. Analyse les risques de l'action {symbol}.

DONNÉES DE BASE:
- Symbole: {symbol}
- Prix actuel: {current_price}$
- Conditions de marché: {market_conditions or 'Non spécifiées'}

VOLATILITÉ ET MOUVEMENT DE PRIX:
- Variation 24h: {market_context.price_change_24h or 'N/A'}%
- Variation 7j: {market_context.price_change_7d or 'N/A'}%
- Variation 30j: {market_context.price_change_30d or 'N/A'}%
"""
        
        if volatility_data:
            prompt += "\nDONNÉES DE VOLATILITÉ:\n"
            for period, vol in volatility_data.items():
                prompt += f"- Volatilité {period}: {vol:.2f}%\n"
        
        if correlation_data:
            prompt += "\nCORRÉLATIONS:\n"
            for asset, corr in correlation_data.items():
                prompt += f"- Corrélation avec {asset}: {corr:.3f}\n"
        
        # Indicateurs techniques liés au risque
        if market_context.moving_avg_50 and market_context.moving_avg_200:
            ma50 = market_context.moving_avg_50
            ma200 = market_context.moving_avg_200
            prompt += f"""
POSITION vs MOYENNES MOBILES:
- Distance MM50: {((current_price - ma50) / ma50 * 100):.2f}%
- Distance MM200: {((current_price - ma200) / ma200 * 100):.2f}%
- Configuration: {"Haussière" if ma50 > ma200 else "Baissière"}
"""
        
        if (market_context.bollinger_upper and 
            market_context.bollinger_lower):
            bb_upper = market_context.bollinger_upper
            bb_lower = market_context.bollinger_lower
            bb_width = (bb_upper - bb_lower) / current_price * 100
            prompt += f"- Largeur Bollinger: {bb_width:.2f}% (volatilité)\n"
        
        prompt += f"""
CONSIGNES D'ANALYSE DES RISQUES:
1. Évalue le risque de volatilité (mouvements de prix importants)
2. Analyse le risque de liquidité (capacité à entrer/sortir)
3. Détermine le risque de corrélation (dépendance aux marchés)
4. Évalue les risques spécifiques à l'entreprise
5. Identifie les risques macroéconomiques
6. Analyse les risques techniques (niveaux de support)
7. Détermine les risques de sentiment/psychologiques

TYPES DE RISQUES À ÉVALUER:
- Risque de marché
- Risque de crédit/défaut
- Risque de liquidité
- Risque opérationnel
- Risque réglementaire
- Risque géopolitique
- Risque de change (si applicable)

RÉPONSE ATTENDUE:
- Niveau de risque global: VERY_LOW, LOW, MODERATE, HIGH, VERY_HIGH
- Principaux risques identifiés (par ordre d'importance)
- Probabilité et impact de chaque risque
- Niveaux de stop-loss suggérés
- Signaux d'alerte à surveiller
- Mesures de mitigation recommandées
- Score de risque/récompense

Analyse complète et objective en français."""
        
        return prompt
    
    @staticmethod
    def create_market_overview_prompt(
        market_indices: Dict[str, float],
        sector_performance: Dict[str, float],
        economic_indicators: Optional[Dict[str, Any]] = None,
        key_events: Optional[List[str]] = None
    ) -> str:
        """Crée un prompt pour une vue d'ensemble du marché."""
        
        prompt = """Tu es un analyste de marché senior. Fournis une vue d'ensemble complète des marchés financiers.

INDICES PRINCIPAUX:
"""
        
        for index, change in market_indices.items():
            direction = "↗️" if change > 0 else "↘️" if change < 0 else "→"
            prompt += f"- {index}: {change:+.2f}% {direction}\n"
        
        prompt += "\nPERFORMANCE SECTORIELLE:\n"
        
        # Trie les secteurs par performance
        sorted_sectors = sorted(sector_performance.items(), key=lambda x: x[1], reverse=True)
        
        for sector, perf in sorted_sectors:
            direction = "🟢" if perf > 1 else "🔴" if perf < -1 else "🟡"
            prompt += f"- {sector}: {perf:+.2f}% {direction}\n"
        
        if economic_indicators:
            prompt += "\nINDICATEURS ÉCONOMIQUES:\n"
            for indicator, value in economic_indicators.items():
                prompt += f"- {indicator}: {value}\n"
        
        if key_events:
            prompt += "\nÉVÉNEMENTS CLÉS:\n"
            for event in key_events:
                prompt += f"- {event}\n"
        
        prompt += """
CONSIGNES D'ANALYSE:
1. Analyse le sentiment général du marché
2. Identifie les thèmes dominants
3. Évalue les opportunités sectorielles
4. Détermine les risques macroéconomiques
5. Identifie les catalyseurs court/moyen terme
6. Évalue l'environnement de volatilité
7. Donne une perspective temporelle (court/moyen/long terme)

RÉPONSE ATTENDUE:
- Sentiment de marché global
- Thèmes d'investissement dominants
- Secteurs à privilégier/éviter
- Niveau de risque général
- Catalyseurs à surveiller
- Recommandations stratégiques
- Outlook temporel

Vue d'ensemble structurée et actionnable en français."""
        
        return prompt