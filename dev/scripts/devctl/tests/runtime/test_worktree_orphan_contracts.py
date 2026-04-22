"""Typed-seam tests for worktree-orphan slice-1 contracts."""

from __future__ import annotations

from dev.scripts.devctl.runtime.worktree_orphan_contracts import (
    ORPHAN_SOURCE_KINDS,
    ACCEPT_ALL_ORPHAN_SCOPES,
    AcceptAllOrphansAction,
    AcceptAllOrphansReceipt,
    CheckoutInventory,
    CheckoutInventoryClassification,
    CheckoutInventoryRow,
    OrphanReconciliationDecision,
    OrphanSnapshot,
    OrphanSnapshotStats,
    OrphanSource,
    OrphanSourceClassification,
    OrphanSourceDecision,
    PublicationEpisode,
    SessionLease,
    WorkPublicationLedger,
    WorkPublicationLedgerEvent,
    WorkPublicationLedgerHeader,
    WorktreeBaseline,
    accept_all_orphans_action_from_mapping,
    accept_all_orphans_receipt_from_mapping,
    checkout_inventory_from_mapping,
    contract_json_schemas,
    orphan_reconciliation_decision_from_mapping,
    orphan_snapshot_from_mapping,
    orphan_source_from_mapping,
    publication_episode_from_mapping,
    session_lease_from_mapping,
    work_publication_event_from_mapping,
    work_publication_ledger_from_mapping,
    worktree_baseline_from_mapping,
)


def test_orphan_snapshot_minimum_example_matches_schema_and_round_trips() -> None:
    source = OrphanSource(
        source_id="src-sibling-1",
        source_kind="unregistered_sibling_clone",
        source_ref="repo-copy:/Users/me/codex-voice 2",
        path="/Users/me/codex-voice 2",
        branch="feature/old",
        dirty_path_count=12,
        untracked_path_count=3,
        unpublished_commit_shas=("abc123",),
        classification=OrphanSourceClassification(
            state="unmanaged_shadow",
            known_governed_auto_sync=False,
            load_bearing=True,
            governance_owner="operator",
            notes=("sibling clone found beside primary repo",),
        ),
        evidence_refs=("filesystem_scan:bounded_siblings",),
    )
    snapshot = OrphanSnapshot(
        snapshot_id="orphan-snap-1",
        snapshot_hash="sha256:snap",
        scan_at_utc="2026-04-22T14:00:00Z",
        scan_trigger="startup",
        scan_scope_applied="bounded_siblings",
        primary_repo_identity="repo:sha256:primary",
        sources=(source,),
        stats=OrphanSnapshotStats(
            total_sources=1,
            unresolved_sources=1,
            dirty_sources=1,
            unpublished_sources=1,
            load_bearing_sources=1,
        ),
        load_bearing=True,
    )

    payload = snapshot.to_dict()
    _assert_minimum_schema(contract_json_schemas()["OrphanSnapshot"], payload)
    restored = orphan_snapshot_from_mapping(payload)

    assert restored == snapshot
    assert restored is not None
    assert restored.sources[0].source_kind == "unregistered_sibling_clone"
    assert restored.sources[0].classification.load_bearing is True


def test_orphan_source_variants_round_trip_through_discriminator() -> None:
    for kind in ORPHAN_SOURCE_KINDS:
        source = OrphanSource(
            source_id=f"src-{kind}",
            source_kind=kind,
            source_ref=f"{kind}:ref",
            classification=OrphanSourceClassification(
                state="classified",
                known_governed_auto_sync=(kind == "current_checkout"),
                load_bearing=False,
            ),
        )

        restored = orphan_source_from_mapping(source.to_dict())

        assert restored == source
        assert restored is not None
        assert restored.source_kind == kind


def test_reconciliation_decision_and_accept_all_action_schema_round_trip() -> None:
    source_decision = OrphanSourceDecision(
        source_ref="repo-copy:/Users/me/codex-voice 2",
        chosen_action="archive_after_user_approval",
        action_args={"archive_root": "dev/archive/orphans"},
        rationale="old sibling copy",
    )
    decision = OrphanReconciliationDecision(
        decision_id="orphan-decision-1",
        responds_to_snapshot_hash="sha256:snap",
        per_source_decisions=(source_decision,),
        operator_identity="operator:jguida",
        authorization_receipt_ref="receipt:operator-1",
        governed_execution_plan_id="orphan-plan-1",
        decided_at_utc="2026-04-22T14:02:00Z",
    )
    action = AcceptAllOrphansAction(
        action_id="accept-all-1",
        reason="first deployment classification",
        scope="worktree",
        operator_identity="operator:jguida",
        authorization_receipt_ref="receipt:operator-1",
        requested_at_utc="2026-04-22T14:03:00Z",
    )
    receipt = AcceptAllOrphansReceipt(
        receipt_id="accept-all-receipt-1",
        action_id=action.action_id,
        scope="worktree",
        affected_orphan_count=57,
        emitted_at_utc="2026-04-22T14:04:00Z",
    )

    schemas = contract_json_schemas()
    _assert_minimum_schema(schemas["OrphanReconciliationDecision"], decision.to_dict())
    _assert_minimum_schema(schemas["AcceptAllOrphansAction"], action.to_dict())
    _assert_minimum_schema(schemas["AcceptAllOrphansReceipt"], receipt.to_dict())

    assert orphan_reconciliation_decision_from_mapping(decision.to_dict()) == decision
    assert accept_all_orphans_action_from_mapping(action.to_dict()) == action
    assert accept_all_orphans_receipt_from_mapping(receipt.to_dict()) == receipt
    assert action.scope in ACCEPT_ALL_ORPHAN_SCOPES


def test_checkout_inventory_preserves_governed_auto_sync_classification() -> None:
    inventory = CheckoutInventory(
        inventory_id="inventory-1",
        generated_at_utc="2026-04-22T14:05:00Z",
        inventory_scope="bounded_siblings",
        filesystem_scan_ref="scan:bounded-siblings-1",
        ledger_headers_ref="ledger_headers:1",
        rows=(
            CheckoutInventoryRow(
                row_id="row-primary",
                state="managed",
                checkout_path="/Users/me/codex-voice",
                checkout_fingerprint="checkout:sha256:primary",
                repo_identity="repo:sha256:primary",
                ledger_header_ref="ledger:primary",
                source_refs=("current_checkout",),
                classification=CheckoutInventoryClassification(
                    known_governed_auto_sync=True,
                    ownership="governed_projection",
                    reason="bridge.md compatibility auto-sync",
                    evidence_refs=("bridge.md",),
                ),
            ),
        ),
    )

    payload = inventory.to_dict()
    _assert_minimum_schema(contract_json_schemas()["CheckoutInventory"], payload)
    restored = checkout_inventory_from_mapping(payload)

    assert restored == inventory
    assert restored is not None
    assert restored.rows[0].classification.known_governed_auto_sync is True


def test_publication_ledger_lease_and_baseline_contracts_round_trip() -> None:
    header = WorkPublicationLedgerHeader(
        ledger_id="ledger-1",
        checkout_fingerprint="checkout:sha256:primary",
        checkout_path="/Users/me/codex-voice",
        git_dir="/Users/me/codex-voice/.git",
        event_log_path="dev/reports/orphans/ledger.events.jsonl",
        state_path="dev/reports/orphans/ledger.state.json",
    )
    event = WorkPublicationLedgerEvent(
        event_id="event-1",
        event_kind="commit_recorded",
        timestamp_utc="2026-04-22T14:06:00Z",
        checkout_fingerprint=header.checkout_fingerprint,
        commit_sha="abc123",
        pipeline_id="pipeline-1",
    )
    episode = PublicationEpisode(
        commit_sha="abc123",
        pipeline_id="pipeline-1",
        status="commit_recorded",
        carries_unpublished=("def456",),
    )
    ledger = WorkPublicationLedger(
        header=header,
        episodes=(episode,),
        latest_event_id=event.event_id,
        unpublished_commits=("def456",),
    )
    lease = SessionLease(
        lease_id="lease-1",
        session_id="local-review",
        agent_role="reviewer",
        interaction_mode="local_terminal",
        started_at_utc="2026-04-22T14:07:00Z",
        heartbeat_at_utc="2026-04-22T14:08:00Z",
        pid=1234,
        rollout_path="~/.codex/sessions/rollout.jsonl",
        declared_scope="MP-377",
        baseline_head_sha="caed14d",
        baseline_snapshot_id="snap-1",
    )
    baseline = WorktreeBaseline(
        baseline_id="baseline-1",
        checkout_fingerprint=header.checkout_fingerprint,
        baseline_head_sha="caed14d",
        baseline_snapshot_id="snap-1",
        recorded_at_utc="2026-04-22T14:09:00Z",
        recording_lease_id=lease.lease_id,
    )

    schemas = contract_json_schemas()
    _assert_minimum_schema(schemas["WorkPublicationLedgerEvent"], event.to_dict())
    _assert_minimum_schema(schemas["WorkPublicationLedger"], ledger.to_dict())
    _assert_minimum_schema(schemas["SessionLease"], lease.to_dict())
    _assert_minimum_schema(schemas["WorktreeBaseline"], baseline.to_dict())

    assert work_publication_event_from_mapping(event.to_dict()) == event
    assert publication_episode_from_mapping(episode.to_dict()) == episode
    assert work_publication_ledger_from_mapping(ledger.to_dict()) == ledger
    assert session_lease_from_mapping(lease.to_dict()) == lease
    assert worktree_baseline_from_mapping(baseline.to_dict()) == baseline


def test_contract_json_schemas_cover_slice_one_contracts() -> None:
    schemas = contract_json_schemas()

    for contract_id in {
        "OrphanSnapshot",
        "OrphanSource",
        "OrphanReconciliationDecision",
        "CheckoutInventory",
        "WorkPublicationLedger",
        "WorkPublicationLedgerEvent",
        "SessionLease",
        "WorktreeBaseline",
        "AcceptAllOrphansAction",
        "AcceptAllOrphansReceipt",
    }:
        assert contract_id in schemas
        assert schemas[contract_id]["title"] == contract_id


def _assert_minimum_schema(
    schema: dict[str, object],
    payload: dict[str, object],
) -> None:
    assert schema["type"] == "object"
    properties = schema["properties"]
    assert isinstance(properties, dict)
    for key in schema["required"]:
        assert key in properties
        assert key in payload
