"""Low-level helpers for current-row proof readers."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path

from dev.scripts.checks.check_bootstrap import REPO_ROOT


class ProofUtils:
    """Shared data-shaping helpers used by the current-row proof modules."""

    @staticmethod
    def iter_jsonish_many(paths: Sequence[Path]) -> Iterable[Mapping[str, object]]:
        for path in paths:
            yield from ProofUtils.iter_jsonish(path)

    @staticmethod
    def iter_jsonish(path: Path) -> Iterable[Mapping[str, object]]:
        if not path.exists():
            return ()

        def rows() -> Iterable[Mapping[str, object]]:
            if path.suffix in {".jsonl", ".ndjson"}:
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
                return
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                return
            if isinstance(payload, Mapping):
                yield payload
            elif isinstance(payload, list):
                for item in payload:
                    if isinstance(item, Mapping):
                        yield item

        return rows()

    @staticmethod
    def nested_mappings(payload: Mapping[str, object]) -> Iterable[Mapping[str, object]]:
        for value in payload.values():
            if isinstance(value, Mapping):
                yield value
                yield from ProofUtils.nested_mappings(value)
            elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
                for item in value:
                    if isinstance(item, Mapping):
                        yield item
                        yield from ProofUtils.nested_mappings(item)

    @staticmethod
    def strings(value: object) -> Iterable[str]:
        if isinstance(value, str):
            if value:
                yield value
            return
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            for item in value:
                text = str(item).strip()
                if text:
                    yield text

    @staticmethod
    def sequence_of_mappings(value: object) -> Iterable[Mapping[str, object]]:
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            for item in value:
                if isinstance(item, Mapping):
                    yield item

    @staticmethod
    def last_prefixed(values: Sequence[str], prefix: str) -> str:
        matched = [value.removeprefix(prefix) for value in values if value.startswith(prefix)]
        return matched[-1] if matched else ""

    @staticmethod
    def nested(payload: Mapping[str, object], keys: Sequence[str]) -> object:
        current: object = payload
        for key in keys:
            if not isinstance(current, Mapping):
                return ""
            current = current.get(key)
        return current

    @staticmethod
    def first_text(payload: Mapping[str, object], keys: Sequence[str]) -> str:
        for key in keys:
            text = str(payload.get(key) or "").strip()
            if text:
                return text
        return ""

    @staticmethod
    def first_nested_text(payloads: Sequence[Mapping[str, object]], keys: Sequence[str]) -> str:
        for payload in payloads:
            text = ProofUtils.first_text(payload, keys)
            if text:
                return text
        return ""

    @staticmethod
    def timestamp_values(payload: Mapping[str, object]) -> Iterable[str]:
        for key, value in payload.items():
            if "timestamp" in key or key.endswith("_at_utc") or key in {"recorded_at_utc", "captured_at_utc"}:
                text = str(value or "").strip()
                if text:
                    yield text
            if isinstance(value, Mapping):
                yield from ProofUtils.timestamp_values(value)
            elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
                for item in value:
                    if isinstance(item, Mapping):
                        yield from ProofUtils.timestamp_values(item)

    @staticmethod
    def last_updated_timestamp(*objects: object) -> str:
        timestamps: list[str] = []
        for obj in objects:
            if isinstance(obj, Mapping):
                timestamps.extend(ProofUtils.timestamp_values(obj))
            elif isinstance(obj, Sequence) and not isinstance(obj, (str, bytes)):
                for item in obj:
                    if isinstance(item, Mapping):
                        timestamps.extend(ProofUtils.timestamp_values(item))
        return sorted(timestamps)[-1] if timestamps else ""

    @staticmethod
    def source_hash(
        plan_row: Mapping[str, object],
        snapshot: Mapping[str, object],
        ingestion_receipt: Mapping[str, object],
    ) -> str:
        for value in (
            snapshot.get("source_hash"),
            snapshot.get("body_hash"),
            ingestion_receipt.get("source_hash"),
            ingestion_receipt.get("canonical_source_hash"),
            plan_row.get("content_hash"),
            ProofUtils.nested(plan_row, ("provenance", "source_hash")),
        ):
            text = str(value or "").strip()
            if text:
                return text
        return ""

    @staticmethod
    def payload_refs_row(payload: Mapping[str, object], row_id: str) -> bool:
        return row_id in json.dumps(payload, sort_keys=True, default=str)

    @staticmethod
    def guard_command(guard_id: str) -> str:
        return f"python3 dev/scripts/checks/{guard_id}.py --format json"

    @staticmethod
    def truthy(value: object) -> bool:
        if isinstance(value, bool):
            return value
        return str(value or "").strip().lower() in {"1", "true", "yes", "ok", "passed", "green"}

    @staticmethod
    def status(value: object) -> str:
        if isinstance(value, Mapping):
            return str(value.get("status") or "")
        return ""

    @staticmethod
    def cell(value: object) -> str:
        return " ".join(str(value or "").split()).replace("|", "\\|")

    @staticmethod
    def sha256_text(text: str) -> str:
        return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()

    @staticmethod
    def repo_relative(path: Path) -> Path:
        try:
            return path.resolve().relative_to(REPO_ROOT)
        except (OSError, ValueError):
            return path
