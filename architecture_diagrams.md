# Diagrammes d'Architecture - Agent IA Financier

## Vue d'Ensemble

Cette collection de diagrammes Mermaid illustre l'architecture complète de l'agent IA financier, depuis la vue d'ensemble jusqu'aux détails d'implémentation.

## 1. Architecture Globale du Système

```mermaid
graph TD
    A[CLI Interface] --> B[Application Layer]
    B --> C[Business Logic Layer]
    C --> D[AI Integration Layer]
    C --> E[Data Layer]
    D --> F[Claude API via OpenRouter]
    E --> G[OpenBB API]
    E --> H[Cache Layer]
    C --> I[Persistence Layer]
    I --> J[SQLite Database]
    I --> K[File System]
    
    subgraph "Core Services"
        L[Error Handler]
        M[Security Manager]
        N[Logger Service]
        O[Event Bus]
    end
    
    B --> L
    B --> M
    B --> N
    B --> O
    
    style A fill:#e1f5fe
    style F fill:#fff3e0
    style G fill:#fff3e0
    style J fill:#f3e5f5
    style K fill:#f3e5f5
```

## 2. Flux de Données Principal

```mermaid
sequenceDiagram
    participant U as Utilisateur
    participant CLI as CLI Handler
    participant SE as Strategy Engine
    participant MDS as Market Data Service
    participant AI as AI Service
    participant DE as Decision Engine
    participant PM as Portfolio Manager
    participant DB as Database
    
    U->>CLI: finagent analyze --strategy momentum
    CLI->>SE: execute_strategy()
    SE->>MDS: get_market_data()
    MDS->>SE: market_data
    SE->>AI: analyze_with_context()
    AI->>SE: analysis_result
    SE->>DE: generate_signals()
    DE->>PM: update_portfolio()
    PM->>DB: save_transactions()
    DB->>PM: confirmation
    PM->>CLI: portfolio_update
    CLI->>U: formatted_results
```

## 3. Architecture du Système de Stratégies

```mermaid
graph LR
    A[YAML Strategy Config] --> B[Strategy Parser]
    B --> C[Strategy Factory]
    C --> D{Strategy Type}
    
    D -->|Technical| E[Technical Strategy]
    D -->|Fundamental| F[Fundamental Strategy]
    D -->|Sentiment| G[Sentiment Strategy]
    D -->|Hybrid| H[Hybrid Strategy]
    
    E --> I[Technical Indicators]
    F --> J[Financial Ratios]
    G --> K[News Sentiment]
    H --> L[Multi-Factor Analysis]
    
    I --> M[Signal Generator]
    J --> M
    K --> M
    L --> M
    
    M --> N[Risk Manager]
    N --> O[Portfolio Decision]
    
    subgraph "Strategy Templates"
        P[Momentum Template]
        Q[Value Template]
        R[Breakout Template]
    end
    
    A -.-> P
    A -.-> Q
    A -.-> R
    
    style A fill:#e8f5e8
    style M fill:#fff3e0
    style O fill:#e1f5fe
```

## 4. Architecture de Persistance Multi-Couches

```mermaid
graph TD
    A[Application Layer] --> B[Repository Layer]
    B --> C[Unit of Work]
    C --> D[Database Session]
    
    subgraph "Cache Layer"
        E[L1 Memory Cache]
        F[L2 Redis Cache]
        G[L3 File Cache]
    end
    
    A --> E
    E --> F
    F --> G
    
    subgraph "Persistence Layer"
        H[SQLite Database]
        I[File Storage]
        J[Configuration Files]
        K[Encrypted Secrets]
    end
    
    D --> H
    B --> I
    B --> J
    B --> K
    
    subgraph "AI Memory System"
        L[Short Term Memory]
        M[Long Term Memory]
        N[Pattern Memory]
        O[Episodic Memory]
    end
    
    H --> L
    H --> M
    H --> N
    H --> O
    
    subgraph "Backup System"
        P[Incremental Backup]
        Q[Full Backup]
        R[Archive Storage]
    end
    
    H --> P
    H --> Q
    Q --> R
    
    style H fill:#f3e5f5
    style E fill:#e1f5fe
    style L fill:#fff3e0
```

## 5. Workflow de Décision IA

```mermaid
flowchart TD
    A[Market Data Input] --> B[Data Validation]
    B --> C[Technical Analysis]
    B --> D[Fundamental Analysis]
    B --> E[Sentiment Analysis]
    
    C --> F[Technical Signals]
    D --> G[Fundamental Signals]
    E --> H[Sentiment Signals]
    
    F --> I[AI Context Builder]
    G --> I
    H --> I
    
    I --> J[Claude AI Analysis]
    J --> K[AI Memory Recall]
    K --> L[Confidence Scoring]
    
    L --> M{Confidence > Threshold}
    M -->|Yes| N[Generate Signal]
    M -->|No| O[Request More Data]
    
    N --> P[Risk Assessment]
    P --> Q{Risk Acceptable}
    Q -->|Yes| R[Execute Decision]
    Q -->|No| S[Modify Signal]
    
    R --> T[Update Portfolio]
    S --> P
    O --> A
    
    T --> U[Store Decision]
    U --> V[Learn from Outcome]
    V --> W[Update AI Memory]
    
    style J fill:#fff3e0
    style M fill:#e8f5e8
    style Q fill:#ffebee
    style W fill:#e1f5fe
```

## 6. Architecture de Sécurité

```mermaid
graph TB
    subgraph "Application Security"
        A[Input Validation]
        B[Session Management]
        C[Rate Limiting]
    end
    
    subgraph "Data Security"
        D[Field Encryption]
        E[Secret Management]
        F[Access Control]
    end
    
    subgraph "Transport Security"
        G[TLS Encryption]
        H[API Token Security]
        I[Certificate Validation]
    end
    
    subgraph "Infrastructure Security"
        J[File Permissions]
        K[Network Security]
        L[Environment Isolation]
    end
    
    A --> D
    B --> E
    C --> F
    
    D --> G
    E --> H
    F --> I
    
    G --> J
    H --> K
    I --> L
    
    subgraph "Security Services"
        M[Encryption Service]
        N[Authentication Service]
        O[Audit Logger]
        P[Security Monitor]
    end
    
    D --> M
    B --> N
    A --> O
    C --> P
    
    subgraph "Key Management"
        Q[Master Key]
        R[API Keys]
        S[Encryption Keys]
        T[Keyring Integration]
    end
    
    M --> Q
    E --> R
    M --> S
    R --> T
    
    style M fill:#ffebee
    style Q fill:#fff3e0
    style O fill:#e8f5e8
```

## 7. Diagramme de Composants CLI

```mermaid
graph LR
    A[User Input] --> B[CLI Handler]
    B --> C[Command Parser]
    C --> D{Command Type}
    
    D -->|Strategy| E[Strategy Commands]
    D -->|Portfolio| F[Portfolio Commands]
    D -->|Analysis| G[Analysis Commands]
    D -->|Config| H[Config Commands]
    
    E --> I[Strategy Service]
    F --> J[Portfolio Service]
    G --> K[Analysis Service]
    H --> L[Config Service]
    
    I --> M[Output Formatter]
    J --> M
    K --> M
    L --> M
    
    M --> N{Output Format}
    N -->|Table| O[Table Formatter]
    N -->|JSON| P[JSON Formatter]
    N -->|Chart| Q[Chart Formatter]
    
    O --> R[Rich Console]
    P --> R
    Q --> R
    
    R --> S[Terminal Output]
    
    subgraph "Validation Layer"
        T[Input Validator]
        U[Strategy Validator]
        V[Security Validator]
    end
    
    C --> T
    E --> U
    B --> V
    
    style B fill:#e1f5fe
    style M fill:#e8f5e8
    style R fill:#fff3e0
```

## 8. Architecture des Providers de Données

```mermaid
graph TD
    A[Data Request] --> B[Data Service Router]
    B --> C{Data Type}
    
    C -->|Market Data| D[Market Data Service]
    C -->|Fundamental| E[Fundamental Service]
    C -->|Technical| F[Technical Service]
    C -->|News| G[News Service]
    
    D --> H[Provider Manager]
    E --> H
    F --> H
    G --> H
    
    H --> I{Provider Selection}
    I -->|Primary| J[OpenBB Provider]
    I -->|Fallback| K[YFinance Provider]
    I -->|Backup| L[Alpha Vantage Provider]
    
    J --> M[HTTP Client]
    K --> M
    L --> M
    
    M --> N[Response Validator]
    N --> O[Data Normalizer]
    O --> P[Cache Manager]
    
    P --> Q{Cache Hit}
    Q -->|Yes| R[Return Cached Data]
    Q -->|No| S[Store in Cache]
    
    S --> T[Return Fresh Data]
    R --> U[Response]
    T --> U
    
    subgraph "Error Handling"
        V[Circuit Breaker]
        W[Retry Logic]
        X[Fallback Handler]
    end
    
    M --> V
    V --> W
    W --> X
    
    subgraph "Rate Limiting"
        Y[Rate Limiter]
        Z[Queue Manager]
    end
    
    M --> Y
    Y --> Z
    
    style J fill:#fff3e0
    style P fill:#e1f5fe
    style V fill:#ffebee
```

## 9. Workflow de Backtesting

```mermaid
flowchart TD
    A[Strategy Config] --> B[Backtest Setup]
    B --> C[Load Historical Data]
    C --> D[Initialize Portfolio]
    D --> E[Time Loop Start]
    
    E --> F[Current Date]
    F --> G[Get Market Data]
    G --> H[Execute Strategy]
    H --> I[Generate Signals]
    
    I --> J{Signal Generated}
    J -->|Yes| K[Simulate Trade]
    J -->|No| L[Next Time Period]
    
    K --> M[Update Portfolio]
    M --> N[Record Transaction]
    N --> O[Calculate Metrics]
    O --> L
    
    L --> P{End of Period}
    P -->|No| F
    P -->|Yes| Q[Final Calculations]
    
    Q --> R[Performance Analysis]
    R --> S[Risk Metrics]
    S --> T[Generate Report]
    
    T --> U[Comparison with Benchmark]
    U --> V[Visualization]
    V --> W[Export Results]
    
    subgraph "Performance Metrics"
        X[Total Return]
        Y[Sharpe Ratio]
        Z[Max Drawdown]
        AA[Win Rate]
    end
    
    R --> X
    R --> Y
    R --> Z
    R --> AA
    
    subgraph "Risk Analysis"
        BB[Volatility]
        CC[Value at Risk]
        DD[Beta]
    end
    
    S --> BB
    S --> CC
    S --> DD
    
    style H fill:#e8f5e8
    style R fill:#e1f5fe
    style S fill:#ffebee
```

## 10. Architecture Event-Driven

```mermaid
graph TD
    A[Domain Events] --> B[Event Bus]
    
    subgraph "Event Publishers"
        C[Market Data Updated]
        D[Signal Generated]
        E[Position Opened]
        F[Risk Limit Exceeded]
        G[Strategy Executed]
    end
    
    C --> B
    D --> B
    E --> B
    F --> B
    G --> B
    
    B --> H[Event Router]
    H --> I{Event Type}
    
    I -->|MarketData| J[Data Handlers]
    I -->|Signal| K[Signal Handlers]
    I -->|Position| L[Portfolio Handlers]
    I -->|Risk| M[Risk Handlers]
    I -->|Strategy| N[Strategy Handlers]
    
    subgraph "Event Handlers"
        J --> O[Cache Updater]
        J --> P[Alert Generator]
        
        K --> Q[Portfolio Updater]
        K --> R[Notification Sender]
        
        L --> S[Performance Tracker]
        L --> T[Audit Logger]
        
        M --> U[Emergency Stop]
        M --> V[Risk Alert]
        
        N --> W[Memory Updater]
        N --> X[Metrics Collector]
    end
    
    subgraph "Event Store"
        Y[Event Log]
        Z[Event Replay]
        AA[Event Snapshots]
    end
    
    B --> Y
    Y --> Z
    Y --> AA
    
    style B fill:#e1f5fe
    style H fill:#e8f5e8
    style Y fill:#fff3e0
```

## 11. Diagramme de Déploiement

```mermaid
graph TB
    subgraph "Local Environment"
        A[User Workstation]
        A --> B[FinAgent CLI]
        B --> C[Python Runtime]
        C --> D[Local SQLite DB]
        C --> E[File System Storage]
        C --> F[Local Cache]
    end
    
    subgraph "External APIs"
        G[OpenBB API]
        H[OpenRouter Claude API]
        I[Alpha Vantage API]
    end
    
    B --> G
    B --> H
    B --> I
    
    subgraph "Security Layer"
        J[OS Keyring]
        K[Encrypted Storage]
        L[TLS Connections]
    end
    
    C --> J
    E --> K
    B --> L
    
    subgraph "Optional Components"
        M[Redis Cache]
        N[Docker Container]
        O[Log Aggregation]
    end
    
    F -.-> M
    C -.-> N
    B -.-> O
    
    subgraph "Configuration"
        P[Environment Variables]
        Q[Config Files]
        R[Strategy Templates]
    end
    
    C --> P
    C --> Q
    B --> R
    
    style A fill:#e1f5fe
    style G fill:#fff3e0
    style H fill:#fff3e0
    style J fill:#ffebee
```

## 12. Diagramme de Classes Principales

```mermaid
classDiagram
    class IStrategyService {
        <<interface>>
        +load_strategy(id) StrategyConfig
        +execute_strategy(id, symbols) List~AnalysisResult~
        +validate_strategy(config) ValidationResult
    }
    
    class StrategyService {
        -strategy_repository: IStrategyRepository
        -validator: IStrategyValidator
        +load_strategy(id) StrategyConfig
        +execute_strategy(id, symbols) List~AnalysisResult~
    }
    
    class BaseStrategy {
        <<abstract>>
        #config: StrategyConfig
        +analyze(data) AnalysisResult*
        +get_signals(analysis) List~Signal~*
    }
    
    class TechnicalStrategy {
        -indicators: List~Indicator~
        +analyze(data) AnalysisResult
        +calculate_indicators() Dict
    }
    
    class IMarketDataProvider {
        <<interface>>
        +get_current_price(symbol) MarketData
        +get_historical_data(symbol, period) List~MarketData~
    }
    
    class OpenBBProvider {
        -api_key: str
        -http_client: HTTPClient
        +get_current_price(symbol) MarketData
        +get_historical_data(symbol, period) List~MarketData~
    }
    
    class Portfolio {
        -id: str
        -positions: List~Position~
        -cash_balance: Decimal
        +add_position(position) void
        +calculate_value() Decimal
    }
    
    class Position {
        -symbol: str
        -quantity: Decimal
        -avg_cost: Decimal
        +market_value() Decimal
        +unrealized_pnl() Decimal
    }
    
    IStrategyService <|-- StrategyService
    BaseStrategy <|-- TechnicalStrategy
    IMarketDataProvider <|-- OpenBBProvider
    StrategyService --> BaseStrategy
    Portfolio *-- Position
    
    class AIMemoryService {
        -short_term: ShortTermMemory
        -long_term: LongTermMemory
        +store_decision(decision) void
        +recall_similar(context) List~Memory~
    }
    
    class SecurityManager {
        -secret_manager: SecretManager
        -encryption: DataEncryption
        +encrypt_data(data) bytes
        +get_api_key(service) str
    }
```

Ces diagrammes offrent une vue complète de :
- **Architecture système** : Vue d'ensemble et interactions
- **Flux de données** : Séquences et workflows
- **Composants métier** : Stratégies et décisions
- **Infrastructure** : Persistance et sécurité
- **Déploiement** : Configuration et environnement
- **Classes** : Structure orientée objet