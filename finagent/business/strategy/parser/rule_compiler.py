"""
Compilateur de règles pour les stratégies de trading.

Ce module compile les règles de trading en code exécutable optimisé
pour une évaluation rapide en temps réel.
"""

import logging
import ast
import inspect
from typing import Dict, List, Any, Callable, Optional, Union
from dataclasses import dataclass
from decimal import Decimal

from ..models.rule_models import (
    Rule, BuyConditions, SellConditions, ConditionOperator,
    RuleOperator, TechnicalCondition, FundamentalCondition,
    SentimentCondition, VolumeCondition, PriceCondition, RiskCondition
)
from ..models.condition_models import IndicatorType, ComparisonOperator

logger = logging.getLogger(__name__)


class CompilationError(Exception):
    """Exception levée lors d'erreurs de compilation."""
    
    def __init__(self, message: str, rule_context: Optional[str] = None):
        self.message = message
        self.rule_context = rule_context
        super().__init__(self._format_message())
    
    def _format_message(self) -> str:
        """Formate le message d'erreur."""
        if self.rule_context:
            return f"Erreur de compilation dans {self.rule_context}: {self.message}"
        return f"Erreur de compilation: {self.message}"


@dataclass
class CompiledCondition:
    """Condition compilée avec fonction d'évaluation."""
    condition_id: str
    evaluator: Callable[[Dict[str, Any]], bool]
    weight: Decimal
    metadata: Dict[str, Any]


@dataclass
class CompiledRule:
    """Règle compilée avec toutes ses conditions."""
    rule_id: str
    buy_conditions: List[CompiledCondition]
    sell_conditions: List[CompiledCondition]
    buy_operator: RuleOperator
    sell_operator: RuleOperator
    metadata: Dict[str, Any]
    
    def evaluate_buy(self, market_data: Dict[str, Any]) -> tuple[bool, float]:
        """
        Évalue les conditions d'achat.
        
        Args:
            market_data: Données de marché
            
        Returns:
            tuple: (signal_triggered, confidence_score)
        """
        return self._evaluate_conditions(
            self.buy_conditions, self.buy_operator, market_data
        )
    
    def evaluate_sell(self, market_data: Dict[str, Any]) -> tuple[bool, float]:
        """
        Évalue les conditions de vente.
        
        Args:
            market_data: Données de marché
            
        Returns:
            tuple: (signal_triggered, confidence_score)
        """
        return self._evaluate_conditions(
            self.sell_conditions, self.sell_operator, market_data
        )
    
    def _evaluate_conditions(
        self, 
        conditions: List[CompiledCondition], 
        operator: RuleOperator,
        market_data: Dict[str, Any]
    ) -> tuple[bool, float]:
        """Évalue une liste de conditions avec un opérateur."""
        if not conditions:
            return False, 0.0
        
        results = []
        weights = []
        
        for condition in conditions:
            try:
                result = condition.evaluator(market_data)
                results.append(result)
                weights.append(float(condition.weight))
            except Exception as e:
                logger.warning(f"Erreur lors de l'évaluation de {condition.condition_id}: {e}")
                results.append(False)
                weights.append(float(condition.weight))
        
        # Calcul du signal selon l'opérateur
        if operator == RuleOperator.AND:
            signal = all(results)
        elif operator == RuleOperator.OR:
            signal = any(results)
        elif operator == RuleOperator.NOT:
            signal = not results[0] if results else False
        else:
            signal = False
        
        # Calcul du score de confiance pondéré
        if weights:
            weighted_score = sum(
                float(result) * weight for result, weight in zip(results, weights)
            ) / sum(weights)
        else:
            weighted_score = 0.0
        
        return signal, weighted_score


class RuleCompiler:
    """Compilateur de règles de trading en code exécutable."""
    
    def __init__(self):
        """Initialise le compilateur."""
        self.logger = logging.getLogger(__name__)
        
        # Registre des fonctions d'évaluation par indicateur
        self._indicator_evaluators = self._build_indicator_evaluators()
        
        # Registre des opérateurs de comparaison
        self._comparison_operators = self._build_comparison_operators()
    
    def compile(self, rules: Dict[str, Any], rule_id: str = "default") -> CompiledRule:
        """
        Compile un ensemble de règles.
        
        Args:
            rules: Règles à compiler
            rule_id: Identifiant de la règle
            
        Returns:
            CompiledRule: Règle compilée
            
        Raises:
            CompilationError: Si la compilation échoue
        """
        try:
            # Compile les conditions d'achat
            buy_conditions = []
            buy_operator = RuleOperator.AND
            
            if 'buy_conditions' in rules:
                buy_data = rules['buy_conditions']
                if isinstance(buy_data, dict):
                    buy_operator = RuleOperator(buy_data.get('operator', 'AND'))
                    conditions_list = buy_data.get('conditions', [])
                    
                    for i, condition_data in enumerate(conditions_list):
                        condition_id = f"{rule_id}_buy_{i}"
                        compiled_condition = self._compile_condition(
                            condition_data, condition_id
                        )
                        buy_conditions.append(compiled_condition)
            
            # Compile les conditions de vente
            sell_conditions = []
            sell_operator = RuleOperator.OR
            
            if 'sell_conditions' in rules:
                sell_data = rules['sell_conditions']
                if isinstance(sell_data, dict):
                    sell_operator = RuleOperator(sell_data.get('operator', 'OR'))
                    conditions_list = sell_data.get('conditions', [])
                    
                    for i, condition_data in enumerate(conditions_list):
                        condition_id = f"{rule_id}_sell_{i}"
                        compiled_condition = self._compile_condition(
                            condition_data, condition_id
                        )
                        sell_conditions.append(compiled_condition)
            
            # Métadonnées
            metadata = {
                'compiled_at': str(logger.handlers[0].formatter.formatTime() if logger.handlers else ''),
                'buy_conditions_count': len(buy_conditions),
                'sell_conditions_count': len(sell_conditions)
            }
            
            return CompiledRule(
                rule_id=rule_id,
                buy_conditions=buy_conditions,
                sell_conditions=sell_conditions,
                buy_operator=buy_operator,
                sell_operator=sell_operator,
                metadata=metadata
            )
            
        except Exception as e:
            raise CompilationError(f"Échec de compilation: {e}", rule_id)
    
    def _compile_condition(self, condition_data: Dict[str, Any], condition_id: str) -> CompiledCondition:
        """
        Compile une condition individuelle.
        
        Args:
            condition_data: Données de la condition
            condition_id: Identifiant de la condition
            
        Returns:
            CompiledCondition: Condition compilée
        """
        # Extraction des paramètres
        indicator = condition_data.get('indicator', '').lower()
        operator = condition_data.get('operator', 'greater')
        value = condition_data.get('value')
        weight = Decimal(str(condition_data.get('weight', 1.0)))
        
        # Paramètres additionnels
        timeframe = condition_data.get('timeframe', '1d')
        lookback = condition_data.get('lookback', 1)
        parameters = condition_data.get('parameters', {})
        
        # Détermine le type de condition
        condition_type = self._determine_condition_type(indicator)
        
        # Crée la fonction d'évaluation
        evaluator = self._create_evaluator(
            condition_type, indicator, operator, value, 
            timeframe, lookback, parameters
        )
        
        # Métadonnées
        metadata = {
            'indicator': indicator,
            'operator': operator,
            'value': value,
            'timeframe': timeframe,
            'lookback': lookback,
            'condition_type': condition_type,
            'parameters': parameters
        }
        
        return CompiledCondition(
            condition_id=condition_id,
            evaluator=evaluator,
            weight=weight,
            metadata=metadata
        )
    
    def _determine_condition_type(self, indicator: str) -> str:
        """Détermine le type de condition basé sur l'indicateur."""
        technical_indicators = {
            'rsi', 'macd', 'sma', 'ema', 'bollinger_bands', 'stochastic',
            'atr', 'adx', 'cci', 'williams_r', 'roc', 'mfi', 'vwap'
        }
        
        fundamental_indicators = {
            'pe_ratio', 'peg_ratio', 'price_to_book', 'debt_to_equity',
            'roe', 'revenue_growth', 'earnings_growth', 'free_cash_flow'
        }
        
        sentiment_indicators = {
            'news_sentiment', 'social_sentiment', 'vix', 'put_call_ratio'
        }
        
        volume_indicators = {
            'volume', 'obv', 'volume_profile'
        }
        
        price_indicators = {
            'price', 'open', 'high', 'low', 'close'
        }
        
        risk_indicators = {
            'stop_loss', 'take_profit', 'max_drawdown'
        }
        
        if indicator in technical_indicators:
            return 'technical'
        elif indicator in fundamental_indicators:
            return 'fundamental'
        elif indicator in sentiment_indicators:
            return 'sentiment'
        elif indicator in volume_indicators:
            return 'volume'
        elif indicator in price_indicators:
            return 'price'
        elif indicator in risk_indicators:
            return 'risk'
        else:
            return 'technical'  # Par défaut
    
    def _create_evaluator(
        self,
        condition_type: str,
        indicator: str,
        operator: str,
        value: Any,
        timeframe: str,
        lookback: int,
        parameters: Dict[str, Any]
    ) -> Callable[[Dict[str, Any]], bool]:
        """
        Crée une fonction d'évaluation pour une condition.
        
        Args:
            condition_type: Type de condition
            indicator: Nom de l'indicateur
            operator: Opérateur de comparaison
            value: Valeur de référence
            timeframe: Timeframe
            lookback: Période de lookback
            parameters: Paramètres additionnels
            
        Returns:
            Callable: Fonction d'évaluation
        """
        # Récupère l'évaluateur d'indicateur
        indicator_func = self._indicator_evaluators.get(indicator)
        if not indicator_func:
            # Évaluateur générique
            indicator_func = self._generic_indicator_evaluator
        
        # Récupère l'opérateur de comparaison
        comparison_func = self._comparison_operators.get(operator)
        if not comparison_func:
            comparison_func = self._comparison_operators['greater']
        
        def evaluator(market_data: Dict[str, Any]) -> bool:
            """Fonction d'évaluation compilée."""
            try:
                # Calcule la valeur de l'indicateur
                indicator_value = indicator_func(
                    market_data, timeframe, lookback, parameters
                )
                
                # Compare avec la valeur de référence
                return comparison_func(indicator_value, value)
                
            except Exception as e:
                self.logger.warning(
                    f"Erreur dans l'évaluation de {indicator}: {e}"
                )
                return False
        
        return evaluator
    
    def _build_indicator_evaluators(self) -> Dict[str, Callable]:
        """Construit le registre des évaluateurs d'indicateurs."""
        return {
            # Indicateurs techniques
            'rsi': self._evaluate_rsi,
            'macd': self._evaluate_macd,
            'sma': self._evaluate_sma,
            'ema': self._evaluate_ema,
            'bollinger_bands': self._evaluate_bollinger_bands,
            'stochastic': self._evaluate_stochastic,
            'atr': self._evaluate_atr,
            'volume': self._evaluate_volume,
            
            # Indicateurs fondamentaux
            'pe_ratio': self._evaluate_pe_ratio,
            'revenue_growth': self._evaluate_revenue_growth,
            'roe': self._evaluate_roe,
            
            # Indicateurs de sentiment
            'news_sentiment': self._evaluate_news_sentiment,
            'vix': self._evaluate_vix,
            
            # Prix
            'price': self._evaluate_price,
            'close': self._evaluate_close,
            
            # Risque
            'stop_loss': self._evaluate_stop_loss,
            'take_profit': self._evaluate_take_profit
        }
    
    def _build_comparison_operators(self) -> Dict[str, Callable]:
        """Construit le registre des opérateurs de comparaison."""
        return {
            'greater': lambda x, y: x > y,
            '>': lambda x, y: x > y,
            'greater_equal': lambda x, y: x >= y,
            '>=': lambda x, y: x >= y,
            'less': lambda x, y: x < y,
            '<': lambda x, y: x < y,
            'less_equal': lambda x, y: x <= y,
            '<=': lambda x, y: x <= y,
            'equal': lambda x, y: x == y,
            '==': lambda x, y: x == y,
            'not_equal': lambda x, y: x != y,
            '!=': lambda x, y: x != y,
            'above': lambda x, y: x > y,
            'below': lambda x, y: x < y,
            'between': lambda x, y: y[0] <= x <= y[1] if isinstance(y, list) and len(y) == 2 else False,
            'outside': lambda x, y: x < y[0] or x > y[1] if isinstance(y, list) and len(y) == 2 else False,
            'crossover_up': self._crossover_up,
            'crossover_down': self._crossover_down
        }
    
    # Évaluateurs d'indicateurs techniques
    def _evaluate_rsi(self, market_data: Dict[str, Any], timeframe: str, lookback: int, params: Dict) -> float:
        """Évalue l'indicateur RSI."""
        period = params.get('period', 14)
        prices = market_data.get('prices', {}).get(timeframe, [])
        
        if len(prices) < period:
            return 50.0  # Valeur neutre par défaut
        
        # Calcul RSI simplifié (version réelle utiliserait une bibliothèque spécialisée)
        gains = []
        losses = []
        
        for i in range(1, min(period + 1, len(prices))):
            change = prices[i]['close'] - prices[i-1]['close']
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        if not gains and not losses:
            return 50.0
        
        avg_gain = sum(gains) / len(gains) if gains else 0
        avg_loss = sum(losses) / len(losses) if losses else 0
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _evaluate_sma(self, market_data: Dict[str, Any], timeframe: str, lookback: int, params: Dict) -> float:
        """Évalue la moyenne mobile simple."""
        period = params.get('period', 20)
        prices = market_data.get('prices', {}).get(timeframe, [])
        
        if len(prices) < period:
            return 0.0
        
        recent_prices = prices[-period:]
        sma = sum(p['close'] for p in recent_prices) / period
        
        return sma
    
    def _evaluate_volume(self, market_data: Dict[str, Any], timeframe: str, lookback: int, params: Dict) -> float:
        """Évalue l'indicateur de volume."""
        prices = market_data.get('prices', {}).get(timeframe, [])
        
        if not prices:
            return 0.0
        
        current_volume = prices[-1].get('volume', 0)
        
        # Volume moyen sur les dernières périodes
        avg_period = params.get('avg_period', 20)
        if len(prices) >= avg_period:
            avg_volume = sum(p.get('volume', 0) for p in prices[-avg_period:]) / avg_period
            return current_volume / avg_volume if avg_volume > 0 else 1.0
        
        return current_volume
    
    def _evaluate_price(self, market_data: Dict[str, Any], timeframe: str, lookback: int, params: Dict) -> float:
        """Évalue le prix."""
        prices = market_data.get('prices', {}).get(timeframe, [])
        price_type = params.get('price_type', 'close')
        
        if not prices:
            return 0.0
        
        return prices[-1].get(price_type, 0.0)
    
    def _evaluate_close(self, market_data: Dict[str, Any], timeframe: str, lookback: int, params: Dict) -> float:
        """Évalue le prix de clôture."""
        prices = market_data.get('prices', {}).get(timeframe, [])
        
        if not prices:
            return 0.0
        
        return prices[-1].get('close', 0.0)
    
    # Évaluateurs d'indicateurs fondamentaux
    def _evaluate_pe_ratio(self, market_data: Dict[str, Any], timeframe: str, lookback: int, params: Dict) -> float:
        """Évalue le ratio P/E."""
        fundamentals = market_data.get('fundamentals', {})
        return fundamentals.get('pe_ratio', 0.0)
    
    def _evaluate_revenue_growth(self, market_data: Dict[str, Any], timeframe: str, lookback: int, params: Dict) -> float:
        """Évalue la croissance du chiffre d'affaires."""
        fundamentals = market_data.get('fundamentals', {})
        return fundamentals.get('revenue_growth', 0.0)
    
    def _evaluate_roe(self, market_data: Dict[str, Any], timeframe: str, lookback: int, params: Dict) -> float:
        """Évalue le ROE."""
        fundamentals = market_data.get('fundamentals', {})
        return fundamentals.get('roe', 0.0)
    
    # Évaluateurs de sentiment
    def _evaluate_news_sentiment(self, market_data: Dict[str, Any], timeframe: str, lookback: int, params: Dict) -> float:
        """Évalue le sentiment des actualités."""
        sentiment = market_data.get('sentiment', {})
        return sentiment.get('news_sentiment', 0.5)
    
    def _evaluate_vix(self, market_data: Dict[str, Any], timeframe: str, lookback: int, params: Dict) -> float:
        """Évalue l'indice VIX."""
        market_indicators = market_data.get('market_indicators', {})
        return market_indicators.get('vix', 20.0)
    
    # Évaluateurs de risque
    def _evaluate_stop_loss(self, market_data: Dict[str, Any], timeframe: str, lookback: int, params: Dict) -> float:
        """Évalue la condition de stop-loss."""
        position = market_data.get('position', {})
        entry_price = position.get('entry_price', 0.0)
        current_price = self._evaluate_close(market_data, timeframe, lookback, params)
        stop_loss_pct = params.get('percentage', 0.05)
        
        if entry_price > 0:
            loss_pct = (entry_price - current_price) / entry_price
            return 1.0 if loss_pct >= stop_loss_pct else 0.0
        
        return 0.0
    
    def _evaluate_take_profit(self, market_data: Dict[str, Any], timeframe: str, lookback: int, params: Dict) -> float:
        """Évalue la condition de take-profit."""
        position = market_data.get('position', {})
        entry_price = position.get('entry_price', 0.0)
        current_price = self._evaluate_close(market_data, timeframe, lookback, params)
        take_profit_pct = params.get('percentage', 0.15)
        
        if entry_price > 0:
            profit_pct = (current_price - entry_price) / entry_price
            return 1.0 if profit_pct >= take_profit_pct else 0.0
        
        return 0.0
    
    # Évaluateurs spéciaux
    def _evaluate_macd(self, market_data: Dict[str, Any], timeframe: str, lookback: int, params: Dict) -> float:
        """Évalue l'indicateur MACD."""
        # Implémentation simplifiée - version réelle utiliserait une bibliothèque spécialisée
        fast_period = params.get('fast_period', 12)
        slow_period = params.get('slow_period', 26)
        
        fast_ema = self._evaluate_sma(market_data, timeframe, lookback, {'period': fast_period})
        slow_ema = self._evaluate_sma(market_data, timeframe, lookback, {'period': slow_period})
        
        return fast_ema - slow_ema
    
    def _evaluate_ema(self, market_data: Dict[str, Any], timeframe: str, lookback: int, params: Dict) -> float:
        """Évalue la moyenne mobile exponentielle."""
        # Implémentation simplifiée
        return self._evaluate_sma(market_data, timeframe, lookback, params)
    
    def _evaluate_bollinger_bands(self, market_data: Dict[str, Any], timeframe: str, lookback: int, params: Dict) -> Dict[str, float]:
        """Évalue les bandes de Bollinger."""
        period = params.get('period', 20)
        std_dev = params.get('std_deviation', 2.0)
        
        sma = self._evaluate_sma(market_data, timeframe, lookback, {'period': period})
        
        # Calcul simplifié de l'écart-type
        prices = market_data.get('prices', {}).get(timeframe, [])
        if len(prices) < period:
            return {'upper': sma, 'middle': sma, 'lower': sma}
        
        recent_prices = [p['close'] for p in prices[-period:]]
        variance = sum((p - sma) ** 2 for p in recent_prices) / period
        std = variance ** 0.5
        
        return {
            'upper': sma + (std_dev * std),
            'middle': sma,
            'lower': sma - (std_dev * std)
        }
    
    def _evaluate_stochastic(self, market_data: Dict[str, Any], timeframe: str, lookback: int, params: Dict) -> Dict[str, float]:
        """Évalue l'oscillateur stochastique."""
        k_period = params.get('k_period', 14)
        prices = market_data.get('prices', {}).get(timeframe, [])
        
        if len(prices) < k_period:
            return {'k': 50.0, 'd': 50.0}
        
        recent_prices = prices[-k_period:]
        highs = [p['high'] for p in recent_prices]
        lows = [p['low'] for p in recent_prices]
        current_close = prices[-1]['close']
        
        highest_high = max(highs)
        lowest_low = min(lows)
        
        if highest_high == lowest_low:
            k_value = 50.0
        else:
            k_value = ((current_close - lowest_low) / (highest_high - lowest_low)) * 100
        
        return {'k': k_value, 'd': k_value}  # Simplification
    
    def _evaluate_atr(self, market_data: Dict[str, Any], timeframe: str, lookback: int, params: Dict) -> float:
        """Évalue l'Average True Range."""
        period = params.get('period', 14)
        prices = market_data.get('prices', {}).get(timeframe, [])
        
        if len(prices) < period + 1:
            return 0.0
        
        true_ranges = []
        for i in range(1, min(period + 1, len(prices))):
            high = prices[i]['high']
            low = prices[i]['low']
            prev_close = prices[i-1]['close']
            
            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
            true_ranges.append(tr)
        
        return sum(true_ranges) / len(true_ranges) if true_ranges else 0.0
    
    def _generic_indicator_evaluator(self, market_data: Dict[str, Any], timeframe: str, lookback: int, params: Dict) -> float:
        """Évaluateur générique pour indicateurs non spécifiés."""
        return 0.0
    
    def _crossover_up(self, current_values: List[float], reference_values: List[float]) -> bool:
        """Détecte un croisement vers le haut."""
        if len(current_values) < 2 or len(reference_values) < 2:
            return False
        
        return (current_values[-2] <= reference_values[-2] and 
                current_values[-1] > reference_values[-1])
    
    def _crossover_down(self, current_values: List[float], reference_values: List[float]) -> bool:
        """Détecte un croisement vers le bas."""
        if len(current_values) < 2 or len(reference_values) < 2:
            return False
        
        return (current_values[-2] >= reference_values[-2] and 
                current_values[-1] < reference_values[-1])
    
    def get_supported_indicators(self) -> List[str]:
        """Retourne la liste des indicateurs supportés."""
        return list(self._indicator_evaluators.keys())
    
    def get_supported_operators(self) -> List[str]:
        """Retourne la liste des opérateurs supportés."""
        return list(self._comparison_operators.keys())