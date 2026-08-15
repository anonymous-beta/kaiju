"""KAIJU system tools — safe command execution and file ops.

safe_mode=True (default): command_exec runs via a RESTRICTED allowlist
and file_read is limited to <10MB in the current directory tree.
Disable safe_mode only on dedicated test boxes: kaiju config --set 'safe_mode false'
"""

from __future__ import annotations

import os
import re
import shlex
import subprocess
from pathlib import Path

from kaiju.tools import Tool
from kaiju.config import KaijuConfig

ALLOWED_BINARIES = {
    "ip", "ss", "netstat", "whoami", "id", "uname", "hostname", "uptime",
    "ps", "df", "du", "ls", "find", "cat", "head", "tail", "grep", "curl",
    "wget", "dig", "nslookup", "host", "nmap", "ping", "traceroute",
    "whois", "git", "python3", "bash", "sh", "openssl", "base64", "xxd",
    "awk", "sed", "sort", "uniq", "wc", "date", "env", "groups", "last",
}

# Blocks shell chaining/metacharacters and destructive keywords in safe_mode
_SHELL_META = re.compile(r"[;|&`$()<>]|\b(rm|mkfs|dd|shutdown|reboot|halt|poweroff)\b")


def _cfg():
    return KaijuConfig()


def command_exec(command: str, timeout: int = 60) -> str:
    """Execute a shell command. In safe_mode only allowlisted binaries run,
    with no shell metacharacters or destructive keywords."""
    safe = _cfg().get("safe_mode", True)
    try:
        parts = shlex.split(command)
    except ValueError as e:
        return f"ERROR: cannot parse command: {e}"
    if not parts:
        return "ERROR: empty command"

    if safe:
        if parts[0] not in ALLOWED_BINARIES:
            return (f"BLOCKED by safe_mode: '{parts[0]}' not in allowlist.\n"
                    f"Allowed: {', '.join(sorted(ALLOWED_BINARIES))}\n"
                    f"Disable with: kaiju config --set 'safe_mode false'")
        if parts[0] in ("bash", "sh", "python3"):
            return "BLOCKED by safe_mode: interpreted shells require safe_mode off"
        if _SHELL_META.search(command):
            return ("BLOCKED by safe_mode: shell metacharacters / destructive "
                    "commands not allowed. Disable safe_mode for full shell power.")

    try:
        # safe_mode: argv list, no shell interpretation (no pipes/redirects)
        r = subprocess.run(parts if safe else command,
                           shell=not safe,
                           capture_output=True, text=True, timeout=timeout)
        out = r.stdout
        if r.stderr:
            out += "\n[stderr] " + r.stderr[:2000]
        if r.returncode != 0:
            out += f"\n[exit code: {r.returncode}]"
        return out.strip() or "(no output)"
    except subprocess.TimeoutExpired:
        return f"ERROR: command timed out after {timeout}s"
    except Exception as e:
        return f"ERROR: {e}"


def file_read(path: str, max_bytes: int = 10 * 1024 * 1024) -> str:
    """Read a file. Default cap: 10MB, current tree only when safe_mode."""
    p = Path(path).expanduser()
    if not p.exists():
        return f"ERROR: no such file: {path}"
    if not p.is_file():
        return f"ERROR: not a regular file: {path}"
    if _cfg().get("safe_mode", True):
        try:
            p.resolve().relative_to(Path.cwd().resolve())
        except ValueError:
            return f"BLOCKED by safe_mode: {path} is outside the working tree"
    if p.stat().st_size > max_bytes:
        return f"ERROR: file too large ({p.stat().st_size} bytes > {max_bytes})"
    try:
        return p.read_text(encoding="utf-8", errors="replace")[:max_bytes]
    except OSError as e:
        return f"ERROR: {e}"


def file_write(path: str, content: str) -> str:
    """Write text to a file (safe_mode: working tree only)."""
    p = Path(path).expanduser()
    if _cfg().get("safe_mode", True):
        try:
            p.resolve().relative_to(Path.cwd().resolve())
        except ValueError:
            return f"BLOCKED by safe_mode: {path} is outside the working tree"
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"Wrote {len(content)} bytes → {p}"
    except OSError as e:
        return f"ERROR: {e}"


def list_directory(path: str = ".") -> str:
    """List a directory with sizes and types."""
    p = Path(path).expanduser()
    if not p.is_dir():
        return f"ERROR: not a directory: {path}"
    out = [f"Listing: {p.resolve()}"]
    try:
        for entry in sorted(p.iterdir(), key=lambda e: e.name.lower()):
            if entry.is_dir():
                out.append(f"  [d] {entry.name}/")
            else:
                try:
                    size = entry.stat().st_size
                    out.append(f"  [f] {entry.name} ({size}B)")
                except OSError:
                    out.append(f"  [f] {entry.name}")
    except OSError as e:
        return f"ERROR: {e}"
    return "\n".join(out)


TOOLS = [
    Tool("command_exec", "Run shell commands (safe_mode allowlist by default)", command_exec, "system", dangerous=True),
    Tool("file_read", "Read text files (10MB cap, tree-restricted in safe_mode)", file_read, "system"),
    Tool("file_write", "Write text files (tree-restricted in safe_mode)", file_write, "system", dangerous=True),
    Tool("list_directory", "List directory contents with sizes", list_directory, "system"),
  ]
