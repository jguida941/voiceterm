"""Handoff helpers for the transitional review-channel launcher.

These helpers reduce the live markdown bridge into explicit handoff artifacts
so fresh conductor sessions can resume without relying on compaction summaries.

Governing docs for this slice:

- `AGENTS.md`
- `dev/active/MASTER_PLAN.md`
- `dev/active/review_channel.md`
- `dev/active/continuous_swarm.md`
- `code_audit.md`
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from .common import display_path
from .time_utils import utc_timestamp

BRIDGE_SECTION_RE = re.compile(r"^##\s+(?P<name>.+?)\s*$")
MARKDOWN_ITEM_RE = re.compile(r"^(?:[-*+]\s+|\d+\.\s+)(?P<value>.+)$")
BRIDGE_METADATA_PATTERNS = {
    "last_codex_poll_utc": re.compile(r"^- Last Codex poll:\s*`(?P<value>.+?)`\s*$"),
    "last_codex_poll_local": re.compile(
        r"^- Last Codex poll \(Local America/New_York\):\s*`(?P<value>.+?)`\s*$"
    ),
    "last_non_audit_worktree_hash": re.compile(
        r"^- Last non-audit worktree hash:\s*`(?P<value>.+?)`\s*$"
    ),
}
TRACKED_BRIDGE_SECTIONS = (
    "Poll Status",
    "Current Verdict",
    "Open Findings",
    "Current Instruction For Claude",
    "Claude Status",
    "Claude Questions",
    "Claude Ack",
    "Last Reviewed Scope",
)
ROLLOVER_ACK_PREFIX = {
    "codex": "Codex rollover ack:",
    "claude": "Claude rollover ack:",
}
ROLLOVER_ACK_SECTION = {
    "codex": "Poll Status",
    "claude": "Claude Ack",
}
BRIDGE_LIVENESS_KEYS = (
    "overall_state",
    "codex_poll_state",
    "last_codex_poll_utc",
    "last_codex_poll_age_seconds",
    "last_reviewed_scope_present",
    "next_action_present",
    "open_findings_present",
    "claude_status_present",
    "claude_ack_present",
)
DEFAULT_CODEX_POLL_DUE_AFTER_SECONDS = 180
DEFAULT_CODEX_POLL_STALE_AFTER_SECONDS = 300
IDLE_NEXT_ACTION_MARKERS = (
    "all green so far",
    "no next action",
    "n/a",
    "none recorded",
    "idle",
    "placeholder",
)
IDLE_FINDING_MARKERS = (
    "(none)",
    "none",
    "no blockers",
    "all clear",
    "all green",
    "resolved",
)
RESOLVED_VERDICT_MARKERS = (
    "accepted",
    "all green",
    "clean",
    "resolved",
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
    codex_poll_state: str
    last_codex_poll_utc: str | None
    last_codex_poll_age_seconds: int | None
    last_reviewed_scope_present: bool
    next_action_present: bool
    open_findings_present: bool
    claude_status_present: bool
    claude_ack_present: bool


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


def extract_bridge_snapshot(bridge_text: str) -> BridgeSnapshot:
    """Parse tracked metadata and live sections from `code_audit.md`."""
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
) -> BridgeLiveness:
    """Reduce current bridge state into a small machine-readable liveness summary."""
    current_instruction = snapshot.sections.get("Current Instruction For Claude", "").strip()
    open_findings = snapshot.sections.get("Open Findings", "").strip()
    last_reviewed_scope = snapshot.sections.get("Last Reviewed Scope", "").strip()
    claude_status = snapshot.sections.get("Claude Status", "").strip()
    claude_ack = snapshot.sections.get("Claude Ack", "").strip()
    last_codex_poll_utc = snapshot.metadata.get("last_codex_poll_utc")
    last_codex_poll_age_seconds = _timestamp_age_seconds(
        last_codex_poll_utc,
        now_utc=now_utc,
    )
    if last_codex_poll_age_seconds is None:
        codex_poll_state = "missing"
    elif last_codex_poll_age_seconds > codex_poll_stale_after_seconds:
        codex_poll_state = "stale"
    elif last_codex_poll_age_seconds > codex_poll_due_after_seconds:
        codex_poll_state = "poll_due"
    else:
        codex_poll_state = "fresh"

    next_action_present = bool(current_instruction)
    last_reviewed_scope_present = bool(last_reviewed_scope)
    claude_status_present = bool(claude_status)
    claude_ack_present = bool(claude_ack)

    if codex_poll_state in {"missing", "stale"}:
        overall_state = "stale"
    elif not last_reviewed_scope_present or not next_action_present:
        overall_state = "waiting_on_peer"
    elif next_action_present and (not claude_status_present or not claude_ack_present):
        overall_state = "waiting_on_peer"
    else:
        overall_state = "fresh"

    return BridgeLiveness(
        overall_state=overall_state,
        codex_poll_state=codex_poll_state,
        last_codex_poll_utc=last_codex_poll_utc,
        last_codex_poll_age_seconds=last_codex_poll_age_seconds,
        last_reviewed_scope_present=last_reviewed_scope_present,
        next_action_present=next_action_present,
        open_findings_present=bool(open_findings),
        claude_status_present=claude_status_present,
        claude_ack_present=claude_ack_present,
    )


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
        "liveness": bridge_liveness_to_dict(summarize_bridge_liveness(snapshot)),
        "resume_state": resume_state,
    }

    markdown_path = bundle_dir / "handoff.md"
    json_path = bundle_dir / "handoff.json"
    markdown_path.write_text(_render_handoff_markdown(payload), encoding="utf-8")
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
            }
            for provider in ("codex", "claude")
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


def validate_live_bridge_contract(snapshot: BridgeSnapshot) -> list[str]:
    """Return contract errors for the minimum live bridge state."""
    errors: list[str] = []
    last_reviewed_scope = snapshot.sections.get("Last Reviewed Scope", "").strip()
    if not last_reviewed_scope:
        errors.append(
            "Missing live `Last Reviewed Scope`; bridge-active coordination must "
            "keep the reviewed path set current."
        )

    current_instruction = snapshot.sections.get("Current Instruction For Claude", "").strip()
    if not current_instruction:
        errors.append(
            "Missing live next action in `Current Instruction For Claude`; the "
            "bridge must always expose the current coding queue."
        )
    elif any(marker in current_instruction.lower() for marker in IDLE_NEXT_ACTION_MARKERS):
        errors.append(
            "`Current Instruction For Claude` must point at the live next task, "
            "not an idle placeholder."
        )

    current_verdict = snapshot.sections.get("Current Verdict", "").strip().lower()
    open_findings = snapshot.sections.get("Open Findings", "").strip().lower()
    if (
        current_verdict
        and any(marker in current_verdict for marker in RESOLVED_VERDICT_MARKERS)
        and (
            not open_findings
            or any(marker in open_findings for marker in IDLE_FINDING_MARKERS)
        )
        and any(marker in current_instruction.lower() for marker in RESOLVED_VERDICT_MARKERS)
    ):
        errors.append(
            "Resolved bridge verdicts must promote the next scoped task in "
            "`Current Instruction For Claude` instead of echoing a completed state."
        )

    return errors


def validate_launch_bridge_state(
    snapshot: BridgeSnapshot,
    *,
    liveness: BridgeLiveness | None = None,
) -> list[str]:
    """Return launch-blocking bridge errors for fresh-conductor bootstrap."""
    errors = validate_live_bridge_contract(snapshot)
    effective_liveness = liveness or summarize_bridge_liveness(snapshot)
    if effective_liveness.codex_poll_state == "missing":
        errors.append(
            "Missing `Last Codex poll`; fresh launch requires a live reviewer poll "
            "timestamp in the bridge header."
        )
    elif effective_liveness.codex_poll_state == "stale":
        errors.append(
            "`Last Codex poll` is stale; fresh launch requires bridge activity "
            "within the five-minute heartbeat contract."
        )
    if not effective_liveness.claude_status_present:
        errors.append(
            "Missing live `Claude Status`; fresh launch requires the implementer "
            "status section before bootstrap."
        )
    if not effective_liveness.claude_ack_present:
        errors.append(
            "Missing live `Claude Ack`; fresh launch requires a current Claude "
            "ACK before bootstrap."
        )
    return errors


def extract_bridge_sections(bridge_text: str) -> dict[str, str]:
    """Parse all `##` bridge sections into a heading -> body map."""
    sections: dict[str, str] = {}
    current_name: str | None = None
    current_lines: list[str] = []
    for raw_line in bridge_text.splitlines():
        match = BRIDGE_SECTION_RE.match(raw_line.strip())
        if match is not None:
            _flush_section(sections, current_name, current_lines)
            current_name = match.group("name").strip()
            current_lines = []
            continue
        if current_name is not None:
            current_lines.append(raw_line.rstrip())
    _flush_section(sections, current_name, current_lines)
    return sections


def _flush_section(
    sections: dict[str, str],
    current_name: str | None,
    current_lines: list[str],
) -> None:
    if current_name is None:
        return
    sections[current_name] = "\n".join(current_lines).strip()
def _render_handoff_markdown(payload: dict[str, object]) -> str:
    lines = ["# Review Channel Handoff", ""]
    lines.append(f"- generated_at: {payload['generated_at']}")
    lines.append(f"- rollover_id: {payload['rollover_id']}")
    lines.append(f"- trigger: {payload['trigger']}")
    lines.append(f"- threshold_pct: {payload['threshold_pct']}")
    lines.append(f"- bridge_path: {payload['bridge_path']}")
    lines.append(f"- review_channel_path: {payload['review_channel_path']}")
    lines.append(
        "- required_codex_ack: "
        f"{expected_rollover_ack_line(provider='codex', rollover_id=str(payload['rollover_id']))}"
    )
    lines.append(
        "- required_claude_ack: "
        f"{expected_rollover_ack_line(provider='claude', rollover_id=str(payload['rollover_id']))}"
    )

    metadata = payload.get("metadata")
    if isinstance(metadata, dict) and metadata:
        lines.append("")
        lines.append("## Metadata")
        for key, value in metadata.items():
            lines.append(f"- {key}: {value}")

    liveness = payload.get("liveness")
    if isinstance(liveness, dict) and liveness:
        lines.append("")
        lines.append("## Liveness")
        for key in BRIDGE_LIVENESS_KEYS:
            lines.append(f"- {key}: {liveness.get(key)}")

    resume_state = payload.get("resume_state")
    if isinstance(resume_state, dict) and resume_state:
        lines.append("")
        lines.append("## Resume State")
        lines.append(f"- next_action: {resume_state.get('next_action') or 'n/a'}")
        lines.append(
            "- reviewed_worktree_hash: "
            f"{resume_state.get('reviewed_worktree_hash') or 'n/a'}"
        )
        lines.append(
            "- current_atomic_step: "
            f"{resume_state.get('current_atomic_step') or 'n/a'}"
        )

        current_blockers = resume_state.get("current_blockers")
        if isinstance(current_blockers, list):
            lines.append("")
            lines.append("### Current Blockers")
            if current_blockers:
                for blocker in current_blockers:
                    lines.append(f"- {blocker}")
            else:
                lines.append("- (none)")

        owned_lanes = resume_state.get("owned_lanes")
        if isinstance(owned_lanes, dict):
            lines.append("")
            lines.append("### Owned Lanes")
            for provider in ("codex", "claude"):
                provider_lanes = owned_lanes.get(provider, [])
                lines.append(f"- {provider}:")
                if isinstance(provider_lanes, list) and provider_lanes:
                    for lane in provider_lanes:
                        if not isinstance(lane, dict):
                            continue
                        lines.append(
                            "  - "
                            f"{lane.get('agent_id')} | {lane.get('lane')} | "
                            f"{lane.get('worktree')} | {lane.get('branch')} | "
                            f"{lane.get('mp_scope')}"
                        )
                else:
                    lines.append("  - (none)")

        launch_ack_state = resume_state.get("launch_ack_state")
        if isinstance(launch_ack_state, dict):
            lines.append("")
            lines.append("### Launch ACK State")
            for provider in ("codex", "claude"):
                ack_state = launch_ack_state.get(provider, {})
                if not isinstance(ack_state, dict):
                    continue
                status = "observed" if ack_state.get("observed") else "pending"
                lines.append(
                    f"- {provider}: {status} | {ack_state.get('required_section')} | "
                    f"{ack_state.get('required_line')}"
                )

    sections = payload.get("sections")
    if isinstance(sections, dict) and sections:
        for name, value in sections.items():
            lines.append("")
            lines.append(f"## {name}")
            lines.append(str(value).strip() or "(empty)")

    return "\n".join(lines)


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
        for provider in ("codex", "claude")
    }


def _group_owned_lanes(
    lane_assignments: list[dict[str, str]],
) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = {"codex": [], "claude": []}
    for lane in lane_assignments:
        provider = lane.get("provider", "").strip().lower()
        if provider not in grouped:
            continue
        grouped[provider].append(
            {
                "agent_id": _normalize_inline_markdown(lane.get("agent_id", "").strip()),
                "lane": _normalize_inline_markdown(lane.get("lane", "").strip()),
                "worktree": _normalize_inline_markdown(lane.get("worktree", "").strip()),
                "branch": _normalize_inline_markdown(lane.get("branch", "").strip()),
                "mp_scope": _normalize_inline_markdown(lane.get("mp_scope", "").strip()),
            }
        )
    return grouped


def _derive_current_atomic_step(snapshot: BridgeSnapshot) -> str | None:
    return (
        _first_markdown_item(snapshot.sections.get("Claude Status", ""))
        or _first_markdown_item(snapshot.sections.get("Current Instruction For Claude", ""))
        or _first_markdown_item(snapshot.sections.get("Last Reviewed Scope", ""))
    )


def _first_markdown_item(raw_text: str) -> str | None:
    items = _extract_markdown_items(raw_text)
    return items[0] if items else None


def _extract_markdown_items(raw_text: str) -> list[str]:
    items: list[str] = []
    for raw_line in raw_text.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue
        match = MARKDOWN_ITEM_RE.match(stripped)
        items.append(
            _normalize_inline_markdown(
                (match.group("value") if match is not None else stripped).strip()
            )
        )
    return items


def _normalize_inline_markdown(value: str) -> str:
    normalized = value.strip()
    wrappers = ("**", "__", "`")
    changed = True
    while normalized and changed:
        changed = False
        for wrapper in wrappers:
            if normalized.startswith(wrapper) and normalized.endswith(wrapper):
                normalized = normalized[len(wrapper) : -len(wrapper)].strip()
                changed = True
                break
    return normalized


def _timestamp_age_seconds(
    raw_value: str | None,
    *,
    now_utc: datetime | None,
) -> int | None:
    parsed = _parse_utc_z(raw_value)
    if parsed is None:
        return None
    current = now_utc or datetime.now(timezone.utc)
    age_seconds = int((current - parsed).total_seconds())
    return max(age_seconds, 0)


def _parse_utc_z(raw_value: str | None) -> datetime | None:
    if not raw_value:
        return None
    normalized = raw_value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)
