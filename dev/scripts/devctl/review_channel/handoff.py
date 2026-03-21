"""Handoff helpers for the transitional review-channel launcher.

These helpers reduce the live markdown bridge into explicit handoff artifacts
so fresh conductor sessions can resume without relying on compaction summaries.

Governing docs for this slice:

- `AGENTS.md`
- `dev/active/MASTER_PLAN.md`
- `dev/active/review_channel.md`
- `dev/active/continuous_swarm.md`
- `bridge.md`
"""

from __future__ import annotations

import json
import re
import time
from hashlib import sha256
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from ..common import display_path
from ..markdown_sections import parse_markdown_sections as extract_bridge_sections
from ..runtime.role_profile import role_for_provider
from ..time_utils import utc_timestamp
from .handoff_constants import (
    BRIDGE_LIVENESS_KEYS,
    BRIDGE_METADATA_PATTERNS,
    DEFAULT_CODEX_POLL_DUE_AFTER_SECONDS,
    DEFAULT_CODEX_POLL_STALE_AFTER_SECONDS,
    GENERIC_NEXT_ACTION_MARKERS,
    IDLE_FINDING_MARKERS,
    IDLE_NEXT_ACTION_MARKERS,
    MARKDOWN_ITEM_RE,
    PLACEHOLDER_STATUS_MARKERS,
    RESOLVED_VERDICT_MARKERS,
    ROLLOVER_ACK_PREFIX,
    ROLLOVER_ACK_SECTION,
    TRACKED_BRIDGE_SECTIONS,
    _RESOLVED_ECHO_RE,
    _is_substantive_text,
)

# validate_launch_bridge_state and validate_live_bridge_contract moved to
# bridge_validation.py. Import from there directly.
from .handoff_markdown import (
    _derive_current_atomic_step,
    _extract_markdown_items,
    _first_markdown_item,
    _group_owned_lanes,
    _normalize_inline_markdown,
)
from .handoff_render import render_handoff_markdown
from .handoff_time import _codex_poll_advanced, _parse_utc_z, _timestamp_age_seconds
from .peer_liveness import (
    CodexPollState,
    IMPLEMENTER_STALL_MARKERS,
    OverallLivenessState,
    ReviewerMode,
    classify_reviewer_freshness,
    normalize_reviewer_mode,
    reviewer_mode_is_active,
)


@dataclass(frozen=True)
class BridgeSnapshot:
    """Current bridge metadata and tracked live sections."""

    metadata: dict[str, str]
    sections: dict[str, str]


@dataclass(frozen=True)
class BridgeLiveness:
    """Reduced liveness signals derived from the transitional markdown bridge."""

    overall_state: str
    reviewer_mode: str
    codex_poll_state: str
    last_codex_poll_utc: str | None
    last_codex_poll_age_seconds: int | None
    last_reviewed_scope_present: bool
    next_action_present: bool
    open_findings_present: bool
    claude_status_present: bool
    claude_ack_present: bool
    claude_ack_current: bool
    current_instruction_revision: str = ""
    claude_ack_revision: str = ""
    reviewed_hash_current: bool | None = None
    implementer_completion_stall: bool = False
    reviewer_freshness: str = ""


@dataclass(frozen=True)
class HandoffBundle:
    """Repo-visible rollover handoff artifact locations."""

    bundle_dir: str
    markdown_path: str
    json_path: str
    generated_at: str
    rollover_id: str
    trigger: str
    threshold_pct: int


_CLAUDE_ACK_REVISION_RE = re.compile(
    r"(?i)\binstruction(?:[-_ ]rev(?:ision)?)?\s*:\s*`?(?P<value>[a-f0-9]{8,64})`?"
)


def extract_bridge_snapshot(bridge_text: str) -> BridgeSnapshot:
    """Parse tracked metadata and live sections from `bridge.md`."""
    metadata: dict[str, str] = {}
    for raw_line in bridge_text.splitlines():
        stripped = raw_line.strip()
        for key, pattern in BRIDGE_METADATA_PATTERNS.items():
            match = pattern.match(stripped)
            if match is not None:
                metadata[key] = match.group("value").strip()

    sections = extract_bridge_sections(bridge_text)

    tracked_sections = {
        name: sections[name]
        for name in TRACKED_BRIDGE_SECTIONS
        if sections.get(name, "").strip()
    }
    return BridgeSnapshot(metadata=metadata, sections=tracked_sections)


def summarize_bridge_liveness(
    snapshot: BridgeSnapshot,
    *,
    now_utc: datetime | None = None,
    codex_poll_due_after_seconds: int = DEFAULT_CODEX_POLL_DUE_AFTER_SECONDS,
    codex_poll_stale_after_seconds: int = DEFAULT_CODEX_POLL_STALE_AFTER_SECONDS,
    current_worktree_hash: str | None = None,
) -> BridgeLiveness:
    """Reduce current bridge state into a small machine-readable liveness summary."""
    current_instruction = snapshot.sections.get("Current Instruction For Claude", "").strip()
    open_findings = snapshot.sections.get("Open Findings", "").strip()
    last_reviewed_scope = snapshot.sections.get("Last Reviewed Scope", "").strip()
    claude_status = snapshot.sections.get("Claude Status", "").strip()
    claude_ack = snapshot.sections.get("Claude Ack", "").strip()
    reviewer_mode = normalize_reviewer_mode(snapshot.metadata.get("reviewer_mode"))
    last_codex_poll_utc = snapshot.metadata.get("last_codex_poll_utc")
    last_codex_poll_age_seconds = _timestamp_age_seconds(
        last_codex_poll_utc,
        now_utc=now_utc,
    )
    if last_codex_poll_age_seconds is None:
        codex_poll_state = CodexPollState.MISSING
    elif last_codex_poll_age_seconds > codex_poll_stale_after_seconds:
        codex_poll_state = CodexPollState.STALE
    elif last_codex_poll_age_seconds > codex_poll_due_after_seconds:
        codex_poll_state = CodexPollState.POLL_DUE
    else:
        codex_poll_state = CodexPollState.FRESH

    lowered_instruction = current_instruction.lower()
    next_action_present = bool(current_instruction) and not any(
        marker in lowered_instruction
        for marker in (*IDLE_NEXT_ACTION_MARKERS, *GENERIC_NEXT_ACTION_MARKERS)
    )
    last_reviewed_scope_present = bool(last_reviewed_scope)
    claude_status_present = _is_substantive_text(claude_status)
    claude_ack_present = _is_substantive_text(claude_ack)
    current_instruction_revision = (
        snapshot.metadata.get("current_instruction_revision") or ""
    ).strip()
    if not current_instruction_revision and current_instruction:
        current_instruction_revision = _instruction_revision(current_instruction)
    claude_ack_revision = _extract_claude_ack_revision(claude_ack)
    claude_ack_current = (
        claude_ack_present
        and (
            not current_instruction_revision
            or claude_ack_revision == current_instruction_revision
        )
    )

    if not reviewer_mode_is_active(reviewer_mode):
        overall_state = OverallLivenessState.INACTIVE
    elif codex_poll_state in {CodexPollState.MISSING, CodexPollState.STALE}:
        overall_state = OverallLivenessState.STALE
    elif not last_reviewed_scope_present or not next_action_present:
        overall_state = OverallLivenessState.WAITING_ON_PEER
    elif next_action_present and (not claude_status_present or not claude_ack_current):
        overall_state = OverallLivenessState.WAITING_ON_PEER
    else:
        overall_state = OverallLivenessState.FRESH

    reviewed_hash_current: bool | None = None
    if current_worktree_hash is not None:
        stored_hash = snapshot.metadata.get("last_non_audit_worktree_hash")
        reviewed_hash_current = (
            stored_hash is not None and stored_hash == current_worktree_hash
        )

    # Detect implementer completion-stall from bridge status/ack text
    combined_implementer = f"{claude_status}\n{claude_ack}".lower()
    implementer_stalled = (
        next_action_present
        and any(marker in combined_implementer for marker in IMPLEMENTER_STALL_MARKERS)
    )

    freshness = classify_reviewer_freshness(last_codex_poll_age_seconds)

    return BridgeLiveness(
        overall_state=overall_state,
        reviewer_mode=reviewer_mode,
        codex_poll_state=codex_poll_state,
        last_codex_poll_utc=last_codex_poll_utc,
        last_codex_poll_age_seconds=last_codex_poll_age_seconds,
        last_reviewed_scope_present=last_reviewed_scope_present,
        next_action_present=next_action_present,
        open_findings_present=bool(open_findings),
        claude_status_present=claude_status_present,
        claude_ack_present=claude_ack_present,
        claude_ack_current=claude_ack_current,
        current_instruction_revision=current_instruction_revision,
        claude_ack_revision=claude_ack_revision,
        reviewed_hash_current=reviewed_hash_current,
        implementer_completion_stall=implementer_stalled,
        reviewer_freshness=freshness,
    )


def _instruction_revision(text: str) -> str:
    normalized = text.strip()
    if not normalized:
        return ""
    return sha256(normalized.encode("utf-8")).hexdigest()[:12]


def _extract_claude_ack_revision(text: str) -> str:
    """Extract the latest Claude ACK revision from the Claude Ack section.

    Contract: the FIRST instruction-rev match is the current/latest ACK.
    Claude should rewrite the current ACK at the top of the section and keep
    stale historical instruction-rev lines out of the live bridge so the first
    regex match stays equal to the true current revision.
    """
    match = _CLAUDE_ACK_REVISION_RE.search(text or "")
    if match is None:
        return ""
    return match.group("value").lower()


def bridge_liveness_to_dict(liveness: BridgeLiveness) -> dict[str, object]:
    """Convert a bridge-liveness dataclass into report-friendly JSON."""
    return asdict(liveness)


def write_handoff_bundle(
    *,
    repo_root: Path,
    bridge_path: Path,
    review_channel_path: Path,
    output_root: Path,
    trigger: str,
    threshold_pct: int,
    lane_assignments: list[dict[str, str]] | None = None,
    current_worktree_hash: str | None = None,
) -> HandoffBundle:
    """Write markdown + JSON handoff artifacts and return their locations."""
    generated_at = utc_timestamp()
    rollover_id = f"rollover-{_safe_timestamp(generated_at)}"
    snapshot = extract_bridge_snapshot(bridge_path.read_text(encoding="utf-8"))
    bundle_dir = output_root / _safe_timestamp(generated_at)
    bundle_dir.mkdir(parents=True, exist_ok=True)
    resume_state = build_handoff_resume_state(
        snapshot,
        rollover_id=rollover_id,
        lane_assignments=lane_assignments,
    )

    payload = {
        "generated_at": generated_at,
        "rollover_id": rollover_id,
        "trigger": trigger,
        "threshold_pct": threshold_pct,
        "bridge_path": display_path(bridge_path, repo_root=repo_root),
        "review_channel_path": display_path(review_channel_path, repo_root=repo_root),
        "metadata": snapshot.metadata,
        "sections": snapshot.sections,
        "liveness": bridge_liveness_to_dict(
            summarize_bridge_liveness(
                snapshot, current_worktree_hash=current_worktree_hash
            )
        ),
        "resume_state": resume_state,
    }

    markdown_path = bundle_dir / "handoff.md"
    json_path = bundle_dir / "handoff.json"
    markdown_path.write_text(
        render_handoff_markdown(
            payload,
            expected_rollover_ack_line=expected_rollover_ack_line,
        ),
        encoding="utf-8",
    )
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    return HandoffBundle(
        bundle_dir=str(bundle_dir),
        markdown_path=str(markdown_path),
        json_path=str(json_path),
        generated_at=generated_at,
        rollover_id=rollover_id,
        trigger=trigger,
        threshold_pct=threshold_pct,
    )


def handoff_bundle_to_dict(bundle: HandoffBundle | None) -> dict[str, str] | None:
    """Convert a handoff bundle dataclass into a report-friendly dict."""
    if bundle is None:
        return None
    return asdict(bundle)


def build_handoff_resume_state(
    snapshot: BridgeSnapshot,
    *,
    rollover_id: str,
    lane_assignments: list[dict[str, str]] | None = None,
) -> dict[str, object]:
    """Reduce bridge + lane state into the minimum repo-visible handoff contract."""
    return {
        "current_blockers": _extract_markdown_items(
            snapshot.sections.get("Open Findings", "")
        ),
        "next_action": _first_markdown_item(
            snapshot.sections.get("Current Instruction For Claude", "")
        ),
        "reviewed_worktree_hash": snapshot.metadata.get("last_non_audit_worktree_hash"),
        "owned_lanes": _group_owned_lanes(lane_assignments or []),
        "current_atomic_step": _derive_current_atomic_step(snapshot),
        "launch_ack_state": {
            provider: {
                "required_line": expected_rollover_ack_line(
                    provider=provider,
                    rollover_id=rollover_id,
                ),
                "required_section": expected_rollover_ack_section(provider=provider),
                "observed": False,
                "role": str(role_for_provider(provider)),
            }
            for provider in ROLLOVER_ACK_PREFIX
        },
    }


def expected_rollover_ack_line(*, provider: str, rollover_id: str) -> str:
    """Return the exact bridge line a fresh conductor must write as an ACK."""
    try:
        prefix = ROLLOVER_ACK_PREFIX[provider]
    except KeyError as exc:
        raise ValueError(f"Unsupported rollover ACK provider: {provider}") from exc
    return f"- {prefix} `{rollover_id}`"


def expected_rollover_ack_section(*, provider: str) -> str:
    """Return the owned bridge section that must contain the rollover ACK."""
    try:
        return ROLLOVER_ACK_SECTION[provider]
    except KeyError as exc:
        raise ValueError(f"Unsupported rollover ACK provider: {provider}") from exc


def wait_for_rollover_ack(
    *,
    bridge_path: Path,
    rollover_id: str,
    timeout_seconds: int,
    poll_interval_seconds: float = 2.0,
) -> dict[str, bool]:
    """Wait for both fresh-conductor ACK lines or until the timeout expires."""
    deadline = time.monotonic() + max(timeout_seconds, 0)
    while True:
        observed = observe_rollover_ack_state(
            bridge_text=bridge_path.read_text(encoding="utf-8"),
            rollover_id=rollover_id,
        )
        if all(observed.values()) or time.monotonic() >= deadline:
            return observed
        time.sleep(max(poll_interval_seconds, 0.1))


def wait_for_codex_poll_refresh(
    *,
    bridge_path: Path,
    previous_poll_utc: str | None,
    timeout_seconds: int,
    poll_interval_seconds: float = 2.0,
) -> dict[str, object]:
    """Wait for a fresh Codex reviewer heartbeat after live launch."""
    deadline = time.monotonic() + max(timeout_seconds, 0)
    while True:
        snapshot = extract_bridge_snapshot(bridge_path.read_text(encoding="utf-8"))
        current_poll_utc = snapshot.metadata.get("last_codex_poll_utc")
        observed = _codex_poll_advanced(
            previous_poll_utc=previous_poll_utc,
            current_poll_utc=current_poll_utc,
        )
        if observed or time.monotonic() >= deadline:
            liveness = summarize_bridge_liveness(snapshot)
            return {
                "observed": observed,
                "last_codex_poll_utc": current_poll_utc,
                "codex_poll_state": liveness.codex_poll_state,
            }
        time.sleep(max(poll_interval_seconds, 0.1))



# Cluster 2 (bridge validation) extracted to bridge_validation.py;
# validate_live_bridge_contract and validate_launch_bridge_state imported above.


def _safe_timestamp(timestamp: str) -> str:
    return timestamp.replace("-", "").replace(":", "").replace(".", "").replace("+", "")


def observe_rollover_ack_state(
    *,
    bridge_text: str,
    rollover_id: str,
) -> dict[str, bool]:
    sections = extract_bridge_sections(bridge_text)
    return {
        provider: (
            _first_markdown_item(
                expected_rollover_ack_line(
                    provider=provider,
                    rollover_id=rollover_id,
                )
            )
            or expected_rollover_ack_line(
                provider=provider,
                rollover_id=rollover_id,
            )
        )
        in _extract_markdown_items(
            sections.get(expected_rollover_ack_section(provider=provider), "")
        )
        for provider in ROLLOVER_ACK_PREFIX
    }



# Cluster 1 (timestamp), Cluster 3 (markdown/lane) extracted to handoff_time.py
# and handoff_markdown.py; imported above for backward compatibility.
