# A11y Agent 🌐🤖

**A11y Agent** es un agente avanzado de auditoría y remediación de accesibilidad web (conforme a **WCAG 2.0 / 2.1 / 2.2** en niveles **A, AA y AAA**). Ofrece un informe equivalente al de herramientas de referencia como **TAW (tawdis.net)**, pero potenciado con **inteligencia artificial semántica**, generación automática de soluciones de código (antes y después), priorización por impacto/esfuerzo, y un **asistente conversacional de remediación**.

---

## 🌟 Características Principales

1. **Estructura Estilo TAW**:
   - Organizado estrictamente por los 4 Principios W3C: **1. Perceptible**, **2. Operable**, **3. Comprensible** y **4. Robusto**.
   - Agrupación por **Criterio de Éxito** (ej. *1.1.1 Contenido no textual*, *1.4.3 Contraste mínimo*).
   - Columnas detalladas: comprobación, técnica W3C (ej. `H37`, `G18`), categoría de resultado, selector CSS, número de línea en el HTML fuente original y fragmento de código.
   - Triaje en 3 categorías:
     - **Problemas**: Fallos deterministas detectados automáticamente.
     - **Advertencias**: Puntos que requieren juicio contextual o revisión humana (todos los hallazgos de IA entran aquí).
     - **No verificados**: Comprobaciones que no pudieron ser determinadas en el DOM.

2. **Juicio Semántico con LLM**:
   - Evaluación contextual de textos alternativos de imágenes (detecta alts vacíos, genéricos como `"foto"`, `"imagen"`, o nombres de archivo).
   - Evaluación de textos de enlaces aislados (*"clic aquí"*, *"leer más"*, *"ver más"*).
   - Detección de discontinuidades en jerarquía de encabezados (`h1` a `h4`).
   - Verificación de etiquetas `<label>` formales frente a placeholders efímeros.
   - Validación del atributo `lang` frente al contenido textual real.

3. **Remediación Accionable**:
   - Cada incidencia incluye una explicación en lenguaje simple y el fragmento de código corregido (**Antes** y **Después**) listo para copiar y pegar.
   - Estimación de **Esfuerzo de corrección** (*bajo*, *medio*, *alto*) e **Impacto** (*crítico*, *alto*, *medio*, *bajo*).

4. **Puntaje Global y Resumen Ejecutivo**:
   - Puntuación de accesibilidad de 0 a 100 ponderada por la gravedad de las barreras detectadas.
   - Resumen ejecutivo estructurado de 5 líneas para dirección o equipos de desarrollo.

5. **Asistente de Chat Integrado**:
   - Interfaz conversacional para preguntar al agente: *"¿Cómo soluciono el problema 1?"* o *"¿Por qué falla el contraste del botón?"*.

6. **Reglas Anti-Alucinación**:
   - Todo hallazgo de IA cita y ancla el nodo HTML exacto comprobado en el código fuente.
   - Los hallazgos de IA se clasifican obligatoriamente como **"Advertencia"** con indicador de confianza (0.0 - 1.0), nunca como fallo definitivo inventado.
   - Se incluye un descargo de responsabilidad metodológico formal: ninguna auditoría automatizada reemplaza la evaluación manual con usuarios con discapacidad.

7. **Seguridad Robusta**:
   - **Protección Anti-SSRF**: Resolución DNS estricta previa que bloquea `localhost`, `127.0.0.1`, `::1` y todos los rangos privados RFC 1918 / link-local / multicast.
   - Respeto del archivo `robots.txt` del sitio.
   - Timeouts de navegación (30s) y límite de tamaño de carga (15 MB).

---

## 🛠️ Stack Tecnológico

- **Lenguaje & API**: Python 3.11+ / FastAPI / Uvicorn / Pydantic v2.
- **Motor de Render**: Playwright (Chromium Headless) para renderizar SPAs (React, Vue, Angular), ejecutar scripts dinámicos y capturar pantallas.
- **Motor de Reglas**: `axe-core 4.10` inyectado y ejecutado localmente (empaquetado sin dependencias externas).
- **Indexación de Código**: BeautifulSoup4 para mapear selectores a números de línea en el HTML fuente.
- **Capa LLM**: Abstracción multi-proveedor (OpenAI / Anthropic / Gemini / motor heurístico offline sin API key).
- **Exportadores**: Jinja2 para HTML autocontenido accesible y Playwright para generación de PDF vectorial de alta fidelidad.

---

## 🚀 Instalación y Puesta en Marcha

### 1. Clonar el repositorio y preparar entorno
```bash
# Crear entorno virtual (opcional pero recomendado)
python -m venv venv
venv\Scripts\activate   # En Windows
source venv/bin/activate  # En Linux/macOS

# Instalar dependencias
pip install -r requirements.txt
# O instalar directamente:
pip install fastapi uvicorn pydantic pydantic-settings playwright beautifulsoup4 httpx jinja2 pytest pytest-asyncio
```

### 2. Instalar el navegador de Playwright
```bash
playwright install chromium
```

### 3. Configurar variables de entorno
Copia la plantilla `.env.example` a `.env`:
```bash
cp .env.example .env
```
*(Si no configuras ninguna API key de LLM, el sistema operará automáticamente con su motor semántico heurístico determinista sin interrupciones).*

---

## 🖥️ Modos de Uso

### 1. Interfaz Web Interactiva
Inicia el servidor web accesible:
```bash
python -m a11y_agent serve --port 8000
```
Abre tu navegador en `http://127.0.0.1:8000`:
- Ingresa la URL a auditar.
- Selecciona la versión de pautas (WCAG 2.0, 2.1 o 2.2) y el nivel (A, AA o AAA).
- Presiona **"Analizar"** para obtener el reporte interactivo, los botones de descarga (HTML, JSON, PDF) y el panel de chat de remediación.

### 2. Modo CLI (Línea de Comandos)
Audita cualquier página web directamente desde la terminal:
```bash
# Auditoría básica con exportación a HTML, JSON y PDF
python -m a11y_agent scan https://ejemplo.com --guidelines "WCAG 2.1" --level AA --export html,json,pdf

# Auditoría de servidor local en desarrollo (flag --allow-private)
python -m a11y_agent scan http://127.0.0.1:8080 --allow-private --export html,json,pdf
```

---

## 🧪 Pruebas Automáticas (3 Escenarios de Referencia)

El proyecto incluye una suite completa de pruebas unitarias y de integración que validan los 3 escenarios exigidos:
1. **Página Accesible** (`fixtures/accessible_page.html`): Caso de referencia con cumplimiento óptimo y puntaje 100/100.
2. **Página con Errores Comunes** (`fixtures/common_errors_page.html`): Detecta imágenes sin alt, contraste deficiente, saltos de títulos, inputs sin label, falta de lang y enlaces ambiguos.
3. **Página Dinámica SPA** (`fixtures/dynamic_spa_page.html`): Contenido generado por JavaScript hidratado en el DOM y auditado con Playwright.

Para ejecutar todas las pruebas (18 pruebas en total):
```bash
pytest tests/ -v
```

---

## 📁 Informes de Muestra Generados

Los informes generados para una auditoría de muestra se encuentran disponibles en la carpeta `reports/`:
- **HTML Interactivo**: [`reports/sample_report.html`](reports/sample_report.html)
- **JSON Estructurado**: [`reports/sample_report.json`](reports/sample_report.json)
- **PDF Vectorial**: [`reports/sample_report.pdf`](reports/sample_report.pdf)
