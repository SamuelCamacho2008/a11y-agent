"""Multi-provider LLM client with structured JSON output and anti-hallucination guards."""

import json
import re
from typing import List, Dict, Any, Optional
import httpx

from a11y_agent.core.config import settings
from a11y_agent.models.schema import (
    Finding, Category, FindingOrigin, ImpactLevel, EffortLevel,
    Principle, WCAGLevel, Remediation
)
from a11y_agent.models.wcag_catalog import get_criterion_details
from a11y_agent.analyzer.line_locator import find_line_number

SEMANTIC_ANALYSIS_SYSTEM_PROMPT = """Eres un especialista senior en accesibilidad web (WCAG 2.1 / 2.2).
Tu tarea es evaluar semánticamente fragmentos HTML específicos que requieren juicio humano/contextual:
1. Textos alternativos de imágenes: ¿son descriptivos del contenido o genéricos ("imagen", "foto", nombres de archivo)?
2. Textos de enlaces: ¿tienen sentido fuera de contexto o son ambiguos ("clic aquí", "leer más", "ver más")?
3. Estructura de encabezados: ¿hay saltos ilógicos de niveles (ej. de h1 a h4) o encabezados vacíos?
4. Etiquetas de formularios: ¿los campos carecen de etiquetas descriptivas visibles o dependen sólo de placeholders?
5. Idioma: ¿está ausente o en conflicto el atributo lang con el contenido?

REGLAS ESTRICTAS ANTI-ALUCINACIÓN:
- SOLO evalúa los fragmentos proporcionados en el payload JSON.
- Todo hallazgo DEBE citar el fragmento HTML exacto (before_snippet) tal como aparece en el input.
- Todo hallazgo debe ser clasificado como "Advertencia" con un nivel de confianza (entre 0.70 y 0.95).
- Si un elemento es ambiguo pero aceptable en su contexto mínimo, clasifícalo como "No verificado" o no generes hallazgo.
- Para cada hallazgo, proporciona el código corregido (after_snippet), una explicación simple y el esfuerzo estimado (bajo, medio, alto).

Responde EXCLUSIVAMENTE con un objeto JSON válido con la siguiente estructura:
{
  "findings": [
    {
      "criterion_id": "1.1.1",
      "w3c_technique": "H37",
      "check_name": "Nombre descriptivo de la comprobación",
      "selector": "selector CSS",
      "html_snippet": "<img ...>",
      "explanation": "Explicación clara en lenguaje sencillo...",
      "impact": "alto" | "medio" | "bajo",
      "confidence": 0.85,
      "remediation": {
        "before_snippet": "<img ...>",
        "after_snippet": "<img ... alt='...'>",
        "advice": "Instrucción concreta de corrección",
        "effort": "bajo" | "medio" | "alto"
      }
    }
  ]
}
"""

class LLMAnalyzer:
    """Manages semantic evaluation via configured LLM provider or heuristic fallback."""

    def __init__(self):
        self.provider = settings.llm_provider
        if self.provider == "auto":
            if settings.anthropic_api_key:
                self.provider = "anthropic"
            elif settings.openai_api_key:
                self.provider = "openai"
            elif settings.gemini_api_key:
                self.provider = "gemini"
            else:
                self.provider = "mock"

    async def analyze_semantics(
        self,
        candidates: Dict[str, Any],
        raw_html: str,
        target_level: WCAGLevel = WCAGLevel.AA
    ) -> List[Finding]:
        """Run semantic analysis on candidates using the active provider."""
        if self.provider == "mock":
            return self._heuristic_mock_analyze(candidates, raw_html)

        try:
            if self.provider == "openai":
                return await self._call_openai(candidates, raw_html)
            elif self.provider == "anthropic":
                return await self._call_anthropic(candidates, raw_html)
            elif self.provider == "gemini":
                return await self._call_gemini(candidates, raw_html)
            else:
                return self._heuristic_mock_analyze(candidates, raw_html)
        except Exception:
            # Fallback graceful to heuristic analysis if API call fails
            return self._heuristic_mock_analyze(candidates, raw_html)

    def _heuristic_mock_analyze(self, candidates: Dict[str, Any], raw_html: str) -> List[Finding]:
        """Deterministic semantic evaluation engine when no external LLM key is configured."""
        findings: List[Finding] = []
        counter = 1

        # 1. Images
        for img_cand in candidates.get("images", []):
            snippet = img_cand["snippet"]
            alt = img_cand.get("alt", "")
            selector = img_cand.get("selector", "img")
            line_no = find_line_number(raw_html, snippet, selector)

            if not alt:
                explanation = "La imagen carece de texto alternativo. Los lectores de pantalla leerán el nombre del archivo o la ignorarán."
                advice = "Agregue un atributo alt descriptivo con el propósito de la imagen."
                after = snippet.replace("<img", '<img alt="Descripción concisa y útil de la imagen"')
            else:
                explanation = f"El texto alternativo '{alt}' es genérico y no describe el contenido visual para usuarios ciegos."
                advice = "Sustituya el texto alternativo por uno que describa objetivamente la función o información de la imagen."
                after = re.sub(r'alt=["\'][^"\']*["\']', 'alt="Descripción objetiva del contenido"', snippet)

            finding = Finding(
                id=f"IA-IMG-{counter:02d}",
                principle=Principle.PERCEPTIBLE,
                criterion_id="1.1.1",
                criterion_title="Contenido no textual",
                level=WCAGLevel.A,
                category=Category.ADVERTENCIA,
                origin=FindingOrigin.IA,
                check_name="Evaluación semántica de texto alternativo",
                w3c_technique="H37",
                selector=selector,
                line_number=line_no,
                html_snippet=snippet,
                explanation=explanation,
                remediation=Remediation(
                    before_snippet=snippet,
                    after_snippet=after,
                    advice=advice,
                    effort=EffortLevel.BAJO
                ),
                impact=ImpactLevel.ALTO,
                confidence=0.88
            )
            findings.append(finding)
            counter += 1

        # 2. Links
        for link_cand in candidates.get("links", []):
            snippet = link_cand["snippet"]
            text = link_cand.get("text", "")
            selector = link_cand.get("selector", "a")
            line_no = find_line_number(raw_html, snippet, selector)

            finding = Finding(
                id=f"IA-LNK-{counter:02d}",
                principle=Principle.OPERABLE,
                criterion_id="2.4.4",
                criterion_title="Propósito de cada enlace (en contexto)",
                level=WCAGLevel.A,
                category=Category.ADVERTENCIA,
                origin=FindingOrigin.IA,
                check_name="Evaluación de claridad del texto de enlace",
                w3c_technique="H30",
                selector=selector,
                line_number=line_no,
                html_snippet=snippet,
                explanation=f"El texto del enlace '{text}' es ambiguo fuera de contexto. Los usuarios de lectores de pantalla navegan frecuentemente por listas de enlaces aislados.",
                remediation=Remediation(
                    before_snippet=snippet,
                    after_snippet=snippet.replace(f">{text}<", ">Ver detalles completos del informe de accesibilidad<"),
                    advice="Sustituya el texto por uno que identifique claramente el destino o agregue un atributo aria-label explicativo.",
                    effort=EffortLevel.BAJO
                ),
                impact=ImpactLevel.MEDIO,
                confidence=0.92
            )
            findings.append(finding)
            counter += 1

        # 3. Headings structure
        headings = candidates.get("headings", [])
        if headings:
            prev_level = 0
            for h in headings:
                curr_level = h["level"]
                if prev_level > 0 and (curr_level - prev_level) > 1:
                    snippet = h["snippet"]
                    line_no = find_line_number(raw_html, snippet)
                    finding = Finding(
                        id=f"IA-HDG-{counter:02d}",
                        principle=Principle.PERCEPTIBLE,
                        criterion_id="1.3.1",
                        criterion_title="Información y relaciones",
                        level=WCAGLevel.A,
                        category=Category.ADVERTENCIA,
                        origin=FindingOrigin.IA,
                        check_name="Discontinuidad en jerarquía de encabezados",
                        w3c_technique="G141",
                        selector=h["tag"],
                        line_number=line_no,
                        html_snippet=snippet,
                        explanation=f"Se detectó un salto brusco de nivel <h{prev_level}> a <h{curr_level}> ('{h['text']}'). La estructura de encabezados debe ser secuencial sin saltos.",
                        remediation=Remediation(
                            before_snippet=snippet,
                            after_snippet=snippet.replace(f"<h{curr_level}", f"<h{prev_level + 1}").replace(f"</h{curr_level}>", f"</h{prev_level + 1}>"),
                            advice=f"Utilice <h{prev_level + 1}> para mantener una jerarquía anidada lógica.",
                            effort=EffortLevel.BAJO
                        ),
                        impact=ImpactLevel.MEDIO,
                        confidence=0.90
                    )
                    findings.append(finding)
                    counter += 1
                prev_level = curr_level

        # 4. Form inputs without labels
        for form_cand in candidates.get("forms", []):
            snippet = form_cand["snippet"]
            selector = form_cand["selector"]
            placeholder = form_cand.get("placeholder", "")
            line_no = find_line_number(raw_html, snippet, selector)

            label_text = placeholder if placeholder else "Nombre del campo"
            field_id = "campo-accesible"
            corrected = f'<label for="{field_id}">{label_text}:</label>\n' + snippet.replace("<input", f'<input id="{field_id}"')

            finding = Finding(
                id=f"IA-FRM-{counter:02d}",
                principle=Principle.UNDERSTANDABLE,
                criterion_id="3.3.2",
                criterion_title="Etiquetas o instrucciones",
                level=WCAGLevel.A,
                category=Category.ADVERTENCIA,
                origin=FindingOrigin.IA,
                check_name="Uso inadecuado de placeholder en vez de etiqueta",
                w3c_technique="H44",
                selector=selector,
                line_number=line_no,
                html_snippet=snippet,
                explanation="El campo no tiene una etiqueta <label> formal. Los placeholders desaparecen al escribir y no son reconocidos como etiquetas persistentes por todas las ayudas técnicas.",
                remediation=Remediation(
                    before_snippet=snippet,
                    after_snippet=corrected,
                    advice="Asocie una etiqueta <label for='...'> visible con el identificador del campo de entrada.",
                    effort=EffortLevel.BAJO
                ),
                impact=ImpactLevel.ALTO,
                confidence=0.95
            )
            findings.append(finding)
            counter += 1

        # 5. Language check
        lang_data = candidates.get("language", {})
        declared_lang = lang_data.get("declared_lang")
        if not declared_lang:
            finding = Finding(
                id=f"IA-LNG-{counter:02d}",
                principle=Principle.UNDERSTANDABLE,
                criterion_id="3.1.1",
                criterion_title="Idioma de la página",
                level=WCAGLevel.A,
                category=Category.ADVERTENCIA,
                origin=FindingOrigin.IA,
                check_name="Atributo lang ausente en etiqueta <html>",
                w3c_technique="H57",
                selector="html",
                line_number=1,
                html_snippet="<html>",
                explanation="La etiqueta <html> no define el idioma del documento. Los sintetizadores de voz pronunciarán el texto con el acento predeterminado del sistema operativo.",
                remediation=Remediation(
                    before_snippet="<html>",
                    after_snippet='<html lang="es">',
                    advice="Declare el idioma primario del documento mediante el atributo lang='es' (o el código correspondiente).",
                    effort=EffortLevel.BAJO
                ),
                impact=ImpactLevel.ALTO,
                confidence=0.99
            )
            findings.append(finding)

        return findings

    async def _call_openai(self, candidates: Dict[str, Any], raw_html: str) -> List[Finding]:
        """Invoke OpenAI API with structured JSON output."""
        api_key = settings.openai_api_key
        model = settings.llm_model or "gpt-4o-mini"
        url = "https://api.openai.com/v1/chat/completions"

        payload = {
            "model": model,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": SEMANTIC_ANALYSIS_SYSTEM_PROMPT},
                {"role": "user", "content": f"Analiza los siguientes fragmentos de la página:\n{json.dumps(candidates, ensure_ascii=False)}"}
            ],
            "temperature": 0.1
        }

        async with httpx.AsyncClient(timeout=25.0) as client:
            resp = await client.post(url, headers={"Authorization": f"Bearer {api_key}"}, json=payload)
            resp.raise_for_status()
            data = resp.json()
            raw_content = data["choices"][0]["message"]["content"]
            parsed = json.loads(raw_content)
            return self._parse_llm_findings(parsed.get("findings", []), raw_html)

    async def _call_anthropic(self, candidates: Dict[str, Any], raw_html: str) -> List[Finding]:
        """Invoke Anthropic Claude API."""
        api_key = settings.anthropic_api_key
        model = settings.llm_model or "claude-3-5-sonnet-20241022"
        url = "https://api.anthropic.com/v1/messages"

        payload = {
            "model": model,
            "max_tokens": 2048,
            "system": SEMANTIC_ANALYSIS_SYSTEM_PROMPT,
            "messages": [
                {"role": "user", "content": f"Analiza los siguientes fragmentos de la página y devuelve JSON estricto:\n{json.dumps(candidates, ensure_ascii=False)}"}
            ],
            "temperature": 0.1
        }

        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

        async with httpx.AsyncClient(timeout=25.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            raw_content = data["content"][0]["text"]
            # Extract JSON block if wrapped in markdown
            match = re.search(r"\{.*\}", raw_content, re.DOTALL)
            parsed = json.loads(match.group(0) if match else raw_content)
            return self._parse_llm_findings(parsed.get("findings", []), raw_html)

    async def _call_gemini(self, candidates: Dict[str, Any], raw_html: str) -> List[Finding]:
        """Invoke Google Gemini API."""
        api_key = settings.gemini_api_key
        model = settings.llm_model or "gemini-1.5-flash"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

        prompt = f"{SEMANTIC_ANALYSIS_SYSTEM_PROMPT}\n\nFragmentos:\n{json.dumps(candidates, ensure_ascii=False)}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json"}
        }

        async with httpx.AsyncClient(timeout=25.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            raw_content = data["candidates"][0]["content"]["parts"][0]["text"]
            parsed = json.loads(raw_content)
            return self._parse_llm_findings(parsed.get("findings", []), raw_html)

    def _parse_llm_findings(self, raw_findings: List[Dict[str, Any]], raw_html: str) -> List[Finding]:
        """Validate and parse raw LLM output enforcing anti-hallucination rules."""
        validated: List[Finding] = []
        counter = 1

        for rf in raw_findings:
            snippet = rf.get("html_snippet", "")
            selector = rf.get("selector", "")
            line_no = find_line_number(raw_html, snippet, selector)

            # Anti-hallucination guard: If node cannot be grounded in raw HTML, reject it
            if line_no is None and snippet:
                continue

            remed_data = rf.get("remediation", {})
            remediation = Remediation(
                before_snippet=remed_data.get("before_snippet", snippet),
                after_snippet=remed_data.get("after_snippet", snippet),
                advice=remed_data.get("advice", "Corregir el elemento según las pautas WCAG."),
                effort=EffortLevel(remed_data.get("effort", "medio"))
            )

            # Strictly enforce Category.ADVERTENCIA for AI findings
            finding = Finding(
                id=f"IA-{counter:03d}",
                principle=criterion_meta["principle"],
                criterion_id=criterion_id,
                criterion_title=criterion_meta["title"],
                level=criterion_meta["level"],
                category=Category.ADVERTENCIA,  # Never Problema for AI
                origin=FindingOrigin.IA,
                check_name=rf.get("check_name", f"Juicio semántico {criterion_id}"),
                w3c_technique=rf.get("w3c_technique", criterion_meta.get("technique", "G94")),
                selector=selector or "html",
                line_number=line_no,
                html_snippet=snippet,
                explanation=rf.get("explanation", "Juicio semántico generado por IA."),
                remediation=remediation,
                impact=ImpactLevel(rf.get("impact", "medio")),
                confidence=float(rf.get("confidence", 0.85))
            )
            validated.append(finding)
            counter += 1

        return validated
