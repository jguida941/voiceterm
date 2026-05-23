"""Typed scope-claim lifecycle for the receipt-steward role (A38.2 S2).

This module is the typed substrate for the READ-only audit-scope claim
the receipt-steward role latches before performing an audit. It mirrors
the four-stage shape of `BypassLifecycle`:

    ReceiptStewardScopeClaimRequest
      -> ReceiptStewardScopeClaimEvaluation
        -> ReceiptStewardScopeClaim
          -> ReceiptStewardScopeClaimExpiry

The role is GOVERNANCE / audit-only. The claim is a typed latch that
records which on-disk scope paths an audit invocation is allowed to
READ from, with a bounded TTL. The default scope_paths cover the
inputs the audit ritual inventories (feature_proof_receipts, plan
index, evidence prose, git history); none of them are mutation
targets.

Persistence lands at `dev/state/receipt_steward_claims.jsonl` via the
shared `append_json_mapping` writer used by the other lifecycle
stores. CLI handlers that call into this module fail closed when no
active claim exists for the requesting actor; the substrate itself
exposes pure helpers and does not write to disk.
"""

from __future__ import annotations

import secrets
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import cast


DEFAULT_RECEIPT_STEWARD_CLAIM_STORE_REL = Path(
    "dev/state/receipt_steward_claims.jsonl"
)

DEFAULT_RECEIPT_STEWARD_TTL_MINUTES = 30

DEFAULT_RECEIPT_STEWARD_SCOPE_PATHS: tuple[str, ...] = (
    "dev/reports/feature_proof_receipts/",
    "dev/state/plan_index.jsonl",
    "dev/active/semantic_tdd_lane.md",
    "evidence.md",
    ".git/",
)

RECEIPT_STEWARD_CLAIM_REQUEST_CONTRACT_ID = "ReceiptStewardScopeClaimRequest"
RECEIPT_STEWARD_CLAIM_EVALUATION_CONTRACT_ID = "ReceiptStewardScopeClaimEvaluation"
RECEIPT_STEWARD_CLAIM_CONTRACT_ID = "ReceiptStewardScopeClaim"
RECEIPT_STEWARD_CLAIM_EXPIRY_CONTRACT_ID = "ReceiptStewardScopeClaimExpiry"
RECEIPT_STEWARD_CLAIM_SCHEMA_VERSION = 1

RECEIPT_STEWARD_CLAIM_EXPIRY_REASONS: frozenset[str] = frozenset(
    {
        "ttl_elapsed",
        "operator_revoked",
        "released_by_actor",
    }
)


@dataclass(frozen=True, slots=True)
class ReceiptStewardScopeClaimRequest:
    """Typed request for a receipt-steward READ-only scope claim.

    Carries the requesting actor's role + session id, the bounded
    scope paths the audit will read, an operator-readable reason, and
    a bounded TTL in minutes. The role must be ``receipt_steward``;
    the helper :func:`request_scope_claim` validates that.
    """

    request_id: str
    actor_role: str
    actor_session_id: str
    scope_paths: tuple[str, ...]
    reason: str
    requested_at_utc: str
    requested_ttl_minutes: int = DEFAULT_RECEIPT_STEWARD_TTL_MINUTES
    schema_version: int = RECEIPT_STEWARD_CLAIM_SCHEMA_VERSION
    contract_id: str = RECEIPT_STEWARD_CLAIM_REQUEST_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["scope_paths"] = list(self.scope_paths)
        return payload

    @classmethod
    def from_mapping(cls, mapping: Mapping[str, object]) -> "ReceiptStewardScopeClaimRequest":
        data = _mapping_payload(mapping)
        return cls(
            request_id=_coerce_str(data.get("request_id")),
            actor_role=_coerce_str(data.get("actor_role")),
            actor_session_id=_coerce_str(data.get("actor_session_id")),
            scope_paths=_coerce_string_tuple(data.get("scope_paths")),
            reason=_coerce_str(data.get("reason")),
            requested_at_utc=_coerce_str(data.get("requested_at_utc")),
            requested_ttl_minutes=_coerce_int(
                data.get("requested_ttl_minutes"),
                default=DEFAULT_RECEIPT_STEWARD_TTL_MINUTES,
            ),
        )


@dataclass(frozen=True, slots=True)
class ReceiptStewardScopeClaimEvaluation:
    """Typed evaluation outcome for one scope-claim request.

    For a READ-only audit role we default to auto-grant when the
    request's scope is a subset of the typed default scope paths;
    operators can still grant explicitly. The denial_reason field is
    empty unless ``granted`` is ``False``.
    """

    evaluation_id: str
    request_id: str
    granted: bool
    granted_at_utc: str
    granted_by_role: str
    denial_reason: str = ""
    schema_version: int = RECEIPT_STEWARD_CLAIM_SCHEMA_VERSION
    contract_id: str = RECEIPT_STEWARD_CLAIM_EVALUATION_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    @classmethod
    def from_mapping(
        cls, mapping: Mapping[str, object]
    ) -> "ReceiptStewardScopeClaimEvaluation":
        data = _mapping_payload(mapping)
        return cls(
            evaluation_id=_coerce_str(data.get("evaluation_id")),
            request_id=_coerce_str(data.get("request_id")),
            granted=bool(data.get("granted", False)),
            granted_at_utc=_coerce_str(data.get("granted_at_utc")),
            granted_by_role=_coerce_str(data.get("granted_by_role")),
            denial_reason=_coerce_str(data.get("denial_reason")),
        )


@dataclass(frozen=True, slots=True)
class ReceiptStewardScopeClaim:
    """Typed READ-only scope claim issued to the receipt-steward role.

    Carries the bounded scope paths and the issued/expiry timestamps.
    ``status`` is one of ``active``, ``expired``, ``released``; the
    pure helper :func:`claim_is_active` returns True only when the
    claim's TTL has not elapsed AND status is ``active``.
    """

    claim_id: str
    actor_session_id: str
    scope_paths: tuple[str, ...]
    issued_at_utc: str
    expiry_utc: str
    parent_request_id: str
    actor_role: str = "receipt_steward"
    status: str = "active"
    schema_version: int = RECEIPT_STEWARD_CLAIM_SCHEMA_VERSION
    contract_id: str = RECEIPT_STEWARD_CLAIM_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["scope_paths"] = list(self.scope_paths)
        return payload

    @classmethod
    def from_mapping(cls, mapping: Mapping[str, object]) -> "ReceiptStewardScopeClaim":
        data = _mapping_payload(mapping)
        return cls(
            claim_id=_coerce_str(data.get("claim_id")),
            actor_session_id=_coerce_str(data.get("actor_session_id")),
            scope_paths=_coerce_string_tuple(data.get("scope_paths")),
            issued_at_utc=_coerce_str(data.get("issued_at_utc")),
            expiry_utc=_coerce_str(data.get("expiry_utc")),
            parent_request_id=_coerce_str(data.get("parent_request_id")),
            actor_role=_coerce_str(data.get("actor_role")) or "receipt_steward",
            status=_coerce_str(data.get("status")) or "active",
        )


@dataclass(frozen=True, slots=True)
class ReceiptStewardScopeClaimExpiry:
    """Typed expiry receipt for one scope claim.

    Three expiry reasons (``ttl_elapsed``, ``operator_revoked``,
    ``released_by_actor``) match the lifecycle vocabulary; unknown
    reasons raise ``ValueError`` through :func:`release_scope_claim`.
    """

    expiry_id: str
    claim_id: str
    expired_at_utc: str
    expiry_reason: str
    schema_version: int = RECEIPT_STEWARD_CLAIM_SCHEMA_VERSION
    contract_id: str = RECEIPT_STEWARD_CLAIM_EXPIRY_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    @classmethod
    def from_mapping(
        cls, mapping: Mapping[str, object]
    ) -> "ReceiptStewardScopeClaimExpiry":
        data = _mapping_payload(mapping)
        return cls(
            expiry_id=_coerce_str(data.get("expiry_id")),
            claim_id=_coerce_str(data.get("claim_id")),
            expired_at_utc=_coerce_str(data.get("expired_at_utc")),
            expiry_reason=_coerce_str(data.get("expiry_reason")),
        )


# ---------------------------------------------------------------------------
# Pure-function reducers
# ---------------------------------------------------------------------------


def request_scope_claim(
    *,
    actor_role: str,
    actor_session_id: str,
    reason: str,
    requested_ttl_minutes: int = DEFAULT_RECEIPT_STEWARD_TTL_MINUTES,
    scope_paths: tuple[str, ...] | None = None,
    now_utc: str | None = None,
    request_id: str | None = None,
) -> ReceiptStewardScopeClaimRequest:
    """Build a typed scope-claim request.

    Fails closed when ``actor_role != "receipt_steward"`` so the role
    boundary is enforced at the substrate level rather than in CLI
    handlers. The TTL is clamped to a positive integer.
    """
    role = (actor_role or "").strip()
    if role != "receipt_steward":
        raise ValueError(
            f"receipt_steward_scope_claim_request_actor_role_mismatch: {role!r}"
        )
    session = (actor_session_id or "").strip()
    if not session:
        raise ValueError("receipt_steward_scope_claim_request_session_id_required")
    reason_text = (reason or "").strip()
    if not reason_text:
        raise ValueError("receipt_steward_scope_claim_request_reason_required")
    ttl_minutes = int(requested_ttl_minutes) if requested_ttl_minutes else 0
    if ttl_minutes <= 0:
        raise ValueError(
            f"receipt_steward_scope_claim_request_ttl_minutes_invalid: {ttl_minutes}"
        )
    paths = tuple(scope_paths) if scope_paths else DEFAULT_RECEIPT_STEWARD_SCOPE_PATHS
    timestamp = now_utc or _now_utc()
    rid = (request_id or "").strip() or _build_request_id(timestamp)
    return ReceiptStewardScopeClaimRequest(
        request_id=rid,
        actor_role=role,
        actor_session_id=session,
        scope_paths=paths,
        reason=reason_text,
        requested_at_utc=timestamp,
        requested_ttl_minutes=ttl_minutes,
    )


def evaluate_scope_claim(
    request: ReceiptStewardScopeClaimRequest,
    *,
    granted_by_role: str = "auto",
    now_utc: str | None = None,
    evaluation_id: str | None = None,
) -> ReceiptStewardScopeClaimEvaluation:
    """Evaluate a scope-claim request.

    Auto-grants when every requested scope path is a prefix of one of
    the typed ``DEFAULT_RECEIPT_STEWARD_SCOPE_PATHS`` entries. An
    operator-provided ``granted_by_role="operator"`` overrides and
    grants any in-scope path.
    """
    timestamp = now_utc or _now_utc()
    eval_id = (evaluation_id or "").strip() or _build_eval_id(timestamp)
    granted_by = (granted_by_role or "").strip() or "auto"

    if granted_by == "operator":
        return ReceiptStewardScopeClaimEvaluation(
            evaluation_id=eval_id,
            request_id=request.request_id,
            granted=True,
            granted_at_utc=timestamp,
            granted_by_role="operator",
        )

    unknown = tuple(
        path
        for path in request.scope_paths
        if not _path_is_in_default_scope(path)
    )
    if unknown:
        return ReceiptStewardScopeClaimEvaluation(
            evaluation_id=eval_id,
            request_id=request.request_id,
            granted=False,
            granted_at_utc=timestamp,
            granted_by_role="auto",
            denial_reason=(
                "scope_paths_outside_default_audit_scope: "
                + ",".join(unknown)
            ),
        )
    return ReceiptStewardScopeClaimEvaluation(
        evaluation_id=eval_id,
        request_id=request.request_id,
        granted=True,
        granted_at_utc=timestamp,
        granted_by_role="auto",
    )


def build_scope_claim(
    request: ReceiptStewardScopeClaimRequest,
    evaluation: ReceiptStewardScopeClaimEvaluation,
    *,
    now_utc: str | None = None,
    claim_id: str | None = None,
) -> ReceiptStewardScopeClaim:
    """Assemble the typed scope claim from a granted evaluation.

    Raises ``ValueError`` when the evaluation did not grant.
    """
    if not evaluation.granted:
        raise ValueError(
            f"receipt_steward_scope_claim_not_granted: {evaluation.denial_reason!r}"
        )
    timestamp = now_utc or _now_utc()
    cid = (claim_id or "").strip() or _build_claim_id(timestamp)
    expiry = _compute_expiry_utc(timestamp, request.requested_ttl_minutes)
    return ReceiptStewardScopeClaim(
        claim_id=cid,
        actor_session_id=request.actor_session_id,
        scope_paths=request.scope_paths,
        issued_at_utc=timestamp,
        expiry_utc=expiry,
        parent_request_id=request.request_id,
        actor_role=request.actor_role,
        status="active",
    )


def claim_is_active(
    claim: ReceiptStewardScopeClaim,
    *,
    now_utc: str | None = None,
) -> bool:
    """Return ``True`` only when the claim is ``active`` and not expired."""
    if claim.status != "active":
        return False
    if not claim.expiry_utc:
        return False
    try:
        expiry_dt = _parse_utc(claim.expiry_utc)
    except ValueError:
        return False
    reference = _parse_utc(now_utc) if now_utc else datetime.now(timezone.utc)
    return reference < expiry_dt


def release_scope_claim(
    claim: ReceiptStewardScopeClaim,
    *,
    expiry_reason: str = "released_by_actor",
    now_utc: str | None = None,
    expiry_id: str | None = None,
) -> tuple[ReceiptStewardScopeClaim, ReceiptStewardScopeClaimExpiry]:
    """Return an expired-status claim plus the typed expiry receipt."""
    reason = (expiry_reason or "").strip()
    if reason not in RECEIPT_STEWARD_CLAIM_EXPIRY_REASONS:
        raise ValueError(f"receipt_steward_scope_claim_expiry_reason_unknown: {reason!r}")
    timestamp = now_utc or _now_utc()
    eid = (expiry_id or "").strip() or _build_expiry_id(timestamp)
    expired_claim = ReceiptStewardScopeClaim(
        claim_id=claim.claim_id,
        actor_session_id=claim.actor_session_id,
        scope_paths=claim.scope_paths,
        issued_at_utc=claim.issued_at_utc,
        expiry_utc=claim.expiry_utc,
        parent_request_id=claim.parent_request_id,
        actor_role=claim.actor_role,
        status=(
            "expired"
            if reason in {"ttl_elapsed", "operator_revoked"}
            else "released"
        ),
    )
    expiry = ReceiptStewardScopeClaimExpiry(
        expiry_id=eid,
        claim_id=claim.claim_id,
        expired_at_utc=timestamp,
        expiry_reason=reason,
    )
    return expired_claim, expiry


def extend_scope_claim(
    claim: ReceiptStewardScopeClaim,
    *,
    additional_minutes: int,
    now_utc: str | None = None,
) -> ReceiptStewardScopeClaim:
    """Return a new claim with the expiry pushed out by N minutes."""
    if additional_minutes <= 0:
        raise ValueError(
            f"receipt_steward_scope_claim_extend_minutes_invalid: {additional_minutes}"
        )
    if claim.status != "active":
        raise ValueError(
            f"receipt_steward_scope_claim_extend_status_invalid: {claim.status!r}"
        )
    base_dt = _parse_utc(claim.expiry_utc)
    new_expiry = (
        base_dt + timedelta(minutes=additional_minutes)
    ).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    return ReceiptStewardScopeClaim(
        claim_id=claim.claim_id,
        actor_session_id=claim.actor_session_id,
        scope_paths=claim.scope_paths,
        issued_at_utc=claim.issued_at_utc,
        expiry_utc=new_expiry,
        parent_request_id=claim.parent_request_id,
        actor_role=claim.actor_role,
        status="active",
    )


# ---------------------------------------------------------------------------
# Private helpers (pure)
# ---------------------------------------------------------------------------


def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _parse_utc(value: str) -> datetime:
    if not value:
        raise ValueError("receipt_steward_scope_claim_timestamp_missing")
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


def _compute_expiry_utc(issued_at_utc: str, ttl_minutes: int) -> str:
    base = _parse_utc(issued_at_utc)
    return (base + timedelta(minutes=ttl_minutes)).strftime(
        "%Y-%m-%dT%H:%M:%S.%fZ"
    )


def _build_request_id(now: str) -> str:
    compact = _compact_timestamp(now)
    return f"ReceiptStewardScopeClaimRequest:{compact}-{secrets.token_hex(4)}"


def _build_eval_id(now: str) -> str:
    compact = _compact_timestamp(now)
    return f"ReceiptStewardScopeClaimEvaluation:{compact}-{secrets.token_hex(4)}"


def _build_claim_id(now: str) -> str:
    compact = _compact_timestamp(now)
    return f"ReceiptStewardScopeClaim:{compact}-{secrets.token_hex(4)}"


def _build_expiry_id(now: str) -> str:
    compact = _compact_timestamp(now)
    return f"ReceiptStewardScopeClaimExpiry:{compact}-{secrets.token_hex(4)}"


def _compact_timestamp(now: str) -> str:
    return (
        now.replace("-", "")
        .replace(":", "")
        .replace(".", "")
        .replace("Z", "")
    )


def _path_is_in_default_scope(path: str) -> bool:
    candidate = (path or "").strip()
    if not candidate:
        return False
    for default in DEFAULT_RECEIPT_STEWARD_SCOPE_PATHS:
        if candidate == default:
            return True
        if default.endswith("/") and candidate.startswith(default):
            return True
        if candidate.startswith(default + "/"):
            return True
    return False


def _mapping_payload(value: object) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        return {}
    return cast(Mapping[str, object], value)


def _coerce_str(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _coerce_int(value: object, *, default: int) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _coerce_string_tuple(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, (list, tuple)):
        return tuple(str(item) for item in value if str(item).strip())
    if isinstance(value, str):
        return (value.strip(),) if value.strip() else ()
    return ()


__all__ = [
    "DEFAULT_RECEIPT_STEWARD_CLAIM_STORE_REL",
    "DEFAULT_RECEIPT_STEWARD_SCOPE_PATHS",
    "DEFAULT_RECEIPT_STEWARD_TTL_MINUTES",
    "RECEIPT_STEWARD_CLAIM_CONTRACT_ID",
    "RECEIPT_STEWARD_CLAIM_EVALUATION_CONTRACT_ID",
    "RECEIPT_STEWARD_CLAIM_EXPIRY_CONTRACT_ID",
    "RECEIPT_STEWARD_CLAIM_EXPIRY_REASONS",
    "RECEIPT_STEWARD_CLAIM_REQUEST_CONTRACT_ID",
    "RECEIPT_STEWARD_CLAIM_SCHEMA_VERSION",
    "ReceiptStewardScopeClaim",
    "ReceiptStewardScopeClaimEvaluation",
    "ReceiptStewardScopeClaimExpiry",
    "ReceiptStewardScopeClaimRequest",
    "build_scope_claim",
    "claim_is_active",
    "evaluate_scope_claim",
    "extend_scope_claim",
    "release_scope_claim",
    "request_scope_claim",
]
