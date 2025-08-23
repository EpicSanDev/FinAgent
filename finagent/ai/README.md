# Module IA FinAgent

Ce module fournit une intelligence artificielle complète pour l'analyse financière, la prise de décision de trading, l'analyse de sentiment et l'interprétation de stratégies en utilisant Claude via OpenRouter.

## 🚀 Démarrage Rapide

### 1. Configuration

Configurez votre clé API OpenRouter :

```bash
export OPENROUTER_API_KEY=your_openrouter_api_key_here
```

### 2. Initialisation

```python
from finagent.ai import initialize_ai_system, get_ai_config

# Initialisation du système IA
await initialize_ai_system()
config = get_ai_config()

# Vérification du statut
from finagent.ai import get_service_status
status = get_service_status()
print(status)
```

## 📊 Services Disponibles

### Service d'Analyse Financière

```python
from finagent.ai import AnalysisService, FinancialAnalysisRequest
from finagent.ai.models.financial_analysis import AnalysisType

# Créer le service
analysis_service = AnalysisService(provider=config.provider)

# Requête d'analyse technique
request = FinancialAnalysisRequest(
    symbol="AAPL",
    analysis_type=AnalysisType.TECHNICAL,
    timeframe="1D",
    market_data={
        "price": 150.25,
        "volume": 50000000,
        "high": 152.00,
        "low": 149.50
    }
)

# Exécuter l'analyse
result = await analysis_service.analyze_market_data(request)
print(f"Tendance: {result.trend_direction}")
print(f"Confiance: {result.confidence}")
```

### Service de Décision de Trading

```python
from finagent.ai import DecisionService, TradingDecisionRequest
from finagent.ai.models.trading_decision import DecisionType

# Créer le service
decision_service = DecisionService(provider=config.provider)

# Requête de décision
request = TradingDecisionRequest(
    symbol="TSLA",
    current_price=Decimal("220.50"),
    portfolio_value=Decimal("100000"),
    risk_tolerance=0.15,
    market_context={
        "volatility": 0.25,
        "trend": "bullish",
        "volume_avg": 45000000
    }
)

# Prendre une décision
decision = await decision_service.make_trading_decision(request)
print(f"Action: {decision.action}")
print(f"Quantity: {decision.quantity}")
print(f"Confidence: {decision.confidence}")
```

### Service d'Analyse de Sentiment

```python
from finagent.ai import SentimentService

# Créer le service
sentiment_service = SentimentService(provider=config.provider)

# Analyser des nouvelles
news_data = [
    "Apple reports record quarterly earnings beating estimates",
    "Market uncertainty grows amid inflation concerns",
    "Tech stocks rally on positive AI developments"
]

sentiment = await sentiment_service.analyze_market_sentiment(
    symbol="AAPL",
    news_data=news_data,
    social_media_data=[]
)

print(f"Sentiment global: {sentiment.overall_sentiment}")
print(f"Score bullish: {sentiment.bullish_score}")
print(f"Score bearish: {sentiment.bearish_score}")
```

### Service de Stratégie

```python
from finagent.ai import StrategyService

# Créer le service
strategy_service = StrategyService(provider=config.provider)

# Interpréter une stratégie personnalisée
strategy_text = """
Acheter quand RSI < 30 et MACD croise à la hausse,
avec stop-loss à -5% et take-profit à +10%.
Utiliser 2% du portfolio maximum par position.
"""

interpretation = await strategy_service.interpret_strategy(
    strategy_description=strategy_text,
    target_symbols=["AAPL", "GOOGL", "MSFT"],
    risk_parameters={"max_drawdown": 0.1, "position_size": 0.02}
)

print(f"Stratégie: {interpretation.strategy_name}")
print(f"Signaux: {interpretation.entry_signals}")
print(f"Risques: {interpretation.risk_assessment}")
```

## 🧠 Système de Mémoire

### Mémoire des Conversations

```python
from finagent.ai.memory import ConversationMemoryManager

memory_manager = ConversationMemoryManager()

# Sauvegarder une conversation
await memory_manager.save_conversation(
    user_id="user123",
    messages=[
        {"role": "user", "content": "Analyse AAPL"},
        {"role": "assistant", "content": "AAPL montre une tendance haussière..."}
    ]
)

# Récupérer l'historique
history = await memory_manager.get_conversation_history("user123", limit=10)
```

### Mémoire des Décisions

```python
from finagent.ai.memory import DecisionMemoryManager

decision_memory = DecisionMemoryManager()

# Sauvegarder une décision
await decision_memory.save_decision(
    symbol="AAPL",
    decision_type="BUY",
    context={"price": 150.25, "reason": "Breakout technique"},
    confidence=0.85
)

# Analyser les performances
performance = await decision_memory.analyze_performance("AAPL")
print(f"Taux de réussite: {performance.success_rate}")
```

## 🔧 Configuration Avancée

### Modèles Claude Disponibles

```python
from finagent.ai.models.base import ModelType

# Modèles disponibles
models = [
    ModelType.CLAUDE_3_5_SONNET,  # Le plus performant
    ModelType.CLAUDE_3_SONNET,    # Équilibre qualité/vitesse
    ModelType.CLAUDE_3_HAIKU,     # Le plus rapide
    ModelType.CLAUDE_3_OPUS       # Le plus créatif
]
```

### Gestion des Prompts

```python
from finagent.ai.prompts import PromptManager, PromptType

prompt_manager = PromptManager()

# Utiliser un prompt personnalisé
custom_prompt = await prompt_manager.create_prompt(
    prompt_type=PromptType.CUSTOM,
    template="Analyse {symbol} en considérant {factors}",
    variables=["symbol", "factors"]
)

# Générer un prompt
generated = await prompt_manager.generate_prompt(
    PromptType.TECHNICAL_ANALYSIS,
    symbol="AAPL",
    timeframe="1H"
)
```

## 📈 Exemples d'Intégration

### Pipeline d'Analyse Complète

```python
async def analyze_and_decide(symbol: str):
    """Pipeline complet d'analyse et de décision."""
    
    # 1. Analyse technique
    analysis_request = FinancialAnalysisRequest(
        symbol=symbol,
        analysis_type=AnalysisType.TECHNICAL,
        timeframe="1D"
    )
    analysis = await analysis_service.analyze_market_data(analysis_request)
    
    # 2. Analyse de sentiment
    sentiment = await sentiment_service.analyze_market_sentiment(
        symbol=symbol,
        news_data=get_latest_news(symbol)  # Fonction externe
    )
    
    # 3. Décision de trading
    decision_request = TradingDecisionRequest(
        symbol=symbol,
        current_price=get_current_price(symbol),  # Fonction externe
        market_context={
            "technical_trend": analysis.trend_direction,
            "sentiment_score": sentiment.overall_sentiment,
            "confidence": analysis.confidence
        }
    )
    decision = await decision_service.make_trading_decision(decision_request)
    
    return {
        "analysis": analysis,
        "sentiment": sentiment,
        "decision": decision
    }

# Utilisation
result = await analyze_and_decide("AAPL")
```

### Stratégie Automatisée

```python
async def automated_strategy():
    """Stratégie automatisée basée sur l'IA."""
    
    watchlist = ["AAPL", "GOOGL", "MSFT", "TSLA"]
    
    for symbol in watchlist:
        try:
            # Analyse complète
            result = await analyze_and_decide(symbol)
            
            # Vérifier les signaux
            if result["decision"].action in ["BUY", "STRONG_BUY"]:
                confidence = result["decision"].confidence
                
                if confidence > 0.8:
                    print(f"🔥 Signal FORT {result['decision'].action} pour {symbol}")
                    print(f"   Confiance: {confidence:.2%}")
                    print(f"   Quantité: {result['decision'].quantity}")
                    
                    # Sauvegarder en mémoire
                    await decision_memory.save_decision(
                        symbol=symbol,
                        decision_type=result["decision"].action,
                        context=result["analysis"].__dict__,
                        confidence=confidence
                    )
            
        except Exception as e:
            print(f"❌ Erreur pour {symbol}: {e}")

# Exécution
await automated_strategy()
```

## 🛡️ Gestion des Erreurs

```python
from finagent.ai.models.base import AIError, RateLimitError, ProviderError

try:
    result = await analysis_service.analyze_market_data(request)
except RateLimitError as e:
    print(f"Limite de taux atteinte: {e.message}")
    # Attendre et réessayer
    await asyncio.sleep(60)
except ProviderError as e:
    print(f"Erreur du provider: {e.message}")
    # Basculer vers un modèle de fallback
except AIError as e:
    print(f"Erreur IA générale: {e.message}")
```

## 🧪 Tests

```bash
# Lancer les tests d'intégration
cd finagent && python tests/test_ai_integration.py

# Avec une clé API configurée
export OPENROUTER_API_KEY=your_key
cd finagent && python tests/test_ai_integration.py
```

## 🔧 Dépannage

### Problèmes Courants

1. **Clé API manquante**
   ```bash
   export OPENROUTER_API_KEY=your_key_here
   ```

2. **Erreurs d'import**
   - Vérifiez que toutes les dépendances sont installées
   - Relancez depuis le répertoire `finagent/`

3. **Erreurs de mémoire**
   - Vérifiez que SQLite est accessible
   - Les fichiers de DB sont créés automatiquement

### Configuration Debug

```python
import structlog
import logging

# Activer le logging détaillé
logging.basicConfig(level=logging.DEBUG)
structlog.configure(
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)
```

## 📚 Architecture

Le module IA suit une architecture en couches :

- **Modèles** : Définitions des structures de données
- **Providers** : Intégration avec Claude via OpenRouter  
- **Services** : Logique métier pour chaque domaine
- **Prompts** : Gestion centralisée des templates
- **Mémoire** : Persistance et apprentissage

Chaque couche est découplée et testable indépendamment.