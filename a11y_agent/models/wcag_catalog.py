"""Official catalog of WCAG 2.0 / 2.1 / 2.2 Principles, Criteria, and W3C Techniques."""

from typing import Dict, Any, Optional
from a11y_agent.models.schema import Principle, WCAGLevel

PRINCIPLES_META = {
    Principle.PERCEPTIBLE: {
        "name": "1. Perceptible",
        "description": "La información y los componentes de la interfaz de usuario deben presentarse a los usuarios de modo que puedan percibirlos (no puede ser invisible para todos sus sentidos)."
    },
    Principle.OPERABLE: {
        "name": "2. Operable",
        "description": "Los componentes de la interfaz de usuario y la navegación deben ser operables (la interfaz no puede requerir una interacción que el usuario no pueda realizar)."
    },
    Principle.UNDERSTANDABLE: {
        "name": "3. Comprensible",
        "description": "La información y el manejo de la interfaz de usuario deben ser comprensibles (el contenido y los controles no pueden resultar confusos o impredecibles)."
    },
    Principle.ROBUST: {
        "name": "4. Robusto",
        "description": "El contenido debe ser suficientemente robusto como para que pueda ser interpretado de forma fiable por una amplia variedad de agentes de usuario, incluyendo tecnologías de asistencia."
    }
}

WCAG_CRITERIA_CATALOG: Dict[str, Dict[str, Any]] = {
    # 1. PERCEPTIBLE
    "1.1.1": {
        "principle": Principle.PERCEPTIBLE,
        "title": "Contenido no textual",
        "level": WCAGLevel.A,
        "version": "2.0",
        "technique": "H37",
        "description": "Todo contenido no textual presentado al usuario tiene una alternativa textual que cumple un propósito equivalente."
    },
    "1.2.1": {
        "principle": Principle.PERCEPTIBLE,
        "title": "Solo audio o solo vídeo (grabado)",
        "level": WCAGLevel.A,
        "version": "2.0",
        "technique": "G158",
        "description": "Se proporciona alternativa para los medios basados en tiempo solo audio o solo vídeo."
    },
    "1.3.1": {
        "principle": Principle.PERCEPTIBLE,
        "title": "Información y relaciones",
        "level": WCAGLevel.A,
        "version": "2.0",
        "technique": "H42",
        "description": "La información, la estructura y las relaciones comunicadas visualmente se determinan por software o están disponibles en el texto."
    },
    "1.3.2": {
        "principle": Principle.PERCEPTIBLE,
        "title": "Secuencia significativa",
        "level": WCAGLevel.A,
        "version": "2.0",
        "technique": "C27",
        "description": "Cuando el orden en que se presenta el contenido afecta su significado, una secuencia de lectura correcta puede ser determinada por software."
    },
    "1.3.3": {
        "principle": Principle.PERCEPTIBLE,
        "title": "Características sensoriales",
        "level": WCAGLevel.A,
        "version": "2.0",
        "technique": "G96",
        "description": "Las instrucciones provistas para entender y operar el contenido no dependen exclusivamente de características sensoriales como forma, color o ubicación."
    },
    "1.4.1": {
        "principle": Principle.PERCEPTIBLE,
        "title": "Uso del color",
        "level": WCAGLevel.A,
        "version": "2.0",
        "technique": "G14",
        "description": "El color no se usa como el único medio visual para transmitir información, indicar una acción o distinguir un elemento visual."
    },
    "1.4.3": {
        "principle": Principle.PERCEPTIBLE,
        "title": "Contraste (mínimo)",
        "level": WCAGLevel.AA,
        "version": "2.0",
        "technique": "G18",
        "description": "La presentación visual de texto e imágenes de texto tiene una relación de contraste de al menos 4.5:1 (o 3:1 para texto grande)."
    },
    "1.4.4": {
        "principle": Principle.PERCEPTIBLE,
        "title": "Cambio de tamaño del texto",
        "level": WCAGLevel.AA,
        "version": "2.0",
        "technique": "G142",
        "description": "El texto puede redimensionarse sin tecnologías de asistencia hasta un 200% sin pérdida de contenido o funcionalidad."
    },
    "1.4.11": {
        "principle": Principle.PERCEPTIBLE,
        "title": "Contraste no textual",
        "level": WCAGLevel.AA,
        "version": "2.1",
        "technique": "G195",
        "description": "Los componentes de interfaz de usuario y objetos gráficos tienen una relación de contraste de al menos 3:1 frente a colores adyacentes."
    },
    "1.4.12": {
        "principle": Principle.PERCEPTIBLE,
        "title": "Espaciado del texto",
        "level": WCAGLevel.AA,
        "version": "2.1",
        "technique": "C36",
        "description": "No hay pérdida de contenido ni funcionalidad al ajustar altura de línea, espaciado de párrafo, palabras y letras."
    },
    "1.4.13": {
        "principle": Principle.PERCEPTIBLE,
        "title": "Contenido al pasar el puntero o enfocar",
        "level": WCAGLevel.AA,
        "version": "2.1",
        "technique": "SCR39",
        "description": "El contenido adicional que aparece al puntero/foco es descartable, señalable y persistente."
    },

    # 2. OPERABLE
    "2.1.1": {
        "principle": Principle.OPERABLE,
        "title": "Teclado",
        "level": WCAGLevel.A,
        "version": "2.0",
        "technique": "G202",
        "description": "Toda la funcionalidad del contenido es operable a través de una interfaz de teclado sin requerir una sincronización específica."
    },
    "2.1.2": {
        "principle": Principle.OPERABLE,
        "title": "Sin trampas para el foco del teclado",
        "level": WCAGLevel.A,
        "version": "2.0",
        "technique": "G21",
        "description": "El foco del teclado puede salir de cualquier componente enfocado usando únicamente teclas estándar."
    },
    "2.4.1": {
        "principle": Principle.OPERABLE,
        "title": "Evitar bloques",
        "level": WCAGLevel.A,
        "version": "2.0",
        "technique": "G1",
        "description": "Se proporciona un mecanismo para evitar los bloques de contenido que se repiten en múltiples páginas (ej. enlaces saltar al contenido)."
    },
    "2.4.2": {
        "principle": Principle.OPERABLE,
        "title": "Titulación de páginas",
        "level": WCAGLevel.A,
        "version": "2.0",
        "technique": "H25",
        "description": "Las páginas web tienen títulos que describen su tema o propósito de forma clara."
    },
    "2.4.3": {
        "principle": Principle.OPERABLE,
        "title": "Orden del foco",
        "level": WCAGLevel.A,
        "version": "2.0",
        "technique": "G59",
        "description": "Si una página web se puede navegar secuencialmente, los componentes reciben el foco en un orden que preserva el significado y la operatividad."
    },
    "2.4.4": {
        "principle": Principle.OPERABLE,
        "title": "Propósito de cada enlace (en contexto)",
        "level": WCAGLevel.A,
        "version": "2.0",
        "technique": "H30",
        "description": "El propósito de cada enlace puede ser determinado con solo el texto del enlace o a través de su contexto inmediato."
    },
    "2.4.6": {
        "principle": Principle.OPERABLE,
        "title": "Encabezados y etiquetas",
        "level": WCAGLevel.AA,
        "version": "2.0",
        "technique": "G130",
        "description": "Los encabezados y las etiquetas describen el tema o propósito del contenido al que preceden."
    },
    "2.4.7": {
        "principle": Principle.OPERABLE,
        "title": "Foco visible",
        "level": WCAGLevel.AA,
        "version": "2.0",
        "technique": "C15",
        "description": "Cualquier interfaz de usuario operable por teclado tiene una forma de operación donde el indicador de foco del teclado es visible."
    },
    "2.5.3": {
        "principle": Principle.OPERABLE,
        "title": "Etiqueta en el nombre",
        "level": WCAGLevel.A,
        "version": "2.1",
        "technique": "G208",
        "description": "Para los componentes con etiquetas de texto visible, el nombre accesible incluye el texto que se presenta visualmente."
    },
    "2.5.8": {
        "principle": Principle.OPERABLE,
        "title": "Tamaño del objetivo (mínimo)",
        "level": WCAGLevel.AA,
        "version": "2.2",
        "technique": "G219",
        "description": "El tamaño del objetivo para las entradas táctiles es de al menos 24 por 24 píxeles CSS, excepto ciertas excepciones."
    },

    # 3. COMPRENSIBLE
    "3.1.1": {
        "principle": Principle.UNDERSTANDABLE,
        "title": "Idioma de la página",
        "level": WCAGLevel.A,
        "version": "2.0",
        "technique": "H57",
        "description": "El idioma humano predeterminado de cada página web puede ser determinado por software a través del atributo lang."
    },
    "3.1.2": {
        "principle": Principle.UNDERSTANDABLE,
        "title": "Idioma de las partes",
        "level": WCAGLevel.AA,
        "version": "2.0",
        "technique": "H58",
        "description": "El idioma de cada pasaje o frase en el contenido puede ser determinado por software."
    },
    "3.2.1": {
        "principle": Principle.UNDERSTANDABLE,
        "title": "Al recibir el foco",
        "level": WCAGLevel.A,
        "version": "2.0",
        "technique": "G107",
        "description": "Cuando cualquier componente recibe el foco, no inicia ningún cambio de contexto inesperado."
    },
    "3.2.2": {
        "principle": Principle.UNDERSTANDABLE,
        "title": "Al recibir entradas",
        "level": WCAGLevel.A,
        "version": "2.0",
        "technique": "G80",
        "description": "El cambio de ajuste en cualquier componente no provoca automáticamente un cambio de contexto a menos que el usuario haya sido avisado."
    },
    "3.3.1": {
        "principle": Principle.UNDERSTANDABLE,
        "title": "Identificación de errores",
        "level": WCAGLevel.A,
        "version": "2.0",
        "technique": "G83",
        "description": "Si se detecta un error de entrada automáticamente, el elemento con error se identifica y el error se describe en texto."
    },
    "3.3.2": {
        "principle": Principle.UNDERSTANDABLE,
        "title": "Etiquetas o instrucciones",
        "level": WCAGLevel.A,
        "version": "2.0",
        "technique": "H44",
        "description": "Se proporcionan etiquetas o instrucciones cuando el contenido requiere la introducción de datos por parte del usuario."
    },

    # 4. ROBUSTO
    "4.1.1": {
        "principle": Principle.ROBUST,
        "title": "Procesamiento (Parsing)",
        "level": WCAGLevel.A,
        "version": "2.0",
        "technique": "H74",
        "description": "Los elementos tienen etiquetas de apertura y cierre completas, están anidados adecuadamente y no contienen atributos duplicados."
    },
    "4.1.2": {
        "principle": Principle.ROBUST,
        "title": "Nombre, función, valor",
        "level": WCAGLevel.A,
        "version": "2.0",
        "technique": "ARIA5",
        "description": "Para todos los componentes de interfaz de usuario, el nombre y la función pueden determinarse por software; los estados y valores pueden ser fijados."
    },
    "4.1.3": {
        "principle": Principle.ROBUST,
        "title": "Mensajes de estado",
        "level": WCAGLevel.AA,
        "version": "2.1",
        "technique": "ARIA22",
        "description": "En contenidos implementados con lenguajes de marcado, los mensajes de estado se determinan por software mediante roles o propiedades aria-live."
    }
}

# Mapping from axe-core rule IDs to WCAG criteria and default techniques
AXE_RULE_MAP: Dict[str, Dict[str, Any]] = {
    "image-alt": {
        "criterion": "1.1.1",
        "technique": "H37",
        "check_name": "Elementos <img> deben tener un atributo alt descriptivo"
    },
    "input-image-alt": {
        "criterion": "1.1.1",
        "technique": "H36",
        "check_name": "Botones de imagen deben tener texto alternativo"
    },
    "area-alt": {
        "criterion": "1.1.1",
        "technique": "H24",
        "check_name": "Elementos <area> de mapas de imágenes deben tener texto alternativo"
    },
    "color-contrast": {
        "criterion": "1.4.3",
        "technique": "G18",
        "check_name": "El contraste de color del texto cumple el umbral mínimo (4.5:1 / 3:1)"
    },
    "heading-order": {
        "criterion": "1.3.1",
        "technique": "G141",
        "check_name": "El orden de los niveles de encabezado debe ser semánticamente secuencial"
    },
    "label": {
        "criterion": "3.3.2",
        "technique": "H44",
        "check_name": "Todo elemento de formulario debe tener una etiqueta asociada"
    },
    "button-name": {
        "criterion": "4.1.2",
        "technique": "ARIA14",
        "check_name": "Los botones deben tener texto perceptible o nombre accesible"
    },
    "link-name": {
        "criterion": "2.4.4",
        "technique": "H30",
        "check_name": "Los enlaces deben tener texto discernible que describa su destino"
    },
    "html-has-lang": {
        "criterion": "3.1.1",
        "technique": "H57",
        "check_name": "El elemento <html> debe tener un atributo lang válido"
    },
    "html-lang-valid": {
        "criterion": "3.1.1",
        "technique": "H57",
        "check_name": "El atributo lang en <html> debe contener un código de idioma BCP 47 válido"
    },
    "document-title": {
        "criterion": "2.4.2",
        "technique": "H25",
        "check_name": "El documento debe tener un elemento <title> no vacío"
    },
    "bypass": {
        "criterion": "2.4.1",
        "technique": "G1",
        "check_name": "La página debe tener medios para saltar la navegación repetitiva"
    },
    "tabindex": {
        "criterion": "2.4.3",
        "technique": "F44",
        "check_name": "Los elementos no deben tener valores de tabindex positivos mayores que 0"
    },
    "aria-roles": {
        "criterion": "4.1.2",
        "technique": "ARIA4",
        "check_name": "Todos los atributos role de ARIA deben ser válidos"
    },
    "aria-valid-attr": {
        "criterion": "4.1.2",
        "technique": "ARIA5",
        "check_name": "Todos los atributos aria-* deben ser válidos"
    },
    "duplicate-id-active": {
        "criterion": "4.1.1",
        "technique": "F77",
        "check_name": "Los elementos interactivos no deben compartir id duplicado"
    },
    "target-size": {
        "criterion": "2.5.8",
        "technique": "G219",
        "check_name": "El tamaño del objetivo táctil debe ser de al menos 24x24 px"
    }
}

def get_criterion_details(criterion_id: str) -> Dict[str, Any]:
    """Retrieve details for a WCAG success criterion, with graceful fallback."""
    if criterion_id in WCAG_CRITERIA_CATALOG:
        return WCAG_CRITERIA_CATALOG[criterion_id]
    return {
        "principle": Principle.PERCEPTIBLE,
        "title": f"Criterio {criterion_id}",
        "level": WCAGLevel.A,
        "version": "2.1",
        "technique": "G94",
        "description": "Comprobación de accesibilidad web."
    }
