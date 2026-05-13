"""Tests for governed lifecycle transition metadata."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from dev.scripts.devctl.runtime.governed_transitions import (
    TransitionContract,
    TransitionStateViolation,
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


@dataclass(frozen=True)
class StateFixture:
    state: str


def _input_state_ref(value: StateFixture) -> str:
    return f"Input:{value.state}"


def _output_state_ref(value: StateFixture) -> str:
    return f"Output:{value.state}"


def test_governed_transition_runtime_enforcement_accepts_legal_states() -> None:
    registry: list[TransitionContract] = []

    @governed_transition(
        transition_id="test.enforced",
        requires=("Input:ready",),
        produces=("Output:done",),
        runtime_enforced=True,
        pre_state_resolver=_input_state_ref,
        post_state_resolver=_output_state_ref,
        registry=registry,
    )
    def transition(value: StateFixture) -> StateFixture:
        return StateFixture(state="done")

    assert transition(StateFixture(state="ready")).state == "done"
    assert registry[0].runtime_enforced is True
    assert getattr(transition, "__governed_transition__") == registry[0]


def test_governed_transition_runtime_enforcement_accepts_any_listed_state() -> None:
    registry: list[TransitionContract] = []

    @governed_transition(
        transition_id="test.enforced_multi_state",
        requires=("Input:ready", "Input:queued"),
        produces=("Output:done", "Output:skipped"),
        runtime_enforced=True,
        pre_state_resolver=_input_state_ref,
        post_state_resolver=_output_state_ref,
        registry=registry,
    )
    def transition(value: StateFixture) -> StateFixture:
        if value.state == "queued":
            return StateFixture(state="skipped")
        return StateFixture(state="done")

    assert transition(StateFixture(state="ready")).state == "done"
    assert transition(StateFixture(state="queued")).state == "skipped"


def test_governed_transition_runtime_enforcement_rejects_bad_pre_state() -> None:
    registry: list[TransitionContract] = []

    @governed_transition(
        transition_id="test.bad_pre",
        requires=("Input:ready",),
        produces=("Output:done",),
        runtime_enforced=True,
        pre_state_resolver=_input_state_ref,
        post_state_resolver=_output_state_ref,
        registry=registry,
    )
    def transition(value: StateFixture) -> StateFixture:
        return StateFixture(state="done")

    with pytest.raises(TransitionStateViolation, match="bad_pre pre_state"):
        transition(StateFixture(state="blocked"))


def test_governed_transition_runtime_enforcement_rejects_bad_post_state() -> None:
    registry: list[TransitionContract] = []

    @governed_transition(
        transition_id="test.bad_post",
        requires=("Input:ready",),
        produces=("Output:done",),
        runtime_enforced=True,
        pre_state_resolver=_input_state_ref,
        post_state_resolver=_output_state_ref,
        registry=registry,
    )
    def transition(value: StateFixture) -> StateFixture:
        return StateFixture(state="stuck")

    with pytest.raises(TransitionStateViolation, match="bad_post post_state"):
        transition(StateFixture(state="ready"))


def test_runtime_enforced_transition_requires_state_resolver() -> None:
    registry: list[TransitionContract] = []

    with pytest.raises(ValueError, match="require at least one state resolver"):

        @governed_transition(
            transition_id="test.no_resolver",
            requires=("Input:ready",),
            produces=("Output:done",),
            runtime_enforced=True,
            registry=registry,
        )
        def transition() -> None:
            return None


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
    assert by_id["bypass.grant_lifetime_bypass"].requires == (
        "BypassReceipt:bypass_receipt_issued",
    )
    assert by_id["bypass.evaluate_request"].runtime_enforced is True
    assert by_id["bypass.expire_lifecycle"].runtime_enforced is True


def test_transition_contract_round_trips_from_mapping() -> None:
    transition = TransitionContract(
        transition_id="test.round_trip",
        requires=("Input:ready",),
        produces=("Output:done",),
        emits=("EvidenceReceipt",),
        graph_path=("Input", "EvidenceReceipt", "Output"),
        runtime_enforced=True,
        owner_module="tests.transitions",
        function_name="transition",
    )

    parsed = transition_from_mapping(transition.to_dict())

    assert parsed == transition
    assert registered_governed_transitions([transition]) == (transition,)
