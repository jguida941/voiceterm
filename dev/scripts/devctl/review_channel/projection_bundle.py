"""Projection bundle writers for review-channel state surfaces."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from copy import deepcopy
from dataclasses import asdict, dataclass
from pathlib import Path

from .context_refs import normalize_context_pack_refs
from .current_session_projection import current_focus_line
from .projection_bundle_markdown import render_latest_markdown
from .projection_observation import build_observation_projection

_TYPED_REVIEW_STATE_KEYS = (
    "schema_version",
    "contract_id",
    "command",
    "action",
    "timestamp",
    "ok",
    "review",
    "queue",
    "current_session",
    "packet_inbox",
    "collaboration",
    "bridge",
    "attention",
    "packets",
    "registry",
    "review_candidate",
    "push_authorization",
    "recovery_assessment",
    "reviewer_runtime",
    "commit_pipeline",
    "coordination",
    "warnings",
    "errors",
    "snapshot_id",
)


@dataclass(frozen=True)
class ReviewChannelProjectionPaths:
    """Paths written for the latest review projections."""

    root_dir: str
    review_state_path: str
    compact_path: str
    full_path: str
    actions_path: str
    trace_path: str
    latest_markdown_path: str
    agent_registry_path: str
    commit_pipeline_path: str = ""


def projection_paths_to_dict(
    paths: ReviewChannelProjectionPaths | Mapping[str, object] | None,
) -> dict[str, str] | None:
    """Convert projection paths into a report-friendly dict."""
    if paths is None:
        return None
    if isinstance(paths, Mapping):
        return {str(key): str(value) for key, value in paths.items()}
    return asdict(paths)

def write_projection_bundle(
    *,
    output_root: Path,
    review_state: dict[str, object],
    agent_registry: dict[str, object],
    action: str,
    trace_events: list[dict[str, object]] | None = None,
    full_extras: dict[str, object] | None = None,
) -> ReviewChannelProjectionPaths:
    """Write a projection bundle from one reduced review-state snapshot."""
    review_state_payload = _normalize_review_state_payload(review_state)
    obs_proj = build_observation_projection(review_state_payload)
    if (
        obs_proj is not None
        and "reviewer_observation" not in review_state_payload
    ):
        review_state_payload["reviewer_observation"] = obs_proj
    compact = _build_compact_projection(review_state_payload)
    actions = _build_actions_projection(review_state_payload)
    full = {
        "schema_version": 1,
        "command": "review-channel",
        "action": action,
        "timestamp": review_state_payload.get("timestamp"),
        "ok": review_state_payload.get("ok"),
        "review_state": review_state_payload,
        "agent_registry": agent_registry,
        "warnings": review_state_payload.get("warnings", []),
        "errors": review_state_payload.get("errors", []),
    }
    if isinstance(full_extras, dict):
        full.update(full_extras)
    latest_markdown = render_latest_markdown(review_state_payload, agent_registry)

    registry_dir = output_root / "registry"
    registry_dir.mkdir(parents=True, exist_ok=True)

    review_state_path = output_root / "review_state.json"
    compact_path = output_root / "compact.json"
    full_path = output_root / "full.json"
    actions_path = output_root / "actions.json"
    trace_path = output_root / "trace.ndjson"
    latest_markdown_path = output_root / "latest.md"
    agent_registry_path = registry_dir / "agents.json"
    commit_pipeline_path = output_root / "commit_pipeline.json"

    review_state_path.write_text(
        json.dumps(review_state_payload, indent=2),
        encoding="utf-8",
    )
    compact_path.write_text(json.dumps(compact, indent=2), encoding="utf-8")
    full_path.write_text(json.dumps(full, indent=2), encoding="utf-8")
    actions_path.write_text(json.dumps(actions, indent=2), encoding="utf-8")
    trace_path.write_text(_render_trace_projection(trace_events or []), encoding="utf-8")
    latest_markdown_path.write_text(latest_markdown, encoding="utf-8")
    agent_registry_path.write_text(
        json.dumps(agent_registry, indent=2),
        encoding="utf-8",
    )
    commit_pipeline_path.write_text(
        json.dumps(review_state_payload.get("commit_pipeline", {}), indent=2),
        encoding="utf-8",
    )

    return ReviewChannelProjectionPaths(
        root_dir=str(output_root),
        review_state_path=str(review_state_path),
        compact_path=str(compact_path),
        full_path=str(full_path),
        actions_path=str(actions_path),
        trace_path=str(trace_path),
        latest_markdown_path=str(latest_markdown_path),
        agent_registry_path=str(agent_registry_path),
        commit_pipeline_path=str(commit_pipeline_path),
    )


def _build_compact_projection(review_state: dict[str, object]) -> dict[str, object]:
    queue = review_state.get("queue", {})
    bridge = review_state.get("bridge", {})
    current_session = review_state.get("current_session", {})
    review_candidate = review_state.get("review_candidate")
    compat = review_state.get("_compat") or {}
    service_identity = compat.get("service_identity")
    attach_auth_policy = compat.get("attach_auth_policy")
    push_decision = compat.get("push_decision")
    doctor = compat.get("doctor")
    commit_pipeline = review_state.get("commit_pipeline")
    snapshot_id = str(review_state.get("snapshot_id") or "").strip()
    current_focus = current_focus_line(review_state)
    return {
        "schema_version": 1,
        "command": "review-channel",
        "timestamp": review_state.get("timestamp"),
        "snapshot_id": snapshot_id,
        "ok": review_state.get("ok"),
        "review": review_state.get("review"),
        "current_session": current_session,
        "review_candidate": review_candidate,
        "recovery_assessment": review_state.get("recovery_assessment"),
        "service_identity": service_identity,
        "attach_auth_policy": attach_auth_policy,
        "push_decision": _with_snapshot_id(push_decision, snapshot_id),
        "doctor": _with_snapshot_id(doctor, snapshot_id),
        "commit_pipeline": commit_pipeline,
        "bridge": {
            "last_codex_poll_utc": bridge.get("last_codex_poll_utc"),
            "last_worktree_hash": bridge.get("last_worktree_hash"),
            "head_at_push_time": bridge.get("head_at_push_time", ""),
            "current_instruction": current_focus,
        },
        "queue": {
            **queue,
            "current_focus": current_focus,
        },
        "reviewer_observation": build_observation_projection(review_state),
        "warnings": review_state.get("warnings", []),
        "errors": review_state.get("errors", []),
    }


def _build_actions_projection(review_state: dict[str, object]) -> dict[str, object]:
    packets = review_state.get("packets")
    action_rows: list[dict[str, object]] = []
    if isinstance(packets, Sequence) and not isinstance(packets, (str, bytes)):
        for packet in packets:
            if not isinstance(packet, dict):
                continue
            action_rows.append(
                {
                    "packet_id": packet.get("packet_id"),
                    "requested_action": packet.get("requested_action"),
                    "policy_hint": packet.get("policy_hint"),
                    "approval_required": packet.get("approval_required"),
                    "status": packet.get("status"),
                    "target_kind": packet.get("target_kind"),
                    "target_ref": packet.get("target_ref"),
                    "target_revision": packet.get("target_revision"),
                    "pipeline_generation": packet.get("pipeline_generation"),
                    "staged_snapshot_hash": packet.get("staged_snapshot_hash"),
                    "guard_results_summary": packet.get("guard_results_summary"),
                    "context_pack_refs": normalize_context_pack_refs(
                        packet.get("context_pack_refs")
                    ),
                }
            )
    return {
        "schema_version": 1,
        "command": "review-channel",
        "timestamp": review_state.get("timestamp"),
        "actions": action_rows,
    }


def _with_snapshot_id(payload: object, snapshot_id: str) -> object:
    if not isinstance(payload, dict):
        return payload
    result = dict(payload)
    if snapshot_id and not result.get("snapshot_id"):
        result["snapshot_id"] = snapshot_id
    return result


def _render_trace_projection(trace_events: list[dict[str, object]]) -> str:
    lines: list[str] = []
    for event in trace_events:
        lines.append(json.dumps(event, sort_keys=True))
    return "\n".join(lines) + ("\n" if lines else "")


def _normalize_review_state_payload(
    review_state: Mapping[str, object],
) -> dict[str, object]:
    """Project review_state artifacts through the typed contract before writing.

    This keeps on-disk `review_state.json` aligned with the runtime dataclass
    schema even when minimal/synthetic callers omit additive fields, while
    preserving compatibility-only extras such as `_compat`.
    """
    from ..runtime.review_state_parser import review_state_from_payload

    normalized = deepcopy(dict(review_state))
    typed_state = review_state_from_payload(normalized)
    if typed_state is None:
        return normalized

    typed_payload = typed_state.to_dict()
    for key in _TYPED_REVIEW_STATE_KEYS:
        normalized[key] = typed_payload.get(key)
    return normalized
