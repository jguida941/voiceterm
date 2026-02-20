# Senior Engineering Audit Baseline (2026-02-20)

## Scope

Audit objective: produce a no-sugarcoat engineering baseline for code quality,
scalability, CI/CD hardening, tooling governance, and automation readiness.

Repository focus: `voiceterm` runtime + tooling surfaces (`src/**`,
`.github/workflows/**`, `dev/scripts/**`, process docs).

## Evidence Snapshot

| Area | Metric | Evidence |
|---|---|---|
| Rust production size | `50,121` LOC across `181` non-test files | `find src/src -name '*.rs' | rg -v '/tests/|tests\\.rs$|_tests\\.rs$' | xargs wc -l` |
| Largest production files | `event_loop/input_dispatch.rs` `1561`, `status_line/format.rs` `1128`, `status_line/buttons.rs` `1059`, `theme/rule_profile.rs` `1050`, `session_guard.rs` `862`, `color_mode.rs` `838` | same as above |
| Inline test coupling | `113/181` production files include `mod tests` | `rg -n "mod tests\\b" src/src --glob '*.rs' ...` |
| `#[allow(...)]` usage | `120` attributes across `42` files; top hotspots: `pty_session/counters.rs` `20`, `ipc/session.rs` `11` | `rg -n "#\\[allow\\(" src/src --glob '*.rs'` |
| Panic/unwrap debt (prod) | `185` non-test `unwrap/expect` call sites | `rg -n "\\b(unwrap|expect)\\(" src/src --glob '*.rs' ...` |
| Workflow action pinning | `42/42` action uses are not SHA pinned | `rg -n "^\\s*-?\\s*uses:" .github/workflows/*.yml` |
| Workflow permissions | `10` workflows missing root `permissions:` block | `docs_lint`, `latency_guard`, `lint_hardening`, `memory_guard`, `parser_fuzz_guard`, `perf_smoke`, `security_guard`, `tooling_control_plane`, `voice_mode_guard`, `wake_word_guard` |
| Workflow concurrency | `12` workflows missing root `concurrency:` block | all except `mutation-testing.yml` and `publish_pypi.yml` |
| Ownership/dependency automation | `.github/CODEOWNERS` missing, `.github/dependabot.yml` missing | file existence checks |
| Lint baseline | `devctl check --profile maintainer-lint` passes | local run completed |
| Marker debt comments | very low explicit TODO/FIXME/HACK footprint (single TODO in `src/src/audio/tests.rs`) | `rg -n "TODO|FIXME|XXX|HACK" .` |

## Findings (Prioritized)

1. **P0 - CI supply-chain hardening gap**
   - Every third-party GitHub Action is tag-pinned (`@v4`, etc.) instead of
     commit-SHA pinned.
   - Most workflows still rely on implicit default token permissions.
   - Most workflows can run duplicate in-flight builds without concurrency
     cancellation.
   - Risk: action-tag compromise, accidental over-privileged token use, and
     avoidable CI waste/race conditions.

2. **P0 - Ownership and dependency governance gap**
   - No `CODEOWNERS` means review routing is policy-only, not enforceable.
   - No Dependabot configuration means dependency drift is manual and easy to
     miss.
   - Risk: slower review accountability and larger, riskier dependency jumps.

3. **P1 - Runtime modularity/scalability pressure**
   - Several runtime files exceed 1,000 lines and keep broad responsibilities.
   - Inline tests are embedded in most production modules (`113/181`), which
     raises merge pressure in busy files.
   - Risk: broad blast radius for changes, slower reviews, and regression risk.

4. **P1 - Lint/debt policy pressure**
   - `#[allow(...)]` and non-test `unwrap/expect` usage remain substantial.
   - Current lanes catch regressions but do not yet enforce debt burn-down
     targets over time.
   - Risk: steady-state tolerance of fragile failure paths and dead-code drift.

5. **P2 - Naming/API cohesion opportunity**
   - Large surfaces (theme/event-loop/status/memory) still have helper overlap
     and mixed naming specificity.
   - Risk: higher ramp-up cost for contributors and slower feature scaling.

## Execution Mapping

- `MP-262` (completed): audit baseline published in this document.
- `MP-263`: CI supply-chain hardening (`uses` SHA pinning, `permissions`,
  `concurrency` policy).
- `MP-264`: ownership/dependency automation (`CODEOWNERS`, `dependabot.yml`).
- `MP-265`: oversized runtime decomposition program with shape budgets.
- `MP-266`: lint/debt burn-down + measurable gates.
- `MP-267`: naming/API cohesion and helper consolidation pass.
- `MP-268` (completed): Rust-reference-first engineering contract codified in
  `AGENTS.md` and `dev/DEVELOPMENT.md`.

## Recommended Execution Order

1. Implement `MP-263` and `MP-264` first (highest governance and CI risk).
2. Run `MP-265` and `MP-266` in parallel tracks with strict non-regression
   evidence on each extraction/debt reduction slice.
3. Apply `MP-267` after first decomposition slices land so naming/API cleanup
   happens against stabilized module boundaries.
