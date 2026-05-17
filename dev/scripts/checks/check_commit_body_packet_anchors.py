#!/usr/bin/env python3
"""Report MP slice commits that lack packet/task-start anchors.

P3 guard: MP slice commits should preserve their review-channel provenance in
the commit message by citing a packet id or task_started evidence. The mandate
packet remains policy-owned in devctl_repo_policy.json.

The guard is report-only while historical commit messages are being backfilled.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

try:
    from check_bootstrap import REPO_ROOT
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


COMMAND = "check_commit_body_packet_anchors"
COMMIT_BODY_PACKET_ANCHORS_GUARD_ID = "CommitBodyPacketAnchors"
COMMIT_BODY_PACKET_ANCHORS_CONTRACT_ID = "CommitBodyPacketAnchorsGuard"
DEFAULT_MAX_COUNT = 200

_RECORD_SEP = "\x1e"
_MP_SLICE_RE = re.compile(r"\bMP-?[A-Z0-9-]*-S\d+[A-Z0-9-]*\b")
_PACKET_ANCHOR_RE = re.compile(r"\b(rev_pkt_\d+|task_started)\b", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class CommitBodyPacketAnchorsGuard:
    """Registry-facing contract for commit-message packet-anchor checks."""

    guard_id: str
    ok: bool
    report_only: bool
    would_fail: bool
    max_count: int
    scanned_commit_count: int = 0
    mp_slice_commit_count: int = 0
    violation_count: int = 0
    violations: tuple[dict[str, object], ...] = field(default_factory=tuple)
    errors: tuple[str, ...] = field(default_factory=tuple)
    schema_version: int = 1
    contract_id: str = "CommitBodyPacketAnchorsGuard"
    command: str = COMMAND


@dataclass(frozen=True)
class CommitAnchorViolation:
    commit_sha: str
    subject: str
    mp_slice_refs: tuple[str, ...]
    detail: str

    def to_dict(self) -> dict[str, object]:
        return {
            "commit_sha": self.commit_sha,
            "subject": self.subject,
            "mp_slice_refs": list(self.mp_slice_refs),
            "detail": self.detail,
        }


@dataclass(frozen=True)
class CommitMessage:
    commit_sha: str
    message: str

    @property
    def subject(self) -> str:
        for line in self.message.splitlines():
            if line.strip():
                return line.strip()
        return ""


def evaluate_commit_body_packet_anchors(
    *,
    repo_root: Path = REPO_ROOT,
    max_count: int = DEFAULT_MAX_COUNT,
    log_text: str | None = None,
) -> CommitBodyPacketAnchorsGuard:
    errors: list[str] = []
    if log_text is None:
        log_text, errors = _git_log_text(repo_root=repo_root, max_count=max_count)
    commits = _parse_git_log_text(log_text)
    violations: list[CommitAnchorViolation] = []
    mp_slice_count = 0
    for commit in commits:
        mp_refs = tuple(dict.fromkeys(_MP_SLICE_RE.findall(commit.message)))
        if not mp_refs:
            continue
        mp_slice_count += 1
        if _PACKET_ANCHOR_RE.search(commit.message):
            continue
        violations.append(
            CommitAnchorViolation(
                commit_sha=commit.commit_sha,
                subject=commit.subject,
                mp_slice_refs=mp_refs,
                detail=(
                    "MP slice commits must cite a rev_pkt_* packet id or "
                    "task_started evidence in the commit message."
                ),
            )
        )

    return CommitBodyPacketAnchorsGuard(
        guard_id=COMMIT_BODY_PACKET_ANCHORS_GUARD_ID,
        ok=True,
        report_only=True,
        would_fail=bool(violations or errors),
        max_count=max_count,
        scanned_commit_count=len(commits),
        mp_slice_commit_count=mp_slice_count,
        violation_count=len(violations),
        violations=tuple(violation.to_dict() for violation in violations[:50]),
        errors=tuple(errors),
    )


def _git_log_text(*, repo_root: Path, max_count: int) -> tuple[str, list[str]]:
    result = subprocess.run(
        [
            "git",
            "log",
            f"--max-count={max_count}",
            "--format=%H%n%B%x1e",
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return "", [result.stderr.strip() or "git_log_failed"]
    return result.stdout, []


def _parse_git_log_text(log_text: str) -> list[CommitMessage]:
    commits: list[CommitMessage] = []
    for raw_record in log_text.split(_RECORD_SEP):
        record = raw_record.strip("\n")
        if not record:
            continue
        lines = record.splitlines()
        if not lines:
            continue
        commit_sha = lines[0].strip()
        message = "\n".join(lines[1:]).strip()
        if commit_sha and message:
            commits.append(CommitMessage(commit_sha=commit_sha, message=message))
    return commits


def _render_md(report: CommitBodyPacketAnchorsGuard) -> str:
    lines = [f"# {COMMAND}", ""]
    lines.append(f"- ok: {report.ok}")
    lines.append(f"- report_only: {report.report_only}")
    lines.append(f"- would_fail: {report.would_fail}")
    lines.append(f"- max_count: {report.max_count}")
    lines.append(f"- scanned_commit_count: {report.scanned_commit_count}")
    lines.append(f"- mp_slice_commit_count: {report.mp_slice_commit_count}")
    lines.append(f"- violation_count: {report.violation_count}")
    if report.errors:
        lines.append("")
        lines.append("## Errors")
        lines.extend(f"- {error}" for error in report.errors)
    if report.violations:
        lines.append("")
        lines.append("## Violations (first 50)")
        for violation in report.violations:
            if not isinstance(violation, dict):
                continue
            lines.append(
                "- "
                f"{violation.get('commit_sha')} "
                f"`{violation.get('subject')}` "
                f"refs={violation.get('mp_slice_refs')}"
            )
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-count", type=int, default=DEFAULT_MAX_COUNT)
    parser.add_argument("--format", choices=("md", "json"), default="md")
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    report = evaluate_commit_body_packet_anchors(max_count=args.max_count)
    if args.format == "json":
        print(json.dumps(asdict(report), indent=2))
    else:
        print(_render_md(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
