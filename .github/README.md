# GitHub Folder Guide

This file explains what lives in `.github/`, why it exists, and what to update when files change.

## What This Folder Contains

| Path | Purpose | When to update |
|---|---|---|
| `.github/CODE_OF_CONDUCT.md` | Community behavior and enforcement policy. | Community standards or reporting path changes. |
| `.github/CONTRIBUTING.md` | Contributor workflow, checks, and PR expectations. | Build/test/docs workflow changes. |
| `.github/SECURITY.md` | Vulnerability reporting and security posture/policy. | Threat model, risky flags, or disclosure/security gate policy changes. |
| `.github/PULL_REQUEST_TEMPLATE.md` | Standard PR checklist for reviewers and authors. | Required checks/docs expectations change. |
| `.github/ISSUE_TEMPLATE/bug_report.md` | Bug report template. | New required reproduction info or renamed product/version fields. |
| `.github/ISSUE_TEMPLATE/feature_request.md` | Feature request template. | Planning intake format changes. |
| `.github/scripts/verify_perf_metrics.py` | Perf-smoke log validator used by CI. | Voice metrics schema or thresholds change. |
| `.github/workflows/*.yml` | CI workflows for build, tests, docs, perf, memory, security, and governance. | CI policy, command lanes, trigger paths, or thresholds change. |
| `.github/README.md` | This index. | Any file is added/removed/renamed or workflow behavior changes. |

## Workflow Matrix

Legend for `Policy`:
- `Required (targeted)` means expected when relevant files/risk class are touched.
- `Optional (scheduled/manual)` means long-running or periodic guardrails.

| Workflow | Trigger | What it enforces | Local equivalent | Policy |
|---|---|---|---|---|
| `.github/workflows/rust_ci.yml` | Push/PR on `src/**` | fmt + clippy + workspace tests | `python3 dev/scripts/devctl.py check --profile ci` | Required (targeted) |
| `.github/workflows/voice_mode_guard.yml` | Push/PR on `src/**` | Macro/send-mode regression tests | `cd src && cargo test --bin voiceterm settings_handlers::tests::toggle_macros_enabled_updates_state_and_status -- --nocapture` and related tests in the workflow | Required (targeted) |
| `.github/workflows/perf_smoke.yml` | Push/PR on `src/**` | Voice perf smoke + log metric validation | `cd src && cargo test --no-default-features legacy_tui::tests::perf_smoke_emits_voice_metrics -- --nocapture` | Required (targeted) |
| `.github/workflows/latency_guard.yml` | Push/PR on `src/**` or latency script/workflow | Synthetic latency regression guardrails | `./dev/scripts/tests/measure_latency.sh --ci-guard` | Required (targeted) |
| `.github/workflows/memory_guard.yml` | Push/PR on `src/**` | Repeated backend thread cleanup test | `cd src && cargo test --no-default-features legacy_tui::tests::memory_guard_backend_threads_drop -- --nocapture` | Required (targeted) |
| `.github/workflows/docs_lint.yml` | Push/PR on key markdown docs | Markdown style for published docs | `markdownlint -c .markdownlint.yaml README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md` | Required (targeted) |
| `.github/workflows/security_guard.yml` | Scheduled, manual, and dependency/security-file push/PR | RustSec advisory policy gate + artifact report | `cd src && (cargo audit --json > ../rustsec-audit.json || true)` then `python3 dev/scripts/check_rustsec_policy.py --input rustsec-audit.json --min-cvss 7.0 --fail-on-kind yanked --fail-on-kind unsound --allowlist-file dev/security/rustsec_allowlist.md` | Required (targeted) + Optional (scheduled/manual) |
| `.github/workflows/parser_fuzz_guard.yml` | Scheduled, manual, and push/PR on PTY parser paths | Property tests for parser boundary safety | `cd src && cargo test pty_session::tests::prop_find_csi_sequence_respects_bounds -- --nocapture` and related tests in the workflow | Required (targeted) + Optional (scheduled/manual) |
| `.github/workflows/audit_traceability_guard.yml` | Push/PR on audit/plan/source paths + manual | Verifies audit findings map to master plan entries | `python3 dev/scripts/check_audit_traceability.py --master-plan dev/active/MASTER_PLAN.md --audit RUST_GUI_AUDIT_2026-02-15.md` | Required (targeted) |
| `.github/workflows/mutation-testing.yml` | Nightly schedule + manual | Sharded mutation testing, aggregated score threshold | `python3 dev/scripts/devctl.py mutation-score --threshold 0.80` | Optional (scheduled/manual) |

## Fast Maintenance Rules

1. If you add, rename, or remove a workflow, update this file in the same change.
2. If a workflow command/threshold changes, update both this file and:
   - `AGENTS.md` (canonical SDLC/release policy)
   - `dev/DEVELOPMENT.md` (developer workflow)
   - `dev/ARCHITECTURE.md` if architecture/workflow/CI mechanics changed
3. If CI scope changes, update `dev/active/MASTER_PLAN.md` when it affects active execution policy.
4. Keep local command examples copy-pasteable and consistent with current binary naming (`voiceterm`).

## Common Local Checks

```bash
python3 dev/scripts/devctl.py check --profile ci
python3 dev/scripts/devctl.py docs-check --user-facing
python3 dev/scripts/devctl.py hygiene
python3 dev/scripts/devctl.py status --ci --format md
```
