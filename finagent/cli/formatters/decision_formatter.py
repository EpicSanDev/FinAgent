"""
Formatter pour les décisions de trading.

Ce module gère le formatage des décisions de trading,
reasoning détaillé, historique et alertes.
"""

from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from enum import Enum

from rich.table import Table
from rich.text import Text
from rich.panel import Panel
from rich.columns import Columns
from rich.align import Align
from rich.layout import Layout
from rich.tree import Tree

from .base_formatter import BaseFormatter


class DecisionFormatter(BaseFormatter):
    """Formatter spécialisé pour les décisions de trading."""
    
    def format(self, data: Any, **kwargs) -> Union[Table, Panel, Layout]:
        """
        Formate les données de décision selon leur type.
        
        Args:
            data: Données de décision à formater
            **kwargs: Options de formatage
            
        Returns:
            Données formatées pour affichage
        """
        if isinstance(data, dict):
            if "decision" in data and "reasoning" in data:
                return self.format_full_decision(data, **kwargs)
            elif "decisions" in data:
                return self.format_decision_history(data, **kwargs)
            elif "alerts" in data:
                return self.format_alerts(data, **kwargs)
            elif "simulation" in data:
                return self.format_simulation_result(data, **kwargs)
        elif isinstance(data, list):
            return self.format_decision_list(data, **kwargs)
        
        return Text(str(data))
    
    def format_full_decision(self, decision_data: Dict[str, Any], **kwargs) -> Layout:
        """
        Formate une décision complète avec reasoning.
        
        Args:
            decision_data: Données de décision complète
            **kwargs: Options de formatage
            
        Returns:
            Layout avec la décision formatée
        """
        layout = Layout()
        
        # Panel principal de décision
        decision_panel = self._create_decision_panel(decision_data)
        
        # Arbre de reasoning
        reasoning_tree = self._create_reasoning_tree(decision_data.get("reasoning", {}))
        
        # Métriques de confiance
        confidence_panel = self._create_confidence_metrics(decision_data)
        
        # Facteurs de risque
        risk_panel = self._create_risk_factors(decision_data.get("risk_factors", []))
        
        # Organisation du layout
        layout.split_row(
            Layout(name="main", ratio=2),
            Layout(name="details", ratio=1)
        )
        
        layout["main"].split_column(
            Layout(decision_panel, size=8),
            Layout(reasoning_tree)
        )
        
        layout["details"].split_column(
            Layout(confidence_panel, size=8),
            Layout(risk_panel)
        )
        
        return layout
    
    def format_decision_history(self, history_data: Dict[str, Any], **kwargs) -> Table:
        """
        Formate l'historique des décisions.
        
        Args:
            history_data: Données d'historique
            **kwargs: Options de formatage
            
        Returns:
            Table avec l'historique
        """
        decisions = history_data.get("decisions", [])
        total_count = history_data.get("total_count", len(decisions))
        
        table = self.create_table(
            title=f"📚 Historique des Décisions ({total_count} total)",
            show_lines=True
        )
        
        table.add_column("Date", style="cyan", no_wrap=True)
        table.add_column("Symbole", style="bold", no_wrap=True)
        table.add_column("Décision", justify="center")
        table.add_column("Confiance", justify="right")
        table.add_column("Prix", justify="right")
        table.add_column("Résultat", justify="right")
        table.add_column("Status", justify="center")
        
        # Tri par date décroissante
        sorted_decisions = sorted(
            decisions,
            key=lambda x: x.get("timestamp", datetime.min),
            reverse=True
        )
        
        for decision in sorted_decisions:
            timestamp = decision.get("timestamp")
            symbol = decision.get("symbol", "N/A")
            action = decision.get("action", "HOLD")
            confidence = decision.get("confidence", 0)
            price = decision.get("price", 0)
            outcome = decision.get("outcome", {})
            status = decision.get("status", "PENDING")
            
            # Formatage de la date
            if isinstance(timestamp, datetime):
                date_str = self.format_datetime(timestamp, include_time=False)
            else:
                date_str = str(timestamp)
            
            # Formatage de l'action
            action_styled = self._format_action_cell(action)
            
            # Formatage du résultat
            if outcome:
                pnl = outcome.get("pnl", 0)
                pnl_percent = outcome.get("pnl_percent", 0)
                if pnl != 0:
                    result_text = f"{self.style_currency(pnl)} ({self.style_percentage(pnl_percent)})"
                else:
                    result_text = "─"
            else:
                result_text = "En cours"
            
            # Formatage du status
            status_styled = self._format_status_cell(status)
            
            table.add_row(
                date_str,
                self.style_symbol(symbol),
                str(action_styled),
                f"{confidence:.1%}",
                f"${price:,.2f}" if price > 0 else "N/A",
                result_text,
                str(status_styled)
            )
        
        return table
    
    def format_alerts(self, alerts_data: Dict[str, Any], **kwargs) -> Panel:
        """
        Formate les alertes et warnings.
        
        Args:
            alerts_data: Données d'alertes
            **kwargs: Options de formatage
            
        Returns:
            Panel avec les alertes
        """
        alerts = alerts_data.get("alerts", [])
        warnings = alerts_data.get("warnings", [])
        errors = alerts_data.get("errors", [])
        
        content_parts = []
        
        # Erreurs (priorité haute)
        if errors:
            content_parts.append("🚨 ERREURS:")
            for error in errors:
                message = error.get("message", "Erreur inconnue")
                timestamp = error.get("timestamp", "")
                content_parts.append(f"  • {self.style_error(message)}")
                if timestamp:
                    content_parts.append(f"    └─ {timestamp}")
            content_parts.append("")
        
        # Warnings (priorité moyenne)
        if warnings:
            content_parts.append("⚠️  AVERTISSEMENTS:")
            for warning in warnings:
                message = warning.get("message", "Avertissement inconnu")
                timestamp = warning.get("timestamp", "")
                content_parts.append(f"  • {self.style_warning(message)}")
                if timestamp:
                    content_parts.append(f"    └─ {timestamp}")
            content_parts.append("")
        
        # Alertes informatives
        if alerts:
            content_parts.append("ℹ️  ALERTES:")
            for alert in alerts:
                message = alert.get("message", "Alerte inconnue")
                timestamp = alert.get("timestamp", "")
                level = alert.get("level", "INFO")
                
                if level.upper() == "HIGH":
                    styled_message = Text(f"🔴 {message}", style="red")
                elif level.upper() == "MEDIUM":
                    styled_message = Text(f"🟡 {message}", style="yellow")
                else:
                    styled_message = Text(f"🟢 {message}", style="green")
                
                content_parts.append(f"  • {styled_message}")
                if timestamp:
                    content_parts.append(f"    └─ {timestamp}")
        
        if not content_parts:
            content_parts.append("✅ Aucune alerte active")
        
        content = "\n".join(content_parts)
        
        # Style selon le niveau de gravité
        if errors:
            style = "red"
        elif warnings:
            style = "yellow"
        else:
            style = "green"
        
        return self.create_panel(
            content,
            title="🚨 Centre d'Alertes",
            style=style
        )
    
    def format_simulation_result(self, simulation_data: Dict[str, Any], **kwargs) -> Layout:
        """
        Formate les résultats de simulation.
        
        Args:
            simulation_data: Données de simulation
            **kwargs: Options de formatage
            
        Returns:
            Layout avec les résultats
        """
        layout = Layout()
        
        # Informations de simulation
        sim_info = self._create_simulation_info_panel(simulation_data)
        
        # Résultats principaux
        results_table = self._create_simulation_results_table(simulation_data)
        
        # Scénarios testés
        scenarios_panel = self._create_scenarios_panel(simulation_data.get("scenarios", []))
        
        # Métriques de performance
        metrics_panel = self._create_simulation_metrics(simulation_data.get("metrics", {}))
        
        # Organisation du layout
        layout.split_row(
            Layout(name="left", ratio=2),
            Layout(name="right", ratio=1)
        )
        
        layout["left"].split_column(
            Layout(sim_info, size=6),
            Layout(results_table)
        )
        
        layout["right"].split_column(
            Layout(metrics_panel, size=10),
            Layout(scenarios_panel)
        )
        
        return layout
    
    def format_decision_list(self, decisions: List[Dict[str, Any]], **kwargs) -> Table:
        """
        Formate une liste simple de décisions.
        
        Args:
            decisions: Liste des décisions
            **kwargs: Options de formatage
            
        Returns:
            Table des décisions
        """
        max_rows = kwargs.get("max_rows", 20)
        title = kwargs.get("title", "Décisions")
        
        table = self.create_table(title=title, show_lines=True)
        
        table.add_column("Symbole", style="cyan bold")
        table.add_column("Action", justify="center")
        table.add_column("Confiance", justify="right")
        table.add_column("Reasoning", no_wrap=False)
        
        # Limitation du nombre de lignes
        display_decisions = decisions[:max_rows] if len(decisions) > max_rows else decisions
        
        for decision in display_decisions:
            symbol = decision.get("symbol", "N/A")
            action = decision.get("action", "HOLD")
            confidence = decision.get("confidence", 0)
            reasoning = decision.get("reasoning_summary", "")
            
            action_styled = self._format_action_cell(action)
            reasoning_truncated = self.truncate_text(reasoning, 60)
            
            table.add_row(
                self.style_symbol(symbol),
                str(action_styled),
                f"{confidence:.1%}",
                reasoning_truncated
            )
        
        return table
    
    # === Méthodes privées pour créer les composants ===
    
    def _create_decision_panel(self, decision_data: Dict[str, Any]) -> Panel:
        """Crée le panel principal de décision."""
        symbol = decision_data.get("symbol", "N/A")
        action = decision_data.get("decision", "HOLD")
        confidence = decision_data.get("confidence", 0)
        timestamp = decision_data.get("timestamp", datetime.now())
        
        content_parts = []
        
        # Header avec timestamp
        if isinstance(timestamp, datetime):
            time_str = self.format_datetime(timestamp)
        else:
            time_str = str(timestamp)
        content_parts.append(f"📅 {time_str}")
        content_parts.append("")
        
        # Décision principale
        action_styled = self._format_action_with_emoji(action, confidence)
        content_parts.append(f"🎯 Décision: {action_styled}")
        
        # Score de confiance
        confidence_bar = self._create_confidence_bar(confidence)
        content_parts.append(f"📊 Confiance: {confidence_bar}")
        
        # Prix recommandés
        price_levels = decision_data.get("price_levels", {})
        if price_levels:
            content_parts.append("")
            content_parts.append("💰 Niveaux de prix:")
            
            for level_type, price in price_levels.items():
                level_name = level_type.replace("_", " ").title()
                content_parts.append(f"  • {level_name}: {self.style_currency(price)}")
        
        # Horizon de temps
        timeframe = decision_data.get("timeframe", "")
        if timeframe:
            content_parts.append(f"⏰ Horizon: {timeframe}")
        
        content = "\n".join(content_parts)
        
        # Style selon l'action
        style = self._get_action_style(action)
        
        return self.create_panel(
            content,
            title=f"🤖 Décision - {self.style_symbol(symbol)}",
            style=style
        )
    
    def _create_reasoning_tree(self, reasoning: Dict[str, Any]) -> Panel:
        """Crée l'arbre de reasoning."""
        if not reasoning:
            return self.create_panel("Pas de reasoning détaillé disponible", title="💭 Reasoning")
        
        tree = Tree("🧠 Analyse de décision")
        
        # Facteurs techniques
        technical = reasoning.get("technical", {})
        if technical:
            tech_branch = tree.add("📊 Analyse technique")
            for indicator, analysis in technical.items():
                if isinstance(analysis, dict):
                    signal = analysis.get("signal", "NEUTRE")
                    strength = analysis.get("strength", 0)
                    emoji = "🟢" if signal == "BUY" else "🔴" if signal == "SELL" else "🟡"
                    tech_branch.add(f"{emoji} {indicator}: {signal} (force: {strength:.1f})")
                else:
                    tech_branch.add(f"• {indicator}: {analysis}")
        
        # Facteurs fondamentaux
        fundamental = reasoning.get("fundamental", {})
        if fundamental:
            fund_branch = tree.add("📈 Analyse fondamentale")
            for metric, value in fundamental.items():
                fund_branch.add(f"• {metric}: {value}")
        
        # Sentiment de marché
        sentiment = reasoning.get("sentiment", {})
        if sentiment:
            sent_branch = tree.add("😊 Sentiment de marché")
            for source, data in sentiment.items():
                if isinstance(data, dict):
                    sentiment_val = data.get("sentiment", "NEUTRE")
                    score = data.get("score", 0)
                    emoji = "😊" if sentiment_val == "POSITIF" else "😟" if sentiment_val == "NÉGATIF" else "😐"
                    sent_branch.add(f"{emoji} {source}: {sentiment_val} ({score:.2f})")
                else:
                    sent_branch.add(f"• {source}: {data}")
        
        # Facteurs de risque
        risks = reasoning.get("risks", [])
        if risks:
            risk_branch = tree.add("⚠️  Facteurs de risque")
            for risk in risks[:5]:  # Top 5
                risk_branch.add(f"⚠️  {risk}")
        
        # Catalyseurs
        catalysts = reasoning.get("catalysts", [])
        if catalysts:
            cat_branch = tree.add("🚀 Catalyseurs")
            for catalyst in catalysts[:5]:  # Top 5
                cat_branch.add(f"🚀 {catalyst}")
        
        return self.create_panel(tree, title="💭 Reasoning Détaillé", style="blue")
    
    def _create_confidence_metrics(self, decision_data: Dict[str, Any]) -> Panel:
        """Crée le panel des métriques de confiance."""
        confidence = decision_data.get("confidence", 0)
        confidence_breakdown = decision_data.get("confidence_breakdown", {})
        
        content_parts = []
        
        # Score global
        confidence_bar = self._create_confidence_bar(confidence)
        content_parts.append(f"📊 Score global:")
        content_parts.append(f"{confidence_bar}")
        content_parts.append("")
        
        # Répartition par composant
        if confidence_breakdown:
            content_parts.append("🔍 Détail par composant:")
            for component, score in confidence_breakdown.items():
                component_name = component.replace("_", " ").title()
                bar = self.create_horizontal_bar(
                    component_name[:12],
                    score,
                    1.0,
                    width=15
                )
                content_parts.append(f"  {bar}")
        
        # Facteurs d'incertitude
        uncertainties = decision_data.get("uncertainties", [])
        if uncertainties:
            content_parts.append("")
            content_parts.append("❓ Incertitudes:")
            for uncertainty in uncertainties[:3]:
                content_parts.append(f"  • {uncertainty}")
        
        content = "\n".join(content_parts)
        
        style = "green" if confidence >= 0.8 else "yellow" if confidence >= 0.6 else "red"
        
        return self.create_panel(
            content,
            title="🎯 Métriques de Confiance",
            style=style
        )
    
    def _create_risk_factors(self, risk_factors: List[Dict[str, Any]]) -> Panel:
        """Crée le panel des facteurs de risque."""
        content_parts = []
        
        if not risk_factors:
            content_parts.append("✅ Aucun risque majeur identifié")
        else:
            # Tri par niveau de risque
            sorted_risks = sorted(
                risk_factors,
                key=lambda x: x.get("level", 0),
                reverse=True
            )
            
            for risk in sorted_risks[:5]:  # Top 5
                description = risk.get("description", "Risque non spécifié")
                level = risk.get("level", 0)
                category = risk.get("category", "Général")
                
                # Style selon le niveau
                if level >= 0.8:
                    emoji = "🚨"
                    style = "red bold"
                elif level >= 0.6:
                    emoji = "⚠️"
                    style = "yellow"
                else:
                    emoji = "ℹ️"
                    style = "blue"
                
                risk_text = Text(f"{emoji} {description}", style=style)
                content_parts.append(f"{risk_text}")
                content_parts.append(f"  └─ Catégorie: {category} | Niveau: {level:.1%}")
                content_parts.append("")
        
        content = "\n".join(content_parts)
        
        # Style selon le risque global
        max_risk = max([r.get("level", 0) for r in risk_factors]) if risk_factors else 0
        style = "red" if max_risk >= 0.8 else "yellow" if max_risk >= 0.6 else "green"
        
        return self.create_panel(
            content,
            title="⚠️  Analyse des Risques",
            style=style
        )
    
    def _create_simulation_info_panel(self, simulation_data: Dict[str, Any]) -> Panel:
        """Crée le panel d'informations de simulation."""
        name = simulation_data.get("simulation_name", "Simulation")
        start_date = simulation_data.get("start_date")
        end_date = simulation_data.get("end_date")
        scenarios_count = len(simulation_data.get("scenarios", []))
        
        content_parts = []
        content_parts.append(f"📋 Nom: {name}")
        
        if start_date and end_date:
            content_parts.append(f"📅 Période: {start_date} → {end_date}")
        
        content_parts.append(f"🎭 Scénarios testés: {scenarios_count}")
        
        execution_time = simulation_data.get("execution_time")
        if execution_time:
            content_parts.append(f"⏱️  Temps d'exécution: {execution_time:.2f}s")
        
        content = "\n".join(content_parts)
        
        return self.create_panel(
            content,
            title="🎮 Simulation de Décision",
            style="blue"
        )
    
    def _create_simulation_results_table(self, simulation_data: Dict[str, Any]) -> Table:
        """Crée le tableau des résultats de simulation."""
        scenarios = simulation_data.get("scenarios", [])
        
        table = self.create_table(
            title="📊 Résultats par Scénario",
            show_lines=True
        )
        
        table.add_column("Scénario", style="cyan")
        table.add_column("Décision", justify="center")
        table.add_column("Confiance", justify="right")
        table.add_column("P&L Simulé", justify="right")
        table.add_column("Probabilité", justify="right")
        
        for scenario in scenarios:
            name = scenario.get("name", "Scénario")
            decision = scenario.get("decision", "HOLD")
            confidence = scenario.get("confidence", 0)
            simulated_pnl = scenario.get("simulated_pnl", 0)
            probability = scenario.get("probability", 0)
            
            decision_styled = self._format_action_cell(decision)
            pnl_styled = self.style_currency(simulated_pnl)
            
            table.add_row(
                name,
                str(decision_styled),
                f"{confidence:.1%}",
                str(pnl_styled),
                f"{probability:.1%}"
            )
        
        return table
    
    def _create_scenarios_panel(self, scenarios: List[Dict[str, Any]]) -> Panel:
        """Crée le panel des scénarios."""
        if not scenarios:
            content = "Aucun scénario défini"
        else:
            content_parts = []
            for i, scenario in enumerate(scenarios[:3], 1):
                name = scenario.get("name", f"Scénario {i}")
                description = scenario.get("description", "")
                probability = scenario.get("probability", 0)
                
                content_parts.append(f"🎭 {name} ({probability:.1%})")
                if description:
                    content_parts.append(f"  {self.truncate_text(description, 40)}")
                content_parts.append("")
            
            content = "\n".join(content_parts)
        
        return self.create_panel(
            content,
            title="🎭 Scénarios",
            style="yellow"
        )
    
    def _create_simulation_metrics(self, metrics: Dict[str, Any]) -> Panel:
        """Crée le panel des métriques de simulation."""
        content_parts = []
        
        success_rate = metrics.get("success_rate", 0)
        avg_confidence = metrics.get("average_confidence", 0)
        expected_return = metrics.get("expected_return", 0)
        risk_score = metrics.get("risk_score", 0)
        
        content_parts.append(f"✅ Taux de réussite: {self.style_percentage(success_rate)}")
        content_parts.append(f"🎯 Confiance moyenne: {avg_confidence:.1%}")
        content_parts.append(f"💰 Retour attendu: {self.style_currency(expected_return)}")
        content_parts.append(f"⚠️  Score de risque: {risk_score:.2f}")
        
        # Recommandation globale
        if success_rate > 0.7 and avg_confidence > 0.8:
            recommendation = "🟢 Recommandation: FORTE"
            style = "green"
        elif success_rate > 0.5 and avg_confidence > 0.6:
            recommendation = "🟡 Recommandation: MODÉRÉE"
            style = "yellow"
        else:
            recommendation = "🔴 Recommandation: FAIBLE"
            style = "red"
        
        content_parts.append("")
        content_parts.append(recommendation)
        
        content = "\n".join(content_parts)
        
        return self.create_panel(
            content,
            title="📊 Métriques Globales",
            style=style
        )
    
    # === Méthodes utilitaires ===
    
    def _create_confidence_bar(self, confidence: float) -> str:
        """Crée une barre de confiance."""
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
    
    def _format_action_cell(self, action: str) -> Text:
        """Formate une cellule d'action."""
        action_upper = action.upper()
        
        if action_upper in ["BUY", "ACHAT"]:
            return Text("🟢 BUY", style="green bold")
        elif action_upper in ["SELL", "VENTE"]:
            return Text("🔴 SELL", style="red bold")
        else:
            return Text("🟡 HOLD", style="yellow bold")
    
    def _format_action_with_emoji(self, action: str, confidence: float) -> Text:
        """Formate une action avec emoji et confiance."""
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
    
    def _format_status_cell(self, status: str) -> Text:
        """Formate une cellule de status."""
        status_upper = status.upper()
        
        if status_upper == "EXECUTED":
            return Text("✅ EXÉCUTÉ", style="green")
        elif status_upper == "PENDING":
            return Text("⏳ EN ATTENTE", style="yellow")
        elif status_upper == "CANCELLED":
            return Text("❌ ANNULÉ", style="red")
        else:
            return Text(status_upper, style="blue")
    
    def _get_action_style(self, action: str) -> str:
        """Retourne le style selon l'action."""
        action_upper = action.upper()
        
        if action_upper in ["BUY", "ACHAT"]:
            return "green"
        elif action_upper in ["SELL", "VENTE"]:
            return "red"
        else:
            return "blue"