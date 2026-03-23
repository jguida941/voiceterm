"""Decision-packet field-route closure proofs for platform contract enforcement."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


def check_decision_packet_mode_ralph_route() -> tuple[dict[str, object], dict[str, object] | None]:
    """Verify DecisionPacket.decision_mode reaches the Ralph prompt policy."""
    from dev.scripts.coderabbit.probe_guidance import attach_probe_guidance
    from dev.scripts.coderabbit.ralph_ai_fix import build_prompt

    backlog_items = [
        {
            "severity": "high",
            "category": "rust",
            "summary": "rust/src/auth.rs:12 - Auth contract needs review.",
            "symbol": "validate_auth",
        }
    ]
    report_payload = {
        "findings": [
            {
                "finding_id": "decision-mode-finding",
                "file_path": "rust/src/auth.rs",
                "symbol": "validate_auth",
                "check_id": "probe_design_smells",
                "severity": "high",
                "line": 10,
                "end_line": 14,
                "ai_instruction": "Extract the auth validator helper before editing the caller.",
            }
        ]
    }
    summary_payload = {
        "decision_packets": [
            {
                "finding_id": "decision-mode-finding",
                "file_path": "rust/src/auth.rs",
                "symbol": "validate_auth",
                "check_id": "probe_design_smells",
                "decision_mode": "approval_required",
                "rationale": "Auth contract changes require approval.",
            }
        ]
    }
    coverage: dict[str, object] = {
        "kind": "field_route",
        "contract_id": "DecisionPacket",
        "field_name": "decision_mode",
        "route_id": "ralph_prompt",
        "consumer": "dev.scripts.coderabbit.ralph_ai_fix:build_prompt",
        "ok": True,
    }

    with tempfile.TemporaryDirectory() as tmp_dir:
        report_root = Path(tmp_dir)
        latest = report_root / "latest"
        latest.mkdir(parents=True, exist_ok=True)
        (report_root / "review_targets.json").write_text(
            json.dumps(report_payload),
            encoding="utf-8",
        )
        (latest / "summary.json").write_text(
            json.dumps(summary_payload),
            encoding="utf-8",
        )
        enriched = attach_probe_guidance(backlog_items, report_root=report_root)

    prompt = build_prompt(enriched, attempt=1)
    if "decision_mode=approval_required" in prompt and "request approval" in prompt.lower():
        coverage["detail"] = (
            "DecisionPacket.decision_mode survives the canonical Ralph route "
            "and gates the prompt policy."
        )
        return coverage, None

    detail = (
        "DecisionPacket.decision_mode is available for the Ralph finding but "
        "does not affect the live remediation prompt."
    )
    coverage["ok"] = False
    coverage["detail"] = detail
    return coverage, {
        "kind": "field_route",
        "contract_id": "DecisionPacket",
        "field_name": "decision_mode",
        "route_id": "ralph_prompt",
        "rule": "unconsumed-field-route",
        "detail": detail,
    }


def check_decision_packet_mode_autonomy_route() -> tuple[dict[str, object], dict[str, object] | None]:
    """Verify DecisionPacket.decision_mode reaches the autonomy loop packet."""
    from datetime import UTC, datetime

    from dev.scripts.devctl.commands import loop_packet

    source_payload = {
        "command": "triage-loop",
        "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "branch": "develop",
        "reason": "resolved",
        "unresolved_count": 0,
        "backlog_items": [
            {
                "severity": "high",
                "category": "python",
                "summary": "dev/scripts/devctl/auth.py:12 - Auth flow needs approval.",
                "file_path": "dev/scripts/devctl/auth.py",
                "symbol": "validate_auth",
                "line": 12,
            }
        ],
    }
    review_targets_payload = {
        "findings": [
            {
                "finding_id": "autonomy-decision-mode-finding",
                "file_path": "dev/scripts/devctl/auth.py",
                "symbol": "validate_auth",
                "check_id": "probe_side_effect_mixing",
                "severity": "high",
                "line": 10,
                "end_line": 14,
                "ai_instruction": "Split the auth validator from the retry orchestration before editing the caller.",
            }
        ]
    }
    summary_payload = {
        "decision_packets": [
            {
                "finding_id": "autonomy-decision-mode-finding",
                "file_path": "dev/scripts/devctl/auth.py",
                "symbol": "validate_auth",
                "check_id": "probe_side_effect_mixing",
                "decision_mode": "approval_required",
                "rationale": "Auth contract changes require approval.",
            }
        ]
    }
    coverage: dict[str, object] = {
        "kind": "field_route",
        "contract_id": "DecisionPacket",
        "field_name": "decision_mode",
        "route_id": "autonomy_loop_packet",
        "consumer": "dev.scripts.devctl.commands.loop_packet:run",
        "ok": True,
    }

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_root = Path(tmp_dir)
        source_path = tmp_root / "triage-loop.json"
        output_path = tmp_root / "loop-packet.json"
        report_root = tmp_root / "probes"
        latest = report_root / "latest"
        latest.mkdir(parents=True, exist_ok=True)
        source_path.write_text(json.dumps(source_payload), encoding="utf-8")
        (report_root / "review_targets.json").write_text(
            json.dumps(review_targets_payload),
            encoding="utf-8",
        )
        (latest / "summary.json").write_text(
            json.dumps(summary_payload),
            encoding="utf-8",
        )
        args = SimpleNamespace(
            source_json=[str(source_path)],
            prefer_source="triage-loop",
            max_age_hours=72.0,
            max_draft_chars=1600,
            allow_auto_send=True,
            format="json",
            output=str(output_path),
            pipe_command=None,
            pipe_args=None,
        )
        previous_root = os.environ.get("DEVCTL_PROBE_REPORT_ROOT")
        os.environ["DEVCTL_PROBE_REPORT_ROOT"] = str(report_root)
        try:
            rc = loop_packet.run(args)
        finally:
            if previous_root is None:
                os.environ.pop("DEVCTL_PROBE_REPORT_ROOT", None)
            else:
                os.environ["DEVCTL_PROBE_REPORT_ROOT"] = previous_root
        payload = json.loads(output_path.read_text(encoding="utf-8"))

    guidance_contract = payload.get("guidance_contract")
    terminal_packet = payload.get("terminal_packet")
    if (
        rc == 0
        and isinstance(guidance_contract, dict)
        and guidance_contract.get("approval_required") is True
        and isinstance(terminal_packet, dict)
        and terminal_packet.get("auto_send") is False
    ):
        coverage["detail"] = (
            "DecisionPacket.decision_mode survives the autonomy route and "
            "blocks auto-send for approval-required guidance."
        )
        return coverage, None

    detail = (
        "DecisionPacket.decision_mode is available for the autonomy slice but "
        "does not gate the emitted loop packet."
    )
    coverage["ok"] = False
    coverage["detail"] = detail
    return coverage, {
        "kind": "field_route",
        "contract_id": "DecisionPacket",
        "field_name": "decision_mode",
        "route_id": "autonomy_loop_packet",
        "rule": "unconsumed-field-route",
        "detail": detail,
    }


def check_decision_packet_mode_guard_run_route() -> tuple[dict[str, object], dict[str, object] | None]:
    """Verify DecisionPacket.decision_mode reaches the guard-run report."""
    from dev.scripts.devctl.commands.guard_run import build_guard_run_report
    from dev.scripts.devctl.guard_run_core import (
        GuardGitSnapshot,
        GuardRunRequest,
        build_guard_run_markdown,
    )

    review_targets_payload = {
        "findings": [
            {
                "finding_id": "guard-run-decision-mode-finding",
                "file_path": "dev/scripts/devctl/commands/guard_run.py",
                "check_id": "probe_side_effect_mixing",
                "severity": "high",
                "line": 42,
                "end_line": 58,
                "ai_instruction": "Split the guard-run follow-up repair plan from the shell wrapper logic.",
            }
        ]
    }
    summary_payload = {
        "decision_packets": [
            {
                "finding_id": "guard-run-decision-mode-finding",
                "file_path": "dev/scripts/devctl/commands/guard_run.py",
                "check_id": "probe_side_effect_mixing",
                "decision_mode": "approval_required",
                "rationale": "Guard-run flow changes require approval.",
            }
        ]
    }
    coverage: dict[str, object] = {
        "kind": "field_route",
        "contract_id": "DecisionPacket",
        "field_name": "decision_mode",
        "route_id": "guard_run_report",
        "consumer": "dev.scripts.devctl.commands.guard_run:build_guard_run_report",
        "ok": True,
    }
    guarded_command = [
        "python3",
        "dev/scripts/devctl.py",
        "docs-check",
        "--strict-tooling",
    ]

    with tempfile.TemporaryDirectory() as tmp_dir:
        report_root = Path(tmp_dir)
        latest = report_root / "latest"
        latest.mkdir(parents=True, exist_ok=True)
        (report_root / "review_targets.json").write_text(
            json.dumps(review_targets_payload),
            encoding="utf-8",
        )
        (latest / "summary.json").write_text(
            json.dumps(summary_payload),
            encoding="utf-8",
        )
        before = GuardGitSnapshot(
            reviewed_worktree_hash="abc123",
            files_changed=("dev/scripts/devctl/commands/guard_run.py",),
            file_count=1,
        )
        after = GuardGitSnapshot(
            reviewed_worktree_hash="abc123",
            files_changed=("dev/scripts/devctl/commands/guard_run.py",),
            file_count=1,
            lines_added=4,
            lines_removed=1,
            diff_churn=5,
        )
        with (
            patch.dict("os.environ", {"DEVCTL_PROBE_REPORT_ROOT": str(report_root)}, clear=False),
            patch(
                "dev.scripts.devctl.commands.guard_run.capture_guard_git_snapshot",
                side_effect=[before, after],
            ),
            patch(
                "dev.scripts.devctl.commands.guard_run.run_cmd",
                side_effect=[{"returncode": 0}, {"returncode": 0}],
            ),
        ):
            report = build_guard_run_report(
                GuardRunRequest(
                    command_args=guarded_command,
                    cwd=None,
                    requested_post_action="cleanup",
                    label="contract-closure-guard-run",
                    dry_run=False,
                )
            )

    markdown = build_guard_run_markdown(report)
    if report.get("guidance_requires_approval") is True and "decision_mode=approval_required" in markdown:
        coverage["detail"] = (
            "DecisionPacket.decision_mode survives the guard-run route and "
            "marks the follow-up packet as approval-gated."
        )
        return coverage, None

    detail = (
        "DecisionPacket.decision_mode is available for guard-run follow-up scope "
        "but does not reach the live report packet."
    )
    coverage["ok"] = False
    coverage["detail"] = detail
    return coverage, {
        "kind": "field_route",
        "contract_id": "DecisionPacket",
        "field_name": "decision_mode",
        "route_id": "guard_run_report",
        "rule": "unconsumed-field-route",
        "detail": detail,
    }
