"""Raw git wrapper that emits typed RawGitBypassReceipt evidence."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

from ..common import (
    add_standard_output_arguments,
    display_path,
    emit_output,
    resolve_repo_path,
    write_output,
)
from ..config import REPO_ROOT
from ..runtime.raw_git_bypass_receipts import (
    DEFAULT_BYPASS_LIFECYCLE_STORE_REL,
    DEFAULT_RAW_GIT_BYPASS_RECEIPT_STORE_REL,
    RawGitBypassAuthority,
    RawGitVerb,
    append_raw_git_bypass_receipt,
    build_raw_git_bypass_receipt,
)
from .vcs.raw_git_execution import raw_git_authority_preflight, subprocess_git_runner
from ..runtime.feature_proof_receipt import (
    FeatureProofReceipt,
    FeatureProofReceiptEmissionFailure,
    feature_proof_receipt_artifact_relpath,
    feature_proof_receipt_from_mapping,
    write_validated_feature_proof_receipt_artifact as write_feature_proof_receipt_artifact,
)
from ..runtime.commit_to_plan_row_reducer import (
    CommitToPlanRowReductionResult,
    PlanRowClosureReceipt,
    reduce_feature_proof_to_plan_rows,
)
from ..runtime.master_plan_contract import DEFAULT_MASTER_PLAN_STORE_REL
from ..runtime.master_plan_store import read_plan_rows_jsonl
from ..runtime.control_decision_obedience import (
    build_attempted_action_receipt,
    evaluate_control_decision_obedience,
)
from ..runtime.control_decision_artifacts import load_control_decision_payload

DEFAULT_OPERATOR_EVIDENCE_REF = "packet:rev_pkt_4022"
GitRunner = Callable[[tuple[str, ...], bool], "GitCommandResult"]
REAL_LIFE_TEST_STATUS_CHOICES = (
    "proven_passed",
    "proven_failed",
    "not_tested_with_rationale",
)
BLOCKING_PLAN_ROW_CLOSURE_OUTCOMES = frozenset(
    {
        "plan_index_missing",
        "plan_row_missing",
        "role_review_receipt_required",
        "status_not_transitionable",
    }
)
_PLAN_ROW_CANDIDATE_RE = re.compile(
    r"\b(?:MP-NEW|MP\d*|PKT-BIND)[A-Z0-9_.:-]*(?:-[A-Z0-9_.:-]+)*\b"
)


@dataclass(frozen=True, slots=True)
class GitCommandResult:
    returncode: int
    stdout: str = ""
    stderr: str = ""


def add_parser(sub) -> None:
    parser = sub.add_parser(
        "raw-git",
        help="Run raw git commit/push while emitting typed bypass receipts",
    )
    parser.add_argument(
        "--store-path",
        default=str(DEFAULT_RAW_GIT_BYPASS_RECEIPT_STORE_REL),
        help="RawGitBypassReceipt JSONL store path.",
    )
    parser.add_argument(
        "--bypass-lifecycle-store-path",
        default=str(DEFAULT_BYPASS_LIFECYCLE_STORE_REL),
        help="BypassLifecycle JSONL store used to validate lifecycle-backed authority.",
    )
    parser.add_argument(
        "--governed-exception-store-path",
        default="dev/state/governed_exception_lifecycles.jsonl",
        help="GovernedExceptionLifecycle JSONL store receiving raw-git exception links.",
    )
    parser.add_argument(
        "--actor",
        default="codex",
        help="Actor executing the raw git operation.",
    )
    parser.add_argument(
        "--role",
        default="",
        help="Actor role used to resolve the live AgentLoopDecision.",
    )
    parser.add_argument(
        "--session-id",
        default="",
        help="Actor session id used to resolve the live AgentLoopDecision.",
    )
    parser.add_argument(
        "--authority",
        choices=tuple(authority.value for authority in RawGitBypassAuthority),
        default=RawGitBypassAuthority.OPERATOR_WITNESSED.value,
        help="Typed authority source for this raw git bypass receipt.",
    )
    parser.add_argument(
        "--bypass-lifecycle-id",
        default="",
        help="Optional BypassLifecycle id when authority is lifecycle-backed.",
    )
    parser.add_argument(
        "--operator-quote-evidence-ref",
        action="append",
        default=None,
        help="Repeatable operator evidence ref; last value is stored on the receipt.",
    )
    parser.add_argument(
        "--feature-id",
        default="",
        help="Feature/plan row id for the FeatureProofReceipt. Defaults to the first MP-style token in the commit body.",
    )
    parser.add_argument(
        "--test-command",
        action="append",
        default=None,
        help="Repeatable validation command to record in the FeatureProofReceipt.",
    )
    parser.add_argument(
        "--tests-passed-count",
        type=int,
        default=None,
        help="Number of passing validation commands recorded in the FeatureProofReceipt.",
    )
    parser.add_argument(
        "--tests-failed-count",
        type=int,
        default=None,
        help="Number of failing validation commands recorded in the FeatureProofReceipt.",
    )
    parser.add_argument(
        "--connectivity-guard",
        action="append",
        default=None,
        help="Repeatable connectivity guard recorded in the FeatureProofReceipt.",
    )
    parser.add_argument(
        "--connectivity-guards-passed",
        choices=("true", "false"),
        default="true",
        help="Whether the recorded connectivity guards passed.",
    )
    parser.add_argument(
        "--dogfood-evidence-ref",
        default="",
        help="Evidence ref for live dogfood invocation recorded in the FeatureProofReceipt.",
    )
    parser.add_argument(
        "--review-fleet-role",
        action="append",
        default=None,
        help="Repeatable review fleet role recorded in the FeatureProofReceipt.",
    )
    parser.add_argument(
        "--review-fleet-actor",
        default="raw-git-wrapper",
        help="Review fleet actor recorded in the FeatureProofReceipt.",
    )
    parser.add_argument(
        "--real-life-test-status",
        choices=REAL_LIFE_TEST_STATUS_CHOICES,
        default="",
        help="Real-life test status recorded in the FeatureProofReceipt.",
    )
    parser.add_argument(
        "--not-tested-rationale",
        default="",
        help="Required rationale when --real-life-test-status is not_tested_with_rationale.",
    )
    parser.add_argument(
        "--evidence-artifact",
        action="append",
        default=None,
        help="Repeatable evidence artifact path recorded in the FeatureProofReceipt.",
    )
    parser.add_argument(
        "--control-decision-input",
        default="",
        help="AgentLoopDecision/control decision JSON path enforced before raw git executes.",
    )
    add_standard_output_arguments(
        parser,
        format_choices=("json", "md"),
        default_format="json",
    )
    actions = parser.add_subparsers(dest="raw_git_action", required=True)
    commit = actions.add_parser(
        "commit",
        help="Run `git commit ...` and append a RawGitBypassReceipt.",
    )
    commit.add_argument("git_args", nargs=argparse.REMAINDER)
    push = actions.add_parser(
        "push",
        help="Run `git push ...` and append a RawGitBypassReceipt.",
    )
    push.add_argument("git_args", nargs=argparse.REMAINDER)


def run(args: Any) -> int:
    report, rc = run_raw_git_action(args)
    output = json.dumps(report, indent=2, sort_keys=True)
    if getattr(args, "format", "json") != "json":
        output = _render_markdown(report)
    emit_output(
        output,
        output_path=getattr(args, "output", None),
        pipe_command=getattr(args, "pipe_command", None),
        pipe_args=getattr(args, "pipe_args", None),
        writer=write_output,
    )
    return rc


def run_raw_git_action(
    args: Any,
    *,
    repo_root: Path = REPO_ROOT,
    git_runner: GitRunner | None = None,
) -> tuple[dict[str, object], int]:
    action = str(getattr(args, "raw_git_action", "") or "").strip()
    if action not in {RawGitVerb.COMMIT.value, RawGitVerb.PUSH.value}:
        return _error_report("unknown_raw_git_action", action), 1
    git_args = _normalized_git_args(getattr(args, "git_args", ()) or ())
    verb = RawGitVerb(action)
    if _is_git_help_request(git_args):
        return _git_noop_report(verb, git_args, "git_help_noop"), 0
    obedience_report = _raw_git_control_decision_obedience_report(
        args,
        verb=verb,
        git_args=git_args,
        repo_root=repo_root,
    )
    if obedience_report and not bool(obedience_report.get("ok")):
        return (
            _error_report(
                "control_decision_obedience_failed",
                json.dumps(obedience_report, sort_keys=True),
            ),
            1,
        )
    if not obedience_report:
        return (
            _error_report(
                "control_decision_required",
                "raw-git requires a live AgentLoopDecision/control decision before git executes.",
            ),
            1,
        )
    preflight = raw_git_authority_preflight(args, repo_root=repo_root, verb=verb)
    if not preflight.ok:
        return _error_report("bypass_authority_invalid", preflight.error), 1
    runner = git_runner or subprocess_git_runner(
        repo_root,
        result_factory=GitCommandResult,
        extra_env=preflight.git_env,
    )

    before_head = _git_stdout(runner, ("rev-parse", "HEAD"))
    before_upstream = _git_stdout(runner, ("rev-parse", "--verify", "@{u}"))
    before_ahead = (
        _git_stdout(runner, ("rev-list", "--reverse", "@{u}..HEAD"))
        if verb is RawGitVerb.PUSH and before_upstream
        else ""
    )
    command_result = runner((verb.value, *git_args), False)
    if command_result.returncode != 0:
        return _git_failure_report(verb, git_args, command_result), command_result.returncode

    after_head = _git_stdout(runner, ("rev-parse", "HEAD"))
    raw_commit_sha = ""
    if verb is RawGitVerb.COMMIT:
        raw_commit_sha = _first_new_commit_sha(
            runner,
            before_head=before_head,
            after_head=after_head,
        )
    if verb is RawGitVerb.COMMIT and not raw_commit_sha:
        return (
            _git_noop_report(
                verb,
                git_args,
                "git_commit_head_unchanged",
                command_result,
            ),
            1,
        )

    commit_sha = raw_commit_sha if verb is RawGitVerb.COMMIT else after_head
    push_range: tuple[str, str] = ()
    if verb is RawGitVerb.PUSH:
        after_ahead = (
            _git_stdout(runner, ("rev-list", "--reverse", "@{u}..HEAD"))
            if before_upstream
            else ""
        )
        if not before_ahead or after_ahead == before_ahead:
            return (
                _git_noop_report(
                    verb,
                    git_args,
                    "git_push_upstream_unchanged",
                    command_result,
                ),
                1,
            )
        if before_upstream and before_head:
            push_range = (before_upstream, before_head)
    affected_paths = _affected_paths(runner, verb=verb, commit_sha=commit_sha, push_range=push_range)
    receipt = build_raw_git_bypass_receipt(
        git_verb=verb,
        executed_at_utc=_now_utc(),
        executed_by_actor=str(getattr(args, "actor", "") or "codex").strip(),
        bypass_authority=preflight.bypass_authority,
        commit_sha=commit_sha if verb is RawGitVerb.COMMIT else "",
        push_range=push_range,
        affected_paths=affected_paths,
        bypass_lifecycle_id=str(getattr(args, "bypass_lifecycle_id", "") or "").strip(),
        operator_quote_evidence_ref=_operator_evidence_ref(args),
        skipped_pre_hooks=_skipped_pre_hooks(verb, git_args),
        git_args=git_args,
    )
    store_path = resolve_repo_path(
        getattr(args, "store_path", ""),
        DEFAULT_RAW_GIT_BYPASS_RECEIPT_STORE_REL,
        repo_root=repo_root,
    )
    governed_exception_store_path = resolve_repo_path(
        getattr(args, "governed_exception_store_path", ""),
        Path("dev/state/governed_exception_lifecycles.jsonl"),
        repo_root=repo_root,
    )
    write_result = append_raw_git_bypass_receipt(
        store_path,
        receipt,
        bypass_lifecycle_store_path=preflight.bypass_lifecycle_store_path,
        governed_exception_store_path=governed_exception_store_path,
    )
    receipt = write_result.receipt
    try:
        proof_paths, proof_warnings = _record_feature_proof_receipts(
            args,
            runner=runner,
            repo_root=repo_root,
            receipt=receipt,
            store_path=store_path,
            governed_exception_store_path=governed_exception_store_path,
            before_ahead=before_ahead,
        )
    except FeatureProofReceiptEmissionFailure as exc:
        return (
            _feature_proof_failure_report(
                verb=verb,
                receipt=receipt,
                write_result=write_result,
                store_path=store_path,
                command_result=command_result,
                error=str(exc),
            ),
            1,
        )
    report = {
        "command": "raw-git",
        "action": verb.value,
        "ok": True,
        "receipt_id": receipt.receipt_id,
        "store_path": display_path(store_path),
        "feature_proof_receipt_paths": list(proof_paths),
        "feature_proof_receipt_warnings": list(proof_warnings),
        "receipt": receipt.to_dict(),
        "write_result": write_result.to_dict(),
        "git_returncode": command_result.returncode,
        "git_stdout": command_result.stdout,
        "git_stderr": command_result.stderr,
    }
    return report, 0


def _git_stdout(runner: GitRunner, args: tuple[str, ...]) -> str:
    result = runner(args, True)
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def _affected_paths(
    runner: GitRunner,
    *,
    verb: RawGitVerb,
    commit_sha: str,
    push_range: tuple[str, str],
) -> tuple[str, ...]:
    if verb is RawGitVerb.COMMIT and commit_sha:
        output = _git_stdout(
            runner,
            ("diff-tree", "--no-commit-id", "--name-only", "-r", commit_sha),
        )
    elif verb is RawGitVerb.PUSH and push_range:
        output = _git_stdout(runner, ("diff", "--name-only", f"{push_range[0]}..{push_range[1]}"))
    else:
        output = ""
    return tuple(line.strip() for line in output.splitlines() if line.strip())


def _raw_git_control_decision_obedience_report(
    args: Any,
    *,
    verb: RawGitVerb,
    git_args: tuple[str, ...],
    repo_root: Path,
) -> dict[str, object]:
    decision = _control_decision_payload(args, repo_root=repo_root)
    if not isinstance(decision, dict) or not decision:
        if _allow_missing_control_decision(args):
            return {
                "ok": True,
                "command": "raw-git.control_decision_obedience",
                "contract_id": "ControlDecisionObeyedGuard",
                "diagnostic_bypass": "allow_missing_control_decision",
            }
        return {}
    report = evaluate_control_decision_obedience(
        decision=decision,
        attempted_actions=(
            build_attempted_action_receipt(
                action_kind=f"raw-git.{verb.value}",
                command=" ".join(
                    (
                        "python3",
                        "dev/scripts/devctl.py",
                        "raw-git",
                        verb.value,
                        *git_args,
                    )
                ),
                argv=("raw-git", verb.value, *git_args),
                actor=str(getattr(args, "actor", "") or ""),
                role=str(getattr(args, "role", "") or ""),
                session_id=str(getattr(args, "session_id", "") or ""),
                mutates=True,
                writes_state=True,
                executes_command=True,
                source_decision_id=str(decision.get("receipt_id") or ""),
                source_snapshot_id=str(decision.get("source_snapshot_id") or ""),
                started_at_utc=_now_utc(),
            ).to_dict(),
        ),
    ).to_dict()
    report["command"] = "raw-git.control_decision_obedience"
    return report


def _allow_missing_control_decision(args: Any) -> bool:
    return bool(getattr(args, "allow_missing_control_decision_for_test", False))


def _control_decision_payload(args: Any, *, repo_root: Path) -> dict[str, object]:
    return load_control_decision_payload(args, repo_root=repo_root)


def _record_feature_proof_receipts(
    args: Any,
    *,
    runner: GitRunner,
    repo_root: Path,
    receipt: object,
    store_path: Path,
    governed_exception_store_path: Path,
    before_ahead: str,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    paths: list[str] = []
    warnings: list[str] = []
    try:
        if not isinstance(receipt, object):
            return (), ()
        if getattr(receipt, "git_verb", None) is RawGitVerb.COMMIT:
            relpath, closure_warnings = _write_raw_git_feature_proof_receipt(
                args,
                runner=runner,
                repo_root=repo_root,
                receipt=receipt,
                store_path=store_path,
                governed_exception_store_path=governed_exception_store_path,
                commit_sha=receipt.commit_sha,
            )
            if relpath:
                paths.append(relpath)
            warnings.extend(closure_warnings)
        elif getattr(receipt, "git_verb", None) is RawGitVerb.PUSH:
            for commit_sha in _commit_lines(before_ahead):
                relpath, closure_warnings = _upsert_pushed_feature_proof_receipt(
                    args,
                    runner=runner,
                    repo_root=repo_root,
                    receipt=receipt,
                    store_path=store_path,
                    governed_exception_store_path=governed_exception_store_path,
                    commit_sha=commit_sha,
                )
                if relpath:
                    paths.append(relpath)
                warnings.extend(closure_warnings)
    except FeatureProofReceiptEmissionFailure:
        raise
    except Exception as exc:
        raise FeatureProofReceiptEmissionFailure(
            f"feature_proof_receipt_write_failed:{exc}"
        ) from exc
    return tuple(paths), tuple(warnings)


def _write_raw_git_feature_proof_receipt(
    args: Any,
    *,
    runner: GitRunner,
    repo_root: Path,
    receipt: Any,
    store_path: Path,
    governed_exception_store_path: Path,
    commit_sha: str,
) -> tuple[str, tuple[str, ...]]:
    if not commit_sha:
        return "", ()
    feature_proof = _raw_git_feature_proof_receipt(
        args,
        runner=runner,
        repo_root=repo_root,
        receipt=receipt,
        store_path=store_path,
        governed_exception_store_path=governed_exception_store_path,
        commit_sha=commit_sha,
    )
    relpath = write_feature_proof_receipt_artifact(repo_root, feature_proof, require_real_tests=True)
    try:
        closure_feature_ids = _feature_ids_for_commit(
            args,
            repo_root=repo_root,
            runner=runner,
            commit_sha=commit_sha,
            primary_feature_id=feature_proof.feature_id,
        )
        closure_results = reduce_feature_proof_to_plan_rows(
            repo_root=repo_root,
            feature_proof=feature_proof,
            feature_ids=closure_feature_ids,
            feature_proof_receipt_path=relpath,
        ) if closure_feature_ids else ()
        _raise_on_plan_row_closure_failures(closure_results)
    except FeatureProofReceiptEmissionFailure as exc:
        if _is_plan_row_closure_failure(exc):
            _delete_feature_proof_receipt(repo_root / relpath)
        raise
    return relpath, _plan_row_closure_warnings(closure_results)


def _upsert_pushed_feature_proof_receipt(
    args: Any,
    *,
    runner: GitRunner,
    repo_root: Path,
    receipt: Any,
    store_path: Path,
    governed_exception_store_path: Path,
    commit_sha: str,
) -> tuple[str, tuple[str, ...]]:
    if not commit_sha:
        return "", ()
    relpath = feature_proof_receipt_artifact_relpath(commit_sha)
    path = repo_root / relpath
    if not path.exists():
        return _write_raw_git_feature_proof_receipt(
            args,
            runner=runner,
            repo_root=repo_root,
            receipt=receipt,
            store_path=store_path,
            governed_exception_store_path=governed_exception_store_path,
            commit_sha=commit_sha,
        )
    payload = json.loads(path.read_text(encoding="utf-8"))
    existing = feature_proof_receipt_from_mapping(payload)
    updated = replace(
        existing,
        bypass_audit_trail_refs=_unique_refs(
            (*existing.bypass_audit_trail_refs, *_raw_git_audit_refs(receipt))
        ),
        evidence_artifacts=_unique_refs(
            (
                *existing.evidence_artifacts,
                display_path(store_path),
                display_path(governed_exception_store_path),
            )
        ),
    )
    original_text = path.read_text(encoding="utf-8")
    relpath = write_feature_proof_receipt_artifact(repo_root, updated, receipt_path=path, require_real_tests=True)
    try:
        closure_feature_ids = _feature_ids_for_commit(
            args,
            repo_root=repo_root,
            runner=runner,
            commit_sha=commit_sha,
            primary_feature_id=updated.feature_id,
        )
        closure_results = reduce_feature_proof_to_plan_rows(
            repo_root=repo_root,
            feature_proof=updated,
            feature_ids=closure_feature_ids,
            feature_proof_receipt_path=relpath,
        ) if closure_feature_ids else ()
        _raise_on_plan_row_closure_failures(closure_results)
    except FeatureProofReceiptEmissionFailure as exc:
        if _is_plan_row_closure_failure(exc):
            path.write_text(original_text, encoding="utf-8")
        raise
    return relpath, _plan_row_closure_warnings(closure_results)


def _raise_on_plan_row_closure_failures(
    results: tuple[CommitToPlanRowReductionResult, ...],
) -> None:
    blocking = tuple(
        result
        for result in results
        if result.outcome in BLOCKING_PLAN_ROW_CLOSURE_OUTCOMES
    )
    if not blocking:
        return
    detail = ";".join(
        f"{result.plan_row_id}:{result.outcome}" for result in blocking
    )
    raise FeatureProofReceiptEmissionFailure(f"plan_row_closure_failed:{detail}")


def _is_plan_row_closure_failure(exc: FeatureProofReceiptEmissionFailure) -> bool:
    return str(exc).startswith("plan_row_closure_failed:")


def _delete_feature_proof_receipt(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def _plan_row_closure_warnings(
    results: tuple[CommitToPlanRowReductionResult, ...],
) -> tuple[str, ...]:
    contract_id = PlanRowClosureReceipt.contract_id
    warnings: list[str] = []
    for result in results:
        if result.warning:
            warnings.append(f"{contract_id}:{result.plan_row_id}:{result.warning}")
        elif not result.ok:
            warnings.append(f"{contract_id}:{result.plan_row_id}:{result.outcome}")
    return tuple(warnings)


def _raw_git_feature_proof_receipt(
    args: Any,
    *,
    runner: GitRunner,
    repo_root: Path,
    receipt: Any,
    store_path: Path,
    governed_exception_store_path: Path,
    commit_sha: str,
) -> FeatureProofReceipt:
    tests_run = _string_items(getattr(args, "test_command", ()) or ())
    failed_count = _optional_count(getattr(args, "tests_failed_count", None), 0)
    passed_count = _optional_count(
        getattr(args, "tests_passed_count", None),
        1 if tests_run and failed_count == 0 else 0,
    )
    status = str(getattr(args, "real_life_test_status", "") or "").strip()
    if not status:
        status = "proven_passed" if tests_run and failed_count == 0 else "not_tested_with_rationale"
    rationale = str(getattr(args, "not_tested_rationale", "") or "").strip()
    if status == "not_tested_with_rationale" and not rationale:
        rationale = (
            "Raw git wrapper emitted the required FeatureProofReceipt anchor; "
            "no validation commands were declared on this raw-git invocation."
        )
    evidence_artifacts = _unique_refs(
        (
            *tuple(_string_items(getattr(args, "evidence_artifact", ()) or ())),
            display_path(store_path),
            display_path(governed_exception_store_path),
        )
    )
    return FeatureProofReceipt(
        feature_id=_feature_id_for_commit(
            args,
            repo_root=repo_root,
            runner=runner,
            commit_sha=commit_sha,
        ),
        commit_sha=commit_sha,
        implementer_actor=str(getattr(args, "actor", "") or "codex").strip() or "codex",
        review_fleet_roles_ran=_string_items(
            getattr(args, "review_fleet_role", ()) or ()
        )
        or ("FeatureLifecycleProof",),
        review_fleet_actor=str(
            getattr(args, "review_fleet_actor", "") or "raw-git-wrapper"
        ).strip()
        or "raw-git-wrapper",
        tests_run=tests_run or ("raw_git_bypass_receipt",),
        tests_passed_count=passed_count,
        tests_failed_count=failed_count,
        connectivity_guards_ran=_string_items(
            getattr(args, "connectivity_guard", ()) or ()
        )
        or ("raw_git_bypass_receipt", "governed_exception_lifecycle"),
        connectivity_guards_passed=_bool_arg(
            getattr(args, "connectivity_guards_passed", "true")
        ),
        dogfood_invocation_evidence_ref=str(
            getattr(args, "dogfood_evidence_ref", "") or ""
        ).strip()
        or f"raw_git_bypass_receipt:{receipt.receipt_id}",
        real_life_test_status=status,
        not_tested_rationale=rationale if status == "not_tested_with_rationale" else None,
        bypass_audit_trail_refs=_raw_git_audit_refs(receipt),
        proven_at_utc=str(getattr(receipt, "executed_at_utc", "") or _now_utc()),
        evidence_artifacts=evidence_artifacts,
    )


def _feature_id_for_commit(
    args: Any,
    *,
    repo_root: Path,
    runner: GitRunner,
    commit_sha: str,
) -> str:
    requested = str(getattr(args, "feature_id", "") or "").strip()
    if requested:
        return requested
    body = _git_stdout(runner, ("log", "-1", "--format=%B", commit_sha))
    plan_row_ids = _plan_row_id_set(repo_root=repo_root)
    for candidate in _candidate_plan_row_refs(body):
        if candidate in plan_row_ids:
            return candidate
    return commit_sha


def _feature_ids_for_commit(
    args: Any,
    *,
    repo_root: Path,
    runner: GitRunner,
    commit_sha: str,
    primary_feature_id: str,
) -> tuple[str, ...]:
    body = _git_stdout(runner, ("log", "-1", "--format=%B", commit_sha))
    requested = str(getattr(args, "feature_id", "") or "").strip()
    plan_row_ids = _plan_row_id_set(repo_root=repo_root)
    resolved_body_refs = tuple(
        candidate
        for candidate in _candidate_plan_row_refs(body)
        if candidate in plan_row_ids
    )
    explicit_unresolved = tuple(
        candidate
        for candidate in (primary_feature_id, requested)
        if candidate and candidate not in plan_row_ids and candidate != commit_sha
    )
    return _unique_refs(
        (
            *tuple(
                candidate
                for candidate in (primary_feature_id, requested)
                if candidate in plan_row_ids
            ),
            *resolved_body_refs,
            *explicit_unresolved,
        )
    )


def _candidate_plan_row_refs(body: str) -> tuple[str, ...]:
    return _unique_refs(
        _strip_plan_row_ref_punctuation(match.group(0))
        for match in _PLAN_ROW_CANDIDATE_RE.finditer(body)
    )


def _strip_plan_row_ref_punctuation(value: str) -> str:
    return value.strip().strip(".,;:)]}'\"")


def _plan_row_id_set(*, repo_root: Path) -> frozenset[str]:
    path = repo_root / DEFAULT_MASTER_PLAN_STORE_REL
    if not path.exists():
        return frozenset()
    return frozenset(row.row_id for row in read_plan_rows_jsonl(path))


def _raw_git_audit_refs(receipt: Any) -> tuple[str, ...]:
    return _unique_refs(
        (
            f"raw_git_bypass_receipt:{receipt.receipt_id}",
            str(getattr(receipt, "receipt_id", "") or ""),
            f"governed_exception:{getattr(receipt, 'governed_exception_id', '')}",
            str(getattr(receipt, "operator_quote_evidence_ref", "") or ""),
            (
                f"bypass_lifecycle_ref:{getattr(receipt, 'bypass_lifecycle_id', '')}"
                if getattr(receipt, "bypass_lifecycle_id", "")
                else ""
            ),
        )
    )


def _commit_lines(value: str) -> tuple[str, ...]:
    return tuple(line.strip() for line in value.splitlines() if line.strip())


def _string_items(values: object) -> tuple[str, ...]:
    if isinstance(values, str):
        candidates = (values,)
    else:
        try:
            candidates = tuple(values)  # type: ignore[arg-type]
        except TypeError:
            candidates = ()
    return _unique_refs(str(value).strip() for value in candidates if str(value).strip())


def _unique_refs(values: object) -> tuple[str, ...]:
    refs: list[str] = []
    seen: set[str] = set()
    try:
        iterator = iter(values)  # type: ignore[arg-type]
    except TypeError:
        return ()
    for value in iterator:
        ref = str(value).strip()
        if not ref or ref in seen:
            continue
        seen.add(ref)
        refs.append(ref)
    return tuple(refs)


def _optional_count(value: object, default: int) -> int:
    if value is None:
        return default
    try:
        return max(int(value), 0)
    except (TypeError, ValueError):
        return default


def _bool_arg(value: object) -> bool:
    return str(value).strip().lower() not in {"0", "false", "no", "off"}


def _first_new_commit_sha(
    runner: GitRunner,
    *,
    before_head: str,
    after_head: str,
) -> str:
    if not after_head or after_head == before_head:
        return ""
    if before_head:
        output = _git_stdout(runner, ("rev-list", "--reverse", f"{before_head}..{after_head}"))
        commits = tuple(line.strip() for line in output.splitlines() if line.strip())
        if commits:
            return commits[0]
    return after_head


def _normalized_git_args(values: object) -> tuple[str, ...]:
    args = tuple(str(value) for value in values if str(value).strip())
    if args and args[0] == "--":
        return args[1:]
    return args


def _is_git_help_request(git_args: tuple[str, ...]) -> bool:
    return git_args in {("--help",), ("-h",), ("help",)}


def _operator_evidence_ref(args: Any) -> str:
    refs = tuple(
        str(value).strip()
        for value in getattr(args, "operator_quote_evidence_ref", ()) or ()
        if str(value).strip()
    )
    return refs[-1] if refs else DEFAULT_OPERATOR_EVIDENCE_REF


def _skipped_pre_hooks(verb: RawGitVerb, git_args: tuple[str, ...]) -> tuple[str, ...]:
    if "--no-verify" not in git_args and "-n" not in git_args:
        return ()
    if verb is RawGitVerb.COMMIT:
        return ("pre-commit", "commit-msg")
    return ("pre-push",)


def _feature_proof_failure_report(
    *,
    verb: RawGitVerb,
    receipt: Any,
    write_result: Any,
    store_path: Path,
    command_result: GitCommandResult,
    error: str,
) -> dict[str, object]:
    """Return a fail-closed report when required proof emission fails."""
    warning = error or "feature_proof_receipt_write_failed"
    reason = (
        "plan_row_closure_failed"
        if warning.startswith("plan_row_closure_failed:")
        else "feature_proof_receipt_write_failed"
    )
    return {
        "command": "raw-git",
        "action": verb.value,
        "ok": False,
        "reason": reason,
        "error": warning,
        "receipt_id": getattr(receipt, "receipt_id", ""),
        "store_path": display_path(store_path),
        "feature_proof_receipt_paths": [],
        "feature_proof_receipt_warnings": [warning],
        "receipt": receipt.to_dict() if hasattr(receipt, "to_dict") else {},
        "write_result": write_result.to_dict()
        if hasattr(write_result, "to_dict")
        else {},
        "git_returncode": command_result.returncode,
        "git_stdout": command_result.stdout,
        "git_stderr": command_result.stderr,
    }


def _git_failure_report(
    verb: RawGitVerb,
    git_args: tuple[str, ...],
    result: GitCommandResult,
) -> dict[str, object]:
    return {
        "command": "raw-git",
        "action": verb.value,
        "ok": False,
        "reason": "git_command_failed",
        "git_args": list(git_args),
        "git_returncode": result.returncode,
        "git_stdout": result.stdout,
        "git_stderr": result.stderr,
    }


def _git_noop_report(
    verb: RawGitVerb,
    git_args: tuple[str, ...],
    reason: str,
    result: GitCommandResult | None = None,
) -> dict[str, object]:
    return {
        "command": "raw-git",
        "action": verb.value,
        "ok": False,
        "reason": reason,
        "git_args": list(git_args),
        "receipt_written": False,
        "git_returncode": result.returncode if result is not None else 0,
        "git_stdout": result.stdout if result is not None else "",
        "git_stderr": result.stderr if result is not None else "",
    }


def _error_report(reason: str, detail: str) -> dict[str, object]:
    return {
        "command": "raw-git",
        "ok": False,
        "reason": reason,
        "detail": detail,
    }


def _render_markdown(report: dict[str, object]) -> str:
    lines = ["# devctl raw-git", ""]
    for key in ("ok", "action", "receipt_id", "store_path", "reason"):
        if key in report:
            lines.append(f"- {key}: `{report[key]}`")
    receipt = report.get("receipt")
    if isinstance(receipt, dict):
        lines.append(f"- git_verb: `{receipt.get('git_verb')}`")
        lines.append(f"- commit_sha: `{receipt.get('commit_sha')}`")
        lines.append(f"- push_range: `{receipt.get('push_range')}`")
        lines.append(f"- skipped_pre_hooks: `{receipt.get('skipped_pre_hooks')}`")
    return "\n".join(lines) + "\n"


def _now_utc() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
