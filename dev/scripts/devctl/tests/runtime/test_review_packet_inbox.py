from __future__ import annotations

from dev.scripts.devctl.runtime.review_packet_inbox import (
    _inbox_command_for_agent,
    _live_packet_ids_by_agent,
    packet_inbox_from_review_state,
    summarize_packet_attention_open_findings,
)


def test_inbox_command_includes_actor_for_arbitrary_provider() -> None:
    """Codex finding rev_pkt_1779 — arbitrary providers must stamp delivery.

    `packet_agents.py` already admits any provider id discovered via
    typed collaboration / registry / session metadata. The inbox-command
    template must follow the same role-symmetric contract: if the agent
    is not one of the known synthetic non-poller targets
    (operator/system), it gets the delivery-stamping `--actor` flag —
    not just the codex/claude/cursor whitelist.
    """
    for provider in ("codex", "claude", "cursor", "gemini", "future-agent"):
        rendered = _inbox_command_for_agent(provider)
        assert f"--target {provider}" in rendered
        assert f"--actor {provider}" in rendered, provider


def test_inbox_command_omits_actor_for_synthetic_non_poller_targets() -> None:
    """Operator/system targets are read-only; stamping delivery would lie.

    These ids do not represent live conductor lanes that can observe a
    packet; emitting `--actor` for them would falsely advance the typed
    delivery-stamp on `action_request` / decision packets, defeating the
    `event_watch_support` deduplication contract.
    """
    for synthetic in ("operator", "system"):
        rendered = _inbox_command_for_agent(synthetic)
        assert f"--target {synthetic}" in rendered
        assert "--actor" not in rendered, synthetic


def test_packet_inbox_drops_persisted_expired_ids_when_live_packets_are_gone() -> None:
    review_state = {
        "packets": [],
        "packet_inbox": {
            "attention_revision": "persisted-rev",
            "agents": [
                {
                    "agent": "codex",
                    "current_instruction_packet_id": "",
                    "latest_finding_packet_id": "rev_pkt_0649",
                    "pending_actionable_packet_ids": [],
                    "expired_unresolved_packet_ids": ["rev_pkt_0649"],
                    "attention_status": "review_needed",
                    "wake_reason": "expired_unresolved_packet",
                    "required_command": "python3 dev/scripts/devctl.py review-channel --action inbox --target codex --status pending --terminal none --format md",
                    "attention_revision": "codex-attention-rev",
                    "delivery_state": "unseen",
                }
            ],
        },
    }

    packet_inbox = packet_inbox_from_review_state(review_state)

    assert packet_inbox is not None
    codex = packet_inbox.for_agent("codex")
    assert codex is not None
    assert codex.latest_finding_packet_id == ""
    assert codex.expired_unresolved_packet_ids == ()
    assert codex.attention_status == "none"
    assert codex.wake_reason == ""


def test_packet_inbox_filters_persisted_expired_ids_to_runtime_transport_packets() -> None:
    review_state = {
        "packets": [
            {
                "packet_id": "rev_pkt_live",
                "kind": "action_request",
                "status": "expired",
                "to_agent": "codex",
                "expires_at_utc": "2000-01-01T00:00:00Z",
            }
        ],
        "packet_inbox": {
            "attention_revision": "persisted-rev",
            "agents": [
                {
                    "agent": "codex",
                    "current_instruction_packet_id": "",
                    "latest_finding_packet_id": "",
                    "pending_actionable_packet_ids": [],
                    "expired_unresolved_packet_ids": [
                        "rev_pkt_live",
                        "rev_pkt_evicted",
                    ],
                    "attention_status": "review_needed",
                    "wake_reason": "expired_unresolved_packet",
                    "required_command": "python3 dev/scripts/devctl.py review-channel --action inbox --target codex --status pending --terminal none --format md",
                    "attention_revision": "codex-attention-rev",
                    "delivery_state": "unseen",
                }
            ],
        },
    }

    packet_inbox = packet_inbox_from_review_state(review_state)

    assert packet_inbox is not None
    codex = packet_inbox.for_agent("codex")
    assert codex is not None
    assert codex.expired_unresolved_packet_ids == ("rev_pkt_live",)


def test_packet_inbox_treats_urgent_attention_metadata_as_actionable() -> None:
    review_state = {
        "packets": [
            {
                "packet_id": "rev_pkt_arch",
                "kind": "task_progress",
                "status": "pending",
                "lifecycle_current_state": "pending",
                "to_agent": "codex",
                "attention_urgency": "urgent",
                "attention_class": "decision",
                "latest_event_id": "rev_evt_urgent",
                "posted_at": "2026-05-11T00:00:00Z",
            }
        ]
    }

    packet_inbox = packet_inbox_from_review_state(review_state)

    assert packet_inbox is not None
    codex = packet_inbox.for_agent("codex")
    assert codex is not None
    assert codex.current_instruction_packet_id == "rev_pkt_arch"
    assert codex.pending_actionable_packet_ids == ("rev_pkt_arch",)
    assert codex.attention_status == "wake_required"
    assert codex.wake_reason == "urgent_attention"


def test_packet_inbox_does_not_treat_archived_pending_as_expired_unresolved() -> None:
    review_state = {
        "packets": [
            {
                "packet_id": "rev_pkt_archived_pending",
                "kind": "finding",
                "status": "pending",
                "to_agent": "codex",
                "expires_at_utc": "2000-01-01T00:00:00Z",
                "lifecycle_current_state": "archived",
                "disposition": {"sink": "archived"},
            }
        ]
    }

    packet_inbox = packet_inbox_from_review_state(review_state)

    assert packet_inbox is not None
    codex = packet_inbox.for_agent("codex")
    assert codex is not None
    assert codex.expired_unresolved_packet_ids == ()
    assert codex.attention_status == "none"
    assert codex.wake_reason == ""


def test_packet_inbox_does_not_treat_archived_expired_as_unresolved() -> None:
    review_state = {
        "packets": [
            {
                "packet_id": "rev_pkt_archived_expired",
                "kind": "finding",
                "status": "expired",
                "to_agent": "codex",
                "expires_at_utc": "2000-01-01T00:00:00Z",
                "lifecycle_current_state": "archived",
                "disposition": {"sink": "archived"},
            }
        ]
    }

    packet_inbox = packet_inbox_from_review_state(review_state)

    assert packet_inbox is not None
    codex = packet_inbox.for_agent("codex")
    assert codex is not None
    assert codex.expired_unresolved_packet_ids == ()
    assert codex.attention_status == "none"
    assert codex.wake_reason == ""


def test_packet_inbox_does_not_treat_durable_archive_as_unresolved() -> None:
    review_state = {
        "packets": [
            {
                "packet_id": "rev_pkt_durable_archive",
                "kind": "finding",
                "status": "pending",
                "to_agent": "codex",
                "expires_at_utc": "2000-01-01T00:00:00Z",
                "lifecycle_current_state": "archived",
                "durable_binding": {
                    "contract_id": "PacketDurableIngestionReceipt",
                    "target_ref": "MP377-P0-PACKET-RELEVANCE-S1",
                },
                "disposition": {
                    "sink": "archived",
                    "archive_classification": "expired_after_durable_binding",
                    "resolution_anchor": (
                        "archive_classification:expired_after_durable_binding"
                    ),
                },
            }
        ]
    }

    packet_inbox = packet_inbox_from_review_state(review_state)

    assert packet_inbox is not None
    codex = packet_inbox.for_agent("codex")
    assert codex is not None
    assert codex.expired_unresolved_packet_ids == ()
    assert codex.attention_status == "none"
    assert codex.wake_reason == ""


def test_packet_inbox_does_not_treat_clock_expired_archive_as_attention() -> None:
    review_state = {
        "packets": [
            {
                "packet_id": "rev_pkt_clock_expired",
                "kind": "finding",
                "status": "pending",
                "to_agent": "codex",
                "expires_at_utc": "2000-01-01T00:00:00Z",
                "lifecycle_current_state": "archived",
                "disposition": {
                    "sink": "archived",
                    "archive_classification": "clock_expired_without_disposition",
                    "resolution_anchor": (
                        "archive_classification:clock_expired_without_disposition"
                    ),
                },
            }
        ]
    }

    packet_inbox = packet_inbox_from_review_state(review_state)

    assert packet_inbox is not None
    codex = packet_inbox.for_agent("codex")
    assert codex is not None
    assert codex.expired_unresolved_packet_ids == ()
    assert codex.attention_status == "none"
    assert codex.wake_reason == ""


def test_packet_inbox_drops_persisted_clock_expired_archive_attention() -> None:
    review_state = {
        "packets": [
            {
                "packet_id": "rev_pkt_clock_expired",
                "kind": "finding",
                "status": "expired",
                "to_agent": "codex",
                "expires_at_utc": "2000-01-01T00:00:00Z",
                "lifecycle_current_state": "archived",
                "disposition": {
                    "sink": "archived",
                    "archive_classification": "clock_expired_without_disposition",
                    "resolution_anchor": (
                        "archive_classification:clock_expired_without_disposition"
                    ),
                },
            },
            {
                "packet_id": "rev_pkt_cursor_live",
                "kind": "instruction",
                "status": "pending",
                "to_agent": "cursor",
                "expires_at_utc": "2999-01-01T00:00:00Z",
            },
        ],
        "packet_inbox": {
            "attention_revision": "persisted-rev",
            "agents": [
                {
                    "agent": "codex",
                    "current_instruction_packet_id": "",
                    "latest_finding_packet_id": "",
                    "pending_actionable_packet_ids": [],
                    "expired_unresolved_packet_ids": ["rev_pkt_clock_expired"],
                    "attention_status": "review_needed",
                    "wake_reason": "expired_unresolved_packet",
                    "required_command": "python3 dev/scripts/devctl.py develop audit-packets --format md",
                    "attention_revision": "codex-attention-rev",
                    "delivery_state": "unseen",
                }
            ],
        },
    }

    packet_inbox = packet_inbox_from_review_state(review_state)

    assert packet_inbox is not None
    codex = packet_inbox.for_agent("codex")
    assert codex is not None
    assert codex.expired_unresolved_packet_ids == ()
    assert codex.attention_status == "none"
    assert codex.wake_reason == ""


def test_packet_inbox_does_not_revive_archived_rows_from_persisted_attention() -> None:
    review_state = {
        "packets": [
            {
                "packet_id": "rev_pkt_archived_pending",
                "kind": "finding",
                "status": "pending",
                "to_agent": "codex",
                "expires_at_utc": "2000-01-01T00:00:00Z",
                "lifecycle_current_state": "archived",
                "disposition": {"sink": "archived"},
            }
        ],
        "packet_inbox": {
            "attention_revision": "persisted-rev",
            "agents": [
                {
                    "agent": "codex",
                    "current_instruction_packet_id": "",
                    "latest_finding_packet_id": "",
                    "pending_actionable_packet_ids": [],
                    "expired_unresolved_packet_ids": ["rev_pkt_archived_pending"],
                    "attention_status": "review_needed",
                    "wake_reason": "expired_unresolved_packet",
                    "required_command": "python3 dev/scripts/devctl.py develop audit-packets --format md",
                    "attention_revision": "codex-attention-rev",
                    "delivery_state": "unseen",
                }
            ],
        },
    }

    packet_inbox = packet_inbox_from_review_state(review_state)

    assert packet_inbox is not None
    codex = packet_inbox.for_agent("codex")
    assert codex is not None
    assert codex.expired_unresolved_packet_ids == ()
    assert codex.attention_status == "none"
    assert codex.wake_reason == ""


def test_open_findings_summary_does_not_revive_evicted_expired_packets() -> None:
    review_state = {
        "packets": [],
        "queue": {
            "pending_total": 0,
            "stale_packet_count": 0,
        },
        "packet_inbox": {
            "attention_revision": "persisted-rev",
            "agents": [
                {
                    "agent": "codex",
                    "current_instruction_packet_id": "",
                    "latest_finding_packet_id": "rev_pkt_0649",
                    "pending_actionable_packet_ids": [],
                    "expired_unresolved_packet_ids": ["rev_pkt_0649"],
                    "attention_status": "review_needed",
                    "wake_reason": "expired_unresolved_packet",
                    "required_command": "python3 dev/scripts/devctl.py review-channel --action inbox --target codex --status pending --terminal none --format md",
                    "attention_revision": "codex-attention-rev",
                    "delivery_state": "unseen",
                }
            ],
        },
    }

    summary = summarize_packet_attention_open_findings(
        review_state,
        fallback="none",
        agent="codex",
    )

    assert summary == "none"


def test_open_findings_summary_drops_stale_packet_summary_when_packet_truth_is_clear() -> None:
    review_state = {
        "packets": [
            {
                "packet_id": "rev_pkt_archived_expired",
                "kind": "finding",
                "status": "expired",
                "to_agent": "codex",
                "lifecycle_current_state": "archived",
                "disposition": {"sink": "archived"},
            }
        ],
        "queue": {
            "pending_total": 0,
            "stale_packet_count": 0,
        },
    }

    summary = summarize_packet_attention_open_findings(
        review_state,
        fallback="725 expired unresolved review packet(s)",
        agent="codex",
    )

    assert summary == "none"


def test_packet_inbox_indexes_current_instruction_by_target_agent() -> None:
    review_state = {
        "packets": [
            {
                "packet_id": "rev_pkt_cursor_1",
                "status": "pending",
                "summary": "Cursor owns the active instruction",
                "body": "Cursor owns the active instruction",
                "kind": "instruction",
                "from_agent": "codex",
                "to_agent": "cursor",
                "requested_action": "continue",
                "expires_at_utc": "2999-01-01T00:00:00Z",
            }
        ]
    }

    packet_inbox = packet_inbox_from_review_state(review_state)

    assert packet_inbox is not None
    cursor = packet_inbox.for_agent("cursor")
    codex = packet_inbox.for_agent("codex")
    assert cursor is not None
    assert codex is not None
    assert cursor.current_instruction_packet_id == "rev_pkt_cursor_1"
    assert codex.current_instruction_packet_id == ""


def test_packet_inbox_keeps_acked_action_request_active_while_executing() -> None:
    review_state = {
        "packets": [
            {
                "packet_id": "rev_pkt_1818",
                "status": "acked",
                "summary": "Run governed checkpoint",
                "body": "Run governed checkpoint",
                "kind": "action_request",
                "from_agent": "codex",
                "to_agent": "claude",
                "requested_action": "run_checkpoint",
                "delivery_observed_at_utc": "2026-04-25T02:22:03Z",
                "delivery_observed_by": "claude",
                "execution_started_at_utc": "2026-04-25T02:23:03Z",
                "execution_started_by": "claude",
                "expires_at_utc": "2999-01-01T00:00:00Z",
            }
        ]
    }

    packet_inbox = packet_inbox_from_review_state(review_state)

    assert packet_inbox is not None
    claude = packet_inbox.for_agent("claude")
    assert claude is not None
    assert claude.current_instruction_packet_id == "rev_pkt_1818"
    assert claude.pending_actionable_packet_ids == ()
    assert claude.delivery_state == "seen"


def test_per_agent_live_packet_merge_uses_pending_truth_not_control_activity() -> None:
    """Persisted inbox merge should not let acked control rows mask pending packets."""
    live_by_agent = _live_packet_ids_by_agent(
        [
            {
                "packet_id": "rev_pkt_pending_finding",
                "kind": "finding",
                "status": "pending",
                "to_agent": "claude",
                "expires_at_utc": "2999-01-01T00:00:00Z",
            },
            {
                "packet_id": "rev_pkt_executing_action",
                "kind": "action_request",
                "status": "acked",
                "to_agent": "claude",
                "requested_action": "run_checkpoint",
                "delivery_observed_at_utc": "2026-04-25T02:22:03Z",
                "delivery_observed_by": "claude",
                "execution_started_at_utc": "2026-04-25T02:23:03Z",
                "execution_started_by": "claude",
                "expires_at_utc": "2999-01-01T00:00:00Z",
            },
        ]
    )

    assert live_by_agent["claude"] == frozenset({"rev_pkt_pending_finding"})


def test_failed_pending_action_request_does_not_drive_inbox() -> None:
    review_state = {
        "packets": [
            {
                "packet_id": "rev_pkt_failed",
                "status": "pending",
                "summary": "Run governed checkpoint",
                "body": "Run governed checkpoint",
                "kind": "action_request",
                "from_agent": "codex",
                "to_agent": "claude",
                "requested_action": "stage_commit_pipeline",
                "execution_failed_at_utc": "2026-04-29T13:00:00Z",
                "execution_failed_reason": "pending_reviewer_packets",
                "expires_at_utc": "2999-01-01T00:00:00Z",
            }
        ]
    }

    packet_inbox = packet_inbox_from_review_state(review_state)

    assert packet_inbox is not None
    claude = packet_inbox.for_agent("claude")
    assert claude is not None
    assert claude.current_instruction_packet_id == ""
    assert claude.pending_actionable_packet_ids == ()
    assert claude.attention_status == "none"
    assert claude.delivery_state == "idle"
