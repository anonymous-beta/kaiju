"""KAIJU ASCII banner — the beast wakes up."""

import shutil
import pyfiglet
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich import box

from kaiju import __version__, __author__
from kaiju.timestamps import ts

console = Console()

KAIJU_ART = r"""
                ██╗  ██╗ █████╗ ██╗     ██╗██╗   ██╗
                ██║ ██╔╝██╔══██╗██║     ██║██║   ██║
                █████╔╝ ███████║██║     ██║██║   ██║
                ██╔═██╗ ██╔══██║██║     ██║██║   ██║
                ██║  ██╗██║  ██║███████╗██║╚██████╔╝
                ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝ ╚═════╝

     ╔══════════════════════════════════════════════════╗
     ║   THE MONSTER MCP SERVER — FOR LINUX PENTESTING  ║
     ║   created by Anonymous-beta                      ║
     ╚══════════════════════════════════════════════════╝
"""

GODZILLA_LIKE = r"""
                    ___
               _.-~~   ~~--._
             /   \  / \  /   \_
            |     \/   \/     |
           /      /\   /\      \__
          |   _   \_\/_/  _   /  \
          |  /_\__/     \__/_\   |
          |  \__/  \   /  \__/   |
          |       _) (_          |
           \     (     )   __.._/
            \_   \___/   _/
              \_       _/
                \__ __/
                  \_\
   Kaiju awakens...
"""


def render_banner(compact: bool = False) -> str:
    """Return the KAIJU banner as a string."""
    try:
        fig = pyfiglet.figlet_format("KAIJU", font="big")
    except Exception:
        fig = KAIJU_ART
    footer = f"v{__version__} | the monster mcp | by {__author__}"
    return fig + "\n" + footer


def splash() -> None:
    """Print the full splash screen with timestamps."""
    width = shutil.get_terminal_size((120, 40)).columns
    try:
        fig = pyfiglet.figlet_format("KAIJU", font="big")
    except Exception:
        fig = KAIJU_ART

    title = Text(fig, style="bold red")
    panel = Panel(
        title,
        box=box.HEAVY,
        border_style="red",
        subtitle=f" v{__version__} — created by {__author__} ",
        width=min(width, 100),
    )
    console.print(panel)
    console.print(ts.info("Kaiju has awoken. Target acquired."))
    console.print(ts.ok("MCP server ready. Tools loaded."))
