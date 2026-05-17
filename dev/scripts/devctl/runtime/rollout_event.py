"""Typed rollout event contract for Codex/Claude session JSONL traces.

Both Codex CLI and Claude Code persist append-only session traces to
``~/.codex/sessions/...`` and ``~/.claude/projects/...``. Those files
carry the full reasoning/tool-call history, including sandbox escalation
prompts and agent errors, which are otherwise invisible to operators on
a remote-control session.

``RolloutEvent`` is the portable typed projection that the
``rollout-tail`` command (and any future bridge projection surface)
reads from either provider's JSONL shape. It intentionally keeps the
raw payload attached so downstream renderers can surface richer detail
without re-parsing the source file.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


ROLLOUT_EVENT_CONTRACT_ID = "RolloutEvent"
ROLLOUT_EVENT_SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class RolloutEvent:
    """One parsed entry from a provider session JSONL trace."""

    timestamp: str
    provider: str
    session_id: str
    event_type: str
    raw_payload: dict[str, Any] = field(default_factory=dict)
    is_escalation_request: bool = False
    is_error: bool = False
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
