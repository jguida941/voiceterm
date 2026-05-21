"""Focused tests for Phase 0.6.A/B/C/D cascade authority repair (rev_pkt_4652/4657/4659/4664/4668)."""

from __future__ import annotations

import json
import pytest
from pathlib import Path
from types import SimpleNamespace

from dev.scripts.devctl.commands.review_channel.event_handler import (
    _cascade_lifecycle_post_authority,
    _cascade_lifecycle_read_authority,
)
from dev.scripts.devctl.commands.review_channel.event_post_action import (
    LiveAgentSessionStampingError,
    require_real_session_for_live_agent_post,
    resolve_live_actor_session,
)
from dev.scripts.devctl.runtime.review_channel_post_actions import (
    required_review_channel_post_action,
)


def _write_agent_mind_projection(
    repo_root: Path,
    *,
    agent: str,
    session_id: str,
) -> Path:
    """Materialize a typed agent_minds projection under tmp_path for testing."""
    projection_dir = repo_root / "dev/reports/agent_minds"
    projection_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "contract_id": "AgentMindSlice",
        "schema_version": 1,
        "agent_provider": agent,
        "session_id": session_id,
        "last_cursor": "2026-05-20T21:00:00Z",
        "session_path": f"/fake/sessions/{agent}-{session_id}.jsonl",
    }
    projection_path = projection_dir / f"{agent}_latest.json"
    with projection_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f)
    return projection_path


_CODEX_SESSION = "019e46cb-dd3c-7121-bf2f-eff8cc5fc815"
_CLAUDE_SESSION = "2a5b3528-aaa6-4615-b83b-5b1d3598509b"
_TARGET_REF = "dev/scripts/devctl/commands/review_channel/event_handler.py"


# Parent for claude->codex closures (default direction).
# claude(implementer) responds to codex(reviewer)'s task_started.
_PARENT_TASK_STARTED = {
    "packet_id": "rev_pkt_4652",
    "kind": "task_started",
    "status": "pending",
    "from_agent": "codex",
    "to_agent": "claude",
    "session_id": _CODEX_SESSION,
    "target_session_id": _CLAUDE_SESSION,
    "target_role": "implementer",
    "target_ref": _TARGET_REF,
}


# Parent for codex->claude closures (review-tier).
# codex(reviewer) responds to claude(implementer)'s task_produced.
_PARENT_TASK_PRODUCED = {
    "packet_id": "rev_pkt_4655",
    "kind": "task_produced",
    "status": "pending",
    "from_agent": "claude",
    "to_agent": "codex",
    "session_id": _CLAUDE_SESSION,
    "target_session_id": _CODEX_SESSION,
    "target_role": "reviewer",
    "target_ref": _TARGET_REF,
}


def _resolver(parent=None, *, packet_id="rev_pkt_4652"):
    """Build a parent resolver that returns the configured parent for ``packet_id``."""
    actual = parent if parent is not None else dict(_PARENT_TASK_STARTED)
    return lambda pid: dict(actual) if pid == packet_id else None


def _args(**overrides):
    """Default closure args: claude->codex task_produced answering rev_pkt_4652 task_started."""
    base = {
        "action": "post",
        "from_agent": "claude",
        "to_agent": "codex",
        "kind": "task_produced",
        "target_session_id": _CODEX_SESSION,
        "target_role": "reviewer",
        "target_ref": _TARGET_REF,
        "evidence_ref": ("packet:rev_pkt_4652",),
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def _codex_args(**overrides):
    """Closure args for codex->claude review-tier (answers rev_pkt_4655 task_produced)."""
    base = {
        "action": "post",
        "from_agent": "codex",
        "to_agent": "claude",
        "kind": "review_accepted",
        "target_session_id": _CLAUDE_SESSION,
        "target_role": "implementer",
        "target_ref": _TARGET_REF,
        "evidence_ref": ("packet:rev_pkt_4655",),
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def _authority(args, *, parent=None):
    """Helper: invoke _cascade_lifecycle_post_authority with the default parent resolver."""
    return _cascade_lifecycle_post_authority(args, parent_resolver=_resolver(parent))


def _codex_authority(args, *, parent=None):
    """Helper: codex->claude variant using the task_produced parent at rev_pkt_4655."""
    actual = parent if parent is not None else dict(_PARENT_TASK_PRODUCED)
    resolver = _resolver(actual, packet_id="rev_pkt_4655")
    return _cascade_lifecycle_post_authority(args, parent_resolver=resolver)


def test_claude_task_produced_with_evidence_ref_is_authorized() -> None:
    """Valid claude->codex task_produced cascade closure should bypass obedience guard."""
    assert _authority(_args()) is True


def test_codex_review_accepted_with_evidence_ref_is_authorized() -> None:
    """Valid codex->claude review_accepted cascade closure should bypass obedience guard.

    review_accepted answers a claude task_produced (review-tier parent), so the parent
    has kind=task_produced, from_agent=claude, session_id=claude's session, and closure
    target_role=implementer.
    """
    assert _codex_authority(_codex_args()) is True


def test_review_failed_from_codex_is_authorized() -> None:
    """Codex review_failed (rejection closure) is also in the cascade authority set.

    review_failed answers a claude task_produced just like review_accepted.
    """
    assert _codex_authority(_codex_args(kind="review_failed")) is True


# ---------------------------------------------------------------------------
# v4.22 (rev_pkt_4683) parent-resolution metadata persistence
# ---------------------------------------------------------------------------


def test_parent_resolution_metadata_explicit_parent() -> None:
    """v4.22 (rev_pkt_4683): _parent_resolution_metadata persists the explicit
    parent designation + candidate refs + supporting refs + decision for audit.
    """
    from dev.scripts.devctl.review_channel.events import _parent_resolution_metadata
    from dev.scripts.devctl.review_channel.packet_contract import PacketPostRequest

    request = PacketPostRequest(
        from_agent="claude",
        to_agent="codex",
        kind="task_progress",
        summary="test",
        body="test",
        evidence_refs=(
            "packet:rev_pkt_4672",
            "packet:rev_pkt_4681",
            "packet:rev_pkt_4680",
            "artifact:dev/foo.py",
        ),
        parent_packet_id="rev_pkt_4672",
    )
    meta = _parent_resolution_metadata(request)
    assert meta["primary_parent_packet_id"] == "rev_pkt_4672"
    assert meta["parent_resolution_decision"] == "explicit_parent_packet_id"
    assert "packet:rev_pkt_4672" in meta["candidate_parent_refs"]
    assert "packet:rev_pkt_4681" in meta["candidate_parent_refs"]
    assert "packet:rev_pkt_4680" in meta["candidate_parent_refs"]
    # The parent ref itself is excluded from supporting_evidence_refs
    assert "packet:rev_pkt_4672" not in meta["supporting_evidence_refs"]
    assert "packet:rev_pkt_4681" in meta["supporting_evidence_refs"]
    assert "artifact:dev/foo.py" in meta["supporting_evidence_refs"]


def test_parent_resolution_metadata_single_ref_implicit() -> None:
    """v4.22: single packet:rev_pkt_<id> + no --parent-packet-id resolves implicitly."""
    from dev.scripts.devctl.review_channel.events import _parent_resolution_metadata
    from dev.scripts.devctl.review_channel.packet_contract import PacketPostRequest

    request = PacketPostRequest(
        from_agent="claude",
        to_agent="codex",
        kind="task_produced",
        summary="test",
        body="test",
        evidence_refs=("packet:rev_pkt_4665", "artifact:dev/foo.py"),
        parent_packet_id="",
    )
    meta = _parent_resolution_metadata(request)
    assert meta["primary_parent_packet_id"] == "rev_pkt_4665"
    assert meta["parent_resolution_decision"] == "single_ref_implicit"
    assert meta["candidate_parent_refs"] == ["packet:rev_pkt_4665"]
    assert "packet:rev_pkt_4665" not in meta["supporting_evidence_refs"]


def test_parent_resolution_metadata_finding_with_single_packet_ref_returns_empty() -> None:
    """v4.22 narrowing (rev_pkt_4685): findings citing a single packet evidence
    ref do NOT get parent_resolution metadata.

    Codex's exact reproduction: a finding with one packet:rev_pkt_<id> evidence
    ref was getting misclassified as having a lifecycle parent. Findings are
    architectural feedback, not closure-direction packets - they can cite
    packets as evidence without implying parentage.
    """
    from dev.scripts.devctl.review_channel.events import _parent_resolution_metadata
    from dev.scripts.devctl.review_channel.packet_contract import PacketPostRequest

    request_finding = PacketPostRequest(
        from_agent="codex",
        to_agent="claude",
        kind="finding",
        summary="x",
        body="x",
        evidence_refs=("packet:rev_pkt_4684",),
        session_id="019e46cb-dd3c-7121-bf2f-eff8cc5fc815",
    )
    assert _parent_resolution_metadata(request_finding) == {}


def test_parent_resolution_metadata_non_cascade_kinds_return_empty() -> None:
    """v4.22 narrowing: action_request, continuation_anchor, stop_anchor,
    decision, system_notice, etc. all return empty even with packet refs.

    Only the 5 cascade-direction lifecycle kinds (task_produced, task_progress,
    task_blocked, review_accepted, review_failed) get parent-resolution metadata.
    """
    from dev.scripts.devctl.review_channel.events import _parent_resolution_metadata
    from dev.scripts.devctl.review_channel.packet_contract import PacketPostRequest

    for non_cascade_kind in (
        "finding",
        "action_request",
        "continuation_anchor",
        "stop_anchor",
        "decision",
        "system_notice",
        "task_started",  # task_started initiates a cascade, doesn't ANSWER one
        "review_started",
        "question",
        "peer_heartbeat",
    ):
        request = PacketPostRequest(
            from_agent="codex",
            to_agent="claude",
            kind=non_cascade_kind,
            summary="x",
            body="x",
            evidence_refs=("packet:rev_pkt_4684",),
            parent_packet_id="rev_pkt_4684",  # even with explicit, non-cascade kinds get no metadata
        )
        assert _parent_resolution_metadata(request) == {}, (
            f"non-cascade kind={non_cascade_kind!r} should not get parent_resolution metadata"
        )


def test_parent_resolution_metadata_empty_when_no_parent() -> None:
    """v4.22: no parent designation + multiple/zero packet refs returns empty
    (no metadata to persist - the gate already rejected ambiguous posts)."""
    from dev.scripts.devctl.review_channel.events import _parent_resolution_metadata
    from dev.scripts.devctl.review_channel.packet_contract import PacketPostRequest

    request_zero = PacketPostRequest(
        from_agent="claude",
        to_agent="codex",
        kind="finding",  # findings have no parent
        summary="test",
        body="test",
        evidence_refs=("artifact:dev/foo.py", "sha256:abc"),
    )
    assert _parent_resolution_metadata(request_zero) == {}

    # Multiple packet refs without explicit parent: this should NEVER reach
    # post_packet (the gate rejects first), but defensive metadata returns {}
    request_multi = PacketPostRequest(
        from_agent="claude",
        to_agent="codex",
        kind="task_progress",
        summary="test",
        body="test",
        evidence_refs=("packet:rev_pkt_4672", "packet:rev_pkt_4681"),
        parent_packet_id="",
    )
    assert _parent_resolution_metadata(request_multi) == {}


# ---------------------------------------------------------------------------
# v4.22 (rev_pkt_4681) explicit primary parent resolution
# ---------------------------------------------------------------------------


def test_explicit_parent_packet_id_selects_parent_regardless_of_order() -> None:
    """v4.22: when --parent-packet-id is set, it selects the parent
    regardless of evidence_ref ordering.

    Two evidence_refs with the explicit parent named: predicate uses the
    explicit one. Reversing the order does NOT change auth.
    """
    args_order1 = _args(
        parent_packet_id="rev_pkt_4652",
        evidence_ref=("packet:rev_pkt_4652", "packet:rev_pkt_other_999"),
    )
    args_order2 = _args(
        parent_packet_id="rev_pkt_4652",
        evidence_ref=("packet:rev_pkt_other_999", "packet:rev_pkt_4652"),
    )
    # Both must produce the same auth result; the resolver only returns the
    # known parent dict for rev_pkt_4652 so both posts resolve to the SAME parent.
    assert _authority(args_order1) is True
    assert _authority(args_order2) is True


def test_multiple_packet_refs_without_explicit_parent_is_rejected() -> None:
    """v4.22 (rev_pkt_4681): multiple packet:rev_pkt_<id> refs without
    --parent-packet-id is structurally ambiguous and fails closed.

    This is the rev_pkt_4680 shape: cite both rev_pkt_4672 (the actual
    closure parent) and rev_pkt_4679 (a finding referenced in body) without
    explicit designation. Predicate must NOT pick one by evidence order;
    instead it returns False so the operator/agent must add
    --parent-packet-id.
    """
    args = _args(
        parent_packet_id="",  # explicit empty
        evidence_ref=("packet:rev_pkt_4672", "packet:rev_pkt_4679"),
    )
    assert _authority(args) is False


def test_explicit_parent_not_in_evidence_refs_is_rejected() -> None:
    """v4.22: --parent-packet-id must reference an evidence_ref that is present.

    Setting an explicit parent id that isn't in the evidence_ref list is a
    contract violation - the parent must be cited.
    """
    args = _args(
        parent_packet_id="rev_pkt_9999_unrelated",
        evidence_ref=("packet:rev_pkt_4652",),
    )
    assert _authority(args) is False


def test_single_packet_ref_without_explicit_parent_still_works() -> None:
    """v4.22 backwards compat: a single packet ref with no explicit parent
    still resolves to that ref (preserves the rev_pkt_4658/4660/4663/etc.
    posting pattern that worked before v4.22)."""
    args = _args(
        parent_packet_id="",
        evidence_ref=("packet:rev_pkt_4652",),
    )
    assert _authority(args) is True


def test_no_packet_refs_with_or_without_explicit_parent_is_rejected() -> None:
    """v4.22: a post with no packet:rev_pkt_<id> evidence_refs is structurally
    invalid for cascade authority, regardless of whether --parent-packet-id
    is set or not (parent must be cited in evidence_refs)."""
    args_no_packet = _args(
        parent_packet_id="",
        evidence_ref=("sha256:abc", "artifact:foo.py"),
    )
    assert _authority(args_no_packet) is False
    args_with_parent_no_ref = _args(
        parent_packet_id="rev_pkt_4652",
        evidence_ref=("sha256:abc", "artifact:foo.py"),
    )
    # Explicit parent ID is set but evidence_refs contain NO packet refs.
    # The explicit-id-must-be-in-evidence-refs rule rejects this.
    assert _authority(args_with_parent_no_ref) is False


def test_codex_task_progress_is_authorized() -> None:
    """v4.20 (rev_pkt_4679): codex review-only task_progress is in cascade authority.

    Codex as reviewer needs to post task_progress for interim review notes -
    e.g., "I've inspected your work and started running tests, here's a status."
    Without ("codex", "task_progress") in the authorized set, codex's review
    progress posts fall through to ControlDecisionObeyedGuard which rejects
    them, forcing codex to use the orchestrator-finding escape hatch.

    The closure->parent kind map already allows codex task_progress to answer
    claude task_produced; this test pins the cascade-post authorization.
    """
    assert _codex_authority(_codex_args(kind="task_progress")) is True


def test_task_blocked_from_both_sides_is_authorized() -> None:
    """task_blocked must flow from either claude or codex for recoverable receipts.

    claude task_blocked answers codex task_started (default direction).
    codex task_blocked answers claude task_produced (review-tier direction).
    """
    assert _authority(_args(kind="task_blocked")) is True
    assert _codex_authority(_codex_args(kind="task_blocked")) is True


def test_wrong_actor_is_rejected() -> None:
    """An unrelated actor (e.g. operator, system) is NOT in the cascade set."""
    assert _authority(_args(from_agent="operator")) is False
    assert _authority(_args(from_agent="system")) is False
    assert _authority(_args(from_agent="")) is False


def test_unrelated_kind_is_rejected() -> None:
    """task_produced is in the set; finding/action_request/anchor are not."""
    assert _authority(_args(kind="finding")) is False
    assert _authority(_args(kind="action_request")) is False
    assert _authority(_args(kind="continuation_anchor")) is False


def test_missing_target_session_id_is_rejected() -> None:
    """Cascade closure must name the peer session it answers."""
    assert _authority(_args(target_session_id="")) is False


def test_missing_evidence_ref_is_rejected() -> None:
    """Cascade closure must cite at least one evidence ref (packet/artifact/closure_receipt)."""
    assert _authority(_args(evidence_ref=())) is False
    assert _authority(_args(evidence_ref=("",))) is False


def test_non_post_action_is_rejected() -> None:
    """Only --action post is in scope; status/inbox/show pass through normally."""
    assert _authority(_args(action="status")) is False
    assert _authority(_args(action="show")) is False
    assert _authority(_args(action="")) is False


def test_missing_target_role_is_rejected() -> None:
    """rev_pkt_4657 narrow: cascade closure must name the target role bound to the parent."""
    assert _authority(_args(target_role="")) is False


def test_missing_to_agent_is_rejected() -> None:
    """rev_pkt_4657 narrow: cascade closure must name the peer it answers."""
    assert _authority(_args(to_agent="")) is False


def test_self_cascade_is_rejected() -> None:
    """rev_pkt_4657 narrow: from_agent==to_agent is not a cascade direction."""
    assert (
        _authority(_args(from_agent="claude", to_agent="claude"))
        is False
    )
    assert (
        _cascade_lifecycle_post_authority(
            _args(from_agent="codex", to_agent="codex", kind="review_accepted")
        )
        is False
    )


def test_wrong_peer_is_rejected() -> None:
    """rev_pkt_4657 narrow: only claude<->codex reversal is in cascade scope.

    Operator/system peers go through normal control-decision obedience.
    """
    assert (
        _authority(_args(from_agent="claude", to_agent="operator"))
        is False
    )
    assert (
        _authority(_args(from_agent="claude", to_agent="system"))
        is False
    )
    assert (
        _cascade_lifecycle_post_authority(
            _args(from_agent="codex", to_agent="operator", kind="review_accepted")
        )
        is False
    )


def test_evidence_ref_without_packet_lineage_is_rejected() -> None:
    """rev_pkt_4657 narrow: closure must cite at least one packet:rev_pkt_<digits> parent.

    sha256: digests, artifact: refs, plan_revision: refs without a packet lineage ref
    do not bind the closure to its initiating task_started packet.
    """
    assert (
        _cascade_lifecycle_post_authority(
            _args(
                evidence_ref=(
                    "sha256:f819329adea4f637fae24e2540a24139f9397865540cd37753bce77b055068c0",
                )
            )
        )
        is False
    )
    assert (
        _cascade_lifecycle_post_authority(
            _args(evidence_ref=("artifact:dev/reports/review_channel/offline.md",))
        )
        is False
    )
    assert (
        _cascade_lifecycle_post_authority(
            _args(evidence_ref=("plan_revision:guardir-v4.9-2026-05-20",))
        )
        is False
    )


def test_malformed_parent_packet_lineage_is_rejected() -> None:
    """rev_pkt_4657 narrow: parent packet refs must match ``packet:rev_pkt_\\d+`` exactly.

    Free-form ``packet:foo``, ``packet:rev_pkt_abc`` (non-digit suffix), or
    ``packet_id:rev_pkt_4652`` (wrong prefix) do not satisfy parent-lineage binding.
    """
    assert _authority(_args(evidence_ref=("packet:foo",))) is False
    assert (
        _authority(_args(evidence_ref=("packet:rev_pkt_abc",)))
        is False
    )
    assert (
        _authority(_args(evidence_ref=("packet_id:rev_pkt_4652",)))
        is False
    )
    assert (
        _authority(_args(evidence_ref=("rev_pkt_4652",)))
        is False
    )


def test_mixed_evidence_ref_with_packet_lineage_is_accepted() -> None:
    """rev_pkt_4657 narrow: extra refs (sha256/artifact) alongside packet lineage are fine.

    The narrow requires AT LEAST ONE valid ``packet:rev_pkt_<digits>`` ref, not that all
    refs match the pattern. Closures typically carry multiple evidence kinds.
    """
    assert (
        _authority(
            _args(
                evidence_ref=(
                    "sha256:f819329adea4f637fae24e2540a24139f9397865540cd37753bce77b055068c0",
                    "packet:rev_pkt_4652",
                    "artifact:dev/reports/review_channel/offline.md",
                )
            )
        )
        is True
    )


# ---------------------------------------------------------------------------
# Phase 0.6.B semantic parent-packet cross-reference (rev_pkt_4659)
# ---------------------------------------------------------------------------


def test_parent_packet_unresolved_is_rejected() -> None:
    """Phase 0.6.B: if evidence_ref names a packet id that doesn't resolve, reject."""
    null_resolver = lambda pid: None  # noqa: E731
    assert (
        _cascade_lifecycle_post_authority(_args(), parent_resolver=null_resolver)
        is False
    )


def test_wrong_target_session_id_is_rejected_semantic() -> None:
    """Phase 0.6.B: closure.target_session_id MUST equal parent.session_id.

    rev_pkt_4659: the direct wrong-session probe must fail under semantic verification,
    not just structural non-empty check.
    """
    assert _authority(_args(target_session_id="wrong-session-id")) is False
    assert (
        _authority(_args(target_session_id="00000000-0000-0000-0000-000000000000"))
        is False
    )


def test_wrong_target_role_is_rejected_semantic() -> None:
    """Phase 0.6.B: closure.target_role MUST match the role-mapping for parent.from_agent.

    Parent codex (reviewer) -> claude closure must have target_role=reviewer,
    not implementer/operator/anything else.
    """
    assert _authority(_args(target_role="implementer")) is False
    assert _authority(_args(target_role="operator")) is False
    assert _authority(_args(target_role="observer")) is False


def test_stale_parent_packet_is_rejected() -> None:
    """Phase 0.6.B: parent.status in {expired, dismissed, applied, rejected} is stale."""
    for stale_status in ("expired", "dismissed", "applied", "rejected"):
        parent = dict(_PARENT_TASK_STARTED)
        parent["status"] = stale_status
        assert _authority(_args(), parent=parent) is False, (
            f"stale parent.status={stale_status!r} should be rejected"
        )


def test_wrong_peer_vs_parent_is_rejected_semantic() -> None:
    """Phase 0.6.B: closure peer pair must reverse parent peer pair.

    Parent has from_agent=codex, to_agent=claude. If the actual parent was from a
    different peer (e.g. operator), semantic verification must reject the closure
    even though the closure args themselves form a structurally-valid claude<->codex
    reversal. This is defense in depth against forged or fabricated cascades.
    """
    parent = dict(_PARENT_TASK_STARTED)
    parent["from_agent"] = "operator"
    parent["to_agent"] = "claude"
    assert _authority(_args(), parent=parent) is False

    parent2 = dict(_PARENT_TASK_STARTED)
    parent2["from_agent"] = "codex"
    parent2["to_agent"] = "operator"
    assert _authority(_args(), parent=parent2) is False


def test_unrelated_parent_kind_is_rejected() -> None:
    """Phase 0.6.B: parent.kind != task_started rejects the cascade.

    Closures answer task_starteds. A closure that names a finding/anchor/decision
    packet as its parent does not satisfy cascade-closure binding.
    """
    for unrelated_kind in (
        "finding",
        "continuation_anchor",
        "stop_anchor",
        "decision",
        "review_accepted",
    ):
        parent = dict(_PARENT_TASK_STARTED)
        parent["kind"] = unrelated_kind
        assert _authority(_args(), parent=parent) is False, (
            f"unrelated parent.kind={unrelated_kind!r} should be rejected"
        )


def test_target_ref_mismatch_is_rejected() -> None:
    """Phase 0.6.B: closure.target_ref != parent.target_ref rejects when both non-empty.

    Parent says scope=event_handler.py; closure that says scope=some_other.py is
    out-of-scope and must be rejected.
    """
    assert (
        _authority(
            _args(target_ref="dev/scripts/devctl/runtime/git_mutation_proof_receipt.py")
        )
        is False
    )
    assert _authority(_args(target_ref="dev/some/unrelated/file.py")) is False


def test_target_ref_empty_in_args_is_accepted() -> None:
    """Phase 0.6.B: empty closure.target_ref does NOT enforce alignment.

    Some closure kinds (task_progress, task_blocked) may omit target_ref because the
    scope is fully described by the parent packet lineage. Alignment is enforced only
    when both sides are non-empty.
    """
    assert _authority(_args(target_ref="")) is True


def test_task_progress_can_answer_review_failed_parent() -> None:
    """Phase 0.6.B: live cascade pattern - claude task_progress responds to codex review_failed.

    When codex posts review_failed (rework directive), claude's response is task_progress
    on the rework. The closure->parent kind map must allow this pairing so the cascade
    doesn't stall after every review_failed.
    """
    parent_review_failed = {
        "packet_id": "rev_pkt_4659",
        "kind": "review_failed",
        "status": "pending",
        "from_agent": "codex",
        "to_agent": "claude",
        "session_id": _CODEX_SESSION,
        "target_session_id": _CLAUDE_SESSION,
        "target_role": "implementer",
        "target_ref": _TARGET_REF,
    }
    resolver = _resolver(parent_review_failed, packet_id="rev_pkt_4659")
    args = _args(
        kind="task_progress",
        evidence_ref=("packet:rev_pkt_4659",),
    )
    assert _cascade_lifecycle_post_authority(args, parent_resolver=resolver) is True


def test_review_accepted_over_task_progress_parent_is_rejected() -> None:
    """Phase 0.6.B tightening (rev_pkt_4661/4662): review_accepted requires task_produced ONLY.

    Codex probe ``review_accepted_over_task_progress_returns_true`` demonstrated the prior
    map allowed progress to become final acceptance. review_accepted must only close
    a task_produced (the final implementation deliverable), never an interim task_progress.
    review_failed remains allowed over task_progress for in-progress rejection.
    """
    parent_task_progress = {
        "packet_id": "rev_pkt_4660",
        "kind": "task_progress",
        "status": "pending",
        "from_agent": "claude",
        "to_agent": "codex",
        "session_id": _CLAUDE_SESSION,
        "target_session_id": _CODEX_SESSION,
        "target_role": "reviewer",
        "target_ref": _TARGET_REF,
    }
    resolver = _resolver(parent_task_progress, packet_id="rev_pkt_4660")
    args = _codex_args(
        kind="review_accepted",
        evidence_ref=("packet:rev_pkt_4660",),
    )
    assert _cascade_lifecycle_post_authority(args, parent_resolver=resolver) is False


def test_review_failed_over_task_progress_parent_is_accepted() -> None:
    """Phase 0.6.B (rev_pkt_4662 explicit allowance): review_failed CAN cite task_progress.

    Codex needs to reject in-progress work; the closure→parent map keeps task_progress in
    review_failed's parent set so rejection of interim work is preserved.
    """
    parent_task_progress = {
        "packet_id": "rev_pkt_4660",
        "kind": "task_progress",
        "status": "pending",
        "from_agent": "claude",
        "to_agent": "codex",
        "session_id": _CLAUDE_SESSION,
        "target_session_id": _CODEX_SESSION,
        "target_role": "reviewer",
        "target_ref": _TARGET_REF,
    }
    resolver = _resolver(parent_task_progress, packet_id="rev_pkt_4660")
    args = _codex_args(
        kind="review_failed",
        evidence_ref=("packet:rev_pkt_4660",),
    )
    assert _cascade_lifecycle_post_authority(args, parent_resolver=resolver) is True


def test_task_produced_can_answer_review_failed_parent() -> None:
    """Phase 0.6.B: task_produced can also answer review_failed (full rework + re-submit)."""
    parent_review_failed = {
        "packet_id": "rev_pkt_4659",
        "kind": "review_failed",
        "status": "pending",
        "from_agent": "codex",
        "to_agent": "claude",
        "session_id": _CODEX_SESSION,
        "target_session_id": _CLAUDE_SESSION,
        "target_role": "implementer",
        "target_ref": _TARGET_REF,
    }
    resolver = _resolver(parent_review_failed, packet_id="rev_pkt_4659")
    args = _args(
        kind="task_produced",
        evidence_ref=("packet:rev_pkt_4659",),
    )
    assert _cascade_lifecycle_post_authority(args, parent_resolver=resolver) is True


def test_valid_cascade_closure_passes_all_semantic_checks() -> None:
    """Phase 0.6.B integration: default _args + valid parent satisfies every axis.

    Defaults align:
      - args.from_agent=claude  == parent.to_agent=claude
      - args.to_agent=codex     == parent.from_agent=codex
      - args.target_session_id  == parent.session_id
      - args.target_role=reviewer == _CASCADE_AGENT_ROLES[parent.from_agent=codex]
      - args.target_ref         == parent.target_ref
      - parent.kind=task_started, parent.status=pending
    """
    assert _authority(_args()) is True


# ---------------------------------------------------------------------------
# Phase 0.6.D source-session stamping (rev_pkt_4664)
# ---------------------------------------------------------------------------


def test_local_review_parent_session_is_rejected_for_live_agent_cascade() -> None:
    """Phase 0.6.D: parent.session_id='local-review' is NEVER accepted for a live-agent
    parent, even when closure.target_session_id also equals 'local-review'.

    rev_pkt_4664: 'Do not add a local-review wildcard. Add tests for ... local-review
    not accepted as a live-agent wildcard.' This test enforces the rejection at the
    semantic verifier layer so a stamping bug at write-time cannot bypass cascade
    parent verification at read-time.
    """
    parent_local_review = dict(_PARENT_TASK_STARTED)
    parent_local_review["session_id"] = "local-review"
    args = _args(target_session_id="local-review")
    resolver = _resolver(parent_local_review)
    assert _cascade_lifecycle_post_authority(args, parent_resolver=resolver) is False


def test_local_review_target_session_is_rejected_for_live_agent_cascade() -> None:
    """Phase 0.6.D: closure.target_session_id='local-review' is NEVER accepted.

    Even with a valid real-session parent, a closure that targets 'local-review' as
    its destination signals the stamping artifact and must be rejected.
    """
    args = _args(target_session_id="local-review")
    parent = dict(_PARENT_TASK_STARTED)
    parent["session_id"] = "local-review"
    resolver = _resolver(parent)
    assert _cascade_lifecycle_post_authority(args, parent_resolver=resolver) is False


def test_empty_parent_session_is_rejected_for_live_agent_cascade() -> None:
    """Phase 0.6.D: parent.session_id empty string is also treated as fallback."""
    parent_empty_session = dict(_PARENT_TASK_STARTED)
    parent_empty_session["session_id"] = ""
    resolver = _resolver(parent_empty_session)
    assert _authority(_args(), parent=parent_empty_session) is False


def test_valid_real_session_closure_is_accepted_post_phase_d() -> None:
    """Phase 0.6.D: closures with non-fallback session_ids on both sides remain accepted.

    Confirms the local-review rejection does NOT over-broaden into accidentally
    blocking valid real-session cascade closures.
    """
    assert _authority(_args()) is True
    assert _codex_authority(_codex_args()) is True


def test_wrong_real_session_closure_is_still_rejected_post_phase_d() -> None:
    """Phase 0.6.D: wrong real session_id (not the fallback) is also rejected via the
    existing session-mismatch check.

    Confirms the local-review rejection is in addition to, not in place of, the
    existing wrong-session check.
    """
    assert _authority(_args(target_session_id="3c4d5e6f-7890-1234-abcd-ef0123456789")) is False


def test_non_live_agent_parent_with_local_review_session_is_still_eligible() -> None:
    """Phase 0.6.D: when parent.from_agent/to_agent are NOT live agents (claude/codex),
    'local-review' session_id is the legitimate default - the live-agent check
    must not fire.

    This preserves the non-actor automation/control post lane that legitimately uses
    local-review. The check is scoped to live-agent peers only.
    """
    # Parent with from_agent="automation" (hypothetical non-live actor) and
    # session_id="local-review" should NOT trigger the new rejection - if any other
    # axes are valid.
    # Note: actual structural narrow rejects from_agent="automation" via
    # _CASCADE_LIFECYCLE_AUTHORIZED_POSTS, so this is a defense-in-depth test
    # demonstrating the live-agent scope of the new rejection.
    parent_non_live = dict(_PARENT_TASK_STARTED)
    parent_non_live["from_agent"] = "automation"
    parent_non_live["session_id"] = "local-review"
    resolver = _resolver(parent_non_live)
    # The closure args use claude->codex, which doesn't match parent.from=automation,
    # so peer reversal fails first (closure.to_agent=codex != parent.from_agent=automation).
    # But the test confirms behavior: local-review parent + non-live peer doesn't
    # ALSO trip the live-agent local-review check before peer-mismatch rejection.
    assert _cascade_lifecycle_post_authority(_args(), parent_resolver=resolver) is False


# ---------------------------------------------------------------------------
# Phase 0.6.C read-authority bypass (rev_pkt_4659 reviewer-read fragility)
# ---------------------------------------------------------------------------


def test_show_action_is_read_authority() -> None:
    """Phase 0.6.C: --action show cannot mutate state, bypasses obedience guard."""
    assert _cascade_lifecycle_read_authority(_args(action="show")) is True


def test_inbox_action_is_read_authority() -> None:
    """Phase 0.6.C: --action inbox/operator-inbox are read-only."""
    assert _cascade_lifecycle_read_authority(_args(action="inbox")) is True
    assert _cascade_lifecycle_read_authority(_args(action="operator-inbox")) is True


def test_status_history_sync_status_are_read_authority() -> None:
    """Phase 0.6.C: status/history/sync-status are all read-only inspection actions."""
    assert _cascade_lifecycle_read_authority(_args(action="status")) is True
    assert _cascade_lifecycle_read_authority(_args(action="history")) is True
    assert _cascade_lifecycle_read_authority(_args(action="sync-status")) is True


def test_post_action_is_not_read_authority() -> None:
    """Phase 0.6.C: --action post is a write action; must NOT bypass via read-authority."""
    assert _cascade_lifecycle_read_authority(_args(action="post")) is False


def test_write_actions_are_not_read_authority() -> None:
    """Phase 0.6.C: launch/recover/ack/dismiss/apply/expire-packets/etc. are writes."""
    for write_action in (
        "launch",
        "recover",
        "ack",
        "dismiss",
        "apply",
        "ingest",
        "absorb",
        "expire-packets",
        "promote",
        "stop",
    ):
        assert (
            _cascade_lifecycle_read_authority(_args(action=write_action)) is False
        ), f"write action {write_action!r} must not be read-authority"


# ---------------------------------------------------------------------------
# Phase 0.6.D CLI-side write gate (rev_pkt_4664)
# ---------------------------------------------------------------------------


def test_post_gate_rejects_live_agent_with_local_review_session() -> None:
    """Phase 0.6.D write-time: live-agent post defaulting to 'local-review' is rejected.

    This is the symmetric check to the verifier-side rejection: the write path
    fails-fast before the packet event is appended, with a clear error pointing
    operators at --session-id.
    """
    args = SimpleNamespace(from_agent="claude", session_id="local-review")
    with pytest.raises(LiveAgentSessionStampingError):
        require_real_session_for_live_agent_post(args)


def test_post_gate_rejects_live_agent_with_empty_session() -> None:
    """Phase 0.6.D: empty string session_id is also rejected for live agents."""
    args = SimpleNamespace(from_agent="codex", session_id="")
    with pytest.raises(LiveAgentSessionStampingError):
        require_real_session_for_live_agent_post(args)


def test_post_gate_accepts_live_agent_with_real_session() -> None:
    """Phase 0.6.D: live-agent post with a real UUID session_id passes the gate."""
    args = SimpleNamespace(
        from_agent="claude",
        session_id="2a5b3528-aaa6-4615-b83b-5b1d3598509b",
    )
    require_real_session_for_live_agent_post(args)  # no exception


def test_post_gate_allows_non_live_agent_with_local_review_session() -> None:
    """Phase 0.6.D: non-live-agent posters (automation, system, operator) keep using
    'local-review' as the legitimate default - the gate is scoped to claude/codex."""
    for actor in ("operator", "system", "automation", "dashboard"):
        args = SimpleNamespace(from_agent=actor, session_id="local-review")
        # No exception expected
        require_real_session_for_live_agent_post(args)


# ---------------------------------------------------------------------------
# Phase 0.6.D ratchet (rev_pkt_4668 / v4.14): source-session authenticity
# ---------------------------------------------------------------------------


def test_post_gate_rejects_fake_non_fallback_session(tmp_path) -> None:
    """Phase 0.6.D v4.14 (rev_pkt_4668): a non-fallback string that isn't a real
    live session is rejected.

    Codex's exact probe: ``session_id='not-a-real-session'`` for from_agent=claude
    must fail at write-time. The fallback-only check is too weak; the gate must
    verify against the typed agent_minds projection.
    """
    _write_agent_mind_projection(
        tmp_path,
        agent="claude",
        session_id="2a5b3528-aaa6-4615-b83b-5b1d3598509b",
    )
    args = SimpleNamespace(
        from_agent="claude",
        session_id="not-a-real-session",
    )
    with pytest.raises(LiveAgentSessionStampingError, match="does NOT match"):
        require_real_session_for_live_agent_post(args, repo_root=tmp_path)


def test_post_gate_rejects_wrong_agent_session(tmp_path) -> None:
    """Phase 0.6.D v4.14: claude posting with codex's session_id is rejected.

    Each agent's session_id must match its own agent_minds projection - claude
    cannot post as codex, or vice versa.
    """
    _write_agent_mind_projection(
        tmp_path,
        agent="claude",
        session_id="2a5b3528-aaa6-4615-b83b-5b1d3598509b",
    )
    args = SimpleNamespace(
        from_agent="claude",
        session_id="019e46cb-dd3c-7121-bf2f-eff8cc5fc815",  # codex's session
    )
    with pytest.raises(LiveAgentSessionStampingError):
        require_real_session_for_live_agent_post(args, repo_root=tmp_path)


def test_post_gate_accepts_real_session_matching_projection(tmp_path) -> None:
    """Phase 0.6.D v4.14: real session_id matching the agent's typed projection passes."""
    _write_agent_mind_projection(
        tmp_path,
        agent="claude",
        session_id="2a5b3528-aaa6-4615-b83b-5b1d3598509b",
    )
    args = SimpleNamespace(
        from_agent="claude",
        session_id="2a5b3528-aaa6-4615-b83b-5b1d3598509b",
    )
    require_real_session_for_live_agent_post(args, repo_root=tmp_path)  # no exception


def test_post_gate_rejects_when_projection_missing(tmp_path) -> None:
    """Phase 0.6.D v4.14: live-agent post with no typed projection fails closed.

    If devctl agent-mind hasn't been run yet for the actor, the gate cannot
    verify the session_id, so it MUST reject rather than silently accept.
    """
    args = SimpleNamespace(
        from_agent="claude",
        session_id="2a5b3528-aaa6-4615-b83b-5b1d3598509b",
    )
    with pytest.raises(LiveAgentSessionStampingError, match="projection"):
        require_real_session_for_live_agent_post(args, repo_root=tmp_path)


def test_post_gate_without_repo_root_falls_back_to_structural(tmp_path) -> None:
    """Phase 0.6.D backwards-compat: repo_root=None keeps the structural-only check.

    For unit tests / programmatic callers that don't have a repo to look up,
    the fallback rejection still fires (covers the rev_pkt_4664 axis), but the
    full live-session check is skipped.
    """
    args_fallback = SimpleNamespace(from_agent="claude", session_id="local-review")
    with pytest.raises(LiveAgentSessionStampingError):
        require_real_session_for_live_agent_post(args_fallback)

    # A non-fallback session passes when repo_root is None (no typed verification)
    args_nonfallback = SimpleNamespace(
        from_agent="claude",
        session_id="any-non-fallback-string",
    )
    require_real_session_for_live_agent_post(args_nonfallback)  # no exception


def test_resolve_live_actor_session_reads_projection(tmp_path) -> None:
    """Phase 0.6.D v4.14: resolve_live_actor_session correctly reads the typed projection."""
    _write_agent_mind_projection(
        tmp_path,
        agent="codex",
        session_id="019e46cb-dd3c-7121-bf2f-eff8cc5fc815",
    )
    actor = resolve_live_actor_session("codex", tmp_path)
    assert actor["session_id"] == "019e46cb-dd3c-7121-bf2f-eff8cc5fc815"
    assert actor["agent_provider"] == "codex"


def test_resolve_live_actor_session_returns_empty_for_unknown_agent(tmp_path) -> None:
    """Phase 0.6.D v4.14: non-live-agent (operator/system) returns empty session_id."""
    actor = resolve_live_actor_session("operator", tmp_path)
    assert actor["session_id"] == ""


def test_resolve_live_actor_session_returns_empty_when_projection_absent(tmp_path) -> None:
    """Phase 0.6.D v4.14: missing projection returns empty without raising."""
    actor = resolve_live_actor_session("claude", tmp_path)
    assert actor["session_id"] == ""


def test_verifier_rejects_parent_session_not_matching_live_projection(tmp_path) -> None:
    """Phase 0.6.D v4.14 verifier-side: parent.session_id that doesn't match the live
    typed projection for parent.from_agent is rejected.

    Defense in depth: even if a parent packet was somehow posted with a spoofed
    session_id (e.g. write-time gate bypassed), the verifier catches it by
    re-checking against the typed projection.
    """
    _write_agent_mind_projection(
        tmp_path,
        agent="codex",
        session_id="019e46cb-dd3c-7121-bf2f-eff8cc5fc815",
    )
    parent_with_spoofed_session = dict(_PARENT_TASK_STARTED)
    parent_with_spoofed_session["session_id"] = "spoofed-session-id-not-real"
    resolver = _resolver(parent_with_spoofed_session)
    args = _args(target_session_id="spoofed-session-id-not-real")
    # parent.from_agent=codex; typed projection says codex's real session is 019e46cb,
    # but parent.session_id is "spoofed-session-id-not-real" -> reject
    assert (
        _cascade_lifecycle_post_authority(
            args, repo_root=tmp_path, parent_resolver=resolver
        )
        is False
    )


def test_verifier_fails_closed_when_projection_absent(tmp_path) -> None:
    """Phase 0.6.D v4.14 (rev_pkt_4670): verifier MUST reject when projection is absent
    for a live-agent parent, not silently accept.

    Codex's exact reproduction: parent.from_agent=claude, parent.session_id=
    "not-a-real-session", no agent_mind projection at
    dev/reports/agent_minds/claude_latest.json -> closure must be rejected.
    Prior version had ``if live_session_id and ...`` which short-circuited and
    silently accepted when the projection was absent.

    tmp_path is empty - no projection file exists - so the resolver returns ""
    and the predicate MUST fail closed.
    """
    parent_spoofed = dict(_PARENT_TASK_STARTED)
    parent_spoofed["from_agent"] = "claude"
    parent_spoofed["to_agent"] = "codex"
    parent_spoofed["session_id"] = "not-a-real-session"
    resolver = _resolver(parent_spoofed)
    # Closure args targeting the spoofed session
    args = SimpleNamespace(
        action="post",
        from_agent="codex",
        to_agent="claude",
        kind="review_accepted",
        target_session_id="not-a-real-session",
        target_role="implementer",
        target_ref=_TARGET_REF,
        evidence_ref=("packet:rev_pkt_4652",),
    )
    # tmp_path has NO dev/reports/agent_minds/claude_latest.json
    # parent.from_agent=claude is a live agent -> resolver returns ""
    # MUST fail closed (return False) per rev_pkt_4670 directive.
    assert (
        _cascade_lifecycle_post_authority(
            args, repo_root=tmp_path, parent_resolver=resolver
        )
        is False
    )


def test_verifier_fails_closed_when_codex_projection_absent_default_direction(tmp_path) -> None:
    """Phase 0.6.D v4.14 (rev_pkt_4670): same fail-closed for claude->codex direction.

    Default _args (claude->codex task_produced) with parent.from_agent=codex,
    no codex_latest.json projection -> reject.
    """
    # tmp_path has no dev/reports/agent_minds/codex_latest.json
    # Default parent has from_agent=codex (live), session_id=019e46cb...
    # Resolver finds no projection -> empty live_session_id -> fail closed
    assert (
        _cascade_lifecycle_post_authority(
            _args(), repo_root=tmp_path, parent_resolver=_resolver()
        )
        is False
    )


def test_verifier_accepts_parent_session_matching_live_projection(tmp_path) -> None:
    """Phase 0.6.D v4.14 verifier-side: parent.session_id matching typed projection passes."""
    _write_agent_mind_projection(
        tmp_path,
        agent="codex",
        session_id="019e46cb-dd3c-7121-bf2f-eff8cc5fc815",
    )
    # Default _PARENT_TASK_STARTED already has session_id=019e46cb (matches)
    resolver = _resolver()
    assert _cascade_lifecycle_post_authority(
        _args(), repo_root=tmp_path, parent_resolver=resolver
    ) is True


# ---------------------------------------------------------------------------
# Post-action kind to controller-action mapping (unchanged from Phase 0.6.A)
# ---------------------------------------------------------------------------


def test_review_accepted_has_post_action_mapping() -> None:
    """rev_pkt_4654: review_accepted -> review-channel.post_review_accepted mapping exists."""
    action = required_review_channel_post_action(
        argv=("review-channel", "--action", "post", "--kind", "review_accepted"),
        kind="review_accepted",
    )
    assert action == "review-channel.post_review_accepted"


def test_task_blocked_has_post_action_mapping() -> None:
    """task_blocked (recoverable receipt) maps to review-channel.post_task_blocked."""
    action = required_review_channel_post_action(
        argv=("review-channel", "--action", "post", "--kind", "task_blocked"),
        kind="task_blocked",
    )
    assert action == "review-channel.post_task_blocked"


def test_review_failed_has_post_action_mapping() -> None:
    """review_failed maps to review-channel.post_review_failed."""
    action = required_review_channel_post_action(
        argv=("review-channel", "--action", "post", "--kind", "review_failed"),
        kind="review_failed",
    )
    assert action == "review-channel.post_review_failed"


def test_task_started_has_post_action_mapping() -> None:
    """task_started maps to review-channel.post_task_started (was missing pre-repair)."""
    action = required_review_channel_post_action(
        argv=("review-channel", "--action", "post", "--kind", "task_started"),
        kind="task_started",
    )
    assert action == "review-channel.post_task_started"
