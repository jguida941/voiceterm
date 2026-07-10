# Platform

Owns the reusable AI-governance platform contract blueprint and future shared
runtime extraction seams.

- `contracts.py`: typed platform-layer, contract, frontend, and portability
  status records.
- `definitions.py`: public reusable-platform definition exports.
- `contract_definitions.py`: static shared-contract definitions.
- `surface_definitions.py`: layer/frontend/boundary/adoption definitions.
- `blueprint.py`: canonical reusable-platform blueprint builder.
- `render.py`: markdown rendering for the read-only blueprint command.
- `parser.py`: CLI registration for read-only platform blueprint commands.

This package is the first code-facing boundary for the broader platform
extraction tracked in `dev/active/ai_governance_platform.md`.
