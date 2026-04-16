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
from ...repo_packs import active_path_config
from ...review_channel.bridge_file import rewrite_bridge_markdown
from ...review_channel.bridge_projection import render_bridge_projection
from ...review_channel.core import bridge_is_active
from ...review_channel.heartbeat import compute_non_audit_worktree_hash
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

        # Atomic governed pipeline: when a receipt commit is requested, the
        # bridge.md projection is a pipeline-generated artifact that must be
        # refreshed inside the same step as the snapshot. We sync it first so
        # its path can enter the preflight allowlist and the final commit
        # captures both typed review-state artifacts in a single commit.
        bridge_sync: dict[str, object] = {}
        allowlist: tuple[str, ...] = (target_display,)
        if receipt_commit:
            from ...runtime.commit_packet_gate import check_commit_packet_gate
            from ..vcs.governed_executor_commit_runtime import (
                load_live_review_state as _load_live_review_state,
                resolve_commit_execution_target as _resolve_commit_target,
            )

            config = active_path_config()
            rc_path = repo_root / config.review_channel_rel
            rc_effective = rc_path if rc_path.exists() else None
            pending_block = check_commit_packet_gate(
                repo_root=repo_root,
                review_channel_path=rc_effective,
                load_review_state_fn=lambda: _load_live_review_state(
                    repo_root=repo_root,
                    review_channel_path=rc_effective,
                ),
                resolve_target_fn=_resolve_commit_target,
            )
            if pending_block is not None:
                return _emit_result(
                    args,
                    snapshot=snapshot,
                    markdown=markdown,
                    payload=payload,
                    target_display=target_display,
                    receipt_result={
                        "ok": False,
                        "reason": "pending_reviewer_packets",
                        "detail": pending_block,
                    },
                    ok=False,
                )

            bridge_sync = _sync_bridge_projection_if_active(repo_root=repo_root)
            bridge_rel = str(bridge_sync.get("bridge_rel") or "").strip()
            if bridge_rel:
                allowlist = (target_display, bridge_rel)

            receipt_result = _preflight_receipt_commit(
                repo_root=repo_root,
                allowlist=allowlist,
            )
            if not receipt_result.get("ok"):
                if bridge_sync:
                    receipt_result["bridge_sync"] = bridge_sync
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
                allowlist=allowlist,
            )
            if bridge_sync:
                receipt_result["bridge_sync"] = bridge_sync

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


def _preflight_receipt_commit(
    *,
    repo_root: Path,
    target_rel: str | None = None,
    allowlist: tuple[str, ...] | None = None,
) -> dict[str, object]:
    """Fail closed when the receipt commit would capture more than governed paths.

    The allowlist is the set of paths produced by this pipeline step itself
    (the snapshot and — when the bridge is active — the bridge.md projection
    refreshed in the same atomic sequence). Any other dirty path indicates
    user work that must be committed separately.
    """
    allow: set[str] = set(allowlist or ())
    if target_rel:
        allow.add(target_rel)

    dirty_result = _dirty_paths(repo_root=repo_root)
    if not dirty_result.get("ok"):
        return dirty_result

    dirty_paths = set(dirty_result.get("dirty_paths", ()))
    non_snapshot_paths = sorted(path for path in dirty_paths if path not in allow)
    if non_snapshot_paths:
        return {
            "ok": False,
            "reason": "non_snapshot_paths_dirty",
            "dirty_paths": non_snapshot_paths,
        }
    return {"ok": True, "reason": "receipt_preflight_passed"}


def _commit_snapshot_receipt(
    *,
    repo_root: Path,
    target_rel: str,
    allowlist: tuple[str, ...] | None = None,
) -> dict[str, object]:
    """Stage and commit the ReviewSnapshot receipt plus its governed siblings.

    When ``allowlist`` includes additional pipeline-generated paths (e.g. the
    refreshed ``bridge.md`` projection), they are staged and committed together
    so every HEAD bump produces exactly one governed receipt commit rather
    than one code commit plus a trailing snapshot commit.
    """
    # Paths this atomic pipeline is authorized to stage/commit.
    allow_tuple = tuple(dict.fromkeys((target_rel, *(allowlist or ()))))

    for path in allow_tuple:
        add_code, _, add_error = run_git_capture(
            ["add", "--", path],
            repo_root=repo_root,
        )
        if add_code != 0:
            return {
                "ok": False,
                "reason": "git_add_failed",
                "error": add_error,
                "path": path,
            }

    staged_result = _staged_paths(repo_root=repo_root)
    if not staged_result.get("ok"):
        return staged_result

    staged_paths = set(staged_result.get("staged_paths", ()))
    non_snapshot_paths = sorted(path for path in staged_paths if path not in allow_tuple)
    if non_snapshot_paths:
        return {
            "ok": False,
            "reason": "non_snapshot_paths_staged",
            "staged_paths": non_snapshot_paths,
        }
    if not staged_paths:
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


def _sync_bridge_projection_if_active(*, repo_root: Path) -> dict[str, object]:
    """Refresh the bridge.md projection from typed review-state as an atomic step.

    The receipt pipeline runs this before the preflight dirty-check so the
    generated bridge.md can enter the same commit as the snapshot receipt
    instead of surfacing as a phantom dirty path. Every field consumers read
    is present in the typed ``review_state.json``; the markdown bridge is a
    compatibility projection that future work will retire.

    TODO(Q100/B): Remove this markdown projection and delete ``bridge.md``
    once all consumers (reviewer poll, operator console, status renderers)
    read typed ``current_session`` fields directly from ``review_state.json``.
    Seam: keep this call site and the matching writer in
    ``dev/scripts/devctl/commands/review_channel/status_bridge_sync.py``
    aligned so retirement can land in one pass.
    """
    config = active_path_config()
    bridge_path = repo_root / config.bridge_rel
    review_channel_path = repo_root / config.review_channel_rel
    if not bridge_path.is_file() or not review_channel_path.is_file():
        return {"synced": False, "reason": "bridge_or_channel_missing"}

    try:
        review_channel_text = review_channel_path.read_text(encoding="utf-8")
    except OSError as exc:
        return {"synced": False, "reason": "review_channel_read_failed", "error": str(exc)}

    if not bridge_is_active(review_channel_text):
        return {"synced": False, "reason": "bridge_not_active"}

    review_state_path = _resolve_review_state_path(repo_root=repo_root, config=config)
    if review_state_path is None:
        return {"synced": False, "reason": "review_state_missing"}

    try:
        review_state_payload = _json.loads(review_state_path.read_text(encoding="utf-8"))
        if not isinstance(review_state_payload, dict):
            return {"synced": False, "reason": "review_state_not_mapping"}
        bridge_rel = str(bridge_path.relative_to(repo_root))
        worktree_hash = compute_non_audit_worktree_hash(
            repo_root=repo_root,
            excluded_rel_paths=(bridge_rel,),
        )

        def transform(_bridge_text: str) -> str:
            rendered, _ = render_bridge_projection(
                review_state=review_state_payload,
                last_worktree_hash=worktree_hash,
            )
            return rendered

        rewrite_bridge_markdown(bridge_path, transform=transform)
    except (OSError, ValueError, _json.JSONDecodeError) as exc:
        return {"synced": False, "reason": "bridge_write_failed", "error": str(exc)}
    return {"synced": True, "reason": "bridge_refreshed", "bridge_rel": bridge_rel}


def _resolve_review_state_path(*, repo_root: Path, config) -> Path | None:
    """Return the first existing review_state.json candidate, if any."""
    for candidate in getattr(config, "review_state_candidates", ()):
        path = repo_root / candidate
        if path.is_file():
            return path
    return None


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
