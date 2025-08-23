# FinAgent CLI - Interface en Ligne de Commande

## 🚀 Vue d'Ensemble

FinAgent CLI est une interface en ligne de commande complète et élégante pour l'agent IA financier FinAgent. Elle offre des outils puissants pour l'analyse financière, la gestion de portefeuilles, le développement de stratégies et la prise de décisions d'investissement.

## ✨ Fonctionnalités Principales

### 📊 Analyse Financière
- **Analyse d'actions individuelles** avec indicateurs techniques
- **Comparaison multi-titres** avec métriques personnalisables
- **Vue d'ensemble du marché** par région et secteur
- **Intégration IA** pour l'analyse de sentiment et les recommandations

### 💼 Gestion de Portefeuilles
- **Création et suivi** de portefeuilles multiples
- **Analyse de performance** avec benchmarks
- **Optimisation automatique** selon différents objectifs
- **Alertes et notifications** personnalisables

### 🎯 Stratégies d'Investissement
- **Création de stratégies** avec templates prédéfinis
- **Backtesting historique** avec métriques de risque
- **Optimisation de paramètres** multi-objectifs
- **Simulation Monte Carlo** pour la validation

### 🤖 Aide à la Décision
- **Analyse de décisions** d'achat/vente
- **Simulation de scénarios** avec intervalles de confiance
- **Historique des décisions** et analyse de performance
- **Gestion des risques** automatisée

### ⚙️ Configuration et Maintenance
- **Gestion centralisée** des paramètres
- **Sauvegarde/restauration** de configurations
- **Cache intelligent** pour les performances
- **Tests de connectivité** aux APIs

## 🖥️ Interfaces Utilisateur

### Interface Standard (CLI)
```bash
# Utilisation directe en ligne de commande
finagent analyze stock AAPL --timeframe 1mo --indicators sma,rsi
finagent portfolio show "Mon Portefeuille" --format table
```

### Interface Interactive (REPL)
```bash
# Mode interactif avec auto-complétion
finagent --interactive
finagent> analyze stock AAPL
finagent> portfolio create "Test Portfolio"
finagent> help
```

### Assistant de Configuration (Wizard)
```bash
# Configuration guidée pas-à-pas
finagent --wizard
```

### Système de Menus
```bash
# Navigation par menus pour débutants
finagent --menu
```

## 📦 Structure du Module

```
finagent/cli/
├── __init__.py                 # Point d'entrée principal
├── main.py                     # CLI principal avec toutes les commandes
├── README.md                   # Cette documentation
│
├── commands/                   # Commandes CLI principales
│   ├── __init__.py
│   ├── analyze_command.py      # Commandes d'analyse (stock, compare, market)
│   ├── portfolio_command.py    # Gestion de portefeuilles
│   ├── strategy_command.py     # Développement de stratégies
│   ├── decision_command.py     # Aide à la décision
│   └── config_command.py       # Configuration système
│
├── interactive/                # Interfaces interactives
│   ├── __init__.py
│   ├── repl.py                # REPL avec Prompt Toolkit
│   ├── wizard.py              # Assistant de configuration
│   └── menu_system.py         # Système de navigation par menus
│
├── formatters/                 # Formatters de sortie élégants
│   ├── __init__.py
│   ├── base_formatter.py      # Classe de base et factory
│   ├── market_formatter.py    # Formatage données de marché
│   ├── analysis_formatter.py  # Formatage analyses techniques
│   ├── portfolio_formatter.py # Formatage portefeuilles
│   └── decision_formatter.py  # Formatage aide à la décision
│
└── utils/                      # Utilitaires CLI
    ├── __init__.py
    ├── validation.py          # Types Click personnalisés et validation
    ├── progress.py            # Barres de progression avancées
    └── cache_utils.py         # Gestion du cache intelligent
```

## 🎨 Formatage et Présentation

Le module CLI utilise la bibliothèque **Rich** pour un formatage élégant :

### Tableaux Dynamiques
```
┌─────────────┬──────────────┬───────────────┬─────────────┐
│ Symbol      │ Price        │ Change        │ Volume      │
├─────────────┼──────────────┼───────────────┼─────────────┤
│ AAPL        │ $185.25      │ +2.1% ↗       │ 45.2M       │
│ MSFT        │ $310.50      │ -0.8% ↘       │ 28.7M       │
│ GOOGL       │ $2,485.00    │ +1.5% ↗       │ 12.1M       │
└─────────────┴──────────────┴───────────────┴─────────────┘
```

### Panneaux Informatifs
```
╭─── 📊 Analyse AAPL ───╮
│ Prix actuel: $185.25  │
│ Variation: +2.1%      │
│ RSI: 65.2 (Neutre)    │
│ Recommandation: HOLD  │
╰───────────────────────╯
```

### Graphiques ASCII
```
Prix AAPL (30 jours)
180 ┤
185 ┤  ╭─╮
190 ┤ ╱   ╰─╮
195 ┤╱      ╰─╮
200 ┤         ╰
```

### Barres de Progression
```
Analyse en cours... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:02
```

## 🔧 Types de Validation Personnalisés

Le module inclut des types Click avancés pour la validation :

```python
# Types disponibles
SymbolType         # Validation des symboles boursiers
AmountType         # Validation des montants financiers
PercentageType     # Validation des pourcentages
DateType           # Validation des dates
TimeframeType      # Validation des périodes temporelles
```

## 📈 Système de Cache Intelligent

Le cache améliore les performances tout en gardant les données à jour :

```python
# Métadonnées automatiques
{
    "key": "AAPL_1d_analysis",
    "timestamp": "2024-01-15T10:30:00Z",
    "expires_at": "2024-01-15T11:00:00Z",
    "data_type": "stock_analysis",
    "dependencies": ["AAPL_price", "AAPL_volume"],
    "size_bytes": 2048
}
```

## 🎯 Intégration avec FinAgent Core

Le CLI s'intègre parfaitement avec les modules core de FinAgent :

```python
# Exemple d'intégration
from finagent.core.market import MarketData
from finagent.core.analysis import TechnicalAnalyzer
from finagent.ai.claude import ClaudeAnalyzer

# Le CLI orchestre ces composants automatiquement
```

## 🚀 Performance et Optimisations

### Chargement Paresseux
- Import des modules seulement quand nécessaire
- Réduction du temps de démarrage

### Mise en Cache Intelligente
- Cache des données de marché avec expiration
- Invalidation automatique des dépendances
- Optimisation des requêtes répétées

### Formatage Asynchrone
- Traitement des données en arrière-plan
- Interface réactive même pour les gros datasets

## 🛡️ Gestion d'Erreurs Robuste

### Validation des Entrées
- Vérification des symboles boursiers
- Validation des montants et pourcentages
- Contrôle des plages de dates

### Gestion des Erreurs API
- Retry automatique avec backoff exponentiel
- Messages d'erreur informatifs
- Mode dégradé quand les APIs sont indisponibles

### Récupération Gracieuse
- Fallback sur les données en cache
- Continuation avec données partielles
- Logs détaillés pour le debugging

## 📚 Documentation Complète

### Guides Disponibles
- **[Guide d'Utilisation](../../docs/CLI_USAGE_GUIDE.md)** - Documentation complète avec exemples
- **[Référence Rapide](../../docs/CLI_QUICK_REFERENCE.md)** - Commandes essentielles
- **[FAQ](../../docs/CLI_FAQ.md)** - Questions fréquentes et solutions
- **[Exemples Pratiques](../../docs/CLI_EXAMPLES.md)** - Scénarios d'utilisation réels

### Aide Intégrée
```bash
# Aide générale
finagent --help

# Aide pour une commande spécifique
finagent analyze --help
finagent portfolio create --help

# Aide contextuelle dans le REPL
finagent> help analyze
finagent> help portfolio
```

## 🔄 Flux de Développement

### Ajout d'une Nouvelle Commande

1. **Créer le module de commande** dans `commands/`
2. **Implémenter les sous-commandes** avec décorateurs Click
3. **Ajouter le formatter** correspondant dans `formatters/`
4. **Intégrer dans `main.py`** comme groupe de commandes
5. **Ajouter les tests** et la documentation

### Exemple de Nouvelle Commande

```python
# commands/new_command.py
import click
from finagent.cli.formatters import get_formatter

@click.group()
def new_command():
    """Nouvelle fonctionnalité."""
    pass

@new_command.command()
@click.argument('symbol')
def action(symbol):
    """Action sur un symbole."""
    # Logique métier
    result = perform_action(symbol)
    
    # Formatage et affichage
    formatter = get_formatter('new', 'table')
    formatter.format_result(result)

# main.py
from finagent.cli.commands.new_command import new_command

cli.add_command(new_command)
```

## 🎪 Extensibilité

### Formatters Personnalisés
```python
# Ajouter un nouveau format
class CustomFormatter(BaseFormatter):
    def format_data(self, data):
        # Implémentation personnalisée
        pass

# Enregistrer le formatter
register_formatter('custom', CustomFormatter)
```

### Types de Validation Personnalisés
```python
# Nouveau type Click
class CustomType(click.ParamType):
    def convert(self, value, param, ctx):
        # Logique de validation
        return validated_value
```

### Plugins Externes
```python
# Structure pour plugins
finagent/plugins/
├── __init__.py
├── my_plugin/
│   ├── __init__.py
│   ├── commands.py
│   └── formatters.py
```

## 📊 Métriques et Monitoring

### Utilisation des Commandes
- Statistiques d'utilisation par commande
- Temps d'exécution moyens
- Taux d'erreur par fonction

### Performance du Cache
- Taux de hit/miss du cache
- Taille et évolution du cache
- Optimisation automatique

### Qualité des Données
- Fraîcheur des données affichées
- Sources de données utilisées
- Latence des APIs externes

---

## 🤝 Contribution

Pour contribuer au développement du CLI :

1. **Fork** le repository
2. **Créer une branche** pour votre fonctionnalité
3. **Développer** avec les patterns établis
4. **Tester** thoroughly
5. **Documenter** vos changements
6. **Soumettre** une pull request

---

💡 **Le CLI FinAgent combine puissance, élégance et simplicité d'utilisation pour offrir une expérience utilisateur exceptionnelle dans l'analyse financière.**