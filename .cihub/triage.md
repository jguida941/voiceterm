# devctl triage

- timestamp: 2026-02-23T12:03:18.881234
- issues: 3
- warnings: 1

## Rollup

- total: 3
- by_severity: high=1, medium=2
- by_category: infra=2, quality=1
- by_owner: platform=2, runtime=1

## Project Snapshot

# triage snapshot

- Branch: develop
- Changelog updated: False
- Master plan updated: False
- Changed files: 0
- Mutation score: 69.35%
- Mutation outcomes: /Users/jguida941/testing_upgrade/codex-voice/src/mutants.out/mutants.out/outcomes.json
- Mutation outcomes updated: 2026-02-20T09:45:48.454007Z (79.29h old)
- CI: error (gh run list failed: Command '['gh', 'run', 'list', '--limit', '5', '--json', 'status,conclusion,displayTitle,headSha,createdAt,updatedAt']' returned non-zero exit status 1.)

## Issues

- [high] infra -> platform: CI fetch failed: gh run list failed: Command '['gh', 'run', 'list', '--limit', '5', '--json', 'status,conclusion,displayTitle,headSha,createdAt,updatedAt']' returned non-zero exit status 1.
- [medium] quality -> runtime: Mutation score below target: 69.35%
- [medium] infra -> platform: cihub triage command failed; check cihub version/flags.

## Next Actions

- Run `python3 dev/scripts/devctl.py status --ci --require-ci --format md` and inspect failing workflow runs.
- Run `python3 dev/scripts/devctl.py check --profile ci` and `python3 dev/scripts/devctl.py mutation-score` to confirm quality gates.

## CIHub

- enabled: True
- command exit: 2
