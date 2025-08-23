"""
Commande de configuration pour la CLI FinAgent.

Cette commande permet de gérer les configurations,
clés API et préférences utilisateur.
"""

import asyncio
import os
from typing import Optional, Dict, Any, List
from pathlib import Path
import json

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.syntax import Syntax

from ..utils import (
    ValidationError, spinner_manager
)

console = Console()

# Configuration par défaut
DEFAULT_CONFIG = {
    "api_keys": {
        "openrouter": None,
        "openbb": None,
        "alpha_vantage": None,
        "finnhub": None
    },
    "preferences": {
        "default_currency": "USD",
        "risk_tolerance": "medium",
        "default_timeframe": "1d",
        "max_position_size": 0.1,
        "enable_notifications": True,
        "auto_save_decisions": False,
        "cache_duration": 3600,
        "log_level": "INFO"
    },
    "portfolio": {
        "default_benchmark": "SPY",
        "commission_rate": 0.001,
        "slippage_rate": 0.0005,
        "initial_capital": 100000.0
    },
    "ai": {
        "model": "claude-3-haiku",
        "temperature": 0.3,
        "max_tokens": 4000,
        "enable_reasoning": True,
        "confidence_threshold": 0.7
    },
    "data": {
        "data_provider": "openbb",
        "update_frequency": "1h",
        "historical_data_years": 5,
        "enable_realtime": False
    },
    "cli": {
        "theme": "auto",
        "verbose": False,
        "show_progress": True,
        "auto_complete": True,
        "color_output": True
    }
}


@click.group()
def config():
    """Commandes de gestion de la configuration."""
    pass


@config.command()
@click.option(
    '--show-sensitive',
    is_flag=True,
    help='Afficher les valeurs sensibles (clés API)'
)
@click.option(
    '--section', '-s',
    type=click.Choice(['api_keys', 'preferences', 'portfolio', 'ai', 'data', 'cli']),
    help='Afficher une section spécifique'
)
@click.option(
    '--format',
    type=click.Choice(['table', 'json', 'yaml']),
    default='table',
    help='Format d\'affichage'
)
@click.pass_context
def show(ctx, show_sensitive: bool, section: Optional[str], format: str):
    """
    Affiche la configuration actuelle.
    
    Exemples:
    \b
        finagent config show
        finagent config show --section api_keys --show-sensitive
        finagent config show --format json
    """
    try:
        verbose = ctx.obj.get('verbose', False) if ctx.obj else False
        
        # Chargement de la configuration
        config_data = _load_config(verbose)
        
        # Filtrage par section si spécifié
        if section:
            if section in config_data:
                config_data = {section: config_data[section]}
            else:
                console.print(f"❌ Section '{section}' non trouvée", style="red")
                return
        
        # Masquage des valeurs sensibles si nécessaire
        if not show_sensitive:
            config_data = _mask_sensitive_values(config_data)
        
        # Affichage selon le format
        if format == 'json':
            console.print_json(json.dumps(config_data, indent=2))
        elif format == 'yaml':
            import yaml
            console.print(yaml.dump(config_data, default_flow_style=False))
        else:
            _display_config_table(config_data, show_sensitive)
    
    except Exception as e:
        console.print(f"❌ Erreur lors de l'affichage: {e}", style="red")
        if verbose:
            console.print_exception()
        ctx.exit(1)


@config.command()
@click.argument('key', required=True)
@click.argument('value', required=False)
@click.option(
    '--type', '-t',
    type=click.Choice(['string', 'int', 'float', 'bool']),
    default='string',
    help='Type de la valeur'
)
@click.option(
    '--secure',
    is_flag=True,
    help='Valeur sensible (sera masquée dans l\'affichage)'
)
@click.option(
    '--validate',
    is_flag=True,
    help='Valider la valeur avant de la définir'
)
@click.pass_context
def set(ctx, key: str, value: Optional[str], type: str, secure: bool, validate: bool):
    """
    Définit une valeur de configuration.
    
    KEY: Clé de configuration (format: section.key)
    VALUE: Valeur à définir (mode interactif si non fournie)
    
    Exemples:
    \b
        finagent config set api_keys.openrouter "sk-..."
        finagent config set preferences.risk_tolerance medium
        finagent config set portfolio.commission_rate 0.001 --type float
    """
    try:
        verbose = ctx.obj.get('verbose', False) if ctx.obj else False
        
        # Validation du format de la clé
        if '.' not in key:
            raise ValidationError("La clé doit être au format 'section.key'")
        
        section, config_key = key.split('.', 1)
        
        # Mode interactif si valeur non fournie
        if value is None:
            value = _prompt_for_value(key, type, secure)
        
        # Conversion du type
        converted_value = _convert_value(value, type)
        
        # Validation si demandée
        if validate:
            _validate_config_value(section, config_key, converted_value)
        
        # Sauvegarde
        _set_config_value(section, config_key, converted_value, verbose)
        
        console.print(f"✅ Configuration mise à jour: {key} = {'***' if secure else converted_value}", style="green")
    
    except ValidationError as e:
        console.print(f"❌ Erreur de validation: {e.message}", style="red")
        ctx.exit(1)
    
    except Exception as e:
        console.print(f"❌ Erreur lors de la mise à jour: {e}", style="red")
        if verbose:
            console.print_exception()
        ctx.exit(1)


@config.command()
@click.argument('key', required=True)
@click.pass_context
def unset(ctx, key: str):
    """
    Supprime une valeur de configuration.
    
    KEY: Clé de configuration à supprimer (format: section.key)
    
    Exemples:
    \b
        finagent config unset api_keys.openrouter
        finagent config unset preferences.custom_setting
    """
    try:
        verbose = ctx.obj.get('verbose', False) if ctx.obj else False
        
        # Validation du format de la clé
        if '.' not in key:
            raise ValidationError("La clé doit être au format 'section.key'")
        
        section, config_key = key.split('.', 1)
        
        # Confirmation
        if not Confirm.ask(f"Supprimer la configuration '{key}' ?"):
            console.print("❌ Suppression annulée", style="yellow")
            return
        
        # Suppression
        _unset_config_value(section, config_key, verbose)
        
        console.print(f"✅ Configuration supprimée: {key}", style="green")
    
    except ValidationError as e:
        console.print(f"❌ Erreur de validation: {e.message}", style="red")
        ctx.exit(1)
    
    except Exception as e:
        console.print(f"❌ Erreur lors de la suppression: {e}", style="red")
        if verbose:
            console.print_exception()
        ctx.exit(1)


@config.command()
@click.option(
    '--backup',
    is_flag=True,
    help='Créer une sauvegarde avant la réinitialisation'
)
@click.option(
    '--section', '-s',
    type=click.Choice(['api_keys', 'preferences', 'portfolio', 'ai', 'data', 'cli']),
    help='Réinitialiser une section spécifique'
)
@click.pass_context
def reset(ctx, backup: bool, section: Optional[str]):
    """
    Remet la configuration aux valeurs par défaut.
    
    Exemples:
    \b
        finagent config reset --backup
        finagent config reset --section preferences
    """
    try:
        verbose = ctx.obj.get('verbose', False) if ctx.obj else False
        
        # Confirmation
        reset_target = f"la section '{section}'" if section else "toute la configuration"
        if not Confirm.ask(f"Réinitialiser {reset_target} aux valeurs par défaut ?"):
            console.print("❌ Réinitialisation annulée", style="yellow")
            return
        
        # Sauvegarde si demandée
        if backup:
            _backup_config(verbose)
            console.print("💾 Sauvegarde créée", style="blue")
        
        # Réinitialisation
        _reset_config(section, verbose)
        
        reset_msg = f"Section '{section}' réinitialisée" if section else "Configuration réinitialisée"
        console.print(f"✅ {reset_msg}", style="green")
    
    except Exception as e:
        console.print(f"❌ Erreur lors de la réinitialisation: {e}", style="red")
        if verbose:
            console.print_exception()
        ctx.exit(1)


@config.command()
@click.option(
    '--output', '-o',
    type=click.Path(),
    help='Fichier de sortie (par défaut: config_backup_YYYYMMDD.json)'
)
@click.option(
    '--include-sensitive',
    is_flag=True,
    help='Inclure les valeurs sensibles dans la sauvegarde'
)
@click.pass_context
def backup(ctx, output: Optional[str], include_sensitive: bool):
    """
    Crée une sauvegarde de la configuration.
    
    Exemples:
    \b
        finagent config backup
        finagent config backup --output my_config.json
        finagent config backup --include-sensitive
    """
    try:
        verbose = ctx.obj.get('verbose', False) if ctx.obj else False
        
        # Nom de fichier par défaut
        if not output:
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output = f"config_backup_{timestamp}.json"
        
        # Création de la sauvegarde
        backup_path = _create_config_backup(output, include_sensitive, verbose)
        
        console.print(f"✅ Sauvegarde créée: {backup_path}", style="green")
    
    except Exception as e:
        console.print(f"❌ Erreur lors de la sauvegarde: {e}", style="red")
        if verbose:
            console.print_exception()
        ctx.exit(1)


@config.command()
@click.argument('backup_file', type=click.Path(exists=True), required=True)
@click.option(
    '--merge',
    is_flag=True,
    help='Fusionner avec la configuration existante'
)
@click.option(
    '--dry-run',
    is_flag=True,
    help='Simuler la restauration sans l\'appliquer'
)
@click.pass_context
def restore(ctx, backup_file: str, merge: bool, dry_run: bool):
    """
    Restaure la configuration depuis une sauvegarde.
    
    BACKUP_FILE: Fichier de sauvegarde à restaurer
    
    Exemples:
    \b
        finagent config restore config_backup.json
        finagent config restore config.json --merge
        finagent config restore backup.json --dry-run
    """
    try:
        verbose = ctx.obj.get('verbose', False) if ctx.obj else False
        
        # Chargement du fichier de sauvegarde
        backup_config = _load_backup_file(backup_file)
        
        # Mode dry-run
        if dry_run:
            console.print("🔍 [blue]Mode simulation - Aucun changement appliqué[/blue]")
            _display_restore_preview(backup_config, merge)
            return
        
        # Confirmation
        action = "Fusionner" if merge else "Remplacer"
        if not Confirm.ask(f"{action} la configuration actuelle avec la sauvegarde ?"):
            console.print("❌ Restauration annulée", style="yellow")
            return
        
        # Restauration
        _restore_config_from_backup(backup_config, merge, verbose)
        
        console.print("✅ Configuration restaurée avec succès", style="green")
    
    except Exception as e:
        console.print(f"❌ Erreur lors de la restauration: {e}", style="red")
        if verbose:
            console.print_exception()
        ctx.exit(1)


@config.command()
@click.pass_context
def init(ctx):
    """
    Initialise la configuration avec un assistant interactif.
    
    Exemples:
    \b
        finagent config init
    """
    try:
        verbose = ctx.obj.get('verbose', False) if ctx.obj else False
        
        console.print(Panel.fit(
            "🚀 [bold blue]Assistant de Configuration FinAgent[/bold blue]\n\n"
            "Cet assistant vous aidera à configurer FinAgent pour vos besoins.\n"
            "Vous pourrez modifier ces paramètres plus tard avec 'finagent config set'.",
            title="🔧 Initialisation",
            border_style="blue"
        ))
        
        # Configuration interactive
        config_data = _interactive_config_setup()
        
        # Sauvegarde
        _save_config(config_data, verbose)
        
        console.print(Panel.fit(
            "✅ [green]Configuration initialisée avec succès![/green]\n\n"
            "💡 Utilisez 'finagent config show' pour voir votre configuration\n"
            "🔧 Utilisez 'finagent config set key value' pour modifier des valeurs",
            title="🎉 Terminé",
            border_style="green"
        ))
    
    except Exception as e:
        console.print(f"❌ Erreur lors de l'initialisation: {e}", style="red")
        if verbose:
            console.print_exception()
        ctx.exit(1)


@config.command()
@click.pass_context
def validate(ctx):
    """
    Valide la configuration actuelle.
    
    Exemples:
    \b
        finagent config validate
    """
    try:
        verbose = ctx.obj.get('verbose', False) if ctx.obj else False
        
        console.print("🔍 Validation de la configuration...", style="blue")
        
        # Validation
        validation_result = _validate_full_config(verbose)
        
        # Affichage des résultats
        _display_validation_results(validation_result)
    
    except Exception as e:
        console.print(f"❌ Erreur lors de la validation: {e}", style="red")
        if verbose:
            console.print_exception()
        ctx.exit(1)


# === Fonctions d'implémentation ===

def _get_config_path() -> Path:
    """Retourne le chemin du fichier de configuration."""
    config_dir = Path.home() / '.finagent'
    config_dir.mkdir(exist_ok=True)
    return config_dir / 'config.json'


def _load_config(verbose: bool = False) -> Dict[str, Any]:
    """Charge la configuration depuis le fichier."""
    config_path = _get_config_path()
    
    if not config_path.exists():
        if verbose:
            console.print("📄 Création de la configuration par défaut", style="dim")
        return DEFAULT_CONFIG.copy()
    
    try:
        with open(config_path, 'r') as f:
            user_config = json.load(f)
        
        # Fusion avec la config par défaut pour les nouvelles clés
        config = DEFAULT_CONFIG.copy()
        _deep_merge(config, user_config)
        return config
    
    except Exception as e:
        console.print(f"⚠️  Erreur de lecture config, utilisation par défaut: {e}", style="yellow")
        return DEFAULT_CONFIG.copy()


def _save_config(config: Dict[str, Any], verbose: bool = False) -> None:
    """Sauvegarde la configuration dans le fichier."""
    config_path = _get_config_path()
    
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        if verbose:
            console.print(f"💾 Configuration sauvegardée: {config_path}", style="dim")
    
    except Exception as e:
        raise Exception(f"Impossible de sauvegarder la configuration: {e}")


def _deep_merge(base: Dict, update: Dict) -> None:
    """Fusionne récursivement deux dictionnaires."""
    for key, value in update.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value


def _mask_sensitive_values(config: Dict[str, Any]) -> Dict[str, Any]:
    """Masque les valeurs sensibles dans la configuration."""
    masked_config = config.copy()
    
    # Masquer les clés API
    if 'api_keys' in masked_config:
        for key, value in masked_config['api_keys'].items():
            if value:
                masked_config['api_keys'][key] = f"{value[:8]}..." if len(str(value)) > 8 else "***"
    
    return masked_config


def _prompt_for_value(key: str, value_type: str, secure: bool) -> str:
    """Demande une valeur à l'utilisateur en mode interactif."""
    if secure:
        return Prompt.ask(f"Valeur pour {key} (sensible)", password=True)
    elif value_type == 'bool':
        return "true" if Confirm.ask(f"Activer {key} ?") else "false"
    elif value_type == 'int':
        return str(IntPrompt.ask(f"Valeur entière pour {key}"))
    else:
        return Prompt.ask(f"Valeur pour {key}")


def _convert_value(value: str, value_type: str) -> Any:
    """Convertit une valeur string vers le type demandé."""
    if value_type == 'bool':
        return value.lower() in ('true', '1', 'yes', 'on', 'enabled')
    elif value_type == 'int':
        return int(value)
    elif value_type == 'float':
        return float(value)
    else:
        return value


def _validate_config_value(section: str, key: str, value: Any) -> None:
    """Valide une valeur de configuration."""
    if section == 'preferences':
        if key == 'risk_tolerance' and value not in ['low', 'medium', 'high']:
            raise ValidationError("risk_tolerance doit être 'low', 'medium' ou 'high'")
        elif key == 'max_position_size' and not (0 < value <= 1):
            raise ValidationError("max_position_size doit être entre 0 et 1")
    
    elif section == 'portfolio':
        if key in ['commission_rate', 'slippage_rate'] and not (0 <= value <= 0.1):
            raise ValidationError(f"{key} doit être entre 0 et 0.1")
        elif key == 'initial_capital' and value <= 0:
            raise ValidationError("initial_capital doit être positif")
    
    elif section == 'ai':
        if key == 'temperature' and not (0 <= value <= 2):
            raise ValidationError("temperature doit être entre 0 et 2")
        elif key == 'confidence_threshold' and not (0 <= value <= 1):
            raise ValidationError("confidence_threshold doit être entre 0 et 1")


def _set_config_value(section: str, key: str, value: Any, verbose: bool) -> None:
    """Définit une valeur de configuration."""
    config = _load_config(verbose)
    
    if section not in config:
        config[section] = {}
    
    config[section][key] = value
    _save_config(config, verbose)


def _unset_config_value(section: str, key: str, verbose: bool) -> None:
    """Supprime une valeur de configuration."""
    config = _load_config(verbose)
    
    if section in config and key in config[section]:
        del config[section][key]
        _save_config(config, verbose)
    else:
        raise Exception(f"Configuration '{section}.{key}' non trouvée")


def _backup_config(verbose: bool) -> str:
    """Crée une sauvegarde automatique de la configuration."""
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f"config_auto_backup_{timestamp}.json"
    return _create_config_backup(backup_name, True, verbose)


def _create_config_backup(filename: str, include_sensitive: bool, verbose: bool) -> str:
    """Crée une sauvegarde de la configuration."""
    config = _load_config(verbose)
    
    if not include_sensitive:
        config = _mask_sensitive_values(config)
    
    backup_path = Path.home() / '.finagent' / 'backups'
    backup_path.mkdir(exist_ok=True)
    
    backup_file = backup_path / filename
    
    with open(backup_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    return str(backup_file)


def _reset_config(section: Optional[str], verbose: bool) -> None:
    """Remet la configuration aux valeurs par défaut."""
    if section:
        config = _load_config(verbose)
        if section in DEFAULT_CONFIG:
            config[section] = DEFAULT_CONFIG[section].copy()
        _save_config(config, verbose)
    else:
        _save_config(DEFAULT_CONFIG.copy(), verbose)


def _load_backup_file(backup_file: str) -> Dict[str, Any]:
    """Charge un fichier de sauvegarde."""
    with open(backup_file, 'r') as f:
        return json.load(f)


def _restore_config_from_backup(backup_config: Dict[str, Any], merge: bool, verbose: bool) -> None:
    """Restaure la configuration depuis une sauvegarde."""
    if merge:
        current_config = _load_config(verbose)
        _deep_merge(current_config, backup_config)
        _save_config(current_config, verbose)
    else:
        _save_config(backup_config, verbose)


def _interactive_config_setup() -> Dict[str, Any]:
    """Configuration interactive complète."""
    config = DEFAULT_CONFIG.copy()
    
    console.print("\n🔑 [bold]Configuration des clés API[/bold]")
    console.print("Les clés API sont optionnelles mais recommandées pour un accès complet aux données.")
    
    # Clés API
    openrouter_key = Prompt.ask(
        "Clé API OpenRouter (pour l'IA)", 
        password=True, 
        default="",
        show_default=False
    )
    if openrouter_key:
        config['api_keys']['openrouter'] = openrouter_key
    
    openbb_key = Prompt.ask(
        "Clé API OpenBB (pour les données financières)", 
        password=True, 
        default="",
        show_default=False
    )
    if openbb_key:
        config['api_keys']['openbb'] = openbb_key
    
    console.print("\n⚙️  [bold]Préférences utilisateur[/bold]")
    
    # Préférences de base
    config['preferences']['default_currency'] = Prompt.ask(
        "Devise par défaut",
        choices=['USD', 'EUR', 'GBP', 'CAD'],
        default='USD'
    )
    
    config['preferences']['risk_tolerance'] = Prompt.ask(
        "Tolérance au risque",
        choices=['low', 'medium', 'high'],
        default='medium'
    )
    
    config['preferences']['enable_notifications'] = Confirm.ask(
        "Activer les notifications ?",
        default=True
    )
    
    console.print("\n📊 [bold]Configuration du portefeuille[/bold]")
    
    # Portefeuille
    config['portfolio']['initial_capital'] = float(Prompt.ask(
        "Capital initial (USD)",
        default="100000"
    ))
    
    config['portfolio']['commission_rate'] = float(Prompt.ask(
        "Taux de commission (%)",
        default="0.1"
    )) / 100
    
    console.print("\n🤖 [bold]Configuration de l'IA[/bold]")
    
    # IA
    config['ai']['temperature'] = float(Prompt.ask(
        "Température du modèle (0-2, plus élevé = plus créatif)",
        default="0.3"
    ))
    
    config['ai']['confidence_threshold'] = float(Prompt.ask(
        "Seuil de confiance minimum (0-1)",
        default="0.7"
    ))
    
    return config


def _validate_full_config(verbose: bool) -> Dict[str, Any]:
    """Valide toute la configuration."""
    config = _load_config(verbose)
    
    issues = []
    warnings = []
    
    # Vérification des clés API
    api_keys = config.get('api_keys', {})
    if not any(api_keys.values()):
        warnings.append("Aucune clé API configurée - fonctionnalités limitées")
    
    # Vérification des préférences
    prefs = config.get('preferences', {})
    if prefs.get('max_position_size', 0) > 0.5:
        warnings.append("max_position_size > 50% - risque élevé")
    
    # Vérification du portefeuille
    portfolio = config.get('portfolio', {})
    if portfolio.get('commission_rate', 0) > 0.01:
        warnings.append("commission_rate > 1% - frais élevés")
    
    return {
        'valid': len(issues) == 0,
        'issues': issues,
        'warnings': warnings,
        'config_sections': list(config.keys()),
        'total_settings': sum(len(section) if isinstance(section, dict) else 1 
                             for section in config.values())
    }


# === Fonctions d'affichage ===

def _display_config_table(config: Dict[str, Any], show_sensitive: bool) -> None:
    """Affiche la configuration sous forme de tableau."""
    for section_name, section_data in config.items():
        if not isinstance(section_data, dict):
            continue
        
        # Titre de section avec emoji
        section_emojis = {
            'api_keys': '🔑',
            'preferences': '⚙️',
            'portfolio': '📊',
            'ai': '🤖',
            'data': '📊',
            'cli': '💻'
        }
        
        emoji = section_emojis.get(section_name, '📋')
        
        table = Table(title=f"{emoji} {section_name.replace('_', ' ').title()}", show_header=True)
        table.add_column("Paramètre", style="cyan")
        table.add_column("Valeur", style="white")
        table.add_column("Type", style="dim")
        
        for key, value in section_data.items():
            # Formatage de la valeur
            if value is None:
                formatted_value = "[dim]Non défini[/dim]"
                value_type = "None"
            elif isinstance(value, bool):
                formatted_value = "✅ Oui" if value else "❌ Non"
                value_type = "bool"
            elif isinstance(value, (int, float)):
                formatted_value = str(value)
                value_type = "number"
            else:
                formatted_value = str(value)
                value_type = "string"
            
            # Masquage pour les API keys
            if section_name == 'api_keys' and not show_sensitive and value:
                formatted_value = "***"
            
            table.add_row(key, formatted_value, value_type)
        
        console.print(table)
        console.print()


def _display_restore_preview(backup_config: Dict[str, Any], merge: bool) -> None:
    """Affiche un aperçu de la restauration."""
    action = "Fusion" if merge else "Remplacement"
    console.print(f"📋 [bold]Aperçu de la restauration ({action})[/bold]\n")
    
    for section, data in backup_config.items():
        if isinstance(data, dict):
            console.print(f"📁 {section}: {len(data)} paramètres")
        else:
            console.print(f"📄 {section}: {data}")


def _display_validation_results(validation_result: Dict[str, Any]) -> None:
    """Affiche les résultats de validation."""
    if validation_result['valid']:
        console.print("✅ [green]Configuration valide![/green]")
    else:
        console.print("❌ [red]Problèmes détectés dans la configuration[/red]")
    
    # Problèmes
    if validation_result['issues']:
        console.print("\n🚨 [red bold]Problèmes:[/red bold]")
        for issue in validation_result['issues']:
            console.print(f"  • {issue}")
    
    # Avertissements
    if validation_result['warnings']:
        console.print("\n⚠️  [yellow bold]Avertissements:[/yellow bold]")
        for warning in validation_result['warnings']:
            console.print(f"  • {warning}")
    
    # Statistiques
    console.print(f"\n📊 [bold]Statistiques:[/bold]")
    console.print(f"  • Sections: {len(validation_result['config_sections'])}")
    console.print(f"  • Paramètres total: {validation_result['total_settings']}")
    console.print(f"  • Sections: {', '.join(validation_result['config_sections'])}")