"""
Service d'analyse financière par IA.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

import structlog

from ..models import (
    AIRequest,
    AIResponse,
    AIProvider,
    ModelType,
    AnalysisRequest,
    AnalysisResult,
    AnalysisType,
    TrendDirection,
    ConfidenceLevel,
    RiskLevel,
    MarketContext,
    TechnicalIndicators,
    FundamentalMetrics,
    SentimentData,
    MarketOverview,
    AIError,
)
from ..prompts import (
    PromptManager,
    PromptContext,
    PromptType,
)
from ..providers import ClaudeProvider

logger = structlog.get_logger(__name__)


class AnalysisService:
    """Service d'analyse financière utilisant l'IA."""
    
    def __init__(
        self,
        ai_provider: AIProvider,
        prompt_manager: PromptManager,
        default_model: ModelType = ModelType.CLAUDE_3_SONNET
    ):
        self.ai_provider = ai_provider
        self.prompt_manager = prompt_manager
        self.default_model = default_model
        
        self.logger = logger.bind(service="analysis")
    
    async def analyze_financial_data(self, request: AnalysisRequest) -> AnalysisResult:
        """Analyse complète des données financières."""
        
        self.logger.info(
            "Début analyse financière",
            symbol=request.market_context.symbol,
            analysis_type=request.analysis_type.value,
            request_id=str(request.request_id)
        )
        
        try:
            # Sélection du modèle optimal selon le type d'analyse
            model = self._select_optimal_model(request.analysis_type)
            
            # Génération du prompt adapté
            prompt_context = self._create_prompt_context(request)
            prompt_type = self._get_prompt_type(request.analysis_type)
            
            prompt = self.prompt_manager.generate_prompt(prompt_type, prompt_context)
            
            # Requête à l'IA
            ai_request = AIRequest(
                model_type=model,
                prompt=prompt,
                context=self._create_ai_context(request),
                temperature=0.3,  # Faible pour analyses financières
                max_tokens=4000
            )
            
            ai_response = await self.ai_provider.send_request(ai_request)
            
            # Parsing et structuration de la réponse
            analysis_result = await self._parse_analysis_response(
                request,
                ai_response,
                model
            )
            
            self.logger.info(
                "Analyse terminée",
                symbol=request.market_context.symbol,
                trend=analysis_result.overall_trend.value,
                confidence=analysis_result.confidence.value,
                tokens_used=ai_response.tokens_used
            )
            
            return analysis_result
            
        except Exception as e:
            self.logger.error(
                "Erreur analyse financière",
                symbol=request.market_context.symbol,
                error=str(e),
                request_id=str(request.request_id)
            )
            raise AIError(f"Erreur lors de l'analyse financière: {str(e)}")
    
    async def technical_analysis(
        self,
        market_context: MarketContext,
        technical_indicators: TechnicalIndicators,
        time_horizon: str = "1d"
    ) -> AnalysisResult:
        """Analyse technique spécialisée."""
        
        request = AnalysisRequest(
            analysis_type=AnalysisType.TECHNICAL,
            market_context=market_context,
            technical_indicators=technical_indicators,
            time_horizon=time_horizon
        )
        
        return await self.analyze_financial_data(request)
    
    async def fundamental_analysis(
        self,
        market_context: MarketContext,
        fundamental_metrics: FundamentalMetrics,
        sector_context: Optional[str] = None
    ) -> AnalysisResult:
        """Analyse fondamentale spécialisée."""
        
        request = AnalysisRequest(
            analysis_type=AnalysisType.FUNDAMENTAL,
            market_context=market_context,
            fundamental_metrics=fundamental_metrics,
            custom_context={"sector_context": sector_context} if sector_context else None
        )
        
        return await self.analyze_financial_data(request)
    
    async def sentiment_analysis(
        self,
        market_context: MarketContext,
        sentiment_data: SentimentData,
        recent_news: Optional[List[str]] = None
    ) -> AnalysisResult:
        """Analyse de sentiment spécialisée."""
        
        custom_context = {}
        if recent_news:
            custom_context["recent_news"] = recent_news
        
        request = AnalysisRequest(
            analysis_type=AnalysisType.SENTIMENT,
            market_context=market_context,
            sentiment_data=sentiment_data,
            custom_context=custom_context if custom_context else None
        )
        
        return await self.analyze_financial_data(request)
    
    async def risk_analysis(
        self,
        market_context: MarketContext,
        volatility_data: Optional[Dict[str, float]] = None,
        correlation_data: Optional[Dict[str, float]] = None,
        market_conditions: Optional[str] = None
    ) -> AnalysisResult:
        """Analyse de risque spécialisée."""
        
        custom_context = {}
        if volatility_data:
            custom_context["volatility_data"] = volatility_data
        if correlation_data:
            custom_context["correlation_data"] = correlation_data
        
        request = AnalysisRequest(
            analysis_type=AnalysisType.RISK,
            market_context=market_context,
            custom_context=custom_context if custom_context else None
        )
        
        return await self.analyze_financial_data(request)
    
    async def market_overview_analysis(
        self,
        market_indices: Dict[str, float],
        sector_performance: Dict[str, float],
        economic_indicators: Optional[Dict[str, Any]] = None,
        key_events: Optional[List[str]] = None
    ) -> MarketOverview:
        """Analyse vue d'ensemble du marché."""
        
        # Crée un contexte de marché fictif pour la vue d'ensemble
        market_context = MarketContext(
            symbol="MARKET",
            current_price=100.0,  # Valeur fictive
            analysis_timestamp=datetime.utcnow()
        )
        
        # Prépare le contexte personnalisé
        custom_context = {
            "market_indices": market_indices,
            "sector_performance": sector_performance,
        }
        if economic_indicators:
            custom_context["economic_indicators"] = economic_indicators
        if key_events:
            custom_context["key_events"] = key_events
        
        # Génère le prompt pour vue d'ensemble
        prompt_context = PromptContext(
            market_context=market_context,
            custom_context=custom_context
        )
        
        prompt = self.prompt_manager.generate_prompt(
            PromptType.MARKET_OVERVIEW,
            prompt_context
        )
        
        # Utilise Claude 3.5 Sonnet pour les analyses complexes
        ai_request = AIRequest(
            model_type=ModelType.CLAUDE_3_5_SONNET,
            prompt=prompt,
            temperature=0.4,
            max_tokens=3000
        )
        
        ai_response = await self.ai_provider.send_request(ai_request)
        
        # Parse la réponse en MarketOverview
        return await self._parse_market_overview_response(
            ai_response,
            market_indices,
            sector_performance
        )
    
    async def multi_timeframe_analysis(
        self,
        market_context: MarketContext,
        technical_indicators: TechnicalIndicators,
        timeframes: List[str] = None
    ) -> Dict[str, AnalysisResult]:
        """Analyse sur plusieurs horizons temporels."""
        
        if not timeframes:
            timeframes = ["1h", "1d", "1w", "1m"]
        
        tasks = []
        for timeframe in timeframes:
            task = self.technical_analysis(
                market_context,
                technical_indicators,
                timeframe
            )
            tasks.append((timeframe, task))
        
        results = {}
        for timeframe, task in tasks:
            try:
                result = await task
                results[timeframe] = result
            except Exception as e:
                self.logger.error(
                    "Erreur analyse multi-timeframe",
                    timeframe=timeframe,
                    error=str(e)
                )
                continue
        
        return results
    
    def _select_optimal_model(self, analysis_type: AnalysisType) -> ModelType:
        """Sélectionne le modèle optimal selon le type d'analyse."""
        
        # Mapping des types d'analyse vers les modèles recommandés
        model_preferences = {
            AnalysisType.TECHNICAL: ModelType.CLAUDE_3_SONNET,      # Bon équilibre vitesse/qualité
            AnalysisType.FUNDAMENTAL: ModelType.CLAUDE_3_5_SONNET,  # Analyse approfondie
            AnalysisType.SENTIMENT: ModelType.CLAUDE_3_SONNET,      # Bon pour nuances
            AnalysisType.RISK: ModelType.CLAUDE_3_5_SONNET,         # Analyse complexe
            AnalysisType.MARKET_OVERVIEW: ModelType.CLAUDE_3_5_SONNET,  # Vue d'ensemble
            AnalysisType.SECTOR_ANALYSIS: ModelType.CLAUDE_3_OPUS,  # Le plus puissant
        }
        
        return model_preferences.get(analysis_type, self.default_model)
    
    def _get_prompt_type(self, analysis_type: AnalysisType) -> PromptType:
        """Convertit le type d'analyse en type de prompt."""
        
        mapping = {
            AnalysisType.TECHNICAL: PromptType.TECHNICAL_ANALYSIS,
            AnalysisType.FUNDAMENTAL: PromptType.FUNDAMENTAL_ANALYSIS,
            AnalysisType.SENTIMENT: PromptType.SENTIMENT_ANALYSIS,
            AnalysisType.RISK: PromptType.RISK_ANALYSIS,
            AnalysisType.MARKET_OVERVIEW: PromptType.MARKET_OVERVIEW,
        }
        
        return mapping.get(analysis_type, PromptType.TECHNICAL_ANALYSIS)
    
    def _create_prompt_context(self, request: AnalysisRequest) -> PromptContext:
        """Crée le contexte pour la génération de prompt."""
        
        return PromptContext(
            market_context=request.market_context,
            technical_indicators=request.technical_indicators,
            fundamental_metrics=request.fundamental_metrics,
            sentiment_data=request.sentiment_data,
            time_horizon=request.time_horizon,
            custom_context=request.custom_context or {}
        )
    
    def _create_ai_context(self, request: AnalysisRequest) -> Dict[str, Any]:
        """Crée le contexte pour la requête IA."""
        
        context = {
            "analysis_type": request.analysis_type.value,
            "symbol": request.market_context.symbol,
            "time_horizon": request.time_horizon,
        }
        
        if request.include_risk_analysis:
            context["include_risk"] = True
        if request.include_sector_comparison:
            context["include_sector"] = True
        
        return context
    
    async def _parse_analysis_response(
        self,
        request: AnalysisRequest,
        ai_response: AIResponse,
        model_used: ModelType
    ) -> AnalysisResult:
        """Parse et structure la réponse d'analyse."""
        
        content = ai_response.content
        
        # Extraction des informations structurées de la réponse
        # En pratique, il faudrait un parser plus sophistiqué
        # ou demander à l'IA de répondre en JSON structuré
        
        # Pour l'instant, utilise des valeurs par défaut et extrait ce qui est possible
        overall_trend = self._extract_trend(content)
        confidence = self._extract_confidence(content)
        risk_level = self._extract_risk_level(content)
        
        # Extraction des scores (simplified)
        bullish_score = self._extract_score(content, "bullish", "haussier")
        bearish_score = self._extract_score(content, "bearish", "baissier")
        
        # Extraction des niveaux de prix
        support_levels = self._extract_price_levels(content, "support")
        resistance_levels = self._extract_price_levels(content, "résistance", "resistance")
        
        # Extraction des facteurs clés
        key_drivers = self._extract_factors(content, "positif", "opportunité", "catalyseur")
        risk_factors = self._extract_factors(content, "risque", "négatif", "menace")
        
        return AnalysisResult(
            request_id=request.request_id,
            analysis_type=request.analysis_type,
            symbol=request.market_context.symbol,
            overall_trend=overall_trend,
            confidence=confidence,
            risk_level=risk_level,
            technical_analysis=content if request.analysis_type == AnalysisType.TECHNICAL else None,
            fundamental_analysis=content if request.analysis_type == AnalysisType.FUNDAMENTAL else None,
            sentiment_analysis=content if request.analysis_type == AnalysisType.SENTIMENT else None,
            risk_analysis=content if request.analysis_type == AnalysisType.RISK else None,
            bullish_score=bullish_score,
            bearish_score=bearish_score,
            support_levels=support_levels,
            resistance_levels=resistance_levels,
            key_drivers=key_drivers,
            risk_factors=risk_factors,
            processing_time=ai_response.processing_time,
            model_used=model_used.value,
            tokens_used=ai_response.tokens_used
        )
    
    async def _parse_market_overview_response(
        self,
        ai_response: AIResponse,
        market_indices: Dict[str, float],
        sector_performance: Dict[str, float]
    ) -> MarketOverview:
        """Parse la réponse de vue d'ensemble du marché."""
        
        content = ai_response.content
        
        # Extraction des informations
        overall_sentiment = self._extract_market_sentiment(content)
        volatility_level = self._extract_risk_level(content)
        
        # Secteurs leaders/perdants basés sur la performance
        sorted_sectors = sorted(sector_performance.items(), key=lambda x: x[1], reverse=True)
        leading_sectors = [sector for sector, _ in sorted_sectors[:3]]
        lagging_sectors = [sector for sector, _ in sorted_sectors[-3:]]
        
        return MarketOverview(
            market_session="regular",  # À déterminer selon l'heure
            overall_sentiment=overall_sentiment,
            volatility_level=volatility_level,
            leading_sectors=leading_sectors,
            lagging_sectors=lagging_sectors,
            market_summary=content,
            outlook=content,  # En pratique, extraire la section outlook
            key_themes=self._extract_themes(content)
        )
    
    def _extract_trend(self, content: str) -> TrendDirection:
        """Extrait la direction de tendance du contenu."""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ["très haussier", "strong bullish", "fortement haussier"]):
            return TrendDirection.STRONG_BULLISH
        elif any(word in content_lower for word in ["haussier", "bullish", "positif"]):
            return TrendDirection.BULLISH
        elif any(word in content_lower for word in ["très baissier", "strong bearish", "fortement baissier"]):
            return TrendDirection.STRONG_BEARISH
        elif any(word in content_lower for word in ["baissier", "bearish", "négatif"]):
            return TrendDirection.BEARISH
        else:
            return TrendDirection.NEUTRAL
    
    def _extract_confidence(self, content: str) -> ConfidenceLevel:
        """Extrait le niveau de confiance du contenu."""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ["très élevé", "very high", "très haute"]):
            return ConfidenceLevel.VERY_HIGH
        elif any(word in content_lower for word in ["élevé", "high", "haute"]):
            return ConfidenceLevel.HIGH
        elif any(word in content_lower for word in ["faible", "low", "basse"]):
            return ConfidenceLevel.LOW
        elif any(word in content_lower for word in ["très faible", "very low", "très basse"]):
            return ConfidenceLevel.VERY_LOW
        else:
            return ConfidenceLevel.MEDIUM
    
    def _extract_risk_level(self, content: str) -> RiskLevel:
        """Extrait le niveau de risque du contenu."""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ["très élevé", "very high", "critique"]):
            return RiskLevel.VERY_HIGH
        elif any(word in content_lower for word in ["élevé", "high"]):
            return RiskLevel.HIGH
        elif any(word in content_lower for word in ["faible", "low"]):
            return RiskLevel.LOW
        elif any(word in content_lower for word in ["très faible", "very low", "minimal"]):
            return RiskLevel.VERY_LOW
        else:
            return RiskLevel.MODERATE
    
    def _extract_score(self, content: str, *keywords) -> float:
        """Extrait un score numérique du contenu."""
        # Implémentation simplifiée - en pratique utiliser regex ou NLP
        import re
        
        for keyword in keywords:
            pattern = rf"{keyword}.*?(\d+(?:\.\d+)?)"
            match = re.search(pattern, content.lower())
            if match:
                try:
                    score = float(match.group(1))
                    return min(1.0, score / 100 if score > 1 else score)
                except:
                    continue
        
        return 0.5  # Valeur par défaut
    
    def _extract_price_levels(self, content: str, *keywords) -> List[float]:
        """Extrait les niveaux de prix du contenu."""
        import re
        
        levels = []
        for keyword in keywords:
            # Cherche des patterns comme "support à 150.5$" ou "résistance 200$"
            pattern = rf"{keyword}.*?(\d+(?:\.\d+)?)\$?"
            matches = re.finditer(pattern, content.lower())
            for match in matches:
                try:
                    level = float(match.group(1))
                    if level not in levels and level > 0:
                        levels.append(level)
                except:
                    continue
        
        return sorted(levels)[:3]  # Max 3 niveaux
    
    def _extract_factors(self, content: str, *keywords) -> List[str]:
        """Extrait les facteurs clés du contenu."""
        import re
        
        factors = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in keywords):
                # Nettoie et extrait le facteur
                if line.startswith('-') or line.startswith('•'):
                    factor = line[1:].strip()
                    if factor and len(factor) > 10:  # Filtre les entrées trop courtes
                        factors.append(factor)
        
        return factors[:5]  # Max 5 facteurs
    
    def _extract_market_sentiment(self, content: str):
        """Extrait le sentiment de marché du contenu."""
        from ..models import MarketSentiment
        
        content_lower = content.lower()
        
        if any(word in content_lower for word in ["extremely greedy", "extrêmement optimiste"]):
            return MarketSentiment.EXTREMELY_GREEDY
        elif any(word in content_lower for word in ["greedy", "optimiste", "cupide"]):
            return MarketSentiment.GREEDY
        elif any(word in content_lower for word in ["extremely fearful", "extrêmement pessimiste"]):
            return MarketSentiment.EXTREMELY_FEARFUL
        elif any(word in content_lower for word in ["fearful", "pessimiste", "craintif"]):
            return MarketSentiment.FEARFUL
        else:
            return MarketSentiment.NEUTRAL
    
    def _extract_themes(self, content: str) -> List[str]:
        """Extrait les thèmes clés du contenu."""
        # Implémentation simplifiée
        themes = []
        
        # Mots-clés pour identifier les thèmes
        theme_keywords = [
            "inflation", "taux", "tech", "énergie", "santé",
            "croissance", "récession", "géopolitique", "crypto",
            "IA", "intelligence artificielle", "transition énergétique"
        ]
        
        content_lower = content.lower()
        for keyword in theme_keywords:
            if keyword in content_lower:
                themes.append(keyword.title())
        
        return themes[:5]  # Max 5 thèmes