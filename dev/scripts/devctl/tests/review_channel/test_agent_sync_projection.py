"""Focused tests for the agent_sync projection (MP377-P0)."""

from __future__ import annotations

import tempfile
from pathlib import Path

from dev.scripts.devctl.review_channel.agent_sync_projection import (
    build_agent_sync_projection,
)
from dev.scripts.devctl.review_channel.event_reducer import refresh_event_bundle
from dev.scripts.devctl.review_channel.event_store import (
    append_event,
    resolve_artifact_paths,
)


def _packet_post_event(
    *,
    idempotency_key: str,
    from_agent: str = "codex",
    to_agent: str = "claude",
    summary: str = "Test",
    body: str = "Body",
) -> dict[str, object]:
    return {
        "event_type": "packet_posted",
        "packet_id": "",
        "trace_id": "",
        "from_agent": from_agent,
        "to_agent": to_agent,
        "kind": "action_request",
        "summary": summary,
        "body": body,
        "requested_action": "stage_commit_pipeline",
        "policy_hint": "safe_auto_apply",
        "idempotency_key": idempotency_key,
    }


def _setup_repo(tmpdir: str) -> tuple[Path, Path, object]:
    root = Path(tmpdir)
    review_channel_path = root / "dev/active/review_channel.md"
    review_channel_path.parent.mkdir(parents=True, exist_ok=True)
    review_channel_path.write_text("# Review Channel\n", encoding="utf-8")
    artifact_paths = resolve_artifact_paths(repo_root=root)
    return root, review_channel_path, artifact_paths


def test_awaiting_picks_newest_action_request_not_oldest() -> None:
    """rev_pkt_2256 fix: awaiting ordering must pick newest, not first/oldest."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root, review_channel_path, artifact_paths = _setup_repo(tmpdir)
        events_path = Path(artifact_paths.event_log_path)
        first = append_event(
            events_path, _packet_post_event(idempotency_key="k1", summary="Old"),
            existing_events=[],
        )
        second = append_event(
            events_path, _packet_post_event(idempotency_key="k2", summary="New"),
            existing_events=[first],
        )

        bundle = refresh_event_bundle(
            repo_root=root,
            review_channel_path=review_channel_path,
            artifact_paths=artifact_paths,
        )
        codex_row = bundle.review_state["agent_sync"]["agents"]["codex"]
        assert codex_row["awaiting_packet_id"] == second["packet_id"]
        assert codex_row["awaiting_packet_id"] != first["packet_id"]


def test_terminal_lifecycle_excluded_from_pending_and_awaiting() -> None:
    """rev_pkt_2256 fix: dismissed/applied/failed packets must not appear as pending."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root, review_channel_path, artifact_paths = _setup_repo(tmpdir)
        events_path = Path(artifact_paths.event_log_path)
        first = append_event(
            events_path, _packet_post_event(idempotency_key="k1"),
            existing_events=[],
        )
        # Dismiss the only packet → it's terminal
        append_event(
            events_path,
            {
                "event_type": "packet_dismissed",
                "packet_id": first["packet_id"],
                "actor": "claude",
                "idempotency_key": "",
            },
            existing_events=[first],
        )

        bundle = refresh_event_bundle(
            repo_root=root,
            review_channel_path=review_channel_path,
            artifact_paths=artifact_paths,
        )
        agents = bundle.review_state["agent_sync"]["agents"]
        # claude should NOT see the dismissed packet as pending
        assert first["packet_id"] not in agents["claude"]["pending_packets_to_me"]
        assert agents["claude"]["derived_status"] == "idle"
        # codex should NOT be awaiting on the dismissed packet
        assert agents["codex"]["awaiting_packet_id"] == ""
        assert agents["codex"]["derived_status"] == "idle"


def test_consumption_cursor_only_credits_explicit_actor_match() -> None:
    """rev_pkt_2256 fix: dismissing a packet to=claude credits codex (the actor), not claude."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root, review_channel_path, artifact_paths = _setup_repo(tmpdir)
        events_path = Path(artifact_paths.event_log_path)
        first = append_event(
            events_path, _packet_post_event(idempotency_key="k1"),
            existing_events=[],
        )
        # Dismiss event with actor=codex, but the packet's to_agent=claude
        append_event(
            events_path,
            {
                "event_type": "packet_dismissed",
                "packet_id": first["packet_id"],
                "actor": "codex",
                "idempotency_key": "",
            },
            existing_events=[first],
        )

        bundle = refresh_event_bundle(
            repo_root=root,
            review_channel_path=review_channel_path,
            artifact_paths=artifact_paths,
        )
        agents = bundle.review_state["agent_sync"]["agents"]
        # claude should NOT have consumption credit — actor was codex.
        assert agents["claude"]["last_consumed_event_id_lower_bound"] == ""
        assert agents["claude"]["last_consumed_evidence_class"] == "none"


def test_packet_acked_codex_to_claude_with_metadata_actor_claude_credits_claude() -> None:
    """rev_pkt_2322/2327: production-shaped packet_acked event credits the metadata.actor.

    Production transition events keep the original packet route in
    ``from_agent``/``to_agent`` and store the acting actor in
    ``metadata.actor``. A codex→claude action_request that claude acks
    must credit claude's consumption cursor, never codex's.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        root, review_channel_path, artifact_paths = _setup_repo(tmpdir)
        events_path = Path(artifact_paths.event_log_path)
        # codex→claude action_request
        first = append_event(
            events_path,
            _packet_post_event(
                idempotency_key="k1",
                from_agent="codex",
                to_agent="claude",
            ),
            existing_events=[],
        )
        # claude acks. Production shape: from_agent=codex (preserved sender),
        # to_agent=claude (preserved recipient), metadata.actor=claude.
        append_event(
            events_path,
            {
                "event_type": "packet_acked",
                "packet_id": first["packet_id"],
                "from_agent": "codex",
                "to_agent": "claude",
                "metadata": {"actor": "claude"},
                "idempotency_key": "",
            },
            existing_events=[first],
        )

        bundle = refresh_event_bundle(
            repo_root=root,
            review_channel_path=review_channel_path,
            artifact_paths=artifact_paths,
        )
        agents = bundle.review_state["agent_sync"]["agents"]
        assert agents["claude"]["last_consumed_event_id_lower_bound"] != ""
        assert agents["claude"]["last_consumed_evidence_class"] == "lower_bound"
        # codex must NOT be credited even though codex is the from_agent.
        assert agents["codex"]["last_consumed_event_id_lower_bound"] == ""


def test_packet_acked_claude_to_codex_with_metadata_actor_codex_credits_codex() -> None:
    """rev_pkt_2322/2327: symmetric production-shaped case for the other direction."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root, review_channel_path, artifact_paths = _setup_repo(tmpdir)
        events_path = Path(artifact_paths.event_log_path)
        first = append_event(
            events_path,
            _packet_post_event(
                idempotency_key="k1",
                from_agent="claude",
                to_agent="codex",
            ),
            existing_events=[],
        )
        # codex acks. Production shape: from_agent=claude (preserved sender),
        # to_agent=codex (preserved recipient), metadata.actor=codex.
        append_event(
            events_path,
            {
                "event_type": "packet_acked",
                "packet_id": first["packet_id"],
                "from_agent": "claude",
                "to_agent": "codex",
                "metadata": {"actor": "codex"},
                "idempotency_key": "",
            },
            existing_events=[first],
        )

        bundle = refresh_event_bundle(
            repo_root=root,
            review_channel_path=review_channel_path,
            artifact_paths=artifact_paths,
        )
        agents = bundle.review_state["agent_sync"]["agents"]
        assert agents["codex"]["last_consumed_event_id_lower_bound"] != ""
        assert agents["codex"]["last_consumed_evidence_class"] == "lower_bound"
        # claude must NOT be credited even though claude is the from_agent.
        assert agents["claude"]["last_consumed_event_id_lower_bound"] == ""


def test_metadata_actor_beats_top_level_actor_and_from_agent() -> None:
    """rev_pkt_2327: precedence — metadata.actor wins over actor and from_agent.

    Even when an event sets BOTH a top-level ``actor`` (legacy shape) AND
    a ``from_agent`` (sender), the canonical acting actor lives in
    ``metadata.actor``. Reading the wrong field would credit the wrong
    side. This test pins the precedence order:
    ``metadata.actor`` > ``actor`` > NOT from_agent (never).
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        root, review_channel_path, artifact_paths = _setup_repo(tmpdir)
        events_path = Path(artifact_paths.event_log_path)
        first = append_event(
            events_path,
            _packet_post_event(
                idempotency_key="k1",
                from_agent="codex",
                to_agent="claude",
            ),
            existing_events=[],
        )
        # Conflict scenario: ALL three fields set with DIFFERENT values.
        # metadata.actor=claude must win; codex (top-level actor) and
        # codex (from_agent) must be ignored as consumption credits.
        append_event(
            events_path,
            {
                "event_type": "packet_acked",
                "packet_id": first["packet_id"],
                "from_agent": "codex",
                "to_agent": "claude",
                "actor": "operator",  # legacy top-level actor (different from metadata)
                "metadata": {"actor": "claude"},  # canonical
                "idempotency_key": "",
            },
            existing_events=[first],
        )

        bundle = refresh_event_bundle(
            repo_root=root,
            review_channel_path=review_channel_path,
            artifact_paths=artifact_paths,
        )
        agents = bundle.review_state["agent_sync"]["agents"]
        # claude (metadata.actor) is credited.
        assert agents["claude"]["last_consumed_event_id_lower_bound"] != ""
        # operator (top-level actor) and codex (from_agent) are NOT credited.
        assert agents.get("operator", {}).get(
            "last_consumed_event_id_lower_bound", ""
        ) == ""
        assert agents["codex"]["last_consumed_event_id_lower_bound"] == ""


def test_canonical_predicate_picks_newest_when_queue_picks_older() -> None:
    """rev_pkt_2326/2337: synthetic divergence — queue picks older priority,
    canonical predicate must surface newest work-board active packet.

    Setup: post 3 action_requests to claude (oldest, middle, newest). v1
    agent_sync's active_action_requests_to_me list contains all 3 in append
    order. The legacy queue priority rule may pick the OLDEST. The canonical
    predicate must pick the NEWEST (highest event-id rank) non-terminal.
    """
    from dev.scripts.devctl.review_channel.active_packet_authority import (
        current_active_packet_for_agent,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        root, review_channel_path, artifact_paths = _setup_repo(tmpdir)
        events_path = Path(artifact_paths.event_log_path)

        # Post 3 action_requests codex→claude with distinct semantic content.
        # Then ack each one so they transition from delivery_pending into
        # active (acknowledged) — that's where active_action_requests_to_me
        # picks them up.
        first = append_event(
            events_path,
            _packet_post_event(
                idempotency_key="oldest", summary="oldest", body="o",
            ),
            existing_events=[],
        )
        first_ack = append_event(
            events_path,
            {
                "event_type": "packet_acked",
                "packet_id": first["packet_id"],
                "from_agent": "codex",
                "to_agent": "claude",
                "metadata": {"actor": "claude"},
                "idempotency_key": "",
            },
            existing_events=[first],
        )
        middle = append_event(
            events_path,
            _packet_post_event(
                idempotency_key="middle", summary="middle", body="m",
            ),
            existing_events=[first, first_ack],
        )
        middle_ack = append_event(
            events_path,
            {
                "event_type": "packet_acked",
                "packet_id": middle["packet_id"],
                "from_agent": "codex",
                "to_agent": "claude",
                "metadata": {"actor": "claude"},
                "idempotency_key": "",
            },
            existing_events=[first, first_ack, middle],
        )
        newest = append_event(
            events_path,
            _packet_post_event(
                idempotency_key="newest", summary="newest", body="n",
            ),
            existing_events=[first, first_ack, middle, middle_ack],
        )
        newest_ack = append_event(
            events_path,
            {
                "event_type": "packet_acked",
                "packet_id": newest["packet_id"],
                "from_agent": "codex",
                "to_agent": "claude",
                "metadata": {"actor": "claude"},
                "idempotency_key": "",
            },
            existing_events=[first, first_ack, middle, middle_ack, newest],
        )

        bundle = refresh_event_bundle(
            repo_root=root,
            review_channel_path=review_channel_path,
            artifact_paths=artifact_paths,
        )

        # All 3 should appear in claude's active_action_requests_to_me.
        agents = bundle.review_state["agent_sync"]["agents"]
        active_list = agents["claude"]["active_action_requests_to_me"]
        for pid in (first["packet_id"], middle["packet_id"], newest["packet_id"]):
            assert pid in active_list, f"{pid} missing from active list"

        # The CANONICAL predicate must pick the newest (highest event-id rank).
        canonical = current_active_packet_for_agent(
            bundle.review_state, "claude",
        )
        assert canonical == newest["packet_id"], (
            f"Canonical predicate picked {canonical!r} but newest active "
            f"work is {newest['packet_id']!r}. Predicate must surface the "
            f"newest non-terminal action_request, not the oldest in "
            f"append order."
        )


def test_projection_is_idle_for_uninvolved_agents() -> None:
    """Default state: agents with no inbound or outbound work are idle."""
    projection = build_agent_sync_projection(
        events=[],
        packet_rows=[],
        registered_agent_ids=["claude", "codex", "operator", "test-actor"],
        refresh_seq=1,
        refreshed_at_utc="2026-04-30T02:15:00Z",
    )
    assert projection["schema_version"] == 1
    assert projection["contract_id"] == "AgentSyncProjection"
    for aid in ("claude", "codex", "operator", "test-actor"):
        row = projection["agents"][aid]
        assert row["derived_status"] == "idle"
        assert row["pending_packets_to_me"] == []
        assert row["active_action_requests_to_me"] == []
        assert row["awaiting_packet_id"] == ""
        assert row["last_packet_emitted_event_id"] == ""


def test_agent_sync_inventory_includes_session_targeted_pending_packet() -> None:
    """Agent-level inventory must not hide packets that require session scope."""
    projection = build_agent_sync_projection(
        events=[
            {"event_id": "rev_evt_10", "event_type": "packet_posted"},
            {"event_id": "rev_evt_11", "event_type": "packet_delivery_observed"},
        ],
        packet_rows=[
            {
                "packet_id": "rev_pkt_session",
                "latest_event_id": "rev_evt_11",
                "to_agent": "claude",
                "from_agent": "codex",
                "kind": "action_request",
                "status": "pending",
                "lifecycle_current_state": "execution_pending",
                "target_role": "implementer",
                "target_session_id": "session-claude",
            }
        ],
        registered_agent_ids=["claude", "codex"],
        refresh_seq=1,
        refreshed_at_utc="2026-05-01T03:45:00Z",
    )

    claude = projection["agents"]["claude"]
    assert "rev_pkt_session" in claude["pending_packets_to_me"]
    assert claude["attention_packet_id"] == ""


def test_agent_sync_inventory_uses_canonical_live_pending_predicate() -> None:
    """Agent sync must agree with queue/lifecycle pending truth."""
    projection = build_agent_sync_projection(
        events=[
            {"event_id": "rev_evt_10", "event_type": "packet_posted"},
            {"event_id": "rev_evt_11", "event_type": "packet_posted"},
            {"event_id": "rev_evt_12", "event_type": "packet_posted"},
        ],
        packet_rows=[
            {
                "packet_id": "rev_pkt_durable",
                "latest_event_id": "rev_evt_10",
                "to_agent": "codex",
                "from_agent": "claude",
                "kind": "finding",
                "status": "pending",
                "lifecycle_current_state": "pending",
                "durable_binding": {
                    "status": "inserted",
                    "binding_target_kind": "plan_row",
                },
            },
            {
                "packet_id": "rev_pkt_expired_transport",
                "latest_event_id": "rev_evt_11",
                "to_agent": "codex",
                "from_agent": "claude",
                "kind": "continuation_anchor",
                "status": "pending",
                "lifecycle_current_state": "pending",
                "expires_at_utc": "2000-01-01T00:00:00Z",
                "metadata": {"transport_expiry_explicit": True},
            },
            {
                "packet_id": "rev_pkt_live_notice",
                "latest_event_id": "rev_evt_12",
                "to_agent": "codex",
                "from_agent": "claude",
                "kind": "system_notice",
                "status": "pending",
                "lifecycle_current_state": "pending",
            },
        ],
        registered_agent_ids=["codex", "claude"],
        refresh_seq=1,
        refreshed_at_utc="2026-05-09T00:45:00Z",
    )

    codex = projection["agents"]["codex"]
    assert codex["pending_packets_to_me"] == ["rev_pkt_live_notice"]
