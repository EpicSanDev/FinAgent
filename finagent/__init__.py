"""
FinAgent - Agent IA pour analyse d'actions financières

Un agent intelligent utilisant Claude AI et OpenBB pour fournir des analyses
financières automatisées et des recommandations d'investissement.

Author: Bastien Javaux
Version: 0.1.0
License: MIT
"""

__version__ = "0.1.0"
__author__ = "Bastien Javaux"
__email__ = "bastien.javaux@example.com"
__license__ = "MIT"
__description__ = "Agent IA pour analyse d'actions financières"

# Imports principaux pour faciliter l'utilisation du package
from finagent.core.errors.exceptions import FinAgentException

# Métadonnées du package
__all__ = [
    "__version__",
    "__author__",
    "__email__",
    "__license__",
    "__description__",
    "FinAgentException",
]

# Information de compatibilité
PYTHON_VERSION_REQUIRED = (3, 11)

# Configuration par défaut
DEFAULT_CONFIG_PATH = "config.yaml"
DEFAULT_DATA_DIR = "./data"
DEFAULT_LOG_LEVEL = "INFO"

# Messages d'information
WELCOME_MESSAGE = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║  ███████╗██╗███╗   ██╗ █████╗  ██████╗ ███████╗███╗   ██╗████████╗           ║
║  ██╔════╝██║████╗  ██║██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝           ║
║  █████╗  ██║██╔██╗ ██║███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║              ║
║  ██╔══╝  ██║██║╚██╗██║██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║              ║
║  ██║     ██║██║ ╚████║██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║              ║
║  ╚═╝     ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝              ║
║                                                                              ║
║  Agent IA pour analyse d'actions financières                                 ║
║  Version {__version__} - Propulsé par Claude AI et OpenBB                           ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

def get_version() -> str:
    """Retourne la version actuelle de FinAgent."""
    return __version__

def check_python_version() -> bool:
    """Vérifie que la version de Python est compatible."""
    import sys
    return sys.version_info >= PYTHON_VERSION_REQUIRED

# Vérification de la compatibilité Python au moment de l'import
if not check_python_version():
    import sys
    raise RuntimeError(
        f"FinAgent nécessite Python {PYTHON_VERSION_REQUIRED[0]}.{PYTHON_VERSION_REQUIRED[1]}+ "
        f"mais vous utilisez Python {sys.version_info.major}.{sys.version_info.minor}"
    )