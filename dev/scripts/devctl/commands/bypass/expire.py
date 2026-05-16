"""`devctl bypass expire` command action."""

from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ...common import (
    add_standard_output_arguments,
    display_path,
    resolve_repo_path,
)
from ...config import REPO_ROOT
from ...runtime.lifetime_bypass_mode import (
    DEFAULT_BYPASS_LIFECYCLE_STORE_REL,
    BypassAuthorityScope,
    BypassExpirySource,
    BypassLifecycle,
    active_bypass_lifecycle_for_receipt_id,
    active_bypass_lifecycles,
    expire_bypass_lifecycle,
    load_bypass_lifecycles,
)


@dataclass(frozen=True, slots=True)
class BypassExpireReport:
    command: str = "bypass"
    action: str = "expire"
    ok: bool = False
    lifecycle_id: str = ""
    receipt_id: str = ""
    state: str = ""
    source: str = ""
    expired_at_utc: str = ""
    store_path: str = ""
    write_result: Mapping[str, object] | None = None
    error: str = ""

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        if self.write_result is None:
            payload.pop("write_result", None)
        return payload


def add_expire_parser(action_sub: Any) -> None:
    expire = action_sub.add_parser(
        "expire",
        help="Expire or revoke one active BypassLifecycle receipt",
    )
    expire.add_argument(
        "--lifecycle-id",
        default="",
        help="Active BypassLifecycle id to expire.",
    )
    expire.add_argument(
        "--receipt-id",
        default="",
        help="Active BypassReceipt id to expire when lifecycle id is omitted.",
    )
    expire.add_argument(
        "--source",
        choices=tuple(source.value for source in BypassExpirySource),
        required=True,
        help="Typed expiry source.",
    )
    expire.add_argument(
        "--reason",
        required=True,
        help="Typed reason recorded on the BypassExpiry receipt.",
    )
    expire.add_argument(
        "--target-role",
        default="implementer",
        help="Target role for active lifecycle lookup.",
    )
    expire.add_argument(
        "--evidence-ref",
        action="append",
        default=None,
        help="Repeatable evidence ref attached to the expiry receipt.",
    )
    expire.add_argument(
        "--store-path",
        default=str(DEFAULT_BYPASS_LIFECYCLE_STORE_REL),
        help="Bypass lifecycle JSONL store path.",
    )
    add_standard_output_arguments(
        expire,
        format_choices=("json", "md"),
        default_format="json",
    )


def expire_action(args: Any) -> tuple[dict[str, object], int]:
    """Expire one active BypassLifecycle row by lifecycle id or receipt id."""
    store_path = resolve_repo_path(
        getattr(args, "store_path", ""),
        DEFAULT_BYPASS_LIFECYCLE_STORE_REL,
        repo_root=REPO_ROOT,
    )
    lifecycle_id = str(getattr(args, "lifecycle_id", "") or "").strip()
    receipt_id = str(getattr(args, "receipt_id", "") or "").strip()
    lifecycle = _resolve_active_lifecycle(
        lifecycle_id=lifecycle_id,
        receipt_id=receipt_id,
        store_path=store_path,
        target_role=str(getattr(args, "target_role", "") or "").strip(),
    )
    if lifecycle is None:
        return (
            BypassExpireReport(
                error="active_bypass_lifecycle_not_found",
                lifecycle_id=lifecycle_id,
                receipt_id=receipt_id,
                store_path=display_path(store_path),
            ).to_dict(),
            1,
        )
    source = BypassExpirySource(str(getattr(args, "source", "") or "").strip())
    reason = str(getattr(args, "reason", "") or "").strip()
    evidence_refs = tuple(
        str(ref).strip()
        for ref in getattr(args, "evidence_ref", ()) or ()
        if str(ref).strip()
    )
    updated = expire_bypass_lifecycle(
        lifecycle,
        expired_at_utc=_now_utc(),
        reason=reason,
        source=source,
        evidence_refs=evidence_refs,
    )
    write_result = _rewrite_lifecycle_store(store_path, updated)
    return (
        BypassExpireReport(
            ok=True,
            lifecycle_id=updated.lifecycle_id,
            receipt_id=updated.expiry.receipt_id if updated.expiry else "",
            state=updated.state.value,
            source=source.value,
            expired_at_utc=updated.expiry.expired_at_utc if updated.expiry else "",
            store_path=display_path(store_path),
            write_result=write_result,
        ).to_dict(),
        0,
    )


def _resolve_active_lifecycle(
    *,
    lifecycle_id: str,
    receipt_id: str,
    store_path: Path,
    target_role: str,
) -> BypassLifecycle | None:
    if lifecycle_id:
        for lifecycle in active_bypass_lifecycles(
            store_path=store_path,
            target_role=target_role,
            required_scope=BypassAuthorityScope.EDIT_ONLY,
        ):
            if lifecycle.lifecycle_id == lifecycle_id:
                return lifecycle
        return None
    return active_bypass_lifecycle_for_receipt_id(
        receipt_id,
        store_path=store_path,
        target_role=target_role,
        required_scope=BypassAuthorityScope.EDIT_ONLY,
    )


def _rewrite_lifecycle_store(
    store_path: Path,
    updated: BypassLifecycle,
) -> dict[str, object]:
    rows = load_bypass_lifecycles(store_path)
    replacement_rows: list[BypassLifecycle] = []
    replaced = False
    for lifecycle in rows:
        if lifecycle.lifecycle_id == updated.lifecycle_id:
            replacement_rows.append(updated)
            replaced = True
        else:
            replacement_rows.append(lifecycle)
    if not replaced:
        raise ValueError(f"bypass_lifecycle_not_found: {updated.lifecycle_id}")

    store_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=store_path.parent,
        delete=False,
    ) as handle:
        for lifecycle in replacement_rows:
            handle.write(json.dumps(lifecycle.to_dict(), sort_keys=True) + "\n")
        tmp_name = handle.name
    os.replace(tmp_name, store_path)
    return {"replaced": True, "row_count": len(replacement_rows)}


def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


__all__ = ["add_expire_parser", "expire_action"]
