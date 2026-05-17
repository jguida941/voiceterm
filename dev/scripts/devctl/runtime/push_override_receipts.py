"""Push override receipt parsing and emission."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .bypass_lifecycle_models import BypassLifecycle
from .remote_commit_pipeline_models import PushAuthorizationRecord
from .push_override_receipt_bypass import (
    active_push_override_bypass_lifecycles,
    matching_active_push_override_bypass_lifecycle,
)
from .push_override_receipt_signing import (
    PUSH_OVERRIDE_RECEIPT_HMAC_CONTRACT_ID,
    push_override_receipt_authorization_with_reason,
    push_override_receipt_hmac_signature,
    push_override_receipt_signature_matches,
)

PUSH_OVERRIDE_RECEIPT_ROOT = Path("dev/audits/push_override_receipts")
_MARKDOWN_FIELD_RE = re.compile(
    r"^(?:[-*]\s*)?\*\*(?P<label>[^*]+):\*\*\s*(?P<value>.*?)\s*$",
    re.MULTILINE,
)
_FULL_SHA_RE = re.compile(r"\b[0-9a-fA-F]{40}\b")


@dataclass(frozen=True, slots=True)
class PushOverrideReceipt:
    """Human-readable override receipt parsed into fields used by the gate."""

    path: Path
    contract: str
    override_id: str
    authorized_head_shas: tuple[str, ...]
    approval_mode: str
    approved_by: str
    override_reason: str
    bypass_lifecycle_id: str
    bypass_receipt_id: str
    hmac_contract: str
    hmac_signature: str


def push_override_receipt_violation(
    *,
    repo_root: Path,
    authorization: PushAuthorizationRecord,
) -> tuple[str, str] | None:
    """Return the blocking reason for an override-push receipt gap."""
    if str(authorization.approval_mode or "").strip() != "override_push":
        return None
    expected_head = str(authorization.authorized_head_sha or "").strip()
    if not expected_head:
        return (
            "push_override_receipt_invalid",
            "Override publication authorization must name the authorized HEAD.",
        )
    if not str(authorization.override_reason or "").strip():
        return (
            "push_override_receipt_invalid",
            "Override publication authorization must include a typed reason.",
        )
    matching_receipts = tuple(
        receipt
        for receipt in load_push_override_receipts(repo_root)
        if any(
            _same_commit(candidate, expected_head)
            for candidate in receipt.authorized_head_shas
        )
    )
    if not matching_receipts:
        return (
            "push_override_receipt_missing",
            (
                "Override publication requires a matching "
                "`PushOverrideReceipt` under dev/audits/push_override_receipts/ "
                "for the authorized HEAD."
            ),
    )
    active_lifecycles = active_push_override_bypass_lifecycles(repo_root)
    missing_by_path = {
        receipt.path: _missing_push_override_receipt_fields(
            receipt,
            authorization=authorization,
            active_lifecycles=active_lifecycles,
        )
        for receipt in matching_receipts
    }
    if any(not missing for missing in missing_by_path.values()):
        return None
    missing_fields = tuple(
        sorted({field for fields in missing_by_path.values() for field in fields})
    )
    return (
        "push_override_receipt_invalid",
        (
            "Matching PushOverrideReceipt is incomplete or malformed; "
            "missing/invalid fields: "
            + ", ".join(missing_fields)
            + "."
        ),
    )


def ensure_push_override_receipt(
    *,
    repo_root: Path,
    authorization: PushAuthorizationRecord,
    override_summary: str = "",
    override_body: str = "",
) -> PushOverrideReceipt | None:
    """Write a durable markdown receipt for an override-push authorization."""
    if str(authorization.approval_mode or "").strip() != "override_push":
        return None
    if not str(authorization.authorized_head_sha or "").strip():
        return None
    override_reason = (
        authorization.override_reason
        or override_summary
        or override_body
    ).strip()
    if not override_reason:
        return None
    active_lifecycles = active_push_override_bypass_lifecycles(repo_root)
    if not active_lifecycles:
        return None
    bypass_lifecycle = active_lifecycles[-1]
    bypass_receipt = bypass_lifecycle.receipt
    if bypass_receipt is None:
        return None
    if push_override_receipt_violation(
        repo_root=repo_root,
        authorization=push_override_receipt_authorization_with_reason(
            authorization,
            override_reason=override_reason,
        ),
    ) is None:
        return None
    receipt_root = repo_root / PUSH_OVERRIDE_RECEIPT_ROOT
    receipt_root.mkdir(parents=True, exist_ok=True)
    receipt_id = (
        authorization.authorization_id
        or authorization.decision_packet_id
        or authorization.authorized_head_sha[:12]
        or "override-push"
    )
    receipt_path = receipt_root / f"{_safe_receipt_filename(receipt_id)}.md"
    signed_authorization = push_override_receipt_authorization_with_reason(
        authorization,
        override_reason=override_reason,
    )
    hmac_signature = push_override_receipt_hmac_signature(
        authorization=signed_authorization,
        override_id=receipt_id,
        bypass_lifecycle=bypass_lifecycle,
    )
    receipt_path.write_text(
        "\n".join(
            (
                "# Push Override Receipt",
                "",
                "**Schema version:** 1",
                "**Contract:** `PushOverrideReceipt`",
                f"**Override id:** `{receipt_id}`",
                f"**Recorded at (UTC):** {authorization.approved_at_utc}",
                f"**Recorded by:** {authorization.approved_by or 'operator'}",
                f"**Authorized HEAD SHA:** `{authorization.authorized_head_sha}`",
                f"**Bypass lifecycle id:** `{bypass_lifecycle.lifecycle_id}`",
                f"**Bypass receipt id:** `{bypass_receipt.receipt_id}`",
                f"**HMAC contract:** `{PUSH_OVERRIDE_RECEIPT_HMAC_CONTRACT_ID}`",
                f"**HMAC signature:** `sha256:{hmac_signature}`",
                "",
                "## Approval typing",
                "",
                f"- **approval_mode:** `{authorization.approval_mode}`",
                f"- **review_verdict:** `{authorization.review_verdict}`",
                "",
                "## Override reason",
                "",
                override_reason.strip(),
                "",
                "## Pipeline authority",
                "",
                f"- **pipeline_id:** `{authorization.pipeline_id}`",
                f"- **generation_id:** `{authorization.generation_id}`",
                f"- **decision_packet_id:** `{authorization.decision_packet_id}`",
                f"- **request_packet_id:** `{authorization.request_packet_id}`",
                "",
            )
        ),
        encoding="utf-8",
    )
    return parse_push_override_receipt(receipt_path)


def load_push_override_receipts(repo_root: Path) -> tuple[PushOverrideReceipt, ...]:
    """Load all readable push override receipts under the repo audit root."""
    receipt_root = repo_root / PUSH_OVERRIDE_RECEIPT_ROOT
    if not receipt_root.is_dir():
        return ()
    receipts: list[PushOverrideReceipt] = []
    for path in sorted(receipt_root.glob("*.md")):
        receipt = parse_push_override_receipt(path)
        if receipt is not None:
            receipts.append(receipt)
    return tuple(receipts)


def parse_push_override_receipt(path: Path) -> PushOverrideReceipt | None:
    """Parse one markdown PushOverrideReceipt file into typed fields."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    fields = {
        _normalize_markdown_field_name(match.group("label")): _clean_markdown_value(
            match.group("value")
        )
        for match in _MARKDOWN_FIELD_RE.finditer(text)
    }
    authorized_head_value = fields.get("authorized_head_sha", "")
    return PushOverrideReceipt(
        path=path,
        contract=fields.get("contract", ""),
        override_id=fields.get("override_id", ""),
        authorized_head_shas=tuple(_FULL_SHA_RE.findall(authorized_head_value)),
        approval_mode=fields.get("approval_mode", ""),
        approved_by=fields.get("approved_by") or fields.get("recorded_by", ""),
        override_reason=_markdown_section(text, "Override reason"),
        bypass_lifecycle_id=fields.get("bypass_lifecycle_id", ""),
        bypass_receipt_id=fields.get("bypass_receipt_id", ""),
        hmac_contract=fields.get("hmac_contract", ""),
        hmac_signature=fields.get("hmac_signature", ""),
    )


def _missing_push_override_receipt_fields(
    receipt: PushOverrideReceipt,
    *,
    authorization: PushAuthorizationRecord,
    active_lifecycles: tuple[BypassLifecycle, ...],
) -> tuple[str, ...]:
    missing: list[str] = []
    if receipt.contract != "PushOverrideReceipt":
        missing.append("contract")
    if not receipt.override_id:
        missing.append("override_id")
    if not receipt.authorized_head_shas:
        missing.append("authorized_head_sha")
    if receipt.approval_mode != "override_push":
        missing.append("approval_mode")
    if not receipt.approved_by:
        missing.append("approved_by")
    if not receipt.override_reason:
        missing.append("override_reason")
    if not receipt.bypass_lifecycle_id:
        missing.append("bypass_lifecycle_id")
    if not receipt.bypass_receipt_id:
        missing.append("bypass_receipt_id")
    if receipt.hmac_contract != PUSH_OVERRIDE_RECEIPT_HMAC_CONTRACT_ID:
        missing.append("hmac_contract")
    bypass_lifecycle = matching_active_push_override_bypass_lifecycle(
        bypass_lifecycle_id=receipt.bypass_lifecycle_id,
        bypass_receipt_id=receipt.bypass_receipt_id,
        active_lifecycles=active_lifecycles,
    )
    if bypass_lifecycle is None:
        missing.append("active_bypass_lifecycle")
    if bypass_lifecycle is None or not push_override_receipt_signature_matches(
        authorization=authorization,
        override_id=receipt.override_id,
        signature=receipt.hmac_signature,
        bypass_lifecycle=bypass_lifecycle,
    ):
        missing.append("hmac_signature")
    return tuple(missing)


def _normalize_markdown_field_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


def _clean_markdown_value(value: str) -> str:
    return value.replace("`", "").strip()


def _markdown_section(text: str, title: str) -> str:
    match = re.search(
        rf"^##\s+{re.escape(title)}\s*$\n(?P<body>.*?)(?=^##\s+|\Z)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    if match is None:
        return ""
    return match.group("body").strip()


def _safe_receipt_filename(value: str) -> str:
    token = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip()).strip("._-")
    return token or "override-push"


def _same_commit(left: str, right: str) -> bool:
    left = str(left or "").strip().lower()
    right = str(right or "").strip().lower()
    return bool(
        left
        and right
        and len(left) == 40
        and len(right) == 40
        and left == right
    )


__all__ = [
    "PUSH_OVERRIDE_RECEIPT_ROOT",
    "PUSH_OVERRIDE_RECEIPT_HMAC_CONTRACT_ID",
    "PushOverrideReceipt",
    "ensure_push_override_receipt",
    "load_push_override_receipts",
    "parse_push_override_receipt",
    "push_override_receipt_violation",
]
