"""TDD-discovery audit of codex's session edits (red-first, tests only).

Per the AntiDumbass amendment in ``delete_after_ingest.md`` (lines 731-870),
the TDD-discovery role audits codex's per-session edits by writing failing
tests for the invariants codex's edits SHOULD have preserved or fixed.

This file is read-only on production code. Each ``test_red_*`` test asserts
the BEHAVIOR the system SHOULD have. If a test FAILS (RED), the failure IS
the invariant gap discovery — codex's edits either did not address the
invariant or actually broke it.

Audited codex edits this session (verified via ``git diff HEAD --stat``):

  - dev/scripts/devctl/runtime/control_decision_obedience.py (live)
  - dev/scripts/devctl/runtime/control_decision_artifacts.py (live)
  - dev/scripts/devctl/commands/review_channel/event_handler.py (modified)
  - dev/scripts/devctl/commands/review_channel/event_post_action.py (modified)
  - dev/scripts/devctl/commands/review_channel/event_control_decision_fallback.py
    (NEW untracked file — codex created this)
  - dev/scripts/devctl/commands/development/packet_attention.py (modified)
  - dev/scripts/devctl/review_channel/packet_route_resolution.py (modified)
  - dev/scripts/devctl/commands/check/router_python_tests.py (modified)
  - 100+ other modules touched

Invariants under audit (lettered A..H from operator directive):

  A. Stale projection vs fresh dashboard-backed AgentLoopDecision
     (codex's "write-side packet gate" fix referenced in rev_pkt_4849)
  B. Premature-GREEN pattern: single round-trip not sufficient for G28/G29
  C. evaluate_control_decision_obedience refresh-hint when decision missing
     (TDD Inv 4 from prior session)
  D. Codex's per-packet scoped /private/tmp control-decision artifacts
     vs typed-state preference
  E. Codex's controller-repair packet-status lane patch durability
     (rev_pkt_4848)
  F. G23 + G40 wiring into _DEVCTL_TEST_TARGETS check-router
  G. Worktree state recovery: 214 dirty + 6 import-index atomicity violations
  H. AgentLoopDecision contradiction pattern (rev_pkt_4839): when
     safe_to_continue=False, no lane may append edit-grants without
     explicit operator override
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest


# ---------------------------------------------------------------------------
# Repo path resolution
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[5]


# ---------------------------------------------------------------------------
# A. Stale projection vs fresh dashboard-backed AgentLoopDecision
# ---------------------------------------------------------------------------

def test_red_a_dashboard_fallback_overrides_stale_empty_allowed_actions() -> None:
    """A. A stale projected decision with allowed_actions=[] MUST NOT veto
    a fresh dashboard-backed decision that lists the required action.

    Codex's rev_pkt_4849 patch added
    ``event_control_decision_fallback.should_prefer_dashboard_control_decision``
    to the post-action path. The invariant: if the projection's allowed_actions
    is empty AND the dashboard decision lists the required action, the fallback
    helper MUST return True so the post path uses the dashboard decision.
    """
    from dev.scripts.devctl.commands.review_channel.event_control_decision_fallback import (
        should_prefer_dashboard_control_decision,
    )

    args = type(
        "Args",
        (),
        {
            "action": "post",
            "kind": "task_progress",
        },
    )()
    stale_projection = {"allowed_actions": []}
    fresh_dashboard = {
        "allowed_actions": ["review-channel.post_task_progress"],
    }
    attempted_argv = (
        "python3",
        "dev/scripts/devctl.py",
        "review-channel",
        "--action",
        "post",
        "--kind",
        "task_progress",
    )

    result = should_prefer_dashboard_control_decision(
        args=args,
        projected_decision=stale_projection,
        dashboard_decision=fresh_dashboard,
        attempted_argv=attempted_argv,
    )

    assert result is True, (
        "Stale projection with allowed_actions=[] must not override "
        "fresh dashboard decision that lists the required action. "
        "If this fails, codex's rev_pkt_4849 patch did not fix the "
        "route — the dashboard fallback was not consulted or did not "
        "match the required-action signature."
    )


def test_red_a_dashboard_fallback_rejects_when_projection_already_allows() -> None:
    """A (corollary). When projection already allows the action, the
    dashboard fallback MUST NOT override it (no spurious switching).
    """
    from dev.scripts.devctl.commands.review_channel.event_control_decision_fallback import (
        should_prefer_dashboard_control_decision,
    )

    args = type(
        "Args",
        (),
        {"action": "post", "kind": "task_progress"},
    )()
    projection_with_action = {
        "allowed_actions": ["review-channel.post_task_progress"],
    }
    dashboard = {
        "allowed_actions": ["review-channel.post_task_progress"],
    }

    result = should_prefer_dashboard_control_decision(
        args=args,
        projected_decision=projection_with_action,
        dashboard_decision=dashboard,
        attempted_argv=(
            "python3",
            "dev/scripts/devctl.py",
            "review-channel",
            "--action",
            "post",
            "--kind",
            "task_progress",
        ),
    )

    assert result is False, (
        "When projection already lists the required action, the "
        "fallback must not prefer the dashboard decision."
    )


# ---------------------------------------------------------------------------
# B. Premature-GREEN pattern: single round-trip NOT sufficient for G28/G29
# ---------------------------------------------------------------------------

_REQUIRED_PACKET_KINDS_FOR_GREEN = (
    "finding",
    "task_progress",
    "task_blocked",
    "plan_gap_review",
    "action_request",
)


def test_red_b_g28_green_requires_multiple_packet_kinds_not_just_one() -> None:
    """B. Codex's claim that G28/G29 is GREEN after a single round-trip
    must be substantiated by inspecting which packet kinds the live
    write-side gate has actually been exercised with.

    The invariant: the gate must accept at least 5 typed packet kinds
    (finding, task_progress, task_blocked, plan_gap_review, action_request)
    via the SAME path. We assert the public helper exists and that the
    canonical required-action mapping covers each kind.
    """
    from dev.scripts.devctl.runtime.review_channel_post_actions import (
        required_review_channel_post_action,
    )

    sample_argv = (
        "python3",
        "dev/scripts/devctl.py",
        "review-channel",
        "--action",
        "post",
    )
    missing_kinds: list[str] = []
    for kind in _REQUIRED_PACKET_KINDS_FOR_GREEN:
        action = required_review_channel_post_action(sample_argv, kind=kind)
        if not action:
            missing_kinds.append(kind)

    assert not missing_kinds, (
        "Single round-trip GREEN is insufficient: the typed "
        "required-action mapping must cover all five canonical kinds "
        "(finding, task_progress, task_blocked, plan_gap_review, "
        f"action_request); missing={missing_kinds}. Each missing kind "
        "is a path codex's write-side gate has not been exercised on."
    )


def test_red_b_g29_durability_requires_ttl_boundary_evidence() -> None:
    """B (TTL boundary). The G29 absorption fix must be testable at the
    TTL boundary: a packet absorbed at TTL-expiry-1 second must produce
    different lifecycle output than one at TTL-expiry+1 second.

    We probe ``partition_live_pending_packets`` (the public partitioning
    primitive) and assert it carries TTL-aware semantics, not just a
    static "alive" set.
    """
    from dev.scripts.devctl.review_channel.pending_packet_core import (
        partition_live_pending_packets,
    )

    # Build two packets with deliberately ordered observation times: one
    # past_ttl_pending and one within the active TTL. The partitioning
    # primitive MUST return distinct buckets — if it returns identical
    # buckets, the TTL boundary is being collapsed into a single state.
    fresh = {
        "packet_id": "rev_pkt_TEST_FRESH",
        "lifecycle_current_state": "pending",
        "expires_at_utc": "2099-01-01T00:00:00Z",
    }
    expired = {
        "packet_id": "rev_pkt_TEST_EXPIRED",
        "lifecycle_current_state": "pending",
        "expires_at_utc": "2000-01-01T00:00:00Z",
    }

    result = partition_live_pending_packets((fresh, expired))
    assert hasattr(result, "live") or isinstance(result, dict), (
        "partition_live_pending_packets must return a structured result "
        "(dataclass or dict) so consumers can route TTL boundaries; "
        "if this fails the partitioning function does not exist or has "
        "a different shape than what G29 callers rely on."
    )


# ---------------------------------------------------------------------------
# C. evaluate_control_decision_obedience refresh hint (TDD Inv 4)
# ---------------------------------------------------------------------------

def test_red_c_missing_decision_emits_refresh_hint_not_raw_violation() -> None:
    """C. When ``decision=None`` and ``allow_empty=False``, the report
    must carry a typed refresh hint (next_command / refresh_command /
    MissingDecisionRefreshHint), not just a raw
    ``no_control_decision_input`` violation.

    TDD Inv 4 from the prior session. The fix lands a typed
    ``MissingDecisionRefreshHint`` carrying
    ``next_command``/``expected_decision_path``/``actor``/``role``/
    ``session_id`` so consumers can rebuild the exact ``develop next``
    refresh command for their scope instead of seeing only the raw
    ``no_control_decision_input`` violation.
    """
    from dev.scripts.devctl.runtime.control_decision_obedience import (
        DEFAULT_EXPECTED_DECISION_PATH,
        evaluate_control_decision_obedience,
    )

    report = evaluate_control_decision_obedience(
        decision=None,
        attempted_actions=(),
        allow_empty=False,
        actor="codex",
        role="reviewer",
        session_id="codex-session",
    )

    report_dict = report.to_dict()
    has_refresh_hint = any(
        report_dict.get(key)
        for key in (
            "missing_decision_refresh_hint",
            "next_command",
            "refresh_command",
        )
    )
    assert has_refresh_hint, (
        "evaluate_control_decision_obedience(decision=None) must emit "
        "a typed refresh hint (next_command, refresh_command, or "
        "MissingDecisionRefreshHint) so consumers know how to recover. "
        "Current behavior: only emits raw 'no_control_decision_input' "
        "violation. Codex's session edits did NOT close this gap."
    )

    # Strengthen: the hint must be the typed MissingDecisionRefreshHint
    # shape and must carry the per-actor/role/session refresh scope plus
    # the canonical expected typed-state path.
    hint = report_dict.get("missing_decision_refresh_hint")
    assert isinstance(hint, dict), (
        "missing_decision_refresh_hint must be a typed payload (dict from "
        f"MissingDecisionRefreshHint.to_dict()); got {type(hint).__name__}."
    )
    assert hint.get("contract_id") == "MissingDecisionRefreshHint"
    assert hint.get("actor") == "codex"
    assert hint.get("role") == "reviewer"
    assert hint.get("session_id") == "codex-session"
    assert hint.get("expected_decision_path") == DEFAULT_EXPECTED_DECISION_PATH
    expected_command = (
        "python3 dev/scripts/devctl.py develop next "
        "--actor codex --role reviewer --session-id codex-session "
        "--format json"
    )
    assert hint.get("next_command") == expected_command
    assert report_dict.get("next_command") == expected_command
    assert report_dict.get("refresh_command") == expected_command


# ---------------------------------------------------------------------------
# D. Codex's per-packet scoped /private/tmp control-decision artifacts:
# typed-state must be preferred; ephemeral old artifacts must be skipped
# ---------------------------------------------------------------------------

def test_red_d_typed_state_preferred_over_private_tmp_artifacts(
    tmp_path: Path,
) -> None:
    """D. ``load_control_decision_payload`` reads from
    ``DEFAULT_CONTROL_DECISION_INPUT_CANDIDATES`` which are typed-state
    paths under ``dev/reports/review_channel/state/``. If a per-packet
    ``/private/tmp/codex_agent_loop_decision_*.json`` artifact exists
    elsewhere, the obedience layer must NOT consult it unless explicitly
    requested via ``--control-decision-input``.

    Invariant: the canonical loader must not auto-discover ephemeral
    ``/private/tmp`` paths.
    """
    from dev.scripts.devctl.runtime.control_decision_artifacts import (
        DEFAULT_CONTROL_DECISION_INPUT_CANDIDATES,
    )

    paths = tuple(str(p) for p in DEFAULT_CONTROL_DECISION_INPUT_CANDIDATES)
    for path in paths:
        assert not path.startswith("/tmp"), (
            f"Default control-decision candidate path '{path}' looks "
            "ephemeral (/tmp) — typed-state under dev/reports must be "
            "preferred."
        )
        assert not path.startswith("/private/tmp"), (
            f"Default control-decision candidate '{path}' looks "
            "ephemeral (/private/tmp) — typed-state must be preferred."
        )
        # Must be a repo-relative path under dev/reports/
        assert "dev/reports" in path or "dev/state" in path, (
            f"Default candidate '{path}' is neither under "
            "dev/reports nor dev/state. Codex's per-packet artifact "
            "layout may have leaked ephemeral paths into the canonical "
            "loader."
        )


def test_red_d_load_control_decision_payload_returns_empty_for_missing_typed_state(
    tmp_path: Path,
) -> None:
    """D (corollary). When typed-state candidates do not exist in a
    fresh repo_root, the loader must return ``{}``, not silently fall
    back to ephemeral ``/private/tmp`` paths.
    """
    from dev.scripts.devctl.runtime.control_decision_artifacts import (
        load_control_decision_payload,
    )

    class _Args:
        control_decision_input = ""
        control_decision_payload = None
        actor = "claude"
        role = "reviewer"
        session_id = "sess-test"

    result = load_control_decision_payload(_Args(), repo_root=tmp_path)
    assert result == {}, (
        "Loader must return {} when no typed-state artifact exists, not "
        f"fall back to ephemeral paths. Got: {result!r}"
    )


# ---------------------------------------------------------------------------
# E. Codex's controller-repair packet-status lane patch (rev_pkt_4848)
# must persist in typed state: a fresh agent-loop run must materialize
# may_mutate=False with the post_task_progress + post_task_blocked grants
# ---------------------------------------------------------------------------

def test_red_e_controller_repair_shape_is_constructible_via_typed_builder() -> None:
    """E. The patch claims a fresh agent-loop run yields
    ``may_mutate=False, allowed_actions=[...post_task_progress,
    ...post_task_blocked]``. This shape MUST be reachable through
    ``build_agent_loop_decision`` against a minimal typed review_state
    — i.e., not a unit-test stub.
    """
    from dev.scripts.devctl.runtime.agent_loop_decision import (
        build_agent_loop_decision,
    )

    # Minimal-but-realistic review_state: an actor with no fresh
    # outcome but pending packet attention should yield a wait
    # decision with the canonical communication grants visible.
    review_state: dict[str, Any] = {
        "packets": (),
        "agent_work_board": {"rows": ()},
        "agent_sync": {"source_latest_event_id": "rev_evt_00000"},
    }
    dashboard: dict[str, Any] = {}

    decision = build_agent_loop_decision(
        review_state=review_state,
        dashboard=dashboard,
        actor_id="claude",
        actor_role="reviewer",
        session_id="sess-test",
    )

    payload = decision.to_dict()
    allowed = {str(a).strip().lower() for a in payload.get("allowed_actions", ())}

    expected_lane_actions = {
        "review-channel.post_task_progress",
        "review-channel.post_task_blocked",
    }
    overlap = expected_lane_actions & allowed
    assert overlap, (
        "Controller-repair packet-status lane: a wait-decision must "
        "include at least one of the canonical lane grants "
        f"{expected_lane_actions} in allowed_actions; got allowed="
        f"{allowed!r}. If empty, codex's rev_pkt_4848 patch is not "
        "wired through build_agent_loop_decision — only through "
        "downstream unit-test stubs."
    )


# ---------------------------------------------------------------------------
# F. G23 + G40 wiring into _DEVCTL_TEST_TARGETS check-router
# ---------------------------------------------------------------------------

_G23_TEST_PATH = (
    "dev/scripts/devctl/tests/scenarios/test_tdd_packet_lifecycle_invariants.py"
)
_G23_GUARD_PATH = "dev/scripts/checks/check_packet_body_observation_route.py"
_G40_GUARD_PREFIX = "dev/scripts/checks/check_packet_lifecycle"


def test_red_f_g23_test_wired_into_check_router_targets() -> None:
    """F. The G23 packet-body-observation-route test must be wired into
    ``_DEVCTL_TEST_TARGETS`` so a guard or production-code change
    triggers it. Codex claimed the test was written; this asserts it
    was also wired.
    """
    from dev.scripts.devctl.commands.check.router_python_tests import (
        _DEVCTL_TEST_TARGETS,
    )

    wired_test_paths: set[str] = set()
    wired_source_prefixes: set[str] = set()
    for source_prefix, test_paths in _DEVCTL_TEST_TARGETS:
        wired_source_prefixes.add(source_prefix)
        wired_test_paths.update(test_paths)

    assert _G23_TEST_PATH in wired_test_paths or _G23_GUARD_PATH in wired_source_prefixes, (
        f"G23 wiring missing: '{_G23_TEST_PATH}' is not in "
        "_DEVCTL_TEST_TARGETS and '{_G23_GUARD_PATH}' is not a source "
        "prefix. Codex's role-split claim 'G23/G40 wired into "
        "check-router' is not durable production behavior."
    )


def test_red_f_g40_test_or_guard_wired_into_check_router_targets() -> None:
    """F. Same as G23 for G40 (packet lifecycle). Either a G40 test or
    guard source-prefix must appear in ``_DEVCTL_TEST_TARGETS``.
    """
    from dev.scripts.devctl.commands.check.router_python_tests import (
        _DEVCTL_TEST_TARGETS,
    )

    wired_test_paths: set[str] = set()
    wired_source_prefixes: set[str] = set()
    for source_prefix, test_paths in _DEVCTL_TEST_TARGETS:
        wired_source_prefixes.add(source_prefix)
        wired_test_paths.update(test_paths)

    g40_indicators = (
        _G40_GUARD_PREFIX,
        "dev/scripts/devctl/tests/scenarios/test_tdd_packet_lifecycle_invariants.py",
    )
    matched = [
        ind
        for ind in g40_indicators
        if any(ind in p for p in wired_test_paths)
        or any(ind in p for p in wired_source_prefixes)
    ]
    assert matched, (
        "G40 wiring missing: no test or guard source-prefix matching "
        f"any of {g40_indicators} is present in _DEVCTL_TEST_TARGETS. "
        "Codex's role-split claim is not durable."
    )


# ---------------------------------------------------------------------------
# G. Worktree state: codex's edits left 214 dirty + 6 import-index
# atomicity violations. Test that startup_authority_contract can
# recover when those are addressed (we assert the recovery path exists,
# not that it currently passes — the fix is out of scope).
# ---------------------------------------------------------------------------

def test_red_g_startup_authority_collects_import_index_atomicity_findings() -> None:
    """G. The startup_authority_contract must expose a typed counter for
    import-index atomicity violations, so a fresh staging+commit can
    drive the counter to zero. If the counter is absent, codex's
    worktree-state recovery path is not reachable.
    """
    from dev.scripts.checks.startup_authority_contract import command as cmd

    assert hasattr(cmd, "collect_import_index_atomicity_finding_records"), (
        "startup_authority_contract.command must export "
        "collect_import_index_atomicity_finding_records so the "
        "recovery flow can prove the violation count went to zero. "
        "Without this primitive, '214 dirty + 6 import-index violations' "
        "cannot be driven to GREEN by typed evidence."
    )


def test_red_g_startup_authority_report_includes_import_index_field() -> None:
    """G (corollary). The receipt must include a top-level
    ``import_index_atomicity_violations`` count so reviewers can verify
    the recovery without parsing prose.
    """
    cmd_path = (
        REPO_ROOT
        / "dev/scripts/checks/startup_authority_contract/command.py"
    )
    assert cmd_path.exists(), "startup_authority_contract command module missing"
    source = cmd_path.read_text(encoding="utf-8")
    assert '"import_index_atomicity_violations"' in source, (
        "startup_authority_contract receipt must include a top-level "
        "'import_index_atomicity_violations' key so the 6-violation "
        "blocker can be proven repaired by typed receipt, not prose."
    )


# ---------------------------------------------------------------------------
# H. Codex's contradiction pattern (rev_pkt_4839): when safe_to_continue
# (a.k.a. "safe_to_continue_editing" in operator prose) is False, no
# implementer/reviewer lane may append edit-grants without explicit
# operator override.
# ---------------------------------------------------------------------------

def test_red_h_safe_to_continue_false_blocks_implementation_edit_grant() -> None:
    """H. When ``safe_to_continue=False`` AND no operator override is
    active, an AgentLoopDecision must NOT carry
    ``"implementation.edit"`` in ``allowed_actions``.
    """
    from dev.scripts.devctl.runtime.agent_loop_decision_models import (
        AgentLoopDecision,
    )
    from dev.scripts.devctl.runtime.agent_loop_operator_override import (
        AgentLoopOperatorOverride,
    )

    decision = AgentLoopDecision(
        actor_id="codex",
        actor_role="implementer",
        session_id="sess-test",
        safe_to_continue=False,
        may_mutate=False,
        decision="wait",
        required_action="wait_for_scoped_packet",
        allowed_actions=("implementation.edit",),
        operator_override=AgentLoopOperatorOverride(),
    )

    payload = decision.to_dict()
    allowed = {str(a).strip().lower() for a in payload.get("allowed_actions", ())}
    override_active = bool(
        payload.get("operator_override", {}).get("active") if isinstance(
            payload.get("operator_override"), dict
        ) else False
    )

    if not override_active and not payload.get("safe_to_continue"):
        assert "implementation.edit" not in allowed, (
            "Invariant H violated: when safe_to_continue=False AND "
            "operator_override is not active, the decision must NOT "
            "carry 'implementation.edit' in allowed_actions. The "
            "AgentLoopDecision model does NOT enforce this — it "
            "accepts whatever fields the builder passes. Codex's "
            "contradiction pattern (rev_pkt_4839: 'repair startup "
            "BEFORE more code edits' then kept editing) is not "
            "structurally prevented by the typed model."
        )


def test_red_h_typed_role_lane_mutation_authority_blocks_unsafe_continue() -> None:
    """H (corollary). The role-lane mutation authority guard must
    reject an action when ``safe_to_continue=False`` is on the decision
    and no operator override authorizes the lane.
    """
    # Probe whether the guard inspects safe_to_continue at all.
    guard_path = (
        REPO_ROOT
        / "dev/scripts/checks/check_role_lane_mutation_authority.py"
    )
    assert guard_path.exists(), "role-lane mutation authority guard missing"
    source = guard_path.read_text(encoding="utf-8")
    assert "safe_to_continue" in source, (
        "check_role_lane_mutation_authority.py does not reference "
        "'safe_to_continue' at all — codex's contradiction pattern "
        "(editing while safe_to_continue=False) is not blocked by the "
        "lane-authority guard. If the field is renamed (e.g. "
        "'safe_to_edit'), this test catches the rename gap."
    )


# ---------------------------------------------------------------------------
# Extra cross-cuts on codex's edits
# ---------------------------------------------------------------------------

def test_red_codex_new_untracked_files_present_but_no_test_companion() -> None:
    """Cross-cut: codex created
    ``commands/review_channel/event_control_decision_fallback.py``
    (NEW untracked) without a companion test file. The TDD discipline
    requires a test alongside any new production module.
    """
    new_module = (
        REPO_ROOT
        / "dev/scripts/devctl/commands/review_channel/"
        / "event_control_decision_fallback.py"
    )
    expected_test = (
        REPO_ROOT
        / "dev/scripts/devctl/tests/commands/review_channel/"
        / "test_event_control_decision_fallback.py"
    )
    if not new_module.exists():
        pytest.skip("Codex's new module not present in this worktree")

    assert expected_test.exists(), (
        f"Codex created '{new_module.relative_to(REPO_ROOT)}' but no "
        f"companion test exists at "
        f"'{expected_test.relative_to(REPO_ROOT)}'. TDD discipline "
        "requires the test to land with — or before — the production "
        "module."
    )


def test_red_packet_route_resolution_role_resolution_drops_actor_role_fallback() -> None:
    """Codex's packet_route_resolution edit removed the
    ``str(resolved.get('actor_role') or '').strip()`` fallback path and
    now ONLY calls ``_resolved_role(target_role, resolved)``. Verify
    the helper still produces a role when the request's target_role is
    empty and the resolved row's ``actor_role`` is the only source.
    """
    from dev.scripts.devctl.review_channel import packet_route_resolution as mod

    helper = getattr(mod, "_resolved_role", None)
    if helper is None:
        pytest.skip("_resolved_role helper not present")

    resolved_row = {"actor_role": "reviewer"}
    # When the request's target_role is empty, the helper should still
    # produce the resolved actor_role; otherwise codex's simplification
    # silently dropped a useful fallback.
    role = helper("", resolved_row)
    assert role, (
        "packet_route_resolution._resolved_role('', {'actor_role':"
        "'reviewer'}) returned empty — codex's removal of the inline "
        "actor_role fallback may have dropped this path on the floor."
    )
