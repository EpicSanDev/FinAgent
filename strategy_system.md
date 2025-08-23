# Système de Stratégies Configurables - Agent IA Financier

## Vue d'Ensemble

Le système de stratégies permet aux traders particuliers de définir leurs propres règles d'analyse et de prise de décision de manière flexible et intuitive, sans programmation.

## Architecture du Système de Stratégies

### 1. Composants Principaux

```
┌─────────────────────────────────────────────────────────┐
│                Strategy Configuration                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ YAML/JSON   │  │ Templates   │  │ Validation  │     │
│  │ Configs     │  │ Library     │  │ Engine      │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                Strategy Engine                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ Parser      │  │ Executor    │  │ Evaluator   │     │
│  │ Engine      │  │ Engine      │  │ Engine      │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                Strategy Types                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ Technical   │  │ Fundamental │  │ Sentiment   │     │
│  │ Analysis    │  │ Analysis    │  │ Analysis    │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
```

### 2. Format de Configuration YAML

#### Structure Générale
```yaml
# Configuration générale de la stratégie
strategy:
  name: "Ma Stratégie Momentum"
  version: "1.0"
  author: "Trader123"
  description: "Stratégie basée sur l'analyse momentum avec confirmation RSI"
  
  # Type de stratégie
  type: "technical"
  
  # Paramètres généraux
  settings:
    risk_tolerance: "medium"  # low, medium, high
    time_horizon: "short"     # short, medium, long
    max_positions: 5
    position_size: 0.1        # 10% du capital par position
    
  # Univers d'investissement
  universe:
    watchlist: ["AAPL", "MSFT", "GOOGL", "NVDA", "TSLA"]
    sectors: ["technology", "healthcare"]
    market_cap: "large"       # small, medium, large
    
  # Critères d'analyse
  analysis:
    # Indicateurs techniques
    technical:
      - type: "rsi"
        period: 14
        oversold: 30
        overbought: 70
        weight: 0.3
        
      - type: "moving_average"
        short_period: 20
        long_period: 50
        signal: "crossover"
        weight: 0.4
        
      - type: "volume"
        analysis: "surge"
        threshold: 1.5
        weight: 0.2
        
    # Indicateurs fondamentaux (optionnel)
    fundamental:
      - type: "pe_ratio"
        max_value: 25
        weight: 0.1
        
    # Analyse sentiment (optionnel)  
    sentiment:
      - type: "news_sentiment"
        threshold: 0.6
        weight: 0.1
        
  # Règles de décision
  rules:
    # Conditions d'achat
    buy_conditions:
      operator: "AND"  # AND, OR
      conditions:
        - indicator: "rsi"
          condition: "below"
          value: 40
          
        - indicator: "moving_average"
          condition: "crossover_up"
          
        - indicator: "volume"
          condition: "above_average"
          multiplier: 1.5
          
    # Conditions de vente
    sell_conditions:
      operator: "OR"
      conditions:
        - indicator: "rsi"
          condition: "above"
          value: 70
          
        - type: "stop_loss"
          percentage: 5
          
        - type: "take_profit"
          percentage: 15
          
    # Filtres et validations
    filters:
      - type: "market_condition"
        condition: "trending"  # trending, ranging, volatile
        
      - type: "liquidity"
        min_volume: 1000000
        
  # Gestion des risques
  risk_management:
    position_sizing:
      method: "fixed_percentage"  # fixed_percentage, volatility_based, kelly
      value: 0.1
      
    stop_loss:
      type: "percentage"  # percentage, atr_based, technical
      value: 5
      
    take_profit:
      type: "percentage"
      value: 15
      
    max_drawdown: 10
    
  # Backtesting et validation
  backtesting:
    start_date: "2023-01-01"
    end_date: "2024-01-01"
    initial_capital: 100000
    commission: 0.001
    
  # Notifications et alertes
  alerts:
    buy_signals: true
    sell_signals: true
    risk_warnings: true
    performance_updates: true
```

### 3. Types de Stratégies Supportées

#### A. Stratégies Techniques
```yaml
strategy:
  type: "technical"
  analysis:
    technical:
      # Moyennes mobiles
      - type: "sma"
        periods: [20, 50, 200]
        
      - type: "ema"  
        periods: [12, 26]
        
      # Oscillateurs
      - type: "rsi"
        period: 14
        
      - type: "stochastic"
        k_period: 14
        d_period: 3
        
      - type: "macd"
        fast: 12
        slow: 26
        signal: 9
        
      # Support/Résistance
      - type: "bollinger_bands"
        period: 20
        std_dev: 2
        
      - type: "fibonacci_retracement"
        levels: [0.236, 0.382, 0.618]
        
      # Volume
      - type: "volume_profile"
        lookback: 20
        
      - type: "on_balance_volume"
```

#### B. Stratégies Fondamentales
```yaml
strategy:
  type: "fundamental"
  analysis:
    fundamental:
      # Ratios de valorisation
      - type: "pe_ratio"
        range: [10, 20]
        
      - type: "peg_ratio"
        max_value: 1.5
        
      - type: "price_to_book"
        max_value: 3
        
      # Croissance
      - type: "revenue_growth"
        min_yearly: 0.1
        min_quarterly: 0.05
        
      - type: "earnings_growth"
        min_yearly: 0.15
        
      # Santé financière
      - type: "debt_to_equity"
        max_value: 0.5
        
      - type: "current_ratio"
        min_value: 1.5
        
      - type: "roe"
        min_value: 0.15
```

#### C. Stratégies Sentiment
```yaml
strategy:
  type: "sentiment"
  analysis:
    sentiment:
      # Actualités
      - type: "news_sentiment"
        sources: ["reuters", "bloomberg", "yahoo"]
        threshold: 0.6
        
      # Réseaux sociaux
      - type: "social_sentiment"
        platforms: ["twitter", "reddit"]
        threshold: 0.7
        
      # Indicateurs de marché
      - type: "vix"
        threshold: 25
        
      - type: "put_call_ratio"
        threshold: 1.1
```

#### D. Stratégies Hybrides
```yaml
strategy:
  type: "hybrid"
  analysis:
    technical:
      - type: "rsi"
        period: 14
        weight: 0.4
        
    fundamental:
      - type: "pe_ratio"
        max_value: 20
        weight: 0.4
        
    sentiment:
      - type: "news_sentiment"
        threshold: 0.6
        weight: 0.2
        
  rules:
    buy_conditions:
      operator: "AND"
      min_score: 0.7  # Score pondéré minimum
```

### 4. Templates Prédéfinis

#### Template 1: Momentum Simple
```yaml
strategy:
  name: "Momentum Simple"
  template: "momentum_basic"
  
  parameters:
    rsi_period: 14
    rsi_oversold: 30
    rsi_overbought: 70
    ma_short: 20
    ma_long: 50
    volume_threshold: 1.5
    
  customizable:
    - "rsi_period"
    - "rsi_oversold" 
    - "rsi_overbought"
    - "volume_threshold"
```

#### Template 2: Value Investing
```yaml
strategy:
  name: "Value Investing"
  template: "value_basic"
  
  parameters:
    max_pe: 15
    max_pb: 2
    min_roe: 0.15
    min_current_ratio: 1.5
    max_debt_equity: 0.3
    
  customizable:
    - "max_pe"
    - "max_pb"
    - "min_roe"
```

#### Template 3: Breakout Strategy
```yaml
strategy:
  name: "Breakout"
  template: "breakout_basic"
  
  parameters:
    lookback_period: 20
    volume_surge: 2.0
    breakout_threshold: 0.02
    stop_loss: 0.05
    take_profit: 0.15
```

### 5. Système de Validation

#### Validation Syntaxique
```python
class StrategyValidator:
    """Validateur de configuration de stratégie"""
    
    def validate_structure(self, config: dict) -> ValidationResult:
        """Valide la structure de base"""
        
    def validate_parameters(self, config: dict) -> ValidationResult:
        """Valide les paramètres et leurs valeurs"""
        
    def validate_logic(self, config: dict) -> ValidationResult:
        """Valide la logique des règles"""
        
    def validate_risk_parameters(self, config: dict) -> ValidationResult:
        """Valide les paramètres de risque"""
```

#### Règles de Validation
```yaml
validation_rules:
  # Paramètres obligatoires
  required_fields:
    - "strategy.name"
    - "strategy.type"
    - "strategy.rules.buy_conditions"
    - "strategy.rules.sell_conditions"
    
  # Plages de valeurs
  parameter_ranges:
    rsi_period: [2, 50]
    rsi_oversold: [10, 40]
    rsi_overbought: [60, 90]
    position_size: [0.01, 0.5]
    stop_loss: [0.01, 0.2]
    
  # Cohérence logique
  logic_checks:
    - "rsi_oversold < rsi_overbought"
    - "stop_loss < take_profit"
    - "position_size * max_positions <= 1.0"
```

### 6. Interface CLI pour Stratégies

#### Commandes CLI
```bash
# Créer une nouvelle stratégie
finagent strategy create --template momentum --name "Ma Stratégie"

# Lister les stratégies disponibles
finagent strategy list

# Valider une stratégie
finagent strategy validate --file my_strategy.yaml

# Backtester une stratégie
finagent strategy backtest --file my_strategy.yaml --period 1y

# Appliquer une stratégie en mode simulation
finagent strategy simulate --file my_strategy.yaml --duration 30d

# Déployer une stratégie en mode live
finagent strategy deploy --file my_strategy.yaml
```

#### Interface Interactive
```bash
# Mode interactif pour création de stratégie
finagent strategy create --interactive

# Questions guidées:
# 1. Quel type de stratégie ? (technical/fundamental/sentiment/hybrid)
# 2. Quel est votre horizon d'investissement ? (court/moyen/long terme)
# 3. Quelle est votre tolérance au risque ? (faible/moyenne/élevée)
# 4. Quels indicateurs souhaitez-vous utiliser ?
# 5. Définir les seuils d'achat/vente...
```

### 7. Exécution et Monitoring

#### Workflow d'Exécution
```
1. Chargement de la stratégie
2. Validation de la configuration
3. Récupération des données de marché
4. Calcul des indicateurs
5. Évaluation des conditions
6. Génération des signaux
7. Application de la gestion des risques
8. Exécution des ordres (simulation/réel)
9. Logging et monitoring
```

#### Métriques de Performance
```yaml
performance_metrics:
  # Rendement
  total_return: 15.5
  annualized_return: 12.3
  benchmark_return: 8.7
  alpha: 3.6
  
  # Risque
  volatility: 18.2
  max_drawdown: 8.5
  sharpe_ratio: 0.87
  sortino_ratio: 1.15
  
  # Trading
  win_rate: 0.65
  avg_win: 8.2
  avg_loss: -4.1
  profit_factor: 1.85
  
  # Activité
  total_trades: 45
  avg_holding_period: 12
  turnover_rate: 2.3
```

### 8. Système de Backtesting

#### Configuration Backtest
```yaml
backtest:
  strategy_file: "momentum_strategy.yaml"
  
  # Période de test
  start_date: "2023-01-01"
  end_date: "2024-01-01"
  
  # Paramètres de simulation
  initial_capital: 100000
  commission: 0.001
  slippage: 0.0005
  
  # Benchmark
  benchmark: "SPY"
  
  # Options avancées
  options:
    reinvest_dividends: true
    adjust_for_splits: true
    exclude_penny_stocks: true
    min_price: 5.0
    
  # Rapports
  reports:
    - "performance_summary"
    - "trade_analysis"
    - "risk_metrics"
    - "drawdown_analysis"
    - "sector_allocation"
```

#### Résultats Backtest
```
=============== BACKTEST RESULTS ===============
Strategy: Momentum Simple
Period: 2023-01-01 to 2024-01-01
Initial Capital: $100,000

PERFORMANCE SUMMARY:
Final Value: $115,500
Total Return: 15.5%
Annualized Return: 15.5%
Benchmark Return (SPY): 8.7%
Alpha: 6.8%

RISK METRICS:
Volatility: 18.2%
Max Drawdown: -8.5%
Sharpe Ratio: 0.87
Calmar Ratio: 1.83

TRADE ANALYSIS:
Total Trades: 45
Winning Trades: 29 (64.4%)
Average Win: 8.2%
Average Loss: -4.1%
Profit Factor: 1.85

TOP PERFORMERS:
1. NVDA: +28.5% (3 trades)
2. AAPL: +12.3% (5 trades)
3. MSFT: +8.7% (4 trades)
```

### 9. Gestion des Erreurs et Edge Cases

#### Validation Runtime
```python
class RuntimeValidator:
    """Validation pendant l'exécution"""
    
    def validate_market_data(self, data):
        """Vérifie la qualité des données"""
        
    def validate_signals(self, signals):
        """Vérifie la cohérence des signaux"""
        
    def validate_risk_limits(self, portfolio):
        """Vérifie les limites de risque"""
```

#### Gestion des Cas Particuliers
- Données manquantes ou erronées
- Marchés fermés ou volatils
- Conditions de liquidité insuffisante
- Dépassement des limites de risque
- Conflits entre signaux
- Erreurs de connectivité API

### 10. Évolution et Maintenance

#### Versioning des Stratégies
```yaml
strategy:
  name: "Ma Stratégie"
  version: "2.1"
  
  changelog:
    - version: "2.1"
      date: "2024-01-15"
      changes:
        - "Ajout du filtre de volume"
        - "Modification du seuil RSI"
        
    - version: "2.0"
      date: "2024-01-01"
      changes:
        - "Refonte complète des règles"
        - "Ajout gestion des risques"
```

#### Migration et Compatibilité
- Support des versions antérieures
- Migration automatique des configurations
- Avertissements de dépréciation
- Documentation des changements breaking