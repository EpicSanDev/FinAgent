"""
Service d'analyse de sentiment avancée par IA.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

import structlog

from ..models import (
    AIRequest,
    AIResponse,
    AIProvider,
    ModelType,
    MarketContext,
    SentimentData,
    MarketSentiment,
    AnalysisResult,
    AnalysisType,
    TrendDirection,
    ConfidenceLevel,
    RiskLevel,
    AIError,
)
from ..prompts import (
    PromptManager,
    PromptContext,
    PromptType,
)

logger = structlog.get_logger(__name__)


class SentimentService:
    """Service d'analyse de sentiment approfondie utilisant l'IA."""
    
    def __init__(
        self,
        ai_provider: AIProvider,
        prompt_manager: PromptManager,
        default_model: ModelType = ModelType.CLAUDE_3_SONNET
    ):
        self.ai_provider = ai_provider
        self.prompt_manager = prompt_manager
        self.default_model = default_model
        
        self.logger = logger.bind(service="sentiment")
    
    async def analyze_comprehensive_sentiment(
        self,
        market_context: MarketContext,
        sentiment_data: SentimentData,
        recent_news: Optional[List[str]] = None,
        social_mentions: Optional[List[str]] = None,
        analyst_reports: Optional[List[str]] = None
    ) -> AnalysisResult:
        """Analyse complète et approfondie du sentiment."""
        
        symbol = market_context.symbol
        
        self.logger.info(
            "Analyse sentiment complète",
            symbol=symbol,
            news_count=sentiment_data.news_count,
            social_mentions=sentiment_data.social_mentions
        )
        
        try:
            # Création du contexte enrichi
            enriched_context = await self._create_enriched_context(
                market_context,
                sentiment_data,
                recent_news,
                social_mentions,
                analyst_reports
            )
            
            # Génération du prompt contextuel
            prompt = self.prompt_manager.generate_prompt(
                PromptType.SENTIMENT_ANALYSIS,
                enriched_context
            )
            
            # Requête à l'IA avec modèle optimisé pour sentiment
            ai_request = AIRequest(
                model_type=ModelType.CLAUDE_3_SONNET,  # Bon pour nuances de sentiment
                prompt=prompt,
                temperature=0.4,  # Un peu plus créatif pour interpréter les nuances
                max_tokens=3500
            )
            
            ai_response = await self.ai_provider.send_request(ai_request)
            
            # Parsing et structuration de l'analyse
            analysis_result = await self._parse_sentiment_analysis(
                market_context,
                sentiment_data,
                ai_response
            )
            
            self.logger.info(
                "Analyse sentiment terminée",
                symbol=symbol,
                sentiment_score=analysis_result.sentiment_score,
                confidence=analysis_result.confidence.value,
                tokens_used=ai_response.tokens_used
            )
            
            return analysis_result
            
        except Exception as e:
            self.logger.error(
                "Erreur analyse sentiment",
                symbol=symbol,
                error=str(e)
            )
            raise AIError(f"Erreur lors de l'analyse de sentiment: {str(e)}")
    
    async def analyze_news_sentiment(
        self,
        symbol: str,
        news_articles: List[Dict[str, Any]],
        time_decay_hours: int = 24
    ) -> Tuple[MarketSentiment, float, List[str]]:
        """Analyse le sentiment des nouvelles avec pondération temporelle."""
        
        if not news_articles:
            return MarketSentiment.NEUTRAL, 0.0, []
        
        # Filtre et pondère les nouvelles par âge
        weighted_articles = []
        now = datetime.utcnow()
        
        for article in news_articles:
            article_time = article.get('published_at', now)
            if isinstance(article_time, str):
                try:
                    article_time = datetime.fromisoformat(article_time.replace('Z', '+00:00'))
                except:
                    article_time = now
            
            hours_old = (now - article_time).total_seconds() / 3600
            if hours_old <= time_decay_hours:
                # Pondération décroissante avec l'âge
                weight = max(0.1, 1.0 - (hours_old / time_decay_hours))
                weighted_articles.append({
                    'content': article.get('title', '') + ' ' + article.get('summary', ''),
                    'weight': weight,
                    'source': article.get('source', 'Unknown')
                })
        
        if not weighted_articles:
            return MarketSentiment.NEUTRAL, 0.0, []
        
        # Analyse chaque article
        sentiment_scores = []
        key_themes = []
        
        for article in weighted_articles[:10]:  # Limite à 10 articles les plus récents
            try:
                score, themes = await self._analyze_single_news_item(
                    symbol,
                    article['content']
                )
                sentiment_scores.append(score * article['weight'])
                key_themes.extend(themes)
                
                # Pause pour éviter le rate limiting
                await asyncio.sleep(0.1)
                
            except Exception as e:
                self.logger.warning(
                    "Erreur analyse article individuel",
                    error=str(e)
                )
                continue
        
        # Calcul du sentiment global
        if sentiment_scores:
            avg_score = sum(sentiment_scores) / len(sentiment_scores)
            overall_sentiment = self._score_to_sentiment(avg_score)
            
            # Déduplication des thèmes
            unique_themes = list(set(key_themes))[:5]
            
            return overall_sentiment, avg_score, unique_themes
        
        return MarketSentiment.NEUTRAL, 0.0, []
    
    async def analyze_social_sentiment(
        self,
        symbol: str,
        social_mentions: List[Dict[str, Any]],
        platform_weights: Optional[Dict[str, float]] = None
    ) -> Tuple[MarketSentiment, float, Dict[str, Any]]:
        """Analyse le sentiment des réseaux sociaux."""
        
        if not social_mentions:
            return MarketSentiment.NEUTRAL, 0.0, {}
        
        # Poids par défaut selon la plateforme
        if not platform_weights:
            platform_weights = {
                'twitter': 1.0,
                'reddit': 0.8,
                'discord': 0.6,
                'telegram': 0.5,
                'stocktwits': 1.2,  # Plus pertinent pour finance
                'fintwit': 1.3
            }
        
        # Analyse par plateforme
        platform_analysis = {}
        weighted_scores = []
        
        for mention in social_mentions[:50]:  # Limite pour performance
            platform = mention.get('platform', 'unknown').lower()
            weight = platform_weights.get(platform, 0.5)
            
            if platform not in platform_analysis:
                platform_analysis[platform] = {
                    'count': 0,
                    'total_score': 0.0,
                    'engagement': 0
                }
            
            # Analyse du contenu
            content = mention.get('content', '')
            engagement = mention.get('engagement', {})
            
            try:
                sentiment_score = await self._analyze_social_mention(symbol, content)
                
                # Pondération par engagement et plateforme
                engagement_weight = self._calculate_engagement_weight(engagement)
                final_weight = weight * engagement_weight
                
                weighted_scores.append(sentiment_score * final_weight)
                
                platform_analysis[platform]['count'] += 1
                platform_analysis[platform]['total_score'] += sentiment_score
                platform_analysis[platform]['engagement'] += engagement_weight
                
            except Exception as e:
                self.logger.warning(
                    "Erreur analyse mention sociale",
                    platform=platform,
                    error=str(e)
                )
                continue
        
        # Calcul du sentiment global
        if weighted_scores:
            avg_score = sum(weighted_scores) / len(weighted_scores)
            overall_sentiment = self._score_to_sentiment(avg_score)
            
            # Normalise les scores par plateforme
            for platform in platform_analysis:
                if platform_analysis[platform]['count'] > 0:
                    platform_analysis[platform]['avg_score'] = (
                        platform_analysis[platform]['total_score'] / 
                        platform_analysis[platform]['count']
                    )
                    platform_analysis[platform]['avg_engagement'] = (
                        platform_analysis[platform]['engagement'] / 
                        platform_analysis[platform]['count']
                    )
            
            return overall_sentiment, avg_score, platform_analysis
        
        return MarketSentiment.NEUTRAL, 0.0, {}
    
    async def detect_sentiment_anomalies(
        self,
        symbol: str,
        current_sentiment: SentimentData,
        historical_baseline: Optional[List[SentimentData]] = None
    ) -> Dict[str, Any]:
        """Détecte les anomalies de sentiment par rapport à la baseline."""
        
        anomalies = {
            'detected': False,
            'severity': 'low',
            'anomaly_types': [],
            'confidence': 0.0,
            'recommendations': []
        }
        
        if not historical_baseline:
            return anomalies
        
        # Calcul de la baseline
        baseline_news = sum(data.news_score for data in historical_baseline) / len(historical_baseline)
        baseline_social = sum(data.social_score or 0 for data in historical_baseline if data.social_score) / len([d for d in historical_baseline if d.social_score])
        
        # Seuils d'anomalie
        news_threshold = 0.3  # Changement de 30%+
        social_threshold = 0.4  # Changement de 40%+
        volume_threshold = 2.0  # 2x le volume normal
        
        # Détection d'anomalies
        news_change = abs(current_sentiment.news_score - baseline_news)
        social_change = abs((current_sentiment.social_score or 0) - baseline_social) if current_sentiment.social_score else 0
        
        # Volume anormal de mentions
        baseline_mentions = sum(data.social_mentions for data in historical_baseline) / len(historical_baseline)
        mention_ratio = current_sentiment.social_mentions / max(1, baseline_mentions)
        
        # Analyse des anomalies
        if news_change > news_threshold:
            anomalies['detected'] = True
            anomalies['anomaly_types'].append({
                'type': 'news_sentiment_spike',
                'magnitude': news_change,
                'direction': 'positive' if current_sentiment.news_score > baseline_news else 'negative'
            })
        
        if social_change > social_threshold:
            anomalies['detected'] = True
            anomalies['anomaly_types'].append({
                'type': 'social_sentiment_anomaly',
                'magnitude': social_change,
                'direction': 'positive' if (current_sentiment.social_score or 0) > baseline_social else 'negative'
            })
        
        if mention_ratio > volume_threshold:
            anomalies['detected'] = True
            anomalies['anomaly_types'].append({
                'type': 'mention_volume_spike',
                'ratio': mention_ratio,
                'current': current_sentiment.social_mentions,
                'baseline': baseline_mentions
            })
        
        # Calcul de la sévérité
        if anomalies['detected']:
            max_magnitude = max([
                news_change / news_threshold,
                social_change / social_threshold,
                mention_ratio / volume_threshold
            ])
            
            if max_magnitude > 3.0:
                anomalies['severity'] = 'critical'
            elif max_magnitude > 2.0:
                anomalies['severity'] = 'high'
            elif max_magnitude > 1.5:
                anomalies['severity'] = 'medium'
            
            anomalies['confidence'] = min(1.0, max_magnitude / 3.0)
            
            # Recommandations
            anomalies['recommendations'] = await self._generate_anomaly_recommendations(
                symbol,
                anomalies['anomaly_types'],
                anomalies['severity']
            )
        
        return anomalies
    
    async def track_sentiment_momentum(
        self,
        symbol: str,
        sentiment_history: List[Tuple[datetime, SentimentData]],
        lookback_days: int = 7
    ) -> Dict[str, Any]:
        """Analyse le momentum du sentiment."""
        
        if len(sentiment_history) < 3:
            return {'momentum': 'insufficient_data'}
        
        # Filtre par période
        cutoff_date = datetime.utcnow() - timedelta(days=lookback_days)
        recent_data = [(dt, data) for dt, data in sentiment_history if dt >= cutoff_date]
        
        if len(recent_data) < 3:
            return {'momentum': 'insufficient_recent_data'}
        
        # Calcul des tendances
        news_scores = [data.news_score for _, data in recent_data]
        social_scores = [data.social_score or 0 for _, data in recent_data if data.social_score]
        
        # Régression linéaire simple pour la tendance
        news_trend = self._calculate_trend(news_scores)
        social_trend = self._calculate_trend(social_scores) if social_scores else 0
        
        # Volatilité du sentiment
        news_volatility = self._calculate_volatility(news_scores)
        social_volatility = self._calculate_volatility(social_scores) if social_scores else 0
        
        # Classification du momentum
        momentum_strength = abs(news_trend) + abs(social_trend)
        
        if momentum_strength > 0.02:  # 2% par jour
            momentum = 'strong_' + ('positive' if news_trend + social_trend > 0 else 'negative')
        elif momentum_strength > 0.01:  # 1% par jour
            momentum = 'moderate_' + ('positive' if news_trend + social_trend > 0 else 'negative')
        elif momentum_strength > 0.005:  # 0.5% par jour
            momentum = 'weak_' + ('positive' if news_trend + social_trend > 0 else 'negative')
        else:
            momentum = 'stable'
        
        return {
            'momentum': momentum,
            'news_trend': news_trend,
            'social_trend': social_trend,
            'news_volatility': news_volatility,
            'social_volatility': social_volatility,
            'momentum_strength': momentum_strength,
            'data_points': len(recent_data),
            'lookback_days': lookback_days
        }
    
    async def _create_enriched_context(
        self,
        market_context: MarketContext,
        sentiment_data: SentimentData,
        recent_news: Optional[List[str]],
        social_mentions: Optional[List[str]],
        analyst_reports: Optional[List[str]]
    ) -> PromptContext:
        """Crée un contexte enrichi pour l'analyse de sentiment."""
        
        custom_context = {}
        
        if recent_news:
            custom_context['recent_news'] = recent_news[:10]  # Limite à 10
        
        if social_mentions:
            custom_context['social_mentions'] = social_mentions[:20]  # Limite à 20
        
        if analyst_reports:
            custom_context['analyst_reports'] = analyst_reports[:5]  # Limite à 5
        
        return PromptContext(
            market_context=market_context,
            sentiment_data=sentiment_data,
            custom_context=custom_context,
            detail_level="detailed"  # Plus de détails pour sentiment
        )
    
    async def _analyze_single_news_item(
        self,
        symbol: str,
        content: str
    ) -> Tuple[float, List[str]]:
        """Analyse le sentiment d'un article individuel."""
        
        # Prompt simple pour analyse d'article
        prompt = f"""Analyse le sentiment de cette nouvelle concernant {symbol}:

"{content}"

Réponds avec:
1. Score de sentiment (-1.0 à +1.0)
2. Thèmes principaux (max 3)

Format: SCORE: X.X | THEMES: theme1, theme2, theme3"""
        
        ai_request = AIRequest(
            model_type=ModelType.CLAUDE_3_HAIKU,  # Rapide pour analyse simple
            prompt=prompt,
            temperature=0.2,
            max_tokens=200
        )
        
        try:
            ai_response = await self.ai_provider.send_request(ai_request)
            return self._parse_simple_sentiment_response(ai_response.content)
        except Exception:
            return 0.0, []  # Neutral par défaut en cas d'erreur
    
    async def _analyze_social_mention(self, symbol: str, content: str) -> float:
        """Analyse le sentiment d'une mention sociale."""
        
        # Analyse plus simple pour mentions sociales
        positive_words = ['bull', 'buy', 'moon', 'rocket', 'up', 'gain', 'profit', 'good', 'great', 'amazing']
        negative_words = ['bear', 'sell', 'dump', 'crash', 'down', 'loss', 'bad', 'terrible', 'awful']
        
        content_lower = content.lower()
        
        positive_count = sum(1 for word in positive_words if word in content_lower)
        negative_count = sum(1 for word in negative_words if word in content_lower)
        
        if positive_count + negative_count == 0:
            return 0.0
        
        score = (positive_count - negative_count) / (positive_count + negative_count)
        return max(-1.0, min(1.0, score))
    
    def _calculate_engagement_weight(self, engagement: Dict[str, Any]) -> float:
        """Calcule le poids basé sur l'engagement."""
        
        likes = engagement.get('likes', 0)
        shares = engagement.get('shares', 0)
        comments = engagement.get('comments', 0)
        
        # Score d'engagement simple
        engagement_score = likes + shares * 2 + comments * 3
        
        # Normalise sur une échelle 0.1 à 2.0
        return max(0.1, min(2.0, 1.0 + engagement_score / 100))
    
    def _score_to_sentiment(self, score: float) -> MarketSentiment:
        """Convertit un score numérique en sentiment de marché."""
        
        if score > 0.6:
            return MarketSentiment.EXTREMELY_GREEDY
        elif score > 0.2:
            return MarketSentiment.GREEDY
        elif score < -0.6:
            return MarketSentiment.EXTREMELY_FEARFUL
        elif score < -0.2:
            return MarketSentiment.FEARFUL
        else:
            return MarketSentiment.NEUTRAL
    
    def _calculate_trend(self, values: List[float]) -> float:
        """Calcule la tendance linéaire simple."""
        
        if len(values) < 2:
            return 0.0
        
        n = len(values)
        x_values = list(range(n))
        
        # Régression linéaire simple
        x_mean = sum(x_values) / n
        y_mean = sum(values) / n
        
        numerator = sum((x_values[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0.0
        
        slope = numerator / denominator
        return slope
    
    def _calculate_volatility(self, values: List[float]) -> float:
        """Calcule la volatilité."""
        
        if len(values) < 2:
            return 0.0
        
        mean_val = sum(values) / len(values)
        variance = sum((val - mean_val) ** 2 for val in values) / len(values)
        return variance ** 0.5
    
    async def _generate_anomaly_recommendations(
        self,
        symbol: str,
        anomaly_types: List[Dict],
        severity: str
    ) -> List[str]:
        """Génère des recommandations basées sur les anomalies détectées."""
        
        recommendations = []
        
        for anomaly in anomaly_types:
            if anomaly['type'] == 'news_sentiment_spike':
                if anomaly['direction'] == 'positive':
                    recommendations.append("Surveiller une potentielle sur-réaction positive")
                else:
                    recommendations.append("Évaluer les risques de baisse supplémentaire")
            
            elif anomaly['type'] == 'social_sentiment_anomaly':
                recommendations.append("Analyser les discussions sur les réseaux sociaux")
                
            elif anomaly['type'] == 'mention_volume_spike':
                recommendations.append("Identifier la cause du pic d'attention")
        
        if severity == 'critical':
            recommendations.append("Considérer une révision urgente de la position")
        elif severity == 'high':
            recommendations.append("Surveiller étroitement l'évolution")
        
        return recommendations
    
    def _parse_simple_sentiment_response(self, content: str) -> Tuple[float, List[str]]:
        """Parse une réponse simple d'analyse de sentiment."""
        
        import re
        
        # Extrait le score
        score_match = re.search(r'SCORE:\s*([+-]?\d+(?:\.\d+)?)', content)
        score = float(score_match.group(1)) if score_match else 0.0
        
        # Extrait les thèmes
        themes_match = re.search(r'THEMES:\s*(.+)', content)
        themes = []
        if themes_match:
            themes_text = themes_match.group(1)
            themes = [theme.strip() for theme in themes_text.split(',')][:3]
        
        return score, themes
    
    async def _parse_sentiment_analysis(
        self,
        market_context: MarketContext,
        sentiment_data: SentimentData,
        ai_response: AIResponse
    ) -> AnalysisResult:
        """Parse l'analyse complète de sentiment."""
        
        content = ai_response.content
        
        # Extraction du sentiment global
        overall_sentiment = self._extract_overall_sentiment(content)
        confidence = self._extract_confidence_from_content(content)
        risk_level = self._extract_risk_level_from_content(content)
        
        # Score de sentiment numérique
        sentiment_score = self._extract_sentiment_score_from_content(content)
        
        # Facteurs clés
        positive_factors = self._extract_factors(content, 'positif', 'optimiste', 'hausse')
        negative_factors = self._extract_factors(content, 'négatif', 'pessimiste', 'baisse')
        
        return AnalysisResult(
            request_id=uuid4(),
            analysis_type=AnalysisType.SENTIMENT,
            symbol=market_context.symbol,
            overall_trend=self._sentiment_to_trend(overall_sentiment),
            confidence=confidence,
            risk_level=risk_level,
            sentiment_analysis=content,
            sentiment_score=sentiment_score,
            key_drivers=positive_factors,
            risk_factors=negative_factors,
            processing_time=ai_response.processing_time,
            model_used=ai_response.model_used or "unknown",
            tokens_used=ai_response.tokens_used
        )
    
    def _extract_overall_sentiment(self, content: str) -> MarketSentiment:
        """Extrait le sentiment global du contenu."""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ['extrêmement positif', 'très optimiste', 'extremely greedy']):
            return MarketSentiment.EXTREMELY_GREEDY
        elif any(word in content_lower for word in ['positif', 'optimiste', 'greedy']):
            return MarketSentiment.GREEDY
        elif any(word in content_lower for word in ['extrêmement négatif', 'très pessimiste', 'extremely fearful']):
            return MarketSentiment.EXTREMELY_FEARFUL
        elif any(word in content_lower for word in ['négatif', 'pessimiste', 'fearful']):
            return MarketSentiment.FEARFUL
        else:
            return MarketSentiment.NEUTRAL
    
    def _sentiment_to_trend(self, sentiment: MarketSentiment) -> TrendDirection:
        """Convertit le sentiment en direction de tendance."""
        mapping = {
            MarketSentiment.EXTREMELY_GREEDY: TrendDirection.STRONG_BULLISH,
            MarketSentiment.GREEDY: TrendDirection.BULLISH,
            MarketSentiment.NEUTRAL: TrendDirection.NEUTRAL,
            MarketSentiment.FEARFUL: TrendDirection.BEARISH,
            MarketSentiment.EXTREMELY_FEARFUL: TrendDirection.STRONG_BEARISH,
        }
        return mapping.get(sentiment, TrendDirection.NEUTRAL)
    
    def _extract_confidence_from_content(self, content: str) -> ConfidenceLevel:
        """Extrait le niveau de confiance."""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ['très élevé', 'very high', 'très haute']):
            return ConfidenceLevel.VERY_HIGH
        elif any(word in content_lower for word in ['élevé', 'high', 'haute']):
            return ConfidenceLevel.HIGH
        elif any(word in content_lower for word in ['faible', 'low', 'basse']):
            return ConfidenceLevel.LOW
        elif any(word in content_lower for word in ['très faible', 'very low']):
            return ConfidenceLevel.VERY_LOW
        else:
            return ConfidenceLevel.MEDIUM
    
    def _extract_risk_level_from_content(self, content: str) -> RiskLevel:
        """Extrait le niveau de risque."""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ['très élevé', 'very high', 'critique']):
            return RiskLevel.VERY_HIGH
        elif any(word in content_lower for word in ['élevé', 'high']):
            return RiskLevel.HIGH
        elif any(word in content_lower for word in ['faible', 'low']):
            return RiskLevel.LOW
        elif any(word in content_lower for word in ['très faible', 'very low', 'minimal']):
            return RiskLevel.VERY_LOW
        else:
            return RiskLevel.MODERATE
    
    def _extract_sentiment_score_from_content(self, content: str) -> float:
        """Extrait le score de sentiment numérique."""
        import re
        
        patterns = [
            r'sentiment.*?score.*?([+-]?\d+(?:\.\d+)?)',
            r'score.*?([+-]?\d+(?:\.\d+)?)',
            r'([+-]?\d+(?:\.\d+)?).*?sentiment'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content.lower())
            if match:
                try:
                    score = float(match.group(1))
                    return max(-1.0, min(1.0, score))
                except:
                    continue
        
        return 0.0  # Neutre par défaut
    
    def _extract_factors(self, content: str, *keywords) -> List[str]:
        """Extrait les facteurs du contenu."""
        factors = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in keywords):
                if line.startswith('-') or line.startswith('•'):
                    factor = line[1:].strip()
                    if factor and len(factor) > 10:
                        factors.append(factor)
        
        return factors[:5]  # Max 5 facteurs