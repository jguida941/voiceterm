"""Tests for the runtime-spine closure guard."""

from __future__ import annotations

from dev.scripts.checks.runtime_spine_closure.support import (
    build_runtime_spine_report,
)


SYSTEM_MAP_TEMPLATE = """# System Map

## 0.6 Canonical Runtime Spine

```
ProjectGovernance \u2705
  \u2514\u2500 PlanExpectationPacket \u274c
      \u2514\u2500 TypedAction \u26a0\ufe0f (record-only)
```

{closure_rule}

{closure_matrix}

## 0.7 Next Section
"""


VALID_MATRIX = """### Runtime Spine Closure Matrix

| Runtime object | Active owner | Typed contract | Producer | Consumer | Regression proof | Graph/context visibility | Carry-forward/compaction path | Priority |
|---|---|---|---|---|---|---|---|---|
| PlanExpectationPacket | `MP377-P0-T01` | `dev/scripts/devctl/runtime/plan_expectation_packet.py` typed contract | `devctl plan compile` producer | `dev/scripts/devctl/runtime/agent_loop_decision.py` consumer | `test_plan_expectation_packet.py` | `context-graph` and `startup-context` | `ContextPack` carry-forward | P0 |
| TypedAction | `MP377-P0-T02` | `dev/scripts/devctl/runtime/typed_action.py` typed contract | `devctl check` producer | `dev/scripts/devctl/runtime/action_result.py` consumer | `check_runtime_spine_closure.py` | `system-map` and `AgentLoopDecision` | `PacketContinuityState` carry-forward | P0 |
"""


def test_runtime_spine_closure_passes_when_risky_items_have_active_owners() -> None:
    report = build_runtime_spine_report(
        system_map_text=SYSTEM_MAP_TEMPLATE.format(
            closure_rule=(
                "**Closure rule:** promote one \u274c/\u26a0\ufe0f per session until "
                "the chain is fully \u2705."
            ),
            closure_matrix=VALID_MATRIX,
        ),
        owner_texts={
            "dev/active/ai_governance_platform.md": (
                "- [ ] MP377-P0-T01 Build PlanExpectationPacket.\n"
                "- [ ] MP377-P0-T02 Wire TypedAction execution contract.\n"
            )
        },
        registered_check_ids=("runtime_spine_closure",),
    )

    assert report["ok"] is True
    assert report["risky_item_count"] == 2
    assert report["closure_matrix_row_count"] == 2


def test_runtime_spine_closure_fails_for_unowned_risky_item() -> None:
    report = build_runtime_spine_report(
        system_map_text=SYSTEM_MAP_TEMPLATE.format(
            closure_rule="**Closure rule:** promote one gap per session.",
            closure_matrix=VALID_MATRIX,
        ),
        owner_texts={"dev/active/ai_governance_platform.md": "TypedAction only\n"},
        registered_check_ids=("runtime_spine_closure",),
    )

    assert report["ok"] is False
    assert any(
        violation.get("component") == "PlanExpectationPacket"
        for violation in report["violations"]
    )


def test_runtime_spine_closure_fails_without_closure_rule() -> None:
    report = build_runtime_spine_report(
        system_map_text=SYSTEM_MAP_TEMPLATE.format(
            closure_rule="",
            closure_matrix=VALID_MATRIX,
        ),
        owner_texts={
            "dev/active/ai_governance_platform.md": (
                "PlanExpectationPacket\nTypedAction\n"
            )
        },
        registered_check_ids=("runtime_spine_closure",),
    )

    assert report["ok"] is False
    assert any(
        violation.get("check") == "runtime_spine_closure_rule_present"
        for violation in report["violations"]
    )


def test_runtime_spine_closure_fails_when_guard_is_unregistered() -> None:
    report = build_runtime_spine_report(
        system_map_text=SYSTEM_MAP_TEMPLATE.format(
            closure_rule="**Closure rule:** promote one gap per session.",
            closure_matrix=VALID_MATRIX,
        ),
        owner_texts={
            "dev/active/ai_governance_platform.md": (
                "PlanExpectationPacket\nTypedAction\n"
            )
        },
        registered_check_ids=(),
    )

    assert report["ok"] is False
    assert any(
        violation.get("check") == "runtime_spine_guard_registered"
        for violation in report["violations"]
    )


def test_runtime_spine_closure_fails_without_matrix() -> None:
    report = build_runtime_spine_report(
        system_map_text=SYSTEM_MAP_TEMPLATE.format(
            closure_rule="**Closure rule:** promote one gap per session.",
            closure_matrix="",
        ),
        owner_texts={"dev/active/ai_governance_platform.md": "PlanExpectationPacket\nTypedAction\n"},
        registered_check_ids=("runtime_spine_closure",),
    )

    assert report["ok"] is False
    assert any(
        violation.get("check") == "runtime_spine_closure_matrix_present"
        for violation in report["violations"]
    )


def test_runtime_spine_closure_fails_for_placeholder_matrix_field() -> None:
    bad_matrix = VALID_MATRIX.replace("`MP377-P0-T01`", "TBD")
    report = build_runtime_spine_report(
        system_map_text=SYSTEM_MAP_TEMPLATE.format(
            closure_rule="**Closure rule:** promote one gap per session.",
            closure_matrix=bad_matrix,
        ),
        owner_texts={"dev/active/ai_governance_platform.md": "PlanExpectationPacket\nTypedAction\n"},
        registered_check_ids=("runtime_spine_closure",),
    )

    assert report["ok"] is False
    assert any(
        violation.get("check") == "runtime_spine_closure_matrix_field_connected"
        and violation.get("field") == "active owner"
        for violation in report["violations"]
    )
