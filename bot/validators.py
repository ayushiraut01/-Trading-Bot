"""
Input validation for order parameters.
All validation logic is centralised here so both the CLI and any
future interface share the same rules.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation


VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_MARKET"}


class ValidationError(ValueError):
    """Raised when user-supplied order parameters fail validation."""


def validate_symbol(symbol: str) -> str:
    """Return the symbol uppercased, or raise ValidationError."""
    symbol = symbol.strip().upper()
    if not symbol.isalnum():
        raise ValidationError(
            f"Symbol '{symbol}' is invalid. Use alphanumeric characters only (e.g. BTCUSDT)."
        )
    return symbol


def validate_side(side: str) -> str:
    """Return the side uppercased, or raise ValidationError."""
    side = side.strip().upper()
    if side not in VALID_SIDES:
        raise ValidationError(
            f"Side '{side}' is not valid. Choose from: {', '.join(sorted(VALID_SIDES))}."
        )
    return side


def validate_order_type(order_type: str) -> str:
    """Return the order type uppercased, or raise ValidationError."""
    order_type = order_type.strip().upper()
    if order_type not in VALID_ORDER_TYPES:
        raise ValidationError(
            f"Order type '{order_type}' is not valid. "
            f"Choose from: {', '.join(sorted(VALID_ORDER_TYPES))}."
        )
    return order_type


def validate_quantity(quantity: str | float) -> Decimal:
    """Return quantity as Decimal, or raise ValidationError."""
    try:
        qty = Decimal(str(quantity))
    except InvalidOperation:
        raise ValidationError(f"Quantity '{quantity}' is not a valid number.")

    if qty <= 0:
        raise ValidationError(f"Quantity must be greater than zero. Got: {qty}.")
    return qty


def validate_price(price: str | float | None, order_type: str) -> Decimal | None:
    """
    Validate the price field.

    - MARKET orders must NOT provide a price.
    - LIMIT and STOP_MARKET orders MUST provide a positive price.
    """
    order_type = order_type.upper()

    if order_type == "MARKET":
        if price is not None:
            raise ValidationError("Price must not be provided for MARKET orders.")
        return None

    # LIMIT / STOP_MARKET require a price
    if price is None:
        raise ValidationError(f"Price is required for {order_type} orders.")

    try:
        p = Decimal(str(price))
    except InvalidOperation:
        raise ValidationError(f"Price '{price}' is not a valid number.")

    if p <= 0:
        raise ValidationError(f"Price must be greater than zero. Got: {p}.")

    return p


def validate_stop_price(stop_price: str | float | None, order_type: str) -> Decimal | None:
    """Validate stop price — only required for STOP_MARKET orders."""
    if order_type.upper() != "STOP_MARKET":
        return None
    if stop_price is None:
        raise ValidationError("Stop price (--stop-price) is required for STOP_MARKET orders.")
    try:
        sp = Decimal(str(stop_price))
    except InvalidOperation:
        raise ValidationError(f"Stop price '{stop_price}' is not a valid number.")
    if sp <= 0:
        raise ValidationError(f"Stop price must be greater than zero. Got: {sp}.")
    return sp
