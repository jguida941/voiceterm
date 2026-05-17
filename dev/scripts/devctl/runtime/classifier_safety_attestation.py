"""Project typed BypassLifecycle authority to Claude classifier hints.

The durable authority remains the BypassLifecycle/BypassReceipt store. This
module only mirrors an active receipt into the operator-local
``.claude/settings.local.json`` classifier surface, which stays gitignored by
repo policy. If an existing ``Bash(*)`` rule is present, the projection is
recorded but marked as wildcard-dominated because the coarse allow rule already
permits the generated receipt-scoped rules.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .bypass_lifecycle_models import BypassAuthorityScope, BypassLifecycle
from .bypass_lifecycle_registry import bypass_lifecycle_active
from .governed_exception_base import json_ready_dict
from .state_store_authority import _atomic_replace_text, state_store_lock

CLASSIFIER_SAFETY_ATTESTATION_CONTRACT_ID = "ClassifierSafetyAttestation"
CLASSIFIER_SAFETY_ATTESTATION_SCHEMA_VERSION = 1
CLASSIFIER_SAFETY_SETTINGS_KEY = "codex_voice_classifier_safety"
DEFAULT_CLAUDE_SETTINGS_LOCAL_REL = Path(".claude/settings.local.json")


@dataclass(frozen=True, slots=True)
class ClassifierSafetyAttestation:
    """Typed evidence projected into Claude-readable local settings."""

    attestation_id: str
    bypass_receipt_id: str
    bypass_lifecycle_id: str
    source_contract: str
    target_surface: str
    settings_path: str
    target_role: str
    authority_scope: str
    granted_at_utc: str
    expires_at_utc: str
    permission_rules: tuple[str, ...]
    evidence_refs: tuple[str, ...] = ()
    schema_version: int = CLASSIFIER_SAFETY_ATTESTATION_SCHEMA_VERSION
    contract_id: str = CLASSIFIER_SAFETY_ATTESTATION_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        return json_ready_dict(asdict(self))


def classifier_permission_rules_for_receipt(receipt_id: str) -> tuple[str, ...]:
    """Return receipt-scoped Claude permission rules for launch recovery paths."""
    normalized = receipt_id.strip()
    receipt_fragment = f"*--bypass-receipt-id {normalized}*" if normalized else "*"
    return (
        (
            "Bash(python3 dev/scripts/devctl.py review-channel --action launch "
            f"{receipt_fragment})"
        ),
        (
            "Bash(python3 dev/scripts/devctl.py review-channel --action recover "
            f"{receipt_fragment})"
        ),
        (
            "Bash(python3 dev/scripts/devctl.py bypass attest "
            f"--receipt-id {normalized}*)"
        ),
    )


def build_classifier_safety_attestation(
    lifecycle: BypassLifecycle,
    *,
    settings_path: Path,
    required_scope: BypassAuthorityScope = BypassAuthorityScope.EDIT_ONLY,
) -> ClassifierSafetyAttestation | None:
    """Build an attestation only from an active typed BypassLifecycle."""
    if not bypass_lifecycle_active(lifecycle, required_scope=required_scope):
        return None
    if lifecycle.receipt is None:
        return None
    receipt = lifecycle.receipt
    evidence_refs = _ordered_unique(
        (
            f"bypass_lifecycle:{lifecycle.lifecycle_id}",
            f"bypass_receipt:{receipt.receipt_id}",
            *lifecycle.activation_evidence_refs,
            *lifecycle.request.evidence_refs,
            *lifecycle.evaluation.authority_evidence_refs,
            *lifecycle.evaluation.policy_evidence_refs,
        )
    )
    return ClassifierSafetyAttestation(
        attestation_id=f"classifier-safety:{receipt.receipt_id}",
        bypass_receipt_id=receipt.receipt_id,
        bypass_lifecycle_id=lifecycle.lifecycle_id,
        source_contract=lifecycle.contract_id,
        target_surface="claude_settings_local",
        settings_path=settings_path.as_posix(),
        target_role=lifecycle.request.target_role,
        authority_scope=receipt.requested_authority_scope.value,
        granted_at_utc=receipt.granted_at_utc,
        expires_at_utc=receipt.expires_at_utc,
        permission_rules=classifier_permission_rules_for_receipt(receipt.receipt_id),
        evidence_refs=evidence_refs,
    )


def project_classifier_safety_attestation(
    settings_path: Path,
    attestation: ClassifierSafetyAttestation,
) -> dict[str, object]:
    """Write one attestation and its permission rules into Claude settings."""
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    with state_store_lock(settings_path) as lock_path:
        payload = _read_settings_payload(settings_path)
        permissions = _ensure_mapping(payload, "permissions")
        allow = _ensure_string_list(permissions, "allow")
        wildcard_dominates = _has_bash_wildcard(allow)
        existing_rules = set(allow)
        added_rules = [
            rule for rule in attestation.permission_rules if rule not in existing_rules
        ]
        allow.extend(added_rules)

        bridge = _ensure_mapping(payload, CLASSIFIER_SAFETY_SETTINGS_KEY)
        attestations = _ensure_mapping_list(bridge, "attestations")
        previous_len = len(attestations)
        attestations[:] = [
            row
            for row in attestations
            if str(row.get("attestation_id") or "")
            != attestation.attestation_id
        ]
        attestations.append(attestation.to_dict())
        bridge["latest_attestation_id"] = attestation.attestation_id
        bridge["latest_bypass_receipt_id"] = attestation.bypass_receipt_id
        bridge["contract_id"] = CLASSIFIER_SAFETY_ATTESTATION_CONTRACT_ID
        bridge["schema_version"] = CLASSIFIER_SAFETY_ATTESTATION_SCHEMA_VERSION
        bridge["classifier_dominated_by_wildcard"] = wildcard_dominates
        if wildcard_dominates:
            bridge["latest_warning"] = "classifier_dominated_by_bash_wildcard"
        else:
            bridge.pop("latest_warning", None)

        content = json.dumps(payload, indent=2, sort_keys=True) + "\n"
        _atomic_replace_text(settings_path, content)
        warnings = (
            ("classifier_dominated_by_bash_wildcard",) if wildcard_dominates else ()
        )
        return {
            "ok": True,
            "settings_path": settings_path.as_posix(),
            "lock_path": lock_path.as_posix(),
            "attestation_id": attestation.attestation_id,
            "bypass_receipt_id": attestation.bypass_receipt_id,
            "permission_rule_count": len(attestation.permission_rules),
            "added_permission_rules": added_rules,
            "replaced_existing_attestation": len(attestations) != previous_len + 1,
            "classifier_dominated_by_wildcard": wildcard_dominates,
            "warnings": warnings,
            "contract_id": CLASSIFIER_SAFETY_ATTESTATION_CONTRACT_ID,
            "schema_version": CLASSIFIER_SAFETY_ATTESTATION_SCHEMA_VERSION,
        }


def _read_settings_payload(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {}
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid Claude settings JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: expected Claude settings JSON object")
    return dict(payload)


def _ensure_mapping(payload: dict[str, Any], key: str) -> dict[str, Any]:
    current = payload.get(key)
    if current is None:
        current = {}
        payload[key] = current
    if not isinstance(current, dict):
        raise ValueError(f"{key}_must_be_object")
    return current


def _ensure_string_list(payload: dict[str, Any], key: str) -> list[str]:
    current = payload.get(key)
    if current is None:
        current = []
        payload[key] = current
    if not isinstance(current, list) or not all(
        isinstance(item, str) for item in current
    ):
        raise ValueError(f"{key}_must_be_string_list")
    return current


def _ensure_mapping_list(payload: dict[str, Any], key: str) -> list[dict[str, Any]]:
    current = payload.get(key)
    if current is None:
        current = []
        payload[key] = current
    if not isinstance(current, list) or not all(
        isinstance(item, Mapping) for item in current
    ):
        raise ValueError(f"{key}_must_be_object_list")
    return current


def _ordered_unique(items: tuple[str, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        normalized = item.strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return tuple(result)


def _has_bash_wildcard(allow_rules: list[str]) -> bool:
    return any(rule.strip() == "Bash(*)" for rule in allow_rules)


__all__ = [
    "CLASSIFIER_SAFETY_ATTESTATION_CONTRACT_ID",
    "CLASSIFIER_SAFETY_ATTESTATION_SCHEMA_VERSION",
    "CLASSIFIER_SAFETY_SETTINGS_KEY",
    "DEFAULT_CLAUDE_SETTINGS_LOCAL_REL",
    "ClassifierSafetyAttestation",
    "build_classifier_safety_attestation",
    "classifier_permission_rules_for_receipt",
    "project_classifier_safety_attestation",
]
