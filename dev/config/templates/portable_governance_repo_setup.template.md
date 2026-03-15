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
   `docs-check`, and `surface_generation` match the target repo’s real layout,
   docs, and starter artifacts.
5. Run the first full adoption pass:

```bash
python3 dev/scripts/devctl.py quality-policy --format md
python3 dev/scripts/devctl.py render-surfaces --write --format md
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
  `docs-check`, and starter `surface_generation` outputs
- gives the repo enough starter surface policy to generate local instructions
  plus tracked stub artifacts with `render-surfaces --write`

## What Humans Or AI Must Still Customize

- `repo_name`
- `repo_governance.check_router.*` path classification
- `repo_governance.docs_check.*` canonical docs/evolution paths
- `repo_governance.surface_generation.*` repo-pack metadata, template context,
  and output paths
- repo-specific add-ons or deprecated command rewrites

## Truthful Scope

The portable quality engine is ready for Python and Rust repos.
Higher-level VoiceTerm-specific workflow helpers such as Ralph, mutation, and
process-hygiene automation still need further extraction before the full
control plane is repo-agnostic.
