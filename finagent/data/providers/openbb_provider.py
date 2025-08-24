"""Minimal OpenBB provider used for market data retrieval.

This implementation uses ``yfinance`` under the hood to provide
basic market data when the official OpenBB API is unavailable.
It exposes the subset of methods required by the CLI commands and
higher level components.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

import os
import structlog
import sys
from httpx import AsyncClient

# Patch pour éviter l'importation de websockets.asyncio dans yfinance
def patch_yfinance_websockets():
    """Patch yfinance pour éviter l'erreur websockets.asyncio."""
    import types
    
    # Créer un module mock pour websockets.asyncio
    mock_module = types.ModuleType('websockets.asyncio')
    mock_client = types.ModuleType('websockets.asyncio.client')
    
    # Créer une fonction mock pour connect
    def mock_connect(*args, **kwargs):
        raise NotImplementedError("WebSocket streaming non disponible - websockets.asyncio non installé")
    
    mock_client.connect = mock_connect
    mock_module.client = mock_client
    
    # Injecter le module mock dans sys.modules
    sys.modules['websockets.asyncio'] = mock_module
    sys.modules['websockets.asyncio.client'] = mock_client

# Appliquer le patch avant d'importer yfinance
patch_yfinance_websockets()

# Maintenant importer yfinance devrait fonctionner
import yfinance as yf

logger = structlog.get_logger(__name__)


class DataFrequency(str, Enum):
    """Frequency options for historical data."""

    DAILY = "1d"
    WEEKLY = "1wk"
    MONTHLY = "1mo"


class MarketDataType(str, Enum):
    """Supported market data types."""

    PRICE = "price"
    VOLUME = "volume"


@dataclass
class OpenBBConfig:
    """Configuration for the OpenBB provider."""

    api_key: Optional[str] = None
    base_url: str = "https://api.openbb.co/v1"
    timeout: int = 30


class OpenBBProvider:
    """Simplified market data provider.

    The implementation falls back to ``yfinance`` which does not require
    authentication. The structure mirrors the expected interface so that
    other components can rely on it transparently.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        cfg = config or {}
        self.config = OpenBBConfig(
            api_key=cfg.get("api_key") or os.getenv("OPENBB_PAT"),
            base_url=cfg.get("base_url") or os.getenv("OPENBB_BASE_URL", "https://api.openbb.co/v1"),
            timeout=cfg.get("timeout", 30),
        )
        self._client: Optional[AsyncClient] = None
        self.is_initialized: bool = False

    async def initialize(self) -> None:
        """Initialise the underlying HTTP client."""
        self._client = AsyncClient(base_url=self.config.base_url, timeout=self.config.timeout)
        self.is_initialized = True
        logger.info("OpenBB Provider initialisé")

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
        self._client = None
        self.is_initialized = False

    async def get_current_price(self, symbol: str) -> Dict[str, Any]:
        """Return the latest available price for ``symbol``."""
        data = await asyncio.to_thread(lambda: yf.Ticker(symbol).history(period="1d"))
        price = float(data["Close"].iloc[-1]) if not data.empty else None
        return {"symbol": symbol, "price": price}

    async def get_historical_data(self, symbol: str, period: str = "1y") -> List[Dict[str, Any]]:
        """Return historical OHLCV data for ``symbol``."""
        hist = await asyncio.to_thread(lambda: yf.Ticker(symbol).history(period=period))
        if hist.empty:
            return []
        hist.reset_index(inplace=True)
        records: List[Dict[str, Any]] = []
        for _, row in hist.iterrows():
            records.append(
                {
                    "date": row["Date"].strftime("%Y-%m-%d"),
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": int(row["Volume"]),
                }
            )
        return records

    async def get_company_info(self, symbol: str) -> Dict[str, Any]:
        """Return basic company information."""
        info = await asyncio.to_thread(lambda: yf.Ticker(symbol).info)
        return info or {}

    async def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Alias for :meth:`get_current_price`."""
        return await self.get_current_price(symbol)
