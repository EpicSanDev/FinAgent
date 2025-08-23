# Guide de Référence Rapide - FinAgent CLI

## 🚀 Commandes Essentielles

### Installation & Configuration

```bash
# Configuration initiale guidée
finagent --wizard

# Configurer les clés API
finagent config set api_keys.openrouter "your_key"
finagent config set api_keys.openbb "your_key"

# Vérifier la configuration
finagent config show
```

### Analyses Rapides

```bash
# Analyse simple d'une action
finagent analyze stock AAPL

# Analyse complète
finagent analyze stock AAPL --depth full --indicators all

# Comparer des actions
finagent analyze compare AAPL MSFT GOOGL

# Vue marché
finagent analyze market
```

### Portefeuilles

```bash
# Créer un portefeuille
finagent portfolio create "Mon Portefeuille" --initial-cash 100000

# Ajouter une position
finagent portfolio add "Mon Portefeuille" --symbol AAPL --quantity 50

# Voir le portefeuille
finagent portfolio show "Mon Portefeuille"

# Analyser les performances
finagent portfolio performance "Mon Portefeuille"
```

### Stratégies

```bash
# Créer une stratégie
finagent strategy create "Ma Stratégie" --template momentum

# Backtesting
finagent strategy backtest "Ma Stratégie" --start-date 2023-01-01

# Optimiser
finagent strategy optimize "Ma Stratégie"
```

### Décisions

```bash
# Analyser une décision
finagent decision analyze TSLA --action buy --quantity 100

# Simuler des scénarios
finagent decision simulate TSLA --scenarios 1000

# Historique
finagent decision history
```

## 🎯 Interfaces Utilisateur

```bash
# REPL interactif (avancé)
finagent --interactive

# Assistant de configuration (débutant)
finagent --wizard

# Système de menus (intermédiaire)
finagent --menu
```

## ⚙️ Options Globales

```bash
# Modes de debug
finagent --verbose <command>    # Mode verbose
finagent --debug <command>      # Mode debug complet

# Configuration personnalisée
finagent --config /path/to/config.json <command>
```

## 📊 Formats de Sortie

```bash
# Table (défaut)
finagent analyze stock AAPL --format table

# JSON
finagent analyze stock AAPL --format json

# YAML
finagent analyze stock AAPL --format yaml

# Sauvegarder
finagent analyze stock AAPL --save-report report.json
```

## 🔧 Gestion du Cache

```bash
# Utiliser le cache (défaut)
finagent analyze stock AAPL --cache

# Ignorer le cache
finagent analyze stock AAPL --no-cache

# Vider le cache
finagent config cache clear
```

## 📅 Timeframes Supportés

- `1m`, `5m`, `15m`, `30m`, `1h` - Intrajournalier
- `1d`, `1w`, `1mo` - Court terme
- `3mo`, `6mo`, `1y`, `2y`, `5y` - Long terme

## 📈 Indicateurs Techniques

- `sma` - Moyenne mobile simple
- `ema` - Moyenne mobile exponentielle
- `rsi` - Relative Strength Index
- `macd` - MACD
- `bollinger` - Bandes de Bollinger
- `all` - Tous les indicateurs

## 💡 Raccourcis REPL

| Raccourci | Action |
|-----------|--------|
| `Tab` | Auto-complétion |
| `Ctrl+R` | Recherche historique |
| `Ctrl+L` | Effacer l'écran |
| `Ctrl+C` | Interrompre |
| `Ctrl+D` | Quitter |
| `?` | Aide contextuelle |
| `help` | Liste des commandes |

## 🎨 Codes de Couleur

- 🟢 **Vert** : Gains, succès, valeurs positives
- 🔴 **Rouge** : Pertes, erreurs, valeurs négatives
- 🟡 **Jaune** : Avertissements, informations importantes
- 🔵 **Cyan** : Titres, en-têtes
- ⚪ **Gris** : Informations secondaires

## 🔐 Variables d'Environnement

```bash
export FINAGENT_OPENROUTER_KEY="your_key"
export FINAGENT_OPENBB_KEY="your_key"
export FINAGENT_CONFIG_PATH="/path/to/config.json"
export FINAGENT_DATA_DIR="/path/to/data"
```

## ❗ Dépannage Express

```bash
# Test de connectivité
finagent config test-connection

# Validation de la configuration
finagent config validate

# Réinitialiser la configuration
finagent config reset

# Version et modules
finagent version
```

## 📱 Exemples Rapides

### Analyse Journalière
```bash
finagent analyze stock AAPL --timeframe 1d --indicators rsi,macd
```

### Portefeuille Diversifié
```bash
finagent portfolio create "Diversifié" --initial-cash 50000
finagent portfolio add "Diversifié" --symbol AAPL --quantity 25
finagent portfolio add "Diversifié" --symbol MSFT --quantity 20
finagent portfolio add "Diversifié" --symbol GOOGL --quantity 5
```

### Stratégie DCA
```bash
finagent strategy create "DCA S&P500" --type dca --symbol SPY --frequency monthly --amount 1000
```

### Décision avec Stop-Loss
```bash
finagent decision analyze TSLA --action buy --quantity 50 --stop-loss 220 --take-profit 280
```

---

💡 **Astuce** : Utilisez `finagent <command> --help` pour l'aide détaillée de chaque commande.