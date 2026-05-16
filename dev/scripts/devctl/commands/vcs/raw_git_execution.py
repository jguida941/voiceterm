"""Execution preflight helpers for the raw-git command."""

from __future__ import annotations

import os
import subprocess
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ...common import resolve_repo_path
from ...runtime.bypass_lifecycle_models import BypassAuthorityScope
from ...runtime.bypass_lifecycle_registry import (
    active_bypass_lifecycle_for_receipt_id,
    active_bypass_lifecycles,
)
from ...runtime.raw_git_bypass_receipts import (
    DEFAULT_BYPASS_LIFECYCLE_STORE_REL,
    RawGitBypassAuthority,
    RawGitVerb,
    raw_git_authority_from_value,
)


@dataclass(frozen=True, slots=True)
class RawGitAuthorityPreflight:
    ok: bool
    bypass_authority: RawGitBypassAuthority
    bypass_lifecycle_store_path: Path
    git_env: Mapping[str, str] | None = None
    error: str = ""


def raw_git_authority_preflight(
    args: Any,
    *,
    repo_root: Path,
    verb: RawGitVerb,
) -> RawGitAuthorityPreflight:
    store_path = resolve_repo_path(
        getattr(args, "bypass_lifecycle_store_path", ""),
        DEFAULT_BYPASS_LIFECYCLE_STORE_REL,
        repo_root=repo_root,
    )
    authority = raw_git_authority_from_value(getattr(args, "authority", ""))
    try:
        _validate_lifecycle_backed_authority(args, verb=verb, authority=authority, store_path=store_path)
    except ValueError as exc:
        return RawGitAuthorityPreflight(False, authority, store_path, error=str(exc))
    git_env = (
        {"DEVCTL_GOVERNED_COMMIT": "1"}
        if verb is RawGitVerb.COMMIT
        and authority is RawGitBypassAuthority.BYPASS_LIFECYCLE_RECEIPT
        else None
    )
    return RawGitAuthorityPreflight(True, authority, store_path, git_env=git_env)


def subprocess_git_runner(
    repo_root: Path,
    *,
    result_factory: Callable[[int, str, str], object],
    extra_env: Mapping[str, str] | None = None,
) -> Callable[[tuple[str, ...], bool], object]:
    child_env = {**os.environ, **extra_env} if extra_env is not None else None

    def _run(args: tuple[str, ...], capture: bool) -> object:
        result = subprocess.run(
            ("git", *args),
            cwd=repo_root,
            text=True,
            capture_output=True,
            check=False,
            env=child_env,
        )
        return result_factory(result.returncode, result.stdout, result.stderr)

    return _run


def _validate_lifecycle_backed_authority(
    args: Any,
    *,
    verb: RawGitVerb,
    authority: RawGitBypassAuthority,
    store_path: Path,
) -> None:
    if authority is not RawGitBypassAuthority.BYPASS_LIFECYCLE_RECEIPT:
        return
    requested_ref = str(getattr(args, "bypass_lifecycle_id", "") or "").strip()
    if not requested_ref:
        raise ValueError("bypass_lifecycle_id required for bypass_lifecycle_receipt")
    required_scope = _required_bypass_scope(verb)
    lifecycle = active_bypass_lifecycle_for_receipt_id(
        requested_ref,
        store_path=store_path,
        required_scope=required_scope,
    )
    if lifecycle is not None:
        return
    for candidate in active_bypass_lifecycles(
        store_path=store_path,
        required_scope=required_scope,
    ):
        if candidate.lifecycle_id == requested_ref:
            return
    raise ValueError("bypass_lifecycle_id not active or not found")


def _required_bypass_scope(verb: RawGitVerb) -> BypassAuthorityScope:
    if verb is RawGitVerb.COMMIT:
        return BypassAuthorityScope.EDIT_AND_COMMIT
    return BypassAuthorityScope.EDIT_COMMIT_AND_PUSH
