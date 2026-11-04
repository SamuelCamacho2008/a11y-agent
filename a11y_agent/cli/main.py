"""CLI command-line interface for A11y Agent."""

import asyncio
import argparse
import sys
from pathlib import Path

from a11y_agent.models.schema import GuidelinesVersion, WCAGLevel
from a11y_agent.analyzer.engine import A11yEngine
from a11y_agent.core.config import settings

def parse_args():
    parser = argparse.ArgumentParser(
        prog="a11y_agent",
        description="A11y Agent: Auditor de Accesibilidad Web (WCAG 2.0 / 2.1 / 2.2) potenciado con IA."
    )
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponibles")

    # Command: scan
    scan_parser = subparsers.add_parser("scan", help="Auditar una página web")
    scan_parser.add_argument("url", type=str, help="URL completa de la página a auditar (ej. https://ejemplo.com)")
    scan_parser.add_argument("--guidelines", choices=["WCAG 2.0", "WCAG 2.1", "WCAG 2.2"], default="WCAG 2.1", help="Versión de las pautas WCAG")
    scan_parser.add_argument("--level", choices=["A", "AA", "AAA"], default="AA", help="Nivel de conformidad objetivo")
    scan_parser.add_argument("--export", default="html,json,pdf", help="Formatos de exportación separados por coma (ej. html,json,pdf)")
    scan_parser.add_argument("--allow-private", action="store_true", help="Permitir direcciones IP locales/privadas (uso exclusivo para desarrollo/pruebas)")

    # Command: serve
    serve_parser = subparsers.add_parser("serve", help="Iniciar el servidor web y la API de A11y Agent")
    serve_parser.add_argument("--host", default="127.0.0.1", help="Host de escucha")
    serve_parser.add_argument("--port", type=int, default=8000, help="Puerto de escucha")

    return parser.parse_args()

async def run_cli_scan(args):
    print(f"\n=======================================================")
    print(f"  A11y Agent - Auditor de Accesibilidad Web (WCAG)")
    print(f"=======================================================")
    print(f"URL: {args.url}")
    print(f"Pautas: {args.guidelines} | Nivel: {args.level}")
    print(f"Exportando formatos: {args.export}")
    print(f"Iniciando análisis headless con Playwright y axe-core...")

    engine = A11yEngine()
    formats = [f.strip().lower() for f in args.export.split(",") if f.strip()]

    try:
        report = await engine.run_audit(
            url=args.url,
            guidelines=GuidelinesVersion(args.guidelines),
            target_level=WCAGLevel(args.level),
            allow_private_ips=args.allow_private,
            export_formats=formats
        )

        print("\n-------------------------------------------------------")
        print(f" AUDITORÍA COMPLETADA EXITOSAMENTE (ID: {report.id})")
        print(f" Tiempo de ejecución: {report.metadata.execution_time_seconds}s")
        print("-------------------------------------------------------")
        print(f" Indicador interno: {report.summary.score} / 100")
        print(f" Problemas (Fallos automáticos): {report.summary.total_problems}")
        print(f" Advertencias (Revisión/IA):    {report.summary.total_warnings}")
        print(f" No verificados:                 {report.summary.total_unverified}")
        print("-------------------------------------------------------")
        print(" Resumen Ejecutivo:")
        print(report.summary.executive_summary)
        print("-------------------------------------------------------")
        print(" Archivos Generados:")
        for fmt in formats:
            out_file = settings.reports_dir / f"{report.id}.{fmt}"
            if out_file.exists():
                print(f"  - [{fmt.upper()}]: {out_file}")
        print("-------------------------------------------------------\n")
        return 0
    except Exception as e:
        print(f"\n[ERROR] Falló la auditoría: {e}\n", file=sys.stderr)
        return 1

def main():
    args = parse_args()
    if not args.command:
        print("Especifique un comando (scan o serve). Use --help para ver las opciones.")
        sys.exit(1)

    if args.command == "scan":
        code = asyncio.run(run_cli_scan(args))
        sys.exit(code)
    elif args.command == "serve":
        import uvicorn
        print(f"Iniciando A11y Agent en http://{args.host}:{args.port}")
        uvicorn.run("a11y_agent.api.main:app", host=args.host, port=args.port, reload=False)

if __name__ == "__main__":
    main()
