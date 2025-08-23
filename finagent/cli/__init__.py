"""
Interface en ligne de commande pour FinAgent.
"""

from .main import cli
from .commands import *

__all__ = ["cli"]