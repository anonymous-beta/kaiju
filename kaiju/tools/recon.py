"""KAIJU recon tools — DNS, subdomains, WHOIS, OSINT, zone transfers."""

from __future__ import annotations

import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional

from kaiju.tools import Tool

# ── helpers ──────────────────────────────────────────────

def _need(pkg: str, hint: str = "") -> str:
    return f"ERROR: missing dependency '{pkg}'. {hint}"


def _resolver():
    try:
        import dns.resolver
    except ImportError:
        return None
    r = dns.resolver.Resolver(configure=True)
    r.timeout = 4
    r.lifetime = 6
    return r


COMMON_SUBDOMAINS = [
    "www", "mail", "remote", "blog", "webmail", "server", "ns1", "ns2",
    "smtp", "secure", "vpn", "m", "shop", "ftp", "api", "dev", "test",
    "staging", "demo", "admin", "portal", "login", "auth", "cdn", "static",
    "assets", "img", "images", "media", "download", "docs", "support",
    "help", "status", "app", "apps", "mobile", "old", "new", "beta", "alpha",
    "prod", "production", "git", "gitlab", "jenkins", "ci", "jira",
    "confluence", "wiki", "forums", "forum", "community", "news", "info",
    "intranet", "internal", "office", "owa", "exchange", "web", "web2",
    "www2", "dev2", "test2", "stg", "stage", "pre", "preprod", "qa", "qc",
    "sandbox", "lab", "labs", "db", "mysql", "db1", "db2", "redis", "mongo",
    "mongodb", "elastic", "es", "kibana", "grafana", "prometheus", "monitor",
    "monitoring", "metrics", "logs", "log", "splunk", "kafka", "rabbitmq",
    "mq", "queue", "storage", "files", "file", "upload", "uploads", "cloud",
    "s3", "bucket", "backup", "backups", "bak", "archive", "cache", "cms",
    "crm", "erp", "pay", "payments", "billing", "invoice", "account",
    "accounts", "signup", "signin", "register", "panel", "cpanel", "whm",
    "mx", "pop", "imap", "mail2", "relay", "spam", "proxy", "gateway", "gw",
    "edge", "waf", "firewall", "bastion", "jump", "puppet", "ansible", "k8s",
    "kubernetes", "cluster", "node", "node1", "node2", "docker", "registry",
    "nexus", "artifactory", "repo", "repos", "svn", "bitbucket", "github",
    "code", "devops", "ops", "sre", "alert", "alerts", "sms", "email",
    "emails", "marketing", "ads", "analytics", "stats", "report", "reports",
    "data", "api2", "apiv1", "apiv2", "v1", "v2", "graphql", "ws", "wss",
    "socket", "chat", "im", "voice", "video", "stream", "live", "player",
    "store", "cart", "checkout", "wallet", "crypto", "btc", "eth",
]

# ── DNS ──────────────────────────────────────────────────

def dns_lookup(domain: str, record_type: str = "A") -> str:
    """Resolve DNS records (A, AAAA, MX, TXT, NS, CNAME, SOA, PTR) for a domain."""
    res = _resolver()
    if res is None:
        return _need("dnspython", "pip install dnspython")
    rt = record_type.upper()
    try:
        answers = res.resolve(domain, rt)
        return f"{domain} {rt}:\n" + "\n".join(f"  {a}" for a in answers)
    except Exception as e:
        return f"{domain} {rt}: {e}"


def subdomain_enum(domain: str, wordlist: Optional[str] = None) -> str:
    """Threaded subdomain brute-force via DNS. Optional custom wordlist file."""
    res = _resolver()
    if res is None:
        return _need("dnspython", "pip install dnspython")

    if wordlist:
        try:
            names = [l.strip() for l in open(wordlist, encoding="utf-8", errors="ignore") if l.strip()]
        except OSError as e:
            return f"ERROR: cannot read wordlist '{wordlist}': {e}"
    else:
        names = COMMON_SUBDOMAINS

    found: List[str] = []

    def probe(name: str) -> Optional[str]:
        fqdn = f"{name}.{domain}"
        try:
            answers = res.resolve(fqdn, "A")
            ips = sorted({str(a) for a in answers})
            return f"  [+] {fqdn} → {', '.join(ips)}"
        except Exception:
            return None

    with ThreadPoolExecutor(max_workers=64) as ex:
        futs = [ex.submit(probe, n) for n in names]
        for fut in as_completed(futs):
            r = fut.result()
            if r:
                found.append(r)

    found.sort()
    head = f"Subdomain enumeration: {domain} ({len(names)} names, {len(found)} alive)"
    return head + "\n" + ("\n".join(found) if found else "  (nothing — try a bigger wordlist)")


def whois_lookup(domain: str) -> str:
    """WHOIS record for a domain: registrar, dates, nameservers, contacts."""
    try:
        import whois
    except ImportError:
        return _need("python-whois", "pip install python-whois")
    try:
        return str(whois.whois(domain))
    except Exception as e:
        return f"ERROR: whois failed: {e}"


def osint_lookup(target: str) -> str:
    """Combined WHOIS + DNS + IP OSINT snapshot."""
    host = target.split("//")[-1].split("/")[0].split(":")[0]
    res = _resolver()
    parts = [f"OSINT snapshot: {host}", "─" * 50]

    try:
        import whois
        w = whois.whois(host)
        for k, label in (("registrar", "registrar"), ("creation_date", "created"),
                         ("updated_date", "updated"), ("expiration_date", "expires")):
            v = w.get(k)
            parts.append(f"[whois] {label}: {v}" if v else "")
    except Exception as e:
        parts.append(f"[whois] {e}")

    if res:
        for rt in ("MX", "NS", "TXT"):
            try:
                answers = [str(a) for a in res.resolve(host, rt)]
                parts.append(f"[dns {rt}] {', '.join(answers[:6])}")
            except Exception:
                pass
        try:
            for a in res.resolve(f"_dmarc.{host}", "TXT"):
                parts.append(f"[dns dmarc] {a}")
        except Exception:
            pass

    try:
        ip = socket.gethostbyname(host)
        parts.append(f"[ip] {host} → {ip}")
        try:
            ptr = socket.gethostbyaddr(ip)[0]
            parts.append(f"[ptr] {ip} → {ptr}")
        except Exception:
            pass
    except Exception as e:
        parts.append(f"[ip] {e}")

    return "\n".join(p for p in parts if p)


def reverse_dns(ip: str) -> str:
    """PTR lookup for an IP address."""
    try:
        host, aliases, _ = socket.gethostbyaddr(ip)
        return f"{ip} → {host} (aliases: {', '.join(aliases) or 'none'})"
    except Exception as e:
        return f"{ip}: {e}"


def zone_transfer(domain: str) -> str:
    """Attempt a DNS zone transfer (AXFR) against every nameserver."""
    res = _resolver()
    if res is None:
        return _need("dnspython", "pip install dnspython")
    try:
        import dns.query, dns.zone
    except ImportError:
        return _need("dnspython")
    try:
        ns_answers = res.resolve(domain, "NS")
    except
