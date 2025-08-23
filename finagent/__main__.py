#!/usr/bin/env python3
"""
FinAgent - Point d'entrée principal du package

Ce module permet d'exécuter FinAgent avec: python -m finagent
"""

import sys
from pathlib import Path

# Ajouter le répertoire parent au PYTHONPATH pour les imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    from finagent.main import main
    main()