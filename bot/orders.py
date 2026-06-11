"""
Order orchestration layer.

Sits between the CLI and the raw API client.  Responsible for:
- Calling validators before touching the network.
- Invoking BinanceClient.place_order().
- Formatting and printing order summaries to stdout.
- Returning structured result dicts for programmatic use.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

from bot.client import BinanceClient, BinanceAPIError
from bot.validators import (
    ValidationError,
    validate_symbol,
    validate_side,
    validate_order_type,
    validate_quantity,
    validate_price,
    validate_stop_price,
)

logger = logging.getLogger("trading_bot.orders")


def _fmt(value: Any, default: str = "N/A") -> str:
    """Return a display-friendly string, falling back to *default*."""
    if value is None or value == "":
        return default
    return str(value)


def print_request_summary(
    symbol: str,
    side: str,
    order_type: str,
    quantity: Decimal,
    price: Decimal | None,
    stop_price: Decimal | None,
) -> None:
    """Print a formatted order-request summary to stdout."""
    separator = "─" * 50
    print(f"\n{separator}")
    print("  ORDER REQUEST SUMMARY")
    print(separator)
    print(f"  Symbol     : {symbol}")
    print(f"  Side       : {side}")
    print(f"  Type       : {order_type}")
    print(f"  Quantity   : {quantity}")
    if price is not None:
        print(f"  Price      : {price}")
    if stop_price is not None:
        print(f"  Stop Price : {stop_price}")
    print(f"{separator}\n")


def print_order_response(response: dict) -> None:
    """Print the key fields from a Binance order response."""
    separator = "─" * 50
    print(f"{separator}")
    print("  ORDER RESPONSE")
    print(separator)
    print(f"  Order ID      : {_fmt(response.get('orderId'))}")
    print(f"  Client OID    : {_fmt(response.get('clientOrderId'))}")
    print(f"  Symbol        : {_fmt(response.get('symbol'))}")
    print(f"  Side          : {_fmt(response.get('side'))}")
    print(f"  Type          : {_fmt(response.get('type'))}")
    print(f"  Status        : {_fmt(response.get('status'))}")
    print(f"  Orig Qty      : {_fmt(response.get('origQty'))}")
    print(f"  Executed Qty  : {_fmt(response.get('executedQty'))}")
    print(f"  Avg Price     : {_fmt(response.get('avgPrice'))}")
    print(f"  Price         : {_fmt(response.get('price'))}")
    if response.get("stopPrice") not in (None, "", "0", "0.00000"):
        print(f"  Stop Price    : {_fmt(response.get('stopPrice'))}")
    print(f"  Time in Force : {_fmt(response.get('timeInForce'))}")
    print(f"  Created At    : {_fmt(response.get('updateTime'))}")
    print(separator)


def place_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    order_type: str,
    quantity: str | float,
    price: str | float | None = None,
    stop_price: str | float | None = None,
    time_in_force: str = "GTC",
) -> dict:
    """
    Validate inputs, place an order, and print a formatted summary.

    Args:
        client:         Authenticated BinanceClient instance.
        symbol:         Trading pair (e.g. 'BTCUSDT').
        side:           'BUY' or 'SELL'.
        order_type:     'MARKET', 'LIMIT', or 'STOP_MARKET'.
        quantity:       Contract quantity.
        price:          Limit price (LIMIT orders only).
        stop_price:     Trigger price (STOP_MARKET orders only).
        time_in_force:  GTC / IOC / FOK.

    Returns:
        The raw Binance order response dict.

    Raises:
        ValidationError: If any input parameter is invalid.
        BinanceAPIError: If the API returns an error.
        requests.RequestException: On network failure.
    """
    # --- Validate all inputs up-front -----------------------------------
    symbol = validate_symbol(symbol)
    side = validate_side(side)
    order_type = validate_order_type(order_type)
    qty = validate_quantity(quantity)
    prc = validate_price(price, order_type)
    stp = validate_stop_price(stop_price, order_type)

    # --- Show what we're about to send ----------------------------------
    print_request_summary(symbol, side, order_type, qty, prc, stp)

    # --- Hit the API ----------------------------------------------------
    try:
        response = client.place_order(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=qty,
            price=prc,
            stop_price=stp,
            time_in_force=time_in_force,
        )
    except ValidationError:
        raise
    except BinanceAPIError as exc:
        logger.error("API error while placing order: %s", exc)
        print(f"\n  ✗  Order FAILED — API error {exc.code}: {exc.message}\n")
        raise
    except Exception as exc:
        logger.error("Unexpected error while placing order: %s", exc)
        print(f"\n  ✗  Order FAILED — {exc}\n")
        raise

    # --- Display the result ---------------------------------------------
    print_order_response(response)
    print(f"  ✓  Order placed successfully!\n")

    return response
