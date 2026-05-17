"""Canonical terminal lifecycle states for packet/exception consumers.

Single source of truth for "is this packet/lifecycle row in a terminal state
that consumers should ignore for active-attention selection?".

Prior to this module the predicate was duplicated across four review_channel
modules (active_packet_authority, agent_work_board_packets,
agent_packet_attention_scope, agent_sync_packet_classification). Three
composed the set from ``agent_sync_models.TERMINAL_NON_SUCCESS_STATES |
TERMINAL_SUCCESS_STATES``; one hard-coded the literal frozenset. None
recognized the two new terminal states emitted by the R297-#175 FOURTH LEG
``GovernedTransitionTypeChecker`` (``closed_via_commit_anchor`` and
``closed_via_bypass_expiry``), which is a typed-state-lies-at-consumer-cursor
defect (memory READ FIRST x 10): the typed substrate emits the state but the
consumer cursors don't ingest it.

composes_with:

- ``review_channel.agent_sync_models.TERMINAL_NON_SUCCESS_STATES`` /
  ``TERMINAL_SUCCESS_STATES`` — packet-disposition terminal semantics.
- ``runtime.governed_transition_typechecker`` — emits
  ``closed_via_commit_anchor`` and ``closed_via_bypass_expiry`` for
  governed-exception transitions backed by typed closure proof.
- ``runtime.raw_git_bypass_lifecycle_closure.RAW_GIT_COMMIT_ANCHOR_STATUS``
  — concrete writer of ``closed_via_commit_anchor``.
"""

from __future__ import annotations

from .agent_sync_models import (
    TERMINAL_NON_SUCCESS_STATES,
    TERMINAL_SUCCESS_STATES,
)

CONTRACT_ID: str = "PacketTerminalLifecycleStates"
SCHEMA_VERSION: int = 1

# Governed-transition typechecker (R297-#175 FOURTH LEG) terminal states.
# Emitted by ``runtime.governed_transition_typechecker`` when a transition is
# validated by typed closure proof:
#   - ``closed_via_commit_anchor``  -> CommitAnchorClosureProof
#   - ``closed_via_bypass_expiry``  -> BypassExpiryReceipt
GOVERNED_TRANSITION_TERMINAL_STATES: frozenset[str] = frozenset(
    {
        "closed_via_commit_anchor",
        "closed_via_bypass_expiry",
    }
)

TERMINAL_LIFECYCLE_STATES: frozenset[str] = (
    TERMINAL_NON_SUCCESS_STATES
    | TERMINAL_SUCCESS_STATES
    | GOVERNED_TRANSITION_TERMINAL_STATES
)


def is_terminal_lifecycle(state: str) -> bool:
    """Return True iff ``state`` is a recognized terminal lifecycle state.

    Empty strings and unknown values are never terminal (treated as live or
    pending so consumers preserve the row for downstream classification).
    """
    if not isinstance(state, str):
        return False
    return state in TERMINAL_LIFECYCLE_STATES


__all__ = [
    "CONTRACT_ID",
    "SCHEMA_VERSION",
    "GOVERNED_TRANSITION_TERMINAL_STATES",
    "TERMINAL_LIFECYCLE_STATES",
    "is_terminal_lifecycle",
]
