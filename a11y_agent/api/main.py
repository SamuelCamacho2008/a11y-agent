"""FastAPI application for A11y Agent."""

import json
import re
import secrets
from pathlib import Path
from typing import Optional, List, Dict
from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from a11y_agent.core.config import settings
from a11y_agent.models.schema import (
    A11yReport, GuidelinesVersion, WCAGLevel, ChatRequest, ChatResponse
)
from a11y_agent.analyzer.engine import A11yEngine
from a11y_agent.analyzer.apk_scanner import APKScanner
from a11y_agent.assistant.chat import A11yChatAssistant
from a11y_agent.reporters.html_reporter import render_html_report

app = FastAPI(
    title="A11y Agent API",
    description="Automated & AI-powered Web & Android APK Accessibility Auditor (WCAG 2.0 / 2.1 / 2.2 / EN 301 549)",
    version="1.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = A11yEngine()
apk_scanner = APKScanner()

# In-memory storage for active session reports
REPORTS_CACHE: Dict[str, A11yReport] = {}

class ScanRequest(BaseModel):
    url: str = Field(..., json_schema_extra={"example": "https://example.com"})
    guidelines: GuidelinesVersion = Field(default=GuidelinesVersion.WCAG_2_1)
    target_level: WCAGLevel = Field(default=WCAGLevel.AA)
    allow_private_ips: bool = Field(default=False)
    export_formats: List[str] = Field(default=["html", "json", "pdf"])

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.version,
        "llm_provider": engine.llm_analyzer.provider,
        "capabilities": ["web_audit", "apk_audit", "public_reports", "remediation_chat"]
    }

# ==============================================================================
# REQUERIMIENTO 1: SERVIDOR DE REPORTES PÚBLICOS (GET /view/{report_id})
# ==============================================================================
@app.get("/view/{report_id}", response_class=HTMLResponse)
async def view_public_report(report_id: str):
    """
    Serve a public, accessible, standalone HTML report via a permanent URL.
    """
    # Security check: Validate report_id format to prevent directory traversal
    if not re.match(r"^rep_[a-zA-Z0-9_-]{8,64}$", report_id):
        raise HTTPException(status_code=400, detail="Identificador de informe inválido o con formato incorrecto.")

    html_file = settings.reports_dir / f"{report_id}.html"
    if html_file.exists():
        content = html_file.read_text(encoding="utf-8")
        return HTMLResponse(
            content=content,
            status_code=200,
            headers={
                "Content-Type": "text/html; charset=utf-8",
                "X-Content-Type-Options": "nosniff",
                "Cache-Control": "public, max-age=3600"
            }
        )

    # Fallback: check if JSON report exists and dynamically render HTML
    json_file = settings.reports_dir / f"{report_id}.json"
    if json_file.exists():
        data = json.loads(json_file.read_text(encoding="utf-8"))
        report = A11yReport.model_validate(data)
        html_content = render_html_report(report)
        html_file.write_text(html_content, encoding="utf-8")
        return HTMLResponse(
            content=html_content,
            status_code=200,
            headers={
                "Content-Type": "text/html; charset=utf-8",
                "X-Content-Type-Options": "nosniff",
                "Cache-Control": "public, max-age=3600"
            }
        )

    raise HTTPException(status_code=404, detail="El informe público solicitado no existe o ha expirado.")

@app.post("/api/scan", response_model=A11yReport)
async def scan_url(scan_req: ScanRequest, request: Request):
    """
    Audit an accessible URL against WCAG guidelines and return full structured report with public URL.
    """
    try:
        base_url = str(request.base_url).rstrip("/")
        report = await engine.run_audit(
            url=scan_req.url,
            guidelines=scan_req.guidelines,
            target_level=scan_req.target_level,
            allow_private_ips=scan_req.allow_private_ips,
            export_formats=scan_req.export_formats,
            base_public_url=base_url
        )
        REPORTS_CACHE[report.id] = report
        return report
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==============================================================================
# REQUERIMIENTO 2: AUDITORÍA DE APLICACIONES ANDROID (POST /api/scan-apk)
# ==============================================================================
@app.post("/api/scan-apk", response_model=A11yReport)
async def scan_apk_package(
    request: Request,
    file: UploadFile = File(...),
    guidelines: GuidelinesVersion = Form(GuidelinesVersion.WCAG_2_2),
    target_level: WCAGLevel = Form(WCAGLevel.AA)
):
    """
    Analyze an uploaded Android APK file for mobile accessibility guidelines (WCAG 2.1/2.2 / EN 301 549).
    """
    filename = file.filename or "app.apk"
    if not filename.lower().endswith(".apk"):
        raise HTTPException(
            status_code=400,
            detail="Formato de archivo inválido. Solo se admiten paquetes de aplicación Android con extensión '.apk'."
        )

    # Save uploaded APK safely to uploads directory
    temp_id = secrets.token_hex(8)
    safe_name = f"{temp_id}_{re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)}"
    temp_apk_path = settings.uploads_dir / safe_name

    try:
        # Read file in chunks and check max size limit
        bytes_read = 0
        with open(temp_apk_path, "wb") as f_out:
            while chunk := await file.read(1024 * 1024):  # 1MB chunks
                bytes_read += len(chunk)
                if bytes_read > settings.max_apk_size_bytes:
                    raise HTTPException(
                        status_code=413,
                        detail=f"El archivo APK supera el tamaño máximo permitido ({settings.max_apk_size_bytes // (1024*1024)} MB)."
                    )
                f_out.write(chunk)

        base_url = str(request.base_url).rstrip("/")
        report = await apk_scanner.scan_apk(
            apk_path=temp_apk_path,
            guidelines=guidelines,
            target_level=target_level,
            export_formats=["html", "json", "pdf"],
            base_public_url=base_url
        )

        REPORTS_CACHE[report.id] = report
        return report

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error durante el análisis del APK: {str(e)}")
    finally:
        # Clean up temporary uploaded file
        if temp_apk_path.exists():
            try:
                temp_apk_path.unlink()
            except Exception:
                pass

@app.get("/api/report/{report_id}", response_model=A11yReport)
async def get_report(report_id: str, request: Request):
    """Retrieve an existing report by ID."""
    report = None
    if report_id in REPORTS_CACHE:
        report = REPORTS_CACHE[report_id]
    else:
        # Check disk cache
        json_file = settings.reports_dir / f"{report_id}.json"
        if json_file.exists():
            data = json.loads(json_file.read_text(encoding="utf-8"))
            report = A11yReport.model_validate(data)
            REPORTS_CACHE[report_id] = report

    if report:
        if not report.public_url:
            report.public_url = f"{str(request.base_url).rstrip('/')}/view/{report.id}"
            report.metadata.public_url = report.public_url
        return report

    raise HTTPException(status_code=404, detail="Informe no encontrado.")

@app.get("/api/report/{report_id}/export/{export_format}")
async def export_report(report_id: str, export_format: str):
    """Download the report in HTML, JSON, or PDF format."""
    format_lower = export_format.lower()
    valid_formats = {"html": "text/html", "json": "application/json", "pdf": "application/pdf"}
    if format_lower not in valid_formats:
        raise HTTPException(status_code=400, detail="Formato de exportación no admitido. Use html, json o pdf.")

    file_path = settings.reports_dir / f"{report_id}.{format_lower}"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"El archivo {format_lower.upper()} no existe.")

    return FileResponse(
        path=file_path,
        media_type=valid_formats[format_lower],
        filename=f"a11y_report_{report_id}.{format_lower}"
    )

@app.post("/api/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    """Ask questions and receive contextual remediation assistance."""
    report = None
    if request.report_id in REPORTS_CACHE:
        report = REPORTS_CACHE[request.report_id]
    else:
        json_file = settings.reports_dir / f"{request.report_id}.json"
        if json_file.exists():
            data = json.loads(json_file.read_text(encoding="utf-8"))
            report = A11yReport.model_validate(data)
            REPORTS_CACHE[request.report_id] = report

    if not report:
        raise HTTPException(status_code=404, detail="Informe asociado no encontrado para iniciar el chat.")

    assistant = A11yChatAssistant(report)
    response = await assistant.answer_question(request.message, request.history)
    return response

# Serve Web UI at root
INDEX_HTML_PATH = Path(__file__).resolve().parent / "static" / "index.html"

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    if INDEX_HTML_PATH.exists():
        return INDEX_HTML_PATH.read_text(encoding="utf-8")
    return "<h1>A11y Agent API is running</h1>"
