"""
Validators spécialisés pour les données de marché.

Ce module fournit la validation spécifique aux données OHLCV,
cotations et autres informations de marché.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal

import arrow

from .base import BaseValidator, ValidationError
from ..models.base import TimeFrame, Symbol
from ..models.market_data import OHLCV, Price, QuoteData


class MarketDataValidator(BaseValidator):
    """
    Validator spécialisé pour les données de marché.
    """
    
    @staticmethod
    def validate_ohlcv_data(
        open_price: Decimal,
        high_price: Decimal,
        low_price: Decimal,
        close_price: Decimal,
        volume: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Valide la cohérence des données OHLCV.
        
        Args:
            open_price: Prix d'ouverture
            high_price: Prix le plus haut
            low_price: Prix le plus bas
            close_price: Prix de fermeture
            volume: Volume (optionnel)
            
        Returns:
            Dictionnaire des données validées
            
        Raises:
            ValidationError: Si les données sont incohérentes
        """
        # Validation des prix positifs
        prices = {
            'open': MarketDataValidator.validate_positive_number(open_price, "open"),
            'high': MarketDataValidator.validate_positive_number(high_price, "high"),
            'low': MarketDataValidator.validate_positive_number(low_price, "low"),
            'close': MarketDataValidator.validate_positive_number(close_price, "close")
        }
        
        # Validation de la cohérence OHLC
        if prices['high'] < prices['open']:
            raise ValidationError("Le prix high doit être >= open")
        
        if prices['high'] < prices['close']:
            raise ValidationError("Le prix high doit être >= close")
        
        if prices['low'] > prices['open']:
            raise ValidationError("Le prix low doit être <= open")
        
        if prices['low'] > prices['close']:
            raise ValidationError("Le prix low doit être <= close")
        
        if prices['high'] < prices['low']:
            raise ValidationError("Le prix high doit être >= low")
        
        # Validation du volume
        validated_volume = None
        if volume is not None:
            if not isinstance(volume, int) or volume < 0:
                raise ValidationError(f"Le volume doit être un entier positif, reçu: {volume}")
            validated_volume = volume
        
        return {
            **prices,
            'volume': validated_volume
        }

    @staticmethod
    def validate_price_movement(
        previous_close: Decimal,
        current_price: Decimal,
        max_change_percent: float = 50.0
    ) -> bool:
        """
        Valide qu'un mouvement de prix est raisonnable.
        
        Args:
            previous_close: Prix de clôture précédent
            current_price: Prix actuel
            max_change_percent: Variation maximale autorisée en %
            
        Returns:
            True si le mouvement est raisonnable
            
        Raises:
            ValidationError: Si le mouvement est suspect
        """
        if previous_close <= 0 or current_price <= 0:
            raise ValidationError("Les prix doivent être positifs")
        
        change_percent = abs((current_price - previous_close) / previous_close) * 100
        
        if change_percent > max_change_percent:
            raise ValidationError(
                f"Mouvement de prix suspect: {change_percent:.2f}% "
                f"(maximum autorisé: {max_change_percent}%)"
            )
        
        return True

    @staticmethod
    def validate_timestamp_sequence(
        timestamps: List[datetime],
        timeframe: TimeFrame,
        tolerance_minutes: int = 5
    ) -> List[datetime]:
        """
        Valide une séquence de timestamps pour un timeframe donné.
        
        Args:
            timestamps: Liste des timestamps
            timeframe: Timeframe attendu
            tolerance_minutes: Tolérance en minutes
            
        Returns:
            Liste des timestamps validés
            
        Raises:
            ValidationError: Si la séquence est invalide
        """
        if not timestamps:
            raise ValidationError("La liste de timestamps ne peut pas être vide")
        
        # Conversion timeframe en minutes
        timeframe_minutes = {
            TimeFrame.MINUTE_1: 1,
            TimeFrame.MINUTE_5: 5,
            TimeFrame.MINUTE_15: 15,
            TimeFrame.MINUTE_30: 30,
            TimeFrame.HOUR_1: 60,
            TimeFrame.HOUR_4: 240,
            TimeFrame.DAY_1: 1440,
            TimeFrame.WEEK_1: 10080,
            TimeFrame.MONTH_1: 43200  # Approximation
        }.get(timeframe)
        
        if timeframe_minutes is None:
            raise ValidationError(f"Timeframe non supporté: {timeframe}")
        
        # Vérification de l'ordre chronologique
        sorted_timestamps = sorted(timestamps)
        if timestamps != sorted_timestamps:
            raise ValidationError("Les timestamps doivent être en ordre chronologique")
        
        # Vérification des intervalles
        for i in range(1, len(timestamps)):
            current = arrow.get(timestamps[i])
            previous = arrow.get(timestamps[i-1])
            
            expected_diff = timedelta(minutes=timeframe_minutes)
            actual_diff = current.datetime - previous.datetime
            tolerance = timedelta(minutes=tolerance_minutes)
            
            if abs(actual_diff - expected_diff) > tolerance:
                raise ValidationError(
                    f"Intervalle incorrect entre {previous} et {current}: "
                    f"{actual_diff} (attendu: {expected_diff})"
                )
        
        return timestamps

    @staticmethod
    def validate_market_hours(
        timestamp: datetime,
        exchange: str = "NYSE",
        allow_extended_hours: bool = True
    ) -> bool:
        """
        Valide qu'un timestamp correspond aux heures de marché.
        
        Args:
            timestamp: Timestamp à valider
            exchange: Bourse (NYSE, NASDAQ, etc.)
            allow_extended_hours: Autoriser les heures étendues
            
        Returns:
            True si dans les heures de marché
        """
        # Conversion en timezone de l'exchange
        if exchange in ["NYSE", "NASDAQ"]:
            # EST/EDT timezone
            ts_local = arrow.get(timestamp).to('US/Eastern')
        else:
            # Par défaut, utilise UTC
            ts_local = arrow.get(timestamp)
        
        # Vérifie si c'est un jour de semaine
        if ts_local.weekday() >= 5:  # Samedi = 5, Dimanche = 6
            return False
        
        # Heures de marché standard (9:30 - 16:00 EST)
        market_open = ts_local.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = ts_local.replace(hour=16, minute=0, second=0, microsecond=0)
        
        # Heures étendues (4:00 - 20:00 EST)
        extended_open = ts_local.replace(hour=4, minute=0, second=0, microsecond=0)
        extended_close = ts_local.replace(hour=20, minute=0, second=0, microsecond=0)
        
        if allow_extended_hours:
            return extended_open <= ts_local <= extended_close
        else:
            return market_open <= ts_local <= market_close

    @staticmethod
    def validate_bid_ask_spread(
        bid: Decimal,
        ask: Decimal,
        max_spread_percent: float = 10.0
    ) -> Tuple[Decimal, Decimal]:
        """
        Valide un spread bid-ask.
        
        Args:
            bid: Prix d'achat
            ask: Prix de vente
            max_spread_percent: Spread maximum en %
            
        Returns:
            Tuple (bid, ask) validé
            
        Raises:
            ValidationError: Si le spread est invalide
        """
        bid = MarketDataValidator.validate_positive_number(bid, "bid")
        ask = MarketDataValidator.validate_positive_number(ask, "ask")
        
        if ask <= bid:
            raise ValidationError(f"Ask ({ask}) doit être > Bid ({bid})")
        
        spread_percent = ((ask - bid) / bid) * 100
        
        if spread_percent > max_spread_percent:
            raise ValidationError(
                f"Spread trop large: {spread_percent:.2f}% "
                f"(maximum: {max_spread_percent}%)"
            )
        
        return bid, ask

    @staticmethod
    def validate_volume_profile(
        volumes: List[int],
        timeframe: TimeFrame,
        min_volume: int = 0,
        max_volume: Optional[int] = None
    ) -> List[int]:
        """
        Valide un profil de volume.
        
        Args:
            volumes: Liste des volumes
            timeframe: Timeframe des données
            min_volume: Volume minimum
            max_volume: Volume maximum (optionnel)
            
        Returns:
            Liste des volumes validés
            
        Raises:
            ValidationError: Si le profil est invalide
        """
        if not volumes:
            raise ValidationError("La liste de volumes ne peut pas être vide")
        
        validated_volumes = []
        
        for i, volume in enumerate(volumes):
            if not isinstance(volume, int) or volume < min_volume:
                raise ValidationError(
                    f"Volume invalide à l'index {i}: {volume} "
                    f"(minimum: {min_volume})"
                )
            
            if max_volume and volume > max_volume:
                raise ValidationError(
                    f"Volume trop élevé à l'index {i}: {volume} "
                    f"(maximum: {max_volume})"
                )
            
            validated_volumes.append(volume)
        
        # Détection de volumes aberrants
        if len(validated_volumes) > 2:
            avg_volume = sum(validated_volumes) / len(validated_volumes)
            
            for i, volume in enumerate(validated_volumes):
                if volume > avg_volume * 10:  # 10x la moyenne
                    # Log mais ne rejette pas (peut être un volume exceptionnel)
                    pass
        
        return validated_volumes

    @staticmethod
    def validate_ohlcv_collection(ohlcv_list: List[OHLCV]) -> List[OHLCV]:
        """
        Valide une collection de données OHLCV.
        
        Args:
            ohlcv_list: Liste des données OHLCV
            
        Returns:
            Liste validée et triée
            
        Raises:
            ValidationError: Si la collection est invalide
        """
        if not ohlcv_list:
            raise ValidationError("La collection OHLCV ne peut pas être vide")
        
        # Vérifie que tous les éléments ont le même symbole et timeframe
        first_symbol = ohlcv_list[0].symbol.symbol
        first_timeframe = ohlcv_list[0].timeframe
        
        for i, ohlcv in enumerate(ohlcv_list):
            if ohlcv.symbol.symbol != first_symbol:
                raise ValidationError(
                    f"Symbole incohérent à l'index {i}: {ohlcv.symbol.symbol} "
                    f"(attendu: {first_symbol})"
                )
            
            if ohlcv.timeframe != first_timeframe:
                raise ValidationError(
                    f"Timeframe incohérent à l'index {i}: {ohlcv.timeframe} "
                    f"(attendu: {first_timeframe})"
                )
        
        # Tri par timestamp
        sorted_ohlcv = sorted(ohlcv_list, key=lambda x: x.timestamp)
        
        # Validation de la séquence temporelle
        timestamps = [ohlcv.timestamp for ohlcv in sorted_ohlcv]
        MarketDataValidator.validate_timestamp_sequence(timestamps, first_timeframe)
        
        return sorted_ohlcv

    @staticmethod
    def detect_data_anomalies(ohlcv_list: List[OHLCV]) -> List[Dict[str, Any]]:
        """
        Détecte les anomalies dans les données OHLCV.
        
        Args:
            ohlcv_list: Liste des données OHLCV
            
        Returns:
            Liste des anomalies détectées
        """
        anomalies = []
        
        if len(ohlcv_list) < 2:
            return anomalies
        
        for i in range(1, len(ohlcv_list)):
            current = ohlcv_list[i]
            previous = ohlcv_list[i-1]
            
            # Détection de gaps importants
            gap_up = (current.low - previous.high) / previous.high
            gap_down = (previous.low - current.high) / previous.high
            
            if gap_up > 0.05:  # Gap up de plus de 5%
                anomalies.append({
                    'type': 'gap_up',
                    'timestamp': current.timestamp,
                    'severity': 'medium' if gap_up < 0.10 else 'high',
                    'value': gap_up,
                    'description': f"Gap up de {gap_up:.2%}"
                })
            
            elif gap_down > 0.05:  # Gap down de plus de 5%
                anomalies.append({
                    'type': 'gap_down',
                    'timestamp': current.timestamp,
                    'severity': 'medium' if gap_down < 0.10 else 'high',
                    'value': gap_down,
                    'description': f"Gap down de {gap_down:.2%}"
                })
            
            # Détection de volumes anormaux
            if current.volume and previous.volume:
                volume_ratio = current.volume / previous.volume
                if volume_ratio > 5:  # Volume 5x supérieur
                    anomalies.append({
                        'type': 'volume_spike',
                        'timestamp': current.timestamp,
                        'severity': 'medium',
                        'value': volume_ratio,
                        'description': f"Volume {volume_ratio:.1f}x supérieur"
                    })
            
            # Détection de volatilité excessive
            daily_range = (current.high - current.low) / current.open
            if daily_range > 0.20:  # Range de plus de 20%
                anomalies.append({
                    'type': 'high_volatility',
                    'timestamp': current.timestamp,
                    'severity': 'medium' if daily_range < 0.30 else 'high',
                    'value': daily_range,
                    'description': f"Volatilité élevée: {daily_range:.2%}"
                })
        
        return anomalies


class QuoteValidator(BaseValidator):
    """
    Validator spécialisé pour les données de cotation en temps réel.
    """
    
    @staticmethod
    def validate_real_time_quote(quote_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valide des données de cotation en temps réel.
        
        Args:
            quote_data: Données de cotation brutes
            
        Returns:
            Données validées
            
        Raises:
            ValidationError: Si les données sont invalides
        """
        required_fields = ['symbol', 'last_price', 'timestamp']
        
        for field in required_fields:
            if field not in quote_data:
                raise ValidationError(f"Champ requis manquant: {field}")
        
        validated = {}
        
        # Validation du symbole
        validated['symbol'] = QuoteValidator.normalize_symbol(quote_data['symbol'])
        
        # Validation du prix
        validated['last_price'] = QuoteValidator.validate_positive_number(
            quote_data['last_price'], 
            'last_price'
        )
        
        # Validation du timestamp
        timestamp = quote_data['timestamp']
        if isinstance(timestamp, str):
            try:
                validated['timestamp'] = arrow.get(timestamp).datetime
            except Exception:
                raise ValidationError(f"Format de timestamp invalide: {timestamp}")
        elif isinstance(timestamp, datetime):
            validated['timestamp'] = timestamp
        else:
            raise ValidationError(f"Type de timestamp invalide: {type(timestamp)}")
        
        # Validation optionnelle du bid/ask
        if 'bid' in quote_data and 'ask' in quote_data:
            validated['bid'], validated['ask'] = QuoteValidator.validate_bid_ask_spread(
                Decimal(str(quote_data['bid'])),
                Decimal(str(quote_data['ask']))
            )
        
        # Validation du volume
        if 'volume' in quote_data:
            volume = quote_data['volume']
            if volume is not None:
                if not isinstance(volume, int) or volume < 0:
                    raise ValidationError(f"Volume invalide: {volume}")
                validated['volume'] = volume
        
        return validated