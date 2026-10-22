"""Source code line locator matching DOM elements/snippets back to original HTML source."""

import re
from typing import Optional, List

def find_line_number(raw_html: str, snippet: Optional[str] = None, selector: Optional[str] = None) -> Optional[int]:
    """
    Locates the 1-based line number in `raw_html` where `snippet` occurs.
    If the exact snippet isn't found, attempts tag + attribute matching or selector id matching.
    Returns None if not identifiable.
    """
    if not raw_html or (not snippet and not selector):
        return None

    lines = raw_html.splitlines()

    # 1. Exact snippet substring match
    if snippet:
        clean_snippet = snippet.strip()
        first_line_snippet = clean_snippet.splitlines()[0].strip() if clean_snippet else ""

        if first_line_snippet:
            for idx, line in enumerate(lines, start=1):
                if first_line_snippet in line:
                    return idx

        # 2. Tag name and key attributes match
        tag_match = re.search(r"<([a-zA-Z0-9\-]+)([^>]*)>", clean_snippet)
        if tag_match:
            tag_name = tag_match.group(1).lower()
            attr_part = tag_match.group(2)

            id_match = re.search(r'id=["\']([^"\']+)["\']', attr_part)
            class_match = re.search(r'class=["\']([^"\']+)["\']', attr_part)
            src_match = re.search(r'src=["\']([^"\']+)["\']', attr_part)
            href_match = re.search(r'href=["\']([^"\']+)["\']', attr_part)

            for idx, line in enumerate(lines, start=1):
                line_lower = line.lower()
                if f"<{tag_name}" in line_lower:
                    if id_match and f'id="{id_match.group(1)}"' in line:
                        return idx
                    if src_match and src_match.group(1) in line:
                        return idx
                    if href_match and href_match.group(1) in line:
                        return idx
                    if class_match and class_match.group(1) in line:
                        return idx

    # 3. Selector id matching (e.g., #my-button or h1#main-heading)
    if selector and "#" in selector:
        id_part = selector.split("#")[-1].split(" ")[0].split(".")[0].strip()
        if id_part:
            id_pattern = re.compile(rf'id=["\']{re.escape(id_part)}["\']', re.IGNORECASE)
            for idx, line in enumerate(lines, start=1):
                if id_pattern.search(line):
                    return idx

    return None
