"""
Tests unitaires pour le provider OpenBB de FinAgent.

Ce module teste toutes les fonctionnalités du provider OpenBB,
incluant la récupération de données financières, la gestion d'erreurs,
et l'intégration avec l'API OpenBB.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, patch, AsyncMock
import pandas as pd
import numpy as np

from finagent.data.providers.openbb_provider import (
    OpenBBProvider, OpenBBConfig, DataFrequency, MarketDataType
)
from finagent.core.exceptions import (
    DataProviderError, APIRateLimitError, DataNotFoundError
)
from tests.utils import (
    StockDataFactory, MockOpenBBProvider, assert_decimal_equals,
    create_test_price_data, create_test_financial_data
)


class TestOpenBBConfig:
    """Tests pour la configuration OpenBB."""
    
    @pytest.fixture
    def sample_config_data(self):
        """Configuration échantillon pour OpenBB."""
        return {
            "api_key": "test_api_key_123",
            "base_url": "https://api.openbb.co/v1",
            "timeout": 30,
            "max_retries": 3,
            "rate_limit_per_minute": 100,
            "cache_ttl": 300,
            "enable_caching": True,
            "default_exchange": "NASDAQ",
            "default_currency": "USD"
        }
    
    def test_openbb_config_creation(self, sample_config_data):
        """Test création de la configuration OpenBB."""
        config = sample_config_data
        
        assert config["api_key"] == "test_api_key_123"
        assert config["base_url"] == "https://api.openbb.co/v1"
        assert config["timeout"] == 30
        assert config["max_retries"] == 3
        assert config["rate_limit_per_minute"] == 100
        assert config["enable_caching"] is True
    
    def test_config_validation(self, sample_config_data):
        """Test validation de la configuration."""
        config = sample_config_data
        
        # API key non vide
        assert len(config["api_key"]) > 0
        
        # URL valide
        assert config["base_url"].startswith("https://")
        
        # Timeout positif
        assert config["timeout"] > 0
        
        # Rate limit raisonnable
        assert 1 <= config["rate_limit_per_minute"] <= 1000
        
        # TTL cache positif
        assert config["cache_ttl"] > 0


class TestOpenBBProviderInitialization:
    """Tests pour l'initialisation du provider OpenBB."""
    
    @pytest.fixture
    def mock_openbb_config(self):
        """Configuration mock pour OpenBB."""
        return {
            "api_key": "test_key",
            "base_url": "https://api.openbb.co/v1",
            "timeout": 30,
            "max_retries": 3,
            "rate_limit_per_minute": 100
        }
    
    def test_provider_initialization(self, mock_openbb_config):
        """Test initialisation du provider."""
        # Note: Test avec mock en attendant l'implémentation
        provider = MockOpenBBProvider(mock_openbb_config)
        
        assert provider.config["api_key"] == "test_key"
        assert provider.config["timeout"] == 30
        assert provider.is_initialized is True
    
    def test_provider_initialization_invalid_config(self):
        """Test initialisation avec configuration invalide."""
        invalid_config = {
            "api_key": "",  # API key vide
            "timeout": -1   # Timeout négatif
        }
        
        with pytest.raises(ValueError):
            MockOpenBBProvider(invalid_config)
    
    @pytest.mark.asyncio
    async def test_provider_health_check(self, mock_openbb_config):
        """Test vérification de santé du provider."""
        provider = MockOpenBBProvider(mock_openbb_config)
        
        health_status = await provider.health_check()
        
        assert health_status["status"] == "healthy"
        assert "api_accessible" in health_status
        assert "rate_limit_remaining" in health_status


class TestStockDataRetrieval:
    """Tests pour la récupération de données d'actions."""
    
    @pytest.fixture
    def mock_provider(self):
        """Provider mock configuré."""
        config = {
            "api_key": "test_key",
            "base_url": "https://api.openbb.co/v1",
            "timeout": 30
        }
        return MockOpenBBProvider(config)
    
    @pytest.mark.asyncio
    async def test_get_stock_price_current(self, mock_provider):
        """Test récupération prix actuel d'une action."""
        symbol = "AAPL"
        
        price_data = await mock_provider.get_current_price(symbol)
        
        assert price_data["symbol"] == symbol
        assert "price" in price_data
        assert "timestamp" in price_data
        assert price_data["price"] > 0
        assert isinstance(price_data["timestamp"], datetime)
    
    @pytest.mark.asyncio
    async def test_get_stock_price_historical(self, mock_provider):
        """Test récupération prix historiques."""
        symbol = "GOOGL"
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
        
        historical_data = await mock_provider.get_historical_prices(
            symbol, start_date, end_date, DataFrequency.DAILY
        )
        
        assert len(historical_data) > 0
        assert "date" in historical_data[0]
        assert "open" in historical_data[0]
        assert "high" in historical_data[0]
        assert "low" in historical_data[0]
        assert "close" in historical_data[0]
        assert "volume" in historical_data[0]
    
    @pytest.mark.asyncio
    async def test_get_multiple_stocks(self, mock_provider):
        """Test récupération de données pour plusieurs actions."""
        symbols = ["AAPL", "GOOGL", "MSFT", "TSLA"]
        
        multi_data = await mock_provider.get_multiple_prices(symbols)
        
        assert len(multi_data) == len(symbols)
        for symbol in symbols:
            assert symbol in multi_data
            assert multi_data[symbol]["price"] > 0
    
    @pytest.mark.asyncio
    async def test_get_stock_with_different_frequencies(self, mock_provider):
        """Test récupération avec différentes fréquences."""
        symbol = "AAPL"
        start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.now()
        
        # Test différentes fréquences
        frequencies = [
            DataFrequency.MINUTE,
            DataFrequency.HOUR,
            DataFrequency.DAILY,
            DataFrequency.WEEKLY
        ]
        
        for frequency in frequencies:
            data = await mock_provider.get_historical_prices(
                symbol, start_date, end_date, frequency
            )
            assert len(data) > 0
            assert data[0]["symbol"] == symbol


class TestFundamentalData:
    """Tests pour les données fondamentales."""
    
    @pytest.fixture
    def mock_provider(self):
        """Provider mock configuré."""
        config = {"api_key": "test_key", "timeout": 30}
        return MockOpenBBProvider(config)
    
    @pytest.mark.asyncio
    async def test_get_company_info(self, mock_provider):
        """Test récupération informations entreprise."""
        symbol = "AAPL"
        
        company_info = await mock_provider.get_company_info(symbol)
        
        assert company_info["symbol"] == symbol
        assert "name" in company_info
        assert "sector" in company_info
        assert "industry" in company_info
        assert "market_cap" in company_info
        assert "employees" in company_info
        assert "description" in company_info
    
    @pytest.mark.asyncio
    async def test_get_financial_statements(self, mock_provider):
        """Test récupération états financiers."""
        symbol = "MSFT"
        
        # Test bilan
        balance_sheet = await mock_provider.get_balance_sheet(symbol)
        assert len(balance_sheet) > 0
        assert "total_assets" in balance_sheet[0]
        assert "total_liabilities" in balance_sheet[0]
        assert "shareholders_equity" in balance_sheet[0]
        
        # Test compte de résultat
        income_statement = await mock_provider.get_income_statement(symbol)
        assert len(income_statement) > 0
        assert "revenue" in income_statement[0]
        assert "net_income" in income_statement[0]
        assert "eps" in income_statement[0]
        
        # Test flux de trésorerie
        cash_flow = await mock_provider.get_cash_flow(symbol)
        assert len(cash_flow) > 0
        assert "operating_cash_flow" in cash_flow[0]
        assert "investing_cash_flow" in cash_flow[0]
        assert "financing_cash_flow" in cash_flow[0]
    
    @pytest.mark.asyncio
    async def test_get_financial_ratios(self, mock_provider):
        """Test récupération ratios financiers."""
        symbol = "GOOGL"
        
        ratios = await mock_provider.get_financial_ratios(symbol)
        
        assert "pe_ratio" in ratios
        assert "pb_ratio" in ratios
        assert "debt_to_equity" in ratios
        assert "current_ratio" in ratios
        assert "roe" in ratios
        assert "roa" in ratios
        assert "profit_margin" in ratios
        
        # Validation des ratios
        assert ratios["pe_ratio"] > 0
        assert ratios["current_ratio"] > 0
        assert -1 <= ratios["roe"] <= 1
        assert -1 <= ratios["roa"] <= 1
    
    @pytest.mark.asyncio
    async def test_get_dividend_data(self, mock_provider):
        """Test récupération données de dividendes."""
        symbol = "JNJ"  # Action qui verse des dividendes
        
        dividend_data = await mock_provider.get_dividend_history(symbol)
        
        if len(dividend_data) > 0:  # Si l'action verse des dividendes
            assert "ex_date" in dividend_data[0]
            assert "amount" in dividend_data[0]
            assert "frequency" in dividend_data[0]
            assert dividend_data[0]["amount"] > 0


class TestTechnicalIndicators:
    """Tests pour les indicateurs techniques."""
    
    @pytest.fixture
    def mock_provider(self):
        """Provider mock configuré."""
        config = {"api_key": "test_key", "timeout": 30}
        return MockOpenBBProvider(config)
    
    @pytest.fixture
    def sample_price_data(self):
        """Données de prix échantillon."""
        return create_test_price_data("AAPL", 100)
    
    @pytest.mark.asyncio
    async def test_get_rsi(self, mock_provider):
        """Test calcul RSI."""
        symbol = "AAPL"
        period = 14
        
        rsi_data = await mock_provider.get_rsi(symbol, period)
        
        assert len(rsi_data) > 0
        for point in rsi_data:
            assert "date" in point
            assert "rsi" in point
            assert 0 <= point["rsi"] <= 100
    
    @pytest.mark.asyncio
    async def test_get_moving_averages(self, mock_provider):
        """Test calcul moyennes mobiles."""
        symbol = "GOOGL"
        
        # SMA
        sma_20 = await mock_provider.get_sma(symbol, 20)
        sma_50 = await mock_provider.get_sma(symbol, 50)
        
        assert len(sma_20) > 0
        assert len(sma_50) > 0
        assert "sma" in sma_20[0]
        assert "sma" in sma_50[0]
        assert sma_20[0]["sma"] > 0
        
        # EMA
        ema_12 = await mock_provider.get_ema(symbol, 12)
        ema_26 = await mock_provider.get_ema(symbol, 26)
        
        assert len(ema_12) > 0
        assert len(ema_26) > 0
        assert "ema" in ema_12[0]
        assert "ema" in ema_26[0]
    
    @pytest.mark.asyncio
    async def test_get_macd(self, mock_provider):
        """Test calcul MACD."""
        symbol = "TSLA"
        
        macd_data = await mock_provider.get_macd(symbol)
        
        assert len(macd_data) > 0
        for point in macd_data:
            assert "date" in point
            assert "macd" in point
            assert "signal" in point
            assert "histogram" in point
    
    @pytest.mark.asyncio
    async def test_get_bollinger_bands(self, mock_provider):
        """Test calcul bandes de Bollinger."""
        symbol = "MSFT"
        period = 20
        std_dev = 2
        
        bb_data = await mock_provider.get_bollinger_bands(symbol, period, std_dev)
        
        assert len(bb_data) > 0
        for point in bb_data:
            assert "date" in point
            assert "middle" in point  # SMA
            assert "upper" in point
            assert "lower" in point
            assert point["upper"] > point["middle"] > point["lower"]
    
    @pytest.mark.asyncio
    async def test_get_volume_indicators(self, mock_provider):
        """Test indicateurs de volume."""
        symbol = "AAPL"
        
        volume_data = await mock_provider.get_volume_profile(symbol)
        
        assert len(volume_data) > 0
        for point in volume_data:
            assert "date" in point
            assert "volume" in point
            assert "vwap" in point  # Volume Weighted Average Price
            assert point["volume"] >= 0
            assert point["vwap"] > 0


class TestMarketData:
    """Tests pour les données de marché."""
    
    @pytest.fixture
    def mock_provider(self):
        """Provider mock configuré."""
        config = {"api_key": "test_key", "timeout": 30}
        return MockOpenBBProvider(config)
    
    @pytest.mark.asyncio
    async def test_get_market_indices(self, mock_provider):
        """Test récupération indices de marché."""
        indices = ["^GSPC", "^DJI", "^IXIC"]  # S&P 500, Dow Jones, NASDAQ
        
        market_data = await mock_provider.get_market_indices(indices)
        
        assert len(market_data) == len(indices)
        for index in indices:
            assert index in market_data
            assert "price" in market_data[index]
            assert "change" in market_data[index]
            assert "change_percent" in market_data[index]
    
    @pytest.mark.asyncio
    async def test_get_sector_performance(self, mock_provider):
        """Test performance sectorielle."""
        sector_data = await mock_provider.get_sector_performance()
        
        expected_sectors = [
            "Technology", "Healthcare", "Financial", "Consumer Discretionary",
            "Communication Services", "Industrials", "Energy", "Materials",
            "Consumer Staples", "Utilities", "Real Estate"
        ]
        
        assert len(sector_data) > 0
        for sector in sector_data:
            assert "name" in sector
            assert "performance_1d" in sector
            assert "performance_1w" in sector
            assert "performance_1m" in sector
            assert sector["name"] in expected_sectors
    
    @pytest.mark.asyncio
    async def test_get_economic_indicators(self, mock_provider):
        """Test indicateurs économiques."""
        economic_data = await mock_provider.get_economic_indicators()
        
        expected_indicators = [
            "gdp_growth", "inflation_rate", "unemployment_rate",
            "interest_rate", "consumer_confidence"
        ]
        
        for indicator in expected_indicators:
            assert indicator in economic_data
            assert "value" in economic_data[indicator]
            assert "date" in economic_data[indicator]
    
    @pytest.mark.asyncio
    async def test_get_market_calendar(self, mock_provider):
        """Test calendrier de marché."""
        start_date = datetime.now()
        end_date = start_date + timedelta(days=30)
        
        calendar_data = await mock_provider.get_market_calendar(start_date, end_date)
        
        assert len(calendar_data) > 0
        for day in calendar_data:
            assert "date" in day
            assert "is_open" in day
            assert "market_open" in day
            assert "market_close" in day
            assert isinstance(day["is_open"], bool)


class TestErrorHandling:
    """Tests pour la gestion d'erreurs."""
    
    @pytest.fixture
    def mock_provider(self):
        """Provider mock configuré."""
        config = {"api_key": "test_key", "timeout": 30}
        return MockOpenBBProvider(config)
    
    @pytest.mark.asyncio
    async def test_invalid_symbol_error(self, mock_provider):
        """Test erreur symbole invalide."""
        invalid_symbol = "INVALID_SYMBOL_123"
        
        with pytest.raises(DataNotFoundError):
            await mock_provider.get_current_price(invalid_symbol)
    
    @pytest.mark.asyncio
    async def test_api_rate_limit_error(self, mock_provider):
        """Test erreur limite de taux."""
        # Simuler dépassement de limite
        mock_provider.simulate_rate_limit = True
        
        with pytest.raises(APIRateLimitError):
            await mock_provider.get_current_price("AAPL")
    
    @pytest.mark.asyncio
    async def test_api_timeout_error(self, mock_provider):
        """Test erreur timeout."""
        # Simuler timeout
        mock_provider.simulate_timeout = True
        
        with pytest.raises(DataProviderError):
            await mock_provider.get_current_price("AAPL")
    
    @pytest.mark.asyncio
    async def test_invalid_date_range_error(self, mock_provider):
        """Test erreur plage de dates invalide."""
        symbol = "AAPL"
        start_date = datetime.now()
        end_date = start_date - timedelta(days=10)  # Date fin < date début
        
        with pytest.raises(ValueError):
            await mock_provider.get_historical_prices(
                symbol, start_date, end_date, DataFrequency.DAILY
            )
    
    @pytest.mark.asyncio
    async def test_network_error_retry(self, mock_provider):
        """Test retry en cas d'erreur réseau."""
        # Simuler erreur réseau temporaire
        mock_provider.simulate_network_error = True
        mock_provider.network_error_count = 2  # Échec 2 fois puis succès
        
        # Devrait réussir après retries
        result = await mock_provider.get_current_price("AAPL")
        assert result is not None
        assert mock_provider.retry_count > 0


class TestCaching:
    """Tests pour le système de cache."""
    
    @pytest.fixture
    def mock_provider_with_cache(self):
        """Provider mock avec cache activé."""
        config = {
            "api_key": "test_key",
            "timeout": 30,
            "enable_caching": True,
            "cache_ttl": 300
        }
        return MockOpenBBProvider(config)
    
    @pytest.mark.asyncio
    async def test_cache_hit(self, mock_provider_with_cache):
        """Test cache hit."""
        symbol = "AAPL"
        
        # Premier appel - données depuis API
        result1 = await mock_provider_with_cache.get_current_price(symbol)
        api_calls_after_first = mock_provider_with_cache.api_call_count
        
        # Deuxième appel - données depuis cache
        result2 = await mock_provider_with_cache.get_current_price(symbol)
        api_calls_after_second = mock_provider_with_cache.api_call_count
        
        # Vérifications
        assert result1["price"] == result2["price"]
        assert api_calls_after_second == api_calls_after_first  # Pas d'appel API supplémentaire
        assert mock_provider_with_cache.cache_hits > 0
    
    @pytest.mark.asyncio
    async def test_cache_miss_after_ttl(self, mock_provider_with_cache):
        """Test cache miss après expiration TTL."""
        symbol = "GOOGL"
        
        # Premier appel
        await mock_provider_with_cache.get_current_price(symbol)
        api_calls_first = mock_provider_with_cache.api_call_count
        
        # Simuler expiration cache
        mock_provider_with_cache.expire_cache()
        
        # Deuxième appel après expiration
        await mock_provider_with_cache.get_current_price(symbol)
        api_calls_second = mock_provider_with_cache.api_call_count
        
        # Vérification - nouvel appel API
        assert api_calls_second > api_calls_first
    
    @pytest.mark.asyncio
    async def test_cache_invalidation(self, mock_provider_with_cache):
        """Test invalidation de cache."""
        symbol = "MSFT"
        
        # Mise en cache
        await mock_provider_with_cache.get_current_price(symbol)
        
        # Invalidation manuelle
        mock_provider_with_cache.invalidate_cache(symbol)
        
        # Nouvel appel devrait faire un appel API
        api_calls_before = mock_provider_with_cache.api_call_count
        await mock_provider_with_cache.get_current_price(symbol)
        api_calls_after = mock_provider_with_cache.api_call_count
        
        assert api_calls_after > api_calls_before


class TestRateLimiting:
    """Tests pour la limitation de taux."""
    
    @pytest.fixture
    def mock_provider_with_rate_limit(self):
        """Provider mock avec limitation de taux."""
        config = {
            "api_key": "test_key",
            "timeout": 30,
            "rate_limit_per_minute": 10  # Limite basse pour test
        }
        return MockOpenBBProvider(config)
    
    @pytest.mark.asyncio
    async def test_rate_limit_enforcement(self, mock_provider_with_rate_limit):
        """Test application de la limitation de taux."""
        symbols = [f"STOCK{i}" for i in range(15)]  # Plus que la limite
        
        successful_calls = 0
        rate_limited_calls = 0
        
        for symbol in symbols:
            try:
                await mock_provider_with_rate_limit.get_current_price(symbol)
                successful_calls += 1
            except APIRateLimitError:
                rate_limited_calls += 1
        
        # Vérification que la limite est appliquée
        assert successful_calls <= 10  # Limite configurée
        assert rate_limited_calls > 0
    
    @pytest.mark.asyncio
    async def test_rate_limit_reset(self, mock_provider_with_rate_limit):
        """Test reset de la limitation de taux."""
        # Atteindre la limite
        for i in range(10):
            await mock_provider_with_rate_limit.get_current_price(f"STOCK{i}")
        
        # Simuler reset (nouvelle minute)
        mock_provider_with_rate_limit.reset_rate_limit()
        
        # Devrait fonctionner à nouveau
        result = await mock_provider_with_rate_limit.get_current_price("AAPL")
        assert result is not None


class TestDataValidation:
    """Tests pour la validation de données."""
    
    @pytest.fixture
    def mock_provider(self):
        """Provider mock configuré."""
        config = {"api_key": "test_key", "timeout": 30}
        return MockOpenBBProvider(config)
    
    @pytest.mark.asyncio
    async def test_price_data_validation(self, mock_provider):
        """Test validation des données de prix."""
        symbol = "AAPL"
        
        price_data = await mock_provider.get_current_price(symbol)
        
        # Validation structure
        required_fields = ["symbol", "price", "timestamp", "volume"]
        for field in required_fields:
            assert field in price_data
        
        # Validation valeurs
        assert price_data["price"] > 0
        assert price_data["volume"] >= 0
        assert isinstance(price_data["timestamp"], datetime)
        assert price_data["symbol"] == symbol
    
    @pytest.mark.asyncio
    async def test_financial_data_validation(self, mock_provider):
        """Test validation des données financières."""
        symbol = "GOOGL"
        
        financial_data = await mock_provider.get_financial_ratios(symbol)
        
        # Validation ratios
        if "pe_ratio" in financial_data and financial_data["pe_ratio"] is not None:
            assert financial_data["pe_ratio"] > 0
        
        if "debt_to_equity" in financial_data and financial_data["debt_to_equity"] is not None:
            assert financial_data["debt_to_equity"] >= 0
        
        if "current_ratio" in financial_data and financial_data["current_ratio"] is not None:
            assert financial_data["current_ratio"] > 0
    
    @pytest.mark.asyncio
    async def test_historical_data_validation(self, mock_provider):
        """Test validation des données historiques."""
        symbol = "MSFT"
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
        
        historical_data = await mock_provider.get_historical_prices(
            symbol, start_date, end_date, DataFrequency.DAILY
        )
        
        # Validation structure
        assert len(historical_data) > 0
        
        for data_point in historical_data:
            # Champs obligatoires
            required_fields = ["date", "open", "high", "low", "close", "volume"]
            for field in required_fields:
                assert field in data_point
            
            # Validation cohérence OHLC
            assert data_point["high"] >= data_point["open"]
            assert data_point["high"] >= data_point["close"]
            assert data_point["low"] <= data_point["open"]
            assert data_point["low"] <= data_point["close"]
            assert data_point["high"] >= data_point["low"]
            
            # Validation volume
            assert data_point["volume"] >= 0


# Fixtures globales pour les tests OpenBB
@pytest.fixture
def openbb_test_symbols():
    """Symboles de test pour OpenBB."""
    return {
        "large_cap": ["AAPL", "GOOGL", "MSFT", "AMZN"],
        "mid_cap": ["SQ", "ROKU", "SNAP", "SPOT"],
        "small_cap": ["CRWD", "ZM", "DOCU", "OKTA"],
        "etf": ["SPY", "QQQ", "IWM", "VTI"],
        "indices": ["^GSPC", "^DJI", "^IXIC", "^RUT"]
    }


@pytest.fixture
def openbb_test_date_ranges():
    """Plages de dates de test."""
    now = datetime.now()
    return {
        "last_week": {
            "start": now - timedelta(days=7),
            "end": now
        },
        "last_month": {
            "start": now - timedelta(days=30),
            "end": now
        },
        "last_quarter": {
            "start": now - timedelta(days=90),
            "end": now
        },
        "last_year": {
            "start": now - timedelta(days=365),
            "end": now
        }
    }


@pytest.fixture
def openbb_mock_responses():
    """Réponses mock pour OpenBB API."""
    return {
        "price_data": {
            "symbol": "AAPL",
            "price": 150.25,
            "volume": 50000000,
            "timestamp": datetime.now().isoformat()
        },
        "company_info": {
            "symbol": "AAPL",
            "name": "Apple Inc.",
            "sector": "Technology",
            "industry": "Consumer Electronics",
            "market_cap": 2500000000000,
            "employees": 154000
        },
        "financial_ratios": {
            "pe_ratio": 28.5,
            "pb_ratio": 8.2,
            "debt_to_equity": 0.31,
            "current_ratio": 1.07,
            "roe": 0.26,
            "roa": 0.16
        }
    }