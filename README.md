# 🦖 KAIJU — The Monster MCP Server

```
██╗  ██╗ █████╗ ██╗     ██╗██╗   ██╗
██║ ██╔╝██╔══██╗██║     ██║██║   ██║
█████╔╝ ███████║██║     ██║██║   ██║
██╔═██╗ ██╔══██║██║     ██║██║   ██║
██║  ██╗██║  ██║███████╗██║╚██████╔╝
╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝ ╚═════╝
```

**KAIJU** — the standalone, AI-powered MCP server for Linux pentesting. Recon, scanning, web attacks, exploit checks, a built-in payload library, and an AI brain — all wrapped in a beautiful terminal UI with signature timestamps. Created by **Anonymous-beta**.

> *"Kaiju awakens. Target acquired."*

---

## ⚡ Why KAIJU?

| Feature | KAIJU | Typical MCP server |
|---|---|---|
| Recon arsenal (DNS, subdomains, WHOIS, OSINT, AXFR) | ✅ built-in | ❌ separate tools |
| Threaded port scanner + banner grab | ✅ built-in | ❌ |
| Web beast mode (dir fuzz, header audit, WAF detect, fingerprint) | ✅ built-in | ❌ |
| Exploit checks (SQLi / XSS / LFI / header injection) | ✅ built-in | ❌ |
| **Payload library exposed as an MCP tool** | ✅ **exclusive** | ❌ nobody has this |
| **AI brain embedded as an MCP tool** (`ai_analyze`) | ✅ **exclusive** | ❌ |
| **Paste-and-go AI API setup wizard** | ✅ **exclusive** | ❌ |
| Signature colored timestamps | ✅ | some |
| Interactive terminal cockpit (TUI) | ✅ **exclusive** | ❌ |
| One-command install + config at `~/.config/kaiju` | ✅ | ❌ |

We can't always be the fastest — so KAIJU ships with things **nobody else has**: the payload library as a tool, the embedded AI brain, the paste-and-go wizard, and the cockpit.

---

## 🚀 Installation

### Requirements
- Linux (Kali / Parrot / Ubuntu / Debian recommended)
- Python **3.10+**
- (Optional but recommended) `nmap`, `traceroute`

### Install from source

```bash
git clone https://github.com/Anonymous-beta/kaiju.git
cd kaiju
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
kaiju banner
```

### Zero-install launcher

```bash
pip install -r requirements.txt
python3 run.py            # splash + help
python3 run.py run        # fire up the MCP server
```

### Quick sanity check

```bash
kaiju banner              # the beast wakes up
kaiju tools               # list the full arsenal
kaiju config --ai         # paste your AI API key
kaiju run                 # start the MCP server (stdio)
```

---

## 🎯 Quick Start

```bash
# 1. Configure the AI (paste your key — done in ~30 seconds)
kaiju config --ai

# 2. Fire up the server (stdio for Claude Desktop / Cursor)
kaiju run

# 3. Or go interactive — the cockpit
kaiju tui
```

---

## 🤖 AI Configuration — paste & go

```bash
kaiju config --ai
```

The wizard asks for a **provider**, you **paste your API key**, it **tests the connection**, and done. KAIJU connects instantly.

**Supported out of the box:**

| Provider | Endpoint | Default model |
|---|---|---|
| OpenAI | `api.openai.com/v1` | `gpt-4o-mini` |
| OpenRouter | `openrouter.ai/api/v1` | `openai/gpt-4o-mini` |
| Groq | `api.groq.com/openai/v1` | `llama-3.3-70b-versatile` |
| Together | `api.together.xyz/v1` | `Llama-3.3-70B-Instruct-Turbo` |
| Mistral | `api.mistral.ai/v1` | `mistral-small-latest` |
| Ollama (local) | `localhost:11434/v1` | `llama3.1` |
| Custom | any OpenAI-compatible URL | anything |

> Local Ollama with no key works too — KAIJU is fully offline-capable.

---

## 🔌 Connecting MCP Clients

### Claude Desktop

Edit `~/.config/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "kaiju": {
      "command": "kaiju",
      "args": ["run"]
    }
  }
}
```

### Cursor / IDE agents

```json
{
  "mcpServers": {
    "kaiju": {
      "command": "kaiju",
      "args": ["run"]
    }
  }
}
```

### Custom client over SSE

```bash
kaiju run --transport sse --host 127.0.0.1 --port 8765
```

Then point your client at `http://127.0.0.1:8765/sse`.

---

## 🛠️ The Arsenal

### `recon` — know your enemy
| Tool | What it does |
|---|---|
| `dns_lookup` | A / AAAA / MX / TXT / NS / CNAME / SOA / PTR |
| `subdomain_enum` | 200+ word built-in list, threaded, custom wordlist support |
| `whois_lookup` | registrar, dates, nameservers, contacts |
| `osint_lookup` | WHOIS + DNS + IP + DMARC + PTR snapshot |
| `reverse_dns` | IP → hostname |
| `zone_transfer` | AXFR attempt against every nameserver |

### `network` — map the battlefield
| Tool | What it does |
|---|---|
| `ping_sweep` | ranges / CIDR / lists, threaded |
| `port_scan` | top-100 or custom ranges, banners, 200 threads |
| `traceroute` | network path |
| `http_probe` | status, size, title, server header |
| `nmap_scan` | full system-nmap wrapper |

### `web` — eat the web
| Tool | What it does |
|---|---|
| `dir_fuzz` | 100+ built-in paths, extensions, threaded |
| `header_audit` | finds the 8 critical headers you're missing |
| `waf_detect` | Cloudflare / Akamai / Imperva / AWS / F5 + payload probes |
| `tech_fingerprint` | server, CMS, framework, JS libs, version hints |

### `exploit` — the teeth
| Tool | What it does |
|---|---|
| `sqli_check` | time-delay + error-pattern + boolean-blind probes |
| `xss_check` | reflection sniffing with markers |
| `lfi_check` | traversal + `php://filter` + `/proc/self/environ` |
| `header_injection_check` | CRLF, CORS, Host-header |
| `payload_library` | **100+ payloads in 11 categories** — as an MCP tool |

### `system` — local power (safe by default)
| Tool | What it does |
|---|---|
| `command_exec` | shell commands, **safe_mode allowlist** by default |
| `file_read` | text files, 10MB cap, tree-restricted in safe_mode |
| `file_write` | write files, tree-restricted in safe_mode |
| `list_directory` | listing with sizes |

### `ai` — the brain
| Tool | What it does |
|---|---|
| `ai_analyze` | paste tool output → AI explains findings + next attack steps |

---

## 💣 The Payload Library

11 categories, 100+ payloads, browsable via the `payload_library` MCP tool:

```
sqli, xss, lfi, rce, ssrf, idor, auth, headers,
deserialization, upload, crypto, misc
```

Example (as an MCP call):

```
payload_library("ssrf")
```

```text
[ssrf]
  • Localhost: http://127.0.0.1/
  • Localhost hex: http://0x7f000001/
  • IPv6 loopback: http://[::1]/
  • AWS metadata: http://169.254.169.254/latest/meta-data/
  • gopher: gopher://127.0.0.1:6379/_INFO
  • dict: dict://127.0.0.1:11211/info
  ...
```

---

## 🛡️ Safe Mode

KAIJU ships with `safe_mode: true`:

- `command_exec` only runs **allowlisted binaries** (`nmap`, `curl`, `dig`, …)
- interpreted shells (`bash -c`, `python3 -c`) are blocked
- `file_read` / `file_write` restricted to the working tree
- exploit checks are **non-invasive probes** (single benign request)

Run KAIJU on a box you own and disable it when you're ready to go full monster:

```bash
kaiju config --set 'safe_mode false'
```

---

## 🕹️ CLI Reference

```bash
kaiju                      # splash + help
kaiju run                  # MCP server (stdio)
kaiju run --transport sse --host 127.0.0.1 --port 8765
kaiju config --ai          # paste-and-go AI wizard
kaiju config --show        # dump config JSON
kaiju config --set 'ai.model gpt-4o'
kaiju config --reset
kaiju tools                # arsenal table
kaiju ai "how do I test for SSRF here?"
kaiju tui                  # interactive cockpit
kaiju banner
kaiju --version
```

---

## 🗂️ Project Structure

```
kaiju/
├── run.py                     # zero-install launcher
├── setup.py / pyproject.toml  # packaging
├── kaiju/
│   ├── banner.py              # the Kaiju splash
│   ├── timestamps.py          # signature timestamps
│   ├── config.py              # XDG config + providers
│   ├── ai.py                  # OpenAI-compatible AI client
│   ├── server.py              # MCP server core
│   ├── cli.py                 # CLI entry
│   ├── tools/                 # the arsenal
│   │   ├── recon.py  network.py  web.py  exploit.py  system.py
│   └── ui/tui.py              # interactive cockpit
```

---

## 📜 License

MIT — Copyright © 2026 **Anonymous-beta**.

---

## 🙏 The Vow

> *"If we can't make it better than the others, we make it have something the others don't have."*

KAIJU has four things nobody else ships:
1. **The payload library as an MCP tool**
2. **The embedded AI brain** (`ai_analyze`)
3. **The paste-and-go AI wizard**
4. **The terminal cockpit**

Now go wake the Kaiju. 🦖
