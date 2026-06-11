#!/usr/bin/env python3
"""
cli.py — Command-line interface for the Binance Futures Testnet trading bot.

Usage examples:
  python cli.py place --symbol BTCUSDT --side BUY  --type MARKET --quantity 0.001
  python cli.py place --symbol BTCUSDT --side SELL --type LIMIT  --quantity 0.001 --price 95000
  python cli.py place --symbol ETHUSDT --side BUY  --type STOP_MARKET --quantity 0.01 --stop-price 3200
  python cli.py account
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys

from dotenv import load_dotenv

from bot.client import BinanceClient, BinanceAPIError
from bot.logging_config import setup_logging
from bot.orders import place_order
from bot.validators import ValidationError

# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------

load_dotenv()  # Load .env if present (API_KEY / API_SECRET)

logger = setup_logging(os.getenv("LOG_LEVEL", "INFO"))


def _get_client() -> BinanceClient:
    """Build a BinanceClient from environment variables, or exit with a clear message."""
    api_key = os.getenv("BINANCE_API_KEY", "").strip()
    api_secret = os.getenv("BINANCE_API_SECRET", "").strip()

    if not api_key or not api_secret:
        print(
            "\n  ✗  Missing credentials.\n"
            "     Set BINANCE_API_KEY and BINANCE_API_SECRET in your environment\n"
            "     or in a .env file in the project root.\n"
        )
        sys.exit(1)

    return BinanceClient(api_key=api_key, api_secret=api_secret)


# ---------------------------------------------------------------------------
# Sub-command handlers
# ---------------------------------------------------------------------------

def cmd_place(args: argparse.Namespace) -> None:
    """Handle the 'place' sub-command."""
    client = _get_client()
    try:
        place_order(
            client=client,
            symbol=args.symbol,
            side=args.side,
            order_type=args.type,
            quantity=args.quantity,
            price=args.price,
            stop_price=args.stop_price,
            time_in_force=args.time_in_force,
        )
    except ValidationError as exc:
        print(f"\n  ✗  Validation error: {exc}\n")
        logger.error("Validation error: %s", exc)
        sys.exit(2)
    except BinanceAPIError as exc:
        sys.exit(3)
    except Exception as exc:
        logger.exception("Unhandled exception")
        sys.exit(4)


def cmd_account(args: argparse.Namespace) -> None:
    """Handle the 'account' sub-command — show account balances."""
    client = _get_client()
    try:
        info = client.get_account()
    except Exception as exc:
        print(f"\n  ✗  Failed to fetch account info: {exc}\n")
        logger.error("Account fetch error: %s", exc)
        sys.exit(3)

    separator = "─" * 50
    print(f"\n{separator}")
    print("  ACCOUNT OVERVIEW")
    print(separator)
    print(f"  Total Wallet Balance  : {info.get('totalWalletBalance', 'N/A')} USDT")
    print(f"  Unrealised PnL        : {info.get('totalUnrealizedProfit', 'N/A')} USDT")
    print(f"  Available Balance     : {info.get('availableBalance', 'N/A')} USDT")

    assets = [a for a in info.get("assets", []) if float(a.get("walletBalance", 0)) != 0]
    if assets:
        print(f"\n  Non-zero asset balances:")
        for asset in assets:
            print(f"    {asset['asset']:10s}  wallet={asset['walletBalance']}  "
                  f"available={asset['availableBalance']}")
    print(f"{separator}\n")


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading_bot",
        description="Binance Futures Testnet — order placement CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Market buy
  python cli.py place --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001

  # Limit sell
  python cli.py place --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 95000

  # Stop-market sell (bonus order type)
  python cli.py place --symbol ETHUSDT --side SELL --type STOP_MARKET --quantity 0.01 --stop-price 3200

  # View account balances
  python cli.py account
        """,
    )

    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")
    subparsers.required = True

    # ---- place ----
    place_parser = subparsers.add_parser(
        "place",
        help="Place a futures order",
        description="Place a MARKET, LIMIT, or STOP_MARKET order on Binance Futures Testnet.",
    )
    place_parser.add_argument(
        "--symbol", required=True, metavar="SYMBOL",
        help="Trading pair, e.g. BTCUSDT",
    )
    place_parser.add_argument(
        "--side", required=True, metavar="SIDE",
        choices=["BUY", "SELL"],
        type=str.upper,
        help="Order side: BUY or SELL",
    )
    place_parser.add_argument(
        "--type", required=True, metavar="TYPE",
        choices=["MARKET", "LIMIT", "STOP_MARKET"],
        type=str.upper,
        help="Order type: MARKET, LIMIT, or STOP_MARKET",
    )
    place_parser.add_argument(
        "--quantity", required=True, type=float, metavar="QTY",
        help="Contract quantity (e.g. 0.001 for BTC)",
    )
    place_parser.add_argument(
        "--price", type=float, default=None, metavar="PRICE",
        help="Limit price — required for LIMIT orders",
    )
    place_parser.add_argument(
        "--stop-price", type=float, default=None, dest="stop_price", metavar="STOP_PRICE",
        help="Stop trigger price — required for STOP_MARKET orders",
    )
    place_parser.add_argument(
        "--time-in-force", default="GTC", dest="time_in_force",
        choices=["GTC", "IOC", "FOK"],
        help="Time-in-force for LIMIT orders (default: GTC)",
    )
    place_parser.set_defaults(func=cmd_place)

    # ---- account ----
    account_parser = subparsers.add_parser(
        "account",
        help="Show account balances",
    )
    account_parser.set_defaults(func=cmd_account)

    return parser


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
