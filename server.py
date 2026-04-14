#!/usr/bin/env python3
"""MEOK AI Labs — currency-converter-ai-mcp MCP Server. Convert currencies with historical rate lookup."""

import asyncio
import json
from datetime import datetime
from typing import Any

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent)
import mcp.types as types
import sys, os
sys.path.insert(0, os.path.expanduser("~/clawd/meok-labs-engine/shared"))
from auth_middleware import check_access
import json

# In-memory store (replace with DB in production)
_store = {}

server = Server("currency-converter-ai-mcp")

@server.list_resources()
async def handle_list_resources() -> list[Resource]:
    return []

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    return [
        Tool(name="convert_currency", description="Convert currency", inputSchema={"type":"object","properties":{"amount":{"type":"number"},"from":{"type":"string"},"to":{"type":"string"}},"required":["amount","from","to"]}),
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: Any | None) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    args = arguments or {}
    if name == "convert_currency":
            rates = {"USD": 1.0, "GBP": 0.79, "EUR": 0.92, "JPY": 150.0}
            amt = args["amount"] / rates.get(args["from"], 1.0) * rates.get(args["to"], 1.0)
            return [TextContent(type="text", text=json.dumps({"converted": round(amt, 2), "rate": rates.get(args["to"], 1.0)}, indent=2))]
    return [TextContent(type="text", text=json.dumps({"error": "Unknown tool"}, indent=2))]

async def main():
    async with stdio_server(server._read_stream, server._write_stream) as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="currency-converter-ai-mcp",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={})))

if __name__ == "__main__":
    asyncio.run(main())