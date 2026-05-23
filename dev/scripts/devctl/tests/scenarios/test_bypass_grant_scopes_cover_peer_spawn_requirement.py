"""Scenario: the operator-facing ``bypass grant --scope`` CLI must expose
at least one scope whose granted-set transitively includes every scope
that another devctl command requires for a typed denial path it
otherwise has no way to escape.

Concretely today: ``peer-spawn`` requires
``BypassAuthorityScope.AGENT_SPAWN_ONLY``. If no ``bypass grant`` scope
choice transitively grants that scope, then the only operator-reachable
remediation for a ``denied_bypass_missing`` peer-spawn output is a path
that goes outside the typed surface (raw bypass flags, harness
classifier territory). This invariant catches that drift before it
ships.
"""

from __future__ import annotations

import argparse
import importlib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[5]


def _bypass_grant_scope_choices() -> list[str]:
    """Inspect the registered argparse parser for ``bypass grant`` and
    return the literal ``--scope`` choices it exposes to the CLI.
    """
    parser_mod = importlib.import_module(
        "dev.scripts.devctl.cli_parser.entrypoint"
    )
    parser = parser_mod.build_parser()
    # Walk subparsers to find: bypass -> grant -> --scope choices.
    def _find_subparsers(p):
        for action in p._actions:
            if isinstance(action, argparse._SubParsersAction):
                return action.choices
        return {}
    top = _find_subparsers(parser)
    bypass = top.get("bypass")
    assert bypass is not None, "'bypass' subcommand not registered"
    grant_subs = _find_subparsers(bypass)
    grant = grant_subs.get("grant")
    assert grant is not None, "'bypass grant' subcommand not registered"
    for action in grant._actions:
        if any(s == "--scope" for s in action.option_strings):
            return list(action.choices) if action.choices else []
    raise AssertionError("'bypass grant --scope' option not found on parser")


def test_bypass_grant_exposes_a_scope_that_transitively_grants_agent_spawn():
    from dev.scripts.devctl.runtime.bypass_lifecycle_models import (
        BypassAuthorityScope,
    )
    from dev.scripts.devctl.runtime.bypass_lifecycle_registry import (
        _GRANTED_SCOPES,
    )

    cli_scopes = _bypass_grant_scope_choices()
    assert cli_scopes, "'bypass grant --scope' exposes no choices at all"

    # Translate CLI dash-form into the enum value form.
    def _to_enum(raw: str) -> BypassAuthorityScope | None:
        normalized = raw.replace("-", "_")
        try:
            return BypassAuthorityScope(normalized)
        except ValueError:
            return None

    covering: list[str] = []
    for raw in cli_scopes:
        scope = _to_enum(raw)
        if scope is None:
            continue
        granted = _GRANTED_SCOPES.get(scope, frozenset())
        if BypassAuthorityScope.AGENT_SPAWN_ONLY in granted:
            covering.append(raw)

    assert covering, (
        "no `bypass grant --scope` choice transitively grants "
        "AGENT_SPAWN_ONLY. The operator cannot issue a receipt that "
        "satisfies peer-spawn's typed authority gate from the canonical "
        "CLI — they will fall back to raw harness bypass flags, which "
        "the auto-classifier blocks.\n"
        f"  cli scope choices:  {cli_scopes}\n"
        "  fix: either expose `agent-spawn-only` as a grant choice, or "
        "ensure an existing exposed scope's granted-set includes it."
    )
