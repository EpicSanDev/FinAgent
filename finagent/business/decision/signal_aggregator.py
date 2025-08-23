"""
Agrégateur de signaux - Consolidation intelligente des signaux de trading.
"""

import logging
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID

from finagent.business.models.decision_models import (
    DecisionSignal,
    SignalAggregation,
    SignalType,
    SignalStrength,
    DecisionAction,
    MarketAnalysis,
    RiskAssessment
)

logger = logging.getLogger(__name__)


class SignalAggregator:
    """
    Agrégateur de signaux intelligent pour la consolidation de multiples sources.
    
    Combine et pondère :
    - Signaux de stratégies utilisateur
    - Signaux d'analyse technique
    - Signaux d'analyse fondamentale
    - Signaux de sentiment
    - Signaux d'analyse IA
    """
    
    def __init__(self):
        """Initialise l'agrégateur de signaux."""
        
        # Poids par type de signal
        self.signal_weights = {
            SignalType.STRATEGY: 0.35,      # Stratégies utilisateur
            SignalType.AI_ANALYSIS: 0.25,   # Analyse IA
            SignalType.TECHNICAL: 0.20,     # Analyse technique
            SignalType.FUNDAMENTAL: 0.15,   # Analyse fondamentale
            SignalType.SENTIMENT: 0.05      # Sentiment de marché
        }
        
        # Facteurs de confiance par force
        self.strength_multipliers = {
            SignalStrength.VERY_WEAK: 0.2,
            SignalStrength.WEAK: 0.4,
            SignalStrength.MODERATE: 0.6,
            SignalStrength.STRONG: 0.8,
            SignalStrength.VERY_STRONG: 1.0
        }
        
        # Configuration d'expiration des signaux
        self.signal_expiry_hours = {
            SignalType.STRATEGY: 24,        # 1 jour
            SignalType.AI_ANALYSIS: 12,     # 12 heures
            SignalType.TECHNICAL: 6,        # 6 heures
            SignalType.FUNDAMENTAL: 72,     # 3 jours
            SignalType.SENTIMENT: 4         # 4 heures
        }
        
        logger.info("Agrégateur de signaux initialisé")
    
    async def aggregate_signals(
        self,
        symbol: str,
        strategy_signals: List[Any],
        market_analysis: Optional[MarketAnalysis] = None,
        risk_assessment: Optional[RiskAssessment] = None
    ) -> SignalAggregation:
        """
        Agrège tous les signaux disponibles pour un symbole.
        
        Args:
            symbol: Symbole du titre
            strategy_signals: Signaux des stratégies utilisateur
            market_analysis: Analyse de marché
            risk_assessment: Évaluation des risques
            
        Returns:
            SignalAggregation: Signaux agrégés avec consensus
        """
        logger.info(f"Agrégation des signaux pour {symbol}")
        
        try:
            # Convertir tous les signaux en format uniforme
            all_signals = []
            
            # 1. Convertir les signaux de stratégies
            all_signals.extend(await self._convert_strategy_signals(strategy_signals))
            
            # 2. Extraire les signaux d'analyse technique
            if market_analysis:
                technical_signals = await self._extract_technical_signals(symbol, market_analysis)
                all_signals.extend(technical_signals)
                
                # 3. Extraire les signaux fondamentaux
                fundamental_signals = await self._extract_fundamental_signals(symbol, market_analysis)
                all_signals.extend(fundamental_signals)
                
                # 4. Extraire les signaux de sentiment
                sentiment_signals = await self._extract_sentiment_signals(symbol, market_analysis)
                all_signals.extend(sentiment_signals)
            
            # 5. Intégrer l'évaluation des risques
            if risk_assessment:
                risk_signals = await self._extract_risk_signals(symbol, risk_assessment)
                all_signals.extend(risk_signals)
            
            # Filtrer les signaux expirés
            active_signals = [s for s in all_signals if not s.is_expired]
            
            # Calculer l'agrégation
            aggregation = await self._calculate_aggregation(symbol, active_signals)
            
            logger.info(f"Agrégation terminée pour {symbol}: {aggregation.aggregated_action}")
            return aggregation
            
        except Exception as e:
            logger.error(f"Erreur agrégation signaux pour {symbol}: {e}")
            
            # Agrégation par défaut en cas d'erreur
            return SignalAggregation(
                symbol=symbol,
                signals=[],
                aggregated_action=DecisionAction.HOLD,
                aggregated_confidence=0.1,
                consensus_strength=0.0,
                buy_signals=0,
                sell_signals=0,
                hold_signals=1,
                weighted_score=0.0
            )
    
    async def _convert_strategy_signals(self, strategy_signals: List[Any]) -> List[DecisionSignal]:
        """Convertit les signaux de stratégies en signaux unifiés."""
        converted_signals = []
        
        for signal in strategy_signals:
            try:
                # Adapter selon le format des signaux de stratégie
                action_map = {
                    "BUY": DecisionAction.BUY,
                    "SELL": DecisionAction.SELL,
                    "HOLD": DecisionAction.HOLD
                }
                
                # Créer le signal unifié
                unified_signal = DecisionSignal(
                    symbol=signal.symbol if hasattr(signal, 'symbol') else signal.get('symbol', ''),
                    signal_type=SignalType.STRATEGY,
                    strength=SignalStrength.MODERATE,  # Par défaut
                    direction=action_map.get(signal.action if hasattr(signal, 'action') else signal.get('action', 'HOLD'), DecisionAction.HOLD),
                    confidence=signal.confidence if hasattr(signal, 'confidence') else signal.get('confidence', 0.6),
                    source=f"Strategy: {signal.strategy_name if hasattr(signal, 'strategy_name') else signal.get('strategy_name', 'Unknown')}",
                    reason=signal.reason if hasattr(signal, 'reason') else signal.get('reason', 'Strategy signal'),
                    weight=self.signal_weights[SignalType.STRATEGY]
                )
                
                converted_signals.append(unified_signal)
                
            except Exception as e:
                logger.warning(f"Erreur conversion signal stratégie: {e}")
                continue
        
        return converted_signals
    
    async def _extract_technical_signals(
        self, 
        symbol: str, 
        market_analysis: MarketAnalysis
    ) -> List[DecisionSignal]:
        """Extrait les signaux d'analyse technique."""
        signals = []
        
        try:
            indicators = market_analysis.technical_indicators
            
            # Signal RSI
            if 'rsi' in indicators:
                rsi = indicators['rsi']
                if rsi < 30:
                    signals.append(DecisionSignal(
                        symbol=symbol,
                        signal_type=SignalType.TECHNICAL,
                        strength=SignalStrength.STRONG if rsi < 20 else SignalStrength.MODERATE,
                        direction=DecisionAction.BUY,
                        confidence=min(0.9, (40 - rsi) / 20),
                        source="RSI Oversold",
                        reason=f"RSI à {rsi:.1f}, zone de survente",
                        weight=self.signal_weights[SignalType.TECHNICAL]
                    ))
                elif rsi > 70:
                    signals.append(DecisionSignal(
                        symbol=symbol,
                        signal_type=SignalType.TECHNICAL,
                        strength=SignalStrength.STRONG if rsi > 80 else SignalStrength.MODERATE,
                        direction=DecisionAction.SELL,
                        confidence=min(0.9, (rsi - 60) / 20),
                        source="RSI Overbought",
                        reason=f"RSI à {rsi:.1f}, zone de surachat",
                        weight=self.signal_weights[SignalType.TECHNICAL]
                    ))
            
            # Signal MACD
            if 'macd' in indicators and 'macd_signal' in indicators:
                macd = indicators['macd']
                macd_signal = indicators['macd_signal']
                
                if macd > macd_signal and macd > 0:
                    signals.append(DecisionSignal(
                        symbol=symbol,
                        signal_type=SignalType.TECHNICAL,
                        strength=SignalStrength.MODERATE,
                        direction=DecisionAction.BUY,
                        confidence=0.7,
                        source="MACD Bullish",
                        reason="MACD au-dessus du signal et positif",
                        weight=self.signal_weights[SignalType.TECHNICAL]
                    ))
                elif macd < macd_signal and macd < 0:
                    signals.append(DecisionSignal(
                        symbol=symbol,
                        signal_type=SignalType.TECHNICAL,
                        strength=SignalStrength.MODERATE,
                        direction=DecisionAction.SELL,
                        confidence=0.7,
                        source="MACD Bearish",
                        reason="MACD en-dessous du signal et négatif",
                        weight=self.signal_weights[SignalType.TECHNICAL]
                    ))
            
            # Signal Bollinger Bands
            if all(k in indicators for k in ['bb_upper', 'bb_lower', 'bb_middle']):
                current_price = float(market_analysis.technical_indicators.get('close', 0))
                bb_upper = indicators['bb_upper']
                bb_lower = indicators['bb_lower']
                bb_middle = indicators['bb_middle']
                
                if current_price <= bb_lower:
                    signals.append(DecisionSignal(
                        symbol=symbol,
                        signal_type=SignalType.TECHNICAL,
                        strength=SignalStrength.MODERATE,
                        direction=DecisionAction.BUY,
                        confidence=0.6,
                        source="Bollinger Bands",
                        reason="Prix près de la bande inférieure",
                        weight=self.signal_weights[SignalType.TECHNICAL]
                    ))
                elif current_price >= bb_upper:
                    signals.append(DecisionSignal(
                        symbol=symbol,
                        signal_type=SignalType.TECHNICAL,
                        strength=SignalStrength.MODERATE,
                        direction=DecisionAction.SELL,
                        confidence=0.6,
                        source="Bollinger Bands",
                        reason="Prix près de la bande supérieure",
                        weight=self.signal_weights[SignalType.TECHNICAL]
                    ))
            
            # Signal de tendance
            trend = market_analysis.trend_direction
            if trend == 'bullish':
                signals.append(DecisionSignal(
                    symbol=symbol,
                    signal_type=SignalType.TECHNICAL,
                    strength=SignalStrength.MODERATE,
                    direction=DecisionAction.BUY,
                    confidence=0.6,
                    source="Trend Analysis",
                    reason="Tendance haussière confirmée",
                    weight=self.signal_weights[SignalType.TECHNICAL] * 0.8
                ))
            elif trend == 'bearish':
                signals.append(DecisionSignal(
                    symbol=symbol,
                    signal_type=SignalType.TECHNICAL,
                    strength=SignalStrength.MODERATE,
                    direction=DecisionAction.SELL,
                    confidence=0.6,
                    source="Trend Analysis",
                    reason="Tendance baissière confirmée",
                    weight=self.signal_weights[SignalType.TECHNICAL] * 0.8
                ))
            
        except Exception as e:
            logger.error(f"Erreur extraction signaux techniques: {e}")
        
        return signals
    
    async def _extract_fundamental_signals(
        self, 
        symbol: str, 
        market_analysis: MarketAnalysis
    ) -> List[DecisionSignal]:
        """Extrait les signaux d'analyse fondamentale."""
        signals = []
        
        try:
            # Signal P/E ratio
            if market_analysis.pe_ratio:
                pe = market_analysis.pe_ratio
                if pe < 15:
                    signals.append(DecisionSignal(
                        symbol=symbol,
                        signal_type=SignalType.FUNDAMENTAL,
                        strength=SignalStrength.MODERATE,
                        direction=DecisionAction.BUY,
                        confidence=min(0.8, (20 - pe) / 10),
                        source="P/E Analysis",
                        reason=f"P/E ratio attractif: {pe:.1f}",
                        weight=self.signal_weights[SignalType.FUNDAMENTAL]
                    ))
                elif pe > 30:
                    signals.append(DecisionSignal(
                        symbol=symbol,
                        signal_type=SignalType.FUNDAMENTAL,
                        strength=SignalStrength.WEAK,
                        direction=DecisionAction.SELL,
                        confidence=min(0.6, (pe - 25) / 20),
                        source="P/E Analysis",
                        reason=f"P/E ratio élevé: {pe:.1f}",
                        weight=self.signal_weights[SignalType.FUNDAMENTAL]
                    ))
            
            # Signal dividend yield
            if market_analysis.dividend_yield:
                dividend_yield = market_analysis.dividend_yield
                if dividend_yield > 0.04:  # 4%
                    signals.append(DecisionSignal(
                        symbol=symbol,
                        signal_type=SignalType.FUNDAMENTAL,
                        strength=SignalStrength.WEAK,
                        direction=DecisionAction.BUY,
                        confidence=0.5,
                        source="Dividend Yield",
                        reason=f"Rendement dividende attractif: {dividend_yield*100:.1f}%",
                        weight=self.signal_weights[SignalType.FUNDAMENTAL] * 0.5
                    ))
            
        except Exception as e:
            logger.error(f"Erreur extraction signaux fondamentaux: {e}")
        
        return signals
    
    async def _extract_sentiment_signals(
        self, 
        symbol: str, 
        market_analysis: MarketAnalysis
    ) -> List[DecisionSignal]:
        """Extrait les signaux de sentiment."""
        signals = []
        
        try:
            sentiment_score = market_analysis.sentiment_score
            
            if sentiment_score > 0.3:
                signals.append(DecisionSignal(
                    symbol=symbol,
                    signal_type=SignalType.SENTIMENT,
                    strength=SignalStrength.WEAK,
                    direction=DecisionAction.BUY,
                    confidence=min(0.7, sentiment_score),
                    source="Market Sentiment",
                    reason=f"Sentiment positif: {sentiment_score:.2f}",
                    weight=self.signal_weights[SignalType.SENTIMENT]
                ))
            elif sentiment_score < -0.3:
                signals.append(DecisionSignal(
                    symbol=symbol,
                    signal_type=SignalType.SENTIMENT,
                    strength=SignalStrength.WEAK,
                    direction=DecisionAction.SELL,
                    confidence=min(0.7, abs(sentiment_score)),
                    source="Market Sentiment",
                    reason=f"Sentiment négatif: {sentiment_score:.2f}",
                    weight=self.signal_weights[SignalType.SENTIMENT]
                ))
            
        except Exception as e:
            logger.error(f"Erreur extraction signaux sentiment: {e}")
        
        return signals
    
    async def _extract_risk_signals(
        self, 
        symbol: str, 
        risk_assessment: RiskAssessment
    ) -> List[DecisionSignal]:
        """Extrait les signaux basés sur l'évaluation des risques."""
        signals = []
        
        try:
            risk_score = risk_assessment.overall_risk_score
            
            # Signal de risque élevé
            if risk_score > 0.8:
                signals.append(DecisionSignal(
                    symbol=symbol,
                    signal_type=SignalType.AI_ANALYSIS,
                    strength=SignalStrength.STRONG,
                    direction=DecisionAction.SELL,
                    confidence=risk_score,
                    source="Risk Assessment",
                    reason=f"Risque élevé détecté: {risk_score:.2f}",
                    weight=self.signal_weights[SignalType.AI_ANALYSIS] * 0.5
                ))
            
            # Signal de faible risque
            elif risk_score < 0.3:
                signals.append(DecisionSignal(
                    symbol=symbol,
                    signal_type=SignalType.AI_ANALYSIS,
                    strength=SignalStrength.WEAK,
                    direction=DecisionAction.BUY,
                    confidence=1 - risk_score,
                    source="Risk Assessment",
                    reason=f"Faible risque: {risk_score:.2f}",
                    weight=self.signal_weights[SignalType.AI_ANALYSIS] * 0.3
                ))
            
        except Exception as e:
            logger.error(f"Erreur extraction signaux risque: {e}")
        
        return signals
    
    async def _calculate_aggregation(
        self, 
        symbol: str, 
        signals: List[DecisionSignal]
    ) -> SignalAggregation:
        """Calcule l'agrégation finale des signaux."""
        
        if not signals:
            return SignalAggregation(
                symbol=symbol,
                signals=[],
                aggregated_action=DecisionAction.HOLD,
                aggregated_confidence=0.0,
                consensus_strength=0.0,
                buy_signals=0,
                sell_signals=0,
                hold_signals=0,
                weighted_score=0.0
            )
        
        # Compter les signaux par action
        buy_signals = [s for s in signals if s.direction == DecisionAction.BUY]
        sell_signals = [s for s in signals if s.direction == DecisionAction.SELL]
        hold_signals = [s for s in signals if s.direction == DecisionAction.HOLD]
        
        # Calculer les scores pondérés
        buy_score = sum(self._calculate_signal_score(s) for s in buy_signals)
        sell_score = sum(self._calculate_signal_score(s) for s in sell_signals)
        hold_score = sum(self._calculate_signal_score(s) for s in hold_signals)
        
        total_score = buy_score + sell_score + hold_score
        
        # Déterminer l'action agrégée
        if buy_score > sell_score and buy_score > hold_score:
            aggregated_action = DecisionAction.BUY
            confidence = buy_score / total_score if total_score > 0 else 0
        elif sell_score > buy_score and sell_score > hold_score:
            aggregated_action = DecisionAction.SELL
            confidence = sell_score / total_score if total_score > 0 else 0
        else:
            aggregated_action = DecisionAction.HOLD
            confidence = hold_score / total_score if total_score > 0 else 0
        
        # Calculer la force du consensus
        max_score = max(buy_score, sell_score, hold_score)
        consensus_strength = max_score / total_score if total_score > 0 else 0
        
        # Calculer les poids par type de signal
        signal_weights = {}
        for signal in signals:
            signal_type = signal.signal_type.value
            if signal_type not in signal_weights:
                signal_weights[signal_type] = 0
            signal_weights[signal_type] += self._calculate_signal_score(signal)
        
        # Normaliser les poids
        total_weight = sum(signal_weights.values())
        if total_weight > 0:
            signal_weights = {k: v / total_weight for k, v in signal_weights.items()}
        
        return SignalAggregation(
            symbol=symbol,
            signals=signals,
            aggregated_action=aggregated_action,
            aggregated_confidence=confidence,
            consensus_strength=consensus_strength,
            buy_signals=len(buy_signals),
            sell_signals=len(sell_signals),
            hold_signals=len(hold_signals),
            weighted_score=max_score,
            signal_weights=signal_weights
        )
    
    def _calculate_signal_score(self, signal: DecisionSignal) -> float:
        """Calcule le score d'un signal individuel."""
        try:
            # Score de base
            base_score = signal.confidence * signal.weight
            
            # Multiplicateur de force
            strength_multiplier = self.strength_multipliers.get(
                signal.strength, 0.6
            )
            
            # Facteur de fraîcheur (plus récent = plus important)
            age_hours = (datetime.now() - signal.timestamp).total_seconds() / 3600
            expiry_hours = self.signal_expiry_hours.get(signal.signal_type, 24)
            freshness_factor = max(0.1, 1 - (age_hours / expiry_hours))
            
            # Score final
            final_score = base_score * strength_multiplier * freshness_factor
            
            return final_score
            
        except Exception as e:
            logger.error(f"Erreur calcul score signal: {e}")
            return 0.1
    
    def update_signal_weights(self, new_weights: Dict[SignalType, float]):
        """Met à jour les poids des types de signaux."""
        try:
            # Valider que la somme des poids = 1.0
            total_weight = sum(new_weights.values())
            if abs(total_weight - 1.0) > 0.01:
                logger.warning(f"Somme des poids != 1.0: {total_weight}")
                # Normaliser
                new_weights = {k: v / total_weight for k, v in new_weights.items()}
            
            self.signal_weights.update(new_weights)
            logger.info("Poids des signaux mis à jour")
            
        except Exception as e:
            logger.error(f"Erreur mise à jour poids signaux: {e}")