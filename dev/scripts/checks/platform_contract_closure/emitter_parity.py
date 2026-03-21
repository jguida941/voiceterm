"""Review-state emitter parity checks for the platform contract-closure guard."""

from __future__ import annotations

from dataclasses import fields
from pathlib import Path

_EXPECTED_COMPAT_KEYS = frozenset({
    "project_id", "runtime", "service_identity", "attach_auth_policy", "agents",
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
    "implementer_completion_stall": bool,
    "publisher_running": bool,
}


def _build_synthetic_review_state() -> dict[str, object]:
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
            "open_findings": "none",
            "last_reviewed_scope": "MP-355",
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


def check_review_state_emitter_parity() -> list[tuple[dict[str, object], dict[str, object] | None]]:
    """Verify event-backed emitter produces parity with ReviewBridgeState contract."""
    from dev.scripts.devctl.runtime.review_state_models import ReviewBridgeState
    from dev.scripts.devctl.review_channel.event_projection import (
        _build_event_bridge_liveness,
        _build_event_bridge_state,
        enrich_event_review_state,
    )

    results: list[tuple[dict[str, object], dict[str, object] | None]] = []
    contract_fields = frozenset(f.name for f in fields(ReviewBridgeState))
    synthetic = _build_synthetic_review_state()
    liveness = _build_event_bridge_liveness(synthetic)
    bridge_state = _build_event_bridge_state(
        review_state=synthetic,
        bridge_liveness=liveness,
    )

    # Check 1: field key parity
    emitted_fields = frozenset(bridge_state.keys())
    missing = sorted(contract_fields - emitted_fields)
    extra = sorted(emitted_fields - contract_fields)
    key_ok = not missing and not extra
    key_coverage: dict[str, object] = {
        "kind": "emitter_parity",
        "contract_id": "ReviewState",
        "check": "bridge_state_keys",
        "ok": key_ok,
    }
    if key_ok:
        key_coverage["detail"] = "Event-backed bridge_state keys match ReviewBridgeState."
        results.append((key_coverage, None))
    else:
        detail = f"bridge_state key drift: missing={missing or 'none'} extra={extra or 'none'}"
        key_coverage["detail"] = detail
        results.append((key_coverage, {
            "kind": "emitter_parity",
            "contract_id": "ReviewState",
            "rule": "emitter-field-gap",
            "detail": detail,
        }))

    # Check 2: field value types
    type_errors: list[str] = []
    for field_name, expected_type in _BRIDGE_STATE_EXPECTED_TYPES.items():
        value = bridge_state.get(field_name)
        if value is not None and not isinstance(value, expected_type):
            type_errors.append(
                f"{field_name}: expected {expected_type}, got {type(value).__name__}"
            )
    type_ok = not type_errors
    type_coverage: dict[str, object] = {
        "kind": "emitter_parity",
        "contract_id": "ReviewState",
        "check": "bridge_state_types",
        "ok": type_ok,
    }
    if type_ok:
        type_coverage["detail"] = "Event-backed bridge_state value types match contract."
        results.append((type_coverage, None))
    else:
        detail = f"bridge_state type drift: {'; '.join(type_errors)}"
        type_coverage["detail"] = detail
        results.append((type_coverage, {
            "kind": "emitter_parity",
            "contract_id": "ReviewState",
            "rule": "emitter-type-drift",
            "detail": detail,
        }))

    # Check 3: _compat transitional field coverage
    repo_root = Path(__file__).resolve().parent.parent.parent.parent.parent
    review_channel_path = repo_root / "dev" / "active" / "review_channel.md"
    projections_root = repo_root / "dev" / "reports" / "review_channel" / "projections" / "latest"
    try:
        enriched, _ = enrich_event_review_state(
            review_state=dict(synthetic),
            repo_root=repo_root,
            review_channel_path=review_channel_path,
            projections_root=projections_root,
        )
    except (OSError, ValueError, KeyError) as exc:
        compat_coverage_err: dict[str, object] = {
            "kind": "emitter_parity",
            "contract_id": "ReviewState",
            "check": "compat_field_coverage",
            "ok": False,
            "detail": f"enrich_event_review_state crashed: {exc}",
        }
        results.append((compat_coverage_err, {
            "kind": "emitter_parity",
            "contract_id": "ReviewState",
            "rule": "compat-enrichment-crash",
            "detail": f"enrich_event_review_state raised {type(exc).__name__}: {exc}",
        }))
        return results
    compat = enriched.get("_compat")
    compat_keys = frozenset(compat.keys()) if isinstance(compat, dict) else frozenset()
    compat_missing = sorted(_EXPECTED_COMPAT_KEYS - compat_keys)
    compat_ok = not compat_missing
    compat_coverage: dict[str, object] = {
        "kind": "emitter_parity",
        "contract_id": "ReviewState",
        "check": "compat_field_coverage",
        "ok": compat_ok,
        "expected_compat_keys": sorted(_EXPECTED_COMPAT_KEYS),
        "emitted_compat_keys": sorted(compat_keys),
    }
    if compat_ok:
        compat_coverage["detail"] = "Event-backed _compat carries all transitional fields."
        results.append((compat_coverage, None))
    else:
        detail = f"_compat missing keys: {compat_missing}"
        compat_coverage["detail"] = detail
        results.append((compat_coverage, {
            "kind": "emitter_parity",
            "contract_id": "ReviewState",
            "rule": "compat-field-gap",
            "detail": detail,
        }))

    # Checks 4-6: on-disk artifact parity.
    # Only run when the latest artifact was produced by the event-backed path
    # (surface_mode == "event-backed"). Artifacts from bridge-backed heartbeats
    # use a different bridge shape and are not emitter-parity failures.
    artifact_path = repo_root / "dev" / "reports" / "review_channel" / "projections" / "latest" / "review_state.json"
    on_disk = _load_event_backed_artifact(artifact_path)
    if on_disk is not None:
        results.extend(_check_artifact_bridge(on_disk, contract_fields))
        results.extend(_check_artifact_packets(on_disk))
        results.extend(_check_full_projection_bridge(artifact_path.parent, contract_fields))

    return results


def _load_event_backed_artifact(path: Path) -> dict[str, object] | None:
    """Load review_state.json only if it was produced by the event-backed path."""
    if not path.is_file():
        return None
    import json as _json

    try:
        data = _json.loads(path.read_text(encoding="utf-8"))
    except (OSError, _json.JSONDecodeError):
        return None
    review = data.get("review")
    if isinstance(review, dict) and review.get("surface_mode") == "event-backed":
        return data
    return None


def _check_artifact_bridge(
    on_disk: dict[str, object],
    contract_fields: frozenset[str],
) -> list[tuple[dict[str, object], dict[str, object] | None]]:
    bridge = on_disk.get("bridge")
    if not isinstance(bridge, dict):
        return []
    missing = sorted(contract_fields - set(bridge.keys()))
    extra = sorted(set(bridge.keys()) - contract_fields)
    ok = not missing and not extra
    cov: dict[str, object] = {
        "kind": "emitter_parity", "contract_id": "ReviewState",
        "check": "artifact_bridge_parity", "ok": ok,
    }
    if ok:
        cov["detail"] = "On-disk review_state.json bridge matches contract."
        return [(cov, None)]
    detail = f"Artifact bridge drift: missing={missing or 'none'} extra={extra or 'none'}"
    cov["detail"] = detail
    return [(cov, {"kind": "emitter_parity", "contract_id": "ReviewState",
                   "rule": "artifact-bridge-drift", "detail": detail})]


def _check_artifact_packets(
    on_disk: dict[str, object],
) -> list[tuple[dict[str, object], dict[str, object] | None]]:
    from dev.scripts.devctl.runtime.review_state_models import ReviewPacketState

    pkt_fields = frozenset(f.name for f in fields(ReviewPacketState))
    # Additive fields that may be absent in stale event state files written
    # before the field was added. These produce coverage notes, not violations.
    _ADDITIVE_FIELDS = frozenset({"posted_at"})
    packets = on_disk.get("packets")
    if not isinstance(packets, list) or not packets:
        return []
    sample = packets[0] if isinstance(packets[0], dict) else {}
    missing = sorted((pkt_fields - _ADDITIVE_FIELDS) - set(sample.keys()))
    cov: dict[str, object] = {
        "kind": "emitter_parity", "contract_id": "ReviewState",
        "check": "packet_shape_boundary", "ok": not missing,
    }
    if not missing:
        cov["detail"] = "Emitted packets are a superset of ReviewPacketState."
        return [(cov, None)]
    detail = f"Packet shape gap: missing {missing}"
    cov["detail"] = detail
    return [(cov, {"kind": "emitter_parity", "contract_id": "ReviewState",
                   "rule": "packet-shape-gap", "detail": detail})]


def _check_full_projection_bridge(
    projections_root: Path,
    contract_fields: frozenset[str],
) -> list[tuple[dict[str, object], dict[str, object] | None]]:
    full_path = projections_root / "full.json"
    if not full_path.is_file():
        return []
    import json as _json

    try:
        full = _json.loads(full_path.read_text(encoding="utf-8"))
    except (OSError, _json.JSONDecodeError):
        return []
    rs = full.get("review_state")
    if not isinstance(rs, dict):
        return []
    bridge = rs.get("bridge")
    if not isinstance(bridge, dict):
        return []
    missing = sorted(contract_fields - set(bridge.keys()))
    ok = not missing
    cov: dict[str, object] = {
        "kind": "emitter_parity", "contract_id": "ReviewState",
        "check": "full_projection_bridge", "ok": ok,
    }
    if ok:
        cov["detail"] = "Full projection bridge matches contract."
        return [(cov, None)]
    detail = f"Full projection bridge drift: missing={missing}"
    cov["detail"] = detail
    return [(cov, {"kind": "emitter_parity", "contract_id": "ReviewState",
                   "rule": "full-projection-bridge-drift", "detail": detail})]
