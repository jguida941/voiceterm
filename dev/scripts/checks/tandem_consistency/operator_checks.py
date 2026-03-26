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
    typed_state: dict[str, object] | None = None,
) -> dict[str, object]:
    """Verify the bridge references the required active plan chain.

    This check validates bridge.md document structure (the Plan Alignment
    section) rather than runtime state. The core logic intentionally remains
    bridge-prose based because the Plan Alignment section has no typed
    equivalent in review_state.json.  ``typed_state`` is accepted for
    signature consistency but is not yet consumed.
    """
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


def check_promotion_state(
    bridge_text: str,
    *,
    typed_state: dict[str, object] | None = None,
) -> dict[str, object]:
    """Verify the bridge is not stuck in a stale promotion state.

    When typed review_state.json is available, reads ``bridge.review_accepted``
    and ``current_session`` fields instead of parsing bridge prose verdict/findings.
    """
    bridge_block = (typed_state or {}).get("bridge") or {}
    cs = (typed_state or {}).get("current_session") or {}
    typed_mode = str(bridge_block.get("reviewer_mode") or "").strip()

    # Prefer typed reviewer_mode
    if typed_mode:
        reviewer_mode = normalize_reviewer_mode(typed_mode)
    else:
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

    # Prefer typed current_instruction
    instruction = str(cs.get("current_instruction") or "").strip() or extract_section(bridge_text, "Current Instruction For Claude")

    if not instruction.strip():
        return {
            "check": "promotion_state",
            "role": TandemRole.OPERATOR,
            "ok": False,
            "detail": "No current instruction — bridge may be idle or stale.",
        }

    # Prefer typed review_accepted; fall back to prose verdict parsing
    typed_accepted = bridge_block.get("review_accepted")
    if typed_accepted is not None:
        is_accepted = bool(typed_accepted)
        typed_findings = str(cs.get("open_findings") or "").strip()
        has_findings = bool(typed_findings) and typed_findings.lower() not in (
            "(none)", "none", "no blockers", "all clear", "all green", "resolved", "(missing)",
        )
    else:
        verdict = extract_section(bridge_text, "Current Verdict")
        findings = extract_section(bridge_text, "Open Findings")
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
