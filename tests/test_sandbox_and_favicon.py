"""Test verification for sandboxed iframe permissions, axe-core execution, CORS fallback, and relative paths."""

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

def test_dynamic_iframe_creation_sets_sandbox_before_append():
    """Verify createAuditSandboxIframe sets sandbox attributes before attaching to DOM."""
    for html_file in [DOCS_DIR / "index.html", REPO_ROOT / "index.html"]:
        content = html_file.read_text(encoding="utf-8")
        assert "function createAuditSandboxIframe" in content
        
        # Verify setAttribute sandbox is before document.body.appendChild
        set_attr_pos = content.find("iframe.setAttribute('sandbox', 'allow-scripts allow-same-origin allow-forms')")
        append_pos = content.find("document.body.appendChild(iframe)")
        assert set_attr_pos != -1, "setAttribute sandbox missing"
        assert append_pos != -1, "appendChild missing"
        assert set_attr_pos < append_pos, "sandbox attribute MUST be set BEFORE appending iframe to DOM"

def test_axe_core_execution_with_onload():
    """Verify runAuditOnHtml attaches onload listener to iframe before executing axe.run."""
    for html_file in [DOCS_DIR / "index.html", REPO_ROOT / "index.html"]:
        content = html_file.read_text(encoding="utf-8")
        assert "iframe.onload = finish" in content or "iframe.onload = onLoaded" in content
        assert "axeResults = await axeEngine.run" in content or "axeResults = await window.axe.run" in content

def test_cors_fallback_proxies_pipeline():
    """Verify multi-proxy pipeline with encodeURIComponent, AllOrigins, and non-blocking fallback."""
    for html_file in [DOCS_DIR / "index.html", REPO_ROOT / "index.html"]:
        content = html_file.read_text(encoding="utf-8")
        assert "fetchHtmlWithCorsFallback" in content
        assert "https://api.allorigins.win/get?url=" in content
        assert "encodeURIComponent(targetUrl)" in content
        assert "https://r.jina.ai/" in content
        assert "https://api.codetabs.com/v1/proxy?quest=" in content

def test_relative_paths_for_github_pages_subpath():
    """Verify relative paths are used for local assets and scripts."""
    for html_file in [DOCS_DIR / "index.html", REPO_ROOT / "index.html"]:
        content = html_file.read_text(encoding="utf-8")
        assert 'href="./favicon.ico"' in content
        assert 'src="./config.js?v=1.2.0"' in content
        assert not ('href="/favicon.ico"' in content)
        assert not ('src="/config.js"' in content)
