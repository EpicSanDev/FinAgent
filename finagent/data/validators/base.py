"""
Validators de base pour les données financières.

Ce module fournit les fonctions de validation communes
utilisées dans tout le système de données.
"""

import re
from datetime import datetime, date, timedelta
from typing import Any, List, Optional, Union, Dict
from decimal import Decimal, InvalidOperation

import arrow
from pydantic import validator, ValidationError

from ..models.base import TimeFrame, Currency, MarketStatus


class ValidationError(Exception):
    """Exception personnalisée pour les erreurs de validation."""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Any = None):
        self.message = message
        self.field = field
        self.value = value
        super().__init__(message)


class BaseValidator:
    """
    Classe de base pour tous les validators.
    
    Fournit des méthodes utilitaires communes.
    """
    
    @staticmethod
    def is_valid_symbol(symbol: str) -> bool:
        """
        Valide qu'un symbole respecte le format attendu.
        
        Args:
            symbol: Symbole à valider
            
        Returns:
            True si valide, False sinon
        """
        if not isinstance(symbol, str):
            return False
        
        # Nettoie le symbole
        symbol = symbol.strip().upper()
        
        # Vérifications de base
        if not symbol or len(symbol) > 10:
            return False
        
        # Pattern pour symboles valides
        # Lettres et chiffres, peut contenir des points ou tirets
        pattern = r'^[A-Z0-9][A-Z0-9.-]*[A-Z0-9]$|^[A-Z0-9]$'
        
        return bool(re.match(pattern, symbol))

    @staticmethod
    def normalize_symbol(symbol: str) -> str:
        """
        Normalise un symbole en format standard.
        
        Args:
            symbol: Symbole à normaliser
            
        Returns:
            Symbole normalisé
            
        Raises:
            ValidationError: Si le symbole est invalide
        """
        if not isinstance(symbol, str):
            raise ValidationError(f"Le symbole doit être une chaîne, reçu: {type(symbol)}")
        
        normalized = symbol.strip().upper()
        
        if not BaseValidator.is_valid_symbol(normalized):
            raise ValidationError(f"Symbole invalide: {symbol}")
        
        return normalized

    @staticmethod
    def is_valid_timeframe(timeframe: Union[str, TimeFrame]) -> bool:
        """
        Valide qu'un timeframe est supporté.
        
        Args:
            timeframe: Timeframe à valider
            
        Returns:
            True si valide, False sinon
        """
        if isinstance(timeframe, TimeFrame):
            return True
        
        if isinstance(timeframe, str):
            try:
                TimeFrame(timeframe)
                return True
            except ValueError:
                return False
        
        return False

    @staticmethod
    def normalize_timeframe(timeframe: Union[str, TimeFrame]) -> TimeFrame:
        """
        Normalise un timeframe en enum TimeFrame.
        
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
            try:
                return TimeFrame(timeframe.lower())
            except ValueError:
                raise ValidationError(f"Timeframe invalide: {timeframe}")
        
        raise ValidationError(f"Type de timeframe invalide: {type(timeframe)}")

    @staticmethod
    def is_valid_date_range(start_date: datetime, end_date: datetime) -> bool:
        """
        Valide qu'une plage de dates est cohérente.
        
        Args:
            start_date: Date de début
            end_date: Date de fin
            
        Returns:
            True si valide, False sinon
        """
        if not isinstance(start_date, datetime) or not isinstance(end_date, datetime):
            return False
        
        # La date de fin doit être après la date de début
        if end_date <= start_date:
            return False
        
        # Les dates ne doivent pas être dans le futur (sauf quelques minutes de tolérance)
        now = arrow.utcnow().naive
        future_tolerance = timedelta(minutes=5)
        
        if start_date > now + future_tolerance:
            return False
        
        return True

    @staticmethod
    def validate_positive_number(value: Union[int, float, Decimal], field_name: str = "value") -> Decimal:
        """
        Valide qu'un nombre est positif et le convertit en Decimal.
        
        Args:
            value: Valeur à valider
            field_name: Nom du champ pour les erreurs
            
        Returns:
            Valeur en Decimal
            
        Raises:
            ValidationError: Si la valeur est invalide
        """
        try:
            decimal_value = Decimal(str(value))
            if decimal_value <= 0:
                raise ValidationError(f"{field_name} doit être positif, reçu: {value}")
            return decimal_value
        except (InvalidOperation, ValueError, TypeError):
            raise ValidationError(f"{field_name} doit être un nombre valide, reçu: {value}")

    @staticmethod
    def validate_percentage(value: Union[int, float, Decimal], field_name: str = "value") -> Decimal:
        """
        Valide qu'une valeur est un pourcentage valide (0-100).
        
        Args:
            value: Valeur à valider
            field_name: Nom du champ pour les erreurs
            
        Returns:
            Valeur en Decimal
            
        Raises:
            ValidationError: Si la valeur est invalide
        """
        try:
            decimal_value = Decimal(str(value))
            if not (0 <= decimal_value <= 100):
                raise ValidationError(f"{field_name} doit être entre 0 et 100, reçu: {value}")
            return decimal_value
        except (InvalidOperation, ValueError, TypeError):
            raise ValidationError(f"{field_name} doit être un nombre valide, reçu: {value}")

    @staticmethod
    def validate_period(period: int, min_period: int = 1, max_period: int = 1000) -> int:
        """
        Valide qu'une période est dans une plage acceptable.
        
        Args:
            period: Période à valider
            min_period: Période minimale
            max_period: Période maximale
            
        Returns:
            Période validée
            
        Raises:
            ValidationError: Si la période est invalide
        """
        if not isinstance(period, int):
            raise ValidationError(f"La période doit être un entier, reçu: {type(period)}")
        
        if not (min_period <= period <= max_period):
            raise ValidationError(
                f"La période doit être entre {min_period} et {max_period}, reçu: {period}"
            )
        
        return period

    @staticmethod
    def validate_symbols_list(symbols: List[str], max_symbols: int = 50) -> List[str]:
        """
        Valide et normalise une liste de symboles.
        
        Args:
            symbols: Liste de symboles à valider
            max_symbols: Nombre maximum de symboles
            
        Returns:
            Liste de symboles normalisés
            
        Raises:
            ValidationError: Si la liste est invalide
        """
        if not isinstance(symbols, list):
            raise ValidationError(f"symbols doit être une liste, reçu: {type(symbols)}")
        
        if not symbols:
            raise ValidationError("La liste de symboles ne peut pas être vide")
        
        if len(symbols) > max_symbols:
            raise ValidationError(f"Trop de symboles ({len(symbols)}), maximum: {max_symbols}")
        
        normalized_symbols = []
        for symbol in symbols:
            try:
                normalized = BaseValidator.normalize_symbol(symbol)
                if normalized not in normalized_symbols:  # Évite les doublons
                    normalized_symbols.append(normalized)
            except ValidationError as e:
                raise ValidationError(f"Symbole invalide dans la liste: {e.message}")
        
        return normalized_symbols

    @staticmethod
    def validate_currency(currency: Union[str, Currency]) -> Currency:
        """
        Valide et normalise une devise.
        
        Args:
            currency: Devise à valider
            
        Returns:
            Devise normalisée
            
        Raises:
            ValidationError: Si la devise est invalide
        """
        if isinstance(currency, Currency):
            return currency
        
        if isinstance(currency, str):
            try:
                return Currency(currency.upper())
            except ValueError:
                raise ValidationError(f"Devise invalide: {currency}")
        
        raise ValidationError(f"Type de devise invalide: {type(currency)}")

    @staticmethod
    def validate_date_string(date_str: str, format_str: str = "%Y-%m-%d") -> datetime:
        """
        Valide et convertit une chaîne de date.
        
        Args:
            date_str: Chaîne de date
            format_str: Format attendu
            
        Returns:
            Date convertie
            
        Raises:
            ValidationError: Si la date est invalide
        """
        try:
            return datetime.strptime(date_str, format_str)
        except ValueError:
            raise ValidationError(f"Format de date invalide: {date_str} (attendu: {format_str})")

    @staticmethod
    def validate_url(url: str) -> str:
        """
        Valide basiquement une URL.
        
        Args:
            url: URL à valider
            
        Returns:
            URL validée
            
        Raises:
            ValidationError: Si l'URL est invalide
        """
        if not isinstance(url, str):
            raise ValidationError(f"L'URL doit être une chaîne, reçu: {type(url)}")
        
        url = url.strip()
        if not url:
            raise ValidationError("L'URL ne peut pas être vide")
        
        # Validation basique d'URL
        url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        if not re.match(url_pattern, url, re.IGNORECASE):
            raise ValidationError(f"Format d'URL invalide: {url}")
        
        return url

    @staticmethod
    def clean_text(text: str, max_length: Optional[int] = None) -> str:
        """
        Nettoie et valide un texte.
        
        Args:
            text: Texte à nettoyer
            max_length: Longueur maximale
            
        Returns:
            Texte nettoyé
            
        Raises:
            ValidationError: Si le texte est invalide
        """
        if not isinstance(text, str):
            raise ValidationError(f"Le texte doit être une chaîne, reçu: {type(text)}")
        
        # Nettoie les espaces
        cleaned = ' '.join(text.strip().split())
        
        if not cleaned:
            raise ValidationError("Le texte ne peut pas être vide")
        
        if max_length and len(cleaned) > max_length:
            raise ValidationError(f"Texte trop long ({len(cleaned)}), maximum: {max_length}")
        
        return cleaned


# Décorateurs pour la validation automatique
def validate_symbol_param(func):
    """Décorateur pour valider automatiquement les paramètres de symbole."""
    def wrapper(*args, **kwargs):
        # Valide le paramètre 'symbol' s'il existe
        if 'symbol' in kwargs:
            kwargs['symbol'] = BaseValidator.normalize_symbol(kwargs['symbol'])
        return func(*args, **kwargs)
    return wrapper


def validate_timeframe_param(func):
    """Décorateur pour valider automatiquement les paramètres de timeframe."""
    def wrapper(*args, **kwargs):
        # Valide le paramètre 'timeframe' s'il existe
        if 'timeframe' in kwargs:
            kwargs['timeframe'] = BaseValidator.normalize_timeframe(kwargs['timeframe'])
        return func(*args, **kwargs)
    return wrapper


def validate_date_range_params(func):
    """Décorateur pour valider automatiquement les plages de dates."""
    def wrapper(*args, **kwargs):
        start_date = kwargs.get('start_date')
        end_date = kwargs.get('end_date')
        
        if start_date and end_date:
            if not BaseValidator.is_valid_date_range(start_date, end_date):
                raise ValidationError("Plage de dates invalide")
        
        return func(*args, **kwargs)
    return wrapper