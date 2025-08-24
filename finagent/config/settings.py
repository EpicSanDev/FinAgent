"""
Configuration des paramètres de FinAgent

Ce module gère le chargement et la validation de la configuration
depuis les fichiers YAML et les variables d'environnement.
"""

from pathlib import Path
from typing import Optional, Dict, Any
import os

from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import yaml

from finagent.core.errors.exceptions import ConfigurationError


class DatabaseSettings(BaseSettings):
    """Configuration de la base de données."""
    url: str = Field(default="sqlite:///./data/finagent.db")
    echo: bool = Field(default=False)
    pool_size: int = Field(default=5)
    max_overflow: int = Field(default=10)
    pool_timeout: int = Field(default=30)
    pool_recycle: int = Field(default=3600)


class APISettings(BaseSettings):
    """Configuration des APIs externes."""
    openrouter_api_key: Optional[str] = Field(default=None)
    openrouter_base_url: str = Field(default="https://openrouter.ai/api/v1")
    openrouter_model: str = Field(default="anthropic/claude-3-sonnet-20240229")
    
    openbb_pat: Optional[str] = Field(default=None)
    # API OpenBB v1 base URL
    openbb_base_url: str = Field(default="https://api.openbb.co/v1")
    
    api_timeout: int = Field(default=30)
    max_retries: int = Field(default=3)
    retry_delay: int = Field(default=1)


class CacheSettings(BaseSettings):
    """Configuration du système de cache."""
    memory_enabled: bool = Field(default=True)
    memory_max_size: int = Field(default=1000)
    memory_ttl: int = Field(default=300)
    
    file_enabled: bool = Field(default=True)
    file_directory: str = Field(default="./data/cache")
    file_max_size_mb: int = Field(default=100)
    file_ttl: int = Field(default=3600)


class LoggingSettings(BaseSettings):
    """Configuration du logging."""
    level: str = Field(default="INFO")
    format: str = Field(default="structured")
    file_enabled: bool = Field(default=True)
    file_path: str = Field(default="./data/logs/finagent.log")
    console_enabled: bool = Field(default=True)
    console_colored: bool = Field(default=True)


class TradingSettings(BaseSettings):
    """Configuration des paramètres de trading."""
    default_position_size: float = Field(default=1000.0)
    default_risk_limit: float = Field(default=2.0)
    max_positions: int = Field(default=20)
    currency: str = Field(default="USD")
    
    @validator('default_risk_limit')
    def validate_risk_limit(cls, v):
        if not 0 < v <= 100:
            raise ValueError('Le risque doit être entre 0 et 100%')
        return v


class Settings(BaseSettings):
    """Configuration principale de FinAgent."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="FINAGENT_"
    )
    
    # Configuration générale
    app_name: str = Field(default="FinAgent")
    app_version: str = Field(default="0.1.0")
    environment: str = Field(default="development")
    debug: bool = Field(default=False)
    
    # Répertoires
    data_dir: str = Field(default="./data")
    config_file: str = Field(default="config.yaml")
    
    # Sous-configurations
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    api: APISettings = Field(default_factory=APISettings)
    cache: CacheSettings = Field(default_factory=CacheSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    trading: TradingSettings = Field(default_factory=TradingSettings)
    
    def __init__(self, config_file: Optional[str] = None, **kwargs):
        """
        Initialise les settings en combinant les sources de configuration.
        
        Args:
            config_file: Chemin vers le fichier de configuration YAML
            **kwargs: Paramètres de configuration supplémentaires
        """
        # Charger la configuration depuis le fichier YAML si fourni
        yaml_config = {}
        if config_file and Path(config_file).exists():
            yaml_config = self._load_yaml_config(config_file)
        elif Path("config.yaml").exists():
            yaml_config = self._load_yaml_config("config.yaml")
        
        # Combiner avec les kwargs fournis
        combined_config = {**yaml_config, **kwargs}
        
        super().__init__(**combined_config)
        
        # Créer les répertoires nécessaires
        self._create_directories()
    
    def _load_yaml_config(self, config_file: str) -> Dict[str, Any]:
        """
        Charge la configuration depuis un fichier YAML.
        
        Args:
            config_file: Chemin vers le fichier YAML
            
        Returns:
            Dict contenant la configuration
            
        Raises:
            ConfigurationError: Si le fichier ne peut pas être lu
        """
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                
            # Aplatir la configuration pour Pydantic
            flat_config = {}
            if 'database' in config:
                flat_config.update({f"database__{k}": v for k, v in config['database'].items()})
            if 'apis' in config:
                if 'openrouter' in config['apis']:
                    flat_config.update({f"api__{k}": v for k, v in config['apis']['openrouter'].items()})
                if 'general' in config['apis']:
                    flat_config.update({f"api__{k}": v for k, v in config['apis']['general'].items()})
            if 'cache' in config and 'memory' in config['cache']:
                flat_config.update({f"cache__{k}": v for k, v in config['cache']['memory'].items()})
            if 'logging' in config:
                flat_config.update({f"logging__{k}": v for k, v in config['logging'].items()})
            if 'trading' in config and 'defaults' in config['trading']:
                flat_config.update({f"trading__{k}": v for k, v in config['trading']['defaults'].items()})
            
            return flat_config
            
        except Exception as e:
            raise ConfigurationError(f"Erreur lors du chargement de {config_file}: {e}")
    
    def _create_directories(self):
        """Crée les répertoires nécessaires."""
        directories = [
            self.data_dir,
            Path(self.logging.file_path).parent,
            self.cache.file_directory,
            f"{self.data_dir}/backups",
            f"{self.data_dir}/exports",
            f"{self.data_dir}/strategies"
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    @property
    def is_development(self) -> bool:
        """Retourne True si on est en mode développement."""
        return self.environment.lower() == "development"
    
    @property
    def is_production(self) -> bool:
        """Retourne True si on est en mode production."""
        return self.environment.lower() == "production"


# Instance globale des settings (singleton pattern)
_settings: Optional[Settings] = None


def get_settings(config_file: Optional[str] = None) -> Settings:
    """
    Retourne l'instance globale des settings.
    
    Args:
        config_file: Chemin vers le fichier de configuration (première fois seulement)
        
    Returns:
        Instance des settings
    """
    global _settings
    if _settings is None:
        _settings = Settings(config_file=config_file)
    return _settings


def reload_settings(config_file: Optional[str] = None) -> Settings:
    """
    Recharge les settings (utile pour les tests ou changements de config).
    
    Args:
        config_file: Chemin vers le fichier de configuration
        
    Returns:
        Nouvelle instance des settings
    """
    global _settings
    _settings = Settings(config_file=config_file)
    return _settings