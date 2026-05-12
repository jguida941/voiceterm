from __future__ import annotations

from dev.scripts.devctl.runtime.role_customization import (
    build_role_creation_action,
    role_creation_action_from_mapping,
    validate_role_creation_action,
)
from dev.scripts.devctl.runtime.role_profile import normalize_tandem_role


def test_custom_role_maps_to_existing_workstream_without_mutating_tandem_role() -> None:
    action = build_role_creation_action(
        role_id="architecture-auditor",
        base_workstream_id="architect",
        display_name="Architecture Auditor",
        instructions=("Audit composability before implementation starts.",),
        guards=("reviewer_response_shape",),
        slash_command_refs=("/role-create", "/role-edit", "/role-guard-add"),
        requested_by="operator",
    )

    assert action.status == "accepted"
    assert normalize_tandem_role("architecture-auditor") is None
    assert action.role.base_workstream_id == "architect"
    assert action.role.base_tandem_role == "reviewer"
    assert action.role.instruction_card_ids == ("architecture_auditor:instruction:1",)
    assert action.role.guard_ids == ("architecture_auditor:guard:1",)
    assert action.instruction_cards[0].rules == (
        "Audit composability before implementation starts.",
    )
    assert action.guards[0].violation_action == "fail_closed"
    assert validate_role_creation_action(action) == ()


def test_role_creation_rejects_provider_specific_command_and_unknown_lane() -> None:
    action = build_role_creation_action(
        role_id="security-reviewer",
        base_workstream_id="not-a-workstream",
        instructions=("Run a security review.",),
        guards=("packet_post",),
        slash_command_refs=("/claude-role-create",),
    )

    assert action.status == "rejected"
    assert "unknown_base_workstream" in action.validation_errors
    assert (
        "provider_specific_slash_command:/claude-role-create"
        in action.validation_errors
    )


def test_role_creation_action_round_trips_from_mapping() -> None:
    original = build_role_creation_action(
        role_id="dogfood tester",
        base_workstream_id="dogfood_tester",
        instructions=("Run the exact check-it command.",),
        guards=("packet_post",),
        slash_command_refs=("/role-create",),
    )

    parsed = role_creation_action_from_mapping(original.to_dict())

    assert parsed.role.role_id == "dogfood_tester"
    assert parsed.role.base_workstream_id == "dogfood_tester"
    assert parsed.instruction_cards[0].role_id == "dogfood_tester"
    assert parsed.guards[0].role_id == "dogfood_tester"
