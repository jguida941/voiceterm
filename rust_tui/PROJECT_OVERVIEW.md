# Codex Voice – Project Overview

## Scope & Goals
- Build a Rust-first TUI wrapper that orchestrates voice capture, transcription, and Codex interactions with low latency (<500 ms per subsystem when healthy).
- Preserve Codex as the core executor; the wrapper layers on voice input, UX polish, and CI/testing discipline.
- Maintain daily architecture notes for traceability (`docs/architecture/YYYY-MM-DD/`) and keep this overview as the immutable map.

## Major Architectural Decisions
1. **2025-11-13 – Fail-Fast PTY Wrapper**  
   - PTY optimization remains optional; any failure disables it for the session within 0.5 s.  
   - UI redraw macro introduced to ensure visible feedback.  
   - Audio resampler warning throttled.  
   - Details: [docs/architecture/2025-11-13/](docs/architecture/2025-11-13/)

## “You Are Here”
- Latest worklog: **2025-11-13** (see link above).  
- Status: Fail-fast PTY path, redraw macro, and audio log throttling implemented with tests + CI commands recorded.  
- Next steps: Integrate telemetry dashboards and tackle PTY reader thread cleanup / voice-capture timeout.
