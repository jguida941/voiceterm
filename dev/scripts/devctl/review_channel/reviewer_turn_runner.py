"""Controller-owned reviewer turn runner for the portable smart loop.

Provides the typed contract that enables a controller to execute one bounded
reviewer turn without chat relay. The turn runner is provider-agnostic:

  1. detect_reviewer_wake() — check inbox + tree hash for wake conditions
  2. build_reviewer_turn_context() — assemble typed input from repo-owned surfaces
  3. [provider executes bounded review — outside this module]
  4. apply_reviewer_turn_result() — route output through packet system

The actual review execution between steps 2-3 is delegated to the reviewer
provider (Codex, Claude, or any future agent). This module provides the
typed envelope, not the reviewer logic.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from ..runtime.role_profile import TandemRole, default_provider_for_role
from .pending_packet_storage import load_pending_packets
from .reviewer_worker import ReviewerWorkerTick, check_review_needed
from .turn_authority import ReviewerTurnAuthority

if TYPE_CHECKING:
    from ..runtime.project_governance_contract import ProjectGovernance


# ── Wake signal constants ──────────────────────────────────────

WAKE_PENDING_PACKET = "pending_packet"
WAKE_TREE_CHANGED = "tree_changed"
WAKE_SCHEDULED = "scheduled"
WAKE_OPERATOR_REQUEST = "operator_request"

# ── Turn status constants ──────────────────────────────────────

TURN_COMPLETED = "completed"
TURN_BLOCKED = "blocked"
TURN_ERROR = "error"
TURN_NO_ACTION = "no_action_needed"

NEXT_WAIT = "wait"
NEXT_CONTINUE = "continue"
NEXT_BLOCKED = "blocked"

PUBLICATION_IMPLEMENTER_OWNS = "implementer_owns"
PUBLICATION_REVIEWER_OWNS = "reviewer_owns"
PUBLICATION_BLOCKED = "blocked"


# ── Dataclass contracts ────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class ReviewerWakeSignal:
    """What triggered the need for a reviewer turn."""

    kind: str
    detail: str
    pending_packet_ids: tuple[str, ...] = ()
    tree_hash_before: str = ""
    tree_hash_after: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ReviewerTurnContext:
    """Everything a reviewer provider needs for one bounded turn.

    The controller builds this from repo-owned surfaces; the reviewer
    provider consumes it to decide what to review and what to emit.
    """

    wake_signal: ReviewerWakeSignal
    authority: ReviewerTurnAuthority
    pending_packets: tuple[dict, ...]
    repo_root: str
    reviewer_provider: str
    implementer_provider: str
    interaction_mode: str

    def to_dict(self) -> dict[str, object]:
        return {
            "wake_signal": self.wake_signal.to_dict(),
            "authority": self.authority.to_dict(),
            "pending_packet_count": len(self.pending_packets),
            "pending_packet_ids": [
                str(p.get("packet_id", "")) for p in self.pending_packets
            ],
            "repo_root": self.repo_root,
            "reviewer_provider": self.reviewer_provider,
            "implementer_provider": self.implementer_provider,
            "interaction_mode": self.interaction_mode,
        }


@dataclass(frozen=True, slots=True)
class ReviewerTurnResult:
    """Output of one bounded reviewer turn."""

    status: str
    emitted_packets: tuple[dict, ...] = ()
    publication_decision: str = ""
    publication_target_sha: str = ""
    next_state: str = NEXT_WAIT
    detail: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


# ── Wake detection ─────────────────────────────────────────────


def detect_reviewer_wake(
    *,
    repo_root: Path,
    bridge_path: Path | None = None,
    governance: ProjectGovernance | None = None,
    reviewer_provider: str = "",
    worker_tick: ReviewerWorkerTick | None = None,
) -> ReviewerWakeSignal | None:
    """Check for conditions that should wake the reviewer loop.

    Resolves ``bridge_path`` from ``governance.bridge_config.bridge_path``
    when governance is provided. Falls back to the direct parameter when
    governance is unavailable.

    Returns None when no wake is needed.
    """
    resolved_bridge = _resolve_bridge_path(
        repo_root=repo_root, bridge_path=bridge_path, governance=governance,
    )
    reviewer_name = (
        reviewer_provider or default_provider_for_role(TandemRole.REVIEWER)
    )
    pending = _pending_packets_for(
        repo_root=repo_root, agent_name=reviewer_name,
    )
    if pending:
        return ReviewerWakeSignal(
            kind=WAKE_PENDING_PACKET,
            detail=f"{len(pending)} pending packet(s) for {reviewer_name}",
            pending_packet_ids=tuple(
                str(p.get("packet_id", "")) for p in pending
            ),
        )
    if resolved_bridge is None:
        return None
    tick = worker_tick or check_review_needed(
        repo_root=repo_root, bridge_path=resolved_bridge,
    )
    if tick.review_needed:
        return ReviewerWakeSignal(
            kind=WAKE_TREE_CHANGED,
            detail=tick.detail,
            tree_hash_before=tick.reviewed_hash,
            tree_hash_after=tick.current_hash,
        )
    return None


# ── Context assembly ───────────────────────────────────────────


def build_reviewer_turn_context(
    *,
    wake_signal: ReviewerWakeSignal,
    authority: ReviewerTurnAuthority,
    repo_root: Path,
    governance: ProjectGovernance | None = None,
    interaction_mode: str = "",
    reviewer_provider: str = "",
    implementer_provider: str = "",
) -> ReviewerTurnContext | None:
    """Assemble typed turn context from repo-owned surfaces.

    When ``governance`` is provided, ``interaction_mode`` defaults to
    ``governance.bridge_config.operator_interaction_mode``.

    Returns None when authority says no reviewer turn is needed (unless
    the wake signal is an operator request, which overrides authority).
    """
    is_operator_override = wake_signal.kind == WAKE_OPERATOR_REQUEST
    if not authority.next_turn_required and not is_operator_override:
        return None
    if (
        authority.next_turn_role != TandemRole.REVIEWER.value
        and not is_operator_override
    ):
        return None

    resolved_reviewer = (
        reviewer_provider
        or default_provider_for_role(TandemRole.REVIEWER)
    )
    resolved_implementer = (
        implementer_provider
        or default_provider_for_role(TandemRole.IMPLEMENTER)
    )
    pending = _pending_packets_for(
        repo_root=repo_root, agent_name=resolved_reviewer,
    )
    return ReviewerTurnContext(
        wake_signal=wake_signal,
        authority=authority,
        pending_packets=tuple(pending),
        repo_root=str(repo_root),
        reviewer_provider=resolved_reviewer,
        implementer_provider=resolved_implementer,
        interaction_mode=(
            interaction_mode
            or (
                governance.bridge_config.operator_interaction_mode
                if governance is not None
                else ""
            )
            or "local_terminal"
        ),
    )


# ── Result validation ──────────────────────────────────────────

_VALID_STATUSES = frozenset({TURN_COMPLETED, TURN_BLOCKED, TURN_ERROR, TURN_NO_ACTION})
_VALID_NEXT_STATES = frozenset({NEXT_WAIT, NEXT_CONTINUE, NEXT_BLOCKED})
_VALID_PUBLICATION = frozenset({
    "", PUBLICATION_IMPLEMENTER_OWNS, PUBLICATION_REVIEWER_OWNS, PUBLICATION_BLOCKED,
})


def validate_turn_result(result: ReviewerTurnResult) -> list[str]:
    """Validate a turn result before applying it. Returns a list of errors."""
    errors: list[str] = []
    if result.status not in _VALID_STATUSES:
        errors.append(f"Unknown turn status: {result.status}")
    if result.next_state not in _VALID_NEXT_STATES:
        errors.append(f"Unknown next state: {result.next_state}")
    if result.publication_decision not in _VALID_PUBLICATION:
        errors.append(f"Unknown publication decision: {result.publication_decision}")
    for i, packet in enumerate(result.emitted_packets):
        if not isinstance(packet, dict):
            errors.append(f"Emitted packet {i} is not a dict")
            continue
        if not packet.get("kind"):
            errors.append(f"Emitted packet {i} missing 'kind'")
        if not packet.get("summary"):
            errors.append(f"Emitted packet {i} missing 'summary'")
    return errors


# ── Internal helpers ───────────────────────────────────────────


def _resolve_bridge_path(
    *,
    repo_root: Path,
    bridge_path: Path | None,
    governance: ProjectGovernance | None,
) -> Path | None:
    """Resolve bridge path from governance or direct parameter."""
    if governance is not None:
        rel = str(governance.bridge_config.bridge_path or "").strip()
        if rel:
            return (repo_root / rel).resolve()
    return bridge_path


def _pending_packets_for(
    *,
    repo_root: Path,
    agent_name: str,
) -> list[dict[str, object]]:
    """Load pending packets addressed to the given agent."""
    try:
        all_pending = load_pending_packets(repo_root)
    except (OSError, ValueError):
        return []

    result: list[dict[str, object]] = []
    for pkt in all_pending:
        if not isinstance(pkt, dict):
            continue
        to_agent = str(pkt.get("to_agent") or "").strip().lower()
        if to_agent != agent_name.lower():
            continue
        status = str(pkt.get("status") or "").strip()
        if status == "pending":
            result.append(pkt)
    return result
