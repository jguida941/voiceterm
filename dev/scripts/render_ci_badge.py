#!/usr/bin/env python3
"""Render a Shields endpoint JSON badge for CI status."""

import argparse
import json
from pathlib import Path


def normalize_status(status: str) -> str:
    """Normalize job/workflow status values into badge states."""
    normalized = status.strip().lower()
    if normalized in {"success", "passing", "passed"}:
        return "passing"
    return "failing"


def color_for_status(status: str) -> str:
    """Return badge color for normalized status."""
    if status == "passing":
        return "black"
    return "red"


def write_badge(path: Path, label: str, message: str, color: str) -> None:
    """Write shields endpoint JSON payload."""
    payload = {
        "schemaVersion": 1,
        "label": label,
        "message": message,
        "color": color,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Render CI badge JSON.")
    parser.add_argument("--status", required=True, help="Job/workflow status")
    parser.add_argument(
        "--output",
        default=".github/badges/ci-status.json",
        help="Output path for shields endpoint JSON",
    )
    parser.add_argument("--label", default="CI", help="Badge label")
    args = parser.parse_args()

    normalized = normalize_status(args.status)
    color = color_for_status(normalized)
    write_badge(Path(args.output), args.label, normalized, color)
    print(f"CI badge: {normalized} ({color})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
