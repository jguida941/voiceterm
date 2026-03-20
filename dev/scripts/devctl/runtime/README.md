# Runtime

Shared runtime contracts that frontends can consume without re-deriving nested
repo-local JSON shapes.

- `control_state.py`: typed `ControlState` models plus adapters that normalize
  current `mobile-status` / review-channel payloads into one reusable contract.
- `action_contracts.py`: typed `TypedAction`, `RunRecord`, `ArtifactStore`,
  `ProviderAdapter`, and `WorkflowAdapter` records plus mapping adapters.
- `value_coercion.py`: shared parser coercion helpers used by runtime contract
  loaders so new contract modules do not duplicate normalization logic.
- `project_governance.py`: typed `ProjectGovernance` startup-authority contract
  with nested records for repo identity (`RepoIdentity`), repo-pack reference
  (`RepoPackRef`), path roots (`PathRoots`), plan-registry roots
  (`PlanRegistryRoots`), artifact roots (`ArtifactRoots`), memory roots
  (`MemoryRoots`), bridge configuration (`BridgeConfig`), enabled guards/probes
  (`EnabledChecks`), and bundle overrides (`BundleOverrides`), plus mapping
  adapters for JSON round-trip.
- `review_state.py`: public `ReviewState` export surface.
- `review_state_models.py`: typed review session/queue/packet/registry models.
- `review_state_parser.py`: normalization logic for `review_state.json` and
  `full.json` review-channel projections.
