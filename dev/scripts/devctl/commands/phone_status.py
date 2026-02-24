"""devctl phone-status command implementation."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..common import pipe_output, write_output
from ..config import REPO_ROOT
from ..phone_status_views import (
    render_report_markdown,
    view_payload,
    write_projection_bundle,
)


def _iso_z(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _resolve_path(raw_path: str) -> Path:
    path = Path(raw_path).expanduser()
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def _load_payload(input_path: Path) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    if not input_path.exists():
        errors.append(f"phone status artifact not found: {input_path}")
        return {}, errors
    try:
        loaded = json.loads(input_path.read_text(encoding="utf-8"))
    except OSError as exc:
        errors.append(str(exc))
        return {}, errors
    except json.JSONDecodeError as exc:
        errors.append(f"invalid json ({exc})")
        return {}, errors
    if not isinstance(loaded, dict):
        errors.append("expected top-level object in phone status artifact")
        return {}, errors
    return loaded, []


def run(args) -> int:
    """Render one phone-oriented autonomy status view from latest queue artifact."""
    warnings: list[str] = []
    errors: list[str] = []

    input_path = _resolve_path(str(args.phone_json))
    payload, load_errors = _load_payload(input_path)
    errors.extend(load_errors)

    selected_view = view_payload(payload, str(args.view)) if not errors else {}

    projection_files: dict[str, str] = {}
    projection_dir: str | None = None
    if args.emit_projections and not errors:
        projection_root = _resolve_path(str(args.emit_projections))
        projection_files = write_projection_bundle(projection_root, payload)
        projection_dir = str(projection_root)

    report = {
        "command": "phone-status",
        "timestamp": _iso_z(datetime.now(timezone.utc)),
        "ok": not errors,
        "input_path": str(input_path),
        "view": str(args.view),
        "view_payload": selected_view,
        "projection_dir": projection_dir,
        "projection_files": projection_files,
        "warnings": warnings,
        "errors": errors,
    }

    output = (
        json.dumps(report, indent=2)
        if args.format == "json"
        else render_report_markdown(report)
    )
    write_output(output, args.output)
    if args.json_output:
        write_output(json.dumps(report, indent=2), args.json_output)
    if args.pipe_command:
        pipe_code = pipe_output(output, args.pipe_command, args.pipe_args)
        if pipe_code != 0:
            return pipe_code
    return 0 if report["ok"] else 1
