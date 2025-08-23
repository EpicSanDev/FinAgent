"""
Formatter pour les analyses IA.

Ce module gère le formatage des analyses générées par l'IA,
incluant les résumés, scores de confiance et recommandations.
"""

from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from enum import Enum

from rich.table import Table
from rich.text import Text
from rich.panel import Panel
from rich.columns import Columns
from rich.align import Align
from rich.progress import Progress, BarColumn, TextColumn
from rich.layout import Layout

from .base_formatter import BaseFormatter


class AnalysisFormatter(BaseFormatter):
    """Formatter spécialisé pour les analyses IA."""
    
    def format(self, data: Any, **kwargs) -> Union[Table, Panel, Text]:
        """
        Formate les données d'analyse selon leur type.
        
        Args:
            data: Données d'analyse à formater
            **kwargs: Options de formatage
            
        Returns:
            Données formatées pour affichage
        """
        if isinstance(data, dict):
            if "analysis_type" in data:
                return self.format_full_analysis(data, **kwargs)
            elif "sentiment" in data:
                return self.format_sentiment_analysis(data, **kwargs)
            elif "recommendation" in data:
                return self.format_recommendation(data, **kwargs)
            elif "confidence_score" in data:
                return self.format_confidence_analysis(data, **kwargs)
        
        return Text(str(data))
    
    def format_full_analysis(self, analysis_data: Dict[str, Any], **kwargs) -> Panel:
        """
        Formate une analyse complète.
        
        Args:
            analysis_data: Données d'analyse complète
            **kwargs: Options de formatage
            
        Returns:
            Panel avec l'analyse formatée
        """
        symbol = analysis_data.get("symbol", "N/A")
        analysis_type = analysis_data.get("analysis_type", "Analyse")
        timestamp = analysis_data.get("timestamp", datetime.now())
        
        # Contenu principal
        content_parts = []
        
        # Header avec timestamp
        if isinstance(timestamp, datetime):
            time_str = self.format_datetime(timestamp)
        else:
            time_str = str(timestamp)
        content_parts.append(f"📅 Analyse du {time_str}")
        
        # Résumé exécutif
        summary = analysis_data.get("summary", "")
        if summary:
            content_parts.append(f"\n📋 Résumé:")
            content_parts.append(f"{summary}")
        
        # Score de confiance global
        confidence = analysis_data.get("confidence_score", 0)
        if confidence > 0:
            confidence_bar = self._create_confidence_bar(confidence)
            content_parts.append(f"\n🎯 Confiance: {confidence_bar}")
        
        # Signaux principaux
        signals = analysis_data.get("signals", [])
        if signals:
            content_parts.append(f"\n🚦 Signaux principaux:")
            for signal in signals[:5]:  # Top 5
                signal_text = self._format_signal(signal)
                content_parts.append(f"  • {signal_text}")
        
        # Points clés
        key_points = analysis_data.get("key_points", [])
        if key_points:
            content_parts.append(f"\n🔑 Points clés:")
            for point in key_points[:3]:  # Top 3
                content_parts.append(f"  • {point}")
        
        # Risques identifiés
        risks = analysis_data.get("risks", [])
        if risks:
            content_parts.append(f"\n⚠️  Risques:")
            for risk in risks[:3]:  # Top 3
                content_parts.append(f"  • {risk}")
        
        content = "\n".join(content_parts)
        
        # Style selon le sentiment global
        sentiment = analysis_data.get("overall_sentiment", "NEUTRE")
        style = self._get_sentiment_style(sentiment)
        
        return self.create_panel(
            content,
            title=f"🤖 {analysis_type} - {self.style_symbol(symbol)}",
            style=style
        )
    
    def format_sentiment_analysis(self, sentiment_data: Dict[str, Any], **kwargs) -> Table:
        """
        Formate une analyse de sentiment.
        
        Args:
            sentiment_data: Données d'analyse de sentiment
            **kwargs: Options de formatage
            
        Returns:
            Table avec les résultats de sentiment
        """
        symbol = sentiment_data.get("symbol", "N/A")
        sentiment = sentiment_data.get("sentiment", {})
        
        # Création du tableau
        table = self.create_table(
            title=f"😊 Analyse de Sentiment - {self.style_symbol(symbol)}",
            show_lines=True
        )
        
        table.add_column("Source", style="cyan", no_wrap=True)
        table.add_column("Sentiment", justify="center")
        table.add_column("Score", justify="right")
        table.add_column("Confiance", justify="right")
        table.add_column("Tendance", justify="center")
        
        # Sources de sentiment
        sources = sentiment.get("sources", {})
        for source_name, source_data in sources.items():
            sentiment_value = source_data.get("sentiment", "NEUTRE")
            score = source_data.get("score", 0)
            confidence = source_data.get("confidence", 0)
            trend = source_data.get("trend", "STABLE")
            
            # Formatage du sentiment
            sentiment_styled = self._format_sentiment_value(sentiment_value, score)
            
            # Formatage de la tendance
            trend_styled = self._format_trend(trend)
            
            table.add_row(
                source_name.title(),
                sentiment_styled,
                f"{score:.2f}",
                f"{confidence:.1%}",
                trend_styled
            )
        
        # Ajout du sentiment global
        overall = sentiment.get("overall", {})
        if overall:
            sentiment_value = overall.get("sentiment", "NEUTRE")
            score = overall.get("score", 0)
            confidence = overall.get("confidence", 0)
            
            sentiment_styled = self._format_sentiment_value(sentiment_value, score)
            
            table.add_row(
                "GLOBAL",
                sentiment_styled,
                f"{score:.2f}",
                f"{confidence:.1%}",
                "─",
                style="bold"
            )
        
        return table
    
    def format_recommendation(self, recommendation_data: Dict[str, Any], **kwargs) -> Panel:
        """
        Formate une recommandation de trading.
        
        Args:
            recommendation_data: Données de recommandation
            **kwargs: Options de formatage
            
        Returns:
            Panel avec la recommandation
        """
        symbol = recommendation_data.get("symbol", "N/A")
        action = recommendation_data.get("recommendation", "HOLD")
        confidence = recommendation_data.get("confidence", 0)
        reasoning = recommendation_data.get("reasoning", "")
        
        # Contenu principal
        content_parts = []
        
        # Action recommandée
        action_styled = self._format_action(action, confidence)
        content_parts.append(f"🎯 Action: {action_styled}")
        
        # Score de confiance
        if confidence > 0:
            confidence_bar = self._create_confidence_bar(confidence)
            content_parts.append(f"📊 Confiance: {confidence_bar}")
        
        # Niveaux de prix
        price_levels = recommendation_data.get("price_levels", {})
        if price_levels:
            content_parts.append(f"\n💰 Niveaux de prix:")
            
            entry = price_levels.get("entry")
            if entry:
                content_parts.append(f"  • Entrée: {self.style_currency(entry)}")
            
            stop_loss = price_levels.get("stop_loss")
            if stop_loss:
                content_parts.append(f"  • Stop Loss: {self.style_currency(stop_loss)}")
            
            take_profit = price_levels.get("take_profit")
            if take_profit:
                content_parts.append(f"  • Take Profit: {self.style_currency(take_profit)}")
        
        # Reasoning détaillé
        if reasoning:
            content_parts.append(f"\n💭 Raisonnement:")
            # Découpage du reasoning en lignes
            reasoning_lines = reasoning.split('\n')
            for line in reasoning_lines[:5]:  # Limiter à 5 lignes
                if line.strip():
                    content_parts.append(f"  {line.strip()}")
        
        # Horizon de temps
        timeframe = recommendation_data.get("timeframe", "")
        if timeframe:
            content_parts.append(f"\n⏰ Horizon: {timeframe}")
        
        # Risk/Reward ratio
        risk_reward = recommendation_data.get("risk_reward_ratio")
        if risk_reward:
            content_parts.append(f"⚖️  Risk/Reward: 1:{risk_reward:.2f}")
        
        content = "\n".join(content_parts)
        
        # Style selon l'action
        style = self._get_action_style(action)
        
        return self.create_panel(
            content,
            title=f"🎯 Recommandation - {self.style_symbol(symbol)}",
            style=style
        )
    
    def format_confidence_analysis(self, confidence_data: Dict[str, Any], **kwargs) -> Layout:
        """
        Formate une analyse de confiance détaillée.
        
        Args:
            confidence_data: Données d'analyse de confiance
            **kwargs: Options de formatage
            
        Returns:
            Layout avec l'analyse de confiance
        """
        layout = Layout()
        
        # Score global
        overall_score = confidence_data.get("confidence_score", 0)
        overall_panel = self._create_confidence_panel(overall_score, "Score Global")
        
        # Facteurs contributeurs
        factors = confidence_data.get("factors", {})
        factors_table = self._create_factors_table(factors)
        
        # Métriques de qualité
        quality_metrics = confidence_data.get("quality_metrics", {})
        quality_panel = self._create_quality_panel(quality_metrics)
        
        # Organisation du layout
        layout.split_row(
            Layout(overall_panel, name="score"),
            Layout(quality_panel, name="quality")
        )
        layout["score"].split_column(
            Layout(overall_panel, size=3),
            Layout(factors_table)
        )
        
        return layout
    
    # === Méthodes utilitaires privées ===
    
    def _create_confidence_bar(self, confidence: float) -> str:
        """Crée une barre de confiance visuelle."""
        width = 20
        filled = int(confidence * width)
        
        if confidence >= 0.8:
            color = "green"
            emoji = "🟢"
        elif confidence >= 0.6:
            color = "yellow"
            emoji = "🟡"
        else:
            color = "red"
            emoji = "🔴"
        
        bar = "█" * filled + "░" * (width - filled)
        return f"{emoji} [{color}]{bar}[/{color}] {confidence:.1%}"
    
    def _format_signal(self, signal: Dict[str, Any]) -> str:
        """Formate un signal de trading."""
        signal_type = signal.get("type", "INFO")
        message = signal.get("message", "")
        strength = signal.get("strength", 0)
        
        # Emoji selon le type
        if signal_type.upper() == "BUY":
            emoji = "🟢"
            style = "green"
        elif signal_type.upper() == "SELL":
            emoji = "🔴"
            style = "red"
        else:
            emoji = "🟡"
            style = "yellow"
        
        # Indicateur de force
        strength_stars = "★" * int(strength * 5)
        
        return f"{emoji} [{style}]{message}[/{style}] ({strength_stars})"
    
    def _format_sentiment_value(self, sentiment: str, score: float) -> Text:
        """Formate une valeur de sentiment."""
        sentiment_upper = sentiment.upper()
        
        if sentiment_upper in ["POSITIF", "POSITIVE", "BULLISH"]:
            emoji = "😊"
            style = "green bold"
        elif sentiment_upper in ["NÉGATIF", "NEGATIVE", "BEARISH"]:
            emoji = "😟"
            style = "red bold"
        else:
            emoji = "😐"
            style = "yellow"
        
        return Text(f"{emoji} {sentiment_upper}", style=style)
    
    def _format_trend(self, trend: str) -> Text:
        """Formate une tendance."""
        trend_upper = trend.upper()
        
        if trend_upper == "UP":
            return Text("📈", style="green")
        elif trend_upper == "DOWN":
            return Text("📉", style="red")
        else:
            return Text("📊", style="yellow")
    
    def _format_action(self, action: str, confidence: float) -> Text:
        """Formate une action de trading."""
        action_upper = action.upper()
        
        if action_upper in ["BUY", "ACHAT"]:
            emoji = "🟢"
            style = "green bold"
        elif action_upper in ["SELL", "VENTE"]:
            emoji = "🔴"
            style = "red bold"
        else:
            emoji = "🟡"
            style = "yellow bold"
        
        confidence_text = f" (confiance: {confidence:.1%})" if confidence > 0 else ""
        return Text(f"{emoji} {action_upper}{confidence_text}", style=style)
    
    def _get_sentiment_style(self, sentiment: str) -> str:
        """Retourne le style selon le sentiment."""
        sentiment_upper = sentiment.upper()
        
        if sentiment_upper in ["POSITIF", "POSITIVE", "BULLISH"]:
            return "green"
        elif sentiment_upper in ["NÉGATIF", "NEGATIVE", "BEARISH"]:
            return "red"
        else:
            return "blue"
    
    def _get_action_style(self, action: str) -> str:
        """Retourne le style selon l'action."""
        action_upper = action.upper()
        
        if action_upper in ["BUY", "ACHAT"]:
            return "green"
        elif action_upper in ["SELL", "VENTE"]:
            return "red"
        else:
            return "blue"
    
    def _create_confidence_panel(self, score: float, title: str) -> Panel:
        """Crée un panel de confiance."""
        confidence_bar = self._create_confidence_bar(score)
        
        content = f"{confidence_bar}\n\n"
        
        if score >= 0.8:
            content += "🔥 Confiance très élevée"
            style = "green"
        elif score >= 0.6:
            content += "✅ Confiance correcte"
            style = "yellow"
        else:
            content += "⚠️  Confiance faible"
            style = "red"
        
        return self.create_panel(content, title=title, style=style)
    
    def _create_factors_table(self, factors: Dict[str, float]) -> Table:
        """Crée un tableau des facteurs de confiance."""
        table = self.create_table(title="Facteurs de confiance", show_lines=True)
        
        table.add_column("Facteur", style="cyan")
        table.add_column("Impact", justify="right")
        table.add_column("Poids", justify="right")
        
        # Tri des facteurs par impact
        sorted_factors = sorted(
            factors.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )
        
        for factor_name, impact in sorted_factors[:10]:  # Top 10
            impact_styled = self.style_positive(f"+{impact:.2f}") if impact > 0 else self.style_negative(f"{impact:.2f}")
            weight = abs(impact) / sum(abs(v) for v in factors.values()) if factors else 0
            
            table.add_row(
                factor_name.replace("_", " ").title(),
                str(impact_styled),
                f"{weight:.1%}"
            )
        
        return table
    
    def _create_quality_panel(self, quality_metrics: Dict[str, Any]) -> Panel:
        """Crée un panel des métriques de qualité."""
        content_parts = []
        
        data_quality = quality_metrics.get("data_quality", 0)
        analysis_depth = quality_metrics.get("analysis_depth", 0)
        source_reliability = quality_metrics.get("source_reliability", 0)
        
        content_parts.append(f"📊 Qualité des données: {data_quality:.1%}")
        content_parts.append(f"🔍 Profondeur d'analyse: {analysis_depth:.1%}")
        content_parts.append(f"🏛️  Fiabilité des sources: {source_reliability:.1%}")
        
        avg_quality = (data_quality + analysis_depth + source_reliability) / 3
        content_parts.append(f"\n📈 Score global: {avg_quality:.1%}")
        
        content = "\n".join(content_parts)
        
        style = "green" if avg_quality >= 0.8 else "yellow" if avg_quality >= 0.6 else "red"
        
        return self.create_panel(content, title="Métriques de qualité", style=style)
    
    def format_technical_indicators(self, indicators_data: Dict[str, Any], **kwargs) -> Table:
        """
        Formate les indicateurs techniques.
        
        Args:
            indicators_data: Données d'indicateurs techniques
            **kwargs: Options de formatage
            
        Returns:
            Table avec les indicateurs
        """
        symbol = indicators_data.get("symbol", "N/A")
        indicators = indicators_data.get("indicators", {})
        
        # Création du tableau
        table = self.create_table(
            title=f"📊 Indicateurs Techniques - {self.style_symbol(symbol)}",
            show_lines=True
        )
        
        table.add_column("Indicateur", style="cyan", no_wrap=True)
        table.add_column("Valeur", justify="right")
        table.add_column("Signal", justify="center")
        table.add_column("Description", no_wrap=False)
        
        # Formatage des indicateurs courants
        for name, data in indicators.items():
            if isinstance(data, dict):
                value = data.get("value", "N/A")
                signal = data.get("signal", "NEUTRE")
                description = data.get("description", "")
            else:
                value = data
                signal = "NEUTRE"
                description = ""
            
            # Style du signal
            if signal.upper() in ["ACHAT", "BUY"]:
                signal_styled = Text("🟢 ACHAT", style="green bold")
            elif signal.upper() in ["VENTE", "SELL"]:
                signal_styled = Text("🔴 VENTE", style="red bold")
            else:
                signal_styled = Text("🟡 NEUTRE", style="yellow")
            
            # Formatage de la valeur
            if isinstance(value, (int, float)):
                value_str = f"{value:.4f}"
            else:
                value_str = str(value)
            
            table.add_row(
                name.upper(),
                value_str,
                signal_styled,
                self.truncate_text(description, 40) if description else "─"
            )
        
        return table