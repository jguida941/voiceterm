"""Bypass lifecycle platform contract rows."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .contracts import ContractField, ContractSpec, CrossLinkSpec

if TYPE_CHECKING:
    from ..runtime.bypass_activation_result import (
        BypassActivated,
        BypassDenied,
    )

    _TYPESTATE_RESULT_REFS: tuple[
        type[BypassActivated],
        type[BypassDenied],
    ]

BYPASS_LIFECYCLE_CONTRACTS: tuple[ContractSpec, ...] = (
    ContractSpec(
        contract_id="BypassRequest",
        owner_layer="governance_runtime",
        purpose=(
            "Typed operator bypass request carrying scope, reason, actor, role, "
            "session, surface, and evidence before any bypass authority can be evaluated."
        ),
        required_fields=(
            ContractField("request_id", "str", "Stable bypass request id."),
            ContractField("scope", "BypassAuthorityScope", "Requested bounded authority scope."),
            ContractField("state", "BypassLifecycleState", "Explicit request state."),
            ContractField("reason", "str", "Operator-visible reason."),
            ContractField("actor", "str", "Actor requesting or authorizing bypass."),
            ContractField("requested_at_utc", "str", "Request timestamp."),
            ContractField("target_role", "str", "Target role lane."),
            ContractField("target_session_id", "str", "Target session id."),
            ContractField("target_surface", "str", "Target surface consuming bypass."),
            ContractField("evidence_refs", "tuple[str, ...]", "Packet/operator evidence refs."),
        ),
        runtime_model="dev.scripts.devctl.runtime.lifetime_bypass_mode:BypassRequest",
        startup_surface_tokens=("request_id", "scope", "target_surface"),
    ),
    ContractSpec(
        contract_id="BypassEvaluation",
        owner_layer="governance_runtime",
        purpose=(
            "Typed reducer result that composes a BypassRequest with policy, "
            "project governance, repo-pack evidence, and GovernedExceptionLifecycle."
        ),
        required_fields=(
            ContractField("evaluation_id", "str", "Stable bypass evaluation id."),
            ContractField("request_id", "str", "Request evaluated."),
            ContractField("decision", "BypassEvaluationDecision", "Approved or denied."),
            ContractField("evaluated_at_utc", "str", "Evaluation timestamp."),
            ContractField("evaluator_actor_id", "str", "Evaluator actor id."),
            ContractField("reason", "str", "Decision reason."),
            ContractField("approved_scope", "BypassAuthorityScope | None", "Granted scope."),
            ContractField(
                "governed_exception_lifecycle_id",
                "str",
                "Governed exception lifecycle issued for approved bypass.",
            ),
            ContractField("authority_evidence_refs", "tuple[str, ...]", "Authority refs."),
            ContractField("policy_evidence_refs", "tuple[str, ...]", "Policy refs."),
        ),
        runtime_model="dev.scripts.devctl.runtime.lifetime_bypass_mode:BypassEvaluation",
        startup_surface_tokens=("evaluation_id", "decision", "request_id"),
        cross_links=(
            CrossLinkSpec(
                "governed_exception_lifecycle_id",
                "GovernedExceptionLifecycle",
                "receipt_proves",
                target_resolver="governed_exception_lifecycle_id",
                required_when="decision == approved",
            ),
        ),
    ),
    ContractSpec(
        contract_id="BypassReceipt",
        owner_layer="governance_runtime",
        purpose=(
            "Typed proof that an approved bypass was issued with bounded scope, "
            "operator evidence, AI evidence, and optional expiry/revocation state."
        ),
        required_fields=(
            ContractField("receipt_id", "str", "Stable bypass receipt id."),
            ContractField("reason", "str", "Approved reason."),
            ContractField("operator_signature", "str", "Operator signature or actor id."),
            ContractField("ai_approval_evidence", "str", "AI-visible approval evidence."),
            ContractField(
                "requested_authority_scope",
                "BypassAuthorityScope",
                "Granted bounded authority scope.",
            ),
            ContractField("state", "BypassLifecycleState", "Explicit receipt state."),
            ContractField("granted_at_utc", "str", "Grant timestamp."),
            ContractField("granted_by_operator_actor_id", "str", "Granting operator actor."),
            ContractField("expires_at_utc", "str", "Optional expiry timestamp."),
            ContractField("revoked_at_utc", "str", "Optional revocation timestamp."),
            ContractField("revoked_reason", "str", "Optional revocation reason."),
        ),
        runtime_model="dev.scripts.devctl.runtime.lifetime_bypass_mode:BypassReceipt",
        startup_surface_tokens=("receipt_id", "requested_authority_scope", "expires_at_utc"),
    ),
    ContractSpec(
        contract_id="BypassExpiry",
        owner_layer="governance_runtime",
        purpose=(
            "Typed expiry/revocation event for time-bound, stop-anchor, or "
            "operator-revoked bypass receipts."
        ),
        required_fields=(
            ContractField("expiry_id", "str", "Stable bypass expiry id."),
            ContractField("receipt_id", "str", "Receipt expired or revoked."),
            ContractField("expired_at_utc", "str", "Expiry timestamp."),
            ContractField("source", "BypassExpirySource", "Expiry source."),
            ContractField("reason", "str", "Expiry reason."),
            ContractField("evidence_refs", "tuple[str, ...]", "Expiry evidence refs."),
        ),
        runtime_model="dev.scripts.devctl.runtime.lifetime_bypass_mode:BypassExpiry",
        startup_surface_tokens=("expiry_id", "receipt_id", "source"),
        cross_links=(
            CrossLinkSpec(
                "receipt_id",
                "BypassReceipt",
                "receipt_proves",
                target_node_kind="receipt",
                target_resolver="bypass_receipt_id",
                required=True,
            ),
        ),
    ),
    ContractSpec(
        contract_id="BypassLifecycle",
        owner_layer="governance_runtime",
        purpose=(
            "Composable typed bypass lifecycle: BypassRequest -> "
            "BypassEvaluation -> BypassReceipt -> BypassExpiry, hosted by "
            "GovernedExceptionLifecycle instead of parallel bypass surfaces."
        ),
        required_fields=(
            ContractField("lifecycle_id", "str", "Stable lifecycle id."),
            ContractField("state", "BypassLifecycleState", "Current bypass lifecycle state."),
            ContractField("request", "BypassRequest", "Request envelope."),
            ContractField("evaluation", "BypassEvaluation", "Evaluation result."),
            ContractField("receipt", "BypassReceipt | None", "Issued receipt."),
            ContractField(
                "governed_exception",
                "GovernedExceptionLifecycle | None",
                "Governed exception host envelope.",
            ),
            ContractField("expiry", "BypassExpiry | None", "Expiry or revocation event."),
            ContractField(
                "activation_evidence_refs",
                "tuple[str, ...]",
                "Activation evidence refs.",
            ),
        ),
        runtime_model="dev.scripts.devctl.runtime.lifetime_bypass_mode:BypassLifecycle",
        startup_surface_tokens=("lifecycle_id", "state", "activation_evidence_refs"),
        cross_links=(
            CrossLinkSpec(
                "request",
                "BypassRequest",
                "contains",
                target_node_kind="typed_contract",
                target_resolver="embedded_bypass_request",
                required=True,
            ),
            CrossLinkSpec(
                "evaluation",
                "BypassEvaluation",
                "contains",
                target_node_kind="typed_contract",
                target_resolver="embedded_bypass_evaluation",
                required=True,
            ),
            CrossLinkSpec(
                "receipt",
                "BypassReceipt",
                "contains",
                target_node_kind="receipt",
                target_resolver="embedded_bypass_receipt",
                required_when="state in {bypass_receipt_issued,bypass_active}",
            ),
            CrossLinkSpec(
                "governed_exception",
                "GovernedExceptionLifecycle",
                "contains",
                target_node_kind="typed_contract",
                target_resolver="embedded_governed_exception_lifecycle",
                required_when="state in {bypass_receipt_issued,bypass_active}",
            ),
            CrossLinkSpec(
                "expiry",
                "BypassExpiry",
                "contains",
                target_node_kind="typed_contract",
                target_resolver="embedded_bypass_expiry",
                required_when="state in {bypass_expired,bypass_revoked}",
            ),
        ),
    ),
)

__all__ = ["BYPASS_LIFECYCLE_CONTRACTS"]
