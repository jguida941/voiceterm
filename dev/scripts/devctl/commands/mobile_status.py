"""devctl mobile-status command implementation."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..common import emit_output, pipe_output, write_output
from ..config import REPO_ROOT
from ..mobile_status_views import (
    render_report_markdown,
    view_payload,
    write_projection_bundle,
)
from ..review_channel_state import (
    projection_paths_to_dict,
    refresh_status_snapshot,
)


def _iso_z(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _resolve_path(raw_path: str) -> Path:
    path = Path(raw_path).expanduser()
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def _load_payload(input_path: Path, *, label: str) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    if not input_path.exists():
        errors.append(f"{label} not found: {input_path}")
        return {}, errors
    try:
        loaded = json.loads(input_path.read_text(encoding="utf-8"))
    except OSError as exc:
        errors.append(str(exc))
        return {}, errors
    except json.JSONDecodeError as exc:
        errors.append(f"invalid json in {label} ({exc})")
        return {}, errors
    if not isinstance(loaded, dict):
        errors.append(f"expected top-level object in {label}")
        return {}, errors
    return loaded, []


def run(args) -> int:
    """Render one merged mobile-safe snapshot from control + review state."""
    warnings: list[str] = []
    errors: list[str] = []

    repo_root = REPO_ROOT.resolve()
    phone_input_path = _resolve_path(str(args.phone_json))
    review_channel_path = _resolve_path(str(args.review_channel_path))
    bridge_path = _resolve_path(str(args.bridge_path))
    review_status_dir = _resolve_path(str(args.review_status_dir))

    controller_payload, load_errors = _load_payload(
        phone_input_path,
        label="phone status artifact",
    )
    if load_errors:
        warnings.extend(load_errors)
        controller_payload = {}

    review_payload: dict[str, Any] = {}
    review_projection_files: dict[str, str] | None = None
    try:
        status_snapshot = refresh_status_snapshot(
            repo_root=repo_root,
            bridge_path=bridge_path,
            review_channel_path=review_channel_path,
            output_root=review_status_dir,
        )
        warnings.extend(status_snapshot.warnings)
        review_projection_files = projection_paths_to_dict(
            status_snapshot.projection_paths
        )
        review_full_path = Path(status_snapshot.projection_paths.full_path)
        review_payload, load_errors = _load_payload(
            review_full_path,
            label="review status projection",
        )
        errors.extend(load_errors)
    except (ValueError, OSError) as exc:
        errors.append(str(exc))

    if not controller_payload and not review_payload:
        errors.append(
            "no live mobile data sources were available; need phone-status or review-channel projections"
        )

    merged_payload: dict[str, Any] = {}
    if not errors:
        merged_payload = {
            "schema_version": 1,
            "command": "mobile-status",
            "timestamp": _iso_z(datetime.now(timezone.utc)),
            "sources": {
                "phone_input_path": str(phone_input_path),
                "review_channel_path": str(review_channel_path),
                "bridge_path": str(bridge_path),
                "review_status_dir": str(review_status_dir),
            },
            "controller_payload": controller_payload,
            "review_payload": review_payload,
        }

    selected_view = view_payload(merged_payload, str(args.view)) if not errors else {}

    projection_files: dict[str, str] = {}
    projection_dir: str | None = None
    if args.emit_projections and not errors:
        projection_root = _resolve_path(str(args.emit_projections))
        projection_files = write_projection_bundle(projection_root, merged_payload)
        projection_dir = str(projection_root)

    report = {
        "command": "mobile-status",
        "timestamp": _iso_z(datetime.now(timezone.utc)),
        "ok": not errors,
        "phone_input_path": str(phone_input_path),
        "review_channel_path": str(review_channel_path),
        "bridge_path": str(bridge_path),
        "review_status_dir": str(review_status_dir),
        "review_projection_files": review_projection_files,
        "view": str(args.view),
        "view_payload": selected_view,
        "projection_dir": projection_dir,
        "projection_files": projection_files,
        "warnings": warnings,
        "errors": errors,
    }

    json_payload = json.dumps(report, indent=2)
    output = json_payload if args.format == "json" else render_report_markdown(report)
    pipe_code = emit_output(
        output,
        output_path=args.output,
        pipe_command=args.pipe_command,
        pipe_args=args.pipe_args,
        additional_outputs=[(json_payload, args.json_output)] if args.json_output else None,
        writer=write_output,
        piper=pipe_output,
    )
    if pipe_code != 0:
        return pipe_code
    return 0 if report["ok"] else 1
