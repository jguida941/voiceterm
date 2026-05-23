"""Tests for typed relaunch-loop contracts."""

from __future__ import annotations

from dev.scripts.devctl.runtime.relaunch_loop_builder import (
    build_relaunch_trigger,
    build_slice_closure_event,
)
from dev.scripts.devctl.runtime.relaunch_loop_models import (
    RelaunchTriggerInput,
    SliceClosureInput,
)


def test_slice_closure_event_normalizes_actor_and_target() -> None:
    event = build_slice_closure_event(
        SliceClosureInput(
            emitter_actor="claude_implementer",
            plan_ref="MP-377",
            closed_slice_id="slice-a",
            next_slice_id="slice-b",
            next_owner_actor="codex_reviewer",
            next_intent="review",
            evidence_packet_ids=("rev_pkt_2975",),
            emitted_at_utc="2026-05-04T16:40:00Z",
        ),
    )

    assert event.emitter_actor == "claude_implementer"
    assert event.next_slice_target.owner_actor == "codex_reviewer"
    assert event.next_slice_target.evidence_packet_ids == ("rev_pkt_2975",)
    assert event.slice_closure_event_id.startswith("slice_close_")


def test_relaunch_trigger_is_queued_for_cross_actor_slice() -> None:
    event = build_slice_closure_event(
        SliceClosureInput(
            emitter_actor="claude_implementer",
            plan_ref="MP-377",
            closed_slice_id="slice-a",
            next_slice_id="slice-b",
            next_owner_actor="codex_reviewer",
            next_intent="review",
            evidence_packet_ids=("rev_pkt_2975",),
            emitted_at_utc="2026-05-04T16:40:00Z",
        ),
    )

    trigger, quota, reason = build_relaunch_trigger(
        RelaunchTriggerInput(
            event=event,
            queued_at_utc="2026-05-04T16:41:00Z",
        ),
    )

    assert quota is None
    assert reason == "queued"
    assert trigger is not None
    assert trigger.target_actor == "codex_reviewer"
    assert trigger.session_seed_packet_id == "rev_pkt_2975"
    assert trigger.launch_command.role == "reviewer"
    assert "--action launch" in trigger.launch_command.command_preview


def test_relaunch_trigger_skips_same_actor_next_slice() -> None:
    event = build_slice_closure_event(
        SliceClosureInput(
            emitter_actor="codex_reviewer",
            plan_ref="MP-377",
            closed_slice_id="slice-a",
            next_slice_id="slice-b",
            next_owner_actor="codex_reviewer",
            next_intent="continue review",
            emitted_at_utc="2026-05-04T16:40:00Z",
        ),
    )

    trigger, quota, reason = build_relaunch_trigger(RelaunchTriggerInput(event=event))

    assert trigger is None
    assert quota is None
    assert reason == "same_actor_next_slice"


def test_relaunch_loop_preserves_flipped_typed_actor_roles() -> None:
    event = build_slice_closure_event(
        SliceClosureInput(
            emitter_actor="claude_reviewer",
            plan_ref="MP-377",
            closed_slice_id="slice-a",
            next_slice_id="slice-b",
            next_owner_actor="codex_implementer",
            next_intent="implement",
            evidence_packet_ids=("rev_pkt_2975",),
            emitted_at_utc="2026-05-04T16:40:00Z",
        ),
    )

    trigger, quota, reason = build_relaunch_trigger(
        RelaunchTriggerInput(
            event=event,
            queued_at_utc="2026-05-04T16:41:00Z",
        ),
    )

    assert event.emitter_actor == "claude_reviewer"
    assert event.next_slice_target.owner_actor == "codex_implementer"
    assert quota is None
    assert reason == "queued"
    assert trigger is not None
    assert trigger.target_actor == "codex_implementer"
    assert trigger.launch_command.role == "implementer"


def test_relaunch_trigger_deduplicates_parent_and_target() -> None:
    event = build_slice_closure_event(
        SliceClosureInput(
            emitter_actor="claude",
            plan_ref="MP-377",
            closed_slice_id="slice-a",
            next_slice_id="slice-b",
            next_owner_actor="codex",
            next_intent="review",
            emitted_at_utc="2026-05-04T16:40:00Z",
        ),
    )
    first, _, _ = build_relaunch_trigger(
        RelaunchTriggerInput(
            event=event,
            queued_at_utc="2026-05-04T16:41:00Z",
        ),
    )
    assert first is not None

    second, quota, reason = build_relaunch_trigger(
        RelaunchTriggerInput(
            event=event,
            queued_at_utc="2026-05-04T16:42:00Z",
            existing_triggers=(first,),
        ),
    )

    assert second is None
    assert quota is None
    assert reason == "duplicate_trigger"
