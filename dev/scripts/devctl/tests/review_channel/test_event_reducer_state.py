"""Focused tests for event-backed reducer current-session state."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from dev.scripts.devctl.review_channel.event_reducer import reduce_events
from dev.scripts.devctl.review_channel.events import (
    refresh_event_bundle,
    resolve_artifact_paths,
)


_TARGET_REVISION = "22fcd435bce993e6006a6d7cfab61f00c9bd6cb2"
_COMMIT_REVISION = "00b8340f1a394fcb7b9bf58a1970f9404ea4a9e3"


def test_packet_applied_stage_commit_pipeline_projects_implementer_ack() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        with patch(
            "dev.scripts.devctl.review_channel.event_reducer_ack_projection."
            "handoff_target_revisions",
            return_value=(_TARGET_REVISION, _COMMIT_REVISION),
        ):
            review_state, _ = reduce_events(
                events=_stage_commit_events(),
                repo_root=repo_root,
                review_channel_path=repo_root / "dev/active/review_channel.md",
                lanes=[],
            )

    current_session = review_state["current_session"]
    assert current_session["implementer_ack_revision"] == _COMMIT_REVISION
    assert current_session["implementer_ack_state"] == "current"
    assert "stage_commit_pipeline handoff applied" in current_session["implementer_ack"]


def test_packet_applied_stage_commit_pipeline_replay_is_idempotent() -> None:
    events = _stage_commit_events()
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        with patch(
            "dev.scripts.devctl.review_channel.event_reducer_ack_projection."
            "handoff_target_revisions",
            return_value=(_TARGET_REVISION, _COMMIT_REVISION),
        ):
            once, _ = reduce_events(
                events=events,
                repo_root=repo_root,
                review_channel_path=repo_root / "dev/active/review_channel.md",
                lanes=[],
            )
            twice, _ = reduce_events(
                events=[*events, dict(events[-1])],
                repo_root=repo_root,
                review_channel_path=repo_root / "dev/active/review_channel.md",
                lanes=[],
            )

    assert twice["current_session"] == once["current_session"]


def test_packet_applied_stage_commit_pipeline_rejects_malformed_outcome() -> None:
    events = _stage_commit_events(outcome_provider="claude")
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        with patch(
            "dev.scripts.devctl.review_channel.event_reducer_ack_projection."
            "handoff_target_revisions",
            return_value=(_TARGET_REVISION, _COMMIT_REVISION),
        ):
            review_state, _ = reduce_events(
                events=events,
                repo_root=repo_root,
                review_channel_path=repo_root / "dev/active/review_channel.md",
                lanes=[],
            )

    current_session = review_state["current_session"]
    assert current_session["implementer_ack_revision"] == ""
    assert current_session["implementer_ack"] == ""
    assert current_session["implementer_ack_state"] == "unknown"


def test_packet_applied_stage_commit_pipeline_rejects_off_chain_outcome() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        with patch(
            "dev.scripts.devctl.review_channel.event_reducer_ack_projection."
            "handoff_target_revisions",
            return_value=("f" * 40,),
        ):
            review_state, _ = reduce_events(
                events=_stage_commit_events(),
                repo_root=repo_root,
                review_channel_path=repo_root / "dev/active/review_channel.md",
                lanes=[],
            )

    current_session = review_state["current_session"]
    assert current_session["implementer_ack_revision"] == ""
    assert current_session["implementer_ack_state"] == "unknown"


def test_refresh_event_bundle_keeps_projected_ack_in_final_current_session() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        review_channel_path = repo_root / "dev/active/review_channel.md"
        review_channel_path.parent.mkdir(parents=True, exist_ok=True)
        review_channel_path.write_text(_review_channel_text(), encoding="utf-8")
        artifact_paths = resolve_artifact_paths(repo_root=repo_root)
        events_path = Path(artifact_paths.event_log_path)
        events_path.parent.mkdir(parents=True, exist_ok=True)
        events_path.write_text(
            "\n".join(json.dumps(event) for event in _stage_commit_events()) + "\n",
            encoding="utf-8",
        )

        with patch(
            "dev.scripts.devctl.review_channel.event_reducer_ack_projection."
            "handoff_target_revisions",
            return_value=(_TARGET_REVISION, _COMMIT_REVISION),
        ):
            bundle = refresh_event_bundle(
                repo_root=repo_root,
                review_channel_path=review_channel_path,
                artifact_paths=artifact_paths,
            )

    current_session = bundle.review_state["current_session"]
    assert current_session["implementer_ack_revision"] == _COMMIT_REVISION
    assert current_session["implementer_ack_state"] == "current"
    assert current_session["implementer_ack"]


def test_packet_wake_attempt_projects_reviewer_wake_without_closing_packet() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        review_state, _ = reduce_events(
            events=_packet_wake_events(),
            repo_root=repo_root,
            review_channel_path=repo_root / "dev/active/review_channel.md",
            lanes=[],
        )

    packet = review_state["packets"][0]
    wake = packet["reviewer_wake"]
    assert packet["packet_id"] == "rev_pkt_wake"
    assert packet["status"] == "pending"
    assert packet["lifecycle_current_state"] == "pending"
    assert wake["contract_id"] == "PacketWakeReceipt"
    assert wake["event_id"] == "rev_evt_2"
    assert wake["wake_method"] == "headless_delegate"
    assert wake["delegated"] is True
    assert wake["visible_session_woke"] is False
    assert wake["spawned_pids"] == [4242]


def _stage_commit_events(*, outcome_provider: str = "codex") -> list[dict[str, object]]:
    packet_fields = {
        "packet_id": "rev_pkt_2097",
        "trace_id": "trace_20260428T141815Z_codex_43893",
        "session_id": "local-review",
        "plan_id": "MP-355",
        "project_id": "project-1",
        "from_agent": "codex",
        "to_agent": "codex",
        "kind": "action_request",
        "summary": "Codex 37 live-runtime matcher handoff",
        "body": "Full guard profile passed.",
        "evidence_refs": [],
        "guidance_refs": [],
        "context_pack_refs": [],
        "confidence": 1.0,
        "requested_action": "stage_commit_pipeline",
        "policy_hint": "safe_auto_apply",
        "approval_required": False,
        "target_kind": "runtime",
        "target_ref": f"devctl_commit:{_COMMIT_REVISION}",
        "target_revision": _TARGET_REVISION,
        "anchor_refs": [],
        "intake_ref": None,
        "mutation_op": None,
        "pipeline_generation": None,
        "staged_snapshot_hash": None,
        "guard_results_summary": None,
        "full_guard_bundle_evidence": "--profile ci",
        "expires_at_utc": "2026-04-28T14:48:14.872078Z",
    }
    posted = {
        **packet_fields,
        "event_id": "rev_evt_43892",
        "event_type": "packet_posted",
        "timestamp_utc": "2026-04-28T14:18:14.872078Z",
        "source": "review_channel",
        "status": "pending",
        "metadata": {},
    }
    outcome = {
        "event_id": "rev_evt_43893",
        "event_type": "agent_session_outcome",
        "timestamp_utc": "2026-04-28T14:18:14.872078Z",
        "schema_version": 1,
        "contract_id": "AgentSessionOutcome",
        "outcome": "completed_handoff",
        "reason": "stage_commit_pipeline_posted_with_full_guard_bundle_evidence",
        "provider": outcome_provider,
        "session_actor_id": outcome_provider,
        "session_actor_role": "review_agent",
        "session_id": "local-review",
        "session_name": f"{outcome_provider}-conductor",
        "observed_at_utc": "2026-04-28T14:18:14.872078Z",
        "finished_at_utc": "2026-04-28T14:18:14.872078Z",
        "source": "review_channel_packet",
        "source_event_id": posted["event_id"],
        "handoff_packet_id": posted["packet_id"],
        "handoff_requested_action": "stage_commit_pipeline",
        "target_kind": "runtime",
        "target_ref": posted["target_ref"],
        "target_revision": posted["target_revision"],
        "workspace_root": "",
    }
    acked = {
        **packet_fields,
        "event_id": "rev_evt_43896",
        "event_type": "packet_acked",
        "timestamp_utc": "2026-04-28T14:20:00.582579Z",
        "source": "review_channel",
        "status": "acked",
        "metadata": {"actor": "codex"},
    }
    applied = {
        **packet_fields,
        "event_id": "rev_evt_43897",
        "event_type": "packet_applied",
        "timestamp_utc": "2026-04-28T14:20:40.552225Z",
        "source": "review_channel",
        "status": "applied",
        "metadata": {"actor": "codex"},
    }
    return [posted, outcome, acked, applied]


def _packet_wake_events() -> list[dict[str, object]]:
    packet_fields = {
        "packet_id": "rev_pkt_wake",
        "trace_id": "trace-wake",
        "session_id": "local-review",
        "plan_id": "MP-377",
        "project_id": "project-1",
        "from_agent": "codex",
        "to_agent": "claude",
        "kind": "system_notice",
        "summary": "Wake Claude dashboard delegate",
        "body": "Please report back.",
        "evidence_refs": [],
        "guidance_refs": [],
        "context_pack_refs": [],
        "confidence": 1.0,
        "requested_action": "review_only",
        "policy_hint": "review_only",
        "approval_required": False,
        "target_kind": None,
        "target_ref": None,
        "target_revision": None,
        "anchor_refs": [],
        "intake_ref": None,
        "mutation_op": None,
        "target_role": "dashboard",
        "target_session_id": "session-visible",
        "pipeline_generation": None,
        "staged_snapshot_hash": None,
        "guard_results_summary": None,
        "full_guard_bundle_evidence": None,
        "expires_at_utc": "2026-05-02T14:00:00Z",
    }
    posted = {
        **packet_fields,
        "event_id": "rev_evt_1",
        "event_type": "packet_posted",
        "timestamp_utc": "2026-05-02T13:00:00Z",
        "source": "review_channel",
        "status": "pending",
        "metadata": {},
    }
    receipt = {
        "contract_id": "PacketWakeReceipt",
        "packet_id": "rev_pkt_wake",
        "attempted": True,
        "woke": False,
        "delegated": True,
        "visible_session_woke": False,
        "reason": "headless_delegate_launched",
        "wake_method": "headless_delegate",
        "target_agent": "claude",
        "target_role": "dashboard",
        "target_session_id": "session-visible",
        "dashboard_session_id": "session-visible",
        "spawned_pids": [4242],
        "delivered_to_pids": [4242],
        "recorded_at_utc": "2026-05-02T13:00:02Z",
    }
    wake = {
        **packet_fields,
        "event_id": "rev_evt_2",
        "event_type": "packet_wake_attempted",
        "timestamp_utc": "2026-05-02T13:00:02Z",
        "source": "review_channel",
        "wake_method": "headless_delegate",
        "delegated": True,
        "visible_session_woke": False,
        "wake_receipt": receipt,
        "metadata": {"wake_receipt": receipt},
    }
    return [posted, wake]


def _review_channel_text() -> str:
    return "\n".join(
        [
            "# Review Channel + Shared Screen Plan",
            "",
            "## Transitional Markdown Bridge (Current Operating Mode)",
            "",
            "| Agent | Lane | Primary active docs | MP scope | Worktree | Branch |",
            "|---|---|---|---|---|---|",
            (
                "| `AGENT-1` | Codex reviewer lane | "
                "`dev/active/review_channel.md` | `MP-355` | "
                "`../wt-a1` | `feature/a1` |"
            ),
        ]
    )
