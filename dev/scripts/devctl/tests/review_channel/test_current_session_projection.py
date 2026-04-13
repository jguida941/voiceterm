"""Focused tests for review-channel current-session projection helpers."""

from __future__ import annotations

from hashlib import sha256
import tempfile
from pathlib import Path

from dev.scripts.devctl.review_channel.current_session_projection import (
    build_bridge_current_session,
    build_event_current_session,
    event_agent_status,
    resolve_current_session_authority,
)
from dev.scripts.devctl.review_channel.current_session_support import (
    prior_typed_current_session,
)
from dev.scripts.devctl.review_channel.event_projection import (
    EventProjectionContext,
    enrich_event_review_state,
)
from dev.scripts.devctl.review_channel.handoff import BridgeSnapshot
from dev.scripts.devctl.review_channel.reviewer_state_normalize import (
    instruction_revision,
)


def test_event_agent_status_prefers_typed_registry_rows() -> None:
    review_state = {
        "registry": {
            "agents": [
                {
                    "agent_id": "claude",
                    "job_state": "active",
                }
            ]
        },
        "_compat": {
            "agents": [
                {
                    "agent_id": "claude",
                    "status": "waiting",
                }
            ]
        },
    }

    assert event_agent_status(review_state, "claude") == "active"


def test_build_event_current_session_uses_registry_without_compat_agents() -> None:
    state = build_event_current_session(
        review_state={
            "review": {"plan_id": "MP-355"},
            "queue": {
                "pending_total": 0,
                "pending_claude": 0,
                "derived_next_instruction": "Fix the producer parity gap.",
            },
            "registry": {
                "agents": [
                    {
                        "agent_id": "claude",
                        "job_state": "active",
                    }
                ]
            },
        },
        bridge_liveness={
            "current_instruction_revision": "abc123def456",
            "claude_ack_revision": "",
            "claude_ack_current": False,
        },
    )

    assert state.current_instruction == "Fix the producer parity gap."
    assert state.implementer_status == "active"
    assert state.implementer_ack == "acknowledged"
    assert state.last_reviewed_scope == "MP-355"


def test_build_event_current_session_preserves_session_hints() -> None:
    state = build_event_current_session(
        review_state={
            "review": {"plan_id": "MP-355"},
            "queue": {
                "pending_total": 0,
                "pending_claude": 0,
                "derived_next_instruction": "Fix the producer parity gap.",
            },
            "registry": {
                "agents": [
                    {
                        "agent_id": "claude",
                        "job_state": "active",
                    }
                ]
            },
        },
        bridge_liveness={
            "current_instruction_revision": "abc123def456",
            "claude_ack_revision": "",
            "claude_ack_current": False,
            "session_state_hints": {
                "claude": {
                    "state": "waiting_for_user_input",
                    "summary": "Claude conductor is waiting for manual input.",
                }
            },
        },
    )

    assert state.implementer_session_state == "waiting_for_user_input"
    assert state.implementer_session_hint == (
        "Claude conductor is waiting for manual input."
    )


def test_build_event_current_session_does_not_promote_findings_to_instruction() -> None:
    state = build_event_current_session(
        review_state={
            "review": {"plan_id": "MP-355"},
            "queue": {
                "pending_total": 1,
                "pending_claude": 0,
                "derived_next_instruction": "",
            },
            "packets": [
                {
                    "packet_id": "rev_pkt_finding",
                    "status": "pending",
                    "summary": "Dashboard dogfood: 6 critical issues",
                    "body": "Finding only.",
                    "kind": "finding",
                    "from_agent": "claude",
                    "to_agent": "codex",
                    "requested_action": "review_only",
                    "expires_at_utc": "2999-01-01T00:00:00Z",
                }
            ],
            "registry": {
                "agents": [
                    {
                        "agent_id": "claude",
                        "job_state": "active",
                    }
                ]
            },
        },
        bridge_liveness={
            "current_instruction_revision": "abc123def456",
            "claude_ack_revision": "",
            "claude_ack_current": False,
        },
    )

    assert state.current_instruction == ""
    assert state.open_findings == "1 pending review packet(s)"


def test_build_event_current_session_preserves_prior_instruction_when_queue_is_empty() -> None:
    state = build_event_current_session(
        review_state={
            "review": {"plan_id": "MP-355"},
            "queue": {
                "pending_total": 0,
                "pending_claude": 0,
                "derived_next_instruction": "",
            },
            "registry": {
                "agents": [
                    {
                        "agent_id": "claude",
                        "job_state": "active",
                    }
                ]
            },
        },
        bridge_liveness={
            "current_instruction_revision": "",
            "claude_ack_revision": "",
            "claude_ack_current": False,
        },
        prior_review_state={
            "current_session": {
                "current_instruction": "Keep the checkpoint lane stable.",
                "current_instruction_revision": "typed-rev-999",
                "implementer_ack": "Acknowledged instruction revision `typed-rev-999`",
                "implementer_ack_revision": "typed-rev-999",
                "implementer_ack_state": "current",
                "open_findings": "none",
                "last_reviewed_scope": "MP-355",
            }
        },
    )

    assert state.current_instruction == "Keep the checkpoint lane stable."
    assert state.current_instruction_revision == "typed-rev-999"
    assert state.implementer_status == "active"


def test_build_event_current_session_canonicalizes_instruction_markdown_revision() -> None:
    raw_instruction = "\n".join(
        [
            "Current-instruction authority now converged; stale Claude Status remains",
            "- Context packet: trigger `review-channel-event`; query terms: `bridge.md`, `review_state.json`",
            "- Canonical refs:",
            "  - `dev/active/loop_chat_bridge.md`",
        ]
    )
    state = build_event_current_session(
        review_state={
            "review": {"plan_id": "MP-355"},
            "queue": {
                "pending_total": 1,
                "pending_claude": 0,
                "derived_next_instruction": raw_instruction,
            },
            "registry": {
                "agents": [
                    {
                        "agent_id": "claude",
                        "job_state": "active",
                    }
                ]
            },
        },
        bridge_liveness={
            "current_instruction_revision": instruction_revision(raw_instruction),
            "claude_ack_revision": "",
            "claude_ack_current": False,
        },
    )

    assert state.current_instruction.startswith("- Current-instruction authority")
    assert state.current_instruction_revision == instruction_revision(
        state.current_instruction
    )


def test_prior_typed_current_session_canonicalizes_instruction_markdown_revision() -> None:
    raw_instruction = "\n".join(
        [
            "Landed: status keeps current instruction revision; commit still blocked on checkpoint/guard lane",
            "- Context packet: trigger `review-channel-event`; query terms: `dev/scripts/devctl.py`, `commit`",
            "- Canonical refs:",
            "  - `dev/scripts/devctl/collect.py`",
            "  - `dev/scripts/devctl/commands/governance/startup_context.py`",
            "  - `dev/scripts/devctl/commands/vcs/governed_executor.py`",
        ]
    )
    session = prior_typed_current_session(
        {
            "current_session": {
                "current_instruction": raw_instruction,
                "current_instruction_revision": instruction_revision(raw_instruction),
            }
        }
    )

    assert session is not None
    assert session.current_instruction.startswith("- Landed:")
    assert session.current_instruction_revision == instruction_revision(
        session.current_instruction
    )


def test_enrich_event_review_state_recovers_bridge_instruction_when_typed_focus_is_blank() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        bridge_path = root / "bridge.md"
        bridge_path.write_text(
            "\n".join(
                [
                    "# Review Bridge",
                    "",
                    "- Last Codex poll: `2026-04-13T00:00:00Z`",
                    "- Current instruction revision: `bridge-rev-123`",
                    "",
                    "## Current Instruction For Claude",
                    "",
                    "- Recover the bridge-backed instruction.",
                    "",
                    "## Claude Status",
                    "",
                    "- waiting for review",
                    "",
                    "## Claude Ack",
                    "",
                    "- acknowledged current instruction revision: bridge-rev-123",
                    "",
                    "## Open Findings",
                    "",
                    "- none",
                    "",
                    "## Last Reviewed Scope",
                    "",
                    "- MP-355",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        review_channel_path = root / "dev/active/review_channel.md"
        review_channel_path.parent.mkdir(parents=True, exist_ok=True)
        review_channel_path.write_text("# Review Channel\n", encoding="utf-8")
        projections_root = root / "dev/reports/review_channel/projections/latest"
        projections_root.mkdir(parents=True, exist_ok=True)

        review_state, _ = enrich_event_review_state(
            review_state={
                "timestamp": "2026-04-13T00:00:00Z",
                "review": {
                    "plan_id": "MP-355",
                    "session_id": "event-backed",
                },
                "queue": {
                    "pending_total": 0,
                    "pending_claude": 0,
                    "pending_codex": 0,
                    "pending_cursor": 0,
                    "pending_operator": 0,
                    "stale_packet_count": 0,
                    "derived_next_instruction": "",
                    "derived_next_instruction_source": {},
                },
                "packets": [],
                "registry": {"agents": []},
                "_compat": {"runtime": {}},
                "warnings": [],
                "errors": [],
            },
            context=EventProjectionContext(
                repo_root=root,
                review_channel_path=review_channel_path,
                projections_root=projections_root,
            ),
        )

    assert (
        review_state["current_session"]["current_instruction"]
        == "- Recover the bridge-backed instruction."
    )
    assert review_state["current_session"]["current_instruction_revision"] == "bridge-rev-123"


def test_bridge_and_event_paths_produce_same_ack_state_when_stale() -> None:
    """Regression: stale_label must be identical across projection paths.

    Before the fix, build_bridge_current_session used stale_label="stale"
    while build_event_current_session used stale_label="unknown". The
    divergence caused _implementer_ack_current in reviewer_runtime_parser
    to fall through to a different code path for the event projection,
    producing a different implementation_blocked result.
    """
    bridge_state = build_bridge_current_session(
        snapshot=BridgeSnapshot(
            metadata={},
            sections={
                "Current Instruction For Claude": "Fix the layout bug.",
                "Claude Status": "working on layout",
                "Claude Questions": "",
                "Claude Ack": "Acknowledged: working on layout",
                "Open Findings": "none",
                "Last Reviewed Scope": "MP-400",
            },
        ),
        bridge_liveness={
            "current_instruction_revision": "rev-abc",
            "claude_ack_revision": "rev-OLD",
            "claude_ack_current": False,
        },
    )

    event_state = build_event_current_session(
        review_state={
            "review": {"plan_id": "MP-400"},
            "queue": {
                "pending_total": 0,
                "pending_claude": 0,
                "derived_next_instruction": "Fix the layout bug.",
            },
            "registry": {
                "agents": [
                    {"agent_id": "claude", "job_state": "working on layout"}
                ]
            },
        },
        bridge_liveness={
            "current_instruction_revision": "rev-abc",
            "claude_ack_revision": "rev-OLD",
            "claude_ack_current": False,
        },
    )

    assert bridge_state.implementer_ack_state == "stale", (
        "bridge path should label a non-current ack as 'stale'"
    )
    assert event_state.implementer_ack_state == "stale", (
        "event path should label a non-current ack as 'stale' (was 'unknown' before fix)"
    )
    assert bridge_state.implementer_ack_state == event_state.implementer_ack_state, (
        "both projection paths must produce the same implementer_ack_state "
        "so that implementation_blocked computes identically"
    )


def test_build_bridge_current_session_rederives_revision_when_instruction_changes() -> None:
    current_instruction = "Implement the repaired reviewer authority slice."
    bridge_state = build_bridge_current_session(
        snapshot=BridgeSnapshot(
            metadata={"current_instruction_revision": "abc123def456"},
            sections={
                "Current Instruction For Claude": current_instruction,
                "Claude Status": "working on the current slice",
                "Claude Questions": "",
                "Claude Ack": "Acknowledged instruction revision `abc123def456`",
                "Open Findings": "none",
                "Last Reviewed Scope": "MP-355",
            },
        ),
        bridge_liveness={
            "current_instruction_revision": "abc123def456",
            "claude_ack_revision": "abc123def456",
            "claude_ack_current": True,
        },
        prior_review_state={
            "current_session": {
                "current_instruction": "Implement the previous slice.",
                "current_instruction_revision": "abc123def456",
            }
        },
    )

    expected_revision = sha256(current_instruction.encode("utf-8")).hexdigest()[:12]

    assert bridge_state.current_instruction_revision == expected_revision
    assert bridge_state.implementer_ack_revision == "abc123def456"
    assert bridge_state.implementer_ack_state == "stale"


def test_resolve_current_session_authority_prefers_live_bridge_checkpoint() -> None:
    resolved = resolve_current_session_authority(
        snapshot=BridgeSnapshot(
            metadata={"current_instruction_revision": "bridge-rev-123"},
            sections={
                "Current Instruction For Claude": "Implement the live bridge checkpoint.",
                "Claude Status": "waiting for review",
                "Claude Questions": "",
                "Claude Ack": "Acknowledged instruction revision `bridge-rev-123`",
                "Open Findings": "- F1: keep reviewer checkpoint visible",
                "Last Reviewed Scope": "MP-355",
            },
        ),
        bridge_liveness={
            "current_instruction_revision": "bridge-rev-123",
            "claude_ack_revision": "bridge-rev-123",
            "claude_ack_current": True,
        },
        prior_review_state={
            "current_session": {
                "current_instruction": "Session launch: Codex, Claude conductors started",
                "current_instruction_revision": "typed-rev-999",
                "implementer_status": "(missing)",
                "implementer_ack": "acknowledged",
                "implementer_ack_revision": "",
                "implementer_ack_state": "stale",
                "implementer_state_hash": "old-hash",
                "open_findings": "1 pending review packet(s)",
                "last_reviewed_scope": "MP-355",
            }
        },
    )

    assert resolved.current_instruction == "Implement the live bridge checkpoint."
    assert resolved.current_instruction_revision == "bridge-rev-123"
    assert resolved.open_findings == "- F1: keep reviewer checkpoint visible"


def test_resolve_current_session_authority_keeps_prior_typed_session_when_bridge_is_overdue() -> None:
    resolved = resolve_current_session_authority(
        snapshot=BridgeSnapshot(
            metadata={"current_instruction_revision": "bridge-rev-123"},
            sections={
                "Current Instruction For Claude": "Implement the stale bridge checkpoint.",
                "Claude Status": "waiting for review",
                "Claude Questions": "",
                "Claude Ack": "Acknowledged instruction revision `bridge-rev-123`",
                "Open Findings": "- stale bridge findings",
                "Last Reviewed Scope": "bridge.md",
            },
        ),
        bridge_liveness={
            "current_instruction_revision": "bridge-rev-123",
            "claude_ack_revision": "bridge-rev-123",
            "claude_ack_current": True,
            "reviewer_freshness": "overdue",
        },
        prior_review_state={
            "current_session": {
                "current_instruction": "Use the newer typed authority instruction.",
                "current_instruction_revision": "typed-rev-999",
                "implementer_status": "- typed status",
                "implementer_ack": "Acknowledged instruction revision `typed-rev-999`",
                "implementer_ack_revision": "typed-rev-999",
                "implementer_ack_state": "current",
                "implementer_state_hash": "typed-hash",
                "open_findings": "- typed findings",
                "last_reviewed_scope": "MP-355",
            }
        },
    )

    assert resolved.current_instruction == "Use the newer typed authority instruction."
    assert resolved.current_instruction_revision == "typed-rev-999"
    assert resolved.open_findings == "- typed findings"


def test_resolve_current_session_authority_recovers_bridge_session_when_prior_is_placeholder() -> None:
    resolved = resolve_current_session_authority(
        snapshot=BridgeSnapshot(
            metadata={"current_instruction_revision": "bridge-rev-123"},
            sections={
                "Current Instruction For Claude": "- Recover the live bridge checkpoint.",
                "Claude Status": "- waiting for review",
                "Claude Questions": "",
                "Claude Ack": "- Acknowledged instruction revision `bridge-rev-123`",
                "Open Findings": "- none",
                "Last Reviewed Scope": "- MP-355",
            },
        ),
        bridge_liveness={
            "current_instruction_revision": "bridge-rev-123",
            "claude_ack_revision": "bridge-rev-123",
            "claude_ack_current": True,
            "reviewer_freshness": "overdue",
        },
        prior_review_state={
            "current_session": {
                "current_instruction": "",
                "current_instruction_revision": "",
                "implementer_status": "",
                "implementer_ack": "acknowledged",
                "implementer_ack_revision": "",
                "implementer_ack_state": "stale",
                "implementer_state_hash": "typed-hash",
                "open_findings": "none",
                "last_reviewed_scope": "MP-355",
            }
        },
    )

    assert resolved.current_instruction == "- Recover the live bridge checkpoint."
    assert resolved.current_instruction_revision == "bridge-rev-123"
