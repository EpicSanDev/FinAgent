"""
Gestionnaire de configuration pour FinAgent.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union
import structlog

logger = structlog.get_logger(__name__)


class ConfigError(Exception):
    """Erreur de configuration."""
    pass


class Config:
    """
    Gestionnaire de configuration centralisé.
    
    Charge la configuration depuis:
    1. Le fichier config.yaml
    2. Les variables d'environnement (priorité plus élevée)
    """
    
    def __init__(self, config_file: Optional[Union[str, Path]] = None):
        """
        Initialise la configuration.
        
        Args:
            config_file: Chemin vers le fichier de configuration (optionnel)
        """
        self._config: Dict[str, Any] = {}
        self._config_file = config_file or self._find_config_file()
        
        # Charger la configuration
        self._load_config()
        
        # Appliquer les surcharges d'environnement
        self._apply_env_overrides()
        
        logger.info("Configuration chargée", config_file=str(self._config_file))
    
    def _find_config_file(self) -> Path:
        """Trouve le fichier de configuration."""
        # Chercher config.yaml dans le répertoire courant ou parent
        current_dir = Path.cwd()
        
        # Essayer le répertoire courant
        config_path = current_dir / "config.yaml"
        if config_path.exists():
            return config_path
        
        # Essayer le répertoire parent
        parent_config = current_dir.parent / "config.yaml"
        if parent_config.exists():
            return parent_config
        
        # Essayer le répertoire du script
        script_dir = Path(__file__).parent.parent.parent
        script_config = script_dir / "config.yaml"
        if script_config.exists():
            return script_config
        
        raise ConfigError("Fichier config.yaml non trouvé")
    
    def _load_config(self) -> None:
        """Charge le fichier de configuration YAML."""
        try:
            if not self._config_file.exists():
                raise ConfigError(f"Fichier de configuration non trouvé: {self._config_file}")
            
            with open(self._config_file, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f) or {}
                
        except yaml.YAMLError as e:
            raise ConfigError(f"Erreur lors du parsing YAML: {e}")
        except Exception as e:
            raise ConfigError(f"Erreur lors du chargement de la configuration: {e}")
    
    def _apply_env_overrides(self) -> None:
        """Applique les surcharges des variables d'environnement."""
        # Mappage des variables d'environnement vers les clés de configuration
        env_mappings = {
            'FINAGENT_ENV': 'app.environment',
            'LOG_LEVEL': 'logging.level',
            'DEBUG_MODE': 'app.debug',
            'OPENROUTER_API_KEY': 'apis.openrouter.api_key',
            'OPENBB_PAT': 'apis.openbb.api_key',
            'DATABASE_URL': 'database.url',
            'REDIS_URL': 'cache.redis.url',
            'CACHE_TTL': 'cache.memory.ttl',
            'CACHE_MAXSIZE': 'cache.memory.max_size',
            'DEFAULT_POSITION_SIZE': 'trading.defaults.position_size',
            'DEFAULT_RISK_LIMIT': 'trading.defaults.risk_limit',
            'API_TIMEOUT': 'apis.general.timeout',
            'MAX_RETRIES': 'apis.general.max_retries',
            'MAX_CONCURRENT_ANALYSIS': 'trading.limits.max_concurrent_analysis',
        }
        
        for env_var, config_path in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                self._set_nested_value(config_path, self._convert_env_value(env_value))
    
    def _convert_env_value(self, value: str) -> Union[str, int, float, bool]:
        """Convertit une valeur d'environnement vers le bon type."""
        # Booléens
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # Entiers
        try:
            return int(value)
        except ValueError:
            pass
        
        # Flottants
        try:
            return float(value)
        except ValueError:
            pass
        
        # String par défaut
        return value
    
    def _set_nested_value(self, path: str, value: Any) -> None:
        """Définit une valeur dans un chemin imbriqué (ex: 'app.debug')."""
        keys = path.split('.')
        current = self._config
        
        # Naviguer jusqu'au parent
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Définir la valeur finale
        current[keys[-1]] = value
    
    def get(self, path: str, default: Any = None) -> Any:
        """
        Récupère une valeur de configuration.
        
        Args:
            path: Chemin de la configuration (ex: 'ai.claude.temperature')
            default: Valeur par défaut si non trouvée
            
        Returns:
            Valeur de configuration
        """
        keys = path.split('.')
        current = self._config
        
        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default
    
    def set(self, path: str, value: Any) -> None:
        """
        Définit une valeur de configuration.
        
        Args:
            path: Chemin de la configuration
            value: Valeur à définir
        """
        self._set_nested_value(path, value)
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Récupère une section complète de configuration.
        
        Args:
            section: Nom de la section
            
        Returns:
            Dictionnaire de la section
        """
        return self.get(section, {})
    
    def to_dict(self) -> Dict[str, Any]:
        """Retourne toute la configuration sous forme de dictionnaire."""
        return self._config.copy()
    
    def has(self, path: str) -> bool:
        """
        Vérifie si un chemin de configuration existe.
        
        Args:
            path: Chemin à vérifier
            
        Returns:
            True si le chemin existe
        """
        return self.get(path) is not None
    
    def reload(self) -> None:
        """Recharge la configuration depuis le fichier."""
        self._load_config()
        self._apply_env_overrides()
        logger.info("Configuration rechargée")


# Instance globale de configuration
_config_instance: Optional[Config] = None


def get_config() -> Config:
    """
    Retourne l'instance globale de configuration.
    
    Returns:
        Instance de configuration
    """
    global _config_instance
    
    if _config_instance is None:
        _config_instance = Config()
    
    return _config_instance


def set_config(config: Config) -> None:
    """
    Définit l'instance globale de configuration.
    
    Args:
        config: Instance de configuration
    """
    global _config_instance
    _config_instance = config


def reload_config() -> None:
    """Recharge la configuration globale."""
    global _config_instance
    
    if _config_instance:
        _config_instance.reload()
    else:
        _config_instance = Config()