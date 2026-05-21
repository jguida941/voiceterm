"""Phase 0.6.A v4.32 (rev_pkt_4706) — typed command-envelope classifier tests.

Plan row: MP-GUARDIR-V4-PHASE-0-6-A-COMMAND-ENVELOPE-NORMALIZATION-S1.
Plan revision: guardir-v4.32-2026-05-20.

v4.32 closure requirements over v4.31:

- Full typed envelope (executor + subject + target + packet_id + source_ref
  + proxy state + runnable + classification + reason).
- Bound proxy validation: ``proxy_authority_ref`` must be in
  ``decision_authority_refs`` for ``proxy_authorized_executable``.
- Robust parser: shlex-tokenized argv walk, not substring matching.
- Parser edge tests: ``--actorial`` flag collision, missing values,
  equals form, quoted/tokenized arguments.
"""

from __future__ import annotations

from dev.scripts.devctl.runtime.command_envelope_classification import (
    CommandEnvelopeClassification,
    CommandEnvelopeFields,
    classify_command_envelope,
    classify_command_mutation,
    parse_command_envelope_fields,
    parse_subject_actor,
)


# ---------------------------------------------------------------------------
# Parser primitives: parse_subject_actor + parse_command_envelope_fields
# ---------------------------------------------------------------------------


def test_parse_subject_actor_extracts_token() -> None:
    cmd = (
        "python3 dev/scripts/devctl.py agent-loop --format json "
        "--actor claude --role implementer"
    )
    assert parse_subject_actor(cmd) == "claude"


def test_parse_subject_actor_no_flag_returns_empty() -> None:
    cmd = "python3 dev/scripts/devctl.py review-channel --action status"
    assert parse_subject_actor(cmd) == ""


def test_parse_subject_actor_tolerates_equals_form() -> None:
    cmd = "python3 dev/scripts/devctl.py agent-loop --actor=codex --role reviewer"
    assert parse_subject_actor(cmd) == "codex"


def test_parse_subject_actor_handles_empty_command() -> None:
    assert parse_subject_actor("") == ""
    assert parse_subject_actor("   ") == ""


# v4.32 PARSER EDGE CASES (codex item 3)


def test_parser_does_not_collide_with_actorial_flag() -> None:
    """v4.32: ``--actorial`` must NOT match ``--actor`` (substring collision
    bug from v4.31). The flag must be an EXACT token."""
    cmd = "python3 cmd.py --actorial verbose --role implementer"
    # In v4.31 this returned 'verbose' (or similar) because of substring
    # matching. In v4.32 it must return "" because there is no --actor token.
    assert parse_subject_actor(cmd) == ""
    fields = parse_command_envelope_fields(cmd)
    assert fields.subject_actor == ""
    assert fields.subject_role == "implementer"


def test_parser_handles_actor_at_end_with_no_value() -> None:
    """v4.32: ``--actor`` with nothing after must not crash; return empty."""
    assert parse_subject_actor("python3 cmd.py --actor") == ""


def test_parser_handles_quoted_actor_value() -> None:
    """v4.32: shlex tokenization correctly unquotes ``--actor "claude"``."""
    cmd = 'python3 cmd.py --actor "claude" --role implementer'
    assert parse_subject_actor(cmd) == "claude"


def test_parser_handles_malformed_command_safely() -> None:
    """v4.32: unparseable shlex input (unclosed quote) returns empty fields."""
    cmd = 'python3 cmd.py --actor "unclosed'
    fields = parse_command_envelope_fields(cmd)
    # Must not raise; returns CommandEnvelopeFields with empty values
    assert isinstance(fields, CommandEnvelopeFields)
    assert fields.subject_actor == ""


def test_parser_extracts_all_envelope_fields() -> None:
    """v4.32: full typed envelope extraction in one parse pass."""
    cmd = (
        "python3 dev/scripts/devctl.py review-channel --action post "
        "--actor claude --actor-role implementer --session-id sess-claude "
        "--target-role reviewer --target-session-id sess-codex "
        "--packet-id rev_pkt_4700 --proxy-authority-ref decision:abc"
    )
    fields = parse_command_envelope_fields(cmd)
    assert fields.subject_actor == "claude"
    assert fields.subject_role == "implementer"
    assert fields.subject_session_id == "sess-claude"
    assert fields.target_role == "reviewer"
    assert fields.target_session_id == "sess-codex"
    assert fields.packet_id == "rev_pkt_4700"
    assert fields.proxy_authority_ref_in_command == "decision:abc"


def test_parser_subject_role_precedence_actor_role_over_role() -> None:
    """v4.32: when both --actor-role and --role appear, --actor-role wins
    because --role is ambiguous between subject and target."""
    cmd = "python3 cmd.py --actor claude --actor-role implementer --role reviewer"
    fields = parse_command_envelope_fields(cmd)
    assert fields.subject_role == "implementer"  # --actor-role wins


def test_parser_subject_role_falls_back_to_role() -> None:
    """v4.32: when only --role is supplied, it populates subject_role."""
    cmd = "python3 cmd.py --actor claude --role implementer"
    fields = parse_command_envelope_fields(cmd)
    assert fields.subject_role == "implementer"


# ---------------------------------------------------------------------------
# Classification: 4-state sum type
# ---------------------------------------------------------------------------


def test_unrunnable_blocker_dominates_classification() -> None:
    """repair_command_runnable=False wins regardless of actor or proxy state."""
    result = classify_command_envelope(
        command="python3 dev/scripts/devctl.py develop next --actor codex",
        current_actor="codex",
        proxy_authority_ref="decision:abc",
        decision_authority_refs=("decision:abc",),
        repair_command_runnable=False,
    )
    assert result.classification == "unrunnable_typed_blocker"
    assert result.repair_command_runnable is False
    assert result.is_unrunnable_blocker is True
    assert result.is_executable is False
    assert result.proxy_authority_ref == ""  # cleared by unrunnable
    assert result.proxy_authority_bound is False


def test_unrunnable_blocker_via_string_false() -> None:
    """JSON-projection 'false' must be honored, not coerced to True."""
    result = classify_command_envelope(
        command="python3 dev/scripts/devctl.py agent-loop --actor claude",
        current_actor="claude",
        repair_command_runnable="false",
    )
    assert result.classification == "unrunnable_typed_blocker"


def test_no_current_actor_preserves_backwards_compat() -> None:
    """Legacy callers (no current_actor) get same_actor_executable always."""
    result = classify_command_envelope(
        command="python3 dev/scripts/devctl.py agent-loop --actor claude",
        current_actor="",
    )
    assert result.classification == "same_actor_executable"
    assert result.is_executable is True
    assert "no current_actor" in result.classification_reason


def test_no_actor_flag_is_same_actor_executable() -> None:
    result = classify_command_envelope(
        command="python3 dev/scripts/devctl.py review-channel --action status",
        current_actor="codex",
    )
    assert result.classification == "same_actor_executable"
    assert result.subject_actor == ""
    assert "no --actor scoping" in result.classification_reason


def test_subject_matches_current_actor_is_same_actor_executable() -> None:
    result = classify_command_envelope(
        command="python3 dev/scripts/devctl.py agent-loop --actor codex --role reviewer",
        current_actor="codex",
    )
    assert result.classification == "same_actor_executable"
    assert result.subject_actor == "codex"
    assert result.executor_actor == "codex"
    assert "matches executor_actor" in result.classification_reason


def test_cross_actor_no_proxy_is_peer_lane_status_only() -> None:
    """v4.30 rev_pkt_4701/4703 reproduction: claude command for codex runner."""
    result = classify_command_envelope(
        command=(
            "python3 dev/scripts/devctl.py agent-loop --format json "
            "--actor claude --role implementer "
            "--session-id 2a5b3528-aaa6-4615-b83b-5b1d3598509b"
        ),
        current_actor="codex",
    )
    assert result.classification == "peer_lane_status_only"
    assert result.subject_actor == "claude"
    assert result.executor_actor == "codex"
    assert result.is_peer_lane is True
    assert result.is_executable is False
    assert result.proxy_authority_ref == ""


# ---------------------------------------------------------------------------
# v4.32 BOUND PROXY VALIDATION (codex item 2)
# ---------------------------------------------------------------------------


def test_v4_32_bound_proxy_authorizes_cross_actor_execution() -> None:
    """v4.32: a cross-actor command WITH a proxy_authority_ref that matches a
    member of ``decision_authority_refs`` is ``proxy_authorized_executable``."""
    result = classify_command_envelope(
        command=(
            "python3 dev/scripts/devctl.py agent-loop --actor claude "
            "--role implementer"
        ),
        current_actor="codex",
        proxy_authority_ref="decision:agent_loop_decision_2026_05_21",
        decision_authority_refs=(
            "decision:agent_loop_decision_2026_05_21",
            "snapshot:cps_2026_05_21",
        ),
    )
    assert result.classification == "proxy_authorized_executable"
    assert result.subject_actor == "claude"
    assert result.executor_actor == "codex"
    assert result.proxy_authority_ref == "decision:agent_loop_decision_2026_05_21"
    assert result.proxy_authority_bound is True
    assert result.is_executable is True
    assert result.is_peer_lane is False
    assert "matched member of decision_authority_refs" in result.classification_reason


def test_v4_32_unbound_proxy_ref_demotes_to_peer_lane() -> None:
    """v4.32 closure requirement: a non-empty proxy_authority_ref that is
    NOT in decision_authority_refs cannot authorize execution. Demoted to
    peer_lane_status_only."""
    result = classify_command_envelope(
        command="python3 dev/scripts/devctl.py agent-loop --actor claude",
        current_actor="codex",
        proxy_authority_ref="decision:unknown_ref_not_in_decision",
        decision_authority_refs=("decision:something_else",),
    )
    assert result.classification == "peer_lane_status_only"
    assert result.proxy_authority_ref == ""  # cleared
    assert result.proxy_authority_bound is False
    assert "NOT in decision_authority_refs" in result.classification_reason


def test_v4_32_proxy_ref_without_decision_refs_is_peer_lane() -> None:
    """v4.32 closure requirement: a proxy_authority_ref WITHOUT
    decision_authority_refs (caller didn't supply them) cannot authorize
    execution. Demoted to peer_lane_status_only."""
    result = classify_command_envelope(
        command="python3 dev/scripts/devctl.py agent-loop --actor claude",
        current_actor="codex",
        proxy_authority_ref="decision:abc",
        # decision_authority_refs not passed (empty default)
    )
    assert result.classification == "peer_lane_status_only"
    assert result.proxy_authority_bound is False
    assert "no decision_authority_refs supplied" in result.classification_reason


def test_v4_32_empty_proxy_ref_is_peer_lane_regardless_of_decision_refs() -> None:
    """v4.32: cross-actor + empty proxy_authority_ref = peer_lane, even when
    decision_authority_refs is populated."""
    result = classify_command_envelope(
        command="python3 dev/scripts/devctl.py agent-loop --actor claude",
        current_actor="codex",
        proxy_authority_ref="",
        decision_authority_refs=("decision:any", "snapshot:any"),
    )
    assert result.classification == "peer_lane_status_only"
    assert result.proxy_authority_ref == ""
    assert result.proxy_authority_bound is False
    assert "without proxy_authority_ref" in result.classification_reason


def test_v4_32_whitespace_only_proxy_ref_is_peer_lane() -> None:
    """v4.32: whitespace-only ref must not authorize."""
    result = classify_command_envelope(
        command="python3 dev/scripts/devctl.py agent-loop --actor claude",
        current_actor="codex",
        proxy_authority_ref="   ",
        decision_authority_refs=("decision:abc",),
    )
    assert result.classification == "peer_lane_status_only"
    assert result.proxy_authority_bound is False


def test_v4_32_unrunnable_dominates_bound_proxy_authority() -> None:
    """v4.32: even with valid bound proxy authority, repair_command_runnable=
    False dominates."""
    result = classify_command_envelope(
        command="python3 dev/scripts/devctl.py agent-loop --actor claude",
        current_actor="codex",
        proxy_authority_ref="decision:bound",
        decision_authority_refs=("decision:bound",),
        repair_command_runnable=False,
    )
    assert result.classification == "unrunnable_typed_blocker"
    assert result.proxy_authority_ref == ""
    assert result.proxy_authority_bound is False


# ---------------------------------------------------------------------------
# v4.32 EXPANDED ENVELOPE FIELDS (codex item 1)
# ---------------------------------------------------------------------------


def test_v4_32_envelope_carries_full_subject_route() -> None:
    """v4.32: classification carries subject_actor, subject_role,
    subject_session_id, target_role, target_session_id, packet_id."""
    result = classify_command_envelope(
        command=(
            "python3 dev/scripts/devctl.py review-channel --action post "
            "--actor claude --actor-role implementer "
            "--session-id sess-claude --target-role reviewer "
            "--target-session-id sess-codex --packet-id rev_pkt_4706"
        ),
        current_actor="claude",
        current_role="implementer",
        current_session_id="sess-claude",
    )
    assert result.classification == "same_actor_executable"
    assert result.subject_actor == "claude"
    assert result.subject_role == "implementer"
    assert result.subject_session_id == "sess-claude"
    assert result.target_role == "reviewer"
    assert result.target_session_id == "sess-codex"
    assert result.packet_id == "rev_pkt_4706"
    assert result.executor_actor == "claude"
    assert result.executor_role == "implementer"
    assert result.executor_session_id == "sess-claude"


def test_v4_32_envelope_carries_source_ref() -> None:
    """v4.32: caller-provided source_ref (e.g.
    ``campaign.claude_next_command``) is preserved in the envelope for audit."""
    result = classify_command_envelope(
        command="python3 cmd.py --actor claude",
        current_actor="codex",
        source_ref="campaign.claude_next_command",
    )
    assert result.source_ref == "campaign.claude_next_command"


def test_v4_32_envelope_records_proxy_execution_flag() -> None:
    """v4.32: ``proxy_execution`` boolean derived from ``_proxy_execution()``
    is exposed on the classification result for downstream audit."""
    result = classify_command_envelope(
        command="python3 cmd.py --actor claude",
        current_actor="codex",
    )
    assert result.proxy_execution is True  # codex executing claude command
    same_actor = classify_command_envelope(
        command="python3 cmd.py --actor codex",
        current_actor="codex",
    )
    assert same_actor.proxy_execution is False


def test_v4_32_envelope_records_decision_authority_refs() -> None:
    """v4.32: classification result preserves the decision_authority_refs
    used during classification for audit."""
    result = classify_command_envelope(
        command="python3 cmd.py --actor claude",
        current_actor="codex",
        proxy_authority_ref="decision:abc",
        decision_authority_refs=("decision:abc", "snapshot:xyz"),
    )
    assert result.decision_authority_refs == ("decision:abc", "snapshot:xyz")


# ---------------------------------------------------------------------------
# Serialization + isinstance properties
# ---------------------------------------------------------------------------


def test_classification_to_dict_round_trips_v4_32_fields() -> None:
    """v4.32: classification dataclass must serialize all 14 fields."""
    result = classify_command_envelope(
        command=(
            "python3 dev/scripts/devctl.py review-channel --action post "
            "--actor claude --target-role reviewer --packet-id rev_pkt_4706"
        ),
        current_actor="codex",
        current_role="reviewer",
        source_ref="campaign.claude_next_command",
    )
    payload = result.to_dict()
    expected_keys = {
        "classification",
        "executor_actor", "executor_role", "executor_session_id",
        "subject_actor", "subject_role", "subject_session_id",
        "target_role", "target_session_id",
        "packet_id", "source_ref",
        "proxy_execution", "proxy_authority_ref", "proxy_authority_bound",
        "repair_command_runnable",
        "classification_reason",
        "decision_authority_refs",
        "schema_version", "contract_id",
    }
    assert expected_keys.issubset(payload.keys())
    assert payload["contract_id"] == "CommandEnvelopeClassification"
    assert payload["schema_version"] == 3  # v4.39 bumped from v4.32's 2
    assert payload["source_ref"] == "campaign.claude_next_command"
    assert payload["packet_id"] == "rev_pkt_4706"


def test_classification_isinstance_check() -> None:
    """Defense in depth: classifier always returns the typed dataclass."""
    result = classify_command_envelope(command="", current_actor="")
    assert isinstance(result, CommandEnvelopeClassification)
    assert result.classification == "same_actor_executable"


def test_rev_pkt_4703_live_reproduction_classified_peer_lane() -> None:
    """v4.31/4.32 regression: codex's exact rev_pkt_4703 shape must classify
    as ``peer_lane_status_only`` so consumers refuse to render it."""
    rev_pkt_4703_command = (
        "python3 dev/scripts/devctl.py agent-loop --format json "
        "--actor claude --role implementer "
        "--session-id 2a5b3528-aaa6-4615-b83b-5b1d3598509b"
    )
    result = classify_command_envelope(
        command=rev_pkt_4703_command,
        current_actor="codex",
    )
    assert result.classification == "peer_lane_status_only"
    assert result.is_executable is False
    assert result.is_peer_lane is True
    assert result.subject_actor == "claude"
    assert result.subject_role == "implementer"
    assert (
        result.subject_session_id == "2a5b3528-aaa6-4615-b83b-5b1d3598509b"
    )


# ---------------------------------------------------------------------------
# v4.39 (rev_pkt_4710) — MUTATION RISK CLASSIFICATION
# ---------------------------------------------------------------------------


def test_classify_command_mutation_none_for_read_only_command() -> None:
    """v4.39: a read-only command returns (none, none)."""
    kind, risk = classify_command_mutation(
        "python3 dev/scripts/devctl.py review-channel --action status"
    )
    assert kind == "none"
    assert risk == "none"


def test_classify_command_mutation_empty_command() -> None:
    assert classify_command_mutation("") == ("none", "none")
    assert classify_command_mutation("   ") == ("none", "none")


def test_classify_command_mutation_git_stash() -> None:
    """v4.39: codex's exact ``git stash`` discipline list."""
    kind, risk = classify_command_mutation("git stash push -m 'temp'")
    assert kind == "git_stash"
    assert risk == "shared_worktree_state"


def test_classify_command_mutation_git_reset() -> None:
    kind, risk = classify_command_mutation("git reset --hard HEAD")
    assert kind == "git_reset"
    assert risk == "shared_worktree_state"


def test_classify_command_mutation_git_checkout() -> None:
    kind, risk = classify_command_mutation("git checkout main")
    assert kind == "git_checkout"
    assert risk == "shared_worktree_state"


def test_classify_command_mutation_git_restore() -> None:
    kind, risk = classify_command_mutation("git restore --staged file.py")
    assert kind == "git_restore"
    assert risk == "shared_worktree_state"


def test_classify_command_mutation_git_clean() -> None:
    """v4.39: codex specifically named the ``git clean`` taxonomy gap."""
    kind, risk = classify_command_mutation("git clean -fdx")
    assert kind == "git_clean"
    assert risk == "shared_worktree_state"


def test_classify_command_mutation_git_apply() -> None:
    kind, risk = classify_command_mutation("git apply patch.diff")
    assert kind == "git_apply"
    assert risk == "shared_worktree_state"


def test_classify_command_mutation_shell_redirect() -> None:
    """v4.39: ``> file`` shell redirection is a mutation surface."""
    kind, risk = classify_command_mutation("echo content > /tmp/output.txt")
    assert kind == "shell_redirect"
    assert risk == "shared_worktree_writes"


def test_classify_command_mutation_shell_append_redirect() -> None:
    """v4.39: ``>>`` (append) is also a write mutation."""
    kind, risk = classify_command_mutation("date >> /tmp/log.txt")
    assert kind == "shell_redirect"
    assert risk == "shared_worktree_writes"


def test_classify_command_mutation_shell_heredoc() -> None:
    """v4.39: ``<<EOF`` heredoc writes are mutation surfaces."""
    kind, risk = classify_command_mutation("cat <<EOF > out.txt\nfoo\nEOF")
    # The here-doc is detected first (it appears before the > in this string)
    assert kind in ("shell_heredoc", "shell_redirect")
    assert risk == "shared_worktree_writes"


def test_classify_command_mutation_shell_herestring() -> None:
    """v4.39: ``<<<word`` herestring writes are mutation surfaces."""
    kind, risk = classify_command_mutation("python3 -c 'pass' <<<'data'")
    assert kind == "shell_herestring"
    assert risk == "shared_worktree_writes"


def test_classify_command_mutation_tee_write() -> None:
    """v4.39: ``tee`` writes to whatever stdin/path supplied."""
    kind, risk = classify_command_mutation("echo foo | tee /tmp/bar.txt")
    assert kind == "tee_write"
    assert risk == "shared_worktree_writes"


def test_classify_command_mutation_git_subcommand_word_boundary() -> None:
    """v4.39: the detection is exact-token. ``git stashabc`` must NOT match
    ``git stash`` (defense against substring collision similar to v4.32
    parser fix)."""
    kind, risk = classify_command_mutation("git stashabc")
    assert kind == "none"
    assert risk == "none"


def test_classify_command_mutation_python_command_with_gt_unaffected() -> None:
    """v4.39: a Python comparison ``>`` inside an inline `python3 -c` string
    must not trigger shell_redirect. The detection requires SPACE-bordered
    `>` so genuine shell redirect is matched but in-code comparisons are
    not."""
    cmd = "python3 -c 'if 1>0: print(1)'"
    kind, risk = classify_command_mutation(cmd)
    assert kind == "none"
    assert risk == "none"


def test_classify_command_envelope_carries_mutation_fields() -> None:
    """v4.39: classify_command_envelope populates the new mutation fields
    on its result, orthogonal to the actor/proxy classification."""
    result = classify_command_envelope(
        command="git stash --include-untracked",
        current_actor="claude",
    )
    assert result.mutation_action_kind == "git_stash"
    assert result.mutation_risk_class == "shared_worktree_state"
    assert result.is_governed_mutation is True
    # Actor/proxy dimensions still work as expected — no --actor token →
    # same_actor_executable (the command runs in the current shell).
    assert result.classification == "same_actor_executable"


def test_classify_command_envelope_read_only_command_not_governed() -> None:
    """v4.39: a read-only command has mutation fields default to 'none' and
    ``is_governed_mutation`` returns False."""
    result = classify_command_envelope(
        command="python3 dev/scripts/devctl.py review-channel --action status",
        current_actor="claude",
    )
    assert result.mutation_action_kind == "none"
    assert result.mutation_risk_class == "none"
    assert result.is_governed_mutation is False


def test_classify_command_envelope_mutation_persists_through_serialization() -> None:
    """v4.39: mutation fields survive to_dict round-trip for audit/logging."""
    result = classify_command_envelope(
        command="git clean -fdx",
        current_actor="claude",
    )
    payload = result.to_dict()
    assert payload["mutation_action_kind"] == "git_clean"
    assert payload["mutation_risk_class"] == "shared_worktree_state"
    assert payload["schema_version"] == 3  # v4.39 bumped from v4.32's 2


def test_classify_command_envelope_mutation_orthogonal_to_proxy() -> None:
    """v4.39: mutation classification is INDEPENDENT of actor/proxy state.
    A peer-lane command can still name a destructive operation."""
    result = classify_command_envelope(
        command="git reset --hard HEAD --actor claude",
        current_actor="codex",
    )
    # Cross-actor without proxy → peer_lane_status_only
    assert result.classification == "peer_lane_status_only"
    # But the mutation kind is still detected
    assert result.mutation_action_kind == "git_reset"
    assert result.mutation_risk_class == "shared_worktree_state"
    assert result.is_governed_mutation is True


# ---------------------------------------------------------------------------
# v4.39.1 (rev_pkt_4711) — Finding 1: is_safe_to_render composite
# ---------------------------------------------------------------------------


def test_v4_39_1_is_safe_to_render_false_for_same_actor_governed_mutation() -> None:
    """v4.39.1 (rev_pkt_4711): a same-actor destructive command must NOT
    render as runnable. ``git clean -fdx`` from current_actor=claude was
    previously is_executable=True, but is_safe_to_render must be False
    because the mutation is governed."""
    result = classify_command_envelope(
        command="git clean -fdx",
        current_actor="claude",
    )
    assert result.classification == "same_actor_executable"
    assert result.is_executable is True  # actor-wise yes
    assert result.is_governed_mutation is True
    assert result.is_safe_to_render is False  # NOT safe to render


def test_v4_39_1_is_safe_to_render_true_for_safe_executable() -> None:
    """v4.39.1: a same-actor non-destructive command renders safely."""
    result = classify_command_envelope(
        command="python3 dev/scripts/devctl.py review-channel --action status",
        current_actor="claude",
    )
    assert result.is_executable is True
    assert result.is_governed_mutation is False
    assert result.is_safe_to_render is True


def test_v4_39_1_is_safe_to_render_false_for_peer_lane_mutation() -> None:
    """v4.39.1: cross-actor destructive command — both dimensions deny."""
    result = classify_command_envelope(
        command="git stash --include-untracked --actor codex",
        current_actor="claude",
    )
    assert result.is_executable is False  # peer lane
    assert result.is_governed_mutation is True
    assert result.is_safe_to_render is False


def test_v4_39_1_codex_regression_git_clean_not_runnable() -> None:
    """v4.39.1 verbatim regression: ``git clean -fdx`` is not emitted as a
    runnable wrapper/next command."""
    result = classify_command_envelope(
        command="git clean -fdx",
        current_actor="claude",
    )
    assert result.is_safe_to_render is False


def test_v4_39_1_codex_regression_git_stash_not_runnable() -> None:
    """v4.39.1 verbatim regression: ``git stash`` is not emitted."""
    result = classify_command_envelope(
        command="git stash --include-untracked",
        current_actor="claude",
    )
    assert result.is_safe_to_render is False


def test_v4_39_1_codex_regression_git_reset_hard_not_runnable() -> None:
    """v4.39.1 verbatim regression: ``git reset --hard`` is not emitted."""
    result = classify_command_envelope(
        command="git reset --hard HEAD",
        current_actor="claude",
    )
    assert result.is_safe_to_render is False


# ---------------------------------------------------------------------------
# v4.39.1 (rev_pkt_4711) — Finding 2: robust shell-redirect detection
# ---------------------------------------------------------------------------


def test_v4_39_1_shell_redirect_no_space_form() -> None:
    """v4.39.1 (codex's exact pattern #1): ``cat >file`` (no space)."""
    kind, risk = classify_command_mutation("cat >file")
    assert kind == "shell_redirect"
    assert risk == "shared_worktree_writes"


def test_v4_39_1_shell_redirect_append_no_space() -> None:
    """v4.39.1 (codex's exact pattern #2): ``printf x>>file`` (no space)."""
    kind, risk = classify_command_mutation("printf x>>file")
    assert kind == "shell_redirect"
    assert risk == "shared_worktree_writes"


def test_v4_39_1_shell_redirect_fd_form() -> None:
    """v4.39.1 (codex's exact pattern #3): ``cmd 2>err.log`` (fd redirect)."""
    kind, risk = classify_command_mutation("cmd 2>err.log")
    assert kind == "shell_redirect"
    assert risk == "shared_worktree_writes"


def test_v4_39_1_shell_redirect_clobber_form() -> None:
    """v4.39.1 (codex's exact pattern #4): ``cmd >|file`` (clobber)."""
    kind, risk = classify_command_mutation("cmd >|file")
    assert kind == "shell_redirect"
    assert risk == "shared_worktree_writes"


def test_v4_39_1_shell_redirect_combined_fd_form() -> None:
    """v4.39.1: ``&>combined`` (merge stdout+stderr) — fd-style redirect."""
    kind, risk = classify_command_mutation("cmd &>combined.log")
    assert kind == "shell_redirect"
    assert risk == "shared_worktree_writes"


def test_v4_39_1_shell_redirect_in_quoted_string_not_matched() -> None:
    """v4.39.1: ``python3 -c 'if 1>0: pass'`` — `>` inside single quotes
    must NOT trigger shell_redirect detection."""
    kind, risk = classify_command_mutation("python3 -c 'if 1>0: pass'")
    assert kind == "none"
    assert risk == "none"


def test_v4_39_1_shell_redirect_in_double_quoted_string_not_matched() -> None:
    """v4.39.1: ``echo "x > y"`` — `>` inside double quotes is not a redirect."""
    kind, risk = classify_command_mutation('echo "x > y"')
    assert kind == "none"
    assert risk == "none"


def test_v4_39_1_shell_redirect_escaped_gt_not_matched() -> None:
    """v4.39.1: an escaped `\>` is not a redirect (defensive)."""
    kind, risk = classify_command_mutation(r"echo foo \>bar")
    assert kind == "none"
    assert risk == "none"


def test_v4_39_1_shell_redirect_heredoc_still_distinguished() -> None:
    """v4.39.1: heredoc precedence over redirect; ``<<`` still classifies
    as heredoc, not as redirect."""
    kind, risk = classify_command_mutation("cat <<EOF\nfoo\nEOF")
    assert kind == "shell_heredoc"
    assert risk == "shared_worktree_writes"


def test_v4_39_1_shell_redirect_herestring_still_distinguished() -> None:
    """v4.39.1: herestring precedence; ``<<<`` classifies as herestring."""
    kind, risk = classify_command_mutation("cmd <<<input_word")
    assert kind == "shell_herestring"
    assert risk == "shared_worktree_writes"


def test_v4_39_1_quote_stripped_text_handles_unbalanced_quote() -> None:
    """v4.39.1 defensive: malformed shell input with unbalanced quote does
    not crash; classifier returns a best-effort result."""
    # The single quote is never closed; subsequent ``>file`` is inside
    # the unclosed quote and should NOT be detected. Defensive: classifier
    # falls back to no-detection rather than crashing.
    kind, risk = classify_command_mutation("echo 'unbalanced >file")
    # Either ``none`` (treated as inside-quote) or ``shell_redirect`` is
    # acceptable; what matters is that it doesn't raise. Assert the call
    # completes and returns one of the expected tuples.
    assert (kind, risk) in {
        ("none", "none"),
        ("shell_redirect", "shared_worktree_writes"),
    }


# ---------------------------------------------------------------------------
# v4.40 (rev_pkt_4712) — extended mutation taxonomy convergence
# ---------------------------------------------------------------------------


def test_v4_40_git_commit_classified_as_governed_repo_state() -> None:
    """v4.40: ``git commit`` is a repo-state mutation."""
    kind, risk = classify_command_mutation("git commit -m 'msg'")
    assert kind == "git_commit"
    assert risk == "governed_repo_state"


def test_v4_40_git_push_classified_as_governed_repo_state() -> None:
    kind, risk = classify_command_mutation("git push origin main")
    assert kind == "git_push"
    assert risk == "governed_repo_state"


def test_v4_40_git_add_classified_as_governed_repo_state() -> None:
    kind, risk = classify_command_mutation("git add .")
    assert kind == "git_add"
    assert risk == "governed_repo_state"


def test_v4_40_devctl_commit_classified() -> None:
    """v4.40: ``devctl.py commit`` recognized via devctl-prefix detection."""
    kind, risk = classify_command_mutation(
        "python3 dev/scripts/devctl.py commit --execute"
    )
    assert kind == "devctl_commit"
    assert risk == "governed_repo_state"


def test_v4_40_devctl_push_classified() -> None:
    kind, risk = classify_command_mutation(
        "python3 dev/scripts/devctl.py push --execute"
    )
    assert kind == "devctl_push"
    assert risk == "governed_repo_state"


def test_v4_40_devctl_pipeline_action_classified() -> None:
    kind, risk = classify_command_mutation(
        "python3 dev/scripts/devctl.py pipeline --action begin --slice-id abc"
    )
    assert kind == "devctl_pipeline_action"
    assert risk == "governed_pipeline_action"


def test_v4_40_devctl_review_channel_ensure_classified() -> None:
    kind, risk = classify_command_mutation(
        "python3 dev/scripts/devctl.py review-channel --action ensure"
    )
    assert kind == "devctl_review_channel_ensure"
    assert risk == "governed_review_channel_lifecycle"


def test_v4_40_devctl_review_channel_recover_classified() -> None:
    kind, risk = classify_command_mutation(
        "python3 dev/scripts/devctl.py review-channel --action recover"
    )
    assert kind == "devctl_review_channel_recover"
    assert risk == "governed_review_channel_lifecycle"


def test_v4_40_devctl_review_channel_launch_classified() -> None:
    kind, risk = classify_command_mutation(
        "python3 dev/scripts/devctl.py review-channel --action launch codex"
    )
    assert kind == "devctl_review_channel_launch"
    assert risk == "governed_review_channel_lifecycle"


def test_v4_40_devctl_review_channel_stop_classified() -> None:
    kind, risk = classify_command_mutation(
        "python3 dev/scripts/devctl.py review-channel --action stop"
    )
    assert kind == "devctl_review_channel_stop"
    assert risk == "governed_review_channel_lifecycle"


def test_v4_40_devctl_review_channel_post_classified() -> None:
    kind, risk = classify_command_mutation(
        "python3 dev/scripts/devctl.py review-channel --action post --kind task_progress"
    )
    assert kind == "devctl_review_channel_post"
    assert risk == "governed_review_channel_lifecycle"


def test_v4_40_devctl_review_channel_apply_classified() -> None:
    kind, risk = classify_command_mutation(
        "python3 dev/scripts/devctl.py review-channel --action apply --packet-id x"
    )
    assert kind == "devctl_review_channel_apply"
    assert risk == "governed_review_channel_lifecycle"


def test_v4_40_devctl_review_channel_dismiss_classified() -> None:
    kind, risk = classify_command_mutation(
        "python3 dev/scripts/devctl.py review-channel --action dismiss --packet-id x"
    )
    assert kind == "devctl_review_channel_dismiss"
    assert risk == "governed_review_channel_lifecycle"


def test_v4_40_devctl_review_channel_absorb_classified() -> None:
    kind, risk = classify_command_mutation(
        "python3 dev/scripts/devctl.py review-channel --action absorb --packet-id x"
    )
    assert kind == "devctl_review_channel_absorb"
    assert risk == "governed_review_channel_lifecycle"


def test_v4_40_devctl_review_channel_reset_implementer_state_classified() -> None:
    kind, risk = classify_command_mutation(
        "python3 dev/scripts/devctl.py review-channel --action reset-implementer-state"
    )
    assert kind == "devctl_review_channel_reset_implementer_state"
    assert risk == "governed_review_channel_lifecycle"


def test_v4_40_apply_patch_classified_as_bypass_surface() -> None:
    """v4.40: ``apply_patch`` action identifier triggers bypass-surface risk."""
    kind, risk = classify_command_mutation(
        "shell.execute 'apply_patch --to dev/scripts/...'"
    )
    assert kind == "apply_patch"
    assert risk == "bypass_surface"


def test_v4_40_raw_git_bypass_classified() -> None:
    """v4.40: ``raw-git`` and ``raw_git`` flags trigger bypass surface."""
    kind1, risk1 = classify_command_mutation("python3 devctl.py raw-git push")
    assert kind1 == "raw_git_bypass"
    assert risk1 == "bypass_surface"
    kind2, risk2 = classify_command_mutation("call raw_git commit")
    assert kind2 == "raw_git_bypass"
    assert risk2 == "bypass_surface"


def test_v4_40_devctl_review_channel_status_NOT_governed() -> None:
    """v4.40 negative: ``review-channel --action status`` is read-only."""
    kind, risk = classify_command_mutation(
        "python3 dev/scripts/devctl.py review-channel --action status --format json"
    )
    assert kind == "none"
    assert risk == "none"


def test_v4_40_devctl_review_channel_show_NOT_governed() -> None:
    """v4.40 negative: ``review-channel --action show`` is read-only."""
    kind, risk = classify_command_mutation(
        "python3 dev/scripts/devctl.py review-channel --action show --packet-id x"
    )
    assert kind == "none"
    assert risk == "none"


def test_v4_40_devctl_session_NOT_governed() -> None:
    """v4.40 negative: ``devctl.py session`` is read-only orientation."""
    kind, risk = classify_command_mutation(
        "python3 dev/scripts/devctl.py session --role reviewer --format json"
    )
    assert kind == "none"
    assert risk == "none"


def test_v4_40_envelope_governed_repo_state_marks_unsafe_to_render() -> None:
    """v4.40: a same-actor ``git commit`` is not safe to render — extends
    the v4.39.1 default-deny to the new repo-state risk class too."""
    result = classify_command_envelope(
        command="git commit -m 'msg'",
        current_actor="claude",
    )
    assert result.mutation_risk_class == "governed_repo_state"
    assert result.is_governed_mutation is True
    assert result.is_safe_to_render is False


def test_v4_40_envelope_review_channel_mutation_marks_unsafe() -> None:
    """v4.40: ``review-channel --action post`` is not safe to render."""
    result = classify_command_envelope(
        command=(
            "python3 dev/scripts/devctl.py review-channel --action post "
            "--kind task_progress --from-agent claude"
        ),
        current_actor="claude",
    )
    assert result.mutation_risk_class == "governed_review_channel_lifecycle"
    assert result.is_safe_to_render is False


# ---------------------------------------------------------------------------
# v4.41 (rev_pkt_4713) — coordination-lane import isolation
# ---------------------------------------------------------------------------


def test_v4_41_proxy_execution_neutral_module_exists() -> None:
    """v4.41: ``proxy_execution`` lives in a neutral module that can be
    imported without pulling control_decision_obedience or the wider
    runtime graph. This breaks the import cycle codex flagged in
    rev_pkt_4713."""
    from dev.scripts.devctl.runtime.proxy_execution import (
        _proxy_execution,
        proxy_execution,
    )
    # Both names export the same callable (backwards-compat alias)
    assert proxy_execution is _proxy_execution
    # Functional check: same semantics as the legacy underscore-prefixed name
    assert proxy_execution(
        executor_actor="codex",
        executor_role="reviewer",
        executor_session_id="s1",
        subject_actor="claude",
        subject_role="implementer",
        subject_session_id="s2",
    ) is True  # cross-actor → proxy
    assert proxy_execution(
        executor_actor="claude",
        executor_role="implementer",
        executor_session_id="s1",
        subject_actor="claude",
        subject_role="implementer",
        subject_session_id="s1",
    ) is False  # same actor+role+session → not proxy


def test_v4_41_control_decision_obedience_re_exports_proxy_execution() -> None:
    """v4.41: legacy callers that import ``_proxy_execution`` from
    ``control_decision_obedience`` must still work (backwards compat via
    re-export)."""
    from dev.scripts.devctl.runtime.control_decision_obedience import (
        _proxy_execution as legacy,
    )
    from dev.scripts.devctl.runtime.proxy_execution import proxy_execution as neutral
    assert legacy is neutral


def test_v4_41_classifier_does_not_directly_depend_on_obedience_module() -> None:
    """v4.41: the classifier's import statement chain MUST NOT name
    ``control_decision_obedience`` directly. Codex's import-cycle error
    was caused by the classifier pulling obedience, which in turn pulled
    action_matching, which v4.40 made pull the classifier itself."""
    import ast
    import pathlib
    src = pathlib.Path(
        "dev/scripts/devctl/runtime/command_envelope_classification.py"
    ).read_text()
    tree = ast.parse(src)
    direct_imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            direct_imports.append(node.module)
    # The classifier MUST import from ``proxy_execution`` (neutral) only,
    # not from ``control_decision_obedience``.
    assert "proxy_execution" in direct_imports
    assert "control_decision_obedience" not in direct_imports, (
        "v4.41 violation: classifier imports from control_decision_obedience, "
        "recreating the cycle codex flagged in rev_pkt_4713."
    )


def test_v4_41_proxy_execution_module_has_no_internal_deps() -> None:
    """v4.41: the neutral primitive module must be a leaf — no imports from
    OTHER devctl runtime modules. Otherwise it could grow new dependencies
    over time that recreate the cycle."""
    import ast
    import pathlib
    src = pathlib.Path(
        "dev/scripts/devctl/runtime/proxy_execution.py"
    ).read_text()
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            # Must NOT import from any sibling runtime module
            assert not node.module.startswith("."), (
                f"v4.41 violation: proxy_execution.py imports from "
                f"sibling module '{node.module}' — must remain a leaf."
            )
            # And no devctl path imports either
            assert "devctl" not in node.module, (
                f"v4.41 violation: proxy_execution.py imports devctl module "
                f"'{node.module}' — must remain a leaf."
            )
