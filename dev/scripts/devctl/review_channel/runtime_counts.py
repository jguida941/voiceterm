"""Operator-facing runtime count helpers for review-channel status surfaces."""

from __future__ import annotations

from collections.abc import Mapping

from ..runtime.role_profile import role_capability_classes
from ..runtime.role_topology import resolve_role_topology
from ..runtime.runtime_count_roles import (
    participant_role_provider_ids,
    provider_has_only_non_tandem_presence,
)


_REVIEW_CAPABILITY_CLASSES = frozenset(
    {"review", "test", "architecture", "governance", "research", "intake"}
)
_IMPLEMENTATION_CAPABILITY_CLASSES = frozenset({"implementation", "mutation"})
_ACTIVE_CONDUCTOR_CAPABILITY_CLASSES = (
    _REVIEW_CAPABILITY_CLASSES | _IMPLEMENTATION_CAPABILITY_CLASSES
)


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
    role_assignments = _rows(session.get("role_assignments"))
    delegated_work = _rows(session.get("delegated_work"))
    live_participants = [row for row in participants if _bool(row.get("live"))]
    bridge_live_totals = _bridge_live_role_totals(bridge)
    live_provider_ids = _live_provider_ids(live_participants)
    live_role_totals = _live_role_totals(
        role_assignments=role_assignments,
        live_participants=live_participants,
    )
    live_reviewer_total = live_role_totals["live_reviewer_total"]
    live_implementer_total = live_role_totals["live_implementer_total"]
    if not participants:
        live_participant_total = bridge_live_totals["live_participants_total"]
        if not live_role_totals["derived_from_typed_roles"]:
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
    topology = resolve_role_topology(bridge, include_runtime_presence=True)
    providers = bridge.get("active_conductor_providers")
    if isinstance(providers, (list, tuple)):
        normalized = [
            str(provider).strip().lower()
            for provider in providers
            if str(provider).strip()
        ]
        return {
            "live_participants_total": len(normalized),
            "live_reviewer_total": len(topology.live_reviewer_providers),
            "live_implementer_total": len(topology.live_implementer_providers),
        }

    return {
        "live_participants_total": len(topology.active_providers),
        "live_reviewer_total": len(topology.live_reviewer_providers),
        "live_implementer_total": len(topology.live_implementer_providers),
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
        role_classes = set(role_capability_classes(_text(row.get("role"))))
        if not role_classes & _ACTIVE_CONDUCTOR_CAPABILITY_CLASSES:
            continue
        provider = _text(row.get("provider") or row.get("agent_id"))
        if provider and provider not in providers:
            providers.append(provider)
    return tuple(providers)


def _live_role_totals(
    *,
    role_assignments: list[Mapping[str, object]],
    live_participants: list[Mapping[str, object]],
) -> dict[str, int | bool]:
    eligible_role_assignments = [
        row
        for row in role_assignments
        if _bool(row.get("live"))
        and not provider_has_only_non_tandem_presence(
            live_participants,
            _text(row.get("provider") or row.get("agent_id")),
            text_fn=_text,
        )
    ]
    topology = resolve_role_topology(
        {
            "collaboration": {
                "role_assignments": eligible_role_assignments,
                "participants": live_participants,
            }
        },
        include_runtime_presence=True,
    )
    reviewer_ids = list(topology.live_reviewer_providers)
    implementer_ids = list(topology.live_implementer_providers)
    if not reviewer_ids:
        reviewer_ids.extend(
            participant_role_provider_ids(
                live_participants,
                "reviewer",
                text_fn=_text,
            )
        )
    if not implementer_ids:
        implementer_ids.extend(
            participant_role_provider_ids(
                live_participants,
                "implementer",
                text_fn=_text,
            )
        )
    return {
        "live_reviewer_total": len(reviewer_ids),
        "live_implementer_total": len(implementer_ids),
        "derived_from_typed_roles": bool(role_assignments),
    }


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
