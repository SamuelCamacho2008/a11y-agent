"""FastAPI application for A11y Agent."""

import json
from pathlib import Path
from typing import Optional, List, Dict
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from a11y_agent.core.config import settings
from a11y_agent.models.schema import (
    A11yReport, GuidelinesVersion, WCAGLevel, ChatRequest, ChatResponse
)
from a11y_agent.analyzer.engine import A11yEngine
from a11y_agent.assistant.chat import A11yChatAssistant
from a11y_agent.reporters.html_reporter import render_html_report

app = FastAPI(
    title="A11y Agent API",
    description="Automated & AI-powered Web Accessibility Auditor (WCAG 2.0 / 2.1 / 2.2)",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = A11yEngine()
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
        "llm_provider": engine.llm_analyzer.provider
    }

@app.post("/api/scan", response_model=A11yReport)
async def scan_url(request: ScanRequest):
    """
    Audit an accessible URL against WCAG guidelines and return full structured report.
    """
    try:
        report = await engine.run_audit(
            url=request.url,
            guidelines=request.guidelines,
            target_level=request.target_level,
            allow_private_ips=request.allow_private_ips,
            export_formats=request.export_formats
        )
        REPORTS_CACHE[report.id] = report
        return report
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/report/{report_id}", response_model=A11yReport)
async def get_report(report_id: str):
    """Retrieve an existing report by ID."""
    if report_id in REPORTS_CACHE:
        return REPORTS_CACHE[report_id]

    # Check disk cache
    json_file = settings.reports_dir / f"{report_id}.json"
    if json_file.exists():
        data = json.loads(json_file.read_text(encoding="utf-8"))
        report = A11yReport.model_validate(data)
        REPORTS_CACHE[report_id] = report
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
