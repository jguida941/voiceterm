#!/usr/bin/env python3
"""Guard against known Rust audit regression patterns across runtime sources."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_ROOT = REPO_ROOT / "src"

PATTERNS = {
    "utf8_prefix_slice": re.compile(
        r"&\s*[A-Za-z_][A-Za-z0-9_]*\s*\[\s*\.\.\s*[A-Za-z_][A-Za-z0-9_]*\.len\(\)\.min\("
    ),
    "char_limit_truncate": re.compile(r"\.truncate\s*\(\s*INPUT_MAX_CHARS\s*\)"),
    "single_pass_secret_find": re.compile(
        r"if\s+let\s+Some\([^)]*\)\s*=\s*redacted\.find\("
    ),
    "deterministic_id_hash_suffix": re.compile(r"wrapping_mul\((?:2654435761|2246822519)\)"),
    "lossy_vad_cast_i16": re.compile(r"\(\s*clamped\s*\*\s*32_768\.0\s*\)\s*as\s*i16"),
}


def _iter_rust_paths() -> list[Path]:
    if not SRC_ROOT.exists():
        return []
    paths: list[Path] = []
    for path in SRC_ROOT.rglob("*.rs"):
        if "target" in path.parts:
            continue
        paths.append(path)
    return sorted(paths)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _count_metrics(text: str | None) -> dict[str, int]:
    if text is None:
        return {name: 0 for name in PATTERNS}
    return {name: len(pattern.findall(text)) for name, pattern in PATTERNS.items()}


def _has_positive_metrics(metrics: dict[str, int]) -> bool:
    return any(value > 0 for value in metrics.values())


def _render_md(report: dict) -> str:
    lines = ["# check_rust_audit_patterns", ""]
    lines.append(f"- ok: {report['ok']}")
    lines.append(f"- files_considered: {report['files_considered']}")
    lines.append(f"- violations: {len(report['violations'])}")
    lines.append(
        "- aggregate: "
        + ", ".join(f"{name}={count}" for name, count in report["totals"].items())
    )
    if report["violations"]:
        lines.append("")
        lines.append("## Violations")
        lines.append(
            "- Guidance: prefer UTF-8-safe prefix helpers, char-safe truncation, "
            "multi-occurrence redaction loops, non-deterministic ID suffixes, and "
            "explicit saturating float-to-i16 conversions."
        )
        for item in report["violations"]:
            flagged = ", ".join(
                f"{name}={count}" for name, count in item["metrics"].items() if count > 0
            )
            lines.append(f"- `{item['path']}`: {flagged}")
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("md", "json"), default="md")
    return parser


def main() -> int:
    args = _build_parser().parse_args()

    paths = _iter_rust_paths()
    violations: list[dict] = []
    totals = {name: 0 for name in PATTERNS}

    for path in paths:
        text = _read_text(path)
        metrics = _count_metrics(text)
        for name, value in metrics.items():
            totals[name] += value
        if _has_positive_metrics(metrics):
            violations.append(
                {
                    "path": path.relative_to(REPO_ROOT).as_posix(),
                    "metrics": metrics,
                }
            )

    report = {
        "command": "check_rust_audit_patterns",
        "timestamp": datetime.now().isoformat(),
        "ok": len(violations) == 0,
        "files_considered": len(paths),
        "totals": totals,
        "violations": violations,
    }

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(_render_md(report))

    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
