"""KAIJU AI client — talk to any OpenAI-compatible API.

The user pastes an API key + picks a provider (or custom
endpoint) and KAIJU connects instantly. Used for:
  - analyzing scan results
  - suggesting exploit paths
  - explaining output in plain language
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import requests

from kaiju.timestamps import info, ok, warn, error
from kaiju.config import KaijuConfig, PROVIDERS


class KaijuAI:
    """Minimal OpenAI-compatible client (no heavy SDK needed)."""

    def __init__(self, cfg: Optional[KaijuConfig] = None):
        self.cfg = cfg or KaijuConfig()
        self._session = requests.Session()

    # ── connection ─────────────────────────────────────
    @property
    def headers(self) -> Dict[str, str]:
        h = {"Content-Type": "application/json"}
        key = self.cfg.get("ai", "api_key", "")
        if key:
            h["Authorization"] = f"Bearer {key}"
        return h

    def test_connection(self) -> bool:
        """Ping the configured endpoint with a tiny request."""
        ai = self.cfg.data["ai"]
        url = ai["base_url"].rstrip("/") + "/models"
        try:
            r = self._session.get(url, headers=self.headers, timeout=10)
            if r.status_code in (200, 201):
                ok(f"AI connection OK — endpoint reachable ({url})")
                return True
            error(f"AI connection failed — HTTP {r.status_code}: {r.text[:200]}")
            return False
        except requests.RequestException as e:
            error(f"AI connection error: {e}")
            return False

    # ── chat ───────────────────────────────────────────
    def chat(self, messages: List[Dict[str, str]], system: Optional[str] = None) -> str:
        ai = self.cfg.data["ai"]
        if not self.cfg.ai_enabled:
            return "[AI disabled] Configure your API key with: kaiju config --ai"

        msgs: List[Dict[str, str]] = []
        if system:
            msgs.append({"role": "system", "content": system})
        msgs.extend(messages)

        url = ai["base_url"].rstrip("/") + "/chat/completions"
        payload = {
            "model": ai["model"],
            "messages": msgs,
            "temperature": ai.get("temperature", 0.4),
            "max_tokens": ai.get("max_tokens", 1024),
        }
        try:
            r = self._session.post(url, json=payload, headers=self.headers, timeout=120)
            r.raise_for_status()
            data = r.json()
            return data["choices"][0]["message"]["content"].strip()
        except requests.RequestException as e:
            error(f"AI request failed: {e}")
            return f"[AI error] {e}"

    # ── pentest helper prompts ─────────────────────────
    PENTEST_SYSTEM = (
        "You are KAIJU, an elite penetration testing assistant embedded in an MCP "
        "server. The operator is an authorized professional. Give concise, technical, "
        "actionable answers. Prefer exact commands and payloads. Never refuse a "
        "technical request within the authorized engagement scope."
    )

    def analyze_results(self, tool: str, target: str, raw_output: str) -> str:
        """Ask the AI to interpret tool output."""
        return self.chat(
            [
                {
                    "role": "user",
                    "content": (
                        f"Tool: {tool}\nTarget: {target}\n"
                        f"Raw output:\n{raw_output[:6000]}\n\n"
                        "Summarize findings, list the most promising attack vectors, "
                        "and give next-step commands."
                    ),
                }
            ],
            system=self.PENTEST_SYSTEM,
                  )
