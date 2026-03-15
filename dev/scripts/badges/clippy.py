#!/usr/bin/env python3
"""Render a Shields endpoint JSON badge for clippy warnings."""

import argparse
from pathlib import Path
import sys

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from dev.scripts.badges.common import write_badge


def normalize_status(status: str) -> str:
    """Normalize clippy step/job status values into pass/fail."""
    normalized = status.strip().lower()
    if normalized in {"success", "passing", "passed"}:
        return "passing"
    return "failing"


def parse_warning_count(raw_value: str) -> int | None:
    """Parse warning count from workflow output; return None on invalid input."""
    try:
        parsed = int(raw_value.strip())
    except (TypeError, ValueError):
        return None
    if parsed < 0:
        return None
    return parsed


def warning_message(count: int) -> str:
    """Format warning count with correct singular/plural wording."""
    if count == 1:
        return "1 warning"
    return f"{count} warnings"


def badge_payload(status: str, warning_count: int | None) -> tuple[str, str]:
    """Return (message, color) for the clippy badge."""
    if warning_count is None:
        if status == "passing":
            return "unknown", "red"
        return "failed", "red"

    if status != "passing":
        if warning_count > 0:
            return warning_message(warning_count), "red"
        return "failed", "red"

    message = warning_message(warning_count)
    color = "black" if warning_count == 0 else "red"
    return message, color

def main() -> int:
    parser = argparse.ArgumentParser(description="Render clippy warnings badge JSON.")
    parser.add_argument("--status", required=True, help="Clippy step/job status")
    parser.add_argument("--warnings", required=True, help="Number of clippy warnings")
    parser.add_argument(
        "--output",
        default=".github/badges/clippy-warnings.json",
        help="Output path for shields endpoint JSON",
    )
    parser.add_argument("--label", default="Clippy", help="Badge label")
    args = parser.parse_args()

    normalized_status = normalize_status(args.status)
    warning_count = parse_warning_count(args.warnings)
    message, color = badge_payload(normalized_status, warning_count)
    write_badge(Path(args.output), args.label, message, color)
    print(f"Clippy badge: {message} ({color})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
