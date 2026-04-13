from mcp.server.fastmcp import FastMCP

mcp = FastMCP("currency-converter")

RATES = {
    "USD": 1.0,
    "EUR": 0.92,
    "GBP": 0.79,
    "JPY": 150.2,
    "CAD": 1.35,
    "AUD": 1.52,
    "CHF": 0.88,
    "CNY": 7.19,
    "INR": 83.1,
    "BRL": 4.95,
}

@mcp.tool()
def convert_currency(amount: float, from_currency: str, to_currency: str) -> dict:
    """Convert amount between currencies."""
    fc = from_currency.upper()
    tc = to_currency.upper()
    if fc not in RATES or tc not in RATES:
        return {"error": "Unsupported currency", "supported": list(RATES.keys())}
    base = amount / RATES[fc]
    converted = base * RATES[tc]
    return {
        "original_amount": amount,
        "from": fc,
        "to": tc,
        "converted_amount": round(converted, 4),
        "rate": round(RATES[tc] / RATES[fc], 6),
    }

@mcp.tool()
def list_supported_currencies() -> dict:
    """Return supported currency codes."""
    return {"currencies": list(RATES.keys()), "base": "USD"}

@mcp.tool()
def batch_convert(amount: float, from_currency: str, to_currencies: list) -> dict:
    """Convert amount to multiple currencies."""
    results = {}
    for tc in to_currencies:
        results[tc.upper()] = convert_currency(amount, from_currency, tc)
    return {"base_amount": amount, "from": from_currency.upper(), "conversions": results}

def main():
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
