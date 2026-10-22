"""Phase 6: Automatic validation with 3 reference scenarios:
1. Accessible page
2. Common accessibility errors page
3. Dynamic JavaScript-heavy SPA page
"""

import threading
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, HTTPServer
from pathlib import Path
import pytest

from a11y_agent.analyzer.engine import A11yEngine
from a11y_agent.models.schema import GuidelinesVersion, WCAGLevel, Category

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"

@pytest.fixture(scope="module")
def local_server():
    """Starts a local HTTP server serving fixtures for testing."""
    handler = partial(SimpleHTTPRequestHandler, directory=str(FIXTURES_DIR))
    server = HTTPServer(("127.0.0.1", 0), handler)
    port = server.server_port

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{port}"
    yield base_url
    server.shutdown()

@pytest.mark.asyncio
async def test_scenario_1_accessible_page(local_server):
    """
    Scenario 1: Accessible Page
    - Must achieve high accessibility score (> 85)
    - Total deterministic problems should be 0 or near 0
    """
    engine = A11yEngine()
    url = f"{local_server}/accessible_page.html"

    report = await engine.run_audit(
        url=url,
        guidelines=GuidelinesVersion.WCAG_2_1,
        target_level=WCAGLevel.AA,
        allow_private_ips=True
    )

    assert report.metadata.execution_time_seconds < 60.0
    assert report.summary.score >= 85
    assert report.summary.total_problems == 0
    assert "HTML5" in report.metadata.technologies

@pytest.mark.asyncio
async def test_scenario_2_common_errors_page(local_server):
    """
    Scenario 2: Common Accessibility Errors Page
    Must detect:
    - Images missing alt / generic alt (1.1.1)
    - Low contrast (1.4.3)
    - Heading hierarchy skip (1.3.1)
    - Missing form label (3.3.2)
    - Missing lang (3.1.1)
    - Ambiguous links (2.4.4)
    """
    engine = A11yEngine()
    url = f"{local_server}/common_errors_page.html"

    report = await engine.run_audit(
        url=url,
        guidelines=GuidelinesVersion.WCAG_2_1,
        target_level=WCAGLevel.AA,
        allow_private_ips=True
    )

    assert report.metadata.execution_time_seconds < 60.0
    assert report.summary.score < 80

    criteria_found = {f.criterion_id for f in report.all_findings}

    # 1. Non-text content (alt)
    assert "1.1.1" in criteria_found

    # 2. Contrast
    assert "1.4.3" in criteria_found

    # 3. Heading hierarchy or info structure
    assert "1.3.1" in criteria_found

    # 4. Form labels
    assert "3.3.2" in criteria_found

    # 5. Page language
    assert "3.1.1" in criteria_found

    # 6. Ambiguous links
    assert "2.4.4" in criteria_found

    # Verify that all findings include criterion, location, and suggested fix
    for f in report.all_findings:
        assert f.criterion_id
        assert f.selector
        assert f.explanation
        assert f.remediation is not None
        assert f.remediation.after_snippet

@pytest.mark.asyncio
async def test_scenario_3_dynamic_spa_page(local_server):
    """
    Scenario 3: Dynamic JavaScript SPA
    - Playwright renders client-side JS elements
    - Detects dynamic image without alt (#dynamic-chart-img)
    - Detects dynamic input without label (#dynamic-filter)
    - Generates report in under 60 seconds
    """
    engine = A11yEngine()
    url = f"{local_server}/dynamic_spa_page.html"

    report = await engine.run_audit(
        url=url,
        guidelines=GuidelinesVersion.WCAG_2_1,
        target_level=WCAGLevel.AA,
        allow_private_ips=True
    )

    assert report.metadata.execution_time_seconds < 60.0

    # Ensure dynamic elements were captured in DOM
    selectors_flagged = [f.selector for f in report.all_findings]
    dynamic_chart_detected = any("dynamic-chart-img" in sel for sel in selectors_flagged)
    dynamic_input_detected = any("dynamic-filter" in sel for sel in selectors_flagged)

    assert dynamic_chart_detected, "Dynamic image injected via JS must be audited"
    assert dynamic_input_detected, "Dynamic form input injected via JS must be audited"
