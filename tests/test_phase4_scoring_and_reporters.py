"""Unit tests for Phase 4: Consolidation, Scoring, and Reporters (JSON, HTML, PDF)."""

import pytest
from pathlib import Path
from a11y_agent.models.schema import (
    Finding, Category, FindingOrigin, ImpactLevel, Principle,
    WCAGLevel, GuidelinesVersion, Remediation, EffortLevel
)
from a11y_agent.analyzer.scorer import calculate_score, deduplicate_findings, build_a11y_report
from a11y_agent.reporters.json_reporter import export_to_json
from a11y_agent.reporters.html_reporter import export_to_html, render_html_report
from a11y_agent.reporters.pdf_reporter import export_to_pdf

def test_calculate_score_and_deduplication():
    f1 = Finding(
        id="P-01",
        principle=Principle.PERCEPTIBLE,
        criterion_id="1.1.1",
        criterion_title="Contenido no textual",
        level=WCAGLevel.A,
        category=Category.PROBLEMA,
        origin=FindingOrigin.REGLA,
        check_name="Img alt missing",
        w3c_technique="H37",
        selector="img.logo",
        line_number=10,
        html_snippet='<img class="logo" src="logo.png">',
        explanation="Missing alt attribute",
        impact=ImpactLevel.CRITICO,
        confidence=1.0
    )

    f2_duplicate = Finding(
        id="IA-01",
        principle=Principle.PERCEPTIBLE,
        criterion_id="1.1.1",
        criterion_title="Contenido no textual",
        level=WCAGLevel.A,
        category=Category.ADVERTENCIA,
        origin=FindingOrigin.IA,
        check_name="Evaluación alt",
        w3c_technique="H37",
        selector="img.logo",
        line_number=10,
        html_snippet='<img class="logo" src="logo.png">',
        explanation="Alt text is missing",
        remediation=Remediation(
            before_snippet='<img class="logo" src="logo.png">',
            after_snippet='<img class="logo" src="logo.png" alt="Logo de la empresa">',
            advice="Add descriptive alt",
            effort=EffortLevel.BAJO
        ),
        impact=ImpactLevel.ALTO,
        confidence=0.9
    )

    f3_warning = Finding(
        id="A-01",
        principle=Principle.OPERABLE,
        criterion_id="2.4.4",
        criterion_title="Propósito de cada enlace",
        level=WCAGLevel.A,
        category=Category.ADVERTENCIA,
        origin=FindingOrigin.IA,
        check_name="Enlace ambiguo",
        w3c_technique="H30",
        selector="a.more",
        line_number=25,
        html_snippet='<a class="more" href="#">leer más</a>',
        explanation="Enlace ambiguo fuera de contexto",
        impact=ImpactLevel.MEDIO,
        confidence=0.85
    )

    raw_findings = [f1, f2_duplicate, f3_warning]
    deduped = deduplicate_findings(raw_findings)

    # f1 and f2_duplicate share same criterion and selector -> should be merged to 1
    assert len(deduped) == 2

    # Score calculation
    score, breakdown = calculate_score(deduped)
    assert 0 <= score <= 100
    assert breakdown["crítico"] == 1
    assert breakdown["medio"] == 1

def test_build_a11y_report_structure():
    f1 = Finding(
        id="P-01",
        principle=Principle.PERCEPTIBLE,
        criterion_id="1.1.1",
        criterion_title="Contenido no textual",
        level=WCAGLevel.A,
        category=Category.PROBLEMA,
        origin=FindingOrigin.REGLA,
        check_name="Falta alt",
        w3c_technique="H37",
        selector="img",
        line_number=5,
        html_snippet='<img src="pic.jpg">',
        explanation="Sin alt",
        impact=ImpactLevel.ALTO,
        confidence=1.0
    )

    report = build_a11y_report(
        report_id="test_rep_123",
        url="https://example.com/test",
        findings=[f1],
        guidelines=GuidelinesVersion.WCAG_2_1,
        target_level=WCAGLevel.AA,
        technologies=["React", "Tailwind CSS"],
        execution_time_seconds=2.5
    )

    assert report.id == "test_rep_123"
    assert report.metadata.url == "https://example.com/test"
    assert "React" in report.metadata.technologies
    assert len(report.principles["perceptible"].success_criteria) == 1
    assert report.summary.total_problems == 1

@pytest.mark.asyncio
async def test_exporters(tmp_path: Path):
    f1 = Finding(
        id="P-01",
        principle=Principle.PERCEPTIBLE,
        criterion_id="1.1.1",
        criterion_title="Contenido no textual",
        level=WCAGLevel.A,
        category=Category.PROBLEMA,
        origin=FindingOrigin.REGLA,
        check_name="Falta texto alternativo",
        w3c_technique="H37",
        selector="img.hero",
        line_number=12,
        html_snippet='<img class="hero" src="hero.jpg">',
        explanation="La imagen no tiene atributo alt",
        remediation=Remediation(
            before_snippet='<img class="hero" src="hero.jpg">',
            after_snippet='<img class="hero" src="hero.jpg" alt="Imagen principal">',
            advice="Añada un alt descriptivo.",
            effort=EffortLevel.BAJO
        ),
        impact=ImpactLevel.ALTO,
        confidence=1.0
    )

    report = build_a11y_report(
        report_id="export_test",
        url="https://example.com",
        findings=[f1]
    )

    # 1. JSON Export
    json_path = tmp_path / "report.json"
    export_to_json(report, json_path)
    assert json_path.exists()
    assert '"score":' in json_path.read_text(encoding="utf-8")

    # 2. HTML Export
    html_path = tmp_path / "report.html"
    export_to_html(report, html_path)
    assert html_path.exists()
    html_text = html_path.read_text(encoding="utf-8")
    assert "Informe de Accesibilidad Web" in html_text
    assert "1.1.1 Contenido no textual" in html_text
    assert "hero.jpg" in html_text

    # 3. PDF Export
    pdf_path = tmp_path / "report.pdf"
    await export_to_pdf(report, pdf_path)
    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 1000  # Non-trivial PDF generated
