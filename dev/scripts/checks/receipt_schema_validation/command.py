"""CLI entrypoint for the receipt-schema validation guard."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

_REPO_ROOT_FOR_PATH = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT_FOR_PATH) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT_FOR_PATH))

try:
    from check_bootstrap import emit_runtime_error
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import emit_runtime_error

from .models import COMMAND, DEFAULT_FEATURE_PROOF_DIR
from .report import build_report, render_markdown


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate typed receipt schemas before receipt-store writes become authority."
    )
    parser.add_argument("--feature-proof-dir", type=Path, default=DEFAULT_FEATURE_PROOF_DIR)
    parser.add_argument("--scope", choices=("changed", "all"), default="changed")
    parser.add_argument("--format", choices=("json", "md"), default="md")
    args = parser.parse_args(argv)
    try:
        report = build_report(feature_proof_dir=args.feature_proof_dir, scope=args.scope)
    except Exception as exc:  # pragma: no cover - defensive guard wrapper
        return emit_runtime_error(COMMAND, args.format, str(exc))
    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(render_markdown(report))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
