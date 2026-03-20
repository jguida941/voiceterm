# Automation Debt Register

Track repeated manual friction that should become guarded automation.

Rule: if a workaround repeats 2+ times in the same MP scope, either automate it
or log it here with a closure plan.

## Open Items

| ID | First seen | MP scope | Repeated manual step | Repeat count | Risk | Current guard path | Automation target | Owner | Status | Exit criteria |
|---|---|---|---|---:|---|---|---|---|---|---|
| ADR-001 | 2026-02-24 | `MP-330..MP-331` | Manual phone-adapter endpoint smoke flow not yet consolidated in a single command | 0 | medium | Baseline audit checklist + explicit manual script | Add `devctl` mobile-control smoke runner with report bundle | unassigned | open | CI/local command executes full endpoint smoke and emits pass/fail artifact |
| ADR-002 | 2026-03-18 | `MP-377` | Manual Codex/Claude bridge polling + re-review loop repeatedly stalls on stale-hash/heartbeat churn instead of promoting next bounded slice | 6 | high | `review-channel reviewer-heartbeat --follow`, `check_review_channel_bridge.py`, manual `code_audit.md` reviewer rewrites | Add one repo-owned `devctl` reviewer-loop action that performs poll -> focused re-review -> bridge checkpoint update -> next-slice promotion (or debt/backlog handoff) in one guarded path | `MP-377` lane (Codex conductor) | open | Single command can run the full review loop without manual bridge babysitting and demonstrates deterministic next-slice promotion within 2 consecutive cycles |

## Closed Items

| ID | Closed date | MP scope | Resolution | Evidence |
|---|---|---|---|---|
