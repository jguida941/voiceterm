"""Role-aware projection for advisory next-command surfaces.

v4.40 (rev_pkt_4712): the local ``MUTATING_NEXT_COMMAND_MARKERS`` substring
registry was converged onto the shared ``classify_command_mutation``
taxonomy. The tuple is retained as a backwards-compatibility alias so
existing imports continue to work, but the canonical check
``command_requests_mutation`` now consults the shared classifier.
"""

from __future__ import annotations

from .command_envelope_classification import classify_command_mutation

READ_ONLY_NEXT_COMMAND = (
    "python3 dev/scripts/devctl.py review-channel --action status "
    "--terminal none --format json"
)
READ_ONLY_ADVISORY_ROLES = frozenset({"dashboard", "observer"})

#: v4.40: retained as a backwards-compat alias for imports that referenced
#: this tuple directly. New code MUST call ``command_requests_mutation``
#: (which delegates to the shared classifier). Updating this tuple alone
#: no longer affects behavior — the classifier owns the taxonomy.
MUTATING_NEXT_COMMAND_MARKERS = (
    " dev/scripts/devctl.py commit",
    " dev/scripts/devctl.py push",
    " dev/scripts/devctl.py pipeline --action",
    " dev/scripts/devctl.py review-channel --action ensure",
    " dev/scripts/devctl.py review-channel --action recover",
    " dev/scripts/devctl.py review-channel --action launch",
    " dev/scripts/devctl.py review-channel --action stop",
    " dev/scripts/devctl.py review-channel --action reset-implementer-state",
    " git add",
    " git commit",
    " git push",
)


def advisory_role_is_read_only(role: object) -> bool:
    """Return True when the caller role must not receive mutating commands."""
    return str(role or "").strip().lower() in READ_ONLY_ADVISORY_ROLES


def command_requests_mutation(command: object) -> bool:
    """Return True when a next-command string asks for a repo mutation.

    v4.40 (rev_pkt_4712): delegates to ``classify_command_mutation`` so the
    governed-mutation taxonomy stays in one place. Any non-``none`` risk
    class (worktree state, worktree writes, repo state, pipeline action,
    review-channel lifecycle, bypass surface) is treated as mutation.
    """
    text = str(command or "").strip()
    if not text:
        return False
    _, risk = classify_command_mutation(text)
    return risk != "none"


def project_next_command_for_role(*, role: object, command: object) -> str:
    """Return the role-visible next command for advisory read surfaces."""
    projected = str(command or "").strip()
    if advisory_role_is_read_only(role) and command_requests_mutation(projected):
        return READ_ONLY_NEXT_COMMAND
    return projected


__all__ = [
    "MUTATING_NEXT_COMMAND_MARKERS",
    "READ_ONLY_ADVISORY_ROLES",
    "READ_ONLY_NEXT_COMMAND",
    "advisory_role_is_read_only",
    "command_requests_mutation",
    "project_next_command_for_role",
]
