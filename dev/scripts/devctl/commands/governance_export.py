"""devctl governance-export command implementation."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass

from ..common import emit_output, pipe_output, write_output
from ..governance_export_support import (
    GovernanceExportRequest,
    build_governance_export,
)
from ..quality_scan_mode import resolve_scan_mode


@dataclass(frozen=True, slots=True)
class GovernanceExportPayload:
    """Serializable output payload for one governance export run."""

    command: str
    snapshot_dir: str
    zip_path: str | None
    copied_sources: list[str]
    generated_artifacts: dict[str, str]
    policy_path: str
    created_at_utc: str


def _render_markdown(result) -> str:
    lines = ["# devctl governance-export", ""]
    lines.append(f"- snapshot_dir: {result.snapshot_dir}")
    lines.append(f"- zip_path: {result.zip_path or '(not created)'}")
    lines.append(f"- copied_source_count: {len(result.copied_sources)}")
    lines.append(f"- generated_artifact_count: {len(result.generated_artifacts)}")
    lines.append(f"- policy_path: {result.policy_path}")
    lines.append(f"- created_at_utc: {result.created_at_utc}")
    lines.append("")
    lines.append("## Generated Artifacts")
    lines.append("")
    for key in sorted(result.generated_artifacts):
        lines.append(f"- {key}: {result.generated_artifacts[key]}")
    return "\n".join(lines)


def run(args) -> int:
    """Export the governance stack plus fresh policy/probe/data-science artifacts."""
    try:
        scan_mode = resolve_scan_mode(
            since_ref=getattr(args, "since_ref", None),
            head_ref=getattr(args, "head_ref", "HEAD"),
            adoption_scan=bool(getattr(args, "adoption_scan", False)),
        )
        result = build_governance_export(
            GovernanceExportRequest(
                export_base_dir=getattr(args, "export_base_dir", None),
                snapshot_name=getattr(args, "snapshot_name", None),
                policy_path=getattr(args, "quality_policy", None),
                since_ref=scan_mode.since_ref,
                head_ref=scan_mode.head_ref,
                create_zip=not bool(getattr(args, "no_zip", False)),
                force=bool(getattr(args, "force", False)),
            )
        )
    except ValueError as exc:
        print(f"error: {exc}")
        return 2

    payload = GovernanceExportPayload(
        command="governance-export",
        snapshot_dir=result.snapshot_dir,
        zip_path=result.zip_path,
        copied_sources=list(result.copied_sources),
        generated_artifacts=result.generated_artifacts,
        policy_path=result.policy_path,
        created_at_utc=result.created_at_utc,
    )
    output = (
        json.dumps(asdict(payload), indent=2)
        if args.format == "json"
        else _render_markdown(result)
    )
    pipe_code = emit_output(
        output,
        output_path=args.output,
        pipe_command=args.pipe_command,
        pipe_args=args.pipe_args,
        writer=write_output,
        piper=pipe_output,
    )
    return 0 if pipe_code == 0 else pipe_code
