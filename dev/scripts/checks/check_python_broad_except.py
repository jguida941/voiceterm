#!/usr/bin/env python3
"""Guard new broad Python exception handlers with explicit rationale/contracts."""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path

try:
    from check_bootstrap import (
        emit_runtime_error,
        import_attr,
        is_under_target_roots,
        utc_timestamp,
    )
except ModuleNotFoundError:  # pragma: no cover - package-style fallback for tests
    from dev.scripts.checks.check_bootstrap import (
        emit_runtime_error,
        import_attr,
        is_under_target_roots,
        utc_timestamp,
    )

list_changed_paths_with_base_map = import_attr(
    "git_change_paths", "list_changed_paths_with_base_map"
)
GuardContext = import_attr("rust_guard_common", "GuardContext")

REPO_ROOT = Path(__file__).resolve().parents[3]
guard = GuardContext(REPO_ROOT)

TARGET_ROOTS = (
    Path("dev/scripts"),
    Path("app/operator_console"),
)
HUNK_RE = re.compile(
    r"^@@ -\d+(?:,\d+)? \+(?P<start>\d+)(?:,(?P<count>\d+))? @@"
)
RATIONALE_RE = re.compile(r"broad-except:\s*allow\b.*\breason\s*=")
FALLBACK_RE = re.compile(r"broad-except:\s*allow\b.*\bfallback\s*=")


def _is_test_path(path: Path) -> bool:
    return "tests" in path.parts or path.name.startswith("test_")
def _collect_python_paths(
    *,
    repo_root: Path,
    candidate_paths: list[Path],
) -> tuple[list[Path], int]:
    paths: set[Path] = set()
    skipped_tests = 0
    for candidate in candidate_paths:
        if candidate.suffix != ".py":
            continue
        if not is_under_target_roots(
            candidate, repo_root=repo_root, target_roots=TARGET_ROOTS
        ):
            continue
        relative = (
            candidate.relative_to(repo_root)
            if candidate.is_absolute()
            else candidate
        )
        if _is_test_path(relative):
            skipped_tests += 1
            continue
        paths.add(repo_root / candidate if not candidate.is_absolute() else candidate)
    return sorted(paths), skipped_tests


def _handler_kind(node_type: ast.expr | None) -> str | None:
    if node_type is None:
        return "bare"
    if isinstance(node_type, ast.Name) and node_type.id in {"Exception", "BaseException"}:
        return node_type.id
    if isinstance(node_type, ast.Attribute) and node_type.attr in {
        "Exception",
        "BaseException",
    }:
        return node_type.attr
    if isinstance(node_type, ast.Tuple):
        members = sorted(
            {
                kind
                for element in node_type.elts
                for kind in [_handler_kind(element)]
                if kind is not None
            }
        )
        if members:
            return ",".join(members)
    return None


def _has_contract_token(
    lines: list[str], line_number: int, *, token_pattern: re.Pattern[str]
) -> bool:
    index = line_number - 1
    if index < 0 or index >= len(lines):
        return False
    if token_pattern.search(lines[index]):
        return True
    probe = index - 1
    while probe >= 0:
        raw = lines[probe].strip()
        if not raw:
            break
        if raw.startswith("#"):
            if token_pattern.search(raw):
                return True
            probe -= 1
            continue
        break
    return False


def _has_rationale(lines: list[str], line_number: int) -> bool:
    return _has_contract_token(lines, line_number, token_pattern=RATIONALE_RE)


def _has_fallback_contract(lines: list[str], line_number: int) -> bool:
    return _has_contract_token(lines, line_number, token_pattern=FALLBACK_RE)


def _handler_suppresses_control_flow(handler: ast.ExceptHandler) -> bool:
    stack = list(handler.body)
    while stack:
        node = stack.pop()
        if isinstance(node, ast.Raise):
            return False
        if isinstance(
            node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)
        ):
            continue
        stack.extend(ast.iter_child_nodes(node))
    return True


def _collect_broad_except_handlers(text: str) -> list[dict]:
    tree = ast.parse(text)
    lines = text.splitlines()
    handlers: list[dict] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ExceptHandler):
            continue
        kind = _handler_kind(node.type)
        if kind is None:
            continue
        handlers.append(
            {
                "line": node.lineno,
                "kind": kind,
                "documented": _has_rationale(lines, node.lineno),
                "fallback_documented": _has_fallback_contract(lines, node.lineno),
                "suppresses": _handler_suppresses_control_flow(node),
            }
        )
    return handlers


def _parse_added_line_numbers(diff_text: str) -> set[int]:
    added_lines: set[int] = set()
    for line in diff_text.splitlines():
        match = HUNK_RE.match(line)
        if match is None:
            continue
        start = int(match.group("start"))
        count = int(match.group("count") or "1")
        if count <= 0:
            continue
        added_lines.update(range(start, start + count))
    return added_lines


def _diff_added_lines(path: Path, *, since_ref: str | None, head_ref: str) -> set[int]:
    relative = (
        path.relative_to(REPO_ROOT).as_posix()
        if path.is_absolute()
        else path.as_posix()
    )
    if since_ref:
        cmd = ["git", "diff", "--unified=0", since_ref, head_ref, "--", relative]
    else:
        cmd = ["git", "diff", "--unified=0", "HEAD", "--", relative]
    result = guard.run_git(cmd, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"failed to diff {relative}")
    return _parse_added_line_numbers(result.stdout)


def build_report(
    *,
    repo_root: Path = REPO_ROOT,
    candidate_paths: list[Path],
    added_lines_by_path: dict[str, set[int] | None],
    mode: str,
    since_ref: str | None = None,
    head_ref: str | None = None,
) -> dict:
    files, skipped_tests = _collect_python_paths(
        repo_root=repo_root,
        candidate_paths=candidate_paths,
    )
    broad_handlers = 0
    candidate_handlers = 0
    documented_candidate_handlers = 0
    suppressive_candidate_handlers = 0
    fallback_documented_candidate_handlers = 0
    violations: list[dict] = []
    parse_errors: list[dict] = []

    for path in files:
        relative_path = path.relative_to(repo_root).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
            handlers = _collect_broad_except_handlers(text)
        except (OSError, SyntaxError, UnicodeDecodeError) as exc:
            parse_errors.append({"path": relative_path, "error": str(exc)})
            continue

        broad_handlers += len(handlers)
        added_lines = added_lines_by_path.get(relative_path)
        for handler in handlers:
            if added_lines is not None and handler["line"] not in added_lines:
                continue
            candidate_handlers += 1
            if handler["documented"]:
                documented_candidate_handlers += 1
            else:
                violations.append(
                    {
                        "path": relative_path,
                        "line": handler["line"],
                        "kind": handler["kind"],
                        "reason": (
                            "new broad exception handler is missing "
                            "`broad-except: allow reason=...` rationale"
                        ),
                    }
                )
                continue

            if not handler["suppresses"]:
                continue
            suppressive_candidate_handlers += 1
            if handler["fallback_documented"]:
                fallback_documented_candidate_handlers += 1
                continue
            violations.append(
                {
                    "path": relative_path,
                    "line": handler["line"],
                    "kind": handler["kind"],
                    "reason": (
                        "new suppressive broad exception handler is missing "
                        "`broad-except: allow reason=... fallback=...` contract"
                    ),
                }
            )

    return {
        "command": "check_python_broad_except",
        "timestamp": utc_timestamp(),
        "ok": not violations and not parse_errors,
        "mode": mode,
        "since_ref": since_ref,
        "head_ref": head_ref,
        "files_scanned": len(files),
        "files_skipped_tests": skipped_tests,
        "broad_handlers": broad_handlers,
        "candidate_handlers": candidate_handlers,
        "documented_candidate_handlers": documented_candidate_handlers,
        "suppressive_candidate_handlers": suppressive_candidate_handlers,
        "fallback_documented_candidate_handlers": fallback_documented_candidate_handlers,
        "violations": violations,
        "parse_errors": parse_errors,
        "target_roots": [path.as_posix() for path in TARGET_ROOTS],
    }


def _render_md(report: dict) -> str:
    lines = ["# check_python_broad_except", ""]
    lines.append(f"- mode: {report['mode']}")
    lines.append(f"- ok: {report['ok']}")
    lines.append(f"- files_scanned: {report['files_scanned']}")
    lines.append(f"- files_skipped_tests: {report['files_skipped_tests']}")
    lines.append(f"- broad_handlers: {report['broad_handlers']}")
    lines.append(f"- candidate_handlers: {report['candidate_handlers']}")
    lines.append(
        f"- documented_candidate_handlers: {report['documented_candidate_handlers']}"
    )
    lines.append(
        f"- suppressive_candidate_handlers: {report['suppressive_candidate_handlers']}"
    )
    lines.append(
        "- fallback_documented_candidate_handlers: "
        f"{report['fallback_documented_candidate_handlers']}"
    )
    lines.append(f"- violations: {len(report['violations'])}")
    lines.append(f"- parse_errors: {len(report['parse_errors'])}")
    if report.get("since_ref"):
        lines.append(f"- since_ref: {report['since_ref']}")
    if report.get("head_ref"):
        lines.append(f"- head_ref: {report['head_ref']}")

    if report["parse_errors"]:
        lines.append("")
        lines.append("## Parse errors")
        for item in report["parse_errors"]:
            lines.append(f"- `{item['path']}`: {item['error']}")

    if report["violations"]:
        lines.append("")
        lines.append("## Violations")
        lines.append(
            "- Guidance: new `except Exception`, `except BaseException`, and "
            "bare `except:` handlers in repo-owned Python tooling/app code "
            "require an explicit nearby `broad-except: allow reason=...` rationale. "
            "If the handler suppresses control-flow by not re-raising, it must also "
            "declare `fallback=...`."
        )
        for item in report["violations"]:
            lines.append(
                f"- `{item['path']}:{item['line']}` ({item['kind']}): {item['reason']}"
            )
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--since-ref", help="Compare against this git ref")
    parser.add_argument(
        "--head-ref", default="HEAD", help="Head ref used with --since-ref"
    )
    parser.add_argument(
        "--paths",
        nargs="+",
        help="Target explicit repo-relative paths instead of a git diff",
    )
    parser.add_argument("--format", choices=("md", "json"), default="md")
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    try:
        if args.paths:
            candidate_paths = [Path(raw) for raw in args.paths]
            added_lines_by_path = {path.as_posix(): None for path in candidate_paths}
            report = build_report(
                repo_root=REPO_ROOT,
                candidate_paths=candidate_paths,
                added_lines_by_path=added_lines_by_path,
                mode="paths",
                head_ref=args.head_ref,
            )
        else:
            if args.since_ref:
                guard.validate_ref(args.since_ref)
                guard.validate_ref(args.head_ref)
            changed_paths, base_map = list_changed_paths_with_base_map(
                guard.run_git,
                args.since_ref,
                args.head_ref,
            )
            added_lines_by_path: dict[str, set[int] | None] = {}
            for path in changed_paths:
                if path.suffix != ".py":
                    continue
                if not is_under_target_roots(
                    path, repo_root=REPO_ROOT, target_roots=TARGET_ROOTS
                ):
                    continue
                relative = path.as_posix()
                base_path = base_map.get(path, path)
                if guard.read_text_from_ref(base_path, args.since_ref or "HEAD") is None:
                    added_lines_by_path[relative] = None
                    continue
                added_lines_by_path[relative] = _diff_added_lines(
                    path,
                    since_ref=args.since_ref,
                    head_ref=args.head_ref,
                )
            report = build_report(
                repo_root=REPO_ROOT,
                candidate_paths=changed_paths,
                added_lines_by_path=added_lines_by_path,
                mode="commit-range" if args.since_ref else "working-tree",
                since_ref=args.since_ref,
                head_ref=args.head_ref,
            )
    except RuntimeError as exc:
        return emit_runtime_error("check_python_broad_except", args.format, str(exc))

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(_render_md(report))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
