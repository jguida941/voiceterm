"""Command entrypoint for the memory-not-authority guard."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone

try:
    from check_bootstrap import REPO_ROOT
except ModuleNotFoundError:  # pragma: no cover - package-style fallback
    from dev.scripts.checks.check_bootstrap import REPO_ROOT

try:
    from memory_authority.checks import run_all_checks
except ModuleNotFoundError:  # pragma: no cover - package-style fallback
    from dev.scripts.checks.memory_authority.checks import run_all_checks


def build_report() -> dict[str, object]:
    """Return current memory-not-authority guard status."""
    violations = run_all_checks(REPO_ROOT)
    return {
        "command": "check_memory_not_authority",
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "ok": not violations,
        "violations": violations,
    }


def render_markdown(report: dict[str, object]) -> str:
    """Render guard output as markdown."""
    violations = report["violations"]
    lines = [
        "# check_memory_not_authority",
        "",
        f"- ok: {report['ok']}",
        f"- violations: {len(violations) if isinstance(violations, list) else 0}",
    ]
    if isinstance(violations, list) and violations:
        lines.extend(["", "## Violations"])
        for violation in violations:
            if isinstance(violation, dict):
                lines.append(_violation_line(violation))
    return "\n".join(lines)


def _violation_line(violation: dict[str, object]) -> str:
    location = str(violation.get("file") or "?")
    if "line" in violation:
        location = f"{location}:{violation['line']}"
    extras = [
        f"{key}={violation[key]}"
        for key in ("key", "trail", "value", "match")
        if key in violation
    ]
    suffix = f" ({', '.join(extras)})" if extras else ""
    return (
        f"- [{violation.get('kind')}] {location}{suffix} -> "
        f"{violation.get('hint')}"
    )


def main() -> int:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="Guard memory is not architecture authority.",
    )
    parser.add_argument("--format", choices=("md", "json"), default="md")
    args = parser.parse_args()
    report = build_report()
    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(render_markdown(report))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
