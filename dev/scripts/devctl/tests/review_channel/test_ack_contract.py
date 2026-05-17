"""Focused regressions for semantic ACK parsing and typed authority."""

from __future__ import annotations

from types import SimpleNamespace

from dev.scripts.devctl.commands.review_channel.event_ack_freshness_action import (
    run_check_ack_freshness_action,
)
from dev.scripts.devctl.commands.review_channel._bridge_poll import (
    build_bridge_poll_result,
)
from dev.scripts.devctl.commands.review_channel.event_action_support import (
    EventActionContext,
)
from dev.scripts.devctl.review_channel.bridge_projection_state import (
    build_bridge_projection_state,
)
from dev.scripts.devctl.review_channel.bridge_validation import (
    validate_live_bridge_contract,
)
from dev.scripts.devctl.review_channel.current_session_projection import (
    build_bridge_current_session,
)
from dev.scripts.devctl.review_channel.reviewer_state_normalize import (
    instruction_revision,
)
from dev.scripts.devctl.review_channel.ack_contract import (
    extract_implementer_ack_revision,
    packet_ack_is_transport_lifecycle_line,
)
from dev.scripts.devctl.review_channel.ack_freshness_authority import (
    build_implementer_ack_freshness_projection,
)
from dev.scripts.devctl.review_channel.handoff import extract_bridge_snapshot


def _bridge_text(*, claude_ack: str) -> str:
    return "\n".join(
        [
            "# Review Bridge",
            "",
            "## Start-Of-Conversation Rules",
            "",
            "Codex is the reviewer. Claude is the coder.",
            "",
            "- Last Codex poll: `2026-03-29T23:20:00Z`",
            "- Last Codex poll (Local America/New_York): `2026-03-29 19:20:00 EDT`",
            "- Reviewer mode: `active_dual_agent`",
            f"- Last non-audit worktree hash: `{'a' * 64}`",
            "- Current instruction revision: `56bcd5d01510`",
            "",
            "## Protocol",
            "",
            "- Keep this file current-state only.",
            "",
            "## Poll Status",
            "",
            "- active reviewer loop",
            "",
            "## Current Verdict",
            "",
            "- reviewer checkpoint pending",
            "",
            "## Open Findings",
            "",
            "- keep the slice bounded",
            "",
            "## Claude Status",
            "",
            "- editing review-channel authority helpers",
            "",
            "## Claude Questions",
            "",
            "- none",
            "",
            "## Claude Ack",
            "",
            claude_ack,
            "",
            "## Current Instruction For Claude",
            "",
            "- Implement the typed authority slice.",
            "",
            "## Last Reviewed Scope",
            "",
            "- dev/scripts/devctl/review_channel",
            "",
        ]
    )


def test_build_bridge_current_session_accepts_semantic_ack_phrase() -> None:
    snapshot = extract_bridge_snapshot(
        _bridge_text(claude_ack="- Acknowledged instruction revision `56bcd5d01510`")
    )

    current_session = build_bridge_current_session(snapshot, {})

    assert current_session.implementer_ack_revision == "56bcd5d01510"
    assert current_session.implementer_ack_state == "current"


def test_validate_live_bridge_contract_accepts_semantic_ack_phrase() -> None:
    snapshot = extract_bridge_snapshot(
        _bridge_text(claude_ack="- Acknowledged instruction revision `56bcd5d01510`")
    )

    errors = validate_live_bridge_contract(snapshot)

    assert not any("Claude Ack" in error for error in errors)


def test_validate_live_bridge_contract_skips_ack_revision_gate_for_wait_placeholder() -> None:
    snapshot = extract_bridge_snapshot(
        _bridge_text(claude_ack="- acknowledged")
        .replace(
            "- Current instruction revision: `56bcd5d01510`\n",
            "",
        )
        .replace(
            "- Implement the typed authority slice.",
            "- Await reviewer instruction refresh.",
        )
    )

    errors = validate_live_bridge_contract(snapshot)

    assert not any("Current instruction revision" in error for error in errors)
    assert not any("Claude Ack" in error for error in errors)


def test_packet_ack_command_does_not_parse_as_implementer_ack() -> None:
    text = "review-channel --action ack --packet-id rev_pkt_1818 --actor claude"

    assert extract_implementer_ack_revision(text) == ""
    assert "transport lifecycle only" in packet_ack_is_transport_lifecycle_line()


def test_build_bridge_current_session_accepts_implementer_heading_aliases() -> None:
    snapshot = extract_bridge_snapshot(
        _bridge_text(claude_ack="- acknowledged; instruction-rev: `56bcd5d01510`")
        .replace("## Claude Status", "## Implementer Status")
        .replace("## Claude Questions", "## Implementer Questions")
        .replace("## Claude Ack", "## Implementer Ack")
    )

    current_session = build_bridge_current_session(snapshot, {})

    assert current_session.implementer_status == "- editing review-channel authority helpers"
    assert current_session.implementer_ack_revision == "56bcd5d01510"
    assert current_session.implementer_ack_state == "current"


def test_build_bridge_projection_state_prefers_typed_current_session_sections() -> None:
    revision = instruction_revision("- Typed instruction wins.")
    projection_state = build_bridge_projection_state(
        bridge_text=_bridge_text(
            claude_ack="- acknowledged; instruction-rev: `deadbeef1234`"
        ),
        bridge_liveness={"current_instruction_revision": revision},
        current_session={
            "current_instruction": "- Typed instruction wins.",
            "current_instruction_revision": revision,
            "implementer_status": "- Typed status wins.",
            "implementer_ack": f"- Acknowledged instruction revision `{revision}`",
            "implementer_ack_revision": revision,
            "open_findings": "- Typed findings win.",
            "last_reviewed_scope": "- typed/scope.py",
        },
        reviewer_runtime={
            "review_acceptance": {
                "current_verdict": "- Typed verdict wins.",
                "open_findings": "- Typed findings win.",
            }
        },
        bridge_state={"current_instruction_revision": revision},
    )

    assert projection_state.sections["Current Verdict"] == "- Typed verdict wins."
    assert projection_state.sections["Open Findings"] == "- Typed findings win."
    assert projection_state.sections["Implementer Status"] == "- Typed status wins."
    assert (
        projection_state.sections["Implementer Ack"]
        == f"- Acknowledged instruction revision `{revision}`"
    )
    assert (
        projection_state.sections["Current Instruction For Implementer"]
        == "- Typed instruction wins."
    )
    assert projection_state.sections["Last Reviewed Scope"] == "- typed/scope.py"
    assert projection_state.metadata["current_instruction_revision"] == revision


def test_build_bridge_poll_result_prefers_typed_current_session_authority() -> None:
    revision = instruction_revision("- Typed instruction wins.")
    result = build_bridge_poll_result(
        _bridge_text(claude_ack="- acknowledged; instruction-rev: `deadbeef1234`"),
        typed_review_state={
            "current_session": {
                "current_instruction": "- Typed instruction wins.",
                "current_instruction_revision": revision,
                "implementer_ack": f"- Acknowledged instruction revision `{revision}`",
                "implementer_ack_revision": revision,
                "implementer_ack_state": "current",
            },
            "bridge": {
                "claude_ack_current": True,
                "reviewed_hash_current": True,
                "review_needed": False,
            },
        },
    )

    assert result.current_instruction == "- Typed instruction wins."
    assert result.current_instruction_revision == revision
    assert result.claude_ack_revision == revision
    assert result.claude_ack_current is True
    assert result.changed_since_last_ack is False
    assert result.reviewed_hash_current is True
    assert result.review_needed is False


def test_ack_freshness_projection_rejects_bridge_only_current_ack() -> None:
    revision = "c278fb3bb6e3"
    projection = build_implementer_ack_freshness_projection(
        review_state=_review_state(
            revision=revision,
            bridge_ack=f"- acknowledged current instruction revision: `{revision}`",
            typed_ack_state="missing",
        ),
        events=(),
    )

    assert projection["ok"] is False
    assert projection["status"] == "bridge_only_drift"
    assert projection["bridge_visible_ack"]["visible"] is True
    assert projection["typed_ack"]["current"] is False


def test_ack_freshness_projection_accepts_typed_ack_event() -> None:
    revision = "c278fb3bb6e3"
    projection = build_implementer_ack_freshness_projection(
        review_state=_review_state(
            revision=revision,
            bridge_ack=f"- acknowledged current instruction revision: `{revision}`",
        ),
        events=(_implementer_ack_event(revision),),
    )

    assert projection["ok"] is True
    assert projection["status"] == "current"
    assert projection["typed_ack"]["source"] == "implementer_ack_event"


def test_check_ack_freshness_action_sets_exit_code_from_projection() -> None:
    revision = "c278fb3bb6e3"
    args = SimpleNamespace(
        action="check-ack-freshness",
        ack_freshness_mode="on_demand",
    )
    context = EventActionContext(
        args=args,
        repo_root=None,
        review_channel_path=None,
        artifact_paths=None,
        build_event_report_fn=_base_event_report,
    )
    bundle = SimpleNamespace(
        review_state=_review_state(
            revision=revision,
            bridge_ack=f"- acknowledged current instruction revision: `{revision}`",
            typed_ack_state="missing",
        ),
        events=[],
    )

    report, exit_code = run_check_ack_freshness_action(
        context=context,
        bundle=bundle,
    )

    assert exit_code == 1
    assert report["ok"] is False
    assert report["ack_freshness"]["status"] == "bridge_only_drift"


def _review_state(
    *,
    revision: str,
    bridge_ack: str,
    typed_ack_state: str = "current",
) -> dict[str, object]:
    return {
        "current_session": {
            "current_instruction": "- Build typed ACK projection.",
            "current_instruction_revision": revision,
            "implementer_status": "- working",
            "implementer_ack": "",
            "implementer_ack_revision": "",
            "implementer_ack_state": typed_ack_state,
        },
        "_compat": {
            "bridge_projection": {
                "sections": {
                    "Implementer Ack": bridge_ack,
                }
            }
        },
    }


def _implementer_ack_event(revision: str) -> dict[str, object]:
    return {
        "event_id": "rev_evt_1",
        "event_type": "review_channel.implementer_ack",
        "schema_version": 1,
        "source": "review_channel",
        "session_id": "local-review",
        "plan_id": "MP-NEW-P188",
        "project_id": "project-1",
        "timestamp_utc": "2026-05-15T00:00:00Z",
        "idempotency_key": f"review_channel.implementer_ack:revision={revision}",
        "nonce": "abc123",
        "payload": {
            "actor": "claude",
            "actor_role": "implementer",
            "target_role": "implementer",
            "target_session_id": "",
            "current_instruction_revision": revision,
            "acknowledged_at_utc": "2026-05-15T00:00:00Z",
            "notes": "",
            "implementer_ack": (
                f"- acknowledged current instruction revision: `{revision}`"
            ),
        },
    }


def _base_event_report(**_kwargs) -> tuple[dict[str, object], int]:
    return (
        {
            "ok": True,
            "exit_ok": True,
            "exit_code": 0,
            "status": "ok",
            "errors": [],
            "warnings": [],
        },
        0,
    )
