#!/usr/bin/env python3
"""Check commit-message plan row references against typed plan authority."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

try:
    from check_bootstrap import REPO_ROOT
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


COMMAND = "check_commit_message_row_id_resolves"
CONTRACT_ID = "CommitMessageRowIdResolvesGuard"
DEFAULT_MAX_COUNT = 200
DEFAULT_PLAN_INDEX_REL = Path("dev/state/plan_index.jsonl")
_RECORD_SEP = "\x1e"
_MP_ROW_RE = re.compile(r"\b(?:MP-NEW|MP-?\d+)-[A-Z0-9][A-Z0-9_-]*\b")
_PACKET_REF_RE = re.compile(r"\brev_pkt_\d+\b")
_CORRUPTED_TITLE_RE = re.compile(r"(?:\\u[0-9a-fA-F]{4}|\.\.S\d+|S\d+\.\.S\d+)")


@dataclass(frozen=True, slots=True)
class CommitMessageRowIdResolvesGuard:
    guard_id: str
    ok: bool
    scanned_commit_count: int
    referenced_row_count: int
    violation_count: int
    violations: tuple[dict[str, object], ...] = field(default_factory=tuple)
    errors: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)
    schema_version: int = 1
    contract_id: str = CONTRACT_ID
    command: str = COMMAND


@dataclass(frozen=True, slots=True)
class CommitMessage:
    commit_sha: str
    message: str
    committed_at_utc: str = ""

    @property
    def subject(self) -> str:
        for line in self.message.splitlines():
            if line.strip():
                return line.strip()
        return ""


def evaluate_commit_message_row_id_resolves(
    *,
    repo_root: Path = REPO_ROOT,
    plan_index_path: Path | None = None,
    log_text: str | None = None,
    max_count: int = DEFAULT_MAX_COUNT,
) -> CommitMessageRowIdResolvesGuard:
    errors: list[str] = []
    warnings: list[str] = []
    if log_text is None:
        log_text, errors = _git_log_text(repo_root=repo_root, max_count=max_count)
    commits = _parse_git_log_text(log_text)
    rows, read_errors = _read_plan_rows(plan_index_path or repo_root / DEFAULT_PLAN_INDEX_REL)
    errors.extend(read_errors)
    enforced_prefixes = _enforced_row_prefixes(repo_root)
    observed_at_utc = _guard_observed_at_utc(repo_root)
    rows_by_id = {str(row.get("row_id") or ""): row for row in rows}
    violations: list[dict[str, object]] = []
    referenced_row_count = 0

    for commit in commits:
        if _commit_before_guard_observed_at(commit, observed_at_utc):
            continue
        if _is_allowlisted_subject(commit.subject):
            continue
        packet_refs = tuple(dict.fromkeys(_PACKET_REF_RE.findall(commit.message)))
        row_refs = tuple(dict.fromkeys(_MP_ROW_RE.findall(commit.message)))
        enforced_row_refs = tuple(
            row_id for row_id in row_refs if _row_ref_enforced(row_id, enforced_prefixes)
        )
        for packet_id in packet_refs:
            if row_refs and not enforced_row_refs:
                continue
            packet_violation = _packet_decomposition_violation(
                commit=commit,
                packet_id=packet_id,
                rows=rows,
            )
            if packet_violation is not None:
                violations.append(packet_violation)

        referenced_row_count += len(row_refs)
        for row_id in enforced_row_refs:
            row = rows_by_id.get(row_id)
            if row is None:
                if packet_refs:
                    continue
                violations.append(
                    _violation(
                        commit=commit,
                        reason="missing_plan_row",
                        referenced_id=row_id,
                        expected_action="ingest_plan_intent",
                    )
                )
                continue
            title = str(row.get("title") or "")
            if _CORRUPTED_TITLE_RE.search(title):
                violations.append(
                    _violation(
                        commit=commit,
                        reason="corrupted_title_persisted",
                        referenced_id=row_id,
                        expected_action="run_plan_row_title_sanitization",
                    )
                )
            if _row_applied_without_commit_anchor(row):
                violations.append(
                    _violation(
                        commit=commit,
                        reason="applied_row_missing_commit_anchor_ref",
                        referenced_id=row_id,
                        expected_action="hydrate_commit_anchor_ref",
                    )
                )

    return CommitMessageRowIdResolvesGuard(
        guard_id=CONTRACT_ID,
        ok=not violations and not errors,
        scanned_commit_count=len(commits),
        referenced_row_count=referenced_row_count,
        violation_count=len(violations),
        violations=tuple(violations),
        errors=tuple(errors),
        warnings=tuple(warnings),
    )


def _enforced_row_prefixes(repo_root: Path) -> tuple[str, ...]:
    mandate = _guard_mandate(repo_root)
    prefixes = mandate.get("enforced_row_prefixes")
    if not isinstance(prefixes, list | tuple):
        return ()
    return tuple(str(prefix or "").strip() for prefix in prefixes if str(prefix or "").strip())


def _guard_observed_at_utc(repo_root: Path) -> str:
    return str(_guard_mandate(repo_root).get("observed_at_utc") or "").strip()


def _guard_mandate(repo_root: Path) -> dict[str, object]:
    path = repo_root / "dev/config/devctl_repo_policy.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    mandates = (
        payload.get("repo_governance", {})
        .get("guard_mandates", {})
        .get(COMMAND, {})
    )
    if not isinstance(mandates, dict):
        return {}
    return mandates


def _row_ref_enforced(row_id: str, prefixes: tuple[str, ...]) -> bool:
    return not prefixes or any(row_id.startswith(prefix) for prefix in prefixes)


def _commit_before_guard_observed_at(commit: CommitMessage, observed_at_utc: str) -> bool:
    if not observed_at_utc or not commit.committed_at_utc:
        return False
    return _normalized_utc(commit.committed_at_utc) < _normalized_utc(observed_at_utc)


def _normalized_utc(value: str) -> str:
    return value.strip().replace("+00:00", "Z")


def _packet_decomposition_violation(
    *,
    commit: CommitMessage,
    packet_id: str,
    rows: list[dict[str, object]],
) -> dict[str, object] | None:
    packet_rows = [row for row in rows if packet_id in _row_packet_refs(row)]
    if not packet_rows:
        return _violation(
            commit=commit,
            reason="packet_without_plan_rows",
            referenced_id=packet_id,
            expected_action="ingest_plan_intent",
        )
    decomposed_rows = [
        row
        for row in packet_rows
        if str(row.get("row_id") or "").startswith("MP-NEW-")
        and str(row.get("mutation_op") or "") == "ingest_plan_intent"
    ]
    pkt_bind_rows = [
        row for row in packet_rows if str(row.get("row_id") or "").startswith("PKT-BIND-")
    ]
    if pkt_bind_rows and not decomposed_rows:
        return _violation(
            commit=commit,
            reason="packet_only_pkt_bind_rows",
            referenced_id=packet_id,
            expected_action="materialize_mp_new_plan_rows",
        )
    return None


def _row_packet_refs(row: dict[str, object]) -> set[str]:
    refs: set[str] = set()
    for key in ("sourced_from_packets", "anchor_refs", "work_evidence_ids"):
        value = row.get(key)
        if isinstance(value, list | tuple):
            for item in value:
                text = str(item or "").strip()
                if text.startswith("packet:"):
                    text = text.removeprefix("packet:")
                if text.startswith("rev_pkt_"):
                    refs.add(text)
    return refs


def _row_applied_without_commit_anchor(row: dict[str, object]) -> bool:
    if str(row.get("status") or "") not in {"applied", "completed"}:
        return False
    if str(row.get("commit_anchor_ref") or "").strip():
        return False
    anchor_refs = row.get("anchor_refs")
    if isinstance(anchor_refs, list | tuple):
        return not any(str(ref or "").startswith("commit:") for ref in anchor_refs)
    return True


def _violation(
    *,
    commit: CommitMessage,
    reason: str,
    referenced_id: str,
    expected_action: str,
) -> dict[str, object]:
    return {
        "commit_sha": commit.commit_sha,
        "subject": commit.subject,
        "reason": reason,
        "referenced_id": referenced_id,
        "expected_action": expected_action,
    }


def _read_plan_rows(path: Path) -> tuple[list[dict[str, object]], list[str]]:
    rows: list[dict[str, object]] = []
    errors: list[str] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return [], [f"plan_index_read_failed:{exc.__class__.__name__}:{path}"]
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"invalid_plan_index_jsonl:{line_number}:{exc.msg}")
            continue
        if isinstance(payload, dict):
            rows.append(payload)
        else:
            errors.append(f"non_object_plan_row:{line_number}")
    return rows, errors


def _is_allowlisted_subject(subject: str) -> bool:
    return subject.startswith("Refresh external review snapshot")


def _git_log_text(*, repo_root: Path, max_count: int) -> tuple[str, list[str]]:
    result = subprocess.run(
        ("git", "log", f"--max-count={max_count}", "--format=%H%x00%cI%n%B%x1e"),
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
        header = lines[0].strip()
        if "\x00" in header:
            commit_sha, committed_at_utc = header.split("\x00", 1)
        else:
            commit_sha, committed_at_utc = header, ""
        message = "\n".join(lines[1:]).strip()
        if commit_sha and message:
            commits.append(
                CommitMessage(
                    commit_sha=commit_sha,
                    committed_at_utc=committed_at_utc,
                    message=message,
                )
            )
    return commits


def _render_md(report: CommitMessageRowIdResolvesGuard) -> str:
    lines = [f"# {COMMAND}", ""]
    lines.append(f"- ok: {report.ok}")
    lines.append(f"- scanned_commit_count: {report.scanned_commit_count}")
    lines.append(f"- referenced_row_count: {report.referenced_row_count}")
    lines.append(f"- violation_count: {report.violation_count}")
    if report.errors:
        lines.append("")
        lines.append("## Errors")
        lines.extend(f"- {error}" for error in report.errors)
    if report.warnings:
        lines.append("")
        lines.append("## Warnings")
        lines.extend(f"- {warning}" for warning in report.warnings)
    if report.violations:
        lines.append("")
        lines.append("## Violations")
        for violation in report.violations[:50]:
            lines.append(
                "- "
                f"{violation.get('commit_sha')} "
                f"{violation.get('reason')} "
                f"ref={violation.get('referenced_id')} "
                f"subject=`{violation.get('subject')}`"
            )
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-count", type=int, default=DEFAULT_MAX_COUNT)
    parser.add_argument("--plan-index-path", default=str(DEFAULT_PLAN_INDEX_REL))
    parser.add_argument("--format", choices=("md", "json"), default="md")
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    report = evaluate_commit_message_row_id_resolves(
        plan_index_path=REPO_ROOT / args.plan_index_path,
        max_count=args.max_count,
    )
    if args.format == "json":
        print(json.dumps(asdict(report), indent=2, sort_keys=True))
    else:
        print(_render_md(report))
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
