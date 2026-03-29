#!/usr/bin/env python3
"""Block new cross-layer Python imports that violate repo-owned platform boundaries."""

from __future__ import annotations

import ast
import json
import sys
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path

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


@dataclass(frozen=True, slots=True)
class BoundaryRule:
    rule_id: str
    include_globs: tuple[str, ...]
    exclude_globs: tuple[str, ...]
    forbidden_import_prefixes: tuple[str, ...]
    allow_import_prefixes: tuple[str, ...]
    guidance: str


@dataclass(frozen=True, slots=True)
class ImportHit:
    import_name: str
    lineno: int


def _coerce_strings(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    values: list[str] = []
    for item in value:
        text = str(item).strip()
        if text:
            values.append(text)
    return tuple(values)


def coerce_boundary_rules(config: dict[str, object]) -> tuple[BoundaryRule, ...]:
    raw_rules = config.get("rules")
    if not isinstance(raw_rules, list):
        return ()
    rules: list[BoundaryRule] = []
    for index, raw_rule in enumerate(raw_rules, start=1):
        if not isinstance(raw_rule, dict):
            continue
        include_globs = _coerce_strings(raw_rule.get("include_globs"))
        forbidden_prefixes = _coerce_strings(raw_rule.get("forbidden_import_prefixes"))
        if not include_globs or not forbidden_prefixes:
            continue
        rule_id = str(raw_rule.get("rule_id") or f"rule_{index}").strip()
        guidance = str(raw_rule.get("guidance") or "").strip()
        if not guidance:
            guidance = (
                "Move the dependency behind a shared runtime/adaptor contract instead "
                "of importing the forbidden layer directly."
            )
        rules.append(
            BoundaryRule(
                rule_id=rule_id,
                include_globs=include_globs,
                exclude_globs=_coerce_strings(raw_rule.get("exclude_globs")),
                forbidden_import_prefixes=forbidden_prefixes,
                allow_import_prefixes=_coerce_strings(raw_rule.get("allow_import_prefixes")),
                guidance=guidance,
            )
        )
    return tuple(rules)


def _normalize_relative_path(repo_root: Path, path: Path) -> Path:
    return path.relative_to(repo_root) if path.is_absolute() else path


def _matches_any(path: Path, patterns: tuple[str, ...]) -> bool:
    path_text = path.as_posix()
    return any(fnmatch(path_text, pattern) for pattern in patterns)


def _matches_import_prefix(import_name: str, prefix: str) -> bool:
    return import_name == prefix or import_name.startswith(f"{prefix}.")


def parse_import_hits(text: str) -> tuple[ImportHit, ...]:
    tree = ast.parse(text)
    hits: list[ImportHit] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                hits.append(ImportHit(import_name=alias.name, lineno=node.lineno))
            continue
        if not isinstance(node, ast.ImportFrom) or not node.module or node.level:
            continue
        if any(alias.name == "*" for alias in node.names):
            hits.append(ImportHit(import_name=node.module, lineno=node.lineno))
            continue
        for alias in node.names:
            hits.append(
                ImportHit(
                    import_name=f"{node.module}.{alias.name}",
                    lineno=node.lineno,
                )
            )
    return tuple(hits)


def _candidate_rule_map(
    repo_root: Path,
    candidate_paths: list[Path],
    rules: tuple[BoundaryRule, ...],
) -> dict[Path, tuple[BoundaryRule, ...]]:
    rule_map: dict[Path, tuple[BoundaryRule, ...]] = {}
    for candidate in candidate_paths:
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


def collect_boundary_violations(
    *,
    repo_root: Path,
    candidate_paths: list[Path],
    rules: tuple[BoundaryRule, ...],
    read_text,
) -> tuple[list[dict[str, object]], int]:
    violations: list[dict[str, object]] = []
    rule_map = _candidate_rule_map(repo_root, candidate_paths, rules)
    for relative_path, matched_rules in sorted(rule_map.items()):
        text = read_text(relative_path)
        if text is None:
            continue
        try:
            import_hits = parse_import_hits(text)
        except SyntaxError as exc:
            violations.append(
                {
                    "path": relative_path.as_posix(),
                    "line": exc.lineno or 1,
                    "rule_id": "syntax_error",
                    "import_name": "(unparsed)",
                    "forbidden_prefix": "",
                    "guidance": "Fix the Python syntax error before the boundary guard can evaluate imports.",
                }
            )
            continue
        for rule in matched_rules:
            for hit in import_hits:
                if any(
                    _matches_import_prefix(hit.import_name, prefix)
                    for prefix in rule.allow_import_prefixes
                ):
                    continue
                forbidden_prefix = next(
                    (
                        prefix
                        for prefix in rule.forbidden_import_prefixes
                        if _matches_import_prefix(hit.import_name, prefix)
                    ),
                    None,
                )
                if forbidden_prefix is None:
                    continue
                violations.append(
                    {
                        "path": relative_path.as_posix(),
                        "line": hit.lineno,
                        "rule_id": rule.rule_id,
                        "import_name": hit.import_name,
                        "forbidden_prefix": forbidden_prefix,
                        "guidance": rule.guidance,
                    }
                )
    violations.sort(key=lambda row: (str(row["path"]), int(row["line"]), str(row["import_name"])))
    return violations, len(rule_map)


def _render_md(report: dict[str, object]) -> str:
    lines = ["# check_platform_layer_boundaries", ""]
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
            lines.append(
                f"- `{violation['path']}:{violation['line']}` imports "
                f"`{violation['import_name']}` (`{violation['rule_id']}`): "
                f"{violation['guidance']}"
            )
    return "\n".join(lines)


def _worktree_python_paths(repo_root: Path) -> list[Path]:
    return sorted(path.relative_to(repo_root) for path in repo_root.rglob("*.py"))


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
        return emit_runtime_error("check_platform_layer_boundaries", args.format, str(exc))

    candidate_paths = _worktree_python_paths(REPO_ROOT) if adoption_scan else changed_paths
    rules = coerce_boundary_rules(resolve_guard_config("platform_layer_boundaries", repo_root=REPO_ROOT))
    read_text = (
        (lambda path: guard.read_text_from_ref(path, args.head_ref))
        if args.since_ref and not adoption_scan
        else guard.read_text_from_worktree
    )
    violations, candidates_scanned = collect_boundary_violations(
        repo_root=REPO_ROOT,
        candidate_paths=candidate_paths,
        rules=rules,
        read_text=read_text,
    )
    report = {
        "command": "check_platform_layer_boundaries",
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
