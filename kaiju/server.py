"""KAIJU MCP server core — exposes every tool over MCP (stdio or SSE).

The server is a standard FastMCP instance, so it plugs into ANY MCP
client (Claude Desktop, Cursor, custom agents…) AND runs standalone
via `kaiju run` or the interactive cockpit.
"""

from __future__ import annotations

from kaiju import __version__
from kaiju.config import KaijuConfig
from kaiju.timestamps import info, ok, kaiju
from kaiju.tools import discover


def build_server():
    """Create and fully register the FastMCP server instance."""
    from mcp.server.fastmcp import FastMCP

    cfg = KaijuConfig()

    mcp = FastMCP(
        "kaiju",
        instructions=(
            "KAIJU — the monster MCP server for Linux pentesting, created by "
            "Anonymous-beta. Provides recon (DNS, subdomains, WHOIS, OSINT, zone "
            "transfers), network scanning (ports, ping, traceroute, HTTP probes), "
            "web analysis (dir fuzzing, header audits, WAF detection, tech "
            "fingerprinting), exploit checks (SQLi, XSS, LFI, header injection) "
            "with a built-in payload library, and safe local system access. "
            "All usage must stay within the operator's authorized scope."
        ),
        version=__version__,
    )

    count = 0
    for t in discover():
        mcp.tool(name=t.name, description=t.description)(t.func)
        count += 1
    info(f"Registered {count} core tools")

    # ── the KAIJU exclusive: built-in AI brain as an MCP tool ──
    from kaiju.ai import KaijuAI
    ai = KaijuAI(cfg)

    def ai_analyze(tool: str, target: str, raw_output: str) -> str:
        """Ask the configured AI to interpret tool output and suggest next attack steps."""
        return ai.analyze_results(tool, target, raw_output)

    mcp.tool(
        name="ai_analyze",
        description="Ask the configured AI to analyze raw tool output and recommend next steps",
    )(ai_analyze)
    info("Registered 1 AI tool (ai_analyze)")

    return mcp


def run(transport: str = "stdio", host: str = "127.0.0.1",
        port: int = 8765, banner: bool = True) -> None:
    """Start the server. transport: stdio | sse"""
    if banner:
        kaiju("KAIJU server booting…")
    mcp = build_server()

    if transport == "stdio":
        ok("Listening on stdio — connect any MCP client")
        mcp.run(transport="stdio")
        return

    ok(f"Listening on SSE {host}:{port}")
    try:
        mcp.run(transport="sse", host=host, port=port)
    except TypeError:  # SDK version differences — try the newer transport name
        try:
            mcp.run(transport="streamable-http", host=host, port=port)
        except TypeError:
            mcp.run(transport="sse")
