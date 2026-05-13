"""Tests for governed lifecycle transition metadata."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from dev.scripts.devctl.runtime.governed_transitions import (
    TransitionContract,
    governed_transition,
    load_governed_transitions,
    load_transition_module_rows,
    registered_governed_transitions,
    transition_from_mapping,
)


def test_governed_transition_uses_custom_registry_without_wrapping() -> None:
    registry: list[TransitionContract] = []

    @governed_transition(
        transition_id="test.transition",
        requires=("Input:ready",),
        produces=("Output:done",),
        emits=("EvidenceReceipt",),
        graph_path=("Input", "Output"),
        registry=registry,
    )
    def transition(value: str) -> str:
        return f"done:{value}"

    assert transition("work") == "done:work"
    assert len(registry) == 1

    metadata = registry[0]
    assert metadata.transition_id == "test.transition"
    assert metadata.requires == ("Input:ready",)
    assert metadata.produces == ("Output:done",)
    assert metadata.emits == ("EvidenceReceipt",)
    assert metadata.graph_path == ("Input", "Output")
    assert metadata.owner_module == __name__
    assert metadata.function_name.endswith("transition")
    assert getattr(transition, "__governed_transition__") == metadata


def test_governed_transition_rejects_duplicate_ids() -> None:
    registry: list[TransitionContract] = []

    def transition() -> None:
        return None

    decorator = governed_transition(
        transition_id="test.duplicate",
        requires=("Input:ready",),
        produces=("Output:done",),
        registry=registry,
    )
    decorator(transition)

    with pytest.raises(ValueError, match="duplicate governed transition id"):
        decorator(transition)


def test_transition_manifest_rows_round_trip(tmp_path: Path) -> None:
    manifest = tmp_path / "transition_modules.jsonl"
    manifest.write_text(
        json.dumps(
            {
                "contract_id": "GovernedTransitionModule",
                "module": "dev.scripts.devctl.runtime.bypass_lifecycle_evaluation",
                "required": True,
                "schema_version": 1,
            }
        )
        + "\n",
        encoding="utf-8",
    )

    rows = load_transition_module_rows(manifest)

    assert len(rows) == 1
    assert rows[0].module == "dev.scripts.devctl.runtime.bypass_lifecycle_evaluation"
    assert rows[0].required is True


def test_real_manifest_loads_bypass_lifecycle_transitions() -> None:
    transitions = load_governed_transitions(repo_root=Path.cwd())
    by_id = {transition.transition_id: transition for transition in transitions}

    assert {
        "bypass.evaluate_request",
        "bypass.expire_lifecycle",
        "bypass.grant_lifetime_bypass",
    } <= set(by_id)
    assert by_id["bypass.evaluate_request"].produces == (
        "BypassLifecycle:bypass_active",
        "BypassLifecycle:bypass_denied",
    )
    assert "BypassLifecycle" in by_id["bypass.evaluate_request"].emits
    assert by_id["bypass.expire_lifecycle"].requires == (
        "BypassLifecycle:bypass_active",
    )


def test_transition_contract_round_trips_from_mapping() -> None:
    transition = TransitionContract(
        transition_id="test.round_trip",
        requires=("Input:ready",),
        produces=("Output:done",),
        emits=("EvidenceReceipt",),
        graph_path=("Input", "EvidenceReceipt", "Output"),
        owner_module="tests.transitions",
        function_name="transition",
    )

    parsed = transition_from_mapping(transition.to_dict())

    assert parsed == transition
    assert registered_governed_transitions([transition]) == (transition,)
