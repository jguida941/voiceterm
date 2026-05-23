"""Support helpers for ``check_staging_source_ingested``."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path

try:
    from check_bootstrap import REPO_ROOT
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT

# ``ProofUtils.strings``/``sequence_of_mappings`` already exist in runtime and
# were duplicated here as ``@staticmethod`` helpers. Routing through the
# canonical runtime module removes the duplication while keeping the
# ``StagingSourceSupport`` class surface intact for existing callers.
from dev.scripts.devctl.runtime.current_row_proof_utils import ProofUtils as _ProofUtils


class StagingSourceSupport:
    """Typed state and source-file helpers for staging source ingestion checks."""

    @staticmethod
    def find_plan_row(path: Path, row_id: str) -> dict[str, object]:
        for row in StagingSourceSupport.iter_jsonl(path):
            if row.get("contract_id") == "PlanRow" and row.get("row_id") == row_id:
                return dict(row)
        return {}

    @staticmethod
    def find_snapshot(path: Path, *, row_id: str, source_hash: str) -> dict[str, object]:
        latest: dict[str, object] = {}
        for snapshot in StagingSourceSupport.iter_jsonl(path):
            if snapshot.get("contract_id") != "PlanSourceSnapshot":
                continue
            if str(snapshot.get("plan_row_id") or "") != row_id:
                continue
            if source_hash and source_hash not in {
                str(snapshot.get("source_hash") or ""),
                str(snapshot.get("body_hash") or ""),
            }:
                continue
            latest = dict(snapshot)
        return latest

    @staticmethod
    def find_receipt(
        path: Path,
        *,
        row_id: str,
        source_hash: str,
        snapshot_id: str,
    ) -> dict[str, object]:
        latest: dict[str, object] = {}
        for receipt in StagingSourceSupport.iter_jsonl(path):
            if receipt.get("contract_id") != "PlanIntentIngestionReceipt":
                continue
            if row_id not in set(StagingSourceSupport.strings(receipt.get("row_ids"))):
                continue
            if source_hash and source_hash not in {
                str(receipt.get("source_hash") or ""),
                str(receipt.get("canonical_source_hash") or ""),
            }:
                continue
            if snapshot_id and snapshot_id not in set(StagingSourceSupport.strings(receipt.get("source_snapshot_ids"))):
                continue
            if str(receipt.get("status") or "") != "accepted":
                continue
            latest = dict(receipt)
        return latest

    @staticmethod
    def row_source_hash(row: Mapping[str, object]) -> str:
        provenance = row.get("provenance")
        if isinstance(provenance, Mapping):
            text = str(provenance.get("source_hash") or "").strip()
            if text:
                return text
        return str(row.get("content_hash") or "").strip()

    @staticmethod
    def receipt_disposition(receipt: Mapping[str, object], row_id: str) -> str:
        for item in StagingSourceSupport.sequence_of_mappings(receipt.get("composition_disposition_matrix")):
            if item.get("row_id") == row_id:
                return str(item.get("disposition") or "")
        return ""

    @staticmethod
    def iter_jsonl(path: Path) -> Iterable[Mapping[str, object]]:
        if not path.exists():
            return ()

        def rows() -> Iterable[Mapping[str, object]]:
            for raw_line in path.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(payload, Mapping):
                    yield payload

        return rows()

    @staticmethod
    def file_hash(path: Path) -> str:
        try:
            data = path.read_bytes()
        except OSError:
            return ""
        return "sha256:" + hashlib.sha256(data).hexdigest()

    strings = staticmethod(_ProofUtils.strings)
    sequence_of_mappings = staticmethod(_ProofUtils.sequence_of_mappings)

    @staticmethod
    def repo_relative(path: Path) -> Path:
        try:
            return path.resolve().relative_to(REPO_ROOT)
        except (OSError, ValueError):
            return path

    @staticmethod
    def render_markdown(report: Mapping[str, object], command: str) -> str:
        lines = [
            f"# {command}",
            "",
            f"- ok: {report.get('ok')}",
            f"- source_path: `{report.get('source_path')}`",
            f"- source_hash: `{report.get('source_hash')}`",
            f"- row_id: `{report.get('row_id')}`",
            f"- source_snapshot_id: `{report.get('source_snapshot_id')}`",
            f"- ingestion_receipt_id: `{report.get('ingestion_receipt_id')}`",
            f"- disposition: `{report.get('disposition')}`",
            f"- failure_count: {report.get('failure_count')}",
        ]
        failures = report.get("failures")
        if isinstance(failures, Sequence) and not isinstance(failures, (str, bytes)):
            lines.extend(["", "## Failures", ""])
            for failure in failures:
                if isinstance(failure, Mapping):
                    lines.append(
                        f"- `{failure.get('reason')}`: {failure.get('detail')} "
                        f"Remediation: {failure.get('remediation')}"
                    )
        return "\n".join(lines)
