#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Compare Rust native STT latency vs Python fallback latency.

Usage:
  dev/scripts/tests/compare_python_rust_voice_latency.sh [--count N] [--auto-install-whisper|--no-auto-install-whisper] [--python-cmd CMD] [latency_measurement args...]

Examples:
  dev/scripts/tests/compare_python_rust_voice_latency.sh --count 3
  dev/scripts/tests/compare_python_rust_voice_latency.sh --count 3 --secs 3 --tail-ms 1500 --max-capture-ms 45000
  dev/scripts/tests/compare_python_rust_voice_latency.sh --count 2 --min-voice-total-ms 400
  dev/scripts/tests/compare_python_rust_voice_latency.sh --count 3 --voice-silence-tail-ms 1500 --voice-max-capture-ms 45000
  dev/scripts/tests/compare_python_rust_voice_latency.sh --count 3 --auto-install-whisper
  dev/scripts/tests/compare_python_rust_voice_latency.sh --count 3 --auto-install-whisper --python-cmd python

Notes:
  - This runs two real-mic measurement passes:
    1) Rust native STT
    2) Python fallback STT (--force-python-fallback)
  - Speak the same short phrase each sample for a fair comparison.
  - `Average total` includes speaking time + silence tail + STT, not STT alone.
  - If `whisper` is missing, interactive runs now prompt to auto-install it.
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
EXTRA_ARGS=()
AUTO_INSTALL_WHISPER="prompt"
PYTHON_CMD="${PYTHON_CMD:-python3}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --count)
      if [[ $# -lt 2 ]]; then
        echo "error: --count requires a value" >&2
        exit 2
      fi
      COUNT="$2"
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
      if [[ $# -lt 2 ]]; then
        echo "error: --python-cmd requires a value" >&2
        exit 2
      fi
      PYTHON_CMD="$2"
      shift 2
      ;;
    --secs)
      if [[ $# -lt 2 ]]; then
        echo "error: --secs requires a value" >&2
        exit 2
      fi
      EXTRA_ARGS+=(--seconds "$2")
      shift 2
      ;;
    --tail-ms)
      if [[ $# -lt 2 ]]; then
        echo "error: --tail-ms requires a value" >&2
        exit 2
      fi
      EXTRA_ARGS+=(--voice-silence-tail-ms "$2")
      shift 2
      ;;
    --max-capture-ms)
      if [[ $# -lt 2 ]]; then
        echo "error: --max-capture-ms requires a value" >&2
        exit 2
      fi
      EXTRA_ARGS+=(--voice-max-capture-ms "$2")
      shift 2
      ;;
    --min-speech-ms)
      if [[ $# -lt 2 ]]; then
        echo "error: --min-speech-ms requires a value" >&2
        exit 2
      fi
      EXTRA_ARGS+=(--voice-min-speech-ms-before-stt "$2")
      shift 2
      ;;
    --voice-silence-)
      echo "error: detected truncated '--voice-silence-' flag. This usually means the command wrapped onto a new line." >&2
      echo "Use one line, or use the short alias '--tail-ms <ms>' instead." >&2
      exit 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --)
      shift
      EXTRA_ARGS+=("$@")
      break
      ;;
    *)
      EXTRA_ARGS+=("$1")
      shift
      ;;
  esac
done

if ! [[ "$COUNT" =~ ^[0-9]+$ ]] || [[ "$COUNT" -lt 1 ]]; then
  echo "error: --count must be a positive integer" >&2
  exit 2
fi

cd "$WORKSPACE_ROOT"

NATIVE_OUT="/tmp/voiceterm-latency-native-$$.log"
PYTHON_OUT="/tmp/voiceterm-latency-python-$$.log"

ensure_whisper_cli() {
  if command -v whisper >/dev/null 2>&1; then
    return 0
  fi

  if [[ "$AUTO_INSTALL_WHISPER" == "prompt" ]] && [[ -t 0 ]]; then
    echo "whisper CLI not found on PATH."
    read -r -p "Install openai-whisper now using '$PYTHON_CMD'? [Y/n] " answer
    answer="${answer:-Y}"
    case "$answer" in
      [Yy]|[Yy][Ee][Ss]) AUTO_INSTALL_WHISPER="true" ;;
      *) AUTO_INSTALL_WHISPER="false" ;;
    esac
  fi

  if [[ "$AUTO_INSTALL_WHISPER" == "true" ]]; then
    if ! command -v "$PYTHON_CMD" >/dev/null 2>&1; then
      echo "error: python command '$PYTHON_CMD' not found (required for --auto-install-whisper)." >&2
      exit 2
    fi

    echo "whisper CLI not found; installing via '$PYTHON_CMD -m pip install openai-whisper'..."
    "$PYTHON_CMD" -m pip install --upgrade pip
    "$PYTHON_CMD" -m pip install openai-whisper
    if command -v pyenv >/dev/null 2>&1; then
      pyenv rehash || true
    fi
  fi

  if ! command -v whisper >/dev/null 2>&1; then
    echo "error: Python fallback requires 'whisper' on PATH." >&2
    echo "Install automatically with this script flag:" >&2
    echo "  dev/scripts/tests/compare_python_rust_voice_latency.sh --auto-install-whisper --count 3" >&2
    echo "Or install manually:" >&2
    echo "  $PYTHON_CMD -m pip install --upgrade pip" >&2
    echo "  $PYTHON_CMD -m pip install openai-whisper" >&2
    if command -v pyenv >/dev/null 2>&1; then
      echo "  pyenv rehash" >&2
    fi
    exit 2
  fi
}

extract_average_metrics() {
  local file="$1"
  python3 - "$file" <<'PY'
import pathlib
import re
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8", errors="replace")
total_matches = re.findall(r"Average total:\s*([0-9]+(?:\.[0-9]+)?)\s*ms", text)
if not total_matches:
    raise SystemExit(f"failed to parse 'Average total' from {path}")

stt_samples = []
for line in text.splitlines():
    stripped = line.strip()
    if not stripped.startswith("|"):
        continue
    cols = [c.strip() for c in stripped.strip("|").split("|")]
    if len(cols) < 8:
        continue
    if cols[0] in {"label", "-------"}:
        continue
    stt_raw = cols[2]
    if re.fullmatch(r"[0-9]+", stt_raw):
        stt_samples.append(int(stt_raw))

avg_total = float(total_matches[-1])
avg_stt = (sum(stt_samples) / len(stt_samples)) if stt_samples else 0.0
print(f"{avg_total}|{avg_stt}")
PY
}

echo "Building release latency harness..."
cargo build --quiet --release --bin latency_measurement

echo ""
echo "Run 1/2: Rust native STT path"
echo "Speak clearly for each sample. Requested samples: $COUNT"
cargo run --quiet --release --bin latency_measurement -- \
  --label rust-native \
  --count "$COUNT" \
  --voice-only \
  ${EXTRA_ARGS[@]+"${EXTRA_ARGS[@]}"} | tee "$NATIVE_OUT"

echo ""
echo "Run 2/2: Python fallback STT path"
echo "Repeat the same phrase for each sample. Requested samples: $COUNT"
ensure_whisper_cli
cargo run --quiet --release --bin latency_measurement -- \
  --label python-fallback \
  --count "$COUNT" \
  --voice-only \
  --force-python-fallback \
  ${EXTRA_ARGS[@]+"${EXTRA_ARGS[@]}"} | tee "$PYTHON_OUT"

NATIVE_METRICS="$(extract_average_metrics "$NATIVE_OUT")"
PYTHON_METRICS="$(extract_average_metrics "$PYTHON_OUT")"
NATIVE_AVG_TOTAL="${NATIVE_METRICS%%|*}"
NATIVE_AVG_STT="${NATIVE_METRICS##*|}"
PYTHON_AVG_TOTAL="${PYTHON_METRICS%%|*}"
PYTHON_AVG_STT="${PYTHON_METRICS##*|}"

echo ""
python3 - "$NATIVE_AVG_TOTAL" "$PYTHON_AVG_TOTAL" "$NATIVE_AVG_STT" "$PYTHON_AVG_STT" <<'PY'
import sys

native_total = float(sys.argv[1])
python_total = float(sys.argv[2])
native_stt = float(sys.argv[3])
python_stt = float(sys.argv[4])

print("=== COMPARISON SUMMARY ===")
print(f"Rust native average total:     {native_total:.1f} ms")
print(f"Python fallback average total: {python_total:.1f} ms")
print("")
print(f"Rust native average STT:       {native_stt:.1f} ms")
print(f"Python fallback average STT:   {python_stt:.1f} ms")
print("")
print("Note: average total includes your speaking duration and silence-tail stop time.")

if native_total <= 0 or python_total <= 0:
    print("Unable to compute speed ratio from non-positive latency values.")
    raise SystemExit(0)

if native_total < python_total:
    ratio = python_total / native_total
    improvement = ((python_total - native_total) / python_total) * 100.0
    print(f"Rust faster by: {python_total - native_total:.1f} ms")
    print(f"Rust speedup: {ratio:.2f}x vs Python")
    print(f"Latency reduction: {improvement:.1f}%")
elif python_total < native_total:
    ratio = native_total / python_total
    print(f"Python faster by: {native_total - python_total:.1f} ms")
    print(f"Python speedup: {ratio:.2f}x vs Rust")
else:
    print("Both paths reported identical average latency.")

if native_stt > 0 and python_stt > 0:
    if native_stt < python_stt:
        print("")
        print(f"STT-only speedup (Rust vs Python): {python_stt / native_stt:.2f}x")
    elif python_stt < native_stt:
        print("")
        print(f"STT-only speedup (Python vs Rust): {native_stt / python_stt:.2f}x")
    else:
        print("")
        print("STT-only speedup: equal")
PY

echo ""
echo "Raw logs:"
echo "  Rust native:   $NATIVE_OUT"
echo "  Python fallback: $PYTHON_OUT"
