# Automation Debt Register

Track repeated manual friction that should become guarded automation.

Rule: if a workaround repeats 2+ times in the same MP scope, either automate it
or log it here with a closure plan.

## Open Items

| ID | First seen | MP scope | Repeated manual step | Repeat count | Risk | Current guard path | Automation target | Owner | Status | Exit criteria |
|---|---|---|---|---:|---|---|---|---|---|---|
| ADR-001 | 2026-02-24 | `MP-330..MP-331` | Manual phone-adapter endpoint smoke flow not yet consolidated in a single command | 0 | medium | Baseline audit checklist + explicit manual script | Add `devctl` mobile-control smoke runner with report bundle | unassigned | open | CI/local command executes full endpoint smoke and emits pass/fail artifact |

## Closed Items

| ID | Closed date | MP scope | Resolution | Evidence |
|---|---|---|---|---|
