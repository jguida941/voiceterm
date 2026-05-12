"""Blocker category helpers for development next-slice selection."""

from __future__ import annotations

_TOPOLOGY_TERMS = (
    "active_dual_agent",
    "single_agent",
    "tools_only",
    "topology",
    "no_live_agents",
    "reviewer mode",
    "live loop",
    "coordination_resync",
    "resync",
    "inactive",
    "review-loop",
    "review_loop",
    "reviewer_freshness",
    "session-liveness",
    "session liveness",
    "launcher-recursion",
    "launcher_recursion",
    "remote-control",
    "remote control",
)

_PACKET_DEBT_TERMS = (
    "packet-debt",
    "packet debt",
    "expired_unresolved_packet",
    "expired unresolved packet",
)

_SELECTOR_TERMS = (
    "next selector",
    "activeworkenvelope",
    "active work envelope",
    "develop next",
)

_GUARD_SCHEDULER_TERMS = (
    "push_preflight_running",
    "run_devctl_push",
    "check-router",
    "check router",
    "route budget",
    "route timeout",
    "guard cadence",
    "guard deferral",
    "long-running",
    "long running",
    "code-shape",
    "code shape",
)

_CHECKPOINT_TERMS = (
    "checkpoint",
    "index.lock",
    "git_index_write_blocked",
    "import_index_atomicity",
    "dirty_path_budget_exceeded",
    "dirty_after_local_checkpoint",
    "startup authority",
    "startup_authority",
    "managed projection",
    "vcs.stage",
)

_AGENT_SUPERVISE_TERMS = (
    "agent-supervise",
    "agent supervise",
    "process_exited",
    "process exit",
    "freeze_detected",
    "process_alive_activity_stale",
    "detached_runtime_only",
    "spawn_authorized",
)

_TEST_POLICY_TERMS = ("code-shape", "code shape", "pytest", "test execution")

_GUARD_SCHEDULER_ROW_IDS = (
    "MP377-P0-SMART-CHECK-DEFERRAL-S1",
    "MP377-P0-GUARD-CADENCE-S1",
    "MP377-P0-GUARD-DEFERRAL-S1",
    "MP377-P0-COMMAND-RESULT-OBSERVABILITY-S1",
    "MP377-P0-T22AN-AB",
)

_TOPOLOGY_ROW_IDS = (
    "MP377-P0-TOPOLOGY-NEUTRAL-NEXT-S1",
    "MP377-P0-ROLE-MATRIX-ROSTER-S1",
    "MP377-P0-LIFECYCLE-ROLE-SIGNOFF-S1",
    "MP377-P0-T22AN-L",
)

_SELECTOR_ROW_IDS = (
    "MP377-P0-TOPOLOGY-NEUTRAL-NEXT-S1",
    "MP377-P0-ACTIVE-WORK-ENVELOPE-S1",
    "MP377-P0-PACKET-INTAKE-SCHEDULER-S1",
)

_PACKET_DEBT_ROW_IDS = ("MP377-P0-PACKET-INTAKE-SCHEDULER-S1",)

_CHECKPOINT_ROW_IDS = (
    "MP377-P0-CHECKPOINT-AUTOMATION-S1",
    "MP377-P0-T22AN-AB",
)

_AGENT_SUPERVISE_ROW_IDS = (
    "MP377-P0-CHECKPOINT-AUTOMATION-S1",
    "MP377-WATCHER-AUTO-TRIGGER-S1",
)

_TEST_POLICY_ROW_IDS = ("MP377-P0-T22AN-AB",)


def blocker_categories(text: str) -> tuple[str, ...]:
    """Return orchestration blocker categories detected in lower-case text."""
    categories: list[str] = []
    _append_if(categories, "topology", text, _TOPOLOGY_TERMS)
    _append_if(categories, "packet_debt", text, _PACKET_DEBT_TERMS)
    _append_if(categories, "selector", text, _SELECTOR_TERMS)
    _append_if(categories, "guard_scheduler", text, _GUARD_SCHEDULER_TERMS)
    _append_if(categories, "checkpoint", text, _CHECKPOINT_TERMS)
    _append_if(categories, "agent_supervise", text, _AGENT_SUPERVISE_TERMS)
    _append_if(categories, "test_policy", text, _TEST_POLICY_TERMS)
    return tuple(dict.fromkeys(categories))


def category_row_ids(category: str) -> tuple[str, ...]:
    """Return active plan row ids that can own one blocker category."""
    if category == "guard_scheduler":
        return _GUARD_SCHEDULER_ROW_IDS
    if category == "topology":
        return _TOPOLOGY_ROW_IDS
    if category == "selector":
        return _SELECTOR_ROW_IDS
    if category == "packet_debt":
        return _PACKET_DEBT_ROW_IDS
    if category == "checkpoint":
        return _CHECKPOINT_ROW_IDS
    if category == "agent_supervise":
        return _AGENT_SUPERVISE_ROW_IDS
    if category == "test_policy":
        return _TEST_POLICY_ROW_IDS
    return ()


def _append_if(
    categories: list[str],
    category: str,
    text: str,
    terms: tuple[str, ...],
) -> None:
    if any(term in text for term in terms):
        categories.append(category)


__all__ = ["blocker_categories", "category_row_ids"]
