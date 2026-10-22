"""JSON exporter for A11yReport."""

from pathlib import Path
from a11y_agent.models.schema import A11yReport

def export_to_json(report: A11yReport, output_path: Path) -> Path:
    """Save the complete A11yReport as a formatted JSON document."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    json_data = report.model_dump_json(indent=2)
    output_path.write_text(json_data, encoding="utf-8")
    return output_path
