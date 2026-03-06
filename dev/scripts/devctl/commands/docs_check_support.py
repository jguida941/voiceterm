"""Compatibility export surface for docs-check helper modules."""

from __future__ import annotations

from .docs_check_messaging import (
    build_failure_reasons,
    build_next_actions,
    collect_gate_messages,
)
from .docs_check_policy import (
    ACTIVE_PLAN_SYNC_SCRIPT_REL,
    AGENTS_BUNDLE_RENDER_SCRIPT_REL,
    BUNDLE_WORKFLOW_PARITY_SCRIPT_REL,
    EVOLUTION_DOC,
    MARKDOWN_METADATA_HEADER_SCRIPT_REL,
    MULTI_AGENT_SYNC_SCRIPT_REL,
    TOOLING_REQUIRED_DOCS,
    USER_DOCS,
    WORKFLOW_SHELL_HYGIENE_SCRIPT_REL,
    is_tooling_change,
    requires_evolution_update,
    scan_deprecated_references,
)

__all__ = [
    "ACTIVE_PLAN_SYNC_SCRIPT_REL",
    "AGENTS_BUNDLE_RENDER_SCRIPT_REL",
    "BUNDLE_WORKFLOW_PARITY_SCRIPT_REL",
    "EVOLUTION_DOC",
    "MARKDOWN_METADATA_HEADER_SCRIPT_REL",
    "MULTI_AGENT_SYNC_SCRIPT_REL",
    "TOOLING_REQUIRED_DOCS",
    "USER_DOCS",
    "WORKFLOW_SHELL_HYGIENE_SCRIPT_REL",
    "build_failure_reasons",
    "build_next_actions",
    "collect_gate_messages",
    "is_tooling_change",
    "requires_evolution_update",
    "scan_deprecated_references",
]

