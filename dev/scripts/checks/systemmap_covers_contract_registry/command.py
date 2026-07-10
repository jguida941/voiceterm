"""Ensure SYSTEM_MAP renders every platform contract-registry id."""

from __future__ import annotations

import argparse
import ast
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence

try:
    from check_bootstrap import REPO_ROOT, emit_runtime_error
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT, emit_runtime_error

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dev.scripts.devctl.platform.contract_registry import (  # noqa: E402
    contract_registry_path,
    read_contract_registry_rows,
)
from dev.scripts.devctl.platform.system_map import (  # noqa: E402
    GENERATED_BLOCK_BEGIN,
    GENERATED_BLOCK_END,
    build_system_map_snapshot,
    render_system_map_markdown,
)

COMMAND = "check_systemmap_covers_contract_registry"
DEFAULT_SYSTEM_MAP_REL = "dev/guides/SYSTEM_MAP.md"
DEFAULT_AUTHORITY_CONTRACT_ID_GLOBS = ("dev/scripts/devctl/platform/*.py",)
REFRESH_COMMAND = (
    "python3 dev/scripts/devctl.py render-surfaces --write --surface "
    "system_map_index --format md"
)


@dataclass(frozen=True, slots=True)
class SystemMapContractCoverageViolation:
    rule: str
    contract_id: str
    detail: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class AuthorityContractIdDeclaration:
    contract_id: str
    path: str
    line_number: int
    source: str


@dataclass(frozen=True, slots=True)
class AuthorityContractIdCoverageViolation:
    rule: str
    contract_id: str
    path: str
    line_number: int
    source: str
    detail: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def evaluate_systemmap_contract_coverage(
    *,
    repo_root: Path = REPO_ROOT,
    registry_path: Path | None = None,
    system_map_path: Path | None = None,
    authority_contract_paths: Sequence[Path] | None = None,
) -> tuple[dict[str, object], tuple[SystemMapContractCoverageViolation, ...]]:
    """Return coverage metadata and violations for registry-to-SYSTEM_MAP drift."""
    resolved_registry_path = registry_path or contract_registry_path(repo_root)
    resolved_system_map_path = system_map_path or repo_root / DEFAULT_SYSTEM_MAP_REL
    rows = read_contract_registry_rows(resolved_registry_path)
    registry_contract_ids = tuple(
        sorted(
            {
                row.registered_contract_id
                for row in rows
                if row.registered_contract_id
            }
        )
    )
    registry_contract_id_set = set(registry_contract_ids)
    authority_declarations, authority_scan_errors = (
        discover_authority_contract_id_declarations(
            repo_root=repo_root,
            authority_contract_paths=authority_contract_paths,
        )
    )
    authority_contract_ids = tuple(
        sorted({declaration.contract_id for declaration in authority_declarations})
    )
    authority_violations = tuple(
        AuthorityContractIdCoverageViolation(
            rule="missing-registry-row",
            contract_id=declaration.contract_id,
            path=declaration.path,
            line_number=declaration.line_number,
            source=declaration.source,
            detail=(
                "Authority file declares a contract_id literal without a matching "
                "contract registry row."
            ),
        )
        for declaration in authority_declarations
        if declaration.contract_id not in registry_contract_id_set
    )
    system_map_text = resolved_system_map_path.read_text(encoding="utf-8")
    generated_block = extract_generated_system_map_block(system_map_text)
    live_block = render_system_map_markdown(
        build_system_map_snapshot(repo_root=repo_root)
    )

    violations: list[SystemMapContractCoverageViolation] = []
    if generated_block is None:
        violations.append(
            SystemMapContractCoverageViolation(
                rule="missing-generated-system-map-block",
                contract_id="",
                detail=(
                    "SYSTEM_MAP.md is missing the devctl generated block markers; "
                    f"refresh with `{REFRESH_COMMAND}`."
                ),
            )
        )
        observed_block = ""
    else:
        observed_block = generated_block
        if generated_block != live_block:
            violations.append(
                SystemMapContractCoverageViolation(
                    rule="stale-generated-system-map-block",
                    contract_id="",
                    detail=(
                        "Generated SYSTEM_MAP block differs from live renderer "
                        f"output; refresh with `{REFRESH_COMMAND}`."
                    ),
                )
            )

    for contract_id in registry_contract_ids:
        if f"`{contract_id}`" in observed_block:
            continue
        violations.append(
            SystemMapContractCoverageViolation(
                rule="missing-contract-id",
                contract_id=contract_id,
                detail=(
                    "Contract registry id is absent from the generated SYSTEM_MAP "
                    "block as a backticked token."
                ),
            )
        )

    coverage = {
        "command": COMMAND,
        "schema_version": 1,
        "registry_path": _display_path(resolved_registry_path, repo_root=repo_root),
        "system_map_path": _display_path(resolved_system_map_path, repo_root=repo_root),
        "registry_row_count": len(rows),
        "unique_contract_count": len(registry_contract_ids),
        "missing_contract_ids": tuple(
            violation.contract_id
            for violation in violations
            if violation.rule == "missing-contract-id" and violation.contract_id
        ),
        "authority_contract_declaration_count": len(authority_declarations),
        "authority_contract_id_count": len(authority_contract_ids),
        "authority_contract_missing_ids": tuple(
            sorted({violation.contract_id for violation in authority_violations})
        ),
        "authority_contract_id_coverage_ok": not (
            authority_violations or authority_scan_errors
        ),
        "authority_contract_id_coverage_report_only": True,
        "authority_contract_id_coverage_would_fail": bool(
            authority_violations or authority_scan_errors
        ),
        "authority_contract_id_scan_errors": tuple(authority_scan_errors),
        "authority_contract_id_violations": tuple(
            violation.to_dict() for violation in authority_violations
        ),
        "generated_block_present": generated_block is not None,
        "generated_block_current": generated_block == live_block,
        "refresh_command": REFRESH_COMMAND,
        "ok": not violations,
    }
    return coverage, tuple(violations)


def extract_generated_system_map_block(text: str) -> str | None:
    """Return the generated block body, excluding markers."""
    begin_index = text.find(GENERATED_BLOCK_BEGIN)
    end_index = text.find(GENERATED_BLOCK_END)
    if begin_index == -1 or end_index == -1 or end_index <= begin_index:
        return None
    body_begin = begin_index + len(GENERATED_BLOCK_BEGIN)
    return text[body_begin:end_index].strip("\n")


def discover_authority_contract_id_declarations(
    *,
    repo_root: Path = REPO_ROOT,
    authority_contract_paths: Sequence[Path] | None = None,
) -> tuple[tuple[AuthorityContractIdDeclaration, ...], tuple[str, ...]]:
    """Find contract_id literals declared by platform authority files."""
    paths = _authority_contract_paths(
        repo_root=repo_root,
        authority_contract_paths=authority_contract_paths,
    )
    declarations: list[AuthorityContractIdDeclaration] = []
    errors: list[str] = []
    seen: set[tuple[str, str, int, str]] = set()
    for path in paths:
        display_path = _display_path(path, repo_root=repo_root)
        try:
            text = path.read_text(encoding="utf-8")
            tree = ast.parse(text, filename=display_path)
        except OSError as exc:
            errors.append(f"read-failed:{display_path}:{exc.__class__.__name__}")
            continue
        except SyntaxError as exc:
            errors.append(f"parse-failed:{display_path}:{exc.lineno}:{exc.msg}")
            continue
        for contract_id, line_number, source in _contract_id_literals(tree):
            key = (contract_id, display_path, line_number, source)
            if key in seen:
                continue
            seen.add(key)
            declarations.append(
                AuthorityContractIdDeclaration(
                    contract_id=contract_id,
                    path=display_path,
                    line_number=line_number,
                    source=source,
                )
            )
    return tuple(declarations), tuple(errors)


def _authority_contract_paths(
    *,
    repo_root: Path,
    authority_contract_paths: Sequence[Path] | None,
) -> tuple[Path, ...]:
    if authority_contract_paths is not None:
        return tuple(sorted({path.resolve() for path in authority_contract_paths}))
    paths: set[Path] = set()
    for pattern in DEFAULT_AUTHORITY_CONTRACT_ID_GLOBS:
        paths.update(repo_root.glob(pattern))
    return tuple(sorted(path for path in paths if path.is_file()))


def _contract_id_literals(tree: ast.AST) -> Iterable[tuple[str, int, str]]:
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            value = _string_literal(node.value)
            if value is None:
                continue
            for target in node.targets:
                if not isinstance(target, ast.Name):
                    continue
                if _is_contract_id_target(target.id):
                    yield value, node.lineno, target.id
        elif isinstance(node, ast.AnnAssign):
            value = _string_literal(node.value)
            if value is None or not isinstance(node.target, ast.Name):
                continue
            if _is_contract_id_target(node.target.id):
                yield value, node.lineno, node.target.id
        elif isinstance(node, ast.Call):
            for keyword in node.keywords:
                if keyword.arg != "contract_id":
                    continue
                value = _string_literal(keyword.value)
                if value is not None:
                    yield value, node.lineno, "keyword:contract_id"


def _is_contract_id_target(name: str) -> bool:
    return name == "contract_id" or name.endswith("CONTRACT_ID")


def _string_literal(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def build_report(
    *,
    repo_root: Path = REPO_ROOT,
    registry_path: Path | None = None,
    system_map_path: Path | None = None,
    authority_contract_paths: Sequence[Path] | None = None,
) -> dict[str, object]:
    coverage, violations = evaluate_systemmap_contract_coverage(
        repo_root=repo_root,
        registry_path=registry_path,
        system_map_path=system_map_path,
        authority_contract_paths=authority_contract_paths,
    )
    return {
        **coverage,
        "violations": [violation.to_dict() for violation in violations],
    }


def render_md(report: dict[str, object]) -> str:
    lines = ["# check_systemmap_covers_contract_registry", ""]
    lines.append(f"- ok: {report.get('ok', False)}")
    lines.append(f"- registry_path: `{report.get('registry_path', '')}`")
    lines.append(f"- system_map_path: `{report.get('system_map_path', '')}`")
    lines.append(f"- registry_row_count: {report.get('registry_row_count', 0)}")
    lines.append(f"- unique_contract_count: {report.get('unique_contract_count', 0)}")
    lines.append(
        f"- generated_block_present: {report.get('generated_block_present', False)}"
    )
    lines.append(
        f"- generated_block_current: {report.get('generated_block_current', False)}"
    )
    lines.append(f"- refresh_command: `{report.get('refresh_command', REFRESH_COMMAND)}`")
    missing = report.get("missing_contract_ids", ())
    missing_count = len(missing) if isinstance(missing, (list, tuple)) else 0
    lines.append(f"- missing_contract_ids: {missing_count}")
    lines.append(
        "- authority_contract_id_coverage_ok: "
        f"{report.get('authority_contract_id_coverage_ok', False)}"
    )
    lines.append(
        "- authority_contract_id_coverage_report_only: "
        f"{report.get('authority_contract_id_coverage_report_only', True)}"
    )
    lines.append(
        "- authority_contract_id_coverage_would_fail: "
        f"{report.get('authority_contract_id_coverage_would_fail', False)}"
    )
    lines.append(
        "- authority_contract_declaration_count: "
        f"{report.get('authority_contract_declaration_count', 0)}"
    )
    authority_missing = report.get("authority_contract_missing_ids", ())
    authority_missing_count = (
        len(authority_missing) if isinstance(authority_missing, (list, tuple)) else 0
    )
    lines.append(f"- authority_contract_missing_ids: {authority_missing_count}")
    violations = report.get("violations", [])
    lines.append(f"- violations: {len(violations) if isinstance(violations, list) else 0}")
    authority_errors = report.get("authority_contract_id_scan_errors", ())
    if isinstance(authority_errors, (list, tuple)) and authority_errors:
        lines.extend(("", "## Authority Contract ID Scan Errors", ""))
        lines.extend(f"- {error}" for error in authority_errors)
    if isinstance(violations, list) and violations:
        lines.extend(("", "## Violations", ""))
        for violation in violations:
            if not isinstance(violation, dict):
                continue
            contract = violation.get("contract_id") or "(system_map)"
            lines.append(
                f"- `{contract}` [{violation.get('rule')}]: "
                f"{violation.get('detail')}"
            )
    authority_violations = report.get("authority_contract_id_violations", ())
    if isinstance(authority_violations, (list, tuple)) and authority_violations:
        lines.extend(("", "## Authority Contract ID Violations (report-only)", ""))
        for violation in authority_violations:
            if not isinstance(violation, dict):
                continue
            lines.append(
                f"- `{violation.get('contract_id')}` "
                f"[{violation.get('rule')}]: "
                f"{violation.get('path')}:{violation.get('line_number')} "
                f"({violation.get('source')})"
            )
    return "\n".join(lines)


def _display_path(path: Path, *, repo_root: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def _resolve_path(value: str | None, *, repo_root: Path) -> Path | None:
    if not value:
        return None
    path = Path(value)
    if path.is_absolute():
        return path
    return repo_root / path


def _resolve_paths(values: Sequence[str] | None, *, repo_root: Path) -> tuple[Path, ...] | None:
    if values is None:
        return None
    return tuple(_resolve_path(value, repo_root=repo_root) for value in values if value)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("json", "md"), default="md")
    parser.add_argument("--registry-path", help="Override the registry JSONL path")
    parser.add_argument("--system-map-path", help="Override the SYSTEM_MAP markdown path")
    parser.add_argument(
        "--authority-contract-path",
        action="append",
        help=(
            "Authority Python file to scan for declared contract_id literals. "
            "May be passed more than once."
        ),
    )
    args = parser.parse_args(argv)
    try:
        report = build_report(
            registry_path=_resolve_path(args.registry_path, repo_root=REPO_ROOT),
            system_map_path=_resolve_path(args.system_map_path, repo_root=REPO_ROOT),
            authority_contract_paths=_resolve_paths(
                args.authority_contract_path,
                repo_root=REPO_ROOT,
            ),
        )
    except (OSError, TypeError, ValueError) as exc:
        return emit_runtime_error(COMMAND, args.format, str(exc))
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_md(report))
    return 0 if report["ok"] else 1
