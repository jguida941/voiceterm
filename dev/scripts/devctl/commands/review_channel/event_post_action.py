"""Post action for the event-backed review-channel command path."""

from __future__ import annotations

import subprocess
from pathlib import Path

from ...runtime.collaboration_packet_kinds import TASK_PRODUCED_PACKET_KIND
from ...review_channel.context_refs import resolve_context_pack_refs
from ...review_channel.events import post_packet
from ...review_channel.packet_contract import (
    PacketAttentionFields,
    PacketGuardBundleEvidenceFields,
    PacketPostRequest,
    PacketRuntimeApprovalFields,
    PacketTargetFields,
    post_kind_requires_typed_evidence,
)
from .event_action_support import EventActionContext
from .event_packet_lookup import packet_by_id


def load_post_body(args) -> str:
    """Read the packet body from --body or --body-file."""
    body = getattr(args, "body", None)
    body_file = getattr(args, "body_file", None)
    if body:
        return str(body)
    assert body_file is not None
    return Path(body_file).read_text(encoding="utf-8")


def run_post_action(
    *,
    context: EventActionContext,
) -> tuple[dict, int, dict[str, object]]:
    """Append one event-backed review packet."""
    bundle, event = post_packet(
        repo_root=context.repo_root,
        review_channel_path=context.review_channel_path,
        artifact_paths=context.artifact_paths,
        request=_post_request(context),
    )
    packet = packet_by_id(bundle.review_state, event.get("packet_id"))
    report, exit_code = context.build_event_report_fn(
        args=context.args,
        bundle=bundle,
        packet=packet,
        event=event,
    )
    return report, exit_code, bundle.review_state


def _post_request(context: EventActionContext) -> PacketPostRequest:
    args = context.args
    evidence_refs = _post_evidence_refs(args)
    _require_typed_evidence_for_post(args, evidence_refs)
    _require_commit_or_clean_worktree_for_publish(
        context.repo_root,
        args,
        evidence_refs,
    )
    return PacketPostRequest(
        from_agent=args.from_agent,
        to_agent=args.to_agent,
        kind=args.kind,
        summary=args.summary,
        body=load_post_body(args),
        evidence_refs=evidence_refs,
        context_pack_refs=tuple(resolve_context_pack_refs(args, context.repo_root)),
        confidence=float(args.confidence),
        requested_action=args.requested_action,
        policy_hint=args.policy_hint,
        approval_required=bool(args.approval_required),
        packet_id=getattr(args, "packet_id", None),
        trace_id=getattr(args, "trace_id", None),
        session_id=args.session_id,
        plan_id=args.plan_id,
        controller_run_id=getattr(args, "controller_run_id", None),
        correlation_id=getattr(args, "correlation_id", "") or "",
        causation_id=getattr(args, "causation_id", "") or "",
        run_id=getattr(args, "run_id", "") or "",
        expires_in_minutes=getattr(args, "expires_in_minutes", None),
        target=_target_fields(args),
        runtime_approval=_runtime_approval_fields(args),
        guard_bundle_evidence=_guard_bundle_evidence_fields(args),
        attention=PacketAttentionFields.from_values(
            attention_urgency=getattr(args, "attention_urgency", None),
            attention_class=getattr(args, "attention_class", None),
        ),
    )


def _post_evidence_refs(args) -> tuple[str, ...]:
    refs = [
        ref
        for ref in (
            _clean_evidence_ref(value)
            for value in getattr(args, "evidence_ref", []) or []
        )
        if ref
    ]
    refs.extend(
        f"artifact:{ref}"
        for ref in (
            _clean_evidence_ref(value)
            for value in getattr(args, "evidence_artifact_path", []) or []
        )
        if ref
    )
    refs.extend(
        f"action_result:{ref}"
        for ref in (
            _clean_evidence_ref(value)
            for value in getattr(args, "action_result_id", []) or []
        )
        if ref
    )
    commit_sha = _clean_evidence_ref(getattr(args, "commit_sha", None))
    if commit_sha:
        refs.append(f"commit:{commit_sha}")
    plan_revision_before = _clean_evidence_ref(
        getattr(args, "plan_revision_before", None)
    )
    plan_revision_after = _clean_evidence_ref(
        getattr(args, "plan_revision_after", None)
    )
    if plan_revision_before and plan_revision_after:
        refs.append(f"plan_revision:{plan_revision_before}->{plan_revision_after}")
    return tuple(dict.fromkeys(refs))


def _clean_evidence_ref(value: object) -> str:
    return str(value or "").strip()


def _require_typed_evidence_for_post(
    args,
    evidence_refs: tuple[str, ...],
) -> None:
    kind = str(getattr(args, "kind", "") or "").strip()
    if not post_kind_requires_typed_evidence(kind) or evidence_refs:
        return
    raise ValueError(
        "review-channel post --kind "
        f"{kind} requires typed evidence: pass --evidence-ref, "
        "--evidence-artifact-path, --action-result-id, --commit-sha, or both "
        "--plan-revision-before and --plan-revision-after."
    )


def _require_commit_or_clean_worktree_for_publish(
    repo_root: Path,
    args,
    evidence_refs: tuple[str, ...],
) -> None:
    kind = str(getattr(args, "kind", "") or "").strip()
    from_agent = str(getattr(args, "from_agent", "") or "").strip().lower()
    if kind != TASK_PRODUCED_PACKET_KIND or from_agent != "codex":
        return
    if any(ref.startswith("commit:") for ref in evidence_refs):
        return
    if _worktree_clean(repo_root):
        return
    raise ValueError(
        "review-channel post --kind task_produced from codex requires commit "
        "evidence or a clean worktree: pass --commit-sha after the governed "
        "commit path, or keep working instead of publishing closure."
    )


def _worktree_clean(repo_root: Path) -> bool:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "status", "--porcelain"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0 and not result.stdout.strip()


def _target_fields(args) -> PacketTargetFields:
    return PacketTargetFields.from_values(
        target_kind=getattr(args, "target_kind", None),
        target_ref=getattr(args, "target_ref", None),
        target_revision=getattr(args, "target_revision", None),
        anchor_refs=getattr(args, "anchor_ref", []),
        intake_ref=getattr(args, "intake_ref", None),
        mutation_op=getattr(args, "mutation_op", None),
        target_role=getattr(args, "target_role", None),
        target_session_id=getattr(args, "target_session_id", None),
        anchor_scope=getattr(args, "anchor_scope", None),
        requested_session_visibility=getattr(
            args,
            "requested_session_visibility",
            None,
        ),
    )


def _runtime_approval_fields(args) -> PacketRuntimeApprovalFields:
    return PacketRuntimeApprovalFields.from_values(
        pipeline_generation=getattr(args, "pipeline_generation", None),
        staged_snapshot_hash=getattr(args, "staged_snapshot_hash", None),
        guard_results_summary=getattr(args, "guard_results_summary", None),
    )


def _guard_bundle_evidence_fields(args) -> PacketGuardBundleEvidenceFields:
    return PacketGuardBundleEvidenceFields.from_values(
        full_guard_bundle_evidence=getattr(
            args,
            "full_guard_bundle_evidence",
            None,
        ),
    )
