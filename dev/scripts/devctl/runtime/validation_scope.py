"""Typed validation-scope contract for guard routing."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ValidationScopeKind(str, Enum):
    """Execution context for a validation bundle."""

    LIVE_WORKTREE = "live_worktree"
    STAGED_TREE = "staged_tree"
    PIPELINE_AUTHORIZED_PHASE = "pipeline_authorized_phase"


@dataclass(frozen=True, slots=True)
class ValidationScope:
    """Typed context that distinguishes live checks from publication checks."""

    kind: ValidationScopeKind = ValidationScopeKind.LIVE_WORKTREE
    since_ref: str | None = None
    head_ref: str = "HEAD"
    range_scope_only: bool = False

    @property
    def pipeline_authorized(self) -> bool:
        return self.kind is ValidationScopeKind.PIPELINE_AUTHORIZED_PHASE

    def to_dict(self) -> dict[str, object]:
        return {
            "contract_id": "ValidationScope",
            "kind": self.kind.value,
            "since_ref": self.since_ref,
            "head_ref": self.head_ref,
            "range_scope_only": self.range_scope_only,
        }


@dataclass(frozen=True, slots=True)
class ValidationContext:
    """Pipeline identity carried beside a validation scope."""

    scope: ValidationScope = field(default_factory=ValidationScope)
    pipeline_ref: str = ""
    commit_sha: str = ""
    branch: str = ""
    repair_phase_paths: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {"contract_id": "ValidationContext"}
        payload["scope"] = self.scope.to_dict()
        payload["pipeline_ref"] = self.pipeline_ref
        payload["commit_sha"] = self.commit_sha
        payload["branch"] = self.branch
        payload["repair_phase_paths"] = list(self.repair_phase_paths)
        return payload


def validation_scope_from_args(args) -> ValidationScope:
    """Build a ValidationScope from argparse-like router args."""
    raw_kind = str(getattr(args, "validation_scope", "") or "").strip()
    kind = _validation_scope_kind(raw_kind)
    return ValidationScope(
        kind=kind,
        since_ref=getattr(args, "since_ref", None),
        head_ref=str(getattr(args, "head_ref", "HEAD") or "HEAD"),
        range_scope_only=bool(getattr(args, "range_scope_only", False)),
    )


def add_validation_scope_argument(parser) -> None:
    """Add the shared validation-scope CLI flag to an argparse parser."""
    parser.add_argument(
        "--validation-scope",
        choices=tuple(kind.value for kind in ValidationScopeKind),
        default=ValidationScopeKind.LIVE_WORKTREE.value,
        help=(
            "Typed validation context. Pipeline-authorized scope keeps live "
            "projection evidence visible without making it publication blocking."
        ),
    )


def apply_validation_scope_to_report(
    report: dict[str, Any],
    validation_scope: ValidationScope,
    *,
    reason: str,
) -> dict[str, Any]:
    """Annotate guard output with validation-scope semantics.

    Standalone and ad-hoc guard invocations remain strict. Inside a governed
    pipeline publication phase, live projection/freshness guards still run and
    publish their original result, but stale live state is advisory rather than
    a hard publication veto.
    """
    scoped = dict(report)
    original_ok = bool(scoped.get("ok", False))
    scoped["validation_scope"] = validation_scope.to_dict()
    scoped["live_worktree_ok"] = original_ok
    if not validation_scope.pipeline_authorized:
        return scoped

    scoped["pipeline_authorized_ok"] = True
    scoped["pipeline_authorized_advisory_reason"] = reason
    if not original_ok:
        scoped["pipeline_scope_original_ok"] = False
        scoped["pipeline_scope_original_errors"] = list(scoped.get("errors") or ())
        scoped["ok"] = True
    return scoped


def _validation_scope_kind(raw_kind: str) -> ValidationScopeKind:
    if raw_kind in {"publication", ValidationScopeKind.PIPELINE_AUTHORIZED_PHASE.value}:
        return ValidationScopeKind.PIPELINE_AUTHORIZED_PHASE
    if raw_kind == ValidationScopeKind.STAGED_TREE.value:
        return ValidationScopeKind.STAGED_TREE
    return ValidationScopeKind.LIVE_WORKTREE


__all__ = [
    "ValidationContext",
    "ValidationScope",
    "ValidationScopeKind",
    "add_validation_scope_argument",
    "apply_validation_scope_to_report",
    "validation_scope_from_args",
]
