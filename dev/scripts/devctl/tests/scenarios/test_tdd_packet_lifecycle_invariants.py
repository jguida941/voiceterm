"""TDD-discovery scenarios for packet lifecycle invariants (red-first).

Per the AntiDumbass Role-Boundary Amendment (lines 731-825) and the A19
"Stale Packet Hygiene" amendment (lines 1185-1342) in
``delete_after_ingest.md``, the operator asserts the system should enforce
several invariants but currently does not. These are TDD-discovery tests:
each test asserts the BEHAVIOR THE SYSTEM SHOULD HAVE; if the test FAILS
("RED"), the failure IS the discovery of a real invariant gap.

Plan refs:
- delete_after_ingest.md lines 311-333 (Jump Index G23-G39, A18, A19/G40)
- delete_after_ingest.md lines 731-895 (AntiDumbass amendments)
- delete_after_ingest.md lines 1185-1342 (A19 Stale Packet Hygiene)
- delete_after_ingest.md lines 1249-1295 (G40 acceptance criteria)

Live evidence at 2026-05-22 (sourced from
``dev/reports/review_channel/events/trace.ndjson``):
- past_ttl_pending (not expired): 2,371 packets
- delivery_emitted_at_utc empty/None: 3,595 packets (rev_pkt_4827 cited
  in A19 amendment as canonical example)
- implementer-targeted, no body_observed: 472 packets
- cross-role observations seen in live trace: 49 (spoof candidates)
- cross-session observations seen in live trace: 8 (spoof candidates)

Role: ``tdd_first_role`` / ``tdd_discovery`` — discovers gaps via failing
assertions; does NOT carry mutation authority for production code. Per
``delete_after_ingest.md`` lines 776-781, "The TDD role does not get
special mutation authority; it discovers and proves the broken invariant
through the same typed role/session/capability substrate."

Test markers:
- Tests prefixed ``test_red_*`` are EXPECTED TO FAIL on current code.
  When they fail, the failure is the invariant gap discovery.
- Tests prefixed ``test_green_*`` document behavior that already works
  and serve as anchors against regression.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from pathlib import Path

import pytest

from dev.scripts.checks import check_packet_body_observation_route as g23_guard
from dev.scripts.devctl.review_channel.pending_packet_core import (
    partition_live_pending_packets,
)

# ---------------------------------------------------------------------------
# Repo path resolution
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[5]
TRACE_PATH = REPO_ROOT / "dev/reports/review_channel/events/trace.ndjson"


def _iter_events() -> Iterable[Mapping[str, object]]:
    if not TRACE_PATH.exists():
        return ()
    rows: list[Mapping[str, object]] = []
    with TRACE_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            text = line.strip()
            if not text:
                continue
            try:
                payload = json.loads(text)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, Mapping):
                rows.append(payload)
    return tuple(rows)


def _index_live_trace() -> dict[str, object]:
    posts: dict[str, Mapping[str, object]] = {}
    expired: set[str] = set()
    observed: dict[str, list[Mapping[str, object]]] = {}
    for event in _iter_events():
        event_type = str(event.get("event_type") or "").strip()
        packet_id = str(event.get("packet_id") or "").strip()
        if not packet_id:
            continue
        if event_type == "packet_posted":
            posts.setdefault(packet_id, event)
        elif event_type == "packet_expired":
            expired.add(packet_id)
        elif event_type == "packet_body_observed":
            observed.setdefault(packet_id, []).append(event)
    return {"posts": posts, "expired": expired, "observed": observed}


# ---------------------------------------------------------------------------
# Fixture builders
# ---------------------------------------------------------------------------


def _make_packet(
    *,
    packet_id: str,
    kind: str = "action_request",
    status: str = "pending",
    posted_at: str,
    expires_at: str | None = None,
    delivery_emitted_at_utc: object = None,
    target_role: str = "implementer",
    target_session_id: str = "session-claude-A",
    body: str = "hello",
    plan_id: str = "MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1",
    target_ref: str = "plan://MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1",
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "packet_id": packet_id,
        "kind": kind,
        "status": status,
        "posted_at": posted_at,
        "expires_at_utc": expires_at,
        "delivery_emitted_at_utc": delivery_emitted_at_utc,
        "target_role": target_role,
        "target_session_id": target_session_id,
        "body": body,
        "target_kind": "plan",
        "target_ref": target_ref,
        "plan_id": plan_id,
        "from_agent": "codex",
        "to_agent": "claude",
        "actor_role": "reviewer",
        "session_id": "019e500d-790b-7033-bf01-34ee6ae08399",
        "requested_action": "implementer_handoff",
        "approval_required": False,
    }


def _make_packet_posted_event(packet: Mapping[str, object]) -> dict[str, object]:
    payload = dict(packet)
    payload["event_type"] = "packet_posted"
    payload["event_id"] = f"evt-posted-{packet.get('packet_id')}"
    return payload


def _make_body_observed_event(
    *,
    packet_id: str,
    role: str,
    session: str,
    body_digest: str = "abc123",
    event_suffix: str = "1",
) -> dict[str, object]:
    return {
        "event_type": "packet_body_observed",
        "event_id": f"evt-observed-{packet_id}-{event_suffix}",
        "packet_id": packet_id,
        "body_observed_role": role,
        "body_observed_session_id": session,
        "body_observed_at_utc": "2026-05-22T18:00:00Z",
        "body_digest": body_digest,
    }


# ---------------------------------------------------------------------------
# Invariant 1: Lifecycle progression — no silent delivery stall
# ---------------------------------------------------------------------------


def test_red_invariant_1_lifecycle_progression_no_silent_delivery_stall():
    """A pending action_request older than 5 minutes whose ``delivery_emitted_at_utc``
    is None/empty must surface a typed blocker. The system currently lets this
    state persist silently.

    Plan ref: A19 G40 acceptance criterion 3 (line 1263-1265 in
    delete_after_ingest.md):
        "delivery_emitted_at_utc is None for any pending packet whose
         posted_at is older than 5 minutes and whose route is sanctioned by
         the control-decision obedience layer."
    Live evidence: rev_pkt_4827 cited in A19 amendment (line 1206-1208) as
    canonical example. The live trace shows 3,595 packets with
    delivery_emitted_at_utc=None.
    """
    # 6 minutes old, no delivery stamp — must be flagged.
    now = datetime(2026, 5, 22, 18, 0, 0, tzinfo=timezone.utc)
    posted_at = "2026-05-22T17:54:00Z"

    packet = _make_packet(
        packet_id="rev_pkt_DELIVERY_STALL",
        kind="action_request",
        posted_at=posted_at,
        expires_at="2026-05-22T18:30:00Z",
        delivery_emitted_at_utc=None,
    )

    # Attempt to import the helper this invariant SHOULD expose. If it
    # doesn't exist yet, that's the gap.
    try:
        from dev.scripts.checks.check_packet_hygiene_enforcement import (
            evaluate_delivery_stall,
        )
    except ImportError:
        pytest.fail(
            "RED: A19 G40 (check_packet_hygiene_enforcement.py) does not "
            "exist yet. Per delete_after_ingest.md line 1251, this guard "
            "must exist and detect delivery-stall packets. Missing module "
            "is itself the invariant gap."
        )

    report = evaluate_delivery_stall(
        packets=(packet,), now=now, stall_threshold_seconds=300
    )
    assert report["ok"] is False, (
        f"RED: delivery stall on {packet['packet_id']} not detected. "
        f"posted_at={posted_at} is 6 min old, delivery_emitted_at_utc=None, "
        "but the system passed."
    )
    assert "rev_pkt_DELIVERY_STALL" in {
        v.get("packet_id") for v in report.get("violations", ())
    }


def test_red_invariant_1b_live_trace_has_delivery_stall_packets():
    """The live trace itself must not show 3000+ packets with
    delivery_emitted_at_utc=None and posted_at > 5 minutes old without typed
    blocker evidence.

    Plan ref: A19 acceptance criteria, lines 1243-1245:
        "delivery_emitted_at_utc must move forward when the post completes
         the delivery side of the lifecycle, or a typed blocker must be
         emitted explaining why delivery is pending."
    """
    trace = _index_live_trace()
    posts = trace["posts"]
    if not posts:
        pytest.skip("trace.ndjson absent; cannot assert live invariant")

    stalled = []
    for packet_id, post in posts.items():
        if post.get("delivery_emitted_at_utc"):
            continue
        # delivery_emitted_at_utc empty/None
        posted_at = str(post.get("posted_at") or post.get("timestamp_utc") or "")
        if not posted_at:
            continue
        try:
            dt = datetime.fromisoformat(posted_at.replace("Z", "+00:00"))
        except ValueError:
            continue
        # We measure against a fixed cutoff so the test is deterministic.
        # Anything posted before 2026-05-22 with no delivery stamp is well
        # beyond the 5-minute threshold.
        cutoff = datetime(2026, 5, 22, 0, 0, 0, tzinfo=timezone.utc)
        if dt.astimezone(timezone.utc) < cutoff:
            stalled.append(packet_id)

    # If the invariant held, the live count should be 0. The plan asserts
    # it is much greater than 0.
    assert len(stalled) == 0, (
        f"RED: {len(stalled)} live packets older than 2026-05-22 have "
        f"delivery_emitted_at_utc=None and no typed blocker. "
        f"sample={stalled[:5]}"
    )


# ---------------------------------------------------------------------------
# Invariant 2: Stale-packet hygiene — past-TTL must not surface as pending
# ---------------------------------------------------------------------------


def test_green_invariant_2_partition_helper_classifies_past_ttl_as_stale():
    """The unit-level helper ``partition_live_pending_packets`` correctly
    separates past-TTL packets into the ``stale`` bucket. This is a GREEN
    anchor: the SHAPE exists, but the SYSTEM-LEVEL invariant fails
    elsewhere (see test_red_invariant_2b which checks the inbox-read
    path actually USES this filter).

    Plan ref: A19 acceptance criteria, lines 1239-1242.
    """
    # Past-TTL action_request
    past_expiry = "2026-05-21T00:00:00Z"  # well in the past
    posted = "2026-05-20T22:00:00Z"
    packet = _make_packet(
        packet_id="rev_pkt_STALE_TTL",
        kind="action_request",
        posted_at=posted,
        expires_at=past_expiry,
        delivery_emitted_at_utc=posted,
    )

    live, stale = partition_live_pending_packets([packet])

    # Invariant: past-TTL action_requests must not appear as "live pending".
    live_ids = {str(p.get("packet_id")) for p in live if isinstance(p, Mapping)}
    assert "rev_pkt_STALE_TTL" not in live_ids, (
        "RED: a past-TTL pending action_request still surfaces in "
        "partition_live_pending_packets's 'live' bucket. It should be "
        "moved to 'stale' (which auto-archives) OR an explicit "
        "--include-stale flag must be required."
    )
    # It SHOULD have ended up in stale.
    stale_ids = {str(p.get("packet_id")) for p in stale if isinstance(p, Mapping)}
    assert "rev_pkt_STALE_TTL" in stale_ids, (
        "RED: past-TTL packet not detected as stale by "
        "partition_live_pending_packets."
    )


def test_red_invariant_2b_inbox_default_excludes_past_ttl():
    """When the user calls ``review-channel --action inbox`` WITHOUT
    ``--include-stale``, the projection must NOT return past-TTL packets
    in the ``pending`` count.

    Plan ref: A19 line 1239-1242. The operator measured 273 pending in
    Claude's inbox; 182 of those were 1-3d old. The invariant is that
    only currently-actionable packets should appear.
    """
    from dev.scripts.devctl.review_channel.pending_packet_storage import (
        load_pending_packet_queue,
    )

    # Per plan, the inbox API should accept include_stale=False (default).
    # We assert the helper signature supports this. If not, gap exists.
    import inspect

    sig = inspect.signature(load_pending_packet_queue)
    assert "include_stale" in sig.parameters, (
        "RED: load_pending_packet_queue has no `include_stale` parameter. "
        "Per A19 amendment line 1241, inbox queries must hide past-TTL "
        "packets by default and require an explicit --include-stale flag."
    )


# ---------------------------------------------------------------------------
# Invariant 3: Body-observation route uniqueness — no cross-role/session
# ---------------------------------------------------------------------------


def test_green_invariant_3a_g23_blocks_cross_role_observation():
    """G23 (check_packet_body_observation_route.py) already enforces that a
    body_observation event from the wrong role is a spoofing violation.
    This green test anchors against regression.

    Plan ref: G23 (Jump Index line 316), implemented at
    dev/scripts/checks/check_packet_body_observation_route.py.
    """
    events = [
        {
            "event_type": "packet_posted",
            "event_id": "evt-posted-X",
            "packet_id": "rev_pkt_X",
            "body": "hello",
            "target_role": "implementer",
            "target_session_id": "session-claude-A",
            "target_ref": "plan:MP-ROW",
            "plan_id": "MP-ROW",
        },
        {
            "event_type": "packet_body_observed",
            "event_id": "evt-observed-X-1",
            "packet_id": "rev_pkt_X",
            "body_observed_role": "reviewer",  # WRONG ROLE — should be implementer
            "body_observed_session_id": "session-claude-A",
            "body_observed_at_utc": "2026-05-22T18:00:00Z",
            "body_digest": "abc",
        },
    ]
    report = g23_guard.build_report(events=events)
    assert report["ok"] is False
    reasons = {v["reason"] for v in report["violations"]}
    assert g23_guard.REASON_CROSS_ROLE_SPOOF in reasons


def test_red_invariant_3b_live_trace_has_cross_role_observations():
    """The live trace must not contain cross-role body observations once
    G23 is wired into check-router AND historical observations are
    backfilled or audited.

    Per the live trace snapshot, 49 packets have body_observed_role !=
    target_role. G23 catches these structurally but the trace itself still
    carries the historic violations; this test documents the gap until a
    typed remediation receipt is emitted.
    """
    trace = _index_live_trace()
    posts: dict[str, Mapping[str, object]] = trace["posts"]
    observed: dict[str, list[Mapping[str, object]]] = trace["observed"]
    if not posts:
        pytest.skip("trace.ndjson absent")

    cross_role = []
    for packet_id, obs_events in observed.items():
        post = posts.get(packet_id)
        if not post:
            continue
        target_role = str(post.get("target_role") or "").strip()
        if not target_role:
            continue
        for obs in obs_events:
            observed_role = str(obs.get("body_observed_role") or "").strip()
            if observed_role and observed_role != target_role:
                cross_role.append((packet_id, target_role, observed_role))
                break

    assert len(cross_role) == 0, (
        f"RED: {len(cross_role)} live packets have cross-role body "
        f"observations and no audit/remediation receipt. "
        f"sample={cross_role[:3]}"
    )


# ---------------------------------------------------------------------------
# Invariant 4: Control-decision artifact must refresh, not silently fail
# ---------------------------------------------------------------------------


def test_red_invariant_4_control_decision_artifact_auto_refreshes():
    """When a previously-authorized actor/role/session reposts the same
    ``task_progress`` packet and the control-decision artifact has aged
    past its event-rank, the post must EITHER auto-refresh from typed
    lifecycle state OR return a typed ``needs_refresh`` blocker — never
    silent ``control_decision_obedience_failed``.

    Plan refs:
    - delete_after_ingest.md lines 877-891 (collaboration blocker
      evidence: ``control_decision_obedience_failed`` and
      ``mutation_attempt_after_may_mutate_false``)
    - delete_after_ingest.md lines 1335-1342 (A19 evidence: claude post
      attempts hit ``control_decision_obedience_failed`` repeatedly)

    The system currently returns a stale-decision blocker only when the
    decision input was present but stale; if the decision is absent the
    error is raw ``no_control_decision_input`` which gives the agent no
    actionable next step.
    """
    from dev.scripts.devctl.runtime.control_decision_obedience import (
        evaluate_control_decision_obedience,
    )

    # Decision absent; one attempted action — operator expects a typed
    # "auto-refresh attempted" or "needs_refresh" outcome with a
    # next_command, not a raw violation.
    attempted_action = {
        "action_kind": "review-channel.post",
        "command": "review-channel --action post --kind task_progress",
        "actor": "claude",
        "role": "implementer",
        "session_id": "session-claude-A",
        "observed_event_id": "rev_evt_85852",
        "started_at_utc": "2026-05-22T18:18:00Z",
    }

    report = evaluate_control_decision_obedience(
        decision=None,
        attempted_actions=(attempted_action,),
    )

    payload = report.to_dict()
    assert report.ok is False  # the surface failure is expected

    # The invariant: when a previously-authorized actor reposts and the
    # artifact is gone, the report must carry a typed refresh hint, not
    # only the raw ``no_control_decision_input`` violation.
    has_refresh_hint = (
        payload.get("stale_decision_blocker") is not None
        or any(
            "refresh" in str(v.get("reason") or "").lower()
            or "auto_refresh" in str(v.get("reason") or "").lower()
            for v in payload.get("violations") or ()
        )
        or "next_command" in payload
        or "refresh_command" in payload
    )
    assert has_refresh_hint, (
        "RED: evaluate_control_decision_obedience returns "
        "`no_control_decision_input` with no typed refresh hint or "
        "next-command. Per plan lines 877-891 the agent has no way to "
        "recover from this state except by reading the violation "
        "string. The output must include `next_command`, "
        "`refresh_command`, or a typed needs-refresh blocker."
    )


# ---------------------------------------------------------------------------
# Invariant 5: Backlog auto-disposition — queue-read auto-archives past TTL
# ---------------------------------------------------------------------------


def test_red_invariant_5_queue_read_auto_archives_past_ttl():
    """Reading the queue must transition past-``expires_at_utc`` pending
    packets to ``expired``/``archived`` automatically. Today, the
    ``expire-packets`` action is on-demand only with ``--limit 20``.

    Plan ref: A19 lines 1219-1224:
        "review-channel --action expire-packets is the only typed
         materialization path. It is on-demand, defaults to --limit 20,
         has no scheduled invocation, no inbox-read-time filter, and no
         pre-route/pre-post hook. Past-TTL packets remain visible in
         projections and inbox queries until somebody manually sweeps in
         20-packet batches."
    """
    # 5 packets, all past TTL — none have packet_expired event yet.
    packets = [
        _make_packet(
            packet_id=f"rev_pkt_QUEUE_STALE_{i}",
            kind="action_request",
            posted_at="2026-05-20T00:00:00Z",
            expires_at="2026-05-20T01:00:00Z",  # past
            delivery_emitted_at_utc="2026-05-20T00:00:00Z",
        )
        for i in range(5)
    ]

    try:
        from dev.scripts.devctl.review_channel.packet_expiry_materialization import (
            materialize_expired_packet_events,
        )
    except ImportError:
        pytest.fail("materialize_expired_packet_events not importable")

    # The invariant: queue read should auto-materialize. Check that the
    # public read API (``collect_pending_packet_queue`` or equivalent)
    # invokes the materialization automatically rather than requiring the
    # operator to call --action expire-packets manually.
    import inspect

    from dev.scripts.devctl.review_channel import pending_packet_storage

    source = inspect.getsource(pending_packet_storage)
    auto_archive_invoked = (
        "materialize_expired_packet_events" in source
        or "auto_expire" in source
        or "auto_archive" in source
    )
    assert auto_archive_invoked, (
        "RED: pending_packet_storage does not auto-archive past-TTL "
        "packets on queue read. Per A19 lines 1219-1224, the on-demand "
        "expire-packets sweep + --limit 20 default cannot drain the "
        "backlog (which sits at 542 stale_packet_count live). The queue "
        "read path must invoke materialize_expired_packet_events or "
        "another typed auto-archive seam."
    )


def test_red_invariant_5b_expire_packets_default_limit_does_not_throttle_drain():
    """The ``expire-packets --limit`` default must not be lower than the
    typical live ``stale_packet_count``. Today the default is 20 while
    live stale count is 542.

    Plan ref: A19 G40 acceptance criterion 5 (line 1269-1271):
        "expire-packets materialization defaults are set higher than the
         live stale count without explicit policy reason, so a single
         sweep cannot drain the backlog."
    """
    # Locate the limit default behavior in the expire-packets action handler.
    # The plan-cited default is 20 (line 1221: "defaults to --limit 20").
    from dev.scripts.devctl.commands.review_channel import (
        event_expire_packets_action as expire_action,
    )

    # The handler currently passes ``limit`` through to
    # ``materialize_expired_packet_events`` as-is when > 0; if no policy-
    # backed clamp upward exists (e.g., a "drain when stale_count is high"
    # auto-policy), the default is whatever the CLI provides. Grep the
    # handler source for any clamp or auto-policy that would raise the
    # limit to drain a 542-packet backlog.
    import inspect

    source = inspect.getsource(expire_action)
    has_auto_drain_policy = (
        "drain_full" in source
        or "stale_count" in source
        or "auto_policy" in source
        or "542" in source
        or "configurable_default" in source
    )
    assert has_auto_drain_policy, (
        "RED: event_expire_packets_action passes user-supplied --limit "
        "through unchanged. There is no policy-backed clamp upward to "
        "drain a backlog of 542 stale packets in one sweep. Per A19 G40 "
        "criterion 5 (line 1269-1271), the default must not throttle "
        "drain when the live stale count is much higher."
    )


# ---------------------------------------------------------------------------
# Invariant 6: Old-packet triage — pending packets on closed rows auto-resolve
# ---------------------------------------------------------------------------


def test_red_invariant_6_packets_bound_to_closed_rows_auto_dismissed():
    """A pending packet whose ``target_ref`` points to a row that no longer
    appears in ``plan_index.jsonl`` (or is marked closed in plan state)
    must be auto-dismissed or auto-superseded. The 542 stale packets in
    claude's inbox include many bound to long-closed rows.

    Plan ref: A19 G40 acceptance criterion 4 (line 1266-1268):
        "A live pending packet older than the hygiene window has no
         durable binding: no PlanRow target, no finding binding, no
         defer/reject/supersede receipt, no closure receipt, and no
         explicit operator-bound TTL."
    """
    # Construct a packet bound to a clearly-fake row that won't exist
    # in plan state.
    packet = _make_packet(
        packet_id="rev_pkt_CLOSED_ROW",
        kind="action_request",
        posted_at="2026-05-20T00:00:00Z",
        expires_at="2026-05-22T00:00:00Z",
        delivery_emitted_at_utc="2026-05-20T00:00:00Z",
        target_ref="plan://MP-DOES-NOT-EXIST-CLOSED-ROW",
        plan_id="MP-DOES-NOT-EXIST-CLOSED-ROW",
    )

    try:
        from dev.scripts.checks.check_packet_hygiene_enforcement import (
            evaluate_durable_binding,
        )
    except ImportError:
        pytest.fail(
            "RED: check_packet_hygiene_enforcement.py (A19 G40) does not "
            "exist. Per plan line 1251 this guard must implement criterion "
            "4 (durable_binding_missing_count). Missing module = gap."
        )

    report = evaluate_durable_binding(
        packets=(packet,),
        plan_row_ids=("MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1",),
    )
    assert report["ok"] is False
    assert "rev_pkt_CLOSED_ROW" in {
        v.get("packet_id") for v in report.get("violations", ())
    }


# ---------------------------------------------------------------------------
# Invariant 7 (bonus): G23 must be wired into check-router
# ---------------------------------------------------------------------------


def test_red_invariant_7_g40_is_wired_into_check_router():
    """Per A19 line 1291-1295, G40 must be wired into check-router. If
    not in check-router, it does not exist.

    Plan ref: A19 amendment line 1291-1295:
        "The guard must be wired into check-router. If it is not in
         check-router, it does not exist."
    """
    from dev.scripts.devctl.commands.check import router_python_tests

    # The registration table is named ``_DEVCTL_TEST_TARGETS`` and maps
    # source paths to required test paths.
    registrations = getattr(router_python_tests, "_DEVCTL_TEST_TARGETS", None)
    assert registrations is not None, (
        "RED: router_python_tests._DEVCTL_TEST_TARGETS not exposed. "
        "Cannot verify G40 wiring."
    )

    source_paths = {str(source_path) for source_path, _ in registrations}
    assert (
        "dev/scripts/checks/check_packet_hygiene_enforcement.py" in source_paths
    ), (
        "RED: G40 check_packet_hygiene_enforcement.py is not registered in "
        "router_python_tests._DEVCTL_TEST_TARGETS. Per plan line 1291-1295, "
        "the guard does not exist until wired into check-router."
    )


# ---------------------------------------------------------------------------
# Anchor: structural assertions that already pass (regression anchor)
# ---------------------------------------------------------------------------


def test_green_partition_handles_well_formed_terminal_packet():
    """A packet with status=expired AND a clear lifecycle event must end up
    in the stale bucket. Anchors that the existing partition helper does
    handle the explicit terminal state correctly.
    """
    packet = _make_packet(
        packet_id="rev_pkt_TERMINAL",
        kind="action_request",
        posted_at="2026-05-20T00:00:00Z",
        expires_at="2026-05-20T01:00:00Z",
        delivery_emitted_at_utc="2026-05-20T00:00:00Z",
        status="expired",
    )
    live, stale = partition_live_pending_packets([packet])
    live_ids = {str(p.get("packet_id")) for p in live if isinstance(p, Mapping)}
    assert "rev_pkt_TERMINAL" not in live_ids


def test_green_g23_passes_when_target_matches_observation():
    """When the body_observed event matches the target role and session,
    G23 passes. Regression anchor.
    """
    events = [
        {
            "event_type": "packet_posted",
            "event_id": "evt-posted-ok",
            "packet_id": "rev_pkt_OK",
            "body": "hello",
            "target_role": "implementer",
            "target_session_id": "session-claude-A",
            "target_ref": "plan:MP-ROW-OK",
            "plan_id": "MP-ROW-OK",
        },
        {
            "event_type": "packet_body_observed",
            "event_id": "evt-observed-ok-1",
            "packet_id": "rev_pkt_OK",
            "body_observed_role": "implementer",
            "body_observed_session_id": "session-claude-A",
            "body_observed_at_utc": "2026-05-22T18:00:00Z",
            "body_digest": "abc",
        },
    ]
    report = g23_guard.build_report(events=events)
    assert report["ok"] is True
    assert report["violation_count"] == 0
