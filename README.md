# Binance Futures Testnet Trading Bot

A clean, production-ready Python CLI bot for placing orders on the Binance USDT-M Futures Testnet.

---

## Features

- Place **Market**, **Limit**, and **Stop-Market** (bonus) orders
- Supports **BUY** and **SELL** sides
- Full **CLI** via `argparse` with `--help` on every command
- Structured **two-layer architecture**: API client (`bot/client.py`) is fully decoupled from CLI logic (`cli.py`)
- Comprehensive **input validation** with clear error messages before any network call is made
- **Structured logging** to both console and a daily log file (`logs/trading_bot_YYYYMMDD.log`)
- Graceful error handling for API errors, network failures, and bad input
- Credentials loaded from environment variables or a `.env` file — nothing hardcoded

---

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py          # Package marker
│   ├── client.py            # Binance REST client (HMAC signing, HTTP, logging)
│   ├── orders.py            # Order orchestration + stdout formatting
│   ├── validators.py        # All input validation logic
│   └── logging_config.py   # Logging setup (file + console handlers)
├── logs/
│   ├── sample_market_order.log
│   └── sample_limit_order.log
├── cli.py                   # CLI entry point (argparse sub-commands)
├── .env.example             # Credentials template
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Prerequisites

- Python 3.8 or higher
- A [Binance Futures Testnet](https://testnet.binancefuture.com) account with API credentials

### 2. Clone / Download

```bash
git clone <your-repo-url>
cd trading_bot
```

### 3. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate        # macOS/Linux
# OR
.venv\Scripts\activate           # Windows
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure credentials

```bash
cp .env.example .env
```

Open `.env` and fill in your Binance Futures Testnet API key and secret:

```
BINANCE_API_KEY=your_testnet_api_key_here
BINANCE_API_SECRET=your_testnet_api_secret_here
```

> **Note:** Credentials can also be exported as shell environment variables instead of using `.env`.

---

## Usage

### Get help

```bash
python cli.py --help
python cli.py place --help
```

### Place a Market order

```bash
python cli.py place --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

### Place a Limit order

```bash
python cli.py place --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 95000
```

### Place a Stop-Market order (bonus)

```bash
python cli.py place --symbol ETHUSDT --side SELL --type STOP_MARKET --quantity 0.01 --stop-price 3200
```

### Check account balances

```bash
python cli.py account
```

### Verbose (debug) logging

```bash
LOG_LEVEL=DEBUG python cli.py place --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

---

## Example Output

**Market order:**

```
──────────────────────────────────────────────────
  ORDER REQUEST SUMMARY
──────────────────────────────────────────────────
  Symbol     : BTCUSDT
  Side       : BUY
  Type       : MARKET
  Quantity   : 0.001
──────────────────────────────────────────────────

──────────────────────────────────────────────────
  ORDER RESPONSE
──────────────────────────────────────────────────
  Order ID      : 4751823
  Client OID    : web_abc123
  Symbol        : BTCUSDT
  Side          : BUY
  Type          : MARKET
  Status        : FILLED
  Orig Qty      : 0.001
  Executed Qty  : 0.001
  Avg Price     : 65432.10
  Price         : 0
  Time in Force : GTC
  Created At    : 1752486121789
──────────────────────────────────────────────────
  ✓  Order placed successfully!
```

---

## Log Files

Logs are written to `logs/trading_bot_YYYYMMDD.log`.

Sample log files are provided in `logs/` for reference:
- `logs/sample_market_order.log` — example MARKET order session
- `logs/sample_limit_order.log` — example LIMIT order session

---

## Assumptions

1. **Testnet only.** The base URL is hardcoded to `https://testnet.binancefuture.com`. Switching to production requires changing `BASE_URL` in `bot/client.py`.
2. **No position mode.** Orders use `positionSide=BOTH` (one-way mode, the testnet default). Hedge mode is not supported.
3. **Quantity precision.** The bot does not auto-round quantities to exchange step sizes. If Binance rejects your quantity with a `-1111` error, adjust the value to match the symbol's `stepSize` (visible in `/fapi/v1/exchangeInfo`).
4. **Stop-Market orders** use the `STOP_MARKET` type and trigger when the mark price crosses `stopPrice`. They do not require a limit price.
5. **Dependencies** are intentionally minimal: `requests` for HTTP and `python-dotenv` for credential loading. No Binance SDK is used, keeping the code transparent and easy to audit.

---

## Running Tests

Unit tests are not included in this initial submission but the validation logic in `bot/validators.py` is easily testable in isolation:

```python
from bot.validators import validate_symbol, validate_side, ValidationError
validate_symbol("btcusdt")   # → "BTCUSDT"
validate_side("buy")         # → "BUY"
```

---

## License

MIT
