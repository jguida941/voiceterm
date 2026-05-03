"""Guard bounded Python test execution policy."""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

PYTEST_CONFIG = REPO_ROOT / "pytest.ini"


def _bundle_violations() -> list[dict[str, str]]:
    return [
        violation
        for bundle, commands in _bundle_registry().items()
        for command in commands
        if (violation := _bundle_violation(bundle, command)) is not None
    ]


def _bundle_registry() -> dict[str, tuple[str, ...]]:
    from dev.scripts.devctl.bundle_registry import BUNDLE_REGISTRY

    return BUNDLE_REGISTRY


def _bundle_violation(bundle: str, command: str) -> dict[str, str] | None:
    if not _is_unbounded_pytest_command(command):
        return None
    return {
        "kind": "raw_pytest_bundle_command",
        "bundle": bundle,
        "command": command,
    }


def _config_violations() -> list[dict[str, str]]:
    if not PYTEST_CONFIG.exists():
        return [{"kind": "missing_pytest_ini", "path": "pytest.ini"}]
    text = PYTEST_CONFIG.read_text(encoding="utf-8")
    required_terms = ("testpaths", "norecursedirs", "-x")
    missing = [term for term in required_terms if term not in text]
    return [
        {"kind": "pytest_ini_missing_policy", "path": "pytest.ini", "term": term}
        for term in missing
    ]


def _is_unbounded_pytest_command(command: str) -> bool:
    try:
        parts = shlex.split(command)
    except ValueError:
        return False
    if len(parts) >= 3 and parts[1:3] == ["-m", "pytest"]:
        return "dev/scripts/devctl.py test-python" not in command
    if parts and Path(parts[0]).name in {"pytest", "py.test"}:
        return True
    if "dev/scripts/devctl.py test-python" in command:
        return False
    return False


def build_report() -> dict[str, object]:
    violations = [*_bundle_violations(), *_config_violations()]
    return {
        "command": "check_pytest_runtime_policy",
        "ok": not violations,
        "violations": violations,
        "bundle_count": len(_bundle_registry()),
        "pytest_config": "pytest.ini",
    }


def render_md(report: dict[str, object]) -> str:
    lines = [
        "# check_pytest_runtime_policy",
        "",
        f"- ok: {report['ok']}",
        f"- bundle_count: {report['bundle_count']}",
        f"- pytest_config: {report['pytest_config']}",
    ]
    violations = report["violations"]
    if isinstance(violations, list) and violations:
        lines.extend(["", "## Violations"])
        for item in violations:
            lines.append(f"- {item}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("md", "json"), default="md")
    args = parser.parse_args(argv)
    report = build_report()
    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(render_md(report))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
