"""Focused tests for review-channel current-session projection helpers."""

from __future__ import annotations

from hashlib import sha256
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.review_channel.current_session_projection import (
    build_bridge_current_session,
    build_event_current_session,
    event_agent_status,
    resolve_current_session_authority,
)
from dev.scripts.devctl.review_channel.current_session_authority import (
    prefer_bridge_current_session,
)
from dev.scripts.devctl.review_channel.current_session_queue import (
    queue_instruction_is_dashboard_route,
)
from dev.scripts.devctl.review_channel.current_session_support import (
    current_session_authority_drift_warning,
    prior_typed_current_session,
)
from dev.scripts.devctl.review_channel.event_projection import (
    EventProjectionContext,
    enrich_event_review_state,
)
from dev.scripts.devctl.review_channel.event_projection_assembly import (
    _resolve_current_session as resolve_event_projection_assembly_current_session,
)
from dev.scripts.devctl.review_channel.event_projection_enrichment import (
    EventProjectionContext as EnrichmentProjectionContext,
    resolve_current_session as resolve_event_projection_enrichment_current_session,
)
from dev.scripts.devctl.review_channel.event_projection_current_session import (
    CurrentSessionResolvers,
    resolve_current_session as resolve_event_projection_current_session,
)
from dev.scripts.devctl.review_channel.event_projection_bridge import (
    build_event_bridge_liveness_projection,
)
from dev.scripts.devctl.review_channel.handoff import BridgeSnapshot
from dev.scripts.devctl.review_channel.status_snapshot_authority import (
    _normalize_current_session_from_packet_truth,
)
from dev.scripts.devctl.review_channel.reviewer_state_normalize import (
    instruction_revision,
)
from dev.scripts.devctl.runtime.review_state_models import ReviewCurrentSessionState


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


def test_prefer_bridge_current_session_fails_closed_when_bridge_has_no_authority() -> None:
    prior_session = ReviewCurrentSessionState(
        current_instruction="Keep the checkpoint lane stable.",
        current_instruction_revision="typed-rev-999",
        implementer_status="active",
        implementer_ack="acknowledged",
        implementer_ack_revision="typed-rev-999",
        implementer_ack_state="current",
        implementer_state_hash="state-hash",
        implementer_session_state="active",
        implementer_session_hint="live",
        open_findings="none",
        last_reviewed_scope="MP-355",
    )
    bridge_session = ReviewCurrentSessionState(
        current_instruction="",
        current_instruction_revision="",
        implementer_status="",
        implementer_ack="",
        implementer_ack_revision="",
        implementer_ack_state="missing",
    )

    assert (
        prefer_bridge_current_session(
            prior_session=prior_session,
            bridge_session=bridge_session,
            bridge_liveness={},
        )
        is False
    )


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
    assert state.implementer_ack == ""
    assert state.implementer_ack_state == "missing"
    assert state.last_reviewed_scope == "MP-355"


def test_build_event_current_session_clears_ack_without_live_instruction() -> None:
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
    )

    assert state.current_instruction == ""
    assert state.current_instruction_revision == ""
    assert state.implementer_ack == ""
    assert state.implementer_ack_revision == ""
    assert state.implementer_ack_state == "missing"


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


def test_build_event_current_session_ignores_non_claude_instruction_source() -> None:
    state = build_event_current_session(
        review_state={
            "review": {"plan_id": "MP-355"},
            "queue": {
                "pending_total": 1,
                "pending_claude": 0,
                "derived_next_instruction": "Claude sent Codex a reviewer-only note.",
                "derived_next_instruction_source": {
                    "packet_id": "rev_pkt_0884",
                    "kind": "instruction",
                    "from_agent": "claude",
                    "to_agent": "codex",
                },
            },
            "packets": [
                {
                    "packet_id": "rev_pkt_0884",
                    "status": "pending",
                    "summary": "Claude sent Codex a reviewer-only note.",
                    "body": "review only",
                    "kind": "instruction",
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


def test_build_event_current_session_surfaces_expired_unresolved_packets() -> None:
    state = build_event_current_session(
        review_state={
            "review": {"plan_id": "MP-355"},
            "queue": {
                "pending_total": 0,
                "pending_claude": 0,
                "derived_next_instruction": "",
            },
            "packets": [
                {
                    "packet_id": "rev_pkt_expired",
                    "status": "pending",
                    "summary": "Operator override still needs attention",
                    "body": "Expired unresolved packet.",
                    "kind": "action_request",
                    "from_agent": "operator",
                    "to_agent": "codex",
                    "requested_action": "review_only",
                    "expires_at_utc": "2000-01-01T00:00:00Z",
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
    assert state.open_findings == "1 expired unresolved review packet(s)"


def test_event_bridge_liveness_does_not_mark_none_as_open_findings() -> None:
    payload = build_event_bridge_liveness_projection(
        {
            "timestamp": "2026-04-15T00:00:00Z",
            "queue": {
                "pending_total": 0,
                "pending_claude": 0,
                "derived_next_instruction": "",
            },
            "registry": {"agents": []},
            "_compat": {},
        }
    )

    assert payload["open_findings_present"] is False


def test_event_bridge_liveness_marks_expired_unresolved_open_findings() -> None:
    payload = build_event_bridge_liveness_projection(
        {
            "timestamp": "2026-04-15T00:00:00Z",
            "queue": {
                "pending_total": 0,
                "pending_claude": 0,
                "derived_next_instruction": "",
            },
            "packets": [
                {
                    "packet_id": "rev_pkt_expired",
                    "status": "pending",
                    "summary": "Expired unresolved finding",
                    "body": "Still needs reviewer attention.",
                    "kind": "finding",
                    "from_agent": "claude",
                    "to_agent": "codex",
                    "requested_action": "review_only",
                    "expires_at_utc": "2000-01-01T00:00:00Z",
                }
            ],
            "registry": {"agents": []},
            "_compat": {},
        }
    )

    assert payload["open_findings_present"] is True


def test_event_bridge_liveness_prefers_bridge_reviewer_mode() -> None:
    payload = build_event_bridge_liveness_projection(
        {
            "timestamp": "2026-04-15T00:00:00Z",
            "_compat": {
                "runtime": {
                    "daemons": {
                        "reviewer_supervisor": {"reviewer_mode": "active_dual_agent"},
                    }
                }
            },
        },
        bridge_snapshot=BridgeSnapshot(
            metadata={"reviewer_mode": "single_agent"},
            sections={},
        ),
    )

    assert payload["reviewer_mode"] == "single_agent"


def test_event_bridge_liveness_ignores_stopped_daemon_reviewer_mode() -> None:
    payload = build_event_bridge_liveness_projection(
        {
            "timestamp": "2026-04-15T00:00:00Z",
            "_compat": {
                "runtime": {
                    "daemons": {
                        "publisher": {
                            "running": False,
                            "reviewer_mode": "active_dual_agent",
                        },
                    }
                }
            },
        },
    )

    assert payload["reviewer_mode"] == "tools_only"


def test_current_session_drift_warning_keeps_fresh_bridge_checkpoint_authority() -> None:
    warning = current_session_authority_drift_warning(
        snapshot=BridgeSnapshot(
            metadata={"current_instruction_revision": "freshrev1234"},
            sections={
                "Current Instruction For Claude": "- Fresh reviewer instruction.",
                "Claude Status": "- Status unavailable.",
                "Claude Ack": "- missing",
                "Open Findings": "- none",
                "Last Reviewed Scope": "- MP-355",
            },
        ),
        prior_review_state={
            "current_session": {
                "current_instruction": "",
                "current_instruction_revision": "",
                "implementer_status": "",
                "implementer_ack": "",
                "implementer_ack_revision": "",
                "implementer_ack_state": "missing",
                "open_findings": "stale packet findings",
                "last_reviewed_scope": "old scope",
            }
        },
        bridge_liveness={"reviewer_freshness": "fresh"},
    )

    assert warning == ""


def test_current_session_drift_warning_ignores_generated_idle_placeholders() -> None:
    warning = current_session_authority_drift_warning(
        snapshot=BridgeSnapshot(
            metadata={"current_instruction_revision": ""},
            sections={
                "Current Instruction For Claude": "- Await reviewer instruction refresh.",
                "Claude Status": "- Status unavailable.",
                "Claude Ack": "- missing",
                "Open Findings": "none",
                "Last Reviewed Scope": "MP-355",
            },
        ),
        prior_review_state={
            "current_session": {
                "current_instruction": "",
                "current_instruction_revision": "",
                "implementer_status": "(missing)",
                "implementer_ack": "",
                "implementer_ack_revision": "",
                "implementer_ack_state": "missing",
                "open_findings": "none",
                "last_reviewed_scope": "MP-355",
            }
        },
        bridge_liveness={"reviewer_freshness": "fresh"},
    )

    assert warning == ""


def test_build_event_current_session_clears_prior_instruction_when_queue_is_empty() -> None:
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
    assert state.implementer_ack == ""
    assert state.implementer_ack_revision == ""
    assert state.implementer_ack_state == "missing"
    assert state.implementer_status == "active"


def test_event_projection_current_session_clears_prior_instruction_when_queue_is_empty() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        current_session = resolve_event_projection_current_session(
            review_state={
                "review": {"plan_id": "MP-355"},
                "queue": {
                    "pending_total": 0,
                    "pending_claude": 0,
                    "derived_next_instruction": "",
                },
                "registry": {"agents": []},
            },
            repo_root=root,
            prior_review_state={
                "current_session": {
                    "current_instruction": "Keep the checkpoint lane stable.",
                    "current_instruction_revision": "typed-rev-999",
                    "implementer_ack": (
                        "Acknowledged instruction revision `typed-rev-999`"
                    ),
                    "implementer_ack_revision": "typed-rev-999",
                    "implementer_ack_state": "current",
                }
            },
            bridge_liveness={
                "current_instruction_revision": "",
                "claude_ack_revision": "",
                "claude_ack_current": False,
            },
            resolvers=CurrentSessionResolvers(
                build_event_current_session_fn=build_event_current_session,
            ),
        )

    assert current_session.current_instruction == "Keep the checkpoint lane stable."
    assert current_session.current_instruction_revision == "typed-rev-999"


def test_build_event_current_session_clears_prior_instruction_when_packets_still_need_attention() -> None:
    state = build_event_current_session(
        review_state={
            "review": {"plan_id": "MP-355"},
            "queue": {
                "pending_total": 0,
                "pending_claude": 0,
                "derived_next_instruction": "",
            },
            "packets": [
                {
                    "packet_id": "rev_pkt_expired",
                    "status": "pending",
                    "summary": "Old action request still needs review",
                    "body": "Expired unresolved packet.",
                    "kind": "action_request",
                    "from_agent": "operator",
                    "to_agent": "codex",
                    "requested_action": "review_only",
                    "expires_at_utc": "2000-01-01T00:00:00Z",
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

    assert state.current_instruction == ""
    assert state.current_instruction_revision == ""
    assert state.open_findings == "1 expired unresolved review packet(s)"


def test_event_projection_does_not_fall_back_to_bridge_instruction_when_packet_findings_exist() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        bridge_path = root / "bridge.md"
        bridge_path.write_text(
            "\n".join(
                [
                    "# Review Channel",
                    "",
                    "## Current Instruction For Claude",
                    "",
                    "- stale bridge instruction",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        current_session = resolve_event_projection_current_session(
            review_state={
                "review": {"plan_id": "MP-355"},
                "queue": {
                    "pending_total": 0,
                    "pending_claude": 0,
                    "derived_next_instruction": "",
                },
                "packets": [
                    {
                        "packet_id": "rev_pkt_expired",
                        "status": "pending",
                        "summary": "Expired unresolved packet",
                        "body": "Still needs reviewer attention.",
                        "kind": "action_request",
                        "from_agent": "operator",
                        "to_agent": "codex",
                        "requested_action": "review_only",
                        "expires_at_utc": "2000-01-01T00:00:00Z",
                    }
                ],
                "registry": {"agents": []},
            },
            repo_root=root,
            prior_review_state={
                "current_session": {
                    "current_instruction": "Keep the checkpoint lane stable.",
                    "current_instruction_revision": "typed-rev-999",
                    "open_findings": "none",
                }
            },
            bridge_liveness={
                "current_instruction_revision": "",
                "claude_ack_revision": "",
                "claude_ack_current": False,
            },
            resolvers=CurrentSessionResolvers(
                build_event_current_session_fn=build_event_current_session,
                build_bridge_current_session_fn=build_bridge_current_session,
            ),
        )

    assert current_session.current_instruction == ""
    assert current_session.open_findings == "1 expired unresolved review packet(s)"


def test_event_projection_uses_persisted_packet_inbox_when_live_packets_are_partial() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        bridge_path = root / "bridge.md"
        bridge_path.write_text(
            "\n".join(
                [
                    "# Review Channel",
                    "",
                    "## Current Instruction For Claude",
                    "",
                    "- Await reviewer instruction refresh.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        current_session = resolve_event_projection_current_session(
            review_state={
                "review": {"plan_id": "MP-355"},
                "queue": {
                    "pending_total": 1,
                    "pending_claude": 1,
                    "derived_next_instruction": (
                        "Priority action_request: Dogfood split-authority "
                        "current-slice contradiction"
                    ),
                    "derived_next_instruction_source": {
                        "packet_id": "rev_pkt_0523",
                        "kind": "action_request",
                        "from_agent": "codex",
                        "to_agent": "claude",
                    },
                },
                "packets": [
                    {
                        "packet_id": "rev_pkt_0523",
                        "status": "pending",
                        "summary": "Dogfood split-authority current-slice contradiction",
                        "body": "Verify the shared current-slice contradiction.",
                        "kind": "action_request",
                        "from_agent": "codex",
                        "to_agent": "claude",
                        "requested_action": "review_only",
                        "expires_at_utc": "2999-01-01T00:00:00Z",
                    }
                ],
                "packet_inbox": {
                    "attention_revision": "packet-attention-rev",
                    "agents": [
                        {
                            "agent": "codex",
                            "current_instruction_packet_id": "",
                            "latest_finding_packet_id": "rev_pkt_0522",
                            "pending_actionable_packet_ids": [],
                            "expired_unresolved_packet_ids": ["rev_pkt_0502"],
                            "attention_status": "review_needed",
                            "wake_reason": "expired_unresolved_packet",
                            "required_command": (
                                "python3 dev/scripts/devctl.py review-channel "
                                "--action inbox --target codex --status pending --terminal none --format md"
                            ),
                            "attention_revision": "codex-attention-rev",
                            "delivery_state": "unseen",
                        },
                        {
                            "agent": "claude",
                            "current_instruction_packet_id": "rev_pkt_0523",
                            "latest_finding_packet_id": "rev_pkt_0517",
                            "pending_actionable_packet_ids": ["rev_pkt_0523"],
                            "expired_unresolved_packet_ids": [],
                            "attention_status": "wake_required",
                            "wake_reason": "action_request_pending",
                            "required_command": (
                                "python3 dev/scripts/devctl.py review-channel "
                                "--action inbox --target claude --status pending --terminal none --format md"
                            ),
                            "attention_revision": "claude-attention-rev",
                            "delivery_state": "notified",
                        },
                    ],
                },
                "registry": {"agents": []},
            },
            repo_root=root,
            prior_review_state={
                "current_session": {
                    "current_instruction": "- stale typed instruction",
                    "current_instruction_revision": "typed-rev-999",
                    "open_findings": "none",
                }
            },
            bridge_liveness={
                "current_instruction_revision": "",
                "claude_ack_revision": "",
                "claude_ack_current": False,
            },
            resolvers=CurrentSessionResolvers(
                build_event_current_session_fn=build_event_current_session,
                build_bridge_current_session_fn=build_bridge_current_session,
            ),
        )

    assert current_session.current_instruction == (
        "Priority action_request: Dogfood split-authority "
        "current-slice contradiction"
    )
    assert current_session.open_findings == (
        "1 pending review packet(s); 1 expired unresolved review packet(s)"
    )


def test_event_projection_current_session_does_not_fallback_to_bridge_instruction_when_blank() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "bridge.md").write_text(
            "\n".join(
                [
                    "# Review Channel",
                    "",
                    "## Current Instruction For Claude",
                    "",
                    "- stale bridge instruction",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        current_session = resolve_event_projection_current_session(
            review_state={
                "review": {"plan_id": "MP-355"},
                "queue": {
                    "pending_total": 0,
                    "pending_claude": 0,
                    "derived_next_instruction": "",
                },
                "registry": {"agents": []},
            },
            repo_root=root,
            prior_review_state={"current_session": {}},
            bridge_liveness={
                "current_instruction_revision": "",
                "claude_ack_revision": "",
                "claude_ack_current": False,
            },
            resolvers=CurrentSessionResolvers(
                build_event_current_session_fn=build_event_current_session,
            ),
        )

    assert current_session.current_instruction == ""


def test_event_projection_enrichment_does_not_fallback_to_bridge_instruction_when_blank() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "bridge.md").write_text(
            "\n".join(
                [
                    "# Review Channel",
                    "",
                    "## Current Instruction For Claude",
                    "",
                    "- stale bridge instruction",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        current_session = resolve_event_projection_enrichment_current_session(
            review_state={
                "review": {"plan_id": "MP-355"},
                "queue": {
                    "pending_total": 0,
                    "pending_claude": 0,
                    "derived_next_instruction": "",
                },
                "registry": {"agents": []},
            },
            context=EnrichmentProjectionContext(
                repo_root=root,
                review_channel_path=root / "dev/active/review_channel.md",
                projections_root=root / "dev/reports/review_channel/projections/latest",
            ),
            bridge_liveness={
                "current_instruction_revision": "",
                "claude_ack_revision": "",
                "claude_ack_current": False,
            },
        )

    assert current_session.current_instruction == ""


def test_event_projection_assembly_does_not_fallback_to_bridge_instruction_when_blank() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "bridge.md").write_text(
            "\n".join(
                [
                    "# Review Channel",
                    "",
                    "## Current Instruction For Claude",
                    "",
                    "- stale bridge instruction",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        current_session = resolve_event_projection_assembly_current_session(
            {
                "review": {"plan_id": "MP-355"},
                "queue": {
                    "pending_total": 0,
                    "pending_claude": 0,
                    "derived_next_instruction": "",
                },
                "registry": {"agents": []},
            },
            SimpleNamespace(prior_review_state={"current_session": {}}, repo_root=root),
            {
                "current_instruction_revision": "",
                "claude_ack_revision": "",
                "claude_ack_current": False,
            },
            SimpleNamespace(
                build_event_current_session=build_event_current_session,
            ),
        )

    assert current_session.current_instruction == ""


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
                "derived_next_instruction_source": {
                    "packet_id": "rev_pkt_0420",
                    "kind": "instruction",
                    "from_agent": "codex",
                    "to_agent": "claude",
                },
            },
            "packets": [
                {
                    "packet_id": "rev_pkt_0420",
                    "status": "pending",
                    "summary": "Current-instruction authority now converged",
                    "body": raw_instruction,
                    "kind": "instruction",
                    "from_agent": "codex",
                    "to_agent": "claude",
                    "requested_action": "continue",
                    "expires_at_utc": "2999-01-01T00:00:00Z",
                }
            ],
            "packet_inbox": {
                "agents": [
                    {
                        "agent": "claude",
                        "current_instruction_packet_id": "rev_pkt_0420",
                        "pending_actionable_packet_ids": ["rev_pkt_0420"],
                        "expired_unresolved_packet_ids": [],
                        "attention_status": "review_needed",
                        "wake_reason": "pending_instruction",
                        "required_command": "",
                        "attention_revision": "codex-attention-rev",
                        "delivery_state": "unseen",
                    }
                ]
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


@patch(
    "dev.scripts.devctl.review_channel.event_projection.attach_conductor_session_state",
)
def test_enrich_event_review_state_does_not_recover_bridge_instruction_when_typed_focus_is_blank(
    _attach_conductor_session_state_mock,
) -> None:
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

    assert review_state["current_session"]["current_instruction"] == ""
    assert review_state["current_session"]["current_instruction_revision"] == ""


def test_event_path_does_not_synthesize_ack_from_empty_packet_queue() -> None:
    """Packet queue emptiness is not the implementer ACK contract."""
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
    assert event_state.implementer_ack == "", (
        "event path must not synthesize `acknowledged` from pending_total=0"
    )
    assert event_state.implementer_ack_state == "missing", (
        "packet lifecycle state alone must not satisfy implementer ACK"
    )


def test_acked_action_request_keeps_instruction_without_implementer_ack() -> None:
    state = build_event_current_session(
        review_state={
            "review": {"plan_id": "MP-400"},
            "queue": {
                "pending_total": 0,
                "pending_claude": 0,
                "derived_next_instruction": (
                    "Priority action_request: Run governed checkpoint"
                ),
                "derived_next_instruction_source": {
                    "packet_id": "rev_pkt_1818",
                    "packet_class": "action_request",
                    "control_state": "in_progress",
                    "to_agent": "claude",
                },
            },
            "registry": {
                "agents": [
                    {"agent_id": "claude", "job_state": "running checkpoint"}
                ]
            },
        },
        bridge_liveness={
            "current_instruction_revision": "",
            "claude_ack_revision": "",
            "claude_ack_current": False,
        },
    )

    assert state.current_instruction == (
        "Priority action_request: Run governed checkpoint"
    )
    assert state.current_instruction_revision
    assert state.implementer_ack == ""
    assert state.implementer_ack_revision == ""
    assert state.implementer_ack_state == "missing"


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


def test_build_event_current_session_clears_revision_when_instruction_missing() -> None:
    state = build_event_current_session(
        review_state={
            "review": {"plan_id": "MP-400"},
            "queue": {
                "pending_total": 0,
                "pending_claude": 0,
                "derived_next_instruction": "",
            },
            "registry": {"agents": []},
        },
        bridge_liveness={
            "current_instruction_revision": "rev-abc",
            "claude_ack_revision": "rev-abc",
            "claude_ack_current": False,
        },
    )

    assert state.current_instruction == ""
    assert state.current_instruction_revision == ""


def test_build_bridge_current_session_clears_revision_when_instruction_missing() -> None:
    state = build_bridge_current_session(
        snapshot=BridgeSnapshot(
            metadata={"current_instruction_revision": "rev-abc"},
            sections={
                "Current Instruction For Claude": "",
                "Claude Status": "",
                "Claude Questions": "",
                "Claude Ack": "",
                "Open Findings": "none",
                "Last Reviewed Scope": "MP-400",
            },
        ),
        bridge_liveness={
            "current_instruction_revision": "rev-abc",
            "claude_ack_revision": "",
            "claude_ack_current": False,
        },
    )

    assert state.current_instruction == "(missing)"
    assert state.current_instruction_revision == ""


def test_build_bridge_current_session_clears_ack_for_refresh_placeholder() -> None:
    state = build_bridge_current_session(
        snapshot=BridgeSnapshot(
            metadata={"current_instruction_revision": "rev-abc"},
            sections={
                "Current Instruction For Claude": "- Await reviewer instruction refresh.",
                "Claude Status": "working",
                "Claude Questions": "",
                "Claude Ack": "Acknowledged instruction revision `rev-abc`",
                "Open Findings": "none",
                "Last Reviewed Scope": "MP-400",
            },
        ),
        bridge_liveness={
            "current_instruction_revision": "rev-abc",
            "claude_ack_revision": "rev-abc",
            "claude_ack_current": True,
        },
    )

    assert state.current_instruction == "- Await reviewer instruction refresh."
    assert state.current_instruction_revision == ""
    assert state.implementer_ack == ""
    assert state.implementer_ack_revision == ""
    assert state.implementer_ack_state == "missing"


def test_normalize_current_session_from_packet_truth_clears_missing_instruction_ack() -> None:
    normalized = _normalize_current_session_from_packet_truth(
        current_session=ReviewCurrentSessionState(
            current_instruction="- Await reviewer instruction refresh.",
            current_instruction_revision="rev-abc",
            implementer_status="working",
            implementer_ack="acknowledged",
            implementer_ack_revision="rev-abc",
            implementer_ack_state="stale",
            implementer_state_hash="stale-hash",
            implementer_session_state="",
            implementer_session_hint="",
            open_findings="none",
            last_reviewed_scope="MP-400",
        ),
        review_state={
            "collaboration": {
                "coding_agent": "claude",
            },
            "packet_inbox": {
                "agents": [
                    {
                        "agent": "claude",
                        "current_instruction_packet_id": "",
                        "pending_actionable_packet_ids": [],
                        "expired_unresolved_packet_ids": [],
                        "wake_reason": "",
                    }
                ]
            }
        },
    )

    assert normalized.current_instruction == ""
    assert normalized.current_instruction_revision == ""
    assert normalized.implementer_ack == ""
    assert normalized.implementer_ack_revision == ""
    assert normalized.implementer_ack_state == "missing"


def test_normalize_current_session_from_packet_truth_preserves_checkpoint_instruction() -> None:
    normalized = _normalize_current_session_from_packet_truth(
        current_session=ReviewCurrentSessionState(
            current_instruction="- Cut a checkpoint before continuing to edit.",
            current_instruction_revision="rev-checkpoint",
            implementer_status="working",
            implementer_ack="acknowledged",
            implementer_ack_revision="rev-checkpoint",
            implementer_ack_state="stale",
            implementer_state_hash="state-hash",
            implementer_session_state="",
            implementer_session_hint="",
            open_findings="none",
            last_reviewed_scope="MP-400",
        ),
        review_state={
            "attention": {"status": "checkpoint_required"},
            "collaboration": {
                "coding_agent": "claude",
            },
            "packet_inbox": {
                "agents": [
                    {
                        "agent": "claude",
                        "current_instruction_packet_id": "",
                        "pending_actionable_packet_ids": [],
                        "expired_unresolved_packet_ids": [],
                        "wake_reason": "",
                    }
                ]
            },
        },
    )

    assert normalized.current_instruction == (
        "- Cut a checkpoint before continuing to edit."
    )
    assert normalized.current_instruction_revision == "rev-checkpoint"
    assert normalized.implementer_ack == "acknowledged"
    assert normalized.implementer_ack_revision == "rev-checkpoint"
    assert normalized.implementer_ack_state == "stale"


def test_build_event_current_session_uses_nondefault_coding_provider_for_instruction_packet_truth() -> None:
    state = build_event_current_session(
        review_state={
            "collaboration": {
                "coding_agent": "cursor",
            },
            "review": {"plan_id": "MP-355"},
            "queue": {
                "pending_total": 1,
                "pending_cursor": 1,
                "derived_next_instruction": "Cursor owns this active instruction.",
                "derived_next_instruction_source": {
                    "packet_id": "rev_pkt_cursor_1",
                    "kind": "instruction",
                    "from_agent": "codex",
                    "to_agent": "cursor",
                },
            },
            "packets": [
                {
                    "packet_id": "rev_pkt_cursor_1",
                    "status": "pending",
                    "summary": "Cursor takes the active slice",
                    "body": "Cursor owns this active instruction.",
                    "kind": "instruction",
                    "from_agent": "codex",
                    "to_agent": "cursor",
                    "requested_action": "continue",
                    "expires_at_utc": "2999-01-01T00:00:00Z",
                }
            ],
            "packet_inbox": {
                "agents": [
                    {
                        "agent": "cursor",
                        "current_instruction_packet_id": "rev_pkt_cursor_1",
                        "pending_actionable_packet_ids": ["rev_pkt_cursor_1"],
                        "expired_unresolved_packet_ids": [],
                        "attention_status": "wake_required",
                        "wake_reason": "instruction_pending",
                        "required_command": "",
                        "attention_revision": "cursor-attention-rev",
                        "delivery_state": "unseen",
                    }
                ]
            },
            "registry": {
                "agents": [
                    {
                        "agent_id": "cursor",
                        "job_state": "active",
                    }
                ]
            },
        },
        bridge_liveness={
            "current_instruction_revision": "rev-cursor-1",
            "implementer_ack_revision": "",
            "implementer_ack_current": False,
        },
    )

    assert state.current_instruction == "Cursor owns this active instruction."
    assert state.implementer_status == "active"


def test_normalize_current_session_from_packet_truth_uses_nondefault_coding_provider() -> None:
    normalized = _normalize_current_session_from_packet_truth(
        current_session=ReviewCurrentSessionState(
            current_instruction="Cursor owns this active instruction.",
            current_instruction_revision="rev-cursor-1",
            implementer_status="working",
            implementer_ack="acknowledged",
            implementer_ack_revision="rev-cursor-1",
            implementer_ack_state="current",
            implementer_state_hash="state-hash",
            implementer_session_state="",
            implementer_session_hint="",
            open_findings="none",
            last_reviewed_scope="MP-355",
        ),
        review_state={
            "collaboration": {
                "coding_agent": "cursor",
            },
            "queue": {
                "derived_next_instruction": "Cursor owns this active instruction.",
                "derived_next_instruction_source": {
                    "packet_id": "rev_pkt_cursor_1",
                    "kind": "instruction",
                    "to_agent": "cursor",
                },
            },
            "packet_inbox": {
                "agents": [
                    {
                        "agent": "cursor",
                        "current_instruction_packet_id": "",
                        "pending_actionable_packet_ids": [],
                        "expired_unresolved_packet_ids": [],
                        "wake_reason": "",
                    }
                ]
            },
        },
    )

    assert normalized.current_instruction == ""
    assert normalized.current_instruction_revision == ""
    assert normalized.implementer_ack == ""
    assert normalized.implementer_ack_state == "missing"


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


def test_resolve_current_session_authority_prefers_active_packet_instruction_over_blank_prior() -> None:
    resolved = resolve_current_session_authority(
        snapshot=BridgeSnapshot(
            metadata={},
            sections={
                "Current Instruction For Claude": "- Await reviewer instruction refresh.",
                "Claude Status": "",
                "Claude Questions": "",
                "Claude Ack": "",
                "Open Findings": "1 pending review packet(s)",
                "Last Reviewed Scope": "MP-355",
            },
        ),
        bridge_liveness={
            "current_instruction_revision": "",
            "claude_ack_revision": "",
            "claude_ack_current": False,
            "reviewer_freshness": "stale",
        },
        prior_review_state={
            "review": {"plan_id": "MP-355"},
            "queue": {
                "pending_total": 0,
                "pending_claude": 0,
                "derived_next_instruction": (
                    "Priority action_request: Run governed checkpoint"
                ),
                "derived_next_instruction_source": {
                    "packet_id": "rev_pkt_1818",
                    "packet_class": "action_request",
                    "control_state": "in_progress",
                    "to_agent": "claude",
                },
            },
            "registry": {
                "agents": [
                    {"agent_id": "claude", "job_state": "running checkpoint"}
                ]
            },
            "current_session": {
                "current_instruction": "",
                "current_instruction_revision": "",
                "implementer_status": "(missing)",
                "implementer_ack": "",
                "implementer_ack_revision": "",
                "implementer_ack_state": "missing",
                "open_findings": "1 pending review packet(s)",
                "last_reviewed_scope": "MP-355",
            },
        },
    )

    assert resolved.current_instruction == (
        "Priority action_request: Run governed checkpoint"
    )
    assert resolved.current_instruction_revision
    assert resolved.implementer_ack_state == "missing"


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


def test_resolve_current_session_authority_ignores_bridge_wait_placeholder() -> None:
    resolved = resolve_current_session_authority(
        snapshot=BridgeSnapshot(
            metadata={"current_instruction_revision": "bridge-rev-123"},
            sections={
                "Current Instruction For Claude": "- Await reviewer instruction refresh.",
                "Claude Status": "- waiting for review",
                "Claude Questions": "",
                "Claude Ack": "- pending",
                "Open Findings": "193 expired unresolved review packet(s)",
                "Last Reviewed Scope": "- MP-355",
            },
        ),
        bridge_liveness={
            "current_instruction_revision": "bridge-rev-123",
            "claude_ack_revision": "",
            "claude_ack_current": False,
            "reviewer_freshness": "fresh",
        },
        prior_review_state={
            "current_session": {
                "current_instruction": "",
                "current_instruction_revision": "",
                "implementer_status": "- Status unavailable.",
                "implementer_ack": "pending",
                "implementer_ack_revision": "",
                "implementer_ack_state": "missing",
                "implementer_state_hash": "typed-hash",
                "open_findings": "193 expired unresolved review packet(s)",
                "last_reviewed_scope": "MP-355",
            }
        },
    )

    assert resolved.current_instruction in {"", "(missing)"}
    assert resolved.current_instruction_revision == ""
    assert resolved.open_findings == "193 expired unresolved review packet(s)"


def test_build_event_current_session_preserves_reviewer_checkpoint_revision_when_packet_attention_clears() -> None:
    """rev_pkt_2922 Finding Y regression guard.

    When packet attention requires clearing the current-session instruction,
    a live reviewer_checkpoint payload's instruction/revision must be
    preserved. Without this, reviewer-checkpoint writes are wiped by the
    subsequent packet-attention clear and `check_review_channel_bridge.py`
    fails because typed current-session instruction revision is missing.
    """
    review_state = {
        "latest_reviewer_checkpoint": {
            "current_instruction": "Codex: address rev_pkt_2922.",
            "current_instruction_revision": "abc1234567ef",
            "open_findings": "",
            "reviewer_mode": "single_agent",
            "worktree_hash": "",
            "reviewer_actor": "codex",
            "reason": "operator-manual-override",
            "event_id": "rev_evt_99999",
            "timestamp": "2026-05-03T22:00:00Z",
        },
        # Packet inbox triggers the clear-from-packet-truth path because no
        # current_instruction_packet_id is set.
        "packet_inbox": {
            "agents": [
                {
                    "agent": "claude",
                    "current_instruction_packet_id": "",
                }
            ],
        },
        "packets": [],
    }
    bridge_liveness = {
        "current_instruction_revision": "",
    }

    resolved = build_event_current_session(
        review_state=review_state,
        bridge_liveness=bridge_liveness,
    )

    # The reviewer_checkpoint instruction/revision MUST be preserved even
    # though packet attention says clear. This is the bug Finding Y named.
    assert resolved.current_instruction == "Codex: address rev_pkt_2922."
    assert resolved.current_instruction_revision == "abc1234567ef"


def test_build_event_current_session_does_not_restore_checkpoint_after_newer_terminal_instruction_packet() -> None:
    review_state = {
        "latest_reviewer_checkpoint": {
            "current_instruction": "Codex: read rev_pkt_2922 + rev_pkt_2923.",
            "current_instruction_revision": "old-checkpoint-rev",
            "event_id": "rev_evt_checkpoint",
            "timestamp_utc": "2026-05-03T22:44:34Z",
        },
        "packet_inbox": {
            "agents": [
                {
                    "agent": "claude",
                    "current_instruction_packet_id": "",
                }
            ],
        },
        "packets": [
            {
                "packet_id": "rev_pkt_3110",
                "kind": "instruction",
                "status": "applied",
                "lifecycle_current_state": "applied",
                "to_agent": "codex",
                "target_role": "dashboard",
                "posted_at": "2026-05-06T17:20:00Z",
            }
        ],
    }

    resolved = build_event_current_session(
        review_state=review_state,
        bridge_liveness={"current_instruction_revision": ""},
    )

    assert resolved.current_instruction == ""
    assert resolved.current_instruction_revision == ""


def test_resolve_current_session_authority_does_not_restore_bridge_after_newer_terminal_instruction_packet() -> None:
    review_state = {
        "current_session": {
            "current_instruction": "Codex: read rev_pkt_2922 + rev_pkt_2923.",
            "current_instruction_revision": "old-checkpoint-rev",
            "implementer_status": "",
            "implementer_ack": "",
            "implementer_ack_revision": "",
            "implementer_ack_state": "missing",
            "implementer_state_hash": "",
            "open_findings": "725 expired unresolved review packet(s)",
            "last_reviewed_scope": "MP-377",
        },
        "latest_reviewer_checkpoint": {
            "current_instruction": "Codex: read rev_pkt_2922 + rev_pkt_2923.",
            "current_instruction_revision": "old-checkpoint-rev",
            "event_id": "rev_evt_checkpoint",
            "timestamp_utc": "2026-05-03T22:44:34Z",
        },
        "packet_inbox": {
            "agents": [
                {
                    "agent": "claude",
                    "current_instruction_packet_id": "",
                }
            ],
        },
        "packets": [
            {
                "packet_id": "rev_pkt_3110",
                "kind": "instruction",
                "status": "applied",
                "lifecycle_current_state": "applied",
                "to_agent": "codex",
                "target_role": "dashboard",
                "posted_at": "2026-05-06T17:20:00Z",
            }
        ],
    }
    snapshot = BridgeSnapshot(
        metadata={},
        sections={
            "Current Instruction For Claude": (
                "Codex: read rev_pkt_2922 + rev_pkt_2923."
            ),
            "Open Findings": "725 expired unresolved review packet(s)",
            "Claude Status": "assigned",
            "Claude Ack": "",
            "Last Reviewed Scope": "MP-377",
        },
    )

    resolved = resolve_current_session_authority(
        snapshot=snapshot,
        bridge_liveness={"current_instruction_revision": "old-checkpoint-rev"},
        prior_review_state=review_state,
    )

    assert resolved.current_instruction == ""
    assert resolved.current_instruction_revision == ""
    assert resolved.open_findings == "none"


def test_resolve_current_session_authority_uses_continuity_index_to_suppress_old_checkpoint() -> None:
    review_state = {
        "current_session": {
            "current_instruction": "Codex: read rev_pkt_2922 + rev_pkt_2923.",
            "current_instruction_revision": "old-checkpoint-rev",
            "implementer_status": "",
            "implementer_ack": "",
            "implementer_ack_revision": "",
            "implementer_ack_state": "missing",
            "implementer_state_hash": "",
            "open_findings": "725 expired unresolved review packet(s)",
            "last_reviewed_scope": "MP-377",
        },
        "latest_reviewer_checkpoint": {
            "current_instruction": "Codex: read rev_pkt_2922 + rev_pkt_2923.",
            "current_instruction_revision": "old-checkpoint-rev",
            "event_id": "rev_evt_52534",
            "timestamp_utc": "2026-05-03T22:44:34Z",
        },
        "packet_inbox": {
            "agents": [
                {
                    "agent": "claude",
                    "current_instruction_packet_id": "",
                }
            ],
        },
        "packets": [],
        "packet_continuity_index": {
            "rows": [
                {
                    "packet_id": "rev_pkt_3110",
                    "status": "applied",
                    "lifecycle_state": "applied",
                    "sink": "archived",
                    "latest_event_id": "rev_evt_53859",
                }
            ]
        },
    }
    snapshot = BridgeSnapshot(
        metadata={},
        sections={
            "Current Instruction For Claude": (
                "Codex: read rev_pkt_2922 + rev_pkt_2923."
            ),
            "Open Findings": "725 expired unresolved review packet(s)",
            "Claude Status": "assigned",
            "Claude Ack": "",
            "Last Reviewed Scope": "MP-377",
        },
    )

    resolved = resolve_current_session_authority(
        snapshot=snapshot,
        bridge_liveness={"current_instruction_revision": "old-checkpoint-rev"},
        prior_review_state=review_state,
    )

    assert resolved.current_instruction == ""
    assert resolved.current_instruction_revision == ""
    assert resolved.open_findings == "none"


def test_build_event_current_session_priority_action_request_overrides_reviewer_checkpoint() -> None:
    review_state = _priority_action_request_review_state()

    resolved = build_event_current_session(
        review_state=review_state,
        bridge_liveness={"current_instruction_revision": ""},
    )

    assert resolved.current_instruction == _PRIORITY_ACTION_REQUEST_INSTRUCTION
    assert resolved.current_instruction_revision
    assert resolved.current_instruction_revision != "old-checkpoint-rev"


def test_build_event_current_session_instruction_packet_overrides_reviewer_checkpoint() -> None:
    review_state = _priority_action_request_review_state()
    review_state["queue"]["derived_next_instruction"] = (
        "Remote-control campaign lane published; continue packet audit"
    )
    review_state["queue"]["derived_next_instruction_source"] = {
        "packet_id": "rev_pkt_3100",
        "packet_class": "instruction",
        "kind": "instruction",
        "from_agent": "codex",
        "to_agent": "claude",
        "target_role": "dashboard",
        "target_session_id": "session-a",
        "selection_policy": "instruction_like_fifo",
    }
    review_state["packet_inbox"]["agents"][1]["current_instruction_packet_id"] = (
        "rev_pkt_3100"
    )
    review_state["packet_inbox"]["agents"][1]["pending_actionable_packet_ids"] = [
        "rev_pkt_3100"
    ]
    review_state["packets"] = [
        {
            "packet_id": "rev_pkt_3100",
            "status": "pending",
            "summary": "Remote-control campaign lane published",
            "body": "Continue packet audit.",
            "kind": "instruction",
            "from_agent": "codex",
            "to_agent": "claude",
            "requested_action": "review_only",
            "target_role": "dashboard",
            "target_session_id": "session-a",
            "expires_at_utc": "2999-01-01T00:00:00Z",
        }
    ]

    resolved = build_event_current_session(
        review_state=review_state,
        bridge_liveness={"current_instruction_revision": ""},
    )

    assert resolved.current_instruction == (
        "Remote-control campaign lane published; continue packet audit"
    )
    assert resolved.current_instruction_revision
    assert resolved.current_instruction_revision != "old-checkpoint-rev"
    assert queue_instruction_is_dashboard_route(
        review_state,
        current_instruction="- Remote-control campaign lane published; continue packet audit",
    )


def test_normalize_current_session_from_packet_truth_preserves_dashboard_instruction() -> None:
    review_state = _priority_action_request_review_state(
        latest_reviewer_checkpoint=False
    )
    review_state["queue"]["derived_next_instruction"] = (
        "Remote-control campaign lane published; continue packet audit"
    )
    review_state["queue"]["derived_next_instruction_source"] = {
        "packet_id": "rev_pkt_3100",
        "packet_class": "instruction",
        "kind": "instruction",
        "from_agent": "codex",
        "to_agent": "claude",
        "target_role": "dashboard",
        "target_session_id": "session-a",
        "selection_policy": "instruction_like_fifo",
    }
    review_state["packet_inbox"]["agents"][0]["current_instruction_packet_id"] = ""
    review_state["packet_inbox"]["agents"][0]["pending_actionable_packet_ids"] = []

    normalized = _normalize_current_session_from_packet_truth(
        current_session=ReviewCurrentSessionState(
            current_instruction=(
                "- Remote-control campaign lane published; continue packet audit"
            ),
            current_instruction_revision="dashboard-rev",
            implementer_status="working",
            implementer_ack="",
            implementer_ack_revision="",
            implementer_ack_state="missing",
            implementer_state_hash="state-hash",
            implementer_session_state="",
            implementer_session_hint="",
            open_findings="none",
            last_reviewed_scope="MP-377",
        ),
        review_state=review_state,
    )

    assert normalized.current_instruction == (
        "- Remote-control campaign lane published; continue packet audit"
    )
    assert normalized.current_instruction_revision == "dashboard-rev"


def test_event_projection_assembly_priority_action_request_survives_attention_clear() -> None:
    review_state = _priority_action_request_review_state()

    resolved = resolve_event_projection_assembly_current_session(
        review_state,
        context=SimpleNamespace(prior_review_state=None),
        bridge_liveness={"current_instruction_revision": ""},
        deps=SimpleNamespace(build_event_current_session=build_event_current_session),
    )

    assert resolved.current_instruction == _PRIORITY_ACTION_REQUEST_INSTRUCTION
    assert resolved.current_instruction_revision
    assert resolved.current_instruction_revision != "old-checkpoint-rev"


def test_normalize_current_session_from_packet_truth_preserves_priority_action_request() -> None:
    normalized = _normalize_current_session_from_packet_truth(
        current_session=ReviewCurrentSessionState(
            current_instruction=_PRIORITY_ACTION_REQUEST_INSTRUCTION,
            current_instruction_revision="priority-rev",
            implementer_status="working",
            implementer_ack="",
            implementer_ack_revision="",
            implementer_ack_state="missing",
            implementer_state_hash="state-hash",
            implementer_session_state="",
            implementer_session_hint="",
            open_findings="none",
            last_reviewed_scope="MP-377",
        ),
        review_state=_priority_action_request_review_state(
            latest_reviewer_checkpoint=False
        ),
    )

    assert normalized.current_instruction == _PRIORITY_ACTION_REQUEST_INSTRUCTION
    assert normalized.current_instruction_revision == "priority-rev"
    assert normalized.implementer_ack_state == "missing"


def test_build_event_current_session_clears_when_no_reviewer_checkpoint_and_packet_attention_clears() -> None:
    """rev_pkt_2922 Finding Y inverse guard: when no live reviewer_checkpoint
    payload exists, the packet-attention clear path must still work
    (legacy behavior) — only packet-derived state should clear."""
    review_state = {
        # No latest_reviewer_checkpoint at all.
        "packet_inbox": {
            "agents": [
                {
                    "agent": "claude",
                    "current_instruction_packet_id": "",
                }
            ],
        },
        "packets": [],
    }
    bridge_liveness = {
        "current_instruction_revision": "stale-revision",
    }

    resolved = build_event_current_session(
        review_state=review_state,
        bridge_liveness=bridge_liveness,
    )

    # Without a live reviewer_checkpoint, the legacy clear behavior holds:
    # current_instruction and revision both empty.
    assert resolved.current_instruction in {"", "(missing)"}
    assert resolved.current_instruction_revision == ""


_PRIORITY_ACTION_REQUEST_INSTRUCTION = (
    "Priority action_request: Stage verified commit pipeline for T22AN-L/Finding Y closure"
)


def _priority_action_request_review_state(
    *,
    latest_reviewer_checkpoint: bool = True,
) -> dict[str, object]:
    review_state: dict[str, object] = {
        "collaboration": {
            "coding_agent": "codex",
        },
        "review": {"plan_id": "MP-377"},
        "queue": {
            "pending_total": 1,
            "pending_claude": 1,
            "derived_next_instruction": _PRIORITY_ACTION_REQUEST_INSTRUCTION,
            "derived_next_instruction_source": {
                "packet_id": "rev_pkt_2929",
                "packet_class": "action_request",
                "kind": "action_request",
                "from_agent": "codex",
                "to_agent": "claude",
                "selection_policy": "action_request_priority",
            },
        },
        "packet_inbox": {
            "attention_revision": "packet-attention-rev",
            "agents": [
                {
                    "agent": "codex",
                    "current_instruction_packet_id": "",
                    "pending_actionable_packet_ids": [],
                    "expired_unresolved_packet_ids": [],
                    "attention_status": "idle",
                    "wake_reason": "",
                    "delivery_state": "idle",
                },
                {
                    "agent": "claude",
                    "current_instruction_packet_id": "rev_pkt_2929",
                    "pending_actionable_packet_ids": ["rev_pkt_2929"],
                    "expired_unresolved_packet_ids": [],
                    "attention_status": "wake_required",
                    "wake_reason": "action_request_pending",
                    "delivery_state": "unseen",
                },
            ],
        },
        "packets": [
            {
                "packet_id": "rev_pkt_2929",
                "status": "pending",
                "summary": "Stage verified commit pipeline",
                "body": "Run the stage_commit_pipeline handoff.",
                "kind": "action_request",
                "from_agent": "codex",
                "to_agent": "claude",
                "requested_action": "stage_commit_pipeline",
                "expires_at_utc": "2999-01-01T00:00:00Z",
            }
        ],
        "registry": {"agents": [{"agent_id": "codex", "job_state": "active"}]},
    }
    if latest_reviewer_checkpoint:
        review_state["latest_reviewer_checkpoint"] = {
            "current_instruction": "Codex: read rev_pkt_2922 + rev_pkt_2923.",
            "current_instruction_revision": "old-checkpoint-rev",
            "event_id": "rev_evt_checkpoint",
            "timestamp": "2026-05-03T22:00:00Z",
        }
    return review_state
