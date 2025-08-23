"""
Formatter pour les données de portefeuille.

Ce module gère le formatage des portefeuilles, positions,
performances et rapports de rééquilibrage.
"""

from typing import Any, Dict, List, Optional, Union
from decimal import Decimal
from datetime import datetime
import math

from rich.table import Table
from rich.text import Text
from rich.panel import Panel
from rich.columns import Columns
from rich.align import Align
from rich.layout import Layout
from rich.progress import Progress, BarColumn, TextColumn, TaskID

from .base_formatter import BaseFormatter


class PortfolioFormatter(BaseFormatter):
    """Formatter spécialisé pour les données de portefeuille."""
    
    def format(self, data: Any, **kwargs) -> Union[Table, Panel, Layout]:
        """
        Formate les données de portefeuille selon leur type.
        
        Args:
            data: Données de portefeuille à formater
            **kwargs: Options de formatage
            
        Returns:
            Données formatées pour affichage
        """
        if isinstance(data, dict):
            if "positions" in data:
                return self.format_portfolio_overview(data, **kwargs)
            elif "performance" in data:
                return self.format_performance_report(data, **kwargs)
            elif "rebalance" in data:
                return self.format_rebalance_report(data, **kwargs)
            elif "allocation" in data:
                return self.format_allocation_chart(data, **kwargs)
        
        return Text(str(data))
    
    def format_portfolio_overview(self, portfolio_data: Dict[str, Any], **kwargs) -> Layout:
        """
        Formate un aperçu complet de portefeuille.
        
        Args:
            portfolio_data: Données complètes du portefeuille
            **kwargs: Options de formatage
            
        Returns:
            Layout avec l'aperçu complet
        """
        layout = Layout()
        
        # Informations générales
        portfolio_info = self._create_portfolio_info_panel(portfolio_data)
        
        # Tableau des positions
        positions_table = self._create_positions_table(portfolio_data.get("positions", []))
        
        # Graphique d'allocation
        allocation_chart = self._create_allocation_panel(portfolio_data.get("allocation", {}))
        
        # Métriques de performance
        performance_panel = self._create_performance_summary(portfolio_data.get("metrics", {}))
        
        # Organisation du layout
        layout.split_row(
            Layout(name="left", ratio=2),
            Layout(name="right", ratio=1)
        )
        
        layout["left"].split_column(
            Layout(portfolio_info, size=6),
            Layout(positions_table)
        )
        
        layout["right"].split_column(
            Layout(performance_panel, size=8),
            Layout(allocation_chart)
        )
        
        return layout
    
    def format_performance_report(self, performance_data: Dict[str, Any], **kwargs) -> Panel:
        """
        Formate un rapport de performance.
        
        Args:
            performance_data: Données de performance
            **kwargs: Options de formatage
            
        Returns:
            Panel avec le rapport de performance
        """
        performance = performance_data.get("performance", {})
        period = performance_data.get("period", "Total")
        
        content_parts = []
        
        # Header avec période
        content_parts.append(f"📊 Période: {period}")
        content_parts.append("─" * 40)
        
        # Rendement total
        total_return = performance.get("total_return", 0)
        total_return_pct = performance.get("total_return_percent", 0)
        if total_return != 0:
            return_text = self.style_currency(total_return)
            return_pct_text = self.style_percentage(total_return_pct)
            content_parts.append(f"💰 Rendement total: {return_text} ({return_pct_text})")
        
        # Rendement annualisé
        annualized_return = performance.get("annualized_return", 0)
        if annualized_return != 0:
            ann_return_text = self.style_percentage(annualized_return)
            content_parts.append(f"📈 Rendement annualisé: {ann_return_text}")
        
        # Volatilité
        volatility = performance.get("volatility", 0)
        if volatility > 0:
            content_parts.append(f"📊 Volatilité: {volatility:.2%}")
        
        # Ratio de Sharpe
        sharpe_ratio = performance.get("sharpe_ratio", 0)
        if sharpe_ratio != 0:
            sharpe_style = "green" if sharpe_ratio > 1 else "yellow" if sharpe_ratio > 0.5 else "red"
            content_parts.append(f"⚖️  Ratio de Sharpe: [{sharpe_style}]{sharpe_ratio:.2f}[/{sharpe_style}]")
        
        # Drawdown maximum
        max_drawdown = performance.get("max_drawdown", 0)
        if max_drawdown != 0:
            dd_text = self.style_negative(f"{max_drawdown:.2%}")
            content_parts.append(f"📉 Drawdown max: {dd_text}")
        
        # Win rate
        win_rate = performance.get("win_rate", 0)
        if win_rate > 0:
            wr_style = "green" if win_rate > 0.6 else "yellow" if win_rate > 0.4 else "red"
            content_parts.append(f"🎯 Taux de réussite: [{wr_style}]{win_rate:.1%}[/{wr_style}]")
        
        # Benchmark comparison
        benchmark_data = performance.get("benchmark", {})
        if benchmark_data:
            content_parts.append(f"\n📊 Comparaison benchmark:")
            benchmark_return = benchmark_data.get("return", 0)
            alpha = performance.get("alpha", total_return_pct - benchmark_return)
            
            bench_text = self.style_percentage(benchmark_return)
            alpha_text = self.style_percentage(alpha)
            content_parts.append(f"  • Benchmark: {bench_text}")
            content_parts.append(f"  • Alpha: {alpha_text}")
        
        content = "\n".join(content_parts)
        
        # Style selon la performance
        style = "green" if total_return_pct > 0 else "red" if total_return_pct < 0 else "blue"
        
        return self.create_panel(
            content,
            title="📈 Rapport de Performance",
            style=style
        )
    
    def format_rebalance_report(self, rebalance_data: Dict[str, Any], **kwargs) -> Layout:
        """
        Formate un rapport de rééquilibrage.
        
        Args:
            rebalance_data: Données de rééquilibrage
            **kwargs: Options de formatage
            
        Returns:
            Layout avec le rapport de rééquilibrage
        """
        layout = Layout()
        
        # Informations générales
        info_panel = self._create_rebalance_info_panel(rebalance_data)
        
        # Actions recommandées
        actions_table = self._create_rebalance_actions_table(
            rebalance_data.get("rebalance", {}).get("actions", [])
        )
        
        # Comparaison avant/après
        comparison_table = self._create_allocation_comparison_table(rebalance_data)
        
        # Organisation du layout
        layout.split_column(
            Layout(info_panel, size=6),
            Layout(actions_table, size=8),
            Layout(comparison_table)
        )
        
        return layout
    
    def format_allocation_chart(self, allocation_data: Dict[str, Any], **kwargs) -> Panel:
        """
        Formate un graphique d'allocation.
        
        Args:
            allocation_data: Données d'allocation
            **kwargs: Options de formatage
            
        Returns:
            Panel avec le graphique d'allocation
        """
        allocation = allocation_data.get("allocation", {})
        total_value = allocation_data.get("total_value", 0)
        
        content_parts = []
        
        if total_value > 0:
            content_parts.append(f"💰 Valeur totale: {self.style_currency(total_value)}")
            content_parts.append("")
        
        # Tri par pourcentage décroissant
        sorted_allocation = sorted(
            allocation.items(),
            key=lambda x: x[1].get("percentage", 0),
            reverse=True
        )
        
        for symbol, data in sorted_allocation:
            percentage = data.get("percentage", 0)
            value = data.get("value", 0)
            
            # Création de la barre de pourcentage
            bar = self.create_horizontal_bar(
                symbol,
                percentage,
                100,
                width=20
            )
            
            value_text = self.style_currency(value)
            content_parts.append(f"{bar} {value_text}")
        
        content = "\n".join(content_parts)
        
        return self.create_panel(
            content,
            title="🥧 Allocation du Portefeuille",
            style="blue"
        )
    
    # === Méthodes privées pour créer les composants ===
    
    def _create_portfolio_info_panel(self, portfolio_data: Dict[str, Any]) -> Panel:
        """Crée le panel d'informations générales du portefeuille."""
        name = portfolio_data.get("name", "Mon Portefeuille")
        created_date = portfolio_data.get("created_date")
        last_updated = portfolio_data.get("last_updated")
        total_value = portfolio_data.get("total_value", 0)
        cash = portfolio_data.get("cash", 0)
        
        content_parts = []
        content_parts.append(f"📁 Nom: {name}")
        
        if created_date:
            if isinstance(created_date, datetime):
                date_str = self.format_datetime(created_date, include_time=False)
            else:
                date_str = str(created_date)
            content_parts.append(f"📅 Créé le: {date_str}")
        
        if last_updated:
            if isinstance(last_updated, datetime):
                update_str = self.format_datetime(last_updated)
            else:
                update_str = str(last_updated)
            content_parts.append(f"🔄 Dernière MAJ: {update_str}")
        
        content_parts.append("")
        content_parts.append(f"💰 Valeur totale: {self.style_currency(total_value)}")
        content_parts.append(f"💵 Liquidités: {self.style_currency(cash)}")
        
        invested = total_value - cash
        if total_value > 0:
            invested_pct = (invested / total_value) * 100
            content_parts.append(f"📊 Investi: {self.style_currency(invested)} ({invested_pct:.1f}%)")
        
        content = "\n".join(content_parts)
        
        return self.create_panel(
            content,
            title="ℹ️  Informations Générales",
            style="blue"
        )
    
    def _create_positions_table(self, positions: List[Dict[str, Any]]) -> Table:
        """Crée le tableau des positions."""
        table = self.create_table(
            title="📊 Positions du Portefeuille",
            show_lines=True
        )
        
        table.add_column("Symbole", style="cyan bold", no_wrap=True)
        table.add_column("Quantité", justify="right")
        table.add_column("Prix Moyen", justify="right")
        table.add_column("Valeur Actuelle", justify="right")
        table.add_column("P&L", justify="right")
        table.add_column("P&L %", justify="right")
        table.add_column("Poids", justify="right")
        
        # Tri par valeur décroissante
        sorted_positions = sorted(
            positions,
            key=lambda x: x.get("current_value", 0),
            reverse=True
        )
        
        for position in sorted_positions:
            symbol = position.get("symbol", "N/A")
            quantity = position.get("quantity", 0)
            avg_price = position.get("average_price", 0)
            current_value = position.get("current_value", 0)
            pnl = position.get("unrealized_pnl", 0)
            pnl_percent = position.get("unrealized_pnl_percent", 0)
            weight = position.get("weight_percent", 0)
            
            # Formatage des valeurs
            pnl_text = self.style_currency(pnl)
            pnl_pct_text = self.style_percentage(pnl_percent)
            
            table.add_row(
                self.style_symbol(symbol),
                f"{quantity:,.0f}",
                f"${avg_price:,.2f}",
                f"${current_value:,.2f}",
                str(pnl_text),
                str(pnl_pct_text),
                f"{weight:.1f}%"
            )
        
        return table
    
    def _create_allocation_panel(self, allocation: Dict[str, Any]) -> Panel:
        """Crée le panel d'allocation."""
        content_parts = []
        
        # Allocation par secteur si disponible
        by_sector = allocation.get("by_sector", {})
        if by_sector:
            content_parts.append("🏭 Par secteur:")
            for sector, percentage in sorted(by_sector.items(), key=lambda x: x[1], reverse=True)[:5]:
                bar = self.create_horizontal_bar(
                    sector[:12],
                    percentage,
                    100,
                    width=15
                )
                content_parts.append(f"  {bar}")
        
        # Allocation par type d'actif
        by_asset_type = allocation.get("by_asset_type", {})
        if by_asset_type:
            if content_parts:
                content_parts.append("")
            content_parts.append("💎 Par type d'actif:")
            for asset_type, percentage in by_asset_type.items():
                bar = self.create_horizontal_bar(
                    asset_type,
                    percentage,
                    100,
                    width=15
                )
                content_parts.append(f"  {bar}")
        
        content = "\n".join(content_parts) if content_parts else "Aucune donnée d'allocation"
        
        return self.create_panel(
            content,
            title="📊 Répartition",
            style="green"
        )
    
    def _create_performance_summary(self, metrics: Dict[str, Any]) -> Panel:
        """Crée le résumé de performance."""
        content_parts = []
        
        # Performance période courante
        daily_return = metrics.get("daily_return", 0)
        weekly_return = metrics.get("weekly_return", 0)
        monthly_return = metrics.get("monthly_return", 0)
        yearly_return = metrics.get("yearly_return", 0)
        
        content_parts.append("📈 Performance:")
        content_parts.append(f"  • Aujourd'hui: {self.style_percentage(daily_return)}")
        content_parts.append(f"  • Cette semaine: {self.style_percentage(weekly_return)}")
        content_parts.append(f"  • Ce mois: {self.style_percentage(monthly_return)}")
        content_parts.append(f"  • Cette année: {self.style_percentage(yearly_return)}")
        
        # Métriques de risque
        content_parts.append("")
        content_parts.append("⚖️  Risque:")
        
        volatility = metrics.get("volatility", 0)
        if volatility > 0:
            content_parts.append(f"  • Volatilité: {volatility:.2%}")
        
        var_95 = metrics.get("var_95", 0)
        if var_95 != 0:
            var_text = self.style_negative(f"{var_95:.2%}")
            content_parts.append(f"  • VaR (95%): {var_text}")
        
        beta = metrics.get("beta", 0)
        if beta > 0:
            content_parts.append(f"  • Beta: {beta:.2f}")
        
        content = "\n".join(content_parts)
        
        # Style selon la performance globale
        overall_performance = yearly_return if yearly_return != 0 else monthly_return
        style = "green" if overall_performance > 0 else "red" if overall_performance < 0 else "blue"
        
        return self.create_panel(
            content,
            title="📊 Métriques",
            style=style
        )
    
    def _create_rebalance_info_panel(self, rebalance_data: Dict[str, Any]) -> Panel:
        """Crée le panel d'informations de rééquilibrage."""
        rebalance = rebalance_data.get("rebalance", {})
        
        content_parts = []
        
        # Raisons du rééquilibrage
        triggers = rebalance.get("triggers", [])
        if triggers:
            content_parts.append("🎯 Déclencheurs:")
            for trigger in triggers:
                content_parts.append(f"  • {trigger}")
        
        # Coût estimé
        estimated_cost = rebalance.get("estimated_cost", 0)
        if estimated_cost > 0:
            content_parts.append(f"\n💰 Coût estimé: {self.style_currency(estimated_cost)}")
        
        # Impact sur les taxes
        tax_impact = rebalance.get("tax_impact", 0)
        if tax_impact > 0:
            content_parts.append(f"🏛️  Impact fiscal: {self.style_currency(tax_impact)}")
        
        # Bénéfice attendu
        expected_benefit = rebalance.get("expected_benefit", "")
        if expected_benefit:
            content_parts.append(f"\n📈 Bénéfice attendu: {expected_benefit}")
        
        content = "\n".join(content_parts)
        
        return self.create_panel(
            content,
            title="🔄 Rééquilibrage Recommandé",
            style="yellow"
        )
    
    def _create_rebalance_actions_table(self, actions: List[Dict[str, Any]]) -> Table:
        """Crée le tableau des actions de rééquilibrage."""
        table = self.create_table(
            title="🎯 Actions Recommandées",
            show_lines=True
        )
        
        table.add_column("Action", style="cyan", no_wrap=True)
        table.add_column("Symbole", style="bold")
        table.add_column("Quantité", justify="right")
        table.add_column("Montant", justify="right")
        table.add_column("Nouveau Poids", justify="right")
        table.add_column("Priorité", justify="center")
        
        # Tri par priorité
        sorted_actions = sorted(
            actions,
            key=lambda x: x.get("priority", 0),
            reverse=True
        )
        
        for action in sorted_actions:
            action_type = action.get("action", "HOLD")
            symbol = action.get("symbol", "N/A")
            quantity = action.get("quantity", 0)
            amount = action.get("amount", 0)
            new_weight = action.get("new_weight_percent", 0)
            priority = action.get("priority", 0)
            
            # Formatage de l'action
            if action_type.upper() == "BUY":
                action_styled = Text("🟢 ACHAT", style="green bold")
            elif action_type.upper() == "SELL":
                action_styled = Text("🔴 VENTE", style="red bold")
            else:
                action_styled = Text("🟡 HOLD", style="yellow")
            
            # Formatage de la priorité
            priority_stars = "★" * min(int(priority), 5)
            
            table.add_row(
                str(action_styled),
                self.style_symbol(symbol),
                f"{quantity:,.0f}",
                str(self.style_currency(amount)),
                f"{new_weight:.1f}%",
                priority_stars
            )
        
        return table
    
    def _create_allocation_comparison_table(self, rebalance_data: Dict[str, Any]) -> Table:
        """Crée le tableau de comparaison avant/après."""
        table = self.create_table(
            title="📊 Comparaison Allocation",
            show_lines=True
        )
        
        table.add_column("Symbole", style="cyan bold")
        table.add_column("Avant", justify="right")
        table.add_column("Après", justify="right")
        table.add_column("Écart", justify="right")
        table.add_column("Tendance", justify="center")
        
        current_allocation = rebalance_data.get("current_allocation", {})
        target_allocation = rebalance_data.get("target_allocation", {})
        
        # Ensemble de tous les symboles
        all_symbols = set(current_allocation.keys()) | set(target_allocation.keys())
        
        for symbol in sorted(all_symbols):
            current_weight = current_allocation.get(symbol, 0)
            target_weight = target_allocation.get(symbol, 0)
            difference = target_weight - current_weight
            
            # Formatage de la tendance
            if abs(difference) < 0.1:
                trend = Text("→", style="yellow")
            elif difference > 0:
                trend = Text("↗", style="green")
            else:
                trend = Text("↘", style="red")
            
            # Formatage de l'écart
            diff_text = self.style_percentage(difference)
            
            table.add_row(
                self.style_symbol(symbol),
                f"{current_weight:.1f}%",
                f"{target_weight:.1f}%",
                str(diff_text),
                trend
            )
        
        return table