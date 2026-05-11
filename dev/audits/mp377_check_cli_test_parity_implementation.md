# MP377 Check CLI Test Parity Implementation Evidence

This source records implementation evidence for `MP377-CHECK-CLI-TEST-PARITY-S1`.
It amends the existing row inserted by the MP-377 codesmell #048-#051 intake
instead of creating a second authority row.

## Evidence

- `rev_pkt_3601`: Codex architecture-choice packet for implementing the
  CLI/focused-test parity guard next.
- `rev_pkt_3602`: Claude architecture review accepted the composition decision
  and agreed that `MP377-CHECK-CLI-TEST-PARITY-S1` is the one new closure row
  for codesmell #050.
- `plan-ingest-17c9b4c7eb5196fc`: Accepted intake receipt that inserted
  `MP377-CHECK-CLI-TEST-PARITY-S1`.

## Implementation

- `dev/scripts/checks/check_check_cli_test_parity.py` validates that managed
  check CLI entrypoints and focused pytest paths share one report/evaluator
  contract.
- `dev/scripts/devctl/tests/checks/test_check_check_cli_test_parity.py` covers
  current managed checks plus negative fixtures for missing CLI shared tokens,
  missing focused-test shared tokens, and script-catalog drift.
- `dev/scripts/devctl/governance/script_catalog_registry.py` registers
  `check_cli_test_parity`.
- `dev/scripts/devctl/bundles/registry.py` includes the guard in the shared
  governance bundle.

## Verification

- `python3 dev/scripts/checks/check_check_cli_test_parity.py --format json`
- `python3 dev/scripts/devctl.py test-python --suite devctl --path dev/scripts/devctl/tests/checks/test_check_check_cli_test_parity.py --format md`
- `python3 dev/scripts/checks/check_bundle_registry_dry.py --format json`
- `python3 dev/scripts/checks/check_schema_migration_spine.py --format json`
- `python3 dev/scripts/checks/check_state_store_authority.py --format json`
- `python3 dev/scripts/devctl.py check-router --format md`
