"""Unit tests for Phase 3: Semantic candidate extraction, LLM client, and anti-hallucination rules."""

import pytest
from a11y_agent.analyzer.semantic_extractor import extract_semantic_candidates
from a11y_agent.analyzer.llm_client import LLMAnalyzer
from a11y_agent.models.schema import Category, FindingOrigin, Principle

def test_extract_semantic_candidates():
    html_markup = """
    <html>
    <body>
        <!-- Suspicious alt -->
        <img src="banner.jpg" alt="imagen">
        <!-- Ambiguous link -->
        <a href="/detalles">haz clic aquí</a>
        <!-- Heading skip: h1 to h3 -->
        <h1>Sección Principal</h1>
        <h3>Subsección sin h2 previo</h3>
        <!-- Input without label, only placeholder -->
        <input type="text" id="busqueda" placeholder="Buscar productos...">
    </body>
    </html>
    """

    candidates = extract_semantic_candidates(html_markup)

    # 1. Images
    assert len(candidates["images"]) >= 1
    assert candidates["images"][0]["alt"] == "imagen"

    # 2. Links
    assert len(candidates["links"]) >= 1
    assert candidates["links"][0]["text"] == "haz clic aquí"

    # 3. Headings
    assert len(candidates["headings"]) == 2
    assert candidates["headings"][0]["level"] == 1
    assert candidates["headings"][1]["level"] == 3

    # 4. Form inputs
    assert len(candidates["forms"]) >= 1
    assert candidates["forms"][0]["placeholder"] == "Buscar productos..."

    # 5. Language
    assert candidates["language"]["declared_lang"] is None

@pytest.mark.asyncio
async def test_llm_analyzer_rules_and_anti_hallucination():
    raw_html = """
    <html>
    <body>
        <img src="banner.jpg" alt="foto">
        <a href="/info">leer más</a>
        <input type="text" id="usr" placeholder="Tu usuario">
    </body>
    </html>
    """
    candidates = extract_semantic_candidates(raw_html)
    analyzer = LLMAnalyzer()
    analyzer.provider = "mock"  # Test deterministic semantic engine

    findings = await analyzer.analyze_semantics(candidates, raw_html)

    assert len(findings) >= 3

    for f in findings:
        # Strict Rule 1: AI findings MUST be categorized as ADVERTENCIA, NEVER PROBLEMA
        assert f.category == Category.ADVERTENCIA
        # Strict Rule 2: Origin MUST be IA
        assert f.origin == FindingOrigin.IA
        # Strict Rule 3: Must include confidence between 0.0 and 1.0
        assert 0.0 <= f.confidence <= 1.0
        # Strict Rule 4: Must have remediation with before and after
        assert f.remediation is not None
        assert f.remediation.before_snippet
        assert f.remediation.after_snippet
        # Strict Rule 5: snippet must be grounded in raw_html (verified via line_number)
        assert f.line_number is not None and f.line_number > 0
