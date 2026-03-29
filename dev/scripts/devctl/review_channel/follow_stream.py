"""Shared follow-stream helpers for review-channel command publishers."""

from __future__ import annotations

import json
from pathlib import Path

from ..common import emit_output


def validate_follow_json_format(*, action: str, output_format: str) -> None:
    """Enforce the explicit NDJSON contract for follow-mode streams."""
    if output_format != "json":
        raise ValueError(
            f"review-channel {action} --follow requires --format json because "
            "follow output is emitted as NDJSON snapshots."
        )


def reset_follow_output(output_path: str | None) -> None:
    """Reset a follow-stream output file before the first frame is appended."""
    if not output_path:
        return
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")


def emit_follow_ndjson_frame(payload: dict[str, object], *, args) -> int:
    """Emit one follow-mode NDJSON frame through the normal output surfaces."""
    content = json.dumps(payload, sort_keys=True)
    return emit_output(
        content,
        output_path=getattr(args, "output", None),
        pipe_command=getattr(args, "pipe_command", None),
        pipe_args=getattr(args, "pipe_args", None),
        announce_output_path=False,
        writer=_append_stream_writer,
    )


def build_follow_output_error_report(
    *,
    action: str,
    snapshots_emitted: int,
    pipe_rc: int,
) -> dict[str, object]:
    """Build the structured follow-stream output failure report."""
    report: dict[str, object] = {}
    report["command"] = "review-channel"
    report["action"] = action
    report["ok"] = False
    report["follow"] = True
    report["snapshots_emitted"] = snapshots_emitted
    report["errors"] = [f"follow output failed with exit code {pipe_rc}"]
    report["_already_emitted"] = True
    return report


def build_follow_completion_report(
    *,
    action: str,
    snapshots_emitted: int,
    ok: bool,
    reviewer_mode: str | None = None,
) -> dict[str, object]:
    """Build the structured follow-stream completion report."""
    report: dict[str, object] = {}
    report["command"] = "review-channel"
    report["action"] = action
    report["ok"] = ok
    report["follow"] = True
    if reviewer_mode is not None:
        report["reviewer_mode"] = reviewer_mode
    report["snapshots_emitted"] = snapshots_emitted
    report["_already_emitted"] = True
    return report


def _append_stream_writer(
    content: str,
    output_path: str | None,
    *,
    announce_output_path: bool = True,
    stdout_content: str | None = None,
) -> None:
    rendered = stdout_content if stdout_content is not None else content
    if output_path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(rendered)
            if not rendered.endswith("\n"):
                handle.write("\n")
        return
    print(rendered)
