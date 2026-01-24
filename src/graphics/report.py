"""Reporting helpers for graphics conversions."""

from __future__ import annotations

import json
from typing import Any, Dict, List


def build_report_text(report: Dict[str, Any]) -> str:
    conflicts = report.get("conflicts", [])
    lines = [
        f"mode: {report.get('mode')}",
        f"image_size: {report.get('image_size')}",
        f"palette_used: {len(report.get('palette_used', []))} colors",
        f"conflicts: {len(conflicts)}",
    ]
    if conflicts:
        lines.append("conflict_cells:")
        for conflict in conflicts[:25]:
            lines.append(
                f"- cell ({conflict['cell_x']},{conflict['cell_y']}): {conflict['colors']}"
            )
        if len(conflicts) > 25:
            lines.append("... more conflicts omitted")
    return "\n".join(lines) + "\n"


def serialize_report_json(report: Dict[str, Any]) -> str:
    return json.dumps(report, indent=2)
