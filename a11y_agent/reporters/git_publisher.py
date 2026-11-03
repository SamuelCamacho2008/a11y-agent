"""Publisher and synchronizer for GitHub Pages public reports and documentation portal."""

import os
import json
import logging
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone

from a11y_agent.core.config import settings
from a11y_agent.models.schema import A11yReport
from a11y_agent.reporters.html_reporter import export_to_html
from a11y_agent.reporters.json_reporter import export_to_json

logger = logging.getLogger("a11y_agent.reporters.git_publisher")

PORTAL_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>A11y Agent — Portal de Informes Públicos de Accesibilidad</title>
    <meta name="description" content="Portal público de auditorías de accesibilidad web (WCAG 2.1/2.2) y aplicaciones móviles Android (EN 301 549).">
    <style>
        :root {
            --bg-color: #0f172a;
            --surface-color: #1e293b;
            --surface-card: #243046;
            --border-color: #334155;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --primary: #38bdf8;
            --primary-hover: #0284c7;
            --success: #22c55e;
            --warning: #f59e0b;
            --danger: #ef4444;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }

        body {
            font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-main);
            line-height: 1.6;
            padding: 2rem 1rem;
        }

        .container {
            max-width: 1100px;
            margin: 0 auto;
        }

        header.portal-header {
            text-align: center;
            margin-bottom: 2.5rem;
            padding-bottom: 2rem;
            border-bottom: 1px solid var(--border-color);
        }

        .badge-repo {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            background: rgba(56, 189, 248, 0.1);
            color: var(--primary);
            border: 1px solid rgba(56, 189, 248, 0.25);
            padding: 0.35rem 0.85rem;
            border-radius: 9999px;
            font-size: 0.85rem;
            font-weight: 600;
            margin-bottom: 1rem;
            text-decoration: none;
        }

        .badge-repo:hover {
            background: rgba(56, 189, 248, 0.2);
        }

        h1 {
            font-size: 2.5rem;
            font-weight: 800;
            color: #ffffff;
            margin-bottom: 0.75rem;
            letter-spacing: -0.025em;
        }

        .subtitle {
            color: var(--text-muted);
            font-size: 1.15rem;
            max-width: 750px;
            margin: 0 auto;
        }

        /* Search Section */
        .search-box {
            background: var(--surface-color);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1.75rem;
            margin-bottom: 2.5rem;
            box-shadow: 0 10px 25px -5px rgba(0,0,0,0.3);
        }

        .search-form {
            display: flex;
            gap: 0.75rem;
            flex-wrap: wrap;
        }

        .search-input {
            flex: 1 1 300px;
            background: var(--surface-card);
            border: 1px solid var(--border-color);
            color: #ffffff;
            padding: 0.85rem 1.25rem;
            border-radius: 8px;
            font-size: 1rem;
            outline: none;
            transition: border-color 0.2s;
        }

        .search-input:focus {
            border-color: var(--primary);
            box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.3);
        }

        .btn-submit {
            background: var(--primary);
            color: #0f172a;
            font-weight: 700;
            border: none;
            padding: 0.85rem 1.5rem;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1rem;
            transition: background 0.2s, transform 0.1s;
        }

        .btn-submit:hover {
            background: var(--primary-hover);
            color: #ffffff;
            transform: translateY(-1px);
        }

        /* Reports Grid */
        .section-title {
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 1.25rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .reports-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 1.25rem;
            margin-bottom: 3rem;
        }

        .report-card {
            background: var(--surface-color);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 1.25rem;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            transition: transform 0.2s, border-color 0.2s;
        }

        .report-card:hover {
            transform: translateY(-2px);
            border-color: var(--primary);
        }

        .card-top {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 0.75rem;
        }

        .tag-pill {
            display: inline-block;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
        }

        .tag-web { background: rgba(56, 189, 248, 0.15); color: var(--primary); }
        .tag-apk { background: rgba(34, 197, 94, 0.15); color: var(--success); }

        .score-pill {
            font-size: 1.2rem;
            font-weight: 800;
            padding: 0.25rem 0.65rem;
            border-radius: 6px;
        }

        .score-high { background: rgba(34, 197, 94, 0.2); color: var(--success); }
        .score-mid { background: rgba(245, 158, 11, 0.2); color: var(--warning); }
        .score-low { background: rgba(239, 68, 68, 0.2); color: var(--danger); }

        .card-title {
            font-size: 1.05rem;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 0.35rem;
            word-break: break-all;
        }

        .card-date {
            font-size: 0.8rem;
            color: var(--text-muted);
            margin-bottom: 1rem;
        }

        .card-metrics {
            display: flex;
            gap: 1rem;
            font-size: 0.85rem;
            margin-bottom: 1rem;
            padding: 0.5rem 0;
            border-top: 1px solid var(--border-color);
            border-bottom: 1px solid var(--border-color);
        }

        .card-link {
            display: inline-block;
            text-align: center;
            background: var(--surface-card);
            border: 1px solid var(--border-color);
            color: var(--primary);
            font-weight: 600;
            text-decoration: none;
            padding: 0.6rem;
            border-radius: 6px;
            transition: background 0.2s, color 0.2s;
        }

        .card-link:hover {
            background: var(--primary);
            color: #0f172a;
        }

        footer {
            text-align: center;
            color: var(--text-muted);
            font-size: 0.9rem;
            padding-top: 2rem;
            border-top: 1px solid var(--border-color);
        }
        footer a { color: var(--primary); text-decoration: none; }
        footer a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="container">
        <header class="portal-header">
            <a href="https://github.com/SamuelCamacho2008/a11y-agent" target="_blank" rel="noopener" class="badge-repo">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/></svg>
                GitHub Repository: SamuelCamacho2008/a11y-agent
            </a>
            <h1>A11y Agent — Informes Públicos</h1>
            <p class="subtitle">
                Plataforma de auditoría inteligente de accesibilidad web (WCAG 2.1 / 2.2) y aplicaciones móviles Android (EN 301 549). Informes compartibles de alta fidelidad alojados en GitHub Pages.
            </p>
        </header>

        <section class="search-box" aria-label="Búsqueda de informe">
            <h2 style="font-size: 1.2rem; margin-bottom: 0.75rem; color: #ffffff;">Buscar Informe por Identificador</h2>
            <form class="search-form" id="searchForm" onsubmit="handleSearch(event)">
                <input
                    type="text"
                    id="reportIdInput"
                    class="search-input"
                    placeholder="Ingrese el ID del informe (ej: rep_9a52de7d12f458c0...)"
                    required
                />
                <button type="submit" class="btn-submit">Abrir Informe</button>
            </form>
        </section>

        <main>
            <div class="section-title">
                <h2>Informes Recientes Publicados</h2>
                <span id="reportsCount" style="font-size: 0.9rem; color: var(--text-muted); font-weight: normal;">Cargando...</span>
            </div>

            <div class="reports-grid" id="reportsGrid">
                <!-- Se inyecta dinámicamente desde reports.json -->
            </div>
        </main>

        <footer>
            <p>
                A11y Agent &copy; 2026 &mdash; Basado en el Modelo TAW y las Pautas W3C WCAG 2.2 / EN 301 549.
                <br>
                Alojado públicamente a través de <a href="https://pages.github.com/" target="_blank" rel="noopener">GitHub Pages</a>.
            </p>
        </footer>
    </div>

    <script>
        // Si la URL contiene ?report=rep_..., redirigir directamente
        const params = new URLSearchParams(window.location.search);
        const reportParam = params.get('report');
        if (reportParam && reportParam.match(/^rep_[a-f0-9]+$/)) {
            window.location.href = './reports/' + reportParam + '.html';
        }

        function handleSearch(e) {
            e.preventDefault();
            const val = document.getElementById('reportIdInput').value.trim();
            if (val) {
                const cleanId = val.replace(/\\.html$/, '');
                window.location.href = './reports/' + cleanId + '.html';
            }
        }

        async function loadReports() {
            const grid = document.getElementById('reportsGrid');
            const countElem = document.getElementById('reportsCount');
            try {
                const res = await fetch('./reports.json');
                if (!res.ok) throw new Error('No se pudo cargar el índice de informes');
                const data = await res.json();
                const reports = Array.isArray(data) ? data : (data.reports || []);

                countElem.textContent = reports.length + ' informe(s) disponible(s)';
                if (reports.length === 0) {
                    grid.innerHTML = '<p style="color: var(--text-muted); grid-column: 1 / -1; text-align: center; padding: 2rem;">No hay informes públicos registrados aún.</p>';
                    return;
                }

                grid.innerHTML = reports.map(r => {
                    const isApk = r.target_type === 'apk';
                    const score = r.score ?? 0;
                    const scoreClass = score >= 80 ? 'score-high' : (score >= 50 ? 'score-mid' : 'score-low');
                    const targetName = r.app_name || r.package_name || r.url || 'Recurso auditado';
                    const dateStr = r.timestamp ? new Date(r.timestamp).toLocaleDateString() : '';

                    return `
                        <article class="report-card">
                            <div>
                                <div class="card-top">
                                    <span class="tag-pill ${isApk ? 'tag-apk' : 'tag-web'}">${isApk ? 'Android APK' : 'Sitio Web'}</span>
                                    <span class="score-pill ${scoreClass}">${score}</span>
                                </div>
                                <h3 class="card-title">${targetName}</h3>
                                <div class="card-date">${dateStr} &bull; ID: <code>${r.id.substring(0, 14)}...</code></div>
                                <div class="card-metrics">
                                    <span style="color: var(--danger);"><strong>${r.total_problems ?? 0}</strong> problemas</span>
                                    <span style="color: var(--warning);"><strong>${r.total_warnings ?? 0}</strong> advertencias</span>
                                </div>
                            </div>
                            <a href="./reports/${r.id}.html" class="card-link">Ver Informe Completo &rarr;</a>
                        </article>
                    `;
                }).join('');
            } catch (err) {
                countElem.textContent = 'Modo estático';
                grid.innerHTML = '<p style="color: var(--text-muted); grid-column: 1 / -1; text-align: center; padding: 2rem;">Utilice el buscador superior para acceder a un informe con su identificador público.</p>';
            }
        }

        loadReports();
    </script>
</body>
</html>
"""

def update_docs_manifest(report: A11yReport) -> Path:
    """
    Maintains `docs/reports.json` with metadata for all published reports.
    """
    manifest_path = settings.docs_dir / "reports.json"
    reports_list: List[Dict[str, Any]] = []

    if manifest_path.exists():
        try:
            content = manifest_path.read_text(encoding="utf-8")
            reports_list = json.loads(content)
            if not isinstance(reports_list, list):
                reports_list = []
        except Exception:
            reports_list = []

    # Update or prepend current report entry
    entry = {
        "id": report.id,
        "target_type": report.target_type,
        "url": report.metadata.url,
        "app_name": report.metadata.app_name or report.app_name,
        "package_name": report.metadata.package_name or report.package_name,
        "score": report.summary.score,
        "total_problems": report.summary.total_problems,
        "total_warnings": report.summary.total_warnings,
        "guidelines": report.metadata.guidelines.value,
        "target_level": report.metadata.target_level.value,
        "timestamp": report.metadata.timestamp.isoformat(),
        "public_url": f"{settings.github_pages_base_url}/reports/{report.id}.html"
    }

    # Filter out existing with same id if already present
    reports_list = [r for r in reports_list if r.get("id") != report.id]
    reports_list.insert(0, entry)  # Prepend newest

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(reports_list, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest_path

def generate_portal_html() -> Path:
    """Ensure `docs/index.html` portal exists and is up to date."""
    portal_path = settings.docs_dir / "index.html"
    portal_path.parent.mkdir(parents=True, exist_ok=True)
    portal_path.write_text(PORTAL_HTML_TEMPLATE, encoding="utf-8")
    return portal_path

def publish_report_to_docs(report: A11yReport) -> Dict[str, Any]:
    """
    Saves report HTML and JSON to the `docs/reports/` directory for GitHub Pages hosting,
    updates `docs/reports.json`, and ensures `docs/index.html` portal is ready.
    """
    settings.docs_reports_dir.mkdir(parents=True, exist_ok=True)

    html_file = settings.docs_reports_dir / f"{report.id}.html"
    json_file = settings.docs_reports_dir / f"{report.id}.json"

    export_to_html(report, html_file)
    export_to_json(report, json_file)

    update_docs_manifest(report)
    generate_portal_html()

    gh_url = f"{settings.github_pages_base_url}/reports/{report.id}.html"

    logger.info(f"Report {report.id} published to GitHub Pages structure: {gh_url}")
    return {
        "report_id": report.id,
        "html_path": str(html_file),
        "json_path": str(json_file),
        "github_pages_url": gh_url
    }

def git_push_report(report_id: str, commit_message: Optional[str] = None) -> Dict[str, Any]:
    """
    Stages `docs/`, commits, and pushes changes to the configured git remote and branch.
    Safely captures errors to prevent breaking runtime execution if network is unavailable.
    """
    gh_url = f"{settings.github_pages_base_url}/reports/{report_id}.html"
    
    try:
        # Check if git is available
        shutil.which("git")
    except Exception:
        return {
            "success": False,
            "message": "Herramienta git no disponible en el sistema.",
            "github_pages_url": gh_url
        }

    git_env = {
        **os.environ,
        "GIT_TERMINAL_PROMPT": "0",
        "GCM_INTERACTIVE": "never",
        "GIT_HTTP_CONNECT_TIMEOUT": "5",
        "GIT_CLIENT_CONNECT_TIMEOUT": "5"
    }

    try:
        # 1. git add docs/
        subprocess.run(
            ["git", "add", "docs/"],
            cwd=str(settings.base_dir),
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
            env=git_env
        )

        # 2. Check if there are changes to commit
        diff_proc = subprocess.run(
            ["git", "diff", "--staged", "--name-only"],
            cwd=str(settings.base_dir),
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
            env=git_env
        )
        staged_files = diff_proc.stdout.strip()

        if not staged_files:
            return {
                "success": True,
                "message": "Los archivos de GitHub Pages ya se encuentran actualizados en el repositorio.",
                "github_pages_url": gh_url
            }

        # 3. Commit
        msg = commit_message or f"docs(reports): publish public report {report_id} to GitHub Pages"
        subprocess.run(
            ["git", "commit", "-m", msg],
            cwd=str(settings.base_dir),
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
            env=git_env
        )

        # 4. Push to remote with timeout
        remote = settings.git_remote
        branch = settings.git_branch
        push_proc = subprocess.run(
            ["git", "push", remote, branch],
            cwd=str(settings.base_dir),
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
            env=git_env
        )

        logger.info(f"Report {report_id} pushed successfully to {remote}/{branch}")
        return {
            "success": True,
            "message": f"Informe sincronizado y publicado en GitHub Pages exitosamente.",
            "github_pages_url": gh_url,
            "commit_message": msg
        }

    except subprocess.TimeoutExpired:
        logger.warning("Timeout al conectar con Git remoto.")
        return {
            "success": False,
            "message": "Tiempo de espera agotado al conectar con el repositorio Git remoto.",
            "github_pages_url": gh_url
        }
    except subprocess.CalledProcessError as e:
        err_msg = e.stderr or e.stdout or str(e)
        logger.warning(f"Error al sincronizar con Git: {err_msg}")
        return {
            "success": False,
            "message": f"Error al ejecutar git push: {err_msg.strip()}",
            "github_pages_url": gh_url
        }
    except Exception as e:
        logger.error(f"Error inesperado al sincronizar reporte con git: {e}")
        return {
            "success": False,
            "message": str(e),
            "github_pages_url": gh_url
        }
