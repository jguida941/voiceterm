"""Shared locked writer helpers for governed JSON/JSONL state stores."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import secrets
import tempfile
from collections.abc import Callable, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class StateStoreWriteResult:
    """Bounded result for one governed store write."""

    store_id: str
    path: str
    write_mode: str
    lock_path: str
    record_count: int = 0
    byte_offset: int = 0
    bytes_written: int = 0
    replaced: bool = False

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class StateStoreAuthorityError(ValueError):
    """Base error for governed store failures."""


class StateStoreCorruptionError(StateStoreAuthorityError):
    """Raised when a governed store contains malformed rows."""


def append_json_mapping(
    path: Path,
    payload: Mapping[str, object],
    *,
    store_id: str = "",
    serializer: Callable[[Mapping[str, object]], str] | None = None,
) -> StateStoreWriteResult:
    """Append one JSON object row under a shared exclusive lock."""
    result = append_json_mappings(
        path,
        (payload,),
        store_id=store_id,
        serializer=serializer,
    )
    return result


def append_json_mappings(
    path: Path,
    payloads: Sequence[Mapping[str, object]],
    *,
    store_id: str = "",
    serializer: Callable[[Mapping[str, object]], str] | None = None,
) -> StateStoreWriteResult:
    """Append one or more JSON object rows under a shared exclusive lock."""
    rows = tuple(_mapping_copy(item) for item in payloads)
    if not rows:
        return StateStoreWriteResult(
            store_id=store_id or path.name,
            path=str(path),
            write_mode="append",
            lock_path=str(_lock_path(path)),
        )
    serializer_fn = serializer or json_line
    rendered_rows = [serializer_fn(row) for row in rows]
    content = "".join(f"{line}\n" for line in rendered_rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with state_store_lock(path) as lock_path:
        byte_offset = path.stat().st_size if path.exists() else 0
        with path.open("a", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            _fsync_file(handle.fileno())
        _fsync_directory(path.parent)
        return StateStoreWriteResult(
            store_id=store_id or path.name,
            path=str(path),
            write_mode="append",
            lock_path=str(lock_path),
            record_count=len(rows),
            byte_offset=byte_offset,
            bytes_written=len(content.encode("utf-8")),
            replaced=False,
        )


def replace_json_mappings(
    path: Path,
    payloads: Sequence[Mapping[str, object]],
    *,
    store_id: str = "",
    serializer: Callable[[Mapping[str, object]], str] | None = None,
) -> StateStoreWriteResult:
    """Atomically replace a governed JSONL/NDJSON file under a shared lock."""
    rows = tuple(_mapping_copy(item) for item in payloads)
    serializer_fn = serializer or json_line
    content = "".join(f"{serializer_fn(row)}\n" for row in rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with state_store_lock(path) as lock_path:
        _atomic_replace_text(path, content)
        return StateStoreWriteResult(
            store_id=store_id or path.name,
            path=str(path),
            write_mode="replace",
            lock_path=str(lock_path),
            record_count=len(rows),
            byte_offset=0,
            bytes_written=len(content.encode("utf-8")),
            replaced=True,
        )


def transform_json_mappings(
    path: Path,
    *,
    transform: Callable[
        [tuple[dict[str, Any], ...]],
        Sequence[Mapping[str, object]],
    ],
    store_id: str = "",
    serializer: Callable[[Mapping[str, object]], str] | None = None,
) -> tuple[dict[str, Any], ...]:
    """Apply one locked read-modify-write transform to a governed JSONL store."""
    serializer_fn = serializer or json_line
    path.parent.mkdir(parents=True, exist_ok=True)
    with state_store_lock(path):
        current = read_json_mappings_strict(path)
        next_rows = tuple(_mapping_copy(item) for item in transform(current))
        content = "".join(f"{serializer_fn(row)}\n" for row in next_rows)
        _atomic_replace_text(path, content)
    return next_rows


def read_json_mappings_strict(path: Path) -> tuple[dict[str, Any], ...]:
    """Read JSON object rows and fail closed on malformed governed data."""
    if not path.exists():
        return ()
    rows: list[dict[str, Any]] = []
    for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise StateStoreCorruptionError(
                f"{path}: line {index}: invalid JSON object: {exc}"
            ) from exc
        if not isinstance(payload, dict):
            raise StateStoreCorruptionError(
                f"{path}: line {index}: expected top-level JSON object"
            )
        rows.append(payload)
    return tuple(rows)


def json_line(
    payload: Mapping[str, object],
    *,
    compact: bool = False,
) -> str:
    """Serialize one JSON object row with stable key ordering."""
    if compact:
        return json.dumps(dict(payload), sort_keys=True, separators=(",", ":"))
    return json.dumps(dict(payload), sort_keys=True)


@contextmanager
def state_store_lock(path: Path):
    """Acquire a stable sidecar lock for one governed store path."""
    lock_path = _lock_path(path)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield lock_path
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def _mapping_copy(payload: Mapping[str, object]) -> dict[str, object]:
    if not isinstance(payload, Mapping):
        raise TypeError(f"expected mapping payload, got {type(payload)!r}")
    return dict(payload)


def _lock_path(path: Path) -> Path:
    digest = hashlib.sha256(str(path.resolve()).encode("utf-8")).hexdigest()
    root = Path(tempfile.gettempdir()) / "devctl-state-store-locks"
    return root / f"{digest}.lock"


def _atomic_replace_text(path: Path, content: str, *, encoding: str = "utf-8") -> None:
    parent = path.parent
    parent.mkdir(parents=True, exist_ok=True)
    tmp_name = f"{path.name}.tmp.{os.getpid()}.{secrets.token_hex(4)}"
    tmp_path = parent / tmp_name
    try:
        with tmp_path.open("w", encoding=encoding) as handle:
            handle.write(content)
            handle.flush()
            _fsync_file(handle.fileno())
        os.replace(tmp_path, path)
        _fsync_directory(parent)
    except Exception:
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise


def _fsync_file(fd: int) -> None:
    try:
        os.fsync(fd)
    except OSError:
        pass


def _fsync_directory(path: Path) -> None:
    try:
        fd = os.open(path, os.O_RDONLY)
    except OSError:
        return
    try:
        _fsync_file(fd)
    finally:
        os.close(fd)


__all__ = [
    "StateStoreAuthorityError",
    "StateStoreCorruptionError",
    "StateStoreWriteResult",
    "append_json_mapping",
    "append_json_mappings",
    "json_line",
    "read_json_mappings_strict",
    "replace_json_mappings",
    "state_store_lock",
    "transform_json_mappings",
]
