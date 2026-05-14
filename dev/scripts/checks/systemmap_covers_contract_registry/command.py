"""Ensure SYSTEM_MAP renders every platform contract-registry id."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

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


def evaluate_systemmap_contract_coverage(
    *,
    repo_root: Path = REPO_ROOT,
    registry_path: Path | None = None,
    system_map_path: Path | None = None,
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


def build_report(
    *,
    repo_root: Path = REPO_ROOT,
    registry_path: Path | None = None,
    system_map_path: Path | None = None,
) -> dict[str, object]:
    coverage, violations = evaluate_systemmap_contract_coverage(
        repo_root=repo_root,
        registry_path=registry_path,
        system_map_path=system_map_path,
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
    violations = report.get("violations", [])
    lines.append(f"- violations: {len(violations) if isinstance(violations, list) else 0}")
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("json", "md"), default="md")
    parser.add_argument("--registry-path", help="Override the registry JSONL path")
    parser.add_argument("--system-map-path", help="Override the SYSTEM_MAP markdown path")
    args = parser.parse_args(argv)
    try:
        report = build_report(
            registry_path=_resolve_path(args.registry_path, repo_root=REPO_ROOT),
            system_map_path=_resolve_path(args.system_map_path, repo_root=REPO_ROOT),
        )
    except (OSError, TypeError, ValueError) as exc:
        return emit_runtime_error(COMMAND, args.format, str(exc))
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_md(report))
    return 0 if report["ok"] else 1
