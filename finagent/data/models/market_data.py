"""
Modèles pour les données de marché financier.

Ce module définit les structures de données pour les prix,
volumes, et autres informations de marché.
"""

from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field, validator
import arrow

from .base import BaseFinancialModel, Symbol, TimeFrame, MarketStatus, Currency, DataQuality


class Price(BaseModel):
    """
    Modèle pour un prix simple.
    
    Utilisé pour les prix actuels, bid/ask, etc.
    """
    
    value: Decimal = Field(
        ...,
        description="Valeur du prix",
        gt=0
    )
    currency: Currency = Field(
        Currency.USD,
        description="Devise du prix"
    )
    timestamp: datetime = Field(
        default_factory=lambda: arrow.utcnow().datetime,
        description="Timestamp du prix"
    )

    @validator('value')
    def validate_price_precision(cls, v: Decimal) -> Decimal:
        """Limite la précision à 4 décimales."""
        return round(v, 4)

    def __str__(self) -> str:
        """Représentation textuelle du prix."""
        return f"{self.value:.2f} {self.currency}"

    def to_float(self) -> float:
        """Convertit le prix en float."""
        return float(self.value)


class OHLCV(BaseFinancialModel):
    """
    Modèle pour les données OHLCV (Open, High, Low, Close, Volume).
    
    Représente une bougie/barre de prix pour une période donnée.
    """
    
    symbol: Symbol = Field(
        ...,
        description="Symbole financier"
    )
    timestamp: datetime = Field(
        ...,
        description="Timestamp de début de la période"
    )
    timeframe: TimeFrame = Field(
        ...,
        description="Timeframe de la bougie"
    )
    open: Decimal = Field(
        ...,
        description="Prix d'ouverture",
        gt=0
    )
    high: Decimal = Field(
        ...,
        description="Prix le plus haut",
        gt=0
    )
    low: Decimal = Field(
        ...,
        description="Prix le plus bas",
        gt=0
    )
    close: Decimal = Field(
        ...,
        description="Prix de fermeture",
        gt=0
    )
    volume: Optional[int] = Field(
        None,
        description="Volume échangé",
        ge=0
    )
    adjusted_close: Optional[Decimal] = Field(
        None,
        description="Prix de fermeture ajusté (dividendes, splits)",
        gt=0
    )
    quality: Optional[DataQuality] = Field(
        None,
        description="Métrique de qualité des données"
    )

    @validator('high')
    def high_must_be_highest(cls, v: Decimal, values: Dict[str, Any]) -> Decimal:
        """Valide que high est le prix le plus élevé."""
        if 'open' in values and v < values['open']:
            raise ValueError('High doit être >= Open')
        if 'low' in values and v < values['low']:
            raise ValueError('High doit être >= Low')
        return v

    @validator('low')
    def low_must_be_lowest(cls, v: Decimal, values: Dict[str, Any]) -> Decimal:
        """Valide que low est le prix le plus bas."""
        if 'open' in values and v > values['open']:
            raise ValueError('Low doit être <= Open')
        if 'close' in values and v > values['close']:
            raise ValueError('Low doit être <= Close')
        return v

    @validator('close')
    def close_within_range(cls, v: Decimal, values: Dict[str, Any]) -> Decimal:
        """Valide que close est dans la fourchette high-low."""
        if 'high' in values and v > values['high']:
            raise ValueError('Close doit être <= High')
        if 'low' in values and v < values['low']:
            raise ValueError('Close doit être >= Low')
        return v

    @property
    def change(self) -> Decimal:
        """Variation absolue (close - open)."""
        return self.close - self.open

    @property
    def change_percent(self) -> Decimal:
        """Variation en pourcentage."""
        if self.open == 0:
            return Decimal('0')
        return (self.change / self.open) * 100

    @property
    def is_green(self) -> bool:
        """Indique si la bougie est verte (hausse)."""
        return self.close > self.open

    @property
    def is_red(self) -> bool:
        """Indique si la bougie est rouge (baisse)."""
        return self.close < self.open

    @property
    def is_doji(self) -> bool:
        """Indique si c'est un doji (open ≈ close)."""
        body_percent = abs(self.change_percent)
        return body_percent < Decimal('0.1')  # Moins de 0.1% de variation

    @property
    def body_size(self) -> Decimal:
        """Taille du corps de la bougie."""
        return abs(self.close - self.open)

    @property
    def upper_shadow(self) -> Decimal:
        """Taille de la mèche supérieure."""
        return self.high - max(self.open, self.close)

    @property
    def lower_shadow(self) -> Decimal:
        """Taille de la mèche inférieure."""
        return min(self.open, self.close) - self.low

    @property
    def true_range(self) -> Decimal:
        """True Range (pour calcul ATR)."""
        # Nécessite la bougie précédente pour un calcul exact
        # Ici on retourne high - low
        return self.high - self.low

    def to_ohlc(self) -> tuple[float, float, float, float]:
        """Retourne un tuple OHLC pour les calculs."""
        return (
            float(self.open),
            float(self.high),
            float(self.low),
            float(self.close)
        )

    def __str__(self) -> str:
        """Représentation textuelle de l'OHLCV."""
        return (
            f"{self.symbol.symbol} {self.timeframe} "
            f"O:{self.open:.2f} H:{self.high:.2f} "
            f"L:{self.low:.2f} C:{self.close:.2f} "
            f"V:{self.volume or 0}"
        )


class QuoteData(BaseFinancialModel):
    """
    Modèle pour les données de cotation en temps réel.
    
    Inclut bid/ask, market status et informations de session.
    """
    
    symbol: Symbol = Field(
        ...,
        description="Symbole financier"
    )
    last_price: Price = Field(
        ...,
        description="Dernier prix échangé"
    )
    bid: Optional[Price] = Field(
        None,
        description="Meilleur prix d'achat"
    )
    ask: Optional[Price] = Field(
        None,
        description="Meilleur prix de vente"
    )
    bid_size: Optional[int] = Field(
        None,
        description="Quantité à l'achat",
        ge=0
    )
    ask_size: Optional[int] = Field(
        None,
        description="Quantité à la vente",
        ge=0
    )
    volume: Optional[int] = Field(
        None,
        description="Volume total de la session",
        ge=0
    )
    market_status: MarketStatus = Field(
        MarketStatus.CLOSED,
        description="Statut du marché"
    )
    previous_close: Optional[Decimal] = Field(
        None,
        description="Clôture précédente",
        gt=0
    )
    day_high: Optional[Decimal] = Field(
        None,
        description="Plus haut de la journée",
        gt=0
    )
    day_low: Optional[Decimal] = Field(
        None,
        description="Plus bas de la journée",
        gt=0
    )
    open_price: Optional[Decimal] = Field(
        None,
        description="Prix d'ouverture de la session",
        gt=0
    )

    @property
    def spread(self) -> Optional[Decimal]:
        """Écart bid-ask."""
        if self.bid and self.ask:
            return self.ask.value - self.bid.value
        return None

    @property
    def spread_percent(self) -> Optional[Decimal]:
        """Écart bid-ask en pourcentage."""
        if self.spread and self.last_price.value > 0:
            return (self.spread / self.last_price.value) * 100
        return None

    @property
    def change_from_previous(self) -> Optional[Decimal]:
        """Variation depuis la clôture précédente."""
        if self.previous_close:
            return self.last_price.value - self.previous_close
        return None

    @property
    def change_percent_from_previous(self) -> Optional[Decimal]:
        """Variation en % depuis la clôture précédente."""
        if self.previous_close and self.previous_close > 0:
            change = self.change_from_previous
            if change is not None:
                return (change / self.previous_close) * 100
        return None

    @property
    def is_trading(self) -> bool:
        """Indique si le marché est ouvert pour trading."""
        return self.market_status in [MarketStatus.OPEN, MarketStatus.PRE_MARKET, MarketStatus.AFTER_HOURS]

    def __str__(self) -> str:
        """Représentation textuelle de la cotation."""
        return f"{self.symbol.symbol}: {self.last_price} ({self.market_status})"


class MarketDataCollection(BaseModel):
    """
    Collection de données de marché pour plusieurs symboles.
    
    Permet de gérer efficacement des lots de données.
    """
    
    data: List[OHLCV] = Field(
        default_factory=list,
        description="Liste des données OHLCV"
    )
    timeframe: TimeFrame = Field(
        ...,
        description="Timeframe commun à toutes les données"
    )
    start_date: Optional[datetime] = Field(
        None,
        description="Date de début de la collection"
    )
    end_date: Optional[datetime] = Field(
        None,
        description="Date de fin de la collection"
    )
    total_records: int = Field(
        0,
        description="Nombre total d'enregistrements",
        ge=0
    )

    @validator('total_records', always=True)
    def update_total_records(cls, v: int, values: Dict[str, Any]) -> int:
        """Met à jour automatiquement le nombre d'enregistrements."""
        if 'data' in values:
            return len(values['data'])
        return v

    def add_ohlcv(self, ohlcv: OHLCV) -> None:
        """Ajoute une donnée OHLCV à la collection."""
        if ohlcv.timeframe != self.timeframe:
            raise ValueError(f"Timeframe mismatch: {ohlcv.timeframe} != {self.timeframe}")
        
        self.data.append(ohlcv)
        self.total_records = len(self.data)
        
        # Met à jour les dates de début/fin
        if not self.start_date or ohlcv.timestamp < self.start_date:
            self.start_date = ohlcv.timestamp
        if not self.end_date or ohlcv.timestamp > self.end_date:
            self.end_date = ohlcv.timestamp

    def get_by_symbol(self, symbol: str) -> List[OHLCV]:
        """Récupère toutes les données pour un symbole donné."""
        return [ohlcv for ohlcv in self.data if ohlcv.symbol.symbol == symbol.upper()]

    def get_symbols(self) -> List[str]:
        """Récupère la liste des symboles uniques."""
        return list(set(ohlcv.symbol.symbol for ohlcv in self.data))

    def sort_by_timestamp(self) -> None:
        """Trie les données par timestamp."""
        self.data.sort(key=lambda x: x.timestamp)

    def to_dataframe(self) -> 'pandas.DataFrame':
        """
        Convertit la collection en DataFrame pandas.
        
        Returns:
            DataFrame avec les colonnes OHLCV
        """
        try:
            import pandas as pd
            
            records = []
            for ohlcv in self.data:
                record = {
                    'symbol': ohlcv.symbol.symbol,
                    'timestamp': ohlcv.timestamp,
                    'open': float(ohlcv.open),
                    'high': float(ohlcv.high),
                    'low': float(ohlcv.low),
                    'close': float(ohlcv.close),
                    'volume': ohlcv.volume,
                    'timeframe': ohlcv.timeframe
                }
                records.append(record)
            
            return pd.DataFrame(records)
        except ImportError:
            raise ImportError("pandas n'est pas disponible pour la conversion")

    def __len__(self) -> int:
        """Retourne le nombre d'éléments dans la collection."""
        return len(self.data)

    def __iter__(self):
        """Permet l'itération sur les données."""
        return iter(self.data)

    def __getitem__(self, index: int) -> OHLCV:
        """Permet l'accès par index."""
        return self.data[index]