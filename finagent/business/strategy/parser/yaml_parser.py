"""
Parseur YAML pour les stratégies de trading.

Ce module contient la logique pour parser et convertir les fichiers YAML
de configuration de stratégies en objets Python structurés.
"""

import logging
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union
from pydantic import ValidationError as PydanticValidationError

from ..models.strategy_models import Strategy
from ..models.rule_models import Rule, BuyConditions, SellConditions
from ..models.rule_models import (
    TechnicalCondition,
    FundamentalCondition,
    SentimentCondition,
    VolumeCondition,
    PriceCondition,
    RiskCondition
)

logger = logging.getLogger(__name__)


class ParseError(Exception):
    """Exception levée lors d'erreurs de parsing YAML."""
    
    def __init__(self, message: str, line: Optional[int] = None, column: Optional[int] = None):
        self.message = message
        self.line = line
        self.column = column
        super().__init__(self._format_message())
    
    def _format_message(self) -> str:
        """Formate le message d'erreur avec les informations de position."""
        if self.line is not None and self.column is not None:
            return f"Ligne {self.line}, colonne {self.column}: {self.message}"
        elif self.line is not None:
            return f"Ligne {self.line}: {self.message}"
        else:
            return self.message


class ValidationError(Exception):
    """Exception levée lors d'erreurs de validation."""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Any = None):
        self.message = message
        self.field = field
        self.value = value
        super().__init__(self._format_message())
    
    def _format_message(self) -> str:
        """Formate le message d'erreur de validation."""
        if self.field:
            return f"Champ '{self.field}': {self.message}"
        return self.message


class StrategyYAMLParser:
    """Parseur pour les fichiers de configuration de stratégies YAML."""
    
    def __init__(self):
        """Initialise le parseur."""
        self.logger = logging.getLogger(__name__)
        
        # Configuration YAML sécurisée
        self._yaml_loader = yaml.SafeLoader
        
        # Mappings des types de conditions
        self._condition_type_mapping = {
            'technical': TechnicalCondition,
            'fundamental': FundamentalCondition,
            'sentiment': SentimentCondition,
            'volume': VolumeCondition,
            'price': PriceCondition,
            'risk': RiskCondition
        }
    
    def parse_file(self, file_path: Union[str, Path]) -> Strategy:
        """
        Parse un fichier YAML de stratégie.
        
        Args:
            file_path: Chemin vers le fichier YAML
            
        Returns:
            Strategy: Objet Strategy validé
            
        Raises:
            ParseError: Si le fichier ne peut pas être parsé
            ValidationError: Si la validation Pydantic échoue
            FileNotFoundError: Si le fichier n'existe pas
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Le fichier {file_path} n'existe pas")
        
        if not file_path.suffix.lower() in ['.yaml', '.yml']:
            raise ParseError(f"Extension de fichier non supportée: {file_path.suffix}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                return self.parse_string(content)
        except UnicodeDecodeError as e:
            raise ParseError(f"Erreur d'encodage du fichier: {e}")
        except Exception as e:
            raise ParseError(f"Erreur lors de la lecture du fichier: {e}")
    
    def parse_string(self, yaml_content: str) -> Strategy:
        """
        Parse une chaîne YAML de stratégie.
        
        Args:
            yaml_content: Contenu YAML sous forme de chaîne
            
        Returns:
            Strategy: Objet Strategy validé
            
        Raises:
            ParseError: Si le YAML ne peut pas être parsé
            ValidationError: Si la validation Pydantic échoue
        """
        try:
            # Parse le YAML
            raw_data = yaml.load(yaml_content, Loader=self._yaml_loader)
            
            if not isinstance(raw_data, dict):
                raise ParseError("Le fichier YAML doit contenir un objet au niveau racine")
            
            # Valide la structure de base
            self._validate_basic_structure(raw_data)
            
            # Traite les règles avant la validation Pydantic
            processed_data = self._preprocess_data(raw_data)
            
            # Crée l'objet Strategy avec validation Pydantic
            return Strategy(**processed_data)
            
        except yaml.YAMLError as e:
            line_info = getattr(e, 'problem_mark', None)
            line = line_info.line + 1 if line_info else None
            column = line_info.column + 1 if line_info else None
            raise ParseError(f"Erreur de syntaxe YAML: {e}", line, column)
            
        except PydanticValidationError as e:
            self._handle_pydantic_error(e)
            
        except Exception as e:
            raise ParseError(f"Erreur inattendue lors du parsing: {e}")
    
    def _validate_basic_structure(self, data: Dict[str, Any]) -> None:
        """
        Valide la structure de base du YAML.
        
        Args:
            data: Données parsées du YAML
            
        Raises:
            ValidationError: Si la structure est invalide
        """
        # Vérifier la présence de la section strategy
        if 'strategy' not in data:
            raise ValidationError("La section 'strategy' est obligatoire")
        
        strategy_config = data['strategy']
        if not isinstance(strategy_config, dict):
            raise ValidationError("La section 'strategy' doit être un objet")
        
        # Vérifier les champs obligatoires
        required_fields = ['name', 'type']
        for field in required_fields:
            if field not in strategy_config:
                raise ValidationError(f"Le champ '{field}' est obligatoire dans la section 'strategy'")
        
        # Vérifier les sections obligatoires
        required_sections = ['analysis', 'rules', 'risk_management']
        for section in required_sections:
            if section not in data:
                raise ValidationError(f"La section '{section}' est obligatoire")
    
    def _preprocess_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prétraite les données avant la validation Pydantic.
        
        Args:
            data: Données brutes du YAML
            
        Returns:
            Dict[str, Any]: Données prétraitées
        """
        processed = data.copy()
        
        # Traite les règles
        if 'rules' in processed:
            processed['rules'] = self._process_rules(processed['rules'])
        
        # Traite l'analyse
        if 'analysis' in processed:
            processed['analysis'] = self._process_analysis(processed['analysis'])
        
        return processed
    
    def _process_rules(self, rules_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Traite la section des règles.
        
        Args:
            rules_data: Données des règles
            
        Returns:
            Dict[str, Any]: Règles traitées
        """
        processed_rules = {}
        
        # Traite les conditions d'achat
        if 'buy_conditions' in rules_data:
            processed_rules['buy_conditions'] = self._process_conditions(
                rules_data['buy_conditions'], 'buy'
            )
        
        # Traite les conditions de vente
        if 'sell_conditions' in rules_data:
            processed_rules['sell_conditions'] = self._process_conditions(
                rules_data['sell_conditions'], 'sell'
            )
        
        # Copie les autres champs tels quels
        for key, value in rules_data.items():
            if key not in ['buy_conditions', 'sell_conditions']:
                processed_rules[key] = value
        
        return processed_rules
    
    def _process_conditions(self, conditions_data: Dict[str, Any], condition_type: str) -> Dict[str, Any]:
        """
        Traite les conditions d'achat ou de vente.
        
        Args:
            conditions_data: Données des conditions
            condition_type: Type de condition ('buy' ou 'sell')
            
        Returns:
            Dict[str, Any]: Conditions traitées
        """
        processed = conditions_data.copy()
        
        if 'conditions' in processed:
            processed_conditions = []
            
            for condition in processed['conditions']:
                processed_condition = self._process_single_condition(condition)
                processed_conditions.append(processed_condition)
            
            processed['conditions'] = processed_conditions
        
        return processed
    
    def _process_single_condition(self, condition_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Traite une condition individuelle.
        
        Args:
            condition_data: Données de la condition
            
        Returns:
            Dict[str, Any]: Condition traitée
        """
        processed = condition_data.copy()
        
        # Détermine le type de condition en fonction de l'indicateur
        if 'indicator' in processed:
            indicator = processed['indicator'].lower()
            
            # Map des indicateurs vers leur type
            indicator_type_map = {
                # Techniques
                'rsi': 'technical',
                'macd': 'technical',
                'sma': 'technical',
                'ema': 'technical',
                'bollinger_bands': 'technical',
                'stochastic': 'technical',
                'atr': 'technical',
                'adx': 'technical',
                
                # Fondamentaux
                'pe_ratio': 'fundamental',
                'peg_ratio': 'fundamental',
                'price_to_book': 'fundamental',
                'debt_to_equity': 'fundamental',
                'roe': 'fundamental',
                'revenue_growth': 'fundamental',
                
                # Sentiment
                'news_sentiment': 'sentiment',
                'social_sentiment': 'sentiment',
                'vix': 'sentiment',
                
                # Volume
                'volume': 'volume',
                'obv': 'volume',
                
                # Prix
                'price': 'price',
                'close': 'price',
                'high': 'price',
                'low': 'price',
                
                # Risque
                'stop_loss': 'risk',
                'take_profit': 'risk'
            }
            
            condition_type = indicator_type_map.get(indicator, 'technical')
            processed['condition_type'] = condition_type
        
        return processed
    
    def _process_analysis(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Traite la section d'analyse.
        
        Args:
            analysis_data: Données d'analyse
            
        Returns:
            Dict[str, Any]: Analyse traitée
        """
        processed = {}
        
        for analysis_type in ['technical', 'fundamental', 'sentiment']:
            if analysis_type in analysis_data:
                processed[analysis_type] = self._process_analysis_indicators(
                    analysis_data[analysis_type], analysis_type
                )
        
        return processed
    
    def _process_analysis_indicators(self, indicators_data: list, analysis_type: str) -> list:
        """
        Traite les indicateurs d'un type d'analyse.
        
        Args:
            indicators_data: Liste des indicateurs
            analysis_type: Type d'analyse
            
        Returns:
            list: Indicateurs traités
        """
        processed_indicators = []
        
        for indicator in indicators_data:
            # Gestion des types : chaîne ou dictionnaire
            if isinstance(indicator, str):
                processed_indicator = {'type': indicator, 'indicator': indicator}
            elif isinstance(indicator, dict):
                processed_indicator = indicator.copy()
                # Ajoute le type d'analyse si manquant
                if 'type' not in processed_indicator and 'indicator' in processed_indicator:
                    processed_indicator['type'] = processed_indicator['indicator']
            else:
                # Ignore les types non supportés
                continue
            
            processed_indicators.append(processed_indicator)
        
        return processed_indicators
    
    def _handle_pydantic_error(self, error: PydanticValidationError) -> None:
        """
        Gère et formate les erreurs de validation Pydantic.
        
        Args:
            error: Erreur de validation Pydantic
            
        Raises:
            ValidationError: Erreur formatée
        """
        errors = []
        
        for err in error.errors():
            location = " -> ".join(str(loc) for loc in err['loc'])
            message = err['msg']
            errors.append(f"{location}: {message}")
        
        combined_message = "\n".join(errors)
        raise ValidationError(f"Erreurs de validation:\n{combined_message}")
    
    def validate_yaml_syntax(self, yaml_content: str) -> bool:
        """
        Valide uniquement la syntaxe YAML sans validation du contenu.
        
        Args:
            yaml_content: Contenu YAML à valider
            
        Returns:
            bool: True si la syntaxe est valide
            
        Raises:
            ParseError: Si la syntaxe YAML est invalide
        """
        try:
            yaml.load(yaml_content, Loader=self._yaml_loader)
            return True
        except yaml.YAMLError as e:
            line_info = getattr(e, 'problem_mark', None)
            line = line_info.line + 1 if line_info else None
            column = line_info.column + 1 if line_info else None
            raise ParseError(f"Syntaxe YAML invalide: {e}", line, column)
    
    def get_supported_indicators(self) -> Dict[str, list]:
        """
        Retourne la liste des indicateurs supportés par type.
        
        Returns:
            Dict[str, list]: Indicateurs supportés par type
        """
        return {
            'technical': [
                'rsi', 'macd', 'sma', 'ema', 'bollinger_bands',
                'stochastic', 'atr', 'adx', 'cci', 'williams_r',
                'roc', 'mfi', 'obv', 'vwap'
            ],
            'fundamental': [
                'pe_ratio', 'peg_ratio', 'price_to_book', 'price_to_sales',
                'debt_to_equity', 'current_ratio', 'roe', 'roa',
                'revenue_growth', 'earnings_growth', 'free_cash_flow'
            ],
            'sentiment': [
                'news_sentiment', 'social_sentiment', 'vix',
                'put_call_ratio', 'insider_trading', 'analyst_recommendations'
            ],
            'volume': [
                'volume', 'obv', 'volume_profile', 'mfi'
            ],
            'price': [
                'price', 'open', 'high', 'low', 'close', 'vwap'
            ],
            'risk': [
                'stop_loss', 'take_profit', 'max_drawdown', 'var', 'cvar'
            ]
        }