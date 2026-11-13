"""Consolidation, deduplication, scoring, and report building."""

from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict
import uuid

from a11y_agent.models.schema import (
    Finding, Category, FindingOrigin, ImpactLevel, Principle, WCAGLevel,
    GuidelinesVersion, SuccessCriterionGroup, PrincipleFindings,
    ReportMetadata, ReportSummary, A11yReport
)
from a11y_agent.models.wcag_catalog import PRINCIPLES_META, get_criterion_details
from a11y_agent.core.config import settings

def deduplicate_findings(findings: List[Finding]) -> List[Finding]:
    """
    Deduplicate findings where rule engine and IA flagged the same node and criterion.
    Priority is given to deterministic rule category, enriched with IA remediation advice.
    """
    seen: Dict[Tuple[str, str], Finding] = {}

    for f in findings:
        key = (f.criterion_id, f.selector)
        if key in seen:
            existing = seen[key]
            # If current finding is IA and existing is rule, enrich existing remediation
            if f.origin == FindingOrigin.IA and existing.origin == FindingOrigin.REGLA:
                if f.remediation and (not existing.remediation or len(f.remediation.advice) > len(existing.remediation.advice)):
                    existing.remediation = f.remediation
                existing.explanation = f"{existing.explanation} | Nota IA: {f.explanation}"
            # If current is rule and existing is IA, promote to rule problem
            elif f.origin == FindingOrigin.REGLA and existing.origin == FindingOrigin.IA:
                f.remediation = existing.remediation or f.remediation
                seen[key] = f
        else:
            seen[key] = f

    return list(seen.values())

def calculate_score(findings: List[Finding]) -> Tuple[int, Dict[str, int]]:
    """
    Calculate an internal heuristic indicator (0-100), not a conformance percentage.
    Returns (score, impact_breakdown).
    """
    score = 100.0
    impact_counts = {
        "crítico": 0,
        "alto": 0,
        "medio": 0,
        "bajo": 0
    }

    penalty_map = {
        # Category.PROBLEMA
        (Category.PROBLEMA, ImpactLevel.CRITICO): 15.0,
        (Category.PROBLEMA, ImpactLevel.ALTO): 10.0,
        (Category.PROBLEMA, ImpactLevel.MEDIO): 5.0,
        (Category.PROBLEMA, ImpactLevel.BAJO): 2.0,
        # Category.ADVERTENCIA
        (Category.ADVERTENCIA, ImpactLevel.CRITICO): 5.0,
        (Category.ADVERTENCIA, ImpactLevel.ALTO): 3.0,
        (Category.ADVERTENCIA, ImpactLevel.MEDIO): 1.5,
        (Category.ADVERTENCIA, ImpactLevel.BAJO): 0.5,
        # Category.NO_VERIFICADO
        (Category.NO_VERIFICADO, ImpactLevel.CRITICO): 1.0,
        (Category.NO_VERIFICADO, ImpactLevel.ALTO): 0.5,
        (Category.NO_VERIFICADO, ImpactLevel.MEDIO): 0.2,
        (Category.NO_VERIFICADO, ImpactLevel.BAJO): 0.5,
    }

    for f in findings:
        impact_counts[f.impact.value] = impact_counts.get(f.impact.value, 0) + 1
        penalty = penalty_map.get((f.category, f.impact), 2.0)
        score -= penalty

    final_score = max(0, min(100, int(score)))
    return final_score, impact_counts

def generate_executive_summary(
    score: int,
    total_problems: int,
    total_warnings: int,
    target_level: WCAGLevel,
    impact_counts: Dict[str, int],
    target_type: str = "web",
    target_name: str = ""
) -> str:
    """Generate concise 5-line executive summary of the accessibility audit."""
    level_status = "satisfactorio" if score >= 85 and total_problems == 0 else "con barreras significativas"
    entity = "La aplicación móvil Android" if target_type == "apk" else "La página"
    name_clause = f" ({target_name})" if target_name and target_type == "apk" else ""
    line1 = f"1. Estado General: {entity}{name_clause} obtiene un indicador interno del agente de {score}/100, evaluada bajo nivel {target_level.value} ({level_status}). No equivale a una certificación ni al puntaje de TAW."
    line2 = f"2. Barreras Críticas: Se detectaron {total_problems} problemas deterministas y {total_warnings} advertencias que requieren revisión experta."
    line3 = f"3. Distribución de Impacto: {impact_counts.get('crítico', 0)} hallazgos de impacto crítico y {impact_counts.get('alto', 0)} de impacto alto requieren priorización."
    line4 = f"4. Conformidad Semántica: Las principales oportunidades de mejora se concentran en etiquetado accesible, contraste y adaptabilidad para tecnologías de asistencia."
    line5 = f"5. Plan de Acción: Se recomienda priorizar los fallos clasificados como Problemas Críticos aplicando las soluciones de código antes/después incluidas en este informe."
    return "\n".join([line1, line2, line3, line4, line5])

def build_a11y_report(
    report_id: str,
    url: str,
    findings: List[Finding],
    guidelines: GuidelinesVersion = GuidelinesVersion.WCAG_2_1,
    target_level: WCAGLevel = WCAGLevel.AA,
    technologies: List[str] = None,
    execution_time_seconds: float = 0.0,
    screenshot_path: str = None,
    target_type: str = "web",
    app_name: Optional[str] = None,
    package_name: Optional[str] = None,
    public_url: Optional[str] = None,
    github_pages_url: Optional[str] = None
) -> A11yReport:
    """
    Consolidate findings, structure by the 4 Principles & Criteria, and produce final A11yReport.
    """
    gh_url = github_pages_url or (f"{settings.github_pages_base_url}/reports/{report_id}.html" if settings.github_pages_enabled else None)
    effective_public_url = public_url or gh_url
    deduped = deduplicate_findings(findings)
    score, impact_counts = calculate_score(deduped)

    total_problems = sum(1 for f in deduped if f.category == Category.PROBLEMA)
    total_warnings = sum(1 for f in deduped if f.category == Category.ADVERTENCIA)
    total_unverified = sum(1 for f in deduped if f.category == Category.NO_VERIFICADO)

    target_display = app_name or package_name or url
    exec_summary = generate_executive_summary(
        score=score,
        total_problems=total_problems,
        total_warnings=total_warnings,
        target_level=target_level,
        impact_counts=impact_counts,
        target_type=target_type,
        target_name=target_display
    )

    # Group by Principle and Success Criterion
    principles_dict: Dict[str, PrincipleFindings] = {}

    for principle_enum in [Principle.PERCEPTIBLE, Principle.OPERABLE, Principle.UNDERSTANDABLE, Principle.ROBUST]:
        meta = PRINCIPLES_META[principle_enum]
        principle_findings = [f for f in deduped if f.principle == principle_enum]

        # Group by criterion_id
        criterion_groups_map: Dict[str, List[Finding]] = defaultdict(list)
        for f in principle_findings:
            criterion_groups_map[f.criterion_id].append(f)

        groups_list: List[SuccessCriterionGroup] = []
        for c_id, c_findings in sorted(criterion_groups_map.items()):
            c_meta = get_criterion_details(c_id)
            groups_list.append(
                SuccessCriterionGroup(
                    criterion_id=c_id,
                    criterion_title=c_meta["title"],
                    level=c_meta["level"],
                    findings=c_findings
                )
            )

        principles_dict[principle_enum.value] = PrincipleFindings(
            key=principle_enum,
            name=meta["name"],
            description=meta["description"],
            success_criteria=groups_list
        )

    metadata = ReportMetadata(
        url=url,
        target_type="apk" if target_type == "apk" else "web",
        app_name=app_name,
        package_name=package_name,
        public_url=effective_public_url,
        github_pages_url=gh_url,
        guidelines=guidelines,
        target_level=target_level,
        technologies=technologies or (["Android APK", "XML Layouts"] if target_type == "apk" else ["HTML5", "CSS3", "JavaScript"]),
        execution_time_seconds=execution_time_seconds,
        screenshot_path=screenshot_path
    )

    summary = ReportSummary(
        score=score,
        executive_summary=exec_summary,
        total_problems=total_problems,
        total_warnings=total_warnings,
        total_unverified=total_unverified,
        impact_breakdown=impact_counts
    )

    return A11yReport(
        id=report_id,
        target_type="apk" if target_type == "apk" else "web",
        app_name=app_name,
        package_name=package_name,
        public_url=effective_public_url,
        github_pages_url=gh_url,
        metadata=metadata,
        summary=summary,
        principles=principles_dict,
        all_findings=deduped
    )
