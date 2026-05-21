"""Phase 0.6.A v4.33 (rev_pkt_4707) — plan-currency authority tests.

Plan row: MP-GUARDIR-V4-PHASE-0-6-A-REVIEW-FEEDBACK-POST-OBEDIENCE-S1.
Plan SHA (current): c31a8b20a8ac6cbd6f98f23a370b1c5605dc70d0e436bf3b2fe3aceb65cc08b9.

Tests cover:
- ``current_canonical_plan_sha()`` reading from plan_source_snapshots.jsonl
- ``packet_target_sha()`` parsing ``sha256:<hash>`` and bare hash forms
- ``plan_currency_rank()`` 2-state mapping (current=2, stale=0)
- Integration with ``attention_priority_key`` — current outranks stale
"""

from __future__ import annotations

import json
from pathlib import Path

from dev.scripts.devctl.review_channel.agent_packet_attention_priority import (
    attention_priority_key,
    best_attention_packet,
)
from dev.scripts.devctl.runtime.plan_currency_authority import (
    PLAN_CURRENCY_RANK_CURRENT,
    PLAN_CURRENCY_RANK_LINEAGE_AMENDED,
    PLAN_CURRENCY_RANK_STALE,
    PlanCurrencyContext,
    PlanRevisionRefreshRequired,
    build_plan_revision_refresh_required,
    current_canonical_plan_sha,
    load_plan_currency_context,
    packet_target_sha,
    plan_currency_rank,
)


# ---------------------------------------------------------------------------
# packet_target_sha
# ---------------------------------------------------------------------------


def test_packet_target_sha_extracts_from_sha256_prefix() -> None:
    packet = {"target_revision": "sha256:abc123def456"}
    assert packet_target_sha(packet) == "abc123def456"


def test_packet_target_sha_extracts_bare_hash() -> None:
    packet = {"target_revision": "abc123def456"}
    assert packet_target_sha(packet) == "abc123def456"


def test_packet_target_sha_empty_when_missing() -> None:
    assert packet_target_sha({}) == ""
    assert packet_target_sha({"target_revision": ""}) == ""
    assert packet_target_sha({"target_revision": "   "}) == ""


def test_packet_target_sha_handles_non_mapping() -> None:
    assert packet_target_sha(None) == ""  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# plan_currency_rank
# ---------------------------------------------------------------------------


def test_plan_currency_rank_current_when_sha_matches() -> None:
    packet = {"target_revision": "sha256:current_sha_hash"}
    assert (
        plan_currency_rank(packet, current_plan_sha="current_sha_hash")
        == PLAN_CURRENCY_RANK_CURRENT
    )


def test_plan_currency_rank_stale_when_sha_differs() -> None:
    packet = {"target_revision": "sha256:older_sha"}
    assert (
        plan_currency_rank(packet, current_plan_sha="newer_sha")
        == PLAN_CURRENCY_RANK_STALE
    )


def test_plan_currency_rank_stale_when_no_current_sha_supplied() -> None:
    """Backwards-compat: empty current_plan_sha → all packets stale (0)."""
    packet = {"target_revision": "sha256:any"}
    assert (
        plan_currency_rank(packet, current_plan_sha="")
        == PLAN_CURRENCY_RANK_STALE
    )


def test_plan_currency_rank_stale_when_packet_has_no_target_revision() -> None:
    """Packets without target_revision (legacy, predating v4 typed-rev work)
    are treated as stale — they can't claim current-plan status."""
    packet = {"kind": "finding"}
    assert (
        plan_currency_rank(packet, current_plan_sha="any_sha")
        == PLAN_CURRENCY_RANK_STALE
    )


def test_plan_currency_rank_compares_bare_to_prefixed() -> None:
    """A packet's target_revision can be sha256-prefixed or bare; the rank
    compares the extracted bare SHA against the (bare) current_plan_sha."""
    packet = {"target_revision": "sha256:c31a8b20a8ac6c"}
    assert (
        plan_currency_rank(packet, current_plan_sha="c31a8b20a8ac6c")
        == PLAN_CURRENCY_RANK_CURRENT
    )


# ---------------------------------------------------------------------------
# current_canonical_plan_sha (reads plan_source_snapshots.jsonl)
# ---------------------------------------------------------------------------


def test_current_canonical_plan_sha_returns_latest(tmp_path: Path) -> None:
    """Picks the snapshot with the latest captured_at_utc."""
    state_dir = tmp_path / "dev" / "state"
    state_dir.mkdir(parents=True)
    path = state_dir / "plan_source_snapshots.jsonl"
    rows = [
        {
            "captured_at_utc": "2026-05-20T01:00:00Z",
            "source_doc_sha256": "older_sha",
        },
        {
            "captured_at_utc": "2026-05-20T15:00:00Z",
            "source_doc_sha256": "newer_sha",
        },
        {
            "captured_at_utc": "2026-05-19T22:00:00Z",
            "source_doc_sha256": "oldest_sha",
        },
    ]
    with path.open("w") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")
    assert current_canonical_plan_sha(repo_root=tmp_path) == "newer_sha"


def test_current_canonical_plan_sha_strips_sha256_prefix(tmp_path: Path) -> None:
    """body_hash and source_doc_sha256 may carry sha256: prefix; the
    returned SHA is bare."""
    state_dir = tmp_path / "dev" / "state"
    state_dir.mkdir(parents=True)
    path = state_dir / "plan_source_snapshots.jsonl"
    row = {
        "captured_at_utc": "2026-05-20T15:00:00Z",
        "body_hash": "sha256:prefixed_sha_value",
    }
    path.write_text(json.dumps(row) + "\n")
    assert current_canonical_plan_sha(repo_root=tmp_path) == "prefixed_sha_value"


def test_current_canonical_plan_sha_empty_when_file_missing(tmp_path: Path) -> None:
    assert current_canonical_plan_sha(repo_root=tmp_path) == ""


def test_current_canonical_plan_sha_skips_malformed_rows(tmp_path: Path) -> None:
    state_dir = tmp_path / "dev" / "state"
    state_dir.mkdir(parents=True)
    path = state_dir / "plan_source_snapshots.jsonl"
    contents = (
        "not-json\n"
        + json.dumps({
            "captured_at_utc": "2026-05-20T01:00:00Z",
            "source_doc_sha256": "valid_sha",
        })
        + "\n"
        + "{broken\n"
    )
    path.write_text(contents)
    assert current_canonical_plan_sha(repo_root=tmp_path) == "valid_sha"


def test_current_canonical_plan_sha_skips_rows_without_sha(tmp_path: Path) -> None:
    state_dir = tmp_path / "dev" / "state"
    state_dir.mkdir(parents=True)
    path = state_dir / "plan_source_snapshots.jsonl"
    rows = [
        {"captured_at_utc": "2026-05-20T15:00:00Z"},  # no sha fields
        {
            "captured_at_utc": "2026-05-20T14:00:00Z",
            "source_doc_sha256": "valid_sha",
        },
    ]
    with path.open("w") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")
    assert current_canonical_plan_sha(repo_root=tmp_path) == "valid_sha"


# ---------------------------------------------------------------------------
# Integration: attention_priority_key respects plan-currency
# ---------------------------------------------------------------------------


def test_priority_key_returns_6_tuple_under_v4_33() -> None:
    """v4.33: priority key gained the plan-currency dimension as #1."""
    packet = {"target_revision": "sha256:abc", "kind": "finding"}
    key = attention_priority_key(packet, source_rank=0, index=0)
    assert len(key) == 6
    assert isinstance(key, tuple)


def test_priority_key_plan_currency_dim_is_zero_without_current_sha() -> None:
    """Backwards compat: when current_plan_sha is not passed, the new
    plan-currency dimension is 0 for all packets, preserving v4.32 ordering."""
    packet = {"target_revision": "sha256:abc", "kind": "finding"}
    key = attention_priority_key(packet, source_rank=0, index=0)
    assert key[0] == PLAN_CURRENCY_RANK_STALE  # plan-currency dimension


def test_priority_key_plan_currency_dim_is_current_when_sha_matches() -> None:
    packet = {"target_revision": "sha256:current_sha", "kind": "finding"}
    key = attention_priority_key(
        packet, source_rank=0, index=0, current_plan_sha="current_sha"
    )
    assert key[0] == PLAN_CURRENCY_RANK_CURRENT


def test_best_attention_packet_picks_current_plan_independent_of_order() -> None:
    """v4.33: with current_plan_sha set, the current-plan packet is selected
    regardless of whether it's listed first or last in pending_packets.
    Order-independence is the value v4.33 adds — legacy tiebreaks were
    index-dependent (fragile to insertion order)."""
    current_plan_sha = "current_sha"
    stale_packet = {
        "packet_id": "rev_pkt_stale",
        "target_revision": "sha256:older_sha",
        "kind": "finding",
        "attention_urgency": "blocking",
        "latest_event_id": "rev_evt_50000",
    }
    current_plan_packet = {
        "packet_id": "rev_pkt_current",
        "target_revision": f"sha256:{current_plan_sha}",
        "kind": "finding",
        "attention_urgency": "blocking",
        "latest_event_id": "rev_evt_50000",
    }
    # Stale listed first
    result_a = best_attention_packet(
        active_packet={},
        pending_packets=(stale_packet, current_plan_packet),
        current_plan_sha=current_plan_sha,
    )
    # Current listed first
    result_b = best_attention_packet(
        active_packet={},
        pending_packets=(current_plan_packet, stale_packet),
        current_plan_sha=current_plan_sha,
    )
    assert result_a["packet_id"] == "rev_pkt_current"
    assert result_b["packet_id"] == "rev_pkt_current"


def test_best_attention_packet_current_plan_beats_higher_event_id_stale() -> None:
    """v4.33 stronger claim: a current-plan packet outranks an OLDER-event-id
    stale packet even when the stale one has higher source_rank (active) and
    higher kind_rank — because plan-currency is the new top dimension."""
    current_plan_sha = "current_sha_v4_33"
    # Stale packet, active (source_rank=1), kind=finding (rank=2):
    # legacy priority key = (urgency, command, event_id, kind+source=3, -1)
    stale_active_high_event = {
        "packet_id": "rev_pkt_stale_active",
        "target_revision": "sha256:older_sha",
        "kind": "finding",
        "attention_urgency": "blocking",
        "latest_event_id": "rev_evt_99999",  # highest event id
    }
    # Current packet, pending (source_rank=0), kind=task_progress (rank=1):
    # legacy priority key = (urgency, command, lower_event_id, kind+source=1, 0)
    # Under v4.32, the stale_active would win on both event_id AND kind+source.
    current_lower_event = {
        "packet_id": "rev_pkt_current_pending",
        "target_revision": f"sha256:{current_plan_sha}",
        "kind": "task_progress",
        "attention_urgency": "blocking",
        "latest_event_id": "rev_evt_50000",  # lower event id
    }
    result = best_attention_packet(
        active_packet=stale_active_high_event,
        pending_packets=(current_lower_event,),
        current_plan_sha=current_plan_sha,
    )
    assert result["packet_id"] == "rev_pkt_current_pending", (
        "v4.33: plan-currency dim (rank 2) outranks the stale packet's "
        "advantages across ALL lower dimensions."
    )


def test_best_attention_packet_falls_through_to_event_id_when_all_stale() -> None:
    """v4.33: when no candidates match current_plan_sha, plan-currency is
    tied at 0 for all and existing dimensions decide."""
    current_plan_sha = "nonmatching_current_sha"
    older = {
        "packet_id": "rev_pkt_4001",
        "target_revision": "sha256:older_sha",
        "kind": "finding",
        "latest_event_id": "rev_evt_50000",
    }
    newer = {
        "packet_id": "rev_pkt_4002",
        "target_revision": "sha256:newer_sha",
        "kind": "finding",
        "latest_event_id": "rev_evt_50001",
    }
    result = best_attention_packet(
        active_packet={},
        pending_packets=(older, newer),
        current_plan_sha=current_plan_sha,
    )
    # Both stale (rank 0); newer event id wins via dimension 4
    assert result["packet_id"] == "rev_pkt_4002"


def test_best_attention_packet_falls_through_when_both_current() -> None:
    """v4.33: when BOTH candidates match current_plan_sha (current=2), the
    tiebreak falls to lower dimensions and the newer/active wins."""
    current_plan_sha = "shared_current_sha"
    older = {
        "packet_id": "rev_pkt_4001",
        "target_revision": f"sha256:{current_plan_sha}",
        "kind": "finding",
        "attention_urgency": "blocking",
        "latest_event_id": "rev_evt_50000",
    }
    newer = {
        "packet_id": "rev_pkt_4002",
        "target_revision": f"sha256:{current_plan_sha}",
        "kind": "finding",
        "attention_urgency": "blocking",
        "latest_event_id": "rev_evt_50001",
    }
    result = best_attention_packet(
        active_packet={},
        pending_packets=(older, newer),
        current_plan_sha=current_plan_sha,
    )
    assert result["packet_id"] == "rev_pkt_4002"


def test_best_attention_packet_empty_when_no_candidates() -> None:
    """Empty inputs return empty dict — preserved from v4.32."""
    assert best_attention_packet(
        active_packet={},
        pending_packets=(),
        current_plan_sha="any",
    ) == {}


# ---------------------------------------------------------------------------
# v4.36 SUPERSESSION-AWARE PLAN CURRENCY (codex rev_pkt_4708)
# ---------------------------------------------------------------------------


def test_plan_currency_rank_lineage_amended_when_sha_in_row_lineage() -> None:
    """v4.36: packet's SHA != current canonical, but appears in the target
    row's snapshot lineage → LINEAGE_AMENDED (rank 1)."""
    packet = {
        "target_revision": "sha256:older_lineage_sha",
        "target_ref": "MP-ROW-A",
    }
    rank = plan_currency_rank(
        packet,
        current_plan_sha="latest_canonical_sha",
        row_snapshot_shas={
            "MP-ROW-A": frozenset({"older_lineage_sha", "latest_canonical_sha"}),
        },
    )
    assert rank == PLAN_CURRENCY_RANK_LINEAGE_AMENDED


def test_plan_currency_rank_current_still_wins_over_lineage() -> None:
    """v4.36: exact-current SHA outranks lineage-amended; both inputs work
    together but exact match wins."""
    packet = {
        "target_revision": "sha256:latest_canonical_sha",
        "target_ref": "MP-ROW-A",
    }
    rank = plan_currency_rank(
        packet,
        current_plan_sha="latest_canonical_sha",
        row_snapshot_shas={
            "MP-ROW-A": frozenset({"older_lineage_sha", "latest_canonical_sha"}),
        },
    )
    assert rank == PLAN_CURRENCY_RANK_CURRENT


def test_plan_currency_rank_stale_when_sha_not_in_lineage() -> None:
    """v4.36: packet's SHA neither current nor in its target row's lineage
    → STALE (rank 0). The packet predates the row's tracked history."""
    packet = {
        "target_revision": "sha256:totally_unrelated_sha",
        "target_ref": "MP-ROW-A",
    }
    rank = plan_currency_rank(
        packet,
        current_plan_sha="latest_canonical_sha",
        row_snapshot_shas={
            "MP-ROW-A": frozenset({"older_lineage_sha", "latest_canonical_sha"}),
        },
    )
    assert rank == PLAN_CURRENCY_RANK_STALE


def test_plan_currency_rank_lineage_requires_target_ref() -> None:
    """v4.36: lineage match requires packet's target_ref to be supplied.
    Without it, can't look up the row's lineage."""
    packet_no_ref = {
        "target_revision": "sha256:older_sha",
        # no target_ref
    }
    rank = plan_currency_rank(
        packet_no_ref,
        current_plan_sha="latest_sha",
        row_snapshot_shas={
            "MP-ROW-A": frozenset({"older_sha", "latest_sha"}),
        },
    )
    assert rank == PLAN_CURRENCY_RANK_STALE


def test_plan_currency_rank_lineage_uses_correct_row() -> None:
    """v4.36: lineage lookup must use the packet's target_ref. A SHA present
    in a DIFFERENT row's lineage does not promote."""
    packet = {
        "target_revision": "sha256:row_b_sha",
        "target_ref": "MP-ROW-A",
    }
    # row_b_sha is in MP-ROW-B's lineage, not MP-ROW-A's
    rank = plan_currency_rank(
        packet,
        current_plan_sha="latest_sha",
        row_snapshot_shas={
            "MP-ROW-A": frozenset({"latest_sha"}),
            "MP-ROW-B": frozenset({"row_b_sha", "latest_sha"}),
        },
    )
    assert rank == PLAN_CURRENCY_RANK_STALE


def test_plan_currency_rank_lineage_without_row_snapshots_is_stale() -> None:
    """v4.36 backwards-compat: when caller passes no row_snapshot_shas,
    lineage match doesn't fire; behaves like v4.33 exact-SHA-only."""
    packet = {
        "target_revision": "sha256:older_sha",
        "target_ref": "MP-ROW-A",
    }
    rank = plan_currency_rank(
        packet,
        current_plan_sha="latest_sha",
        # row_snapshot_shas omitted
    )
    assert rank == PLAN_CURRENCY_RANK_STALE


def test_load_plan_currency_context_builds_lineage_map(tmp_path: Path) -> None:
    """v4.36: load_plan_currency_context walks snapshots and assembles
    a per-row SHAs lineage map."""
    state_dir = tmp_path / "dev" / "state"
    state_dir.mkdir(parents=True)
    path = state_dir / "plan_source_snapshots.jsonl"
    rows = [
        {
            "captured_at_utc": "2026-05-20T01:00:00Z",
            "plan_row_id": "MP-ROW-A",
            "body_hash": "sha256:row_a_sha_v1",
        },
        {
            "captured_at_utc": "2026-05-20T08:00:00Z",
            "plan_row_id": "MP-ROW-A",
            "body_hash": "sha256:row_a_sha_v2",
        },
        {
            "captured_at_utc": "2026-05-20T15:00:00Z",
            "plan_row_id": "MP-ROW-B",
            "body_hash": "sha256:row_b_sha_v1",
        },
    ]
    with path.open("w") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")
    ctx = load_plan_currency_context(repo_root=tmp_path)
    assert ctx.current_plan_sha == "row_b_sha_v1"  # latest captured_at
    assert ctx.row_snapshot_shas["MP-ROW-A"] == frozenset(
        {"row_a_sha_v1", "row_a_sha_v2"}
    )
    assert ctx.row_snapshot_shas["MP-ROW-B"] == frozenset({"row_b_sha_v1"})


def test_load_plan_currency_context_empty_when_no_file(tmp_path: Path) -> None:
    ctx = load_plan_currency_context(repo_root=tmp_path)
    assert ctx.current_plan_sha == ""
    assert ctx.row_snapshot_shas == {}
    assert ctx.empty is True


def test_build_plan_revision_refresh_required_carries_typed_fields() -> None:
    """v4.36: the typed refresh-required blocker carries old packet id,
    SHA, latest canonical, target row, and requested kind."""
    packet = {
        "packet_id": "rev_pkt_4707",
        "target_revision": "sha256:older_sha_v33",
        "target_ref": "MP-GUARDIR-V4-PHASE-0-6-A-COMMAND-ENVELOPE-NORMALIZATION-S1",
    }
    blocker = build_plan_revision_refresh_required(
        packet=packet,
        latest_canonical_sha="latest_sha_v36",
    )
    assert isinstance(blocker, PlanRevisionRefreshRequired)
    assert blocker.old_packet_id == "rev_pkt_4707"
    assert blocker.old_packet_sha == "older_sha_v33"
    assert blocker.latest_canonical_sha == "latest_sha_v36"
    assert (
        blocker.target_row_id
        == "MP-GUARDIR-V4-PHASE-0-6-A-COMMAND-ENVELOPE-NORMALIZATION-S1"
    )
    assert blocker.requested_refresh_kind == "task_progress"
    assert blocker.contract_id == "PlanRevisionRefreshRequired"
    payload = blocker.to_dict()
    assert payload["blocker_id"].startswith("plan_revision_refresh:")
    assert "rev_pkt_4707" in payload["blocker_id"]


def test_best_attention_packet_lineage_amended_outranks_stale() -> None:
    """v4.36 LIVE SCENARIO (codex rev_pkt_4708): a packet posted against
    an older revision of its target row (rev_pkt_4707-shaped) must outrank
    a truly stale backlog packet (rev_pkt_4698-shaped) via LINEAGE_AMENDED
    rank."""
    current_canonical = "v4_36_canonical_sha"
    row_lineage = {
        "MP-ROW-A": frozenset({"v4_33_sha", "v4_34_sha", "v4_36_canonical_sha"}),
    }
    lineage_amended_packet = {
        "packet_id": "rev_pkt_4707_shape",
        "target_revision": "sha256:v4_33_sha",  # in lineage, not current
        "target_ref": "MP-ROW-A",
        "kind": "finding",
        "attention_urgency": "blocking",
        "latest_event_id": "rev_evt_50001",
    }
    truly_stale_packet = {
        "packet_id": "rev_pkt_4698_shape",
        "target_revision": "sha256:unrelated_old_sha",
        "target_ref": "MP-ROW-Z",  # different row
        "kind": "task_progress",
        "attention_urgency": "blocking",
        "latest_event_id": "rev_evt_50000",
    }
    result = best_attention_packet(
        active_packet=truly_stale_packet,
        pending_packets=(lineage_amended_packet,),
        current_plan_sha=current_canonical,
        row_snapshot_shas=row_lineage,
    )
    assert result["packet_id"] == "rev_pkt_4707_shape", (
        "v4.36: LINEAGE_AMENDED (rank 1) outranks STALE (rank 0) even when "
        "the stale packet is active (source_rank=1)."
    )


def test_best_attention_packet_current_outranks_both_lineage_and_stale() -> None:
    """v4.36: monotonic ordering CURRENT > LINEAGE_AMENDED > STALE.
    A truly current packet (exact SHA match) wins over a lineage-amended
    candidate, which wins over a truly stale one."""
    current_canonical = "current_sha"
    row_lineage = {
        "MP-ROW-A": frozenset({"old_sha_in_lineage", "current_sha"}),
    }
    current = {
        "packet_id": "current_pkt",
        "target_revision": f"sha256:{current_canonical}",
        "target_ref": "MP-ROW-A",
        "kind": "finding",
        "attention_urgency": "blocking",
    }
    lineage_amended = {
        "packet_id": "lineage_pkt",
        "target_revision": "sha256:old_sha_in_lineage",
        "target_ref": "MP-ROW-A",
        "kind": "finding",
        "attention_urgency": "blocking",
    }
    stale = {
        "packet_id": "stale_pkt",
        "target_revision": "sha256:unrelated",
        "target_ref": "MP-ROW-Z",
        "kind": "finding",
        "attention_urgency": "blocking",
    }
    result = best_attention_packet(
        active_packet={},
        pending_packets=(stale, lineage_amended, current),
        current_plan_sha=current_canonical,
        row_snapshot_shas=row_lineage,
    )
    assert result["packet_id"] == "current_pkt"


def test_v4_36_rev_pkt_4707_lineage_scenario_recreates_codex_directive() -> None:
    """v4.36 (codex rev_pkt_4708 verbatim spec): rev_pkt_4707 posted against
    v4.33 SHA c31a8b20 stays current after v4.36 amendments (SHA 4a6ebf7a)
    to the same target row because c31a8b20 is in the row's snapshot
    lineage."""
    v4_33_sha = "c31a8b20a8ac6cbd6f98f23a370b1c5605dc70d0e436bf3b2fe3aceb65cc08b9"
    v4_36_sha = "4a6ebf7a4315c8fbb31cfb33eb63ee8cb589949e394e14c2e69ba66eac1eb02e"
    row_lineage = {
        "MP-GUARDIR-V4-PHASE-0-6-A-REVIEW-FEEDBACK-POST-OBEDIENCE-S1": frozenset(
            {v4_33_sha, "v4_34_intermediate", "v4_35_intermediate", v4_36_sha}
        ),
    }
    rev_pkt_4707 = {
        "packet_id": "rev_pkt_4707",
        "target_revision": f"sha256:{v4_33_sha}",
        "target_ref": "MP-GUARDIR-V4-PHASE-0-6-A-REVIEW-FEEDBACK-POST-OBEDIENCE-S1",
        "kind": "finding",
        "attention_urgency": "blocking",
    }
    rev_pkt_4698_shape = {
        "packet_id": "rev_pkt_4698_shape",
        "target_revision": "sha256:cb440b6a_v4_29_unrelated_lineage",
        "target_ref": "MP-GUARDIR-V4-PHASE-0-6-A-STARTUP-REPAIR-COMMAND-S1",
        "kind": "task_progress",
        "attention_urgency": "blocking",
    }
    rank_v33 = plan_currency_rank(
        rev_pkt_4707,
        current_plan_sha=v4_36_sha,
        row_snapshot_shas=row_lineage,
    )
    rank_4698 = plan_currency_rank(
        rev_pkt_4698_shape,
        current_plan_sha=v4_36_sha,
        row_snapshot_shas=row_lineage,
    )
    assert rank_v33 == PLAN_CURRENCY_RANK_LINEAGE_AMENDED, (
        "v4.36 directive: rev_pkt_4707 must remain LINEAGE_AMENDED, not "
        "demoted to stale by exact-SHA mismatch."
    )
    assert rank_4698 == PLAN_CURRENCY_RANK_STALE
    # Defense-in-depth: rev_pkt_4707 must win selection over rev_pkt_4698
    result = best_attention_packet(
        active_packet=rev_pkt_4698_shape,
        pending_packets=(rev_pkt_4707,),
        current_plan_sha=v4_36_sha,
        row_snapshot_shas=row_lineage,
    )
    assert result["packet_id"] == "rev_pkt_4707"


def test_plan_currency_context_default_is_empty() -> None:
    """v4.36: default-constructed context is empty (no SHA, no lineage)."""
    ctx = PlanCurrencyContext()
    assert ctx.current_plan_sha == ""
    assert ctx.row_snapshot_shas == {}
    assert ctx.empty is True
    ctx2 = PlanCurrencyContext(current_plan_sha="abc")
    assert ctx2.empty is False


# ---------------------------------------------------------------------------
# v4.37 (rev_pkt_4709) — PlanRevisionRefreshRequired emission on
# PacketAttentionState. Tests build_packet_attention_state directly with
# the new fields; the agent_packet_attention.py wiring is exercised via
# integration-shape construction.
# ---------------------------------------------------------------------------


def test_build_packet_attention_state_carries_refresh_fields() -> None:
    """v4.37: build_packet_attention_state accepts and stores the 5 typed
    refresh-required fields."""
    from dev.scripts.devctl.runtime.reviewer_runtime_models import (
        build_packet_attention_state,
    )
    state = build_packet_attention_state(
        observation_actor_id="claude",
        observation_session_id="sess-claude",
        latest_inbox_event_id="rev_evt_50001",
        latest_attention_packet_id="rev_pkt_4707",
        latest_attention_changed_at_utc="2026-05-21T02:21Z",
        last_observed_event_id="rev_evt_50001",
        last_observed_at_utc="2026-05-21T02:30Z",
        pending_packet_count=1,
        plan_revision_refresh_required=True,
        plan_revision_refresh_old_packet_id="rev_pkt_4707",
        plan_revision_refresh_old_sha="c31a8b20a8ac",
        plan_revision_refresh_latest_sha="4a6ebf7a4315",
        plan_revision_refresh_target_row_id=(
            "MP-GUARDIR-V4-PHASE-0-6-A-REVIEW-FEEDBACK-POST-OBEDIENCE-S1"
        ),
    )
    assert state.plan_revision_refresh_required is True
    assert state.plan_revision_refresh_old_packet_id == "rev_pkt_4707"
    assert state.plan_revision_refresh_old_sha == "c31a8b20a8ac"
    assert state.plan_revision_refresh_latest_sha == "4a6ebf7a4315"
    assert (
        state.plan_revision_refresh_target_row_id
        == "MP-GUARDIR-V4-PHASE-0-6-A-REVIEW-FEEDBACK-POST-OBEDIENCE-S1"
    )
    # When refresh_required is True, pivot_reasons must contain the new
    # entry and wake_required must be True.
    assert "plan_revision_refresh_required" in state.pivot_reasons
    assert state.wake_required is True


def test_build_packet_attention_state_refresh_defaults_false() -> None:
    """v4.37: omitting the refresh fields preserves backwards-compat —
    they default to False/empty, no pivot reason added."""
    from dev.scripts.devctl.runtime.reviewer_runtime_models import (
        build_packet_attention_state,
    )
    state = build_packet_attention_state(
        observation_actor_id="claude",
        observation_session_id="sess-claude",
        latest_inbox_event_id="rev_evt_50001",
        latest_attention_packet_id="rev_pkt_4707",
        latest_attention_changed_at_utc="2026-05-21T02:21Z",
        last_observed_event_id="rev_evt_50001",
        last_observed_at_utc="2026-05-21T02:30Z",
        pending_packet_count=0,
    )
    assert state.plan_revision_refresh_required is False
    assert state.plan_revision_refresh_old_packet_id == ""
    assert state.plan_revision_refresh_old_sha == ""
    assert state.plan_revision_refresh_latest_sha == ""
    assert state.plan_revision_refresh_target_row_id == ""
    assert "plan_revision_refresh_required" not in state.pivot_reasons


def test_build_packet_attention_state_refresh_pivot_reason_appears_once() -> None:
    """v4.37: pivot_reasons stays deduplicated — refresh entry appears only
    once, even when other reasons already set wake_required=True."""
    from dev.scripts.devctl.runtime.reviewer_runtime_models import (
        build_packet_attention_state,
    )
    state = build_packet_attention_state(
        observation_actor_id="claude",
        observation_session_id="sess-claude",
        latest_inbox_event_id="rev_evt_50001",
        latest_attention_packet_id="rev_pkt_4707",
        latest_attention_changed_at_utc="",
        last_observed_event_id="rev_evt_50000",  # behind latest → wake_required
        last_observed_at_utc="",
        pending_packet_count=3,  # also adds pending_packets_unconsumed
        plan_revision_refresh_required=True,
        plan_revision_refresh_old_packet_id="rev_pkt_4707",
        plan_revision_refresh_old_sha="c31a8b20",
        plan_revision_refresh_latest_sha="4a6ebf7a",
        plan_revision_refresh_target_row_id="MP-ROW-A",
    )
    refresh_count = sum(
        1 for reason in state.pivot_reasons
        if reason == "plan_revision_refresh_required"
    )
    assert refresh_count == 1
    assert state.wake_required is True


def test_packet_attention_state_default_has_refresh_fields() -> None:
    """v4.37: the dataclass default-constructor exposes the new fields
    with empty/False defaults, matching the function defaults."""
    from dev.scripts.devctl.runtime.reviewer_runtime_models import (
        PacketAttentionState,
    )
    state = PacketAttentionState()
    assert state.plan_revision_refresh_required is False
    assert state.plan_revision_refresh_old_packet_id == ""
    assert state.plan_revision_refresh_old_sha == ""
    assert state.plan_revision_refresh_latest_sha == ""
    assert state.plan_revision_refresh_target_row_id == ""
