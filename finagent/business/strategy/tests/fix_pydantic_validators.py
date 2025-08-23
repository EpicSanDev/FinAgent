"""
Script pour corriger les validateurs Pydantic dans tous les fichiers de modèles.
"""

import os
import re
from pathlib import Path

def fix_field_validators(content):
    """Corrige les field_validator avec mode='before' au lieu de pre=True."""
    
    # Remplacer @field_validator('field', pre=True) par @field_validator('field', mode='before')
    content = re.sub(
        r"@field_validator\(([^)]+),\s*pre=True\)",
        r"@field_validator(\1, mode='before')",
        content
    )
    
    # Remplacer @field_validator('field') par @field_validator('field', mode='after') pour cohérence
    # Mais seulement si pas déjà de mode spécifié
    content = re.sub(
        r"@field_validator\(([^)]+)\)(?!\s*,\s*mode=)",
        r"@field_validator(\1, mode='after')",
        content
    )
    
    return content

def fix_model_validators(content):
    """Corrige les model_validator pour utiliser la bonne syntaxe."""
    
    # Les model_validator(mode='before') sont corrects
    # Mais s'assurer qu'ils utilisent cls au lieu de values dans les méthodes
    
    return content

def fix_validator_methods(content):
    """Corrige la signature des méthodes de validation."""
    
    # Pour field_validator avec mode='after', remplacer (cls, v, values) par (cls, v, info)
    # Pour field_validator avec mode='before', garder (cls, v)
    # Pour model_validator avec mode='before', utiliser (cls, values) ou (cls, data)
    
    lines = content.split('\n')
    new_lines = []
    in_validator = False
    validator_mode = None
    
    for i, line in enumerate(lines):
        if '@field_validator' in line:
            in_validator = True
            if "mode='before'" in line:
                validator_mode = 'before'
            else:
                validator_mode = 'after'
        elif '@model_validator' in line:
            in_validator = True
            validator_mode = 'model'
        elif in_validator and line.strip().startswith('def '):
            # Corriger la signature de la méthode
            if validator_mode == 'before':
                # Pour field_validator mode='before': def method(cls, v)
                line = re.sub(
                    r'def (\w+)\(cls,\s*v,\s*values\)',
                    r'def \1(cls, v)',
                    line
                )
            elif validator_mode == 'after':
                # Pour field_validator mode='after': def method(cls, v, info)
                line = re.sub(
                    r'def (\w+)\(cls,\s*v,\s*values\)',
                    r'def \1(cls, v, info)',
                    line
                )
                # Aussi corriger l'accès aux autres champs
                # Remplacer values.get('field') par info.data.get('field') dans les lignes suivantes
            elif validator_mode == 'model':
                # Pour model_validator: def method(cls, values) ou def method(cls, data)
                line = re.sub(
                    r'def (\w+)\(cls,\s*values\)',
                    r'def \1(cls, data)',
                    line
                )
            in_validator = False
            validator_mode = None
        
        new_lines.append(line)
    
    return '\n'.join(new_lines)

def fix_values_access(content):
    """Corrige l'accès aux valeurs dans les validateurs."""
    
    # Dans les field_validator mode='after', remplacer values.get() par info.data.get()
    # Dans les model_validator, values reste values ou devient data
    
    lines = content.split('\n')
    new_lines = []
    in_field_validator_after = False
    in_model_validator = False
    
    for i, line in enumerate(lines):
        if '@field_validator' in line and "mode='after'" in line:
            in_field_validator_after = True
        elif '@field_validator' in line and "mode='before'" in line:
            in_field_validator_after = False
        elif '@model_validator' in line:
            in_model_validator = True
        elif line.strip().startswith('def ') and (in_field_validator_after or in_model_validator):
            in_field_validator_after = False
            in_model_validator = False
        elif in_field_validator_after:
            # Remplacer values.get() par info.data.get()
            line = line.replace("values.get(", "info.data.get(")
            line = line.replace("values[", "info.data[")
        elif in_model_validator:
            # Remplacer values par data si nécessaire
            line = line.replace("values.get(", "data.get(")
            line = line.replace("values[", "data[")
    
        new_lines.append(line)
    
    return '\n'.join(new_lines)

def fix_file(file_path):
    """Corrige un fichier de modèles."""
    print(f"Correction de {file_path}...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Appliquer les corrections
    content = fix_field_validators(content)
    content = fix_model_validators(content)
    content = fix_validator_methods(content)
    content = fix_values_access(content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ {file_path} corrigé")

def main():
    """Corrige tous les fichiers de modèles."""
    models_dir = Path(__file__).parent.parent / "models"
    
    model_files = [
        models_dir / "strategy_models.py",
        models_dir / "rule_models.py", 
        models_dir / "condition_models.py"
    ]
    
    for file_path in model_files:
        if file_path.exists():
            fix_file(file_path)
        else:
            print(f"⚠️  Fichier non trouvé: {file_path}")
    
    print("\n🎉 Toutes les corrections Pydantic terminées !")

if __name__ == "__main__":
    main()