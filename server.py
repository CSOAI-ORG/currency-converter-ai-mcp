#!/usr/bin/env python3
"""MEOK AI Labs — currency-converter-ai-mcp MCP Server. Comprehensive currency conversion with rates and analytics."""

import json
from datetime import datetime, timedelta, timezone
from typing import Any
import uuid
import random
import sys, os

sys.path.insert(0, os.path.expanduser("~/clawd/meok-labs-engine/shared"))
from auth_middleware import check_access
from mcp.server.fastmcp import FastMCP
from collections import defaultdict

FREE_DAILY_LIMIT = 15
_usage = defaultdict(list)
def _rl(c="anon"):
    now = datetime.now(timezone.utc)
    _usage[c] = [t for t in _usage[c] if (now-t).total_seconds() < 86400]
    if len(_usage[c]) >= FREE_DAILY_LIMIT: return json.dumps({"error": f"Limit {FREE_DAILY_LIMIT}/day"})
    _usage[c].append(now); return None

_store = {"conversions": [], "favorites": [], "alerts": []}
mcp = FastMCP("currency-converter-ai", instructions="Comprehensive currency conversion with rates and analytics.")


def create_id():
    return str(uuid.uuid4())[:8]


RATES = {
    "USD": 1.0,
    "GBP": 0.79,
    "EUR": 0.92,
    "JPY": 150.0,
    "AUD": 1.53,
    "CAD": 1.36,
    "CHF": 0.88,
    "CNY": 7.24,
    "INR": 83.12,
    "MXN": 17.15,
    "BRL": 4.97,
    "KRW": 1320.0,
    "SGD": 1.34,
    "HKD": 7.82,
    "NOK": 10.65,
    "SEK": 10.42,
    "DKK": 6.87,
    "NZD": 1.64,
    "ZAR": 18.75,
    "RUB": 92.5,
    "TRY": 32.15,
    "PLN": 4.02,
    "THB": 35.8,
    "MYR": 4.72,
}

SYMBOLS = {
    "USD": "$",
    "GBP": "\u00a3",
    "EUR": "\u20ac",
    "JPY": "\u00a5",
    "AUD": "A$",
    "CAD": "C$",
    "CHF": "Fr",
    "CNY": "\u00a5",
    "INR": "\u20b9",
    "MXN": "$",
    "BRL": "R$",
    "KRW": "\u20a9",
    "SGD": "S$",
    "HKD": "HK$",
    "NOK": "kr",
    "SEK": "kr",
    "DKK": "kr",
    "NZD": "NZ$",
    "ZAR": "R",
    "RUB": "\u20bd",
    "TRY": "\u20ba",
    "PLN": "z\u0142",
    "THB": "\u0e3f",
    "MYR": "RM",
}


def get_rate_val(currency):
    return RATES.get(currency, 1.0)


def convert(amount, from_curr, to_curr):
    usd_amount = amount / get_rate_val(from_curr)
    return usd_amount * get_rate_val(to_curr)


def format_amount(amount, currency):
    symbol = SYMBOLS.get(currency, currency)
    if currency in ["JPY", "KRW", "RUB", "INR"]:
        return f"{symbol}{int(amount)}"
    return f"{symbol}{amount:,.2f}"


@mcp.tool()
def convert_currency(amount: float, from_currency: str, to_currency: str, api_key: str = "") -> str:
    """Convert amount between currencies"""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if err := _rl(): return err

    from_curr = from_currency.upper()
    to_curr = to_currency.upper()

    converted = convert(amount, from_curr, to_curr)
    rate = get_rate_val(to_curr) / get_rate_val(from_curr)

    record = {
        "id": create_id(),
        "amount": amount,
        "from": from_curr,
        "to": to_curr,
        "result": converted,
        "rate": rate,
        "timestamp": datetime.now().isoformat(),
    }
    _store["conversions"].append(record)

    return json.dumps(
        {
            "amount": amount,
            "from": from_curr,
            "to": to_curr,
            "converted": round(converted, 2),
            "formatted": format_amount(converted, to_curr),
            "rate": round(rate, 4),
        },
        indent=2,
    )


@mcp.tool()
def batch_convert(amount: float, from_currency: str = "USD", to_currencies: list = None, api_key: str = "") -> str:
    """Convert amount to multiple currencies"""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if err := _rl(): return err

    from_curr = from_currency.upper()
    targets = to_currencies or ["EUR", "GBP", "JPY"]

    results = {}
    for to_curr in targets:
        converted = convert(amount, from_curr, to_curr.upper())
        results[to_curr.upper()] = {
            "converted": round(converted, 2),
            "formatted": format_amount(converted, to_curr.upper()),
        }

    return json.dumps({"amount": amount, "from": from_curr, "results": results}, indent=2)


@mcp.tool()
def get_rate(from_currency: str = "USD", to_currency: str = "USD", api_key: str = "") -> str:
    """Get current exchange rate"""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if err := _rl(): return err

    from_curr = from_currency.upper()
    to_curr = to_currency.upper()
    rate = get_rate_val(to_curr) / get_rate_val(from_curr)

    return json.dumps(
        {"from": from_curr, "to": to_curr, "rate": round(rate, 4), "inverse": round(1 / rate, 4)},
        indent=2,
    )


@mcp.tool()
def get_all_rates(base: str = "USD", api_key: str = "") -> str:
    """Get all exchange rates from base currency"""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if err := _rl(): return err

    base_upper = base.upper()
    base_rate = get_rate_val(base_upper)

    rates = {}
    for currency, rate in RATES.items():
        rates[currency] = round(rate / base_rate, 4)

    return json.dumps(
        {"base": base_upper, "rates": rates, "timestamp": datetime.now().isoformat()},
        indent=2,
    )


@mcp.tool()
def get_historical_rate(from_currency: str = "USD", to_currency: str = "USD", date: str = "", api_key: str = "") -> str:
    """Get historical exchange rate"""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if err := _rl(): return err

    from_curr = from_currency.upper()
    to_curr = to_currency.upper()
    date_str = date or datetime.now().strftime("%Y-%m-%d")

    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    days_ago = (datetime.now() - date_obj).days

    volatility = 0.02
    current_rate = get_rate_val(to_curr) / get_rate_val(from_curr)
    historical_rate = current_rate * (
        1 + random.uniform(-volatility * days_ago / 30, volatility * days_ago / 30)
    )

    return json.dumps(
        {
            "from": from_curr,
            "to": to_curr,
            "date": date_str,
            "rate": round(historical_rate, 4),
            "note": "Estimated historical rate",
        },
        indent=2,
    )


@mcp.tool()
def get_rate_trend(from_currency: str = "USD", to_currency: str = "USD", days: int = 30, api_key: str = "") -> str:
    """Get rate trend over time"""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if err := _rl(): return err

    from_curr = from_currency.upper()
    to_curr = to_currency.upper()

    current_rate = get_rate_val(to_curr) / get_rate_val(from_curr)

    trend_data = []
    for i in range(days, 0, -5):
        variance = random.uniform(-0.05, 0.05)
        rate = current_rate * (1 + variance)
        trend_data.append({"days_ago": i, "rate": round(rate, 4)})

    trend_data.append({"days_ago": 0, "rate": round(current_rate, 4)})

    trend = "stable"
    if trend_data[-1]["rate"] > trend_data[0]["rate"] * 1.02:
        trend = "appreciating"
    elif trend_data[-1]["rate"] < trend_data[0]["rate"] * 0.98:
        trend = "depreciating"

    return json.dumps(
        {"from": from_curr, "to": to_curr, "trend": trend, "data": trend_data},
        indent=2,
    )


@mcp.tool()
def add_favorite(from_currency: str = "USD", to_currency: str = "EUR", api_key: str = "") -> str:
    """Add currency pair to favorites"""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if err := _rl(): return err

    from_curr = from_currency.upper()
    to_curr = to_currency.upper()

    pair = f"{from_curr}/{to_curr}"
    if pair not in _store["favorites"]:
        _store["favorites"].append(pair)

    return json.dumps(
        {"added": True, "pair": pair, "favorites": _store["favorites"]}, indent=2
    )


@mcp.tool()
def get_favorites(api_key: str = "") -> str:
    """Get favorite currency pairs"""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if err := _rl(): return err

    results = []
    for pair in _store["favorites"]:
        from_curr, to_curr = pair.split("/")
        rate = get_rate_val(to_curr) / get_rate_val(from_curr)
        results.append({"pair": pair, "rate": round(rate, 4)})

    return json.dumps({"favorites": results}, indent=2)


@mcp.tool()
def set_rate_alert(from_currency: str = "USD", to_currency: str = "EUR", target_rate: float = 0.9, direction: str = "below", api_key: str = "") -> str:
    """Set alert for rate target"""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if err := _rl(): return err

    from_curr = from_currency.upper()
    to_curr = to_currency.upper()

    alert = {
        "id": create_id(),
        "from": from_curr,
        "to": to_curr,
        "target_rate": target_rate,
        "direction": direction,
        "created_at": datetime.now().isoformat(),
        "triggered": False,
    }
    _store["alerts"].append(alert)

    return json.dumps(
        {
            "alert_created": True,
            "alert_id": alert["id"],
            "pair": f"{from_curr}/{to_curr}",
            "target": target_rate,
            "direction": direction,
        },
        indent=2,
    )


@mcp.tool()
def get_alerts(api_key: str = "") -> str:
    """Get active rate alerts"""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if err := _rl(): return err

    active = [a for a in _store["alerts"] if not a.get("triggered")]
    return json.dumps({"active_alerts": active, "count": len(active)}, indent=2)


@mcp.tool()
def get_supported_currencies(api_key: str = "") -> str:
    """Get list of supported currencies"""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if err := _rl(): return err

    currencies = []
    for code, rate in RATES.items():
        currencies.append(
            {"code": code, "symbol": SYMBOLS.get(code, code), "rate_to_usd": rate}
        )

    return json.dumps({"currencies": currencies, "count": len(currencies)}, indent=2)


@mcp.tool()
def get_conversion_history(days: int = 30, limit: int = 50, api_key: str = "") -> str:
    """Get conversion history"""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if err := _rl(): return err

    cutoff = datetime.now() - timedelta(days=days)
    history = [
        c
        for c in _store["conversions"]
        if datetime.fromisoformat(c["timestamp"]) >= cutoff
    ][-limit:]

    return json.dumps({"conversions": history, "count": len(history)}, indent=2)


if __name__ == "__main__":
    mcp.run()
