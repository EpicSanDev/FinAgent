# Gestion d'Erreurs et Robustesse - Agent IA Financier

## Vue d'Ensemble

Le système de gestion d'erreurs garantit la fiabilité et la résilience de l'agent IA financier face aux pannes, erreurs de données, problèmes de connectivité et autres situations exceptionnelles.

## 1. Hiérarchie d'Exceptions

### Exceptions Personnalisées
```python
from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime

class ErrorSeverity(Enum):
    """Niveaux de sévérité des erreurs"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """Catégories d'erreurs"""
    VALIDATION = "validation"
    DATA_ACCESS = "data_access"
    EXTERNAL_API = "external_api"
    BUSINESS_LOGIC = "business_logic"
    CONFIGURATION = "configuration"
    SECURITY = "security"
    PERFORMANCE = "performance"

class FinAgentException(Exception):
    """Exception de base pour l'agent financier"""
    
    def __init__(
        self,
        message: str,
        error_code: str,
        category: ErrorCategory,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.category = category
        self.severity = severity
        self.details = details or {}
        self.cause = cause
        self.timestamp = datetime.utcnow()
        self.trace_id = self._generate_trace_id()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'exception en dictionnaire pour logging"""
        return {
            "message": self.message,
            "error_code": self.error_code,
            "category": self.category.value,
            "severity": self.severity.value,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "trace_id": self.trace_id,
            "cause": str(self.cause) if self.cause else None
        }

# ================================
# EXCEPTIONS SPÉCIALISÉES
# ================================

class ValidationError(FinAgentException):
    """Erreurs de validation des données"""
    
    def __init__(self, message: str, field: str = None, value: Any = None, **kwargs):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.MEDIUM,
            details={"field": field, "value": value},
            **kwargs
        )

class DataAccessError(FinAgentException):
    """Erreurs d'accès aux données"""
    
    def __init__(self, message: str, source: str = None, **kwargs):
        super().__init__(
            message=message,
            error_code="DATA_ACCESS_ERROR",
            category=ErrorCategory.DATA_ACCESS,
            severity=ErrorSeverity.HIGH,
            details={"source": source},
            **kwargs
        )

class ExternalAPIError(FinAgentException):
    """Erreurs d'API externes"""
    
    def __init__(self, message: str, service: str, status_code: int = None, **kwargs):
        super().__init__(
            message=message,
            error_code="EXTERNAL_API_ERROR",
            category=ErrorCategory.EXTERNAL_API,
            severity=ErrorSeverity.HIGH,
            details={"service": service, "status_code": status_code},
            **kwargs
        )

class StrategyExecutionError(FinAgentException):
    """Erreurs d'exécution de stratégie"""
    
    def __init__(self, message: str, strategy_name: str, **kwargs):
        super().__init__(
            message=message,
            error_code="STRATEGY_EXECUTION_ERROR",
            category=ErrorCategory.BUSINESS_LOGIC,
            severity=ErrorSeverity.HIGH,
            details={"strategy_name": strategy_name},
            **kwargs
        )

class ConfigurationError(FinAgentException):
    """Erreurs de configuration"""
    
    def __init__(self, message: str, config_key: str = None, **kwargs):
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            category=ErrorCategory.CONFIGURATION,
            severity=ErrorSeverity.CRITICAL,
            details={"config_key": config_key},
            **kwargs
        )

class SecurityError(FinAgentException):
    """Erreurs de sécurité"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            error_code="SECURITY_ERROR",
            category=ErrorCategory.SECURITY,
            severity=ErrorSeverity.CRITICAL,
            **kwargs
        )

class RateLimitError(FinAgentException):
    """Erreurs de limite de taux"""
    
    def __init__(self, message: str, service: str, retry_after: int = None, **kwargs):
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_ERROR",
            category=ErrorCategory.EXTERNAL_API,
            severity=ErrorSeverity.MEDIUM,
            details={"service": service, "retry_after": retry_after},
            **kwargs
        )
```

## 2. Patterns de Résilience

### Circuit Breaker Pattern
```python
from enum import Enum
from typing import Callable, Any
from datetime import datetime, timedelta
import asyncio

class CircuitState(Enum):
    CLOSED = "closed"      # Fonctionnement normal
    OPEN = "open"          # Circuit ouvert, bloque les appels
    HALF_OPEN = "half_open"  # Test de récupération

class CircuitBreaker:
    """Implémentation du pattern Circuit Breaker"""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Exécute une fonction avec protection circuit breaker"""
        
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise ExternalAPIError(
                    f"Circuit breaker is OPEN for {func.__name__}",
                    service=func.__name__
                )
        
        try:
            result = await self._execute_function(func, *args, **kwargs)
            self._on_success()
            return result
            
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Vérifie si on peut tenter de fermer le circuit"""
        if self.last_failure_time is None:
            return False
        return datetime.utcnow() - self.last_failure_time >= timedelta(seconds=self.recovery_timeout)
    
    def _on_success(self):
        """Appelé en cas de succès"""
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def _on_failure(self):
        """Appelé en cas d'échec"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
    
    async def _execute_function(self, func: Callable, *args, **kwargs) -> Any:
        """Exécute la fonction de manière appropriée"""
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            return func(*args, **kwargs)

# Décorateur pour circuit breaker
def circuit_breaker(failure_threshold: int = 5, recovery_timeout: int = 60):
    def decorator(func):
        breaker = CircuitBreaker(failure_threshold, recovery_timeout)
        
        async def wrapper(*args, **kwargs):
            return await breaker.call(func, *args, **kwargs)
        
        return wrapper
    return decorator
```

### Retry Pattern avec Backoff Exponentiel
```python
import random
from typing import Type, Tuple, Callable
from tenacity import (
    retry, 
    stop_after_attempt, 
    wait_exponential, 
    retry_if_exception_type,
    before_sleep_log
)
import structlog

logger = structlog.get_logger()

class RetryConfig:
    """Configuration pour les tentatives de retry"""
    
    def __init__(
        self,
        max_attempts: int = 3,
        min_wait: float = 1.0,
        max_wait: float = 60.0,
        multiplier: float = 2.0,
        jitter: bool = True,
        retriable_exceptions: Tuple[Type[Exception], ...] = (ExternalAPIError, DataAccessError)
    ):
        self.max_attempts = max_attempts
        self.min_wait = min_wait
        self.max_wait = max_wait
        self.multiplier = multiplier
        self.jitter = jitter
        self.retriable_exceptions = retriable_exceptions

def create_retry_decorator(config: RetryConfig):
    """Crée un décorateur de retry avec configuration personnalisée"""
    
    wait_strategy = wait_exponential(
        multiplier=config.multiplier,
        min=config.min_wait,
        max=config.max_wait
    )
    
    if config.jitter:
        wait_strategy = wait_strategy + wait_exponential(
            multiplier=0.1,
            min=0,
            max=1
        )
    
    return retry(
        stop=stop_after_attempt(config.max_attempts),
        wait=wait_strategy,
        retry=retry_if_exception_type(config.retriable_exceptions),
        before_sleep=before_sleep_log(logger, log_level="WARNING")
    )

# Configurations spécialisées
MARKET_DATA_RETRY = RetryConfig(
    max_attempts=3,
    min_wait=1.0,
    max_wait=10.0,
    retriable_exceptions=(ExternalAPIError, DataAccessError)
)

AI_API_RETRY = RetryConfig(
    max_attempts=2,
    min_wait=2.0,
    max_wait=30.0,
    retriable_exceptions=(ExternalAPIError, RateLimitError)
)

DATABASE_RETRY = RetryConfig(
    max_attempts=5,
    min_wait=0.5,
    max_wait=5.0,
    retriable_exceptions=(DataAccessError,)
)
```

### Timeout et Rate Limiting
```python
import asyncio
import time
from typing import Dict, Optional
from collections import defaultdict, deque

class RateLimiter:
    """Limiteur de taux pour API externes"""
    
    def __init__(self, max_requests: int, time_window: int):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: Dict[str, deque] = defaultdict(deque)
    
    async def acquire(self, key: str) -> bool:
        """Acquiert une permission pour une requête"""
        now = time.time()
        request_times = self.requests[key]
        
        # Nettoie les anciennes requêtes
        while request_times and request_times[0] <= now - self.time_window:
            request_times.popleft()
        
        # Vérifie si on peut faire une nouvelle requête
        if len(request_times) < self.max_requests:
            request_times.append(now)
            return True
        
        return False
    
    async def wait_if_needed(self, key: str) -> None:
        """Attend si nécessaire avant de permettre une requête"""
        while not await self.acquire(key):
            await asyncio.sleep(0.1)

class TimeoutConfig:
    """Configuration des timeouts"""
    
    def __init__(
        self,
        connect_timeout: float = 10.0,
        read_timeout: float = 30.0,
        total_timeout: float = 60.0
    ):
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout
        self.total_timeout = total_timeout

async def with_timeout(coro, timeout: float):
    """Exécute une coroutine avec timeout"""
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        raise ExternalAPIError(
            f"Operation timed out after {timeout} seconds",
            service="timeout"
        )
```

## 3. Validation et Sanitisation

### Système de Validation Robuste
```python
from typing import Any, List, Union, Type
from pydantic import BaseModel, validator, ValidationError as PydanticValidationError
from decimal import Decimal

class DataValidator:
    """Validateur de données robuste"""
    
    @staticmethod
    def validate_symbol(symbol: str) -> str:
        """Valide et normalise un symbole financier"""
        if not symbol or not isinstance(symbol, str):
            raise ValidationError("Symbol must be a non-empty string", field="symbol", value=symbol)
        
        symbol = symbol.upper().strip()
        if not symbol.isalpha() or len(symbol) > 10:
            raise ValidationError("Invalid symbol format", field="symbol", value=symbol)
        
        return symbol
    
    @staticmethod
    def validate_price(price: Union[float, Decimal, str]) -> Decimal:
        """Valide et convertit un prix"""
        try:
            price_decimal = Decimal(str(price))
            if price_decimal <= 0:
                raise ValidationError("Price must be positive", field="price", value=price)
            return price_decimal
        except (ValueError, TypeError):
            raise ValidationError("Invalid price format", field="price", value=price)
    
    @staticmethod
    def validate_quantity(quantity: Union[int, float, Decimal]) -> Decimal:
        """Valide une quantité"""
        try:
            qty_decimal = Decimal(str(quantity))
            if qty_decimal < 0:
                raise ValidationError("Quantity cannot be negative", field="quantity", value=quantity)
            return qty_decimal
        except (ValueError, TypeError):
            raise ValidationError("Invalid quantity format", field="quantity", value=quantity)
    
    @staticmethod
    def sanitize_text_input(text: str, max_length: int = 1000) -> str:
        """Sanitise une entrée texte"""
        if not isinstance(text, str):
            raise ValidationError("Text input must be a string", field="text", value=text)
        
        # Supprime les caractères dangereux
        sanitized = ''.join(c for c in text if c.isprintable())
        sanitized = sanitized.strip()
        
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized

class SafeMarketData(BaseModel):
    """Modèle de données de marché avec validation robuste"""
    
    symbol: str
    timestamp: datetime
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal
    volume: int
    
    @validator('symbol')
    def validate_symbol(cls, v):
        return DataValidator.validate_symbol(v)
    
    @validator('open_price', 'high_price', 'low_price', 'close_price')
    def validate_prices(cls, v):
        return DataValidator.validate_price(v)
    
    @validator('volume')
    def validate_volume(cls, v):
        if v < 0:
            raise ValueError("Volume cannot be negative")
        return v
    
    @validator('high_price', always=True)
    def validate_price_relationships(cls, v, values):
        """Valide les relations entre les prix"""
        if 'low_price' in values and v < values['low_price']:
            raise ValueError("High price cannot be lower than low price")
        return v
```

## 4. Fallback et Récupération

### Système de Fallback pour APIs
```python
from typing import List, Callable, Any, Optional
import asyncio

class FallbackProvider:
    """Système de fallback pour providers de données"""
    
    def __init__(self, providers: List[Callable]):
        self.providers = providers
        self.current_provider_index = 0
    
    async def execute_with_fallback(self, *args, **kwargs) -> Any:
        """Exécute avec système de fallback"""
        last_exception = None
        
        for i, provider in enumerate(self.providers):
            try:
                logger.info(f"Trying provider {i}: {provider.__name__}")
                result = await self._call_provider(provider, *args, **kwargs)
                
                # Met à jour le provider préféré si ce n'est pas le premier
                if i != self.current_provider_index:
                    self.current_provider_index = i
                    logger.info(f"Switched to provider {i} as primary")
                
                return result
                
            except Exception as e:
                logger.warning(f"Provider {i} failed: {str(e)}")
                last_exception = e
                continue
        
        # Tous les providers ont échoué
        raise DataAccessError(
            f"All providers failed. Last error: {str(last_exception)}",
            source="fallback_system",
            cause=last_exception
        )
    
    async def _call_provider(self, provider: Callable, *args, **kwargs) -> Any:
        """Appelle un provider avec timeout"""
        if asyncio.iscoroutinefunction(provider):
            return await with_timeout(provider(*args, **kwargs), timeout=30.0)
        else:
            return provider(*args, **kwargs)

class HealthCheck:
    """Système de vérification de santé des services"""
    
    def __init__(self):
        self.service_health = {}
    
    async def check_service_health(self, service_name: str, health_check_func: Callable) -> bool:
        """Vérifie la santé d'un service"""
        try:
            await with_timeout(health_check_func(), timeout=10.0)
            self.service_health[service_name] = {
                'status': 'healthy',
                'last_check': datetime.utcnow(),
                'consecutive_failures': 0
            }
            return True
            
        except Exception as e:
            current_failures = self.service_health.get(service_name, {}).get('consecutive_failures', 0)
            self.service_health[service_name] = {
                'status': 'unhealthy',
                'last_check': datetime.utcnow(),
                'last_error': str(e),
                'consecutive_failures': current_failures + 1
            }
            return False
    
    def is_service_healthy(self, service_name: str) -> bool:
        """Vérifie si un service est sain"""
        health = self.service_health.get(service_name, {})
        return health.get('status') == 'healthy'
```

## 5. Logging et Monitoring d'Erreurs

### Système de Logging Structuré
```python
import structlog
from typing import Dict, Any
import traceback
import sys

class ErrorLogger:
    """Logger spécialisé pour les erreurs"""
    
    def __init__(self):
        self.logger = structlog.get_logger(__name__)
    
    def log_error(
        self,
        exception: Exception,
        context: Dict[str, Any] = None,
        user_id: str = None,
        operation: str = None
    ):
        """Log une erreur avec contexte complet"""
        
        error_data = {
            "error_type": type(exception).__name__,
            "error_message": str(exception),
            "operation": operation,
            "user_id": user_id,
            "context": context or {},
            "traceback": traceback.format_exc()
        }
        
        # Ajoute des détails spécifiques si c'est une FinAgentException
        if isinstance(exception, FinAgentException):
            error_data.update(exception.to_dict())
        
        # Log selon la sévérité
        if isinstance(exception, FinAgentException):
            if exception.severity == ErrorSeverity.CRITICAL:
                self.logger.critical("Critical error occurred", **error_data)
            elif exception.severity == ErrorSeverity.HIGH:
                self.logger.error("High severity error", **error_data)
            elif exception.severity == ErrorSeverity.MEDIUM:
                self.logger.warning("Medium severity error", **error_data)
            else:
                self.logger.info("Low severity error", **error_data)
        else:
            self.logger.error("Unhandled exception", **error_data)
    
    def log_performance_issue(
        self,
        operation: str,
        duration: float,
        threshold: float,
        context: Dict[str, Any] = None
    ):
        """Log un problème de performance"""
        self.logger.warning(
            "Performance issue detected",
            operation=operation,
            duration=duration,
            threshold=threshold,
            context=context or {}
        )

class MetricsCollector:
    """Collecteur de métriques d'erreurs"""
    
    def __init__(self):
        self.error_counts = defaultdict(int)
        self.error_rates = defaultdict(list)
    
    def record_error(self, error_type: str, service: str = None):
        """Enregistre une erreur"""
        key = f"{service or 'unknown'}:{error_type}"
        self.error_counts[key] += 1
        self.error_rates[key].append(datetime.utcnow())
    
    def get_error_rate(self, error_type: str, time_window: int = 3600) -> float:
        """Calcule le taux d'erreur sur une fenêtre de temps"""
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=time_window)
        
        recent_errors = [
            ts for ts in self.error_rates.get(error_type, [])
            if ts > cutoff
        ]
        
        return len(recent_errors) / time_window * 3600  # Erreurs par heure
```

## 6. Gestion des États Dégradés

### Mode Dégradé
```python
from enum import Enum
from typing import Set

class ServiceMode(Enum):
    NORMAL = "normal"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"
    EMERGENCY = "emergency"

class DegradedModeManager:
    """Gestionnaire du mode dégradé"""
    
    def __init__(self):
        self.current_mode = ServiceMode.NORMAL
        self.disabled_features: Set[str] = set()
        self.fallback_configs = {}
    
    def enable_degraded_mode(self, reason: str, disabled_features: List[str] = None):
        """Active le mode dégradé"""
        self.current_mode = ServiceMode.DEGRADED
        self.disabled_features.update(disabled_features or [])
        
        logger.warning(
            "Degraded mode enabled",
            reason=reason,
            disabled_features=list(self.disabled_features)
        )
    
    def is_feature_available(self, feature: str) -> bool:
        """Vérifie si une fonctionnalité est disponible"""
        if self.current_mode == ServiceMode.EMERGENCY:
            return feature in ["basic_portfolio", "emergency_stop"]
        
        return feature not in self.disabled_features
    
    def get_fallback_config(self, service: str) -> Dict[str, Any]:
        """Récupère la configuration de fallback"""
        return self.fallback_configs.get(service, {})

# Configuration des modes dégradés
DEGRADED_MODE_CONFIGS = {
    "ai_service_down": {
        "disabled_features": ["ai_analysis", "sentiment_analysis"],
        "fallback_strategy": "technical_only"
    },
    "market_data_limited": {
        "disabled_features": ["realtime_data", "advanced_indicators"],
        "fallback_strategy": "cached_data_only"
    },
    "high_error_rate": {
        "disabled_features": ["automated_trading", "real_money_mode"],
        "fallback_strategy": "simulation_only"
    }
}
```

## 7. Système d'Alertes et Notifications

### Gestionnaire d'Alertes
```python
from typing import List, Callable
from enum import Enum

class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class Alert(BaseModel):
    """Modèle d'alerte"""
    id: str
    level: AlertLevel
    title: str
    message: str
    source: str
    timestamp: datetime
    context: Dict[str, Any]
    resolved: bool = False

class AlertManager:
    """Gestionnaire d'alertes"""
    
    def __init__(self):
        self.alert_handlers: List[Callable] = []
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
    
    def register_handler(self, handler: Callable):
        """Enregistre un gestionnaire d'alerte"""
        self.alert_handlers.append(handler)
    
    async def send_alert(self, alert: Alert):
        """Envoie une alerte"""
        self.active_alerts[alert.id] = alert
        self.alert_history.append(alert)
        
        # Notifie tous les handlers
        for handler in self.alert_handlers:
            try:
                await handler(alert)
            except Exception as e:
                logger.error(f"Alert handler failed: {e}")
    
    async def resolve_alert(self, alert_id: str):
        """Résout une alerte"""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].resolved = True
            del self.active_alerts[alert_id]

class EmailAlertHandler:
    """Gestionnaire d'alertes par email"""
    
    async def __call__(self, alert: Alert):
        if alert.level in [AlertLevel.ERROR, AlertLevel.CRITICAL]:
            await self._send_email(alert)
    
    async def _send_email(self, alert: Alert):
        """Envoie un email d'alerte"""
        # Implémentation de l'envoi d'email
        pass

class CLIAlertHandler:
    """Gestionnaire d'alertes pour CLI"""
    
    async def __call__(self, alert: Alert):
        color = {
            AlertLevel.INFO: "blue",
            AlertLevel.WARNING: "yellow",
            AlertLevel.ERROR: "red",
            AlertLevel.CRITICAL: "bright_red"
        }.get(alert.level, "white")
        
        rich_console.print(f"[{color}]ALERT: {alert.title}[/{color}]")
        rich_console.print(f"  {alert.message}")
```

## 8. Récupération Automatique

### Système de Auto-Healing
```python
class AutoHealingManager:
    """Gestionnaire de récupération automatique"""
    
    def __init__(self):
        self.healing_strategies = {}
        self.recovery_attempts = defaultdict(int)
        
    def register_healing_strategy(self, error_type: Type[Exception], strategy: Callable):
        """Enregistre une stratégie de récupération"""
        self.healing_strategies[error_type] = strategy
    
    async def attempt_healing(self, exception: Exception, context: Dict[str, Any]) -> bool:
        """Tente une récupération automatique"""
        error_type = type(exception)
        
        if error_type not in self.healing_strategies:
            return False
        
        # Limite le nombre de tentatives
        attempt_key = f"{error_type.__name__}:{context.get('operation', 'unknown')}"
        if self.recovery_attempts[attempt_key] >= 3:
            logger.warning(f"Max recovery attempts reached for {attempt_key}")
            return False
        
        try:
            self.recovery_attempts[attempt_key] += 1
            strategy = self.healing_strategies[error_type]
            success = await strategy(exception, context)
            
            if success:
                logger.info(f"Auto-healing successful for {error_type.__name__}")
                self.recovery_attempts[attempt_key] = 0  # Reset counter
            
            return success
            
        except Exception as healing_error:
            logger.error(f"Auto-healing failed: {healing_error}")
            return False

# Stratégies de récupération
async def heal_database_connection(exception: DataAccessError, context: Dict[str, Any]) -> bool:
    """Récupère une connexion base de données"""
    try:
        # Reconnexion à la base de données
        database_manager = context.get('database_manager')
        if database_manager:
            await database_manager.reconnect()
            return True
    except Exception:
        pass
    return False

async def heal_api_rate_limit(exception: RateLimitError, context: Dict[str, Any]) -> bool:
    """Récupère d'une limite de taux"""
    retry_after = exception.details.get('retry_after', 60)
    logger.info(f"Rate limit hit, waiting {retry_after} seconds")
    await asyncio.sleep(retry_after)
    return True

async def heal_cache_corruption(exception: DataAccessError, context: Dict[str, Any]) -> bool:
    """Récupère d'une corruption de cache"""
    if 'cache' in context:
        cache = context['cache']
        await cache.clear()
        logger.info("Cache cleared due to corruption")
        return True
    return False
```

## 9. Monitoring et Métriques

### Dashboard de Santé du Système
```python
class SystemHealthDashboard:
    """Dashboard de santé du système"""
    
    def __init__(self):
        self.metrics = {}
        self.last_update = datetime.utcnow()
    
    async def collect_metrics(self) -> Dict[str, Any]:
        """Collecte les métriques de santé"""
        return {
            "error_rates": await self._get_error_rates(),
            "service_availability": await self._get_service_availability(),
            "performance_metrics": await self._get_performance_metrics(),
            "resource_usage": await self._get_resource_usage(),
            "active_alerts": len(alert_manager.active_alerts),
            "last_update": self.last_update.isoformat()
        }
    
    async def _get_error_rates(self) -> Dict[str, float]:
        """Récupère les taux d'erreur"""
        return {
            "total_error_rate": metrics_collector.get_error_rate("total"),
            "api_error_rate": metrics_collector.get_error_rate("api_error"),
            "validation_error_rate": metrics_collector.get_error_rate("validation_error")
        }
    
    async def _get_service_availability(self) -> Dict[str, str]:
        """Récupère la disponibilité des services"""
        return {
            service: "healthy" if health_checker.is_service_healthy(service) else "unhealthy"
            for service in ["openbb", "claude", "database", "cache"]
        }
```

Cette architecture de gestion d'erreurs offre :
- **Résilience** : Circuit breakers et fallbacks automatiques
- **Observabilité** : Logging structuré et métriques détaillées
- **Récupération** : Auto-healing et modes dégradés
- **Prévention** : Validation robuste et rate limiting
- **Alertes** : Système d'alertes multi-canal configurable