"""Extracts targeted HTML snippets for semantic evaluation by the LLM."""

import re
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup

SUSPICIOUS_ALT_PATTERNS = [
    r"^imagen$", r"^foto$", r"^image$", r"^picture$", r"^photo$",
    r"^banner$", r"^logo$", r"^grafico$", r"^graphic$", r"^placeholder$",
    r"\.(jpg|jpeg|png|gif|webp|svg)$", r"^dsc_\d+", r"^img_\d+", r"^screenshot"
]

AMBIGUOUS_LINK_TEXTS = {
    "clic aquí", "haz clic aquí", "click aquí", "click here", "leer más", "read more",
    "más", "ver más", "aquí", "here", "más información", "more info", "descargar",
    "download", "link", "enlace", "ir", "continuar", "más detalles",
    # Accent-free equivalents
    "clic aqui", "haz clic aqui", "click aqui", "leer mas", "mas", "ver mas", "aqui",
    "mas informacion", "mas detalles"
}

def extract_semantic_candidates(html_content: str) -> Dict[str, Any]:
    """
    Extract only the relevant candidates for LLM semantic judgment:
    1. Suspicious or generic alt texts on images
    2. Ambiguous or context-less link texts
    3. Heading structure hierarchy
    4. Form input labels vs placeholders
    5. Document language attribute vs sample text
    """
    soup = BeautifulSoup(html_content, "html.parser")
    candidates = {
        "images": [],
        "links": [],
        "headings": [],
        "forms": [],
        "language": {}
    }

    # 1. Images
    for img in soup.find_all("img"):
        alt = (img.get("alt") or "").strip()
        src = img.get("src") or ""
        is_suspicious = False
        reason = ""

        # Check if alt matches generic patterns
        if alt:
            lower_alt = alt.lower()
            for pattern in SUSPICIOUS_ALT_PATTERNS:
                if re.search(pattern, lower_alt):
                    is_suspicious = True
                    reason = f"Texto alternativo genérico o nombre de archivo ('{alt}')"
                    break
            if not is_suspicious and lower_alt == src.lower():
                is_suspicious = True
                reason = "El atributo alt es idéntico a la ruta de la fuente src"
        else:
            # If empty alt without role="presentation"
            if img.get("role") != "presentation" and img.get("aria-hidden") != "true":
                is_suspicious = True
                reason = "Imagen sin atributo alt o con alt vacío sin marcar como decorativa"

        if is_suspicious:
            snippet = str(img)[:300]
            selector = f"img[src='{src}']" if src else "img"
            candidates["images"].append({
                "snippet": snippet,
                "selector": selector,
                "alt": alt,
                "src": src,
                "reason": reason
            })

    # 2. Links
    for a in soup.find_all("a"):
        text = a.get_text(strip=True)
        aria_label = a.get("aria-label", "").strip()
        title = a.get("title", "").strip()
        href = a.get("href", "")
        effective_text = (aria_label or text or title).lower()

        is_ambiguous = False
        reason = ""

        if effective_text in AMBIGUOUS_LINK_TEXTS:
            is_ambiguous = True
            reason = f"Texto de enlace no descriptivo fuera de contexto: '{text or aria_label}'"
        elif not effective_text and not a.find("img"):
            is_ambiguous = True
            reason = "Enlace vacío sin texto perceptible ni aria-label"

        if is_ambiguous:
            snippet = str(a)[:300]
            selector = f"a[href='{href}']" if href else "a"
            candidates["links"].append({
                "snippet": snippet,
                "selector": selector,
                "text": text,
                "href": href,
                "reason": reason
            })

    # 3. Headings hierarchy
    headings = []
    for h in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
        level = int(h.name[1])
        text = h.get_text(strip=True)
        headings.append({
            "tag": h.name,
            "level": level,
            "text": text[:80],
            "snippet": str(h)[:200]
        })
    candidates["headings"] = headings

    # 4. Form inputs without explicit label
    for field in soup.find_all(["input", "select", "textarea"]):
        input_type = field.get("type", "text").lower()
        if input_type in ("hidden", "submit", "button", "reset"):
            continue

        field_id = field.get("id")
        has_label = False
        if field_id:
            label = soup.find("label", attrs={"for": field_id})
            if label and label.get_text(strip=True):
                has_label = True

        if not has_label and field.find_parent("label"):
            has_label = True

        if not has_label:
            placeholder = field.get("placeholder", "").strip()
            aria_label = field.get("aria-label", "").strip()
            aria_labelledby = field.get("aria-labelledby", "").strip()

            if not aria_label and not aria_labelledby:
                candidates["forms"].append({
                    "snippet": str(field)[:250],
                    "selector": f"{field.name}#{field_id}" if field_id else field.name,
                    "placeholder": placeholder,
                    "reason": "Campo de formulario sin <label> asociado; el placeholder no sustituye a la etiqueta accesible"
                })

    # 5. Language
    html_tag = soup.find("html")
    lang_attr = html_tag.get("lang") if html_tag else None
    body_text_sample = soup.body.get_text(separator=" ", strip=True)[:300] if soup.body else ""
    candidates["language"] = {
        "declared_lang": lang_attr,
        "sample_text": body_text_sample
    }

    return candidates
