"""Policy constants and scanners used by docs-check."""

from __future__ import annotations

import re
from pathlib import Path

from ..script_catalog import check_script_relative_path

USER_DOCS = [
    "README.md",
    "QUICK_START.md",
    "guides/USAGE.md",
    "guides/CLI_FLAGS.md",
    "guides/INSTALL.md",
    "guides/TROUBLESHOOTING.md",
]

TOOLING_CHANGE_PREFIXES = (
    "dev/scripts/",
    "scripts/macro-packs/",
    ".github/workflows/",
)
TOOLING_CHANGE_EXACT = {
    "Makefile",
    "AGENTS.md",
    "dev/DEVELOPMENT.md",
    "dev/guides/DEVELOPMENT.md",
    "dev/scripts/README.md",
}
TOOLING_REQUIRED_DOCS = [
    "AGENTS.md",
    "dev/guides/DEVELOPMENT.md",
    "dev/scripts/README.md",
    "dev/active/MASTER_PLAN.md",
]
# Legacy bridge aliases are retired; tooling updates must touch canonical docs.
TOOLING_REQUIRED_DOC_ALIASES: dict[str, tuple[str, ...]] = {}
EVOLUTION_DOC = "dev/history/ENGINEERING_EVOLUTION.md"
EVOLUTION_CHANGE_PREFIXES = (
    "dev/scripts/",
    ".github/workflows/",
)
EVOLUTION_CHANGE_EXACT = {
    "AGENTS.md",
    "dev/ARCHITECTURE.md",
    "dev/DEVELOPMENT.md",
    "dev/guides/ARCHITECTURE.md",
    "dev/guides/DEVELOPMENT.md",
    "dev/scripts/README.md",
    "dev/active/MASTER_PLAN.md",
}

DEPRECATED_REFERENCE_TARGETS = [
    "AGENTS.md",
    "dev/DEVELOPMENT.md",
    "dev/guides/DEVELOPMENT.md",
    "dev/scripts/README.md",
    "scripts/macro-packs/full-dev.yaml",
    "Makefile",
]
DEPRECATED_REFERENCE_PATTERNS = [
    {
        "name": "release-script",
        "regex": re.compile(r"\./dev/scripts/release\.sh\b"),
        "replacement": "python3 dev/scripts/devctl.py release --version <version>",
    },
    {
        "name": "homebrew-script",
        "regex": re.compile(r"\./dev/scripts/update-homebrew\.sh\b"),
        "replacement": "python3 dev/scripts/devctl.py homebrew --version <version>",
    },
    {
        "name": "pypi-script",
        "regex": re.compile(r"\./dev/scripts/publish-pypi\.sh\b"),
        "replacement": "python3 dev/scripts/devctl.py pypi --upload",
    },
    {
        "name": "notes-script",
        "regex": re.compile(r"\./dev/scripts/generate-release-notes\.sh\b"),
        "replacement": "python3 dev/scripts/devctl.py release-notes --version <version>",
    },
]

ACTIVE_PLAN_SYNC_SCRIPT_REL = check_script_relative_path("active_plan_sync")
MULTI_AGENT_SYNC_SCRIPT_REL = check_script_relative_path("multi_agent_sync")
MARKDOWN_METADATA_HEADER_SCRIPT_REL = check_script_relative_path(
    "markdown_metadata_header"
)
WORKFLOW_SHELL_HYGIENE_SCRIPT_REL = check_script_relative_path("workflow_shell_hygiene")
BUNDLE_WORKFLOW_PARITY_SCRIPT_REL = check_script_relative_path("bundle_workflow_parity")
AGENTS_BUNDLE_RENDER_SCRIPT_REL = check_script_relative_path("agents_bundle_render")


def is_tooling_change(path: str) -> bool:
    """Return True when the changed path is considered tooling/process scope."""
    return path in TOOLING_CHANGE_EXACT or path.startswith(TOOLING_CHANGE_PREFIXES)


def requires_evolution_update(path: str) -> bool:
    """Return True when a path requires an engineering-evolution log update."""
    return path in EVOLUTION_CHANGE_EXACT or path.startswith(EVOLUTION_CHANGE_PREFIXES)


def scan_deprecated_references(repo_root: Path) -> list[dict]:
    """Find legacy helper-script references in governance-controlled files."""
    violations = []
    for relative in DEPRECATED_REFERENCE_TARGETS:
        path = repo_root / relative
        if not path.exists():
            continue
        for lineno, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            for spec in DEPRECATED_REFERENCE_PATTERNS:
                if spec["regex"].search(line):
                    violations.append(
                        {
                            "file": relative,
                            "line": lineno,
                            "pattern": spec["name"],
                            "line_text": line.strip(),
                            "replacement": spec["replacement"],
                        }
                    )
    return violations
