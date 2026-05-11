"""Typed receipt for ground-truth probe runs before architecture design."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from ..time_utils import utc_timestamp
from .state_store_authority import append_json_mapping

GROUND_TRUTH_PROBE_RUN_RECEIPT_CONTRACT_ID = "GroundTruthProbeRunReceipt"
GROUND_TRUTH_PROBE_RUN_RECEIPT_SCHEMA_VERSION = 1
DEFAULT_GROUND_TRUTH_RECEIPT_REL = Path("dev/state/ground_truth_probe_receipts.jsonl")

_TRIGGER_PATH_PREFIXES = (
    "dev/scripts/devctl/platform/runtime_state_contract_rows",
    "dev/scripts/devctl/runtime/",
    "dev/scripts/devctl/commands/",
)
_TRIGGER_CONTENT_MARKERS = (
    "ContractSpec(",
    "contract_id",
    "proof_channel",
    "source_proof_channel",
    "physical_confirmation_method",
    "RuntimeTruthSnapshot",
    "GroundTruthProbeRunReceipt",
)
_EXCLUDED_PREFIXES = (
    "dev/scripts/devctl/tests/",
    "dev/scripts/checks/",
    "dev/reports/",
)
_EXCLUDED_EXACT = {
    DEFAULT_GROUND_TRUTH_RECEIPT_REL.as_posix(),
}


@dataclass(frozen=True, slots=True)
class GroundTruthProbeRunReceipt:
    """Evidence that a design pass looked at upstream truth first."""

    schema_version: int = GROUND_TRUTH_PROBE_RUN_RECEIPT_SCHEMA_VERSION
    contract_id: str = GROUND_TRUTH_PROBE_RUN_RECEIPT_CONTRACT_ID
    created_at_utc: str = ""
    base_ref: str = ""
    head_ref: str = "HEAD"
    changed_paths_digest: str = ""
    trigger_kind: str = "authority_or_proof_surface"
    trigger_paths: tuple[str, ...] = ()
    design_ids: tuple[str, ...] = ()
    required_probe_ids: tuple[str, ...] = ()
    observed_probe_ids: tuple[str, ...] = ()
    probe_report_path: str = ""
    probe_report_sha256: str = ""
    verdict: str = "missing"
    warnings: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["trigger_paths"] = list(self.trigger_paths)
        payload["design_ids"] = list(self.design_ids)
        payload["required_probe_ids"] = list(self.required_probe_ids)
        payload["observed_probe_ids"] = list(self.observed_probe_ids)
        payload["warnings"] = list(self.warnings)
        return payload


@dataclass(frozen=True, slots=True)
class GroundTruthProbeRunInput:
    """Inputs used to construct one ground-truth probe receipt."""

    trigger_paths: tuple[str, ...] = ()
    design_ids: tuple[str, ...] = ()
    required_probe_ids: tuple[str, ...] = ()
    observed_probe_ids: tuple[str, ...] = ()
    base_ref: str = ""
    head_ref: str = "HEAD"
    probe_report_path: str = ""
    probe_report_sha256: str = ""
    warnings: tuple[str, ...] = ()


def build_ground_truth_probe_receipt(
    inputs: GroundTruthProbeRunInput,
) -> GroundTruthProbeRunReceipt:
    """Build a deterministic receipt over the trigger path set."""
    triggers = _normalized_unique(inputs.trigger_paths)
    required = _normalized_unique(inputs.required_probe_ids)
    observed = _normalized_unique(inputs.observed_probe_ids)
    missing = tuple(item for item in required if item not in set(observed))
    receipt_warnings = [str(item) for item in inputs.warnings if str(item).strip()]
    receipt_warnings.extend(f"missing_probe:{item}" for item in missing)
    return GroundTruthProbeRunReceipt(
        created_at_utc=utc_timestamp(),
        base_ref=inputs.base_ref,
        head_ref=inputs.head_ref or "HEAD",
        changed_paths_digest=trigger_paths_digest(triggers),
        trigger_paths=triggers,
        design_ids=_normalized_unique(inputs.design_ids),
        required_probe_ids=required,
        observed_probe_ids=observed,
        probe_report_path=inputs.probe_report_path,
        probe_report_sha256=inputs.probe_report_sha256,
        verdict="satisfied" if triggers and not missing else "missing",
        warnings=tuple(receipt_warnings),
    )


def trigger_paths_digest(paths: Iterable[str]) -> str:
    """Return a stable digest for the ordered trigger path set."""
    normalized = "\n".join(_normalized_unique(paths))
    return "sha256:" + hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def append_ground_truth_probe_receipt(
    receipt: GroundTruthProbeRunReceipt,
    *,
    repo_root: Path,
    receipt_path: str | Path | None = None,
) -> Path:
    """Append one receipt row to the repo-local typed state ledger."""
    path = _receipt_path(repo_root, receipt_path)
    append_json_mapping(
        path,
        receipt.to_dict(),
        store_id="ground_truth_probe_receipts",
    )
    return path


def latest_ground_truth_probe_receipt(
    *,
    repo_root: Path,
    receipt_path: str | Path | None = None,
) -> GroundTruthProbeRunReceipt | None:
    """Read the latest well-formed receipt row from the typed state ledger."""
    path = _receipt_path(repo_root, receipt_path)
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    for line in reversed(lines):
        payload = _loads(line)
        if isinstance(payload, Mapping):
            receipt = ground_truth_probe_receipt_from_mapping(payload)
            if receipt is not None:
                return receipt
    return None


def ground_truth_probe_receipt_from_mapping(
    payload: Mapping[str, object],
) -> GroundTruthProbeRunReceipt | None:
    """Deserialize one receipt mapping."""
    if str(payload.get("contract_id") or "") != GROUND_TRUTH_PROBE_RUN_RECEIPT_CONTRACT_ID:
        return None
    return GroundTruthProbeRunReceipt(
        schema_version=_int(payload.get("schema_version"), default=1),
        contract_id=GROUND_TRUTH_PROBE_RUN_RECEIPT_CONTRACT_ID,
        created_at_utc=_text(payload.get("created_at_utc")),
        base_ref=_text(payload.get("base_ref")),
        head_ref=_text(payload.get("head_ref")) or "HEAD",
        changed_paths_digest=_text(payload.get("changed_paths_digest")),
        trigger_kind=_text(payload.get("trigger_kind"))
        or "authority_or_proof_surface",
        trigger_paths=_strings(payload.get("trigger_paths")),
        design_ids=_strings(payload.get("design_ids")),
        required_probe_ids=_strings(payload.get("required_probe_ids")),
        observed_probe_ids=_strings(payload.get("observed_probe_ids")),
        probe_report_path=_text(payload.get("probe_report_path")),
        probe_report_sha256=_text(payload.get("probe_report_sha256")),
        verdict=_text(payload.get("verdict")) or "missing",
        warnings=_strings(payload.get("warnings")),
    )


def detect_ground_truth_trigger_paths(
    *,
    repo_root: Path,
    changed_paths: Iterable[str],
) -> tuple[str, ...]:
    """Return changed paths that introduce authority/proof design surfaces."""
    triggers: list[str] = []
    for raw_path in _normalized_unique(changed_paths):
        if _excluded(raw_path) or not _candidate_path(raw_path):
            continue
        path = repo_root / raw_path
        if not path.exists() or path.suffix != ".py":
            continue
        text = _read_text(path)
        if any(marker in text for marker in _TRIGGER_CONTENT_MARKERS):
            triggers.append(raw_path)
    return tuple(triggers)


def _receipt_path(repo_root: Path, receipt_path: str | Path | None) -> Path:
    path = Path(receipt_path) if receipt_path else DEFAULT_GROUND_TRUTH_RECEIPT_REL
    if path.is_absolute():
        return path
    return repo_root / path


def _candidate_path(path: str) -> bool:
    return any(path.startswith(prefix) for prefix in _TRIGGER_PATH_PREFIXES)


def _excluded(path: str) -> bool:
    return path in _EXCLUDED_EXACT or any(path.startswith(prefix) for prefix in _EXCLUDED_PREFIXES)


def _normalized_unique(values: Iterable[str]) -> tuple[str, ...]:
    rows: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text and text not in rows:
            rows.append(text)
    return tuple(sorted(rows))


def _loads(line: str) -> object:
    try:
        return json.loads(line)
    except json.JSONDecodeError:
        return {}


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _strings(value: object) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return _normalized_unique(str(item) for item in value)


def _text(value: object) -> str:
    return str(value or "").strip()


def _int(value: object, *, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


__all__ = [
    "DEFAULT_GROUND_TRUTH_RECEIPT_REL",
    "GROUND_TRUTH_PROBE_RUN_RECEIPT_CONTRACT_ID",
    "GROUND_TRUTH_PROBE_RUN_RECEIPT_SCHEMA_VERSION",
    "GroundTruthProbeRunInput",
    "GroundTruthProbeRunReceipt",
    "append_ground_truth_probe_receipt",
    "build_ground_truth_probe_receipt",
    "detect_ground_truth_trigger_paths",
    "ground_truth_probe_receipt_from_mapping",
    "latest_ground_truth_probe_receipt",
    "trigger_paths_digest",
]
