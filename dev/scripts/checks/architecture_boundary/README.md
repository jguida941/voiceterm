# Architecture Boundary Checks

Helper logic for `check_platform_layer_boundaries.py`.

- Keep the public guard entrypoint at
  `dev/scripts/checks/check_platform_layer_boundaries.py`.
- Keep the implementation under `dev/scripts/checks/architecture_boundary/`
  so the crowded `dev/scripts/checks/` root stays reserved for stable
  runnable entrypoints.
- Treat this family as the first self-hosting extraction-enforcement slice:
  it blocks new frontend-to-orchestration imports where the active platform
  plan now requires runtime-contract seams instead.
