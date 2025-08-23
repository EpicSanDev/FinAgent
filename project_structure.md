# Structure de Fichiers et Organisation - Agent IA Financier

## Vue d'Ensemble

Cette structure reflète l'architecture modulaire conçue, suivant les principes de séparation des responsabilités et les bonnes pratiques Python pour la maintenabilité et l'extensibilité.

## 1. Structure Générale du Projet

```
finagent/
├── pyproject.toml                 # Configuration Poetry et métadonnées
├── README.md                      # Documentation principale
├── LICENSE                        # Licence du projet
├── .gitignore                     # Fichiers à ignorer par Git
├── .env.example                   # Template de variables d'environnement
├── Dockerfile                     # Container Docker (optionnel)
├── docker-compose.yml             # Orchestration multi-services (optionnel)
│
├── finagent/                      # Package principal
│   ├── __init__.py
│   ├── main.py                    # Point d'entrée principal
│   ├── config/                    # Configuration
│   ├── cli/                       # Interface ligne de commande
│   ├── business/                  # Logique métier
│   ├── ai/                        # Services IA
│   ├── data/                      # Accès aux données
│   ├── persistence/               # Persistance et stockage
│   ├── core/                      # Services transversaux
│   └── utils/                     # Utilitaires communs
│
├── tests/                         # Tests
│   ├── unit/                      # Tests unitaires
│   ├── integration/               # Tests d'intégration
│   ├── fixtures/                  # Données de test
│   └── conftest.py                # Configuration pytest
│
├── docs/                          # Documentation
│   ├── api/                       # Documentation API
│   ├── architecture/              # Documentation architecture
│   ├── user-guide/                # Guide utilisateur
│   └── examples/                  # Exemples d'utilisation
│
├── scripts/                       # Scripts utilitaires
│   ├── setup/                     # Scripts d'installation
│   ├── migration/                 # Scripts de migration
│   └── maintenance/               # Scripts de maintenance
│
├── templates/                     # Templates de stratégies
│   ├── strategies/                # Templates de stratégies prédéfinies
│   └── configs/                   # Templates de configuration
│
└── data/                          # Données locales (non versionnées)
    ├── cache/                     # Cache local
    ├── logs/                      # Fichiers de log
    ├── backups/                   # Sauvegardes
    └── exports/                   # Exports de données
```

## 2. Structure Détaillée du Package Principal

### A. Configuration (`finagent/config/`)
```
finagent/config/
├── __init__.py
├── settings.py                    # Configuration principale
├── database.py                    # Configuration base de données
├── security.py                    # Configuration sécurité
├── logging.py                     # Configuration logging
├── defaults/                      # Configurations par défaut
│   ├── __init__.py
│   ├── development.yaml
│   ├── production.yaml
│   └── testing.yaml
└── schemas/                       # Schémas de validation
    ├── __init__.py
    ├── strategy_schema.yaml
    ├── portfolio_schema.yaml
    └── user_schema.yaml
```

### B. Interface CLI (`finagent/cli/`)
```
finagent/cli/
├── __init__.py
├── main.py                        # Point d'entrée CLI principal
├── commands/                      # Commandes CLI
│   ├── __init__.py
│   ├── strategy.py                # Commandes stratégies
│   ├── portfolio.py               # Commandes portefeuille
│   ├── analysis.py                # Commandes analyse
│   ├── config.py                  # Commandes configuration
│   └── admin.py                   # Commandes administratives
├── formatters/                    # Formatage des sorties
│   ├── __init__.py
│   ├── table_formatter.py
│   ├── json_formatter.py
│   └── chart_formatter.py
└── validators/                    # Validation des entrées CLI
    ├── __init__.py
    ├── strategy_validator.py
    └── input_validator.py
```

### C. Logique Métier (`finagent/business/`)
```
finagent/business/
├── __init__.py
├── strategy/                      # Gestion des stratégies
│   ├── __init__.py
│   ├── strategy_service.py
│   ├── strategy_engine.py
│   ├── strategy_factory.py
│   ├── base_strategy.py
│   ├── technical/                 # Stratégies techniques
│   │   ├── __init__.py
│   │   ├── momentum_strategy.py
│   │   ├── mean_reversion_strategy.py
│   │   └── breakout_strategy.py
│   ├── fundamental/               # Stratégies fondamentales
│   │   ├── __init__.py
│   │   ├── value_strategy.py
│   │   └── growth_strategy.py
│   └── hybrid/                    # Stratégies hybrides
│       ├── __init__.py
│       └── multi_factor_strategy.py
├── decision/                      # Moteur de décision
│   ├── __init__.py
│   ├── decision_service.py
│   ├── decision_engine.py
│   ├── signal_generator.py
│   └── risk_manager.py
├── portfolio/                     # Gestion portefeuille
│   ├── __init__.py
│   ├── portfolio_service.py
│   ├── portfolio_manager.py
│   ├── position.py
│   ├── performance_tracker.py
│   └── risk_calculator.py
└── backtesting/                   # Système de backtesting
    ├── __init__.py
    ├── backtest_engine.py
    ├── backtest_service.py
    └── performance_analyzer.py
```

### D. Services IA (`finagent/ai/`)
```
finagent/ai/
├── __init__.py
├── providers/                     # Fournisseurs IA
│   ├── __init__.py
│   ├── base_provider.py
│   ├── claude_provider.py
│   └── openai_provider.py
├── services/                      # Services IA
│   ├── __init__.py
│   ├── analysis_service.py
│   ├── sentiment_service.py
│   └── prediction_service.py
├── memory/                        # Système de mémoire IA
│   ├── __init__.py
│   ├── memory_service.py
│   ├── short_term_memory.py
│   ├── long_term_memory.py
│   └── pattern_memory.py
├── prompts/                       # Gestion des prompts
│   ├── __init__.py
│   ├── prompt_manager.py
│   ├── templates/
│   │   ├── analysis_prompts.yaml
│   │   ├── decision_prompts.yaml
│   │   └── explanation_prompts.yaml
│   └── context/
│       ├── __init__.py
│       ├── context_builder.py
│       └── market_context.py
└── models/                        # Modèles de données IA
    ├── __init__.py
    ├── analysis_models.py
    ├── prediction_models.py
    └── sentiment_models.py
```

### E. Accès aux Données (`finagent/data/`)
```
finagent/data/
├── __init__.py
├── providers/                     # Fournisseurs de données
│   ├── __init__.py
│   ├── base_provider.py
│   ├── openbb_provider.py
│   ├── yfinance_provider.py
│   └── alpha_vantage_provider.py
├── services/                      # Services de données
│   ├── __init__.py
│   ├── market_data_service.py
│   ├── fundamental_data_service.py
│   ├── technical_indicator_service.py
│   └── news_service.py
├── cache/                         # Système de cache
│   ├── __init__.py
│   ├── cache_manager.py
│   ├── memory_cache.py
│   ├── redis_cache.py
│   └── file_cache.py
├── models/                        # Modèles de données
│   ├── __init__.py
│   ├── market_data.py
│   ├── financial_data.py
│   ├── symbol.py
│   └── indicators.py
└── validators/                    # Validation des données
    ├── __init__.py
    ├── data_validator.py
    └── schema_validator.py
```

### F. Persistance (`finagent/persistence/`)
```
finagent/persistence/
├── __init__.py
├── database/                      # Base de données
│   ├── __init__.py
│   ├── connection.py
│   ├── models/                    # Modèles SQLAlchemy
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── user.py
│   │   ├── strategy.py
│   │   ├── portfolio.py
│   │   ├── transaction.py
│   │   └── ai_memory.py
│   └── migrations/                # Migrations Alembic
│       ├── env.py
│       ├── script.py.mako
│       └── versions/
├── repositories/                  # Pattern Repository
│   ├── __init__.py
│   ├── base_repository.py
│   ├── strategy_repository.py
│   ├── portfolio_repository.py
│   ├── user_repository.py
│   └── memory_repository.py
├── storage/                       # Stockage fichiers
│   ├── __init__.py
│   ├── file_storage.py
│   ├── config_storage.py
│   └── backup_storage.py
└── unit_of_work/                  # Pattern Unit of Work
    ├── __init__.py
    └── unit_of_work.py
```

### G. Services Transversaux (`finagent/core/`)
```
finagent/core/
├── __init__.py
├── errors/                        # Gestion d'erreurs
│   ├── __init__.py
│   ├── exceptions.py
│   ├── error_handler.py
│   └── error_codes.py
├── security/                      # Sécurité
│   ├── __init__.py
│   ├── security_manager.py
│   ├── encryption_service.py
│   ├── secret_manager.py
│   └── auth_service.py
├── logging/                       # Logging
│   ├── __init__.py
│   ├── logger.py
│   ├── formatters.py
│   └── handlers.py
├── events/                        # Système d'événements
│   ├── __init__.py
│   ├── event_bus.py
│   ├── event_handler.py
│   └── events.py
├── middleware/                    # Middleware
│   ├── __init__.py
│   ├── logging_middleware.py
│   ├── caching_middleware.py
│   └── security_middleware.py
├── patterns/                      # Patterns transversaux
│   ├── __init__.py
│   ├── circuit_breaker.py
│   ├── retry_handler.py
│   └── rate_limiter.py
└── dependency_injection/          # Injection de dépendances
    ├── __init__.py
    ├── container.py
    └── configuration.py
```

### H. Utilitaires (`finagent/utils/`)
```
finagent/utils/
├── __init__.py
├── date_utils.py                  # Utilitaires de date
├── math_utils.py                  # Utilitaires mathématiques
├── file_utils.py                  # Utilitaires de fichiers
├── string_utils.py                # Utilitaires de chaînes
├── validation_utils.py            # Utilitaires de validation
├── async_utils.py                 # Utilitaires async
└── testing_utils.py               # Utilitaires de test
```

## 3. Structure des Tests

```
tests/
├── conftest.py                    # Configuration pytest globale
├── fixtures/                      # Fixtures de test
│   ├── __init__.py
│   ├── market_data_fixtures.py
│   ├── strategy_fixtures.py
│   └── portfolio_fixtures.py
├── unit/                          # Tests unitaires
│   ├── __init__.py
│   ├── test_config/
│   ├── test_cli/
│   ├── test_business/
│   │   ├── test_strategy/
│   │   ├── test_decision/
│   │   └── test_portfolio/
│   ├── test_ai/
│   ├── test_data/
│   ├── test_persistence/
│   ├── test_core/
│   └── test_utils/
├── integration/                   # Tests d'intégration
│   ├── __init__.py
│   ├── test_api_integration.py
│   ├── test_database_integration.py
│   ├── test_strategy_execution.py
│   └── test_end_to_end.py
├── performance/                   # Tests de performance
│   ├── __init__.py
│   ├── test_strategy_performance.py
│   └── test_data_loading.py
└── security/                      # Tests de sécurité
    ├── __init__.py
    ├── test_encryption.py
    ├── test_authentication.py
    └── test_input_validation.py
```

## 4. Documentation

```
docs/
├── index.md                       # Page d'accueil documentation
├── installation.md               # Guide d'installation
├── quickstart.md                 # Guide de démarrage rapide
├── user-guide/                   # Guide utilisateur
│   ├── getting-started.md
│   ├── creating-strategies.md
│   ├── managing-portfolio.md
│   ├── running-analysis.md
│   └── configuration.md
├── api/                          # Documentation API
│   ├── cli-reference.md
│   ├── python-api.md
│   └── examples/
├── architecture/                 # Documentation architecture
│   ├── overview.md
│   ├── components.md
│   ├── security.md
│   └── deployment.md
├── development/                  # Guide développement
│   ├── setup.md
│   ├── contributing.md
│   ├── testing.md
│   └── release-process.md
└── troubleshooting/              # Dépannage
    ├── common-issues.md
    ├── error-codes.md
    └── faq.md
```

## 5. Scripts et Utilitaires

```
scripts/
├── setup/                        # Scripts d'installation
│   ├── install.sh                # Installation Linux/macOS
│   ├── install.ps1               # Installation Windows
│   ├── setup_database.py         # Configuration base de données
│   └── initialize_config.py      # Configuration initiale
├── migration/                    # Scripts de migration
│   ├── migrate_database.py
│   ├── migrate_config.py
│   └── data_migration/
├── maintenance/                  # Scripts de maintenance
│   ├── cleanup_cache.py
│   ├── backup_data.py
│   ├── optimize_database.py
│   └── health_check.py
├── development/                  # Scripts de développement
│   ├── run_tests.sh
│   ├── lint_code.sh
│   ├── generate_docs.py
│   └── create_release.py
└── deployment/                   # Scripts de déploiement
    ├── deploy.sh
    ├── docker_build.sh
    └── package_release.py
```

## 6. Templates et Exemples

```
templates/
├── strategies/                   # Templates de stratégies
│   ├── momentum_basic.yaml
│   ├── value_investing.yaml
│   ├── technical_analysis.yaml
│   └── custom_template.yaml
├── configs/                      # Templates de configuration
│   ├── development.yaml
│   ├── production.yaml
│   └── user_config_template.yaml
└── portfolios/                   # Templates de portefeuilles
    ├── conservative.yaml
    ├── aggressive.yaml
    └── balanced.yaml
```

## 7. Fichiers de Configuration Projet

### A. pyproject.toml
```toml
[tool.poetry]
name = "finagent"
version = "0.1.0"
description = "Agent IA pour analyse d'actions financières"
authors = ["Votre Nom <email@example.com>"]
readme = "README.md"
license = "MIT"
homepage = "https://github.com/username/finagent"
repository = "https://github.com/username/finagent"
documentation = "https://finagent.readthedocs.io"
keywords = ["finance", "ai", "trading", "analysis"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Financial and Insurance Industry",
    "Topic :: Office/Business :: Financial :: Investment",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.11",
]

[tool.poetry.dependencies]
python = "^3.11"
# [Dépendances comme défini précédemment]

[tool.poetry.group.dev.dependencies]
# [Dépendances de développement]

[tool.poetry.scripts]
finagent = "finagent.main:main"

[tool.poetry.plugins."finagent.plugins"]
# Support pour plugins futurs

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

# Configuration des outils
[tool.black]
line-length = 88
target-version = ['py311']
include = '\.pyi?$'
extend-exclude = '''
/(
  # Répertoires à exclure
  \.git
  | \.venv
  | build
  | dist
)/
'''

[tool.ruff]
line-length = 88
target-version = "py311"
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
    "I",  # isort
    "N",  # pep8-naming
    "B",  # flake8-bugbear
    "S",  # flake8-bandit
]
ignore = [
    "S101",  # Use of assert
    "S603",  # subprocess untrusted input
]

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true

[[tool.mypy.overrides]]
module = [
    "openbb.*",
    "yfinance.*",
    "redis.*",
]
ignore_missing_imports = true

[tool.pytest.ini_options]
minversion = "7.0"
addopts = "-ra -q --strict-markers --strict-config"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
markers = [
    "unit: marks tests as unit tests",
    "integration: marks tests as integration tests",
    "slow: marks tests as slow",
    "security: marks tests as security tests",
]
filterwarnings = [
    "error",
    "ignore::UserWarning",
    "ignore::DeprecationWarning",
]

[tool.coverage.run]
source = ["finagent"]
omit = [
    "*/tests/*",
    "*/test_*",
    "*/__pycache__/*",
    "*/migrations/*",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "if self.debug:",
    "if settings.DEBUG",
    "raise AssertionError",
    "raise NotImplementedError",
    "if 0:",
    "if __name__ == .__main__.:",
    "class .*\\bProtocol\\):",
    "@(abc\\.)?abstractmethod",
]
```

### B. .gitignore
```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
pip-wheel-metadata/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Project specific
/data/
/logs/
/cache/
/backups/
/exports/
*.log
*.sqlite
*.db

# Security
.env
.env.*
!.env.example
secrets/
keys/
certificates/

# Documentation builds
docs/_build/
site/

# Coverage
.coverage
.coverage.*
coverage.xml
*.cover
.hypothesis/
.pytest_cache/

# Jupyter
.ipynb_checkpoints
```

### C. .env.example
```bash
# Configuration exemple - Copier vers .env et modifier

# Base de données
DATABASE_URL=sqlite:///./finagent.db

# APIs
OPENBB_API_KEY=your_openbb_api_key_here
OPENROUTER_API_KEY=your_openrouter_api_key_here
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key_here

# Cache
REDIS_URL=redis://localhost:6379/0
CACHE_BACKEND=memory

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/finagent.log

# Sécurité
SECRET_KEY=your_secret_key_here
ENCRYPTION_KEY_FILE=./keys/encryption.key

# Performance
MAX_CONCURRENT_REQUESTS=10
REQUEST_TIMEOUT=30
```

## 8. Conventions de Nommage

### A. Fichiers et Modules
- **snake_case** pour tous les fichiers Python
- **kebab-case** pour les fichiers de configuration
- Préfixes descriptifs pour les types de fichiers :
  - `test_` pour les tests
  - `_base` pour les classes de base
  - `_interface` pour les interfaces
  - `_service` pour les services

### B. Classes et Fonctions
- **PascalCase** pour les classes
- **snake_case** pour les fonctions et méthodes
- **UPPER_CASE** pour les constantes
- Interfaces préfixées par `I` (ex: `IStrategyService`)

### C. Packages et Modules
- Noms courts et descriptifs
- Éviter les abréviations sauf si courantes
- Groupement logique par fonctionnalité
- Hiérarchie claire parent-enfant

Cette structure offre :
- **Modularité** : Séparation claire des responsabilités
- **Extensibilité** : Facile d'ajouter de nouveaux composants
- **Maintenabilité** : Code organisé et facile à naviguer
- **Testabilité** : Structure supportant tous types de tests
- **Standardisation** : Suit les conventions Python