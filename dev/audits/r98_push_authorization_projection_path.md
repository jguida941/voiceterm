# R98 Push Authorization Projection Path

Generated: 2026-05-14

## Finding

`devctl push --execute` completed the routed preflight checks for HEAD
`aee417b681a30dc8703212b9c1a846707ef8a191` but blocked publication with
`push_authorization_missing`.

The active authorization is present in
`dev/reports/review_channel/projections/latest/commit_pipeline.json`:

- `authorization_id`: `push-auth-20260514T225019404533Z`
- `authorized_head_sha`: `aee417b681a30dc8703212b9c1a846707ef8a191`
- `approval_mode`: `commit_pipeline_approval`
- `guard_status`: `pass`

The publication gate currently loads the pipeline through
`active_path_config().review_status_dir_rel`, which resolves to
`dev/reports/review_channel/latest`. That directory does not contain
`commit_pipeline.json`; the stale sibling
`dev/reports/review_channel/projections/commit_pipeline.json` is also empty.

## Required Fix

Make publication authorization consume the canonical event-backed pipeline
artifact under `review_projections_dir_rel`, with a compatibility fallback for
legacy status roots. Add coverage proving an authorization stored in
`projections/latest/commit_pipeline.json` is visible to
`publication_authorization_decision()`.
