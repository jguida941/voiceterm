"""Field-route closure proofs for platform contract enforcement."""

from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

FieldRouteCheck = Callable[[], tuple[dict[str, object], dict[str, object] | None]]


def check_finding_ai_instruction_ralph_route() -> tuple[dict[str, object], dict[str, object] | None]:
    """Verify a populated Finding.ai_instruction reaches the Ralph prompt."""
    from dev.scripts.coderabbit.probe_guidance import attach_probe_guidance
    from dev.scripts.coderabbit.ralph_ai_fix import build_prompt

    expected_instruction = "Extract the auth validator helper before editing the caller."
    backlog_items = [
        {
            "severity": "high",
            "category": "rust",
            "summary": "rust/src/auth.rs:12 - Unused import in auth.rs",
        }
    ]
    review_targets_payload = {
        "findings": [
            {
                "file_path": "rust/src/auth.rs",
                "check_id": "probe_design_smells",
                "severity": "high",
                "line": 10,
                "end_line": 14,
                "ai_instruction": expected_instruction,
            }
        ]
    }
    coverage: dict[str, object] = {
        "kind": "field_route",
        "contract_id": "Finding",
        "field_name": "ai_instruction",
        "route_id": "ralph_prompt",
        "consumer": "dev.scripts.coderabbit.ralph_ai_fix:build_prompt",
        "ok": True,
    }

    with tempfile.TemporaryDirectory() as tmp_dir:
        report_root = Path(tmp_dir)
        (report_root / "review_targets.json").write_text(
            json.dumps(review_targets_payload),
            encoding="utf-8",
        )
        enriched = attach_probe_guidance(backlog_items, report_root=report_root)

    guidance = enriched[0].get("probe_guidance") if enriched else None
    if not isinstance(guidance, list) or not guidance:
        detail = (
            "Finding.ai_instruction is produced by probe artifacts but is not "
            "attached to the Ralph remediation item before prompt assembly."
        )
        coverage["ok"] = False
        coverage["detail"] = detail
        return coverage, {
            "kind": "field_route",
            "contract_id": "Finding",
            "field_name": "ai_instruction",
            "route_id": "ralph_prompt",
            "rule": "unconsumed-field-route",
            "detail": detail,
        }

    prompt = build_prompt(enriched, attempt=1)
    if expected_instruction in prompt:
        coverage["detail"] = (
            "Finding.ai_instruction survives the canonical Ralph route from "
            "probe artifact to live remediation prompt."
        )
        return coverage, None

    detail = (
        "Finding.ai_instruction is attached to the Ralph remediation item but "
        "does not reach the live prompt output."
    )
    coverage["ok"] = False
    coverage["detail"] = detail
    return coverage, {
        "kind": "field_route",
        "contract_id": "Finding",
        "field_name": "ai_instruction",
        "route_id": "ralph_prompt",
        "rule": "unconsumed-field-route",
        "detail": detail,
    }


def check_finding_ai_instruction_autonomy_route() -> tuple[dict[str, object], dict[str, object] | None]:
    """Verify a populated Finding.ai_instruction reaches the autonomy loop packet."""
    from dev.scripts.devctl.commands import loop_packet

    expected_instruction = "Split the auth validator from the retry orchestration before editing the caller."
    source_payload = {
        "command": "triage-loop",
        "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "branch": "develop",
        "reason": "no fix command configured",
        "unresolved_count": 1,
        "backlog_items": [
            {
                "severity": "high",
                "category": "python",
                "summary": "dev/scripts/devctl/auth.py:12 - Auth flow and retry loop are coupled.",
                "file_path": "dev/scripts/devctl/auth.py",
                "line": 12,
            }
        ],
    }
    review_targets_payload = {
        "findings": [
            {
                "file_path": "dev/scripts/devctl/auth.py",
                "check_id": "probe_side_effect_mixing",
                "severity": "high",
                "line": 10,
                "end_line": 14,
                "ai_instruction": expected_instruction,
            }
        ]
    }
    coverage: dict[str, object] = {
        "kind": "field_route",
        "contract_id": "Finding",
        "field_name": "ai_instruction",
        "route_id": "autonomy_loop_packet",
        "consumer": "dev.scripts.devctl.commands.loop_packet:run",
        "ok": True,
    }

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_root = Path(tmp_dir)
        source_path = tmp_root / "triage-loop.json"
        output_path = tmp_root / "loop-packet.json"
        report_root = tmp_root / "probes"
        report_root.mkdir(parents=True, exist_ok=True)
        source_path.write_text(json.dumps(source_payload), encoding="utf-8")
        (report_root / "review_targets.json").write_text(
            json.dumps(review_targets_payload),
            encoding="utf-8",
        )
        args = SimpleNamespace(
            source_json=[str(source_path)],
            prefer_source="triage-loop",
            max_age_hours=72.0,
            max_draft_chars=1600,
            allow_auto_send=False,
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

    if rc != 0:
        detail = "Autonomy loop-packet route failed before prompt generation completed."
        coverage["ok"] = False
        coverage["detail"] = detail
        return coverage, {
            "kind": "field_route",
            "contract_id": "Finding",
            "field_name": "ai_instruction",
            "route_id": "autonomy_loop_packet",
            "rule": "unconsumed-field-route",
            "detail": detail,
        }

    prompt = str(
        ((payload.get("terminal_packet") or {}).get("draft_text"))
        if isinstance(payload.get("terminal_packet"), dict)
        else ""
    )
    if expected_instruction in prompt:
        coverage["detail"] = (
            "Finding.ai_instruction survives the canonical autonomy route from "
            "probe artifact to loop-packet terminal draft."
        )
        return coverage, None

    detail = (
        "Finding.ai_instruction is available for the autonomy slice but does "
        "not reach the loop-packet terminal draft."
    )
    coverage["ok"] = False
    coverage["detail"] = detail
    return coverage, {
        "kind": "field_route",
        "contract_id": "Finding",
        "field_name": "ai_instruction",
        "route_id": "autonomy_loop_packet",
        "rule": "unconsumed-field-route",
        "detail": detail,
    }


def check_finding_ai_instruction_guard_run_route() -> tuple[dict[str, object], dict[str, object] | None]:
    """Verify a populated Finding.ai_instruction reaches the guard-run follow-up packet."""
    from dev.scripts.devctl.commands.guard_run import build_guard_run_report
    from dev.scripts.devctl.guard_run_core import (
        GuardGitSnapshot,
        GuardRunRequest,
        build_guard_run_markdown,
    )

    expected_instruction = "Split the guard-run follow-up repair plan from the shell wrapper logic."
    review_targets_payload = {
        "findings": [
            {
                "file_path": "dev/scripts/devctl/commands/guard_run.py",
                "check_id": "probe_side_effect_mixing",
                "severity": "high",
                "line": 42,
                "end_line": 58,
                "ai_instruction": expected_instruction,
            }
        ]
    }
    coverage: dict[str, object] = {
        "kind": "field_route",
        "contract_id": "Finding",
        "field_name": "ai_instruction",
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
        (report_root / "review_targets.json").write_text(
            json.dumps(review_targets_payload),
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

    probe_guidance = report.get("probe_guidance")
    guidance_refs = report.get("guidance_refs")
    markdown = build_guard_run_markdown(report)
    if (
        isinstance(probe_guidance, list)
        and probe_guidance
        and isinstance(guidance_refs, list)
        and guidance_refs
        and expected_instruction in markdown
    ):
        coverage["detail"] = (
            "Finding.ai_instruction survives the canonical guard-run route from "
            "probe artifact to follow-up packet guidance section."
        )
        return coverage, None

    detail = (
        "Finding.ai_instruction is available for guard-run follow-up scope but "
        "does not reach the live report guidance packet."
    )
    coverage["ok"] = False
    coverage["detail"] = detail
    return coverage, {
        "kind": "field_route",
        "contract_id": "Finding",
        "field_name": "ai_instruction",
        "route_id": "guard_run_report",
        "rule": "unconsumed-field-route",
        "detail": detail,
    }


FIELD_ROUTE_CHECKS: tuple[FieldRouteCheck, ...] = (
    check_finding_ai_instruction_ralph_route,
    check_finding_ai_instruction_autonomy_route,
    check_finding_ai_instruction_guard_run_route,
)

FIELD_ROUTE_FAMILY_REGISTRY: dict[tuple[str, str], tuple[str, ...]] = {
    ("Finding", "ai_instruction"): (
        "ralph_prompt",
        "autonomy_loop_packet",
        "guard_run_report",
    ),
}
