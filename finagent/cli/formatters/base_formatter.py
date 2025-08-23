"""
Formatter de base pour la CLI FinAgent.

Ce module fournit la classe de base et les utilitaires communs
pour le formatage cohérent de toutes les sorties CLI.
"""

import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from decimal import Decimal
from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.style import Style
from rich.progress import Progress
from rich.align import Align
from rich.layout import Layout
from rich.markup import escape


class BaseFormatter(ABC):
    """
    Classe de base pour tous les formatters CLI.
    
    Fournit des utilitaires communs et un interface cohérente
    pour le formatage des sorties utilisateur.
    """
    
    def __init__(self, console: Optional[Console] = None):
        """
        Initialise le formatter de base.
        
        Args:
            console: Instance Rich Console à utiliser (optionnel)
        """
        self.console = console or Console()
        self.terminal_width = self._get_terminal_width()
        
    def _get_terminal_width(self) -> int:
        """Retourne la largeur du terminal."""
        try:
            return min(self.console.size.width, 120)  # Max 120 chars
        except (AttributeError, OSError):
            return 80  # Fallback
    
    # === Méthodes de formatage des couleurs et styles ===
    
    def style_positive(self, value: Union[str, float, Decimal]) -> Text:
        """Style pour valeurs positives (gains)."""
        return Text(str(value), style="green bold")
    
    def style_negative(self, value: Union[str, float, Decimal]) -> Text:
        """Style pour valeurs négatives (pertes)."""
        return Text(str(value), style="red bold")
    
    def style_neutral(self, value: Union[str, float, Decimal]) -> Text:
        """Style pour valeurs neutres."""
        return Text(str(value), style="white")
    
    def style_percentage(self, percentage: float) -> Text:
        """Style pour pourcentages avec couleur selon signe."""
        if percentage > 0:
            return Text(f"+{percentage:.2f}%", style="green bold")
        elif percentage < 0:
            return Text(f"{percentage:.2f}%", style="red bold")
        else:
            return Text(f"{percentage:.2f}%", style="white")
    
    def style_currency(self, amount: Union[float, Decimal], currency: str = "$") -> Text:
        """Style pour montants monétaires."""
        if amount > 0:
            return Text(f"{currency}{amount:,.2f}", style="green")
        elif amount < 0:
            return Text(f"-{currency}{abs(amount):,.2f}", style="red")
        else:
            return Text(f"{currency}{amount:,.2f}", style="white")
    
    def style_symbol(self, symbol: str) -> Text:
        """Style pour symboles boursiers."""
        return Text(symbol.upper(), style="cyan bold")
    
    def style_header(self, text: str) -> Text:
        """Style pour headers."""
        return Text(text, style="blue bold")
    
    def style_success(self, text: str) -> Text:
        """Style pour messages de succès."""
        return Text(f"✅ {text}", style="green")
    
    def style_warning(self, text: str) -> Text:
        """Style pour avertissements."""
        return Text(f"⚠️  {text}", style="yellow")
    
    def style_error(self, text: str) -> Text:
        """Style pour erreurs."""
        return Text(f"❌ {text}", style="red bold")
    
    def style_info(self, text: str) -> Text:
        """Style pour informations."""
        return Text(f"ℹ️  {text}", style="blue")
    
    # === Méthodes de création de tableaux ===
    
    def create_table(
        self,
        title: Optional[str] = None,
        show_header: bool = True,
        show_lines: bool = False,
        expand: bool = True
    ) -> Table:
        """
        Crée un tableau avec le style standard FinAgent.
        
        Args:
            title: Titre du tableau
            show_header: Afficher l'header
            show_lines: Afficher les lignes de séparation
            expand: Étendre à la largeur disponible
            
        Returns:
            Table configuré
        """
        table = Table(
            title=title,
            show_header=show_header,
            show_lines=show_lines,
            expand=expand,
            title_style="bold blue",
            header_style="bold cyan",
            border_style="blue"
        )
        return table
    
    def create_panel(
        self,
        content: Union[str, Text],
        title: Optional[str] = None,
        subtitle: Optional[str] = None,
        style: str = "blue"
    ) -> Panel:
        """
        Crée un panel avec le style standard.
        
        Args:
            content: Contenu du panel
            title: Titre du panel
            subtitle: Sous-titre du panel
            style: Style de la bordure
            
        Returns:
            Panel configuré
        """
        return Panel(
            content,
            title=title,
            subtitle=subtitle,
            border_style=style,
            title_justify="left"
        )
    
    # === Méthodes utilitaires de formatage ===
    
    def format_datetime(self, dt: datetime, include_time: bool = True) -> str:
        """Formate une datetime."""
        if include_time:
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        return dt.strftime("%Y-%m-%d")
    
    def format_large_number(self, number: Union[int, float, Decimal]) -> str:
        """Formate les grands nombres (K, M, B)."""
        if abs(number) >= 1_000_000_000:
            return f"{number/1_000_000_000:.2f}B"
        elif abs(number) >= 1_000_000:
            return f"{number/1_000_000:.2f}M"
        elif abs(number) >= 1_000:
            return f"{number/1_000:.2f}K"
        else:
            return f"{number:.2f}"
    
    def truncate_text(self, text: str, max_length: int = 50) -> str:
        """Tronque le texte si trop long."""
        if len(text) <= max_length:
            return text
        return f"{text[:max_length-3]}..."
    
    def create_progress_bar(self, description: str = "Progression") -> Progress:
        """Crée une barre de progression standard."""
        return Progress(
            console=self.console,
            auto_refresh=True,
            refresh_per_second=10
        )
    
    # === Méthodes de génération de graphiques ASCII ===
    
    def create_ascii_chart(
        self,
        data: List[float],
        height: int = 10,
        width: Optional[int] = None
    ) -> str:
        """
        Crée un graphique ASCII simple.
        
        Args:
            data: Données à afficher
            height: Hauteur du graphique
            width: Largeur du graphique (auto si None)
            
        Returns:
            Graphique ASCII sous forme de string
        """
        if not data:
            return "Aucune donnée à afficher"
        
        width = width or min(len(data), self.terminal_width - 10)
        
        # Normalisation des données
        min_val = min(data)
        max_val = max(data)
        value_range = max_val - min_val
        
        if value_range == 0:
            return "Données constantes"
        
        # Création du graphique
        lines = []
        for row in range(height, 0, -1):
            line = ""
            for i in range(min(len(data), width)):
                normalized = (data[i] - min_val) / value_range
                threshold = row / height
                
                if normalized >= threshold:
                    line += "█"
                elif normalized >= threshold - 0.1:
                    line += "▓"
                elif normalized >= threshold - 0.2:
                    line += "▒"
                else:
                    line += " "
            lines.append(line)
        
        return "\n".join(lines)
    
    def create_horizontal_bar(
        self,
        label: str,
        value: float,
        max_value: float,
        width: int = 20
    ) -> str:
        """
        Crée une barre horizontale ASCII.
        
        Args:
            label: Label de la barre
            value: Valeur actuelle
            max_value: Valeur maximale
            width: Largeur de la barre
            
        Returns:
            Barre ASCII formatée
        """
        if max_value == 0:
            filled = 0
        else:
            filled = int((value / max_value) * width)
        
        bar = "█" * filled + "░" * (width - filled)
        percentage = (value / max_value * 100) if max_value > 0 else 0
        
        return f"{label:<15} |{bar}| {percentage:>6.1f}%"
    
    # === Méthodes abstraites à implémenter ===
    
    @abstractmethod
    def format(self, data: Any, **kwargs) -> Union[str, Text, Table, Panel]:
        """
        Méthode principale de formatage.
        
        Args:
            data: Données à formater
            **kwargs: Options de formatage
            
        Returns:
            Données formatées pour affichage
        """
        pass
    
    # === Méthodes d'affichage ===
    
    def print(self, content: Any, **kwargs) -> None:
        """Affiche le contenu formaté."""
        self.console.print(content, **kwargs)
    
    def print_header(self, title: str, subtitle: Optional[str] = None) -> None:
        """Affiche un header principal."""
        header_text = f"🤖 FinAgent - {title}"
        if subtitle:
            header_text += f"\n{subtitle}"
        
        panel = Panel(
            Align.center(header_text),
            style="blue",
            title_justify="center"
        )
        self.console.print(panel)
        self.console.print()
    
    def print_section(self, title: str) -> None:
        """Affiche un titre de section."""
        self.console.print(f"\n📊 {title}", style="cyan bold")
        self.console.print("─" * (len(title) + 4), style="cyan")
    
    def print_separator(self) -> None:
        """Affiche un séparateur."""
        self.console.print("─" * self.terminal_width, style="dim")