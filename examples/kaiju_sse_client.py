"""Connect a custom MCP client to KAIJU over SSE.

Usage:
    kaiju run --transport sse --host 127.0.0.1 --port 8765
    python3 examples/kaiju_sse_client.py
"""

import asyncio
from mcp import ClientSession
from mcp.client.sse import sse_client


async def main():
    async with sse_client("http://127.0.0.1:8765/sse") as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print(f"⚡ KAIJU connected — {len(tools.tools)} tools armed\n")
            for t in sorted(tools.tools, key=lambda x: x.name):
                print(f"  {t.name:24s} {t.description.splitlines()[0]}")


if __name__ == "__main__":
    asyncio.run(main())
