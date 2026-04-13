"""Bounded parity subchecks for event-backed review-state emitters."""

from __future__ import annotations

from dataclasses import fields
from pathlib import Path

from dev.scripts.devctl.runtime.review_bridge_field_authority import (
    EVENT_BRIDGE_CLASSIFIED_FIELDS,
)

_EXPECTED_COMPAT_KEYS = frozenset({
    "project_id",
    "runtime",
    "service_identity",
    "attach_auth_policy",
    "doctor",
    "agents",
})

_BRIDGE_STATE_EXPECTED_TYPES: dict[str, type] = {
    "overall_state": str,
    "codex_poll_state": str,
    "reviewer_mode": str,
    "last_codex_poll_utc": str,
    "last_codex_poll_age_seconds": int,
    "last_worktree_hash": str,
    "current_instruction": str,
    "open_findings": str,
    "claude_status": str,
    "claude_ack": str,
    "claude_ack_current": bool,
    "current_instruction_revision": str,
    "claude_ack_revision": str,
    "last_reviewed_scope": str,
    "reviewed_hash_current": bool,
    "review_needed": bool,
    "review_accepted": bool,
    "implementer_completion_stall": bool,
    "publisher_running": bool,
}


def build_synthetic_review_state() -> dict[str, object]:
    """Minimal synthetic review_state for probing emitter output shape."""
    return {
        "timestamp": "2026-01-01T00:00:00Z",
        "ok": True,
        "review": {"plan_id": "test"},
        "queue": {"pending_total": 0, "pending_claude": 0},
        "current_session": {
            "current_instruction": "keep the slice bounded",
            "current_instruction_revision": "abc123def456",
            "implementer_status": "active",
            "implementer_ack": "acknowledged",
            "implementer_ack_revision": "abc123def456",
            "implementer_ack_state": "current",
            "implementer_state_hash": "",
            "implementer_session_state": "",
            "implementer_session_hint": "",
            "open_findings": "none",
            "last_reviewed_scope": "MP-355",
        },
        "collaboration": {
            "schema_version": 1,
            "contract_id": "CollaborationSession",
            "session_id": "synthetic-session",
            "plan_id": "test",
            "status": "handoff_only",
            "reviewer_mode": "tools_only",
            "operator_mode": "manual",
            "lead_agent": "codex",
            "review_agent": "codex",
            "coding_agent": "claude",
            "current_slice": "keep the slice bounded",
            "peer_review": {
                "current_instruction": "keep the slice bounded",
                "current_instruction_revision": "abc123def456",
                "open_findings": "none",
                "implementer_status": "active",
                "implementer_ack": "acknowledged",
                "implementer_ack_state": "current",
            },
            "arbitration": {"status": "clear", "summary": "", "owner": ""},
            "restart": {
                "status": "handoff_only",
                "resumable": True,
                "source": "review_state",
            },
            "ready_gates": [],
            "role_assignments": [],
            "participants": [],
            "delegated_work": [],
        },
        "packets": [],
        "errors": [],
        "_compat": {
            "project_id": "synthetic",
            "runtime": {"daemons": {"publisher": {}}},
            "service_identity": {},
            "attach_auth_policy": {},
            "agents": [],
        },
    }


def check_bridge_state_keys(
    *,
    bridge_state: dict[str, object],
    contract_fields: frozenset[str],
) -> tuple[dict[str, object], dict[str, object] | None]:
    emitted_fields = frozenset(bridge_state.keys())
    missing = sorted(contract_fields - emitted_fields)
    extra = sorted(emitted_fields - contract_fields)
    coverage: dict[str, object] = {
        "kind": "emitter_parity",
        "contract_id": "ReviewState",
        "check": "bridge_state_keys",
        "ok": not missing and not extra,
    }
    if coverage["ok"]:
        coverage["detail"] = "Event-backed bridge_state keys match ReviewBridgeState."
        return coverage, None
    detail = f"bridge_state key drift: missing={missing or 'none'} extra={extra or 'none'}"
    coverage["detail"] = detail
    return coverage, {
        "kind": "emitter_parity",
        "contract_id": "ReviewState",
        "rule": "emitter-field-gap",
        "detail": detail,
    }


def check_bridge_state_types(
    bridge_state: dict[str, object],
) -> tuple[dict[str, object], dict[str, object] | None]:
    type_errors: list[str] = []
    for field_name, expected_type in _BRIDGE_STATE_EXPECTED_TYPES.items():
        value = bridge_state.get(field_name)
        if value is not None and not isinstance(value, expected_type):
            type_errors.append(
                f"{field_name}: expected {expected_type}, got {type(value).__name__}"
            )
    coverage: dict[str, object] = {
        "kind": "emitter_parity",
        "contract_id": "ReviewState",
        "check": "bridge_state_types",
        "ok": not type_errors,
    }
    if coverage["ok"]:
        coverage["detail"] = "Event-backed bridge_state value types match contract."
        return coverage, None
    detail = f"bridge_state type drift: {'; '.join(type_errors)}"
    coverage["detail"] = detail
    return coverage, {
        "kind": "emitter_parity",
        "contract_id": "ReviewState",
        "rule": "emitter-type-drift",
        "detail": detail,
    }


def check_bridge_field_authority_taxonomy(
    *,
    contract_fields: frozenset[str],
) -> tuple[dict[str, object], dict[str, object] | None]:
    missing = sorted(contract_fields - EVENT_BRIDGE_CLASSIFIED_FIELDS)
    extra = sorted(EVENT_BRIDGE_CLASSIFIED_FIELDS - contract_fields)
    coverage: dict[str, object] = {
        "kind": "emitter_parity",
        "contract_id": "ReviewState",
        "check": "bridge_field_authority_taxonomy",
        "ok": not missing and not extra,
    }
    if coverage["ok"]:
        coverage["detail"] = (
            "Event-backed bridge fields are classified by authority level."
        )
        return coverage, None
    detail = (
        "bridge field taxonomy drift: "
        f"missing={missing or 'none'} extra={extra or 'none'}"
    )
    coverage["detail"] = detail
    return coverage, {
        "kind": "emitter_parity",
        "contract_id": "ReviewState",
        "rule": "bridge-field-taxonomy-drift",
        "detail": detail,
    }


def check_compat_field_coverage(
    *,
    synthetic: dict[str, object],
    repo_root: Path,
) -> tuple[dict[str, object], dict[str, object] | None]:
    from dev.scripts.devctl.review_channel.event_projection import enrich_event_review_state
    from dev.scripts.devctl.review_channel.event_projection_enrichment import (
        EventProjectionContext,
    )

    review_channel_path = repo_root / "dev" / "active" / "review_channel.md"
    projections_root = (
        repo_root / "dev" / "reports" / "review_channel" / "projections" / "latest"
    )
    try:
        enriched, _ = enrich_event_review_state(
            review_state=dict(synthetic),
            context=EventProjectionContext(
                repo_root=repo_root,
                review_channel_path=review_channel_path,
                projections_root=projections_root,
            ),
        )
    except (OSError, ValueError, KeyError) as exc:
        coverage: dict[str, object] = {
            "kind": "emitter_parity",
            "contract_id": "ReviewState",
            "check": "compat_field_coverage",
            "ok": False,
            "detail": f"enrich_event_review_state crashed: {exc}",
        }
        return coverage, {
            "kind": "emitter_parity",
            "contract_id": "ReviewState",
            "rule": "compat-enrichment-crash",
            "detail": f"enrich_event_review_state raised {type(exc).__name__}: {exc}",
        }

    compat = enriched.get("_compat")
    compat_keys = frozenset(compat.keys()) if isinstance(compat, dict) else frozenset()
    compat_missing = sorted(_EXPECTED_COMPAT_KEYS - compat_keys)
    coverage = {
        "kind": "emitter_parity",
        "contract_id": "ReviewState",
        "check": "compat_field_coverage",
        "ok": not compat_missing,
        "expected_compat_keys": sorted(_EXPECTED_COMPAT_KEYS),
        "emitted_compat_keys": sorted(compat_keys),
    }
    if coverage["ok"]:
        coverage["detail"] = "Event-backed _compat carries all transitional fields."
        return coverage, None
    detail = f"_compat missing keys: {compat_missing}"
    coverage["detail"] = detail
    return coverage, {
        "kind": "emitter_parity",
        "contract_id": "ReviewState",
        "rule": "compat-field-gap",
        "detail": detail,
    }


def review_bridge_contract_fields() -> frozenset[str]:
    from dev.scripts.devctl.runtime.review_state_models import ReviewBridgeState

    return frozenset(f.name for f in fields(ReviewBridgeState))
