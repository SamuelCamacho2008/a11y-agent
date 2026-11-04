"""Test verification for sandboxed iframe permissions, axe-core execution, CORS fallback, content validation, and relative paths."""

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
        assert 'style="display: none;"' not in content or 'audit-sandbox" style="display: none;"' not in content

def test_dynamic_iframe_creation_sets_sandbox_before_append():
    """Verify createAuditSandboxIframe sets sandbox attributes before attaching to DOM."""
    for html_file in [DOCS_DIR / "index.html", REPO_ROOT / "index.html"]:
        content = html_file.read_text(encoding="utf-8")
        assert "function createAuditSandboxIframe" in content
        
        set_attr_pos = content.find("iframe.setAttribute('sandbox', 'allow-scripts allow-same-origin allow-forms')")
        assert set_attr_pos != -1, "setAttribute sandbox missing"

def test_html_content_validation():
    """Verify content validation checks length > 500 chars and structural HTML tags."""
    for html_file in [DOCS_DIR / "index.html", REPO_ROOT / "index.html"]:
        content = html_file.read_text(encoding="utf-8")
        assert "function isValidHtmlContent" in content
        assert "trimmed.length < 500" in content
        assert "INVALID_HTML_CONTENT" in content

def test_axe_core_execution_with_onload_and_srcdoc():
    """Verify runAuditOnHtml uses srcdoc, attaches load listener to iframe, and runs on targetDoc."""
    for html_file in [DOCS_DIR / "index.html", REPO_ROOT / "index.html"]:
        content = html_file.read_text(encoding="utf-8")
        assert "iframe.srcdoc = htmlWithBase" in content
        assert "iframe.onload = finish" in content
        assert "iframe.addEventListener('load', finish)" in content
        assert "const targetDoc = iframe.contentDocument || iframe.contentWindow.document;" in content
        assert "window.axe.run(targetDoc," in content
        # Verify debug console logs
        assert "Nodos evaluados en el DOM:" in content
        assert "Muestra del body:" in content
        # Verify empty DOM detection
        assert "EMPTY_DOM_DETECTED" in content

def test_cors_fallback_proxies_pipeline():
    """Verify multi-proxy pipeline with encodeURIComponent, AllOrigins, Jina, CodeTabs."""
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
