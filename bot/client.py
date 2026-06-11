"""
Binance Futures Testnet API client.

Wraps direct REST calls to https://testnet.binancefuture.com so the
rest of the application never has to deal with raw HTTP or HMAC signing.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import time
from decimal import Decimal
from typing import Any
from urllib.parse import urlencode

import requests

logger = logging.getLogger("trading_bot.client")

BASE_URL = "https://testnet.binancefuture.com"
RECV_WINDOW = 5000  # ms


class BinanceAPIError(Exception):
    """Raised when the Binance API returns an error response."""

    def __init__(self, code: int, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"Binance API error {code}: {message}")


class BinanceClient:
    """
    Thin wrapper around the Binance USDT-M Futures Testnet REST API.

    Handles:
    - HMAC-SHA256 request signing
    - Timestamping
    - HTTP-level error handling
    - Structured logging of every request and response
    """

    def __init__(self, api_key: str, api_secret: str, timeout: int = 10) -> None:
        self._api_key = api_key
        self._api_secret = api_secret
        self._timeout = timeout
        self._session = requests.Session()
        self._session.headers.update(
            {
                "X-MBX-APIKEY": self._api_key,
                "Content-Type": "application/x-www-form-urlencoded",
            }
        )
        logger.info("BinanceClient initialised (base_url=%s)", BASE_URL)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _sign(self, params: dict) -> dict:
        """Append a timestamp and HMAC signature to a parameter dict."""
        params["timestamp"] = int(time.time() * 1000)
        params["recvWindow"] = RECV_WINDOW
        query_string = urlencode(params)
        signature = hmac.new(
            self._api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        params["signature"] = signature
        return params

    def _request(self, method: str, path: str, params: dict | None = None) -> Any:
        """
        Execute a signed HTTP request and return the parsed JSON body.

        Raises:
            BinanceAPIError: for API-level errors (non-2xx or error JSON).
            requests.RequestException: for network-level failures.
        """
        params = params or {}
        params = self._sign(params)

        url = BASE_URL + path
        logger.debug("→ %s %s  params=%s", method.upper(), url, {k: v for k, v in params.items() if k != "signature"})

        try:
            if method.upper() == "GET":
                response = self._session.get(url, params=params, timeout=self._timeout)
            else:
                response = self._session.post(url, data=params, timeout=self._timeout)
        except requests.ConnectionError as exc:
            logger.error("Network connection failed: %s", exc)
            raise
        except requests.Timeout:
            logger.error("Request to %s timed out after %ss", url, self._timeout)
            raise

        logger.debug("← HTTP %s  body=%s", response.status_code, response.text[:500])

        # Parse JSON first so we can surface API-level error messages
        try:
            data = response.json()
        except ValueError:
            response.raise_for_status()
            raise BinanceAPIError(-1, f"Non-JSON response: {response.text[:200]}")

        if isinstance(data, dict) and "code" in data and data["code"] != 200:
            # Binance error responses look like {"code": -1102, "msg": "..."}
            if data["code"] < 0:
                raise BinanceAPIError(data["code"], data.get("msg", "Unknown error"))

        response.raise_for_status()
        return data

    # ------------------------------------------------------------------
    # Public API methods
    # ------------------------------------------------------------------

    def get_exchange_info(self) -> dict:
        """Fetch exchange trading rules (no auth required)."""
        response = requests.get(BASE_URL + "/fapi/v1/exchangeInfo", timeout=self._timeout)
        response.raise_for_status()
        return response.json()

    def get_account(self) -> dict:
        """Return account information including balances."""
        return self._request("GET", "/fapi/v2/account")

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: Decimal,
        price: Decimal | None = None,
        stop_price: Decimal | None = None,
        time_in_force: str = "GTC",
    ) -> dict:
        """
        Place a futures order.

        Args:
            symbol:        Trading pair, e.g. 'BTCUSDT'.
            side:          'BUY' or 'SELL'.
            order_type:    'MARKET', 'LIMIT', or 'STOP_MARKET'.
            quantity:      Contract quantity.
            price:         Limit price (required for LIMIT orders).
            stop_price:    Trigger price (required for STOP_MARKET orders).
            time_in_force: GTC / IOC / FOK (used for LIMIT orders).

        Returns:
            Raw order response dict from Binance.
        """
        params: dict[str, Any] = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": str(quantity),
        }

        if order_type == "LIMIT":
            if price is None:
                raise ValueError("price is required for LIMIT orders")
            params["price"] = str(price)
            params["timeInForce"] = time_in_force

        if order_type == "STOP_MARKET":
            if stop_price is None:
                raise ValueError("stop_price is required for STOP_MARKET orders")
            params["stopPrice"] = str(stop_price)

        logger.info(
            "Placing order — symbol=%s side=%s type=%s qty=%s price=%s stop=%s",
            symbol, side, order_type, quantity, price, stop_price,
        )

        response = self._request("POST", "/fapi/v1/order", params)
        logger.info("Order placed — orderId=%s status=%s", response.get("orderId"), response.get("status"))
        return response
