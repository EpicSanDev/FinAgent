# Interfaces et APIs Internes - Agent IA Financier

## Vue d'Ensemble

Ce document définit les contrats d'interface entre tous les composants du système, garantissant un couplage faible et une haute cohésion entre les modules.

## 1. Architecture des Interfaces

### Hiérarchie des Interfaces
```
┌─────────────────────────────────────────────────────────┐
│                 Application Layer                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ CLI Service │  │ Command Bus │  │ Event Bus   │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                 Business Interfaces                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ Strategy    │  │ Portfolio   │  │ Decision    │     │
│  │ Service     │  │ Service     │  │ Service     │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                 Infrastructure Interfaces               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ Data        │  │ AI          │  │ Cache       │     │
│  │ Providers   │  │ Providers   │  │ Providers   │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
```

## 2. Modèles de Données Partagés

### Modèles Core Business
```python
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union
from decimal import Decimal
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from pydantic import BaseModel, Field

# ================================
# ENUMERATIONS
# ================================

class AssetType(str, Enum):
    STOCK = "stock"
    ETF = "etf"
    CRYPTO = "crypto"
    FOREX = "forex"

class DecisionType(str, Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"

class SignalStrength(str, Enum):
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    VERY_STRONG = "very_strong"

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"

# ================================
# CORE DATA MODELS
# ================================

class Symbol(BaseModel):
    """Représentation d'un symbole financier"""
    ticker: str
    name: str
    asset_type: AssetType
    exchange: str
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap: Optional[Decimal] = None

class MarketData(BaseModel):
    """Données de marché pour un symbole"""
    symbol: str
    timestamp: datetime
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal
    volume: int
    adjusted_close: Optional[Decimal] = None

class TechnicalIndicator(BaseModel):
    """Indicateur technique"""
    name: str
    value: Union[Decimal, Dict[str, Decimal]]
    timestamp: datetime
    parameters: Dict[str, Union[str, int, float]]

class FundamentalData(BaseModel):
    """Données fondamentales"""
    symbol: str
    period: str  # quarterly, annually
    revenue: Optional[Decimal] = None
    net_income: Optional[Decimal] = None
    pe_ratio: Optional[Decimal] = None
    pb_ratio: Optional[Decimal] = None
    debt_to_equity: Optional[Decimal] = None
    roe: Optional[Decimal] = None
    reported_date: datetime

class AnalysisResult(BaseModel):
    """Résultat d'une analyse"""
    symbol: str
    strategy_name: str
    analysis_timestamp: datetime
    technical_score: Optional[Decimal] = None
    fundamental_score: Optional[Decimal] = None
    sentiment_score: Optional[Decimal] = None
    overall_score: Decimal
    confidence: Decimal = Field(ge=0, le=1)
    indicators: List[TechnicalIndicator] = []
    reasoning: str

class Signal(BaseModel):
    """Signal de trading"""
    symbol: str
    signal_type: DecisionType
    strength: SignalStrength
    confidence: Decimal = Field(ge=0, le=1)
    target_price: Optional[Decimal] = None
    stop_loss: Optional[Decimal] = None
    take_profit: Optional[Decimal] = None
    reasoning: str
    generated_at: datetime
    expires_at: Optional[datetime] = None

class Position(BaseModel):
    """Position dans le portefeuille"""
    symbol: str
    quantity: Decimal
    avg_cost: Decimal
    current_price: Decimal
    market_value: Decimal
    unrealized_pnl: Decimal
    unrealized_pnl_percent: Decimal
    opened_at: datetime
    last_updated: datetime

class Portfolio(BaseModel):
    """Portefeuille"""
    id: str
    name: str
    total_value: Decimal
    cash_balance: Decimal
    invested_value: Decimal
    total_return: Decimal
    total_return_percent: Decimal
    positions: List[Position]
    last_updated: datetime

# ================================
# CONFIGURATION MODELS
# ================================

class StrategyConfig(BaseModel):
    """Configuration d'une stratégie"""
    name: str
    version: str
    strategy_type: str
    parameters: Dict[str, Union[str, int, float, bool]]
    risk_management: Dict[str, Union[str, float]]
    universe: List[str]
    active: bool = True

class RiskManagementConfig(BaseModel):
    """Configuration de gestion des risques"""
    max_position_size: Decimal = Field(ge=0, le=1)
    max_portfolio_risk: Decimal = Field(ge=0, le=1)
    stop_loss_percent: Decimal
    take_profit_percent: Decimal
    max_drawdown_percent: Decimal
    risk_free_rate: Decimal = Field(default=Decimal("0.02"))
```

## 3. Interfaces des Services Business

### Interface Strategy Service
```python
class IStrategyService(ABC):
    """Interface pour le service de stratégies"""
    
    @abstractmethod
    async def load_strategy(self, strategy_id: str) -> StrategyConfig:
        """Charge une stratégie par son ID"""
        pass
    
    @abstractmethod
    async def validate_strategy(self, config: StrategyConfig) -> ValidationResult:
        """Valide une configuration de stratégie"""
        pass
    
    @abstractmethod
    async def execute_strategy(self, strategy_id: str, symbols: List[str]) -> List[AnalysisResult]:
        """Exécute une stratégie sur une liste de symboles"""
        pass
    
    @abstractmethod
    async def backtest_strategy(self, config: StrategyConfig, period: DateRange) -> BacktestResult:
        """Effectue un backtest d'une stratégie"""
        pass

class IDecisionService(ABC):
    """Interface pour le service de décision"""
    
    @abstractmethod
    async def generate_signals(self, analysis_results: List[AnalysisResult]) -> List[Signal]:
        """Génère des signaux basés sur les résultats d'analyse"""
        pass
    
    @abstractmethod
    async def validate_signals(self, signals: List[Signal], portfolio: Portfolio) -> List[Signal]:
        """Valide les signaux contre le portefeuille actuel"""
        pass
    
    @abstractmethod
    async def apply_risk_management(self, signals: List[Signal], config: RiskManagementConfig) -> List[Signal]:
        """Applique la gestion des risques aux signaux"""
        pass

class IPortfolioService(ABC):
    """Interface pour le service de portefeuille"""
    
    @abstractmethod
    async def get_portfolio(self, portfolio_id: str) -> Portfolio:
        """Récupère un portefeuille"""
        pass
    
    @abstractmethod
    async def update_positions(self, portfolio_id: str, market_data: List[MarketData]) -> Portfolio:
        """Met à jour les positions avec les dernières données de marché"""
        pass
    
    @abstractmethod
    async def calculate_metrics(self, portfolio_id: str) -> PortfolioMetrics:
        """Calcule les métriques de performance"""
        pass
    
    @abstractmethod
    async def simulate_trade(self, portfolio_id: str, signal: Signal) -> TradeSimulation:
        """Simule l'exécution d'un trade"""
        pass
```

## 4. Interfaces des Providers de Données

### Interface Market Data Provider
```python
class IMarketDataProvider(ABC):
    """Interface pour les fournisseurs de données de marché"""
    
    @abstractmethod
    async def get_current_price(self, symbol: str) -> MarketData:
        """Récupère le prix actuel d'un symbole"""
        pass
    
    @abstractmethod
    async def get_historical_data(self, symbol: str, period: DateRange, timeframe: str) -> List[MarketData]:
        """Récupère les données historiques"""
        pass
    
    @abstractmethod
    async def get_multiple_quotes(self, symbols: List[str]) -> Dict[str, MarketData]:
        """Récupère les cours de plusieurs symboles"""
        pass
    
    @abstractmethod
    async def search_symbols(self, query: str) -> List[Symbol]:
        """Recherche des symboles"""
        pass

class IFundamentalDataProvider(ABC):
    """Interface pour les données fondamentales"""
    
    @abstractmethod
    async def get_financial_statements(self, symbol: str) -> FinancialStatements:
        """Récupère les états financiers"""
        pass
    
    @abstractmethod
    async def get_key_metrics(self, symbol: str) -> FundamentalData:
        """Récupère les métriques clés"""
        pass
    
    @abstractmethod
    async def get_company_info(self, symbol: str) -> CompanyInfo:
        """Récupère les informations de l'entreprise"""
        pass

class ITechnicalIndicatorProvider(ABC):
    """Interface pour les indicateurs techniques"""
    
    @abstractmethod
    async def calculate_rsi(self, symbol: str, period: int = 14) -> TechnicalIndicator:
        """Calcule le RSI"""
        pass
    
    @abstractmethod
    async def calculate_moving_averages(self, symbol: str, periods: List[int]) -> List[TechnicalIndicator]:
        """Calcule les moyennes mobiles"""
        pass
    
    @abstractmethod
    async def calculate_macd(self, symbol: str, fast: int = 12, slow: int = 26, signal: int = 9) -> TechnicalIndicator:
        """Calcule le MACD"""
        pass
    
    @abstractmethod
    async def calculate_bollinger_bands(self, symbol: str, period: int = 20, std_dev: float = 2.0) -> TechnicalIndicator:
        """Calcule les bandes de Bollinger"""
        pass
```

## 5. Interfaces AI et Machine Learning

### Interface AI Provider
```python
class IAIProvider(ABC):
    """Interface pour les fournisseurs d'IA"""
    
    @abstractmethod
    async def analyze_market_sentiment(self, context: MarketContext) -> SentimentAnalysis:
        """Analyse le sentiment du marché"""
        pass
    
    @abstractmethod
    async def generate_analysis(self, data: AnalysisInput) -> AnalysisResult:
        """Génère une analyse basée sur les données"""
        pass
    
    @abstractmethod
    async def predict_price_movement(self, symbol: str, timeframe: str) -> PricePrediction:
        """Prédit le mouvement de prix"""
        pass
    
    @abstractmethod
    async def explain_decision(self, analysis: AnalysisResult) -> str:
        """Explique une décision d'analyse"""
        pass

class IMemoryService(ABC):
    """Interface pour le service de mémoire IA"""
    
    @abstractmethod
    async def store_decision(self, decision: Decision, context: MarketContext) -> str:
        """Stocke une décision avec son contexte"""
        pass
    
    @abstractmethod
    async def recall_similar_situations(self, context: MarketContext) -> List[HistoricalContext]:
        """Rappelle des situations similaires"""
        pass
    
    @abstractmethod
    async def learn_from_outcome(self, decision_id: str, outcome: TradingOutcome) -> None:
        """Apprend à partir du résultat d'une décision"""
        pass
    
    @abstractmethod
    async def get_confidence_score(self, analysis: AnalysisResult) -> Decimal:
        """Calcule un score de confiance basé sur l'historique"""
        pass
```

## 6. Interfaces de Cache et Persistance

### Interface Cache Provider
```python
class ICacheProvider(ABC):
    """Interface pour les fournisseurs de cache"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Récupère une valeur du cache"""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Stocke une valeur dans le cache"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> None:
        """Supprime une clé du cache"""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Vérifie l'existence d'une clé"""
        pass
    
    @abstractmethod
    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalide toutes les clés correspondant au pattern"""
        pass

class IRepository(ABC):
    """Interface de base pour les repositories"""
    
    @abstractmethod
    async def save(self, entity: Any) -> Any:
        """Sauvegarde une entité"""
        pass
    
    @abstractmethod
    async def find_by_id(self, entity_id: str) -> Optional[Any]:
        """Trouve une entité par ID"""
        pass
    
    @abstractmethod
    async def find_all(self, filters: Optional[Dict] = None) -> List[Any]:
        """Trouve toutes les entités avec filtres optionnels"""
        pass
    
    @abstractmethod
    async def delete(self, entity_id: str) -> bool:
        """Supprime une entité"""
        pass
```

## 7. Event-Driven Architecture

### Système d'Événements
```python
class DomainEvent(BaseModel):
    """Événement de domaine de base"""
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    aggregate_id: str
    version: int
    data: Dict[str, Any]

class MarketDataUpdated(DomainEvent):
    """Événement de mise à jour des données de marché"""
    event_type: str = "market_data_updated"

class SignalGenerated(DomainEvent):
    """Événement de génération de signal"""
    event_type: str = "signal_generated"

class PositionOpened(DomainEvent):
    """Événement d'ouverture de position"""
    event_type: str = "position_opened"

class RiskLimitExceeded(DomainEvent):
    """Événement de dépassement de limite de risque"""
    event_type: str = "risk_limit_exceeded"

class IEventBus(ABC):
    """Interface pour le bus d'événements"""
    
    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        """Publie un événement"""
        pass
    
    @abstractmethod
    async def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """S'abonne à un type d'événement"""
        pass
    
    @abstractmethod
    async def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """Se désabonne d'un type d'événement"""
        pass

class IEventHandler(ABC):
    """Interface pour les gestionnaires d'événements"""
    
    @abstractmethod
    async def handle(self, event: DomainEvent) -> None:
        """Traite un événement"""
        pass
    
    @abstractmethod
    def can_handle(self, event_type: str) -> bool:
        """Vérifie si le handler peut traiter ce type d'événement"""
        pass
```

## 8. Command Query Responsibility Segregation (CQRS)

### Commands et Queries
```python
class Command(BaseModel):
    """Commande de base"""
    command_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None

class Query(BaseModel):
    """Requête de base"""
    query_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Commands
class ExecuteStrategyCommand(Command):
    """Commande d'exécution de stratégie"""
    strategy_id: str
    symbols: List[str]
    simulation_mode: bool = True

class CreateSignalCommand(Command):
    """Commande de création de signal"""
    analysis_result: AnalysisResult
    strategy_config: StrategyConfig

class UpdatePortfolioCommand(Command):
    """Commande de mise à jour de portefeuille"""
    portfolio_id: str
    signals: List[Signal]

# Queries
class GetPortfolioQuery(Query):
    """Requête de récupération de portefeuille"""
    portfolio_id: str
    include_positions: bool = True

class GetStrategyPerformanceQuery(Query):
    """Requête de performance de stratégie"""
    strategy_id: str
    period: DateRange

class SearchSymbolsQuery(Query):
    """Requête de recherche de symboles"""
    query: str
    asset_types: List[AssetType] = []
    limit: int = 10

# Handlers
class ICommandHandler(ABC):
    """Interface pour les gestionnaires de commandes"""
    
    @abstractmethod
    async def handle(self, command: Command) -> CommandResult:
        """Traite une commande"""
        pass

class IQueryHandler(ABC):
    """Interface pour les gestionnaires de requêtes"""
    
    @abstractmethod
    async def handle(self, query: Query) -> QueryResult:
        """Traite une requête"""
        pass
```

## 9. Dependency Injection Container

### Configuration de l'Injection de Dépendances
```python
class IDependencyContainer(ABC):
    """Interface pour le conteneur d'injection de dépendances"""
    
    @abstractmethod
    def register_singleton(self, interface: Type, implementation: Type) -> None:
        """Enregistre un service singleton"""
        pass
    
    @abstractmethod
    def register_transient(self, interface: Type, implementation: Type) -> None:
        """Enregistre un service transient"""
        pass
    
    @abstractmethod
    def register_instance(self, interface: Type, instance: Any) -> None:
        """Enregistre une instance spécifique"""
        pass
    
    @abstractmethod
    def resolve(self, interface: Type) -> Any:
        """Résout une dépendance"""
        pass
    
    @abstractmethod
    def resolve_all(self, interface: Type) -> List[Any]:
        """Résout toutes les implémentations d'une interface"""
        pass

# Configuration du conteneur
def configure_container(container: IDependencyContainer) -> None:
    """Configure le conteneur d'injection de dépendances"""
    
    # Services business
    container.register_singleton(IStrategyService, StrategyService)
    container.register_singleton(IDecisionService, DecisionService)
    container.register_singleton(IPortfolioService, PortfolioService)
    
    # Providers de données
    container.register_singleton(IMarketDataProvider, OpenBBMarketDataProvider)
    container.register_singleton(ITechnicalIndicatorProvider, TechnicalIndicatorService)
    container.register_singleton(IFundamentalDataProvider, OpenBBFundamentalProvider)
    
    # IA et ML
    container.register_singleton(IAIProvider, ClaudeAIProvider)
    container.register_singleton(IMemoryService, AIMemoryService)
    
    # Infrastructure
    container.register_singleton(ICacheProvider, RedisCacheProvider)
    container.register_singleton(IEventBus, InMemoryEventBus)
    
    # Repositories
    container.register_transient(IStrategyRepository, SQLiteStrategyRepository)
    container.register_transient(IPortfolioRepository, SQLitePortfolioRepository)
    container.register_transient(IDecisionRepository, SQLiteDecisionRepository)
```

## 10. Interfaces CLI et Communication

### Interface CLI Service
```python
class ICLIService(ABC):
    """Interface pour le service CLI"""
    
    @abstractmethod
    async def execute_command(self, command: str, args: Dict[str, Any]) -> CLIResult:
        """Exécute une commande CLI"""
        pass
    
    @abstractmethod
    async def format_output(self, data: Any, format_type: str = "table") -> str:
        """Formate la sortie pour affichage"""
        pass
    
    @abstractmethod
    async def handle_interactive_input(self, prompt: str, options: List[str]) -> str:
        """Gère les entrées interactives"""
        pass

class INotificationService(ABC):
    """Interface pour le service de notifications"""
    
    @abstractmethod
    async def send_alert(self, alert: Alert) -> None:
        """Envoie une alerte"""
        pass
    
    @abstractmethod
    async def send_signal_notification(self, signal: Signal) -> None:
        """Envoie une notification de signal"""
        pass
    
    @abstractmethod
    async def send_performance_report(self, report: PerformanceReport) -> None:
        """Envoie un rapport de performance"""
        pass
```

## 11. Validation et Contrôles

### Interface de Validation
```python
class IValidator(ABC):
    """Interface pour les validateurs"""
    
    @abstractmethod
    async def validate(self, data: Any) -> ValidationResult:
        """Valide des données"""
        pass

class ValidationResult(BaseModel):
    """Résultat de validation"""
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []

class IStrategyValidator(IValidator):
    """Interface pour la validation de stratégies"""
    
    @abstractmethod
    async def validate_config_syntax(self, config: StrategyConfig) -> ValidationResult:
        """Valide la syntaxe de la configuration"""
        pass
    
    @abstractmethod
    async def validate_parameters(self, config: StrategyConfig) -> ValidationResult:
        """Valide les paramètres"""
        pass
    
    @abstractmethod
    async def validate_risk_settings(self, config: StrategyConfig) -> ValidationResult:
        """Valide les paramètres de risque"""
        pass
```

## 12. Middleware et Intercepteurs

### Interface Middleware
```python
class IMiddleware(ABC):
    """Interface pour les middleware"""
    
    @abstractmethod
    async def process(self, request: Any, next_handler: Callable) -> Any:
        """Traite une requête avec middleware"""
        pass

class LoggingMiddleware(IMiddleware):
    """Middleware de logging"""
    
    async def process(self, request: Any, next_handler: Callable) -> Any:
        start_time = time.time()
        result = await next_handler(request)
        duration = time.time() - start_time
        logger.info(f"Request processed in {duration:.2f}s")
        return result

class CachingMiddleware(IMiddleware):
    """Middleware de cache"""
    
    async def process(self, request: Any, next_handler: Callable) -> Any:
        cache_key = self.generate_cache_key(request)
        cached_result = await self.cache.get(cache_key)
        if cached_result:
            return cached_result
        
        result = await next_handler(request)
        await self.cache.set(cache_key, result, ttl=3600)
        return result
```

Cette architecture d'interfaces offre :
- **Couplage faible** : Séparation claire entre abstraction et implémentation
- **Testabilité** : Facilite les mocks et tests unitaires  
- **Extensibilité** : Permet l'ajout de nouvelles implémentations
- **Maintenabilité** : Contrats clairs entre composants
- **Flexibilité** : Support de multiples providers et stratégies