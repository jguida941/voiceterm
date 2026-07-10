"""Projection bundle writers for review-channel state surfaces."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path

from ..runtime.authority_snapshot import project_authority_snapshot
from .projection_bundle_compact import (
    build_compact_projection,
    projection_next_command,
)
from .projection_bundle_io import (
    ReviewChannelProjectionBundleContents,
    ReviewChannelProjectionPaths,
    canonical_projection_root_for_status_root,
    projection_bundle_lock,
    projection_paths_for_root,
    projection_paths_to_dict,
    write_prepared_projection_bundle,
)
from .projection_bundle_parity import apply_phase_zero_parity_projection
from .projection_bundle_markdown import render_latest_markdown
from .projection_bundle_payloads import (
    build_actions_projection,
    build_full_projection,
)
from .projection_observation import build_observation_projection
from .recovery_command_suppression import (
    suppress_legacy_recovery_command_when_remote_only,
)

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
    "authority_snapshot",
    "round_proofs",
    "agent_sync",
    "agent_work_board",
    "agent_loop_decisions",
    "attention_windows",
    "session_status_projection",
    "coordination_state",
    "warnings",
    "errors",
    "snapshot_id",
    "zref",
)


def artifact_writes_suppressed() -> bool:
    """Return whether read-side commands should avoid projection writes."""
    return os.environ.get("DEVCTL_NO_ARTIFACT_WRITES", "") == "1"


def _json_artifact(payload: object) -> str:
    """Return compact JSON for machine-read projection artifacts."""
    return json.dumps(payload, separators=(",", ":"))


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
    contents = prepare_projection_bundle_contents(
        review_state=review_state,
        agent_registry=agent_registry,
        action=action,
        trace_events=trace_events,
        full_extras=full_extras,
    )
    with projection_bundle_lock(output_root):
        return write_prepared_projection_bundle(
            output_root=output_root,
            contents=contents,
        )


def prepare_projection_bundle_contents(
    *,
    review_state: dict[str, object],
    agent_registry: dict[str, object],
    action: str,
    trace_events: list[dict[str, object]] | None = None,
    full_extras: dict[str, object] | None = None,
) -> ReviewChannelProjectionBundleContents:
    """Build all projection files from one canonicalized review-state snapshot."""
    review_state_payload = canonicalize_projection_review_state(review_state)
    suppress_legacy_recovery_command_when_remote_only(review_state_payload)
    compact = build_compact_projection(review_state_payload)
    actions = build_actions_projection(review_state_payload)
    full = build_full_projection(
        action=action,
        review_state=review_state_payload,
        agent_registry=agent_registry,
    )
    if isinstance(full_extras, dict):
        full.update(full_extras)
    latest_markdown = render_latest_markdown(review_state_payload, agent_registry)

    return ReviewChannelProjectionBundleContents(
        review_state_json=_json_artifact(review_state_payload),
        compact_json=_json_artifact(compact),
        full_json=_json_artifact(full),
        actions_json=_json_artifact(actions),
        trace_text=_render_trace_projection(trace_events or []),
        latest_markdown=latest_markdown,
        agent_registry_json=_json_artifact(agent_registry),
        commit_pipeline_json=_json_artifact(
            review_state_payload.get("commit_pipeline", {})
        ),
    )


def canonicalize_projection_review_state(
    review_state: Mapping[str, object],
) -> dict[str, object]:
    """Return the same canonical review-state payload that bundle writes persist."""
    review_state_payload = _normalize_review_state_payload(review_state)
    _apply_review_state_authority_context(review_state_payload)
    obs_proj = build_observation_projection(review_state_payload)
    if (
        obs_proj is not None
        and "reviewer_observation" not in review_state_payload
    ):
        review_state_payload["reviewer_observation"] = obs_proj
    project_authority_snapshot(
        review_state_payload,
        caller_role="observer",
        next_command=projection_next_command(review_state_payload),
    )
    apply_phase_zero_parity_projection(review_state_payload)
    from .agent_work_board_posture import apply_work_board_session_posture
    review_state_payload = apply_work_board_session_posture(review_state_payload)
    return review_state_payload


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


def _apply_review_state_authority_context(
    review_state_payload: dict[str, object],
) -> None:
    """Seed shared authority fields from the typed review-state contract.

    Startup already projects observed topology and implementation permission
    through the shared control-topology reducer. Mirror that same reducer here
    before the compact `AuthoritySnapshot` is compiled so status, doctor,
    session-resume, and startup can agree on the same runtime truth.
    """
    from ..runtime.control_topology import derive_startup_control_truth
    from ..runtime.review_state_parser import review_state_from_payload

    typed_state = review_state_from_payload(review_state_payload)
    if typed_state is None:
        return

    observed_control_topology, implementation_permission = (
        derive_startup_control_truth(typed_state)
    )
    review_state_payload["observed_control_topology"] = observed_control_topology
    review_state_payload["implementation_permission"] = implementation_permission
