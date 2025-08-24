"""
Validators spécialisés pour les indicateurs techniques.

Ce module fournit la validation spécifique aux paramètres
et résultats des indicateurs techniques.
"""

from typing import Dict, List, Optional, Any, Union
from decimal import Decimal

from .base import BaseValidator, ValidationError
from ..models.base import TimeFrame
from ..models.technical_indicators import IndicatorType, BaseIndicator, MACD, BollingerBands


class IndicatorValidator(BaseValidator):
    """
    Validator spécialisé pour les indicateurs techniques.
    """
    
    # Plages valides pour chaque type d'indicateur
    INDICATOR_RANGES = {
        IndicatorType.RSI: (0, 100),
        IndicatorType.STOCH: (0, 100),
        IndicatorType.WILLIAMS_R: (-100, 0),
        IndicatorType.CCI: (-300, 300),
        IndicatorType.ADX: (0, 100),
    }
    
    # Périodes recommandées pour chaque indicateur
    RECOMMENDED_PERIODS = {
        IndicatorType.SMA: (5, 200),
        IndicatorType.EMA: (5, 200),
        IndicatorType.RSI: (2, 50),
        IndicatorType.STOCH: (5, 30),
        IndicatorType.MACD: (5, 50),  # Pour la période signal
        IndicatorType.BOLLINGER: (10, 50),
        IndicatorType.ATR: (5, 50),
    }

    @staticmethod
    def validate_indicator_period(
        indicator_type: IndicatorType,
        period: int
    ) -> int:
        """
        Valide la période d'un indicateur selon son type.
        
        Args:
            indicator_type: Type d'indicateur
            period: Période à valider
            
        Returns:
            Période validée
            
        Raises:
            ValidationError: Si la période est invalide
        """
        # Validation générale
        period = IndicatorValidator.validate_period(period, 1, 500)
        
        # Validation spécifique par type
        if indicator_type in IndicatorValidator.RECOMMENDED_PERIODS:
            min_period, max_period = IndicatorValidator.RECOMMENDED_PERIODS[indicator_type]
            
            if not (min_period <= period <= max_period):
                # Warning mais pas d'erreur
                pass  # On pourrait logger un warning ici
        
        return period

    @staticmethod
    def validate_indicator_value(
        indicator_type: IndicatorType,
        value: Union[Decimal, float],
        field_name: str = "value"
    ) -> Decimal:
        """
        Valide qu'une valeur d'indicateur est dans la plage attendue.
        
        Args:
            indicator_type: Type d'indicateur
            value: Valeur à valider
            field_name: Nom du champ pour les erreurs
            
        Returns:
            Valeur validée en Decimal
            
        Raises:
            ValidationError: Si la valeur est hors plage
        """
        try:
            decimal_value = Decimal(str(value))
        except (ValueError, TypeError):
            raise ValidationError(f"{field_name} doit être un nombre valide, reçu: {value}")
        
        # Vérification des plages spécifiques
        if indicator_type in IndicatorValidator.INDICATOR_RANGES:
            min_val, max_val = IndicatorValidator.INDICATOR_RANGES[indicator_type]
            
            if not (min_val <= decimal_value <= max_val):
                raise ValidationError(
                    f"{field_name} pour {indicator_type} doit être entre "
                    f"{min_val} et {max_val}, reçu: {decimal_value}"
                )
        
        return decimal_value

    @staticmethod
    def validate_rsi_parameters(period: int = 14) -> Dict[str, Any]:
        """
        Valide les paramètres du RSI.
        
        Args:
            period: Période du RSI
            
        Returns:
            Paramètres validés
        """
        validated_period = IndicatorValidator.validate_indicator_period(
            IndicatorType.RSI, period
        )
        
        return {'period': validated_period}

    @staticmethod
    def validate_rsi_value(value: Union[Decimal, float]) -> Decimal:
        """
        Valide une valeur RSI.
        
        Args:
            value: Valeur RSI
            
        Returns:
            Valeur validée
        """
        return IndicatorValidator.validate_indicator_value(
            IndicatorType.RSI, value, "RSI"
        )

    @staticmethod
    def validate_macd_parameters(
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ) -> Dict[str, Any]:
        """
        Valide les paramètres du MACD.
        
        Args:
            fast_period: Période EMA rapide
            slow_period: Période EMA lente
            signal_period: Période EMA signal
            
        Returns:
            Paramètres validés
            
        Raises:
            ValidationError: Si les paramètres sont invalides
        """
        # Validation des périodes individuelles
        fast = IndicatorValidator.validate_period(fast_period, 1, 100)
        slow = IndicatorValidator.validate_period(slow_period, 1, 100)
        signal = IndicatorValidator.validate_period(signal_period, 1, 50)
        
        # Validation des relations entre périodes
        if fast >= slow:
            raise ValidationError(
                f"La période rapide ({fast}) doit être < période lente ({slow})"
            )
        
        if signal > fast:
            raise ValidationError(
                f"La période signal ({signal}) doit être <= période rapide ({fast})"
            )
        
        return {
            'fast_period': fast,
            'slow_period': slow,
            'signal_period': signal
        }

    @staticmethod
    def validate_bollinger_parameters(
        period: int = 20,
        std_multiplier: float = 2.0
    ) -> Dict[str, Any]:
        """
        Valide les paramètres des Bandes de Bollinger.
        
        Args:
            period: Période de la moyenne mobile
            std_multiplier: Multiplicateur d'écart-type
            
        Returns:
            Paramètres validés
            
        Raises:
            ValidationError: Si les paramètres sont invalides
        """
        validated_period = IndicatorValidator.validate_indicator_period(
            IndicatorType.BOLLINGER, period
        )
        
        # Validation du multiplicateur
        if not isinstance(std_multiplier, (int, float)) or std_multiplier <= 0:
            raise ValidationError(
                f"Le multiplicateur d'écart-type doit être positif, reçu: {std_multiplier}"
            )
        
        if std_multiplier > 5.0:
            raise ValidationError(
                f"Multiplicateur trop élevé: {std_multiplier} (maximum recommandé: 5.0)"
            )
        
        return {
            'period': validated_period,
            'std_multiplier': Decimal(str(std_multiplier))
        }

    @staticmethod
    def validate_bollinger_bands(
        middle: Decimal,
        upper: Decimal,
        lower: Decimal,
        std_dev: Decimal
    ) -> Dict[str, Decimal]:
        """
        Valide la cohérence des Bandes de Bollinger.
        
        Args:
            middle: Bande du milieu
            upper: Bande supérieure
            lower: Bande inférieure
            std_dev: Écart-type
            
        Returns:
            Bandes validées
            
        Raises:
            ValidationError: Si les bandes sont incohérentes
        """
        # Validation des prix positifs
        middle = IndicatorValidator.validate_positive_number(middle, "middle_band")
        upper = IndicatorValidator.validate_positive_number(upper, "upper_band")
        lower = IndicatorValidator.validate_positive_number(lower, "lower_band")
        std_dev = IndicatorValidator.validate_positive_number(std_dev, "std_dev")
        
        # Validation de l'ordre des bandes
        if upper <= middle:
            raise ValidationError(f"Bande supérieure ({upper}) doit être > milieu ({middle})")
        
        if lower >= middle:
            raise ValidationError(f"Bande inférieure ({lower}) doit être < milieu ({middle})")
        
        # Validation de la symétrie approximative
        upper_distance = upper - middle
        lower_distance = middle - lower
        
        # Tolérance de 5% pour la symétrie
        symmetry_ratio = min(upper_distance, lower_distance) / max(upper_distance, lower_distance)
        if symmetry_ratio < 0.95:
            # Warning mais pas d'erreur (peut être normal selon la volatilité)
            pass
        
        return {
            'middle_band': middle,
            'upper_band': upper,
            'lower_band': lower,
            'std_dev': std_dev
        }

    @staticmethod
    def validate_stochastic_parameters(
        k_period: int = 14,
        d_period: int = 3,
        smooth_k: int = 1
    ) -> Dict[str, Any]:
        """
        Valide les paramètres du Stochastique.
        
        Args:
            k_period: Période pour %K
            d_period: Période pour %D
            smooth_k: Lissage de %K
            
        Returns:
            Paramètres validés
        """
        k_period = IndicatorValidator.validate_period(k_period, 1, 100)
        d_period = IndicatorValidator.validate_period(d_period, 1, 50)
        smooth_k = IndicatorValidator.validate_period(smooth_k, 1, 10)
        
        return {
            'k_period': k_period,
            'd_period': d_period,
            'smooth_k': smooth_k
        }

    @staticmethod
    def validate_stochastic_values(
        k_percent: Union[Decimal, float],
        d_percent: Union[Decimal, float]
    ) -> Dict[str, Decimal]:
        """
        Valide les valeurs du Stochastique.
        
        Args:
            k_percent: Valeur %K
            d_percent: Valeur %D
            
        Returns:
            Valeurs validées
        """
        k_val = IndicatorValidator.validate_indicator_value(
            IndicatorType.STOCH, k_percent, "%K"
        )
        d_val = IndicatorValidator.validate_indicator_value(
            IndicatorType.STOCH, d_percent, "%D"
        )
        
        return {
            'k_percent': k_val,
            'd_percent': d_val
        }

    @staticmethod
    def validate_moving_average_parameters(
        ma_type: IndicatorType,
        period: int,
        timeframe: TimeFrame
    ) -> Dict[str, Any]:
        """
        Valide les paramètres d'une moyenne mobile.
        
        Args:
            ma_type: Type de moyenne mobile
            period: Période
            timeframe: Timeframe
            
        Returns:
            Paramètres validés
            
        Raises:
            ValidationError: Si les paramètres sont invalides
        """
        # Vérification du type
        valid_ma_types = [IndicatorType.SMA, IndicatorType.EMA, IndicatorType.WMA]
        if ma_type not in valid_ma_types:
            raise ValidationError(f"Type de moyenne mobile invalide: {ma_type}")
        
        # Validation de la période
        validated_period = IndicatorValidator.validate_indicator_period(ma_type, period)
        
        # Validation de la cohérence période/timeframe
        IndicatorValidator._validate_period_timeframe_coherence(validated_period, timeframe)
        
        return {
            'ma_type': ma_type,
            'period': validated_period,
            'timeframe': timeframe
        }

    @staticmethod
    def _validate_period_timeframe_coherence(period: int, timeframe: TimeFrame) -> None:
        """
        Valide la cohérence entre période et timeframe.
        
        Args:
            period: Période de l'indicateur
            timeframe: Timeframe des données
            
        Raises:
            ValidationError: Si la combinaison est incohérente
        """
        # Conversions approximatives en minutes
        timeframe_minutes = {
            TimeFrame.MINUTE_1: 1,
            TimeFrame.MINUTE_5: 5,
            TimeFrame.MINUTE_15: 15,
            TimeFrame.MINUTE_30: 30,
            TimeFrame.HOUR_1: 60,
            TimeFrame.HOUR_4: 240,
            TimeFrame.DAY_1: 1440,
            TimeFrame.WEEK_1: 10080,
            TimeFrame.MONTH_1: 43200
        }
        
        tf_minutes = timeframe_minutes.get(timeframe)
        if tf_minutes is None:
            return  # Timeframe non reconnu, pas de validation
        
        total_minutes = period * tf_minutes
        
        # Avertissements pour des combinaisons problématiques
        if total_minutes < 60:  # Moins d'1 heure
            # Très court terme, peut être volatil
            pass
        elif total_minutes > 525600:  # Plus d'1 an
            # Très long terme, peut être trop lissé
            pass

    @staticmethod
    def validate_indicator_collection(
        indicators: Dict[str, BaseIndicator],
        symbol: str,
        timeframe: TimeFrame
    ) -> Dict[str, BaseIndicator]:
        """
        Valide une collection d'indicateurs.
        
        Args:
            indicators: Dictionnaire des indicateurs
            symbol: Symbole attendu
            timeframe: Timeframe attendu
            
        Returns:
            Collection validée
            
        Raises:
            ValidationError: Si la collection est invalide
        """
        if not indicators:
            raise ValidationError("La collection d'indicateurs ne peut pas être vide")
        
        validated = {}
        
        for name, indicator in indicators.items():
            # Validation du nom
            if not isinstance(name, str) or not name.strip():
                raise ValidationError(f"Nom d'indicateur invalide: {name}")
            
            # Validation de l'indicateur
            if not isinstance(indicator, BaseIndicator):
                raise ValidationError(f"Type d'indicateur invalide pour {name}")
            
            # Vérification de la cohérence
            if indicator.symbol.symbol != symbol.upper():
                raise ValidationError(
                    f"Symbole incohérent pour {name}: {indicator.symbol.symbol} "
                    f"(attendu: {symbol.upper()})"
                )
            
            if indicator.timeframe != timeframe:
                raise ValidationError(
                    f"Timeframe incohérent pour {name}: {indicator.timeframe} "
                    f"(attendu: {timeframe})"
                )
            
            validated[name] = indicator
        
        return validated

    @staticmethod
    def detect_indicator_divergences(
        price_data: List[Decimal],
        indicator_data: List[Decimal],
        indicator_type: IndicatorType,
        lookback_periods: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Détecte les divergences entre prix et indicateur.
        
        Args:
            price_data: Données de prix (closes)
            indicator_data: Données de l'indicateur
            indicator_type: Type d'indicateur
            lookback_periods: Nombre de périodes à analyser
            
        Returns:
            Liste des divergences détectées
        """
        if len(price_data) != len(indicator_data):
            raise ValidationError("Les listes de prix et indicateur doivent avoir la même taille")
        
        if len(price_data) < lookback_periods + 2:
            return []  # Pas assez de données
        
        divergences = []
        
        # Analyse des dernières périodes
        for i in range(lookback_periods, len(price_data)):
            price_current = price_data[i]
            price_previous = price_data[i - lookback_periods]
            
            indicator_current = indicator_data[i]
            indicator_previous = indicator_data[i - lookback_periods]
            
            # Détection divergence haussière
            if (price_current < price_previous and 
                indicator_current > indicator_previous):
                divergences.append({
                    'type': 'bullish_divergence',
                    'index': i,
                    'strength': abs((indicator_current - indicator_previous) / indicator_previous),
                    'description': 'Prix baisse mais indicateur monte'
                })
            
            # Détection divergence baissière
            elif (price_current > price_previous and 
                  indicator_current < indicator_previous):
                divergences.append({
                    'type': 'bearish_divergence',
                    'index': i,
                    'strength': abs((indicator_current - indicator_previous) / indicator_previous),
                    'description': 'Prix monte mais indicateur baisse'
                })
        
        return divergences

    @staticmethod
    def calculate_indicator_correlation(
        indicator1_data: List[Decimal],
        indicator2_data: List[Decimal],
        min_correlation: float = 0.7
    ) -> Dict[str, Any]:
        """
        Calcule la corrélation entre deux séries d'indicateurs.
        
        Args:
            indicator1_data: Données du premier indicateur
            indicator2_data: Données du second indicateur
            min_correlation: Corrélation minimale pour alerte
            
        Returns:
            Résultats de l'analyse de corrélation
        """
        if len(indicator1_data) != len(indicator2_data):
            raise ValidationError("Les séries doivent avoir la même longueur")
        
        if len(indicator1_data) < 10:
            return {'correlation': None, 'significance': 'insufficient_data'}
        
        # Calcul simple de corrélation de Pearson
        try:
            import numpy as np
            
            data1 = np.array([float(x) for x in indicator1_data])
            data2 = np.array([float(x) for x in indicator2_data])
            
            correlation = np.corrcoef(data1, data2)[0, 1]
            
            # Évaluation de la signification
            if abs(correlation) >= min_correlation:
                significance = 'high'
            elif abs(correlation) >= 0.5:
                significance = 'medium'
            else:
                significance = 'low'
            
            return {
                'correlation': float(correlation),
                'significance': significance,
                'sample_size': len(indicator1_data),
                'is_redundant': abs(correlation) > 0.9
            }
            
        except ImportError:
            # Fallback sans numpy
            return {
                'correlation': None,
                'significance': 'calculation_unavailable'
            }