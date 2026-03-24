"""Focused tests for typed Session Resume parsing."""

from __future__ import annotations

from dev.scripts.devctl.runtime.session_resume import (
    extract_session_resume_state,
    session_resume_from_mapping,
)


def test_extract_session_resume_state_parses_labeled_entries() -> None:
    markdown = """# Plan

## Scope

Scope text.

## Session Resume

- Current status: Startup authority is partially wired.
- Current goal: Land the first startup intake packet.
- Next action: Run bundle.tooling and inspect failures.
"""

    state = extract_session_resume_state(markdown)

    assert state is not None
    assert state.current_status == "Startup authority is partially wired."
    assert state.current_goal == "Land the first startup intake packet."
    assert state.next_action == "Run bundle.tooling and inspect failures."
    assert state.summary == "Land the first startup intake packet."
    assert len(state.entries) == 3


def test_extract_session_resume_state_keeps_subsection_context() -> None:
    markdown = """# Plan

## Session Resume

### Current status

- 2026-03-23 follow-up: Keep startup-context authoritative.
- Current goal: Replace boolean-only continuity detection.
"""

    state = extract_session_resume_state(markdown)

    assert state is not None
    assert state.entries[0].subsection == "Current status"
    assert state.entries[0].date_hint == "2026-03-23"
    assert state.current_goal == "Replace boolean-only continuity detection."


def test_session_resume_from_mapping_roundtrips_entries() -> None:
    payload = {
        "section_hash": "resume1234",
        "summary": "Continue the authority loop slice.",
        "current_status": "",
        "current_goal": "Land the first startup intake packet.",
        "next_action": "Run bundle.tooling and inspect failures.",
        "entries": [
            {
                "text": "Land the first startup intake packet.",
                "item_kind": "bullet",
                "subsection": "",
                "label": "Current goal",
                "date_hint": "",
            }
        ],
    }

    state = session_resume_from_mapping(payload)

    assert state is not None
    assert state.to_dict() == payload
