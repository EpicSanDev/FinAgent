"""
Module de validation pour les données financières.

Ce module fournit des validateurs pour s'assurer de la cohérence
et de la qualité des données financières.
"""

import re
from datetime import datetime, timedelta
from typing import Optional, Union, List
from decimal import Decimal

from .models.base import TimeFrame, Symbol


class ValidationError(Exception):
    """Exception levée lors d'erreurs de validation."""
    
    def __init__(self, message: str, suggestions: Optional[List[str]] = None):
        self.message = message
        self.suggestions = suggestions or []
        super().__init__(message)


class BaseValidator:
    """Validateur de base pour les données financières."""
    
    # Patterns de validation
    SYMBOL_PATTERN = re.compile(r'^[A-Z]{1,5}(\.[A-Z]{1,2})?$')
    
    @classmethod
    def normalize_symbol(cls, symbol: str) -> str:
        """
        Normalise un symbole financier.
        
        Args:
            symbol: Symbole à normaliser
            
        Returns:
            Symbole normalisé
            
        Raises:
            ValidationError: Si le symbole est invalide
        """
        if not symbol or not isinstance(symbol, str):
            raise ValidationError("Le symbole doit être une chaîne non vide")
        
        # Nettoyage et normalisation
        normalized = symbol.strip().upper()
        
        # Validation du format
        if not cls.SYMBOL_PATTERN.match(normalized):
            suggestions = [
                "Utiliser uniquement des lettres majuscules",
                "Longueur entre 1 et 5 caractères",
                "Format: SYMBOL ou SYMBOL.EX"
            ]
            raise ValidationError(
                f"Format de symbole invalide: {symbol}",
                suggestions=suggestions
            )
        
        return normalized
    
    @classmethod
    def normalize_timeframe(cls, timeframe: Union[str, TimeFrame]) -> TimeFrame:
        """
        Normalise un timeframe.
        
        Args:
            timeframe: Timeframe à normaliser
            
        Returns:
            TimeFrame normalisé
            
        Raises:
            ValidationError: Si le timeframe est invalide
        """
        if isinstance(timeframe, TimeFrame):
            return timeframe
        
        if isinstance(timeframe, str):
            # Mapping des formats courants
            timeframe_mapping = {
                '1m': TimeFrame.MINUTE_1,
                '5m': TimeFrame.MINUTE_5,
                '15m': TimeFrame.MINUTE_15,
                '30m': TimeFrame.MINUTE_30,
                '1h': TimeFrame.HOUR_1,
                '4h': TimeFrame.HOUR_4,
                '1d': TimeFrame.DAY_1,
                '1w': TimeFrame.WEEK_1,
                '1mo': TimeFrame.MONTH_1,
                '1M': TimeFrame.MONTH_1,
                # Formats alternatifs
                'daily': TimeFrame.DAY_1,
                'weekly': TimeFrame.WEEK_1,
                'monthly': TimeFrame.MONTH_1,
            }
            
            normalized_tf = timeframe_mapping.get(timeframe.lower())
            if normalized_tf:
                return normalized_tf
        
        # Si aucune correspondance trouvée
        valid_formats = list(TimeFrame.__members__.keys())
        raise ValidationError(
            f"Timeframe invalide: {timeframe}",
            suggestions=valid_formats[:5]  # Montrer les 5 premiers
        )
    
    @classmethod
    def validate_date_string(cls, date_str: str) -> datetime:
        """
        Valide et convertit une chaîne de date.
        
        Args:
            date_str: Date sous forme de chaîne
            
        Returns:
            Objet datetime
            
        Raises:
            ValidationError: Si le format est invalide
        """
        if not date_str:
            raise ValidationError("Date requise")
        
        # Formats supportés
        date_formats = [
            '%Y-%m-%d',
            '%Y/%m/%d',
            '%d/%m/%Y',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%SZ'
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        raise ValidationError(
            f"Format de date invalide: {date_str}",
            suggestions=['YYYY-MM-DD', 'YYYY/MM/DD', 'DD/MM/YYYY']
        )
    
    @classmethod
    def is_valid_date_range(cls, start_date: datetime, end_date: datetime) -> bool:
        """
        Vérifie si une plage de dates est valide.
        
        Args:
            start_date: Date de début
            end_date: Date de fin
            
        Returns:
            True si la plage est valide
        """
        if start_date >= end_date:
            return False
        
        # Vérifier que les dates ne sont pas trop anciennes (>10 ans)
        ten_years_ago = datetime.now() - timedelta(days=3650)
        if start_date < ten_years_ago:
            return False
        
        # Vérifier que les dates ne sont pas dans le futur
        if end_date > datetime.now():
            return False
        
        return True
    
    @classmethod
    def validate_price(cls, price: Union[float, Decimal, str]) -> Decimal:
        """
        Valide et normalise un prix.
        
        Args:
            price: Prix à valider
            
        Returns:
            Prix sous forme de Decimal
            
        Raises:
            ValidationError: Si le prix est invalide
        """
        try:
            decimal_price = Decimal(str(price))
            
            if decimal_price < 0:
                raise ValidationError("Le prix doit être positif")
            
            if decimal_price > Decimal('1000000'):  # 1 million max
                raise ValidationError("Prix trop élevé (max: 1,000,000)")
            
            return decimal_price
            
        except (ValueError, TypeError) as e:
            raise ValidationError(f"Format de prix invalide: {price}")
    
    @classmethod
    def validate_volume(cls, volume: Union[int, float, str]) -> int:
        """
        Valide et normalise un volume.
        
        Args:
            volume: Volume à valider
            
        Returns:
            Volume sous forme d'entier
            
        Raises:
            ValidationError: Si le volume est invalide
        """
        try:
            int_volume = int(float(volume))
            
            if int_volume < 0:
                raise ValidationError("Le volume doit être positif")
            
            return int_volume
            
        except (ValueError, TypeError):
            raise ValidationError(f"Format de volume invalide: {volume}")
    
    @classmethod
    def validate_percentage(cls, percentage: Union[float, str]) -> float:
        """
        Valide un pourcentage.
        
        Args:
            percentage: Pourcentage à valider
            
        Returns:
            Pourcentage sous forme de float
            
        Raises:
            ValidationError: Si le pourcentage est invalide
        """
        try:
            float_percentage = float(percentage)
            
            # Vérification de plausibilité (entre -100% et +1000%)
            if float_percentage < -100 or float_percentage > 1000:
                raise ValidationError("Pourcentage hors limites (-100% à +1000%)")
            
            return float_percentage
            
        except (ValueError, TypeError):
            raise ValidationError(f"Format de pourcentage invalide: {percentage}")


class MarketDataValidator(BaseValidator):
    """Validateur spécialisé pour les données de marché."""
    
    @classmethod
    def validate_ohlcv(cls, open_price: Decimal, high: Decimal, 
                      low: Decimal, close: Decimal, volume: Optional[int] = None) -> bool:
        """
        Valide la cohérence des données OHLCV.
        
        Args:
            open_price: Prix d'ouverture
            high: Prix maximum
            low: Prix minimum
            close: Prix de clôture
            volume: Volume (optionnel)
            
        Returns:
            True si les données sont cohérentes
            
        Raises:
            ValidationError: Si les données sont incohérentes
        """
        # Validation des prix individuels
        prices = [open_price, high, low, close]
        for price in prices:
            cls.validate_price(price)
        
        # Validation de la cohérence OHLC
        if high < max(open_price, low, close):
            raise ValidationError("Le prix maximum doit être le plus élevé")
        
        if low > min(open_price, high, close):
            raise ValidationError("Le prix minimum doit être le plus bas")
        
        if volume is not None:
            cls.validate_volume(volume)
        
        return True


class TechnicalIndicatorValidator(BaseValidator):
    """Validateur pour les indicateurs techniques."""
    
    @classmethod
    def validate_rsi(cls, rsi_value: float) -> float:
        """
        Valide une valeur RSI.
        
        Args:
            rsi_value: Valeur RSI à valider
            
        Returns:
            Valeur RSI validée
            
        Raises:
            ValidationError: Si la valeur est invalide
        """
        if not 0 <= rsi_value <= 100:
            raise ValidationError("RSI doit être entre 0 et 100")
        
        return rsi_value
    
    @classmethod
    def validate_macd(cls, macd_value: float) -> float:
        """
        Valide une valeur MACD.
        
        Args:
            macd_value: Valeur MACD à valider
            
        Returns:
            Valeur MACD validée
        """
        # MACD peut être négatif, on vérifie juste que c'est un nombre valide
        if not isinstance(macd_value, (int, float)) or abs(macd_value) > 1000:
            raise ValidationError("Valeur MACD invalide")
        
        return float(macd_value)
    
    @classmethod
    def validate_moving_average(cls, ma_value: float, price_reference: float) -> float:
        """
        Valide une moyenne mobile.
        
        Args:
            ma_value: Valeur de la moyenne mobile
            price_reference: Prix de référence pour validation
            
        Returns:
            Valeur de moyenne mobile validée
            
        Raises:
            ValidationError: Si la valeur est incohérente
        """
        cls.validate_price(ma_value)
        
        # Vérification de plausibilité (la MA ne devrait pas être trop éloignée du prix)
        if abs(ma_value - price_reference) > price_reference * 2:
            raise ValidationError("Moyenne mobile trop éloignée du prix de référence")
        
        return ma_value