"""Unit and integration tests for GitHub Pages public reports publishing."""

import json
import pytest
from pathlib import Path

from a11y_agent.core.config import settings
from a11y_agent.models.schema import (
    Finding, Category, Principle, WCAGLevel, GuidelinesVersion,
    FindingOrigin, ImpactLevel
)
from a11y_agent.analyzer.scorer import build_a11y_report
from a11y_agent.reporters.git_publisher import (
    publish_report_to_docs, update_docs_manifest, generate_portal_html, git_push_report
)

@pytest.fixture
def dummy_report():
    report_id = "rep_gh_pages_test_1234567890abcdef"
    f1 = Finding(
        id="P-001",
        principle=Principle.PERCEPTIBLE,
        criterion_id="1.1.1",
        criterion_title="Contenido no textual",
        level=WCAGLevel.A,
        category=Category.PROBLEMA,
        origin=FindingOrigin.REGLA,
        check_name="Falta texto alternativo",
        w3c_technique="H37",
        selector="img.logo",
        line_number=12,
        html_snippet='<img class="logo" src="logo.png">',
        explanation="La imagen no tiene atributo alt.",
        impact=ImpactLevel.ALTO,
        confidence=1.0
    )
    report = build_a11y_report(
        report_id=report_id,
        url="https://ejemplo.com/landing",
        findings=[f1],
        guidelines=GuidelinesVersion.WCAG_2_2,
        target_level=WCAGLevel.AA,
        technologies=["HTML5", "TailwindCSS"],
        target_type="web"
    )
    return report

def test_publish_report_to_docs_creates_files(dummy_report):
    """Verifica que publish_report_to_docs genera el HTML, JSON, portal y manifiesto en docs/."""
    result = publish_report_to_docs(dummy_report)

    assert result["report_id"] == dummy_report.id
    assert "https://samuelcamacho2008.github.io/a11y-agent/reports/" in result["github_pages_url"]

    html_file = Path(result["html_path"])
    json_file = Path(result["json_path"])
    assert html_file.exists()
    assert json_file.exists()

    # Verify portal index.html exists
    portal_html = settings.docs_dir / "index.html"
    assert portal_html.exists()
    assert "A11y Agent" in portal_html.read_text(encoding="utf-8")

    # Verify reports.json manifest has the entry
    manifest_file = settings.docs_dir / "reports.json"
    assert manifest_file.exists()
    manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
    assert any(r["id"] == dummy_report.id for r in manifest_data)

def test_report_schema_has_github_pages_url(dummy_report):
    """Verifica que el modelo A11yReport contiene la URL de GitHub Pages."""
    assert dummy_report.github_pages_url is not None
    assert dummy_report.github_pages_url.startswith("https://samuelcamacho2008.github.io/a11y-agent/reports/")
    assert dummy_report.public_url == dummy_report.github_pages_url

def test_git_push_report_logic(monkeypatch):
    """Verifica la lógica de git_push_report cuando git add/diff/commit/push se ejecutan."""
    class MockProc:
        returncode = 0
        stdout = "docs/reports.json\n"
        stderr = ""

    def mock_run(cmd, *args, **kwargs):
        return MockProc()

    monkeypatch.setattr("a11y_agent.reporters.git_publisher.subprocess.run", mock_run)
    res = git_push_report("rep_test_123")
    assert res["success"] is True
    assert "github_pages_url" in res
    assert "rep_test_123" in res["github_pages_url"]
