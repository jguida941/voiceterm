"""Typed-action mutation adapter composing with the command-envelope classifier.

Phase 0.6.A v4.42 (rev_pkt_4714 / plan row
``MP-GUARDIR-V4-PHASE-0-6-A-COMMAND-ENVELOPE-NORMALIZATION-S1``) closes the
remaining v4.40 invariant: 3 consumers still classify mutation/executability
from TYPED ACTION IDENTIFIERS (e.g. ``vcs.commit``, ``run_devctl_push``,
``runtime.recover``) rather than free-form command text. The shared
``classify_command_mutation`` taxonomy only consumes command text; typed
action labels need a parallel lookup that returns the SAME
``(MutationActionKind, MutationRiskClass)`` tuple shape.

This module provides ``classify_typed_action`` — a leaf-safe adapter that
maps typed action identifiers to the shared mutation taxonomy. It imports
ONLY the Literal type aliases from ``command_envelope_classification``
(no runtime dependencies) so the coordination-lane import-isolation
invariant established in v4.41 is preserved.

Consumer surfaces wired in v4.42:
- ``dev/scripts/devctl/commands/development/final_response_gate_agent_loop.py``
- ``dev/scripts/devctl/runtime/control_decision_consistency.py``
- ``dev/scripts/devctl/runtime/action_routing.py``
"""

from __future__ import annotations

from .command_envelope_classification import MutationActionKind, MutationRiskClass
from .value_coercion import coerce_string

#: Typed action labels mapped to ``(MutationActionKind, MutationRiskClass)``.
#: Labels are matched after normalization (lower-case, hyphens / spaces /
#: dots → underscores) so callers can pass either form (``vcs.commit`` or
#: ``vcs_commit``) and get the same classification.
_TYPED_ACTION_KIND_MAP: dict[str, tuple[MutationActionKind, MutationRiskClass]] = {
    # action_routing.py _MUTATING_ACTIONS labels (dot form)
    "implementation_edit": ("implementation_edit", "governed_runtime_state"),
    "vcs_stage": ("git_add", "governed_repo_state"),
    "vcs_commit": ("devctl_commit", "governed_repo_state"),
    "vcs_push": ("devctl_push", "governed_repo_state"),
    "runtime_recover": ("runtime_recover", "governed_runtime_state"),
    "runtime_terminate": ("runtime_terminate", "governed_runtime_state"),
    # control_decision_consistency._mutation_next_action normalized identifiers
    "run_devctl_push": ("devctl_push", "governed_repo_state"),
    "run_devctl_commit": ("devctl_commit", "governed_repo_state"),
    "raw_git": ("raw_git_bypass", "bypass_surface"),
    "raw_git_commit": ("raw_git_bypass", "bypass_surface"),
    "git_push": ("git_push", "governed_repo_state"),
    "git_commit": ("git_commit", "governed_repo_state"),
}


def normalize_typed_action_label(value: object) -> str:
    """Normalize a typed action label to its canonical key form.

    Maps ``vcs.commit`` / ``vcs-commit`` / ``vcs commit`` → ``vcs_commit``.
    Returns ``""`` for None / empty input. Lower-cases and trims whitespace
    so callers don't have to.
    """
    text = coerce_string(value).strip().lower()
    if not text:
        return ""
    return text.replace(".", "_").replace("-", "_").replace(" ", "_")


def classify_typed_action(
    action_label: object,
) -> tuple[MutationActionKind, MutationRiskClass]:
    """Classify a typed action identifier into the shared mutation taxonomy.

    Returns ``(MutationActionKind, MutationRiskClass)`` matching the shape
    returned by ``classify_command_mutation`` for command text.

    For unrecognized labels, returns ``("none", "none")`` — the adapter is
    additive; callers that don't find a typed-action match can fall back
    to ``classify_command_mutation`` on the underlying command text.
    """
    normalized = normalize_typed_action_label(action_label)
    if not normalized:
        return ("none", "none")
    return _TYPED_ACTION_KIND_MAP.get(normalized, ("none", "none"))


def typed_action_is_mutation(action_label: object) -> bool:
    """Convenience predicate: True when the action label names a mutation.

    Equivalent to ``classify_typed_action(...)[1] != "none"``. Provided so
    consumers that need a boolean instead of the typed tuple can call this
    directly.
    """
    _, risk = classify_typed_action(action_label)
    return risk != "none"


__all__ = [
    "classify_typed_action",
    "normalize_typed_action_label",
    "typed_action_is_mutation",
]
