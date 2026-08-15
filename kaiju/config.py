"""KAIJU configuration manager.

Stores config in ~/.config/kaiju/config.json (XDG-compliant).
Handles the AI API configuration: paste a key → test → save.
Supports any OpenAI-compatible endpoint out of the box:
  OpenAI, OpenRouter, Groq, Together, local Ollama, vLLM,
  LM Studio, or any custom base_url.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from kaiju.timestamps import info, ok, warn, error

CONFIG_DIR = Path(
    os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")
) / "kaiju"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULTS: Dict[str, Any] = {
    "ai": {
        "enabled": False,
        "provider": "openai",
        "api_key": "",
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o-mini",
        "temperature": 0.4,
        "max_tokens": 1024,
    },
    "ui": {
        "theme": "kaiju_red",
        "banner": True,
        "timestamps": True,
    },
    "mcp": {
        "name": "kaiju",
        "host": "127.0.0.1",
        "port": 8765,
        "transport": "stdio",      # stdio | sse
    },
    "safe_mode": True,             # blocks destructive tools when True
    "log_file": "",
}

PROVIDERS = {
    "openai":      {"base_url": "https://api.openai.com/v1",      "model": "gpt-4o-mini"},
    "openrouter":  {"base_url": "https://openrouter.ai/api/v1",   "model": "openai/gpt-4o-mini"},
    "groq":        {"base_url": "https://api.groq.com/openai/v1", "model": "llama-3.3-70b-versatile"},
    "together":    {"base_url": "https://api.together.xyz/v1",    "model": "meta-llama/Llama-3.3-70B-Instruct-Turbo"},
    "mistral":     {"base_url": "https://api.mistral.ai/v1",      "model": "mistral-small-latest"},
    "ollama":      {"base_url": "http://localhost:11434/v1",      "model": "llama3.1"},
    "custom":      {"base_url": "",                               "model": ""},
}


class KaijuConfig:
    """Load/save KAIJU config."""

    def __init__(self, path: Path = CONFIG_FILE):
        self.path = path
        self.data = self._load()

    def _load(self) -> Dict[str, Any]:
        if self.path.exists():
            try:
                loaded = json.loads(self.path.read_text())
                merged = dict(DEFAULTS)
                merged.update(loaded)
                return merged
            except json.JSONDecodeError:
                warn(f"Config corrupted at {self.path} — using defaults.")
                return dict(DEFAULTS)
        return dict(DEFAULTS)

    def save(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=2))
        ok(f"Config saved → {self.path}")

    # ── getters ────────────────────────────────────────
    def get(self, section: str, key: Optional[str] = None, default: Any = None) -> Any:
        if key is None:
            return self.data.get(section, DEFAULTS.get(section, {}))
        return self.data.get(section, {}).get(key, default)

    def set(self, section: str, key: str, value: Any) -> None:
        self.data.setdefault(section, {})[key] = value

    # ── AI helpers ─────────────────────────────────────
    @property
    def ai_enabled(self) -> bool:
        return bool(self.data["ai"].get("enabled") and self.data["ai"].get("api_key"))

    def describe_ai(self) -> str:
        ai = self.data["ai"]
        state = "ON" if self.ai_enabled else "OFF"
        return (f"AI {state} | provider={ai['provider']} | model={ai['model']} | "
                f"endpoint={ai['base_url']}")
