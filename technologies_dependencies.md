# Technologies et Dépendances Python - Agent IA Financier

## Version Python Recommandée
- **Python 3.11+** : Performance optimisée et nouvelles fonctionnalités

## Dépendances Principales

### 1. Interface CLI
```toml
# CLI Framework
click = "^8.1.7"              # Framework CLI robuste et extensible
rich = "^13.7.0"              # Affichage riche dans le terminal
typer = "^0.9.0"              # Alternative moderne à Click (optionnel)
```

**Justification** :
- `click` : Standard de facto pour CLI Python
- `rich` : Tables, progress bars, couleurs pour UX améliorée
- `typer` : Plus moderne, basé sur type hints

### 2. Données Financières
```toml
# OpenBB Integration
openbb = "^4.1.0"             # SDK OpenBB pour données financières
pandas = "^2.1.4"             # Manipulation de données
numpy = "^1.26.2"             # Calculs numériques
yfinance = "^0.2.18"          # Yahoo Finance (backup)
```

**Justification** :
- `openbb` : Source principale de données financières
- `pandas` : Standard pour manipulation de données financières
- `numpy` : Performance pour calculs mathématiques
- `yfinance` : Source de données alternative

### 3. Intelligence Artificielle
```toml
# IA et LLM
openai = "^1.12.0"            # Client OpenAI (compatible OpenRouter)
anthropic = "^0.18.0"         # Client Anthropic direct (backup)
httpx = "^0.27.0"             # Client HTTP async moderne
tenacity = "^8.2.3"           # Retry logic pour APIs
```

**Justification** :
- `openai` : Compatible avec OpenRouter pour Claude
- `anthropic` : Client direct en backup
- `httpx` : Performance et support async
- `tenacity` : Gestion robuste des retries

### 4. Persistance et Base de Données
```toml
# Base de données
sqlalchemy = "^2.0.25"        # ORM moderne et performant
alembic = "^1.13.1"           # Migrations de base de données
sqlite3 = "built-in"          # Base de données locale simple
redis = "^5.0.1"              # Cache et sessions (optionnel)
```

**Justification** :
- `sqlalchemy` : ORM Python de référence
- `alembic` : Gestion des migrations
- `sqlite3` : Simple pour traders particuliers
- `redis` : Cache haute performance (si nécessaire)

### 5. Configuration et Sérialisation
```toml
# Configuration
pydantic = "^2.5.3"           # Validation de données et settings
pydantic-settings = "^2.1.0"  # Gestion des settings
pyyaml = "^6.0.1"             # Fichiers de configuration YAML
tomli = "^2.0.1"              # Lecture fichiers TOML
```

**Justification** :
- `pydantic` : Validation robuste et type-safe
- `pyyaml` : Configuration utilisateur lisible
- `tomli` : Configuration technique (pyproject.toml)

### 6. Logging et Monitoring
```toml
# Logging et monitoring
structlog = "^23.2.0"         # Logging structuré
loguru = "^0.7.2"             # Alternative simple à structlog
python-json-logger = "^2.0.7" # JSON logging format
```

**Justification** :
- `structlog` : Logging structuré pour debugging
- `loguru` : Simple et puissant
- JSON logging pour analyse future

### 7. Sécurité et Chiffrement
```toml
# Sécurité
cryptography = "^42.0.2"      # Chiffrement des clés API
keyring = "^24.3.0"           # Stockage sécurisé des secrets
python-dotenv = "^1.0.0"      # Variables d'environnement
```

**Justification** :
- `cryptography` : Standard pour chiffrement
- `keyring` : Intégration OS pour secrets
- `python-dotenv` : Gestion simple des env vars

### 8. Tests et Qualité de Code
```toml
# Tests et développement
pytest = "^7.4.4"             # Framework de tests
pytest-asyncio = "^0.23.3"    # Tests async
pytest-mock = "^3.12.0"       # Mocking facilité
coverage = "^7.4.0"           # Couverture de code
black = "^23.12.1"            # Formatage de code
ruff = "^0.1.9"               # Linting ultra-rapide
mypy = "^1.8.0"               # Type checking
```

**Justification** :
- `pytest` : Standard pour tests Python
- `black` : Formatage automatique
- `ruff` : Linter moderne et rapide
- `mypy` : Sécurité des types

### 9. Utilitaires et Performance
```toml
# Utilitaires
python-dateutil = "^2.8.2"    # Manipulation de dates
arrow = "^1.3.0"              # Dates plus conviviales
schedule = "^1.2.1"           # Planification de tâches
psutil = "^5.9.6"             # Monitoring système
cachetools = "^5.3.2"         # Cache en mémoire
```

**Justification** :
- `arrow` : Manipulation de dates intuitive
- `schedule` : Tâches périodiques simples
- `psutil` : Monitoring des ressources
- `cachetools` : Cache LRU et TTL

## Structure du fichier pyproject.toml

```toml
[tool.poetry]
name = "finagent"
version = "0.1.0"
description = "Agent IA pour analyse d'actions financières"
authors = ["Your Name <your.email@example.com>"]
readme = "README.md"
packages = [{include = "finagent"}]

[tool.poetry.dependencies]
python = "^3.11"

# CLI
click = "^8.1.7"
rich = "^13.7.0"

# Data & Finance
openbb = "^4.1.0"
pandas = "^2.1.4"
numpy = "^1.26.2"
yfinance = "^0.2.18"

# AI & HTTP
openai = "^1.12.0"
httpx = "^0.27.0"
tenacity = "^8.2.3"

# Database & Persistence
sqlalchemy = "^2.0.25"
alembic = "^1.13.1"

# Configuration
pydantic = "^2.5.3"
pydantic-settings = "^2.1.0"
pyyaml = "^6.0.1"

# Security
cryptography = "^42.0.2"
keyring = "^24.3.0"
python-dotenv = "^1.0.0"

# Logging
structlog = "^23.2.0"

# Utilities
arrow = "^1.3.0"
schedule = "^1.2.1"
cachetools = "^5.3.2"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.4"
pytest-asyncio = "^0.23.3"
pytest-mock = "^3.12.0"
coverage = "^7.4.0"
black = "^23.12.1"
ruff = "^0.1.9"
mypy = "^1.8.0"

[tool.poetry.scripts]
finagent = "finagent.cli.main:app"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

[tool.black]
line-length = 88
target-version = ['py311']

[tool.ruff]
line-length = 88
target-version = "py311"
select = ["E", "F", "I", "N", "B", "S"]

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --tb=short"

[tool.coverage.run]
source = ["finagent"]
omit = ["*/tests/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError"
]
```

## Architecture de Dépendances

### Couches et Dépendances
```
CLI Layer:           click, rich, typer
Business Layer:      pandas, numpy, pydantic
AI Layer:            openai, httpx, tenacity
Data Layer:          openbb, yfinance, cachetools
Persistence Layer:   sqlalchemy, alembic
Security Layer:      cryptography, keyring
Core Services:       structlog, arrow, schedule
```

### Diagramme de Dépendances

```
┌─────────────────┐
│   CLI (click)   │
└─────────┬───────┘
          │
┌─────────▼───────┐    ┌─────────────────┐
│  Business Logic │────│ AI Integration │
│   (pydantic)    │    │   (openai)      │
└─────────┬───────┘    └─────────────────┘
          │
┌─────────▼───────┐    ┌─────────────────┐
│   Data Layer    │────│  Cache Tools    │
│   (openbb)      │    │ (cachetools)    │
└─────────┬───────┘    └─────────────────┘
          │
┌─────────▼───────┐    ┌─────────────────┐
│  Persistence    │────│   Security      │
│ (sqlalchemy)    │    │ (cryptography)  │
└─────────────────┘    └─────────────────┘
```

## Gestion des Versions

### Stratégie de Versioning
- **Semantic Versioning** : MAJOR.MINOR.PATCH
- **Dépendances** : Utilisation de contraintes flexibles (`^`)
- **Lock File** : `poetry.lock` pour reproductibilité

### Environnements
```bash
# Production
poetry install --only=main

# Développement  
poetry install

# Tests seulement
poetry install --only=dev
```

## Optimisations de Performance

### 1. Import Lazy
```python
# Utilisation de TYPE_CHECKING pour imports
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from openbb import OpenBBFigure
```

### 2. Cache Dependencies
```python
# Cache configuré avec cachetools
from cachetools import TTLCache, cached

@cached(cache=TTLCache(maxsize=128, ttl=300))
def get_market_data(symbol: str):
    pass
```

### 3. Async Where Beneficial
```python
# httpx pour appels API async
import httpx

async def call_claude_api(prompt: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(...)
```

## Considérations de Déploiement

### Docker (optionnel)
```dockerfile
FROM python:3.11-slim

# Install poetry
RUN pip install poetry

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry install --only=main

# Copy application
COPY finagent/ ./finagent/

# Set entrypoint
ENTRYPOINT ["poetry", "run", "finagent"]
```

### Installation Locale
```bash
# Clone repository
git clone <repo-url>
cd finagent

# Install with poetry
poetry install

# Or with pip
pip install -e .
```

## Alternatives et Justifications

### CLI Framework
- **Click** ✅ : Mature, stable, large ecosystem
- **Typer** ⚠️ : Plus moderne mais moins mature
- **argparse** ❌ : Trop basique pour interface complexe

### HTTP Client
- **httpx** ✅ : Moderne, async, compatible requests
- **requests** ⚠️ : Simple mais pas async
- **aiohttp** ❌ : Plus complexe, orienté serveur

### Validation de Données
- **Pydantic** ✅ : Standard, performance, type hints
- **marshmallow** ⚠️ : Mature mais plus verbeux
- **cerberus** ❌ : Moins de fonctionnalités

### Base de Données
- **SQLite** ✅ : Simple, pas de serveur, parfait pour usage local
- **PostgreSQL** ⚠️ : Plus puissant mais complexité d'installation
- **MongoDB** ❌ : Overkill pour données structurées financières