#!/usr/bin/env python3
"""Inventory and guard provider/topology hardcodes for Phase 0.6.C."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

_BOOT_ROOT = str(Path(__file__).resolve().parents[4])
if _BOOT_ROOT not in sys.path:
    sys.path.insert(0, _BOOT_ROOT)

try:
    from check_bootstrap import REPO_ROOT, utc_timestamp
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT, utc_timestamp

PROVIDER_LITERALS = ("codex", "claude", "cursor")
COUNT_COUPLED_RE = re.compile(r"\b(active_)?(single|dual|triple)_agent\b", re.I)
INVENTORY_REL_PATH = Path("dev/state/topology_hardcode_inventory.jsonl")
SCAN_FILE_RELS = (
    Path("dev/scripts/devctl/governance/instruction_boot_card.py"),
)
SCAN_ROOT_RELS = (Path("dev/scripts/devctl/runtime"),)


@dataclass(frozen=True)
class TopologyHardcodeInventory:
    contract_id: str
    schema_version: int
    path: str
    line: int
    column: int
    finding_kind: str
    value: str
    excerpt: str
    fingerprint: str
    phase: str = "0.6.C"
    status: str = "existing_inventory_only"
    remediation_phase: str = "6"


def scan_topology_hardcodes(*, repo_root: Path = REPO_ROOT) -> list[TopologyHardcodeInventory]:
    rows: list[TopologyHardcodeInventory] = []
    for path in _scan_paths(repo_root):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        rows.extend(_scan_python_text(path=path, repo_root=repo_root, text=text))
    return sorted(rows, key=lambda row: (row.path, row.line, row.column, row.finding_kind, row.value))


def build_report(
    *,
    repo_root: Path = REPO_ROOT,
    inventory_path: Path | None = None,
    mode: str = "all",
) -> dict[str, object]:
    current_rows = _filter_rows(scan_topology_hardcodes(repo_root=repo_root), mode)
    inventory_rel = inventory_path or repo_root / INVENTORY_REL_PATH
    inventory_rows, inventory_errors = _load_inventory(inventory_rel)
    inventory_rows = _filter_rows(inventory_rows, mode)
    inventory_fingerprints = {row.fingerprint for row in inventory_rows}
    current_fingerprints = {row.fingerprint for row in current_rows}
    uninventoried = [
        asdict(row) for row in current_rows if row.fingerprint not in inventory_fingerprints
    ]
    stale = [
        asdict(row) for row in inventory_rows if row.fingerprint not in current_fingerprints
    ]
    violations: list[dict[str, object]] = []
    if inventory_errors:
        violations.extend(inventory_errors)
    for row in uninventoried:
        row["check"] = "new_uninventoried_topology_hardcode"
        violations.append(row)
    return {
        "command": "check_topology_hardcode_inventory",
        "timestamp": utc_timestamp(),
        "ok": not violations,
        "mode": mode,
        "inventory_path": str(inventory_rel),
        "current_count": len(current_rows),
        "inventory_count": len(inventory_rows),
        "uninventoried_count": len(uninventoried),
        "stale_inventory_count": len(stale),
        "violations": violations,
        "stale_inventory": stale,
    }


def write_inventory(*, repo_root: Path = REPO_ROOT) -> Path:
    rows = scan_topology_hardcodes(repo_root=repo_root)
    path = repo_root / INVENTORY_REL_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(asdict(row), sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    return path


def _scan_paths(repo_root: Path) -> tuple[Path, ...]:
    paths: list[Path] = []
    for rel in SCAN_FILE_RELS:
        path = repo_root / rel
        if path.is_file():
            paths.append(path)
    for rel in SCAN_ROOT_RELS:
        root = repo_root / rel
        if root.is_dir():
            paths.extend(sorted(root.glob("*.py")))
    return tuple(dict.fromkeys(paths))


def _scan_python_text(
    *,
    path: Path,
    repo_root: Path,
    text: str,
) -> list[TopologyHardcodeInventory]:
    rows: list[TopologyHardcodeInventory] = []
    lines = text.splitlines()
    try:
        tree = ast.parse(text)
    except SyntaxError:
        tree = None
    if tree is not None:
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                value = node.value.strip()
                lower = value.lower()
                if lower in PROVIDER_LITERALS:
                    rows.append(
                        _row(
                            path=path,
                            repo_root=repo_root,
                            line=node.lineno,
                            column=node.col_offset,
                            finding_kind="provider_literal",
                            value=lower,
                            lines=lines,
                        )
                    )
                if COUNT_COUPLED_RE.search(lower):
                    rows.append(
                        _row(
                            path=path,
                            repo_root=repo_root,
                            line=node.lineno,
                            column=node.col_offset,
                            finding_kind="count_coupled_topology",
                            value=value,
                            lines=lines,
                        )
                    )
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                for target in _assignment_targets(node):
                    if COUNT_COUPLED_RE.search(target.lower()):
                        rows.append(
                            _row(
                                path=path,
                                repo_root=repo_root,
                                line=node.lineno,
                                column=node.col_offset,
                                finding_kind="count_coupled_topology",
                                value=target,
                                lines=lines,
                            )
                        )
    return _dedupe(rows)


def _assignment_targets(node: ast.AST) -> tuple[str, ...]:
    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
    names: list[str] = []
    for target in targets:
        if isinstance(target, ast.Name):
            names.append(target.id)
        elif isinstance(target, ast.Attribute):
            names.append(target.attr)
    return tuple(names)


def _row(
    *,
    path: Path,
    repo_root: Path,
    line: int,
    column: int,
    finding_kind: str,
    value: str,
    lines: list[str],
) -> TopologyHardcodeInventory:
    rel = path.relative_to(repo_root).as_posix()
    excerpt = lines[line - 1].strip() if 0 < line <= len(lines) else ""
    fingerprint = hashlib.sha256(
        f"{rel}\0{finding_kind}\0{value}\0{excerpt}".encode("utf-8")
    ).hexdigest()
    return TopologyHardcodeInventory(
        contract_id="TopologyHardcodeInventory",
        schema_version=1,
        path=rel,
        line=line,
        column=column,
        finding_kind=finding_kind,
        value=value,
        excerpt=excerpt,
        fingerprint=fingerprint,
    )


def _dedupe(rows: list[TopologyHardcodeInventory]) -> list[TopologyHardcodeInventory]:
    seen: set[str] = set()
    unique: list[TopologyHardcodeInventory] = []
    for row in rows:
        if row.fingerprint in seen:
            continue
        seen.add(row.fingerprint)
        unique.append(row)
    return unique


def _filter_rows(
    rows: list[TopologyHardcodeInventory],
    mode: str,
) -> list[TopologyHardcodeInventory]:
    if mode == "provider":
        return [row for row in rows if row.finding_kind == "provider_literal"]
    if mode == "count":
        return [row for row in rows if row.finding_kind == "count_coupled_topology"]
    return rows


def _load_inventory(path: Path) -> tuple[list[TopologyHardcodeInventory], list[dict[str, object]]]:
    if not path.is_file():
        return [], [
            {
                "check": "topology_inventory_missing",
                "path": str(path),
                "detail": "Phase 0.6.C claims topology inventory exists, but the file is missing.",
            }
        ]
    rows: list[TopologyHardcodeInventory] = []
    errors: list[dict[str, object]] = []
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            payload = json.loads(raw)
            rows.append(TopologyHardcodeInventory(**payload))
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            errors.append(
                {
                    "check": "topology_inventory_row_invalid",
                    "path": str(path),
                    "line": line_no,
                    "detail": str(exc),
                }
            )
    return rows, errors


def _render_md(report: dict[str, object]) -> str:
    violations = report.get("violations")
    rows = violations if isinstance(violations, list) else []
    lines = ["# check_topology_hardcode_inventory", ""]
    lines.append(f"- ok: {report['ok']}")
    lines.append(f"- mode: {report['mode']}")
    lines.append(f"- current_count: {report['current_count']}")
    lines.append(f"- inventory_count: {report['inventory_count']}")
    lines.append(f"- uninventoried_count: {report['uninventoried_count']}")
    lines.append(f"- stale_inventory_count: {report['stale_inventory_count']}")
    if rows:
        lines.append("")
        lines.append("## Violations")
        for row in rows:
            if not isinstance(row, dict):
                continue
            location = f"{row.get('path')}:{row.get('line', 0)}"
            lines.append(f"- `{location}` {row.get('check')}: {row.get('detail') or row.get('excerpt')}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("md", "json"), default="md")
    parser.add_argument("--mode", choices=("all", "provider", "count"), default="all")
    parser.add_argument("--write-inventory", action="store_true")
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])
    if args.write_inventory:
        path = write_inventory()
        print(f"wrote {path.relative_to(REPO_ROOT)}")
        return 0
    report = build_report(mode=args.mode)
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(_render_md(report))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
