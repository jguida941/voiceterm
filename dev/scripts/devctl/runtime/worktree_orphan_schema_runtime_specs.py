"""Runtime ledger/lease schema specs for worktree-orphan contracts."""

from __future__ import annotations

from .worktree_orphan_schema_support import array, field, object_ref, spec
from .worktree_orphan_types import (
    ACCEPT_ALL_ORPHAN_SCOPES,
    WORK_PUBLICATION_EVENT_KINDS,
)


def runtime_schema_specs():
    return _PUBLICATION_SCHEMA_SPECS + _LEASE_SCHEMA_SPECS + _ACCEPT_ALL_SCHEMA_SPECS


_PUBLICATION_SCHEMA_SPECS = (
    spec(
        "WorkPublicationLedgerHeader",
        (
            "ledger_id",
            "checkout_fingerprint",
            "checkout_path",
            "git_dir",
            "event_log_path",
            "state_path",
        ),
        field("ledger_id"),
        field("checkout_fingerprint"),
        field("checkout_path"),
        field("git_dir"),
        field("event_log_path"),
        field("state_path"),
        field("created_at_utc"),
        field("updated_at_utc"),
    ),
    spec(
        "WorkPublicationLedgerEvent",
        ("event_id", "event_kind", "timestamp_utc", "checkout_fingerprint"),
        field("event_id"),
        field("event_kind", enum_values=WORK_PUBLICATION_EVENT_KINDS),
        field("timestamp_utc"),
        field("checkout_fingerprint"),
        field("commit_sha"),
        field("pipeline_id"),
        field("parent_event_id"),
        field("payload", "object"),
    ),
    spec(
        "PublicationEpisode",
        ("commit_sha", "pipeline_id", "status"),
        field("commit_sha"),
        field("pipeline_id"),
        field("status"),
        field("started_at_utc"),
        field("updated_at_utc"),
        array("carries_unpublished"),
    ),
    spec(
        "WorkPublicationLedger",
        ("schema_version", "contract_id", "header", "episodes"),
        field("schema_version", "integer"),
        field("contract_id", const_value="WorkPublicationLedger"),
        object_ref("header", "WorkPublicationLedgerHeader"),
        array("episodes", item_ref="PublicationEpisode"),
        field("latest_event_id"),
        array("unpublished_commits"),
    ),
)

_LEASE_SCHEMA_SPECS = (
    spec(
        "SessionLease",
        (
            "schema_version",
            "contract_id",
            "lease_id",
            "session_id",
            "agent_role",
            "interaction_mode",
            "started_at_utc",
            "heartbeat_at_utc",
            "pid",
            "rollout_path",
            "declared_scope",
            "baseline_head_sha",
            "baseline_snapshot_id",
        ),
        field("schema_version", "integer"),
        field("contract_id", const_value="SessionLease"),
        field("lease_id"),
        field("session_id"),
        field("agent_role"),
        field("interaction_mode"),
        field("started_at_utc"),
        field("heartbeat_at_utc"),
        field("pid", "integer"),
        field("rollout_path"),
        field("declared_scope"),
        field("baseline_head_sha"),
        field("baseline_snapshot_id"),
    ),
    spec(
        "WorktreeBaseline",
        (
            "schema_version",
            "contract_id",
            "baseline_id",
            "checkout_fingerprint",
            "baseline_head_sha",
            "baseline_snapshot_id",
            "recorded_at_utc",
            "recording_lease_id",
        ),
        field("schema_version", "integer"),
        field("contract_id", const_value="WorktreeBaseline"),
        field("baseline_id"),
        field("checkout_fingerprint"),
        field("baseline_head_sha"),
        field("baseline_snapshot_id"),
        field("recorded_at_utc"),
        field("recording_lease_id"),
    ),
)

_ACCEPT_ALL_SCHEMA_SPECS = (
    spec(
        "AcceptAllOrphansAction",
        (
            "schema_version",
            "contract_id",
            "action_id",
            "reason",
            "scope",
            "operator_identity",
            "authorization_receipt_ref",
        ),
        field("schema_version", "integer"),
        field("contract_id", const_value="AcceptAllOrphansAction"),
        field("action_id"),
        field("reason"),
        field("scope", enum_values=ACCEPT_ALL_ORPHAN_SCOPES),
        field("operator_identity"),
        field("authorization_receipt_ref"),
        field("requested_at_utc"),
    ),
    spec(
        "AcceptAllOrphansReceipt",
        (
            "schema_version",
            "contract_id",
            "receipt_id",
            "action_id",
            "scope",
            "affected_orphan_count",
            "emitted_at_utc",
        ),
        field("schema_version", "integer"),
        field("contract_id", const_value="AcceptAllOrphansReceipt"),
        field("receipt_id"),
        field("action_id"),
        field("scope", enum_values=ACCEPT_ALL_ORPHAN_SCOPES),
        field("affected_orphan_count", "integer"),
        field("emitted_at_utc"),
    ),
)


__all__ = ["runtime_schema_specs"]
