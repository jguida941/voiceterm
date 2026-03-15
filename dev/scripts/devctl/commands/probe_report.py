"""devctl probe-report command implementation."""

from __future__ import annotations

from pathlib import Path

from ..config import get_repo_root, set_repo_root
from ..runtime.machine_output import ArtifactOutputOptions, emit_machine_artifact_output
from ..quality_policy import resolve_review_probe_script_ids
from ..quality_scan_mode import resolve_scan_mode
from ..review_probe_report import (
    DEFAULT_PROBE_REPORT_OUTPUT_ROOT,
    build_probe_report,
    render_probe_report_markdown,
    render_probe_report_terminal,
)


def run(args) -> int:
    """Run all registered probes and emit one aggregated review-probe report."""
    repo_path = getattr(args, "repo_path", None)
    previous_root = get_repo_root()
    effective_root = None
    if repo_path:
        set_repo_root(Path(repo_path))
        effective_root = get_repo_root()
    try:
        try:
            scan_mode = resolve_scan_mode(
                since_ref=getattr(args, "since_ref", None),
                head_ref=getattr(args, "head_ref", "HEAD"),
                adoption_scan=bool(getattr(args, "adoption_scan", False)),
            )
        except ValueError as exc:
            print(f"error: {exc}")
            return 2
        policy_path = getattr(args, "quality_policy", None)
        probe_ids = resolve_review_probe_script_ids(
            repo_root=effective_root,
            policy_path=policy_path,
        )
        report = build_probe_report(
            since_ref=scan_mode.since_ref,
            head_ref=scan_mode.head_ref,
            emit_artifacts=getattr(args, "emit_artifacts", True),
            output_root=getattr(args, "output_root", DEFAULT_PROBE_REPORT_OUTPUT_ROOT),
            policy_path=policy_path,
            probe_ids=probe_ids,
        )
        if args.format == "terminal":
            human_output = render_probe_report_terminal(report)
        else:
            human_output = render_probe_report_markdown(report)

        return emit_machine_artifact_output(
            args,
            command="probe-report",
            json_payload=report,
            human_output=human_output,
            options=ArtifactOutputOptions(
                ok=bool(report["ok"]),
                summary={
                    "probe_count": ((report.get("summary") or {}).get("probe_count")),
                    "risk_hints": ((report.get("summary") or {}).get("risk_hints")),
                },
                json_output_path=args.json_output,
            ),
        )
    finally:
        if repo_path:
            set_repo_root(previous_root)
