"""Check raw-git mutation callsites against the governed executor ancestry."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT
    from dev.scripts.devctl.governance_graph.mutation_bypass import (
        DEFAULT_PROOF_ARTIFACT,
        build_report,
    )
except ModuleNotFoundError:
    from check_bootstrap import REPO_ROOT, ensure_repo_root_on_syspath

    ensure_repo_root_on_syspath(REPO_ROOT)

    from dev.scripts.devctl.governance_graph.mutation_bypass import (
        DEFAULT_PROOF_ARTIFACT,
        build_report,
    )


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("md", "json"), default="md")
    parser.add_argument(
        "--proof-output",
        default=DEFAULT_PROOF_ARTIFACT,
        help="Repo-relative or absolute path for the persisted proof artifact.",
    )
    return parser.parse_args(argv)


def _resolve_output_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def _render_md(report: dict[str, object]) -> str:
    lines = ["# check_mutation_bypass_graph_closure", ""]
    lines.append(f"- ok: {report.get('ok')}")
    lines.append(f"- proof_artifact: {report.get('proof_artifact', 'missing')}")
    lines.append(f"- node_count: {report.get('node_count', 0)}")
    lines.append(f"- edge_count: {report.get('edge_count', 0)}")
    lines.append(f"- bypasses: {len(report.get('bypasses') or [])}")
    lines.append(f"- parse_errors: {len(report.get('parse_errors') or [])}")

    bypasses = report.get("bypasses") or []
    if bypasses:
        lines.extend(["", "## Ungoverned Paths"])
        for item in bypasses:
            lines.append(
                f"- `{item['path']}:{item['line']}` `{item['git_verb']}` via "
                f"`{item['command_source']}` inside `{item['containing_function']}`"
            )
            for path in item.get("reachable_entrypoints") or []:
                lines.append(
                    "  path: "
                    + " -> ".join(path.get("path") or [])
                )

    classified_debt = report.get("classified_debt") or {}
    hook_owned = classified_debt.get("hook_owned") or []
    if hook_owned:
        lines.extend(["", "## Hook-Owned Callsites"])
        for item in hook_owned:
            lines.append(
                f"- `{item['path']}:{item['line']}` `{item['git_verb']}`"
            )

    test_helpers = classified_debt.get("test_helpers") or []
    if test_helpers:
        lines.extend(["", "## Test Helpers"])
        for item in test_helpers:
            lines.append(f"- `{item['path']}:{item['line']}` dynamic git wrapper")

    parse_errors = report.get("parse_errors") or []
    if parse_errors:
        lines.extend(["", "## Parse Errors"])
        for item in parse_errors:
            lines.append(f"- `{item['path']}`: {item['error']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    report = build_report(
        repo_root=REPO_ROOT,
        proof_output_path=_resolve_output_path(args.proof_output),
    )
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(_render_md(report))
    return 0 if report.get("ok", False) else 1


if __name__ == "__main__":
    raise SystemExit(main())
