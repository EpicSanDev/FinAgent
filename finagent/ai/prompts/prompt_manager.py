"""
Gestionnaire centralisé des prompts pour l'IA.
"""

import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

import structlog
from pydantic import BaseModel, Field, ConfigDict

from ..models import (
    MarketContext,
    TechnicalIndicators,
    FundamentalMetrics,
    SentimentData,
    TradingContext,
    RiskParameters,
    AnalysisResult,
    AnalysisType,
    DecisionType,
    ModelType,
)
from .financial_analysis_prompts import FinancialAnalysisPrompts
from .trading_decision_prompts import TradingDecisionPrompts

logger = structlog.get_logger(__name__)


class PromptType(str, Enum):
    """Types de prompts disponibles."""
    TECHNICAL_ANALYSIS = "technical_analysis"
    FUNDAMENTAL_ANALYSIS = "fundamental_analysis"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    RISK_ANALYSIS = "risk_analysis"
    MARKET_OVERVIEW = "market_overview"
    BUY_DECISION = "buy_decision"
    SELL_DECISION = "sell_decision"
    HOLD_DECISION = "hold_decision"
    PORTFOLIO_REBALANCING = "portfolio_rebalancing"
    RISK_MANAGEMENT = "risk_management"
    STRATEGY_ANALYSIS = "strategy_analysis"
    CUSTOM = "custom"


class PromptTemplate(BaseModel):
    """Template de prompt réutilisable."""
    
    model_config = ConfigDict(protected_namespaces=())
    
    template_id: UUID = Field(default_factory=uuid4)
    name: str
    prompt_type: PromptType
    template: str
    description: Optional[str] = None
    variables: List[str] = Field(default_factory=list)  # Variables requises
    model_preferences: Dict[ModelType, float] = Field(default_factory=dict)  # Score de préférence par modèle
    tags: List[str] = Field(default_factory=list)
    
    # Métadonnées
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    version: str = Field(default="1.0")
    author: Optional[str] = None
    
    # Usage et performance
    usage_count: int = Field(default=0, ge=0)
    average_tokens: Optional[int] = Field(None, ge=0)
    success_rate: Optional[float] = Field(None, ge=0, le=1)
    
    def format(self, **kwargs) -> str:
        """Formate le template avec les variables fournies."""
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            missing_var = str(e).strip("'")
            raise ValueError(f"Variable manquante pour le template '{self.name}': {missing_var}")
    
    def validate_variables(self, variables: Dict[str, Any]) -> List[str]:
        """Valide que toutes les variables requises sont présentes."""
        missing = []
        for var in self.variables:
            if var not in variables:
                missing.append(var)
        return missing
    
    def record_usage(self, tokens_used: Optional[int] = None, success: bool = True):
        """Enregistre l'utilisation du template."""
        self.usage_count += 1
        
        if tokens_used:
            if self.average_tokens:
                self.average_tokens = int((self.average_tokens * (self.usage_count - 1) + tokens_used) / self.usage_count)
            else:
                self.average_tokens = tokens_used
        
        if self.success_rate is not None:
            self.success_rate = (self.success_rate * (self.usage_count - 1) + (1.0 if success else 0.0)) / self.usage_count
        else:
            self.success_rate = 1.0 if success else 0.0


class PromptContext(BaseModel):
    """Contexte pour la génération de prompts."""
    
    context_id: UUID = Field(default_factory=uuid4)
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    
    # Données financières
    market_context: Optional[MarketContext] = None
    technical_indicators: Optional[TechnicalIndicators] = None
    fundamental_metrics: Optional[FundamentalMetrics] = None
    sentiment_data: Optional[SentimentData] = None
    trading_context: Optional[TradingContext] = None
    risk_parameters: Optional[RiskParameters] = None
    analysis_result: Optional[AnalysisResult] = None
    
    # Contexte stratégique
    strategy_name: Optional[str] = None
    time_horizon: str = Field(default="1d")
    aggressive_mode: bool = Field(default=False)
    market_conditions: Optional[str] = None
    
    # Préférences utilisateur
    language: str = Field(default="fr")
    detail_level: str = Field(default="normal")  # "brief", "normal", "detailed"
    risk_tolerance: str = Field(default="moderate")  # "conservative", "moderate", "aggressive"
    
    # Contexte additionnel
    custom_context: Dict[str, Any] = Field(default_factory=dict)
    previous_decisions: List[str] = Field(default_factory=list)
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PromptManager:
    """Gestionnaire centralisé des prompts."""
    
    def __init__(self, templates_path: Optional[Path] = None):
        self.templates_path = templates_path
        self.templates: Dict[PromptType, List[PromptTemplate]] = {}
        self.custom_templates: Dict[str, PromptTemplate] = {}
        
        self.logger = logger.bind(component="prompt_manager")
        
        # Générateurs de prompts spécialisés
        self.financial_analysis = FinancialAnalysisPrompts()
        self.trading_decisions = TradingDecisionPrompts()
        
        # Charge les templates par défaut
        self._load_default_templates()
        
        # Charge les templates personnalisés si disponibles
        if self.templates_path and self.templates_path.exists():
            self._load_custom_templates()
    
    def _load_default_templates(self):
        """Charge les templates par défaut."""
        # Templates d'analyse financière
        self._register_default_template(
            PromptType.TECHNICAL_ANALYSIS,
            "Analyse Technique Standard",
            "Template pour analyse technique complète",
            ["market_context", "technical_indicators", "time_horizon"],
            {ModelType.CLAUDE_3_SONNET: 0.9, ModelType.CLAUDE_3_HAIKU: 0.7}
        )
        
        self._register_default_template(
            PromptType.FUNDAMENTAL_ANALYSIS,
            "Analyse Fondamentale Standard",
            "Template pour analyse fondamentale complète",
            ["market_context", "fundamental_metrics", "sector_context"],
            {ModelType.CLAUDE_3_SONNET: 0.95, ModelType.CLAUDE_3_OPUS: 0.9}
        )
        
        # Templates de décision de trading
        self._register_default_template(
            PromptType.BUY_DECISION,
            "Décision d'Achat Standard",
            "Template pour évaluer une opportunité d'achat",
            ["trading_context", "analysis_result", "risk_parameters"],
            {ModelType.CLAUDE_3_5_SONNET: 0.95, ModelType.CLAUDE_3_SONNET: 0.85}
        )
        
        self._register_default_template(
            PromptType.SELL_DECISION,
            "Décision de Vente Standard",
            "Template pour évaluer une opportunité de vente",
            ["trading_context", "analysis_result", "risk_parameters"],
            {ModelType.CLAUDE_3_5_SONNET: 0.95, ModelType.CLAUDE_3_SONNET: 0.85}
        )
        
        self.logger.info("Templates par défaut chargés", count=len(self.templates))
    
    def _register_default_template(
        self,
        prompt_type: PromptType,
        name: str,
        description: str,
        variables: List[str],
        model_preferences: Dict[ModelType, float]
    ):
        """Enregistre un template par défaut."""
        template = PromptTemplate(
            name=name,
            prompt_type=prompt_type,
            template="",  # Sera généré dynamiquement
            description=description,
            variables=variables,
            model_preferences=model_preferences,
            author="FinAgent System"
        )
        
        if prompt_type not in self.templates:
            self.templates[prompt_type] = []
        self.templates[prompt_type].append(template)
    
    def _load_custom_templates(self):
        """Charge les templates personnalisés depuis les fichiers."""
        try:
            for template_file in self.templates_path.glob("*.json"):
                with open(template_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    template = PromptTemplate(**data)
                    self.custom_templates[str(template.template_id)] = template
                    
            self.logger.info("Templates personnalisés chargés", count=len(self.custom_templates))
        except Exception as e:
            self.logger.error("Erreur chargement templates personnalisés", error=str(e))
    
    def generate_prompt(
        self,
        prompt_type: PromptType,
        context: PromptContext,
        template_name: Optional[str] = None
    ) -> str:
        """Génère un prompt basé sur le type et le contexte."""
        
        self.logger.info(
            "Génération prompt",
            prompt_type=prompt_type.value,
            template_name=template_name,
            context_id=str(context.context_id)
        )
        
        # Utilise les générateurs spécialisés pour les prompts dynamiques
        if prompt_type == PromptType.TECHNICAL_ANALYSIS:
            if not context.market_context or not context.technical_indicators:
                raise ValueError("MarketContext et TechnicalIndicators requis pour l'analyse technique")
            
            return self.financial_analysis.create_technical_analysis_prompt(
                context.market_context,
                context.technical_indicators,
                context.time_horizon
            )
        
        elif prompt_type == PromptType.FUNDAMENTAL_ANALYSIS:
            if not context.market_context or not context.fundamental_metrics:
                raise ValueError("MarketContext et FundamentalMetrics requis pour l'analyse fondamentale")
            
            return self.financial_analysis.create_fundamental_analysis_prompt(
                context.market_context,
                context.fundamental_metrics,
                context.custom_context.get("sector_context")
            )
        
        elif prompt_type == PromptType.SENTIMENT_ANALYSIS:
            if not context.market_context or not context.sentiment_data:
                raise ValueError("MarketContext et SentimentData requis pour l'analyse de sentiment")
            
            return self.financial_analysis.create_sentiment_analysis_prompt(
                context.market_context,
                context.sentiment_data,
                context.custom_context.get("recent_news")
            )
        
        elif prompt_type == PromptType.RISK_ANALYSIS:
            if not context.market_context:
                raise ValueError("MarketContext requis pour l'analyse de risque")
            
            return self.financial_analysis.create_risk_analysis_prompt(
                context.market_context,
                context.custom_context.get("volatility_data"),
                context.custom_context.get("correlation_data"),
                context.market_conditions
            )
        
        elif prompt_type == PromptType.BUY_DECISION:
            if not all([context.trading_context, context.analysis_result, context.risk_parameters]):
                raise ValueError("TradingContext, AnalysisResult et RiskParameters requis")
            
            return self.trading_decisions.create_buy_decision_prompt(
                context.trading_context,
                context.analysis_result,
                context.risk_parameters,
                context.strategy_name
            )
        
        elif prompt_type == PromptType.SELL_DECISION:
            if not all([context.trading_context, context.analysis_result, context.risk_parameters]):
                raise ValueError("TradingContext, AnalysisResult et RiskParameters requis")
            
            return self.trading_decisions.create_sell_decision_prompt(
                context.trading_context,
                context.analysis_result,
                context.risk_parameters,
                context.custom_context.get("hold_period_days")
            )
        
        elif prompt_type == PromptType.HOLD_DECISION:
            if not context.trading_context or not context.analysis_result:
                raise ValueError("TradingContext et AnalysisResult requis")
            
            return self.trading_decisions.create_hold_decision_prompt(
                context.trading_context,
                context.analysis_result,
                context.market_conditions
            )
        
        else:
            # Utilise un template enregistré
            template = self._get_template(prompt_type, template_name)
            if not template:
                raise ValueError(f"Aucun template trouvé pour {prompt_type.value}")
            
            # Prépare les variables pour le template
            variables = self._prepare_template_variables(context)
            missing = template.validate_variables(variables)
            if missing:
                raise ValueError(f"Variables manquantes: {missing}")
            
            return template.format(**variables)
    
    def _get_template(self, prompt_type: PromptType, template_name: Optional[str] = None) -> Optional[PromptTemplate]:
        """Récupère un template par type et nom."""
        templates = self.templates.get(prompt_type, [])
        
        if template_name:
            for template in templates:
                if template.name == template_name:
                    return template
        
        # Retourne le premier template si aucun nom spécifié
        return templates[0] if templates else None
    
    def _prepare_template_variables(self, context: PromptContext) -> Dict[str, Any]:
        """Prépare les variables pour les templates."""
        variables = {}
        
        # Ajoute tous les champs du contexte
        if context.market_context:
            variables["market_context"] = context.market_context
        if context.technical_indicators:
            variables["technical_indicators"] = context.technical_indicators
        if context.fundamental_metrics:
            variables["fundamental_metrics"] = context.fundamental_metrics
        if context.sentiment_data:
            variables["sentiment_data"] = context.sentiment_data
        if context.trading_context:
            variables["trading_context"] = context.trading_context
        if context.analysis_result:
            variables["analysis_result"] = context.analysis_result
        
        # Ajoute les variables simples
        variables.update({
            "strategy_name": context.strategy_name,
            "time_horizon": context.time_horizon,
            "market_conditions": context.market_conditions,
            "language": context.language,
            "detail_level": context.detail_level,
            "risk_tolerance": context.risk_tolerance,
        })
        
        # Ajoute le contexte personnalisé
        variables.update(context.custom_context)
        
        return variables
    
    def get_recommended_model(self, prompt_type: PromptType, template_name: Optional[str] = None) -> Optional[ModelType]:
        """Retourne le modèle recommandé pour un type de prompt."""
        template = self._get_template(prompt_type, template_name)
        if not template or not template.model_preferences:
            return None
        
        # Retourne le modèle avec le score le plus élevé
        return max(template.model_preferences.items(), key=lambda x: x[1])[0]
    
    def create_custom_template(
        self,
        name: str,
        prompt_type: PromptType,
        template: str,
        description: Optional[str] = None,
        variables: Optional[List[str]] = None,
        model_preferences: Optional[Dict[ModelType, float]] = None
    ) -> PromptTemplate:
        """Crée un template personnalisé."""
        custom_template = PromptTemplate(
            name=name,
            prompt_type=prompt_type,
            template=template,
            description=description,
            variables=variables or [],
            model_preferences=model_preferences or {},
            tags=["custom"]
        )
        
        self.custom_templates[str(custom_template.template_id)] = custom_template
        
        self.logger.info("Template personnalisé créé", template_id=str(custom_template.template_id), name=name)
        
        return custom_template
    
    def save_custom_templates(self):
        """Sauvegarde les templates personnalisés."""
        if not self.templates_path:
            return
        
        self.templates_path.mkdir(parents=True, exist_ok=True)
        
        for template_id, template in self.custom_templates.items():
            file_path = self.templates_path / f"{template_id}.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(template.model_dump(), f, indent=2, ensure_ascii=False, default=str)
        
        self.logger.info("Templates personnalisés sauvegardés", count=len(self.custom_templates))
    
    def get_template_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques d'utilisation des templates."""
        stats = {
            "total_templates": len(self.templates) + len(self.custom_templates),
            "default_templates": sum(len(templates) for templates in self.templates.values()),
            "custom_templates": len(self.custom_templates),
            "most_used": [],
            "best_performance": []
        }
        
        # Templates les plus utilisés
        all_templates = []
        for templates in self.templates.values():
            all_templates.extend(templates)
        all_templates.extend(self.custom_templates.values())
        
        most_used = sorted(all_templates, key=lambda t: t.usage_count, reverse=True)[:5]
        stats["most_used"] = [{"name": t.name, "usage": t.usage_count} for t in most_used]
        
        # Meilleure performance
        best_perf = sorted(
            [t for t in all_templates if t.success_rate is not None],
            key=lambda t: t.success_rate,
            reverse=True
        )[:5]
        stats["best_performance"] = [{"name": t.name, "success_rate": t.success_rate} for t in best_perf]
        
        return stats


# Factory function
def create_prompt_manager(templates_path: Optional[str] = None) -> PromptManager:
    """Crée un gestionnaire de prompts."""
    path = Path(templates_path) if templates_path else None
    return PromptManager(path)