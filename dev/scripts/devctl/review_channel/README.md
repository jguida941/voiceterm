# Review Channel

Owns review-channel events, state, prompts, and projections.

- New review-channel logic belongs here.
- `attention.py` owns the typed stale-peer / stale-reviewer attention contract.
- `state.py` owns projection refresh orchestration; `status_projection.py` owns
  bridge-backed review-state payload assembly.
- `launch.py` owns session-script generation; `terminal_app.py` owns macOS
  Terminal.app launch behavior.
- Root-level `review_channel_*.py` files remain compatibility shims only.
