"""
REPL (Read-Eval-Print Loop) interactif pour FinAgent.

Fournit une interface interactive avancée avec auto-complétion,
historique des commandes et aide contextuelle.
"""

import asyncio
import sys
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
import shlex

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter, NestedCompleter
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.shortcuts import confirm, message_dialog
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.live import Live

# Imports des commandes
from ..commands import COMMANDS
from ..utils import ValidationError

console = Console()


class FinAgentREPL:
    """Interface REPL interactive pour FinAgent."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialise le REPL avec la configuration."""
        self.config_path = config_path
        self.session_start = datetime.now()
        self.command_history = []
        self.is_running = False
        
        # Configuration du style
        self.style = Style.from_dict({
            'prompt': '#00aa00 bold',
            'path': '#884444',
            'continuation': '#888888',
            'completion-menu.completion': 'bg:#008888 #ffffff',
            'completion-menu.completion.current': 'bg:#00aaaa #000000',
            'scrollbar.background': 'bg:#88aaaa',
            'scrollbar.button': 'bg:#222222',
        })
        
        # Configuration des raccourcis clavier
        self.key_bindings = KeyBindings()
        self._setup_key_bindings()
        
        # Préparation de l'auto-complétion
        self.completer = self._create_completer()
        
        # Session Prompt Toolkit
        self.session = PromptSession(
            completer=self.completer,
            style=self.style,
            key_bindings=self.key_bindings,
            history=FileHistory('.finagent_history'),
            complete_while_typing=True,
            enable_history_search=True,
            mouse_support=True
        )
    
    def _setup_key_bindings(self) -> None:
        """Configure les raccourcis clavier personnalisés."""
        
        @self.key_bindings.add('c-h')  # Ctrl+H pour l'aide
        def show_help(event):
            """Affiche l'aide rapide."""
            self._show_quick_help()
        
        @self.key_bindings.add('c-q')  # Ctrl+Q pour quitter
        def quit_repl(event):
            """Quitte le REPL."""
            if confirm("Quitter FinAgent REPL ?"):
                self.is_running = False
                event.app.exit()
        
        @self.key_bindings.add('c-l')  # Ctrl+L pour nettoyer l'écran
        def clear_screen(event):
            """Nettoie l'écran."""
            console.clear()
            self._show_banner()
        
        @self.key_bindings.add('c-r')  # Ctrl+R pour l'historique des résultats
        def show_results_history(event):
            """Affiche l'historique des résultats."""
            self._show_command_history()
    
    def _create_completer(self) -> NestedCompleter:
        """Crée l'auto-compléteur pour les commandes."""
        
        # Commandes de base
        base_commands = {
            'help': None,
            'exit': None,
            'quit': None,
            'clear': None,
            'history': None,
            'status': None
        }
        
        # Commandes principales avec sous-commandes
        main_commands = {}
        for cmd_name, cmd_info in COMMANDS.items():
            # Simulation des sous-commandes (à adapter selon les vraies commandes)
            if cmd_name == 'analyze':
                main_commands[cmd_name] = {
                    'stock': WordCompleter(['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN']),
                    'compare': None,
                    'market': None
                }
            elif cmd_name == 'portfolio':
                main_commands[cmd_name] = {
                    'create': None,
                    'add': None,
                    'show': None,
                    'list': None,
                    'optimize': None,
                    'performance': None
                }
            elif cmd_name == 'strategy':
                main_commands[cmd_name] = {
                    'create': None,
                    'validate': None,
                    'backtest': None,
                    'optimize': None,
                    'list': None,
                    'show': None
                }
            elif cmd_name == 'decision':
                main_commands[cmd_name] = {
                    'analyze': None,
                    'history': None,
                    'cancel': None,
                    'performance': None,
                    'simulate': None
                }
            elif cmd_name == 'config':
                main_commands[cmd_name] = {
                    'show': None,
                    'set': None,
                    'unset': None,
                    'reset': None,
                    'backup': None,
                    'restore': None,
                    'init': None,
                    'validate': None
                }
        
        # Fusion des commandes
        all_commands = {**base_commands, **main_commands}
        
        return NestedCompleter.from_nested_dict(all_commands)
    
    def _show_banner(self) -> None:
        """Affiche la bannière de bienvenue."""
        banner_text = """
[bold blue]🚀 FinAgent CLI Interactive[/bold blue]
[dim]Agent IA pour l'analyse financière et la gestion de portefeuilles[/dim]

💡 [yellow]Commandes rapides:[/yellow]
   • [cyan]help[/cyan] - Aide complète
   • [cyan]status[/cyan] - État du système  
   • [cyan]analyze stock AAPL[/cyan] - Analyser une action
   • [cyan]portfolio list[/cyan] - Lister les portefeuilles

🔧 [yellow]Raccourcis:[/yellow]
   • [cyan]Ctrl+H[/cyan] - Aide rapide
   • [cyan]Ctrl+L[/cyan] - Nettoyer l'écran
   • [cyan]Ctrl+R[/cyan] - Historique des commandes
   • [cyan]Ctrl+Q[/cyan] - Quitter

📅 Session démarrée: [dim]{start_time}[/dim]
        """.strip()
        
        console.print(Panel(
            banner_text.format(start_time=self.session_start.strftime('%d/%m/%Y %H:%M')),
            title="🎯 FinAgent REPL",
            border_style="blue",
            expand=False
        ))
        console.print()
    
    def _show_quick_help(self) -> None:
        """Affiche l'aide rapide."""
        help_table = Table(title="🆘 Aide Rapide FinAgent", show_header=True)
        help_table.add_column("Commande", style="cyan bold", no_wrap=True)
        help_table.add_column("Description", style="white")
        help_table.add_column("Exemple", style="dim")
        
        help_commands = [
            ("analyze stock SYMBOL", "Analyser une action", "analyze stock AAPL"),
            ("portfolio list", "Lister les portefeuilles", "portfolio list"),
            ("strategy backtest FILE", "Tester une stratégie", "strategy backtest ma_strategy.yaml"),
            ("decision analyze SYMBOL", "Décision de trading", "decision analyze MSFT --amount 5000"),
            ("config show", "Voir la configuration", "config show --section api_keys"),
            ("help [COMMAND]", "Aide détaillée", "help analyze"),
            ("history", "Historique de la session", "history"),
            ("status", "État du système", "status"),
            ("clear", "Nettoyer l'écran", "clear"),
            ("exit / quit", "Quitter", "exit")
        ]
        
        for cmd, desc, example in help_commands:
            help_table.add_row(cmd, desc, example)
        
        console.print(help_table)
        console.print()
    
    def _show_command_history(self) -> None:
        """Affiche l'historique des commandes de la session."""
        if not self.command_history:
            console.print("📭 Aucune commande exécutée dans cette session", style="yellow")
            return
        
        history_table = Table(title="📜 Historique de la Session", show_header=True)
        history_table.add_column("#", style="dim", width=3)
        history_table.add_column("Heure", style="dim", width=8)
        history_table.add_column("Commande", style="cyan")
        history_table.add_column("Statut", justify="center", width=8)
        history_table.add_column("Durée", justify="right", width=8)
        
        for i, entry in enumerate(self.command_history[-20:], 1):  # Dernières 20 commandes
            status_color = "green" if entry['success'] else "red"
            status_text = "✅" if entry['success'] else "❌"
            
            history_table.add_row(
                str(i),
                entry['timestamp'].strftime('%H:%M:%S'),
                entry['command'],
                f"[{status_color}]{status_text}[/{status_color}]",
                f"{entry['duration']:.2f}s"
            )
        
        console.print(history_table)
        console.print()
    
    def _show_system_status(self) -> None:
        """Affiche l'état du système."""
        # Simulation d'informations système
        status_info = {
            "Session": {
                "Durée": str(datetime.now() - self.session_start).split('.')[0],
                "Commandes exécutées": len(self.command_history),
                "Dernière commande": self.command_history[-1]['command'] if self.command_history else "Aucune"
            },
            "Configuration": {
                "Fichier config": self.config_path or "~/.finagent/config.json",
                "Mode verbeux": "Activé" if getattr(self, 'verbose', False) else "Désactivé",
                "Cache": "Activé"
            },
            "Services": {
                "API OpenRouter": "🟢 Connecté" if True else "🔴 Déconnecté",  # Simulation
                "API OpenBB": "🟢 Connecté" if True else "🔴 Déconnecté",
                "Cache local": "🟢 Actif"
            }
        }
        
        for section, data in status_info.items():
            table = Table(title=f"📊 {section}", show_header=True)
            table.add_column("Paramètre", style="cyan")
            table.add_column("Valeur", style="white")
            
            for key, value in data.items():
                table.add_row(key, str(value))
            
            console.print(table)
        
        console.print()
    
    async def _execute_command(self, command_line: str) -> Dict[str, Any]:
        """Exécute une commande et retourne le résultat."""
        start_time = datetime.now()
        success = False
        error_message = None
        
        try:
            # Parsing de la commande
            parts = shlex.split(command_line)
            if not parts:
                return {'success': True, 'duration': 0, 'output': None}
            
            main_cmd = parts[0].lower()
            
            # Commandes intégrées du REPL
            if main_cmd in ['help', '?']:
                if len(parts) > 1:
                    self._show_command_help(parts[1])
                else:
                    self._show_quick_help()
                success = True
            
            elif main_cmd in ['exit', 'quit']:
                self.is_running = False
                console.print("👋 Au revoir !", style="blue")
                success = True
            
            elif main_cmd == 'clear':
                console.clear()
                self._show_banner()
                success = True
            
            elif main_cmd == 'history':
                self._show_command_history()
                success = True
            
            elif main_cmd == 'status':
                self._show_system_status()
                success = True
            
            # Commandes principales FinAgent
            elif main_cmd in COMMANDS:
                # Simulation d'exécution des commandes principales
                await self._execute_main_command(parts)
                success = True
            
            else:
                console.print(f"❌ Commande inconnue: {main_cmd}", style="red")
                console.print("💡 Tapez 'help' pour voir les commandes disponibles")
                error_message = f"Commande inconnue: {main_cmd}"
        
        except KeyboardInterrupt:
            console.print("\n⚠️  Commande interrompue", style="yellow")
            error_message = "Commande interrompue"
        
        except Exception as e:
            console.print(f"❌ Erreur: {e}", style="red")
            error_message = str(e)
        
        finally:
            duration = (datetime.now() - start_time).total_seconds()
            
            # Enregistrement dans l'historique
            self.command_history.append({
                'command': command_line,
                'timestamp': start_time,
                'success': success,
                'duration': duration,
                'error': error_message
            })
            
            return {
                'success': success,
                'duration': duration,
                'error': error_message
            }
    
    async def _execute_main_command(self, parts: List[str]) -> None:
        """Simule l'exécution d'une commande principale."""
        main_cmd = parts[0]
        
        # Simulation avec un spinner
        from ..utils import spinner_manager
        
        with spinner_manager.spinner_context(f"Exécution de {' '.join(parts)}..."):
            await asyncio.sleep(1)  # Simulation
        
        # Message de simulation
        console.print(f"✅ [green]Commande '{' '.join(parts)}' exécutée avec succès[/green]")
        console.print(f"💡 [dim]Note: Intégration avec les vraies commandes en cours de développement[/dim]")
    
    def _show_command_help(self, command: str) -> None:
        """Affiche l'aide pour une commande spécifique."""
        if command in COMMANDS:
            cmd_info = COMMANDS[command]
            console.print(Panel(
                f"[bold cyan]{command}[/bold cyan]\n\n"
                f"📄 Description: {cmd_info['description']}\n"
                f"🏷️  Catégorie: {cmd_info['category']}\n\n"
                f"💡 Pour plus d'informations, utilisez:\n"
                f"   [cyan]finagent {command} --help[/cyan]",
                title=f"🆘 Aide - {command}",
                border_style="blue"
            ))
        else:
            console.print(f"❌ Commande '{command}' inconnue", style="red")
    
    def get_prompt_message(self) -> HTML:
        """Génère le message de prompt personnalisé."""
        # Indicateur de statut
        status_color = "green" if self.is_running else "red"
        
        # Durée de session
        session_duration = datetime.now() - self.session_start
        duration_str = f"{session_duration.seconds // 60}m{session_duration.seconds % 60}s"
        
        return HTML(
            f'<prompt>finagent</prompt>'
            f'<path> [{duration_str}]</path>'
            f'<continuation> › </continuation>'
        )
    
    async def run(self) -> None:
        """Lance la boucle principale du REPL."""
        self.is_running = True
        
        # Affichage de la bannière
        console.clear()
        self._show_banner()
        
        try:
            while self.is_running:
                try:
                    # Prompt interactif
                    command_line = await self.session.prompt_async(
                        self.get_prompt_message(),
                        complete_while_typing=True
                    )
                    
                    # Ignorer les lignes vides
                    if not command_line.strip():
                        continue
                    
                    # Exécution de la commande
                    result = await self._execute_command(command_line.strip())
                    
                    # Affichage optionnel du temps d'exécution
                    if result['duration'] > 1.0:  # Plus d'1 seconde
                        console.print(f"⏱️  Exécutée en {result['duration']:.2f}s", style="dim")
                    
                    console.print()  # Ligne vide pour la lisibilité
                
                except KeyboardInterrupt:
                    console.print("\n👋 Session interrompue. Tapez 'exit' pour quitter proprement.", style="yellow")
                
                except EOFError:
                    # Ctrl+D
                    console.print("\n👋 Au revoir !", style="blue")
                    break
        
        finally:
            # Nettoyage et statistiques de session
            self._show_session_summary()
    
    def _show_session_summary(self) -> None:
        """Affiche un résumé de la session."""
        duration = datetime.now() - self.session_start
        total_commands = len(self.command_history)
        successful_commands = sum(1 for cmd in self.command_history if cmd['success'])
        
        console.print(Panel(
            f"📊 [bold]Résumé de la session[/bold]\n\n"
            f"⏱️  Durée: {str(duration).split('.')[0]}\n"
            f"🔢 Commandes exécutées: {total_commands}\n"
            f"✅ Succès: {successful_commands}\n"
            f"❌ Échecs: {total_commands - successful_commands}\n"
            f"📅 Fin: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
            title="🎯 Session FinAgent REPL",
            border_style="blue"
        ))


# === Fonction principale pour lancer le REPL ===

async def start_repl(config_path: Optional[str] = None, verbose: bool = False) -> None:
    """Lance le REPL interactif FinAgent."""
    try:
        repl = FinAgentREPL(config_path)
        repl.verbose = verbose
        await repl.run()
    
    except Exception as e:
        console.print(f"❌ Erreur fatale du REPL: {e}", style="red")
        if verbose:
            console.print_exception()
        sys.exit(1)


def run_repl_sync(config_path: Optional[str] = None, verbose: bool = False) -> None:
    """Lance le REPL de manière synchrone."""
    try:
        asyncio.run(start_repl(config_path, verbose))
    except KeyboardInterrupt:
        console.print("\n👋 REPL fermé par l'utilisateur", style="yellow")
    except Exception as e:
        console.print(f"❌ Erreur lors du lancement du REPL: {e}", style="red")
        sys.exit(1)


if __name__ == "__main__":
    # Test du REPL
    run_repl_sync()