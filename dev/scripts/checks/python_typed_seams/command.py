#!/usr/bin/env python3
"""Block `object` + `getattr()` bags on configured typed Python seams."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

try:
    from check_bootstrap import (
        REPO_ROOT,
        build_since_ref_format_parser,
        emit_runtime_error,
        import_attr,
        resolve_guard_config,
        utc_timestamp,
    )
except ModuleNotFoundError:  # pragma: no cover - import fallback for package-style test loading
    from dev.scripts.checks.check_bootstrap import (
        REPO_ROOT,
        build_since_ref_format_parser,
        emit_runtime_error,
        import_attr,
        resolve_guard_config,
        utc_timestamp,
    )

try:
    from dev.scripts.devctl.quality_scan_mode import is_adoption_scan
except ModuleNotFoundError:  # pragma: no cover
    repo_root_str = str(REPO_ROOT)
    if repo_root_str not in sys.path:
        sys.path.insert(0, repo_root_str)
    from dev.scripts.devctl.quality_scan_mode import is_adoption_scan

list_changed_paths = import_attr("rust_guard_common", "list_changed_paths")
GuardContext = import_attr("rust_guard_common", "GuardContext")

guard = GuardContext(REPO_ROOT)

try:
    from .scanner import parse_object_getattr_hits
except ImportError:  # pragma: no cover - direct file loading in tests
    from scanner import parse_object_getattr_hits


@dataclass(frozen=True, slots=True)
class TypedSeamRule:
    rule_id: str
    include_globs: tuple[str, ...]
    exclude_globs: tuple[str, ...]
    min_object_getattr_calls: int
    guidance: str


def _coerce_strings(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(text for item in value if (text := str(item).strip()))


def _coerce_positive_int(value: object, *, default: int) -> int:
    if value is None:
        return default
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def coerce_typed_seam_rules(config: dict[str, object]) -> tuple[TypedSeamRule, ...]:
    raw_rules = config.get("rules")
    if not isinstance(raw_rules, list):
        return ()
    rules: list[TypedSeamRule] = []
    for index, raw_rule in enumerate(raw_rules, start=1):
        if not isinstance(raw_rule, dict):
            continue
        include_globs = _coerce_strings(raw_rule.get("include_globs"))
        if not include_globs:
            continue
        rule_id = str(raw_rule.get("rule_id") or f"rule_{index}").strip()
        guidance = str(raw_rule.get("guidance") or "").strip()
        if not guidance:
            guidance = (
                "Convert the boundary bag into a typed dataclass, TypedDict, or "
                "Protocol-backed contract before fixed-field access."
            )
        rules.append(
            TypedSeamRule(
                rule_id=rule_id,
                include_globs=include_globs,
                exclude_globs=_coerce_strings(raw_rule.get("exclude_globs")),
                min_object_getattr_calls=_coerce_positive_int(
                    raw_rule.get("min_object_getattr_calls"),
                    default=1,
                ),
                guidance=guidance,
            )
        )
    return tuple(rules)


def _normalize_relative_path(repo_root: Path, path: Path) -> Path:
    return path.relative_to(repo_root) if path.is_absolute() else path


def _matches_any(path: Path, patterns: tuple[str, ...]) -> bool:
    pure_path = PurePosixPath(path.as_posix())
    for pattern in patterns:
        variants = {pattern}
        if "/**/" in pattern:
            variants.add(pattern.replace("/**/", "/"))
        if any(pure_path.match(variant) for variant in variants):
            return True
    return False


def _candidate_rule_map(
    repo_root: Path,
    candidate_paths: list[Path],
    rules: tuple[TypedSeamRule, ...],
) -> dict[Path, tuple[TypedSeamRule, ...]]:
    rule_map: dict[Path, tuple[TypedSeamRule, ...]] = {}
    for candidate in candidate_paths:
        if candidate.suffix != ".py":
            continue
        relative = _normalize_relative_path(repo_root, candidate)
        matched_rules = tuple(
            rule
            for rule in rules
            if _matches_any(relative, rule.include_globs)
            and not _matches_any(relative, rule.exclude_globs)
        )
        if matched_rules:
            rule_map[relative] = matched_rules
    return rule_map


def collect_typed_seam_violations(
    *,
    repo_root: Path,
    candidate_paths: list[Path],
    rules: tuple[TypedSeamRule, ...],
    read_text,
) -> tuple[list[dict[str, object]], int]:
    violations: list[dict[str, object]] = []
    rule_map = _candidate_rule_map(repo_root, candidate_paths, rules)
    for relative_path, matched_rules in sorted(rule_map.items()):
        text = read_text(relative_path)
        if text is None:
            continue
        try:
            function_hits = parse_object_getattr_hits(text)
        except SyntaxError as exc:
            violations.append(
                {
                    "path": relative_path.as_posix(),
                    "line": exc.lineno or 1,
                    "rule_id": "syntax_error",
                    "function_name": "(unparsed)",
                    "param_name": "",
                    "getattr_count": 0,
                    "attr_names": (),
                    "hit_lines": (),
                    "guidance": "Fix the Python syntax error before the typed-seam guard can evaluate the file.",
                }
            )
            continue
        for rule in matched_rules:
            for hit in function_hits:
                if int(hit["getattr_count"]) < rule.min_object_getattr_calls:
                    continue
                violations.append(
                    {
                        "path": relative_path.as_posix(),
                        "line": int(hit["function_line"]),
                        "rule_id": rule.rule_id,
                        "function_name": hit["function_name"],
                        "param_name": hit["param_name"],
                        "getattr_count": int(hit["getattr_count"]),
                        "attr_names": tuple(hit["attr_names"]),
                        "hit_lines": tuple(hit["hit_lines"]),
                        "guidance": rule.guidance,
                    }
                )
    violations.sort(
        key=lambda row: (
            str(row["path"]),
            int(row["line"]),
            str(row["function_name"]),
            str(row["param_name"]),
        )
    )
    return violations, len(rule_map)


def _worktree_python_paths(repo_root: Path) -> list[Path]:
    return sorted(path.relative_to(repo_root) for path in repo_root.rglob("*.py"))


def _render_md(report: dict[str, object]) -> str:
    lines = ["# check_python_typed_seams", ""]
    lines.append(f"- mode: {report['mode']}")
    lines.append(f"- ok: {report['ok']}")
    lines.append(f"- files_changed: {report['files_changed']}")
    lines.append(f"- configured_rules: {report['configured_rules']}")
    lines.append(f"- candidates_scanned: {report['candidates_scanned']}")
    lines.append(f"- violations: {len(report['violations'])}")
    if report.get("since_ref"):
        lines.append(f"- since_ref: {report['since_ref']}")
    if report.get("head_ref"):
        lines.append(f"- head_ref: {report['head_ref']}")
    if report["violations"]:
        lines.extend(("", "## Violations"))
        for violation in report["violations"]:
            attr_names = ", ".join(f"`{name}`" for name in violation["attr_names"]) or "(none)"
            lines.append(
                f"- `{violation['path']}:{violation['line']}` "
                f"`{violation['function_name']}` uses `getattr()` {violation['getattr_count']} "
                f"time(s) on `object` parameter `{violation['param_name']}` "
                f"for {attr_names} (`{violation['rule_id']}`): {violation['guidance']}"
            )
    return "\n".join(lines)


def main() -> int:
    args = build_since_ref_format_parser(__doc__ or "").parse_args()
    adoption_scan = is_adoption_scan(since_ref=args.since_ref, head_ref=args.head_ref)
    mode = "adoption-scan" if adoption_scan else ("commit-range" if args.since_ref else "working-tree")
    try:
        if args.since_ref:
            guard.validate_ref(args.since_ref)
            guard.validate_ref(args.head_ref)
        changed_paths = list_changed_paths(guard.run_git, args.since_ref, args.head_ref)
    except RuntimeError as exc:
        return emit_runtime_error("check_python_typed_seams", args.format, str(exc))

    candidate_paths = _worktree_python_paths(REPO_ROOT) if adoption_scan else changed_paths
    rules = coerce_typed_seam_rules(resolve_guard_config("python_typed_seams", repo_root=REPO_ROOT))
    read_text = (
        (lambda path: guard.read_text_from_ref(path, args.head_ref))
        if args.since_ref and not adoption_scan
        else guard.read_text_from_worktree
    )
    violations, candidates_scanned = collect_typed_seam_violations(
        repo_root=REPO_ROOT,
        candidate_paths=candidate_paths,
        rules=rules,
        read_text=read_text,
    )
    report = {
        "command": "check_python_typed_seams",
        "timestamp": utc_timestamp(),
        "mode": mode,
        "since_ref": None if adoption_scan else args.since_ref,
        "head_ref": None if adoption_scan else args.head_ref,
        "ok": len(violations) == 0,
        "files_changed": len(changed_paths),
        "configured_rules": len(rules),
        "candidates_scanned": candidates_scanned,
        "violations": violations,
    }
    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(_render_md(report))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
