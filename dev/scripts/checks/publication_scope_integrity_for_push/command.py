"""Run publication-scope integrity against the push preflight ref range."""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import replace
from pathlib import Path

try:
    from check_publication_scope_integrity import (
        REPO_ROOT,
        emit_runtime_error,
        evaluate_publication_scope_integrity,
        render_markdown,
    )
except ModuleNotFoundError:
    from dev.scripts.checks.check_publication_scope_integrity import (
        REPO_ROOT,
        emit_runtime_error,
        evaluate_publication_scope_integrity,
        render_markdown,
    )


COMMAND = "check_publication_scope_integrity_for_push"


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        base_sha, base_warnings = _resolve_ref(args.base_ref, "base_ref")
        head_sha, head_warnings = _resolve_ref(args.head_ref, "head_ref")
        report = evaluate_publication_scope_integrity(
            base_sha=base_sha,
            head_sha=head_sha,
        )
        report = _append_warnings(report, (*base_warnings, *head_warnings))
    # broad-except: allow reason=top-level guard CLI safety fallback=emit_runtime_error
    except Exception as exc:
        emit_runtime_error(COMMAND, exc, format=getattr(args, "format", "json"))
        return 2
    if args.format == "md":
        print(render_markdown(report))
    else:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    return 0 if report.ok else 1


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-ref", required=True)
    parser.add_argument("--head-ref", required=True)
    parser.add_argument("--format", choices=("json", "md"), default="json")
    return parser.parse_args(argv)


def _resolve_ref(ref: str, label: str) -> tuple[str, tuple[str, ...]]:
    text = str(ref or "").strip()
    result = subprocess.run(
        ("git", "rev-parse", "--verify", text),
        cwd=Path(REPO_ROOT),
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode == 0:
        return result.stdout.strip(), ()
    detail = result.stderr.strip() or result.stdout.strip() or "git command failed"
    return "", (f"{label}_unavailable:{detail}",)


def _append_warnings(report, warnings: tuple[str, ...]):
    if not warnings:
        return report
    return replace(report, ok=False, warnings=(*warnings, *report.warnings))


if __name__ == "__main__":
    raise SystemExit(main())
