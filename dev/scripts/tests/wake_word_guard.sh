#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/../../.." && pwd)"
SOAK_ROUNDS="${WAKE_WORD_SOAK_ROUNDS:-4}"

RUST_DIR="${REPO_ROOT}/rust"
if [[ ! -d "${RUST_DIR}" ]]; then
  RUST_DIR="${REPO_ROOT}/src"
fi

cd "${RUST_DIR}"

echo "Running wake-word regression guard tests..."
cargo test --bin voiceterm wake_word::tests::contains_hotword_phrase_detects_supported_aliases -- --nocapture
cargo test --bin voiceterm wake_word::tests::wake_runtime_sync_starts_stops_and_pauses_listener -- --nocapture
cargo test --bin voiceterm wake_word::tests::wake_runtime_sync_restarts_listener_when_settings_change -- --nocapture
cargo test --bin voiceterm event_loop::tests::wake_word_detection_starts_capture_via_shared_trigger_path -- --nocapture
cargo test --bin voiceterm event_loop::tests::wake_word_detection_is_ignored_while_recording -- --nocapture
cargo test --bin voiceterm event_loop::tests::wake_word_detection_is_ignored_when_disabled -- --nocapture
cargo test --bin voiceterm event_loop::tests::wake_word_detection_is_ignored_when_overlay_is_open -- --nocapture
cargo test --bin voiceterm event_loop::tests::run_periodic_tasks_wake_badge_pulse_refreshes_full_hud_when_interval_elapsed -- --nocapture
cargo test --bin voiceterm event_loop::tests::run_periodic_tasks_wake_badge_pulse_waits_for_interval -- --nocapture

echo "Running wake-word soak gate (${SOAK_ROUNDS} rounds)..."
for i in $(seq 1 "${SOAK_ROUNDS}"); do
  echo "Wake-word soak iteration ${i}/${SOAK_ROUNDS}"
  cargo test --bin voiceterm wake_word::tests::hotword_guardrail_soak_false_positive_and_latency -- --nocapture
done

echo "Wake-word guard checks passed."
