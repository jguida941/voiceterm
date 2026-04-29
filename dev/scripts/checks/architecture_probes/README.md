# Architecture Probes

Advisory probes in this package consume typed platform architecture snapshots
instead of only scanning line-level syntax. Keep root `probe_architecture_*.py`
files as public entrypoint shims and put implementation here once the family
grows beyond a single probe.

- `probe_architecture_connectivity.py` checks typed architecture edge coverage.
- `probe_typed_authority_provenance.py` checks that typed authority signals
  carry ingestion provenance and an `InstructionPriorityDecision`.
