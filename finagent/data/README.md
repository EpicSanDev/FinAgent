# Intégration OpenBB - Documentation Complète

Cette documentation couvre l'intégration complète avec OpenBB pour l'accès aux données financières dans le projet FinAgent.

## Vue d'ensemble

L'intégration OpenBB fournit une couche d'abstraction robuste pour accéder aux données financières avec :

- **Cache multi-niveaux** pour optimiser les performances
- **Validation automatique** des données et paramètres
- **Services de haut niveau** pour données de marché, indicateurs techniques et nouvelles
- **Gestion d'erreurs** et retry automatique
- **Analyse de sentiment** intégrée pour les nouvelles financières

## Architecture

```
finagent/data/
├── models/              # Modèles de données Pydantic
│   ├── base.py         # Classes de base et enums
│   ├── market_data.py  # OHLCV, quotes, collections
│   ├── technical_indicators.py  # Indicateurs techniques
│   └── news.py         # Nouvelles et sentiment
├── validators/         # Validation des données
│   └── base.py        # Validateurs principaux
├── cache/             # Système de cache
│   ├── memory_cache.py    # Cache mémoire L1
│   ├── cache_manager.py   # Gestionnaire multi-niveaux
│   └── cache_keys.py      # Clés et tags de cache
├── providers/         # Providers de données
│   └── openbb_provider.py # Interface OpenBB principale
├── services/          # Services de haut niveau
│   ├── market_data_service.py      # Données de marché
│   ├── technical_indicators_service.py  # Indicateurs techniques
│   └── news_service.py             # Nouvelles et sentiment
└── integration_test.py # Test d'intégration complet
```

## Utilisation Rapide

### Configuration de base

```python
from finagent.data import FinancialDataManager

# Initialisation avec cache activé
manager = FinancialDataManager(enable_cache=True)

# Analyse complète d'un symbole
analysis = await manager.comprehensive_analysis("AAPL")

# Analyse de portefeuille
portfolio = await manager.portfolio_analysis(["AAPL", "GOOGL", "MSFT"])

# Aperçu du marché
market_overview = await manager.market_overview()
```

### Utilisation des services individuels

```python
from finagent.data import (
    OpenBBProvider, MarketDataService, 
    TechnicalIndicatorsService, NewsService,
    MultiLevelCacheManager, MemoryCache
)

# Configuration du cache
cache = MemoryCache(max_size=1000)
cache_manager = MultiLevelCacheManager(l1_cache=cache)

# Initialisation des services
provider = OpenBBProvider(cache_manager=cache_manager)
market_service = MarketDataService(provider, cache_manager)
indicators_service = TechnicalIndicatorsService(provider, cache_manager)
news_service = NewsService(provider, cache_manager)
```

## Guides d'utilisation détaillés

### 1. Données de Marché

#### Données historiques

```python
from finagent.data import MarketDataService, TimeFrame
from datetime import datetime, timedelta

# Récupération de données historiques
end_date = datetime.now()
start_date = end_date - timedelta(days=30)

market_data = await market_service.get_historical_data(
    symbol="AAPL",
    timeframe=TimeFrame.DAY_1,
    start_date=start_date,
    end_date=end_date
)

print(f"Récupéré {len(market_data.data)} points de données")
for point in market_data.data[-5:]:  # 5 derniers points
    print(f"{point.timestamp}: O={point.open} H={point.high} L={point.low} C={point.close}")
```

#### Cotations en temps réel

```python
# Quote en temps réel
quote = await market_service.get_quote("AAPL")
print(f"AAPL: Bid={quote.bid} Ask={quote.ask} Last={quote.last_price}")

# Quotes multiples
symbols = ["AAPL", "GOOGL", "MSFT"]
quotes = await market_service.get_multiple_quotes(symbols)
for symbol, quote in quotes.items():
    print(f"{symbol}: {quote.last_price}")
```

#### Conversion DataFrame

```python
# Conversion en DataFrame pandas pour analyse
df = market_data.to_dataframe()
print(df.head())

# Calculs personnalisés
df['sma_20'] = df['close'].rolling(window=20).mean()
df['volatility'] = df['close'].pct_change().rolling(window=20).std()
```

### 2. Indicateurs Techniques

#### Indicateurs simples

```python
from finagent.data import TechnicalIndicatorsService, IndicatorType

# Moyennes mobiles
sma_20 = await indicators_service.calculate_moving_average(
    symbol="AAPL",
    timeframe=TimeFrame.DAY_1,
    ma_type=IndicatorType.SMA,
    period=20
)
print(f"SMA(20): {sma_20.value}")

# RSI
rsi = await indicators_service.calculate_rsi(
    symbol="AAPL",
    timeframe=TimeFrame.DAY_1,
    period=14
)
print(f"RSI(14): {rsi.value} - Signal: {rsi.signal}")
```

#### Indicateurs complexes

```python
# MACD
macd = await indicators_service.calculate_macd(
    symbol="AAPL",
    timeframe=TimeFrame.DAY_1,
    fast_period=12,
    slow_period=26,
    signal_period=9
)
print(f"MACD: {macd.macd_line:.4f}")
print(f"Signal: {macd.signal_line:.4f}")
print(f"Histogram: {macd.histogram:.4f}")
print(f"Bullish crossover: {macd.is_bullish_crossover}")

# Bollinger Bands
bollinger = await indicators_service.calculate_bollinger_bands(
    symbol="AAPL",
    timeframe=TimeFrame.DAY_1,
    period=20,
    std_multiplier=2.0
)
print(f"Bollinger Bands:")
print(f"  Upper: {bollinger.upper_band}")
print(f"  Middle: {bollinger.middle_band}")
print(f"  Lower: {bollinger.lower_band}")
print(f"  Bandwidth: {bollinger.bandwidth_percent:.1f}%")
```

#### Collection d'indicateurs

```python
# Calcul de multiples indicateurs en parallèle
indicators_config = [
    {'type': 'sma', 'period': 20},
    {'type': 'sma', 'period': 50},
    {'type': 'ema', 'period': 12},
    {'type': 'rsi', 'period': 14},
    {'type': 'macd', 'fast': 12, 'slow': 26, 'signal': 9},
    {'type': 'bollinger', 'period': 20, 'std_multiplier': 2.0},
    {'type': 'stochastic', 'k_period': 14, 'd_period': 3}
]

collection = await indicators_service.calculate_indicator_collection(
    symbol="AAPL",
    timeframe=TimeFrame.DAY_1,
    indicators=indicators_config
)

# Analyse des signaux
summary = collection.generate_summary()
print(f"Résumé des signaux pour {summary['symbol']}:")
for indicator, signal in summary['signals'].items():
    print(f"  {indicator}: {signal}")
```

### 3. Nouvelles et Sentiment

#### Nouvelles d'entreprise

```python
from finagent.data import NewsService
from datetime import datetime, timedelta

# Nouvelles récentes d'une entreprise
news_collection = await news_service.get_company_news(
    symbol="AAPL",
    limit=50,
    start_date=datetime.now() - timedelta(days=7),
    include_sentiment=True
)

print(f"Récupéré {len(news_collection.articles)} articles")

# Analyse des articles récents
recent_articles = news_collection.get_recent_articles(hours=24)
high_impact = news_collection.get_high_impact_articles()

print(f"Articles récents (24h): {len(recent_articles)}")
print(f"Articles fort impact: {len(high_impact)}")

# Affichage des articles
for article in recent_articles[:5]:
    print(f"\n{article.title}")
    print(f"Source: {article.source.name}")
    print(f"Sentiment: {article.sentiment} (Score: {article.sentiment_score:.2f})")
    print(f"Impact: {article.impact_score:.2f}")
```

#### Analyse de sentiment

```python
# Analyse de sentiment agrégée
sentiment_analysis = await news_service.analyze_sentiment_for_symbol(
    symbol="AAPL",
    hours=24,
    min_articles=3
)

if sentiment_analysis:
    print(f"Analyse sentiment AAPL (24h):")
    print(f"  Articles analysés: {sentiment_analysis.total_articles}")
    print(f"  Sentiment moyen: {sentiment_analysis.average_sentiment:.2f}")
    print(f"  Sentiment pondéré: {sentiment_analysis.weighted_sentiment:.2f}")
    print(f"  Sentiment global: {sentiment_analysis.overall_sentiment}")
    print(f"  Confiance: {sentiment_analysis.confidence_score:.2f}")
    print(f"  Sujets tendance: {', '.join(sentiment_analysis.trending_topics[:3])}")
```

#### Nouvelles multi-symboles

```python
# Nouvelles pour plusieurs symboles
symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]
multi_news = await news_service.get_multi_symbol_news(
    symbols=symbols,
    limit_per_symbol=20,
    include_sentiment=True
)

print(f"Total articles: {len(multi_news.articles)}")
print(f"Symboles couverts: {[s.symbol for s in multi_news.symbols]}")

# Analyse sentiment par symbole
for symbol in symbols:
    symbol_sentiment = await news_service.analyze_sentiment_for_symbol(symbol, hours=24)
    if symbol_sentiment:
        print(f"{symbol}: {symbol_sentiment.overall_sentiment} ({symbol_sentiment.total_articles} articles)")
```

#### Actions tendance

```python
# Identification des actions tendance
trending = await news_service.get_trending_stocks(
    hours=24,
    min_mentions=5,
    limit=10
)

print("Actions tendance (24h):")
for stock in trending:
    print(f"  {stock['symbol']}: {stock['mentions']} mentions, "
          f"sentiment {stock['sentiment_label']} ({stock['avg_sentiment']:.2f}), "
          f"score tendance {stock['trend_score']:.2f}")
```

### 4. Recherche et Filtrage

#### Recherche de nouvelles

```python
# Recherche par mots-clés
search_results = await news_service.search_news(
    query="earnings beat",
    limit=50,
    symbols=["AAPL", "GOOGL", "MSFT"],  # Optionnel
    categories=[NewsCategory.EARNINGS, NewsCategory.ANALYST]  # Optionnel
)

print(f"Résultats de recherche: {len(search_results.articles)} articles")
for article in search_results.articles[:3]:
    print(f"- {article.title} ({article.category})")
```

#### Nouvelles du marché général

```python
# Aperçu général du marché
market_news = await news_service.get_market_news(
    limit=100,
    categories=[NewsCategory.MARKET, NewsCategory.EARNINGS],
    include_sentiment=True
)

print(f"Nouvelles du marché: {len(market_news.articles)} articles")

# Analyse sentiment global du marché
recent_market = market_news.get_recent_articles(hours=6)
sentiments = [a.sentiment_score for a in recent_market if a.sentiment_score is not None]

if sentiments:
    avg_sentiment = sum(sentiments) / len(sentiments)
    print(f"Sentiment marché (6h): {avg_sentiment:.2f}")
```

## Gestion du Cache

### Configuration du cache

```python
from finagent.data import MemoryCache, MultiLevelCacheManager, CacheStrategy

# Cache mémoire personnalisé
memory_cache = MemoryCache(
    max_size=2000,        # Taille max
    default_ttl=3600,     # TTL par défaut (1h)
    eviction_policy="LRU" # Politique d'éviction
)

# Gestionnaire multi-niveaux
cache_manager = MultiLevelCacheManager(
    l1_cache=memory_cache,
    strategy=CacheStrategy.READ_THROUGH
)

# Utilisation avec les services
provider = OpenBBProvider(cache_manager=cache_manager)
```

### Métriques de cache

```python
# Statistiques du cache
cache_stats = memory_cache.get_stats()
print(f"Cache - Hits: {cache_stats['hits']}, Misses: {cache_stats['misses']}")
print(f"Hit rate: {cache_stats['hit_rate']:.1%}")
print(f"Taille actuelle: {cache_stats['current_size']}/{cache_stats['max_size']}")

# Nettoyage manuel
memory_cache.clear()
```

### Tags et invalidation

```python
from finagent.data import CacheTags

# Invalidation par tags
await cache_manager.invalidate_by_tag(CacheTags.symbol("AAPL"))
await cache_manager.invalidate_by_tag(CacheTags.NEWS)
await cache_manager.invalidate_by_tag(CacheTags.TECHNICAL_INDICATORS)
```

## Gestion d'Erreurs

### Types d'erreurs

```python
from finagent.data import (
    ValidationError, OpenBBError, RateLimitError, 
    DataNotFoundError, IndicatorCalculationError,
    InsufficientDataError, NewsAnalysisError
)

try:
    # Opération sur les données
    data = await market_service.get_historical_data("INVALID_SYMBOL")
    
except ValidationError as e:
    print(f"Erreur de validation: {e}")
    
except RateLimitError as e:
    print(f"Limite de taux atteinte: {e}")
    print(f"Retry après: {e.retry_after} secondes")
    
except DataNotFoundError as e:
    print(f"Données non trouvées: {e}")
    
except OpenBBError as e:
    print(f"Erreur OpenBB: {e}")
    
except Exception as e:
    print(f"Erreur inattendue: {e}")
```

### Retry automatique

Le système inclut un retry automatique pour les erreurs temporaires :

- **Erreurs réseau** : 3 tentatives avec backoff exponentiel
- **Rate limiting** : Attente automatique selon les headers
- **Erreurs de timeout** : Retry avec délai croissant

## Monitoring et Health Check

### Statut de santé

```python
# Vérification du système complet
health = await manager.get_system_health()
print(f"Statut général: {health['overall_status']}")

for service_name, service_health in health['services'].items():
    print(f"{service_name}: {service_health['status']}")
    if 'metrics' in service_health:
        metrics = service_health['metrics']
        print(f"  - Cache hit rate: {metrics.get('hit_rate', 0):.1%}")
        print(f"  - Erreurs: {metrics.get('errors_count', 0)}")
```

### Métriques des services

```python
# Métriques détaillées par service
market_health = await market_service.get_health_status()
indicators_health = await indicators_service.get_health_status()
news_health = await news_service.get_health_status()

print("=== MÉTRIQUES DÉTAILLÉES ===")
for service, health in [
    ("Market Data", market_health),
    ("Technical Indicators", indicators_health),
    ("News", news_health)
]:
    print(f"\n{service}:")
    metrics = health.get('metrics', {})
    for key, value in metrics.items():
        print(f"  {key}: {value}")
```

## Exemples d'Analyse Complète

### Analyse technique complète

```python
async def complete_technical_analysis(symbol: str):
    """Analyse technique complète d'un symbole."""
    
    # 1. Données de marché
    market_data = await market_service.get_historical_data(
        symbol=symbol,
        timeframe=TimeFrame.DAY_1,
        lookback_days=100
    )
    
    # 2. Indicateurs multiples
    indicators = await indicators_service.calculate_indicator_collection(
        symbol=symbol,
        timeframe=TimeFrame.DAY_1,
        indicators=[
            {'type': 'sma', 'period': 20},
            {'type': 'sma', 'period': 50},
            {'type': 'sma', 'period': 200},
            {'type': 'rsi', 'period': 14},
            {'type': 'macd'},
            {'type': 'bollinger', 'period': 20},
            {'type': 'stochastic'}
        ]
    )
    
    # 3. Analyse des signaux
    current_price = float(market_data.data[-1].close)
    
    signals = {
        'price': current_price,
        'trend': 'NEUTRE',
        'momentum': 'NEUTRE',
        'support_resistance': {}
    }
    
    # Analyse de tendance (moyennes mobiles)
    sma_20 = indicators.get_indicator('SMA_20')
    sma_50 = indicators.get_indicator('SMA_50')
    sma_200 = indicators.get_indicator('SMA_200')
    
    if sma_20 and sma_50 and sma_200:
        if current_price > float(sma_20.value) > float(sma_50.value) > float(sma_200.value):
            signals['trend'] = 'TRÈS_HAUSSIER'
        elif current_price > float(sma_20.value) > float(sma_50.value):
            signals['trend'] = 'HAUSSIER'
        elif current_price < float(sma_20.value) < float(sma_50.value):
            signals['trend'] = 'BAISSIER'
    
    # Momentum (RSI + Stochastic)
    rsi = indicators.get_indicator('RSI_14')
    stoch = indicators.get_indicator('STOCHASTIC')
    
    if rsi and stoch:
        if rsi.is_oversold and stoch.is_oversold:
            signals['momentum'] = 'SURVENDU_FORT'
        elif rsi.is_overbought and stoch.is_overbought:
            signals['momentum'] = 'SURACHETÉ_FORT'
        elif rsi.is_oversold or stoch.is_oversold:
            signals['momentum'] = 'SURVENDU'
        elif rsi.is_overbought or stoch.is_overbought:
            signals['momentum'] = 'SURACHETÉ'
    
    # Support/Résistance (Bollinger Bands)
    bollinger = indicators.get_indicator('BOLLINGER')
    if bollinger:
        signals['support_resistance'] = {
            'support': float(bollinger.lower_band),
            'resistance': float(bollinger.upper_band),
            'middle': float(bollinger.middle_band),
            'squeeze': bollinger.get_squeeze_level()
        }
    
    return signals

# Utilisation
analysis = await complete_technical_analysis("AAPL")
print(f"Analyse AAPL: Tendance={analysis['trend']}, Momentum={analysis['momentum']}")
```

### Dashboard de marché

```python
async def create_market_dashboard():
    """Crée un dashboard complet du marché."""
    
    # Indices principaux
    indices = ['SPY', 'QQQ', 'IWM', 'VIX']
    indices_data = {}
    
    for index in indices:
        try:
            quote = await market_service.get_quote(index)
            rsi = await indicators_service.calculate_rsi(index, TimeFrame.DAY_1)
            
            indices_data[index] = {
                'price': float(quote.last_price) if quote.last_price else None,
                'rsi': float(rsi.value) if rsi else None,
                'rsi_signal': rsi.signal if rsi else None
            }
        except Exception as e:
            print(f"Erreur pour {index}: {e}")
    
    # Actions tendance
    trending = await news_service.get_trending_stocks(hours=24, limit=10)
    
    # Sentiment général du marché
    market_news = await news_service.get_market_news(limit=50)
    recent_articles = market_news.get_recent_articles(hours=6)
    
    sentiments = [a.sentiment_score for a in recent_articles if a.sentiment_score]
    market_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
    
    dashboard = {
        'timestamp': datetime.now(),
        'indices': indices_data,
        'trending_stocks': trending[:5],
        'market_sentiment': {
            'score': market_sentiment,
            'articles_count': len(sentiments),
            'label': 'POSITIF' if market_sentiment > 0.2 else 'NÉGATIF' if market_sentiment < -0.2 else 'NEUTRE'
        }
    }
    
    return dashboard

# Utilisation
dashboard = await create_market_dashboard()
print("=== DASHBOARD MARCHÉ ===")
print(f"Sentiment: {dashboard['market_sentiment']['label']} ({dashboard['market_sentiment']['score']:.2f})")
print("\nIndices:")
for name, data in dashboard['indices'].items():
    print(f"  {name}: {data['price']} (RSI: {data['rsi']:.1f} - {data['rsi_signal']})")
print("\nActions tendance:")
for stock in dashboard['trending_stocks']:
    print(f"  {stock['symbol']}: {stock['mentions']} mentions, {stock['sentiment_label']}")
```

## Bonnes Pratiques

### 1. Gestion des ressources

```python
# Toujours fermer les services
try:
    manager = FinancialDataManager()
    # ... utilisation
finally:
    await manager.close()

# Ou utiliser un context manager personnalisé
from contextlib import asynccontextmanager

@asynccontextmanager
async def financial_data_context():
    manager = FinancialDataManager()
    try:
        yield manager
    finally:
        await manager.close()

# Utilisation
async with financial_data_context() as manager:
    analysis = await manager.comprehensive_analysis("AAPL")
```

### 2. Gestion des erreurs en production

```python
import logging
from finagent.data import ValidationError, OpenBBError

logger = logging.getLogger(__name__)

async def safe_data_retrieval(symbol: str):
    """Récupération sécurisée de données avec gestion d'erreurs."""
    try:
        return await market_service.get_historical_data(symbol)
    
    except ValidationError as e:
        logger.warning(f"Symbole invalide {symbol}: {e}")
        return None
    
    except RateLimitError as e:
        logger.warning(f"Rate limit atteint: {e}")
        # Planifier un retry plus tard
        return None
    
    except DataNotFoundError as e:
        logger.info(f"Pas de données pour {symbol}: {e}")
        return None
    
    except OpenBBError as e:
        logger.error(f"Erreur OpenBB pour {symbol}: {e}")
        # Notifier les administrateurs
        return None
    
    except Exception as e:
        logger.error(f"Erreur inattendue pour {symbol}: {e}", exc_info=True)
        return None
```

### 3. Configuration pour différents environnements

```python
# config.py
import os
from finagent.data import DEFAULT_CACHE_SIZE, DEFAULT_CACHE_TTL

class DataConfig:
    """Configuration pour les données financières."""
    
    # Cache
    CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() == "true"
    CACHE_SIZE = int(os.getenv("CACHE_SIZE", DEFAULT_CACHE_SIZE))
    CACHE_TTL = int(os.getenv("CACHE_TTL", DEFAULT_CACHE_TTL))
    
    # OpenBB
    OPENBB_RATE_LIMIT = int(os.getenv("OPENBB_RATE_LIMIT", "10"))  # req/sec
    OPENBB_TIMEOUT = int(os.getenv("OPENBB_TIMEOUT", "30"))  # secondes
    
    # Retry
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_DELAY = int(os.getenv("RETRY_DELAY", "1"))  # secondes

# Utilisation
def create_production_manager():
    """Crée un manager configuré pour la production."""
    return FinancialDataManager(
        enable_cache=DataConfig.CACHE_ENABLED,
        cache_size=DataConfig.CACHE_SIZE,
        cache_ttl=DataConfig.CACHE_TTL
    )
```

## Performance et Optimisation

### Optimisations recommandées

1. **Cache intelligent** : Ajustez les TTL selon la volatilité des données
2. **Requêtes groupées** : Utilisez les méthodes multi-symboles
3. **Calculs parallèles** : Les indicateurs sont calculés en parallèle automatiquement
4. **Filtrage précoce** : Filtrez les données au niveau du provider quand possible

### Monitoring de performance

```python
import time
from typing import Dict, Any

class PerformanceMonitor:
    """Moniteur de performance pour les opérations de données."""
    
    def __init__(self):
        self.metrics: Dict[str, Any] = {
            'operations': 0,
            'total_time': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
    
    async def timed_operation(self, operation, *args, **kwargs):
        """Exécute une opération en mesurant le temps."""
        start_time = time.time()
        try:
            result = await operation(*args, **kwargs)
            self.metrics['operations'] += 1
            return result
        finally:
            self.metrics['total_time'] += time.time() - start_time
    
    def get_stats(self) -> Dict[str, float]:
        """Retourne les statistiques de performance."""
        ops = self.metrics['operations']
        return {
            'avg_operation_time': self.metrics['total_time'] / max(1, ops),
            'operations_count': ops,
            'cache_hit_rate': self.metrics['cache_hits'] / max(1, self.metrics['cache_hits'] + self.metrics['cache_misses'])
        }

# Utilisation
monitor = PerformanceMonitor()

# Surveillance des opérations
data = await monitor.timed_operation(
    market_service.get_historical_data,
    "AAPL",
    TimeFrame.DAY_1
)

stats = monitor.get_stats()
print(f"Temps moyen par opération: {stats['avg_operation_time']:.2f}s")
```

Cette documentation couvre tous les aspects de l'intégration OpenBB. Pour des exemples plus spécifiques ou des cas d'usage avancés, consultez le fichier `integration_test.py` qui contient des démonstrations pratiques complètes.