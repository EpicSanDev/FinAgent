# Système de Mémoire et Persistance - Agent IA Financier

## Vue d'Ensemble

Le système de mémoire et persistance permet à l'agent IA de :
- Apprendre et s'améliorer au fil du temps
- Conserver l'historique des décisions et résultats
- Maintenir les configurations et préférences utilisateur
- Optimiser les performances via mise en cache intelligente

## Architecture de Persistance

### 1. Couches de Stockage

```
┌─────────────────────────────────────────────────────────┐
│                    Memory Layer                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │   L1 Cache  │  │ Working Set │  │ AI Context  │     │
│  │  (Redis)    │  │ (RAM Dict)  │  │ (Memory)    │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                 Persistence Layer                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │  SQLite DB  │  │ File System │  │ Time Series │     │
│  │ (Relations) │  │ (Configs)   │  │ (InfluxDB)  │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                   Backup Layer                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ Local Backup│  │ Export/     │  │ Version     │     │
│  │ (Archives)  │  │ Import      │  │ Control     │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
```

### 2. Modèle de Données Relationnel

#### Schéma SQLite Principal

```sql
-- ================================
-- USER AND SETTINGS
-- ================================

CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    preferences JSON
);

CREATE TABLE user_settings (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    setting_key TEXT NOT NULL,
    setting_value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ================================
-- STRATEGIES
-- ================================

CREATE TABLE strategies (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    name TEXT NOT NULL,
    version TEXT DEFAULT '1.0',
    type TEXT NOT NULL, -- technical, fundamental, sentiment, hybrid
    config JSON NOT NULL,
    status TEXT DEFAULT 'active', -- active, inactive, archived
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP
);

CREATE TABLE strategy_versions (
    id INTEGER PRIMARY KEY,
    strategy_id INTEGER REFERENCES strategies(id),
    version TEXT NOT NULL,
    config JSON NOT NULL,
    changelog TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE strategy_performance (
    id INTEGER PRIMARY KEY,
    strategy_id INTEGER REFERENCES strategies(id),
    period_start DATE,
    period_end DATE,
    total_return REAL,
    sharpe_ratio REAL,
    max_drawdown REAL,
    win_rate REAL,
    total_trades INTEGER,
    metrics JSON,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ================================
-- PORTFOLIO AND POSITIONS
-- ================================

CREATE TABLE portfolios (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    name TEXT NOT NULL,
    initial_capital REAL,
    current_value REAL,
    cash_balance REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE positions (
    id INTEGER PRIMARY KEY,
    portfolio_id INTEGER REFERENCES portfolios(id),
    symbol TEXT NOT NULL,
    quantity REAL,
    avg_price REAL,
    current_price REAL,
    market_value REAL,
    unrealized_pnl REAL,
    opened_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE transactions (
    id INTEGER PRIMARY KEY,
    portfolio_id INTEGER REFERENCES portfolios(id),
    strategy_id INTEGER REFERENCES strategies(id),
    symbol TEXT NOT NULL,
    transaction_type TEXT, -- buy, sell, dividend
    quantity REAL,
    price REAL,
    commission REAL,
    total_amount REAL,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

-- ================================
-- MARKET DATA AND CACHE
-- ================================

CREATE TABLE market_data_cache (
    id INTEGER PRIMARY KEY,
    symbol TEXT NOT NULL,
    data_type TEXT NOT NULL, -- price, volume, indicators
    timeframe TEXT, -- 1m, 5m, 1h, 1d
    date_time TIMESTAMP,
    data JSON,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE symbols_metadata (
    symbol TEXT PRIMARY KEY,
    company_name TEXT,
    sector TEXT,
    industry TEXT,
    market_cap REAL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ================================
-- AI MEMORY AND LEARNING
-- ================================

CREATE TABLE ai_memory (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    memory_type TEXT, -- decision, pattern, feedback, observation
    context JSON,
    content TEXT,
    relevance_score REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP,
    access_count INTEGER DEFAULT 0
);

CREATE TABLE decision_history (
    id INTEGER PRIMARY KEY,
    strategy_id INTEGER REFERENCES strategies(id),
    symbol TEXT NOT NULL,
    decision_type TEXT, -- buy, sell, hold
    confidence_score REAL,
    reasoning TEXT,
    market_context JSON,
    actual_outcome REAL, -- performance après la décision
    decided_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    outcome_measured_at TIMESTAMP
);

CREATE TABLE pattern_recognition (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    pattern_type TEXT,
    pattern_data JSON,
    success_rate REAL,
    occurrences INTEGER,
    last_seen TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ================================
-- NOTIFICATIONS AND ALERTS
-- ================================

CREATE TABLE alerts (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    strategy_id INTEGER REFERENCES strategies(id),
    alert_type TEXT, -- buy_signal, sell_signal, risk_warning
    symbol TEXT,
    message TEXT,
    priority INTEGER, -- 1=low, 2=medium, 3=high, 4=critical
    status TEXT DEFAULT 'pending', -- pending, sent, acknowledged
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMP,
    acknowledged_at TIMESTAMP
);

-- ================================
-- INDEXES FOR PERFORMANCE
-- ================================

CREATE INDEX idx_strategies_user_id ON strategies(user_id);
CREATE INDEX idx_strategies_status ON strategies(status);
CREATE INDEX idx_positions_portfolio_id ON positions(portfolio_id);
CREATE INDEX idx_positions_symbol ON positions(symbol);
CREATE INDEX idx_transactions_portfolio_id ON transactions(portfolio_id);
CREATE INDEX idx_transactions_symbol ON transactions(symbol);
CREATE INDEX idx_transactions_executed_at ON transactions(executed_at);
CREATE INDEX idx_market_data_symbol_type ON market_data_cache(symbol, data_type);
CREATE INDEX idx_market_data_expires_at ON market_data_cache(expires_at);
CREATE INDEX idx_ai_memory_user_type ON ai_memory(user_id, memory_type);
CREATE INDEX idx_decision_history_strategy ON decision_history(strategy_id);
CREATE INDEX idx_decision_history_symbol ON decision_history(symbol);
CREATE INDEX idx_alerts_user_status ON alerts(user_id, status);
```

### 3. Système de Mémoire IA

#### Architecture de la Mémoire IA
```python
class AIMemorySystem:
    """Système de mémoire pour l'IA permettant l'apprentissage"""
    
    def __init__(self):
        self.short_term_memory = ShortTermMemory()
        self.long_term_memory = LongTermMemory()
        self.pattern_memory = PatternMemory()
        self.episodic_memory = EpisodicMemory()
    
    def store_decision(self, decision: Decision, context: MarketContext):
        """Stocke une décision et son contexte"""
        
    def store_outcome(self, decision_id: str, outcome: Outcome):
        """Stocke le résultat d'une décision"""
        
    def recall_similar_situations(self, current_context: MarketContext) -> List[Memory]:
        """Rappelle des situations similaires"""
        
    def update_patterns(self, new_data: Any):
        """Met à jour les patterns reconnus"""
```

#### Types de Mémoire

##### 1. Mémoire à Court Terme
```python
class ShortTermMemory:
    """Mémoire de travail pour la session actuelle"""
    
    def __init__(self, max_size: int = 1000):
        self.buffer = deque(maxlen=max_size)
        self.current_context = {}
        
    def add_event(self, event: MemoryEvent):
        """Ajoute un événement à la mémoire à court terme"""
        
    def get_recent_context(self, lookback_minutes: int = 60):
        """Récupère le contexte récent"""
```

##### 2. Mémoire à Long Terme
```python
class LongTermMemory:
    """Mémoire persistante pour l'apprentissage"""
    
    def store_pattern(self, pattern: Pattern, success_rate: float):
        """Stocke un pattern avec son taux de succès"""
        
    def retrieve_patterns(self, context: Context) -> List[Pattern]:
        """Récupère les patterns pertinents"""
        
    def update_pattern_performance(self, pattern_id: str, outcome: bool):
        """Met à jour la performance d'un pattern"""
```

##### 3. Mémoire Épisodique
```python
class EpisodicMemory:
    """Mémoire des épisodes de trading spécifiques"""
    
    def store_episode(self, episode: TradingEpisode):
        """Stocke un épisode de trading complet"""
        
    def find_similar_episodes(self, current_situation: Situation) -> List[Episode]:
        """Trouve des épisodes similaires"""
```

### 4. Stratégies de Cache

#### Cache Multi-Niveaux
```python
class CacheManager:
    """Gestionnaire de cache multi-niveaux"""
    
    def __init__(self):
        self.l1_cache = MemoryCache(max_size=1000)  # RAM
        self.l2_cache = RedisCache() if redis_available else FileCache()
        self.l3_cache = DatabaseCache()  # SQLite
        
    def get(self, key: str, cache_level: int = None):
        """Récupère une valeur avec stratégie de cache"""
        
    def set(self, key: str, value: Any, ttl: int = 3600):
        """Stocke une valeur à tous les niveaux appropriés"""
        
    def invalidate(self, pattern: str):
        """Invalide les entrées correspondant au pattern"""
```

#### Stratégies de Cache par Type de Données

##### 1. Données de Marché
```python
class MarketDataCache:
    """Cache spécialisé pour les données de marché"""
    
    CACHE_RULES = {
        'realtime_price': {'ttl': 5, 'level': 'L1'},      # 5 secondes
        'daily_price': {'ttl': 3600, 'level': 'L2'},     # 1 heure
        'indicators': {'ttl': 1800, 'level': 'L2'},      # 30 minutes
        'fundamentals': {'ttl': 86400, 'level': 'L3'},   # 1 jour
        'historical': {'ttl': 604800, 'level': 'L3'}     # 1 semaine
    }
```

##### 2. Résultats IA
```python
class AIResultsCache:
    """Cache pour les résultats d'analyse IA"""
    
    def cache_analysis(self, symbol: str, strategy: str, analysis: Analysis):
        """Cache une analyse IA avec contexte"""
        
    def get_cached_analysis(self, symbol: str, strategy: str, max_age: int = 3600):
        """Récupère une analyse en cache si elle est récente"""
```

### 5. Gestion de la Configuration

#### Système de Configuration Hiérarchique
```
Configuration Priority (highest to lowest):
1. Command line arguments
2. Environment variables  
3. User-specific config files (~/.finagent/config.yaml)
4. Project config files (./config.yaml)
5. Default configuration
```

#### Structure des Fichiers de Configuration
```yaml
# ~/.finagent/config.yaml
finagent:
  # Base de données
  database:
    url: "sqlite:///~/.finagent/finagent.db"
    echo: false
    pool_size: 5
    
  # Cache
  cache:
    backend: "memory"  # memory, redis, file
    redis_url: "redis://localhost:6379/0"
    default_ttl: 3600
    max_memory_cache_size: 1000
    
  # IA et APIs
  ai:
    provider: "openrouter"
    model: "anthropic/claude-3-sonnet"
    max_tokens: 4000
    temperature: 0.1
    
  openbb:
    api_key: "${OPENBB_API_KEY}"
    
  # Logging
  logging:
    level: "INFO"
    format: "structured"
    file: "~/.finagent/logs/finagent.log"
    max_size: "10MB"
    backup_count: 5
    
  # Sécurité
  security:
    encryption_key_file: "~/.finagent/keys/encryption.key"
    keyring_service: "finagent"
    
  # Performance
  performance:
    max_concurrent_requests: 10
    request_timeout: 30
    retry_attempts: 3
    backoff_factor: 2.0
```

### 6. Système de Sauvegarde et Récupération

#### Stratégie de Sauvegarde
```python
class BackupManager:
    """Gestionnaire de sauvegardes automatiques"""
    
    def __init__(self, config: BackupConfig):
        self.config = config
        self.backup_schedule = BackupSchedule()
        
    def create_backup(self, backup_type: BackupType = BackupType.INCREMENTAL):
        """Crée une sauvegarde"""
        
    def restore_backup(self, backup_path: str, target_date: datetime = None):
        """Restaure depuis une sauvegarde"""
        
    def cleanup_old_backups(self):
        """Nettoie les anciennes sauvegardes selon la politique"""
```

#### Types de Sauvegarde
```python
class BackupType(Enum):
    FULL = "full"           # Sauvegarde complète
    INCREMENTAL = "incremental"  # Sauvegarde incrémentale
    DIFFERENTIAL = "differential"  # Sauvegarde différentielle
    CONFIGURATION = "config"  # Configuration seulement
    AI_MEMORY = "memory"     # Mémoire IA seulement
```

#### Planification des Sauvegardes
```yaml
backup:
  schedule:
    full_backup: "weekly"      # Tous les dimanches
    incremental: "daily"       # Tous les jours à 2h
    config_backup: "on_change" # À chaque modification
    
  retention:
    daily_backups: 7          # 7 jours
    weekly_backups: 4         # 4 semaines  
    monthly_backups: 12       # 12 mois
    
  location:
    local_path: "~/.finagent/backups"
    cloud_sync: false         # Future: sync cloud
    compression: true
    encryption: true
```

### 7. Migration et Versioning

#### Système de Migration
```python
class MigrationManager:
    """Gestionnaire des migrations de schéma"""
    
    def __init__(self):
        self.migrations_path = "finagent/migrations"
        self.current_version = self.get_current_version()
        
    def migrate_to_latest(self):
        """Migre vers la dernière version"""
        
    def migrate_to_version(self, target_version: str):
        """Migre vers une version spécifique"""
        
    def rollback_migration(self, steps: int = 1):
        """Annule les dernières migrations"""
```

#### Exemple de Migration
```python
# migrations/001_initial_schema.py
def upgrade():
    """Crée le schéma initial"""
    conn.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

def downgrade():
    """Annule la migration"""
    conn.execute("DROP TABLE users")
```

### 8. Optimisations de Performance

#### Indexation Intelligente
```python
class IndexManager:
    """Gestion automatique des index pour performance"""
    
    def analyze_query_patterns(self):
        """Analyse les patterns de requêtes"""
        
    def suggest_indexes(self) -> List[IndexSuggestion]:
        """Suggère des index pour optimiser les performances"""
        
    def create_adaptive_indexes(self):
        """Crée des index adaptatifs selon l'usage"""
```

#### Partitionnement des Données
```python
class DataPartitioner:
    """Partitionnement des données par date/symbole"""
    
    def partition_by_date(self, table: str, date_column: str):
        """Partitionne une table par date"""
        
    def partition_by_symbol(self, table: str):
        """Partitionne une table par symbole"""
```

#### Compression et Archivage
```python
class DataArchiver:
    """Archivage des données anciennes"""
    
    ARCHIVE_RULES = {
        'market_data_cache': 30,    # Archive après 30 jours
        'decision_history': 365,    # Archive après 1 an
        'ai_memory': None,          # Ne jamais archiver
        'transactions': None        # Ne jamais archiver
    }
    
    def archive_old_data(self):
        """Archive les données anciennes selon les règles"""
```

### 9. Monitoring et Métriques

#### Métriques de Performance
```python
class PerformanceMonitor:
    """Monitoring des performances du système de persistance"""
    
    def track_query_performance(self):
        """Suit les performances des requêtes"""
        
    def track_cache_hit_ratio(self):
        """Suit le taux de succès du cache"""
        
    def track_storage_usage(self):
        """Suit l'utilisation du stockage"""
        
    def generate_performance_report(self):
        """Génère un rapport de performance"""
```

#### Alertes Système
```yaml
alerts:
  database_size: 
    warning: "1GB"
    critical: "5GB"
    
  cache_hit_ratio:
    warning: 0.7
    critical: 0.5
    
  query_performance:
    slow_query_threshold: "1s"
    
  backup_status:
    missing_backup_days: 2
    
  memory_usage:
    warning: "80%"
    critical: "95%"
```

### 10. Intégration avec le Reste du Système

#### Repository Pattern Implementation
```python
class BaseRepository:
    """Classe de base pour tous les repositories"""
    
    def __init__(self, session: Session):
        self.session = session
        
    def save(self, entity):
        """Sauvegarde une entité"""
        
    def find_by_id(self, entity_id):
        """Trouve par ID"""
        
    def find_all(self):
        """Trouve toutes les entités"""
        
    def delete(self, entity):
        """Supprime une entité"""

class StrategyRepository(BaseRepository):
    """Repository pour les stratégies"""
    
    def find_by_user(self, user_id: int) -> List[Strategy]:
        """Trouve les stratégies d'un utilisateur"""
        
    def find_active_strategies(self) -> List[Strategy]:
        """Trouve les stratégies actives"""
```

#### Unit of Work Pattern
```python
class UnitOfWork:
    """Unit of Work pour gérer les transactions"""
    
    def __init__(self):
        self.session = create_session()
        self.strategies = StrategyRepository(self.session)
        self.portfolios = PortfolioRepository(self.session)
        self.decisions = DecisionRepository(self.session)
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.commit()
        else:
            self.rollback()
        self.session.close()
        
    def commit(self):
        self.session.commit()
        
    def rollback(self):
        self.session.rollback()
```

Cette architecture de mémoire et persistance offre :
- **Scalabilité** : Support de croissance des données
- **Performance** : Cache multi-niveaux optimisé
- **Fiabilité** : Sauvegardes automatiques et récupération
- **Apprentissage** : Mémoire IA pour amélioration continue
- **Maintenabilité** : Migrations et versioning automatisés