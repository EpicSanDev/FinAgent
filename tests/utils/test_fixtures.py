"""
Fixtures pytest réutilisables pour FinAgent.

Ce module contient des fixtures spécialisées pour différents composants
et des factories pour créer des objets de test complexes.
"""

import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Optional
from uuid import uuid4, UUID
from unittest.mock import Mock, AsyncMock

import pytest
from faker import Faker
import factory
from factory import fuzzy

from finagent.ai.models.base import (
    AIRequest, AIResponse, ModelType, ConfidenceLevel, TokenUsage
)
from finagent.business.models.decision_models import (
    DecisionContext, DecisionResult, DecisionAction, RiskAssessment
)
from finagent.business.models.portfolio_models import (
    Portfolio, Position, Transaction, TransactionType
)
from finagent.business.strategy.models.strategy_models import (
    StrategyType, RiskTolerance, TimeHorizon
)

fake = Faker()
Faker.seed(42)  # Seed fixe pour reproductibilité


# ============================================================================
# FACTORIES POUR DONNÉES FINANCIÈRES
# ============================================================================

class StockDataFactory(factory.DictFactory):
    """Factory pour données d'actions."""
    
    symbol = factory.LazyFunction(lambda: fake.random_element(['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']))
    name = factory.LazyAttribute(lambda obj: f"{obj['symbol']} Corporation")
    price = fuzzy.FuzzyDecimal(50.0, 500.0, precision=2)
    change = fuzzy.FuzzyDecimal(-10.0, 10.0, precision=2)
    change_percent = factory.LazyAttribute(lambda obj: (obj['change'] / obj['price']) * 100)
    volume = fuzzy.FuzzyInteger(1_000_000, 100_000_000)
    market_cap = fuzzy.FuzzyInteger(1_000_000_000, 3_000_000_000_000)
    pe_ratio = fuzzy.FuzzyDecimal(10.0, 50.0, precision=1)
    dividend_yield = fuzzy.FuzzyDecimal(0.0, 5.0, precision=2)
    week_52_high = factory.LazyAttribute(lambda obj: obj['price'] * Decimal('1.2'))
    week_52_low = factory.LazyAttribute(lambda obj: obj['price'] * Decimal('0.8'))


class TechnicalIndicatorsFactory(factory.DictFactory):
    """Factory pour indicateurs techniques."""
    
    rsi = fuzzy.FuzzyDecimal(20.0, 80.0, precision=1)
    macd = fuzzy.FuzzyDecimal(-2.0, 2.0, precision=3)
    macd_signal = fuzzy.FuzzyDecimal(-2.0, 2.0, precision=3)
    bb_upper = fuzzy.FuzzyDecimal(150.0, 200.0, precision=2)
    bb_middle = fuzzy.FuzzyDecimal(140.0, 160.0, precision=2)
    bb_lower = fuzzy.FuzzyDecimal(130.0, 150.0, precision=2)
    sma_20 = fuzzy.FuzzyDecimal(140.0, 160.0, precision=2)
    sma_50 = fuzzy.FuzzyDecimal(135.0, 155.0, precision=2)
    sma_200 = fuzzy.FuzzyDecimal(130.0, 150.0, precision=2)
    ema_12 = fuzzy.FuzzyDecimal(145.0, 165.0, precision=2)
    ema_26 = fuzzy.FuzzyDecimal(140.0, 160.0, precision=2)
    volume_sma = fuzzy.FuzzyInteger(30_000_000, 80_000_000)


class NewsDataFactory(factory.DictFactory):
    """Factory pour données de news."""
    
    title = factory.LazyFunction(lambda: fake.sentence(nb_words=8)[:-1])
    content = factory.LazyFunction(lambda: fake.text(max_nb_chars=500))
    published_at = factory.LazyFunction(lambda: fake.date_time_between(start_date='-7d', end_date='now'))
    source = factory.LazyFunction(lambda: fake.random_element([
        'Reuters', 'Bloomberg', 'Financial Times', 'Wall Street Journal', 'MarketWatch'
    ]))
    sentiment = factory.LazyFunction(lambda: fake.random_element(['positive', 'negative', 'neutral']))
    relevance = fuzzy.FuzzyDecimal(0.1, 1.0, precision=2)
    url = factory.LazyFunction(lambda: fake.url())


# ============================================================================
# FACTORIES POUR MODÈLES IA
# ============================================================================

class AIRequestFactory(factory.Factory):
    """Factory pour requêtes IA."""
    
    class Meta:
        model = AIRequest
    
    prompt = factory.LazyFunction(lambda: fake.text(max_nb_chars=200))
    model_type = factory.LazyFunction(lambda: fake.random_element(list(ModelType)))
    temperature = fuzzy.FuzzyDecimal(0.0, 1.0, precision=1)
    max_tokens = fuzzy.FuzzyInteger(1000, 8000)
    context = factory.LazyFunction(lambda: {"symbol": fake.random_element(['AAPL', 'MSFT'])})


class AIResponseFactory(factory.Factory):
    """Factory pour réponses IA."""
    
    class Meta:
        model = AIResponse
    
    request_id = factory.LazyFunction(uuid4)
    content = factory.LazyFunction(lambda: fake.text(max_nb_chars=1000))
    model_used = factory.LazyFunction(lambda: fake.random_element(list(ModelType)))
    tokens_used = fuzzy.FuzzyInteger(100, 2000)
    processing_time = fuzzy.FuzzyDecimal(0.5, 5.0, precision=2)
    confidence = factory.LazyFunction(lambda: fake.random_element(list(ConfidenceLevel)))
    metadata = factory.LazyFunction(lambda: {"temperature": 0.3, "model_version": "1.0"})


class TokenUsageFactory(factory.Factory):
    """Factory pour utilisation des tokens."""
    
    class Meta:
        model = TokenUsage
    
    prompt_tokens = fuzzy.FuzzyInteger(50, 500)
    completion_tokens = fuzzy.FuzzyInteger(100, 1000)
    total_tokens = factory.LazyAttribute(lambda obj: obj.prompt_tokens + obj.completion_tokens)
    estimated_cost = factory.LazyAttribute(lambda obj: obj.total_tokens * Decimal('0.0001'))


# ============================================================================
# FACTORIES POUR BUSINESS MODELS
# ============================================================================

class PositionFactory(factory.Factory):
    """Factory pour positions de portefeuille."""
    
    class Meta:
        model = Position
    
    id = factory.LazyFunction(uuid4)
    symbol = factory.LazyFunction(lambda: fake.random_element(['AAPL', 'MSFT', 'GOOGL']))
    quantity = fuzzy.FuzzyInteger(1, 1000)
    average_cost = fuzzy.FuzzyDecimal(50.0, 300.0, precision=2)
    current_price = factory.LazyAttribute(lambda obj: obj.average_cost * Decimal(fake.random.uniform(0.8, 1.2)))
    opened_at = factory.LazyFunction(lambda: fake.date_time_between(start_date='-1y', end_date='now'))


class TransactionFactory(factory.Factory):
    """Factory pour transactions."""
    
    class Meta:
        model = Transaction
    
    id = factory.LazyFunction(uuid4)
    symbol = factory.LazyFunction(lambda: fake.random_element(['AAPL', 'MSFT', 'GOOGL']))
    transaction_type = factory.LazyFunction(lambda: fake.random_element(list(TransactionType)))
    quantity = fuzzy.FuzzyInteger(1, 100)
    price = fuzzy.FuzzyDecimal(50.0, 300.0, precision=2)
    total_amount = factory.LazyAttribute(lambda obj: obj.quantity * obj.price)
    executed_at = factory.LazyFunction(lambda: fake.date_time_between(start_date='-30d', end_date='now'))


class PortfolioFactory(factory.Factory):
    """Factory pour portefeuilles."""
    
    class Meta:
        model = Portfolio
    
    id = factory.LazyFunction(uuid4)
    name = factory.LazyFunction(lambda: f"Portfolio {fake.word().title()}")
    cash = fuzzy.FuzzyDecimal(1000.0, 100000.0, precision=2)
    total_value = factory.LazyAttribute(lambda obj: obj.cash * Decimal(fake.random.uniform(1.1, 2.0)))
    created_at = factory.LazyFunction(lambda: fake.date_time_between(start_date='-2y', end_date='-1y'))
    updated_at = factory.LazyFunction(lambda: fake.date_time_between(start_date='-1d', end_date='now'))


class DecisionResultFactory(factory.Factory):
    """Factory pour résultats de décision."""
    
    class Meta:
        model = DecisionResult
    
    id = factory.LazyFunction(uuid4)
    symbol = factory.LazyFunction(lambda: fake.random_element(['AAPL', 'MSFT', 'GOOGL']))
    action = factory.LazyFunction(lambda: fake.random_element(list(DecisionAction)))
    confidence = factory.LazyFunction(lambda: fake.random_element(list(ConfidenceLevel)))
    reasoning = factory.LazyFunction(lambda: fake.text(max_nb_chars=300))
    risk_score = fuzzy.FuzzyDecimal(0.0, 1.0, precision=2)
    expected_return = fuzzy.FuzzyDecimal(-0.2, 0.3, precision=3)
    time_horizon = fuzzy.FuzzyInteger(1, 365)
    created_at = factory.LazyFunction(datetime.utcnow)


# ============================================================================
# FIXTURES SPÉCIALISÉES
# ============================================================================

@pytest.fixture
def stock_data_sample():
    """Échantillon de données d'actions."""
    return StockDataFactory()


@pytest.fixture
def technical_indicators_sample():
    """Échantillon d'indicateurs techniques."""
    return TechnicalIndicatorsFactory()


@pytest.fixture
def news_data_sample():
    """Échantillon de données de news."""
    return [NewsDataFactory() for _ in range(3)]


@pytest.fixture
def ai_request_sample():
    """Échantillon de requête IA."""
    return AIRequestFactory()


@pytest.fixture
def ai_response_sample():
    """Échantillon de réponse IA."""
    return AIResponseFactory()


@pytest.fixture
def portfolio_sample():
    """Échantillon de portefeuille avec positions."""
    portfolio = PortfolioFactory()
    positions = [PositionFactory() for _ in range(3)]
    transactions = [TransactionFactory() for _ in range(5)]
    return {
        'portfolio': portfolio,
        'positions': positions,
        'transactions': transactions
    }


@pytest.fixture
def decision_context_sample():
    """Échantillon de contexte de décision."""
    return {
        'symbol': 'AAPL',
        'stock_data': StockDataFactory(symbol='AAPL'),
        'technical_indicators': TechnicalIndicatorsFactory(),
        'news': [NewsDataFactory() for _ in range(2)],
        'portfolio': PortfolioFactory(),
        'strategy_config': {
            'name': 'Test Strategy',
            'type': StrategyType.TECHNICAL,
            'risk_tolerance': RiskTolerance.MEDIUM,
            'time_horizon': TimeHorizon.MEDIUM
        }
    }


@pytest.fixture
def mock_market_data():
    """Données de marché mock complètes."""
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']
    return {
        symbol: {
            'stock_data': StockDataFactory(symbol=symbol),
            'indicators': TechnicalIndicatorsFactory(),
            'news': [NewsDataFactory() for _ in range(2)]
        }
        for symbol in symbols
    }


@pytest.fixture
def strategy_configs_sample():
    """Échantillons de configurations de stratégies."""
    return [
        {
            'name': 'Momentum Strategy',
            'type': StrategyType.TECHNICAL,
            'risk_tolerance': RiskTolerance.HIGH,
            'time_horizon': TimeHorizon.SHORT,
            'rules': [
                {
                    'name': 'RSI Momentum',
                    'conditions': [{'indicator': 'rsi', 'operator': '>', 'value': 70}],
                    'action': 'sell',
                    'weight': 0.8
                }
            ]
        },
        {
            'name': 'Value Strategy', 
            'type': StrategyType.FUNDAMENTAL,
            'risk_tolerance': RiskTolerance.LOW,
            'time_horizon': TimeHorizon.LONG,
            'rules': [
                {
                    'name': 'Low PE',
                    'conditions': [{'indicator': 'pe_ratio', 'operator': '<', 'value': 15}],
                    'action': 'buy',
                    'weight': 0.6
                }
            ]
        }
    ]


@pytest.fixture
def performance_metrics_sample():
    """Échantillon de métriques de performance."""
    return {
        'total_return': Decimal('0.15'),
        'annualized_return': Decimal('0.12'),
        'volatility': Decimal('0.18'),
        'sharpe_ratio': Decimal('0.67'),
        'max_drawdown': Decimal('-0.08'),
        'win_rate': Decimal('0.65'),
        'profit_factor': Decimal('1.35'),
        'calmar_ratio': Decimal('1.5'),
        'sortino_ratio': Decimal('0.89')
    }


# ============================================================================
# UTILITIES POUR CRÉATION D'OBJETS COMPLEXES
# ============================================================================

def create_test_portfolio_with_positions(num_positions: int = 3) -> Dict[str, Any]:
    """Crée un portefeuille de test avec positions."""
    portfolio = PortfolioFactory()
    positions = [PositionFactory() for _ in range(num_positions)]
    transactions = [TransactionFactory() for _ in range(num_positions * 2)]
    
    return {
        'portfolio': portfolio,
        'positions': positions,
        'transactions': transactions,
        'metrics': {
            'total_value': sum(pos.quantity * pos.current_price for pos in positions) + portfolio.cash,
            'total_cost': sum(pos.quantity * pos.average_cost for pos in positions),
            'unrealized_pnl': sum(pos.quantity * (pos.current_price - pos.average_cost) for pos in positions)
        }
    }


def create_test_market_scenario(scenario_type: str = 'normal') -> Dict[str, Any]:
    """Crée un scénario de marché pour tests."""
    scenarios = {
        'bull_market': {
            'price_multiplier': 1.2,
            'volume_multiplier': 1.5,
            'sentiment': 'positive'
        },
        'bear_market': {
            'price_multiplier': 0.8,
            'volume_multiplier': 1.3,
            'sentiment': 'negative'
        },
        'volatile': {
            'price_multiplier': 1.0,
            'volume_multiplier': 2.0,
            'sentiment': 'neutral'
        },
        'normal': {
            'price_multiplier': 1.0,
            'volume_multiplier': 1.0,
            'sentiment': 'neutral'
        }
    }
    
    config = scenarios.get(scenario_type, scenarios['normal'])
    
    return {
        'scenario': scenario_type,
        'config': config,
        'symbols': ['AAPL', 'MSFT', 'GOOGL'],
        'data': {
            symbol: StockDataFactory(
                symbol=symbol,
                price=Decimal(str(150.0 * config['price_multiplier'])),
                volume=int(50_000_000 * config['volume_multiplier'])
            )
            for symbol in ['AAPL', 'MSFT', 'GOOGL']
        }
    }


def create_test_strategy_execution(strategy_name: str, num_signals: int = 5) -> Dict[str, Any]:
    """Crée une exécution de stratégie pour tests."""
    return {
        'strategy_name': strategy_name,
        'execution_id': uuid4(),
        'started_at': datetime.utcnow() - timedelta(hours=1),
        'completed_at': datetime.utcnow(),
        'signals': [DecisionResultFactory() for _ in range(num_signals)],
        'performance': {
            'signals_generated': num_signals,
            'successful_trades': fake.random.randint(0, num_signals),
            'total_return': Decimal(str(fake.random.uniform(-0.1, 0.2))),
            'execution_time': fake.random.uniform(0.5, 5.0)
        }
    }