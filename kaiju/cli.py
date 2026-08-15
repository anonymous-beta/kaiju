"""KAIJU command-line interface.

    kaiju                     splash + help
    kaiju run [--transport stdio|sse] [--host H] [--port P]
    kaiju config --ai         AI API paste-and-go wizard
    kaiju config --show       dump current config
    kaiju config --set 'ai.model gpt-4o'
    kaiju config --reset
    kaiju tools               list the arsenal
    kaiju ai <question>       ask the AI brain
    kaiju tui                 launch the interactive cockpit
    kaiju banner
"""

from __future__ import annotations

import argparse
import json
import sys

from kaiju import __version__, __author__
from kaiju.config import KaijuConfig, PROVIDERS
from kaiju.timestamps import info, ok, warn, error, kaiju


# ── subcommands ──────────────────────────────────────────

def cmd_run(args) -> int:
    from kaiju.server import run
    run(transport=args.transport, host=args.host, port=args.port,
        banner=not args.no_banner)
    return 0


def cmd_config(args) -> int:
    cfg = KaijuConfig()

    if args.show:
        print(json.dumps(cfg.data, indent=2))
        return 0

    if args.reset:
        cfg.path.unlink(missing_ok=True)
        ok("Config wiped — KAIJU back to factory settings.")
        return 0

    if args.set:
        parts = args.set.split(" ", 1)
        if len(parts) != 2 or "." not in parts[0]:
            error("Usage: kaiju config --set 'section.key value'  e.g. 'ai.model gpt-4o'")
            return 1
        section, key = parts[0].split(".", 1)
        val: object = parts[1]
        if val.lower() in ("true", "false"):
            val = val.lower() == "true"
        elif val.isdigit():
            val = int(val)
        cfg.set(section, key, val)
        cfg.save()
        ok(f"Set {parts[0]} = {val}")
        return 0

    if not args.ai:
        info("Usage: kaiju config --ai  |  --show  |  --set 'section.key value'  |  --reset")
        return 0

    return _ai_wizard(cfg)


def _ai_wizard(cfg: KaijuConfig) -> int:
    """The slick paste-and-go AI setup."""
    from questionary import select, text, password, confirm
    from kaiju.ai import KaijuAI

    kaiju("AI configuration wizard — paste your key, we do the rest.")
    provider = select("Choose AI provider:", choices=list(PROVIDERS.keys())).ask()
    if not provider:
        return 1

    base_url = PROVIDERS[provider]["base_url"]
    model = PROVIDERS[provider]["model"]
    if provider == "custom":
        base_url = text(
            "Custom OpenAI-compatible base URL\n(e.g. http://localhost:11434/v1 for Ollama):"
        ).ask() or ""
        model = text("Default model name:").ask() or ""

    api_key = password(
        "Paste your API key (blank only if endpoint needs none, e.g. local Ollama):"
    ).ask() or ""

    if provider != "custom":
        model = text("Model:", default=model).ask() or model

    cfg.set("ai", "provider", provider)
    cfg.set("ai", "base_url", base_url)
    cfg.set("ai", "api_key", api_key)
    cfg.set("ai", "model", model)
    cfg.save()

    ai = KaijuAI(cfg)
    if api_key or provider == "ollama":
        if ai.test_connection():
            enabled = confirm("Enable AI mode?", default=True).ask()
            cfg.set("ai", "enabled", bool(enabled))
            cfg.save()
            ok("AI configuration complete — KAIJU is now self-aware.")
        else:
            warn("Connection failed — config saved anyway; fix endpoint and re-test.")
    else:
        cfg.set("ai", "enabled", False)
        cfg.save()
        warn("No API key given — AI stays disabled for now.")
    return 0


def cmd_tools(args) -> int:
    from rich.console import Console
    from rich.table import Table
    from rich import box
    from kaiju.tools import discover

    console = Console()
    tools = sorted(discover(), key=lambda t: (t.category, t.name))
    table = Table(
        title=f"KAIJU arsenal — {len(tools)} tools",
        box=box.HEAVY_HEAD, border_style="red",
    )
    table.add_column("Tool", style="bold cyan", no_wrap=True)
    table.add_column("Category", style="magenta")
    table.add_column("Description")
    for t in tools:
        badge = "  [bold yellow]⚠[/]" if t.dangerous else ""
        table.add_row(t.name, t.category, t.description + badge)
    console.print(table)
    return 0


def cmd_ai(args) -> int:
    from rich.console import Console
    from kaiju.ai import KaijuAI

    console = Console()
    cfg = KaijuConfig()
    if not cfg.ai_enabled:
        error("AI not configured — run: kaiju config --ai")
        return 1
    question = " ".join(args.question)
    info(f"KAIJU AI thinking about: {question}")
    ai = KaijuAI(cfg)
    answer = ai.chat(
        [{"role": "user", "content": question}],
        system=KaijuAI.PENTEST_SYSTEM,
    )
    console.print(answer, markup=False)
    return 0


def cmd_tui(args) -> int:
    from kaiju.ui.tui import KaijuTUI
    KaijuTUI().run()
    return 0


def cmd_banner(args) -> int:
    from kaiju.banner import render_banner
    print(render_banner())
    return 0


# ── main ─────────────────────────────────────────────────

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="kaiju",
        description="KAIJU — the monster MCP server for Linux pentesting (by Anonymous-beta)",
    )
    parser.add_argument("--version", action="version",
                        version=f"KAIJU v{__version__} — created by {__author__} 🦖")

    sub = parser.add_subparsers(dest="command")

    p_run = sub.add_parser("run", help="Start the MCP server (stdio or SSE)")
    p_run.add_argument("--transport", choices=["stdio", "sse"], default="stdio")
    p_run.add_argument("--host", default="127.0.0.1")
    p_run.add_argument("--port", type=int, default=8765)
    p_run.add_argument("--no-banner", action="store_true")
    p_run.set_defaults(func=cmd_run)

    p_cfg = sub.add_parser("config", help="AI API config + settings")
    p_cfg.add_argument("--ai", action="store_true", help="Run the paste-and-go AI wizard")
    p_cfg.add_argument("--show", action="store_true", help="Show current config")
    p_cfg.add_argument("--set", metavar="'section.key value'", help="Set a config value")
    p_cfg.add_argument("--reset", action="store_true", help="Wipe config")
    p_cfg.set_defaults(func=cmd_config)

    p_tools = sub.add_parser("tools", help="List every tool")
    p_tools.set_defaults(func=cmd_tools)

    p_ai = sub.add_parser("ai", help="Ask the KAIJU AI brain")
    p_ai.add_argument("question", nargs="+")
    p_ai.set_defaults(func=cmd_ai)

    p_tui = sub.add_parser("tui", help="Launch the interactive terminal cockpit")
    p_tui.set_defaults(func=cmd_tui)

    p_banner = sub.add_parser("banner", help="Print the banner")
    p_banner.set_defaults(func=cmd_banner)

    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        from kaiju.banner import splash
        splash()
        parser.print_help()
        return 0
    return args.func(args) or 0


if __name__ == "__main__":
    sys.exit(main())
