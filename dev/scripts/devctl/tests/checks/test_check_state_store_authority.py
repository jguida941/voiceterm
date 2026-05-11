"""Tests for the governed state-store authority check."""

from __future__ import annotations

from dataclasses import replace

from dev.scripts.checks.check_state_store_authority import (
    evaluate_state_store_authority,
)
from dev.scripts.devctl.platform.schema_migration_spine import (
    durable_schema_policies,
)


def test_state_store_authority_passes_registered_current_policies() -> None:
    coverage, violations = evaluate_state_store_authority()

    assert coverage["ok"] is True
    assert coverage["registered_policy_count"] >= 3
    assert "RemoteControlCollaborationCampaign" in coverage[
        "planned_policy_contract_ids"
    ]
    assert violations == ()


def test_state_store_authority_flags_unresolvable_registered_writer() -> None:
    policies = list(durable_schema_policies())
    registered_index = _first_registered_index(policies)
    policies[registered_index] = replace(
        policies[registered_index],
        store_authority="missing.module:writer",
    )

    coverage, violations = evaluate_state_store_authority(policies=tuple(policies))

    assert coverage["ok"] is False
    assert any(
        violation.rule == "registered-store-writer-unresolvable"
        and violation.contract_id == policies[registered_index].contract_id
        for violation in violations
    )


def test_state_store_authority_flags_writer_without_shared_authority() -> None:
    policies = list(durable_schema_policies())
    registered_index = _first_registered_index(policies)
    policies[registered_index] = replace(
        policies[registered_index],
        store_authority=(
            "dev.scripts.devctl.platform.schema_migration_spine:"
            "durable_schema_policies"
        ),
    )

    coverage, violations = evaluate_state_store_authority(policies=tuple(policies))

    assert coverage["ok"] is False
    assert any(
        violation.rule == "registered-store-writer-not-state-store-backed"
        and violation.contract_id == policies[registered_index].contract_id
        for violation in violations
    )


def _first_registered_index(policies) -> int:
    for index, policy in enumerate(policies):
        if policy.store_authority_status == "registered_advisory":
            return index
    raise AssertionError("expected at least one registered policy")
