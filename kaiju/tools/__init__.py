"""KAIJU tool registry — every tool in one place."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List


@dataclass
class Tool:
    name: str
    description: str
    func: Callable[..., str]
    category: str = "general"
    dangerous: bool = False      # active attack tool — gated by safe_mode where relevant


def discover() -> List[Tool]:
    """Import all tool modules and return the full registry."""
    from kaiju.tools import recon, network, web, exploit, system

    tools: List[Tool] = []
    for module in (recon, network, web, exploit, system):
        tools.extend(getattr(module, "TOOLS", []))
    return tools


def get(name: str) -> Tool:
    for t in discover():
        if t.name == name:
            return t
    raise KeyError(f"Tool '{name}' not found")
