"""
Exceptions personnalisées pour FinAgent

Ce module définit toutes les exceptions spécifiques à l'application
pour une gestion d'erreurs cohérente et informative.
"""

from typing import Optional, Dict, Any


class FinAgentException(Exception):
    """
    Exception de base pour toutes les erreurs spécifiques à FinAgent.
    
    Toutes les autres exceptions personnalisées doivent hériter de cette classe.
    """
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ConfigurationError(FinAgentException):
    """Erreur de configuration de l'application."""
    pass


class APIConnectionError(FinAgentException):
    """Erreur de connexion aux APIs externes (OpenBB, Claude, etc.)."""
    pass


class DataValidationError(FinAgentException):
    """Erreur de validation des données financières."""
    pass


class StrategyError(FinAgentException):
    """Erreur dans l'exécution ou la configuration d'une stratégie."""
    pass


class PortfolioError(FinAgentException):
    """Erreur dans la gestion du portefeuille."""
    pass


class SecurityError(FinAgentException):
    """Erreur de sécurité (chiffrement, authentification, etc.)."""
    pass


class CacheError(FinAgentException):
    """Erreur dans le système de cache."""
    pass


class DatabaseError(FinAgentException):
    """Erreur de base de données."""
    pass


class AIServiceError(FinAgentException):
    """Erreur dans les services d'intelligence artificielle."""
    pass


# Alias pour compatibilité
FinAgentError = FinAgentException

# TODO: Ajouter d'autres exceptions spécifiques selon les besoins
# lors du développement des modules métier