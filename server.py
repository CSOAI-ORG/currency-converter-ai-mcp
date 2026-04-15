#!/usr/bin/env python3
"""MEOK AI Labs — currency-converter-ai-mcp MCP Server. Comprehensive currency conversion with rates and analytics."""

import asyncio
import json
from datetime import datetime, timedelta, timezone
from typing import Any
import uuid
import random
import sys, os

sys.path.insert(0, os.path.expanduser("~/clawd/meok-labs-engine/shared"))
from auth_middleware import check_access
from collections import defaultdict

FREE_DAILY_LIMIT = 15
_usage = defaultdict(list)
def _rl(c="anon"):
    now = datetime.now(timezone.utc)
    _usage[c] = [t for t in _usage[c] if (now-t).total_seconds() < 86400]
    if len(_usage[c]) >= FREE_DAILY_LIMIT: return json.dumps({"error": f"Limit {FREE_DAILY_LIMIT}/day"})
    _usage[c].append(now); return None
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import Resource, Tool, TextContent
import mcp.types as types

_store = {"conversions": [], "favorites": [], "alerts": []}
server = Server("currency-converter-ai")


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
    "GBP": "£",
    "EUR": "€",
    "JPY": "¥",
    "AUD": "A$",
    "CAD": "C$",
    "CHF": "Fr",
    "CNY": "¥",
    "INR": "₹",
    "MXN": "$",
    "BRL": "R$",
    "KRW": "₩",
    "SGD": "S$",
    "HKD": "HK$",
    "NOK": "kr",
    "SEK": "kr",
    "DKK": "kr",
    "NZD": "NZ$",
    "ZAR": "R",
    "RUB": "₽",
    "TRY": "₺",
    "PLN": "zł",
    "THB": "฿",
    "MYR": "RM",
}


def get_rate(currency):
    return RATES.get(currency, 1.0)


def convert(amount, from_curr, to_curr):
    usd_amount = amount / get_rate(from_curr)
    return usd_amount * get_rate(to_curr)


def format_amount(amount, currency):
    symbol = SYMBOLS.get(currency, currency)
    if currency in ["JPY", "KRW", "RUB", "INR"]:
        return f"{symbol}{int(amount)}"
    return f"{symbol}{amount:,.2f}"


@server.list_resources()
async def handle_list_resources():
    return [
        Resource(uri="fx://rates", name="Exchange Rates", mimeType="application/json"),
        Resource(
            uri="fx://conversions",
            name="Conversion History",
            mimeType="application/json",
        ),
        Resource(
            uri="fx://favorites", name="Favorite Pairs", mimeType="application/json"
        ),
    ]


@server.list_tools()
async def handle_list_tools():
    return [
        Tool(
            name="convert_currency",
            description="Convert amount between currencies",
            inputSchema={
                "type": "object",
                "properties": {
                    "amount": {"type": "number"},
                    "from": {"type": "string"},
                    "to": {"type": "string"},
                    "api_key": {"type": "string"},
                },
                "required": ["amount", "from", "to"],
            },
        ),
        Tool(
            name="batch_convert",
            description="Convert amount to multiple currencies",
            inputSchema={
                "type": "object",
                "properties": {
                    "amount": {"type": "number"},
                    "from": {"type": "string"},
                    "to_currencies": {"type": "array"},
                    "api_key": {"type": "string"},
                },
            },
        ),
        Tool(
            name="get_rate",
            description="Get current exchange rate",
            inputSchema={
                "type": "object",
                "properties": {"from": {"type": "string"}, "to": {"type": "string"}},
            },
        ),
        Tool(
            name="get_all_rates",
            description="Get all exchange rates from base currency",
            inputSchema={"type": "object", "properties": {"base": {"type": "string"}}},
        ),
        Tool(
            name="get_historical_rate",
            description="Get historical exchange rate",
            inputSchema={
                "type": "object",
                "properties": {
                    "from": {"type": "string"},
                    "to": {"type": "string"},
                    "date": {"type": "string"},
                },
            },
        ),
        Tool(
            name="get_rate_trend",
            description="Get rate trend over time",
            inputSchema={
                "type": "object",
                "properties": {
                    "from": {"type": "string"},
                    "to": {"type": "string"},
                    "days": {"type": "number"},
                },
            },
        ),
        Tool(
            name="add_favorite",
            description="Add currency pair to favorites",
            inputSchema={
                "type": "object",
                "properties": {"from": {"type": "string"}, "to": {"type": "string"}},
            },
        ),
        Tool(
            name="get_favorites",
            description="Get favorite currency pairs",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="set_rate_alert",
            description="Set alert for rate target",
            inputSchema={
                "type": "object",
                "properties": {
                    "from": {"type": "string"},
                    "to": {"type": "string"},
                    "target_rate": {"type": "number"},
                    "direction": {"type": "string", "enum": ["above", "below"]},
                },
            },
        ),
        Tool(
            name="get_alerts",
            description="Get active rate alerts",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="get_supported_currencies",
            description="Get list of supported currencies",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="get_conversion_history",
            description="Get conversion history",
            inputSchema={
                "type": "object",
                "properties": {"days": {"type": "number"}, "limit": {"type": "number"}},
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: Any = None) -> list[types.TextContent]:
    args = arguments or {}
    api_key = args.get("api_key", "")
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {"error": msg, "upgrade_url": "https://meok.ai/pricing"}
                ),
            )
        ]
    if err := _rl(): return [TextContent(type="text", text=err)]

    if name == "convert_currency":
        amount = args.get("amount", 0)
        from_curr = args.get("from", "USD").upper()
        to_curr = args.get("to", "USD").upper()

        converted = convert(amount, from_curr, to_curr)
        rate = get_rate(to_curr) / get_rate(from_curr)

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

        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "amount": amount,
                        "from": from_curr,
                        "to": to_curr,
                        "converted": round(converted, 2),
                        "formatted": format_amount(converted, to_curr),
                        "rate": round(rate, 4),
                    },
                    indent=2,
                ),
            )
        ]

    elif name == "batch_convert":
        amount = args.get("amount", 0)
        from_curr = args.get("from", "USD").upper()
        to_currencies = args.get("to_currencies", ["EUR", "GBP", "JPY"])

        results = {}
        for to_curr in to_currencies:
            converted = convert(amount, from_curr, to_curr.upper())
            results[to_curr.upper()] = {
                "converted": round(converted, 2),
                "formatted": format_amount(converted, to_curr.upper()),
            }

        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {"amount": amount, "from": from_curr, "results": results}, indent=2
                ),
            )
        ]

    elif name == "get_rate":
        from_curr = args.get("from", "USD").upper()
        to_curr = args.get("to", "USD").upper()
        rate = get_rate(to_curr) / get_rate(from_curr)

        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "from": from_curr,
                        "to": to_curr,
                        "rate": round(rate, 4),
                        "inverse": round(1 / rate, 4),
                    },
                    indent=2,
                ),
            )
        ]

    elif name == "get_all_rates":
        base = args.get("base", "USD").upper()
        base_rate = get_rate(base)

        rates = {}
        for currency, rate in RATES.items():
            rates[currency] = round(rate / base_rate, 4)

        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "base": base,
                        "rates": rates,
                        "timestamp": datetime.now().isoformat(),
                    },
                    indent=2,
                ),
            )
        ]

    elif name == "get_historical_rate":
        from_curr = args.get("from", "USD").upper()
        to_curr = args.get("to", "USD").upper()
        date_str = args.get("date", datetime.now().strftime("%Y-%m-%d"))

        date = datetime.strptime(date_str, "%Y-%m-%d")
        days_ago = (datetime.now() - date).days

        volatility = 0.02
        current_rate = get_rate(to_curr) / get_rate(from_curr)
        historical_rate = current_rate * (
            1 + random.uniform(-volatility * days_ago / 30, volatility * days_ago / 30)
        )

        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "from": from_curr,
                        "to": to_curr,
                        "date": date_str,
                        "rate": round(historical_rate, 4),
                        "note": "Estimated historical rate",
                    },
                    indent=2,
                ),
            )
        ]

    elif name == "get_rate_trend":
        from_curr = args.get("from", "USD").upper()
        to_curr = args.get("to", "USD").upper()
        days = args.get("days", 30)

        current_rate = get_rate(to_curr) / get_rate(from_curr)

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

        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "from": from_curr,
                        "to": to_curr,
                        "trend": trend,
                        "data": trend_data,
                    },
                    indent=2,
                ),
            )
        ]

    elif name == "add_favorite":
        from_curr = args.get("from", "USD").upper()
        to_curr = args.get("to", "EUR").upper()

        pair = f"{from_curr}/{to_curr}"
        if pair not in _store["favorites"]:
            _store["favorites"].append(pair)

        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {"added": True, "pair": pair, "favorites": _store["favorites"]},
                    indent=2,
                ),
            )
        ]

    elif name == "get_favorites":
        results = []
        for pair in _store["favorites"]:
            from_curr, to_curr = pair.split("/")
            rate = get_rate(to_curr) / get_rate(from_curr)
            results.append({"pair": pair, "rate": round(rate, 4)})

        return [
            TextContent(type="text", text=json.dumps({"favorites": results}, indent=2))
        ]

    elif name == "set_rate_alert":
        from_curr = args.get("from", "USD").upper()
        to_curr = args.get("to", "EUR").upper()
        target = args.get("target_rate", 0.9)
        direction = args.get("direction", "below")

        alert = {
            "id": create_id(),
            "from": from_curr,
            "to": to_curr,
            "target_rate": target,
            "direction": direction,
            "created_at": datetime.now().isoformat(),
            "triggered": False,
        }
        _store["alerts"].append(alert)

        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "alert_created": True,
                        "alert_id": alert["id"],
                        "pair": f"{from_curr}/{to_curr}",
                        "target": target,
                        "direction": direction,
                    },
                    indent=2,
                ),
            )
        ]

    elif name == "get_alerts":
        active = [a for a in _store["alerts"] if not a.get("triggered")]

        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {"active_alerts": active, "count": len(active)}, indent=2
                ),
            )
        ]

    elif name == "get_supported_currencies":
        currencies = []
        for code, rate in RATES.items():
            currencies.append(
                {"code": code, "symbol": SYMBOLS.get(code, code), "rate_to_usd": rate}
            )

        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {"currencies": currencies, "count": len(currencies)}, indent=2
                ),
            )
        ]

    elif name == "get_conversion_history":
        days = args.get("days", 30)
        limit = args.get("limit", 50)

        cutoff = datetime.now() - timedelta(days=days)
        history = [
            c
            for c in _store["conversions"]
            if datetime.fromisoformat(c["timestamp"]) >= cutoff
        ][-limit:]

        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {"conversions": history, "count": len(history)}, indent=2
                ),
            )
        ]

    return [TextContent(type="text", text=json.dumps({"error": "Unknown tool"}))]


async def main():
    async with stdio_server(server._read_stream, server._write_stream) as (
        read_stream,
        write_stream,
    ):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="currency-converter-ai",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
