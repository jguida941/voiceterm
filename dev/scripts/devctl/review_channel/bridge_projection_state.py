"""Typed payload helpers for bridge-compatibility projection rebuilds."""

from __future__ import annotations

from collections.abc import Mapping
import hashlib
from dataclasses import asdict, dataclass

from .bridge_projection_contract import BRIDGE_SECTION_ORDER
from .bridge_projection_instruction import (
    is_placeholder_instruction as _is_placeholder_instruction,
)
from .bridge_projection_metadata import (
    format_local_poll_time as _format_local_poll_time,
    projection_metadata as _projection_metadata,
)
from .bridge_projection_sections import (
    int_value as _int_value,
    mapping as _mapping,
    string_mapping as _string_mapping,
    tuple_strings as _tuple_strings,
    with_fallback_sections as _with_fallback_sections,
)
from .bridge_projection_validation import (
    bridge_projection_drop_headings,
    bridge_projection_parts,
    validate_flat_bridge_sections as _validate_flat_bridge_sections,
)
from .bridge_validation_poll_status import poll_status_is_automation_only_refresh
from .handoff import BridgeSnapshot, extract_bridge_snapshot
from .pending_packets import live_pending_packets

@dataclass(frozen=True)
class BridgeProjectionState:
    """Typed bridge-section payload used to rebuild the compatibility projection."""

    metadata: dict[str, str]
    sections: dict[str, str]
    lines_before: int
    bytes_before: int
    dropped_headings: tuple[str, ...]
    sanitized_sections: tuple[str, ...]


def bridge_projection_state_to_dict(
    state: BridgeProjectionState | None,
) -> dict[str, object] | None:
    if state is None:
        return None
    return asdict(state)


def build_bridge_projection_state(
    *,
    bridge_text: str,
    bridge_liveness: Mapping[str, object],
    current_session: Mapping[str, object] | None = None,
    reviewer_runtime: Mapping[str, object] | None = None,
    bridge_state: Mapping[str, object] | None = None,
    packets: list[dict[str, object]] | None = None,
) -> BridgeProjectionState:
    """Capture the typed bridge payload needed for a pure compatibility render."""
    snapshot = extract_bridge_snapshot(bridge_text)
    sections, sanitized_sections = bridge_projection_parts(
        raw_sections=snapshot.sections,
        current_session=_mapping(current_session),
        reviewer_runtime=_mapping(reviewer_runtime),
        packets=packets,
    )
    if poll_status_is_automation_only_refresh(snapshot.sections.get("Poll Status", "")):
        sections["Poll Status"] = ""
    return BridgeProjectionState(
        metadata=_projection_metadata(
            snapshot=snapshot,
            bridge_liveness=bridge_liveness,
            sections=sections,
            current_session=_mapping(current_session),
            bridge_state=_mapping(bridge_state),
        ),
        sections=sections,
        lines_before=len(bridge_text.splitlines()),
        bytes_before=len(bridge_text.encode("utf-8")),
        dropped_headings=bridge_projection_drop_headings(bridge_text),
        sanitized_sections=tuple(sanitized_sections),
    )


def bridge_projection_state_from_review_state(
    review_state: Mapping[str, object],
) -> BridgeProjectionState:
    """Read the typed bridge render payload from `review_state.json`."""
    review_state = _review_state_payload(review_state)
    compat = _mapping(review_state.get("_compat"))
    projection = _mapping(compat.get("bridge_projection"))
    metadata = _string_mapping(projection.get("metadata"))
    sections = _string_mapping(projection.get("sections"))
    current_session = _mapping(review_state.get("current_session"))
    reviewer_runtime = _mapping(review_state.get("reviewer_runtime"))
    bridge_state = _mapping(review_state.get("bridge"))
    packets = review_state.get("packets")
    live_packets = list(live_pending_packets(packets)) if isinstance(packets, list) else None
    sections, sanitized_sections = bridge_projection_parts(
        raw_sections=sections,
        current_session=current_session,
        reviewer_runtime=reviewer_runtime,
        packets=live_packets,
    )
    sections = _with_fallback_sections(review_state, sections)
    for heading in BRIDGE_SECTION_ORDER:
        sections.setdefault(heading, "")
    metadata = _projection_metadata(
        snapshot=BridgeSnapshot(metadata=metadata, sections=sections),
        bridge_liveness=bridge_state,
        sections=sections,
        current_session=current_session,
        bridge_state=bridge_state,
    )
    state = BridgeProjectionState(
        metadata=metadata,
        sections=sections,
        lines_before=_int_value(projection.get("lines_before")),
        bytes_before=_int_value(projection.get("bytes_before")),
        dropped_headings=_tuple_strings(projection.get("dropped_headings")),
        sanitized_sections=tuple(
            dict.fromkeys(
                (
                    *_tuple_strings(projection.get("sanitized_sections")),
                    *sanitized_sections,
                )
            )
        ),
    )
    _validate_flat_bridge_sections(state.sections)
    return state


def _review_state_payload(
    review_state: Mapping[str, object],
) -> Mapping[str, object]:
    nested = review_state.get("review_state")
    return nested if isinstance(nested, Mapping) else review_state


def bridge_projection_metadata_lines(
    projection_state: BridgeProjectionState,
    *,
    last_worktree_hash: str,
) -> list[str]:
    """Render bridge metadata lines from typed projection state."""
    metadata = projection_state.metadata
    current_instruction = projection_state.sections["Current Instruction For Claude"]
    current_revision = metadata.get("current_instruction_revision", "").strip()
    typed_instruction_cleared = (
        metadata.get("current_instruction_explicitly_cleared", "").strip().lower()
        == "true"
    )
    if (
        not typed_instruction_cleared
        and not current_revision
        and current_instruction.strip()
        and not _is_placeholder_instruction(current_instruction)
    ):
        current_revision = hashlib.sha256(
            current_instruction.strip().encode("utf-8")
        ).hexdigest()[:12]
    last_codex_poll_utc = metadata.get("last_codex_poll_utc", "").strip()
    last_codex_poll_local = metadata.get("last_codex_poll_local", "").strip()
    if not last_codex_poll_local and last_codex_poll_utc:
        last_codex_poll_local = _format_local_poll_time(last_codex_poll_utc)
    from ..repo_packs import active_path_config

    tz_label = active_path_config().display_timezone
    reviewer_mode = metadata.get("reviewer_mode", "tools_only")
    lines = [
        f"- Last Codex poll: `{last_codex_poll_utc}`",
        f"- Last Codex poll (Local {tz_label}): "
        f"`{last_codex_poll_local}`",
        f"- Reviewer mode: `{reviewer_mode}`",
        f"- Last non-audit worktree hash: `{last_worktree_hash}`",
        f"- Current instruction revision: `{current_revision}`",
    ]
    declared_mode = metadata.get("declared_reviewer_mode", "").strip()
    if declared_mode and declared_mode != reviewer_mode:
        lines.insert(3, f"- Declared reviewer mode: `{declared_mode}`")
    return lines
