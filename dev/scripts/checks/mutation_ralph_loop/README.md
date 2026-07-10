# Mutation Ralph Loop

Helper logic for the bounded mutation remediation loop.

- Keep the stable compatibility import surface at
  `dev/scripts/checks/mutation_ralph_loop_core.py`.
- Keep outcome parsing and loop orchestration under
  `dev/scripts/checks/mutation_ralph_loop/` so the crowded checks root stays
  reserved for stable runnable entrypoints and compatibility seams.
