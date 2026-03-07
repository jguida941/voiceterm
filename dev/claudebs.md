# Claude Audit Working Brief (Reference)

Status: refreshed 2026-03-06

This file is a local working brief.
It is not execution authority.

Execution authority:
- `dev/active/MASTER_PLAN.md` (tracker)
- `dev/active/pre_release_architecture_audit.md` (canonical findings + execution checklist)

## Intent

Use the consolidated audit findings to run a sequential remediation pass.
Start with high-impact, low-risk fixes. Keep behavior stable unless an issue is
explicitly safety-critical.

## Required Quality Bar

All work in this lane must follow the readability standards already used in this
repo:

- Keep comments simple and useful; explain intent and constraints.
- Keep Python docstrings concise and clear for public APIs.
- Prefer explicit names and small focused helpers over dense logic.
- Preserve existing style consistency across Rust and Python surfaces.
- Do not trade clarity for cleverness.

## Immediate Sequence

1. Governance/docs sync for active-plan registration and discoverability links.
2. Confirm `dev/active/pre_release_architecture_audit.md` as single execution plan.
3. Keep findings and sequencing in `dev/active/pre_release_architecture_audit.md`; correct contradictions before edits.
4. Start remediation with CRITICAL runtime fix: remove `env::set_var` from `main.rs`.
5. Continue do-now items in order, validating each step with required checks.

## Verify Before Touching

- `rust/src/voice.rs` clone path: investigate ownership before changing.
- `join_thread_with_timeout` dedupe: compare behavior/signatures before extracting.
- Python import fallback removal: define canonical invocation contract first.

## Validation Baseline

- `python3 dev/scripts/checks/check_active_plan_sync.py`
- `python3 dev/scripts/checks/check_multi_agent_sync.py`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- Runtime edits: `python3 dev/scripts/devctl.py check --profile ci`
