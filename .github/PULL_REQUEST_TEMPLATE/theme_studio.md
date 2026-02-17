## Theme Studio PR

Use this template for Theme Studio work (MP-148..MP-182).
If this is not Theme Studio scope, use `.github/PULL_REQUEST_TEMPLATE.md`.

### Summary

What changed and why?

### Master Plan Linkage

- [ ] Linked MP items: `MP-____`, `MP-____`
- [ ] `dev/active/MASTER_PLAN.md` updated for scope/status changes
- [ ] `dev/active/theme_upgrade.md` updated if gates/scope changed

### Gate Checklist (`TS-G01`..`TS-G15`)

Mark each gate as:
- `[x]` pass
- `[ ]` not passed
- `N/A` with reason in notes

- [ ] `TS-G01 Ownership`
- [ ] `TS-G02 Schema`
- [ ] `TS-G03 Resolver`
- [ ] `TS-G04 Component IDs`
- [ ] `TS-G05 Studio Controls`
- [ ] `TS-G06 Snapshot Matrix`
- [ ] `TS-G07 Interaction UX`
- [ ] `TS-G08 Edit Safety`
- [ ] `TS-G09 Capability Fallback`
- [ ] `TS-G10 Runtime Budget`
- [ ] `TS-G11 Docs/Operator`
- [ ] `TS-G12 Release Readiness`
- [ ] `TS-G13 Inspector`
- [ ] `TS-G14 Rule Engine`
- [ ] `TS-G15 Ecosystem Packs`

### Gate Notes

For any gate marked not passed or `N/A`, explain why and link the tracking MP/task.

- `TS-G__`:

### Verification Bundle

- [ ] `python3 dev/scripts/devctl.py check --profile ci`
- [ ] `python3 dev/scripts/devctl.py docs-check --user-facing`
- [ ] `python3 dev/scripts/devctl.py hygiene`
- [ ] `cd src && cargo test --bin voiceterm`

### Evidence Artifacts

- [ ] Snapshot diffs attached for touched surfaces/states
- [ ] Terminal capability matrix output attached (if capability paths touched)
- [ ] Interaction QA checklist attached (keyboard-only + mouse)
- [ ] Rollback/import-export proof attached (if editor/persistence touched)
- [ ] Performance/memory evidence attached (if render/update hot paths touched)

### Docs + UX Alignment

- [ ] `dev/CHANGELOG.md` updated for user-facing behavior changes
- [ ] `guides/USAGE.md` updated if controls/UX changed
- [ ] `guides/CLI_FLAGS.md` updated if flags/defaults changed
- [ ] `guides/TROUBLESHOOTING.md` updated if failure/recovery behavior changed
- [ ] Screenshots/tables updated where UI output changed
