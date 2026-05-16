"""Report and proof helpers for ``devctl bypass expire``."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path

from ...common import display_path
from ...runtime.lifetime_bypass_mode import BypassLifecycle, load_bypass_lifecycles


@dataclass(frozen=True, slots=True)
class BypassExpireReport:
    command: str = "bypass"
    action: str = "expire"
    ok: bool = False
    dry_run: bool = False
    lifecycle_id: str = ""
    receipt_id: str = ""
    state: str = ""
    source: str = ""
    expired_at_utc: str = ""
    store_path: str = ""
    inputs_scanned: tuple[str, ...] = ()
    assertions_evaluated: tuple[str, ...] = ()
    proof_evidence_refs: tuple[str, ...] = ()
    write_result: Mapping[str, object] | None = None
    error: str = ""

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["inputs_scanned"] = list(self.inputs_scanned)
        payload["assertions_evaluated"] = list(self.assertions_evaluated)
        payload["proof_evidence_refs"] = list(self.proof_evidence_refs)

        if self.write_result is None:
            payload.pop("write_result", None)
        return payload


def dry_run_write_result(
    store_path: Path,
    updated: BypassLifecycle,
) -> dict[str, object]:
    row_count = len(load_bypass_lifecycles(store_path))
    return {
        "dry_run": True,
        "would_replace": True,
        "lifecycle_id": updated.lifecycle_id,
        "row_count": row_count,
    }


def expire_inputs_scanned(
    *,
    store_path: Path,
    lifecycle_id: str,
    receipt_id: str,
    target_role: str,
) -> tuple[str, ...]:
    return tuple(
        item
        for item in (
            f"store_path:{display_path(store_path)}",
            f"lifecycle_id:{lifecycle_id}" if lifecycle_id else "",
            f"receipt_id:{receipt_id}" if receipt_id else "",
            f"target_role:{target_role}" if target_role else "",
        )
        if item
    )


def expire_assertions_evaluated(*, dry_run: bool) -> tuple[str, ...]:
    write_assertion = (
        "store_rewrite_skipped_dry_run"
        if dry_run
        else "store_rewrite_completed"
    )
    return (
        "active_lifecycle_resolved:true",
        "expiry_transition_constructed:true",
        write_assertion,
    )


def expire_proof_evidence_refs(
    *,
    lifecycle_id: str,
    receipt_id: str,
    evidence_refs: tuple[str, ...],
    store_path: Path,
) -> tuple[str, ...]:
    refs = [
        f"bypass_lifecycle:{lifecycle_id}" if lifecycle_id else "",
        f"bypass_receipt:{receipt_id}" if receipt_id else "",
        f"store:{display_path(store_path)}",
        *evidence_refs,
    ]
    return tuple(dict.fromkeys(ref for ref in refs if ref))


__all__ = [
    "BypassExpireReport",
    "dry_run_write_result",
    "expire_assertions_evaluated",
    "expire_inputs_scanned",
    "expire_proof_evidence_refs",
]
