"""Unit and regression tests for Phase 1E: Parity between Local and GitHub Pages."""

import json
import re
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / "docs"

def test_nojekyll_files_exist():
    """Verify that .nojekyll exists both in root and docs/ to prevent GitHub Pages Jekyll processing."""
    assert (REPO_ROOT / ".nojekyll").exists(), "Root .nojekyll missing"
    assert (DOCS_DIR / ".nojekyll").exists(), "docs/.nojekyll missing"

def test_config_js_exists_and_configured():
    """Verify that config.js exists in root and docs/ with valid structure."""
    for cfg_path in [REPO_ROOT / "config.js", DOCS_DIR / "config.js"]:
        assert cfg_path.exists(), f"Configuration file {cfg_path} missing"
        content = cfg_path.read_text(encoding="utf-8")
        assert "window.A11Y_CONFIG" in content
        assert "apiEndpoint" in content
        assert "backendTimeoutMs: 120000" in content
        assert "enableClientFallback" in content
        assert "isProduction" in content

def test_render_backend_configuration_matches_frontend():
    """Keep the Render API service and both frontend configs aligned."""
    render_config = (REPO_ROOT / "render.yaml").read_text(encoding="utf-8")
    expected_endpoint = "https://a11y-agent-api-samuelcamacho2008.onrender.com"

    assert "name: a11y-agent-api-samuelcamacho2008" in render_config
    assert "healthCheckPath: /api/health" in render_config
    for config_path in [REPO_ROOT / "config.js", DOCS_DIR / "config.js"]:
        assert expected_endpoint in config_path.read_text(encoding="utf-8")

def test_playwright_version_matches_docker_image():
    """Keep Playwright's Python package aligned with the bundled Chromium version."""
    dockerfile = (REPO_ROOT / "Dockerfile").read_text(encoding="utf-8")
    requirements = (REPO_ROOT / "requirements.txt").read_text(encoding="utf-8")

    image_match = re.search(r"playwright/python:v([0-9.]+)-jammy", dockerfile)
    package_match = re.search(r"^playwright==([0-9.]+)$", requirements, re.MULTILINE)

    assert image_match, "Playwright Docker image version is missing"
    assert package_match, "Playwright dependency must be pinned to an exact version"
    assert package_match.group(1) == image_match.group(1)

def test_subresource_integrity_and_config_in_html():
    """Verify docs/index.html and root index.html have SRI hashes and load config.js."""
    for html_file in [DOCS_DIR / "index.html", REPO_ROOT / "index.html"]:
        content = html_file.read_text(encoding="utf-8")
        
        # Verify SRI for axe-core
        assert 'integrity="sha384-uRREz/ppJZIpDhIttoybaVPSlxS7NFe1tCOkH3QVl+H3eM2aL90a140yzYKYh8TA"' in content, (
            f"axe-core SRI hash missing in {html_file}"
        )
        assert 'crossorigin="anonymous"' in content

        # Verify SRI for JSZip
        assert 'integrity="sha384-+mbV2IY1Zk/X1p/nWllGySJSUN8uMs+gUAN10Or95UBH0fpj6GfKgPmgC5EXieXG"' in content, (
            f"JSZip SRI hash missing in {html_file}"
        )

        # Verify config.js script load (relative path)
        assert 'config.js?v=1.2.2"' in content, f"config.js missing in {html_file}"

def test_no_insecure_mixed_content_http():
    """Verify no active mixed-content http:// resources are referenced in production index.html."""
    content = (DOCS_DIR / "index.html").read_text(encoding="utf-8")
    
    # Match script, img, link, iframe with http:// (not localhost)
    insecure_tags = re.findall(r'<(?:script|img|link|iframe)[^>]+(?:src|href)=["\']http://(?!localhost|127\.0\.0\.1)[^"\']+["\']', content, re.IGNORECASE)
    assert len(insecure_tags) == 0, f"Found insecure HTTP resources: {insecure_tags}"

def test_external_links_have_rel_noopener():
    """Verify that all target="_blank" links include rel="noopener" to prevent window.opener vulnerabilities."""
    content = (DOCS_DIR / "index.html").read_text(encoding="utf-8")
    blank_links_without_noopener = re.findall(r'<a\s+[^>]*target=["\']_blank["\'](?!>[^<]*</a>)[^>]*(?!rel=["\'][^"\']*noopener[^"\']*["\'])[^>]*>', content)
    # Validate each blank link specifically
    for link in re.finditer(r'<a\b[^>]*target=["\']_blank["\'][^>]*>', content):
        tag = link.group(0)
        assert 'rel="noopener' in tag or "rel='noopener" in tag or 'rel="noreferrer' in tag, f"Link missing rel='noopener': {tag}"

def test_tabs_wai_aria_accessibility_pattern():
    """Verify accessible tabs contract (role=tablist, role=tab, role=tabpanel, aria-selected, aria-controls)."""
    content = (DOCS_DIR / "index.html").read_text(encoding="utf-8")
    
    assert 'role="tablist"' in content
    assert 'role="tab"' in content
    assert 'role="tabpanel"' in content
    assert 'aria-selected="true"' in content
    assert 'aria-controls=' in content
    assert 'aria-labelledby=' in content
    
    # Confirm obsolete coverage tab was completely purged
    assert 'id="tab-coverage"' not in content
    assert 'id="panel-coverage"' not in content
    assert 'Mapa de Cobertura' not in content

def test_deploy_workflow_configuration():
    """Verify GitHub Actions Pages deployment workflow."""
    workflow = REPO_ROOT / ".github" / "workflows" / "deploy-pages.yml"
    assert workflow.exists()
    content = workflow.read_text(encoding="utf-8")
    assert "upload-pages-artifact" in content
    assert "deploy-pages" in content
    assert "branches:\n      - main" in content or "branches: [ main ]" in content or "branches:\n      - 'main'" in content
