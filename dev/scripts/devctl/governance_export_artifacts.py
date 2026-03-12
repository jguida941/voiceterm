"""Generated artifact helpers for portable governance exports."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .commands import quality_policy as quality_policy_command
from .data_science.metrics import run_data_science_snapshot
from .quality_policy import resolve_quality_policy
from .review_probe_report import (
    build_probe_report,
    render_probe_report_markdown,
    resolve_probe_report_path,
)


def write_generated_artifacts(
    *,
    snapshot_dir: Path,
    repo_root: Path,
    policy_path: str | Path | None,
    since_ref: str | None,
    head_ref: str,
) -> dict[str, str]:
    """Write fresh portable review artifacts under the exported snapshot."""
    generated_dir = snapshot_dir / "generated"
    generated_dir.mkdir(parents=True, exist_ok=True)

    quality_output_dir = generated_dir / "quality_policy"
    quality_output_dir.mkdir(parents=True, exist_ok=True)
    policy = resolve_quality_policy(
        repo_root=repo_root,
        policy_path=policy_path,
    )
    quality_payload = quality_policy_command.QualityPolicyPayload(
        command="quality-policy",
        repo_name=policy.repo_name,
        policy_path=str(policy.policy_path),
        schema_version=policy.schema_version,
        capabilities=quality_policy_command.CapabilityPayload(
            python=policy.capabilities.python,
            rust=policy.capabilities.rust,
        ),
        quality_scopes=quality_policy_command.ScopePayload(
            python_guard_roots=[path.as_posix() for path in policy.scopes.python_guard_roots],
            python_probe_roots=[path.as_posix() for path in policy.scopes.python_probe_roots],
            rust_guard_roots=[path.as_posix() for path in policy.scopes.rust_guard_roots],
            rust_probe_roots=[path.as_posix() for path in policy.scopes.rust_probe_roots],
        ),
        ai_guard_checks=[quality_policy_command._step_payload(spec) for spec in policy.ai_guard_checks],
        review_probe_checks=[quality_policy_command._step_payload(spec) for spec in policy.review_probe_checks],
        guard_configs=policy.guard_configs,
        warnings=list(policy.warnings),
    )
    quality_json_path = quality_output_dir / "quality_policy.json"
    quality_md_path = quality_output_dir / "quality_policy.md"
    quality_json_path.write_text(json.dumps(asdict(quality_payload), indent=2), encoding="utf-8")
    quality_md_path.write_text(
        quality_policy_command._render_markdown(policy),
        encoding="utf-8",
    )
    artifacts = {
        "quality_policy_json": str(quality_json_path),
        "quality_policy_md": str(quality_md_path),
    }

    probe_output_dir = generated_dir / "probe_report"
    report = build_probe_report(
        policy_path=policy_path,
        since_ref=since_ref,
        head_ref=head_ref,
        emit_artifacts=True,
        output_root=resolve_probe_report_path(probe_output_dir),
    )
    summary_json_path = probe_output_dir / "latest" / "summary.json"
    summary_md_path = probe_output_dir / "latest" / "summary.md"
    if not summary_json_path.exists():
        summary_json_path.parent.mkdir(parents=True, exist_ok=True)
        summary_json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    if not summary_md_path.exists():
        summary_md_path.write_text(
            render_probe_report_markdown(report),
            encoding="utf-8",
        )
    artifacts.update(
        {
            "probe_report_json": str(summary_json_path),
            "probe_report_md": str(summary_md_path),
        }
    )
    for name, path in (report.get("artifact_paths") or {}).items():
        if isinstance(path, str):
            artifacts[f"probe_{name}"] = path

    data_science_report = run_data_science_snapshot(
        trigger_command="devctl:governance-export",
        output_root=str(generated_dir / "data_science"),
    )
    paths = data_science_report.get("paths") or {}
    artifacts.update(
        {
            "data_science_json": str(paths.get("summary_json") or ""),
            "data_science_md": str(paths.get("summary_md") or ""),
            "data_science_history_jsonl": str(paths.get("history_jsonl") or ""),
        }
    )
    return artifacts
