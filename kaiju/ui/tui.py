"""KAIJU interactive cockpit — pick a tool, aim, fire, all in one screen."""

from __future__ import annotations

import shlex

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from rich import box

from kaiju.timestamps import info, ok, warn, error, kaiju
from kaiju.tools import discover, get


class KaijuTUI:
    def __init__(self):
        self.console = Console()
        self.tools = sorted(discover(), key=lambda t: (t.category, t.name))

    def _header(self) -> None:
        from kaiju.banner import splash
        splash()

    def _menu(self) -> None:
        table = Table(title="KAIJU COCKPIT — arsenal", box=box.HEAVY_HEAD,
                      border_style="red", show_lines=False)
        table.add_column("#", style="bold red", width=3)
        table.add_column("Tool", style="bold cyan")
        table.add_column("Category", style="magenta")
        table.add_column("Description")
        for i, t in enumerate(self.tools, 1):
            table.add_row(str(i), t.name, t.category, t.description)
        table.add_row("", "ai_ask", "ai", "Chat with the KAIJU AI brain")
        table.add_row("", "help", "—", "Show this menu")
        table.add_row("", "exit", "—", "Leave the cockpit")
        self.console.print(table)

    def _call(self, name: str, args: str) -> None:
        try:
            tool = get(name)
        except KeyError:
            error(f"Unknown tool: {name} — type 'help'")
            return
        params = shlex.split(args)
        try:
            info(f"Firing {name} with {params}")
            result = tool.func(*params)
            self.console.print(Panel(result, title=f"⚡ {name} output",
                                     border_style="green"))
        except TypeError as e:
            error(f"Bad arguments for {name}: {e}")
            self.console.print(f"usage: {name} <args…>")
        except Exception as e:
            error(f"{name} crashed: {e}")

    def run(self) -> None:
        self._header()
        kaiju("Cockpit engaged. Type 'help' for the menu, 'exit' to leave.")
        while True:
            try:
                raw = Prompt.ask("[bold red]kaiju[/bold red]")
            except (KeyboardInterrupt, EOFError):
                ok("Kaiju goes back to sleep. Sayonara.")
                return
            raw = raw.strip()
            if not raw:
                continue
            parts = shlex.split(raw)
            cmd, args = parts[0].lower(), " ".join(parts[1:])
            if cmd in ("exit", "quit", "q"):
                ok("Kaiju goes back to sleep. Sayonara.")
                return
            if cmd == "help":
                self._menu()
                continue
            self._call(cmd, args)
