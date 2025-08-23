"""
Utilitaires et helpers pour les tests FinAgent.

Ce module contient des fonctions utilitaires communes utilisées
dans l'ensemble des tests pour simplifier et standardiser les opérations.
"""

import asyncio
import json
import os
import tempfile
import time
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, AsyncGenerator, Generator
from unittest.mock import Mock, AsyncMock, patch
from uuid import UUID, uuid4

import pytest
import yaml
from freezegun import freeze_time

from finagent.core.errors.exceptions import FinAgentException
from finagent.ai.models.base import AIRequest, AIResponse, ModelType


# ============================================================================
# ASSERTIONS CUSTOMISÉES
# ============================================================================

def assert_valid_uuid(value: Union[str, UUID]) -> bool:
    """Vérifie qu'une valeur est un UUID valide."""
    try:
        if isinstance(value, str):
            UUID(value)
        elif isinstance(value, UUID):
            pass  # Déjà un UUID
        else:
            return False
        return True
    except (ValueError, TypeError):
        return False


def assert_decimal_equals(actual: Decimal, expected: Decimal, precision: int = 2) -> bool:
    """Compare deux décimaux avec une précision donnée."""
    multiplier = Decimal(10) ** precision
    actual_rounded = (actual * multiplier).to_integral_value() / multiplier
    expected_rounded = (expected * multiplier).to_integral_value() / multiplier
    return actual_rounded == expected_rounded


def assert_datetime_close(actual: datetime, expected: datetime, delta_seconds: int = 5) -> bool:
    """Vérifie que deux dates sont proches à quelques secondes près."""
    diff = abs((actual - expected).total_seconds())
    return diff <= delta_seconds


def assert_portfolio_valid(portfolio_data: Dict[str, Any]) -> bool:
    """Vérifie qu'un portefeuille a une structure valide."""
    required_fields = ['id', 'name', 'cash', 'total_value']
    
    for field in required_fields:
        if field not in portfolio_data:
            return False
    
    # Vérifications de cohérence
    if portfolio_data['cash'] < 0:
        return False
    
    if portfolio_data['total_value'] < portfolio_data['cash']:
        return False
    
    return True


def assert_stock_data_valid(stock_data: Dict[str, Any]) -> bool:
    """Vérifie qu'une donnée d'action a une structure valide."""
    required_fields = ['symbol', 'price', 'volume']
    
    for field in required_fields:
        if field not in stock_data:
            return False
    
    # Vérifications de cohérence
    if stock_data['price'] <= 0:
        return False
    
    if stock_data['volume'] < 0:
        return False
    
    return True


# ============================================================================
# CONTEXT MANAGERS
# ============================================================================

@contextmanager
def temporary_config_file(config_data: Dict[str, Any]) -> Generator[Path, None, None]:
    """Crée un fichier de configuration temporaire."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config_data, f, default_flow_style=False)
        temp_path = Path(f.name)
    
    try:
        yield temp_path
    finally:
        if temp_path.exists():
            temp_path.unlink()


@contextmanager
def temporary_directory() -> Generator[Path, None, None]:
    """Crée un répertoire temporaire."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@contextmanager
def mock_environment_variables(**env_vars) -> Generator[None, None, None]:
    """Mock des variables d'environnement temporaires."""
    original_values = {}
    
    # Sauvegarde les valeurs originales
    for key in env_vars:
        original_values[key] = os.environ.get(key)
        os.environ[key] = str(env_vars[key])
    
    try:
        yield
    finally:
        # Restaure les valeurs originales
        for key, original_value in original_values.items():
            if original_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original_value


@asynccontextmanager
async def async_timer() -> AsyncGenerator[Dict[str, float], None]:
    """Context manager pour mesurer le temps d'exécution async."""
    start_time = time.time()
    timing_info = {"start": start_time}
    
    try:
        yield timing_info
    finally:
        end_time = time.time()
        timing_info.update({
            "end": end_time,
            "duration": end_time - start_time
        })


@contextmanager
def capture_logs(logger_name: str = None) -> Generator[List[str], None, None]:
    """Capture les logs pour vérification dans les tests."""
    import logging
    from io import StringIO
    
    # Crée un handler pour capturer les logs
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    
    # Configure le logger
    logger = logging.getLogger(logger_name) if logger_name else logging.getLogger()
    original_level = logger.level
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    
    captured_logs = []
    
    try:
        yield captured_logs
        # Récupère les logs capturés
        log_contents = log_capture.getvalue()
        captured_logs.extend(log_contents.strip().split('\n') if log_contents.strip() else [])
    finally:
        logger.removeHandler(handler)
        logger.setLevel(original_level)
        log_capture.close()


# ============================================================================
# HELPERS POUR DONNÉES DE TEST
# ============================================================================

def create_sample_ai_request(prompt: str = "Test prompt", **kwargs) -> AIRequest:
    """Crée une requête IA échantillon."""
    defaults = {
        "prompt": prompt,
        "model_type": ModelType.CLAUDE_3_SONNET,
        "temperature": 0.3,
        "max_tokens": 2000,
        "context": {"test": True}
    }
    defaults.update(kwargs)
    return AIRequest(**defaults)


def create_sample_ai_response(request_id: UUID = None, **kwargs) -> AIResponse:
    """Crée une réponse IA échantillon."""
    defaults = {
        "request_id": request_id or uuid4(),
        "content": "Sample AI response content for testing purposes.",
        "model_used": ModelType.CLAUDE_3_SONNET,
        "tokens_used": 150,
        "processing_time": 1.5,
        "confidence": "medium"
    }
    defaults.update(kwargs)
    return AIResponse(**defaults)


def create_sample_stock_data(symbol: str = "AAPL", **kwargs) -> Dict[str, Any]:
    """Crée des données d'action échantillon."""
    defaults = {
        "symbol": symbol,
        "name": f"{symbol} Corporation",
        "price": 150.25,
        "change": 2.50,
        "change_percent": 1.69,
        "volume": 45_000_000,
        "market_cap": 2_500_000_000_000,
        "pe_ratio": 25.3,
        "dividend_yield": 0.5
    }
    defaults.update(kwargs)
    return defaults


def create_sample_portfolio(**kwargs) -> Dict[str, Any]:
    """Crée un portefeuille échantillon."""
    defaults = {
        "id": uuid4(),
        "name": "Test Portfolio",
        "cash": Decimal("10000.00"),
        "total_value": Decimal("15000.00"),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    defaults.update(kwargs)
    return defaults


def create_sample_position(symbol: str = "AAPL", **kwargs) -> Dict[str, Any]:
    """Crée une position échantillon."""
    defaults = {
        "id": uuid4(),
        "symbol": symbol,
        "quantity": 100,
        "average_cost": Decimal("140.00"),
        "current_price": Decimal("150.25"),
        "opened_at": datetime.utcnow() - timedelta(days=30)
    }
    defaults.update(kwargs)
    return defaults


# ============================================================================
# HELPERS POUR TESTS ASYNCHRONES
# ============================================================================

async def wait_for_condition(
    condition_func, 
    timeout: float = 5.0, 
    check_interval: float = 0.1
) -> bool:
    """Attend qu'une condition soit vraie ou timeout."""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        if await condition_func() if asyncio.iscoroutinefunction(condition_func) else condition_func():
            return True
        await asyncio.sleep(check_interval)
    
    return False


async def run_with_timeout(coro, timeout: float = 5.0):
    """Exécute une coroutine avec timeout."""
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        pytest.fail(f"Operation timed out after {timeout} seconds")


def make_async_test(timeout: float = 10.0):
    """Décorateur pour tests asynchrones avec timeout."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            return await run_with_timeout(func(*args, **kwargs), timeout)
        return wrapper
    return decorator


# ============================================================================
# HELPERS POUR VALIDATION
# ============================================================================

def validate_json_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """Valide des données contre un schéma JSON."""
    try:
        import jsonschema
        jsonschema.validate(data, schema)
        return True
    except ImportError:
        pytest.skip("jsonschema not available")
    except jsonschema.ValidationError:
        return False


def validate_decimal_precision(value: Decimal, expected_places: int) -> bool:
    """Valide qu'un décimal a le bon nombre de décimales."""
    _, digits, exponent = value.as_tuple()
    return abs(exponent) == expected_places


def validate_date_range(date_value: datetime, start: datetime, end: datetime) -> bool:
    """Valide qu'une date est dans une plage donnée."""
    return start <= date_value <= end


# ============================================================================
# HELPERS POUR MOCKING
# ============================================================================

def create_mock_async_context_manager(return_value=None):
    """Crée un context manager asynchrone mock."""
    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = return_value
    mock_cm.__aexit__.return_value = None
    return mock_cm


def patch_async_method(target: str, return_value=None, side_effect=None):
    """Patch une méthode asynchrone."""
    mock = AsyncMock()
    if return_value is not None:
        mock.return_value = return_value
    if side_effect is not None:
        mock.side_effect = side_effect
    return patch(target, mock)


def create_mock_http_response(status_code: int = 200, json_data: Dict = None, text_data: str = None):
    """Crée une réponse HTTP mock."""
    mock_response = Mock()
    mock_response.status_code = status_code
    mock_response.json.return_value = json_data or {}
    mock_response.text = text_data or json.dumps(json_data or {})
    mock_response.headers = {"Content-Type": "application/json"}
    return mock_response


# ============================================================================
# HELPERS POUR BENCHMARKING
# ============================================================================

class PerformanceTimer:
    """Timer pour mesurer les performances."""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.measurements = []
    
    def start(self):
        """Démarre le timer."""
        self.start_time = time.perf_counter()
    
    def stop(self):
        """Arrête le timer."""
        self.end_time = time.perf_counter()
        if self.start_time:
            duration = self.end_time - self.start_time
            self.measurements.append(duration)
            return duration
        return 0
    
    def average(self) -> float:
        """Retourne le temps moyen."""
        return sum(self.measurements) / len(self.measurements) if self.measurements else 0
    
    def reset(self):
        """Remet à zéro les mesures."""
        self.measurements.clear()
        self.start_time = None
        self.end_time = None


@contextmanager
def performance_benchmark(name: str = "test") -> Generator[PerformanceTimer, None, None]:
    """Context manager pour benchmark de performance."""
    timer = PerformanceTimer()
    timer.start()
    
    try:
        yield timer
    finally:
        duration = timer.stop()
        print(f"Benchmark '{name}': {duration:.4f} seconds")


# ============================================================================
# HELPERS POUR DONNÉES DE FIXTURES
# ============================================================================

def load_test_data(filename: str) -> Dict[str, Any]:
    """Charge des données de test depuis un fichier JSON."""
    test_data_dir = Path(__file__).parent.parent / "fixtures" / "data"
    file_path = test_data_dir / filename
    
    if not file_path.exists():
        pytest.skip(f"Test data file not found: {filename}")
    
    with open(file_path, 'r') as f:
        if filename.endswith('.json'):
            return json.load(f)
        elif filename.endswith('.yaml') or filename.endswith('.yml'):
            return yaml.safe_load(f)
        else:
            return {"content": f.read()}


def save_test_data(data: Dict[str, Any], filename: str):
    """Sauvegarde des données de test dans un fichier."""
    test_data_dir = Path(__file__).parent.parent / "fixtures" / "data"
    test_data_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = test_data_dir / filename
    
    with open(file_path, 'w') as f:
        if filename.endswith('.json'):
            json.dump(data, f, indent=2, default=str)
        elif filename.endswith('.yaml') or filename.endswith('.yml'):
            yaml.dump(data, f, default_flow_style=False)
        else:
            f.write(str(data))


# ============================================================================
# HELPERS POUR NETTOYAGE
# ============================================================================

def cleanup_test_files(pattern: str = "test_*"):
    """Nettoie les fichiers de test temporaires."""
    temp_dir = Path(tempfile.gettempdir())
    for file_path in temp_dir.glob(pattern):
        try:
            if file_path.is_file():
                file_path.unlink()
            elif file_path.is_dir():
                import shutil
                shutil.rmtree(file_path)
        except OSError:
            pass  # Ignore les erreurs de nettoyage


def reset_singletons():
    """Remet à zéro les singletons pour les tests."""
    # À adapter selon les singletons présents dans FinAgent
    pass


# ============================================================================
# DECORATORS UTILES
# ============================================================================

def skip_if_no_api_key(provider: str):
    """Skip le test si la clé API n'est pas disponible."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            env_var = f"FINAGENT_{provider.upper()}_API_KEY"
            if not os.getenv(env_var):
                pytest.skip(f"No API key found for {provider} (set {env_var})")
            return func(*args, **kwargs)
        return wrapper
    return decorator


def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """Retry un test en cas d'échec."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        time.sleep(delay)
                    
            # Si tous les essais ont échoué, lève la dernière exception
            raise last_exception
        return wrapper
    return decorator