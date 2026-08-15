"""KAIJU web tools — dir fuzz, headers audit, WAF detect, tech fingerprint."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional

import requests
from bs4 import BeautifulSoup

from kaiju.tools import Tool

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) KAIJU/1.0"}

COMMON_PATHS = [
    "robots.txt", "sitemap.xml", "admin", "login", "wp-admin", "wp-login.php",
    ".git/config", ".env", "config.php", "phpinfo.php", "backup.zip",
    "backup.sql", "db.sql", "dump.sql", ".htaccess", "server-status",
    "api", "api/v1", "graphql", "swagger", "swagger-ui.html", "api-docs",
    "v2/api-docs", "actuator", "actuator/env", "actuator/health", ".well-known",
    "crossdomain.xml", "README.md", "README", "LICENSE", "CHANGELOG", "VERSION",
    "test", "tests", "debug", "dev", "old", "new", "backup", "bak", "tmp",
    "temp", "uploads", "upload", "downloads", "files", "static", "assets",
    "js", "css", "img", "images", "fonts", "vendor", "node_modules",
    "phpmyadmin", "pma", "adminer", "console", "shell", "cmd", "webadmin",
    "manager", "status", "health", "info", "info.php", "status.php",
    "index.php.bak", "index.php~", ".DS_Store", ".bash_history",
    "config.json", "config.yml", "config.yaml", "settings.php",
    "web.config", "application.properties", "package.json", "composer.json",
]


def _session():
    s = requests.Session()
    s.headers.update(UA)
    s.verify = False
    import urllib3
    urllib3.disable_warnings()
    return s


def dir_fuzz(base_url: str, wordlist: Optional[str] = None,
             extensions: str = "php,txt,bak,sql,json", threads: int = 30,
             timeout: float = 6.0) -> str:
    """Brute-force directories/files on a web root. Custom wordlist or built-in."""
    import os
    base = base_url.rstrip("/")
    if not base.startswith(("http://", "https://")):
        base = "http://" + base

    if wordlist:
        try:
            words = [l.strip() for l in open(wordlist, encoding="utf-8", errors="ignore")
                     if l.strip() and not l.startswith("#")]
        except OSError as e:
            return f"ERROR: cannot read wordlist: {e}"
    else:
        words = COMMON_PATHS
        if extensions.strip():
            bare = [w for w in words if not w.endswith((".php", ".txt", ".html"))]
            for w in list(bare):
                for ext in extensions.replace(" ", "").split(","):
                    words.append(f"{w}.{ext}")

    s = _session()
    found: List[str] = []

    def probe(path: str) -> Optional[str]:
        url = f"{base}/{path}"
        try:
            r = s.get(url, timeout=timeout, allow_redirects=False)
            if r.status_code in (200, 204, 301, 302, 307, 308, 401, 403):
                size = len(r.content)
                loc = r.headers.get("Location", "")
                return f"  [{r.status_code}] /{path} ({size}B)" + (f" → {loc}" if loc else "")
        except Exception:
            pass
        return None

    with ThreadPoolExecutor(max_workers=threads) as ex:
        futs = [ex.submit(probe, w) for w in dict.fromkeys(words)]
        for f in as_completed(futs):
            r = f.result()
            if r:
                found.append(r)

    found.sort()
    return (f"Dir fuzz: {base} ({len(dict.fromkeys(words))} paths, {len(found)} hits)\n"
            + "\n".join(found) if found else f"Dir fuzz: {base} — no hits")


def header_audit(url: str) -> str:
    """Check security headers — find the ones the target is missing."""
    u = url if url.startswith(("http://", "https://")) else "http://" + url
    s = _session()
    try:
        r = s.get(u, timeout=10)
    except Exception as e:
        return f"ERROR: {e}"
    h = {k.lower(): v for k, v in r.headers.items()}

    checks = {
        "strict-transport-security": "HSTS",
        "content-security-policy": "CSP",
        "x-content-type-options": "X-Content-Type-Options",
        "x-frame-options": "X-Frame-Options",
        "referrer-policy": "Referrer-Policy",
        "permissions-policy": "Permissions-Policy",
        "x-xss-protection": "X-XSS-Protection",
        "cache-control": "Cache-Control",
    }
    out = [f"Header audit: {u} ({r.status_code})"]
    missing = []
    for k, label in checks.items():
        if k in h:
            out.append(f"  [+] {label}: {h[k][:100]}")
        else:
            missing.append(label)
            out.append(f"  [-] {label}: MISSING")
    server = h.get("server") or h.get("via")
    if server:
        out.append(f"  [i] Server: {server}")
    out.append(f"  summary: {len(checks) - len(missing)}/{len(checks)} present, "
               f"missing: {', '.join(missing) or 'none'}")
    return "\n".join(out)


def waf_detect(url: str) -> str:
    """Probe for WAF presence using signature payloads and headers."""
    u = url if url.startswith(("http://", "https://")) else "http://" + url
    s = _session()
    out = [f"WAF detection: {u}"]
    payloads = [
        ("sqli", "/?id=1' OR '1'='1"),
        ("xss", "/?q=<script>alert(1)</script>"),
        ("path", "/..%2f..%2fetc%2fpasswd"),
        ("rce", "/?cmd=;id"),
    ]
    waf_signals = {
        "cloudflare": ["cf-ray", "cloudflare"],
        "akamai": ["akamai", "akamai-"],
        "imperva": ["incapsula", "x-iinfo"],
        "sucuri": ["sucuri"],
        "f5": ["bigip", "f5"],
        "aws waf": ["x-amz-cf-id", "awswaf"],
        "modsecurity": ["mod_security", "modsecurity"],
        "barracuda": ["barracuda"],
        "fastly": ["fastly"],
        "citrix": ["citrix", "ns-"],
    }
    detected = set()
    try:
        r0 = s.get(u, timeout=10)
        for name, sigs in waf_signals.items():
            for sig in sigs:
                if sig.lower() in str(r0.headers).lower():
                    detected.add(name)
    except Exception as e:
        return f"ERROR: {e}"

    for label, path in payloads:
        try:
            r = s.get(u + path, timeout=10)
            if r.status_code in (403, 406, 429, 500, 501):
                body = r.text[:3000].lower()
                if any(x in body for x in ("blocked", "attack", "suspicious",
                                           "malicious", "waf", "security", "denied")):
                    detected.add(f"blocker@/{label}")
        except Exception:
            pass

    if detected:
        out.append("  [+] WAF detected:")
        for d in sorted(detected):
            out.append(f"      • {d}")
    else:
        out.append("  [-] No obvious WAF signatures (may still have one — verify manually)")
    return "\n".join(out)


def tech_fingerprint(url: str) -> str:
    """Fingerprint server, framework, CMS, analytics, and exposed technologies."""
    u = url if url.startswith(("http://", "https://")) else "http://" + url
    s = _session()
    try:
        r = s.get(u, timeout=10)
    except Exception as e:
        return f"ERROR: {e}"
    out = [f"Tech fingerprint: {u} ({r.status_code})"]
    body = r.text[:500000].lower()
    headers = str(r.headers).lower()

    techs = {
        "nginx": ["nginx"], "apache": ["apache"], "iis": ["microsoft-iis"],
        "cloudflare": ["cloudflare", "cf-ray"],
        "wordpress": ["wp-content", "wp-includes", "wp-json"],
        "joomla": ["joomla", "com_content"], "drupal": ["drupal"],
        "laravel": ["laravel", "x-laravel"], "django": ["csrftoken", "django"],
        "flask": ["flask", "werkzeug"], "rails": ["rails", "x-powered-by: phusion"],
        "express": ["x-powered-by: express"],
        "react": ["__react", "reactjs"], "vue": ["__vue__", "vue.js"],
        "angular": ["ng-version", "angular"],
        "jquery": ["jquery"], "bootstrap": ["bootstrap"],
        "php": ["php", "x-powered-by: php"], "asp.net": ["asp.net", "viewstate"],
        "java": ["jsessionid", "java"], "tomcat": ["tomcat"], "jetty": ["jetty"],
        "elasticsearch": ["elasticsearch"], "grafana": ["grafana"],
        "jenkins": ["jenkins"], "gitlab": ["gitlab"], "kibana": ["kibana"],
    }
    hits = [name for name, sigs in techs.items() if any(x in headers or x in body for x in sigs)]
    for t in sorted(hits):
        out.append(f"  [+] {t}")

    # version hints
    for pat, label in [("wp-content/themes/([^/]+)", "theme"),
                       ("wp-content/plugins/([^/]+)", "plugin"),
                       ("generator[^>]*content=\"([^\"]+)\"", "generator"),
                       ("x-powered-by: ([^\r\n]+)", "x-powered-by")]:
        import re
        m = re.search(pat, r.text, re.I)
        if m:
            out.append(f"  [i] {label}: {m.group(1)[:60]}")

    if len(hits) == 0:
        out.append("  [-] no known signatures — check manually")
    return "\n".join(out)


TOOLS = [
    Tool("dir_fuzz", "Brute-force web paths (built-in wordlist or custom file)", dir_fuzz, "web"),
    Tool("header_audit", "Security headers audit — spot the missing ones", header_audit, "web"),
    Tool("waf_detect", "WAF fingerprinting with signature payloads", waf_detect, "web"),
    Tool("tech_fingerprint", "Detect server, CMS, framework and JS libraries", tech_fingerprint, "web"),
  ]
