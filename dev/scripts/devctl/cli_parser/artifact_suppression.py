"""Artifact-write suppression policy for read-only devctl commands."""

from __future__ import annotations

import os
from collections.abc import Callable, Collection
from typing import Any


# Environment variable checked by command handlers and artifact writers to
# suppress incidental filesystem writes (receipts, snapshots) that would
# otherwise make "read-only" commands fail on read-only mounts. Set
# automatically for READ_ONLY_COMMANDS; can also be set externally by MCP
# adapters or container orchestration.
ARTIFACT_WRITES_ENV = "DEVCTL_NO_ARTIFACT_WRITES"
_CONTEXT_GRAPH_BOOTSTRAP_MODE = "bootstrap"
_REVIEW_CHANNEL_READ_ONLY_ACTIONS = frozenset(
    {
        "status",
        "doctor",
        "watch",
        "inbox",
        "operator-inbox",
        "sync-status",
        "history",
        "show",
        "bridge-poll",
        "render-bridge",
    }
)


def artifact_writes_suppressed() -> bool:
    """True when incidental artifact writes should be skipped."""
    return os.environ.get(ARTIFACT_WRITES_ENV, "") == "1"


def read_only_command_suppresses_artifact_writes(
    args: Any,
    read_only_commands: Collection[str],
) -> bool:
    """Return whether the dispatcher should set artifact-write suppression."""
    if args.command not in read_only_commands:
        return False

    override = _ARTIFACT_SUPPRESSION_OVERRIDES.get(args.command)
    if override is None:
        return True

    return override(args)


def _develop_suppresses_artifact_writes(args: Any) -> bool:
    action = str(
        getattr(args, "action_flag", None)
        or getattr(args, "action", None)
        or "status"
    )
    if action == "ingest-plan":
        return False
    return not bool(getattr(args, "drain_packets", False))


def _context_graph_suppresses_artifact_writes(args: Any) -> bool:
    return getattr(args, "mode", "") != _CONTEXT_GRAPH_BOOTSTRAP_MODE


def _review_channel_suppresses_artifact_writes(args: Any) -> bool:
    action = str(getattr(args, "action", "") or "")
    return action in _REVIEW_CHANNEL_READ_ONLY_ACTIONS


_ARTIFACT_SUPPRESSION_OVERRIDES: dict[str, Callable[[Any], bool]] = {
    "develop": _develop_suppresses_artifact_writes,
    "context-graph": _context_graph_suppresses_artifact_writes,
    "review-channel": _review_channel_suppresses_artifact_writes,
}


__all__ = [
    "ARTIFACT_WRITES_ENV",
    "artifact_writes_suppressed",
    "read_only_command_suppresses_artifact_writes",
]
