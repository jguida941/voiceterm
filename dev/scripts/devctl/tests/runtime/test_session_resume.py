"""Focused tests for typed Session Resume parsing."""

from __future__ import annotations

from dev.scripts.devctl.markdown_sections import parse_markdown_sections
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


def test_extract_session_resume_handles_bold_emphasis_labels() -> None:
    markdown = """# Plan

## Session Resume

- **Current goal:** Land slice X.
- _Next action:_ Run tests.
- *Status:* In progress.
- __Current status:__ Startup authority partially wired.
"""

    state = extract_session_resume_state(markdown)

    assert state is not None
    assert state.current_goal == "Land slice X."
    assert state.next_action == "Run tests."
    assert state.current_status == "Startup authority partially wired."
    # Bold-wrapped labels must resolve into real typed labels, not bleed
    # their emphasis tokens into the entry body.
    labels = {entry.label for entry in state.entries}
    assert "Current goal" in labels
    assert "Next action" in labels
    assert "Status" in labels
    assert "Current status" in labels
    for entry in state.entries:
        assert not entry.text.startswith("*")
        assert not entry.text.startswith("_")
        assert not entry.text.endswith("*")
        assert not entry.text.endswith("_")


def test_extract_session_resume_falls_back_to_subsection_label() -> None:
    markdown = """# Plan

## Session Resume

### Current goal

- Land the first startup intake packet.

### Next action

- Run bundle.tooling and inspect failures.
"""

    state = extract_session_resume_state(markdown)

    assert state is not None
    # No labeled bullet exists here; the subsection heading carries the
    # label and the first bullet under it must bind as the typed field.
    assert state.current_goal == "Land the first startup intake packet."
    assert state.next_action == "Run bundle.tooling and inspect failures."


def test_extract_session_resume_label_overrides_subsection() -> None:
    markdown = """# Plan

## Session Resume

### Current goal

- Subsection-only bullet content.
- Current goal: Label-bound bullet wins.
"""

    state = extract_session_resume_state(markdown)

    assert state is not None
    # Both a labeled bullet AND a matching subsection exist. The labeled
    # bullet must win — author intent beats inherited heading context.
    assert state.current_goal == "Label-bound bullet wins."


def test_parse_markdown_sections_concatenates_duplicate_headings() -> None:
    markdown = """# Plan

## Session Resume

- First block entry.

## Scope

Scope text.

## Session Resume

- Second block entry.
"""

    sections = parse_markdown_sections(markdown)

    # Duplicate `## Session Resume` headings must both survive instead of
    # silently last-wins. The concatenated body must contain content from
    # both blocks so downstream parsers see the full resume history.
    assert "First block entry." in sections["Session Resume"]
    assert "Second block entry." in sections["Session Resume"]


def test_extract_session_resume_finds_entries_from_duplicate_sections() -> None:
    markdown = """# Plan

## Session Resume

- Current goal: First-block goal.

## Scope

Scope text.

## Session Resume

- Next action: Second-block action.
"""

    state = extract_session_resume_state(markdown)

    assert state is not None
    # Both blocks contribute entries, not just the last-seen block.
    texts = [entry.text for entry in state.entries]
    assert "First-block goal." in texts
    assert "Second-block action." in texts
    # And the typed field pickers resolve across both blocks.
    assert state.current_goal == "First-block goal."
    assert state.next_action == "Second-block action."


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
