"""Static accessibility scanner for Android APK packages (WCAG 2.1 / 2.2 / EN 301 549)."""

import os
import re
import time
import zipfile
import secrets
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from a11y_agent.core.config import settings
from a11y_agent.models.schema import (
    Finding, Category, FindingOrigin, ImpactLevel, EffortLevel,
    Principle, WCAGLevel, GuidelinesVersion, Remediation, A11yReport
)
from a11y_agent.models.wcag_catalog import get_criterion_details
from a11y_agent.analyzer.scorer import build_a11y_report
from a11y_agent.analyzer.llm_client import LLMAnalyzer
from a11y_agent.reporters.html_reporter import export_to_html
from a11y_agent.reporters.json_reporter import export_to_json
from a11y_agent.reporters.pdf_reporter import export_to_pdf

ANDROID_NS = "http://schemas.android.com/apk/res/android"
APP_NS = "http://schemas.android.com/apk/res-auto"

GENERIC_DESCRIPTION_PATTERNS = [
    r"^image$", r"^imagen$", r"^foto$", r"^picture$", r"^icon$", r"^icono$",
    r"^button$", r"^boton$", r"^btn$", r"^img_\d+$", r"^icon_\d+$",
    r"\.(png|jpg|jpeg|svg|webp|xml)$"
]

INTERACTIVE_VIEWS = {
    "button", "imagebutton", "floatingactionbutton", "checkbox",
    "radiobutton", "switch", "togglebutton", "seekbars"
}

def calculate_luminance(r: int, g: int, b: int) -> float:
    """Calculate relative luminance for sRGB color."""
    vals = []
    for c in (r, g, b):
        c_norm = c / 255.0
        if c_norm <= 0.03928:
            vals.append(c_norm / 12.92)
        else:
            vals.append(((c_norm + 0.055) / 1.055) ** 2.4)
    return 0.2126 * vals[0] + 0.7152 * vals[1] + 0.0722 * vals[2]

def calculate_contrast_ratio(hex1: str, hex2: str) -> Optional[float]:
    """Calculate contrast ratio between two hex colors (#RRGGBB or #AARRGGBB)."""
    try:
        def parse_hex(h: str) -> Tuple[int, int, int]:
            clean = h.lstrip("#")
            if len(clean) == 8:
                clean = clean[2:]  # ignore alpha
            if len(clean) == 3:
                clean = "".join([c * 2 for c in clean])
            if len(clean) != 6:
                raise ValueError()
            return int(clean[0:2], 16), int(clean[2:4], 16), int(clean[4:6], 16)

        c1 = parse_hex(hex1)
        c2 = parse_hex(hex2)
        l1 = calculate_luminance(*c1)
        l2 = calculate_luminance(*c2)
        lighter = max(l1, l2)
        darker = min(l1, l2)
        return round((lighter + 0.05) / (darker + 0.05), 2)
    except Exception:
        return None

def parse_dimension_dp(val: str) -> Optional[float]:
    """Extract float value from dp/dip dimension string."""
    if not val:
        return None
    match = re.search(r"(\d+(?:\.\d+)?)\s*(?:dp|dip)", val.lower())
    return round(float(match.group(1)), 2) if match else None

class APKScanner:
    """Performs static accessibility analysis on Android APK archives."""

    def __init__(self):
        self.llm_analyzer = LLMAnalyzer()

    def decode_xml(self, raw_bytes: bytes) -> Optional[str]:
        """
        Decode raw bytes of an Android XML file (supports binary AXML and plaintext).
        """
        if not raw_bytes:
            return None

        # Check if already plaintext XML
        try:
            text = raw_bytes.decode("utf-8").strip()
            if text.startswith("<") and text.endswith(">"):
                return text
        except UnicodeDecodeError:
            pass

        # Use Androguard's AXMLPrinter for binary AXML
        try:
            from androguard.core.axml import AXMLPrinter
            printer = AXMLPrinter(raw_bytes)
            if printer.is_valid():
                xml_content = printer.get_xml()
                if isinstance(xml_content, bytes):
                    return xml_content.decode("utf-8", errors="replace")
                return str(xml_content)
        except Exception:
            pass

        return None

    def extract_apk_components(self, apk_path: Path) -> Dict[str, Any]:
        """
        Extract manifest, layout XMLs, package info, and metadata from APK.
        """
        components = {
            "package_name": "unknown.package",
            "app_name": None,
            "version_name": None,
            "target_sdk": None,
            "min_sdk": None,
            "manifest_raw": None,
            "manifest_tree": None,
            "layouts": {},  # file_path -> (raw_xml_string, ElementTree root)
            "technologies": ["Android APK", "XML Layouts"]
        }

        # 1. Try high-level androguard APK parser
        try:
            from androguard.core.apk import APK
            apk = APK(str(apk_path))
            components["package_name"] = apk.get_package() or apk_path.stem
            components["app_name"] = apk.get_app_name() or apk_path.stem
            components["version_name"] = apk.get_androidversion_name()
            components["target_sdk"] = apk.get_target_sdk_version()
            components["min_sdk"] = apk.get_min_sdk_version()

            if apk.get_libraries():
                for lib in apk.get_libraries()[:5]:
                    components["technologies"].append(str(lib))
        except Exception:
            # Fallback for mock APKs or minimal packages
            components["package_name"] = apk_path.stem

        # 2. Extract layouts and manifest using zipfile
        try:
            with zipfile.ZipFile(apk_path, "r") as zf:
                # Check for DEX (Java/Kotlin indicator)
                has_dex = any(name.endswith(".dex") for name in zf.namelist())
                if has_dex and "Java/Kotlin" not in components["technologies"]:
                    components["technologies"].append("Java/Kotlin")

                # AndroidManifest.xml
                if "AndroidManifest.xml" in zf.namelist():
                    manifest_bytes = zf.read("AndroidManifest.xml")
                    decoded_manifest = self.decode_xml(manifest_bytes)
                    if decoded_manifest:
                        components["manifest_raw"] = decoded_manifest
                        try:
                            m_tree = ET.fromstring(decoded_manifest)
                            components["manifest_tree"] = m_tree
                            pkg = m_tree.attrib.get("package")
                            if pkg:
                                components["package_name"] = pkg
                            app_elem = m_tree.find("application")
                            if app_elem is not None:
                                for k, v in app_elem.attrib.items():
                                    if "label" in k.lower() and v and not v.startswith("@"):
                                        components["app_name"] = v
                        except Exception:
                            pass

                # Layout files under res/layout*/
                for name in zf.namelist():
                    if (name.startswith("res/layout") or name.startswith("layout")) and name.endswith(".xml"):
                        try:
                            layout_bytes = zf.read(name)
                            decoded_layout = self.decode_xml(layout_bytes)
                            if decoded_layout:
                                try:
                                    tree = ET.fromstring(decoded_layout)
                                    components["layouts"][name] = (decoded_layout, tree)
                                except Exception:
                                    pass
                        except Exception:
                            continue
        except Exception as e:
            raise ValueError(f"No se pudo descomprimir o procesar el archivo APK: {e}")

        return components

    def scan_layout_element(
        self,
        elem: ET.Element,
        layout_name: str,
        finding_id_prefix: str,
        counter: int
    ) -> List[Finding]:
        """Inspect a single UI XML element for mobile accessibility rules."""
        findings = []

        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        tag_lower = tag.lower()

        # Extract attributes handling Android namespace
        attrs = {}
        for k, v in elem.attrib.items():
            clean_k = k.split("}")[-1] if "}" in k else k
            attrs[clean_k] = v

        view_id = attrs.get("id", "").split("/")[-1] if attrs.get("id") else f"anon_{tag}_{counter}"
        selector = f"{layout_name}#{view_id}" if attrs.get("id") else f"{layout_name} > {tag}"
        snippet = ET.tostring(elem, encoding="utf-8").decode("utf-8")[:300]

        is_clickable = attrs.get("clickable") == "true" or "onclick" in [k.lower() for k in attrs.keys()] or tag_lower in INTERACTIVE_VIEWS
        content_desc = attrs.get("contentDescription", "").strip()
        important_for_a11y = attrs.get("importantForAccessibility", "").lower()

        # -------------------------------------------------------------
        # Rule 1: Missing or Generic contentDescription on Image / Buttons (WCAG 1.1.1 / EN 301 549 11.1.1.1)
        # -------------------------------------------------------------
        if tag_lower in ("imagebutton", "imageview", "floatingactionbutton"):
            is_suspicious = False
            for pat in GENERIC_DESCRIPTION_PATTERNS:
                if re.search(pat, content_desc, re.IGNORECASE):
                    is_suspicious = True
                    break

            if not content_desc and important_for_a11y not in ("no", "nohidedescendants"):
                if is_clickable or tag_lower in ("imagebutton", "floatingactionbutton"):
                    findings.append(Finding(
                        id=f"{finding_id_prefix}-111-{counter:03d}",
                        principle=Principle.PERCEPTIBLE,
                        criterion_id="1.1.1",
                        criterion_title="Contenido no textual (Android)",
                        level=WCAGLevel.A,
                        category=Category.PROBLEMA,
                        origin=FindingOrigin.REGLA,
                        check_name="Control gráfico sin descripción accesible (android:contentDescription ausente)",
                        w3c_technique="AND1",
                        selector=selector,
                        line_number=None,
                        html_snippet=snippet,
                        explanation=f"El componente interactivo <{tag}> carece de 'android:contentDescription'. Los lectores de pantalla como TalkBack no podrán informar su propósito al usuario ciego.",
                        remediation=Remediation(
                            before_snippet=snippet,
                            after_snippet=snippet.replace(f"<{tag}", f'<{tag} android:contentDescription="@string/desc_{view_id}"'),
                            advice="Defina un recurso de texto accesible descriptivo con 'android:contentDescription'. Si la imagen es puramente decorativa, use android:importantForAccessibility='no'.",
                            effort=EffortLevel.BAJO
                        ),
                        impact=ImpactLevel.CRITICO,
                        confidence=1.0
                    ))
            elif is_suspicious:
                findings.append(Finding(
                    id=f"{finding_id_prefix}-111-GEN-{counter:03d}",
                    principle=Principle.PERCEPTIBLE,
                    criterion_id="1.1.1",
                    criterion_title="Contenido no textual (Android)",
                    level=WCAGLevel.A,
                    category=Category.ADVERTENCIA,
                    origin=FindingOrigin.REGLA,
                    check_name="Texto alternativo genérico o nombre de archivo en android:contentDescription",
                    w3c_technique="AND1",
                    selector=selector,
                    line_number=None,
                    html_snippet=snippet,
                    explanation=f"El atributo contentDescription '{content_desc}' parece ser un nombre de archivo o término genérico que no comunica la función real del control.",
                    remediation=Remediation(
                        before_snippet=snippet,
                        after_snippet=snippet.replace(f'android:contentDescription="{content_desc}"', f'android:contentDescription="@string/desc_{view_id}"'),
                        advice="Reemplace la descripción genérica por una frase concisa que explique la acción o información comunicada.",
                        effort=EffortLevel.BAJO
                    ),
                    impact=ImpactLevel.ALTO,
                    confidence=0.88
                ))

        # -------------------------------------------------------------
        # Rule 2: Form Inputs without Accessible Label or Hint (WCAG 3.3.2 / EN 301 549 11.3.3.2)
        # -------------------------------------------------------------
        if tag_lower in ("edittext", "textinputedittext", "autocompletetextview"):
            has_hint = bool(attrs.get("hint"))
            has_label = bool(attrs.get("labelFor")) or bool(content_desc)
            if not has_hint and not has_label:
                findings.append(Finding(
                    id=f"{finding_id_prefix}-332-{counter:03d}",
                    principle=Principle.UNDERSTANDABLE,
                    criterion_id="3.3.2",
                    criterion_title="Etiquetas o instrucciones (Android)",
                    level=WCAGLevel.A,
                    category=Category.PROBLEMA,
                    origin=FindingOrigin.REGLA,
                    check_name="Campo de entrada de texto sin etiqueta ni hint accesible",
                    w3c_technique="AND2",
                    selector=selector,
                    line_number=None,
                    html_snippet=snippet,
                    explanation=f"El campo <{tag}> no define 'android:hint', 'android:labelFor' ni 'android:contentDescription'. Los usuarios de tecnologías de asistencia no sabrán qué dato deben introducir.",
                    remediation=Remediation(
                        before_snippet=snippet,
                        after_snippet=snippet.replace(f"<{tag}", f'<{tag} android:hint="@string/hint_{view_id}" android:autofillHints="name"'),
                        advice="Agregue 'android:hint' o vincule un TextView descriptivo mediante 'android:labelFor'.",
                        effort=EffortLevel.BAJO
                    ),
                    impact=ImpactLevel.ALTO,
                    confidence=1.0
                ))

        # -------------------------------------------------------------
        # Rule 3: Touch Target Size Below 48x48dp (WCAG 2.5.8 / 2.5.5 / Android Standard)
        # -------------------------------------------------------------
        if is_clickable:
            width_str = attrs.get("layout_width", "")
            height_str = attrs.get("layout_height", "")
            min_width_str = attrs.get("minWidth", "")
            min_height_str = attrs.get("minHeight", "")

            w = parse_dimension_dp(width_str)
            h = parse_dimension_dp(height_str)
            min_w = parse_dimension_dp(min_width_str)
            min_h = parse_dimension_dp(min_height_str)

            effective_w = max(w or 48, min_w or 0) if w else (min_w or 48)
            effective_h = max(h or 48, min_h or 0) if h else (min_h or 48)

            # If explicitly smaller than 48dp
            is_under_48 = (w is not None and w < 48 and (min_w is None or min_w < 48)) or \
                          (h is not None and h < 48 and (min_h is None or min_h < 48))

            if is_under_48:
                is_critical = (w is not None and w < 24) or (h is not None and h < 24)
                cat = Category.PROBLEMA if is_critical else Category.ADVERTENCIA
                crit = "2.5.8" if is_critical else "2.5.5"

                findings.append(Finding(
                    id=f"{finding_id_prefix}-258-{counter:03d}",
                    principle=Principle.OPERABLE,
                    criterion_id=crit,
                    criterion_title="Tamaño del objetivo táctil (Android Target Size)",
                    level=WCAGLevel.AA if is_critical else WCAGLevel.AAA,
                    category=cat,
                    origin=FindingOrigin.REGLA,
                    check_name=f"Objetivo táctil con dimensiones inferiores a 48x48dp ({w or '?'}x{h or '?'}dp)",
                    w3c_technique="G219",
                    selector=selector,
                    line_number=None,
                    html_snippet=snippet,
                    explanation=f"El elemento interactivo <{tag}> tiene dimensiones táctiles reducidas ({w or '?'}x{h or '?'}dp). La pauta Android y WCAG recomiendan un mínimo de 48x48dp para evitar pulsaciones erróneas en pantallas táctiles.",
                    remediation=Remediation(
                        before_snippet=snippet,
                        after_snippet=snippet.replace(f"<{tag}", f'<{tag} android:minWidth="48dp" android:minHeight="48dp" android:padding="10dp"'),
                        advice="Establezca 'android:minWidth=\"48dp\"' y 'android:minHeight=\"48dp\"' o compense con padding interno para alcanzar el área táctil recomendada.",
                        effort=EffortLevel.BAJO
                    ),
                    impact=ImpactLevel.ALTO if is_critical else ImpactLevel.MEDIO,
                    confidence=0.95
                ))

        # -------------------------------------------------------------
        # Rule 4: Interactive Control Hidden from Accessibility (WCAG 4.1.2 / EN 301 549 11.4.1.2)
        # -------------------------------------------------------------
        if is_clickable and important_for_a11y in ("no", "nohidedescendants"):
            findings.append(Finding(
                id=f"{finding_id_prefix}-412-SUP-{counter:03d}",
                principle=Principle.ROBUST,
                criterion_id="4.1.2",
                criterion_title="Nombre, función, valor (Android)",
                level=WCAGLevel.A,
                category=Category.PROBLEMA,
                origin=FindingOrigin.REGLA,
                check_name="Control interactivo oculto indebidamente con android:importantForAccessibility='no'",
                w3c_technique="AND4",
                selector=selector,
                line_number=None,
                html_snippet=snippet,
                explanation=f"El componente interactivo <{tag}> fue marcado con importantForAccessibility='{important_for_a11y}'. Esto elimina el elemento del árbol accesible de TalkBack, impidiendo su uso a personas con discapacidad visual.",
                remediation=Remediation(
                    before_snippet=snippet,
                    after_snippet=re.sub(r'android:importantForAccessibility="[^"]*"', 'android:importantForAccessibility="yes"', snippet),
                    advice="Elimine 'android:importantForAccessibility=\"no\"' o cámbielo a 'yes' en controles que admiten clics o interacción.",
                    effort=EffortLevel.BAJO
                ),
                impact=ImpactLevel.CRITICO,
                confidence=1.0
            ))

        # -------------------------------------------------------------
        # Rule 5: Hardcoded Colors with Insufficient Contrast (WCAG 1.4.3 / EN 301 549 11.1.4.3)
        # -------------------------------------------------------------
        text_color = attrs.get("textColor")
        bg_color = attrs.get("background")
        if text_color and bg_color and text_color.startswith("#") and bg_color.startswith("#"):
            ratio = calculate_contrast_ratio(text_color, bg_color)
            if ratio is not None and ratio < 4.5:
                findings.append(Finding(
                    id=f"{finding_id_prefix}-143-COL-{counter:03d}",
                    principle=Principle.PERCEPTIBLE,
                    criterion_id="1.4.3",
                    criterion_title="Contraste (mínimo) en vistas Android",
                    level=WCAGLevel.AA,
                    category=Category.PROBLEMA,
                    origin=FindingOrigin.REGLA,
                    check_name=f"Contraste de color insuficiente ({ratio}:1 frente al mínimo 4.5:1)",
                    w3c_technique="G18",
                    selector=selector,
                    line_number=None,
                    html_snippet=snippet,
                    explanation=f"La relación de contraste entre el texto ({text_color}) y el fondo ({bg_color}) es de {ratio}:1, por debajo del estándar mínimo de 4.5:1 para texto normal.",
                    remediation=Remediation(
                        before_snippet=snippet,
                        after_snippet=snippet.replace(f'android:textColor="{text_color}"', 'android:textColor="#0f172a"'),
                        advice="Oscurezca el color del texto o aclare el fondo para garantizar un ratio de contraste superior a 4.5:1.",
                        effort=EffortLevel.MEDIO
                    ),
                    impact=ImpactLevel.ALTO,
                    confidence=0.98
                ))

        return findings

    def scan_manifest(self, manifest_tree: ET.Element) -> List[Finding]:
        """Verify accessibility settings in AndroidManifest.xml."""
        findings = []
        if manifest_tree is None:
            return findings

        app_elem = manifest_tree.find("application")
        if app_elem is not None:
            attrs = {k.split("}")[-1]: v for k, v in app_elem.attrib.items()}

            # Check android:label on application
            if not attrs.get("label"):
                findings.append(Finding(
                    id="APK-MAN-242",
                    principle=Principle.OPERABLE,
                    criterion_id="2.4.2",
                    criterion_title="Titulación de páginas y aplicaciones",
                    level=WCAGLevel.A,
                    category=Category.PROBLEMA,
                    origin=FindingOrigin.REGLA,
                    check_name="Etiqueta accesible de la aplicación ausente (android:label)",
                    w3c_technique="H25",
                    selector="AndroidManifest.xml > application",
                    line_number=None,
                    html_snippet=ET.tostring(app_elem, encoding="utf-8").decode("utf-8")[:200],
                    explanation="El elemento <application> no define el atributo 'android:label'. TalkBack y el lanzador del sistema no podrán identificar verbalmente la aplicación.",
                    remediation=Remediation(
                        before_snippet="<application ...>",
                        after_snippet='<application android:label="@string/app_name" ...>',
                        advice="Declare el nombre accesible de la app con 'android:label=\"@string/app_name\"'.",
                        effort=EffortLevel.BAJO
                    ),
                    impact=ImpactLevel.ALTO,
                    confidence=1.0
                ))

            # Check RTL support (bidirectional readability 1.3.2 / 3.1.2)
            if attrs.get("supportsRtl") != "true":
                findings.append(Finding(
                    id="APK-MAN-132",
                    principle=Principle.PERCEPTIBLE,
                    criterion_id="1.3.2",
                    criterion_title="Secuencia significativa / Soporte bidireccional",
                    level=WCAGLevel.A,
                    category=Category.ADVERTENCIA,
                    origin=FindingOrigin.REGLA,
                    check_name="Falta declaración explícita de soporte RTL (android:supportsRtl)",
                    w3c_technique="G57",
                    selector="AndroidManifest.xml > application",
                    line_number=None,
                    html_snippet="<application ...>",
                    explanation="La aplicación no declara 'android:supportsRtl=\"true\"', lo cual puede desordenar la secuencia de lectura para usuarios de idiomas de derecha a izquierda (árabe, hebreo).",
                    remediation=Remediation(
                        before_snippet="<application ...>",
                        after_snippet='<application android:supportsRtl="true" ...>',
                        advice="Active el soporte de diseño bidireccional añadiendo 'android:supportsRtl=\"true\"'.",
                        effort=EffortLevel.BAJO
                    ),
                    impact=ImpactLevel.BAJO,
                    confidence=0.90
                ))

        return findings

    async def scan_apk(
        self,
        apk_path: Path,
        guidelines: GuidelinesVersion = GuidelinesVersion.WCAG_2_2,
        target_level: WCAGLevel = WCAGLevel.AA,
        export_formats: Optional[List[str]] = None,
        base_public_url: Optional[str] = None
    ) -> A11yReport:
        """
        Execute full static accessibility audit on an Android APK package.
        """
        start_time = time.time()
        report_id = f"rep_{secrets.token_hex(16)}"
        public_url = f"{base_public_url.rstrip('/')}/view/{report_id}" if base_public_url else f"/view/{report_id}"

        # 1. Unpack & inspect APK
        comp = self.extract_apk_components(apk_path)
        pkg_name = comp["package_name"]
        app_name = comp["app_name"] or pkg_name

        all_findings: List[Finding] = []

        # 2. Check AndroidManifest.xml
        if comp.get("manifest_tree") is not None:
            manifest_findings = self.scan_manifest(comp["manifest_tree"])
            all_findings.extend(manifest_findings)

        # 3. Check layout files
        counter = 1
        semantic_candidates = {"images": [], "links": [], "headings": [], "forms": []}

        for layout_file, (raw_xml, tree) in comp.get("layouts", {}).items():
            for elem in tree.iter():
                elem_findings = self.scan_layout_element(
                    elem=elem,
                    layout_name=layout_file,
                    finding_id_prefix=f"APK-{counter:02d}",
                    counter=counter
                )
                all_findings.extend(elem_findings)
                counter += 1

                # Gather candidates for semantic LLM assessment
                tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
                content_desc = elem.attrib.get(f"{{{ANDROID_NS}}}contentDescription") or elem.attrib.get("contentDescription", "")
                if content_desc and len(content_desc) < 40:
                    semantic_candidates["images"].append({
                        "snippet": ET.tostring(elem, encoding="utf-8").decode("utf-8")[:250],
                        "selector": f"{layout_file}#{elem.attrib.get('id', tag)}",
                        "alt": content_desc,
                        "src": tag,
                        "reason": f"Descripción de control Android: '{content_desc}'"
                    })

        # 4. Semantic LLM judgment on Android contentDescriptions (if candidates exist)
        if semantic_candidates["images"]:
            try:
                # We reuse the LLM analyzer with mobile context
                ia_findings = await self.llm_analyzer.analyze_semantics(
                    candidates=semantic_candidates,
                    raw_html="\n".join([raw for raw, _ in comp.get("layouts", {}).values()]),
                    target_level=target_level
                )
                all_findings.extend(ia_findings)
            except Exception:
                pass

        elapsed = round(time.time() - start_time, 2)
        technologies = comp["technologies"]
        if comp.get("target_sdk"):
            technologies.append(f"Target SDK {comp['target_sdk']}")

        # 5. Build consolidated report
        url_identifier = f"apk://{pkg_name} ({apk_path.name})"
        report = build_a11y_report(
            report_id=report_id,
            url=url_identifier,
            findings=all_findings,
            guidelines=guidelines,
            target_level=target_level,
            technologies=technologies,
            execution_time_seconds=elapsed,
            screenshot_path=None,
            target_type="apk",
            app_name=app_name,
            package_name=pkg_name,
            public_url=public_url
        )

        # 6. Export outputs (HTML, JSON, PDF)
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

        return report
