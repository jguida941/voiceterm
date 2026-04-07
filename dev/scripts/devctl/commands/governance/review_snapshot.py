"""devctl review-snapshot command.

Builds a typed ``ReviewSnapshot`` and emits it as markdown, JSON, or a
terminal summary. The canonical use is ``--write``, which regenerates the
repo-pack-configured snapshot file (default ``dev/audits/REVIEW_SNAPSHOT.md``)
so an external reviewer can audit the repository directly from GitHub.

The same builder is invoked from ``governed_executor`` post-commit and from
``devctl push --execute`` pre-push, so every governed commit and push
refreshes the file automatically.
"""

from __future__ import annotations

import json as _json
from pathlib import Path

from ...common import add_standard_output_arguments
from ...config import get_repo_root
from ...runtime.governance_scan import scan_repo_governance_safely
from ...runtime.review_snapshot import build_review_snapshot
from ...runtime.review_snapshot_render import render_review_snapshot_markdown
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
    if getattr(args, "write", False):
        target_path = _resolve_target_path(
            repo_root=repo_root,
            override=getattr(args, "target", ""),
            governance=governance,
        )
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(markdown, encoding="utf-8")
        target_display = str(target_path.relative_to(repo_root))

    human_output = _select_human_output(args, snapshot=snapshot, markdown=markdown)
    summary = {
        "generation_stamp": snapshot.identity.generation_stamp,
        "head_sha": snapshot.identity.head_sha,
        "branch": snapshot.identity.branch,
        "commit_count": snapshot.delta.commit_count,
        "bundle_classes": list(snapshot.delta.bundle_classes_touched),
        "risk_addons": list(snapshot.delta.risk_addons_triggered),
        "governance_open_findings": snapshot.quality.governance_open_findings,
        "write_target": target_display,
    }
    return emit_governance_command_output(
        args,
        command="review-snapshot",
        json_payload=payload,
        markdown_output=human_output,
        ok=True,
        summary=summary,
    )


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
