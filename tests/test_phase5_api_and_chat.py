"""Unit tests for Phase 5: FastAPI endpoints and Chat Assistant."""

import pytest
from unittest.mock import AsyncMock
from httpx import AsyncClient, ASGITransport
from a11y_agent.api.main import app, REPORTS_CACHE, engine
from a11y_agent.models.schema import (
    A11yReport, ReportMetadata, ReportSummary, Finding, Category,
    Principle, WCAGLevel, GuidelinesVersion, FindingOrigin, Remediation, EffortLevel, ImpactLevel
)

@pytest.fixture
def sample_report():
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
        selector="img.avatar",
        line_number=14,
        html_snippet='<img class="avatar" src="avatar.jpg">',
        explanation="La imagen no tiene atributo alt",
        remediation=Remediation(
            before_snippet='<img class="avatar" src="avatar.jpg">',
            after_snippet='<img class="avatar" src="avatar.jpg" alt="Foto de perfil del usuario">',
            advice="Incluya una descripción funcional del usuario.",
            effort=EffortLevel.BAJO
        ),
        impact=ImpactLevel.ALTO,
        confidence=1.0
    )

    meta = ReportMetadata(
        url="https://ejemplo.com",
        guidelines=GuidelinesVersion.WCAG_2_1,
        target_level=WCAGLevel.AA,
        technologies=["HTML5"]
    )
    summary = ReportSummary(
        score=75,
        executive_summary="Resumen de prueba",
        total_problems=1,
        total_warnings=0,
        total_unverified=0
    )
    report = A11yReport(
        id="rep_test_fixture",
        metadata=meta,
        summary=summary,
        principles={},
        all_findings=[f1]
    )
    REPORTS_CACHE[report.id] = report
    return report

@pytest.mark.asyncio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "A11y Agent" in data["service"]

@pytest.mark.asyncio
async def test_chat_endpoint(sample_report):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Question referencing problem 1
        resp = await client.post(
            "/api/chat",
            json={
                "report_id": sample_report.id,
                "message": "¿Cómo arreglo el problema 1?"
            }
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "reply" in data
        assert "Foto de perfil del usuario" in data["reply"]
        assert "H37" in data["reply"]

@pytest.mark.asyncio
async def test_get_report_endpoint(sample_report):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(f"/api/report/{sample_report.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == sample_report.id
        assert data["summary"]["score"] == 75

@pytest.mark.asyncio
async def test_scan_route_passes_cookie_dismissal_preference(sample_report, monkeypatch):
    mock_run_audit = AsyncMock(return_value=sample_report)
    monkeypatch.setattr(engine, "run_audit", mock_run_audit)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/scan",
            json={
                "url": "https://example.com",
                "dismiss_cookies": True,
                "export_formats": []
            }
        )

    assert response.status_code == 200
    assert mock_run_audit.await_args.kwargs["dismiss_cookies"] is True
