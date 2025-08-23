# Documentation des Tests FinAgent

Cette documentation décrit l'organisation et l'utilisation de la suite de tests complète pour FinAgent.

## 📁 Structure des Tests

```
tests/
├── conftest.py              # Configuration globale pytest et fixtures partagées
├── pytest.ini              # Configuration pytest
├── requirements-test.txt    # Dépendances spécifiques aux tests
├── test_config.yaml        # Configuration pour l'environnement de test
├── README.md               # Ce fichier
├── utils/                  # Utilitaires et helpers de test
│   ├── __init__.py         # Exports des utilitaires
│   ├── test_fixtures.py    # Factories pour objets de test
│   ├── mock_providers.py   # Mocks pour APIs externes
│   ├── test_data_generator.py # Générateurs de données réalistes
│   └── test_helpers.py     # Fonctions utilitaires
├── unit/                   # Tests unitaires
│   ├── __init__.py         # Index des tests unitaires
│   ├── test_data_models.py # Tests modèles de données IA
│   ├── test_strategy_models.py # Tests modèles de stratégies
│   ├── test_decision_models.py # Tests modèles de décision/portfolio
│   ├── test_openbb_provider.py # Tests provider OpenBB
│   ├── test_claude_provider.py # Tests provider Claude
│   ├── test_strategy_engine.py # Tests moteur de stratégies
│   ├── test_portfolio_manager.py # Tests gestionnaire portfolio
│   └── test_cli.py         # Tests interface CLI
├── integration/            # Tests d'intégration (à créer)
├── performance/            # Tests de performance (à créer)
├── robustness/            # Tests de robustesse (à créer)
└── security/              # Tests de sécurité (à créer)
```

## 🧪 Types de Tests Implémentés

### Tests Unitaires (✅ Complétés)

#### 1. **Modèles de Données** (`test_data_models.py`)
- **AIRequest/AIResponse** : Validation des requêtes et réponses IA
- **TokenUsage** : Suivi de consommation de tokens
- **RateLimitInfo** : Gestion des limites de taux
- **MessageRole** : Validation des rôles de messages
- **Énumérations IA** : Validation de tous les types et statuts

**Coverage ciblé** : ~95% des modèles Pydantic IA

#### 2. **Modèles de Stratégies** (`test_strategy_models.py`)
- **Énumérations** : StrategyType, RiskTolerance, TimeHorizon, etc.
- **Conditions et Règles** : Validation logique métier
- **Configuration Stratégies** : Structure YAML complète
- **Validation** : Cohérence et contraintes métier
- **Optimisation** : Tests de performance de stratégies

**Coverage ciblé** : ~90% du système de stratégies

#### 3. **Modèles de Décision** (`test_decision_models.py`)
- **InvestmentDecision** : Validation des décisions d'investissement
- **PortfolioAction** : Actions sur le portefeuille
- **AssetAllocation** : Gestion d'allocation d'actifs
- **Transaction/Position** : Modèles de transactions et positions
- **Métriques** : Calculs de performance et risque

**Coverage ciblé** : ~95% des modèles financiers

#### 4. **Provider OpenBB** (`test_openbb_provider.py`)
- **Configuration** : Validation setup API
- **Données de marché** : Prix, volumes, indicateurs
- **Données fondamentales** : États financiers, ratios
- **Indicateurs techniques** : RSI, MACD, moyennes mobiles
- **Gestion d'erreurs** : Rate limiting, timeouts, erreurs API
- **Cache** : Système de mise en cache

**Coverage ciblé** : ~85% du provider (sans appels API réels)

#### 5. **Provider Claude** (`test_claude_provider.py`)
- **Configuration** : Setup OpenRouter/Claude
- **Génération IA** : Complétions et conversations
- **Gestion tokens** : Comptage et limites
- **Rate limiting** : Gestion des quotas
- **Streaming** : Réponses en temps réel
- **Spécialisations** : Analyse financière, évaluation risques

**Coverage ciblé** : ~85% du provider IA

#### 6. **Moteur de Stratégies** (`test_strategy_engine.py`)
- **Chargement YAML** : Validation et parsing
- **Évaluation règles** : Logique conditionnelle
- **Génération signaux** : Agrégation et pondération
- **Backtesting** : Tests historiques
- **Optimisation** : Amélioration paramètres

**Coverage ciblé** : ~90% du moteur de stratégies

#### 7. **Gestionnaire Portfolio** (`test_portfolio_manager.py`)
- **Gestion positions** : Ajout/suppression/modification
- **Allocation actifs** : Optimisation et rééquilibrage
- **Gestion risques** : VaR, limites, corrélations
- **Performance** : Métriques et attribution
- **Optimisation** : Mean-variance, risk parity, Black-Litterman

**Coverage ciblé** : ~90% de la gestion de portfolio

#### 8. **Interface CLI** (`test_cli.py`)
- **Commandes principales** : analyze, portfolio, strategy, market
- **Validation arguments** : Gestion erreurs utilisateur
- **Formats sortie** : JSON, table, CSV
- **Mode interactif** : Session conversationnelle
- **Configuration** : Gestion fichiers config

**Coverage ciblé** : ~80% de l'interface CLI

## 🚀 Utilisation des Tests

### Exécution Complète
```bash
# Tous les tests
pytest tests/

# Tests unitaires seulement
pytest tests/unit/

# Avec couverture détaillée
pytest tests/unit/ --cov=finagent --cov-report=html --cov-report=term-missing
```

### Exécution Sélective
```bash
# Un module spécifique
pytest tests/unit/test_strategy_engine.py

# Une classe de tests
pytest tests/unit/test_data_models.py::TestAIRequestModel

# Un test spécifique
pytest tests/unit/test_data_models.py::TestAIRequestModel::test_ai_request_creation

# Tests par marqueurs
pytest -m "not slow"  # Exclure tests lents
pytest -m "integration"  # Tests d'intégration seulement
```

### Modes de Debug
```bash
# Mode verbose
pytest tests/unit/ -v

# Arrêt au premier échec
pytest tests/unit/ -x

# Debug avec PDB
pytest tests/unit/ --pdb

# Profiling
pytest tests/unit/ --profile
```

## 🛠️ Fixtures et Utilitaires

### Factories de Données
```python
from tests.utils import (
    StockDataFactory,      # Génère données financières
    AIRequestFactory,      # Crée requêtes IA
    PortfolioFactory,      # Construit portefeuilles
    TransactionFactory     # Simule transactions
)

# Utilisation
stock_data = StockDataFactory.create_realistic_data("AAPL", days=30)
ai_request = AIRequestFactory.create_financial_analysis("GOOGL")
```

### Mocks de Providers
```python
from tests.utils import MockOpenBBProvider, MockClaudeProvider

# Provider OpenBB simulé
mock_openbb = MockOpenBBProvider(config)
price_data = await mock_openbb.get_current_price("AAPL")

# Provider Claude simulé  
mock_claude = MockClaudeProvider(config)
response = await mock_claude.generate_completion("Analyze this stock")
```

### Helpers de Test
```python
from tests.utils import (
    assert_valid_uuid,     # Validation UUID
    assert_decimal_equals, # Comparaison décimaux
    create_test_portfolio, # Portfolio type
    benchmark_performance  # Mesure performance
)
```

## 📊 Métriques de Qualité

### Objectifs de Couverture
- **Global** : ≥ 85%
- **Modèles critiques** : ≥ 95% 
- **Logique métier** : ≥ 90%
- **Providers** : ≥ 85%
- **CLI/Interface** : ≥ 80%

### Indicateurs de Performance
- **Temps d'exécution** : < 30 secondes (tests unitaires)
- **Fiabilité** : < 1% de tests flaky
- **Maintenabilité** : Couverture mutation ≥ 70%

### Métriques Actuelles
```bash
# Générer rapport complet
pytest tests/unit/ \
    --cov=finagent \
    --cov-report=html \
    --cov-report=term-missing \
    --cov-fail-under=85 \
    --durations=10
```

## 🔧 Configuration et Environnement

### Variables d'Environnement
```bash
# Mode test
export FINAGENT_ENV=test

# APIs mock (éviter vrais appels)
export FINAGENT_MOCK_APIS=true

# Niveau de log pour debug
export FINAGENT_LOG_LEVEL=DEBUG
```

### Configuration Test
Le fichier [`test_config.yaml`](./test_config.yaml) contient :
- URLs de test pour APIs
- Clés API fictives
- Timeouts réduits
- Cache désactivé
- Mode verbose

### Base de Données Test
- **SQLite** en mémoire pour rapidité
- **Données synthétiques** générées automatiquement
- **Isolation** complète entre tests
- **Cleanup** automatique après chaque test

## 🐛 Debug et Troubleshooting

### Tests Qui Échouent
```bash
# Re-exécuter les échecs seulement
pytest --lf tests/unit/

# Mode debug détaillé
pytest tests/unit/test_failing.py -vvv --tb=long

# Avec PDB interactif
pytest tests/unit/test_failing.py --pdb
```

### Performance Lente
```bash
# Identifier tests lents
pytest tests/unit/ --durations=0

# Profiler un test spécifique
pytest tests/unit/test_slow.py --profile-svg
```

### Problèmes de Mock
- Vérifier que `MockOpenBBProvider` et `MockClaudeProvider` sont utilisés
- S'assurer que les patches sont appliqués au bon niveau
- Vérifier l'isolation entre tests

### Erreurs de Configuration
- Valider [`pytest.ini`](./pytest.ini)
- Vérifier [`conftest.py`](./conftest.py)
- Contrôler les fixtures partagées

## 📋 Checklist Tests

### Avant Commit
- [ ] Tous les tests passent : `pytest tests/unit/`
- [ ] Couverture ≥ 85% : `--cov-fail-under=85`
- [ ] Pas de warnings : `-W error`
- [ ] Linting : `flake8 tests/`
- [ ] Type checking : `mypy tests/`

### Avant Release
- [ ] Tests complets : `pytest tests/`
- [ ] Tests de régression
- [ ] Validation sur données réelles (env staging)
- [ ] Documentation à jour
- [ ] Benchmarks de performance

## 🔮 Prochaines Étapes

### Tests d'Intégration (À venir)
- Workflows complets bout-en-bout
- Intégration réelle avec APIs OpenBB/Claude
- Tests CLI avec vraies données
- Validation persistence de données

### Tests de Performance (À venir)
- Benchmarks de latence
- Tests de charge (100+ symboles simultanés)
- Stress tests (stratégies complexes)
- Profiling mémoire

### Tests de Robustesse (À venir)
- Gestion pannes réseau
- Récupération après erreurs
- Validation données corrompues
- Tests de chaos

### Tests de Sécurité (À venir)
- Validation des clés API
- Protection données sensibles
- Tests d'injection
- Audit de sécurité

---

## 📞 Support

Pour questions ou problèmes avec les tests :

1. **Documentation** : Lire ce README et les docstrings
2. **Logs** : Activer le mode verbose (`-v`)
3. **Issues** : Créer un ticket avec détails reproduction
4. **Debug** : Utiliser `--pdb` pour investigation interactive

**Objectif** : Suite de tests robuste, maintenable et complète pour assurer la qualité de FinAgent en production.