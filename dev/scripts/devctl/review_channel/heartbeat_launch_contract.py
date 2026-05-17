"""Launch-contract validation helpers for bridge heartbeat refreshes."""

from __future__ import annotations

from .bridge_validation import validate_launch_bridge_state

REFRESHABLE_LAUNCH_ERRORS = (
    "Missing `Last Codex poll`;",
    "Missing `Last Codex poll`",
    "`Last Codex poll` is stale;",
    "`Last Codex poll` is stale",
)


def is_refreshable_launch_error(error: str) -> bool:
    """Return whether a launch error is safe for heartbeat-only refresh."""
    stripped = error.strip()
    return any(stripped.startswith(prefix) for prefix in REFRESHABLE_LAUNCH_ERRORS)


def validate_refreshable_launch_contract(
    *,
    snapshot: object,
    liveness: object,
    allow_non_refreshable_launch_errors: bool,
) -> None:
    """Reject heartbeat refreshes when launch has non-heartbeat blockers."""
    launch_errors = validate_launch_bridge_state(snapshot, liveness=liveness)
    non_refreshable = [
        error for error in launch_errors if not is_refreshable_launch_error(error)
    ]
    if non_refreshable and not allow_non_refreshable_launch_errors:
        raise ValueError(
            "Bridge heartbeat refresh refused because the launch contract has "
            "other blockers: " + "; ".join(non_refreshable)
        )
