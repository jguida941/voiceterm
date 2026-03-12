#!/usr/bin/env python3
"""Guard against non-regressive growth of Python lint/type suppression comments."""

from __future__ import annotations

import argparse
import io
import json
import re
import sys
import tokenize
from pathlib import Path

try:
    from check_bootstrap import (
        build_since_ref_format_parser,
        emit_runtime_error,
        import_attr,
        is_under_target_roots,
        resolve_quality_scope_roots,
        utc_timestamp,
    )
except ModuleNotFoundError:  # pragma: no cover - import fallback for package-style test loading
    from dev.scripts.checks.check_bootstrap import (
        build_since_ref_format_parser,
        emit_runtime_error,
        import_attr,
        is_under_target_roots,
        resolve_quality_scope_roots,
        utc_timestamp,
    )

list_changed_paths_with_base_map = import_attr("git_change_paths", "list_changed_paths_with_base_map")
GuardContext = import_attr("rust_guard_common", "GuardContext")

REPO_ROOT = Path(__file__).resolve().parents[3]
guard = GuardContext(REPO_ROOT)

TARGET_ROOTS = (*resolve_quality_scope_roots("python_guard", repo_root=REPO_ROOT),)
SUPPRESSION_PATTERNS = {
    "noqa": re.compile(r"^#\s*noqa(?:\b|:)", re.IGNORECASE),
    "type_ignore": re.compile(r"^#\s*type:\s*ignore\b", re.IGNORECASE),
    "pylint_disable": re.compile(r"^#\s*pylint:\s*disable(?:\b|=)", re.IGNORECASE),
    "pyright_ignore": re.compile(r"^#\s*pyright:\s*ignore\b", re.IGNORECASE),
}
SUPPRESSION_LABELS = {
    "noqa": "# noqa",
    "type_ignore": "# type: ignore",
    "pylint_disable": "# pylint: disable",
    "pyright_ignore": "# pyright: ignore",
}


def _empty_counts() -> dict[str, int]:
    return {key: 0 for key in SUPPRESSION_PATTERNS}


def _iter_comment_tokens(text: str | None) -> tuple[str, ...]:
    if text is None:
        return ()
    try:
        stream = io.StringIO(text)
        return tuple(
            token.string for token in tokenize.generate_tokens(stream.readline) if token.type == tokenize.COMMENT
        )
    except (SyntaxError, tokenize.TokenError):
        return ()


def _count_suppressions(text: str | None) -> dict[str, int]:
    counts = _empty_counts()
    for comment in _iter_comment_tokens(text):
        for kind, pattern in SUPPRESSION_PATTERNS.items():
            if pattern.search(comment):
                counts[kind] += 1
    return counts


def _growth(base: dict[str, int], current: dict[str, int]) -> dict[str, int]:
    return {key: current[key] - base[key] for key in base}


def _has_positive_growth(growth: dict[str, int]) -> bool:
    return any(value > 0 for value in growth.values())


def _format_growth(growth: dict[str, int]) -> str:
    parts = [f"{SUPPRESSION_LABELS[kind]} {value:+d}" for kind, value in growth.items() if value != 0]
    return ", ".join(parts) if parts else "none"


def build_report(
    *,
    repo_root: Path = REPO_ROOT,
    candidate_paths: list[Path],
    base_text_by_path: dict[str, str | None],
    current_text_by_path: dict[str, str | None],
    mode: str,
) -> dict:
    files_considered = 0
    files_skipped_non_python = 0
    violations: list[dict] = []
    totals = {f"{kind}_growth": 0 for kind in SUPPRESSION_PATTERNS}

    for candidate in candidate_paths:
        if candidate.suffix != ".py":
            files_skipped_non_python += 1
            continue
        if not is_under_target_roots(
            candidate,
            repo_root=repo_root,
            target_roots=TARGET_ROOTS,
        ):
            files_skipped_non_python += 1
            continue

        relative_path = candidate.relative_to(repo_root).as_posix() if candidate.is_absolute() else candidate.as_posix()
        files_considered += 1

        base = _count_suppressions(base_text_by_path.get(relative_path))
        current = _count_suppressions(current_text_by_path.get(relative_path))
        growth = _growth(base, current)

        for kind, value in growth.items():
            totals[f"{kind}_growth"] += value

        if _has_positive_growth(growth):
            violations.append(
                {
                    "path": relative_path,
                    "base": base,
                    "current": current,
                    "growth": growth,
                }
            )

    return {
        "command": "check_python_suppression_debt",
        "timestamp": utc_timestamp(),
        "mode": mode,
        "ok": len(violations) == 0,
        "files_changed": len(candidate_paths),
        "files_considered": files_considered,
        "files_skipped_non_python": files_skipped_non_python,
        "totals": totals,
        "violations": violations,
    }


def _render_md(report: dict) -> str:
    lines = ["# check_python_suppression_debt", ""]
    lines.append(f"- mode: {report['mode']}")
    lines.append(f"- ok: {report['ok']}")
    lines.append(f"- files_changed: {report['files_changed']}")
    lines.append(f"- files_considered: {report['files_considered']}")
    lines.append(f"- files_skipped_non_python: {report['files_skipped_non_python']}")
    lines.append(f"- violations: {len(report['violations'])}")
    if report.get("since_ref"):
        lines.append(f"- since_ref: {report['since_ref']}")
    if report.get("head_ref"):
        lines.append(f"- head_ref: {report['head_ref']}")

    aggregate_growth = {kind: report["totals"][f"{kind}_growth"] for kind in SUPPRESSION_PATTERNS}
    lines.append(f"- aggregate_growth: {_format_growth(aggregate_growth)}")

    if report["violations"]:
        lines.append("")
        lines.append("## Violations")
        lines.append(
            "- Guidance: prefer fixing the underlying lint/type issue or "
            "tightening module boundaries over adding more suppression comments."
        )
        lines.append(
            "- Guidance: if a suppression is genuinely unavoidable, isolate it to "
            "one compatibility boundary instead of spreading it through the file."
        )
        for item in report["violations"]:
            lines.append(f"- `{item['path']}`: {_format_growth(item['growth'])}")
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    return build_since_ref_format_parser(__doc__ or "")


def main() -> int:
    args = _build_parser().parse_args()

    try:
        if args.since_ref:
            guard.validate_ref(args.since_ref)
            guard.validate_ref(args.head_ref)
        changed_paths, base_map = list_changed_paths_with_base_map(
            guard.run_git,
            args.since_ref,
            args.head_ref,
        )
    except RuntimeError as exc:
        return emit_runtime_error("check_python_suppression_debt", args.format, str(exc))

    base_text_by_path: dict[str, str | None] = {}
    current_text_by_path: dict[str, str | None] = {}
    for path in changed_paths:
        if path.suffix != ".py":
            continue
        relative_path = path.as_posix()
        base_path = base_map.get(path, path)
        if args.since_ref:
            base_text = guard.read_text_from_ref(base_path, args.since_ref)
            current_text = guard.read_text_from_ref(path, args.head_ref)
        else:
            base_text = guard.read_text_from_ref(base_path, "HEAD")
            current_text = guard.read_text_from_worktree(path)
        base_text_by_path[relative_path] = base_text
        current_text_by_path[relative_path] = current_text

    report = build_report(
        repo_root=REPO_ROOT,
        candidate_paths=changed_paths,
        base_text_by_path=base_text_by_path,
        current_text_by_path=current_text_by_path,
        mode="commit-range" if args.since_ref else "working-tree",
    )
    report["since_ref"] = args.since_ref
    report["head_ref"] = args.head_ref

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(_render_md(report))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
