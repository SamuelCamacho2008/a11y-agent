"""Pydantic data models for A11y Agent conforming to WCAG 2.1 / 2.2 and mobile accessibility specifications."""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field

class Principle(str, Enum):
    PERCEPTIBLE = "perceptible"
    OPERABLE = "operable"
    UNDERSTANDABLE = "understandable"
    ROBUST = "robust"

class WCAGLevel(str, Enum):
    A = "A"
    AA = "AA"
    AAA = "AAA"

class GuidelinesVersion(str, Enum):
    WCAG_2_0 = "WCAG 2.0"
    WCAG_2_1 = "WCAG 2.1"
    WCAG_2_2 = "WCAG 2.2"
    EN_301_549 = "EN 301 549"

class Category(str, Enum):
    PROBLEMA = "Problema"
    ADVERTENCIA = "Advertencia"
    NO_VERIFICADO = "No verificado"

class FindingOrigin(str, Enum):
    REGLA = "regla"
    IA = "ia"

class ImpactLevel(str, Enum):
    CRITICO = "crítico"
    ALTO = "alto"
    MEDIO = "medio"
    BAJO = "bajo"

class EffortLevel(str, Enum):
    BAJO = "bajo"
    MEDIO = "medio"
    ALTO = "alto"

class Remediation(BaseModel):
    before_snippet: str = Field(..., description="Fragmento de código con el problema")
    after_snippet: str = Field(..., description="Fragmento de código con la solución accesible")
    advice: str = Field(..., description="Instrucciones claras de corrección")
    effort: EffortLevel = Field(default=EffortLevel.MEDIO, description="Esfuerzo estimado de corrección")

class Finding(BaseModel):
    id: str = Field(..., description="Identificador único del hallazgo (ej. P1-1.1.1-01)")
    principle: Principle = Field(..., description="Principio WCAG al que pertenece")
    criterion_id: str = Field(..., description="Criterio de éxito (ej. 1.1.1)")
    criterion_title: str = Field(..., description="Nombre del criterio (ej. Contenido no textual)")
    level: WCAGLevel = Field(default=WCAGLevel.A, description="Nivel de conformidad (A, AA, AAA)")
    category: Category = Field(..., description="Problema, Advertencia o No verificado")
    origin: FindingOrigin = Field(default=FindingOrigin.REGLA, description="Origen de detección (regla o ia)")
    check_name: str = Field(..., description="Nombre técnico de la comprobación")
    w3c_technique: str = Field(default="G94", description="Técnica W3C o móvil asociada (ej. H37, AND1, G219)")
    selector: str = Field(..., description="Selector CSS, XPath o View ID del elemento")
    line_number: Optional[int] = Field(default=None, description="Número de línea en el código fuente si fue localizado")
    html_snippet: str = Field(..., description="Fragmento de código analizado (HTML o XML Android)")
    explanation: str = Field(..., description="Explicación en lenguaje simple del impacto en la accesibilidad")
    remediation: Optional[Remediation] = Field(default=None, description="Solución concreta antes y después")
    impact: ImpactLevel = Field(default=ImpactLevel.MEDIO, description="Nivel de impacto en el usuario")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Grado de certeza (1.0 para reglas, 0.0-1.0 para IA)")

class SuccessCriterionGroup(BaseModel):
    criterion_id: str
    criterion_title: str
    level: WCAGLevel
    findings: List[Finding] = Field(default_factory=list)

class PrincipleFindings(BaseModel):
    key: Principle
    name: str
    description: str
    success_criteria: List[SuccessCriterionGroup] = Field(default_factory=list)

class ReportMetadata(BaseModel):
    url: str = Field(..., description="URL analizada o identificador del paquete APK")
    target_type: Literal["web", "apk"] = Field(default="web", description="Tipo de recurso analizado ('web' o 'apk')")
    app_name: Optional[str] = Field(default=None, description="Nombre de la aplicación móvil (si aplica)")
    package_name: Optional[str] = Field(default=None, description="Package Name de la app Android (si aplica)")
    public_url: Optional[str] = Field(default=None, description="Enlace público compartible del informe")
    github_pages_url: Optional[str] = Field(default=None, description="Enlace público permanente en GitHub Pages")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    guidelines: GuidelinesVersion = Field(default=GuidelinesVersion.WCAG_2_1)
    target_level: WCAGLevel = Field(default=WCAGLevel.AA)
    technologies: List[str] = Field(default_factory=list)
    execution_time_seconds: float = 0.0
    screenshot_path: Optional[str] = None

class ReportSummary(BaseModel):
    score: int = Field(..., ge=0, le=100, description="Indicador interno heurístico (0-100); no es un porcentaje de conformidad ni una puntuación oficial de TAW")
    executive_summary: str = Field(..., description="Resumen ejecutivo conciso de 5 líneas")
    total_problems: int = 0
    total_warnings: int = 0
    total_unverified: int = 0
    impact_breakdown: Dict[str, int] = Field(default_factory=dict)

class A11yReport(BaseModel):
    id: str
    target_type: Literal["web", "apk"] = Field(default="web", description="Tipo de recurso analizado ('web' o 'apk')")
    app_name: Optional[str] = Field(default=None, description="Nombre de la app si es APK")
    package_name: Optional[str] = Field(default=None, description="Package Name de la app si es APK")
    public_url: Optional[str] = Field(default=None, description="Enlace público compartible permanente")
    github_pages_url: Optional[str] = Field(default=None, description="Enlace público permanente en GitHub Pages")
    metadata: ReportMetadata
    summary: ReportSummary
    principles: Dict[str, PrincipleFindings]
    all_findings: List[Finding] = Field(default_factory=list)
    disclaimer: str = (
        "AVISO IMPORTANTE: Esta auditoría automática y asistida por IA es una herramienta de apoyo "
        "y no sustituye la evaluación manual exhaustiva realizada por expertos ni las pruebas directas "
        "con usuarios con discapacidad empleando tecnologías de asistencia (lectores de pantalla TalkBack, NVDA, switches, etc.)."
    )

class ChatMessage(BaseModel):
    role: str = Field(..., description="'user', 'assistant' o 'system'")
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ChatRequest(BaseModel):
    report_id: str
    message: str
    history: List[ChatMessage] = Field(default_factory=list)

class ChatResponse(BaseModel):
    reply: str
    referenced_findings: List[str] = Field(default_factory=list)
