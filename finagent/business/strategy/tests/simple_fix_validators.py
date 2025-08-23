"""
Script simple pour corriger les validateurs Pydantic.
"""

import re
from pathlib import Path

def fix_duplicate_modes(content):
    """Corrige les modes dupliqués dans field_validator."""
    # Remplacer mode='before', mode='after' par juste mode='before'
    content = re.sub(
        r"@field_validator\(([^)]+),\s*mode='before',\s*mode='after'\)",
        r"@field_validator(\1, mode='before')",
        content
    )
    
    # Remplacer mode='after', mode='before' par juste mode='before'  
    content = re.sub(
        r"@field_validator\(([^)]+),\s*mode='after',\s*mode='before'\)",
        r"@field_validator(\1, mode='before')",
        content
    )
    
    return content

def simple_fix_file(file_path):
    """Correction simple d'un fichier."""
    print(f"Correction simple de {file_path}...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Correction des modes dupliqués
    content = fix_duplicate_modes(content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ {file_path} corrigé")

def main():
    """Corrige les erreurs de syntaxe."""
    models_dir = Path(__file__).parent.parent / "models"
    
    model_files = [
        models_dir / "strategy_models.py",
        models_dir / "rule_models.py", 
        models_dir / "condition_models.py"
    ]
    
    for file_path in model_files:
        if file_path.exists():
            simple_fix_file(file_path)
        else:
            print(f"⚠️  Fichier non trouvé: {file_path}")
    
    print("\n🎉 Corrections de syntaxe terminées !")

if __name__ == "__main__":
    main()