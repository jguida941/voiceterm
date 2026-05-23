"""Shared helpers for current-row projection command actions."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from ..config import REPO_ROOT
from ..runtime.current_row_proof_bundle import build_current_row_proof_bundle


def build_current_row_proof_report(args, *, row_id: str) -> dict[str, object]:
    """Shared ``_build_report`` body for current-row projection commands.

    Previously each of ``plan_execution_projection_receipt`` and
    ``plan_execution_projection_steps`` carried an identical 13-line
    ``_build_report`` clone. The shared definition removes the duplicate.
    """

    return build_current_row_proof_bundle(
        row_id=row_id,
        plan_index_path=Path(args.plan_index_path),
        snapshots_path=Path(args.snapshots_path),
        ingestion_receipts_path=Path(args.ingestion_receipts_path),
        closure_receipts_path=Path(args.closure_receipts_path),
        feature_proof_dir=Path(args.feature_proof_dir),
        guard_output_paths=(Path(args.guard_output),),
        dogfood_output_paths=(Path(args.dogfood_output),),
        collaboration_evidence_paths=(Path(args.collaboration_evidence),),
        final_gate_paths=(Path(args.final_gate_output),),
    )


class ProjectionCommandSupport:
    """Small filesystem, JSON, and receipt helpers for projection commands."""

    @staticmethod
    def json_payload(text: str) -> dict[str, object]:
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            return {"raw_stdout": text}
        if isinstance(payload, dict):
            return payload
        return {"raw_stdout": text}

    @staticmethod
    def guard_ok(payload: dict[str, object], returncode: int) -> bool:
        ok = payload.get("ok")
        if isinstance(ok, bool):
            return ok
        return returncode == 0

    @classmethod
    def receipt_id(
        cls,
        row_id: str,
        guard_id: str,
        timestamp: str,
        stdout: str,
        stderr: str,
    ) -> str:
        digest = cls.receipt_token(row_id, guard_id, timestamp, stdout, stderr)
        return f"guard-run-{guard_id}-{digest}"

    @staticmethod
    def receipt_token(*parts: str) -> str:
        return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()[:16]

    @staticmethod
    def append_jsonl(path: Path, payload: dict[str, object]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n")

    @staticmethod
    def utc_timestamp() -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    @staticmethod
    def repo_relative(path: Path) -> Path:
        try:
            return path.resolve().relative_to(REPO_ROOT)
        except (OSError, ValueError):
            return path

    @staticmethod
    def path_token(value: str) -> str:
        token = "".join(char for char in value if char.isalnum() or char in "._-")[:80]
        return token or "unknown"
