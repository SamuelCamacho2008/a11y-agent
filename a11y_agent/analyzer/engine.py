"""Main accessibility audit orchestration engine."""

import time
import secrets
from pathlib import Path
from typing import Optional, List

from a11y_agent.core.config import settings
from a11y_agent.models.schema import (
    A11yReport, GuidelinesVersion, WCAGLevel
)
from a11y_agent.crawler.browser import get_browser_page
from a11y_agent.crawler.fetcher import fetch_and_render_page
from a11y_agent.analyzer.axe_runner import run_axe_core
from a11y_agent.analyzer.semantic_extractor import extract_semantic_candidates
from a11y_agent.analyzer.llm_client import LLMAnalyzer
from a11y_agent.analyzer.scorer import build_a11y_report
from a11y_agent.reporters.html_reporter import export_to_html
from a11y_agent.reporters.json_reporter import export_to_json
from a11y_agent.reporters.pdf_reporter import export_to_pdf

class A11yEngine:
    """Orchestrates the entire accessibility audit pipeline."""

    def __init__(self):
        self.llm_analyzer = LLMAnalyzer()

    async def run_audit(
        self,
        url: str,
        guidelines: GuidelinesVersion = GuidelinesVersion.WCAG_2_1,
        target_level: WCAGLevel = WCAGLevel.AA,
        allow_private_ips: bool = False,
        dismiss_cookies: bool = False,
        export_formats: Optional[List[str]] = None,
        base_public_url: Optional[str] = None
    ) -> A11yReport:
        """
        Execute full pipeline:
        1. SSRF & network checks
        2. Dynamic render & screenshot via Playwright
        3. Automated rules via axe-core
        4. Semantic checks via LLM
        5. Consolidation, scoring, and report generation
        6. Optional export to HTML/JSON/PDF
        """
        start_time = time.time()
        # Cryptographically strong, non-enumerable 32-character hexadecimal token
        report_id = f"rep_{secrets.token_hex(16)}"
        public_url = f"{base_public_url.rstrip('/')}/view/{report_id}" if base_public_url else f"/view/{report_id}"

        async with get_browser_page() as page:
            # 1 & 2: Fetch and render dynamically
            crawl_res = await fetch_and_render_page(
                url=url,
                report_id=report_id,
                allow_private_ips=allow_private_ips,
                page_instance=page,
                dismiss_cookies=dismiss_cookies
            )

            # 3: Run axe-core automated rules on the live page
            rule_findings = await run_axe_core(
                page=page,
                raw_html=crawl_res.rendered_dom,
                guidelines=guidelines,
                target_level=target_level
            )

            # 4: Extract candidates and run LLM semantic judgment
            candidates = extract_semantic_candidates(crawl_res.rendered_dom)
            ia_findings = await self.llm_analyzer.analyze_semantics(
                candidates=candidates,
                raw_html=crawl_res.rendered_dom,
                target_level=target_level
            )

            # 5: Combine, deduplicate, score, and group by principles
            all_raw_findings = rule_findings + ia_findings
            execution_time = round(time.time() - start_time, 2)

            report = build_a11y_report(
                report_id=report_id,
                url=crawl_res.url,
                findings=all_raw_findings,
                guidelines=guidelines,
                target_level=target_level,
                technologies=crawl_res.technologies,
                execution_time_seconds=execution_time,
                screenshot_path=crawl_res.screenshot_path,
                target_type="web",
                public_url=public_url
            )

            # 6: Export formats if requested
            formats = export_formats or ["html", "json"]
            if "html" in formats:
                html_path = settings.reports_dir / f"{report_id}.html"
                export_to_html(report, html_path)
            if "json" in formats:
                json_path = settings.reports_dir / f"{report_id}.json"
                export_to_json(report, json_path)
            if "pdf" in formats:
                pdf_path = settings.reports_dir / f"{report_id}.pdf"
                await export_to_pdf(report, pdf_path)

            # 7: Publish to GitHub Pages docs structure
            if settings.github_pages_enabled:
                from a11y_agent.reporters.git_publisher import publish_report_to_docs
                publish_report_to_docs(report)

            return report
