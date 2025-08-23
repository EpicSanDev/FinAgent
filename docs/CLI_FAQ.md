# FAQ - FinAgent CLI

## 🤔 Questions Fréquemment Posées

### 📦 Installation et Configuration

#### Q: Comment installer FinAgent CLI ?
**R:** 
```bash
pip install finagent

# Pour les interfaces interactives
pip install prompt-toolkit rich
```

#### Q: Comment configurer mes clés API ?
**R:** Utilisez l'assistant de configuration :
```bash
finagent --wizard
```

Ou configurez manuellement :
```bash
finagent config set api_keys.openrouter "your_key"
finagent config set api_keys.openbb "your_key"
```

#### Q: Où sont stockées mes configurations ?
**R:** Dans le répertoire `~/.finagent/config.json`. Vous pouvez également spécifier un chemin personnalisé :
```bash
finagent --config /path/to/custom/config.json
```

#### Q: Comment obtenir les clés API nécessaires ?
**R:** 
- **OpenRouter** : https://openrouter.ai/keys (requis pour l'IA)
- **OpenBB** : https://my.openbb.co/app/platform/credentials (recommandé)
- **Alpha Vantage** : https://www.alphavantage.co/support/#api-key (optionnel)

### 🎯 Utilisation des Interfaces

#### Q: Quelle interface choisir selon mon niveau ?
**R:** 
- **Débutant** : `finagent --wizard` (assistant guidé)
- **Intermédiaire** : `finagent --menu` (navigation par menus)
- **Avancé** : `finagent --interactive` (REPL avec auto-complétion)

#### Q: Comment utiliser l'auto-complétion dans le REPL ?
**R:** Appuyez sur `Tab` pour déclencher l'auto-complétion. Utilisez `?` pour l'aide contextuelle et `help` pour lister toutes les commandes.

#### Q: Les interfaces interactives ne fonctionnent pas ?
**R:** Installez les dépendances nécessaires :
```bash
pip install prompt-toolkit rich
```

### 📊 Analyse de Marché

#### Q: Quels symboles puis-je analyser ?
**R:** Tous les symboles disponibles sur les marchés financiers majeurs :
- Actions US : AAPL, MSFT, GOOGL, etc.
- Indices : SPY, QQQ, DIA, etc.
- Crypto : BTC-USD, ETH-USD, etc.
- Internationaux : TSM, ASML, etc.

#### Q: Comment analyser une action européenne ?
**R:** Utilisez le suffixe approprié :
```bash
finagent analyze stock ASML.AS  # Amsterdam
finagent analyze stock SAP.DE   # Frankfurt
finagent analyze stock LVMH.PA  # Paris
```

#### Q: Que signifient les différents niveaux de profondeur ?
**R:** 
- `basic` : Prix, volume, variation
- `standard` : + indicateurs techniques de base
- `detailed` : + analyse fondamentale
- `full` : + sentiment, prédictions IA, analyse complète

#### Q: Comment sauvegarder mes analyses ?
**R:** 
```bash
finagent analyze stock AAPL --save-report analysis.json --format json
finagent analyze stock AAPL --save-report analysis.yaml --format yaml
```

### 💼 Gestion de Portefeuilles

#### Q: Comment créer mon premier portefeuille ?
**R:** 
```bash
finagent portfolio create "Mon Premier Portefeuille" --initial-cash 50000
```

#### Q: Puis-je importer un portefeuille existant ?
**R:** Pas directement dans cette version. Créez le portefeuille et ajoutez les positions une par une :
```bash
finagent portfolio add "Mon Portefeuille" --symbol AAPL --quantity 50 --price 180
```

#### Q: Comment suivre la performance de mon portefeuille ?
**R:** 
```bash
finagent portfolio performance "Mon Portefeuille" --timeframe 1y --benchmark SPY
```

#### Q: Qu'est-ce que l'optimisation de portefeuille ?
**R:** L'optimisation recalcule les poids optimaux de chaque position selon un objectif (maximiser le rendement, minimiser le risque, etc.) :
```bash
finagent portfolio optimize "Mon Portefeuille" --objective sharpe_ratio
```

### 📋 Stratégies d'Investissement

#### Q: Quels types de stratégies puis-je créer ?
**R:** 
- **Momentum** : Suit les tendances de prix
- **Mean Reversion** : Exploitation des retours à la moyenne
- **DCA** : Dollar Cost Averaging (investissement périodique)
- **Value** : Basée sur les fondamentaux
- **Personnalisée** : Vos propres règles

#### Q: Comment tester une stratégie ?
**R:** Utilisez le backtesting :
```bash
finagent strategy backtest "Ma Stratégie" --start-date 2020-01-01 --end-date 2024-01-01
```

#### Q: Puis-je optimiser les paramètres d'une stratégie ?
**R:** Oui :
```bash
finagent strategy optimize "Ma Stratégie" --parameter lookback_period=10,20,30
```

### 🎯 Décisions de Trading

#### Q: Comment l'IA m'aide-t-elle dans mes décisions ?
**R:** L'IA analyse les données techniques, fondamentales et de sentiment pour fournir des recommandations justifiées :
```bash
finagent decision analyze TSLA --action buy --quantity 100 --include-reasoning
```

#### Q: Qu'est-ce que la simulation Monte Carlo ?
**R:** Une technique qui simule des milliers de scénarios possibles pour évaluer les risques :
```bash
finagent decision simulate AAPL --scenarios 1000 --horizon 30
```

#### Q: Comment suivre mes décisions passées ?
**R:** 
```bash
finagent decision history --limit 50
finagent decision performance --timeframe 6mo
```

### ⚙️ Configuration et Personnalisation

#### Q: Comment changer le modèle d'IA utilisé ?
**R:** 
```bash
finagent config set ai.model claude-3-opus      # Plus puissant
finagent config set ai.model claude-3-haiku     # Plus rapide
finagent config set ai.temperature 0.1          # Plus conservateur
```

#### Q: Comment configurer ma tolérance au risque ?
**R:** 
```bash
finagent config set preferences.risk_tolerance conservative  # Conservateur
finagent config set preferences.risk_tolerance moderate      # Modéré
finagent config set preferences.risk_tolerance aggressive    # Agressif
```

#### Q: Comment changer la fréquence de mise à jour des données ?
**R:** 
```bash
finagent config set data.update_frequency 1m   # 1 minute (temps réel)
finagent config set data.update_frequency 1h   # 1 heure
finagent config set data.update_frequency 1d   # 1 jour
```

### 🔧 Dépannage

#### Q: "Symbole UNKNOWN non trouvé" - Que faire ?
**R:** 
1. Vérifiez l'orthographe du symbole
2. Utilisez le bon suffixe pour les marchés internationaux
3. Vérifiez que le symbole existe sur votre source de données
4. Essayez un autre fournisseur de données

#### Q: "Clé API manquante" - Comment résoudre ?
**R:** 
```bash
# Vérifier la configuration
finagent config show --section api_keys

# Configurer la clé manquante
finagent config set api_keys.openrouter "your_key"
```

#### Q: Les données semblent obsolètes ?
**R:** 
```bash
# Forcer la mise à jour sans cache
finagent analyze stock AAPL --no-cache

# Vider tout le cache
finagent config cache clear
```

#### Q: Comment activer le mode debug ?
**R:** 
```bash
finagent --debug --verbose analyze stock AAPL
```

#### Q: L'interface est lente ou se bloque ?
**R:** 
1. Vérifiez votre connexion internet
2. Testez avec `--no-cache`
3. Réduisez la profondeur d'analyse (`--depth basic`)
4. Vérifiez les logs en mode verbose

### 💡 Conseils et Bonnes Pratiques

#### Q: Comment bien organiser mes portefeuilles ?
**R:** 
- Utilisez des noms descriptifs : "Tech Growth 2024", "Dividend Income"
- Séparez par objectif : croissance, revenus, spéculation
- Documentez vos stratégies dans la description

#### Q: À quelle fréquence analyser mes investissements ?
**R:** 
- **Trading actif** : Quotidiennement avec `--timeframe 1d`
- **Investissement long terme** : Hebdomadairement avec `--timeframe 1w`
- **Révision portefeuille** : Mensuellement avec analyse complète

#### Q: Comment interpréter les recommandations de l'IA ?
**R:** 
- Examinez toujours le raisonnement (`--include-reasoning`)
- Considérez votre propre analyse
- Utilisez les simulations pour évaluer les risques
- Ne suivez jamais aveuglément une recommandation

#### Q: Comment sauvegarder mes données importantes ?
**R:** 
```bash
# Sauvegarder la configuration
finagent config backup config_backup_$(date +%Y%m%d).json

# Exporter les analyses importantes
finagent analyze stock AAPL --save-report aapl_analysis_$(date +%Y%m%d).json
```

### 🚀 Fonctionnalités Avancées

#### Q: Puis-je automatiser des analyses ?
**R:** Utilisez des scripts bash ou des tâches cron :
```bash
#!/bin/bash
# Analyse quotidienne des actions favorites
for symbol in AAPL MSFT GOOGL; do
  finagent analyze stock $symbol --save-report ${symbol}_$(date +%Y%m%d).json
done
```

#### Q: Comment créer un script de surveillance de portefeuille ?
**R:** 
```bash
#!/bin/bash
# surveillance_portefeuille.sh
finagent portfolio performance "Mon Portefeuille" --format json > performance.json
python analyze_performance.py performance.json
```

#### Q: Puis-je intégrer FinAgent dans mes propres applications ?
**R:** FinAgent est conçu avec une architecture modulaire. Vous pouvez importer les modules Python directement :
```python
from finagent.cli.commands import analyze_command
from finagent.cli.formatters import create_formatter
```

### 📞 Support et Ressources

#### Q: Où trouver plus de documentation ?
**R:** 
- Guide complet : `docs/CLI_USAGE_GUIDE.md`
- Référence rapide : `docs/CLI_QUICK_REFERENCE.md`
- Exemples : `docs/CLI_EXAMPLES.md`
- Architecture : `ARCHITECTURE_REFERENCE.md`

#### Q: Comment signaler un bug ou demander une fonctionnalité ?
**R:** 
- GitHub Issues pour les bugs et demandes de fonctionnalités
- Documentation dans `/docs` pour les guides
- Exemples dans `/examples` pour les cas d'usage

#### Q: Puis-je contribuer au projet ?
**R:** Absolument ! Le projet suit une architecture modulaire qui facilite les contributions :
- Nouveaux formatters dans `finagent/cli/formatters/`
- Nouvelles commandes dans `finagent/cli/commands/`
- Nouveaux utilitaires dans `finagent/cli/utils/`

---

💡 **Astuce finale** : Explorez les commandes avec `--help` et n'hésitez pas à utiliser les interfaces interactives pour découvrir les fonctionnalités !