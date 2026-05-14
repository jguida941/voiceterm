# Review Channel

Owns review-channel events, state, prompts, and projections.

- New review-channel logic belongs here.
- `agent_packet_attention.py`, `agent_packet_attention_decision.py`, and
  `recovery_assessment.py` own the typed stale-peer / stale-reviewer attention
  and recovery contracts; `attention.py` is only a compatibility shim.
- `state.py` owns projection refresh orchestration; `status_projection.py` owns
  bridge-backed review-state payload assembly.
- `launch.py` owns session-script generation; `terminal_app.py` owns macOS
  Terminal.app launch behavior.
- Root-level `review_channel_*.py` files remain compatibility shims only.
