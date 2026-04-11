"""Operator-facing runtime count helpers for review-channel status surfaces."""

from __future__ import annotations

from collections.abc import Mapping


def build_runtime_counts(
    *,
    collaboration: Mapping[str, object] | None = None,
    publisher_running: bool | None = None,
    reviewer_supervisor_running: bool | None = None,
    bridge_liveness: Mapping[str, object] | None = None,
    requested_worker_budgets: Mapping[str, object] | None = None,
) -> dict[str, int]:
    """Return explicit live runtime counts for operator surfaces."""
    session = collaboration if isinstance(collaboration, Mapping) else {}
    bridge = bridge_liveness if isinstance(bridge_liveness, Mapping) else {}
    participants = _rows(session.get("participants"))
    delegated_work = _rows(session.get("delegated_work"))
    live_participants = [row for row in participants if _bool(row.get("live"))]
    bridge_live_totals = _bridge_live_role_totals(bridge)
    live_provider_ids = _live_provider_ids(live_participants)
    live_reviewer_total = sum(
        1
        for row in live_participants
        if _text(row.get("role")) == "reviewer"
    )
    live_implementer_total = sum(
        1
        for row in live_participants
        if _text(row.get("role")) == "implementer"
    )
    if not participants:
        live_participant_total = bridge_live_totals["live_participants_total"]
        live_reviewer_total = bridge_live_totals["live_reviewer_total"]
        live_implementer_total = bridge_live_totals["live_implementer_total"]
        active_conductor_count = _active_conductor_count(
            bridge=bridge,
            live_participants=live_participants,
        )
    else:
        live_participant_total = len(live_participants)
        active_conductor_count = len(live_provider_ids)
    requested_worker_budget_total = _requested_worker_budget_total(
        participants=participants,
        requested_worker_budgets=requested_worker_budgets,
    )
    active_daemon_total = int(
        bool(_coalesce_bool(publisher_running, bridge.get("publisher_running")))
    ) + int(
        bool(
            _coalesce_bool(
                reviewer_supervisor_running,
                bridge.get("reviewer_supervisor_running"),
            )
        )
    )

    counts: dict[str, int] = {}
    counts["participants_total"] = len(participants)
    counts["live_participants_total"] = live_participant_total
    counts["live_reviewer_total"] = live_reviewer_total
    counts["live_implementer_total"] = live_implementer_total
    counts["delegated_receipt_total"] = len(delegated_work)
    counts["live_delegated_receipt_total"] = sum(
        1 for row in delegated_work if _bool(row.get("live"))
    )
    counts["requested_worker_budget_total"] = requested_worker_budget_total
    counts["active_daemon_total"] = active_daemon_total
    counts["active_conductor_count"] = active_conductor_count
    counts["live_participant_count"] = live_participant_total
    counts["live_reviewer_count"] = live_reviewer_total
    counts["live_implementer_count"] = live_implementer_total
    counts["running_daemon_count"] = active_daemon_total
    counts["delegated_work_total"] = len(delegated_work)
    return counts


def _active_conductor_count(
    *,
    bridge: Mapping[str, object],
    live_participants: list[Mapping[str, object]],
) -> int:
    live_provider_ids = _live_provider_ids(live_participants)
    if live_provider_ids:
        return len(live_provider_ids)

    providers = bridge.get("active_conductor_providers")
    if isinstance(providers, (list, tuple)):
        normalized = {
            str(provider).strip()
            for provider in providers
            if str(provider).strip()
        }
        if normalized:
            return len(normalized)

    codex_live = _coalesce_bool(None, bridge.get("codex_conductor_active"))
    claude_live = _coalesce_bool(None, bridge.get("claude_conductor_active"))
    if codex_live is not None or claude_live is not None:
        return int(bool(codex_live)) + int(bool(claude_live))

    return 0


def _bridge_live_role_totals(bridge: Mapping[str, object]) -> dict[str, int]:
    codex_live = _coalesce_bool(None, bridge.get("codex_conductor_active"))
    claude_live = _coalesce_bool(None, bridge.get("claude_conductor_active"))
    if codex_live is not None or claude_live is not None:
        return {
            "live_participants_total": int(bool(codex_live)) + int(bool(claude_live)),
            "live_reviewer_total": int(bool(codex_live)),
            "live_implementer_total": int(bool(claude_live)),
        }

    providers = bridge.get("active_conductor_providers")
    if isinstance(providers, (list, tuple)):
        normalized = [
            str(provider).strip().lower()
            for provider in providers
            if str(provider).strip()
        ]
        return {
            "live_participants_total": len(normalized),
            "live_reviewer_total": sum(1 for provider in normalized if provider == "codex"),
            "live_implementer_total": sum(
                1 for provider in normalized if provider == "claude"
            ),
        }

    return {
        "live_participants_total": 0,
        "live_reviewer_total": 0,
        "live_implementer_total": 0,
    }


def _requested_worker_budget_total(
    *,
    participants: list[Mapping[str, object]],
    requested_worker_budgets: Mapping[str, object] | None,
) -> int:
    participant_total = sum(
        max(_int(row.get("requested_worker_budget")), 0) for row in participants
    )
    if participant_total > 0:
        return participant_total
    budgets = (
        requested_worker_budgets
        if isinstance(requested_worker_budgets, Mapping)
        else {}
    )
    return sum(max(_int(value), 0) for value in budgets.values())


def _rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, (list, tuple)):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _live_provider_ids(
    live_participants: list[Mapping[str, object]],
) -> tuple[str, ...]:
    providers: list[str] = []
    for row in live_participants:
        provider = _text(row.get("provider") or row.get("agent_id"))
        if provider and provider not in providers:
            providers.append(provider)
    return tuple(providers)


def _bool(value: object) -> bool:
    return bool(value)


def _int(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _coalesce_bool(primary: bool | None, fallback: object) -> bool | None:
    if primary is not None:
        return bool(primary)
    if fallback is None:
        return None
    return bool(fallback)


def _text(value: object) -> str:
    return str(value or "").strip().lower()
