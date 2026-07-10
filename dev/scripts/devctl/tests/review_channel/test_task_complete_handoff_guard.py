from __future__ import annotations

import json
import os
from pathlib import Path

from dev.scripts.devctl.review_channel.event_store import (
    load_events,
    resolve_artifact_paths,
)
from dev.scripts.devctl.review_channel.events import post_packet
from dev.scripts.devctl.review_channel.packet_contract import (
    PacketPostRequest,
    PacketTargetFields,
)
from dev.scripts.devctl.review_channel.task_complete_handoff_guard import (
    TaskCompleteHandoffRequest,
    emit_handoff_for_latest_task_complete,
)
from dev.scripts.devctl.tests.test_review_channel_context_refs import (
    _review_channel_text,
)


def test_task_complete_guard_posts_missing_stage_handoff(tmp_path: Path) -> None:
    review_channel_path = tmp_path / "dev/active/review_channel.md"
    review_channel_path.parent.mkdir(parents=True, exist_ok=True)
    review_channel_path.write_text(_review_channel_text(), encoding="utf-8")
    sessions_root = tmp_path / "sessions"
    rollout_path = sessions_root / "2026/04/28/rollout-20260428-codex.jsonl"
    rollout_path.parent.mkdir(parents=True, exist_ok=True)
    rollout_path.write_text(
        json.dumps(
            {
                "timestamp": "2026-04-28T19:20:00Z",
                "type": "event_msg",
                "payload": {
                    "type": "task_complete",
                    "last_agent_message": "Slice complete with guard evidence.",
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    target_revision = "a" * 40

    result = emit_handoff_for_latest_task_complete(
        TaskCompleteHandoffRequest(
            repo_root=tmp_path,
            sessions_root=sessions_root,
            target_revision=target_revision,
            guard_evidence="--profile ci",
            conductor_exit_code="0",
        )
    )
    artifact_paths = resolve_artifact_paths(repo_root=tmp_path)
    events = load_events(Path(artifact_paths.event_log_path))
    handoff = next(event for event in events if event.get("packet_id") == result.packet_id)

    assert result.status == "posted"
    assert result.target_ref == f"devctl_commit:{target_revision}"
    assert handoff["kind"] == "action_request"
    assert handoff["from_agent"] == "codex"
    assert handoff["to_agent"] == "claude"
    assert handoff["requested_action"] == "stage_commit_pipeline"
    assert handoff["target_revision"] == target_revision
    assert handoff["full_guard_bundle_evidence"] == "--profile ci"
    assert "Slice complete with guard evidence." in str(handoff["body"])


def test_task_complete_guard_dedupes_existing_stage_handoff(tmp_path: Path) -> None:
    review_channel_path = tmp_path / "dev/active/review_channel.md"
    review_channel_path.parent.mkdir(parents=True, exist_ok=True)
    review_channel_path.write_text(_review_channel_text(), encoding="utf-8")
    sessions_root = tmp_path / "sessions"
    rollout_path = sessions_root / "2026/04/28/rollout-20260428-codex.jsonl"
    rollout_path.parent.mkdir(parents=True, exist_ok=True)
    rollout_path.write_text(
        json.dumps(
            {
                "timestamp": "2026-04-28T19:25:00Z",
                "type": "event_msg",
                "payload": {"type": "task_complete"},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    request = TaskCompleteHandoffRequest(
        repo_root=tmp_path,
        sessions_root=sessions_root,
        target_revision="b" * 40,
    )

    posted = emit_handoff_for_latest_task_complete(request)
    skipped = emit_handoff_for_latest_task_complete(request)
    artifact_paths = resolve_artifact_paths(repo_root=tmp_path)
    stage_posts = [
        event
        for event in load_events(Path(artifact_paths.event_log_path))
        if event.get("event_type") == "packet_posted"
        and event.get("requested_action") == "stage_commit_pipeline"
    ]

    assert posted.status == "posted"
    assert skipped.status == "skipped"
    assert skipped.reason == "matching_stage_handoff_exists"
    assert len(stage_posts) == 1


def test_task_complete_guard_uses_latest_session_with_task_complete(
    tmp_path: Path,
) -> None:
    review_channel_path = tmp_path / "dev/active/review_channel.md"
    review_channel_path.parent.mkdir(parents=True, exist_ok=True)
    review_channel_path.write_text(_review_channel_text(), encoding="utf-8")
    sessions_root = tmp_path / "sessions"
    old_rollout = sessions_root / "2026/04/28/rollout-20260428-old-codex.jsonl"
    new_rollout = sessions_root / "2026/04/28/rollout-20260428-new-codex.jsonl"
    old_rollout.parent.mkdir(parents=True, exist_ok=True)
    old_rollout.write_text(
        json.dumps(
            {
                "timestamp": "2026-04-28T19:25:00Z",
                "type": "event_msg",
                "payload": {"type": "task_complete"},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    new_rollout.write_text(
        json.dumps(
            {
                "timestamp": "2026-04-28T19:30:00Z",
                "type": "event_msg",
                "payload": {"type": "turn_context"},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    os.utime(old_rollout, (1_772_000_000, 1_772_000_000))
    os.utime(new_rollout, (1_772_000_300, 1_772_000_300))

    result = emit_handoff_for_latest_task_complete(
        TaskCompleteHandoffRequest(
            repo_root=tmp_path,
            sessions_root=sessions_root,
            target_revision="d" * 40,
        )
    )

    assert result.status == "posted"
    assert result.rollout_path == str(old_rollout)
    assert result.task_complete_at_utc == "2026-04-28T19:25:00Z"


def test_task_complete_guard_rejects_handoff_when_continuation_anchor_applies(
    tmp_path: Path,
) -> None:
    review_channel_path = tmp_path / "dev/active/review_channel.md"
    review_channel_path.parent.mkdir(parents=True, exist_ok=True)
    review_channel_path.write_text(_review_channel_text(), encoding="utf-8")
    sessions_root = tmp_path / "sessions"
    rollout_path = sessions_root / "2026/04/28/rollout-20260428-codex.jsonl"
    rollout_path.parent.mkdir(parents=True, exist_ok=True)
    rollout_path.write_text(
        json.dumps(
            {
                "timestamp": "2026-04-28T19:30:00Z",
                "type": "event_msg",
                "payload": {"type": "task_complete"},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    artifact_paths = resolve_artifact_paths(repo_root=tmp_path)
    post_packet(
        repo_root=tmp_path,
        review_channel_path=review_channel_path,
        artifact_paths=artifact_paths,
        request=PacketPostRequest(
            from_agent="claude",
            to_agent="codex",
            kind="continuation_anchor",
            summary="Continue MP-377",
            body="Keep the implementer role working across session replacement.",
            target=PacketTargetFields.from_values(
                target_role="implementer",
                target_session_id="dead-session",
                anchor_scope="role",
            ),
        ),
    )

    result = emit_handoff_for_latest_task_complete(
        TaskCompleteHandoffRequest(
            repo_root=tmp_path,
            sessions_root=sessions_root,
            target_revision="c" * 40,
            actor_role="implementer",
        )
    )
    events = load_events(Path(artifact_paths.event_log_path))
    stage_posts = [
        event
        for event in events
        if event.get("event_type") == "packet_posted"
        and event.get("requested_action") == "stage_commit_pipeline"
    ]

    assert result.status == "blocked"
    assert result.reason == (
        "task_complete_rejected_by_policy:continuation_anchor_body_unobserved"
    )
    assert "review-channel --action show" in result.next_command
    assert "--packet-id" in result.next_command
    assert stage_posts == []
