"""Thin command wrappers for the bounded review-channel wait actions."""

from __future__ import annotations

from collections.abc import Callable, Mapping
import time
from pathlib import Path

from ..review_channel_command import RuntimePaths, _coerce_runtime_paths
from ._reviewer_wait import run_reviewer_wait_action as _run_reviewer_wait_action_impl
from ._wait import (
    ImplementerWaitDeps,
    run_implementer_wait_action as _run_implementer_wait_action_impl,
)
from ._wait_shared import WaitDeps


def run_implementer_wait_action(
    *,
    args,
    repo_root: Path,
    paths: RuntimePaths | Mapping[str, object],
    run_status_action_fn: Callable[..., tuple[dict[str, object], int]],
) -> tuple[dict, int]:
    """Run the Claude-side bounded wait loop over reviewer-owned state."""
    runtime_paths = _coerce_runtime_paths(paths)
    deps = ImplementerWaitDeps(
        run_status_action_fn=run_status_action_fn,
        read_bridge_text_fn=lambda path: path.read_text(encoding="utf-8"),
        monotonic_fn=lambda: time.monotonic(),
        sleep_fn=lambda seconds: time.sleep(seconds),
    )
    return _run_implementer_wait_action_impl(
        args=args,
        repo_root=repo_root,
        paths=runtime_paths,
        deps=deps,
    )


def run_reviewer_wait_action(
    *,
    args,
    repo_root: Path,
    paths: RuntimePaths | Mapping[str, object],
    run_status_action_fn: Callable[..., tuple[dict[str, object], int]],
) -> tuple[dict, int]:
    """Run the Codex-side bounded wait loop over reviewer-worker/current-session truth."""
    runtime_paths = _coerce_runtime_paths(paths)
    deps = WaitDeps(
        run_status_action_fn=run_status_action_fn,
        read_bridge_text_fn=lambda path: path.read_text(encoding="utf-8"),
        monotonic_fn=lambda: time.monotonic(),
        sleep_fn=lambda seconds: time.sleep(seconds),
    )
    return _run_reviewer_wait_action_impl(
        args=args,
        repo_root=repo_root,
        paths=runtime_paths,
        deps=deps,
    )
