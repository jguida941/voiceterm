"""Snapshot/zref/provenance helpers for review-surface consistency checks."""

from __future__ import annotations

import json

from .support import _nested


def snapshot_ids(
    *,
    startup: dict[str, object],
    review_state: dict[str, object],
    compact: dict[str, object],
    commit_pipeline: dict[str, object],
    bridge_poll: dict[str, object],
    turn_authority: dict[str, object],
) -> dict[str, str]:
    return {
        "startup_context": _nested(startup, "snapshot_id"),
        "startup_push_decision": _nested(startup, "push_decision", "snapshot_id"),
        "review_state": _nested(review_state, "snapshot_id"),
        "review_state_commit_pipeline": _nested(
            review_state, "commit_pipeline", "snapshot_id"
        ),
        "review_state_doctor": _nested(review_state, "_compat", "doctor", "snapshot_id"),
        "review_state_bridge_projection": _nested(
            review_state,
            "_compat",
            "bridge_projection",
            "metadata",
            "snapshot_id",
        ),
        "compact": _nested(compact, "snapshot_id"),
        "compact_push_decision": _nested(compact, "push_decision", "snapshot_id"),
        "compact_doctor": _nested(compact, "doctor", "snapshot_id"),
        "commit_pipeline": _nested(commit_pipeline, "snapshot_id"),
        "bridge_poll": _nested(bridge_poll, "snapshot_id"),
        "turn_authority": _nested(turn_authority, "snapshot_id"),
    }


def zrefs(
    *,
    startup: dict[str, object],
    review_state: dict[str, object],
    compact: dict[str, object],
    commit_pipeline: dict[str, object],
    bridge_poll: dict[str, object],
    turn_authority: dict[str, object],
) -> dict[str, str]:
    return {
        "startup_context": _nested(startup, "zref"),
        "startup_push_decision": _nested(startup, "push_decision", "zref"),
        "review_state": _nested(review_state, "zref"),
        "review_state_commit_pipeline": _nested(review_state, "commit_pipeline", "zref"),
        "review_state_bridge_projection": _nested(
            review_state,
            "_compat",
            "bridge_projection",
            "metadata",
            "zref",
        ),
        "review_state_registry": _nested(review_state, "registry", "zref"),
        "compact": _nested(compact, "zref"),
        "compact_push_decision": _nested(compact, "push_decision", "zref"),
        "commit_pipeline": _nested(commit_pipeline, "zref"),
        "bridge_poll": _nested(bridge_poll, "zref"),
        "turn_authority": _nested(turn_authority, "zref"),
    }


def generation_ids(
    *,
    review_state: dict[str, object],
    compact: dict[str, object],
    commit_pipeline: dict[str, object],
) -> dict[str, str]:
    return {
        "review_state_commit_pipeline": _nested(
            review_state, "commit_pipeline", "generation_id"
        ),
        "review_state_doctor": _nested(review_state, "_compat", "doctor", "generation_id"),
        "compact_doctor": _nested(compact, "doctor", "generation_id"),
        "commit_pipeline": _nested(commit_pipeline, "generation_id"),
    }


def snapshot_errors(
    snapshot_ids: dict[str, str],
    zrefs: dict[str, str],
    generation_ids: dict[str, str],
) -> list[str]:
    errors: list[str] = []
    missing = [surface for surface, value in snapshot_ids.items() if not value]
    if missing:
        errors.append("missing snapshot_id on: " + ", ".join(sorted(missing)))
    missing_zrefs = [surface for surface, value in zrefs.items() if not value]
    if missing_zrefs:
        errors.append("missing zref on: " + ", ".join(sorted(missing_zrefs)))
    nonempty_snapshots = sorted({value for value in snapshot_ids.values() if value})
    nonempty_zrefs = sorted({value for value in zrefs.values() if value})
    nonempty_generations = sorted({value for value in generation_ids.values() if value})
    if len(nonempty_snapshots) > 1:
        errors.append("snapshot_id mismatch: " + ", ".join(nonempty_snapshots))
    if len(nonempty_zrefs) > 1:
        errors.append("zref mismatch: " + ", ".join(nonempty_zrefs))
    if len(nonempty_generations) > 1:
        errors.append("pipeline generation mismatch: " + ", ".join(nonempty_generations))
    return errors


def provenance_payloads(
    *,
    review_state: dict[str, object],
) -> dict[str, dict[str, object]]:
    surfaces = {
        "review_state": review_state,
        "review_state_registry": _nested(review_state, "registry"),
        "review_state_bridge_projection": _nested(
            review_state,
            "_compat",
            "bridge_projection",
            "metadata",
        ),
    }
    return {
        surface: surface_provenance(payload)
        for surface, payload in surfaces.items()
        if isinstance(payload, dict)
    }


def provenance_errors(
    provenance: dict[str, dict[str, object]],
) -> list[str]:
    errors: list[str] = []
    if not provenance:
        return errors
    required_keys = (
        "source_identity",
        "source_contract",
        "source_command",
        "observed_fields",
        "inferred_fields",
    )
    missing = [
        surface
        for surface, payload in provenance.items()
        if any(not payload.get(key) for key in required_keys)
    ]
    if missing:
        errors.append("missing provenance tuple on: " + ", ".join(sorted(missing)))
    normalized = {
        surface: json.dumps(payload, sort_keys=True)
        for surface, payload in provenance.items()
        if all(payload.get(key) for key in required_keys)
    }
    if len(set(normalized.values())) > 1:
        surfaces = ", ".join(
            f"{surface}={payload}"
            for surface, payload in sorted(normalized.items())
        )
        errors.append("provenance mismatch: " + surfaces)
    return errors


def surface_provenance(payload: dict[str, object]) -> dict[str, object]:
    return {
        "source_identity": _nested(payload, "source_identity") or {},
        "source_contract": _nested(payload, "source_contract"),
        "source_command": _nested(payload, "source_command"),
        "observed_fields": list(_nested(payload, "observed_fields") or []),
        "inferred_fields": list(_nested(payload, "inferred_fields") or []),
    }
