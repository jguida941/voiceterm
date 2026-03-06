# MCP and Devctl Alignment

This document defines how MCP fits this repo without replacing `devctl`.

## Decision

1. `devctl` remains the canonical control plane.
2. MCP is optional and additive.
3. MCP exposure is read-only and allowlisted.
4. Release/safety guarantees come from code + tests, not prompt text.

## Why This Repo Is Not MCP-First

This repo already enforces critical guardrails directly in `devctl` command
paths (`check`, `ship`, cleanup protections, release gates). That means the
core safety model is executable and testable in-repo.

MCP can still help as a transport interface for agents/tools that expect MCP,
but it should not become a duplicate authority layer.

## When To Use Which Path

| Need | Use | Why |
|---|---|---|
| Run enforcement (`check`, `ship`, cleanup, release gates) | `devctl` commands directly | `devctl` is the executable authority and owns guardrails |
| Serve read-only snapshots to an MCP-native client | `devctl mcp` | MCP is the adapter/transport layer only |
| Add new release/safety policy | `devctl` command + tests first, then optional MCP exposure | prevents duplicate policy layers and drift |
| Bypass release/safety checks | not allowed | MCP must not bypass `devctl` enforcement contracts |

## Current MCP Surface

Command entrypoint:

```bash
python3 dev/scripts/devctl.py mcp
python3 dev/scripts/devctl.py mcp --tool status_snapshot --tool-args-json '{"include_ci": true}'
python3 dev/scripts/devctl.py mcp --serve-stdio
```

Allowlist config:

- `dev/config/mcp_tools_allowlist.json`

Current tools:

1. `status_snapshot`
2. `report_snapshot`
3. `compat_matrix_snapshot`
4. `release_contract_snapshot`

Current resources:

1. `devctl://mcp/allowlist`
2. `devctl://devctl/release-contract`

## Safety Contract

1. Tools must be allowlisted.
2. Tools must be explicitly marked `read_only: true`.
3. Non-read-only entries are rejected.
4. Cleanup semantics stay owned by `devctl` cleanup commands and path guards.
5. MCP does not bypass existing release gates.

## Regression Contract

Required code-level contract tests:

1. `check --profile release` enforces
   `status --ci --require-ci` + CodeRabbit/Ralph gates.
2. `ship --verify` runs release verification subchecks in enforced order.
3. Cleanup protections keep deletes within managed roots and protect guarded
   paths.
4. MCP adapter rejects unknown tools and non-read-only allowlist entries.

Current test locations:

- `dev/scripts/devctl/tests/test_check.py`
- `dev/scripts/devctl/tests/test_ship.py`
- `dev/scripts/devctl/tests/test_reports_retention.py`
- `dev/scripts/devctl/tests/test_mcp.py`

## Extension Rules

When adding a new MCP tool/resource:

1. Add handler logic in `dev/scripts/devctl/commands/mcp.py`.
2. Add allowlist entry in `dev/config/mcp_tools_allowlist.json`.
3. Add/extend tests in `dev/scripts/devctl/tests/test_mcp.py`.
4. Update `dev/DEVCTL_AUTOGUIDE.md` and `dev/scripts/README.md`.
5. Keep behavior read-only unless policy explicitly changes.

## Closure Semantics

`dev/active/*.md` files are execution trackers. When work closes, trackers
should move out of active state, but durable docs (this file, architecture,
autoguide, command reference) stay.
