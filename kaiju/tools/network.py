"""KAIJU network tools — ping, ports, traceroute, HTTP probes."""

from __future__ import annotations

import ipaddress
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional, Tuple

from kaiju.tools import Tool


def _parse_targets(target: str) -> List[str]:
    """Expand '10.0.0.1-5' or '10.0.0.0/28' or comma lists into IPs."""
    hosts: List[str] = []
    for part in target.replace(" ", "").split(","):
        if not part:
            continue
        if "-" in part and "/" not in part:
            base, _, end = part.rpartition("-")
            if not base or not end:
                hosts.append(part); continue
            try:
                start_ip = ipaddress.ip_address(base)
                end_ip = ipaddress.ip_address(f"{base.rsplit('.',1)[0]}.{end}")
            except ValueError:
                hosts.append(part); continue
            cur = int(start_ip)
            while cur <= int(end_ip):
                hosts.append(str(ipaddress.ip_address(cur)))
                cur += 1
        elif "/" in part:
            try:
                hosts.extend(str(i) for i in ipaddress.ip_network(part, strict=False).hosts())
            except ValueError:
                hosts.append(part)
        else:
            hosts.append(part)
    return hosts


def _resolve(host: str) -> Optional[str]:
    try:
        return socket.gethostbyname(host)
    except Exception:
        return None


def ping_sweep(targets: str, count: int = 2, timeout: float = 1.5) -> str:
    """Ping sweep with expansion support (ranges/CIDR/lists). Returns alive hosts."""
    hosts = _parse_targets(targets)
    out = [f"Ping sweep: {len(hosts)} hosts"]
    alive: List[str] = []

    def ping(host: str) -> Optional[str]:
        try:
            r = __import__("subprocess").run(
                ["ping", "-c", str(count), "-W", str(int(timeout)), host],
                capture_output=True, timeout=count * timeout + 3)
            if r.returncode == 0:
                return host
        except Exception:
            pass
        return None

    with ThreadPoolExecutor(max_workers=32) as ex:
        futs = [ex.submit(ping, h) for h in hosts]
        for f in as_completed(futs):
            r = f.result()
            if r:
                alive.append(r)

    alive.sort()
    out.append(f"  alive ({len(alive)}): {', '.join(alive) if alive else 'none'}")
    return "\n".join(out)


def port_scan(target: str, ports: str = "1-1000", timeout: float = 1.0) -> str:
    """TCP connect scan. Ports: '80', '22,80,443', '1-1024' or 'top100'."""
    ip = _resolve(target) or target
    out = [f"Port scan: {target} ({ip})"]

    port_list: List[int] = []
    if ports.lower() == "top100":
        top = [22,80,443,21,25,53,110,143,389,445,3306,3389,5432,6379,27017,
               8080,8443,8000,8888,9000,9200,11211,5900,1433,1521,2049,2375,
               3000,4000,5000,5601,7001,7474,8009,8500,9001,9092,10000,11211,
               111,135,139,161,179,587,993,995,1080,1194,1434,1723,2222,2483,
               2484,3060,3268,3306,4444,4786,5060,5061,5222,5223,5432,5555,
               5800,5900,5984,5985,6379,6443,7000,7001,7002,7443,7474,8000,
               8008,8009,8080,8081,8082,8083,8084,8085,8086,8087,8088,8089,
               8090,8181,8443,8880,8888,9000,9001,9002,9003,9004,9005,9006,
               9007,9008,9009,9010,9042,9050,9090,9091,9092,9200,9300,9443,
               10000,10001,11211,15672,27017,27018,28017]
        port_list = sorted(set(top))
    else:
        for p in ports.replace(" ", "").split(","):
            if not p:
                continue
            if "-" in p:
                a, b = p.split("-", 1)
                port_list.extend(range(int(a), int(b) + 1))
            else:
                port_list.append(int(p))
    port_list = sorted(set(p for p in port_list if 0 < p < 65536))

    open_ports: List[Tuple[int, str]] = []

    def probe(p: int) -> Optional[Tuple[int, str]]:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(timeout)
                if s.connect_ex((ip, p)) == 0:
                    svc = ""
                    try:
                        s.settimeout(2.0)
                        banner = s.recv(128).decode(errors="ignore").strip()
                        svc = banner[:60] if banner else ""
                    except Exception:
                        pass
                    return (p, svc)
        except Exception:
            pass
        return None

    with ThreadPoolExecutor(max_workers=200) as ex:
        futs = [ex.submit(probe, p) for p in port_list]
        for f in as_completed(futs):
            r = f.result()
            if r:
                open_ports.append(r)

    open_ports.sort()
    if not open_ports:
        out.append("  no open ports found")
    for p, banner in open_ports:
        out.append(f"  [+] {p:>5}/tcp  open" + (f"  [{banner}]" if banner else ""))
    return "\n".join(out)


def traceroute(target: str, max_hops: int = 30) -> str:
    """UDP-based traceroute (falls back to ICMP via ping -T where available)."""
    ip = _resolve(target) or target
    try:
        import subprocess
        r = subprocess.run(["traceroute", "-n", "-m", str(max_hops), ip],
                           capture_output=True, timeout=120)
        if r.returncode == 0:
            return r.stdout.decode(errors="ignore")
        return f"ERROR: traceroute failed:\n{r.stderr.decode(errors='ignore')}"
    except FileNotFoundError:
        return "ERROR: 'traceroute' not installed — apt install traceroute"
    except Exception as e:
        return f"ERROR: {e}"


def http_probe(urls: str, timeout: float = 8.0) -> str:
    """HTTP(S) probe of a comma-separated URL list — status, size, title, server."""
    import requests, urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    out = []
    for u in urls.split(","):
        u = u.strip()
        if not u:
            continue
        if not u.startswith(("http://", "https://")):
            u = "http://" + u
        try:
            r = requests.get(u, timeout=timeout, verify=False,
                             headers={"User-Agent": "Mozilla/5.0 KAIJU/1.0"},
                             allow_redirects=True)
            title = ""
            try:
                from bs4 import BeautifulSoup
                title = BeautifulSoup(r.text[:200000], "html.parser").title
                title = title.string.strip()[:60] if title and title.string else ""
            except Exception:
                pass
            out.append(f"  {u} → {r.status_code} ({len(r.content)}B)"
                       + (f" server={r.headers.get('Server')}" if r.headers.get("Server") else "")
                       + (f" title={title!r}" if title else ""))
        except Exception as e:
            out.append(f"  {u} → ERROR {e}")
    return "HTTP probe:\n" + "\n".join(out)


def nmap_scan(target: str, args: str = "-sV") -> str:
    """Wrap nmap (must be installed). Example args: -sV, -A, -sC -sV -p-"""
    import subprocess
    cmd = ["nmap", *args.split(), target]
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=600)
        if r.returncode in (0, 1):
            return r.stdout.decode(errors="ignore")
        return f"ERROR: nmap returned {r.returncode}:\n{r.stderr.decode(errors='ignore')}"
    except FileNotFoundError:
        return "ERROR: nmap not installed — apt install nmap"
    except Exception as e:
        return f"ERROR: {e}"


TOOLS = [
    Tool("ping_sweep", "Ping sweep with CIDR/range/list expansion", ping_sweep, "network"),
    Tool("port_scan", "Fast threaded TCP connect scan with banner grab", port_scan, "network"),
    Tool("traceroute", "Network path tracing to a target", traceroute, "network"),
    Tool("http_probe", "Probe HTTP(s) URLs: status, size, title, server header", http_probe, "network"),
    Tool("nmap_scan", "Full nmap wrapper (system nmap required)", nmap_scan, "network"),
      ]
