"""axe-core injection and automated rule evaluation."""

import json
from pathlib import Path
from typing import List, Dict, Any, Tuple
from bs4 import BeautifulSoup
from playwright.async_api import Page

from a11y_agent.models.schema import (
    Finding, Category, FindingOrigin, ImpactLevel, EffortLevel,
    Principle, WCAGLevel, GuidelinesVersion, Remediation
)
from a11y_agent.models.wcag_catalog import AXE_RULE_MAP, get_criterion_details
from a11y_agent.analyzer.line_locator import find_line_number

AXE_SCRIPT_PATH = Path(__file__).resolve().parent / "vendor" / "axe.min.js"

def get_axe_tags(guidelines: GuidelinesVersion, target_level: WCAGLevel) -> List[str]:
    """Map guidelines and level to corresponding axe-core tags cumulatively."""
    tags = ["wcag2a"]
    if target_level in (WCAGLevel.AA, WCAGLevel.AAA):
        tags.append("wcag2aa")
    if target_level == WCAGLevel.AAA:
        tags.append("wcag2aaa")

    if guidelines in (GuidelinesVersion.WCAG_2_1, GuidelinesVersion.WCAG_2_2):
        tags.append("wcag21a")
        if target_level in (WCAGLevel.AA, WCAGLevel.AAA):
            tags.append("wcag21aa")
        if target_level == WCAGLevel.AAA:
            tags.append("wcag21aaa")

    if guidelines == GuidelinesVersion.WCAG_2_2:
        if target_level in (WCAGLevel.AA, WCAGLevel.AAA):
            tags.append("wcag22aa")

    return list(set(tags))

def map_axe_impact(axe_impact: str) -> ImpactLevel:
    """Map axe impact strings to ImpactLevel enum."""
    mapping = {
        "critical": ImpactLevel.CRITICO,
        "serious": ImpactLevel.ALTO,
        "moderate": ImpactLevel.MEDIO,
        "minor": ImpactLevel.BAJO
    }
    return mapping.get((axe_impact or "").lower(), ImpactLevel.MEDIO)

def infer_wcag_criterion(rule_id: str, tags: List[str]) -> Tuple[str, str, str]:
    """
    Given an axe rule ID and its tags, resolve (criterion_id, technique, check_name).
    """
    if rule_id in AXE_RULE_MAP:
        mapping = AXE_RULE_MAP[rule_id]
        return mapping["criterion"], mapping["technique"], mapping["check_name"]

    # Try to infer criterion from tags (e.g., 'wcag111' -> '1.1.1', 'wcag143' -> '1.4.3')
    for tag in tags:
        if tag.startswith("wcag") and len(tag) == 7 and tag[4:].isdigit():
            c_digits = tag[4:]
            c_id = f"{c_digits[0]}.{c_digits[1]}.{c_digits[2]}"
            details = get_criterion_details(c_id)
            return c_id, details.get("technique", "G94"), details.get("title", f"Criterio {c_id}")

    # Fallback to general criteria
    return "4.1.2", "ARIA5", f"Comprobación {rule_id}"

def generate_heuristic_remediation(rule_id: str, snippet: str, failure_summary: str) -> Remediation:
    """Produce immediate deterministic remediation guidance before or alongside LLM advice."""
    before = snippet.strip()
    after = before
    advice = failure_summary or "Modificar el elemento para cumplir con la pauta WCAG."
    effort = EffortLevel.MEDIO

    if rule_id == "image-alt":
        effort = EffortLevel.BAJO
        if "alt=" not in before:
            after = before.replace("<img", '<img alt="Descripción clara de la imagen"')
        else:
            after = before.replace('alt=""', 'alt="Descripción clara de la imagen"')
        advice = "Agregue un atributo alt con una descripción funcional y precisa de la imagen."

    elif rule_id == "color-contrast":
        effort = EffortLevel.MEDIO
        advice = "Ajuste el color de texto o fondo para alcanzar un contraste mínimo de 4.5:1 (o 3:1 para texto mayor a 18pt/24px)."

    elif rule_id == "label":
        effort = EffortLevel.BAJO
        after = f'<label for="campo-id">Etiqueta descriptiva:</label>\n{before}'
        advice = "Asocie un elemento <label for='...'> con el id del campo o use aria-label."

    elif rule_id == "link-name":
        effort = EffortLevel.BAJO
        after = before.replace("></a>", ">Descripción del enlace</a>").replace(">click aquí<", ">nombre del recurso destino<")
        advice = "Proporcione un texto de enlace claro que explique a dónde dirige fuera de contexto."

    elif rule_id in ("html-has-lang", "html-lang-valid"):
        effort = EffortLevel.BAJO
        after = '<html lang="es">'
        advice = "Declare el idioma principal del documento usando el atributo lang (ej. lang='es')."

    return Remediation(
        before_snippet=before,
        after_snippet=after,
        advice=advice,
        effort=effort
    )

async def run_axe_core(
    page: Page,
    raw_html: str,
    guidelines: GuidelinesVersion = GuidelinesVersion.WCAG_2_1,
    target_level: WCAGLevel = WCAGLevel.AA
) -> List[Finding]:
    """
    Inject axe-core into the Playwright page, execute against the requested WCAG level,
    and parse the output into standardized Finding models. Handles WCAG 2.2 obsolete rules.
    """
    if not AXE_SCRIPT_PATH.exists():
        raise FileNotFoundError(f"No se encontró el script de axe-core en {AXE_SCRIPT_PATH}")

    axe_script = AXE_SCRIPT_PATH.read_text(encoding="utf-8")
    tags = get_axe_tags(guidelines, target_level)

    # Inject and run axe
    await page.evaluate(axe_script)
    axe_options = {
        "runOnly": {
            "type": "tag",
            "values": tags
        }
    }

    axe_results_raw = await page.evaluate(
        """(options) => {
            return axe.run(document, options);
        }""",
        axe_options
    )

    findings: List[Finding] = []
    finding_counter = 1

    # Process Violations (Categoría: Problema)
    for v in axe_results_raw.get("violations", []):
        rule_id = v.get("id", "rule")
        rule_tags = v.get("tags", [])
        criterion_id, technique, check_name = infer_wcag_criterion(rule_id, rule_tags)

        # En WCAG 2.2, el criterio 4.1.1 (Parsing) fue eliminado por obsoleto por el W3C
        if guidelines == GuidelinesVersion.WCAG_2_2 and (rule_id == "parsing" or criterion_id == "4.1.1"):
            continue

        criterion_meta = get_criterion_details(criterion_id)
        impact = map_axe_impact(v.get("impact", "moderate"))

        for node in v.get("nodes", []):
            snippet = node.get("html", "")
            target_selectors = node.get("target", [])
            selector = " > ".join(target_selectors) if isinstance(target_selectors, list) else str(target_selectors)
            line_no = find_line_number(raw_html, snippet, selector)
            summary = node.get("failureSummary", v.get("description", ""))

            remediation = generate_heuristic_remediation(rule_id, snippet, summary)

            finding = Finding(
                id=f"P-{finding_counter:03d}",
                principle=criterion_meta["principle"],
                criterion_id=criterion_id,
                criterion_title=criterion_meta["title"],
                level=criterion_meta["level"],
                category=Category.PROBLEMA,
                origin=FindingOrigin.REGLA,
                check_name=check_name,
                w3c_technique=technique,
                selector=selector or "html",
                line_number=line_no,
                html_snippet=snippet,
                explanation=v.get("help", v.get("description", "Incidencia detectada por regla automática.")),
                remediation=remediation,
                impact=impact,
                confidence=1.0
            )
            findings.append(finding)
            finding_counter += 1

    # Axe incomplete results need human review; they are not confirmed violations.
    for inc in axe_results_raw.get("incomplete", []):
        rule_id = inc.get("id", "rule")
        rule_tags = inc.get("tags", [])
        criterion_id, technique, check_name = infer_wcag_criterion(rule_id, rule_tags)

        if guidelines == GuidelinesVersion.WCAG_2_2 and (rule_id == "parsing" or criterion_id == "4.1.1"):
            continue

        criterion_meta = get_criterion_details(criterion_id)
        impact = map_axe_impact(inc.get("impact", "minor"))

        for node in inc.get("nodes", []):
            snippet = node.get("html", "")
            target_selectors = node.get("target", [])
            selector = " > ".join(target_selectors) if isinstance(target_selectors, list) else str(target_selectors)
            line_no = find_line_number(raw_html, snippet, selector)

            remediation = generate_heuristic_remediation(rule_id, snippet, inc.get("help", ""))

            finding = Finding(
                id=f"NV-{finding_counter:03d}",
                principle=criterion_meta["principle"],
                criterion_id=criterion_id,
                criterion_title=criterion_meta["title"],
                level=criterion_meta["level"],
                category=Category.NO_VERIFICADO,
                origin=FindingOrigin.REGLA,
                check_name=f"[Revisión requerida] {check_name}",
                w3c_technique=technique,
                selector=selector or "html",
                line_number=line_no,
                html_snippet=snippet,
                explanation=f"Axe-core no pudo determinar automáticamente el resultado: {inc.get('help', '')}. Requiere verificación manual.",
                remediation=remediation,
                impact=impact,
                confidence=0.75
            )
            findings.append(finding)
            finding_counter += 1

    # Only request a caption review when the page actually contains a video.
    if BeautifulSoup(raw_html, "html.parser").find("video"):
        findings.append(Finding(
            id=f"NV-{finding_counter:03d}",
            principle=Principle.PERCEPTIBLE,
            criterion_id="1.2.2",
            criterion_title="Subtítulos (pregrabados)",
            level=WCAGLevel.A,
            category=Category.NO_VERIFICADO,
            origin=FindingOrigin.REGLA,
            check_name="Verificación de subtítulos en medios sincronizados",
            w3c_technique="G87",
            selector="video",
            line_number=find_line_number(raw_html, "<video", "video"),
            html_snippet="<video> ... </video>",
            explanation="La presencia de video requiere revisar manualmente si contiene audio sincronizado y subtítulos exactos.",
            remediation=Remediation(
                before_snippet="<video src='video.mp4'></video>",
                after_snippet="<video src='video.mp4'><track kind='captions' src='sub.vtt' srclang='es' label='Español'></video>",
                advice="Revise el contenido del video y proporcione subtítulos sincronizados cuando haya audio hablado.",
                effort=EffortLevel.MEDIO
            ),
            impact=ImpactLevel.MEDIO,
            confidence=0.5
        ))

    return findings
