"""Load live controller decisions from typed runtime artifacts."""

from __future__ import annotations

import json
import os
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from .control_decision_packet_inbox import merge_packet_attention
from .value_coercion import coerce_string

DEFAULT_CONTROL_DECISION_INPUT_CANDIDATES = (
    Path("dev/reports/review_channel/state/latest.json"),
)
DEFAULT_STARTUP_AUTHORITY_CANDIDATES = (
    Path("dev/reports/startup/latest/receipt.json"),
)
CONTROL_DECISION_ARTIFACT_ROOT_REL = Path(
    "dev/reports/review_channel/control_decisions"
)


def load_control_decision_payload(
    args: Any,
    *,
    repo_root: Path,
    candidate_paths: Sequence[Path] = DEFAULT_CONTROL_DECISION_INPUT_CANDIDATES,
) -> dict[str, object]:
    """Load a controller decision from inline, explicit, or default artifacts."""

    inline_payload = getattr(args, "control_decision_payload", None)
    if isinstance(inline_payload, dict):
        return inline_payload
    path_value = coerce_string(getattr(args, "control_decision_input", "")).strip()
    actor = coerce_string(getattr(args, "actor", ""))
    role = coerce_string(getattr(args, "role", ""))
    session_id = coerce_string(getattr(args, "session_id", ""))
    if path_value:
        path = _resolve_repo_path(path_value, repo_root=repo_root)
        return control_decision_payload_from_path(
            path,
            actor=actor,
            role=role,
            session_id=session_id,
        )
    payload = load_latest_agent_loop_decision(
        repo_root=repo_root,
        actor=actor,
        role=role,
        session_id=session_id,
        candidate_paths=candidate_paths,
    )
    if payload:
        return _merge_latest_startup_authority(
            payload,
            repo_root=repo_root,
            actor=actor,
            role=role,
        )
    return {}


def load_latest_agent_loop_decision(
    *,
    repo_root: Path,
    actor: str = "",
    role: str = "",
    session_id: str = "",
    candidate_paths: Sequence[Path] = DEFAULT_CONTROL_DECISION_INPUT_CANDIDATES,
) -> dict[str, object]:
    """Resolve the canonical latest AgentLoopDecision artifact for a scoped actor."""

    for candidate in candidate_paths:
        path = repo_root / candidate
        if not path.exists():
            continue
        payload = control_decision_payload_from_path(
            path,
            actor=actor,
            role=role,
            session_id=session_id,
        )
        if payload:
            return payload
    return {}


def control_decision_payload_from_path(
    path: Path,
    *,
    actor: str = "",
    role: str = "",
    session_id: str = "",
) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        return control_decision_payload_from_mapping(
            payload,
            actor=actor,
            role=role,
            session_id=session_id,
        )
    return {}


def control_decision_payload_from_mapping(
    payload: Mapping[str, object],
    *,
    actor: str = "",
    role: str = "",
    session_id: str = "",
) -> dict[str, object]:
    if isinstance(payload.get("agent_loop_decision"), dict):
        return _validated_decision(
            merge_packet_attention(  # type: ignore[index]
                dict(payload["agent_loop_decision"]),
                payload,
                actor=actor,
            ),
            source_payload=payload,
        )
    if isinstance(payload.get("control_decision"), dict):
        return _validated_decision(
            merge_packet_attention(  # type: ignore[index]
                dict(payload["control_decision"]),
                payload,
                actor=actor,
            ),
            source_payload=payload,
        )
    if coerce_string(payload.get("contract_id")) == "AgentLoopDecision":
        return _validated_decision(dict(payload), source_payload=payload)
    rows = payload.get("agent_loop_decisions")
    if isinstance(rows, Sequence) and not isinstance(rows, (str, bytes)):
        decision = _select_agent_loop_decision(
            tuple(item for item in rows if isinstance(item, Mapping)),
            actor=actor,
            role=role,
            session_id=session_id,
        )
        return _validated_decision(
            merge_packet_attention(decision, payload, actor=actor),
            source_payload=payload,
        )
    return {}


def control_decision_input_for_route(
    payload: Mapping[str, object],
    *,
    actor: str,
    role: str,
    session_id: str,
) -> str:
    """Return the stable decision artifact path for one actor/role/session."""

    if not (actor and role and session_id):
        return ""
    rows = payload.get("agent_loop_decisions")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        return ""
    decision = _select_agent_loop_decision(
        tuple(item for item in rows if isinstance(item, Mapping)),
        actor=actor,
        role=role,
        session_id=session_id,
    )
    if not decision:
        return ""
    relpath = control_decision_artifact_relpath(decision)
    return relpath.as_posix() if relpath is not None else ""


def control_decision_artifact_relpath(
    decision: Mapping[str, object],
) -> Path | None:
    """Return the repo-relative stable artifact path for a decision row."""

    if not _decision_has_source(decision):
        return None
    source = _slug(
        coerce_string(decision.get("source_latest_event_id")).strip()
        or coerce_string(decision.get("source_snapshot_id")).strip()
        or coerce_string(decision.get("receipt_id")).strip()
    )
    actor = _slug(coerce_string(decision.get("actor_id")).strip())
    role = _slug(coerce_string(decision.get("actor_role")).strip())
    session_id = _slug(coerce_string(decision.get("session_id")).strip())
    if not (source and actor and role and session_id):
        return None
    return CONTROL_DECISION_ARTIFACT_ROOT_REL / source / (
        f"{actor}-{role}-{session_id}.json"
    )


def write_control_decision_artifacts(
    payload: Mapping[str, object],
    *,
    repo_root: Path,
) -> tuple[Path, ...]:
    """Write stable ignored AgentLoopDecision artifacts for emitted commands."""

    rows = payload.get("agent_loop_decisions")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        return ()
    written: list[Path] = []
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        relpath = control_decision_artifact_relpath(row)
        if relpath is None:
            continue
        path = repo_root / relpath
        _atomic_write_json(path, dict(row))
        written.append(path)
    return tuple(written)


def _select_agent_loop_decision(
    rows: Sequence[Mapping[str, object]],
    *,
    actor: str,
    role: str,
    session_id: str,
) -> dict[str, object]:
    if not (actor and role and session_id):
        return {}
    candidates = tuple(rows)
    if actor:
        candidates = tuple(row for row in candidates if _matches(row, "actor_id", actor))
    if role:
        candidates = tuple(
            row for row in candidates if _matches(row, "actor_role", role)
        )
    if session_id:
        candidates = tuple(
            row for row in candidates if _matches(row, "session_id", session_id)
        )
    if len(candidates) == 1:
        return dict(candidates[0])
    return {}


def _slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", value.strip()).strip("-")


def _atomic_write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(dict(payload), indent=2, sort_keys=True) + "\n"
    tmp_path = path.with_name(f"{path.name}.tmp.{os.getpid()}")
    try:
        tmp_path.write_text(content, encoding="utf-8")
        os.replace(tmp_path, path)
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass


def _matches(row: Mapping[str, object], key: str, expected: str) -> bool:
    return coerce_string(row.get(key)).strip().lower() == expected.strip().lower()


def _validated_decision(
    decision: Mapping[str, object],
    *,
    source_payload: Mapping[str, object],
) -> dict[str, object]:
    if not decision:
        return {}
    if not _decision_has_source(decision):
        return {}
    latest_event_id = _source_latest_event_id(source_payload)
    if latest_event_id and not _decision_matches_latest_event(decision, latest_event_id):
        return {}
    result = dict(decision)
    source_head_sha = _source_head_sha(source_payload)
    if source_head_sha:
        result.setdefault("source_head_sha", source_head_sha)
    return result


def _decision_has_source(decision: Mapping[str, object]) -> bool:
    return bool(
        coerce_string(decision.get("source_latest_event_id")).strip()
        or coerce_string(decision.get("source_snapshot_id")).strip()
    )


def _decision_matches_latest_event(
    decision: Mapping[str, object],
    latest_event_id: str,
) -> bool:
    decision_event_id = coerce_string(decision.get("source_latest_event_id")).strip()
    if decision_event_id:
        return decision_event_id == latest_event_id
    snapshot_id = coerce_string(decision.get("source_snapshot_id")).strip()
    return snapshot_id.endswith(latest_event_id)


def source_latest_event_id_from_reduced_state(payload: Mapping[str, object]) -> str:
    """v4.43.2 (rev_pkt_4717): canonical extraction order for the
    ``source_latest_event_id`` cursor across typed review-channel reduced
    state. Walks the priority paths in order:

    1. ``agent_runtime_clock.source_latest_event_id`` (canonical clock)
    2. ``typed_snapshot_freshness.source_latest_event_id``
    3. ``agent_sync.source_latest_event_id``
    4. ``reviewer_runtime.agent_runtime_clock.source_latest_event_id``
    5. ``reviewer_runtime.source_latest_event_id``
    6. top-level ``source_latest_event_id``

    Returns ``""`` when none of the paths resolves to a non-empty string.

    The public name was promoted from the prior ``_source_latest_event_id``
    in v4.43.2 per codex's directive: review-channel consumers (like the
    obedience guard's stale-decision detector) must reuse this shared
    extractor instead of building parallel cursor selectors that bypass
    the typed reducer projections.
    """
    for path in (
        ("agent_runtime_clock", "source_latest_event_id"),
        ("typed_snapshot_freshness", "source_latest_event_id"),
        ("agent_sync", "source_latest_event_id"),
        ("reviewer_runtime", "agent_runtime_clock", "source_latest_event_id"),
        ("reviewer_runtime", "source_latest_event_id"),
        ("source_latest_event_id",),
    ):
        value = _nested_string(payload, path)
        if value:
            return value
    return ""


#: Backwards-compatible alias for the historical underscore-prefixed name.
#: Existing callers within this module reference ``_source_latest_event_id``;
#: the underscore form is preserved so they continue to work, but new
#: consumers should use the public ``source_latest_event_id_from_reduced_state``.
_source_latest_event_id = source_latest_event_id_from_reduced_state


def _source_head_sha(payload: Mapping[str, object]) -> str:
    for path in (
        ("source_identity", "head_sha"),
        ("reviewer_runtime", "source_identity", "head_sha"),
        ("authority_snapshot", "source_identity", "head_sha"),
    ):
        value = _nested_string(payload, path)
        if value:
            return value
    return ""


def _merge_latest_startup_authority(
    decision: Mapping[str, object],
    *,
    repo_root: Path,
    actor: str,
    role: str,
) -> dict[str, object]:
    result = dict(decision)
    for candidate in DEFAULT_STARTUP_AUTHORITY_CANDIDATES:
        path = repo_root / candidate
        if not path.exists():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(payload, Mapping):
            continue
        authority = payload.get("authority_snapshot")
        if not isinstance(authority, Mapping):
            continue
        if not _authority_matches_subject(authority, actor=actor, role=role):
            continue
        if not _authority_fresh_for_decision(authority, result):
            continue
        snapshot_id = coerce_string(authority.get("snapshot_id")).strip()
        if not snapshot_id:
            continue
        _merge_string_sequence_field(result, authority, "allowed_actions")
        _merge_string_sequence_field(result, authority, "blocked_actions")
        result.setdefault("startup_authority_snapshot_id", snapshot_id)
        source_head_sha = _nested_string(authority, ("source_identity", "head_sha"))
        if source_head_sha:
            result.setdefault("startup_authority_source_head_sha", source_head_sha)
        return result
    return result


def _authority_fresh_for_decision(
    authority: Mapping[str, object],
    decision: Mapping[str, object],
) -> bool:
    decision_head = coerce_string(decision.get("source_head_sha")).strip()
    if not decision_head:
        return True
    authority_head = _nested_string(authority, ("source_identity", "head_sha"))
    return bool(authority_head) and authority_head == decision_head


def _authority_matches_subject(
    authority: Mapping[str, object],
    *,
    actor: str,
    role: str,
) -> bool:
    authority_actor = coerce_string(authority.get("actor_identity")).strip().lower()
    authority_role = coerce_string(authority.get("actor_role")).strip().lower()
    if actor and authority_actor and authority_actor != actor.strip().lower():
        return False
    if role and authority_role and authority_role != role.strip().lower():
        return False
    return bool(authority_actor or authority_role)


def _merge_string_sequence_field(
    target: dict[str, object],
    source: Mapping[str, object],
    key: str,
) -> None:
    merged: list[str] = []
    for value in (target.get(key), source.get(key)):
        if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
            continue
        for item in value:
            text = coerce_string(item).strip()
            if text and text not in merged:
                merged.append(text)
    if merged:
        target[key] = merged


def _nested_string(payload: Mapping[str, object], path: Sequence[str]) -> str:
    current: object = payload
    for key in path:
        if not isinstance(current, Mapping):
            return ""
        current = current.get(key)
    return coerce_string(current).strip()


def _resolve_repo_path(value: str, *, repo_root: Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return repo_root / path


__all__ = [
    "CONTROL_DECISION_ARTIFACT_ROOT_REL",
    "DEFAULT_CONTROL_DECISION_INPUT_CANDIDATES",
    "control_decision_artifact_relpath",
    "control_decision_input_for_route",
    "control_decision_payload_from_mapping",
    "control_decision_payload_from_path",
    "load_latest_agent_loop_decision",
    "load_control_decision_payload",
    "source_latest_event_id_from_reduced_state",
    "write_control_decision_artifacts",
]
