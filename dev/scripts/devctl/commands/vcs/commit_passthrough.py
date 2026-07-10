"""Passthrough parsing helpers for the governed commit command."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CommitPassthrough:
    """Supported passthrough flags for the governed commit path."""

    allow_empty: bool = False
    no_edit: bool = False
    unsupported: tuple[str, ...] = ()


def parse_passthrough(args) -> CommitPassthrough:
    """Normalize supported passthrough flags and reject the rest."""
    allow_empty = False
    no_edit = False
    unsupported: list[str] = []
    for value in getattr(args, "passthrough", None) or ():
        flag = str(value or "").strip()
        if not flag:
            continue
        if flag == "--allow-empty":
            allow_empty = True
            continue
        if flag == "--no-edit":
            no_edit = True
            continue
        unsupported.append(flag)
    return CommitPassthrough(
        allow_empty=allow_empty,
        no_edit=no_edit,
        unsupported=tuple(unsupported),
    )


def build_git_commit_cmd(args) -> list[str]:
    """Compatibility helper used by parser tests and docs."""
    cmd = ["git", "commit"]
    if getattr(args, "message", None):
        cmd.extend(["-m", args.message])
    if getattr(args, "amend", False):
        cmd.append("--amend")
    extra = getattr(args, "passthrough", None) or []
    cmd.extend(extra)
    return cmd
