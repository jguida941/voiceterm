#!/usr/bin/env python3
"""Fail when receipt commit_sha references do not resolve or declare external origin."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

try:
    from check_bootstrap import REPO_ROOT, emit_runtime_error, utc_timestamp
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import (
        REPO_ROOT,
        emit_runtime_error,
        utc_timestamp,
    )

try:
    from _git_status_helpers import git_commit_exists as _git_commit_exists
except ModuleNotFoundError:
    from dev.scripts.checks._git_status_helpers import (
        git_commit_exists as _git_commit_exists,
    )


COMMAND = "check_receipt_commit_anchor_refs"
CONTRACT_ID = "ReceiptCommitAnchorRefsGuard"

REASON_UNRESOLVED_COMMIT = "receipt_commit_sha_unresolved"
REASON_EXTERNAL_INCOMPLETE = "receipt_external_reference_incomplete"

DISPLAY_TEXT = (
    "AI DUMBASS ALERT: receipt references an orphan commit SHA. Receipt commit "
    "anchors must resolve locally or carry typed external-reference metadata."
)

DEFAULT_SCAN_ROOTS = (
    "dev/state",
    "dev/reports/feature_proof_receipts",
    "dev/reports/push",
    "dev/reports/dogfood",
)


@dataclass(frozen=True, slots=True)
class CommitAnchorRef:
    path: str
    contract_id: str
    receipt_id: str
    commit_sha: str
    external_reference: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class CommitAnchorViolation:
    path: str
    reason: str
    detail: str
    remediation: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def build_report(
    *,
    repo_root: Path = REPO_ROOT,
    scope: str = "changed",
    changed_paths: Sequence[str | Path] | None = None,
    receipt_paths: Sequence[str | Path] | None = None,
    commit_exists: Callable[[str], bool] | None = None,
) -> dict[str, object]:
    warnings: list[str] = []
    paths = _receipt_paths_for_scope(
        repo_root=repo_root,
        scope=scope,
        changed_paths=changed_paths,
        receipt_paths=receipt_paths,
        warnings=warnings,
    )
    resolver = commit_exists or (lambda sha: _git_commit_exists(repo_root, sha))
    refs: list[CommitAnchorRef] = []
    violations: list[CommitAnchorViolation] = []

    for path in paths:
        for payload in _iter_receipt_payloads(path):
            commit_sha = str(payload.get("commit_sha") or "").strip()
            if not commit_sha:
                continue
            display_path = str(_repo_relative(path, repo_root))
            external_ok, external_present = _external_reference_complete(payload)
            refs.append(
                CommitAnchorRef(
                    path=display_path,
                    contract_id=str(payload.get("contract_id") or ""),
                    receipt_id=str(payload.get("receipt_id") or payload.get("finding_id") or ""),
                    commit_sha=commit_sha,
                    external_reference=external_present,
                )
            )
            if resolver(commit_sha):
                continue
            if external_present and external_ok:
                continue
            if external_present and not external_ok:
                violations.append(
                    CommitAnchorViolation(
                        path=display_path,
                        reason=REASON_EXTERNAL_INCOMPLETE,
                        detail=(
                            f"commit_sha={commit_sha!r} is external but missing "
                            "upstream_repo/repo, branch, or reason"
                        ),
                        remediation=(
                            "Set external_reference with upstream_repo, branch, and reason."
                        ),
                    )
                )
                continue
            violations.append(
                CommitAnchorViolation(
                    path=display_path,
                    reason=REASON_UNRESOLVED_COMMIT,
                    detail=f"commit_sha={commit_sha!r} does not resolve locally",
                    remediation=(
                        "Use a local commit SHA or add typed external_reference metadata "
                        "with upstream repo, branch, and reason."
                    ),
                )
            )

    return {
        "schema_version": 1,
        "contract_id": CONTRACT_ID,
        "command": COMMAND,
        "timestamp": utc_timestamp(),
        "ok": not violations,
        "display_text": DISPLAY_TEXT if violations else "",
        "scope": scope,
        "receipt_path_count": len(paths),
        "commit_ref_count": len(refs),
        "external_reference_count": sum(1 for ref in refs if ref.external_reference),
        "violation_count": len(violations),
        "commit_refs": [ref.to_dict() for ref in refs],
        "violations": [violation.to_dict() for violation in violations],
        "warnings": warnings,
    }


def _receipt_paths_for_scope(
    *,
    repo_root: Path,
    scope: str,
    changed_paths: Sequence[str | Path] | None,
    receipt_paths: Sequence[str | Path] | None,
    warnings: list[str],
) -> tuple[Path, ...]:
    if receipt_paths is not None:
        return tuple(_resolve_path(repo_root, path) for path in receipt_paths)
    if scope == "all":
        return _all_receipt_paths(repo_root)
    if scope != "changed":
        warnings.append(f"unknown scope {scope!r}; defaulting to changed")
    paths = (
        tuple(Path(path) for path in changed_paths)
        if changed_paths is not None
        else _git_changed_paths(repo_root, warnings)
    )
    return _changed_receipt_paths(paths, repo_root=repo_root)


def _all_receipt_paths(repo_root: Path) -> tuple[Path, ...]:
    paths: set[Path] = set()
    for root_text in DEFAULT_SCAN_ROOTS:
        root = repo_root / root_text
        if not root.exists():
            continue
        if root.is_file():
            paths.add(root)
            continue
        for suffix in ("*.jsonl", "*.json"):
            paths.update(path for path in root.glob(suffix) if path.is_file())
    return tuple(sorted(paths))


def _changed_receipt_paths(
    changed_paths: Sequence[Path],
    *,
    repo_root: Path,
) -> tuple[Path, ...]:
    paths: set[Path] = set()
    for changed_path in changed_paths:
        candidate = changed_path if changed_path.is_absolute() else repo_root / changed_path
        if not candidate.is_file():
            continue
        rel = str(_repo_relative(candidate, repo_root))
        if not rel.endswith((".json", ".jsonl")):
            continue
        if rel.startswith("dev/state/") or any(
            rel.startswith(f"{root}/") for root in DEFAULT_SCAN_ROOTS if root != "dev/state"
        ):
            paths.add(candidate)
    return tuple(sorted(paths))


def _git_changed_paths(repo_root: Path, warnings: list[str]) -> tuple[Path, ...]:
    result = subprocess.run(
        (
            "git",
            "status",
            "--short",
            "--untracked-files=all",
            "--",
            "dev/state",
            "dev/reports/feature_proof_receipts",
            "dev/reports/push",
            "dev/reports/dogfood",
        ),
        cwd=repo_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        warnings.append(f"git status failed: {result.stderr.strip()}")
        return ()
    paths: list[Path] = []
    for line in result.stdout.splitlines():
        path_text = line[3:].strip()
        if " -> " in path_text:
            path_text = path_text.split(" -> ", 1)[1].strip()
        if path_text:
            paths.append(Path(path_text))
    return tuple(paths)


def _iter_receipt_payloads(path: Path) -> Iterable[Mapping[str, object]]:
    try:
        raw_text = path.read_text(encoding="utf-8")
    except OSError:
        return ()
    if path.suffix == ".jsonl":
        return tuple(_jsonl_payloads(raw_text))
    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError:
        return ()
    return (payload,) if isinstance(payload, Mapping) else ()


def _jsonl_payloads(raw_text: str) -> Iterable[Mapping[str, object]]:
    for raw_line in raw_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, Mapping):
            yield payload


def _external_reference_complete(payload: Mapping[str, object]) -> tuple[bool, bool]:
    external = payload.get("external_reference")
    if not isinstance(external, Mapping):
        return False, False
    repo = str(external.get("upstream_repo") or external.get("repo") or "").strip()
    branch = str(external.get("branch") or "").strip()
    reason = str(external.get("reason") or "").strip()
    return bool(repo and branch and reason), True


def _resolve_path(repo_root: Path, path: str | Path) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else repo_root / candidate


def _repo_relative(path: Path, repo_root: Path = REPO_ROOT) -> Path:
    try:
        return path.resolve().relative_to(repo_root.resolve())
    except (OSError, ValueError):
        return path


def _render_md(report: Mapping[str, object]) -> str:
    lines = [
        f"# {COMMAND}",
        "",
        f"- ok: {report['ok']}",
        f"- scope: {report['scope']}",
        f"- receipt_path_count: {report['receipt_path_count']}",
        f"- commit_ref_count: {report['commit_ref_count']}",
        f"- violation_count: {report['violation_count']}",
    ]
    violations = report.get("violations") or []
    if violations:
        lines.extend(["", "## Violations"])
        for violation in violations:
            if isinstance(violation, Mapping):
                lines.append(
                    f"- {violation.get('path')}: {violation.get('reason')} - "
                    f"{violation.get('detail')}"
                )
    return "\n".join(lines) + "\n"


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("json", "md"), default="md")
    parser.add_argument("--scope", choices=("changed", "all"), default="changed")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(tuple(argv if argv is not None else sys.argv[1:]))
    try:
        report = build_report(scope=args.scope)
    except Exception as exc:  # pragma: no cover - defensive CLI guardrail
        return emit_runtime_error(command=COMMAND, exc=exc, output_format=args.format)
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=False))
    else:
        print(_render_md(report), end="")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
