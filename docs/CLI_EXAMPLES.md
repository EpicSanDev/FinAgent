# Exemples Pratiques - FinAgent CLI

## 🎯 Scénarios d'Utilisation Réels

Cette documentation présente des exemples concrets d'utilisation de FinAgent CLI pour différents profils d'investisseurs et cas d'usage.

## 📊 1. Analyste Financier - Recherche Quotidienne

### Analyse Matinale du Marché

```bash
#!/bin/bash
# analyse_matinale.sh - Script d'analyse quotidienne

echo "📊 Analyse matinale du marché - $(date)"

# Vue d'ensemble du marché
finagent analyze market --regions US,EU --format table

# Analyse des grands indices
for index in SPY QQQ DIA VTI; do
  echo "Analyse de $index..."
  finagent analyze stock $index \
    --timeframe 1d \
    --indicators sma,ema,rsi \
    --include-sentiment \
    --save-report "reports/daily_${index}_$(date +%Y%m%d).json"
done

# Top performers et losers
finagent analyze market --top-movers 10 --format table
```

### Analyse Sectorielle Hebdomadaire

```bash
#!/bin/bash
# analyse_sectorielle.sh

sectors=("XLK" "XLF" "XLV" "XLE" "XLI" "XLY" "XLP" "XLU" "XLRE" "XLB" "XLC")

echo "📈 Analyse sectorielle hebdomadaire"

for sector in "${sectors[@]}"; do
  finagent analyze stock $sector \
    --timeframe 1w \
    --depth detailed \
    --indicators all \
    --save-report "reports/sector_${sector}_weekly.json"
done

# Comparaison des secteurs
finagent analyze compare "${sectors[@]}" \
  --criteria performance,volatility \
  --timeframe 1mo
```

## 💼 2. Gestionnaire de Portefeuille - Suivi d'Investissements

### Création d'un Portefeuille Diversifié

```bash
# Portefeuille équilibré pour investisseur modéré
finagent portfolio create "Portefeuille Équilibré 2024" \
  --description "Allocation diversifiée pour croissance modérée" \
  --initial-cash 100000 \
  --strategy balanced

# Allocation par secteur (exemple)
# Technology 25%
finagent portfolio add "Portefeuille Équilibré 2024" --symbol AAPL --quantity 69 --price 180.00
finagent portfolio add "Portefeuille Équilibré 2024" --symbol MSFT --quantity 42 --price 300.00
finagent portfolio add "Portefeuille Équilibré 2024" --symbol GOOGL --quantity 4 --price 2500.00

# Healthcare 20%
finagent portfolio add "Portefeuille Équilibré 2024" --symbol JNJ --quantity 125 --price 160.00
finagent portfolio add "Portefeuille Équilibré 2024" --symbol PFE --quantity 333 --price 30.00

# Finance 15%
finagent portfolio add "Portefeuille Équilibré 2024" --symbol JPM --quantity 70 --price 150.00
finagent portfolio add "Portefeuille Équilibré 2024" --symbol BAC --quantity 200 --price 35.00

# Consumer Goods 15%
finagent portfolio add "Portefeuille Équilibré 2024" --symbol PG --quantity 65 --price 155.00
finagent portfolio add "Portefeuille Équilibré 2024" --symbol KO --quantity 175 --price 57.00

# Energy 10%
finagent portfolio add "Portefeuille Équilibré 2024" --symbol XOM --quantity 95 --price 105.00

# Utilities 10%
finagent portfolio add "Portefeuille Équilibré 2024" --symbol NEE --quantity 130 --price 77.00

# Real Estate 5%
finagent portfolio add "Portefeuille Équilibré 2024" --symbol VNQ --quantity 50 --price 100.00
```

### Suivi de Performance Mensuel

```bash
#!/bin/bash
# suivi_mensuel.sh

portfolio_name="Portefeuille Équilibré 2024"

echo "📊 Rapport mensuel - $portfolio_name"

# Performance générale
finagent portfolio performance "$portfolio_name" \
  --timeframe 1mo \
  --benchmark SPY \
  --save-report "reports/monthly_performance_$(date +%Y%m).json"

# Analyse détaillée
finagent portfolio show "$portfolio_name" --format table

# Recommandations de rééquilibrage
finagent portfolio optimize "$portfolio_name" \
  --objective sharpe_ratio \
  --constraints max_weight=0.15

# Alerte sur les positions perdantes
finagent portfolio analyze "$portfolio_name" \
  --alerts underperforming \
  --threshold -10
```

## 🤖 3. Trader Algorithmique - Développement de Stratégies

### Stratégie Momentum Simple

```bash
# Création d'une stratégie momentum
finagent strategy create "Momentum Tech Stocks" \
  --template momentum \
  --description "Stratégie momentum sur les valeurs technologiques" \
  --symbols AAPL,MSFT,GOOGL,AMZN,META,NVDA,AMD,CRM,ORCL,ADBE

# Configuration des paramètres
finagent strategy configure "Momentum Tech Stocks" \
  --parameter lookback_period=20 \
  --parameter threshold=0.05 \
  --parameter stop_loss=0.1 \
  --parameter take_profit=0.2

# Backtesting sur 3 ans
finagent strategy backtest "Momentum Tech Stocks" \
  --start-date 2021-01-01 \
  --end-date 2024-01-01 \
  --initial-capital 100000 \
  --save-report "backtest_momentum_tech.json"

# Optimisation des paramètres
finagent strategy optimize "Momentum Tech Stocks" \
  --parameter lookback_period=10,15,20,25,30 \
  --parameter threshold=0.03,0.05,0.07,0.1 \
  --metric sharpe_ratio \
  --periods 1000
```

### Stratégie DCA (Dollar Cost Averaging)

```bash
# Stratégie d'investissement périodique
finagent strategy create "DCA S&P 500" \
  --type dca \
  --description "Investissement mensuel dans l'indice S&P 500" \
  --symbol SPY \
  --frequency monthly \
  --amount 2000

# Simulation sur 10 ans
finagent strategy backtest "DCA S&P 500" \
  --start-date 2014-01-01 \
  --end-date 2024-01-01 \
  --initial-capital 0

# Comparaison avec investissement unique
finagent strategy create "Lump Sum S&P 500" \
  --type buy_and_hold \
  --symbol SPY \
  --amount 240000  # 2000 * 12 * 10 ans

finagent strategy compare "DCA S&P 500" "Lump Sum S&P 500" \
  --metrics returns,volatility,max_drawdown
```

### Stratégie Mean Reversion

```bash
# Stratégie de retour à la moyenne
finagent strategy create "Mean Reversion Quality" \
  --template mean_reversion \
  --description "Retour à la moyenne sur actions de qualité" \
  --symbols MSFT,AAPL,JNJ,PG,KO,WMT,V,MA

# Configuration spécifique
finagent strategy configure "Mean Reversion Quality" \
  --parameter bollinger_period=20 \
  --parameter bollinger_std=2 \
  --parameter rsi_oversold=30 \
  --parameter rsi_overbought=70 \
  --parameter min_volume=1000000

# Test avec différentes périodes de marché
finagent strategy backtest "Mean Reversion Quality" \
  --start-date 2020-03-01 --end-date 2020-06-01 \
  --label "COVID_Crash" \
  --save-report "meanrev_covid.json"

finagent strategy backtest "Mean Reversion Quality" \
  --start-date 2022-01-01 --end-date 2022-12-31 \
  --label "Bear_Market_2022" \
  --save-report "meanrev_bear2022.json"
```

## 🎯 4. Investisseur Particulier - Décisions Personnelles

### Analyse Avant Achat

```bash
# Je veux acheter Tesla - dois-je le faire maintenant ?
finagent decision analyze TSLA \
  --action buy \
  --quantity 50 \
  --budget 10000 \
  --include-reasoning \
  --risk-analysis

# Simulation de différents scénarios
finagent decision simulate TSLA \
  --scenarios 1000 \
  --horizon 60 \  # 60 jours
  --confidence-levels 90,95,99

# Comparaison avec alternatives
finagent analyze compare TSLA NIO RIVN LCID \
  --criteria growth,volatility,sentiment \
  --timeframe 1y
```

### Gestion de Position Existante

```bash
# J'ai 100 actions Apple achetées à 150$ - que faire ?
finagent decision analyze AAPL \
  --action evaluate \
  --current-position 100 \
  --purchase-price 150.00 \
  --include-reasoning

# Analyse de l'évolution récente
finagent analyze stock AAPL \
  --timeframe 3mo \
  --depth full \
  --indicators all \
  --include-sentiment

# Recommandation stop-loss/take-profit
finagent decision risk-management AAPL \
  --position-size 100 \
  --entry-price 150.00 \
  --risk-tolerance moderate
```

### Diversification de Portefeuille

```bash
# Mon portefeuille est-il bien diversifié ?
finagent portfolio analyze "Mon Portefeuille" \
  --diversification-analysis \
  --sector-allocation \
  --correlation-matrix

# Suggestions d'amélioration
finagent portfolio optimize "Mon Portefeuille" \
  --objective diversification \
  --constraints min_positions=10,max_weight=0.2

# Ajout d'exposition internationale
finagent analyze compare VTI VXUS VWO \
  --criteria correlation,performance \
  --timeframe 5y
```

## 📈 5. Analyste Quantitatif - Recherche Avancée

### Analyse de Corrélations

```bash
#!/bin/bash
# correlation_analysis.sh

# Analyse des corrélations sectorielles
sectors=("XLK" "XLF" "XLV" "XLE" "XLI")

echo "🔍 Analyse de corrélations sectorielles"

# Générer les données pour chaque secteur
for sector in "${sectors[@]}"; do
  finagent analyze stock $sector \
    --timeframe 2y \
    --format json \
    --save-report "data/${sector}_2y.json"
done

# Analyse de corrélation croisée
finagent analyze correlation "${sectors[@]}" \
  --timeframe 2y \
  --rolling-window 60 \
  --save-report "correlation_analysis.json"
```

### Backtesting Avancé avec Monte Carlo

```bash
# Test de robustesse d'une stratégie
finagent strategy backtest "Ma Stratégie" \
  --monte-carlo-runs 1000 \
  --random-start-dates \
  --bootstrap-returns \
  --confidence-intervals 90,95,99

# Analyse des périodes de drawdown
finagent strategy analyze "Ma Stratégie" \
  --drawdown-analysis \
  --risk-metrics var,cvar,max_drawdown \
  --stress-test market_crashes
```

### Optimisation Multi-Objectifs

```bash
# Optimisation Pareto pour équilibrer rendement/risque
finagent strategy optimize "Multi-Asset Strategy" \
  --objectives return,risk,sharpe_ratio \
  --method pareto \
  --constraints \
    min_weight=0.05 \
    max_weight=0.3 \
    max_turnover=0.2

# Test de sensibilité des paramètres
finagent strategy sensitivity "Multi-Asset Strategy" \
  --parameters lookback,threshold,stop_loss \
  --ranges 10:30:5,0.03:0.1:0.01,0.05:0.2:0.05 \
  --metric sharpe_ratio
```

## 📅 6. Scripts d'Automatisation

### Surveillance Quotidienne Automatisée

```bash
#!/bin/bash
# surveillance_quotidienne.sh
# À lancer avec cron : 0 9 * * 1-5 /path/to/surveillance_quotidienne.sh

DATE=$(date +%Y%m%d)
REPORT_DIR="reports/daily/$DATE"
mkdir -p "$REPORT_DIR"

# Watchlist personnelle
WATCHLIST=("AAPL" "MSFT" "GOOGL" "AMZN" "TSLA" "NVDA" "META")

echo "🔍 Surveillance quotidienne - $DATE"

# Analyse rapide de chaque titre
for symbol in "${WATCHLIST[@]}"; do
  echo "Analyse de $symbol..."
  finagent analyze stock $symbol \
    --timeframe 1d \
    --indicators rsi,macd \
    --format json \
    --save-report "$REPORT_DIR/${symbol}.json"
  
  # Alerte si RSI extrême
  rsi=$(jq '.technical_indicators.rsi.current' "$REPORT_DIR/${symbol}.json")
  if (( $(echo "$rsi < 30" | bc -l) )); then
    echo "🚨 ALERTE: $symbol RSI oversold ($rsi)"
  elif (( $(echo "$rsi > 70" | bc -l) )); then
    echo "🚨 ALERTE: $symbol RSI overbought ($rsi)"
  fi
done

# Analyse de marché global
finagent analyze market \
  --format json \
  --save-report "$REPORT_DIR/market_overview.json"

echo "✅ Surveillance terminée - Rapports dans $REPORT_DIR"
```

### Rééquilibrage Automatique de Portefeuille

```bash
#!/bin/bash
# rebalancing_check.sh
# À lancer mensuellement

PORTFOLIO="Portefeuille Principal"
THRESHOLD=0.05  # 5% de déviation max

echo "⚖️ Vérification de rééquilibrage - $PORTFOLIO"

# Analyse de l'allocation actuelle
finagent portfolio show "$PORTFOLIO" \
  --allocation-analysis \
  --format json \
  --save-report "current_allocation.json"

# Vérification des déviations
finagent portfolio check-deviation "$PORTFOLIO" \
  --target-allocation config/target_allocation.json \
  --threshold $THRESHOLD

# Si rééquilibrage nécessaire, générer les ordres
if [ $? -eq 1 ]; then
  echo "📋 Rééquilibrage recommandé"
  finagent portfolio rebalance "$PORTFOLIO" \
    --target-allocation config/target_allocation.json \
    --generate-orders \
    --save-orders "rebalancing_orders_$(date +%Y%m%d).json"
else
  echo "✅ Portefeuille équilibré"
fi
```

### Reporting Hebdomadaire

```bash
#!/bin/bash
# weekly_report.sh

WEEK=$(date +%Y-W%U)
REPORT_FILE="reports/weekly_report_$WEEK.html"

echo "📊 Génération du rapport hebdomadaire"

# Début du rapport HTML
cat > "$REPORT_FILE" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>Rapport Hebdomadaire - Semaine $WEEK</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .positive { color: green; }
        .negative { color: red; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <h1>📊 Rapport Hebdomadaire - Semaine $WEEK</h1>
EOF

# Performance des portefeuilles
echo "<h2>💼 Performance des Portefeuilles</h2>" >> "$REPORT_FILE"
finagent portfolio list --format html >> "$REPORT_FILE"

# Analyses de la semaine
echo "<h2>📈 Analyses de la Semaine</h2>" >> "$REPORT_FILE"
ls reports/daily/ | tail -7 | while read day; do
  echo "<h3>$day</h3>" >> "$REPORT_FILE"
  echo "<ul>" >> "$REPORT_FILE"
  find "reports/daily/$day" -name "*.json" | while read file; do
    symbol=$(basename "$file" .json)
    change=$(jq '.price_change_percent' "$file")
    echo "<li>$symbol: $change%</li>" >> "$REPORT_FILE"
  done
  echo "</ul>" >> "$REPORT_FILE"
done

# Fin du rapport
cat >> "$REPORT_FILE" << EOF
    <hr>
    <p><em>Rapport généré automatiquement par FinAgent CLI</em></p>
</body>
</html>
EOF

echo "✅ Rapport généré: $REPORT_FILE"
```

## 🔧 Scripts de Maintenance

### Nettoyage et Optimisation

```bash
#!/bin/bash
# maintenance.sh

echo "🧹 Maintenance FinAgent"

# Nettoyage du cache ancien (> 7 jours)
finagent config cache clean --older-than 7d

# Archivage des anciens rapports
find reports/ -name "*.json" -mtime +30 -exec mv {} archive/ \;

# Vérification de l'intégrité de la configuration
finagent config validate

# Test de connectivité aux APIs
finagent config test-connection

# Sauvegarde de la configuration
finagent config backup "backups/config_$(date +%Y%m%d).json"

echo "✅ Maintenance terminée"
```

---

💡 **Note :** Ces exemples sont des templates que vous pouvez adapter selon vos besoins spécifiques. N'hésitez pas à les modifier et à expérimenter !