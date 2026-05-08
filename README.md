<div align="center">

# Currency Converter Ai MCP

**MCP server for currency converter ai mcp operations**

[![PyPI](https://img.shields.io/pypi/v/meok-currency-converter-ai-mcp)](https://pypi.org/project/meok-currency-converter-ai-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![MEOK AI Labs](https://img.shields.io/badge/MEOK_AI_Labs-MCP_Server-purple)](https://meok.ai)

</div>

## Overview

Currency Converter Ai MCP provides AI-powered tools via the Model Context Protocol (MCP).

## Tools

| Tool | Description |
|------|-------------|
| `convert_currency` | Convert amount between currencies |
| `batch_convert` | Convert amount to multiple currencies |
| `get_rate` | Get current exchange rate |
| `get_all_rates` | Get all exchange rates from base currency |
| `get_historical_rate` | Get historical exchange rate |
| `get_rate_trend` | Get rate trend over time |
| `add_favorite` | Add currency pair to favorites |
| `get_favorites` | Get favorite currency pairs |
| `set_rate_alert` | Set alert for rate target |
| `get_alerts` | Get active rate alerts |
| `get_supported_currencies` | Get list of supported currencies |
| `get_conversion_history` | Get conversion history |

## Installation

```bash
pip install meok-currency-converter-ai-mcp
```

## Usage with Claude Desktop

Add to your Claude Desktop MCP config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "currency-converter-ai": {
      "command": "python",
      "args": ["-m", "meok_currency_converter_ai_mcp.server"]
    }
  }
}
```

## Usage with FastMCP

```python
from mcp.server.fastmcp import FastMCP

# This server exposes 12 tool(s) via MCP
# See server.py for full implementation
```

## License

MIT © [MEOK AI Labs](https://meok.ai)
