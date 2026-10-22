"""SSRF Protection and Robots.txt validation module."""

import ipaddress
import socket
from urllib.parse import urlparse
import httpx
from urllib.robotparser import RobotFileParser
from a11y_agent.core.exceptions import SSRFSecurityError
from a11y_agent.core.config import settings

def is_ip_allowed(ip_str: str) -> bool:
    """
    Check if an IP address is a safe public IP (not loopback, private, link-local, multicast, or reserved).
    """
    try:
        ip = ipaddress.ip_address(ip_str)
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        ):
            return False
        return True
    except ValueError:
        return False


def validate_url_security(url: str, allow_private_ips: bool = False) -> str:
    """
    Validate that the URL is strictly http/https and does not resolve to private/internal networks.
    Returns the sanitized URL if valid, raises SSRFSecurityError otherwise.
    """
    if not url or not isinstance(url, str):
        raise SSRFSecurityError("URL no válida o vacía.")

    parsed = urlparse(url.strip())
    if parsed.scheme not in ("http", "https"):
        raise SSRFSecurityError(f"Esquema no permitido '{parsed.scheme}'. Solo se admite http y https.")

    hostname = parsed.hostname
    if not hostname:
        raise SSRFSecurityError("La URL no contiene un nombre de host válido.")

    # Disallow known localhost aliases directly
    lower_host = hostname.lower()
    if lower_host in ("localhost", "127.0.0.1", "::1", "0.0.0.0", "local"):
        if not allow_private_ips:
            raise SSRFSecurityError(f"Acceso denegado a host local: {hostname}")

    # DNS Resolution check to prevent SSRF and DNS rebinding
    try:
        # Resolve all IPv4 and IPv6 addresses for the host
        addr_info = socket.getaddrinfo(hostname, parsed.port or (443 if parsed.scheme == "https" else 80), proto=socket.IPPROTO_TCP)
        resolved_ips = {item[4][0] for item in addr_info}
    except socket.gaierror as e:
        raise SSRFSecurityError(f"No se pudo resolver el nombre de dominio '{hostname}': {e}")

    if not resolved_ips:
        raise SSRFSecurityError(f"No se encontraron direcciones IP para el host '{hostname}'.")

    if not allow_private_ips:
        for ip in resolved_ips:
            if not is_ip_allowed(ip):
                raise SSRFSecurityError(
                    f"Riesgo de seguridad SSRF: El host '{hostname}' resuelve a una IP interna/privada ({ip})."
                )

    return url.strip()


async def check_robots_txt_allowed(url: str, user_agent: str = settings.user_agent) -> bool:
    """
    Check if the target URL is allowed by the site's robots.txt.
    Returns True if allowed or if robots.txt is unreachable/404.
    """
    if not settings.respect_robots_txt:
        return True

    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    try:
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
            resp = await client.get(robots_url, headers={"User-Agent": user_agent})
            if resp.status_code == 200:
                rp = RobotFileParser()
                rp.parse(resp.text.splitlines())
                return rp.can_fetch(user_agent, url)
            # If 404 or other 4xx/5xx status, crawl is generally permitted
            return True
    except Exception:
        # If robots.txt cannot be reached, permit crawl gracefully
        return True
