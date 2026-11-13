"""Lightweight client-side technology stack detector."""

import re
from typing import List, Dict, Any
from bs4 import BeautifulSoup

def detect_technologies(html_content: str, headers: Dict[str, str] = None) -> List[str]:
    """
    Detect web frameworks, CMSs, libraries, and UI technologies present in the page.
    """
    detected = set()
    headers = headers or {}
    lower_html = html_content.lower()

    # Always include HTML5 as baseline web technology
    detected.add("HTML5")

    # Server / Header checks
    server = headers.get("server", "").lower()
    x_powered_by = headers.get("x-powered-by", "").lower()
    if "apache" in server:
        detected.add("Apache")
    if "nginx" in server:
        detected.add("Nginx")
    if "cloudflare" in server:
        detected.add("Cloudflare")
    if "php" in x_powered_by or ".php" in lower_html:
        detected.add("PHP")
    if "asp.net" in x_powered_by:
        detected.add("ASP.NET")

    # Frameworks & Libraries via DOM / HTML markers
    if "__next" in lower_html or "/_next/" in lower_html:
        detected.add("Next.js")
        detected.add("React")
    elif "react" in lower_html or "data-reactroot" in lower_html:
        detected.add("React")

    if "__nuxt" in lower_html or "/_nuxt/" in lower_html:
        detected.add("Nuxt.js")
        detected.add("Vue.js")
    elif "data-v-" in lower_html or "vue" in lower_html:
        detected.add("Vue.js")

    if "ng-version" in lower_html or re.search(r'\bng-(?:app|model|controller|bind)\b', lower_html):
        detected.add("Angular")

    if "svelte" in lower_html:
        detected.add("Svelte")

    if "jquery" in lower_html:
        detected.add("jQuery")

    if "wp-content" in lower_html or "wp-includes" in lower_html:
        detected.add("WordPress")

    if "bootstrap" in lower_html:
        detected.add("Bootstrap")

    if "tailwind" in lower_html or "tw-" in lower_html or re.search(r'class="[^"]*(?:flex|grid|p-\d|m-\d|text-[a-z]+-\d+)[^"]*"', html_content):
        detected.add("Tailwind CSS")

    # ARIA / Accessibility features
    if "role=" in lower_html or "aria-" in lower_html:
        detected.add("WAI-ARIA")

    if "<svg" in lower_html:
        detected.add("SVG")

    if "<canvas" in lower_html:
        detected.add("HTML5 Canvas")

    # Meta generator
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        generator = soup.find("meta", attrs={"name": re.compile(r"^generator$", re.I)})
        if generator and generator.get("content"):
            detected.add(generator.get("content"))
    except Exception:
        pass

    return sorted(list(detected)) if detected else ["HTML5", "CSS3", "JavaScript"]
