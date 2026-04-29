# Portable Governance Setup For `greenfield_python`

This file is the one obvious bootstrap surface for an AI or maintainer setting this repo up with the portable devctl guard/probe stack. It should frame this repo as a first-party client/product integration over the portable governance platform, while repo packs and typed runtime contracts stay backend authority for arbitrary repos.

## Detected Repo Shape

- repo_name: `greenfield_python`
- detected_capabilities: `Python`
- starter_policy_path: `dev/config/devctl_repo_policy.json`
- starter_policy_preset: `quality_presets/portable_python.json`

## Read These Files First

- `dev/guides/PORTABLE_GOVERNANCE_SETUP.md`
- `dev/config/devctl_repo_policy.json`
- `dev/scripts/README.md`
- `dev/guides/PORTABLE_CODE_GOVERNANCE.md`

## Run Order

1. `Copy or export the governance stack into the target repo if it is not already present.`
2. `cd /Users/jguida941/testing_upgrade/codex-voice/dev/test_data/adopter_repo_fixtures/greenfield_python`
3. `Inspect the starter policy at `dev/config/devctl_repo_policy.json` and tighten repo_governance paths before strict use.`
4. `python3 dev/scripts/devctl.py quality-policy --format md`
5. `python3 dev/scripts/devctl.py render-surfaces --write --format md`
6. `python3 dev/scripts/devctl.py check --profile ci --adoption-scan`
7. `python3 dev/scripts/devctl.py probe-report --adoption-scan --format md`

## Customize Before Strict Use

- Tighten `repo_governance.check_router.*` so lane routing matches this repo's real runtime/tooling/docs boundaries.
- Tighten `repo_governance.docs_check.*` so canonical user docs, maintainer docs, and engineering-history files reflect this repo instead of the starter defaults.
- Review the resolved `quality-policy` output before treating the first `adoption-scan` as authoritative.

## Truthful Scope

- The portable quality engine is ready for Python and Rust repos.
- Higher-level control-plane helpers (mutation loops, host-process hygiene, operator-console automation) are still repo-local to the originating project and not yet part of the portable core.
- This repo (`greenfield_python`) is one first-party client/product integration of the portable governance platform. Each adopting repo must supply its own product name, project summary, and repo identity through repo-pack metadata; repo packs and typed runtime contracts remain backend authority for arbitrary repos instead of inheriting defaults from any other project.
