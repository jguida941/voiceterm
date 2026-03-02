#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
if [[ -d "$REPO_ROOT/rust" ]]; then
  WORKSPACE_ROOT="$REPO_ROOT/rust"
elif [[ -d "$REPO_ROOT/src" ]]; then
  WORKSPACE_ROOT="$REPO_ROOT/src"
else
  echo "error: unable to locate Rust workspace (expected rust/ or src/)" >&2
  exit 2
fi
pushd "$WORKSPACE_ROOT" >/dev/null

CLIPS=(
  "short:1000:700"
  "medium:3000:700"
  "long:8000:700"
)

echo "| clip | capture_ms | speech_ms | silence_tail_ms | frames_processed | early_stop |"
echo "| --- | --- | --- | --- | --- | --- |"

for spec in "${CLIPS[@]}"; do
  IFS=":" read -r label speech silence <<<"$spec"
  raw=$(cargo run --quiet --release --bin voice_benchmark -- \
    --label "$label" \
    --speech-ms "$speech" \
    --silence-ms "$silence")

  parsed=$(python3 - "$raw" <<'PY'
import sys

line = sys.argv[1]
parts = {}
for chunk in line.split("|"):
    if "=" in chunk:
        key, value = chunk.split("=", 1)
        parts[key.strip()] = value.strip()

required = [
    "label",
    "capture_ms",
    "speech_ms",
    "silence_tail_ms",
    "frames_processed",
    "early_stop",
]

missing = [key for key in required if key not in parts]
if missing:
    raise SystemExit(f"missing metrics {missing} in line: {line}")

print(
    f"| {parts['label']} | {parts['capture_ms']} | {parts['speech_ms']} | "
    f"{parts['silence_tail_ms']} | {parts['frames_processed']} | {parts['early_stop']} |"
)
PY
)

  echo "$parsed"
done

popd >/dev/null
