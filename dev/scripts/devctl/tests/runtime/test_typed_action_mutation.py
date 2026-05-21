"""Phase 0.6.A v4.42 (rev_pkt_4714) — typed-action mutation adapter tests.

Plan row: MP-GUARDIR-V4-PHASE-0-6-A-COMMAND-ENVELOPE-NORMALIZATION-S1.
Plan revision: guardir-v4.42-2026-05-20.

The adapter ``classify_typed_action`` composes with
``classify_command_mutation`` by returning the SAME
``(MutationActionKind, MutationRiskClass)`` tuple shape for typed action
identifiers (e.g. ``vcs.commit``, ``run_devctl_push``).

Tests cover:
- Identifier normalization (dots → underscores, etc.)
- Mapping coverage for codex's 3 named consumer registries
- Consumer convergence: action_routing._MUTATING_ACTIONS, control_decision_consistency._mutation_next_action
- Codex's verbatim Finding 1 + Finding 2 regression reproductions
"""

from __future__ import annotations

from dev.scripts.devctl.runtime.typed_action_mutation import (
    classify_typed_action,
    normalize_typed_action_label,
    typed_action_is_mutation,
)


# ---------------------------------------------------------------------------
# Label normalization
# ---------------------------------------------------------------------------


def test_normalize_dot_form() -> None:
    """v4.42: ``vcs.commit`` (dot form) → ``vcs_commit`` (underscore form)."""
    assert normalize_typed_action_label("vcs.commit") == "vcs_commit"


def test_normalize_hyphen_form() -> None:
    assert normalize_typed_action_label("vcs-commit") == "vcs_commit"


def test_normalize_space_form() -> None:
    assert normalize_typed_action_label("vcs commit") == "vcs_commit"


def test_normalize_already_normalized() -> None:
    assert normalize_typed_action_label("vcs_commit") == "vcs_commit"


def test_normalize_uppercase_lowercased() -> None:
    assert normalize_typed_action_label("VCS.Commit") == "vcs_commit"


def test_normalize_empty_returns_empty() -> None:
    assert normalize_typed_action_label("") == ""
    assert normalize_typed_action_label(None) == ""
    assert normalize_typed_action_label("   ") == ""


# ---------------------------------------------------------------------------
# action_routing typed labels (Finding 3 surface)
# ---------------------------------------------------------------------------


def test_action_routing_vcs_commit_classified() -> None:
    """v4.42: ``vcs.commit`` action label maps to governed_repo_state."""
    kind, risk = classify_typed_action("vcs.commit")
    assert kind == "devctl_commit"
    assert risk == "governed_repo_state"


def test_action_routing_vcs_push_classified() -> None:
    kind, risk = classify_typed_action("vcs.push")
    assert kind == "devctl_push"
    assert risk == "governed_repo_state"


def test_action_routing_vcs_stage_classified() -> None:
    kind, risk = classify_typed_action("vcs.stage")
    assert kind == "git_add"
    assert risk == "governed_repo_state"


def test_action_routing_implementation_edit_classified() -> None:
    """v4.42: ``implementation.edit`` is governed_runtime_state (source-tree
    mutation through the implementation lane)."""
    kind, risk = classify_typed_action("implementation.edit")
    assert kind == "implementation_edit"
    assert risk == "governed_runtime_state"


def test_action_routing_runtime_recover_classified() -> None:
    kind, risk = classify_typed_action("runtime.recover")
    assert kind == "runtime_recover"
    assert risk == "governed_runtime_state"


def test_action_routing_runtime_terminate_classified() -> None:
    kind, risk = classify_typed_action("runtime.terminate")
    assert kind == "runtime_terminate"
    assert risk == "governed_runtime_state"


# ---------------------------------------------------------------------------
# control_decision_consistency normalized identifiers (Finding 2 surface)
# ---------------------------------------------------------------------------


def test_consistency_run_devctl_push_classified() -> None:
    kind, risk = classify_typed_action("run_devctl_push")
    assert kind == "devctl_push"
    assert risk == "governed_repo_state"


def test_consistency_run_devctl_commit_classified() -> None:
    kind, risk = classify_typed_action("run_devctl_commit")
    assert kind == "devctl_commit"
    assert risk == "governed_repo_state"


def test_consistency_raw_git_classified() -> None:
    kind, risk = classify_typed_action("raw_git")
    assert kind == "raw_git_bypass"
    assert risk == "bypass_surface"


def test_consistency_raw_git_commit_classified() -> None:
    kind, risk = classify_typed_action("raw_git_commit")
    assert kind == "raw_git_bypass"
    assert risk == "bypass_surface"


def test_consistency_git_push_typed_classified() -> None:
    kind, risk = classify_typed_action("git_push")
    assert kind == "git_push"
    assert risk == "governed_repo_state"


def test_consistency_git_commit_typed_classified() -> None:
    kind, risk = classify_typed_action("git_commit")
    assert kind == "git_commit"
    assert risk == "governed_repo_state"


# ---------------------------------------------------------------------------
# Negative coverage
# ---------------------------------------------------------------------------


def test_unrecognized_typed_action_returns_none() -> None:
    """v4.42: an unrecognized typed action returns (none, none) so callers
    can fall through to command-text classification or report no mutation."""
    kind, risk = classify_typed_action("totally_unknown_action")
    assert kind == "none"
    assert risk == "none"


def test_empty_typed_action_returns_none() -> None:
    assert classify_typed_action("") == ("none", "none")
    assert classify_typed_action(None) == ("none", "none")


def test_read_only_action_returns_none() -> None:
    """v4.42 negative: read-only action labels (e.g. ``startup-context``)
    must NOT classify as mutation."""
    assert classify_typed_action("startup-context") == ("none", "none")
    assert classify_typed_action("review-channel.status") == ("none", "none")


def test_typed_action_is_mutation_predicate() -> None:
    assert typed_action_is_mutation("vcs.commit") is True
    assert typed_action_is_mutation("startup-context") is False
    assert typed_action_is_mutation("") is False


# ---------------------------------------------------------------------------
# Convergence drift guard — action_routing._MUTATING_ACTIONS membership
# ---------------------------------------------------------------------------


def test_action_routing_mutating_actions_all_classify() -> None:
    """v4.42 convergence drift guard: every member of action_routing's
    ``_MUTATING_ACTIONS`` tuple MUST be recognized by the typed-action
    adapter. If a new entry is added to ``_MUTATING_ACTIONS`` without a
    corresponding mapping in ``typed_action_mutation``, this test fails."""
    from dev.scripts.devctl.runtime.action_routing import _MUTATING_ACTIONS
    for action in _MUTATING_ACTIONS:
        kind, risk = classify_typed_action(action)
        assert risk != "none", (
            f"action_routing._MUTATING_ACTIONS member {action!r} is not "
            f"recognized by typed_action_mutation.classify_typed_action. "
            f"Add a mapping to runtime/typed_action_mutation.py."
        )


# ---------------------------------------------------------------------------
# Codex's verbatim Finding 1 regression (final_response_gate_agent_loop)
# ---------------------------------------------------------------------------


def test_v4_42_finding_1_is_executable_next_command_rejects_push() -> None:
    """v4.42 (rev_pkt_4714 Finding 1 verbatim regression): codex caught
    ``is_executable_next_command(...)`` returning True for
    ``python3 dev/scripts/devctl.py push --execute``. The function MUST
    return False now — even though ``push`` is in the devctl family,
    it's a governed_repo_state mutation."""
    from dev.scripts.devctl.commands.development.final_response_gate_agent_loop import (
        is_executable_next_command,
    )
    assert is_executable_next_command(
        "python3 dev/scripts/devctl.py push --execute"
    ) is False


def test_v4_42_finding_1_is_executable_allows_read_only_devctl() -> None:
    """v4.42: read-only devctl commands MUST still be executable (e.g.
    ``review-channel --action status`` from the gate's repair flow)."""
    from dev.scripts.devctl.commands.development.final_response_gate_agent_loop import (
        is_executable_next_command,
    )
    assert is_executable_next_command(
        "python3 dev/scripts/devctl.py review-channel --action status --format json"
    ) is True
    assert is_executable_next_command(
        "python3 dev/scripts/devctl.py session --role reviewer --format json"
    ) is True


def test_v4_42_finding_1_is_executable_rejects_git_clean() -> None:
    """v4.42: also test git clean / stash / reset — they're not devctl-family
    so they were always False, but v4.42 makes the rationale 'is_governed_mutation'
    not 'not_devctl_family'."""
    from dev.scripts.devctl.commands.development.final_response_gate_agent_loop import (
        is_executable_next_command,
    )
    # These are not devctl-family, so they return False even pre-v4.42
    assert is_executable_next_command("git clean -fdx") is False
    assert is_executable_next_command("git stash --include-untracked") is False


def test_v4_42_finding_1_is_executable_rejects_devctl_pipeline_action() -> None:
    """v4.42: ``devctl pipeline --action begin`` is governed_pipeline_action;
    must not be executable."""
    from dev.scripts.devctl.commands.development.final_response_gate_agent_loop import (
        is_executable_next_command,
    )
    assert is_executable_next_command(
        "python3 dev/scripts/devctl.py pipeline --action begin"
    ) is False


# ---------------------------------------------------------------------------
# Codex's verbatim Finding 2 regression (control_decision_consistency)
# ---------------------------------------------------------------------------


def test_v4_42_finding_2_blank_next_action_with_destructive_command() -> None:
    """v4.42 (rev_pkt_4714 Finding 2 verbatim regression): codex caught
    consistency_violations() returning [] for a decision with
    ``may_mutate=false, next_command='git clean -fdx', can_run_next_command=true,
    next_action=''``. The new ``_mutation_next_command`` helper closes the
    gap — there MUST be a violation now."""
    from dev.scripts.devctl.runtime.control_decision_consistency import (
        control_decision_violations,
    )
    decision = {
        "may_mutate": False,
        "next_command": "git clean -fdx",
        "can_run_next_command": True,
        "next_action": "",
    }
    violations = control_decision_violations(decision)
    assert len(violations) >= 1
    reasons = {v.reason for v in violations}
    assert "mutation_command_projected_while_mutation_blocked" in reasons


def test_v4_42_finding_2_blank_action_with_safe_command_no_violation() -> None:
    """v4.42 negative: blank next_action with a SAFE next_command produces
    no mutation-related violation."""
    from dev.scripts.devctl.runtime.control_decision_consistency import (
        control_decision_violations,
    )
    decision = {
        "may_mutate": False,
        "next_command": "python3 dev/scripts/devctl.py review-channel --action status",
        "can_run_next_command": True,
        "next_action": "",
    }
    violations = control_decision_violations(decision)
    reasons = {v.reason for v in violations}
    assert "mutation_command_projected_while_mutation_blocked" not in reasons


def test_v4_42_finding_2_both_action_and_command_only_emits_one_violation() -> None:
    """v4.42: when BOTH next_action and next_command name a mutation, the
    primary violation (from next_action) takes precedence — we don't
    double-fire. The elif branch ensures the command-only check only
    runs when the action-based check didn't fire."""
    from dev.scripts.devctl.runtime.control_decision_consistency import (
        control_decision_violations,
    )
    decision = {
        "may_mutate": False,
        "next_command": "git clean -fdx",
        "can_run_next_command": True,
        "next_action": "vcs.push",  # typed action mutation
    }
    violations = control_decision_violations(decision)
    reasons = {v.reason for v in violations}
    # Primary violation from next_action fires
    assert (
        "push_projected_while_mutation_blocked" in reasons
        or "mutation_projected_while_mutation_blocked" in reasons
    )
    # Secondary command-only check does NOT fire (elif)
    assert "mutation_command_projected_while_mutation_blocked" not in reasons


def test_v4_42_finding_2_may_mutate_true_no_violation() -> None:
    """v4.42: when may_mutate=True, no violation regardless of next_command."""
    from dev.scripts.devctl.runtime.control_decision_consistency import (
        control_decision_violations,
    )
    decision = {
        "may_mutate": True,
        "next_command": "git clean -fdx",
        "can_run_next_command": True,
        "next_action": "",
    }
    violations = control_decision_violations(decision)
    reasons = {v.reason for v in violations}
    assert "mutation_command_projected_while_mutation_blocked" not in reasons
