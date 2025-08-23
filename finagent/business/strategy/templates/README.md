# Templates de Stratégies FinAgent

Ce répertoire contient des templates de stratégies prêts à l'emploi pour le système FinAgent. Chaque template démontre une approche de trading différente avec des configurations complètes et des bonnes pratiques.

## Templates Disponibles

### 1. Basic Momentum Strategy (`basic_momentum_strategy.yaml`)

**Type :** Momentum / Suivi de tendance  
**Niveau de risque :** Moyen  
**Fréquence :** Quotidienne  

**Description :**
Stratégie classique de momentum basée sur les croisements de moyennes mobiles et le RSI. Idéale pour les débutants souhaitant comprendre les concepts de base.

**Caractéristiques principales :**
- Utilise les moyennes mobiles 20/50 pour détecter les tendances
- RSI pour éviter les zones de surachat/survente
- Confirmation par le volume
- Gestion des risques conservative (5% stop-loss, 15% take-profit)

**Instruments cibles :** Actions tech grandes capitalisations (AAPL, GOOGL, MSFT, AMZN)

**Performance attendue :**
- Rendement annuel : 12%
- Volatilité : 18%
- Ratio de Sharpe : ~0.67
- Drawdown max : 10%

### 2. Mean Reversion Strategy (`mean_reversion_strategy.yaml`)

**Type :** Retour à la moyenne  
**Niveau de risque :** Faible  
**Fréquence :** Intraday (3x/jour)  

**Description :**
Stratégie exploitant les déviations temporaires par rapport à la moyenne historique. Particulièrement efficace en marchés latéraux et pour les actions défensives.

**Caractéristiques principales :**
- Bandes de Bollinger pour identifier les zones de survente/surachat
- Z-Score pour mesurer les déviations statistiques
- Positions courtes (holding period ~5-10 jours)
- Gestion des risques très serrée (3% stop-loss, 8% take-profit)

**Instruments cibles :** Actions défensives (JNJ, PG, KO, PFE, WMT)

**Performance attendue :**
- Rendement annuel : 8%
- Volatilité : 12%
- Ratio de Sharpe : ~0.8
- Drawdown max : 6%
- Excellent en marchés latéraux/volatils

### 3. Breakout Strategy (`breakout_strategy.yaml`)

**Type :** Cassure / Momentum agressif  
**Niveau de risque :** Élevé  
**Fréquence :** Temps réel  

**Description :**
Stratégie agressive exploitant les cassures de niveaux de résistance avec confirmation de volume. Optimisée pour capturer les mouvements importants sur actions volatiles.

**Caractéristiques principales :**
- Détection automatique des niveaux de support/résistance
- Confirmation obligatoire par le volume (>150% de la moyenne)
- Stop-loss trailing pour protéger les profits
- Prise de profit échelonnée (8%, 15%, 25%)

**Instruments cibles :** Actions volatiles tech (TSLA, NVDA, AMD, NFLX, CRM)

**Performance attendue :**
- Rendement annuel : 20%
- Volatilité : 25%
- Ratio de Sharpe : ~0.9
- Drawdown max : 15%
- Excellent en marchés haussiers/volatils

## Structure des Templates

Chaque template YAML comprend les sections suivantes :

### Sections Obligatoires

```yaml
strategy:           # Métadonnées de la stratégie
instruments:        # Actifs à trader
buy_conditions:     # Conditions d'achat
sell_conditions:    # Conditions de vente
risk_management:    # Gestion des risques
execution:          # Paramètres d'exécution
data_requirements:  # Besoins en données
```

### Sections Optionnelles

```yaml
backtesting:        # Configuration du backtesting
metadata:           # Tags et performance attendue
alerts:             # Configuration des alertes
advanced:           # Paramètres avancés
paper_trading:      # Configuration du paper trading
```

## Utilisation des Templates

### 1. Copie et Personnalisation

```bash
# Copier un template
cp basic_momentum_strategy.yaml my_custom_strategy.yaml

# Éditer selon vos besoins
nano my_custom_strategy.yaml
```

### 2. Chargement dans FinAgent

```python
from finagent.business.strategy.manager import StrategyManager

# Initialiser le gestionnaire
manager = StrategyManager()
await manager.initialize()

# Charger la stratégie
strategy_id = await manager.add_strategy_from_file("my_custom_strategy.yaml")

# Démarrer la stratégie
await manager.start_strategy(strategy_id)
```

### 3. Validation et Test

```python
# Validation de la stratégie
from finagent.business.strategy.parser import StrategyValidator

validator = StrategyValidator()
result = await validator.validate_strategy_file("my_custom_strategy.yaml")

if result.is_valid:
    print("Stratégie valide !")
else:
    print(f"Erreurs: {result.get_error_summary()}")
```

## Personnalisation des Templates

### Paramètres Fréquemment Modifiés

1. **Instruments** : Adapter la liste des actions selon votre univers
2. **Seuils des indicateurs** : Ajuster selon la volatilité des marchés
3. **Gestion des risques** : Adapter stop-loss/take-profit selon votre tolérance
4. **Fréquence d'exécution** : Modifier selon vos capacités techniques
5. **Taille des positions** : Ajuster selon votre capital

### Exemples de Modifications

```yaml
# Modifier les instruments
instruments:
  - symbol: "VOO"    # ETF S&P 500
    weight: 0.50
  - symbol: "VTI"    # ETF Total Stock Market
    weight: 0.50

# Ajuster les seuils RSI pour plus de sensibilité
rsi_oversold:
  threshold: 35      # Au lieu de 30
  
# Réduire le stop-loss pour plus de sécurité
stop_loss:
  value: 0.03        # 3% au lieu de 5%
```

## Bonnes Pratiques

### 1. Testing Progressif

1. **Paper Trading** : Toujours commencer par du paper trading
2. **Backtesting** : Valider sur données historiques (min. 2 ans)
3. **Forward Testing** : Tester en réel avec petit capital
4. **Scaling** : Augmenter progressivement les positions

### 2. Gestion des Risques

```yaml
# Toujours définir des limites claires
risk_management:
  stop_loss:
    value: 0.05      # Maximum 5% de perte par position
  position_sizing:
    value: 0.02      # Maximum 2% du portefeuille par position
  max_drawdown:
    value: 0.10      # Arrêt si drawdown > 10%
```

### 3. Monitoring

```yaml
# Configurer des alertes appropriées
alerts:
  performance_alerts:
    drawdown_warning: 0.05   # Alerte à 5% de drawdown
  technical_alerts:
    rsi_extreme: [20, 80]    # RSI extrême
  notifications:
    email: true
    webhook: "https://your-webhook-url.com"
```

### 4. Optimisation Continue

- **Monitoring quotidien** des performances
- **Revue mensuelle** des paramètres
- **Optimisation trimestrielle** des seuils
- **Adaptation** aux conditions de marché

## FAQ

**Q: Puis-je combiner plusieurs templates ?**
R: Oui, vous pouvez créer des stratégies hybrides en combinant les conditions de différents templates.

**Q: Comment adapter un template à d'autres classes d'actifs ?**
R: Modifiez la section `instruments` et ajustez les paramètres selon la volatilité de la classe d'actifs.

**Q: Quelle fréquence de données recommandée ?**
R: 
- Momentum : Données journalières suffisantes
- Mean Reversion : Données horaires recommandées
- Breakout : Données 5-minutes nécessaires

**Q: Comment gérer les coûts de transaction ?**
R: Configurez la section `backtesting.transaction_costs` avec vos coûts réels pour des simulations précises.

**Q: Puis-je utiliser des indicateurs personnalisés ?**
R: Oui, ajoutez vos indicateurs dans `data_requirements.indicators` et référencez-les dans les conditions.

## Support et Contributions

Pour des questions ou contributions :
- 📧 Email : support@finagent.com
- 📚 Documentation : https://docs.finagent.com
- 🐛 Issues : https://github.com/finagent/issues
- 💬 Community : https://discord.gg/finagent

## Clause de Non-Responsabilité

⚠️ **IMPORTANT** : Ces templates sont fournis à des fins éducatives et de démonstration. Le trading comporte des risques significants de perte. Toujours :
- Tester en paper trading avant le trading réel
- Ne jamais risquer plus que vous ne pouvez vous permettre de perdre
- Consulter un conseiller financier si nécessaire
- Comprendre que les performances passées ne garantissent pas les résultats futurs