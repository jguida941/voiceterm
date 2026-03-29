"""Policy defaults and data models for docs-check."""

from __future__ import annotations

import re
from dataclasses import dataclass

from ...script_catalog import check_script_relative_path

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
GUIDE_CONTRACT_SYNC_SCRIPT_REL = check_script_relative_path("guide_contract_sync")
INSTRUCTION_SURFACE_SYNC_SCRIPT_REL = check_script_relative_path(
    "instruction_surface_sync"
)


@dataclass(frozen=True, slots=True)
class DeprecatedReferencePattern:
    """One deprecated-reference rule used by docs-check."""

    name: str
    regex: re.Pattern[str]
    replacement: str


@dataclass(frozen=True, slots=True)
class ToolingDocRequirementRule:
    """One policy-owned docs-governance rule for a tooling scope."""

    rule_id: str
    trigger_prefixes: tuple[str, ...]
    trigger_exact_paths: frozenset[str]
    required_docs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DocsCheckPolicy:
    """Resolved docs-check policy loaded from repo governance config."""

    user_docs: tuple[str, ...]
    tooling_change_prefixes: tuple[str, ...]
    tooling_change_exact: frozenset[str]
    tooling_required_docs: tuple[str, ...]
    tooling_required_doc_aliases: dict[str, tuple[str, ...]]
    tooling_doc_requirement_rules: tuple[ToolingDocRequirementRule, ...]
    evolution_doc: str
    evolution_change_prefixes: tuple[str, ...]
    evolution_change_exact: frozenset[str]
    deprecated_reference_targets: tuple[str, ...]
    deprecated_reference_patterns: tuple[DeprecatedReferencePattern, ...]
    policy_path: str
    warnings: tuple[str, ...]
