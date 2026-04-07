"""devctl review-snapshot command.

Builds a typed ``ReviewSnapshot`` and emits it as markdown, JSON, or a
terminal summary. The canonical use is ``--write``, which regenerates the
repo-pack-configured snapshot file (default ``dev/audits/REVIEW_SNAPSHOT.md``)
so an external reviewer can audit the repository directly from GitHub.

The same builder backs the managed commit hooks: pre-commit writes a projection
into the code commit, and ``--receipt-commit`` is the post-commit/publication
path that creates a trailing snapshot-only commit for external reviewers.
"""

from __future__ import annotations

import os
import json as _json
import subprocess
from pathlib import Path

from ...common import add_standard_output_arguments
from ...config import get_repo_root
from ...runtime.governance_scan import scan_repo_governance_safely
from ...runtime.review_snapshot import build_review_snapshot
from ...runtime.review_snapshot_render import render_review_snapshot_markdown
from ...runtime.vcs import run_git_capture
from .common import emit_governance_command_output


def add_parser(subparsers) -> None:
    """Register the ``review-snapshot`` CLI parser."""
    cmd = subparsers.add_parser(
        "review-snapshot",
        help=(
            "Render or write the typed external-review snapshot "
            "(default: dev/audits/REVIEW_SNAPSHOT.md). Run --write once "
            "per repo to initialize the file; subsequent governed commits "
            "auto-refresh it in place as part of the committed tree."
        ),
    )
    cmd.add_argument(
        "--write",
        action="store_true",
        default=False,
        help=(
            "Write the rendered markdown to the repo-pack-configured path. "
            "Required for the first invocation on any adopter repo — the "
            "governed commit hook is a no-op until this file exists."
        ),
    )
    cmd.add_argument(
        "--receipt-commit",
        action="store_true",
        default=False,
        help=(
            "After writing the snapshot, create a snapshot-only receipt commit "
            "bound to the current HEAD. This is the post-commit/publication "
            "path; it fails closed if any other path is dirty."
        ),
    )
    cmd.add_argument(
        "--target",
        default="",
        help=(
            "Override the write target path (defaults to "
            "governance.artifact_roots.review_snapshot_path)."
        ),
    )
    cmd.add_argument(
        "--previous-head",
        default="",
        help="Optional previous HEAD SHA used to bound the delta range.",
    )
    cmd.add_argument(
        "--commit-limit",
        type=int,
        default=25,
        help="Maximum number of commits to include in the delta (default 25).",
    )
    add_standard_output_arguments(
        cmd,
        format_choices=("md", "json", "terminal"),
        default_format="md",
    )


def run(args) -> int:
    """Build, render, and (optionally) write the ReviewSnapshot."""
    repo_root = get_repo_root()
    governance = scan_repo_governance_safely(repo_root)
    previous_head = (getattr(args, "previous_head", "") or "").strip()
    limit = max(1, int(getattr(args, "commit_limit", 25) or 25))
    snapshot = build_review_snapshot(
        repo_root=repo_root,
        previous_head_sha=previous_head,
        commit_limit=limit,
    )
    markdown = render_review_snapshot_markdown(snapshot)
    payload = snapshot.to_dict()

    target_display = ""
    receipt_commit = bool(getattr(args, "receipt_commit", False))
    receipt_result: dict[str, object] = {}
    write_requested = bool(getattr(args, "write", False) or receipt_commit)
    if write_requested:
        target_path = _resolve_target_path(
            repo_root=repo_root,
            override=getattr(args, "target", ""),
            governance=governance,
        )
        target_display = str(target_path.relative_to(repo_root))
        if receipt_commit:
            receipt_result = _preflight_receipt_commit(
                repo_root=repo_root,
                target_rel=target_display,
            )
            if not receipt_result.get("ok"):
                return _emit_result(
                    args,
                    snapshot=snapshot,
                    markdown=markdown,
                    payload=payload,
                    target_display=target_display,
                    receipt_result=receipt_result,
                    ok=False,
                )

        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(markdown, encoding="utf-8")
        if receipt_commit:
            receipt_result = _commit_snapshot_receipt(
                repo_root=repo_root,
                target_rel=target_display,
            )

    ok = not receipt_result or bool(receipt_result.get("ok"))
    return _emit_result(
        args,
        snapshot=snapshot,
        markdown=markdown,
        payload=payload,
        target_display=target_display,
        receipt_result=receipt_result,
        ok=ok,
    )


def _emit_result(
    args,
    *,
    snapshot,
    markdown: str,
    payload: dict,
    target_display: str,
    receipt_result: dict[str, object],
    ok: bool,
) -> int:
    """Emit a review-snapshot command result with optional receipt metadata."""
    human_output = _select_human_output(args, snapshot=snapshot, markdown=markdown)
    if receipt_result:
        human_output = "\n".join(
            [
                human_output,
                "",
                f"receipt: {receipt_result.get('reason', 'n/a')}",
                f"  ok: {str(receipt_result.get('ok', False)).lower()}",
                f"  commit: {receipt_result.get('commit_sha', '') or '-'}",
            ]
        )
    summary = {
        "generation_stamp": snapshot.identity.generation_stamp,
        "head_sha": snapshot.identity.head_sha,
        "branch": snapshot.identity.branch,
        "commit_count": snapshot.delta.commit_count,
        "bundle_classes": list(snapshot.delta.bundle_classes_touched),
        "risk_addons": list(snapshot.delta.risk_addons_triggered),
        "governance_open_findings": snapshot.quality.governance_open_findings,
        "write_target": target_display,
        "receipt_commit": receipt_result,
    }
    return emit_governance_command_output(
        args,
        command="review-snapshot",
        json_payload=payload,
        markdown_output=human_output,
        ok=ok,
        summary=summary,
    )


def _preflight_receipt_commit(*, repo_root: Path, target_rel: str) -> dict[str, object]:
    """Fail closed when a receipt commit would capture more than the snapshot."""
    dirty_result = _dirty_paths(repo_root=repo_root)
    if not dirty_result.get("ok"):
        return dirty_result

    dirty_paths = set(dirty_result.get("dirty_paths", ()))
    non_snapshot_paths = sorted(path for path in dirty_paths if path != target_rel)
    if non_snapshot_paths:
        return {
            "ok": False,
            "reason": "non_snapshot_paths_dirty",
            "dirty_paths": non_snapshot_paths,
        }
    return {"ok": True, "reason": "receipt_preflight_passed"}


def _commit_snapshot_receipt(*, repo_root: Path, target_rel: str) -> dict[str, object]:
    """Stage and commit only the generated ReviewSnapshot receipt."""
    add_code, _, add_error = run_git_capture(
        ["add", "--", target_rel],
        repo_root=repo_root,
    )
    if add_code != 0:
        return {
            "ok": False,
            "reason": "git_add_failed",
            "error": add_error,
        }

    staged_result = _staged_paths(repo_root=repo_root)
    if not staged_result.get("ok"):
        return staged_result

    staged_paths = set(staged_result.get("staged_paths", ()))
    non_snapshot_paths = sorted(path for path in staged_paths if path != target_rel)
    if non_snapshot_paths:
        return {
            "ok": False,
            "reason": "non_snapshot_paths_staged",
            "staged_paths": non_snapshot_paths,
        }
    if target_rel not in staged_paths:
        return {"ok": True, "reason": "receipt_unchanged", "commit_sha": ""}

    head_code, head_short, head_error = run_git_capture(
        ["rev-parse", "--short", "HEAD"],
        repo_root=repo_root,
    )
    if head_code != 0:
        return {
            "ok": False,
            "reason": "head_lookup_failed",
            "error": head_error,
        }

    env = os.environ.copy()
    env["DEVCTL_NO_REVIEW_SNAPSHOT_REFRESH"] = "1"
    env["DEVCTL_REVIEW_SNAPSHOT_RECEIPT_COMMIT"] = "1"
    completed = subprocess.run(
        [
            "git",
            "commit",
            "-m",
            f"Refresh external review snapshot for {head_short}",
        ],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )
    if completed.returncode != 0:
        return {
            "ok": False,
            "reason": "git_commit_failed",
            "error": (completed.stderr or completed.stdout or "").strip(),
        }

    commit_code, commit_sha, commit_error = run_git_capture(
        ["rev-parse", "HEAD"],
        repo_root=repo_root,
    )
    if commit_code != 0:
        return {
            "ok": False,
            "reason": "receipt_head_lookup_failed",
            "error": commit_error,
        }
    return {
        "ok": True,
        "reason": "receipt_committed",
        "commit_sha": commit_sha,
    }


def _dirty_paths(*, repo_root: Path) -> dict[str, object]:
    """Return all dirty repo-relative paths using git plumbing."""
    commands = (
        ("worktree", ["diff", "--name-only"]),
        ("index", ["diff", "--cached", "--name-only"]),
        ("untracked", ["ls-files", "--others", "--exclude-standard"]),
    )
    paths: set[str] = set()
    for label, command in commands:
        code, output, error = run_git_capture(command, repo_root=repo_root)
        if code != 0:
            return {
                "ok": False,
                "reason": f"{label}_dirty_lookup_failed",
                "error": error,
            }
        paths.update(line.strip() for line in output.splitlines() if line.strip())
    return {"ok": True, "reason": "dirty_paths_loaded", "dirty_paths": sorted(paths)}


def _staged_paths(*, repo_root: Path) -> dict[str, object]:
    code, output, error = run_git_capture(
        ["diff", "--cached", "--name-only"],
        repo_root=repo_root,
    )
    if code != 0:
        return {
            "ok": False,
            "reason": "staged_paths_lookup_failed",
            "error": error,
        }
    return {
        "ok": True,
        "reason": "staged_paths_loaded",
        "staged_paths": sorted(line.strip() for line in output.splitlines() if line.strip()),
    }


def _resolve_target_path(
    *,
    repo_root: Path,
    override: str,
    governance: object,
) -> Path:
    """Resolve the write target, preferring CLI override, then repo-pack config."""
    if override:
        candidate = override.strip()
    else:
        candidate = _governance_review_snapshot_path(governance)
    if not candidate:
        candidate = "dev/audits/REVIEW_SNAPSHOT.md"
    path = Path(candidate)
    if not path.is_absolute():
        path = repo_root / path
    return path


def _governance_review_snapshot_path(governance: object) -> str:
    """Read the configured review_snapshot_path from ProjectGovernance, if present."""
    if governance is None:
        return ""
    artifact_roots = getattr(governance, "artifact_roots", None)
    if artifact_roots is None:
        return ""
    value = getattr(artifact_roots, "review_snapshot_path", "")
    return str(value or "").strip()


def _select_human_output(args, *, snapshot, markdown: str) -> str:
    fmt = getattr(args, "format", "md")
    if fmt == "json":
        return _json.dumps(snapshot.to_dict(), indent=2, sort_keys=True)
    if fmt == "terminal":
        return _render_terminal_summary(snapshot)
    return markdown


def _render_terminal_summary(snapshot) -> str:
    identity = snapshot.identity
    state = snapshot.governance_state
    delta = snapshot.delta
    quality = snapshot.quality
    lines = [
        f"review-snapshot {identity.generation_stamp or 'n/a'}",
        f"  repo: {identity.repo_name or 'n/a'}@{identity.branch or 'n/a'}",
        f"  head: {identity.head_sha_short or 'n/a'} — {identity.head_subject or ''}",
        f"  push: {state.push_action or 'n/a'} ({state.push_reason or ''})",
        f"  reviewer: {state.reviewer_mode or 'n/a'}/{state.interaction_mode}",
        f"  pipeline: {state.pipeline_state or 'n/a'}",
        f"  delta: {delta.commit_count} commits, {delta.files_changed_count} files, "
        f"+{delta.total_insertions}/-{delta.total_deletions}",
        f"  bundle classes: {', '.join(delta.bundle_classes_touched) or '-'}",
        f"  risk add-ons: {', '.join(delta.risk_addons_triggered) or '-'}",
        f"  findings: {quality.governance_open_findings} open / "
        f"{quality.governance_total_findings} total",
    ]
    return "\n".join(lines)


__all__ = ["add_parser", "run"]
