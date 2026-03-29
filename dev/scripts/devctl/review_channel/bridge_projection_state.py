"""Typed payload helpers for bridge-compatibility projection rebuilds."""

from __future__ import annotations

from collections.abc import Mapping
import hashlib
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from .bridge_section_validation import find_embedded_markdown_headings
from .bridge_sanitize import (
    BRIDGE_ALLOWED_H2,
    BRIDGE_SECTION_LINE_LIMITS,
    sanitize_bridge_sections,
)
from .handoff import extract_bridge_snapshot

BRIDGE_SECTION_ORDER = (
    "Poll Status",
    "Current Verdict",
    "Open Findings",
    "Claude Status",
    "Claude Questions",
    "Claude Ack",
    "Current Instruction For Claude",
    "Last Reviewed Scope",
)

_H2_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
_LOCAL_TZ = ZoneInfo("America/New_York")
_LOCAL_TIME_FORMAT = "%Y-%m-%d %H:%M:%S %Z"


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
) -> BridgeProjectionState:
    """Capture the typed bridge payload needed for a pure compatibility render."""
    snapshot = extract_bridge_snapshot(bridge_text)
    sections, sanitized_sections = sanitize_bridge_sections(
        _tracked_sections(snapshot.sections),
        section_line_limits=BRIDGE_SECTION_LINE_LIMITS,
    )
    _validate_flat_bridge_sections(sections)
    return BridgeProjectionState(
        metadata=_projection_metadata(
            snapshot=snapshot,
            bridge_liveness=bridge_liveness,
            sections=sections,
        ),
        sections=sections,
        lines_before=len(bridge_text.splitlines()),
        bytes_before=len(bridge_text.encode("utf-8")),
        dropped_headings=tuple(
            heading
            for heading in _ordered_unique(
                match.group(1).strip() for match in _H2_RE.finditer(bridge_text)
            )
            if heading not in BRIDGE_ALLOWED_H2
        ),
        sanitized_sections=tuple(sanitized_sections),
    )


def bridge_projection_state_from_review_state(
    review_state: Mapping[str, object],
) -> BridgeProjectionState:
    """Read the typed bridge render payload from `review_state.json`."""
    compat = _mapping(review_state.get("_compat"))
    projection = _mapping(compat.get("bridge_projection"))
    metadata = _string_mapping(projection.get("metadata"))
    sections = _string_mapping(projection.get("sections"))
    missing = [heading for heading in BRIDGE_SECTION_ORDER if heading not in sections]
    if missing:
        raise ValueError(
            "Typed bridge projection is missing fixed sections: "
            + ", ".join(f"`{heading}`" for heading in missing)
        )
    state = BridgeProjectionState(
        metadata=metadata,
        sections=sections,
        lines_before=_int_value(projection.get("lines_before")),
        bytes_before=_int_value(projection.get("bytes_before")),
        dropped_headings=_tuple_strings(projection.get("dropped_headings")),
        sanitized_sections=_tuple_strings(projection.get("sanitized_sections")),
    )
    _validate_flat_bridge_sections(state.sections)
    return state


def bridge_projection_metadata_lines(
    projection_state: BridgeProjectionState,
    *,
    last_worktree_hash: str,
) -> list[str]:
    """Render bridge metadata lines from typed projection state."""
    metadata = projection_state.metadata
    current_instruction = projection_state.sections["Current Instruction For Claude"]
    current_revision = metadata.get("current_instruction_revision", "").strip()
    if not current_revision and current_instruction.strip():
        current_revision = hashlib.sha256(
            current_instruction.strip().encode("utf-8")
        ).hexdigest()[:12]
    last_codex_poll_utc = metadata.get("last_codex_poll_utc", "").strip()
    last_codex_poll_local = metadata.get("last_codex_poll_local", "").strip()
    if not last_codex_poll_local and last_codex_poll_utc:
        last_codex_poll_local = _format_local_poll_time(last_codex_poll_utc)
    return [
        f"- Last Codex poll: `{last_codex_poll_utc}`",
        "- Last Codex poll (Local America/New_York): "
        f"`{last_codex_poll_local}`",
        f"- Reviewer mode: `{metadata.get('reviewer_mode', 'active_dual_agent')}`",
        f"- Last non-audit worktree hash: `{last_worktree_hash}`",
        f"- Current instruction revision: `{current_revision}`",
    ]


def _projection_metadata(
    *,
    snapshot,
    bridge_liveness: Mapping[str, object],
    sections: Mapping[str, str],
) -> dict[str, str]:
    current_instruction = str(sections.get("Current Instruction For Claude", "")).strip()
    current_revision = str(
        bridge_liveness.get("current_instruction_revision")
        or snapshot.metadata.get("current_instruction_revision")
        or ""
    ).strip()
    if not current_revision and current_instruction:
        current_revision = hashlib.sha256(
            current_instruction.encode("utf-8")
        ).hexdigest()[:12]
    last_codex_poll_utc = str(snapshot.metadata.get("last_codex_poll_utc") or "").strip()
    last_codex_poll_local = str(
        snapshot.metadata.get("last_codex_poll_local") or ""
    ).strip()
    if not last_codex_poll_local and last_codex_poll_utc:
        last_codex_poll_local = _format_local_poll_time(last_codex_poll_utc)
    return {
        "last_codex_poll_utc": last_codex_poll_utc,
        "last_codex_poll_local": last_codex_poll_local,
        "reviewer_mode": str(
            bridge_liveness.get("reviewer_mode")
            or snapshot.metadata.get("reviewer_mode")
            or "active_dual_agent"
        ).strip(),
        "current_instruction_revision": current_revision,
    }


def _tracked_sections(raw_sections: Mapping[str, str]) -> dict[str, str]:
    return {
        heading: str(raw_sections.get(heading, ""))
        for heading in BRIDGE_SECTION_ORDER
    }


def _validate_flat_bridge_sections(sections: Mapping[str, str]) -> None:
    errors: list[str] = []
    for heading in BRIDGE_SECTION_ORDER:
        heading_hits = find_embedded_markdown_headings(str(sections.get(heading, "")))
        if not heading_hits:
            continue
        quoted = "; ".join(f"`{line}`" for line in heading_hits)
        errors.append(f"`{heading}`: {quoted}")
    if errors:
        raise ValueError(
            "Typed bridge projection rejected embedded markdown headings in fixed "
            "sections: " + "; ".join(errors)
        )


def _format_local_poll_time(last_codex_poll_utc: str) -> str:
    try:
        parsed = datetime.strptime(
            last_codex_poll_utc,
            "%Y-%m-%dT%H:%M:%SZ",
        ).replace(tzinfo=timezone.utc)
    except ValueError:
        return ""
    return parsed.astimezone(_LOCAL_TZ).strftime(_LOCAL_TIME_FORMAT)


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _string_mapping(value: object) -> dict[str, str]:
    if not isinstance(value, Mapping):
        return {}
    return {str(key): str(item or "") for key, item in value.items()}


def _tuple_strings(value: object) -> tuple[str, ...]:
    if isinstance(value, (list, tuple)):
        return tuple(str(item) for item in value if str(item).strip())
    return ()


def _int_value(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _ordered_unique(values) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered
