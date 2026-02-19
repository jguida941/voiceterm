# Documentation and Organization Audit (Accuracy-Corrected)

**Date:** 2026-02-19  
**Scope:** Repo docs structure, readability, duplication, and process discoverability  
**Purpose of this revision:** Correct inaccurate claims in the prior audit and keep only actionable recommendations aligned with current repo state.

---

## Executive Summary

The documentation is strong and already includes substantial governance automation.  
The biggest remaining improvements are:

1. Rewrite high-traffic `dev/` docs in plain language (less policy jargon, shorter sentences, clearer steps).
2. Add user-facing flowcharts in a few key guides where they help decisions.
3. Reduce duplication across onboarding docs (`README.md`, `QUICK_START.md`, guides).
4. Make contributor flow easier to scan in `.github/CONTRIBUTING.md`.
5. Resolve orphan/stale docs (`.github/GUIDE.md`, `dev/BACKLOG.md`) with an explicit decision.

---

## Accuracy Corrections to Prior Draft

| Prior claim | Correct status (2026-02-19) | Evidence |
|---|---|---|
| Missing dev push/process flowchart | **Outdated**. Added in `dev/DEVELOPMENT.md` | `End-to-end lifecycle flow`, `When to push where` |
| Missing issue templates | **Incorrect**. Already present | `.github/ISSUE_TEMPLATE/bug_report.md`, `.github/ISSUE_TEMPLATE/feature_request.md` |
| Whisper guide not linked from README | **Incorrect**. Already linked | `README.md` links `guides/WHISPER.md` |
| `DEV_INDEX.md` should be removed as redundant | **Not recommended now**. It is part of current governance/navigation contract | Referenced by `AGENTS.md`, `README.md`, lint/governance command sets |
| "No flowcharts for developer workflow" | **Outdated**. Multiple already exist | `dev/DEVELOPMENT.md`, `dev/ARCHITECTURE.md`, `dev/history/ENGINEERING_EVOLUTION.md`, `README.md` |

---

## Current Documentation State (Verified)

### Strengths

- Clear user docs split under `guides/`.
- Strong developer/process docs split under `dev/`.
- Governance checks are automated and enforced in CI:
  - `docs-check` (`--user-facing`, `--strict-tooling`)
  - `check_agents_contract.py`
  - `check_active_plan_sync.py`
  - `check_release_version_parity.py`
  - `check_cli_flags_parity.py`
  - `check_screenshot_integrity.py`
- Multiple Mermaid diagrams already exist in key docs:
  - `README.md`
  - `dev/DEVELOPMENT.md`
  - `dev/ARCHITECTURE.md`
  - `dev/history/ENGINEERING_EVOLUTION.md`

### Scale reality (not a bug, but important)

- `AGENTS.md` is intentionally dense and policy-driven (AI + maintainer governance).
- `dev/active/MASTER_PLAN.md` is an internal execution tracker, not contributor onboarding.
- `dev/ARCHITECTURE.md` and `dev/history/ENGINEERING_EVOLUTION.md` are long by design.

---

## Remaining Gaps That Still Make Sense to Fix

| Area | Current issue | Recommended fix |
|---|---|---|
| `dev/` doc language | Many sections read as policy-heavy/governance-heavy and are hard to scan quickly | Do a plain-language pass on `dev/README.md`, `dev/DEVELOPMENT.md`, and key `dev/` landing sections while preserving technical accuracy |
| User journey visuals | No lifecycle/diagnostic flowcharts in `guides/USAGE.md` and `guides/TROUBLESHOOTING.md` | Add concise Mermaid diagrams for voice lifecycle and troubleshooting decision tree |
| Install choice clarity | README install choices are readable but still text-heavy | Add install decision flowchart in `README.md` |
| Contributor quick path | `.github/CONTRIBUTING.md` is concise but not visual | Add one contributor flowchart (`branch -> change type -> checks -> PR`) |
| Quick start control density | `QUICK_START.md` still lists many controls in one block | Split into "core controls" and link to full controls in `guides/USAGE.md` |
| Command duplication | Some overlap remains across `AGENTS.md`, `dev/DEVELOPMENT.md`, `dev/scripts/README.md` | Keep `AGENTS.md` canonical and shorten duplicates to "summary + link" |
| Orphan/stale docs | `.github/GUIDE.md` unreferenced; `dev/BACKLOG.md` appears stale vs `MASTER_PLAN` backlog | Explicitly archive/remove or integrate |

---

## Decision Matrix for Prior Recommendations

Status values:

- `keep`: execute as proposed
- `modify`: execute, but adjusted for current architecture/process
- `drop`: do not execute (incorrect or conflicts with current governance)

| # | Prior recommendation | Status | Decision |
|---|---|---|---|
| 1 | Add human-oriented contributor guidance | `keep` | Add a simple contributor flow to `.github/CONTRIBUTING.md`; keep `AGENTS.md` canonical |
| 2 | Deduplicate CLI flags across docs | `modify` | Keep short "common flags" snippets in onboarding docs, canonical full reference in `guides/CLI_FLAGS.md` |
| 3 | Deduplicate install steps between README and QUICK_START | `keep` | Reduce repeated prose; keep role separation |
| 4 | Add troubleshooting flowchart | `keep` | Add to `guides/TROUBLESHOOTING.md` |
| 5 | Add voice lifecycle flowchart to USAGE | `keep` | Add to `guides/USAGE.md` |
| 6 | Simplify QUICK_START controls | `keep` | Split core vs full controls |
| 7 | Add install decision flowchart to README | `keep` | Add compact decision tree |
| 8 | Deduplicate CI/check command lists across AGENTS/DEVELOPMENT/scripts | `modify` | Preserve AGENTS bundles; convert other docs to summary + deep-link style |
| 9 | Add "Start Here" to ARCHITECTURE | `keep` | Add short new-contributor file map |
| 10 | Deduplicate release workflow across 3 files | `modify` | Keep AGENTS policy + scripts command inventory; trim duplicate procedural text |
| 11 | Remove `DEV_INDEX.md` | `drop` | Keep due to active governance/discovery linkage |
| 12 | Add issue templates | `drop` | Already done |
| 13 | Handle `.github/GUIDE.md` and `dev/BACKLOG.md` | `keep` | Required cleanup decision |
| 14 | Add contributor workflow flowchart | `keep` | Add to `.github/CONTRIBUTING.md` |
| 15 | Plain-language pass on QUICK_START and INSTALL | `keep` | Focused wording pass without policy drift |
| 16 | Add screenshot version labels | `modify` | Optional; if done, keep lightweight and automate freshness via existing screenshot checks |
| 17 | Link WHISPER guide from more places | `modify` | README already linked; consider adding one pointer in `guides/CLI_FLAGS.md` Whisper section |
| 18 | Friendlier language in ENGINEERING_EVOLUTION quick-read | `optional` | Nice-to-have only; lower priority |
| 19 | Add release flowchart to `dev/scripts/README.md` | `optional` | Useful but not urgent given existing lifecycle chart in DEVELOPMENT |
| 20 | Enable GitHub Discussions | `optional` | Product/community decision, not docs blocker |

---

## Updated Execution Plan (Start Now)

### Phase 0 (highest impact, do first)

1. Plain-language pass for `dev/README.md`:
   - replace policy-heavy wording with direct "what this file is for" language.
   - keep links/authority unchanged.
2. Plain-language pass for `dev/DEVELOPMENT.md`:
   - simplify section intros and command explanations.
   - keep command content and safety expectations unchanged.
3. Plain-language pass for `dev/ARCHITECTURE.md` intro and workflow text:
   - keep diagrams and technical facts.
   - simplify narrative around them.
4. Add a style rule for `dev/` docs: "write for a user or dev who is new to this repo."

### Phase 1 (high impact, low risk)

1. Add `README.md` install decision flowchart.
2. Add `guides/USAGE.md` voice input lifecycle flowchart.
3. Add `guides/TROUBLESHOOTING.md` diagnosis flowchart.
4. Add contributor workflow flowchart to `.github/CONTRIBUTING.md`.
5. Split `QUICK_START.md` controls into:
   - core controls
   - link to full controls (`guides/USAGE.md`)

### Phase 2 (duplication and cleanup)

1. Reduce repeated check/release prose in `dev/DEVELOPMENT.md` and `dev/scripts/README.md` where AGENTS already defines canonical bundles.
2. Reduce repeated install prose between `README.md` and `QUICK_START.md`.
3. Decide fate of `.github/GUIDE.md`:
   - integrate into `.github/CONTRIBUTING.md`, or
   - archive/remove.
4. Decide fate of `dev/BACKLOG.md`:
   - archive, or
   - explicitly mark as non-canonical and link `MASTER_PLAN` backlog authority.

### Phase 3 (nice-to-have polish)

1. Add `ARCHITECTURE.md` "Start Here" quick file map.
2. Optionally add screenshot version labels if they do not create maintenance burden.
3. Optional language polish in `dev/history/ENGINEERING_EVOLUTION.md` quick-read sections.

---

## Validation Criteria

All docs changes in this plan should pass:

```bash
python3 dev/scripts/devctl.py docs-check --user-facing
python3 dev/scripts/devctl.py docs-check --strict-tooling
python3 dev/scripts/devctl.py hygiene
python3 dev/scripts/check_agents_contract.py
python3 dev/scripts/check_active_plan_sync.py
python3 dev/scripts/check_cli_flags_parity.py
python3 dev/scripts/check_screenshot_integrity.py --stale-days 120
markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md AGENTS.md dev/DEVELOPMENT.md dev/scripts/README.md dev/active/MASTER_PLAN.md dev/history/ENGINEERING_EVOLUTION.md
find . -maxdepth 1 -type f -name '--*'
```

---

## Final Note

This corrected audit keeps the strong parts of the prior review, removes factual drift, and narrows execution to items that still produce real value under the current documentation governance model.
