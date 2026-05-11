"""Projection bundle writers for review-channel state surfaces."""

from __future__ import annotations

import json
import os
import secrets
from contextlib import contextmanager
from collections.abc import Mapping
from copy import deepcopy
from dataclasses import asdict, dataclass
from pathlib import Path

from ..runtime.authority_snapshot import (
    project_authority_snapshot,
    summary_blockers,
    summary_next_command,
)
from ..runtime.surface_provenance import (
    attach_surface_provenance,
    surface_provenance_from_mapping,
)
from .current_session_projection import current_focus_line
from .projection_bundle_parity import apply_phase_zero_parity_projection
from .projection_bundle_markdown import render_latest_markdown
from .projection_bundle_payloads import (
    build_actions_projection,
    build_full_projection,
)
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
    "authority_snapshot",
    "round_proofs",
    "agent_sync",
    "agent_work_board",
    "agent_loop_decisions",
    "attention_windows",
    "coordination_state",
    "warnings",
    "errors",
    "snapshot_id",
    "zref",
)
_PROJECTION_BUNDLE_LOCK_DEPTH = 0


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


@dataclass(frozen=True)
class ReviewChannelProjectionBundleContents:
    """Prepared projection file contents for one review-state snapshot."""

    review_state_json: str
    compact_json: str
    full_json: str
    actions_json: str
    trace_text: str
    latest_markdown: str
    agent_registry_json: str
    commit_pipeline_json: str


def artifact_writes_suppressed() -> bool:
    """Return whether read-side commands should avoid projection writes."""
    return os.environ.get("DEVCTL_NO_ARTIFACT_WRITES", "") == "1"


def projection_paths_for_root(output_root: Path) -> ReviewChannelProjectionPaths:
    """Return the canonical projection paths without writing any files."""
    registry_dir = output_root / "registry"
    return ReviewChannelProjectionPaths(
        root_dir=str(output_root),
        review_state_path=str(output_root / "review_state.json"),
        compact_path=str(output_root / "compact.json"),
        full_path=str(output_root / "full.json"),
        actions_path=str(output_root / "actions.json"),
        trace_path=str(output_root / "trace.ndjson"),
        latest_markdown_path=str(output_root / "latest.md"),
        agent_registry_path=str(registry_dir / "agents.json"),
        commit_pipeline_path=str(output_root / "commit_pipeline.json"),
    )


def _atomic_write_text(path: Path, content: str, *, encoding: str = "utf-8") -> None:
    """Atomically replace ``path`` with ``content``.

    Per Codex rev_pkt_2406/2409/2413: write to a unique tempfile in the
    SAME directory, fsync, then ``os.replace`` into the final name.
    POSIX ``rename(2)`` and Windows ``MoveFileEx(MOVEFILE_REPLACE_EXISTING)``
    both guarantee atomic same-directory replacement, so concurrent
    readers either see the old file or the fully-written new file —
    never a half-written state.

    The tempfile name uses ``<final>.tmp.<pid>.<nonce>`` to keep parallel
    publications from the same process collision-safe.
    """
    parent = path.parent
    parent.mkdir(parents=True, exist_ok=True)
    tmp_name = f"{path.name}.tmp.{os.getpid()}.{secrets.token_hex(4)}"
    tmp_path = parent / tmp_name
    try:
        with open(tmp_path, "w", encoding=encoding) as fh:
            fh.write(content)
            fh.flush()
            try:
                os.fsync(fh.fileno())
            except OSError:
                # fsync may not be supported on every fs (e.g. tmpfs).
                # Atomicity of rename(2) still holds; persistence is best-effort.
                pass
        os.replace(tmp_path, path)
    # broad-except: allow reason=atomic projection write cleanup must preserve original write failure fallback=remove temp file then re-raise
    except Exception:
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise


def _json_artifact(payload: object) -> str:
    """Return compact JSON for machine-read projection artifacts."""
    return json.dumps(payload, separators=(",", ":"))


def projection_paths_to_dict(
    paths: ReviewChannelProjectionPaths | Mapping[str, object] | None,
) -> dict[str, str] | None:
    """Convert projection paths into a report-friendly dict."""
    if paths is None:
        return None
    if isinstance(paths, Mapping):
        return {str(key): str(value) for key, value in paths.items()}
    return asdict(paths)


@contextmanager
def projection_bundle_lock(*roots: Path):
    """Serialize sibling projection-root readers and writers."""
    global _PROJECTION_BUNDLE_LOCK_DEPTH
    if _PROJECTION_BUNDLE_LOCK_DEPTH > 0:
        yield
        return
    lock_dir = _projection_bundle_lock_dir(tuple(roots))
    lock_dir.mkdir(parents=True, exist_ok=True)
    lock_path = lock_dir / ".projection_bundle.lock"
    try:
        import fcntl
    except ImportError:
        yield
        return
    with open(lock_path, "a", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        _PROJECTION_BUNDLE_LOCK_DEPTH += 1
        try:
            yield
        finally:
            _PROJECTION_BUNDLE_LOCK_DEPTH -= 1
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def _projection_bundle_lock_dir(roots: tuple[Path, ...]) -> Path:
    resolved = tuple(root.resolve() for root in roots if root is not None)
    if not resolved:
        return Path(".").resolve()
    common = Path(os.path.commonpath([str(root) for root in resolved]))
    while common.name in {"latest", "projections"} and common.parent != common:
        common = common.parent
    return common

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


def write_projection_bundle_mirrors(
    *,
    output_root: Path,
    mirror_roots: tuple[Path, ...] = (),
    review_state: dict[str, object],
    agent_registry: dict[str, object],
    action: str,
    trace_events: list[dict[str, object]] | None = None,
    full_extras: dict[str, object] | None = None,
) -> ReviewChannelProjectionPaths:
    """Write canonical and mirror roots from one prepared projection payload."""
    contents = prepare_projection_bundle_contents(
        review_state=review_state,
        agent_registry=agent_registry,
        action=action,
        trace_events=trace_events,
        full_extras=full_extras,
    )
    with projection_bundle_lock(output_root, *mirror_roots):
        paths = write_prepared_projection_bundle(
            output_root=output_root,
            contents=contents,
        )
        canonical_root = output_root.resolve()
        for mirror_root in mirror_roots:
            if mirror_root.resolve() == canonical_root:
                continue
            write_prepared_projection_bundle(
                output_root=mirror_root,
                contents=contents,
            )
    return paths


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
    compact = _build_compact_projection(review_state_payload)
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


def write_prepared_projection_bundle(
    *,
    output_root: Path,
    contents: ReviewChannelProjectionBundleContents,
) -> ReviewChannelProjectionPaths:
    """Atomically publish prepared projection contents into one root."""
    paths = projection_paths_for_root(output_root)
    review_state_path = Path(paths.review_state_path)
    compact_path = Path(paths.compact_path)
    full_path = Path(paths.full_path)
    actions_path = Path(paths.actions_path)
    trace_path = Path(paths.trace_path)
    latest_markdown_path = Path(paths.latest_markdown_path)
    agent_registry_path = Path(paths.agent_registry_path)
    commit_pipeline_path = Path(paths.commit_pipeline_path)

    # Per Codex rev_pkt_2406/2409/2413: publish each bundle file atomically.
    # The earlier code wrote review_state.json first then compact/full/etc.
    # sequentially with no atomicity, so any reader entering between writes
    # observed mismatched snapshot_id/zref between siblings — exactly the
    # parity flake check_review_surface_consistency caught. Per-file
    # tempfile + ``os.replace`` in the SAME directory is atomic on POSIX
    # and Windows. ``commit_pipeline.json`` is written LAST and acts as
    # the publication-complete marker.
    _atomic_write_text(
        review_state_path,
        contents.review_state_json,
    )
    _atomic_write_text(compact_path, contents.compact_json)
    _atomic_write_text(full_path, contents.full_json)
    _atomic_write_text(actions_path, contents.actions_json)
    _atomic_write_text(trace_path, contents.trace_text)
    _atomic_write_text(latest_markdown_path, contents.latest_markdown)
    _atomic_write_text(agent_registry_path, contents.agent_registry_json)
    _atomic_write_text(
        commit_pipeline_path,
        contents.commit_pipeline_json,
    )

    return paths


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
        next_command=_projection_next_command(review_state_payload),
    )
    apply_phase_zero_parity_projection(review_state_payload)
    from .agent_work_board_posture import apply_work_board_session_posture
    review_state_payload = apply_work_board_session_posture(review_state_payload)
    return review_state_payload


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
    zref = str(review_state.get("zref") or "").strip()
    current_focus = current_focus_line(review_state)
    payload = {
        "schema_version": 1,
        "command": "review-channel",
        "timestamp": review_state.get("timestamp"),
        "snapshot_id": snapshot_id,
        "zref": zref,
        "ok": review_state.get("ok"),
        "review": review_state.get("review"),
        "authority_snapshot": review_state.get("authority_snapshot"),
        "current_session": current_session,
        "review_candidate": review_candidate,
        "recovery_assessment": review_state.get("recovery_assessment"),
        "service_identity": service_identity,
        "attach_auth_policy": attach_auth_policy,
        "push_decision": _with_surface_identity(push_decision, snapshot_id, zref),
        "doctor": _with_surface_identity(doctor, snapshot_id, zref),
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
    return attach_surface_provenance(
        payload,
        provenance=surface_provenance_from_mapping(review_state),
    )


def _with_surface_identity(payload: object, snapshot_id: str, zref: str) -> object:
    if not isinstance(payload, dict):
        return payload
    result = dict(payload)
    if snapshot_id and not result.get("snapshot_id"):
        result["snapshot_id"] = snapshot_id
    if zref and not result.get("zref"):
        result["zref"] = zref
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

def _projection_next_command(review_state: Mapping[str, object]) -> str:
    recovery = _mapping(review_state.get("recovery_assessment"))
    decision = _mapping(recovery.get("decision"))
    if str(decision.get("action_id") or "").strip() == "cut_checkpoint":
        command = str(decision.get("command") or "").strip()
        if command:
            return command

    if summary_blockers(review_state):
        command = summary_next_command(review_state)
        if command:
            return command

    compat = _mapping(review_state.get("_compat"))
    doctor = _mapping(compat.get("doctor"))
    attention = _mapping(review_state.get("attention"))
    recovery = _mapping(review_state.get("recovery_assessment"))
    decision = _mapping(recovery.get("decision"))
    push_decision = _mapping(compat.get("push_decision"))
    for candidate in (
        doctor.get("recommended_command"),
        decision.get("command"),
        attention.get("recommended_command"),
        push_decision.get("next_step_command"),
    ):
        command = str(candidate or "").strip()
        if command:
            return command
    return ""


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}
