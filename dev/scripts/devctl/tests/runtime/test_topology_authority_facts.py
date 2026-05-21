"""v4.55.3 (rev_pkt_4772) regression tests for `topology_authority_facts`.

Codex's task_started: *legacy topology labels (`single_agent`,
`dual_agent`, `multi_agent_active`, `tools_only`, `active_dual_agent`,
`multiple_agents`) must not grant or block runtime authority.* These
tests assert that the typed-fact helpers honor `role_assignments` as
authority and treat the legacy labels as diagnostic-only.
"""

from __future__ import annotations

from dev.scripts.devctl.runtime.topology_authority_facts import (
    legacy_label_is_authority_evidence_only,
    live_implementer_present,
    live_reviewer_present,
    typed_collaboration_from_review_state,
)


def test_v4553_typed_reviewer_assignment_grants_live_reviewer() -> None:
    collaboration = {
        "role_assignments": [
            {
                "agent_id": "codex",
                "provider": "codex",
                "role_id": "review_agent",
                "live": True,
            }
        ]
    }
    assert live_reviewer_present(collaboration) is True


def test_v4553_typed_implementer_assignment_grants_live_implementer() -> None:
    collaboration = {
        "role_assignments": [
            {
                "agent_id": "claude",
                "provider": "claude",
                "role_id": "coding_agent",
                "live": True,
            }
        ]
    }
    assert live_implementer_present(collaboration) is True


def test_v4553_legacy_label_alone_does_not_grant_live_reviewer() -> None:
    """Core acceptance per rev_pkt_4772: a legacy label alone, without
    any typed `role_assignments`, must NOT grant runtime authority. A
    controller that previously branched on `reviewer_mode ==
    "active_dual_agent"` now gets False.
    """
    for label in (
        "active_dual_agent",
        "dual_agent",
        "single_agent",
        "multi_agent_active",
        "multiple_agents",
        "tools_only",
    ):
        assert live_reviewer_present({}, legacy_label=label) is False, label
        assert live_reviewer_present(None, legacy_label=label) is False, label


def test_v4553_legacy_label_alone_does_not_grant_live_implementer() -> None:
    for label in ("active_dual_agent", "dual_agent", "single_agent"):
        assert live_implementer_present({}, legacy_label=label) is False, label


def test_v4553_dead_assignment_does_not_grant_authority() -> None:
    """`live=False` on a role_assignment must NOT grant presence even if
    the legacy label says otherwise."""
    collaboration = {
        "role_assignments": [
            {
                "agent_id": "codex",
                "provider": "codex",
                "role_id": "review_agent",
                "live": False,
            }
        ]
    }
    assert live_reviewer_present(collaboration, legacy_label="active_dual_agent") is False


def test_v4553_wrong_role_id_not_counted_as_reviewer() -> None:
    """A coding_agent role_assignment is NOT a reviewer."""
    collaboration = {
        "role_assignments": [
            {
                "agent_id": "claude",
                "provider": "claude",
                "role_id": "coding_agent",
                "live": True,
            }
        ]
    }
    assert live_reviewer_present(collaboration) is False


def test_v4553_legacy_label_evidence_only_predicate() -> None:
    """The predicate identifies each legacy label codex specifically
    flagged in rev_pkt_4772 as authority-evidence-only."""
    for label in (
        "single_agent",
        "dual_agent",
        "multi_agent_active",
        "multi_agent_orchestrated",
        "active_dual_agent",
        "multiple_agents",
        "tools_only",
    ):
        assert legacy_label_is_authority_evidence_only(label) is True, label
    # Other strings (typed roles, etc.) are NOT in this set.
    for label in ("reviewer", "implementer", "subagent", "", "unknown"):
        assert legacy_label_is_authority_evidence_only(label) is False, label


def test_v4553_typed_collaboration_extractor_returns_mapping() -> None:
    """Production-builder helper: when `review_state_payload` carries
    `collaboration` as a mapping, the extractor returns it so that
    AutoModeInputs.collaboration can be populated."""
    review_state = {
        "collaboration": {
            "role_assignments": [
                {"agent_id": "codex", "role_id": "review_agent", "live": True}
            ]
        }
    }
    extracted = typed_collaboration_from_review_state(review_state)
    assert extracted is not None
    assert "role_assignments" in extracted


def test_v4553_typed_collaboration_extractor_returns_none_for_missing() -> None:
    """When review_state_payload is None or has no collaboration block,
    the extractor returns None, which preserves the legacy-fallback
    branch in auto_mode (back-compat for callers not yet updated)."""
    assert typed_collaboration_from_review_state(None) is None
    assert typed_collaboration_from_review_state({}) is None
    assert typed_collaboration_from_review_state({"other_key": 1}) is None
    # Non-mapping `collaboration` is rejected — only a mapping shape
    # counts as typed collaboration evidence.
    assert typed_collaboration_from_review_state({"collaboration": []}) is None
    assert typed_collaboration_from_review_state({"collaboration": "single_agent"}) is None


def test_v4553_production_path_legacy_label_alone_blocks_reviewer_alive() -> None:
    """rev_pkt_4775 production-builder regression: a review_state_payload
    that has `collaboration` but with empty `role_assignments` must
    produce `reviewer_alive=False` even when the legacy `reviewer_mode`
    label says "active_dual_agent". This proves the production builder
    path consumes typed facts, not legacy labels.
    """
    from dev.scripts.devctl.runtime.auto_mode import (
        AutoModeInputs,
        resolve_auto_mode_phase,
    )

    review_state_payload = {
        "collaboration": {"role_assignments": []}  # empty typed facts
    }
    typed_collaboration = typed_collaboration_from_review_state(review_state_payload)
    assert typed_collaboration is not None  # mapping shape preserved

    state = resolve_auto_mode_phase(
        AutoModeInputs(
            reviewer_mode="active_dual_agent",  # legacy label says alive
            collaboration=typed_collaboration,  # but typed facts say not
            timestamp_utc="2026-05-21T14:10:00Z",
        )
    )
    assert state.reviewer_alive is False


def test_v4553_composite_guard_legacy_strings_cannot_grant_authority_across_surfaces() -> None:
    """rev_pkt_4776 acceptance: a composite guard test that asserts the
    "direct legacy strings cannot grant mutation/recovery/wake/fanout
    or packet/final-gate ownership" principle across multiple authority
    surfaces via the typed-fact module. Each of the six retired
    legacy labels (`single_agent`, `dual_agent`, `multi_agent_active`,
    `multi_agent_orchestrated`, `active_dual_agent`, `multiple_agents`,
    `tools_only`) must:
      (a) be marked as authority-evidence-only,
      (b) NOT grant `live_reviewer_present` alone (without typed
          role_assignments),
      (c) NOT grant `live_implementer_present` alone.
    """
    legacy_labels = (
        "single_agent",
        "dual_agent",
        "multi_agent_active",
        "multi_agent_orchestrated",
        "active_dual_agent",
        "multiple_agents",
        "tools_only",
    )
    for label in legacy_labels:
        # (a) evidence-only predicate must return True for every retired
        # label
        assert legacy_label_is_authority_evidence_only(label) is True, label

        # (b) legacy label cannot grant reviewer presence alone
        assert live_reviewer_present({}, legacy_label=label) is False, label
        assert live_reviewer_present(None, legacy_label=label) is False, label

        # (c) legacy label cannot grant implementer presence alone
        assert live_implementer_present({}, legacy_label=label) is False, label
        assert live_implementer_present(None, legacy_label=label) is False, label

        # `collaboration` with empty role_assignments must also yield False
        assert live_reviewer_present({"role_assignments": []}, legacy_label=label) is False, label
        assert live_implementer_present({"role_assignments": []}, legacy_label=label) is False, label


def test_v4553_typed_typed_facts_with_concurrent_legacy_label_still_dominate() -> None:
    """When both typed role_assignments and a legacy label are present,
    the typed-fact answer is what determines authority. Legacy is
    diagnostic only.
    """
    collaboration = {
        "role_assignments": [
            {
                "agent_id": "codex",
                "provider": "codex",
                "role_id": "review_agent",
                "live": True,
            }
        ]
    }
    # Typed says reviewer present → authority is True regardless of label.
    assert live_reviewer_present(collaboration, legacy_label="single_agent") is True
    # Typed says nobody → authority is False regardless of "active_dual_agent" label.
    assert live_reviewer_present({}, legacy_label="active_dual_agent") is False
