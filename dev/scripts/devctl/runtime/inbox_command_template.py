"""Inbox-poll command template helpers.

Extracted from ``review_packet_inbox.py`` to keep that module under the
Python soft file-size limit (350 lines). Owns the
``--target``/``--actor`` template policy and the synthetic-target
exclusion list (codex finding rev_pkt_1779).
"""

from __future__ import annotations

import os
import sys


# Synthetic / non-poller targets (operator, system) must use the
# read-only inbox template: they aren't real conductor lanes with a
# live actor that can "observe" the packet, so stamping
# `delivery_observed_at_utc` as if they did would falsify the typed
# receipt contract.
#
# Use an exclusion list (rather than a whitelist of known providers)
# so any future implementer added through collaboration / registry /
# session metadata — beyond codex/claude/cursor — still gets the
# delivery-stamping template by default. Mirroring `packet_agents.py`
# admits arbitrary provider ids, and a whitelist here would silently
# break delivery stamping for those new lanes.
_NON_CONDUCTOR_AGENTS: frozenset[str] = frozenset({"operator", "system"})

# Match the launch.py / peer_recovery.py pattern: derive the interpreter
# from the currently-running Python so generated commands work under the
# same interpreter-selection the rest of the review-channel runtime
# uses. Hardcoding `python3` breaks on pyenv systems where that shim
# resolves to a stale interpreter (e.g., 3.10 without `datetime.UTC`).
_DEVCTL_INTERPRETER = os.path.basename(sys.executable) or "python3"

_INBOX_COMMAND_TEMPLATE = (
    f"{_DEVCTL_INTERPRETER} dev/scripts/devctl.py review-channel --action inbox "
    "--target {agent} --actor {agent} --status pending "
    "--terminal none --format md"
)
_OPERATOR_INBOX_COMMAND_TEMPLATE = (
    f"{_DEVCTL_INTERPRETER} dev/scripts/devctl.py review-channel --action inbox "
    "--target {agent} --status pending "
    "--terminal none --format md"
)


def inbox_command_for_agent(agent: str) -> str:
    """Render the inbox-poll command for one agent.

    Real conductor-backed agents — including any provider id admitted
    by ``packet_agents.py`` beyond the codex/claude/cursor defaults —
    get the delivery-stamping template with ``--actor``. Only the
    synthetic non-poller targets in ``_NON_CONDUCTOR_AGENTS``
    (``operator``, ``system``) fall back to the read-only template,
    so routine queue inspection doesn't falsely stamp delivery on
    live ``action_request`` packets.
    """
    template = (
        _OPERATOR_INBOX_COMMAND_TEMPLATE
        if str(agent or "").strip().lower() in _NON_CONDUCTOR_AGENTS
        else _INBOX_COMMAND_TEMPLATE
    )
    return template.format(agent=agent)
