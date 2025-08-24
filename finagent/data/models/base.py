"""
Modèles de base pour les données financières.

Ce module définit les classes de base et les types communs
utilisés dans tous les modèles de données.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, Union
from decimal import Decimal

from pydantic import BaseModel, Field, validator
import arrow


class TimeFrame(str, Enum):
    """Énumération des timeframes supportés."""
    
    MINUTE_1 = "1m"
    MINUTE_5 = "5m"
    MINUTE_15 = "15m"
    MINUTE_30 = "30m"
    HOUR_1 = "1h"
    HOUR_4 = "4h"
    DAY_1 = "1d"
    WEEK_1 = "1w"
    MONTH_1 = "1M"


class MarketStatus(str, Enum):
    """Statut du marché."""
    
    OPEN = "open"
    CLOSED = "closed"
    PRE_MARKET = "pre_market"
    AFTER_HOURS = "after_hours"
    HOLIDAY = "holiday"


class Currency(str, Enum):
    """Devises supportées."""
    
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"
    CHF = "CHF"
    CAD = "CAD"
    AUD = "AUD"


class BaseFinancialModel(BaseModel):
    """
    Modèle de base pour toutes les données financières.
    
    Fournit des fonctionnalités communes :
    - Validation automatique des types
    - Sérialisation/désérialisation JSON
    - Gestion des timestamps
    - Métadonnées de traçabilité
    """
    
    created_at: datetime = Field(
        default_factory=lambda: arrow.utcnow().datetime,
        description="Timestamp de création du modèle"
    )
    updated_at: Optional[datetime] = Field(
        None,
        description="Timestamp de dernière modification"
    )
    source: Optional[str] = Field(
        None,
        description="Source des données (ex: 'openbb', 'yfinance')"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Métadonnées additionnelles"
    )

    class Config:
        """Configuration Pydantic."""
        
        # Permet l'utilisation d'enums
        use_enum_values = True
        # Validation stricte des types
        validate_assignment = True
        # Sérialisation JSON avec support des datetime
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }
        # Exemple de données pour la documentation
        schema_extra = {
            "example": {
                "created_at": "2024-08-23T10:30:00Z",
                "updated_at": "2024-08-23T10:35:00Z",
                "source": "openbb",
                "metadata": {"version": "1.0", "quality": "high"}
            }
        }

    @validator('updated_at', pre=True, always=True)
    def set_updated_at(cls, v: Optional[datetime]) -> datetime:
        """Met à jour automatiquement updated_at lors des modifications."""
        return v or arrow.utcnow().datetime

    def update(self, **kwargs: Any) -> 'BaseFinancialModel':
        """
        Met à jour le modèle avec de nouvelles valeurs.
        
        Args:
            **kwargs: Nouvelles valeurs à appliquer
            
        Returns:
            Instance mise à jour du modèle
        """
        update_data = self.dict()
        update_data.update(kwargs)
        update_data['updated_at'] = arrow.utcnow().datetime
        return self.__class__(**update_data)

    def to_dict(self, exclude_none: bool = True) -> Dict[str, Any]:
        """
        Convertit le modèle en dictionnaire.
        
        Args:
            exclude_none: Exclure les valeurs None du résultat
            
        Returns:
            Dictionnaire représentant le modèle
        """
        return self.dict(exclude_none=exclude_none)

    def add_metadata(self, key: str, value: Any) -> None:
        """
        Ajoute une métadonnée au modèle.
        
        Args:
            key: Clé de la métadonnée
            value: Valeur de la métadonnée
        """
        self.metadata[key] = value
        self.updated_at = arrow.utcnow().datetime


class Symbol(BaseModel):
    """
    Modèle pour un symbole financier.
    
    Représente un instrument financier avec toutes ses informations.
    """
    
    symbol: str = Field(
        ...,
        description="Symbole ticker (ex: 'AAPL', 'MSFT')",
        min_length=1,
        max_length=10
    )
    name: Optional[str] = Field(
        None,
        description="Nom complet de l'entreprise"
    )
    exchange: Optional[str] = Field(
        None,
        description="Bourse de cotation (ex: 'NASDAQ', 'NYSE')"
    )
    currency: Currency = Field(
        Currency.USD,
        description="Devise de cotation"
    )
    sector: Optional[str] = Field(
        None,
        description="Secteur d'activité"
    )
    industry: Optional[str] = Field(
        None,
        description="Industrie spécifique"
    )
    market_cap: Optional[Decimal] = Field(
        None,
        description="Capitalisation boursière"
    )
    is_active: bool = Field(
        True,
        description="Le symbole est-il actuellement tradable"
    )

    @validator('symbol')
    def symbol_must_be_uppercase(cls, v: str) -> str:
        """Convertit le symbole en majuscules."""
        return v.upper().strip()

    @validator('market_cap')
    def market_cap_must_be_positive(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Valide que la capitalisation est positive."""
        if v is not None and v <= 0:
            raise ValueError('La capitalisation boursière doit être positive')
        return v

    def __str__(self) -> str:
        """Représentation textuelle du symbole."""
        if self.name:
            return f"{self.symbol} ({self.name})"
        return self.symbol

    def __hash__(self) -> int:
        """Hash basé sur le symbole pour utilisation dans des sets/dicts."""
        return hash(self.symbol)

    def __eq__(self, other: object) -> bool:
        """Égalité basée sur le symbole."""
        if isinstance(other, Symbol):
            return self.symbol == other.symbol
        if isinstance(other, str):
            return self.symbol == other.upper()
        return False


class DataQuality(BaseModel):
    """
    Modèle pour évaluer la qualité des données.
    
    Permet de tracker la fiabilité et la fraîcheur des données.
    """
    
    score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Score de qualité entre 0 et 1"
    )
    freshness_seconds: Optional[int] = Field(
        None,
        description="Fraîcheur des données en secondes"
    )
    completeness: float = Field(
        1.0,
        ge=0.0,
        le=1.0,
        description="Completude des données (0-1)"
    )
    accuracy: float = Field(
        1.0,
        ge=0.0,
        le=1.0,
        description="Précision estimée des données (0-1)"
    )
    source_reliability: float = Field(
        1.0,
        ge=0.0,
        le=1.0,
        description="Fiabilité de la source (0-1)"
    )
    issues: list[str] = Field(
        default_factory=list,
        description="Liste des problèmes détectés"
    )

    @property
    def is_stale(self) -> bool:
        """Indique si les données sont considérées comme obsolètes (>5min)."""
        if self.freshness_seconds is None:
            return False
        return self.freshness_seconds > 300  # 5 minutes

    @property
    def is_high_quality(self) -> bool:
        """Indique si les données sont de haute qualité (score > 0.8)."""
        return self.score > 0.8

    def add_issue(self, issue: str) -> None:
        """Ajoute un problème détecté."""
        if issue not in self.issues:
            self.issues.append(issue)
            # Recalcule le score en fonction du nombre de problèmes
            self.score = max(0.0, self.score - 0.1 * len(self.issues))