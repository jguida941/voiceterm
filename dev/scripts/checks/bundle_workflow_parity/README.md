# Bundle Workflow Parity

Helper logic for `check_bundle_workflow_parity.py`.

- Keep the public guard entrypoint at
  `dev/scripts/checks/check_bundle_workflow_parity.py`.
- Keep workflow parsing, trigger-path extraction, and job-sequence checks under
  `dev/scripts/checks/bundle_workflow_parity/` so the crowded checks root
  stays reserved for stable runnable entrypoints.
