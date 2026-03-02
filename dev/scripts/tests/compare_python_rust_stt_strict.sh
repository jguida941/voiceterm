#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Strict STT-only benchmark: same WAV clip, same model, Rust vs Python.

Usage:
  dev/scripts/tests/compare_python_rust_stt_strict.sh [options]

Options:
  --count N                     STT runs per engine on the same WAV (default: 3)
  --seconds N, --secs N         Capture duration in seconds (default: 3)
  --whisper-model NAME          Model name for Python whisper (default: base.en)
  --whisper-model-path PATH     GGML model path for Rust whisper-rs
  --lang CODE                   Language for transcription (default: en)
  --ffmpeg-device DEVICE        Input device override for ffmpeg
  --auto-install-whisper        Install openai-whisper if whisper CLI/module missing
  --no-auto-install-whisper     Disable auto install prompt/install
  --python-cmd CMD              Python command used for installs/runs (default: python3)
  -h, --help                    Show help

Examples:
  dev/scripts/tests/compare_python_rust_stt_strict.sh --count 3 --secs 3
  dev/scripts/tests/compare_python_rust_stt_strict.sh --count 5 --whisper-model base.en
EOF
}

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
if [[ -d "$REPO_ROOT/rust" ]]; then
  WORKSPACE_ROOT="$REPO_ROOT/rust"
elif [[ -d "$REPO_ROOT/src" ]]; then
  WORKSPACE_ROOT="$REPO_ROOT/src"
else
  echo "error: unable to locate Rust workspace (expected rust/ or src/)" >&2
  exit 2
fi

COUNT=3
SECONDS_CAPTURE=3
WHISPER_MODEL="base.en"
WHISPER_MODEL_PATH=""
LANGUAGE="en"
FFMPEG_DEVICE=""
AUTO_INSTALL_WHISPER="prompt"
PYTHON_CMD="${PYTHON_CMD:-python3}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --count)
      COUNT="$2"
      shift 2
      ;;
    --seconds|--secs)
      SECONDS_CAPTURE="$2"
      shift 2
      ;;
    --whisper-model)
      WHISPER_MODEL="$2"
      shift 2
      ;;
    --whisper-model-path)
      WHISPER_MODEL_PATH="$2"
      shift 2
      ;;
    --lang)
      LANGUAGE="$2"
      shift 2
      ;;
    --ffmpeg-device)
      FFMPEG_DEVICE="$2"
      shift 2
      ;;
    --auto-install-whisper)
      AUTO_INSTALL_WHISPER="true"
      shift
      ;;
    --no-auto-install-whisper)
      AUTO_INSTALL_WHISPER="false"
      shift
      ;;
    --python-cmd)
      PYTHON_CMD="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "error: unknown option '$1'" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if ! [[ "$COUNT" =~ ^[0-9]+$ ]] || [[ "$COUNT" -lt 1 ]]; then
  echo "error: --count must be a positive integer" >&2
  exit 2
fi
if ! [[ "$SECONDS_CAPTURE" =~ ^[0-9]+$ ]] || [[ "$SECONDS_CAPTURE" -lt 1 ]]; then
  echo "error: --seconds/--secs must be a positive integer" >&2
  exit 2
fi

ensure_whisper_python() {
  if "$PYTHON_CMD" - <<'PY' >/dev/null 2>&1
import importlib
importlib.import_module("whisper")
PY
  then
    return 0
  fi

  if [[ "$AUTO_INSTALL_WHISPER" == "prompt" ]] && [[ -t 0 ]]; then
    echo "Python module 'whisper' not found."
    read -r -p "Install openai-whisper now using '$PYTHON_CMD'? [Y/n] " answer
    answer="${answer:-Y}"
    case "$answer" in
      [Yy]|[Yy][Ee][Ss]) AUTO_INSTALL_WHISPER="true" ;;
      *) AUTO_INSTALL_WHISPER="false" ;;
    esac
  fi

  if [[ "$AUTO_INSTALL_WHISPER" == "true" ]]; then
    "$PYTHON_CMD" -m pip install --upgrade pip
    "$PYTHON_CMD" -m pip install openai-whisper
    if command -v pyenv >/dev/null 2>&1; then
      pyenv rehash || true
    fi
  fi

  "$PYTHON_CMD" - <<'PY' >/dev/null 2>&1
import importlib
importlib.import_module("whisper")
PY
}

discover_rust_model_path() {
  local model="$1"
  local model_base="${model%.en}"
  local candidates=(
    "$REPO_ROOT/whisper_models/ggml-${model}.bin"
    "$REPO_ROOT/whisper_models/ggml-${model_base}.en.bin"
    "$REPO_ROOT/whisper_models/ggml-${model_base}.bin"
    "$REPO_ROOT/whisper_models/ggml-base.en.bin"
    "$HOME/.local/share/voiceterm/models/ggml-${model}.bin"
    "$HOME/.local/share/voiceterm/models/ggml-${model_base}.en.bin"
    "$HOME/.local/share/voiceterm/models/ggml-${model_base}.bin"
    "$HOME/.local/share/voiceterm/models/ggml-base.en.bin"
  )
  for candidate in "${candidates[@]}"; do
    if [[ -f "$candidate" ]]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done
  return 1
}

if [[ -z "$WHISPER_MODEL_PATH" ]]; then
  if ! WHISPER_MODEL_PATH="$(discover_rust_model_path "$WHISPER_MODEL")"; then
    echo "error: unable to locate a Rust GGML model for '$WHISPER_MODEL'." >&2
    echo "Pass one explicitly with --whisper-model-path <path>." >&2
    exit 2
  fi
fi

if [[ ! -f "$WHISPER_MODEL_PATH" ]]; then
  echo "error: whisper model path does not exist: $WHISPER_MODEL_PATH" >&2
  exit 2
fi

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "error: ffmpeg is required on PATH" >&2
  exit 2
fi

if ! command -v "$PYTHON_CMD" >/dev/null 2>&1; then
  echo "error: python command '$PYTHON_CMD' not found" >&2
  exit 2
fi

if ! ensure_whisper_python; then
  echo "error: Python module 'whisper' is unavailable. Re-run with --auto-install-whisper." >&2
  exit 2
fi

WAV_PATH="/tmp/voiceterm-strict-stt-$$.wav"
cleanup() {
  rm -f "$WAV_PATH"
}
trap cleanup EXIT

echo "Recording one shared WAV clip for strict STT comparison."
echo "Model (Python): $WHISPER_MODEL"
echo "Model (Rust GGML path): $WHISPER_MODEL_PATH"
echo "Runs per engine: $COUNT"
echo ""
read -r -p "Press Enter, then speak for ${SECONDS_CAPTURE}s..." _

if [[ "$(uname -s)" == "Darwin" ]]; then
  INPUT_DEVICE="${FFMPEG_DEVICE:-:0}"
  ffmpeg -loglevel error -y -f avfoundation -i "$INPUT_DEVICE" -t "$SECONDS_CAPTURE" -ac 1 -ar 16000 "$WAV_PATH"
elif [[ "$(uname -s)" == "Linux" ]]; then
  INPUT_DEVICE="${FFMPEG_DEVICE:-default}"
  ffmpeg -loglevel error -y -f pulse -i "$INPUT_DEVICE" -t "$SECONDS_CAPTURE" -ac 1 -ar 16000 "$WAV_PATH"
else
  echo "error: unsupported OS for automatic capture ($(uname -s))." >&2
  exit 2
fi

cd "$WORKSPACE_ROOT"
cargo build --quiet --release --bin stt_file_benchmark

RUST_LINE="$(cargo run --quiet --release --bin stt_file_benchmark -- \
  --wav "$WAV_PATH" \
  --runs "$COUNT" \
  --whisper-model "$WHISPER_MODEL" \
  --whisper-model-path "$WHISPER_MODEL_PATH" \
  --lang "$LANGUAGE")"

PYTHON_LINE="$("$PYTHON_CMD" - "$WAV_PATH" "$WHISPER_MODEL" "$COUNT" "$LANGUAGE" <<'PY'
import statistics
import sys
import time

import whisper

wav_path = sys.argv[1]
model_name = sys.argv[2]
runs = int(sys.argv[3])
lang = sys.argv[4]

model = whisper.load_model(model_name)
times = []
last_text = ""
for _ in range(runs):
    start = time.perf_counter()
    result = model.transcribe(
        wav_path,
        language=None if lang == "auto" else lang,
        fp16=False,
        verbose=False,
    )
    times.append((time.perf_counter() - start) * 1000.0)
    last_text = (result.get("text") or "").strip()

print(
    "stt_file_benchmark|engine=python|runs={}|avg_stt_ms={:.1f}|min_stt_ms={:.1f}|max_stt_ms={:.1f}|chars={}".format(
        runs,
        statistics.mean(times),
        min(times),
        max(times),
        len(last_text),
    )
)
PY
)"

extract_metric() {
  local line="$1"
  local key="$2"
  printf '%s\n' "$line" | tr '|' '\n' | awk -F= -v key="$key" '$1 == key {print $2}'
}

RUST_AVG="$(extract_metric "$RUST_LINE" "avg_stt_ms")"
PYTHON_AVG="$(extract_metric "$PYTHON_LINE" "avg_stt_ms")"
RUST_MIN="$(extract_metric "$RUST_LINE" "min_stt_ms")"
RUST_MAX="$(extract_metric "$RUST_LINE" "max_stt_ms")"
PYTHON_MIN="$(extract_metric "$PYTHON_LINE" "min_stt_ms")"
PYTHON_MAX="$(extract_metric "$PYTHON_LINE" "max_stt_ms")"

echo ""
echo "=== STRICT STT COMPARISON (SAME WAV + SAME MODEL) ==="
echo "Rust:   avg=${RUST_AVG} ms (min=${RUST_MIN}, max=${RUST_MAX})"
echo "Python: avg=${PYTHON_AVG} ms (min=${PYTHON_MIN}, max=${PYTHON_MAX})"
echo ""
python3 - "$RUST_AVG" "$PYTHON_AVG" <<'PY'
import sys

rust = float(sys.argv[1])
python = float(sys.argv[2])

if rust <= 0 or python <= 0:
    print("Unable to compute speedup from non-positive values.")
    raise SystemExit(0)

if rust < python:
    print(f"Rust STT speedup vs Python: {python / rust:.2f}x")
    print(f"Rust STT faster by: {python - rust:.1f} ms")
elif python < rust:
    print(f"Python STT speedup vs Rust: {rust / python:.2f}x")
    print(f"Python STT faster by: {rust - python:.1f} ms")
else:
    print("Rust and Python STT times are equal.")
PY

echo ""
echo "Raw lines:"
echo "  $RUST_LINE"
echo "  $PYTHON_LINE"
