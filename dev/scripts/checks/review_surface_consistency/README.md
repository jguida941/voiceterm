# Review Surface Consistency

Implementation package for `check_review_surface_consistency.py`.

- Keep the public guard entrypoint at `dev/scripts/checks/check_review_surface_consistency.py`.
- Keep the implementation and helper modules under this package so the crowded `checks/` root stays shim-only.
- Proof-tick expected values must come from explicit field authority priority,
  not from surface iteration order. `operator_interaction_mode` is a separate
  operator-channel axis from review-loop `reviewer_mode`.
