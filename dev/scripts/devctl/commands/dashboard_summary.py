"""Summary compilation for the DashboardSnapshot.

Derives prioritized operator conclusions (overall state, blockers, next
actor) from an already-assembled snapshot.  No artifact IO -- every field
is deterministic from snapshot data.
"""

from __future__ import annotations

from typing import Any


def _is_reviewer_overdue(age_label: str) -> bool:
    """Return True when the reviewer age label indicates staleness (>10 min)."""
    if not age_label or age_label == "--":
        return False
    if age_label.endswith("h ago"):
        return True
    if age_label.endswith("m ago"):
        try:
            minutes = int(age_label.replace("m ago", "").strip())
            return minutes > 10
        except ValueError:
            return False
    return False


def _build_one_line(
    overall_state: str,
    infra_state: str,
    now: dict[str, Any],
    reviewer_overdue: bool,
    has_quality_fail: bool,
    gate_failures: list[str],
    pub_state: str,
) -> str:
    """Compile all summary signals into one readable operator sentence."""
    parts: list[str] = []
    owner = now.get("owner", "unknown")
    parts.append(f"{owner} active")
    parts.append(f"infra {infra_state}")
    if reviewer_overdue:
        parts.append("reviewer stale")
    if has_quality_fail:
        gates = ", ".join(gate_failures)
        parts.append(f"quality gate failing on {gates}")
    if pub_state in ("NOT CURRENT", "STALE"):
        parts.append("push blocked")
    if overall_state == "healthy":
        parts.append("all green")
    return "; ".join(parts) + "."


def _compile_summary(snapshot: dict) -> dict:
    """Compile raw dashboard state into prioritized operator conclusions.

    Reads only from the already-assembled snapshot sections -- no new artifact
    IO.  Every derived field is deterministic from snapshot data.

    Delegates to ``_compile_summary_state`` for overall state derivation and
    ``_compile_summary_fields`` for the remaining fields.
    """
    state_data = _compile_summary_state(snapshot)
    return _compile_summary_fields(snapshot, state_data)


def _compile_summary_state(snapshot: dict) -> dict:
    """Derive overall state and intermediate signals from snapshot sections.

    Returns a dict with keys used by ``_compile_summary_fields`` to produce
    the final summary.
    """
    quality = snapshot.get("quality", {})
    health = snapshot.get("health", {})
    now = snapshot.get("now", {})
    coordination = snapshot.get("coordination", {})
    workers = snapshot.get("workers", [])

    # Infra state from daemon running counts
    active_daemons = health.get("active_daemons", 0)
    if active_daemons >= 2:
        infra_state = "healthy"
    elif active_daemons == 1:
        infra_state = "degraded"
    else:
        infra_state = "down"
    infra_label = (
        f"{active_daemons} daemon{'s' if active_daemons != 1 else ''} running"
    )

    # Quality gate failures
    quality_gates = ["docs_gate", "plan_sync", "bridge", "code_shape",
                     "instr_sync", "clippy"]
    gate_failures = [
        g for g in quality_gates if quality.get(g, "").upper() == "FAIL"
    ]
    has_quality_fail = bool(gate_failures)

    # Reviewer staleness
    attention_status = health.get("attention_status", "n/a")
    attention_not_healthy = attention_status not in ("healthy", "n/a")
    reviewer_age_label = coordination.get("reviewer_age", "--")
    reviewer_overdue = _is_reviewer_overdue(reviewer_age_label)

    # Recovery check
    recovery_states = {
        "implementer_state_reset_required", "review_loop_relaunch_required",
        "implementer_relaunch_required", "runtime_missing",
    }
    needs_recovery = attention_status in recovery_states

    # Worker truth
    impl_stale = coordination.get("implementer_state", "") == "stale"
    impl_waiting = any(
        w.get("state", "").upper() in ("WAITING_FOR_ACK", "INACTIVE")
        for w in workers
        if w.get("scope", "").lower() == "implementer"
        or w.get("id", "") == "W2"
    )
    no_conductor = (
        health.get("codex_conductor", {}).get("alive") is False
        or health.get("codex_conductor", {}).get("pid") is None
    ) and (
        health.get("claude_conductor", {}).get("alive") is False
        or health.get("claude_conductor", {}).get("pid") is None
    )

    # Overall state with truth precedence
    if needs_recovery or (no_conductor and attention_not_healthy):
        overall_state = "awaiting_recovery"
    elif has_quality_fail and (impl_stale or impl_waiting):
        overall_state = "validation_blocked"
    elif has_quality_fail or attention_not_healthy:
        overall_state = "blocked"
    elif reviewer_overdue:
        overall_state = "waiting"
    elif impl_stale or impl_waiting:
        overall_state = "awaiting_ack"
    elif now.get("owner") == "Implementer" and not impl_stale:
        overall_state = "active"
    else:
        overall_state = "healthy"

    return {
        "overall_state": overall_state,
        "infra_state": infra_state,
        "infra_label": infra_label,
        "has_quality_fail": has_quality_fail,
        "gate_failures": gate_failures,
        "attention_not_healthy": attention_not_healthy,
        "attention_status": attention_status,
        "reviewer_overdue": reviewer_overdue,
        "reviewer_age_label": reviewer_age_label,
        "needs_recovery": needs_recovery,
        "impl_stale": impl_stale,
        "impl_waiting": impl_waiting,
    }


def _compile_summary_fields(snapshot: dict, state: dict) -> dict:
    """Produce the final summary dict from snapshot and pre-computed state signals."""
    now = snapshot.get("now", {})
    publication = snapshot.get("publication", {})
    quality = snapshot.get("quality", {})

    overall_state = state["overall_state"]
    needs_recovery = state["needs_recovery"]
    has_quality_fail = state["has_quality_fail"]
    reviewer_overdue = state["reviewer_overdue"]
    impl_stale = state["impl_stale"]
    impl_waiting = state["impl_waiting"]
    gate_failures = state["gate_failures"]
    attention_not_healthy = state["attention_not_healthy"]
    attention_status = state["attention_status"]
    reviewer_age_label = state["reviewer_age_label"]

    # Block class
    block_parts: list[str] = []
    if has_quality_fail:
        block_parts.append("quality")
    if reviewer_overdue:
        block_parts.append("reviewer")
    pub_state = publication.get("effective", "n/a")
    if pub_state in ("NOT CURRENT", "STALE"):
        block_parts.append("push")
    block_class = " + ".join(block_parts) if block_parts else "none"

    # Next actor
    if needs_recovery:
        next_actor = "operator"
    elif overall_state == "validation_blocked":
        next_actor = "implementer"
    elif reviewer_overdue:
        next_actor = "reviewer"
    elif impl_stale or impl_waiting:
        next_actor = "operator"
    elif now.get("owner", "").lower() == "implementer":
        next_actor = "implementer"
    else:
        next_actor = "operator"

    # Next command hint
    if needs_recovery:
        next_command_hint = "reset implementer state, relaunch conductors"
    elif overall_state == "validation_blocked":
        next_command_hint = "fix code-shape debt, rerun validation"
    elif has_quality_fail:
        next_command_hint = "fix code-shape debt"
    elif reviewer_overdue:
        next_command_hint = "relaunch Codex"
    elif pub_state in ("NOT CURRENT", "STALE"):
        next_command_hint = "run check --profile ci"
    else:
        next_command_hint = "continue current slice"

    # Primary blocker
    failing = quality.get("failing", [])
    top_blocker = now.get("top_blocker", "none")
    if top_blocker and top_blocker != "none":
        primary_blocker = top_blocker
    elif gate_failures:
        fail_file = failing[0] if failing else "unknown"
        primary_blocker = f"{gate_failures[0]} fail in {fail_file}"
    else:
        primary_blocker = "none"

    # Secondary blocker
    if attention_not_healthy:
        secondary_blocker = f"Attention {attention_status}"
    elif reviewer_overdue:
        secondary_blocker = f"Reviewer heartbeat stale ({reviewer_age_label})"
    else:
        secondary_blocker = "none"

    # One line
    one_line = _build_one_line(
        overall_state, state["infra_state"], now, reviewer_overdue,
        has_quality_fail, gate_failures, pub_state,
    )

    return {
        "overall_state": overall_state,
        "block_class": block_class,
        "next_actor": next_actor,
        "next_command_hint": next_command_hint,
        "infra_state": state["infra_state"],
        "infra_label": state["infra_label"],
        "primary_blocker": primary_blocker,
        "secondary_blocker": secondary_blocker,
        "one_line": one_line,
    }
