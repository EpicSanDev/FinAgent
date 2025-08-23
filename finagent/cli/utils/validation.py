"""
Utilitaires de validation pour la CLI FinAgent.

Ce module fournit des validateurs pour les entrées utilisateur,
symboles boursiers, montants, dates et autres paramètres.
"""

import re
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from typing import Any, List, Optional, Union, Tuple
from pathlib import Path

import click
from rich.console import Console

console = Console()


class ValidationError(Exception):
    """Exception levée lors d'une erreur de validation."""
    
    def __init__(self, message: str, field: str = "", suggestions: List[str] = None):
        super().__init__(message)
        self.message = message
        self.field = field
        self.suggestions = suggestions or []


def validate_symbol(symbol: str) -> str:
    """
    Valide un symbole boursier.
    
    Args:
        symbol: Symbole à valider
        
    Returns:
        Symbole validé en majuscules
        
    Raises:
        ValidationError: Si le symbole n'est pas valide
    """
    if not symbol:
        raise ValidationError("Le symbole ne peut pas être vide", "symbol")
    
    # Nettoyage du symbole
    clean_symbol = symbol.strip().upper()
    
    # Validation du format (lettres et optionnellement points pour les indices)
    if not re.match(r'^[A-Z]{1,10}(\.[A-Z]{1,5})?$', clean_symbol):
        raise ValidationError(
            f"Format de symbole invalide: '{symbol}'. "
            "Utilisez 1-10 lettres (ex: AAPL, MSFT, ^GSPC)",
            "symbol",
            ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]
        )
    
    # Vérifications supplémentaires
    if len(clean_symbol) > 10:
        raise ValidationError(
            f"Symbole trop long: '{symbol}' (max 10 caractères)",
            "symbol"
        )
    
    return clean_symbol


def validate_amount(amount: Union[str, int, float, Decimal], 
                   min_value: Optional[float] = None,
                   max_value: Optional[float] = None) -> Decimal:
    """
    Valide un montant monétaire.
    
    Args:
        amount: Montant à valider
        min_value: Valeur minimale autorisée
        max_value: Valeur maximale autorisée
        
    Returns:
        Montant validé comme Decimal
        
    Raises:
        ValidationError: Si le montant n'est pas valide
    """
    if amount is None or amount == "":
        raise ValidationError("Le montant ne peut pas être vide", "amount")
    
    try:
        if isinstance(amount, str):
            # Nettoyage de la chaîne (suppression des espaces, virgules, etc.)
            clean_amount = amount.strip().replace(",", "").replace(" ", "")
            
            # Support pour les suffixes (K, M, B)
            multiplier = 1
            if clean_amount.upper().endswith('K'):
                multiplier = 1_000
                clean_amount = clean_amount[:-1]
            elif clean_amount.upper().endswith('M'):
                multiplier = 1_000_000
                clean_amount = clean_amount[:-1]
            elif clean_amount.upper().endswith('B'):
                multiplier = 1_000_000_000
                clean_amount = clean_amount[:-1]
            
            # Suppression du symbole $ si présent
            if clean_amount.startswith('$'):
                clean_amount = clean_amount[1:]
            
            decimal_amount = Decimal(clean_amount) * multiplier
        else:
            decimal_amount = Decimal(str(amount))
            
    except (InvalidOperation, ValueError) as e:
        raise ValidationError(
            f"Format de montant invalide: '{amount}'. "
            "Utilisez un nombre décimal (ex: 1000, 1.5K, 2.3M)",
            "amount",
            ["1000", "1.5K", "2.3M", "10.50"]
        ) from e
    
    # Vérification des limites
    if min_value is not None and decimal_amount < Decimal(str(min_value)):
        raise ValidationError(
            f"Montant trop faible: {decimal_amount}. Minimum: {min_value}",
            "amount"
        )
    
    if max_value is not None and decimal_amount > Decimal(str(max_value)):
        raise ValidationError(
            f"Montant trop élevé: {decimal_amount}. Maximum: {max_value}",
            "amount"
        )
    
    return decimal_amount


def validate_percentage(percentage: Union[str, int, float]) -> float:
    """
    Valide un pourcentage.
    
    Args:
        percentage: Pourcentage à valider
        
    Returns:
        Pourcentage validé (0-100)
        
    Raises:
        ValidationError: Si le pourcentage n'est pas valide
    """
    if percentage is None or percentage == "":
        raise ValidationError("Le pourcentage ne peut pas être vide", "percentage")
    
    try:
        if isinstance(percentage, str):
            clean_pct = percentage.strip().replace("%", "").replace(" ", "")
            float_pct = float(clean_pct)
        else:
            float_pct = float(percentage)
            
    except ValueError as e:
        raise ValidationError(
            f"Format de pourcentage invalide: '{percentage}'. "
            "Utilisez un nombre (ex: 10, 15.5, 50%)",
            "percentage",
            ["10", "15.5", "50%", "0.25"]
        ) from e
    
    # Conversion si nécessaire (0.1 -> 10%)
    if 0 <= float_pct <= 1:
        float_pct *= 100
    
    if not 0 <= float_pct <= 100:
        raise ValidationError(
            f"Pourcentage hors limites: {float_pct}%. Doit être entre 0% et 100%",
            "percentage"
        )
    
    return float_pct


def validate_date(date_input: Union[str, datetime, date]) -> date:
    """
    Valide une date.
    
    Args:
        date_input: Date à valider
        
    Returns:
        Date validée
        
    Raises:
        ValidationError: Si la date n'est pas valide
    """
    if date_input is None or date_input == "":
        raise ValidationError("La date ne peut pas être vide", "date")
    
    if isinstance(date_input, date):
        return date_input
    
    if isinstance(date_input, datetime):
        return date_input.date()
    
    # Parsing de chaîne de caractères
    date_formats = [
        "%Y-%m-%d",  # 2024-01-15
        "%d/%m/%Y",  # 15/01/2024
        "%d-%m-%Y",  # 15-01-2024
        "%Y/%m/%d",  # 2024/01/15
        "%d %b %Y",  # 15 Jan 2024
        "%d %B %Y",  # 15 January 2024
    ]
    
    clean_date = str(date_input).strip()
    
    for date_format in date_formats:
        try:
            parsed_date = datetime.strptime(clean_date, date_format).date()
            
            # Vérification de plausibilité (pas dans le futur lointain)
            today = date.today()
            if parsed_date > today.replace(year=today.year + 10):
                raise ValidationError(
                    f"Date trop éloignée dans le futur: {parsed_date}",
                    "date"
                )
            
            return parsed_date
            
        except ValueError:
            continue
    
    raise ValidationError(
        f"Format de date invalide: '{date_input}'. "
        "Utilisez YYYY-MM-DD, DD/MM/YYYY, ou DD Mon YYYY",
        "date",
        ["2024-01-15", "15/01/2024", "15 Jan 2024"]
    )


def validate_timeframe(timeframe: str) -> str:
    """
    Valide un timeframe.
    
    Args:
        timeframe: Timeframe à valider
        
    Returns:
        Timeframe validé
        
    Raises:
        ValidationError: Si le timeframe n'est pas valide
    """
    if not timeframe:
        raise ValidationError("Le timeframe ne peut pas être vide", "timeframe")
    
    clean_timeframe = timeframe.strip().lower()
    
    # Timeframes valides
    valid_timeframes = {
        # Minutes
        '1m', '5m', '15m', '30m',
        # Heures  
        '1h', '2h', '4h', '6h', '12h',
        # Jours
        '1d', '3d', '5d',
        # Semaines/Mois/Années
        '1w', '2w', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y'
    }
    
    if clean_timeframe not in valid_timeframes:
        raise ValidationError(
            f"Timeframe invalide: '{timeframe}'. "
            f"Utilisez: {', '.join(sorted(valid_timeframes))}",
            "timeframe",
            ["1d", "1w", "1mo", "1y"]
        )
    
    return clean_timeframe


def validate_file_path(file_path: Union[str, Path], 
                      must_exist: bool = True,
                      extensions: Optional[List[str]] = None) -> Path:
    """
    Valide un chemin de fichier.
    
    Args:
        file_path: Chemin à valider
        must_exist: Si True, le fichier doit exister
        extensions: Extensions autorisées (ex: ['.yaml', '.yml'])
        
    Returns:
        Path validé
        
    Raises:
        ValidationError: Si le chemin n'est pas valide
    """
    if not file_path:
        raise ValidationError("Le chemin de fichier ne peut pas être vide", "file_path")
    
    path = Path(file_path)
    
    if must_exist and not path.exists():
        raise ValidationError(
            f"Fichier introuvable: {path}",
            "file_path"
        )
    
    if extensions:
        if path.suffix.lower() not in [ext.lower() for ext in extensions]:
            raise ValidationError(
                f"Extension de fichier invalide: {path.suffix}. "
                f"Extensions autorisées: {', '.join(extensions)}",
                "file_path",
                [f"example{ext}" for ext in extensions[:3]]
            )
    
    return path


def validate_strategy_name(name: str) -> str:
    """
    Valide un nom de stratégie.
    
    Args:
        name: Nom à valider
        
    Returns:
        Nom validé
        
    Raises:
        ValidationError: Si le nom n'est pas valide
    """
    if not name:
        raise ValidationError("Le nom de stratégie ne peut pas être vide", "strategy_name")
    
    clean_name = name.strip()
    
    # Vérification de la longueur
    if len(clean_name) < 3:
        raise ValidationError(
            f"Nom de stratégie trop court: '{name}' (minimum 3 caractères)",
            "strategy_name"
        )
    
    if len(clean_name) > 50:
        raise ValidationError(
            f"Nom de stratégie trop long: '{name}' (maximum 50 caractères)",
            "strategy_name"
        )
    
    # Vérification des caractères autorisés
    if not re.match(r'^[a-zA-Z0-9_\-\s]+$', clean_name):
        raise ValidationError(
            f"Nom de stratégie invalide: '{name}'. "
            "Utilisez uniquement des lettres, chiffres, espaces, - et _",
            "strategy_name",
            ["ma_strategie", "momentum-strategy", "Strategy 2024"]
        )
    
    return clean_name


def validate_portfolio_name(name: str) -> str:
    """
    Valide un nom de portefeuille.
    
    Args:
        name: Nom à valider
        
    Returns:
        Nom validé
        
    Raises:
        ValidationError: Si le nom n'est pas valide
    """
    return validate_strategy_name(name)  # Mêmes règles


# Validateurs Click personnalisés
class SymbolParamType(click.ParamType):
    """Type de paramètre Click pour les symboles boursiers."""
    
    name = "symbol"
    
    def convert(self, value: Any, param: Optional[click.Parameter], ctx: Optional[click.Context]) -> str:
        try:
            return validate_symbol(value)
        except ValidationError as e:
            self.fail(f"{e.message}", param, ctx)


class AmountParamType(click.ParamType):
    """Type de paramètre Click pour les montants."""
    
    name = "amount"
    
    def __init__(self, min_value: Optional[float] = None, max_value: Optional[float] = None):
        self.min_value = min_value
        self.max_value = max_value
    
    def convert(self, value: Any, param: Optional[click.Parameter], ctx: Optional[click.Context]) -> Decimal:
        try:
            return validate_amount(value, self.min_value, self.max_value)
        except ValidationError as e:
            self.fail(f"{e.message}", param, ctx)


class PercentageParamType(click.ParamType):
    """Type de paramètre Click pour les pourcentages."""
    
    name = "percentage"
    
    def convert(self, value: Any, param: Optional[click.Parameter], ctx: Optional[click.Context]) -> float:
        try:
            return validate_percentage(value)
        except ValidationError as e:
            self.fail(f"{e.message}", param, ctx)


class TimeframeParamType(click.ParamType):
    """Type de paramètre Click pour les timeframes."""
    
    name = "timeframe"
    
    def convert(self, value: Any, param: Optional[click.Parameter], ctx: Optional[click.Context]) -> str:
        try:
            return validate_timeframe(value)
        except ValidationError as e:
            self.fail(f"{e.message}", param, ctx)


# Instances réutilisables des types
SYMBOL = SymbolParamType()
AMOUNT = AmountParamType()
POSITIVE_AMOUNT = AmountParamType(min_value=0.01)
PERCENTAGE = PercentageParamType()
TIMEFRAME = TimeframeParamType()


def format_validation_error(error: ValidationError) -> str:
    """
    Formate une erreur de validation pour l'affichage.
    
    Args:
        error: Erreur de validation
        
    Returns:
        Message d'erreur formaté
    """
    message = f"❌ {error.message}"
    
    if error.suggestions:
        message += f"\n💡 Exemples valides: {', '.join(error.suggestions)}"
    
    return message


def interactive_validation(prompt: str, 
                         validator: callable,
                         max_attempts: int = 3) -> Any:
    """
    Validation interactive avec retry automatique.
    
    Args:
        prompt: Message à afficher à l'utilisateur
        validator: Fonction de validation à utiliser
        max_attempts: Nombre maximum de tentatives
        
    Returns:
        Valeur validée
        
    Raises:
        ValidationError: Si l'utilisateur dépasse le nombre de tentatives
    """
    for attempt in range(max_attempts):
        try:
            value = click.prompt(prompt)
            return validator(value)
        except ValidationError as e:
            console.print(format_validation_error(e), style="red")
            if attempt < max_attempts - 1:
                console.print(f"Tentative {attempt + 2}/{max_attempts}", style="yellow")
            else:
                raise ValidationError(f"Trop de tentatives invalides pour: {prompt}")
    
    # Ne devrait jamais arriver, mais pour la sécurité du type
    raise ValidationError("Erreur de validation inattendue")