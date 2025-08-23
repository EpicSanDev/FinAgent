"""
Formatter pour les données de marché.

Ce module gère le formatage élégant des données OHLCV,
indicateurs techniques et informations de marché.
"""

from typing import Any, Dict, List, Optional, Union
from decimal import Decimal
from datetime import datetime
import pandas as pd

from rich.table import Table
from rich.text import Text
from rich.panel import Panel
from rich.columns import Columns
from rich.align import Align

from .base_formatter import BaseFormatter


class MarketFormatter(BaseFormatter):
    """Formatter spécialisé pour les données de marché."""
    
    def format(self, data: Any, **kwargs) -> Union[Table, Panel, Text]:
        """
        Formate les données de marché selon leur type.
        
        Args:
            data: Données de marché à formater
            **kwargs: Options de formatage
            
        Returns:
            Données formatées pour affichage
        """
        if isinstance(data, dict):
            if "ohlcv" in data or "price" in data:
                return self.format_price_data(data, **kwargs)
            elif "indicators" in data:
                return self.format_technical_indicators(data, **kwargs)
            elif "quote" in data:
                return self.format_quote(data, **kwargs)
        elif isinstance(data, pd.DataFrame):
            return self.format_dataframe(data, **kwargs)
        
        return Text(str(data))
    
    def format_quote(self, quote_data: Dict[str, Any], **kwargs) -> Panel:
        """
        Formate une quote de marché en temps réel.
        
        Args:
            quote_data: Données de quote
            **kwargs: Options de formatage
            
        Returns:
            Panel avec les informations de quote
        """
        symbol = quote_data.get("symbol", "N/A")
        price = quote_data.get("price", 0)
        change = quote_data.get("change", 0)
        change_percent = quote_data.get("change_percent", 0)
        volume = quote_data.get("volume", 0)
        market_cap = quote_data.get("market_cap", 0)
        
        # Création du contenu principal
        content_lines = []
        
        # Prix actuel avec variation
        price_text = self.style_currency(price)
        if change != 0:
            change_text = self.style_currency(change)
            percent_text = self.style_percentage(change_percent)
            content_lines.append(f"Prix: {price_text} ({change_text} {percent_text})")
        else:
            content_lines.append(f"Prix: {price_text}")
        
        # Volume et market cap
        if volume > 0:
            volume_formatted = self.format_large_number(volume)
            content_lines.append(f"Volume: {volume_formatted}")
        
        if market_cap > 0:
            mcap_formatted = self.format_large_number(market_cap)
            content_lines.append(f"Market Cap: {mcap_formatted}")
        
        # Timestamp
        timestamp = quote_data.get("timestamp")
        if timestamp:
            if isinstance(timestamp, datetime):
                time_str = self.format_datetime(timestamp)
            else:
                time_str = str(timestamp)
            content_lines.append(f"Dernière mise à jour: {time_str}")
        
        content = "\n".join(content_lines)
        
        # Style du panel selon la performance
        style = "green" if change > 0 else "red" if change < 0 else "blue"
        
        return self.create_panel(
            content,
            title=f"📈 Quote {self.style_symbol(symbol)}",
            style=style
        )
    
    def format_price_data(self, price_data: Dict[str, Any], **kwargs) -> Table:
        """
        Formate les données OHLCV historiques.
        
        Args:
            price_data: Données de prix historiques
            **kwargs: Options de formatage
            
        Returns:
            Table avec les données OHLCV
        """
        symbol = price_data.get("symbol", "N/A")
        ohlcv_data = price_data.get("ohlcv", [])
        
        # Création du tableau
        table = self.create_table(
            title=f"📊 Données de prix - {self.style_symbol(symbol)}",
            show_lines=True
        )
        
        # Headers
        table.add_column("Date", style="cyan", no_wrap=True)
        table.add_column("Ouverture", justify="right")
        table.add_column("Plus Haut", justify="right")
        table.add_column("Plus Bas", justify="right")
        table.add_column("Clôture", justify="right")
        table.add_column("Volume", justify="right")
        table.add_column("Variation", justify="right")
        
        # Ajout des données (dernières 10 sessions par défaut)
        max_rows = kwargs.get("max_rows", 10)
        recent_data = ohlcv_data[-max_rows:] if len(ohlcv_data) > max_rows else ohlcv_data
        
        for row in recent_data:
            date = row.get("date", "N/A")
            open_price = row.get("open", 0)
            high_price = row.get("high", 0)
            low_price = row.get("low", 0)
            close_price = row.get("close", 0)
            volume = row.get("volume", 0)
            
            # Calcul de la variation
            if open_price > 0:
                change_percent = ((close_price - open_price) / open_price) * 100
            else:
                change_percent = 0
            
            # Formatage de la date
            if isinstance(date, datetime):
                date_str = self.format_datetime(date, include_time=False)
            else:
                date_str = str(date)
            
            # Ajout de la ligne
            table.add_row(
                date_str,
                f"${open_price:,.2f}",
                f"${high_price:,.2f}",
                f"${low_price:,.2f}",
                f"${close_price:,.2f}",
                self.format_large_number(volume),
                str(self.style_percentage(change_percent))
            )
        
        return table
    
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
            if signal.upper() == "ACHAT":
                signal_styled = Text("🟢 ACHAT", style="green bold")
            elif signal.upper() == "VENTE":
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
                self.truncate_text(description, 40)
            )
        
        return table
    
    def format_dataframe(self, df: pd.DataFrame, **kwargs) -> Table:
        """
        Formate un DataFrame pandas en table Rich.
        
        Args:
            df: DataFrame à formater
            **kwargs: Options de formatage
            
        Returns:
            Table formatée
        """
        title = kwargs.get("title", "Données de marché")
        max_rows = kwargs.get("max_rows", 20)
        
        # Limitation du nombre de lignes
        if len(df) > max_rows:
            df = df.tail(max_rows)
        
        table = self.create_table(title=title, show_lines=True)
        
        # Ajout des colonnes
        for col in df.columns:
            table.add_column(str(col), justify="right")
        
        # Ajout des données
        for _, row in df.iterrows():
            formatted_row = []
            for value in row:
                if pd.isna(value):
                    formatted_row.append("N/A")
                elif isinstance(value, (int, float)):
                    if abs(value) > 1000:
                        formatted_row.append(self.format_large_number(value))
                    else:
                        formatted_row.append(f"{value:.2f}")
                else:
                    formatted_row.append(str(value))
            
            table.add_row(*formatted_row)
        
        return table
    
    def format_market_overview(self, overview_data: Dict[str, Any], **kwargs) -> Panel:
        """
        Formate un aperçu de marché global.
        
        Args:
            overview_data: Données d'aperçu de marché
            **kwargs: Options de formatage
            
        Returns:
            Panel avec l'aperçu de marché
        """
        indices = overview_data.get("indices", {})
        sectors = overview_data.get("sectors", {})
        market_status = overview_data.get("status", "FERMÉ")
        
        content_parts = []
        
        # Status du marché
        status_style = "green" if market_status == "OUVERT" else "red"
        content_parts.append(f"Status: [{status_style}]{market_status}[/{status_style}]")
        
        # Indices principaux
        if indices:
            content_parts.append("\n📈 Indices principaux:")
            for name, data in indices.items():
                price = data.get("price", 0)
                change = data.get("change_percent", 0)
                change_text = self.style_percentage(change)
                content_parts.append(f"  {name}: ${price:,.2f} ({change_text})")
        
        # Performance sectorielle
        if sectors:
            content_parts.append("\n🏭 Performance sectorielle:")
            sorted_sectors = sorted(
                sectors.items(),
                key=lambda x: x[1].get("change_percent", 0),
                reverse=True
            )[:5]  # Top 5
            
            for name, data in sorted_sectors:
                change = data.get("change_percent", 0)
                change_text = self.style_percentage(change)
                content_parts.append(f"  {name}: {change_text}")
        
        content = "\n".join(content_parts)
        
        return self.create_panel(
            content,
            title="🌍 Aperçu de marché",
            style="blue"
        )
    
    def create_price_chart(self, prices: List[float], **kwargs) -> str:
        """
        Crée un graphique ASCII des prix.
        
        Args:
            prices: Liste des prix
            **kwargs: Options de formatage
            
        Returns:
            Graphique ASCII sous forme de string
        """
        height = kwargs.get("height", 10)
        width = kwargs.get("width", None)
        
        if not prices:
            return "Aucune donnée de prix disponible"
        
        chart = self.create_ascii_chart(prices, height, width)
        
        # Ajout des labels de prix
        min_price = min(prices)
        max_price = max(prices)
        
        labels = [
            f"Max: ${max_price:,.2f}",
            f"Min: ${min_price:,.2f}",
            f"Dernier: ${prices[-1]:,.2f}"
        ]
        
        return f"{chart}\n\n" + " | ".join(labels)
    
    def create_volume_bars(self, volumes: List[float], **kwargs) -> str:
        """
        Crée des barres de volume ASCII.
        
        Args:
            volumes: Liste des volumes
            **kwargs: Options de formatage
            
        Returns:
            Barres de volume ASCII
        """
        if not volumes:
            return "Aucune donnée de volume disponible"
        
        max_volume = max(volumes)
        if max_volume == 0:
            return "Volume nul"
        
        bars = []
        for i, volume in enumerate(volumes[-20:]):  # Dernières 20 sessions
            bar = self.create_horizontal_bar(
                f"J{i+1:2d}",
                volume,
                max_volume,
                width=15
            )
            bars.append(bar)
        
        return "\n".join(bars)