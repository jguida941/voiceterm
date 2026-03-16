"""Operator-owned tandem-consistency checks."""

from __future__ import annotations

from pathlib import Path

from dev.scripts.devctl.review_channel.peer_liveness import (
    normalize_reviewer_mode,
    reviewer_mode_is_active,
)
from dev.scripts.devctl.runtime.role_profile import TandemRole

from .support import extract_metadata_value, extract_section


def check_plan_alignment(
    bridge_text: str,
    *,
    repo_root: Path | None = None,
) -> dict[str, object]:
    """Verify the bridge references the required active plan chain."""
    plan_alignment = extract_section(bridge_text, "Plan Alignment")
    if not plan_alignment.strip():
        return {
            "check": "plan_alignment",
            "role": TandemRole.OPERATOR,
            "ok": False,
            "detail": "No Plan Alignment section found in bridge.",
        }

    has_continuous_swarm = "continuous_swarm.md" in plan_alignment
    has_master_plan = "MASTER_PLAN" in plan_alignment
    missing: list[str] = []
    if not has_master_plan:
        missing.append("MASTER_PLAN")
    if not has_continuous_swarm:
        missing.append("continuous_swarm.md")
    if missing:
        return {
            "check": "plan_alignment",
            "role": TandemRole.OPERATOR,
            "ok": False,
            "references_continuous_swarm": has_continuous_swarm,
            "references_master_plan": has_master_plan,
            "detail": (
                "Plan Alignment is missing required references: "
                f"{', '.join(missing)}."
            ),
        }

    missing_files: list[str] = []
    if repo_root is not None:
        for rel_path in (
            "dev/active/MASTER_PLAN.md",
            "dev/active/continuous_swarm.md",
        ):
            if not (repo_root / rel_path).exists():
                missing_files.append(rel_path)
    if missing_files:
        return {
            "check": "plan_alignment",
            "role": TandemRole.OPERATOR,
            "ok": False,
            "references_continuous_swarm": has_continuous_swarm,
            "references_master_plan": has_master_plan,
            "missing_files": missing_files,
            "detail": (
                "Referenced plan files missing on disk: "
                f"{', '.join(missing_files)}."
            ),
        }

    return {
        "check": "plan_alignment",
        "role": TandemRole.OPERATOR,
        "ok": True,
        "references_continuous_swarm": has_continuous_swarm,
        "references_master_plan": has_master_plan,
        "detail": "Plan alignment chain is complete (MASTER_PLAN → continuous_swarm.md).",
    }


def check_promotion_state(bridge_text: str) -> dict[str, object]:
    """Verify the bridge is not stuck in a stale promotion state."""
    reviewer_mode = normalize_reviewer_mode(
        extract_metadata_value(bridge_text, "Reviewer mode:")
    )
    if not reviewer_mode_is_active(reviewer_mode):
        return {
            "check": "promotion_state",
            "role": TandemRole.OPERATOR,
            "ok": True,
            "status": "inactive",
            "detail": f"Reviewer mode is `{reviewer_mode}`; promotion state is inactive.",
        }

    verdict = extract_section(bridge_text, "Current Verdict")
    instruction = extract_section(bridge_text, "Current Instruction For Claude")
    findings = extract_section(bridge_text, "Open Findings")

    if not instruction.strip():
        return {
            "check": "promotion_state",
            "role": TandemRole.OPERATOR,
            "ok": False,
            "detail": "No current instruction — bridge may be idle or stale.",
        }

    verdict_lower = verdict.lower()
    accepted_signals = ("accepted", "complete", "all green", "reviewer-accepted")
    is_accepted = any(signal in verdict_lower for signal in accepted_signals)
    has_findings = bool(findings.strip()) and findings.strip() != "(missing)"

    if is_accepted and not has_findings:
        return {
            "check": "promotion_state",
            "role": TandemRole.OPERATOR,
            "ok": True,
            "status": "ready_for_promotion",
            "detail": (
                "Verdict is accepted with no open findings — "
                "ready for next-task promotion."
            ),
        }

    return {
        "check": "promotion_state",
        "role": TandemRole.OPERATOR,
        "ok": True,
        "status": "active",
        "detail": "Promotion state is active (work in progress).",
    }
