"""devctl system-picture command implementation."""

from __future__ import annotations

from ..runtime.machine_output import ArtifactOutputOptions, emit_machine_artifact_output
from .system_picture import (
    build_system_picture_snapshot,
    resolve_system_picture_ledger_path,
    resolve_system_picture_output_root,
    write_system_picture_artifacts,
    write_system_picture_ledger,
)
from .system_picture_render import render_system_picture_markdown


def run(args) -> int:
    """Build the generated startup/runtime/evidence reducer snapshot."""
    output_root = resolve_system_picture_output_root(args.output_root)
    snapshot = build_system_picture_snapshot()
    artifact_paths = write_system_picture_artifacts(snapshot, output_root=output_root)

    ledger_path = ""
    if getattr(args, "write_ledger", False):
        resolved_ledger_path = resolve_system_picture_ledger_path(args.ledger_path)
        ledger_path = write_system_picture_ledger(
            snapshot,
            ledger_path=resolved_ledger_path,
        )

    payload = snapshot.to_dict()
    payload["command"] = "system-picture"
    payload["output_root"] = str(output_root)
    payload["paths"] = artifact_paths
    payload["write_ledger"] = bool(getattr(args, "write_ledger", False))
    payload["ledger_path"] = ledger_path

    return emit_machine_artifact_output(
        args,
        command="system-picture",
        json_payload=payload,
        human_output=render_system_picture_markdown(snapshot),
        options=ArtifactOutputOptions(
            summary={
                "snapshot_id": snapshot.snapshot_id,
                "current_section_count": snapshot.current_section_count,
                "stale_section_count": snapshot.stale_section_count,
                "missing_section_count": snapshot.missing_section_count,
                "write_ledger": bool(getattr(args, "write_ledger", False)),
            },
            json_output_path=getattr(args, "json_output", None),
        ),
    )
