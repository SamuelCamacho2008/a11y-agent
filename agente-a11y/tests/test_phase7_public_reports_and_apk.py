"""Unit and integration tests for Phase 7:
1. Public Report Server (GET /view/{report_id} and persistent storage).
2. Android APK Accessibility Auditor (POST /api/scan-apk and APKScanner engine).
"""

import io
import zipfile
import pytest
from pathlib import Path
from httpx import AsyncClient, ASGITransport

from a11y_agent.api.main import app, REPORTS_CACHE
from a11y_agent.analyzer.apk_scanner import (
    APKScanner, parse_dimension_dp, calculate_luminance, calculate_contrast_ratio
)
from a11y_agent.models.schema import (
    A11yReport, ReportMetadata, ReportSummary, Finding, Category,
    Principle, WCAGLevel, GuidelinesVersion, FindingOrigin, Remediation,
    EffortLevel, ImpactLevel
)
from a11y_agent.core.config import settings
from a11y_agent.reporters.html_reporter import export_to_html
from a11y_agent.reporters.json_reporter import export_to_json

@pytest.fixture
def sample_persisted_report(tmp_path):
    report_id = "rep_test_public_1234567890abcdef"
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
        selector="img.banner",
        line_number=5,
        html_snippet='<img class="banner" src="banner.jpg">',
        explanation="La imagen no contiene atributo alt.",
        impact=ImpactLevel.ALTO,
        confidence=1.0
    )
    meta = ReportMetadata(
        url="https://ejemplo.com/public",
        target_type="web",
        guidelines=GuidelinesVersion.WCAG_2_1,
        target_level=WCAGLevel.AA,
        technologies=["HTML5"]
    )
    summary = ReportSummary(
        score=82,
        executive_summary="Reporte de prueba persistido",
        total_problems=1,
        total_warnings=0,
        total_unverified=0
    )
    report = A11yReport(
        id=report_id,
        target_type="web",
        public_url=f"http://localhost:8000/view/{report_id}",
        metadata=meta,
        summary=summary,
        principles={},
        all_findings=[f1]
    )
    
    # Save in REPORTS_CACHE and disk
    REPORTS_CACHE[report_id] = report
    export_to_html(report, settings.reports_dir / f"{report_id}.html")
    export_to_json(report, settings.reports_dir / f"{report_id}.json")
    
    yield report

@pytest.fixture
def sample_apk_bytes():
    """Generates an in-memory zip resembling an Android APK with layout and manifest."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        manifest_xml = """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.example.accessibleapp"
    android:versionCode="1"
    android:versionName="1.0">
    <application
        android:label="Accessible Test App"
        android:supportsRtl="true">
        <activity android:name=".MainActivity" />
    </application>
</manifest>"""
        zf.writestr("AndroidManifest.xml", manifest_xml)

        layout_xml = """<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:orientation="vertical">

    <!-- Issue 1: ImageButton without contentDescription (1.1.1) -->
    <ImageButton
        android:id="@+id/btn_cart"
        android:layout_width="48dp"
        android:layout_height="48dp"
        android:src="@drawable/ic_cart" />

    <!-- Issue 2: EditText without hint or labelFor (3.3.2) -->
    <EditText
        android:id="@+id/input_user"
        android:layout_width="match_parent"
        android:layout_height="48dp" />

    <!-- Issue 3: Small touch target < 48dp (2.5.8 / 2.5.5) -->
    <Button
        android:id="@+id/btn_small"
        android:layout_width="32dp"
        android:layout_height="24dp"
        android:text="OK" />

    <!-- Issue 4: importantForAccessibility="no" on clickable control (4.1.2) -->
    <Button
        android:id="@+id/btn_hidden_interactive"
        android:layout_width="50dp"
        android:layout_height="50dp"
        android:text="Ignorado"
        android:importantForAccessibility="no" />

    <!-- Issue 5: Low color contrast (1.4.3) -->
    <TextView
        android:id="@+id/txt_low_contrast"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:text="Texto con bajo contraste"
        android:textColor="#CCCCCC"
        android:background="#FFFFFF" />

    <!-- Accessible element with descriptive contentDescription -->
    <ImageView
        android:id="@+id/img_good"
        android:layout_width="48dp"
        android:layout_height="48dp"
        android:contentDescription="Logotipo accesible de la aplicación" />
</LinearLayout>"""
        zf.writestr("res/layout/activity_main.xml", layout_xml)

    return buffer.getvalue()


# =========================================================================
# REQUERIMIENTO 1: Tests de Servidor de Reportes Públicos
# =========================================================================

@pytest.mark.asyncio
async def test_get_public_report_view_success(sample_persisted_report):
    """Verifica que GET /view/{report_id} sirve el HTML de forma limpia y accesible."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(f"/view/{sample_persisted_report.id}")
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("content-type", "")
        assert "A11y Agent" in resp.text
        assert sample_persisted_report.id in resp.text
        assert "Reporte de prueba persistido" in resp.text

@pytest.mark.asyncio
async def test_get_public_report_view_not_found():
    """Verifica que un report_id inexistente retorna 404."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/view/rep_non_existent_99999999")
        assert resp.status_code == 404
        data = resp.json()
        assert "no existe" in data["detail"].lower()

@pytest.mark.asyncio
async def test_get_public_report_path_traversal_prevention():
    """Verifica que ataques de directory traversal son bloqueados."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/view/..%2F..%2Fetc%2Fpasswd")
        assert resp.status_code in (400, 404)


# =========================================================================
# REQUERIMIENTO 2: Tests del Analizador de APK y Endpoint
# =========================================================================

def test_apk_scanner_dimension_and_contrast_helpers():
    """Prueba las funciones auxiliares de dimensiones y cálculo de contraste WCAG."""
    # parse_dimension_dp
    assert parse_dimension_dp("48dp") == 48.0
    assert parse_dimension_dp("32.5dip") == 32.5
    assert parse_dimension_dp("wrap_content") is None
    assert parse_dimension_dp("@dimen/btn_height") is None

    # Luminance & contrast ratio
    lum_white = calculate_luminance(255, 255, 255)
    lum_black = calculate_luminance(0, 0, 0)
    assert lum_white == 1.0
    assert lum_black == 0.0

    ratio_black_white = calculate_contrast_ratio("#000000", "#FFFFFF")
    assert pytest.approx(ratio_black_white, 0.1) == 21.0

    ratio_white_white = calculate_contrast_ratio("#FFFFFF", "#FFFFFF")
    assert pytest.approx(ratio_white_white, 0.1) == 1.0

    # Low contrast: #CCCCCC on #FFFFFF has ratio ~1.6:1 (fails WCAG 1.4.3 minimum 4.5:1)
    ratio_low = calculate_contrast_ratio("#CCCCCC", "#FFFFFF")
    assert ratio_low is not None
    assert ratio_low < 4.5

@pytest.mark.asyncio
async def test_apk_scanner_engine_analysis(tmp_path, sample_apk_bytes):
    """Ejecuta el motor APKScanner sobre un APK sintetizado y verifica la detección de reglas móviles."""
    apk_file = tmp_path / "test_app.apk"
    apk_file.write_bytes(sample_apk_bytes)

    scanner = APKScanner()
    report = await scanner.scan_apk(
        apk_path=apk_file,
        guidelines=GuidelinesVersion.EN_301_549,
        target_level=WCAGLevel.AA,
        base_public_url="http://localhost:8000"
    )

    assert report is not None
    assert report.target_type == "apk"
    assert report.package_name == "com.example.accessibleapp"
    assert report.app_name == "Accessible Test App"
    assert report.public_url.startswith("http://localhost:8000/view/rep_")
    assert report.summary.score < 100
    assert len(report.all_findings) >= 4

    criterion_ids = [f.criterion_id for f in report.all_findings]
    assert "1.1.1" in criterion_ids  # Missing contentDescription on ImageButton
    assert "3.3.2" in criterion_ids  # Missing hint on EditText
    assert any(c in criterion_ids for c in ("2.5.8", "2.5.5"))  # Small touch target
    assert "4.1.2" in criterion_ids  # importantForAccessibility="no" on interactive button

    # Verify remediation snippets are XML
    f_111 = next(f for f in report.all_findings if f.criterion_id == "1.1.1")
    assert f_111.remediation is not None
    assert "android:contentDescription" in f_111.remediation.after_snippet
    assert f_111.category == Category.PROBLEMA

@pytest.mark.asyncio
async def test_api_scan_apk_endpoint_validation_and_flow(sample_apk_bytes):
    """Verifica el endpoint POST /api/scan-apk para archivo inválido y para APK válido."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Reject non-.apk extension
        files_invalid = {"file": ("documento.pdf", b"Dummy PDF content", "application/pdf")}
        resp_invalid = await client.post("/api/scan-apk", files=files_invalid)
        assert resp_invalid.status_code == 400
        assert "apk" in resp_invalid.json()["detail"].lower()

        # 2. Valid .apk upload
        files_valid = {"file": ("mifastapp.apk", sample_apk_bytes, "application/vnd.android.package-archive")}
        data = {
            "guidelines": "WCAG 2.2",
            "target_level": "AA"
        }
        resp_valid = await client.post("/api/scan-apk", files=files_valid, data=data)
        assert resp_valid.status_code == 200
        report_data = resp_valid.json()

        assert report_data["target_type"] == "apk"
        assert report_data["package_name"] == "com.example.accessibleapp"
        assert report_data["app_name"] == "Accessible Test App"
        assert "public_url" in report_data
        assert "/view/" in report_data["public_url"]
        assert len(report_data["all_findings"]) > 0

        # 3. Test that the generated public_url works via GET /view/{report_id}
        report_id = report_data["id"]
        resp_view = await client.get(f"/view/{report_id}")
        assert resp_view.status_code == 200
        assert "text/html" in resp_view.headers.get("content-type", "")
        assert "Accessible Test App" in resp_view.text
