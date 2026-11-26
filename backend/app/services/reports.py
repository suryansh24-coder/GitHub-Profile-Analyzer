from __future__ import annotations

import csv
import io
import json
from typing import Any

SUPPORTED = {"json", "csv", "markdown"}


def export_report(payload: dict[str, Any], format: str, title: str = "Analysis report") -> dict[str, str]:
    if format not in SUPPORTED:
        raise ValueError("Unsupported export format.")
    if format == "json":
        return {"filename": "report.json", "contentType": "application/json", "content": json.dumps(payload, indent=2, ensure_ascii=False, default=str)}

    if format == "csv":
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["section", "key", "value"])
        for section, value in payload.items():
            if isinstance(value, dict):
                for key, item in value.items():
                    if isinstance(item, (list, dict)):
                        item = json.dumps(item, ensure_ascii=False, default=str)
                    writer.writerow([section, key, item])
            elif isinstance(value, list):
                for index, item in enumerate(value):
                    if isinstance(item, (list, dict)):
                        item = json.dumps(item, ensure_ascii=False, default=str)
                    writer.writerow([section, f"item-{index + 1}", item])
            else:
                writer.writerow([section, "-", value])
        return {"filename": "report.csv", "contentType": "text/csv", "content": buffer.getvalue()}

    lines = [f"# {title}", "", f"Generated: {payload.get('generatedAt', 'unknown')}", ""]
    for section, value in payload.items():
        if section == "generatedAt":
            continue
        lines.extend([f"## {section.replace('_', ' ').title()}", ""])
        if isinstance(value, dict):
            for key, item in value.items():
                rendered = json.dumps(item, ensure_ascii=False, default=str) if isinstance(item, (list, dict)) else str(item)
                lines.append(f"- **{key}**: {rendered}")
        elif isinstance(value, list):
            for item in value[:30]:
                lines.append(f"- {json.dumps(item, ensure_ascii=False, default=str) if isinstance(item, (list, dict)) else item}")
        else:
            lines.append(str(value))
        lines.append("")
    return {"filename": "report.md", "contentType": "text/markdown", "content": "\n".join(lines)}
