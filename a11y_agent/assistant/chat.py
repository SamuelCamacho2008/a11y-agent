"""Interactive accessibility remediation chat assistant."""

import re
from typing import Optional, List, Dict
import httpx

from a11y_agent.core.config import settings
from a11y_agent.models.schema import A11yReport, Finding, ChatMessage, ChatResponse

CHAT_SYSTEM_PROMPT = """Eres el asistente de remediación de A11y Agent.
Tu objetivo es ayudar al usuario a entender y corregir las barreras de accesibilidad detectadas en el informe.
Instrucciones:
1. Explica el impacto en usuarios con discapacidad en lenguaje comprensible y empático.
2. Proporciona soluciones de código concretas (HTML, CSS o WAI-ARIA) listas para copiar y pegar.
3. Cita la técnica W3C aplicable.
4. Mantén las respuestas estructuradas y concisas.
"""

class A11yChatAssistant:
    """Provides conversational remediation guidance based on audit findings."""

    def __init__(self, report: A11yReport):
        self.report = report

    def find_referenced_finding(self, query: str) -> Optional[Finding]:
        """
        Locates the finding being queried (e.g. "problema 3", "hallazgo 1", "P-002", "IA-01", "imagen").
        """
        query_lower = query.lower()

        # Check for explicit ID match
        for f in self.report.all_findings:
            if f.id.lower() in query_lower:
                return f

        # Check for numeric reference e.g., "problema 3" or "#3" or "el 3"
        num_match = re.search(r'(?:problema|hallazgo|incidencia|número|num|#)\s*(\d+)', query_lower)
        if not num_match:
            num_match = re.search(r'\b(\d+)\b', query_lower)

        if num_match:
            idx = int(num_match.group(1)) - 1
            if 0 <= idx < len(self.report.all_findings):
                return self.report.all_findings[idx]

        # Check for keyword matches (imagen, alt, contraste, link, enlace, label)
        if "imagen" in query_lower or "alt" in query_lower:
            for f in self.report.all_findings:
                if f.criterion_id == "1.1.1":
                    return f

        if "contraste" in query_lower or "color" in query_lower:
            for f in self.report.all_findings:
                if f.criterion_id in ("1.4.3", "1.4.11"):
                    return f

        if "enlace" in query_lower or "link" in query_lower:
            for f in self.report.all_findings:
                if f.criterion_id == "2.4.4":
                    return f

        if "formulario" in query_lower or "label" in query_lower or "etiqueta" in query_lower:
            for f in self.report.all_findings:
                if f.criterion_id in ("3.3.2", "4.1.2"):
                    return f

        return None

    async def answer_question(self, user_message: str, history: List[ChatMessage] = None) -> ChatResponse:
        """Generate remediation guidance for the user's question."""
        target_finding = self.find_referenced_finding(user_message)
        referenced_ids = [target_finding.id] if target_finding else []

        # If LLM key is configured, use LLM with context
        if settings.openai_api_key or settings.anthropic_api_key or settings.gemini_api_key:
            try:
                return await self._answer_with_llm(user_message, target_finding, history)
            except Exception:
                pass  # Fall back to heuristic answer

        return self._answer_heuristic(user_message, target_finding)

    def _answer_heuristic(self, query: str, finding: Optional[Finding]) -> ChatResponse:
        """Deterministic expert advice generation."""
        if finding:
            rem = finding.remediation
            advice = rem.advice if rem else "Ajuste el código para cumplir con WCAG."
            before = rem.before_snippet if rem else finding.html_snippet
            after = rem.after_snippet if rem else finding.html_snippet

            reply = (
                f"### Solución para {finding.id}: {finding.check_name} (WCAG {finding.criterion_id})\n\n"
                f"**¿Por qué es un problema?**\n"
                f"{finding.explanation}\n\n"
                f"**Cómo solucionarlo (Esfuerzo: {rem.effort.value if rem else 'medio'}):**\n"
                f"{advice}\n\n"
                f"**Código Actual:**\n"
                f"```html\n{before}\n```\n\n"
                f"**Código Corregido Recomendado:**\n"
                f"```html\n{after}\n```\n\n"
                f"*Técnica W3C recomendada: {finding.w3c_technique}*."
            )
            return ChatResponse(reply=reply, referenced_findings=[finding.id])

        # General inquiry
        reply = (
            f"He revisado el informe de la página ({self.report.metadata.url}). "
            f"Se encontraron un total de {self.report.summary.total_problems} problemas deterministas y "
            f"{self.report.summary.total_warnings} advertencias.\n\n"
            f"Puedes preguntarme sobre cualquier hallazgo específico (por ejemplo: *'¿Cómo soluciono el problema 1?'* "
            f"o *'¿Cómo arreglo el contraste del texto?'*)."
        )
        return ChatResponse(reply=reply, referenced_findings=[])

    async def _answer_with_llm(
        self,
        query: str,
        finding: Optional[Finding],
        history: List[ChatMessage] = None
    ) -> ChatResponse:
        """Call external LLM for conversational advice."""
        context = f"Informe de URL: {self.report.metadata.url}\nPuntaje: {self.report.summary.score}/100\n"
        if finding:
            context += (
                f"Hallazgo en consulta: ID={finding.id}, Criterio={finding.criterion_id} ({finding.criterion_title}), "
                f"Elemento={finding.selector}, Snippet={finding.html_snippet}, Explicación={finding.explanation}\n"
            )
            if finding.remediation:
                context += f"Solución previa sugerida: {finding.remediation.advice}\n"

        prompt = f"Contexto de la auditoría:\n{context}\n\nPregunta del usuario: {query}"

        # Standard OpenAI call
        if settings.openai_api_key:
            async with httpx.AsyncClient(timeout=20.0) as client:
                res = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                    json={
                        "model": settings.llm_model or "gpt-4o-mini",
                        "messages": [
                            {"role": "system", "content": CHAT_SYSTEM_PROMPT},
                            {"role": "user", "content": prompt}
                        ]
                    }
                )
                res.raise_for_status()
                text = res.json()["choices"][0]["message"]["content"]
                return ChatResponse(reply=text, referenced_findings=[finding.id] if finding else [])

        return self._answer_heuristic(query, finding)
