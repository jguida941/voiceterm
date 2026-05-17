# Devctl

`devctl` is the canonical maintainer control plane for repo checks, reporting, and release tooling.

- `cli.py`: top-level command parser and dispatcher.
- Root-level package modules are reserved for cross-cutting infrastructure and temporary compatibility shims.
- Canonical feature ownership belongs in the subpackages documented below.
- `governance/`: repo-policy loaders, surface-generation helpers, and
  governance-owned parser wiring for reusable adoption/bootstrap surfaces.
- `platform/`: reusable AI-governance platform contract blueprint and shared extraction boundary definitions.
- `runtime/`: typed shared runtime state contracts consumed by CLI/UI/mobile surfaces.
