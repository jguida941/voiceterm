"""Typed proof that a git mutation changed the object or remote ref claimed."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from .correlation_spine import CorrelationContext, correlation_context_from_mapping
from .ref_collections import unique_refs
from .value_coercion import (
    coerce_bool,
    coerce_int,
    coerce_mapping,
    coerce_string,
    coerce_string_items,
)
from .vcs import run_git_capture

GIT_MUTATION_PROOF_RECEIPT_CONTRACT_ID = "GitMutationProofReceipt"
GIT_MUTATION_PROOF_RECEIPT_SCHEMA_VERSION = 1
GIT_MUTATION_PROOF_RECEIPT_STORE_REL = "dev/reports/git_mutation_proof_receipts.jsonl"


@dataclass(frozen=True, slots=True)
class GitMutationProofReceipt:
    """Evidence row for one commit or push mutation boundary."""

    schema_version: int = GIT_MUTATION_PROOF_RECEIPT_SCHEMA_VERSION
    contract_id: str = GIT_MUTATION_PROOF_RECEIPT_CONTRACT_ID
    receipt_id: str = ""
    mutation_kind: str = ""
    action_id: str = ""
    pipeline_id: str = ""
    plan_row_id: str = ""
    command_name: str = ""
    command_returncode: int = 0
    operation_returned_success: bool = False
    expected_sha: str = ""
    observed_local_sha: str = ""
    observed_remote_sha: str = ""
    object_type: str = ""
    remote_name: str = ""
    branch_name: str = ""
    verified: bool = False
    status: str = "unknown"
    failure_reason: str = ""
    recorded_at_utc: str = ""
    produced_by: str = "devctl"
    code_identity_hash: str = ""
    evidence_refs: tuple[str, ...] = ()
    artifact_paths: tuple[str, ...] = ()
    correlation_context: CorrelationContext = field(default_factory=CorrelationContext)

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["evidence_refs"] = list(self.evidence_refs)
        payload["artifact_paths"] = list(self.artifact_paths)
        return payload


def git_mutation_proof_receipt_from_mapping(
    payload: Mapping[str, object],
) -> GitMutationProofReceipt:
    """Normalize a JSON mapping into a GitMutationProofReceipt."""
    mapping = coerce_mapping(payload)
    correlation_context = correlation_context_from_mapping(
        mapping.get("correlation_context") or mapping
    )
    return GitMutationProofReceipt(
        schema_version=coerce_int(mapping.get("schema_version"))
        or GIT_MUTATION_PROOF_RECEIPT_SCHEMA_VERSION,
        contract_id=coerce_string(mapping.get("contract_id"))
        or GIT_MUTATION_PROOF_RECEIPT_CONTRACT_ID,
        receipt_id=coerce_string(mapping.get("receipt_id")),
        mutation_kind=coerce_string(mapping.get("mutation_kind")),
        action_id=coerce_string(mapping.get("action_id")),
        pipeline_id=coerce_string(mapping.get("pipeline_id")),
        plan_row_id=coerce_string(mapping.get("plan_row_id")),
        command_name=coerce_string(mapping.get("command_name")),
        command_returncode=coerce_int(mapping.get("command_returncode")),
        operation_returned_success=coerce_bool(
            mapping.get("operation_returned_success")
        ),
        expected_sha=coerce_string(mapping.get("expected_sha")),
        observed_local_sha=coerce_string(mapping.get("observed_local_sha")),
        observed_remote_sha=coerce_string(mapping.get("observed_remote_sha")),
        object_type=coerce_string(mapping.get("object_type")),
        remote_name=coerce_string(mapping.get("remote_name")),
        branch_name=coerce_string(mapping.get("branch_name")),
        verified=coerce_bool(mapping.get("verified")),
        status=coerce_string(mapping.get("status")) or "unknown",
        failure_reason=coerce_string(mapping.get("failure_reason")),
        recorded_at_utc=coerce_string(mapping.get("recorded_at_utc")),
        produced_by=coerce_string(mapping.get("produced_by")) or "devctl",
        code_identity_hash=coerce_string(mapping.get("code_identity_hash")),
        evidence_refs=coerce_string_items(mapping.get("evidence_refs")),
        artifact_paths=coerce_string_items(mapping.get("artifact_paths")),
        correlation_context=correlation_context,
    )


def build_commit_git_mutation_proof_receipt(
    *,
    repo_root: Path,
    claim: GitMutationProofReceipt,
    allow_reachable_head: bool = False,
) -> GitMutationProofReceipt:
    """Build a commit proof by checking the claimed commit object and HEAD."""
    expected_sha = claim.expected_sha
    observed_head = _git_stdout(repo_root, "rev-parse", "HEAD")
    object_type = _git_stdout(repo_root, "cat-file", "-t", expected_sha)
    head_matches_expected = observed_head == expected_sha
    expected_reachable_from_head = (
        bool(allow_reachable_head)
        and bool(expected_sha)
        and bool(observed_head)
        and object_type == "commit"
        and _git_success(
            repo_root,
            "merge-base",
            "--is-ancestor",
            expected_sha,
            observed_head,
        )
    )
    verified = (
        bool(claim.operation_returned_success)
        and bool(expected_sha)
        and object_type == "commit"
        and (head_matches_expected or expected_reachable_from_head)
    )
    failure_reason = ""
    if not verified:
        failure_reason = _first_failure(
            (
                (
                    not claim.operation_returned_success,
                    "git_commit_returned_failure",
                ),
                (not expected_sha, "missing_expected_sha"),
                (object_type != "commit", "expected_sha_not_commit_object"),
                (
                    not head_matches_expected and not expected_reachable_from_head,
                    "head_does_not_match_expected_sha",
                ),
            )
        )
    return GitMutationProofReceipt(
        receipt_id=claim.receipt_id
        or _receipt_id("commit", expected_sha or observed_head or claim.action_id),
        mutation_kind="commit",
        action_id=claim.action_id,
        pipeline_id=claim.pipeline_id,
        plan_row_id=claim.plan_row_id,
        command_name="git commit",
        command_returncode=claim.command_returncode,
        operation_returned_success=bool(claim.operation_returned_success),
        expected_sha=expected_sha,
        observed_local_sha=observed_head,
        object_type=object_type,
        verified=verified,
        status="verified" if verified else "failed",
        failure_reason=failure_reason,
        recorded_at_utc=_utc_now(),
        code_identity_hash=claim.code_identity_hash,
        artifact_paths=tuple(path for path in claim.artifact_paths if path),
        evidence_refs=unique_refs(
            (
                _ref("commit", expected_sha),
                _ref("local_head", observed_head),
                _ref("reachable_head", observed_head)
                if expected_reachable_from_head
                else "",
                _ref("pipeline", claim.pipeline_id),
                _ref("plan", claim.plan_row_id),
                _ref("code_identity", claim.code_identity_hash),
            )
        ),
        correlation_context=claim.correlation_context,
    )


def build_push_git_mutation_proof_receipt(
    *,
    repo_root: Path,
    claim: GitMutationProofReceipt,
) -> GitMutationProofReceipt:
    """Build a push proof by checking the claimed remote branch ref."""
    expected_sha = claim.expected_sha
    remote_name = claim.remote_name
    branch_name = claim.branch_name
    observed_remote_sha = claim.observed_remote_sha
    local_sha = claim.observed_local_sha or _git_stdout(repo_root, "rev-parse", "HEAD")
    verified = (
        bool(claim.operation_returned_success)
        and bool(expected_sha)
        and local_sha == expected_sha
        and observed_remote_sha == expected_sha
    )
    failure_reason = ""
    if not verified:
        failure_reason = _first_failure(
            (
                (not claim.operation_returned_success, "git_push_returned_failure"),
                (not expected_sha, "missing_expected_sha"),
                (local_sha != expected_sha, "head_does_not_match_expected_sha"),
                (
                    observed_remote_sha != expected_sha,
                    "remote_ref_does_not_match_expected_sha",
                ),
            )
        )
    return GitMutationProofReceipt(
        receipt_id=claim.receipt_id
        or _receipt_id(
            "push",
            ":".join((remote_name, branch_name, expected_sha or observed_remote_sha)),
        ),
        mutation_kind="push",
        action_id=claim.action_id,
        pipeline_id=claim.pipeline_id,
        plan_row_id=claim.plan_row_id,
        command_name="git push",
        command_returncode=claim.command_returncode,
        operation_returned_success=bool(claim.operation_returned_success),
        expected_sha=expected_sha,
        observed_local_sha=local_sha,
        observed_remote_sha=observed_remote_sha,
        remote_name=remote_name,
        branch_name=branch_name,
        verified=verified,
        status="verified" if verified else "failed",
        failure_reason=failure_reason,
        recorded_at_utc=_utc_now(),
        code_identity_hash=claim.code_identity_hash,
        artifact_paths=tuple(path for path in claim.artifact_paths if path),
        evidence_refs=unique_refs(
            (
                _ref("commit", expected_sha),
                _ref("local_head", local_sha),
                _ref("remote_head", observed_remote_sha),
                _ref("remote", remote_name),
                _ref("branch", branch_name),
                _ref("pipeline", claim.pipeline_id),
                _ref("plan", claim.plan_row_id),
                _ref("code_identity", claim.code_identity_hash),
            )
        ),
        correlation_context=claim.correlation_context,
    )


def append_git_mutation_proof_receipt(
    repo_root: Path,
    receipt: GitMutationProofReceipt,
    *,
    store_relpath: str = GIT_MUTATION_PROOF_RECEIPT_STORE_REL,
) -> str:
    """Append a receipt to the JSONL store and return the repo-relative path."""
    path = repo_root / store_relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(receipt.to_dict(), sort_keys=True) + "\n")
    return store_relpath


def read_git_mutation_proof_receipts(
    repo_root: Path,
    *,
    store_relpath: str = GIT_MUTATION_PROOF_RECEIPT_STORE_REL,
) -> tuple[GitMutationProofReceipt, ...]:
    """Read all valid proof receipts from the JSONL store."""
    path = repo_root / store_relpath
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return ()
    receipts: list[GitMutationProofReceipt] = []
    for raw in lines:
        if not raw.strip():
            continue
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, Mapping):
            receipts.append(git_mutation_proof_receipt_from_mapping(payload))
    return tuple(receipts)


def _git_stdout(repo_root: Path, *args: str) -> str:
    code, stdout, _stderr = run_git_capture(list(args), repo_root=repo_root)
    if code != 0:
        return ""
    return stdout.strip().splitlines()[0].strip() if stdout.strip() else ""


def _git_success(repo_root: Path, *args: str) -> bool:
    code, _stdout, _stderr = run_git_capture(list(args), repo_root=repo_root)
    return code == 0


def _first_failure(items: Iterable[tuple[bool, str]]) -> str:
    for failed, reason in items:
        if failed:
            return reason
    return "verification_failed"


def _receipt_id(kind: str, token: str) -> str:
    safe = "".join(char for char in token if char.isalnum() or char in "._:-")[:96]
    return f"git_mutation_proof:{kind}:{safe or 'unknown'}"


def _ref(kind: str, value: str) -> str:
    return f"{kind}:{value}" if value else ""


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


__all__ = [
    "GIT_MUTATION_PROOF_RECEIPT_CONTRACT_ID",
    "GIT_MUTATION_PROOF_RECEIPT_SCHEMA_VERSION",
    "GIT_MUTATION_PROOF_RECEIPT_STORE_REL",
    "GitMutationProofReceipt",
    "append_git_mutation_proof_receipt",
    "build_commit_git_mutation_proof_receipt",
    "build_push_git_mutation_proof_receipt",
    "git_mutation_proof_receipt_from_mapping",
    "read_git_mutation_proof_receipts",
]
