"""
Commandes CLI pour FinAgent.
"""

from .ai_commands import ai_group
from .config_commands import config_group
from .analysis_commands import analysis_group

__all__ = [
    "ai_group",
    "config_group", 
    "analysis_group"
]