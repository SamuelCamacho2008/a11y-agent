"""Unit tests for Phase 1: Security, SSRF validation, and Crawler components."""

import pytest
from a11y_agent.core.security import is_ip_allowed, validate_url_security
from a11y_agent.core.exceptions import SSRFSecurityError
from a11y_agent.crawler.detector import detect_technologies

def test_ip_filtering():
    """Verify that private, loopback and reserved IPs are rejected."""
    # Forbidden IPs
    assert not is_ip_allowed("127.0.0.1")
    assert not is_ip_allowed("10.0.0.1")
    assert not is_ip_allowed("172.16.5.4")
    assert not is_ip_allowed("192.168.1.1")
    assert not is_ip_allowed("169.254.169.254")
    assert not is_ip_allowed("::1")
    assert not is_ip_allowed("0.0.0.0")

    # Allowed public IPs
    assert is_ip_allowed("8.8.8.8")
    assert is_ip_allowed("1.1.1.1")
    assert is_ip_allowed("93.184.216.34")

def test_validate_url_security_schemes():
    """Verify scheme restrictions."""
    with pytest.raises(SSRFSecurityError, match="Esquema no permitido"):
        validate_url_security("ftp://example.com")

    with pytest.raises(SSRFSecurityError, match="Esquema no permitido"):
        validate_url_security("file:///etc/passwd")

    with pytest.raises(SSRFSecurityError, match="Esquema no permitido"):
        validate_url_security("gopher://example.com")

def test_validate_url_security_localhost_blocked():
    """Verify localhost is strictly blocked."""
    with pytest.raises(SSRFSecurityError, match="host local"):
        validate_url_security("http://localhost:8000/test")

    with pytest.raises(SSRFSecurityError, match="host local"):
        validate_url_security("http://127.0.0.1:3000")

def test_detect_technologies():
    """Verify technology stack detection from DOM markup."""
    sample_html = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <title>Test Page</title>
        <meta name="generator" content="WordPress 6.4">
    </head>
    <body class="bg-gray-100 flex flex-col">
        <div id="__next">
            <div data-reactroot="">
                <button role="button" aria-expanded="false" class="p-4">Menú</button>
                <svg width="24" height="24"></svg>
            </div>
        </div>
    </body>
    </html>
    """
    techs = detect_technologies(sample_html)
    assert "React" in techs
    assert "Next.js" in techs
    assert "WordPress 6.4" in techs
    assert "WAI-ARIA" in techs
    assert "SVG" in techs
    assert "Tailwind CSS" in techs
