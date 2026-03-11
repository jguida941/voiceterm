"""Episode normalization and persistence helpers for watchdog analytics."""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import asdict
from pathlib import Path
from typing import Any

from ..config import REPO_ROOT
from ..jsonl_support import parse_json_line_dict
from .models import GuardedCodingEpisode, guarded_coding_episode_from_dict

DEFAULT_EPISODE_ROOT = Path("dev/reports/autonomy/watchdog/episodes")
_KNOWN_PROVIDERS = frozenset({"codex", "claude", "shared", "unknown"})
_KNOWN_GUARD_RESULTS = frozenset({"pass", "fail", "skipped", "noisy"})
_KNOWN_REVIEWER_VERDICTS = frozenset(
    {"accepted", "accepted_with_followups", "rejected", "deferred"}
)


def build_guarded_coding_episode(report: dict[str, Any]) -> GuardedCodingEpisode:
    """Build the canonical typed episode row from one guard-run report."""
    before = _snapshot(report, "diff_snapshot_before")
    after = _snapshot(report, "diff_snapshot_after")
    raw_context = report.get("watchdog_context")
    context = raw_context if isinstance(raw_context, dict) else {}
    runtime_seconds = float(report.get("guard_runtime_seconds") or 0.0)
    ok = bool(report.get("ok"))
    files_changed = after.get("files_changed") or before.get("files_changed") or []

    explicit_guard = str(context.get("guard_result") or "").strip().lower()
    guard_result = explicit_guard if explicit_guard in _KNOWN_GUARD_RESULTS else ("pass" if ok else "fail")

    explicit_verdict = str(context.get("reviewer_verdict") or "").strip().lower()
    reviewer_verdict = explicit_verdict if explicit_verdict in _KNOWN_REVIEWER_VERDICTS else ("accepted" if ok else "rejected")

    cmd_tokens = [str(part).lower() for part in report.get("command_args") or []]
    cmd_joined = " ".join(cmd_tokens)
    test_runtime = runtime_seconds if ("cargo test" in cmd_joined or "pytest" in cmd_joined or "unittest" in cmd_joined) else 0.0
    explicit_context_provider = str(context.get("provider") or "").strip().lower()
    if explicit_context_provider in _KNOWN_PROVIDERS:
        provider = explicit_context_provider
    else:
        explicit_env_provider = str(os.environ.get("DEVCTL_WATCHDOG_PROVIDER") or "").strip().lower()
        if explicit_env_provider in _KNOWN_PROVIDERS:
            provider = explicit_env_provider
        else:
            provider_tokens = " ".join(
                [str(report.get("label") or ""), str(report.get("command_display") or "")]
            ).lower()
            if "codex" in provider_tokens and "claude" in provider_tokens:
                provider = "shared"
            elif "codex" in provider_tokens:
                provider = "codex"
            elif "claude" in provider_tokens:
                provider = "claude"
            else:
                provider = "unknown"

    if "cargo" in cmd_tokens or "rust/" in cmd_joined or "--manifest-path rust/" in cmd_joined:
        guard_family = "rust"
    elif "markdownlint" in cmd_tokens or "docs-check" in cmd_joined:
        guard_family = "docs"
    elif "devctl.py" in cmd_joined or "check_" in cmd_joined or "hygiene" in cmd_joined:
        guard_family = "tooling"
    elif any(part.endswith(".py") for part in cmd_tokens) or "python" in cmd_joined:
        guard_family = "python"
    else:
        guard_family = "targeted"

    probe_scan = report.get("probe_scan")
    if isinstance(probe_scan, dict):
        escaped_findings_count = int(probe_scan.get("high_count", 0))
    else:
        escaped_findings_count = max(int(context.get("escaped_findings_count") or 0), 0)

    return GuardedCodingEpisode(
        episode_id=f"episode-{uuid.uuid4().hex[:12]}",
        task_id=str(report.get("label") or "guarded-command"),
        plan_id=str(os.environ.get("DEVCTL_MP_SCOPE") or "unscoped"),
        controller_run_id=str(os.environ.get("DEVCTL_AUDIT_CYCLE_ID") or "local"),
        provider=provider,
        session_id=str(
            context.get("session_id")
            or os.environ.get("DEVCTL_WATCHDOG_SESSION_ID")
            or "unknown"
        ),
        peer_session_id=str(
            context.get("peer_session_id")
            or os.environ.get("DEVCTL_WATCHDOG_PEER_SESSION_ID")
            or ""
        ),
        reviewed_worktree_hash_before=str(before.get("reviewed_worktree_hash") or ""),
        reviewed_worktree_hash_after=str(after.get("reviewed_worktree_hash") or ""),
        guard_family=guard_family,
        guard_command_id=str(report.get("command_display") or ""),
        trigger_reason=str(context.get("trigger_reason") or "manual_guard_run"),
        files_changed=tuple(str(item).strip() for item in files_changed if str(item).strip()),
        file_count=int(after.get("file_count") or before.get("file_count") or 0),
        lines_added_before_guard=int(before.get("lines_added") or 0),
        lines_removed_before_guard=int(before.get("lines_removed") or 0),
        lines_added_after_guard=int(after.get("lines_added") or 0),
        lines_removed_after_guard=int(after.get("lines_removed") or 0),
        diff_churn_before_guard=int(before.get("diff_churn") or 0),
        diff_churn_after_guard=int(after.get("diff_churn") or 0),
        guard_started_at_utc=report.get("guard_started_at_utc"),
        guard_finished_at_utc=report.get("guard_finished_at_utc"),
        episode_started_at_utc=report.get("guard_started_at_utc"),
        episode_finished_at_utc=report.get("guard_finished_at_utc"),
        first_edit_at_utc=report.get("guard_started_at_utc"),
        terminal_active_seconds=runtime_seconds,
        terminal_idle_seconds=0.0,
        guard_runtime_seconds=runtime_seconds,
        test_runtime_seconds=test_runtime,
        review_to_fix_seconds=0.0,
        time_to_green_seconds=runtime_seconds if ok else None,
        retry_count=max(int(context.get("retry_count") or 0), 0),
        guard_fail_count_before_green=0 if ok else 1,
        test_fail_count_before_green=0 if ok else 1,
        review_findings_count=0,
        escaped_findings_count=escaped_findings_count,
        handoff_count=0,
        stale_peer_pause_count=0,
        guard_result=guard_result,
        reviewer_verdict=reviewer_verdict,
        post_action=str(report.get("resolved_post_action") or "none"),
        cwd=str(report.get("cwd") or ""),
    )


def emit_guarded_coding_episode(report: dict[str, Any]) -> str | None:
    """Persist one canonical episode row plus a per-episode summary payload."""
    if bool(report.get("dry_run")):
        return None
    episode = build_guarded_coding_episode(report)
    raw_episode_root = str(os.environ.get("DEVCTL_WATCHDOG_EPISODE_ROOT") or "").strip()
    if raw_episode_root:
        episode_path = Path(raw_episode_root).expanduser()
        root = episode_path if episode_path.is_absolute() else (REPO_ROOT / episode_path).resolve()
    else:
        root = (REPO_ROOT / DEFAULT_EPISODE_ROOT).resolve()
    root.mkdir(parents=True, exist_ok=True)
    summary_dir = root / episode.episode_id
    summary_dir.mkdir(parents=True, exist_ok=True)
    summary_path = summary_dir / "summary.json"
    summary_path.write_text(
        json.dumps({"episode": asdict(episode), "guard_run_report": report}, indent=2),
        encoding="utf-8",
    )
    with (root / "guarded_coding_episode.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(asdict(episode), sort_keys=True))
        handle.write("\n")
    return str(summary_path)


def read_guarded_coding_episodes(
    root: Path,
    *,
    max_rows: int,
) -> list[GuardedCodingEpisode]:
    """Read canonical typed episodes from the JSONL store."""
    jsonl_path = root if root.suffix == ".jsonl" else root / "guarded_coding_episode.jsonl"
    rows: list[GuardedCodingEpisode] = []
    try:
        with jsonl_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                payload = parse_json_line_dict(line)
                if payload is None:
                    continue
                rows.append(guarded_coding_episode_from_dict(payload))
                if len(rows) > max(1, max_rows):
                    rows.pop(0)
    except OSError:
        return []
    return rows


def _snapshot(report: dict[str, Any], key: str) -> dict[str, Any]:
    value = report.get(key)
    return value if isinstance(value, dict) else {}
