# 🤖 FinAgent - Agent IA Financier

**Agent intelligent pour l'analyse d'actions financières propulsé par Claude AI et OpenBB**

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

---

## 📋 Table des Matières

- [🎯 Vue d'Ensemble](#-vue-densemble)
- [✨ Caractéristiques](#-caractéristiques)
- [📦 Installation](#-installation)
- [⚙️ Configuration](#%EF%B8%8F-configuration)
- [🚀 Utilisation](#-utilisation)
- [📖 Documentation](#-documentation)
- [🛠️ Développement](#%EF%B8%8F-développement)
- [🤝 Contribution](#-contribution)
- [📄 Licence](#-licence)

---

## 🎯 Vue d'Ensemble

FinAgent est un agent d'intelligence artificielle conçu pour aider les traders particuliers à analyser les marchés financiers. Il combine la puissance de **Claude AI** pour l'analyse qualitative avec les données financières de qualité institutionnelle d'**OpenBB** pour fournir des recommandations d'investissement personnalisées.

### 🔍 Problème Résolu

- **Analyse complexe** : Traitement automatique de grandes quantités de données financières
- **Prise de décision** : Recommandations basées sur l'IA avec explications détaillées
- **Gain de temps** : Automation des analyses répétitives
- **Objectivité** : Réduction des biais émotionnels dans les décisions d'investissement

---

## ✨ Caractéristiques

### 🎯 **Analyse Intelligente**
- 🤖 Analyse qualitative avec Claude AI
- 📊 Données financières temps réel via OpenBB
- 📈 Indicateurs techniques avancés
- 💡 Recommandations expliquées

### 🔧 **Configurabilité**
- 📝 Stratégies personnalisables en YAML
- ⚙️ Paramètres de risque ajustables
- 🎛️ Configuration flexible par environnement
- 🔄 Templates de stratégies prêts à l'emploi

### 🛡️ **Sécurité & Robustesse**
- 🔐 Chiffrement des clés API
- 🔄 Retry automatique et circuit breaker
- 📝 Logging structuré complet
- 🧪 Tests automatisés

### 📊 **Interface CLI Moderne**
- 🌈 Interface colorée avec Rich
- 📋 Tableaux et graphiques intégrés
- ⚡ Commandes intuitives
- 📱 Sortie formatée (JSON, CSV, Tables)

---

## 📦 Installation

### Prérequis

- **Python 3.11+** (recommandé: 3.11 ou 3.12)
- **Poetry** (gestionnaire de dépendances) ou **pip**

### Option 1: Installation avec Poetry (Recommandée)

```bash
# Cloner le repository
git clone https://github.com/votre-username/finagent.git
cd finagent

# Installer les dépendances avec Poetry
poetry install

# Activer l'environnement virtuel
poetry shell

# Vérifier l'installation
finagent --version
```

### Option 2: Installation avec pip

```bash
# Cloner le repository
git clone https://github.com/votre-username/finagent.git
cd finagent

# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/macOS
# ou
venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -r requirements.txt

# Installer le package en mode développement
pip install -e .

# Vérifier l'installation
finagent --version
```

### Option 3: Installation depuis PyPI (Future)

```bash
# Installation directe (quand disponible)
pip install finagent

# Ou avec Poetry
poetry add finagent
```

---

## ⚙️ Configuration

### 1. Variables d'Environnement

Copiez le fichier d'exemple et configurez vos clés API :

```bash
cp .env.example .env
```

Éditez le fichier `.env` avec vos clés :

```bash
# APIs requises
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENBB_PAT=your_openbb_personal_access_token_here

# Configuration optionnelle
FINAGENT_ENV=development
LOG_LEVEL=INFO
DEFAULT_POSITION_SIZE=1000
```

### 2. Obtenir les Clés API

#### OpenRouter (pour Claude AI)
1. Créez un compte sur [OpenRouter](https://openrouter.ai/)
2. Générez une clé API dans votre dashboard
3. Ajoutez du crédit à votre compte

#### OpenBB Hub
1. Créez un compte gratuit sur [OpenBB Hub](https://my.openbb.co/)
2. Générez un Personal Access Token (PAT)
3. Le plan gratuit offre des quotas généreux

### 3. Configuration Avancée

Le fichier `config.yaml` permet une configuration fine :

```yaml
# Exemple de configuration personnalisée
trading:
  defaults:
    position_size: 5000
    risk_limit: 1.5
    
ai:
  claude:
    temperature: 0.2
    max_tokens: 3000
```

---

## 🚀 Utilisation

### Démarrage Rapide

```bash
# Vérifier l'installation et la configuration
finagent config show

# Analyser une action
finagent analyze stock --symbol AAPL --period 1y

# Lister les stratégies disponibles
finagent strategy list

# Créer une nouvelle stratégie
finagent strategy create --name ma_strategie --template momentum

# Voir le statut du portefeuille
finagent portfolio status
```

### Commandes Principales

#### 🔍 **Analyse**
```bash
# Analyse complète d'une action
finagent analyze stock -s AAPL -p 6m

# Analyse multiple
finagent analyze batch --symbols AAPL,MSFT,GOOGL

# Analyse avec stratégie spécifique
finagent analyze stock -s TSLA --strategy growth
```

#### 📊 **Stratégies**
```bash
# Créer une stratégie momentum
finagent strategy create --name momentum_tech --template momentum

# Valider une stratégie
finagent strategy validate --file strategies/ma_strategie.yaml

# Backtester une stratégie
finagent strategy backtest --name momentum_tech --period 2y
```

#### 💼 **Portefeuille**
```bash
# Statut actuel
finagent portfolio status

# Historique des performances
finagent portfolio history --period 1y

# Simulation d'achat
finagent portfolio simulate buy AAPL 100 --strategy conservative
```

#### ⚙️ **Configuration**
```bash
# Assistant de configuration
finagent config setup

# Afficher la configuration
finagent config show

# Tester les connexions API
finagent config test-apis
```

---

## 📖 Documentation

### Structure du Projet

```
finagent/
├── finagent/           # Code source principal
│   ├── cli/           # Interface ligne de commande
│   ├── business/      # Logique métier
│   ├── ai/            # Services IA (Claude)
│   ├── data/          # Accès aux données (OpenBB)
│   ├── persistence/   # Base de données
│   └── core/          # Services transversaux
├── tests/             # Tests automatisés
├── docs/              # Documentation détaillée
└── templates/         # Templates de stratégies
```

### Documentation Complète

- 📚 [Guide Utilisateur](docs/user-guide/)
- 🏗️ [Architecture](docs/architecture/)
- 🔌 [API Reference](docs/api/)
- 📝 [Exemples](docs/examples/)

---

## 🛠️ Développement

### Configuration de l'Environnement

```bash
# Cloner le projet
git clone https://github.com/votre-username/finagent.git
cd finagent

# Installer avec les dépendances de développement
poetry install

# Installer les hooks pre-commit
pre-commit install

# Lancer les tests
make test

# Lancer le linting
make lint

# Générer la documentation
make docs
```

### Commandes Make Disponibles

```bash
make help          # Affiche l'aide
make install       # Installation complète
make test          # Lance tous les tests
make test-unit     # Tests unitaires seulement
make test-cov      # Tests avec couverture
make lint          # Linting (black, ruff, mypy)
make format        # Formatage automatique
make clean         # Nettoyage des fichiers temporaires
make docs          # Génération de la documentation
make build         # Build du package
make release       # Préparation d'une release
```

### Tests

```bash
# Tests unitaires
pytest tests/unit/

# Tests d'intégration
pytest tests/integration/

# Tests avec couverture
pytest --cov=finagent --cov-report=html

# Tests de sécurité
pytest tests/security/
```

### Standards de Code

- **Formatage** : Black (88 caractères)
- **Linting** : Ruff
- **Type Checking** : MyPy
- **Tests** : Pytest
- **Documentation** : Docstrings Google Style

---

## 🤝 Contribution

Les contributions sont les bienvenues ! Voir [CONTRIBUTING.md](CONTRIBUTING.md) pour les détails.

### Processus de Contribution

1. 🍴 Fork le projet
2. 🌿 Créez une branche feature (`git checkout -b feature/amazing-feature`)
3. ✨ Committez vos changements (`git commit -m 'Add amazing feature'`)
4. 📤 Pushez vers la branche (`git push origin feature/amazing-feature`)
5. 🔄 Ouvrez une Pull Request

### Directives

- ✅ Ajoutez des tests pour les nouvelles fonctionnalités
- 📝 Mettez à jour la documentation
- 🎨 Suivez les standards de code
- 🔒 Respectez les principes de sécurité

---

## 📊 Roadmap

### Phase 1 : Fondations ✅
- [x] Architecture de base
- [x] Configuration système
- [x] Interface CLI basique
- [x] Structure de données

### Phase 2 : Intégrations (En cours)
- [ ] Client OpenBB complet
- [ ] Client Claude/OpenRouter
- [ ] Système de cache
- [ ] Gestion sécurisée des clés

### Phase 3 : Logique Métier
- [ ] Moteur de stratégies
- [ ] Portfolio manager
- [ ] Decision engine
- [ ] Système de mémoire IA

### Phase 4 : Finalisation
- [ ] Interface CLI avancée
- [ ] Documentation complète
- [ ] Tests complets
- [ ] Package distribution

---

## 🐛 Support

### Problèmes Courants

**Installation échoue**
```bash
# Vérifiez la version Python
python --version  # Doit être 3.11+

# Mettez à jour pip
pip install --upgrade pip

# Installez Poetry si nécessaire
curl -sSL https://install.python-poetry.org | python3 -
```

**Erreur de clé API**
```bash
# Vérifiez vos variables d'environnement
finagent config show

# Testez les connexions
finagent config test-apis
```

### Obtenir de l'Aide

- 🐛 [Issues GitHub](https://github.com/votre-username/finagent/issues)
- 💬 [Discussions](https://github.com/votre-username/finagent/discussions)
- 📧 Email: support@finagent.com

---

## 📄 Licence

Ce projet est sous licence MIT - voir le fichier [LICENSE](LICENSE) pour les détails.

---

## 🙏 Remerciements

- **Anthropic** pour Claude AI
- **OpenBB** pour les données financières
- **La communauté Python** pour les excellents outils
- **Tous les contributeurs** qui rendent ce projet possible

---

<div align="center">

**⭐ Si ce projet vous aide, n'hésitez pas à lui donner une étoile ! ⭐**

Fait avec ❤️ pour la communauté des traders

</div>