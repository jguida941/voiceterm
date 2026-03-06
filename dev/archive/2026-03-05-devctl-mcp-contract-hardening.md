# Devctl MCP Contract Hardening Plan

**Status**: closed  |  **Last updated**: 2026-03-05 | **Owner:** Tooling control plane
Execution plan contract: required

## Scope

Keep `devctl` as the canonical control plane and add MCP only as an optional,
read-only adapter surface. This scope hardens release/safety behavior by
locking `devctl` guardrails into executable contract tests instead of relying
on doc guidance alone.

Closure rule for this plan: when all checklist items are complete, close this
scope in active tracking and move it to archive/reference state if needed.
Durable docs (architecture, autoguide, command reference) stay in place.

## Execution Checklist

- [x] Extract `check --profile release` gate command contract into code-owned
      helpers.
- [x] Extract `ship --verify` subcheck sequence into code-owned helpers.
- [x] Add read-only `devctl mcp` command surface with explicit allowlist and
      stdio MCP transport mode.
- [x] Add/expand tests for check/ship contract behavior and cleanup-path
      safety constraints.
- [x] Publish durable MCP + contract hardening docs in maintainer surfaces
      (`dev/ARCHITECTURE.md`, `dev/DEVCTL_AUTOGUIDE.md`,
      `dev/scripts/README.md`, `dev/MCP_DEVCTL_ALIGNMENT.md`).
- [x] Run tooling verification commands and record evidence.
- [x] Mark MP scope complete in `dev/active/MASTER_PLAN.md`.

## Progress Log

- 2026-03-05: Added extracted release-gate contract helper in
  `dev/scripts/devctl/commands/check.py` (`build_release_gate_commands`).
- 2026-03-05: Added extracted `ship --verify` contract helper in
  `dev/scripts/devctl/commands/ship_steps.py` (`build_verify_checks`).
- 2026-03-05: Added read-only MCP adapter command
  (`dev/scripts/devctl/commands/mcp.py`) and allowlist config
  (`dev/config/mcp_tools_allowlist.json`), plus CLI/parser/list wiring.
- 2026-03-05: Added/expanded contract tests:
  `test_check.py`, `test_ship.py`, `test_mcp.py`,
  `test_reports_retention.py`.
- 2026-03-05: Clarified closure semantics to preserve durable docs and close
  only active-tracker state for this scope.
- 2026-03-05: Closed scope and moved tracker out of `dev/active` into archive.
- 2026-03-06: Post-closure hardening pass tightened MCP argument validation
  (`--tool-args-json` now requires `--tool`), aligned stdio `resources/read`
  mime-type output with allowlist metadata, and expanded MCP contract tests
  for duplicate-allowlist and JSON-RPC invalid-param edge cases.

## Audit Evidence

- `python3 -m unittest dev.scripts.devctl.tests.test_check`
  -> `Ran 50 tests ... OK`
- `python3 -m unittest dev.scripts.devctl.tests.test_ship`
  -> `Ran 19 tests ... OK`
- `python3 -m unittest dev.scripts.devctl.tests.test_mcp`
  -> `Ran 19 tests ... OK`
- `python3 -m unittest dev.scripts.devctl.tests.test_reports_retention`
  -> `Ran 2 tests ... OK`
- `python3 dev/scripts/checks/check_active_plan_sync.py`
  -> `ok: True`
- `python3 dev/scripts/checks/check_multi_agent_sync.py`
  -> `ok: True`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
  -> `ok: True`
- `python3 dev/scripts/devctl.py hygiene`
  -> `ok: True`
