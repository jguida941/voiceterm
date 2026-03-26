# Portable Governance Repo Setup

Use this template when another repo needs the portable devctl guard/probe stack.

## Goal

Get a new Python and/or Rust repo to a first deterministic governance run with
the least manual setup possible.

## Install Flow

1. Export or copy the governance stack into the target repo.
2. From the target repo root, run:

```bash
python3 dev/scripts/devctl.py governance-bootstrap --target-repo . --format md
```

This also writes a repo-local bootstrap guide at:

```bash
dev/guides/PORTABLE_GOVERNANCE_SETUP.md
```

Use that file as the first thing an AI or maintainer reads inside the target
repo.

3. Inspect the generated starter policy:

```bash
dev/config/devctl_repo_policy.json
```

4. Tighten the repo-owned `repo_governance` paths so `check-router`,
   `docs-check`, `surface_generation`, and `repo_governance.push` match the
   target repo’s real layout, docs, starter artifacts, and branch workflow.
5. Run the first full adoption pass:

```bash
python3 dev/scripts/devctl.py quality-policy --format md
python3 dev/scripts/devctl.py render-surfaces --write --format md
python3 dev/scripts/devctl.py startup-context --format md
python3 dev/scripts/devctl.py check --profile ci --adoption-scan
python3 dev/scripts/devctl.py probe-report --adoption-scan --format md
```

## What `governance-bootstrap` Writes

- repairs copied or broken `.git` indirection when needed
- writes `dev/config/devctl_repo_policy.json` if the target repo does not
  already have one
- writes `dev/guides/PORTABLE_GOVERNANCE_SETUP.md` unless the repo already has
  one
- picks the nearest portable preset (`portable_python`, `portable_rust`, or
  `portable_python_rust`) from detected repo capabilities
- seeds conservative `repo_governance` defaults for `check-router`,
  `docs-check`, `repo_governance.push`, and starter `surface_generation`
  outputs
- gives the repo enough starter surface policy to generate local instructions
  plus tracked pre-commit, post-commit, and pre-push stub artifacts with
  `render-surfaces --write`

## What Humans Or AI Must Still Customize

- `repo_name`
- `repo_governance.check_router.*` path classification
- `repo_governance.docs_check.*` canonical docs/evolution paths
- `repo_governance.push.*` branch rules, checkpoint thresholds, and post-push routing
- `repo_governance.surface_generation.*` repo-pack metadata, template context,
  and output paths
- repo-specific add-ons or deprecated command rewrites

## Commit / Review / Push Contract

- After a bounded checkpoint/commit, rerun
  `python3 dev/scripts/devctl.py startup-context --format md`.
- Treat `push_decision` as the portable next-step contract:
  `await_checkpoint`, `await_review`, `run_devctl_push`, `no_push_needed`.
- Only run `python3 dev/scripts/devctl.py push --execute` when the typed
  contract says `run_devctl_push`; do not infer push readiness from a clean
  worktree alone.

## Truthful Scope

The portable quality engine is ready for Python and Rust repos.
Higher-level VoiceTerm-specific workflow helpers such as Ralph, mutation, and
process-hygiene automation still need further extraction before the full
control plane is repo-agnostic.
