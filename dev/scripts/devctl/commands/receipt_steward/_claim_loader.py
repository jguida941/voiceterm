"""Shared loader for the latest active ReceiptStewardScopeClaim.

CLI handlers in this package read the typed claim store
(`dev/state/receipt_steward_claims.jsonl`) before performing an
audit. The audit commands fail closed when no active claim exists
for the requesting actor session id; `--allow-no-claim` is reserved
for the dogfood/test paths that exercise the substrate without
seeding a claim first.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ...common import resolve_repo_path
from ...config import REPO_ROOT
from ...runtime.receipt_steward_scope_claim import (
    DEFAULT_RECEIPT_STEWARD_CLAIM_STORE_REL,
    ReceiptStewardScopeClaim,
    claim_is_active,
)


def load_active_claim_for_audit(
    args: Any,
    *,
    required: bool = True,
) -> tuple[ReceiptStewardScopeClaim | None, str | None]:
    """Return the latest active claim for the requesting actor session.

    Returns ``(claim, None)`` on success, ``(None, error_code)`` when
    no active claim exists. When ``required`` is False the caller is
    expected to honor `--allow-no-claim` semantics; we still return
    the claim if one is found, so dogfood-without-claim still surfaces
    the claim id when present.
    """
    store_path = resolve_repo_path(
        getattr(args, "store_path", "") or str(DEFAULT_RECEIPT_STEWARD_CLAIM_STORE_REL),
        DEFAULT_RECEIPT_STEWARD_CLAIM_STORE_REL,
        repo_root=REPO_ROOT,
    )
    actor_session = str(getattr(args, "actor_session_id", "") or "").strip()
    if not store_path.exists():
        return None, ("active_claim_not_found" if required else None)
    try:
        text = store_path.read_text(encoding="utf-8")
    except OSError:
        return None, ("active_claim_store_unreadable" if required else None)

    latest: ReceiptStewardScopeClaim | None = None
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        candidate = row.get("claim") if isinstance(row, dict) else None
        if not isinstance(candidate, dict):
            continue
        parsed = ReceiptStewardScopeClaim.from_mapping(candidate)
        if actor_session and parsed.actor_session_id != actor_session:
            continue
        latest = parsed

    if latest is None:
        return None, ("active_claim_not_found" if required else None)
    if not claim_is_active(latest):
        return None, ("active_claim_expired" if required else None)
    return latest, None


__all__ = ["load_active_claim_for_audit"]
