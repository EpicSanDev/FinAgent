"""
Modèles pour les indicateurs techniques.

Ce module définit les structures de données pour tous les
indicateurs techniques utilisés dans l'analyse financière.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any, Union
from enum import Enum

from pydantic import BaseModel, Field, validator
import arrow

from .base import BaseFinancialModel, Symbol, TimeFrame, DataQuality


class IndicatorType(str, Enum):
    """Types d'indicateurs techniques."""
    
    # Moyennes mobiles
    SMA = "sma"  # Simple Moving Average
    EMA = "ema"  # Exponential Moving Average
    WMA = "wma"  # Weighted Moving Average
    
    # Oscillateurs
    RSI = "rsi"  # Relative Strength Index
    STOCH = "stoch"  # Stochastic
    WILLIAMS_R = "williams_r"  # Williams %R
    CCI = "cci"  # Commodity Channel Index
    
    # Volatilité
    BOLLINGER = "bollinger"  # Bollinger Bands
    ATR = "atr"  # Average True Range
    
    # Momentum
    MACD = "macd"  # MACD
    ADX = "adx"  # Average Directional Index
    
    # Volume
    OBV = "obv"  # On Balance Volume
    VOLUME_SMA = "volume_sma"  # Volume Moving Average


class BaseIndicator(BaseFinancialModel):
    """
    Classe de base pour tous les indicateurs techniques.
    
    Fournit les propriétés communes à tous les indicateurs.
    """
    
    symbol: Symbol = Field(
        ...,
        description="Symbole financier"
    )
    timestamp: datetime = Field(
        ...,
        description="Timestamp de calcul de l'indicateur"
    )
    timeframe: TimeFrame = Field(
        ...,
        description="Timeframe utilisé pour le calcul"
    )
    indicator_type: IndicatorType = Field(
        ...,
        description="Type d'indicateur"
    )
    period: int = Field(
        ...,
        description="Période utilisée pour le calcul",
        gt=0
    )
    quality: Optional[DataQuality] = Field(
        None,
        description="Qualité des données source"
    )

    def __str__(self) -> str:
        """Représentation textuelle de l'indicateur."""
        return f"{self.indicator_type.upper()}({self.period}) for {self.symbol.symbol}"


class SimpleIndicator(BaseIndicator):
    """
    Indicateur simple avec une seule valeur.
    
    Utilisé pour SMA, EMA, RSI, ATR, etc.
    """
    
    value: Decimal = Field(
        ...,
        description="Valeur de l'indicateur"
    )
    
    @property
    def signal_strength(self) -> Optional[str]:
        """Évalue la force du signal selon le type d'indicateur."""
        if self.indicator_type == IndicatorType.RSI:
            if self.value > 70:
                return "SURACHETÉ"
            elif self.value < 30:
                return "SURVENDU"
            else:
                return "NEUTRE"
        
        return None

    def __str__(self) -> str:
        """Représentation textuelle avec valeur."""
        base = super().__str__()
        return f"{base} = {self.value:.2f}"


class MovingAverage(SimpleIndicator):
    """
    Modèle spécialisé pour les moyennes mobiles.
    """
    
    indicator_type: IndicatorType = Field(
        ...,
        description="Type de moyenne mobile (SMA, EMA, WMA)"
    )
    
    @validator('indicator_type')
    def validate_ma_type(cls, v: IndicatorType) -> IndicatorType:
        """Valide que c'est bien un type de moyenne mobile."""
        valid_types = [IndicatorType.SMA, IndicatorType.EMA, IndicatorType.WMA]
        if v not in valid_types:
            raise ValueError(f"Type invalide pour MovingAverage: {v}")
        return v

    def compare_to_price(self, current_price: Decimal) -> str:
        """Compare le prix actuel à la moyenne mobile."""
        if current_price > self.value:
            return "AU-DESSUS"
        elif current_price < self.value:
            return "EN-DESSOUS"
        else:
            return "SUR_LA_LIGNE"


class RSI(SimpleIndicator):
    """
    Modèle spécialisé pour le RSI (Relative Strength Index).
    """
    
    indicator_type: IndicatorType = Field(
        default=IndicatorType.RSI,
        description="Type fixé à RSI"
    )
    
    @validator('value')
    def validate_rsi_range(cls, v: Decimal) -> Decimal:
        """Valide que le RSI est entre 0 et 100."""
        if not (0 <= v <= 100):
            raise ValueError(f"RSI doit être entre 0 et 100, reçu: {v}")
        return v

    @property
    def is_overbought(self) -> bool:
        """Indique si le RSI est en survente."""
        return self.value > 70

    @property
    def is_oversold(self) -> bool:
        """Indique si le RSI est en surachat."""
        return self.value < 30

    @property
    def signal(self) -> str:
        """Signal du RSI."""
        if self.is_overbought:
            return "VENTE"
        elif self.is_oversold:
            return "ACHAT"
        else:
            return "NEUTRE"


class MACD(BaseIndicator):
    """
    Modèle pour l'indicateur MACD (Moving Average Convergence Divergence).
    """
    
    indicator_type: IndicatorType = Field(
        default=IndicatorType.MACD,
        description="Type fixé à MACD"
    )
    macd_line: Decimal = Field(
        ...,
        description="Ligne MACD (EMA12 - EMA26)"
    )
    signal_line: Decimal = Field(
        ...,
        description="Ligne de signal (EMA9 du MACD)"
    )
    histogram: Decimal = Field(
        ...,
        description="Histogramme (MACD - Signal)"
    )
    fast_period: int = Field(
        12,
        description="Période EMA rapide",
        gt=0
    )
    slow_period: int = Field(
        26,
        description="Période EMA lente",
        gt=0
    )
    signal_period: int = Field(
        9,
        description="Période EMA signal",
        gt=0
    )

    @property
    def is_bullish_crossover(self) -> bool:
        """Indique si c'est un croisement haussier (MACD > Signal)."""
        return self.macd_line > self.signal_line

    @property
    def is_bearish_crossover(self) -> bool:
        """Indique si c'est un croisement baissier (MACD < Signal)."""
        return self.macd_line < self.signal_line

    @property
    def signal_strength(self) -> str:
        """Force du signal MACD."""
        if abs(self.histogram) > abs(self.macd_line) * Decimal('0.1'):
            return "FORT"
        elif abs(self.histogram) > abs(self.macd_line) * Decimal('0.05'):
            return "MODÉRÉ"
        else:
            return "FAIBLE"

    def __str__(self) -> str:
        """Représentation textuelle du MACD."""
        base = super().__str__()
        return f"{base} MACD:{self.macd_line:.4f} Signal:{self.signal_line:.4f} Hist:{self.histogram:.4f}"


class BollingerBands(BaseIndicator):
    """
    Modèle pour les Bandes de Bollinger.
    """
    
    indicator_type: IndicatorType = Field(
        default=IndicatorType.BOLLINGER,
        description="Type fixé à Bollinger"
    )
    middle_band: Decimal = Field(
        ...,
        description="Bande du milieu (SMA)"
    )
    upper_band: Decimal = Field(
        ...,
        description="Bande supérieure (SMA + 2*STD)"
    )
    lower_band: Decimal = Field(
        ...,
        description="Bande inférieure (SMA - 2*STD)"
    )
    std_dev: Decimal = Field(
        ...,
        description="Écart-type utilisé"
    )
    std_multiplier: Decimal = Field(
        Decimal('2.0'),
        description="Multiplicateur d'écart-type"
    )

    @validator('upper_band')
    def upper_must_be_higher(cls, v: Decimal, values: Dict[str, Any]) -> Decimal:
        """Valide que la bande supérieure est plus haute que le milieu."""
        if 'middle_band' in values and v <= values['middle_band']:
            raise ValueError("La bande supérieure doit être > bande du milieu")
        return v

    @validator('lower_band')
    def lower_must_be_lower(cls, v: Decimal, values: Dict[str, Any]) -> Decimal:
        """Valide que la bande inférieure est plus basse que le milieu."""
        if 'middle_band' in values and v >= values['middle_band']:
            raise ValueError("La bande inférieure doit être < bande du milieu")
        return v

    @property
    def bandwidth(self) -> Decimal:
        """Largeur des bandes (upper - lower)."""
        return self.upper_band - self.lower_band

    @property
    def bandwidth_percent(self) -> Decimal:
        """Largeur des bandes en pourcentage du milieu."""
        if self.middle_band == 0:
            return Decimal('0')
        return (self.bandwidth / self.middle_band) * 100

    def get_position(self, price: Decimal) -> str:
        """Détermine la position du prix par rapport aux bandes."""
        if price > self.upper_band:
            return "AU-DESSUS_SUPÉRIEURE"
        elif price < self.lower_band:
            return "EN-DESSOUS_INFÉRIEURE"
        elif price > self.middle_band:
            return "MOITIÉ_SUPÉRIEURE"
        else:
            return "MOITIÉ_INFÉRIEURE"

    def get_squeeze_level(self) -> str:
        """Évalue le niveau de compression des bandes."""
        if self.bandwidth_percent < Decimal('10'):
            return "FORTE_COMPRESSION"
        elif self.bandwidth_percent < Decimal('15'):
            return "COMPRESSION_MODÉRÉE"
        elif self.bandwidth_percent > Decimal('25'):
            return "FORTE_EXPANSION"
        else:
            return "NORMAL"

    def __str__(self) -> str:
        """Représentation textuelle des Bollinger Bands."""
        base = super().__str__()
        return f"{base} Upper:{self.upper_band:.2f} Middle:{self.middle_band:.2f} Lower:{self.lower_band:.2f}"


class Stochastic(BaseIndicator):
    """
    Modèle pour l'oscillateur Stochastique.
    """
    
    indicator_type: IndicatorType = Field(
        default=IndicatorType.STOCH,
        description="Type fixé à Stochastic"
    )
    k_percent: Decimal = Field(
        ...,
        description="Valeur %K",
        ge=0,
        le=100
    )
    d_percent: Decimal = Field(
        ...,
        description="Valeur %D (moyenne mobile de %K)",
        ge=0,
        le=100
    )
    k_period: int = Field(
        14,
        description="Période pour %K",
        gt=0
    )
    d_period: int = Field(
        3,
        description="Période pour %D",
        gt=0
    )

    @property
    def is_overbought(self) -> bool:
        """Indique si le Stochastic est en survente."""
        return self.k_percent > 80 and self.d_percent > 80

    @property
    def is_oversold(self) -> bool:
        """Indique si le Stochastic est en surachat."""
        return self.k_percent < 20 and self.d_percent < 20

    @property
    def is_bullish_crossover(self) -> bool:
        """Indique si %K croise %D vers le haut."""
        return self.k_percent > self.d_percent

    @property
    def signal(self) -> str:
        """Signal du Stochastic."""
        if self.is_oversold and self.is_bullish_crossover:
            return "ACHAT_FORT"
        elif self.is_overbought and not self.is_bullish_crossover:
            return "VENTE_FORTE"
        elif self.is_oversold:
            return "ACHAT_POTENTIEL"
        elif self.is_overbought:
            return "VENTE_POTENTIELLE"
        else:
            return "NEUTRE"

    def __str__(self) -> str:
        """Représentation textuelle du Stochastic."""
        base = super().__str__()
        return f"{base} %K:{self.k_percent:.1f} %D:{self.d_percent:.1f}"


class IndicatorCollection(BaseModel):
    """
    Collection d'indicateurs techniques pour un symbole et timeframe.
    
    Permet de gérer efficacement plusieurs indicateurs ensemble.
    """
    
    symbol: Symbol = Field(
        ...,
        description="Symbole financier"
    )
    timeframe: TimeFrame = Field(
        ...,
        description="Timeframe des indicateurs"
    )
    timestamp: datetime = Field(
        default_factory=lambda: arrow.utcnow().datetime,
        description="Timestamp de la collection"
    )
    indicators: Dict[str, Union[SimpleIndicator, MACD, BollingerBands, Stochastic]] = Field(
        default_factory=dict,
        description="Dictionnaire des indicateurs par nom"
    )
    
    def add_indicator(self, name: str, indicator: BaseIndicator) -> None:
        """Ajoute un indicateur à la collection."""
        if indicator.symbol != self.symbol:
            raise ValueError(f"Symbole mismatch: {indicator.symbol} != {self.symbol}")
        if indicator.timeframe != self.timeframe:
            raise ValueError(f"Timeframe mismatch: {indicator.timeframe} != {self.timeframe}")
        
        self.indicators[name] = indicator

    def get_indicator(self, name: str) -> Optional[BaseIndicator]:
        """Récupère un indicateur par nom."""
        return self.indicators.get(name)

    def get_moving_averages(self) -> List[MovingAverage]:
        """Récupère toutes les moyennes mobiles."""
        return [
            ind for ind in self.indicators.values()
            if isinstance(ind, MovingAverage)
        ]

    def get_oscillators(self) -> List[Union[RSI, Stochastic]]:
        """Récupère tous les oscillateurs."""
        return [
            ind for ind in self.indicators.values()
            if isinstance(ind, (RSI, Stochastic))
        ]

    def get_trend_indicators(self) -> List[Union[MACD, BollingerBands]]:
        """Récupère les indicateurs de tendance."""
        return [
            ind for ind in self.indicators.values()
            if isinstance(ind, (MACD, BollingerBands))
        ]

    def generate_summary(self) -> Dict[str, Any]:
        """Génère un résumé des signaux de tous les indicateurs."""
        summary = {
            'symbol': self.symbol.symbol,
            'timeframe': self.timeframe,
            'timestamp': self.timestamp,
            'signals': {},
            'trend': 'NEUTRE',
            'momentum': 'NEUTRE',
            'volatility': 'NORMALE'
        }
        
        # Analyse des signaux individuels
        for name, indicator in self.indicators.items():
            if hasattr(indicator, 'signal'):
                summary['signals'][name] = indicator.signal
            elif hasattr(indicator, 'signal_strength'):
                summary['signals'][name] = indicator.signal_strength
        
        return summary

    def __len__(self) -> int:
        """Retourne le nombre d'indicateurs."""
        return len(self.indicators)

    def __contains__(self, name: str) -> bool:
        """Vérifie si un indicateur existe."""
        return name in self.indicators

    def __str__(self) -> str:
        """Représentation textuelle de la collection."""
        return f"IndicatorCollection for {self.symbol.symbol} ({len(self.indicators)} indicators)"