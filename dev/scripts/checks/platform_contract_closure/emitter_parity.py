"""Review-state emitter parity checks for the platform contract-closure guard."""

from __future__ import annotations

from dataclasses import fields
from pathlib import Path

from .emitter_parity_contract_checks import (
    _BRIDGE_STATE_EXPECTED_TYPES,
    build_synthetic_review_state as _build_synthetic_review_state,
    check_bridge_field_authority_taxonomy,
    check_bridge_state_keys,
    check_bridge_state_types,
    check_compat_field_coverage,
    review_bridge_contract_fields,
)
from .emitter_parity_roundtrip import check_bridge_state_parser_roundtrip


def check_review_state_emitter_parity() -> list[tuple[dict[str, object], dict[str, object] | None]]:
    """Verify event-backed emitter produces parity with ReviewBridgeState contract."""
    from dev.scripts.devctl.review_channel.event_projection import (
        build_event_bridge_liveness_projection,
        build_event_bridge_state_projection,
    )

    repo_root = Path(__file__).resolve().parent.parent.parent.parent.parent
    results: list[tuple[dict[str, object], dict[str, object] | None]] = []
    contract_fields = review_bridge_contract_fields()
    synthetic = _build_synthetic_review_state()
    liveness = build_event_bridge_liveness_projection(synthetic)
    bridge_state = build_event_bridge_state_projection(
        review_state=synthetic,
        bridge_liveness=liveness,
    )

    for coverage, violation in (
        check_bridge_state_keys(
            bridge_state=bridge_state,
            contract_fields=contract_fields,
        ),
        check_bridge_state_types(bridge_state),
        check_bridge_field_authority_taxonomy(contract_fields=contract_fields),
    ):
        results.append((coverage, violation))
    results.extend(
        check_bridge_state_parser_roundtrip(
            synthetic=synthetic,
            bridge_state=bridge_state,
            bridge_liveness=liveness,
            contract_fields=contract_fields,
        )
    )
    results.append(
        check_compat_field_coverage(
            synthetic=synthetic,
            repo_root=repo_root,
        )
    )

    # Checks 6-8: on-disk artifact parity.
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
    _ADDITIVE_FIELDS = frozenset(
        {
            "posted_at",
            "pipeline_generation",
            "staged_snapshot_hash",
            "guard_results_summary",
        }
    )
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
