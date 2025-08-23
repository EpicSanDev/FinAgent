"""
Validateur avancé pour les stratégies de trading.

Ce module contient la logique de validation métier et de cohérence
pour les stratégies, au-delà de la validation structurelle de Pydantic.
"""

import logging
from decimal import Decimal
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

from ..models.strategy_models import Strategy, StrategyType
from ..models.rule_models import Rule, BuyConditions, SellConditions
from ..models.condition_models import IndicatorType

logger = logging.getLogger(__name__)


@dataclass
class ValidationIssue:
    """Représente un problème de validation."""
    level: str  # 'error', 'warning', 'info'
    code: str
    message: str
    field: Optional[str] = None
    suggestion: Optional[str] = None


class ValidationError(Exception):
    """Exception levée pour les erreurs de validation critiques."""
    
    def __init__(self, message: str, issues: List[ValidationIssue] = None):
        self.message = message
        self.issues = issues or []
        super().__init__(message)


@dataclass
class ValidationResult:
    """Résultat de la validation d'une stratégie."""
    is_valid: bool
    issues: List[ValidationIssue]
    
    @property
    def errors(self) -> List[ValidationIssue]:
        """Retourne uniquement les erreurs."""
        return [issue for issue in self.issues if issue.level == 'error']
    
    @property
    def warnings(self) -> List[ValidationIssue]:
        """Retourne uniquement les avertissements."""
        return [issue for issue in self.issues if issue.level == 'warning']
    
    @property
    def infos(self) -> List[ValidationIssue]:
        """Retourne uniquement les informations."""
        return [issue for issue in self.issues if issue.level == 'info']
    
    def has_errors(self) -> bool:
        """Vérifie s'il y a des erreurs."""
        return len(self.errors) > 0
    
    def summary(self) -> str:
        """Retourne un résumé de la validation."""
        return (f"Validation: {'✓ Réussie' if self.is_valid else '✗ Échouée'} - "
                f"{len(self.errors)} erreurs, {len(self.warnings)} avertissements")


class StrategyValidator:
    """Validateur avancé pour les stratégies de trading."""
    
    def __init__(self):
        """Initialise le validateur."""
        self.logger = logging.getLogger(__name__)
        
        # Règles de validation par défaut
        self._validation_rules = self._load_default_rules()
        
        # Seuils de validation
        self._thresholds = {
            'max_position_size': Decimal('0.5'),  # 50% max par position
            'max_total_exposure': Decimal('1.0'),  # 100% exposition max
            'min_stop_loss': Decimal('0.01'),     # 1% min stop-loss
            'max_stop_loss': Decimal('0.25'),     # 25% max stop-loss
            'min_take_profit': Decimal('0.02'),   # 2% min take-profit
            'max_drawdown_limit': Decimal('0.30'), # 30% max drawdown
            'min_analysis_weight': Decimal('0.1'), # 10% min poids analyse
            'max_holding_period': 365,             # 1 an max
            'min_conditions': 1,                   # 1 condition min
            'max_conditions': 20                   # 20 conditions max
        }
    
    def validate(self, strategy: Strategy) -> ValidationResult:
        """
        Valide une stratégie complète.
        
        Args:
            strategy: Stratégie à valider
            
        Returns:
            ValidationResult: Résultat de la validation
        """
        issues = []
        
        try:
            # Validation de la configuration de base
            issues.extend(self._validate_strategy_config(strategy))
            
            # Validation des paramètres
            issues.extend(self._validate_settings(strategy))
            
            # Validation de l'univers d'investissement
            if strategy.universe:
                issues.extend(self._validate_universe(strategy))
            
            # Validation de l'analyse
            issues.extend(self._validate_analysis(strategy))
            
            # Validation des règles
            issues.extend(self._validate_rules(strategy))
            
            # Validation de la gestion des risques
            issues.extend(self._validate_risk_management(strategy))
            
            # Validation du backtesting
            if strategy.backtesting:
                issues.extend(self._validate_backtesting(strategy))
            
            # Validation de la cohérence globale
            issues.extend(self._validate_global_consistency(strategy))
            
            # Déterminer si la stratégie est valide
            has_errors = any(issue.level == 'error' for issue in issues)
            is_valid = not has_errors
            
            return ValidationResult(is_valid=is_valid, issues=issues)
            
        except Exception as e:
            error_issue = ValidationIssue(
                level='error',
                code='VALIDATION_EXCEPTION',
                message=f"Erreur inattendue lors de la validation: {e}"
            )
            return ValidationResult(is_valid=False, issues=[error_issue])
    
    def _validate_strategy_config(self, strategy: Strategy) -> List[ValidationIssue]:
        """Valide la configuration de base de la stratégie."""
        issues = []
        config = strategy.strategy
        
        # Validation du nom
        if len(config.name.strip()) < 3:
            issues.append(ValidationIssue(
                level='error',
                code='INVALID_NAME_LENGTH',
                message="Le nom de la stratégie doit contenir au moins 3 caractères",
                field='strategy.name'
            ))
        
        # Validation de la version
        version_parts = config.version.split('.')
        if len(version_parts) < 2:
            issues.append(ValidationIssue(
                level='warning',
                code='INVALID_VERSION_FORMAT',
                message="Le format de version recommandé est 'MAJOR.MINOR' ou 'MAJOR.MINOR.PATCH'",
                field='strategy.version'
            ))
        
        # Validation du type de stratégie
        if config.type == StrategyType.HYBRID:
            issues.append(ValidationIssue(
                level='info',
                code='HYBRID_STRATEGY',
                message="Les stratégies hybrides nécessitent plus de ressources de calcul",
                field='strategy.type'
            ))
        
        return issues
    
    def _validate_settings(self, strategy: Strategy) -> List[ValidationIssue]:
        """Valide les paramètres généraux."""
        issues = []
        settings = strategy.settings
        
        if not settings:
            return issues
        
        # Validation de la taille de position
        if settings.position_size > self._thresholds['max_position_size']:
            issues.append(ValidationIssue(
                level='error',
                code='POSITION_SIZE_TOO_LARGE',
                message=f"Taille de position trop élevée: {settings.position_size}",
                field='settings.position_size',
                suggestion=f"Utiliser une taille <= {self._thresholds['max_position_size']}"
            ))
        
        # Validation de l'exposition totale
        total_exposure = settings.position_size * settings.max_positions
        if total_exposure > self._thresholds['max_total_exposure']:
            issues.append(ValidationIssue(
                level='error',
                code='TOTAL_EXPOSURE_TOO_HIGH',
                message=f"Exposition totale trop élevée: {total_exposure}",
                field='settings',
                suggestion="Réduire position_size ou max_positions"
            ))
        
        # Validation du nombre de positions
        if settings.max_positions > 50:
            issues.append(ValidationIssue(
                level='warning',
                code='TOO_MANY_POSITIONS',
                message=f"Nombre élevé de positions: {settings.max_positions}",
                field='settings.max_positions',
                suggestion="Considérer <= 20 positions pour une gestion optimale"
            ))
        
        return issues
    
    def _validate_universe(self, strategy: Strategy) -> List[ValidationIssue]:
        """Valide l'univers d'investissement."""
        issues = []
        universe = strategy.universe
        
        # Validation de la watchlist
        if universe.watchlist:
            if len(universe.watchlist) == 0:
                issues.append(ValidationIssue(
                    level='warning',
                    code='EMPTY_WATCHLIST',
                    message="Watchlist vide spécifiée",
                    field='universe.watchlist'
                ))
            elif len(universe.watchlist) > 100:
                issues.append(ValidationIssue(
                    level='warning',
                    code='LARGE_WATCHLIST',
                    message=f"Watchlist très large: {len(universe.watchlist)} symboles",
                    field='universe.watchlist',
                    suggestion="Considérer une watchlist plus focalisée"
                ))
            
            # Validation du format des symboles
            for symbol in universe.watchlist:
                if not symbol.isalnum() or len(symbol) > 10:
                    issues.append(ValidationIssue(
                        level='warning',
                        code='INVALID_SYMBOL_FORMAT',
                        message=f"Format de symbole suspect: {symbol}",
                        field='universe.watchlist'
                    ))
        
        # Validation des filtres
        if universe.min_price and universe.min_price < Decimal('1.0'):
            issues.append(ValidationIssue(
                level='warning',
                code='LOW_MIN_PRICE',
                message=f"Prix minimum très bas: {universe.min_price}",
                field='universe.min_price',
                suggestion="Éviter les penny stocks pour réduire le risque"
            ))
        
        if universe.min_volume and universe.min_volume < 100000:
            issues.append(ValidationIssue(
                level='warning',
                code='LOW_MIN_VOLUME',
                message=f"Volume minimum faible: {universe.min_volume}",
                field='universe.min_volume',
                suggestion="Volume >= 1M pour une meilleure liquidité"
            ))
        
        return issues
    
    def _validate_analysis(self, strategy: Strategy) -> List[ValidationIssue]:
        """Valide la configuration d'analyse."""
        issues = []
        analysis = strategy.analysis
        
        # Vérifier qu'au moins un type d'analyse est défini
        has_technical = analysis.technical and len(analysis.technical) > 0
        has_fundamental = analysis.fundamental and len(analysis.fundamental) > 0
        has_sentiment = analysis.sentiment and len(analysis.sentiment) > 0
        
        if not any([has_technical, has_fundamental, has_sentiment]):
            issues.append(ValidationIssue(
                level='error',
                code='NO_ANALYSIS_DEFINED',
                message="Aucun indicateur d'analyse défini",
                field='analysis'
            ))
        
        # Validation des poids d'analyse technique
        if has_technical:
            total_weight = sum(ind.weight for ind in analysis.technical)
            if total_weight > Decimal('1.0'):
                issues.append(ValidationIssue(
                    level='error',
                    code='TECHNICAL_WEIGHTS_EXCEED_LIMIT',
                    message=f"Poids total analyse technique: {total_weight} > 1.0",
                    field='analysis.technical'
                ))
        
        # Validation des poids d'analyse fondamentale
        if has_fundamental:
            total_weight = sum(ind.weight for ind in analysis.fundamental)
            if total_weight > Decimal('1.0'):
                issues.append(ValidationIssue(
                    level='error',
                    code='FUNDAMENTAL_WEIGHTS_EXCEED_LIMIT',
                    message=f"Poids total analyse fondamentale: {total_weight} > 1.0",
                    field='analysis.fundamental'
                ))
        
        # Validation des poids d'analyse de sentiment
        if has_sentiment:
            total_weight = sum(ind.weight for ind in analysis.sentiment)
            if total_weight > Decimal('1.0'):
                issues.append(ValidationIssue(
                    level='error',
                    code='SENTIMENT_WEIGHTS_EXCEED_LIMIT',
                    message=f"Poids total analyse sentiment: {total_weight} > 1.0",
                    field='analysis.sentiment'
                ))
        
        # Avertissement pour stratégies déséquilibrées
        if strategy.strategy.type == StrategyType.HYBRID:
            if not (has_technical and has_fundamental):
                issues.append(ValidationIssue(
                    level='warning',
                    code='INCOMPLETE_HYBRID_STRATEGY',
                    message="Stratégie hybride incomplète",
                    suggestion="Inclure analyse technique ET fondamentale"
                ))
        
        return issues
    
    def _validate_rules(self, strategy: Strategy) -> List[ValidationIssue]:
        """Valide les règles de trading."""
        issues = []
        rules = strategy.rules
        
        # Validation des conditions d'achat
        if 'buy_conditions' in rules:
            buy_cond = rules['buy_conditions']
            if isinstance(buy_cond, dict) and 'conditions' in buy_cond:
                conditions = buy_cond['conditions']
                if len(conditions) == 0:
                    issues.append(ValidationIssue(
                        level='error',
                        code='NO_BUY_CONDITIONS',
                        message="Aucune condition d'achat définie",
                        field='rules.buy_conditions'
                    ))
                elif len(conditions) > self._thresholds['max_conditions']:
                    issues.append(ValidationIssue(
                        level='warning',
                        code='TOO_MANY_BUY_CONDITIONS',
                        message=f"Trop de conditions d'achat: {len(conditions)}",
                        field='rules.buy_conditions',
                        suggestion="Simplifier pour améliorer les performances"
                    ))
        
        # Validation des conditions de vente
        if 'sell_conditions' in rules:
            sell_cond = rules['sell_conditions']
            if isinstance(sell_cond, dict) and 'conditions' in sell_cond:
                conditions = sell_cond['conditions']
                if len(conditions) == 0:
                    issues.append(ValidationIssue(
                        level='error',
                        code='NO_SELL_CONDITIONS',
                        message="Aucune condition de vente définie",
                        field='rules.sell_conditions'
                    ))
        
        return issues
    
    def _validate_risk_management(self, strategy: Strategy) -> List[ValidationIssue]:
        """Valide la gestion des risques."""
        issues = []
        risk_mgmt = strategy.risk_management
        
        # Validation du stop-loss
        if risk_mgmt.stop_loss:
            stop_loss_val = risk_mgmt.stop_loss.value
            if stop_loss_val < self._thresholds['min_stop_loss']:
                issues.append(ValidationIssue(
                    level='warning',
                    code='STOP_LOSS_TOO_TIGHT',
                    message=f"Stop-loss très serré: {stop_loss_val}",
                    field='risk_management.stop_loss.value',
                    suggestion="Risque de sorties prématurées"
                ))
            elif stop_loss_val > self._thresholds['max_stop_loss']:
                issues.append(ValidationIssue(
                    level='error',
                    code='STOP_LOSS_TOO_WIDE',
                    message=f"Stop-loss trop large: {stop_loss_val}",
                    field='risk_management.stop_loss.value',
                    suggestion=f"Utiliser <= {self._thresholds['max_stop_loss']}"
                ))
        else:
            issues.append(ValidationIssue(
                level='warning',
                code='NO_STOP_LOSS',
                message="Aucun stop-loss défini",
                field='risk_management.stop_loss',
                suggestion="Définir un stop-loss pour limiter les pertes"
            ))
        
        # Validation du take-profit
        if risk_mgmt.take_profit:
            take_profit_val = risk_mgmt.take_profit.value
            if take_profit_val < self._thresholds['min_take_profit']:
                issues.append(ValidationIssue(
                    level='warning',
                    code='TAKE_PROFIT_TOO_SMALL',
                    message=f"Take-profit faible: {take_profit_val}",
                    field='risk_management.take_profit.value'
                ))
            
            # Vérifier ratio risk/reward
            if risk_mgmt.stop_loss:
                ratio = take_profit_val / risk_mgmt.stop_loss.value
                if ratio < Decimal('1.5'):
                    issues.append(ValidationIssue(
                        level='warning',
                        code='POOR_RISK_REWARD_RATIO',
                        message=f"Ratio risque/récompense faible: {ratio:.2f}",
                        field='risk_management',
                        suggestion="Viser un ratio >= 2:1"
                    ))
        
        # Validation du drawdown maximum
        if risk_mgmt.max_drawdown:
            if risk_mgmt.max_drawdown > self._thresholds['max_drawdown_limit']:
                issues.append(ValidationIssue(
                    level='error',
                    code='MAX_DRAWDOWN_TOO_HIGH',
                    message=f"Drawdown max trop élevé: {risk_mgmt.max_drawdown}",
                    field='risk_management.max_drawdown',
                    suggestion=f"Utiliser <= {self._thresholds['max_drawdown_limit']}"
                ))
        
        return issues
    
    def _validate_backtesting(self, strategy: Strategy) -> List[ValidationIssue]:
        """Valide la configuration du backtesting."""
        issues = []
        backtest = strategy.backtesting
        
        # Validation des dates
        try:
            start_date = datetime.strptime(backtest.start_date, '%Y-%m-%d')
            end_date = datetime.strptime(backtest.end_date, '%Y-%m-%d')
            
            # Vérifier la période
            period = end_date - start_date
            if period.days < 30:
                issues.append(ValidationIssue(
                    level='warning',
                    code='BACKTEST_PERIOD_TOO_SHORT',
                    message=f"Période de backtest courte: {period.days} jours",
                    field='backtesting',
                    suggestion="Utiliser au moins 3 mois pour des résultats fiables"
                ))
            elif period.days > 3650:  # 10 ans
                issues.append(ValidationIssue(
                    level='info',
                    code='BACKTEST_PERIOD_VERY_LONG',
                    message=f"Période de backtest très longue: {period.days} jours",
                    field='backtesting'
                ))
            
            # Vérifier que les dates ne sont pas dans le futur
            now = datetime.now()
            if end_date > now:
                issues.append(ValidationIssue(
                    level='error',
                    code='BACKTEST_END_DATE_FUTURE',
                    message="La date de fin ne peut pas être dans le futur",
                    field='backtesting.end_date'
                ))
        
        except ValueError as e:
            issues.append(ValidationIssue(
                level='error',
                code='INVALID_BACKTEST_DATES',
                message=f"Format de date invalide: {e}",
                field='backtesting'
            ))
        
        # Validation du capital initial
        if backtest.initial_capital < Decimal('1000'):
            issues.append(ValidationIssue(
                level='warning',
                code='LOW_INITIAL_CAPITAL',
                message=f"Capital initial faible: {backtest.initial_capital}",
                field='backtesting.initial_capital'
            ))
        
        # Validation des commissions
        if backtest.commission > Decimal('0.01'):  # 1%
            issues.append(ValidationIssue(
                level='warning',
                code='HIGH_COMMISSION',
                message=f"Commission élevée: {backtest.commission}",
                field='backtesting.commission'
            ))
        
        return issues
    
    def _validate_global_consistency(self, strategy: Strategy) -> List[ValidationIssue]:
        """Valide la cohérence globale de la stratégie."""
        issues = []
        
        # Vérifier la cohérence entre type de stratégie et analyse
        strategy_type = strategy.strategy.type
        analysis = strategy.analysis
        
        if strategy_type == StrategyType.TECHNICAL and not analysis.technical:
            issues.append(ValidationIssue(
                level='error',
                code='INCONSISTENT_STRATEGY_TYPE',
                message="Stratégie technique sans indicateurs techniques",
                field='strategy.type'
            ))
        
        if strategy_type == StrategyType.FUNDAMENTAL and not analysis.fundamental:
            issues.append(ValidationIssue(
                level='error',
                code='INCONSISTENT_STRATEGY_TYPE',
                message="Stratégie fondamentale sans indicateurs fondamentaux",
                field='strategy.type'
            ))
        
        # Vérifier la cohérence temporelle
        settings = strategy.settings
        if settings and settings.time_horizon == 'short':
            if analysis.fundamental and len(analysis.fundamental) > 0:
                issues.append(ValidationIssue(
                    level='warning',
                    code='INCONSISTENT_TIME_HORIZON',
                    message="Analyse fondamentale avec horizon court terme",
                    suggestion="L'analyse fondamentale est plus adaptée au long terme"
                ))
        
        return issues
    
    def _load_default_rules(self) -> Dict[str, Any]:
        """Charge les règles de validation par défaut."""
        return {
            'required_sections': ['strategy', 'analysis', 'rules', 'risk_management'],
            'required_strategy_fields': ['name', 'type'],
            'allowed_strategy_types': ['technical', 'fundamental', 'sentiment', 'hybrid'],
            'max_name_length': 100,
            'max_description_length': 500,
            'version_pattern': r'^\d+\.\d+(\.\d+)?$'
        }
    
    def get_validation_summary(self, result: ValidationResult) -> str:
        """
        Génère un résumé détaillé de la validation.
        
        Args:
            result: Résultat de validation
            
        Returns:
            str: Résumé formaté
        """
        lines = [result.summary()]
        
        if result.errors:
            lines.append("\nErreurs:")
            for error in result.errors:
                lines.append(f"  ❌ {error.code}: {error.message}")
                if error.suggestion:
                    lines.append(f"     💡 {error.suggestion}")
        
        if result.warnings:
            lines.append("\nAvertissements:")
            for warning in result.warnings:
                lines.append(f"  ⚠️  {warning.code}: {warning.message}")
                if warning.suggestion:
                    lines.append(f"     💡 {warning.suggestion}")
        
        if result.infos:
            lines.append("\nInformations:")
            for info in result.infos:
                lines.append(f"  ℹ️  {info.code}: {info.message}")
        
        return "\n".join(lines)

    def validate_strategy(self, strategy: Strategy) -> ValidationResult:
        """
        Méthode principale de validation d'une stratégie.
        
        Args:
            strategy: Stratégie à valider
            
        Returns:
            ValidationResult: Résultat de la validation
        """
        return self.validate(strategy)