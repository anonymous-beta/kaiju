"""KAIJU timestamps — beautiful, colored, consistent.

Every log line gets a styled timestamp like:

    [14:32:05] ⚡ KAIJU | INFO | message

Configurable: enable/disable, colors, icon, format.
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Optional

from rich.console import Console
from rich.text import Text

console = Console()

# Global style knobs — change at runtime with set_style()
_STYLE = {
    "enabled": True,
    "show_icon": True,
    "icon": "⚡",
    "time_format": "%H:%M:%S",
    "show_date": False,
    "brackets": ("[", "]"),
    "separator": " | ",
    "colors": {
        "time": "bold cyan",
        "level": {
            "INFO": "cyan",
            "OK": "bold green",
            "WARN": "bold yellow",
            "ERROR": "bold red",
            "DEBUG": "dim magenta",
            "CRIT": "bold white on red",
            "KAJU": "bold red",
        },
        "icon": "yellow",
    },
}


def set_style(**kwargs) -> None:
    """Update timestamp style at runtime."""
    for k, v in kwargs.items():
        if k in _STYLE:
            _STYLE[k] = v


def _now() -> str:
    fmt = _STYLE["time_format"]
    if _STYLE["show_date"]:
        fmt = "%Y-%m-%d " + fmt
    return datetime.now().strftime(fmt)


def _base(level: str, message: str, to_console: bool = True) -> str:
    s = _STYLE
    if not s["enabled"]:
        return message

    lb, rb = s["brackets"]
    time_part = f"{lb}{_now()}{rb}"
    icon = f" {s['icon']} " if s["show_icon"] else " "
    lvl_color = s["colors"]["level"].get(level.upper(), "white")
    lvl_part = f"{lb}{level.upper()}{rb}"

    if to_console:
        t = Text()
        t.append(time_part, style=s["colors"]["time"])
        t.append(icon, style=s["colors"]["icon"])
        t.append(lvl_part, style=lvl_color)
        t.append(s["separator"], style="dim")
        t.append(message)
        console.print(t)
        return ""
    return f"{time_part}{icon}{lvl_part}{s['separator']}{message}"


# ── public API ──────────────────────────────────────────
def info(msg: str) -> str:
    return _base("INFO", msg)


def ok(msg: str) -> str:
    return _base("OK", msg)


def warn(msg: str) -> str:
    return _base("WARN", msg)


def error(msg: str) -> str:
    return _base("ERROR", msg)


def debug(msg: str) -> str:
    return _base("DEBUG", msg)


def crit(msg: str) -> str:
    return _base("CRIT", msg)


def kaiju(msg: str) -> str:
    """The signature KAIJU line."""
    return _base("KAJU", msg)


def raw(msg: str, style: str = "white") -> str:
    console.print(msg, style=style)
    return ""


def banner_line(msg: str) -> str:
    """Timestamped line used inside banners/panels."""
    return _base("KAJU", msg, to_console=False)
