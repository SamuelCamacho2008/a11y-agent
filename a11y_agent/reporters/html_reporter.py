"""Accessible HTML report generator inspired by TAW, styled with modern accessible CSS."""

from pathlib import Path
from jinja2 import Template
from a11y_agent.models.schema import A11yReport

HTML_REPORT_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Informe de Accesibilidad - {{ report.metadata.url }} | A11y Agent</title>
    <style>
        :root {
            --bg-main: #f8fafc;
            --bg-card: #ffffff;
            --text-main: #0f172a;
            --text-muted: #475569;
            --border-color: #cbd5e1;
            --primary: #0284c7;
            --primary-dark: #0369a1;
            --danger: #dc2626;
            --danger-bg: #fef2f2;
            --warning: #d97706;
            --warning-bg: #fffbeb;
            --info: #2563eb;
            --info-bg: #eff6ff;
            --success: #16a34a;
            --success-bg: #f0fdf4;
        }

        body {
            font-family: system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg-main);
            color: var(--text-main);
            line-height: 1.6;
            margin: 0;
            padding: 1.5rem;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        header.report-header {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1.75rem;
            margin-bottom: 2rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }

        h1 {
            margin-top: 0;
            color: var(--text-main);
            font-size: 1.75rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .meta-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 1rem;
            margin-top: 1.25rem;
            padding-top: 1rem;
            border-top: 1px solid var(--border-color);
        }

        .meta-item strong {
            display: block;
            color: var(--text-muted);
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .meta-item span {
            font-size: 1rem;
            font-weight: 600;
            word-break: break-all;
        }

        .tech-badge {
            display: inline-block;
            background: #e2e8f0;
            color: #1e293b;
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
            font-size: 0.8rem;
            margin-right: 0.35rem;
            margin-top: 0.25rem;
        }

        /* Summary Dashboard */
        .summary-dashboard {
            display: grid;
            grid-template-columns: 220px 1fr;
            gap: 1.5rem;
            margin-bottom: 2rem;
        }

        @media (max-width: 768px) {
            .summary-dashboard {
                grid-template-columns: 1fr;
            }
        }

        .score-box {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1.5rem;
            text-align: center;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
        }

        .score-circle {
            width: 110px;
            height: 110px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 2.25rem;
            font-weight: 800;
            margin-bottom: 0.75rem;
            border: 6px solid;
        }

        .score-high { border-color: var(--success); color: var(--success); }
        .score-mid { border-color: var(--warning); color: var(--warning); }
        .score-low { border-color: var(--danger); color: var(--danger); }

        .kpi-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 1rem;
            margin-bottom: 1rem;
        }

        .kpi-card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1rem;
            border-left: 5px solid;
        }

        .kpi-card.danger { border-left-color: var(--danger); }
        .kpi-card.warning { border-left-color: var(--warning); }
        .kpi-card.info { border-left-color: var(--info); }

        .kpi-number {
            font-size: 1.8rem;
            font-weight: 700;
            line-height: 1;
            margin-bottom: 0.25rem;
        }

        .kpi-label {
            color: var(--text-muted);
            font-size: 0.85rem;
            font-weight: 600;
        }

        .exec-summary-box {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1.25rem;
        }

        .exec-summary-box h3 {
            margin-top: 0;
            font-size: 1.1rem;
            margin-bottom: 0.5rem;
        }

        .exec-summary-text {
            white-space: pre-line;
            color: var(--text-main);
            font-size: 0.95rem;
        }

        /* Principles & Criteria Tables */
        .principle-section {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            margin-bottom: 2rem;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }

        .principle-header {
            background: #f1f5f9;
            padding: 1rem 1.5rem;
            border-bottom: 1px solid var(--border-color);
        }

        .principle-header h2 {
            margin: 0;
            font-size: 1.35rem;
            color: #0f172a;
        }

        .principle-desc {
            margin: 0.25rem 0 0 0;
            color: var(--text-muted);
            font-size: 0.9rem;
        }

        .criterion-block {
            padding: 1.25rem 1.5rem;
            border-bottom: 1px solid var(--border-color);
        }

        .criterion-block:last-child {
            border-bottom: none;
        }

        .criterion-title {
            font-size: 1.1rem;
            font-weight: 700;
            margin: 0 0 0.75rem 0;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .badge-level {
            background: #0f172a;
            color: #ffffff;
            font-size: 0.75rem;
            padding: 0.15rem 0.45rem;
            border-radius: 3px;
        }

        /* TAW-like table */
        table.taw-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9rem;
            margin-top: 0.75rem;
        }

        table.taw-table th, table.taw-table td {
            border: 1px solid var(--border-color);
            padding: 0.65rem 0.85rem;
            text-align: left;
            vertical-align: top;
        }

        table.taw-table th {
            background: #f8fafc;
            color: #334155;
            font-weight: 600;
        }

        .badge-cat {
            display: inline-block;
            font-size: 0.75rem;
            font-weight: 700;
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
            text-align: center;
        }

        .badge-cat.problema {
            background: var(--danger-bg);
            color: var(--danger);
            border: 1px solid #fecaca;
        }

        .badge-cat.advertencia {
            background: var(--warning-bg);
            color: var(--warning);
            border: 1px solid #fed7aa;
        }

        .badge-origin {
            display: inline-block;
            font-size: 0.7rem;
            padding: 0.15rem 0.4rem;
            border-radius: 3px;
            text-transform: uppercase;
            font-weight: 700;
            margin-top: 0.25rem;
        }

        .badge-origin.ia {
            background: #ede9fe;
            color: #6b21a8;
        }

        .badge-origin.regla {
            background: #e0f2fe;
            color: #0369a1;
        }

        code.snippet {
            display: block;
            background: #1e293b;
            color: #f8fafc;
            padding: 0.5rem;
            border-radius: 4px;
            font-family: Consolas, Monaco, "Courier New", monospace;
            font-size: 0.82rem;
            overflow-x: auto;
            max-width: 500px;
            white-space: pre-wrap;
            word-break: break-all;
        }

        .remediation-box {
            margin-top: 0.5rem;
            padding: 0.5rem;
            background: #f8fafc;
            border-left: 3px solid var(--success);
            font-size: 0.85rem;
        }

        .diff-code {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0.5rem;
            margin-top: 0.35rem;
        }

        .diff-before {
            background: #fef2f2;
            border: 1px solid #fecaca;
            padding: 0.35rem;
            font-family: monospace;
            font-size: 0.8rem;
            word-break: break-all;
        }

        .diff-after {
            background: #f0fdf4;
            border: 1px solid #bbf7d0;
            padding: 0.35rem;
            font-family: monospace;
            font-size: 0.8rem;
            word-break: break-all;
        }

        footer.report-footer {
            margin-top: 3rem;
            padding: 1.5rem;
            background: #f1f5f9;
            border-radius: 8px;
            font-size: 0.85rem;
            color: var(--text-muted);
            border-left: 4px solid #64748b;
        }

        @media print {
            body { padding: 0; background: #fff; }
            .container { max-width: 100%; }
            .principle-section { break-inside: avoid; margin-bottom: 1.5rem; }
        }
    </style>
</head>
<body>
<div class="container">
    <!-- Header -->
    <header class="report-header">
        <h1>
            <span>&#9855;</span> Informe de Accesibilidad Web (A11y Agent)
        </h1>
        <div class="meta-grid">
            <div class="meta-item">
                <strong>Recurso Analizado</strong>
                <span><a href="{{ report.metadata.url }}" target="_blank" rel="noopener">{{ report.metadata.url }}</a></span>
            </div>
            <div class="meta-item">
                <strong>Fecha y Hora (UTC)</strong>
                <span>{{ report.metadata.timestamp.strftime('%Y-%m-%d %H:%M:%S') }}</span>
            </div>
            <div class="meta-item">
                <strong>Pautas & Nivel</strong>
                <span>{{ report.metadata.guidelines.value }} — Nivel {{ report.metadata.target_level.value }}</span>
            </div>
            <div class="meta-item">
                <strong>Tecnologías Detectadas</strong>
                <div>
                    {% for tech in report.metadata.technologies %}
                    <span class="tech-badge">{{ tech }}</span>
                    {% endfor %}
                </div>
            </div>
        </div>
    </header>

    <!-- Dashboard -->
    <section class="summary-dashboard" aria-label="Resumen ejecutivo">
        <div class="score-box">
            <div class="score-circle {% if report.summary.score >= 80 %}score-high{% elif report.summary.score >= 50 %}score-mid{% else %}score-low{% endif %}">
                {{ report.summary.score }}
            </div>
            <strong>Puntaje Global</strong>
            <small style="color: var(--text-muted);">Escala 0 a 100</small>
        </div>

        <div>
            <div class="kpi-cards">
                <div class="kpi-card danger">
                    <div class="kpi-number" style="color: var(--danger);">{{ report.summary.total_problems }}</div>
                    <div class="kpi-label">Problemas (Fallos Automáticos)</div>
                </div>
                <div class="kpi-card warning">
                    <div class="kpi-number" style="color: var(--warning);">{{ report.summary.total_warnings }}</div>
                    <div class="kpi-label">Advertencias (Revisión/IA)</div>
                </div>
                <div class="kpi-card info">
                    <div class="kpi-number" style="color: var(--info);">{{ report.summary.total_unverified }}</div>
                    <div class="kpi-label">No Verificados</div>
                </div>
            </div>

            <div class="exec-summary-box">
                <h3>Resumen Ejecutivo</h3>
                <div class="exec-summary-text">{{ report.summary.executive_summary }}</div>
            </div>
        </div>
    </section>

    <!-- 4 Principles Sections -->
    {% for p_key, principle in report.principles.items() %}
    <section class="principle-section" aria-labelledby="principle-heading-{{ p_key }}">
        <div class="principle-header">
            <h2 id="principle-heading-{{ p_key }}">{{ principle.name }}</h2>
            <p class="principle-desc">{{ principle.description }}</p>
        </div>

        {% if principle.success_criteria|length == 0 %}
        <div style="padding: 1.5rem; color: var(--success); font-weight: 500;">
            &#10003; No se detectaron problemas ni advertencias en este principio para el nivel seleccionado.
        </div>
        {% else %}
        {% for criterion in principle.success_criteria %}
        <div class="criterion-block">
            <div class="criterion-title">
                <span>{{ criterion.criterion_id }} {{ criterion.criterion_title }}</span>
                <span class="badge-level">Nivel {{ criterion.level.value }}</span>
            </div>

            <table class="taw-table">
                <thead>
                    <tr>
                        <th style="width: 140px;">Resultado</th>
                        <th style="width: 180px;">Comprobación / Técnica</th>
                        <th style="width: 160px;">Ubicación & Línea</th>
                        <th>Incidencia & Solución de Código</th>
                    </tr>
                </thead>
                <tbody>
                    {% for finding in criterion.findings %}
                    <tr>
                        <td>
                            <span class="badge-cat {% if finding.category.value == 'Problema' %}problema{% else %}advertencia{% endif %}">
                                {{ finding.category.value }}
                            </span>
                            <br>
                            <span class="badge-origin {% if finding.origin.value == 'ia' %}ia{% else %}regla{% endif %}">
                                {{ finding.origin.value }}
                            </span>
                            <br>
                            <small style="color: var(--text-muted); font-size: 0.75rem;">Impacto: {{ finding.impact.value }}</small>
                        </td>
                        <td>
                            <strong>{{ finding.check_name }}</strong>
                            <br>
                            <small style="color: var(--text-muted);">Técnica W3C: <strong>{{ finding.w3c_technique }}</strong></small>
                            <br>
                            <small style="color: #64748b;">ID: {{ finding.id }}</small>
                        </td>
                        <td>
                            <strong style="font-size: 0.8rem; font-family: monospace;">{{ finding.selector }}</strong>
                            {% if finding.line_number %}
                            <br>
                            <span style="color: var(--primary-dark); font-weight: 600; font-size: 0.8rem;">
                                Línea HTML: {{ finding.line_number }}
                            </span>
                            {% else %}
                            <br>
                            <small style="color: var(--text-muted);">Línea no indexada</small>
                            {% endif %}
                        </td>
                        <td>
                            <div>{{ finding.explanation }}</div>
                            <div style="margin-top: 0.4rem;">
                                <code class="snippet">{{ finding.html_snippet }}</code>
                            </div>
                            {% if finding.remediation %}
                            <div class="remediation-box">
                                <strong>Solución Sugerida (Esfuerzo {{ finding.remediation.effort.value }}):</strong> {{ finding.remediation.advice }}
                                <div class="diff-code">
                                    <div class="diff-before">
                                        <div style="font-weight: 700; color: var(--danger); font-size: 0.75rem;">Antes:</div>
                                        <code>{{ finding.remediation.before_snippet }}</code>
                                    </div>
                                    <div class="diff-after">
                                        <div style="font-weight: 700; color: var(--success); font-size: 0.75rem;">Después (Accesible):</div>
                                        <code>{{ finding.remediation.after_snippet }}</code>
                                    </div>
                                </div>
                            </div>
                            {% endif %}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% endfor %}
        {% endif %}
    </section>
    {% endfor %}

    <!-- Footer Disclaimer -->
    <footer class="report-footer">
        <strong>Aviso Legal y Metodológico:</strong> {{ report.disclaimer }}
    </footer>
</div>
</body>
</html>
"""

def render_html_report(report: A11yReport) -> str:
    """Render the A11yReport into a self-contained HTML string."""
    template = Template(HTML_REPORT_TEMPLATE)
    return template.render(report=report)

def export_to_html(report: A11yReport, output_path: Path) -> Path:
    """Save the rendered HTML report to a file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    html_content = render_html_report(report)
    output_path.write_text(html_content, encoding="utf-8")
    return output_path
