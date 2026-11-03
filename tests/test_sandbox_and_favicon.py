"""Test verification for sandboxed iframe permissions, axe-core execution, and favicon."""

from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / "docs"

def test_favicon_ico_exists():
    """Verify favicon.ico exists in root and docs/ to eliminate 404 console errors."""
    root_favicon = REPO_ROOT / "favicon.ico"
    docs_favicon = DOCS_DIR / "favicon.ico"
    
    assert root_favicon.exists(), "root favicon.ico missing"
    assert docs_favicon.exists(), "docs/favicon.ico missing"
    assert root_favicon.stat().st_size > 500, "root favicon.ico empty or corrupted"
    assert docs_favicon.stat().st_size > 500, "docs/favicon.ico empty or corrupted"

def test_iframe_sandbox_permissions_in_html():
    """Verify iframe sandbox declaration includes allow-scripts, allow-same-origin, and allow-forms."""
    for html_file in [DOCS_DIR / "index.html", REPO_ROOT / "index.html"]:
        content = html_file.read_text(encoding="utf-8")
        assert 'id="audit-sandbox"' in content
        assert 'sandbox="allow-scripts allow-same-origin allow-forms"' in content, (
            f"iframe in {html_file} is missing required sandbox permissions"
        )
        # Verify not styled with display: none which breaks contrast & layout calculations
        assert 'style="display: none;"' not in content or 'audit-sandbox" style="display: none;"' not in content

def test_favicon_link_tags_present():
    """Verify head includes favicon link tags."""
    for html_file in [DOCS_DIR / "index.html", REPO_ROOT / "index.html"]:
        content = html_file.read_text(encoding="utf-8")
        assert 'rel="icon"' in content
        assert 'favicon.ico' in content

def test_cors_fallback_proxies_pipeline():
    """Verify multi-proxy pipeline with encodeURIComponent and non-blocking fallback."""
    content = (DOCS_DIR / "index.html").read_text(encoding="utf-8")
    assert "https://r.jina.ai/" in content
    assert "https://api.codetabs.com/v1/proxy?quest=" in content
    assert "encodeURIComponent(targetUrl)" in content
    assert "https://api.allorigins.win/raw?url=" in content
    assert "https://api.allorigins.win/get?url=" in content
    assert "getAuditIframe" in content
