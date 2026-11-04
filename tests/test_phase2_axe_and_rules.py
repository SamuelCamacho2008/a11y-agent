"""Unit tests for Phase 2: axe-core runner, line locator, and WCAG rules mapping."""

import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock
from playwright.async_api import async_playwright
from a11y_agent.analyzer.line_locator import find_line_number
from a11y_agent.analyzer.axe_runner import get_axe_tags, run_axe_core
from a11y_agent.models.schema import GuidelinesVersion, WCAGLevel, Category, Principle

def test_line_locator():
    raw_html = (
        "<!DOCTYPE html>\n"
        "<html>\n"
        "<head><title>Test</title></head>\n"
        "<body>\n"
        '    <h1 id="main-heading">Título</h1>\n'
        '    <img src="logo.png">\n'
        '    <button class="btn-action">Enviar</button>\n'
        "</body>\n"
        "</html>"
    )

    line_img = find_line_number(raw_html, '<img src="logo.png">')
    assert line_img == 6

    line_btn = find_line_number(raw_html, '<button class="btn-action">Enviar</button>')
    assert line_btn == 7

    line_h1 = find_line_number(raw_html, "", selector="h1#main-heading")
    assert line_h1 == 5

def test_get_axe_tags():
    tags_20_a = get_axe_tags(GuidelinesVersion.WCAG_2_0, WCAGLevel.A)
    assert "wcag2a" in tags_20_a
    assert "wcag2aa" not in tags_20_a

    tags_21_aa = get_axe_tags(GuidelinesVersion.WCAG_2_1, WCAGLevel.AA)
    assert "wcag2a" in tags_21_aa
    assert "wcag2aa" in tags_21_aa
    assert "wcag21a" in tags_21_aa
    assert "wcag21aa" in tags_21_aa

    tags_22_aa = get_axe_tags(GuidelinesVersion.WCAG_2_2, WCAGLevel.AA)
    assert "wcag22aa" in tags_22_aa

@pytest.mark.asyncio
async def test_axe_runner_execution():
    test_html = """
    <!DOCTYPE html>
    <html>
    <head><title>Inaccessible Page</title></head>
    <body>
        <!-- Missing alt attribute: 1.1.1 (Level A) -->
        <img id="bad-image" src="banner.jpg">
        <!-- Low contrast: 1.4.3 (Level AA) -->
        <p style="color: #ccc; background-color: #fff;">Texto ilegible con bajo contraste</p>
        <!-- Form field without label: 3.3.2 (Level A) -->
        <input type="text" id="email-field">
    </body>
    </html>
    """
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_content(test_html)

        findings = await run_axe_core(
            page=page,
            raw_html=test_html,
            guidelines=GuidelinesVersion.WCAG_2_1,
            target_level=WCAGLevel.AA
        )
        await browser.close()

    assert len(findings) >= 3

    # Check that image without alt is detected as Problema in Perceptible
    img_finding = next((f for f in findings if f.criterion_id == "1.1.1"), None)
    assert img_finding is not None
    assert img_finding.category == Category.PROBLEMA
    assert img_finding.principle == Principle.PERCEPTIBLE
    assert img_finding.line_number == 7
    assert img_finding.remediation is not None
    assert 'alt=' in img_finding.remediation.after_snippet

    # Check label finding
    label_finding = next((f for f in findings if f.criterion_id == "3.3.2"), None)
    assert label_finding is not None
    assert label_finding.category == Category.PROBLEMA
    assert label_finding.principle == Principle.UNDERSTANDABLE

@pytest.mark.asyncio
async def test_axe_incomplete_is_unverified_and_caption_check_requires_video():
    axe_results = {
        "violations": [],
        "incomplete": [{
            "id": "color-contrast",
            "tags": ["wcag2aa", "wcag143"],
            "impact": "moderate",
            "help": "Elements must meet minimum color contrast ratio thresholds",
            "nodes": [{
                "html": "<p>Texto</p>",
                "target": ["p"],
                "failureSummary": "Review the contrast."
            }]
        }]
    }

    page_without_video = SimpleNamespace(
        evaluate=AsyncMock(side_effect=[None, axe_results])
    )
    findings = await run_axe_core(
        page=page_without_video,
        raw_html="<html><body><p>Texto</p></body></html>",
        guidelines=GuidelinesVersion.WCAG_2_1,
        target_level=WCAGLevel.AA
    )

    contrast_finding = next(f for f in findings if f.criterion_id == "1.4.3")
    assert contrast_finding.category == Category.NO_VERIFICADO
    assert not any(f.criterion_id == "1.2.2" for f in findings)

    page_with_video = SimpleNamespace(
        evaluate=AsyncMock(side_effect=[None, {"violations": [], "incomplete": []}])
    )
    findings_with_video = await run_axe_core(
        page=page_with_video,
        raw_html="<html><body><video src='clip.mp4'></video></body></html>",
        guidelines=GuidelinesVersion.WCAG_2_1,
        target_level=WCAGLevel.AA
    )
    caption_finding = next(f for f in findings_with_video if f.criterion_id == "1.2.2")
    assert caption_finding.category == Category.NO_VERIFICADO
