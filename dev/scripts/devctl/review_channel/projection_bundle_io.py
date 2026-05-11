"""I/O helpers for review-channel projection bundles."""

from __future__ import annotations

import os
import secrets
from collections.abc import Mapping
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class _ProjectionBundleLockState:
    """In-process reentrant lock depth for projection bundle writes."""

    depth: int = 0

    def is_nested(self) -> bool:
        return self.depth > 0

    def enter(self) -> None:
        self.depth += 1

    def exit(self) -> None:
        self.depth -= 1


_PROJECTION_BUNDLE_LOCK_STATE = _ProjectionBundleLockState()


@dataclass(frozen=True)
class ReviewChannelProjectionPaths:
    """Paths written for the latest review projections."""

    root_dir: str
    review_state_path: str
    compact_path: str
    full_path: str
    actions_path: str
    trace_path: str
    latest_markdown_path: str
    agent_registry_path: str
    commit_pipeline_path: str = ""


@dataclass(frozen=True)
class ReviewChannelProjectionBundleContents:
    """Prepared projection file contents for one review-state snapshot."""

    review_state_json: str
    compact_json: str
    full_json: str
    actions_json: str
    trace_text: str
    latest_markdown: str
    agent_registry_json: str
    commit_pipeline_json: str


def projection_paths_for_root(output_root: Path) -> ReviewChannelProjectionPaths:
    """Return the canonical projection paths without writing any files."""
    registry_dir = output_root / "registry"
    return ReviewChannelProjectionPaths(
        root_dir=str(output_root),
        review_state_path=str(output_root / "review_state.json"),
        compact_path=str(output_root / "compact.json"),
        full_path=str(output_root / "full.json"),
        actions_path=str(output_root / "actions.json"),
        trace_path=str(output_root / "trace.ndjson"),
        latest_markdown_path=str(output_root / "latest.md"),
        agent_registry_path=str(registry_dir / "agents.json"),
        commit_pipeline_path=str(output_root / "commit_pipeline.json"),
    )


def canonical_projection_root_for_status_root(output_root: Path) -> Path:
    """Return the canonical review-state projection root for a status root."""
    if output_root.name == "latest" and output_root.parent.name != "projections":
        return output_root.parent / "projections" / output_root.name
    return output_root


def projection_paths_to_dict(
    paths: ReviewChannelProjectionPaths | Mapping[str, object] | None,
) -> dict[str, str] | None:
    """Convert projection paths into a report-friendly dict."""
    if paths is None:
        return None
    if isinstance(paths, Mapping):
        return {str(key): str(value) for key, value in paths.items()}
    return asdict(paths)


@contextmanager
def projection_bundle_lock(*roots: Path):
    """Serialize sibling projection-root readers and writers."""
    lock_state = _PROJECTION_BUNDLE_LOCK_STATE
    if lock_state.is_nested():
        yield
        return
    lock_dir = _projection_bundle_lock_dir(tuple(roots))
    lock_dir.mkdir(parents=True, exist_ok=True)
    lock_path = lock_dir / ".projection_bundle.lock"
    try:
        import fcntl
    except ImportError:
        yield
        return
    with open(lock_path, "a", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        lock_state.enter()
        try:
            yield
        finally:
            lock_state.exit()
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def write_prepared_projection_bundle(
    *,
    output_root: Path,
    contents: ReviewChannelProjectionBundleContents,
) -> ReviewChannelProjectionPaths:
    """Atomically publish prepared projection contents into one root."""
    paths = projection_paths_for_root(output_root)
    review_state_path = Path(paths.review_state_path)
    compact_path = Path(paths.compact_path)
    full_path = Path(paths.full_path)
    actions_path = Path(paths.actions_path)
    trace_path = Path(paths.trace_path)
    latest_markdown_path = Path(paths.latest_markdown_path)
    agent_registry_path = Path(paths.agent_registry_path)
    commit_pipeline_path = Path(paths.commit_pipeline_path)

    # Per Codex rev_pkt_2406/2409/2413: publish each bundle file atomically.
    # The earlier code wrote review_state.json first then compact/full/etc.
    # sequentially with no atomicity, so any reader entering between writes
    # observed mismatched snapshot_id/zref between siblings.
    atomic_write_text(review_state_path, contents.review_state_json)
    atomic_write_text(compact_path, contents.compact_json)
    atomic_write_text(full_path, contents.full_json)
    atomic_write_text(actions_path, contents.actions_json)
    atomic_write_text(trace_path, contents.trace_text)
    atomic_write_text(latest_markdown_path, contents.latest_markdown)
    atomic_write_text(agent_registry_path, contents.agent_registry_json)
    atomic_write_text(commit_pipeline_path, contents.commit_pipeline_json)

    return paths


def atomic_write_text(path: Path, content: str, *, encoding: str = "utf-8") -> None:
    """Atomically replace ``path`` with ``content``."""
    parent = path.parent
    parent.mkdir(parents=True, exist_ok=True)
    tmp_name = f"{path.name}.tmp.{os.getpid()}.{secrets.token_hex(4)}"
    tmp_path = parent / tmp_name
    try:
        with open(tmp_path, "w", encoding=encoding) as fh:
            fh.write(content)
            fh.flush()
            try:
                os.fsync(fh.fileno())
            except OSError:
                # fsync may not be supported on every fs; rename atomicity still holds.
                pass
        os.replace(tmp_path, path)
    # broad-except: allow reason=atomic projection write cleanup must preserve original write failure fallback=remove temp file then re-raise
    except Exception:
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise


def _projection_bundle_lock_dir(roots: tuple[Path, ...]) -> Path:
    resolved = tuple(root.resolve() for root in roots if root is not None)
    if not resolved:
        return Path(".").resolve()
    common = Path(os.path.commonpath([str(root) for root in resolved]))
    while common.name in {"latest", "projections"} and common.parent != common:
        common = common.parent
    return common


__all__ = [
    "ReviewChannelProjectionBundleContents",
    "ReviewChannelProjectionPaths",
    "atomic_write_text",
    "canonical_projection_root_for_status_root",
    "projection_bundle_lock",
    "projection_paths_for_root",
    "projection_paths_to_dict",
    "write_prepared_projection_bundle",
]
