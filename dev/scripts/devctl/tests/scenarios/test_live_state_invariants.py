"""Live-state semantic TDD invariants for `devctl review-channel sync-status`.

These tests run the actual `devctl review-channel --action sync-status` command
against the live repo state and assert internal-consistency invariants on its
JSON output. A failure is the structured semantic receipt: pytest's
`AssertionError` message names the conflicting fields so the bug is readable
in one line.

Per the Live-State Semantic TDD plan (Phase B), Phase B starts with TWO
intra-command invariants (no cross-command coupling). Both invariants read
the actual emitted JSON paths from sync-status:

  Invariant 1 — value-side contradiction check:
    `awaiting_reviewer_ack` barrier exists ⇒ some attention signal active
    in the SAME output (unopened body packet count, pending count, or
    `attention_status`).

  Invariant 2 — contract-shape check:
    `coordination_state.coordination_topology` must not emit deprecated
    AGENT-COUNTING labels (`multi_agent_active`, `single_agent_active`,
    `no_active_agents`) without a typed migration-debt note. Per the
    AntiDumbass amendment in `delete_after_ingest.md` and operator
    directive, topology is role-based — agent counts are NOT topology.
    This catches the architectural smell at every sync-status emission.

Field paths read:
  - `output["work_board"]["barriers"]` (lane barriers)
  - `output["packet_attention"]["unopened_body_packet_count"]`
  - `output["packet_attention"]["pending_packet_count"]`
  - `output["coordination_state"]["attention_status"]`
  - `output["coordination_state"]["coordination_topology"]`
  - `output["coordination_state"]["notes"]` (migration-debt
    acknowledgment surface)

Reducer source files:
  - dev/scripts/devctl/review_channel/coordination_state_projection.py:24-77
    (the projection emitted as `coordination_state` in sync-status output)
  - dev/scripts/devctl/platform/coordination_topology_models.py:65
    (the snapshot — SEPARATE shape, NOT the projection)

This file is NOT yet wired into `_DEVCTL_TEST_TARGETS` per plan Phase B
sequencing: tests are run manually until green, then wired in Phase D.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[5]


def _run_sync_status() -> dict:
    """Run `devctl review-channel --action sync-status` and return parsed JSON.

    Sets `DEVCTL_NO_ARTIFACT_WRITES=1` so the probe does not pollute typed
    receipt stores during a test run.
    """
    env = dict(os.environ)
    env["DEVCTL_NO_ARTIFACT_WRITES"] = "1"
    result = subprocess.run(
        [
            sys.executable,
            "dev/scripts/devctl.py",
            "review-channel",
            "--action",
            "sync-status",
            "--terminal",
            "none",
            "--format",
            "json",
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        env=env,
        timeout=60,
    )
    assert result.returncode == 0, (
        f"sync-status exited {result.returncode}; stderr:\n{result.stderr[:1000]}"
    )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(
            f"sync-status output is not valid JSON: {exc}\n"
            f"first 500 chars: {result.stdout[:500]}"
        ) from exc


def _awaiting_reviewer_ack_barriers(output: dict) -> list[dict]:
    """Return all lane barrier rows with kind=awaiting_reviewer_ack."""
    work_board = output.get("work_board") or {}
    barriers = work_board.get("barriers") or []
    return [
        barrier
        for barrier in barriers
        if isinstance(barrier, dict)
        and barrier.get("kind") == "awaiting_reviewer_ack"
    ]


# ---------------------------------------------------------------------------
# Invariant 1 — sync_status_awaiting_reviewer_ack_requires_attention
# ---------------------------------------------------------------------------

def test_sync_status_awaiting_reviewer_ack_requires_attention():
    """If sync-status lists an awaiting_reviewer_ack lane barrier, the SAME
    output must also expose an attention signal (non-zero unopened body
    packet count OR `attention_status` indicating review/checkpoint/repair).

    The contradiction this catches: sync-status output that says
    `attention_status=inactive` AND `unopened_body_packet_count=0` while
    SIMULTANEOUSLY listing a lane barrier where a packet is awaiting
    reviewer ack. That is self-contradictory.
    """
    output = _run_sync_status()
    barriers = _awaiting_reviewer_ack_barriers(output)
    if not barriers:
        pytest.skip("no awaiting_reviewer_ack barriers on this live state")

    packet_attention = output.get("packet_attention") or {}
    unopened = int(packet_attention.get("unopened_body_packet_count") or 0)
    pending_count = int(packet_attention.get("pending_packet_count") or 0)
    coordination_state = output.get("coordination_state") or {}
    attention_status = coordination_state.get("attention_status") or ""

    attention_active_terms = {
        "active",
        "review_required",
        "checkpoint_required",
        "repair_required",
        "blocked",
        "wake_required",
    }
    attention_active = (
        unopened > 0
        or pending_count > 0
        or attention_status in attention_active_terms
    )

    assert attention_active, (
        "INVARIANT VIOLATED: sync_status_awaiting_reviewer_ack_requires_attention\n"
        f"  awaiting_reviewer_ack barriers: {len(barriers)} "
        f"(targets: {[b.get('target_packet_id') for b in barriers[:5]]})\n"
        f"  packet_attention.unopened_body_packet_count: {unopened}\n"
        f"  packet_attention.pending_packet_count: {pending_count}\n"
        f"  coordination_state.attention_status: {attention_status!r}\n"
        "  Either at least one attention signal must be active (unopened>0, "
        "pending>0, or attention_status in {active, review_required, "
        "checkpoint_required, repair_required, blocked, wake_required}), or "
        "the lane barriers must be cleared. Same-output contradiction."
    )


# ---------------------------------------------------------------------------
# Invariants 2a / 2b — coordination_topology smell, two-test split
# ---------------------------------------------------------------------------
#
# Per the Pro-architecture-review two-test split (durable plan
# "Phase B revised — TWO-test split"):
#
#   2a (current-safety quarantine): passes today; protects against
#       deprecated agent-counting labels being used as canonical AUTHORITY
#       even if they remain in the projection. Detects regression where a
#       deprecated label starts driving authority_mode / recovery_eligibility
#       / final-response permission.
#
#   2b (target architecture): @pytest.mark.xfail(strict=True) — stays RED
#       as a permanent visible ratchet against the deprecated enum existing
#       AT ALL in coordination_state.coordination_topology. Lifts only when
#       phase 6 remediation replaces the Literal with role-based vocabulary.
#       NOT wired into check-router; not a blocking gate input.
#
# Why this is the right shape (per durable plan):
#   - 2a is "do not bless the broken model" with current-safety teeth
#   - 2b is "the broken model itself is the bug" as visible debt
#   - Together they prevent regression AND drive migration without
#     silencing either signal.

_DEPRECATED_AGENT_COUNTING_TOPOLOGY_LABELS = frozenset({
    "single_agent",
    "dual_agent",
    "single_agent_active",
    "multi_agent_active",
    "no_active_agents",
    "active_dual_agent",
    "dual_agent_active",
})

# Fields that, if driven by a deprecated topology label, would constitute
# the broken vocabulary becoming canonical authority. Source contract:
# review_channel/coordination_state_projection.py — these are the OTHER
# fields in CoordinationStateProjection besides coordination_topology.
_AUTHORITY_FIELDS_THAT_MUST_NOT_BE_DRIVEN_BY_DEPRECATED_TOPOLOGY = (
    "authority_mode",
    "recovery_eligibility",
)


def test_sync_status_agent_count_topology_must_be_quarantined():
    """Invariant 2a — CURRENT SAFETY (passes today, regression guard).

    If `coordination_state.coordination_topology` is one of the deprecated
    agent-counting labels (`single_agent`, `dual_agent`, `single_agent_active`,
    `multi_agent_active`, `no_active_agents`, ...), the SAME output MUST NOT
    let that deprecated value escape into canonical authority fields:

      - `authority_mode` MUST NOT echo the deprecated label verbatim
      - `recovery_eligibility` MUST NOT echo the deprecated label verbatim
      - `legacy_authority_label` / `legacy_reviewer_mode` MAY hold the old
        vocabulary (those are explicit compatibility fields)

    The architecture intent: agent-count topology is migration debt; it can
    still APPEAR in `coordination_topology` while phase 6 remediation is
    pending, but it MUST NOT drive authority decisions. This test catches
    regression where a consumer starts treating the deprecated label as
    canonical authority.

    Source:
      - dev/scripts/devctl/review_channel/coordination_state_projection.py:24-29
        (the deprecated `CoordinationTopology` Literal)
      - dev/scripts/devctl/review_channel/coordination_state_projection.py:32-37
        (the typed `AuthorityMode` Literal — does NOT contain deprecated topology)
      - delete_after_ingest.md lines 1345-1370, 1713 (architecture rule)
      - dev/state/topology_hardcode_inventory.jsonl (155 inventoried sites)
    """
    output = _run_sync_status()
    coordination_state = output.get("coordination_state") or {}
    topology = coordination_state.get("coordination_topology") or ""
    if topology not in _DEPRECATED_AGENT_COUNTING_TOPOLOGY_LABELS:
        pytest.skip(
            f"coordination_topology={topology!r} is not a deprecated "
            "agent-count label — invariant 2a not in scope"
        )

    leaks = []
    for field_name in _AUTHORITY_FIELDS_THAT_MUST_NOT_BE_DRIVEN_BY_DEPRECATED_TOPOLOGY:
        value = coordination_state.get(field_name) or ""
        if value in _DEPRECATED_AGENT_COUNTING_TOPOLOGY_LABELS:
            leaks.append((field_name, value))

    assert not leaks, (
        "INVARIANT VIOLATED: sync_status_agent_count_topology_must_be_quarantined\n"
        f"  coordination_state.coordination_topology: {topology!r}\n"
        f"  authority fields leaking deprecated topology: {leaks}\n"
        "  Deprecated agent-count topology labels MUST NOT drive canonical\n"
        "  authority fields. Per delete_after_ingest.md 1345-1370 / 1713 and\n"
        "  the AntiDumbass amendment, authority lives in role/session-typed\n"
        "  state, NOT in agent-count topology labels. Legacy compatibility\n"
        "  fields (legacy_authority_label, legacy_reviewer_mode) MAY carry\n"
        "  the old vocabulary; authority_mode and recovery_eligibility MUST\n"
        "  NOT. Phase 6 remediation is the durable fix; this test is the\n"
        "  near-term regression guard."
    )


def test_sync_status_does_not_promote_agent_count_topology_as_authority():
    """Invariant 2b — TARGET ARCHITECTURE (xfail-strict ratchet until phase 6).

    `coordination_state.coordination_topology` MUST NOT be any of the
    deprecated agent-counting labels at all. Canonical coordination must
    be role/authority/session based and agent-agnostic.

    Allowed values:
      - `unknown` (fail-closed default per rev_pkt_2298)
      - role-based shape, e.g. `typed_role_topology[reviewer:claude;implementer:codex]`
        from `runtime/role_topology.py:97-105` (`typed_role_topology_label`)
      - other future role/authority/session-graph vocabulary

    Forbidden values (the current broken Literal):
      - `single_agent`, `dual_agent`, `single_agent_active`,
        `multi_agent_active`, `no_active_agents`, `active_dual_agent`

    `observed_runtime.active_actor_count` continues to live as evidence; it
    just CANNOT be the topology authority answer.

    This test stays RED as a permanent visible ratchet against the
    deprecated `CoordinationTopology = Literal[...]` at
    `dev/scripts/devctl/review_channel/coordination_state_projection.py:24-29`.
    The strict-xfail marker means: if the topology stops emitting deprecated
    labels (i.e. phase 6 remediation landed), THIS TEST WILL FAIL by xpassing
    — forcing operator review of the migration. That is intentional.

    Pro-architecture-review target-state surface (durable plan):
      {
        "coordination_state": {
          "coordination_model": "role_authority_session_graph",
          "authority_mode": "review_gated",
          "runtime_posture": "active",
          "observed_runtime": {"active_actor_count": 2, ...},
          "role_assignments": [
            {"provider": "claude", "role": "implementer"},
            {"provider": "codex", "role": "reviewer"}
          ],
          "legacy_topology_label": "multi_agent_active"
        }
      }
    """
    output = _run_sync_status()
    coordination_state = output.get("coordination_state") or {}
    topology = coordination_state.get("coordination_topology") or ""

    assert topology not in _DEPRECATED_AGENT_COUNTING_TOPOLOGY_LABELS, (
        "INVARIANT VIOLATED: "
        "sync_status_does_not_promote_agent_count_topology_as_authority\n"
        f"  coordination_state.coordination_topology: {topology!r}\n"
        "  This is a deprecated agent-counting label being emitted as live\n"
        "  topology. Per delete_after_ingest.md AntiDumbass amendment\n"
        "  (lines 731-870, 1345-1370, 1713), canonical coordination must be\n"
        "  role/authority/session based and agent-agnostic.\n"
        "  active_actor_count belongs under observed_runtime as EVIDENCE only.\n"
        "  The CoordinationTopology Literal at\n"
        "  dev/scripts/devctl/review_channel/coordination_state_projection.py:24-29\n"
        "  is migration debt; phase 6 remediation per\n"
        "  dev/state/topology_hardcode_inventory.jsonl (155 inventoried sites)\n"
        "  replaces it with role-based vocabulary.\n"
        "  Operator directive: 'There should be no single agent. There should\n"
        "  be no dual agent. That's the fucking problem.'"
    )


# ---------------------------------------------------------------------------
# Invariant 3 — gate_blocker_source_must_match_unsatisfied_ground_truth_receipt
#
# Dogfood invariant: when the latest GroundTruthProbeRunReceipt verdict is
# 'unsatisfied' AND develop next --enforce-final-response-gate blocks
# completion, the gate's reported blocker source MUST cite the receipt
# (source == 'ground_truth_probe_receipt'), NOT an orchestration signal
# that would silently hide the typed proof from the agent.
#
# Why this exists: during E2-minimal execution we observed the gate
# blocking with source='continuation_signal' (orchestration check) even
# though an unsatisfied ground-truth receipt was sitting in the ledger.
# A consuming agent reading the gate output would never see the
# receipt-based block reason — they'd see "orchestration step required"
# instead. That's the EXACT failure mode the live-state TDD system is
# designed to catch: surface contradicts its own deeper evidence.
# ---------------------------------------------------------------------------

import json as _json_module  # local alias so the import order at top is unchanged


def _read_latest_ground_truth_receipt() -> dict | None:
    """Return the latest receipt row from the typed ledger, or None."""
    ledger = REPO_ROOT / "dev/state/ground_truth_probe_receipts.jsonl"
    if not ledger.exists():
        return None
    text = ledger.read_text(encoding="utf-8").strip()
    if not text:
        return None
    last_line = text.splitlines()[-1]
    try:
        return _json_module.loads(last_line)
    except _json_module.JSONDecodeError:
        return None


def _run_develop_next_with_final_response_gate() -> dict:
    """Run develop next --enforce-final-response-gate and return parsed JSON."""
    env = dict(os.environ)
    env["DEVCTL_NO_ARTIFACT_WRITES"] = "1"
    result = subprocess.run(
        [
            sys.executable,
            "dev/scripts/devctl.py",
            "develop",
            "next",
            "--actor",
            "agent",
            "--enforce-final-response-gate",
            "--format",
            "json",
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        env=env,
        timeout=120,
    )
    try:
        return _json_module.loads(result.stdout)
    except _json_module.JSONDecodeError as exc:
        raise AssertionError(
            f"develop next output is not valid JSON: {exc}\n"
            f"first 500 chars: {result.stdout[:500]}"
        ) from exc


# ---------------------------------------------------------------------------
# Invariant 3-self — gate_block_link_is_self_proving_via_known_unsatisfied_receipt
#
# Anti-skip-rot companion to invariant 3. Invariant 3 above can pytest.skip
# when (no receipt) / (latest=satisfied) / (gate not blocking). In most CI
# runs at least one of those fires, so the assertion path never executes
# and the test rots into a placebo.
#
# This invariant runs INLINE: it constructs a known-unsatisfied receipt in
# a tmp ledger, calls the gate's receipt-block function directly with that
# ledger as repo_root, and asserts the link without any ambient state.
# Result: the assert always runs. No skips. No rot.
# ---------------------------------------------------------------------------

def test_gate_block_link_is_self_proving_via_known_unsatisfied_receipt(tmp_path):
    """Construct a fake unsatisfied receipt in tmp_path's ledger and assert
    that ``_ground_truth_receipt_final_response_block()`` returns a block
    with ``source='ground_truth_probe_receipt'``.

    This proves the gate's receipt-block path is wired correctly WITHOUT
    depending on the live dev/state ledger. The assertion runs every time
    the suite runs — there is no ambient escape hatch.
    """
    from datetime import datetime, timezone
    from dev.scripts.devctl.commands.development.final_response_gate import (
        _ground_truth_receipt_final_response_block,
    )
    from dev.scripts.devctl.commands.development.orchestration_models import (
        DevelopmentContinuationRequiredSignal,
    )

    # Build a minimal ledger row matching GroundTruthProbeRunReceipt shape.
    now = datetime.now(tz=timezone.utc).isoformat().replace("+00:00", "Z")
    fake_receipt = {
        "schema_version": 1,
        "contract_id": "GroundTruthProbeRunReceipt",
        "created_at_utc": now,
        "base_ref": "",
        "head_ref": "HEAD",
        "changed_paths_digest": "sha256:" + "0" * 64,
        "trigger_kind": "authority_or_proof_surface",
        "trigger_paths": ["dev/scripts/devctl/tests/scenarios/test_live_state_invariants.py"],
        "design_ids": ["ground-truth-probe"],
        "required_probe_ids": ["live_state_invariants_v1"],
        "observed_probe_ids": [],
        "probe_report_path": "dev/reports/ground_truth_probe_pytest/fake.txt",
        "probe_report_sha256": "sha256:" + "f" * 64,
        "verdict": "unsatisfied",
        "warnings": ["pytest_target_failed:fake"],
    }

    ledger_dir = tmp_path / "dev" / "state"
    ledger_dir.mkdir(parents=True)
    ledger_path = ledger_dir / "ground_truth_probe_receipts.jsonl"
    ledger_path.write_text(_json_module.dumps(fake_receipt) + "\n", encoding="utf-8")

    continuation = DevelopmentContinuationRequiredSignal()

    block = _ground_truth_receipt_final_response_block(
        continuation,
        repo_root=tmp_path,
        next_slice_id="",
        expected_trigger_paths=(),
        now_utc=None,
    )

    assert block is not None, (
        "SELF-PROVING INVARIANT VIOLATED: gate's receipt-block function "
        "returned None even though the ledger had an unsatisfied receipt. "
        "The gate is silently skipping typed proof — the receipt-block "
        "link is broken."
    )
    assert block.source == "ground_truth_probe_receipt", (
        "SELF-PROVING INVARIANT VIOLATED: receipt-block returned but its "
        f"source field is {block.source!r}, not 'ground_truth_probe_receipt'. "
        "A reading agent would not see typed proof as the canonical block "
        "reason."
    )
    assert block.allow_final_response is False, (
        f"SELF-PROVING INVARIANT VIOLATED: gate allowed final response "
        f"despite unsatisfied receipt. allow_final_response={block.allow_final_response!r}"
    )
    assert "unsatisfied" in (block.reason or "").lower(), (
        f"Expected block.reason to name the unsatisfied verdict; "
        f"got {block.reason!r}"
    )


# ---------------------------------------------------------------------------
# Invariant 4 — inbox_pending_packets_must_not_exceed_hygiene_window
#
# Source: delete_after_ingest.md A19 (Stale Packet Hygiene Enforcement,
# operator amendment 2026-05-22). The amendment documents a same-output
# contradiction: review-channel --action inbox surfaces packets as
# `status=pending` while their `posted_at` is days past the hygiene
# window (default 24h for current-row implementer lanes).
#
# Per A19: "Past-TTL packets must either be auto-archived (typed
# lifecycle transition) or hidden behind an explicit --include-stale
# flag so the default lane view reflects only actionable items."
#
# This invariant catches the contradiction directly. When the live
# inbox returns pending packets older than the hygiene window without
# --include-stale set, the lane view is lying about what's actionable.
# ---------------------------------------------------------------------------

from datetime import datetime as _datetime, timezone as _timezone

# Operator-specified hygiene window for current-row implementer lanes
# (A19, line 1818 of delete_after_ingest.md). Configurable per repo-pack
# policy in the canonical implementation; here we pin the documented
# default so the invariant matches the amendment.
_DEFAULT_INBOX_HYGIENE_WINDOW_SECONDS = 24 * 60 * 60  # 24 hours


def _run_inbox_pending() -> dict:
    """Run review-channel --action inbox for the claude lane, pending only."""
    env = dict(os.environ)
    env["DEVCTL_NO_ARTIFACT_WRITES"] = "1"
    result = subprocess.run(
        [
            sys.executable,
            "dev/scripts/devctl.py",
            "review-channel",
            "--action", "inbox",
            "--target", "claude",
            "--actor", "claude",
            "--status", "pending",
            "--terminal", "none",
            "--limit", "1000",
            "--format", "json",
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        env=env,
        timeout=120,
    )
    if result.returncode != 0:
        raise AssertionError(
            f"inbox query exited {result.returncode}\n"
            f"stderr: {result.stderr[:500]}"
        )
    return _json_module.loads(result.stdout)


def _parse_utc(value: str) -> _datetime | None:
    """Parse an ISO UTC string into a timezone-aware datetime."""
    if not value:
        return None
    text = value.replace("Z", "+00:00")
    try:
        dt = _datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=_timezone.utc)
    return dt


def test_inbox_pending_packets_must_not_exceed_hygiene_window():
    """If review-channel --action inbox returns packets with status=pending
    and --include-stale is NOT set, none of those packets may have
    posted_at older than the hygiene window (24h default per A19).

    A19 documents this as a real, operator-asserted contradiction:
      pending_total in Claude inbox: 273
      posted_at age <1d: 24 (expected)
      posted_at age 1-3d: 182 (NOT expected)
      posted_at age 3-7d: 12
      posted_at age 7-30d: 55

    The lane is showing 249 packets as pending that the operator says
    should not be visible without --include-stale.

    Source rule: delete_after_ingest.md lines 1800-1803:
      "Inbox query results must not surface past-TTL packets as
       `pending` to the live agent reading their lane. Past-TTL packets
       must either be auto-archived (typed lifecycle transition) or
       hidden behind an explicit --include-stale flag so the default
       lane view reflects only actionable items."
    """
    output = _run_inbox_pending()
    packets = output.get("packets") or []
    if not packets:
        pytest.skip("inbox returned zero pending packets — invariant not in scope")

    now = _datetime.now(tz=_timezone.utc)
    stale: list[tuple[str, int]] = []
    for packet in packets:
        if not isinstance(packet, dict):
            continue
        if str(packet.get("status") or "").strip() != "pending":
            continue
        posted_at = _parse_utc(str(packet.get("posted_at") or ""))
        if posted_at is None:
            continue
        age_seconds = int((now - posted_at).total_seconds())
        if age_seconds > _DEFAULT_INBOX_HYGIENE_WINDOW_SECONDS:
            packet_id = str(packet.get("packet_id") or packet.get("id") or "?")
            stale.append((packet_id, age_seconds))

    if not stale:
        return  # green: all pending packets are within the hygiene window

    stale.sort(key=lambda row: row[1], reverse=True)
    preview = ", ".join(
        f"{pid}({secs // 3600}h)" for pid, secs in stale[:5]
    )

    assert not stale, (
        "INVARIANT VIOLATED: inbox_pending_packets_must_not_exceed_hygiene_window\n"
        f"  pending packets returned by inbox: {len(packets)}\n"
        f"  stale packets (posted_at > 24h ago, still status=pending): {len(stale)}\n"
        f"  oldest 5 (id, age): {preview}\n"
        "\n"
        "Per delete_after_ingest.md A19 (lines 1800-1803): inbox query\n"
        "results must NOT surface past-TTL packets as `pending` to the\n"
        "live agent reading their lane. Past-TTL packets must either be\n"
        "auto-archived (typed lifecycle transition) or hidden behind an\n"
        "explicit --include-stale flag.\n"
        "\n"
        "Owner: A19 stale-packet hygiene enforcement.\n"
        "Fix surface: G40 check_packet_hygiene_enforcement.py, or extend\n"
        "the existing review-channel inbox query to filter past-TTL\n"
        "rows by default."
    )


# ---------------------------------------------------------------------------
# Invariant 5 - work_board_row_role_must_not_grant_mutation_capabilities
#
# Source: delete_after_ingest.md A18 (Hierarchical Role Fanout And
# Single-Writer Lease Invariant, lines 1561-1733) plus the AntiDumbass
# Role-Boundary Amendment (lines 1292-1457).
#
# Rule: a work_board row whose role is in the read-only set (reviewer,
# observer, dashboard, plan_steward, orchestrator) MUST NOT carry any
# repo.* mutation capability (repo.commit, repo.stage, repo.stage_handoff).
# This is the live-state check for the "role declared vs action
# authorized" contradiction shape: a reviewer claiming mutation
# capability would let one agent silently overwrite another's work.
#
# Proactive: runs on EVERY row, every time. No skip path that lets the
# assertion never execute.
# ---------------------------------------------------------------------------

_READ_ONLY_ROLES = frozenset({
    "reviewer",
    "observer",
    "dashboard",
    "plan_steward",
    "orchestrator",
})

_MUTATION_CAPABILITIES = frozenset({
    "repo.commit",
    "repo.stage",
    "repo.stage_handoff",
    "repo.push",
    "repo.write",
})


def test_work_board_row_role_must_not_grant_mutation_capabilities():
    """For every work_board row, if its `role` is in the read-only set,
    its `granted_capabilities` MUST NOT include any repo.* mutation right.

    The AntiDumbass amendment (delete_after_ingest.md lines 1371-1389)
    states verbatim:
        "Reviewer/orchestrator/plan-steward lanes cannot mutate
         implementation files unless a typed mutation lease, typed
         proxy authority, or typed role switch exists."

    A18 (lines 1561-1733) names the same rule from the single-writer
    angle: a role without mutation capability MUST NOT hold a write
    lease or carry mutation rights in its granted_capabilities.

    This test surfaces any row where the projection itself contradicts
    that rule. A violation means the role boundary is leaking - the
    typed surface is granting a non-implementer role the ability to
    mutate, which is the exact precondition for two-writer corruption.
    """
    output = _run_sync_status()
    work_board = output.get("work_board") or {}
    rows = work_board.get("rows") or []
    if not rows:
        pytest.skip("work_board has zero rows - invariant not in scope")

    violations: list[dict] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        role = str(row.get("role") or "").strip().lower()
        if role not in _READ_ONLY_ROLES:
            continue
        granted = row.get("granted_capabilities") or []
        if not isinstance(granted, list):
            continue
        leaked = sorted(
            cap for cap in granted
            if str(cap).strip().lower() in _MUTATION_CAPABILITIES
        )
        if leaked:
            violations.append({
                "provider": str(row.get("provider") or ""),
                "actor_id": str(row.get("actor_id") or ""),
                "role": role,
                "leaked_capabilities": leaked,
                "mutation_mode": str(row.get("mutation_mode") or ""),
                "path_scope": row.get("path_scope") or [],
            })

    assert not violations, (
        "INVARIANT VIOLATED: work_board_row_role_must_not_grant_mutation_capabilities\n"
        f"  work_board rows: {len(rows)}\n"
        f"  read-only roles with mutation capability leaks: {len(violations)}\n"
        + "\n".join(
            f"    - provider={v['provider']!r} actor_id={v['actor_id']!r} "
            f"role={v['role']!r} mutation_mode={v['mutation_mode']!r} "
            f"leaked={v['leaked_capabilities']!r} path_scope={v['path_scope']!r}"
            for v in violations[:5]
        )
        + "\n\n"
        "Per delete_after_ingest.md A18 (1561-1733) and the AntiDumbass\n"
        "amendment (1371-1389): reviewer / orchestrator / plan_steward /\n"
        "observer / dashboard lanes cannot mutate implementation files\n"
        "unless a typed mutation lease, typed proxy authority, or typed\n"
        "role switch exists. A row whose role is in the read-only set\n"
        "but whose granted_capabilities include repo.* mutation rights\n"
        "is the exact precondition for two-writer silent corruption.\n"
        "\n"
        "Fix surface: dev/scripts/devctl/runtime/conductor_capability.py\n"
        "(role -> capability mapping) and the projection emitter that\n"
        "fills granted_capabilities on work_board rows. Either tighten\n"
        "the capability set for read-only roles, or emit a typed\n"
        "mutation-lease record proving the override is authorized."
    )


# ---------------------------------------------------------------------------
# Invariant 5-self - role_capability_rule_catches_known_violations
#
# Anti-skip-rot companion to invariant 5. Live work_board may contain
# zero rows with read-only roles, making invariant 5 vacuously pass
# without exercising its assertion path. This test runs the same rule
# against constructed rows so the violation logic is verified every
# time, regardless of ambient state.
# ---------------------------------------------------------------------------

def _row_violates_role_capability_rule(row: dict) -> list[str]:
    """Return the leaked mutation capabilities for one work_board row.

    Mirrors the inline logic in invariant 5 so the rule is testable
    without depending on the live projection containing a reviewer row.
    """
    role = str(row.get("role") or "").strip().lower()
    if role not in _READ_ONLY_ROLES:
        return []
    granted = row.get("granted_capabilities") or []
    if not isinstance(granted, list):
        return []
    return sorted(
        cap for cap in granted
        if str(cap).strip().lower() in _MUTATION_CAPABILITIES
    )


def test_role_capability_rule_catches_known_violations():
    """Verify the role->capability rule rejects known-bad rows and
    accepts known-good rows. This is the anti-skip-rot guarantee: the
    rule's correctness is tested every run, even when the live
    projection has no reviewer rows.

    Cases:
      A) reviewer + repo.commit                 -> violation
      B) observer + repo.stage + runtime.observe -> violation
      C) plan_steward + repo.stage_handoff      -> violation
      D) implementer + repo.commit              -> OK (mutation role)
      E) reviewer + runtime.observe only        -> OK (no mutation cap)
      F) reviewer + empty capabilities          -> OK
    """
    cases = [
        ("A reviewer with repo.commit",
         {"role": "reviewer", "granted_capabilities": ["repo.commit", "runtime.observe"]},
         ["repo.commit"]),
        ("B observer with repo.stage",
         {"role": "observer", "granted_capabilities": ["repo.stage", "runtime.observe"]},
         ["repo.stage"]),
        ("C plan_steward with stage_handoff",
         {"role": "plan_steward", "granted_capabilities": ["repo.stage_handoff"]},
         ["repo.stage_handoff"]),
        ("D implementer with repo.commit (allowed)",
         {"role": "implementer", "granted_capabilities": ["repo.commit", "repo.stage"]},
         []),
        ("E reviewer with only runtime.observe (allowed)",
         {"role": "reviewer", "granted_capabilities": ["runtime.observe", "approval.commit"]},
         []),
        ("F reviewer with empty capabilities (allowed)",
         {"role": "reviewer", "granted_capabilities": []},
         []),
    ]
    failures: list[str] = []
    for label, row, expected in cases:
        actual = _row_violates_role_capability_rule(row)
        if actual != expected:
            failures.append(
                f"  case {label}: expected leaked={expected!r}, got {actual!r}"
            )
    assert not failures, (
        "SELF-PROVING INVARIANT VIOLATED: role->capability rule does not "
        "behave as documented in delete_after_ingest.md A18 / AntiDumbass.\n"
        + "\n".join(failures)
    )


# ---------------------------------------------------------------------------
# Invariant 6 - work_board_row_role_drift_must_carry_typed_role_source
#
# Source: AntiDumbass amendment (delete_after_ingest.md lines 1292-1457).
# Rule: when a work_board row's declared_role != authority_role, the
# projection MUST expose a non-empty `role_source` from the canonical
# typed set so the drift is auditable. Silent drift is a contradiction
# between what the session asserted and what the typed authority decided.
#
# Canonical role_source values from
# review_channel/agent_work_board_roles.py:65-139:
#   actor_authority, session_declared_role, remote_control_attachment,
#   declared_role_without_mutation_authority, collaboration_participant,
#   legacy_provider_default, unresolved, helper_session_demotion
# ---------------------------------------------------------------------------

_CANONICAL_ROLE_SOURCES = frozenset({
    "actor_authority",
    "session_declared_role",
    "remote_control_attachment",
    "declared_role_without_mutation_authority",
    "collaboration_participant",
    "legacy_provider_default",
    "unresolved",
    "helper_session_demotion",
})


def test_work_board_row_role_drift_must_carry_typed_role_source():
    """For each work_board row, if declared_role != authority_role, the
    same row MUST expose a non-empty `role_source` field whose value is
    in the canonical typed set.

    Per the AntiDumbass amendment, role inversion (a session declaring
    one role while typed authority assigns another) is acceptable only
    when the projection labels HOW the drift was resolved. An unlabeled
    drift is silent ambiguity - a reading agent cannot tell whether
    authority overrode the declaration legitimately or the projection
    is leaking stale data.
    """
    output = _run_sync_status()
    rows = (output.get("work_board") or {}).get("rows") or []
    if not rows:
        pytest.skip("work_board has zero rows - invariant not in scope")

    violations: list[dict] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        declared = str(row.get("declared_role") or "").strip().lower()
        authority = str(row.get("authority_role") or "").strip().lower()
        if not declared or not authority or declared == authority:
            continue
        role_source = str(row.get("role_source") or "").strip().lower()
        if role_source and role_source in _CANONICAL_ROLE_SOURCES:
            continue
        violations.append({
            "provider": str(row.get("provider") or ""),
            "actor_id": str(row.get("actor_id") or ""),
            "declared_role": declared,
            "authority_role": authority,
            "role_source": role_source,
        })

    assert not violations, (
        "INVARIANT VIOLATED: work_board_row_role_drift_must_carry_typed_role_source\n"
        f"  rows with unlabeled declared/authority drift: {len(violations)}\n"
        + "\n".join(
            f"    - provider={v['provider']!r} declared={v['declared_role']!r} "
            f"authority={v['authority_role']!r} role_source={v['role_source']!r}"
            for v in violations[:5]
        )
        + "\n\n"
        "Per delete_after_ingest.md AntiDumbass amendment (1292-1457): when\n"
        "a row's declared_role disagrees with authority_role, role_source\n"
        "MUST be one of the canonical typed values listed in\n"
        "review_channel/agent_work_board_roles.py:65-139 so the override\n"
        "is auditable. An empty or non-canonical role_source means the\n"
        "drift is silent - a reading agent cannot tell whether the\n"
        "override is legitimate."
    )


# ---------------------------------------------------------------------------
# Invariant 7 - posted_packets_must_have_delivery_emitted_at_utc
#
# Source: delete_after_ingest.md A19 line 1767-1769:
#   "delivery_emitted_at_utc=None observed on live rev_pkt_4827 even
#    though posted_at was already set, suggesting the delivery half
#    of the lifecycle did not fire."
#
# Pattern: lifecycle half-finished. A packet with posted_at set but
# delivery_emitted_at_utc null AND status=pending is in an
# inconsistent state - the producer half of the transport completed
# but the consumer-visible delivery signal never fired. Reading agents
# that watch delivery_emitted_at_utc as the readiness signal will
# never see these packets transition.
# ---------------------------------------------------------------------------

def test_posted_packets_must_have_delivery_emitted_at_utc():
    """For each pending packet returned by the live inbox query, if
    posted_at is set, delivery_emitted_at_utc MUST also be set.

    Per A19: the packet lifecycle has two halves - the producer post
    and the delivery emission. Both must complete or a typed blocker
    must explain why. A null delivery field on a posted, pending
    packet is the contradiction A19 documented.
    """
    output = _run_inbox_pending()
    packets = output.get("packets") or []
    if not packets:
        pytest.skip("inbox returned zero pending packets - invariant not in scope")

    violations: list[dict] = []
    for packet in packets:
        if not isinstance(packet, dict):
            continue
        if str(packet.get("status") or "").strip() != "pending":
            continue
        posted_at = str(packet.get("posted_at") or "").strip()
        if not posted_at:
            continue
        delivery = packet.get("delivery_emitted_at_utc")
        if delivery is None or str(delivery).strip() == "":
            violations.append({
                "packet_id": str(packet.get("packet_id") or "?"),
                "posted_at": posted_at,
                "status": "pending",
            })

    assert not violations, (
        "INVARIANT VIOLATED: posted_packets_must_have_delivery_emitted_at_utc\n"
        f"  pending packets inspected: {len(packets)}\n"
        f"  half-lifecycle violations (posted_at set, delivery_emitted_at_utc null): "
        f"{len(violations)}\n"
        "  examples:\n"
        + "\n".join(
            f"    - {v['packet_id']} posted_at={v['posted_at']!r}"
            for v in violations[:5]
        )
        + "\n\n"
        "Per delete_after_ingest.md A19 (lines 1767-1769, 1804-1806): a\n"
        "packet with posted_at set but no delivery_emitted_at_utc is in\n"
        "lifecycle limbo. Either the producer never fired the delivery\n"
        "half, or a typed blocker must record why. Currently neither is\n"
        "happening - delivery is silently missing.\n"
        "\n"
        "Fix surface: review-channel event store / delivery emission step.\n"
        "Either (a) emit delivery_emitted_at_utc when the packet becomes\n"
        "visible to its target, or (b) emit a typed blocker explaining\n"
        "why delivery is pending."
    )


# ---------------------------------------------------------------------------
# Invariant 8 - orphan_files_ok_must_imply_empty_violations
#
# Source: delete_after_ingest.md A30 (Orphan Guard Semantics) and A35
# (Orphan Guard Fake-Green Must Fail Closed). The amendments warn
# against the fake-green pattern: ok=True while violations is non-empty.
#
# Pattern #6 from the semantic-tdd library: empty/positive required
# field treated as success while underlying evidence proves otherwise.
# ---------------------------------------------------------------------------

def _run_check_orphan_files() -> dict:
    """Invoke check_orphan_files.py and return the parsed JSON."""
    env = dict(os.environ)
    env["DEVCTL_NO_ARTIFACT_WRITES"] = "1"
    result = subprocess.run(
        [sys.executable, "dev/scripts/checks/check_orphan_files.py", "--format", "json"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        env=env,
        timeout=120,
    )
    return _json_module.loads(result.stdout)


def test_orphan_files_ok_must_imply_empty_violations():
    """If check_orphan_files reports ok=True (or status=ok), violations
    MUST be empty AND violation_count MUST be 0.

    A30/A35 explicitly forbid the fake-green pattern: a guard that says
    'ok' while its own violations list is non-empty is the worst class
    of code smell - it makes the guard untrustworthy, which means
    operators stop checking it.

    This invariant is a regression guard: it stays in the suite to
    catch any future refactor that accidentally re-introduces fake-green.
    """
    output = _run_check_orphan_files()
    ok = bool(output.get("ok", False))
    status = str(output.get("status") or "").strip().lower()
    is_green = ok or status == "ok"
    if not is_green:
        pytest.skip(
            f"check_orphan_files reports ok={ok!r} status={status!r}; "
            "fake-green rule only applies when guard claims OK"
        )

    violations = output.get("violations") or []
    violation_count = int(output.get("violation_count") or 0)

    assert violation_count == 0 and not violations, (
        "INVARIANT VIOLATED: orphan_files_ok_must_imply_empty_violations\n"
        f"  ok: {ok}, status: {status!r}\n"
        f"  violation_count: {violation_count}\n"
        f"  violations: {len(violations)} present\n"
        + "\n".join(
            f"    - {(v.get('path') if isinstance(v, dict) else v)!r}"
            for v in violations[:3]
        )
        + "\n\n"
        "Per delete_after_ingest.md A30 (line 227) and A35 (line 508):\n"
        "a guard claiming ok=True while violations is non-empty is\n"
        "fake-green, the worst class of code smell. The guard must\n"
        "either report violations and ok=False, or have an empty\n"
        "violations list."
    )


# ---------------------------------------------------------------------------
# Invariant 9 - operator_routed_packets_must_be_acked_within_ttl
#
# Source: delete_after_ingest.md A20 (Operator-Authority-Sovereignty
# Amendment, line 1905-1992). Operator-routed packets must be acked
# within the operator-ack TTL (default 5 minutes for remote-control
# sessions) or a typed OperatorMandateRefreshHint must surface.
# ---------------------------------------------------------------------------

_OPERATOR_MANDATE_KINDS = frozenset({
    "action_request",
    "operator_routed",
    "plan_gap_review",
})

_OPERATOR_ACK_TTL_SECONDS = 5 * 60  # A20 default 5 minutes


@pytest.mark.xfail(
    strict=True,
    reason=(
        "A20 ratchet (delete_after_ingest.md lines 1905-1992). Operator "
        "mandates are documented as overdue in the live ledger but the "
        "canonical fix - G41 check_operator_mandate_obedience.py plus "
        "operator-mandate short-circuit in evaluate_control_decision_obedience "
        "- is substantial new infrastructure that is OPEN. This invariant "
        "stays RED as the visible signal. When G41 lands and the ledger "
        "is cleaned, the test will xpass and force operator review."
    ),
)
def test_operator_routed_packets_must_be_acked_within_ttl():
    """If a packet has from_agent=operator AND kind in the mandate set
    AND status=pending, its posted_at MUST be within the operator-ack
    TTL (5 minutes for remote-control sessions).

    A20 amendment line 1951-1953: 'An operator-routed packet has been
    pending in any agent inbox for longer than the configured
    operator-ack TTL (default 5 minutes for remote-control sessions)
    without typed ack from the addressed actor.'

    A reading agent that misses an operator mandate causes the exact
    failure mode the amendment describes: 'prior codex session ignored
    three explicit operator-routed mandates for 30+ minutes and
    continued unsanctioned code edits for 8 hours.'
    """
    env = dict(os.environ)
    env["DEVCTL_NO_ARTIFACT_WRITES"] = "1"
    result = subprocess.run(
        [
            sys.executable,
            "dev/scripts/devctl.py",
            "review-channel",
            "--action", "inbox",
            "--target", "claude",
            "--actor", "claude",
            "--terminal", "none",
            "--limit", "200",
            "--include-stale",
            "--format", "json",
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        env=env,
        timeout=120,
    )
    output = _json_module.loads(result.stdout)
    packets = output.get("packets") or []
    if not packets:
        pytest.skip("inbox returned zero packets - invariant not in scope")

    now = _datetime.now(tz=_timezone.utc)
    overdue: list[dict] = []
    for packet in packets:
        if not isinstance(packet, dict):
            continue
        from_agent = str(packet.get("from_agent") or "").strip().lower()
        if from_agent != "operator":
            continue
        kind = str(packet.get("kind") or "").strip().lower()
        if kind not in _OPERATOR_MANDATE_KINDS:
            continue
        if str(packet.get("status") or "").strip() != "pending":
            continue
        posted_at = _parse_utc(str(packet.get("posted_at") or ""))
        if posted_at is None:
            continue
        age = int((now - posted_at).total_seconds())
        if age > _OPERATOR_ACK_TTL_SECONDS:
            overdue.append({
                "packet_id": str(packet.get("packet_id") or "?"),
                "kind": kind,
                "age_seconds": age,
                "posted_at": str(packet.get("posted_at") or ""),
            })

    assert not overdue, (
        "INVARIANT VIOLATED: operator_routed_packets_must_be_acked_within_ttl\n"
        f"  operator mandate packets past 5-minute ack TTL: {len(overdue)}\n"
        + "\n".join(
            f"    - {p['packet_id']} kind={p['kind']!r} "
            f"age={p['age_seconds'] // 60}m posted_at={p['posted_at']!r}"
            for p in overdue[:5]
        )
        + "\n\n"
        "Per delete_after_ingest.md A20 (line 1905-1992): operator-routed\n"
        "packets are at the top of the authority hierarchy and MUST be\n"
        "acked within 5 minutes for remote-control sessions. Long-pending\n"
        "operator mandates are the exact precondition for the documented\n"
        "8-hour unsanctioned-edit failure mode.\n"
        "\n"
        "Fix surface: G41 check_operator_mandate_obedience.py is the\n"
        "documented canonical guard. The addressed actor must either ack\n"
        "the packet or the agent loop must short-circuit on the\n"
        "OperatorMandate per A20."
    )


# ---------------------------------------------------------------------------
# Invariant 10 - a25_connectivity_sweep_must_be_green
#
# Source: delete_after_ingest.md A25 (Connectivity-First Priority
# Amendment, line 102). All 5 connectivity-sweep guards MUST report
# ok=True before feature work. Catches orphans, duplicates, stranded
# consumers, typed-seam violations, and broken contract wiring as a
# unified gate.
#
# This is the per-operator-directive "run other roles too to look for
# duplication and make sure everything connects with the system map"
# invariant. The TDD role runs all the connectivity-related guards in
# one assertion.
# ---------------------------------------------------------------------------

_A25_CONNECTIVITY_GUARDS = (
    "dev/scripts/checks/check_contract_connectivity.py",
    "dev/scripts/checks/check_orphan_files.py",
    "dev/scripts/checks/check_function_duplication.py",
    "dev/scripts/checks/check_contract_consumer_coverage_sweep.py",
    "dev/scripts/checks/check_python_typed_seams.py",
)


def test_a25_connectivity_sweep_must_be_green():
    """A25 requires all 5 connectivity-sweep guards to be green before
    feature work. Run each guard with --format json, parse the result,
    assert every guard reports ok=True with zero new violations.

    Fail-closed property: ANY guard reporting ok=False fails the
    invariant. The reading agent sees which guard fired without having
    to invoke each individually.
    """
    env = dict(os.environ)
    env["DEVCTL_NO_ARTIFACT_WRITES"] = "1"
    red_guards: list[dict] = []
    for guard_path in _A25_CONNECTIVITY_GUARDS:
        result = subprocess.run(
            [sys.executable, guard_path, "--format", "json"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            env=env,
            timeout=180,
        )
        try:
            payload = _json_module.loads(result.stdout)
        except _json_module.JSONDecodeError:
            red_guards.append({
                "guard": guard_path,
                "ok": None,
                "reason": "non-json output",
                "stderr_first_200": (result.stderr or "")[:200],
            })
            continue
        if not bool(payload.get("ok", False)):
            red_guards.append({
                "guard": guard_path,
                "ok": False,
                "violation_count": payload.get("violation_count"),
                "violations_preview": (payload.get("violations") or [])[:2],
            })

    assert not red_guards, (
        "INVARIANT VIOLATED: a25_connectivity_sweep_must_be_green\n"
        f"  red guards: {len(red_guards)} / {len(_A25_CONNECTIVITY_GUARDS)}\n"
        + "\n".join(
            f"    - {g['guard']}: ok={g.get('ok')!r} "
            f"violation_count={g.get('violation_count')!r}"
            for g in red_guards
        )
        + "\n\n"
        "Per delete_after_ingest.md A25 (line 102-141): all 5 connectivity\n"
        "guards must be green before feature work. The operator explicitly\n"
        "asserted: 'isn't that the first thing we should do, make sure\n"
        "there's no duplicates, make sure that everything is connected,\n"
        "making sure there's no orphans?' A red connectivity sweep means\n"
        "the network has invisible disconnections; adding more code on top\n"
        "is building on broken wiring."
    )


# ---------------------------------------------------------------------------
# Invariant 11 - body_open_required_must_not_target_already_observed_packet
#
# Source: delete_after_ingest.md A17 (Packet Body-Open Route, Expiry
# Refresh, And Visible Consumption, line 4859-4910). The amendment
# documents the exact contradiction: 'Claude could see and read the
# packet body through the provider session, but the typed lifecycle
# still reported packet_body_open_required.'
#
# Live evidence captured 2026-05-23: agent_loop_decision reports
# body_open_required: True for rev_pkt_4839, yet that packet's
# body_observed_at_utc is set and body_observed_by names the same
# actor whose loop is reportedly blocked.
#
# Rule: if agent_loop_decision.body_open_required is True for a
# packet, that packet's body_observed_at_utc MUST be empty. The
# observation already happened; the prerequisite cannot still be
# "required."
# ---------------------------------------------------------------------------

@pytest.mark.xfail(
    strict=True,
    reason=(
        "A17 ratchet (delete_after_ingest.md lines 4859-4910). The "
        "controller emits body_open_required=True for rev_pkt_4839 even "
        "though that packet's body_observed_at_utc is set by the same "
        "actor. The fix surface is upstream of "
        "control_decision_packet_inbox.py:103-122 - the upstream caller "
        "that produces required_action='open_packet_body' must check "
        "body_observed_at_utc before emitting that action. The fix is "
        "multi-layer and beyond the scope of this autonomous slice; this "
        "invariant stays RED as the visible signal."
    ),
)
def test_body_open_required_must_not_target_already_observed_packet():
    """For each agent_loop_decision with body_open_required=True, the
    body_open_packet_id MUST point at a packet whose
    body_observed_at_utc is empty.

    Catches the A17 contradiction live: a controller telling an actor
    to 'open the body' of a packet that actor has already observed.
    """
    output = _run_sync_status()
    decisions = output.get("agent_loop_decisions") or []
    if not isinstance(decisions, list) or not decisions:
        pytest.skip("agent_loop_decisions empty - invariant not in scope")

    # Build a packet lookup by id. sync-status's packets[] is scoped to
    # the canonical-active set; for body_observed_at_utc data we may
    # also need the per-actor inbox. Only query the actors with active
    # body_open_required flags to keep the test fast.
    packets_by_id: dict[str, dict] = {}
    for packet in output.get("packets") or []:
        if isinstance(packet, dict):
            pid = str(packet.get("packet_id") or "").strip()
            if pid:
                packets_by_id[pid] = packet
    actors_with_body_open: set[str] = {
        str(d.get("actor_id") or "").strip()
        for d in decisions
        if isinstance(d, dict)
        and bool(d.get("body_open_required", False))
        and d.get("body_open_packet_id")
    }
    env = dict(os.environ)
    env["DEVCTL_NO_ARTIFACT_WRITES"] = "1"
    for actor in actors_with_body_open:
        if not actor:
            continue
        try:
            inbox_result = subprocess.run(
                [
                    sys.executable,
                    "dev/scripts/devctl.py",
                    "review-channel",
                    "--action", "inbox",
                    "--target", actor,
                    "--actor", actor,
                    "--terminal", "none",
                    "--limit", "100",
                    "--include-stale",
                    "--format", "json",
                ],
                cwd=str(REPO_ROOT),
                capture_output=True,
                text=True,
                env=env,
                timeout=30,
            )
            inbox = _json_module.loads(inbox_result.stdout)
            for packet in inbox.get("packets") or []:
                if isinstance(packet, dict):
                    pid = str(packet.get("packet_id") or "").strip()
                    if pid and pid not in packets_by_id:
                        packets_by_id[pid] = packet
        except (subprocess.SubprocessError, _json_module.JSONDecodeError):
            continue

    violations: list[dict] = []
    for decision in decisions:
        if not isinstance(decision, dict):
            continue
        if not bool(decision.get("body_open_required", False)):
            continue
        target = str(decision.get("body_open_packet_id") or "").strip()
        if not target:
            continue
        packet = packets_by_id.get(target)
        if packet is None:
            continue
        observed = str(packet.get("body_observed_at_utc") or "").strip()
        if not observed:
            continue
        violations.append({
            "actor_id": str(decision.get("actor_id") or ""),
            "body_open_packet_id": target,
            "observed_at": observed,
            "observed_by": str(packet.get("body_observed_by") or ""),
        })

    assert not violations, (
        "INVARIANT VIOLATED: body_open_required_must_not_target_already_observed_packet\n"
        f"  controller-vs-packet contradictions: {len(violations)}\n"
        + "\n".join(
            f"    - actor={v['actor_id']!r} required_to_open={v['body_open_packet_id']!r} "
            f"but already observed by {v['observed_by']!r} at {v['observed_at']!r}"
            for v in violations[:5]
        )
        + "\n\n"
        "Per delete_after_ingest.md A17 (lines 4859-4910): a packet whose\n"
        "body has been observed (body_observed_at_utc set) MUST NOT also\n"
        "be the target of body_open_required=True on an agent_loop_decision.\n"
        "The prerequisite is satisfied; the controller is reporting it as\n"
        "still-pending. A reading agent following the gate's stated next\n"
        "command would try to 'open' a packet they already opened.\n"
        "\n"
        "Fix surface: agent_loop_decision_builder.py - the body_open_required\n"
        "computation must check the packet's body_observed_at_utc field and\n"
        "advance to the next lifecycle step (typically semantic_ingestion)\n"
        "rather than re-emitting the satisfied prerequisite."
    )


# ---------------------------------------------------------------------------
# Invariant 12 - stale_packet_count_must_match_past_expiry_warning
#
# Same-output contradiction caught against live sync-status:
#   queue.stale_packet_count: 0
#   warnings: ['One or more pending runtime-transport review packets are
#              past their expiry timestamp.']
#
# These two fields cannot both be true: either the count is non-zero
# and the warning is correct, or the count is zero and the warning is
# stale. A reading agent that trusts stale_packet_count moves on; a
# reading agent that trusts the warning re-runs expire-packets. They
# never agree.
# ---------------------------------------------------------------------------

_STALE_WARNING_FRAGMENTS = (
    "past their expiry timestamp",
    "past their expiry",
    "stale packet",
)


def test_stale_packet_count_must_match_past_expiry_warning():
    """If queue.stale_packet_count is 0, no warning may claim packets
    are past their expiry timestamp. If the warning fires,
    stale_packet_count MUST be non-zero.

    Same-output contradiction: the counter and the warning are derived
    from the same underlying state; they must agree.
    """
    output = _run_sync_status()
    queue = output.get("queue") or {}
    count = int(queue.get("stale_packet_count") or 0)
    warnings_blob = " ".join(str(w).lower() for w in (output.get("warnings") or []))
    warning_fired = any(frag in warnings_blob for frag in _STALE_WARNING_FRAGMENTS)

    if not warning_fired and count == 0:
        return  # both signals agree: clean
    if warning_fired and count > 0:
        return  # both signals agree: dirty

    assert False, (
        "INVARIANT VIOLATED: stale_packet_count_must_match_past_expiry_warning\n"
        f"  queue.stale_packet_count: {count}\n"
        f"  warning fired: {warning_fired}\n"
        f"  warnings: {output.get('warnings')!r}\n"
        "\n"
        "Same-output contradiction: the counter and the warning are derived\n"
        "from the same underlying packet store; they cannot disagree.\n"
        "A reading agent that trusts stale_packet_count==0 moves on; a\n"
        "reading agent that trusts the warning re-runs expire-packets.\n"
        "They never agree.\n"
        "\n"
        "Fix surface: wherever the warning is emitted (likely the queue\n"
        "reducer in dev/scripts/devctl/review_channel/) must use the same\n"
        "stale_packet_count it just produced, or the count must include\n"
        "the same past-TTL set the warning detects."
    )


# ---------------------------------------------------------------------------
# Invariant 13 - pending_totals_must_agree_across_surfaces
#
# Three different surfaces report pending packet totals:
#   queue.pending_total        - canonical-active set
#   queue.agent_sync_pending_total - sum across agent_sync rows
#   sum(agents[*].pending_packets_to_me) - per-actor inbox arrays
#
# These three counts derive from the same underlying state. If they
# disagree, the projection layer is drifting. Regression guard against
# future divergence.
# ---------------------------------------------------------------------------

def test_pending_totals_must_agree_across_surfaces():
    """queue.pending_total, queue.agent_sync_pending_total, and the sum
    of agents[*].pending_packets_to_me MUST all agree.

    These three counts come from the same packet set. Divergence
    means a downstream consumer reading any one of them can be
    contradicted by another.
    """
    output = _run_sync_status()
    queue = output.get("queue") or {}
    pending_total = int(queue.get("pending_total") or 0)
    sync_total = int(queue.get("agent_sync_pending_total") or 0)
    agents = output.get("agents") or {}
    agent_sum = sum(
        len((row or {}).get("pending_packets_to_me") or [])
        for row in agents.values()
        if isinstance(row, dict)
    )

    if pending_total == sync_total == agent_sum:
        return

    assert False, (
        "INVARIANT VIOLATED: pending_totals_must_agree_across_surfaces\n"
        f"  queue.pending_total:          {pending_total}\n"
        f"  queue.agent_sync_pending_total: {sync_total}\n"
        f"  sum(agents[*].pending_packets_to_me): {agent_sum}\n"
        "\n"
        "These three surfaces derive from the same packet store and\n"
        "MUST agree. A drift means a reading agent that trusts one\n"
        "field can be contradicted by another."
    )


# ---------------------------------------------------------------------------
# Invariant 14 - blocked_agents_must_name_awaiting_evidence
#
# If an agent's derived_status is 'blocked', the same row MUST name a
# typed reason: awaiting_packet_id OR awaiting_from_agent OR
# awaiting_evidence_class != 'none'. A blocked agent with no named
# blocker is silent indecision - the reading agent cannot tell whether
# the lane is actually stuck or just mis-classified.
# ---------------------------------------------------------------------------

def test_blocked_agents_must_name_awaiting_evidence():
    """For each agent in sync-status, if derived_status=='blocked',
    the same row MUST name a typed blocker via awaiting_packet_id or
    awaiting_from_agent or awaiting_evidence_class.

    Catches silent block: status says stuck but no field names the
    blocker.
    """
    output = _run_sync_status()
    agents = output.get("agents") or {}
    silent_blocks: list[dict] = []
    for agent_id, info in agents.items():
        if not isinstance(info, dict):
            continue
        if str(info.get("derived_status") or "").strip().lower() != "blocked":
            continue
        awaiting_packet = str(info.get("awaiting_packet_id") or "").strip()
        awaiting_agent = str(info.get("awaiting_from_agent") or "").strip()
        awaiting_class = str(info.get("awaiting_evidence_class") or "").strip().lower()
        named = awaiting_packet or awaiting_agent or (awaiting_class and awaiting_class != "none")
        if not named:
            silent_blocks.append({
                "agent_id": agent_id,
                "derived_status": "blocked",
                "awaiting_packet_id": awaiting_packet,
                "awaiting_from_agent": awaiting_agent,
                "awaiting_evidence_class": awaiting_class,
            })
    assert not silent_blocks, (
        "INVARIANT VIOLATED: blocked_agents_must_name_awaiting_evidence\n"
        f"  silent-block agents: {len(silent_blocks)}\n"
        + "\n".join(
            f"    - {b['agent_id']!r}: status=blocked but no awaiting_packet_id, "
            f"no awaiting_from_agent, awaiting_evidence_class={b['awaiting_evidence_class']!r}"
            for b in silent_blocks
        )
        + "\n\n"
        "A reading agent cannot diagnose a silent block. The projection\n"
        "must name what the agent is waiting on."
    )


# ---------------------------------------------------------------------------
# Invariant 15 - voiceterm_platform_leakage_count_must_not_grow
#
# Source: delete_after_ingest.md A4 (line 4115). 73 platform-code
# voiceterm references documented as leakage debt; ~310 including
# tests. This invariant ratchets the file-count downward - the count
# may decrease (good) but never increase (regression).
#
# Live measurement at this commit: 121 files under dev/scripts/devctl
# match /voiceterm|VoiceTerm|VOICETERM/ (modulo __pycache__).
# ---------------------------------------------------------------------------

VOICETERM_LEAKAGE_FILE_CEILING = 122


def test_voiceterm_platform_leakage_count_must_not_grow():
    """Count files under dev/scripts/devctl that still contain
    VoiceTerm references and assert the count is at or below the
    recorded ceiling.

    A4 lists 9 high-leverage targets and ~73 total platform-code
    references. The ratchet ensures we walk this down, not up.
    """
    import pathlib
    import re
    pattern = re.compile(r"voiceterm|VoiceTerm|VOICETERM")
    devctl_root = REPO_ROOT / "dev" / "scripts" / "devctl"
    hits = 0
    for path in devctl_root.rglob("*"):
        if not path.is_file():
            continue
        if "__pycache__" in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except (OSError, UnicodeDecodeError):
            continue
        if pattern.search(text):
            hits += 1

    assert hits <= VOICETERM_LEAKAGE_FILE_CEILING, (
        "INVARIANT VIOLATED: voiceterm_platform_leakage_count_must_not_grow\n"
        f"  current hit count: {hits}\n"
        f"  ratchet ceiling:   {VOICETERM_LEAKAGE_FILE_CEILING}\n"
        "\n"
        "Per delete_after_ingest.md A4 (line 4115): voiceterm references\n"
        "in platform code are leakage debt. The ratchet allows the count\n"
        "to decrease but not grow. If you intentionally added a new\n"
        "voiceterm reference inside repo_packs/voiceterm/, exclude that\n"
        "subtree from the count. Otherwise, fix the leak."
    )
    # Information-only: print current count so the ratchet can be lowered
    # when leakage is repaired.
    print(f"[voiceterm leakage] current={hits} ceiling={VOICETERM_LEAKAGE_FILE_CEILING}")


# ---------------------------------------------------------------------------
# Invariant 16 - fpr_proven_passed_without_pytest_node_id_must_not_grow
#
# Source: delete_after_ingest.md A12 line 4365: 'has proven_passed
# without at least one concrete pytest node id in tests_run'.
#
# Live measurement at this commit: 37 of 153 FPRs claim
# real_life_test_status=proven_passed but tests_run contains no
# string with '::' (the pytest node id marker). Ratchet keeps it
# from growing; future remediation walks it down.
# ---------------------------------------------------------------------------

FPR_PROVEN_WITHOUT_NODE_ID_CEILING = 37


def test_fpr_proven_passed_without_pytest_node_id_must_not_grow():
    """Count FeatureProofReceipts where real_life_test_status==proven_passed
    but tests_run has no string containing '::'. Per A12 line 4365 this
    is the exact half-built pattern - claim of proof without concrete
    pytest evidence.
    """
    import pathlib
    fpr_dir = REPO_ROOT / "dev" / "reports" / "feature_proof_receipts"
    if not fpr_dir.exists():
        pytest.skip("FPR directory not present - invariant not in scope")
    bad_count = 0
    bad_samples: list[str] = []
    for path in sorted(fpr_dir.glob("*.json")):
        try:
            data = _json_module.loads(path.read_text(encoding="utf-8"))
        except _json_module.JSONDecodeError:
            continue
        if str(data.get("real_life_test_status") or "") != "proven_passed":
            continue
        tests_run = data.get("tests_run") or []
        if not isinstance(tests_run, list):
            continue
        if not any("::" in str(t) for t in tests_run):
            bad_count += 1
            if len(bad_samples) < 3:
                bad_samples.append(path.name)
    assert bad_count <= FPR_PROVEN_WITHOUT_NODE_ID_CEILING, (
        "INVARIANT VIOLATED: fpr_proven_passed_without_pytest_node_id_must_not_grow\n"
        f"  current bad-FPR count:   {bad_count}\n"
        f"  ratchet ceiling:         {FPR_PROVEN_WITHOUT_NODE_ID_CEILING}\n"
        f"  sample bad receipts:     {bad_samples}\n"
        "\n"
        "Per delete_after_ingest.md A12 (line 4365): a FeatureProofReceipt\n"
        "with real_life_test_status=proven_passed must include at least one\n"
        "concrete pytest node id (a string containing '::') in tests_run.\n"
        "Claims of proof without proof-bearing evidence are the same\n"
        "half-built pattern A11 was meant to catch."
    )


# ---------------------------------------------------------------------------
# Invariant 17 - fpr_unresolved_commit_sha_must_not_grow
#
# Source: delete_after_ingest.md A12 line 4366: 'has commit_sha that
# does not resolve via git cat-file -e <sha> against the local repo
# OR named ancestry receipt'.
#
# Live count at this commit: 2 FPRs have unresolvable commit_sha. One
# is a template placeholder; the other is a real sha that may have
# been amended away. Ratchet keeps the count from growing.
# ---------------------------------------------------------------------------

FPR_UNRESOLVED_COMMIT_SHA_CEILING = 2


def test_fpr_unresolved_commit_sha_must_not_grow():
    """Each FeatureProofReceipt with a commit_sha set must have that
    sha resolve via `git cat-file -e`. Per A12 line 4366 this is a
    half-built receipt - claim of commit-anchored proof without a
    commit.
    """
    import pathlib
    fpr_dir = REPO_ROOT / "dev" / "reports" / "feature_proof_receipts"
    if not fpr_dir.exists():
        pytest.skip("FPR directory not present")
    unresolved = 0
    for path in sorted(fpr_dir.glob("*.json")):
        try:
            data = _json_module.loads(path.read_text(encoding="utf-8"))
        except _json_module.JSONDecodeError:
            continue
        sha = str(data.get("commit_sha") or "").strip()
        if not sha:
            continue
        result = subprocess.run(
            ["git", "cat-file", "-e", sha],
            cwd=str(REPO_ROOT),
            capture_output=True,
            timeout=10,
        )
        if result.returncode != 0:
            unresolved += 1
    assert unresolved <= FPR_UNRESOLVED_COMMIT_SHA_CEILING, (
        "INVARIANT VIOLATED: fpr_unresolved_commit_sha_must_not_grow\n"
        f"  unresolved count: {unresolved}\n"
        f"  ceiling:          {FPR_UNRESOLVED_COMMIT_SHA_CEILING}\n"
        "\n"
        "Per A12 (line 4366): commit_sha on a FPR must resolve via\n"
        "git cat-file -e. Unresolvable shas indicate the FPR is\n"
        "claiming proof against a commit that no longer exists."
    )


# ---------------------------------------------------------------------------
# Invariant 18 - system_map_orphan_references_must_not_grow
#
# Per the operator directive about connectivity to system_map MD:
# SYSTEM_MAP.md references Python module paths via backticks; each
# reference SHOULD resolve to a real file in the repo. References to
# non-existent modules are documented-vs-real contradictions - the
# map is lying about what code exists.
#
# Live count at this commit: 14 references in SYSTEM_MAP.md do not
# resolve to a file under dev/. Ratchet keeps this from growing.
# ---------------------------------------------------------------------------

SYSTEM_MAP_ORPHAN_REFERENCE_CEILING = 14


def test_system_map_orphan_references_must_not_grow():
    """Count backtick-quoted Python module paths in
    dev/guides/SYSTEM_MAP.md that don't resolve to a real file in
    the repo. Ratchet against documentation drifting from code.
    """
    import pathlib
    import re
    system_map = REPO_ROOT / "dev" / "guides" / "SYSTEM_MAP.md"
    if not system_map.exists():
        pytest.skip("SYSTEM_MAP.md not present - invariant not in scope")
    text = system_map.read_text(encoding="utf-8")
    refs = set(re.findall(r"`([a-zA-Z_/.][a-zA-Z_0-9/.]*\.py)`", text))
    missing: list[str] = []
    for ref in sorted(refs):
        if (REPO_ROOT / ref).exists():
            continue
        # Allow basename-match anywhere under dev/
        name = pathlib.Path(ref).name
        found = list((REPO_ROOT / "dev").rglob(name))
        if not found:
            missing.append(ref)
    assert len(missing) <= SYSTEM_MAP_ORPHAN_REFERENCE_CEILING, (
        "INVARIANT VIOLATED: system_map_orphan_references_must_not_grow\n"
        f"  current orphan refs: {len(missing)}\n"
        f"  ceiling:             {SYSTEM_MAP_ORPHAN_REFERENCE_CEILING}\n"
        f"  samples: {missing[:5]}\n"
        "\n"
        "SYSTEM_MAP.md is the navigation projection over typed contracts.\n"
        "Backtick-quoted module paths must resolve to real files. A\n"
        "reference to a non-existent module means SYSTEM_MAP is lying\n"
        "about what the codebase contains - documented-vs-real\n"
        "contradiction.\n"
        "\n"
        "Either create the missing module, remove the reference, or\n"
        "regenerate SYSTEM_MAP via `devctl render-surfaces --write`."
    )


# ---------------------------------------------------------------------------
# Invariant 19 - active_plan_sync_must_be_green
#
# Source: CLAUDE.md active-plan onboarding rule and the existing
# check_active_plan_sync.py guard. Every file under dev/active/ must
# be entered in dev/active/INDEX.md. Regression guard for the rule.
# ---------------------------------------------------------------------------

def test_active_plan_sync_must_be_green():
    """dev/scripts/checks/check_active_plan_sync.py must report ok=True
    with empty errors. Catches new dev/active/ files added without an
    INDEX.md row, per CLAUDE.md active-plan onboarding rule.
    """
    env = dict(os.environ)
    env["DEVCTL_NO_ARTIFACT_WRITES"] = "1"
    result = subprocess.run(
        [sys.executable, "dev/scripts/checks/check_active_plan_sync.py", "--format", "json"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        env=env,
        timeout=60,
    )
    payload = _json_module.loads(result.stdout)
    errors = payload.get("errors") or []
    assert bool(payload.get("ok", False)) and not errors, (
        "INVARIANT VIOLATED: active_plan_sync_must_be_green\n"
        f"  ok: {payload.get('ok')!r}\n"
        f"  errors: {errors}\n"
        "\n"
        "Per CLAUDE.md active-plan onboarding rule: every file under\n"
        "dev/active/ must have a row in dev/active/INDEX.md.\n"
        "Run `python3 dev/scripts/checks/check_active_plan_sync.py` to\n"
        "see which file is orphaned, then add a row to INDEX.md."
    )


# ---------------------------------------------------------------------------
# Invariant 20 - blocked_loop_state_must_name_top_blocker
#
# Same-output contradiction: an agent_loop_decision with
# loop_state='blocked' MUST name what is blocking it. Either
# top_blocker is a non-'inactive' state OR blocker_reason is
# non-empty.
#
# Live evidence: both claude and codex agent_loop_decisions report
# loop_state='blocked' AND top_blocker='inactive' AND
# blocker_reason='' - the loop is blocked but no field names what
# is blocking it.
# ---------------------------------------------------------------------------

def test_blocked_loop_state_must_name_top_blocker():
    """If agent_loop_decision.loop_state == 'blocked', the same
    decision MUST name a typed blocker via top_blocker (non-'inactive')
    OR blocker_reason (non-empty).

    Catches silent block at the loop-decision layer - status says
    stuck but no field names why.
    """
    output = _run_sync_status()
    decisions = output.get("agent_loop_decisions") or []
    if not isinstance(decisions, list) or not decisions:
        pytest.skip("agent_loop_decisions empty - invariant not in scope")

    silent_blocks: list[dict] = []
    for de in decisions:
        if not isinstance(de, dict):
            continue
        loop_state = str(de.get("loop_state") or "").strip().lower()
        if loop_state != "blocked":
            continue
        top_blocker = str(de.get("top_blocker") or "").strip().lower()
        blocker_reason = str(de.get("blocker_reason") or "").strip()
        named = (top_blocker and top_blocker != "inactive") or blocker_reason
        if not named:
            silent_blocks.append({
                "actor_id": str(de.get("actor_id") or ""),
                "actor_role": str(de.get("actor_role") or ""),
                "loop_state": loop_state,
                "top_blocker": top_blocker,
                "blocker_reason": blocker_reason,
                "required_action": str(de.get("required_action") or ""),
            })

    assert not silent_blocks, (
        "INVARIANT VIOLATED: blocked_loop_state_must_name_top_blocker\n"
        f"  silent loop blocks: {len(silent_blocks)}\n"
        + "\n".join(
            f"    - actor={b['actor_id']!r} role={b['actor_role']!r} "
            f"loop_state=blocked top_blocker={b['top_blocker']!r} "
            f"blocker_reason={b['blocker_reason']!r} "
            f"required_action={b['required_action']!r}"
            for b in silent_blocks
        )
        + "\n\n"
        "Same-output contradiction: loop_state='blocked' while no\n"
        "blocker field names the cause. A reading agent cannot tell\n"
        "what to fix. The projection must either set top_blocker to\n"
        "a non-'inactive' state OR fill blocker_reason with the\n"
        "typed cause string.\n"
        "\n"
        "Fix surface: agent_loop_decision_builder.py - whenever the\n"
        "loop_state is computed as 'blocked', the same builder must\n"
        "name top_blocker. Currently it appears the loop_state setter\n"
        "and the top_blocker setter run independently."
    )


# ---------------------------------------------------------------------------
# Invariant 21 - review_state_projection_must_not_be_stale
#
# develop next reads review_state from
# dev/reports/review_channel/projections/latest/review_state.json.
# If that file is too old, develop next operates on stale data and
# reports wrong values (e.g., campaign.coordination_topology may
# emit the deprecated agent-count label while the live in-memory
# projection emits the new role-based string).
#
# Ratchet against severely stale projection files. The natural
# refresh path is `devctl develop launch --dry-run` or a fresh
# review_channel command without DEVCTL_NO_ARTIFACT_WRITES=1.
# ---------------------------------------------------------------------------

_REVIEW_STATE_PROJECTION_MAX_AGE_HOURS = 48


def test_review_state_projection_must_not_be_stale():
    """The cached review_state.json projection should be no older
    than 48 hours. Anything older means develop-next-style commands
    are reading stale typed state.
    """
    import pathlib
    from datetime import datetime, timezone
    projection = REPO_ROOT / "dev/reports/review_channel/projections/latest/review_state.json"
    if not projection.exists():
        pytest.skip("review_state.json projection not present")
    mtime = datetime.fromtimestamp(projection.stat().st_mtime, tz=timezone.utc)
    age_hours = (datetime.now(tz=timezone.utc) - mtime).total_seconds() / 3600.0
    assert age_hours < _REVIEW_STATE_PROJECTION_MAX_AGE_HOURS, (
        "INVARIANT VIOLATED: review_state_projection_must_not_be_stale\n"
        f"  projection age: {age_hours:.1f} hours\n"
        f"  max age:        {_REVIEW_STATE_PROJECTION_MAX_AGE_HOURS} hours\n"
        f"  projection path: {projection}\n"
        "\n"
        "develop next reads coordination_state, packet_attention, and\n"
        "other typed fields from this cached projection. A stale\n"
        "projection causes develop next to report wrong values while\n"
        "live sync-status (which builds in-memory) is correct -\n"
        "different surfaces of the same system disagree about basic\n"
        "facts. Refresh via `devctl develop launch --dry-run` or a\n"
        "review-channel command without DEVCTL_NO_ARTIFACT_WRITES=1."
    )


# ---------------------------------------------------------------------------
# Invariant 22 - every_contract_registry_row_must_have_valid_owner_path
#
# dev/state/contract_registry.jsonl lists every registered platform
# contract with python_owner_path. Each path MUST resolve to a real
# file in the repo. A dangling owner_path means the registry claims
# a contract exists at a location that has no implementation - the
# typed-state ledger is lying about what code backs which contract.
# ---------------------------------------------------------------------------

def test_every_contract_registry_row_must_have_valid_owner_path():
    """Walk dev/state/contract_registry.jsonl and assert every row's
    python_owner_path (when set) resolves to a real file under the
    repo root.

    Currently all 248 rows pass; this is a regression guard against
    future contract-registry drift.
    """
    import pathlib
    registry = REPO_ROOT / "dev" / "state" / "contract_registry.jsonl"
    if not registry.exists():
        pytest.skip("contract_registry.jsonl not present")
    missing: list[tuple[str, str]] = []
    total = 0
    for line in registry.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        total += 1
        try:
            row = _json_module.loads(line)
        except _json_module.JSONDecodeError:
            continue
        path = str(row.get("python_owner_path") or "").strip()
        if not path:
            continue
        full = REPO_ROOT / path
        if not full.exists():
            missing.append((str(row.get("contract_id") or "?"), path))
    assert not missing, (
        "INVARIANT VIOLATED: every_contract_registry_row_must_have_valid_owner_path\n"
        f"  rows checked: {total}\n"
        f"  dangling owner paths: {len(missing)}\n"
        + "\n".join(f"    - {cid}: {p}" for cid, p in missing[:5])
        + "\n\n"
        "Contract registry rows are typed claims that the contract exists\n"
        "at python_owner_path. A dangling path means the registry is\n"
        "lying about what code implements which contract."
    )


# ---------------------------------------------------------------------------
# Invariant 23 - plan_rows_applied_status_must_have_applied_at_utc
#
# Source: delete_after_ingest.md A12 line 4380-4385 (G13 PlanRow-Closure-
# Coverage Guard). Any PlanRow with status in {applied, completed, closed,
# archived} must record when it was applied. Ratchet at current count.
# ---------------------------------------------------------------------------

PLAN_ROWS_COMPLETED_WITHOUT_APPLIED_AT_CEILING = 30


def test_plan_rows_applied_status_must_have_applied_at_utc():
    """Any PlanRow row whose status indicates completion must have a
    non-empty applied_at_utc. Currently 30 rows violate this; ratchet
    keeps it from growing.
    """
    import pathlib
    plan_index = REPO_ROOT / "dev" / "state" / "plan_index.jsonl"
    if not plan_index.exists():
        pytest.skip("plan_index.jsonl not present")
    completed_states = {"applied", "completed", "closed", "archived"}
    mismatched = 0
    for line in plan_index.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = _json_module.loads(line)
        except _json_module.JSONDecodeError:
            continue
        status = str(row.get("status") or "").strip().lower()
        if status not in completed_states:
            continue
        applied_at = str(row.get("applied_at_utc") or "").strip()
        if not applied_at:
            mismatched += 1
    assert mismatched <= PLAN_ROWS_COMPLETED_WITHOUT_APPLIED_AT_CEILING, (
        "INVARIANT VIOLATED: plan_rows_applied_status_must_have_applied_at_utc\n"
        f"  current count: {mismatched}\n"
        f"  ceiling:       {PLAN_ROWS_COMPLETED_WITHOUT_APPLIED_AT_CEILING}\n"
        "\n"
        "Per A12 G13: any PlanRow whose status indicates completion\n"
        "(applied / completed / closed / archived) must have\n"
        "applied_at_utc set. Currently this is a typed-state debt\n"
        "ratchet; walk it down by backfilling timestamps or moving\n"
        "the rows to a different status."
    )


# ---------------------------------------------------------------------------
# Invariant 24 - plan_rows_applied_must_have_commit_anchor_ref
#
# Same source (A12 G13/G14). Rows marked 'applied' must name a commit.
# ---------------------------------------------------------------------------

PLAN_ROWS_APPLIED_WITHOUT_COMMIT_CEILING = 10


def test_plan_rows_applied_must_have_commit_anchor_ref():
    """Any PlanRow with status='applied' must record commit_anchor_ref.
    Currently 10 rows violate this; ratchet at the live count.
    """
    import pathlib
    plan_index = REPO_ROOT / "dev" / "state" / "plan_index.jsonl"
    if not plan_index.exists():
        pytest.skip("plan_index.jsonl not present")
    mismatched = 0
    for line in plan_index.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = _json_module.loads(line)
        except _json_module.JSONDecodeError:
            continue
        if str(row.get("status") or "").strip().lower() != "applied":
            continue
        if not str(row.get("commit_anchor_ref") or "").strip():
            mismatched += 1
    assert mismatched <= PLAN_ROWS_APPLIED_WITHOUT_COMMIT_CEILING, (
        "INVARIANT VIOLATED: plan_rows_applied_must_have_commit_anchor_ref\n"
        f"  current count: {mismatched}\n"
        f"  ceiling:       {PLAN_ROWS_APPLIED_WITHOUT_COMMIT_CEILING}\n"
        "\n"
        "Per A12 G14: rows applied must have a typed commit anchor.\n"
        "Ratchet at the existing debt count."
    )


def test_gate_blocker_source_must_match_unsatisfied_ground_truth_receipt():
    """If the latest receipt is unsatisfied AND the gate blocks, the gate's
    `final_response_gate.source` must be 'ground_truth_probe_receipt'.

    This catches the exact contradiction observed during E2-minimal
    execution: the receipt verdict was 'unsatisfied' but the gate cited
    'continuation_signal' (orchestration check) as the block reason,
    hiding the typed proof from any reading agent.
    """
    # Read the gate FIRST so the receipt-state check below matches the
    # ledger state at the moment the gate evaluated. Reading the ledger
    # first creates a race: a new probe receipt can land between the
    # ledger read and the gate read, and the test sees state that does
    # not match what the gate evaluated.
    gate_output = _run_develop_next_with_final_response_gate()
    latest = _read_latest_ground_truth_receipt()
    if latest is None:
        pytest.skip(
            "no ground-truth-probe receipt ledger entries - invariant not in scope"
        )
    if latest.get("verdict") == "satisfied":
        pytest.skip(
            f"latest receipt verdict is {latest.get('verdict')!r}; invariant only "
            "applies when an unsatisfied receipt is the most recent ledger row"
        )

    gate_block = gate_output.get("final_response_gate") or {}
    allow_final_response = gate_block.get("allow_final_response", True)
    gate_source = gate_block.get("source") or ""
    gate_reason = gate_block.get("reason") or ""

    if allow_final_response:
        pytest.skip(
            "gate is currently allowing final response - invariant only "
            "applies when the gate is blocking"
        )

    assert gate_source == "ground_truth_probe_receipt", (
        "INVARIANT VIOLATED: "
        "gate_blocker_source_must_match_unsatisfied_ground_truth_receipt\n"
        f"  ground_truth_probe_receipt.verdict: {latest.get('verdict')!r}\n"
        f"  ground_truth_probe_receipt.created_at_utc: {latest.get('created_at_utc')!r}\n"
        f"  final_response_gate.source: {gate_source!r}\n"
        f"  final_response_gate.reason: {gate_reason!r}\n"
        f"  final_response_gate.allow_final_response: {allow_final_response}\n"
        "  The receipt ledger has an UNSATISFIED row but the gate cites a\n"
        "  different blocker source. A consuming agent reading the gate\n"
        "  output never sees the typed receipt as the block reason — the\n"
        "  authoritative proof is hidden behind orchestration metadata.\n"
        "  Per the live-state semantic TDD plan: typed receipt verdicts are\n"
        "  authoritative proof and MUST surface as the canonical block\n"
        "  reason whenever they are unsatisfied.\n"
        "  Fix lives in commands/development/final_response_gate.py: when\n"
        "  _ground_truth_receipt_final_response_block() returns a typed\n"
        "  block, it must be preferred over orchestration-signal blocks."
    )

