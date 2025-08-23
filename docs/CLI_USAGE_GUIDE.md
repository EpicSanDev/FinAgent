# Guide d'Utilisation CLI FinAgent

## 🎯 Introduction

FinAgent CLI est une interface complète en ligne de commande pour l'analyse financière propulsée par l'IA. Cette documentation vous guide dans l'utilisation de toutes les fonctionnalités disponibles.

## 📋 Table des Matières

1. [Installation et Configuration](#installation-et-configuration)
2. [Démarrage Rapide](#démarrage-rapide)
3. [Interfaces Utilisateur](#interfaces-utilisateur)
4. [Commandes Principales](#commandes-principales)
5. [Exemples Pratiques](#exemples-pratiques)
6. [Configuration Avancée](#configuration-avancée)
7. [Dépannage](#dépannage)

## 📦 Installation et Configuration

### Prérequis

```bash
# Python 3.8+
pip install finagent

# Dépendances optionnelles pour interfaces interactives
pip install prompt-toolkit rich
```

### Configuration Initiale

Utilisez l'assistant de configuration guidé :

```bash
python -m finagent.cli.main --wizard
```

Ou configurez manuellement :

```bash
# Configurer les clés API
finagent config set api_keys.openrouter "your_openrouter_key"
finagent config set api_keys.openbb "your_openbb_key"

# Configurer vos préférences
finagent config set preferences.risk_tolerance moderate
finagent config set preferences.default_currency USD
```

## 🚀 Démarrage Rapide

### Vérification de l'Installation

```bash
# Afficher la version et les modules disponibles
finagent version

# Afficher l'aide générale
finagent --help
```

### Première Analyse

```bash
# Analyse simple d'une action
finagent analyze stock AAPL

# Analyse détaillée avec indicateurs techniques
finagent analyze stock AAPL --depth full --indicators all
```

## 🎯 Interfaces Utilisateur

FinAgent offre trois interfaces selon votre niveau d'expérience :

### 1. Interface REPL (Avancée)

```bash
# Lance l'interface interactive avec auto-complétion
finagent --interactive
```

**Fonctionnalités :**
- Auto-complétion intelligente
- Historique des commandes
- Raccourcis clavier
- Aide contextuelle

**Raccourcis utiles :**
- `Tab` : Auto-complétion
- `Ctrl+R` : Recherche dans l'historique
- `?` : Aide contextuelle
- `help` : Liste des commandes

### 2. Assistant de Configuration (Débutant)

```bash
# Lance l'assistant pas-à-pas
finagent --wizard
```

**Idéal pour :**
- Nouveaux utilisateurs
- Configuration initiale
- Paramétrage guidé

### 3. Système de Menus (Intermédiaire)

```bash
# Lance la navigation par menus
finagent --menu
```

**Fonctionnalités :**
- Navigation intuitive
- Actions guidées
- Interface visuelle
- Descriptions détaillées

## 📊 Commandes Principales

### Analyse de Marché (`analyze`)

#### Analyser une Action

```bash
# Analyse de base
finagent analyze stock AAPL

# Analyse complète avec tous les indicateurs
finagent analyze stock AAPL \
  --timeframe 1y \
  --indicators all \
  --depth full \
  --include-sentiment \
  --include-fundamental

# Sauvegarder le rapport
finagent analyze stock MSFT \
  --save-report reports/msft_analysis.json \
  --format json
```

**Options disponibles :**
- `--timeframe` : Période (1d, 1w, 1mo, 1y, etc.)
- `--indicators` : Indicateurs techniques (sma, ema, rsi, macd, bollinger, all)
- `--depth` : Profondeur (basic, standard, detailed, full)
- `--include-sentiment` : Analyse de sentiment
- `--include-fundamental` : Analyse fondamentale

#### Comparer des Actions

```bash
# Comparaison simple
finagent analyze compare AAPL MSFT GOOGL

# Comparaison détaillée avec critères spécifiques
finagent analyze compare AAPL MSFT GOOGL \
  --criteria performance,valuation,growth \
  --timeframe 1y \
  --format table
```

#### Analyse de Marché

```bash
# Vue d'ensemble du marché
finagent analyze market

# Analyse sectorielle
finagent analyze market --sectors technology,healthcare,finance

# Analyse avec focus géographique
finagent analyze market --regions US,EU,ASIA
```

### Gestion de Portefeuilles (`portfolio`)

#### Créer un Portefeuille

```bash
# Création de base
finagent portfolio create "Mon Portefeuille Tech" \
  --description "Portefeuille axé sur la technologie" \
  --initial-cash 100000

# Avec stratégie d'allocation
finagent portfolio create "Portefeuille Équilibré" \
  --strategy balanced \
  --risk-tolerance moderate \
  --initial-cash 50000
```

#### Ajouter des Positions

```bash
# Ajouter une position
finagent portfolio add "Mon Portefeuille Tech" \
  --symbol AAPL \
  --quantity 50 \
  --price 180.50

# Ajouter plusieurs positions
finagent portfolio add "Mon Portefeuille Tech" \
  --symbol MSFT --quantity 30 --price 300.00 \
  --symbol GOOGL --quantity 20 --price 2500.00
```

#### Analyser un Portefeuille

```bash
# Affichage du portefeuille
finagent portfolio show "Mon Portefeuille Tech"

# Analyse de performance
finagent portfolio performance "Mon Portefeuille Tech" \
  --timeframe 1y \
  --benchmark SPY

# Optimisation
finagent portfolio optimize "Mon Portefeuille Tech" \
  --objective sharpe_ratio \
  --constraints max_weight=0.2
```

### Stratégies d'Investissement (`strategy`)

#### Créer une Stratégie

```bash
# Nouvelle stratégie à partir d'un template
finagent strategy create "Ma Stratégie Momentum" \
  --template momentum \
  --description "Stratégie basée sur le momentum"

# Stratégie personnalisée
finagent strategy create "DCA Bitcoin" \
  --type dca \
  --symbols BTC-USD \
  --frequency monthly \
  --amount 1000
```

#### Backtesting

```bash
# Test de stratégie
finagent strategy backtest "Ma Stratégie Momentum" \
  --start-date 2023-01-01 \
  --end-date 2024-01-01 \
  --initial-capital 100000

# Test avec optimisation des paramètres
finagent strategy backtest "Ma Stratégie Momentum" \
  --optimize-params \
  --metric sharpe_ratio \
  --periods 1000
```

#### Validation

```bash
# Valider une stratégie
finagent strategy validate "Ma Stratégie Momentum"

# Comparer plusieurs stratégies
finagent strategy compare "Stratégie A" "Stratégie B" "Stratégie C" \
  --metrics returns,volatility,sharpe_ratio
```

### Décisions de Trading (`decision`)

#### Analyser une Décision

```bash
# Analyse d'achat/vente
finagent decision analyze TSLA \
  --action buy \
  --quantity 100 \
  --target-price 250.00

# Avec analyse de risque
finagent decision analyze TSLA \
  --action buy \
  --quantity 100 \
  --risk-analysis \
  --stop-loss 220.00 \
  --take-profit 280.00
```

#### Simulation Monte Carlo

```bash
# Simulation de scénarios
finagent decision simulate AAPL \
  --scenarios 1000 \
  --horizon 30 \
  --confidence-levels 90,95,99

# Simulation avec paramètres personnalisés
finagent decision simulate AAPL \
  --scenarios 5000 \
  --volatility 0.25 \
  --drift 0.08 \
  --horizon 60
```

#### Historique et Performance

```bash
# Historique des décisions
finagent decision history --limit 50

# Performance des décisions
finagent decision performance \
  --timeframe 6mo \
  --group-by symbol

# Annuler une décision
finagent decision cancel --decision-id "dec_123456"
```

### Configuration (`config`)

#### Afficher la Configuration

```bash
# Configuration complète
finagent config show

# Section spécifique
finagent config show --section api_keys
finagent config show --section preferences
```

#### Modifier la Configuration

```bash
# Définir une valeur
finagent config set preferences.risk_tolerance aggressive
finagent config set ai.model claude-3-opus
finagent config set data.update_frequency 1h

# Supprimer une valeur
finagent config unset api_keys.alpha_vantage

# Réinitialiser
finagent config reset --section preferences
```

#### Gestion des Profils

```bash
# Sauvegarder la configuration
finagent config backup config_backup_2024.json

# Restaurer
finagent config restore config_backup_2024.json

# Initialiser pour un nouveau projet
finagent config init --template trading_bot
```

## 💡 Exemples Pratiques

### Exemple 1: Analyse Complète d'une Action

```bash
# Analyse technique et fondamentale complète
finagent analyze stock AAPL \
  --timeframe 1y \
  --indicators all \
  --depth full \
  --include-sentiment \
  --include-fundamental \
  --save-report aapl_analysis.json
```

### Exemple 2: Création et Gestion d'un Portefeuille

```bash
# 1. Créer le portefeuille
finagent portfolio create "Tech Growth" \
  --initial-cash 100000 \
  --strategy growth

# 2. Ajouter des positions
finagent portfolio add "Tech Growth" --symbol AAPL --quantity 50 --price 180
finagent portfolio add "Tech Growth" --symbol MSFT --quantity 30 --price 300
finagent portfolio add "Tech Growth" --symbol GOOGL --quantity 10 --price 2500

# 3. Analyser la performance
finagent portfolio performance "Tech Growth" --benchmark QQQ

# 4. Optimiser l'allocation
finagent portfolio optimize "Tech Growth" --objective max_return
```

### Exemple 3: Développement et Test d'une Stratégie

```bash
# 1. Créer la stratégie
finagent strategy create "Momentum FAANG" \
  --template momentum \
  --symbols AAPL,MSFT,GOOGL,AMZN,META

# 2. Valider la stratégie
finagent strategy validate "Momentum FAANG"

# 3. Backtesting
finagent strategy backtest "Momentum FAANG" \
  --start-date 2020-01-01 \
  --end-date 2024-01-01 \
  --initial-capital 100000

# 4. Optimiser les paramètres
finagent strategy optimize "Momentum FAANG" \
  --parameter lookback_period=10,20,30 \
  --parameter threshold=0.05,0.1,0.15
```

### Exemple 4: Prise de Décision avec IA

```bash
# 1. Analyser la décision
finagent decision analyze TSLA \
  --action buy \
  --quantity 100 \
  --include-reasoning

# 2. Simulation de risque
finagent decision simulate TSLA \
  --scenarios 1000 \
  --horizon 30 \
  --risk-metrics

# 3. Suivre la performance
finagent decision performance --symbol TSLA --timeframe 3mo
```

## ⚙️ Configuration Avancée

### Fichier de Configuration

Le fichier de configuration (`~/.finagent/config.json`) contient :

```json
{
  "api_keys": {
    "openrouter": "your_key_here",
    "openbb": "your_key_here"
  },
  "preferences": {
    "risk_tolerance": "moderate",
    "default_currency": "USD",
    "max_position_size": 0.1
  },
  "ai": {
    "model": "claude-3-sonnet",
    "temperature": 0.3,
    "confidence_threshold": 0.7
  },
  "data": {
    "data_provider": "openbb",
    "update_frequency": "1h",
    "cache_duration": 3600
  }
}
```

### Variables d'Environnement

```bash
# Clés API
export FINAGENT_OPENROUTER_KEY="your_key"
export FINAGENT_OPENBB_KEY="your_key"

# Configuration
export FINAGENT_CONFIG_PATH="/custom/path/config.json"
export FINAGENT_DATA_DIR="/custom/data/directory"
```

### Options Globales

```bash
# Mode verbose pour debugging
finagent --verbose analyze stock AAPL

# Mode debug complet
finagent --debug portfolio show "Mon Portefeuille"

# Configuration personnalisée
finagent --config /path/to/custom/config.json analyze market
```

## 🔧 Dépannage

### Problèmes Courants

#### 1. Erreur d'Import des Interfaces Interactives

```bash
# Erreur
❌ Interface REPL non disponible (dépendances manquantes)

# Solution
pip install prompt-toolkit rich
```

#### 2. Clés API Non Configurées

```bash
# Erreur
❌ Clé API OpenRouter manquante

# Solution
finagent config set api_keys.openrouter "your_key_here"
# Ou utiliser l'assistant
finagent --wizard
```

#### 3. Données Non Trouvées

```bash
# Erreur
❌ Symbole UNKNOWN non trouvé

# Vérifications
finagent analyze stock AAPL  # Utiliser un symbole valide
finagent config show --section data  # Vérifier la configuration
```

#### 4. Cache Corrompu

```bash
# Vider le cache
finagent config cache clear

# Désactiver temporairement
finagent analyze stock AAPL --no-cache
```

### Logs et Debug

```bash
# Activer les logs détaillés
finagent --debug --verbose analyze stock AAPL

# Vérifier la configuration
finagent config validate

# Test de connectivité
finagent config test-connection
```

### Support

- **Documentation complète** : `/docs`
- **Exemples** : `/examples`
- **Issues** : GitHub Issues
- **FAQ** : `/docs/FAQ.md`

## 📈 Bonnes Pratiques

### 1. Sécurité

- Ne jamais committre les clés API
- Utiliser des variables d'environnement
- Sauvegarder régulièrement la configuration

### 2. Performance

- Utiliser le cache pour les requêtes fréquentes
- Ajuster la fréquence de mise à jour selon les besoins
- Optimiser les paramètres IA selon votre usage

### 3. Organisation

- Nommer clairement vos portefeuilles et stratégies
- Documenter vos stratégies personnalisées
- Sauvegarder les rapports importants

### 4. Apprentissage

- Commencer par l'assistant de configuration
- Utiliser le mode interactif pour explorer
- Tester avec de petits montants d'abord

---

**📝 Note :** Cette documentation couvre la version 1.0.0 de FinAgent CLI. Pour les dernières mises à jour, consultez la documentation officielle.