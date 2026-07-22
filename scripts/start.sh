#!/bin/bash
#
# VoiceTerm - Quick Start
# Double-click this file or run: ./scripts/start.sh (from repo root)
#

# Detect platform
OS="$(uname -s)"
case "$OS" in
    Darwin) PLATFORM="macos" ;;
    Linux)  PLATFORM="linux" ;;
    MINGW*|MSYS*|CYGWIN*) PLATFORM="windows" ;;
    *)      PLATFORM="unknown" ;;
esac

if [ "$PLATFORM" = "windows" ]; then
    echo "Windows is not yet supported. Try WSL2 with Linux instructions."
    exit 1
fi

# Save the user's current directory so voiceterm works on their project
VOICETERM_CWD="$(pwd)"
export VOICETERM_CWD

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT_DIR_REAL="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P 2>/dev/null || true)"
if [ -z "$SCRIPT_DIR_REAL" ]; then
    SCRIPT_DIR_REAL="$SCRIPT_DIR"
fi
cd "$SCRIPT_DIR" || exit 1

# Colors used by startup diagnostics
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

if [ -n "${NO_COLOR:-}" ]; then
    YELLOW=''
    RED=''
    NC=''
fi

# Minimal startup - Rust binary shows the full banner
echo ""

# Startup output-only mode for tests
if [ "${VOICETERM_STARTUP_ONLY:-0}" = "1" ]; then
    exit 0
fi

# Resolve binary (prefer local build; avoid wrapper recursion)
OVERLAY_BIN=""
if [ -x "$SCRIPT_DIR/rust/target/release/voiceterm" ]; then
    OVERLAY_BIN="$SCRIPT_DIR/rust/target/release/voiceterm"
fi

# Check if Rust overlay exists
if [ -z "$OVERLAY_BIN" ]; then
    echo -e "${YELLOW}Building VoiceTerm (first time setup)...${NC}"
    if ! (cd rust && cargo build --release --bin voiceterm); then
        echo -e "${RED}Build failed. Please check the error above.${NC}"
        exit 1
    fi
    OVERLAY_BIN="$SCRIPT_DIR/rust/target/release/voiceterm"
fi

# Check if whisper model exists
MODEL_PATH=""
DEFAULT_MODELS_DIR="$SCRIPT_DIR/whisper_models"
FALLBACK_MODELS_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/voiceterm/models"
MODEL_DIR=""

IS_HOMEBREW=0
case "$SCRIPT_DIR_REAL" in
    /opt/homebrew/Cellar/*|/usr/local/Cellar/*|/home/linuxbrew/.linuxbrew/Cellar/*|/opt/homebrew/opt/*|/usr/local/opt/*|/home/linuxbrew/.linuxbrew/opt/*)
        IS_HOMEBREW=1
        ;;
esac

if [ -n "${VOICETERM_MODEL_DIR:-}" ]; then
    MODEL_DIR="$VOICETERM_MODEL_DIR"
elif [ "$IS_HOMEBREW" -eq 1 ]; then
    MODEL_DIR="$FALLBACK_MODELS_DIR"
else
    if mkdir -p "$DEFAULT_MODELS_DIR" 2>/dev/null && [ -w "$DEFAULT_MODELS_DIR" ]; then
        MODEL_DIR="$DEFAULT_MODELS_DIR"
    else
        MODEL_DIR="$FALLBACK_MODELS_DIR"
    fi
fi

HAS_WHISPER_ARG=0
for arg in "$@"; do
    case "$arg" in
        --whisper-model-path|--whisper-model-path=*)
            HAS_WHISPER_ARG=1
            ;;
    esac
done

find_model() {
    local search_dir="$1"
    for candidate in \
        "ggml-small.en.bin" \
        "ggml-small.bin" \
        "ggml-base.en.bin" \
        "ggml-base.bin" \
        "ggml-tiny.en.bin" \
        "ggml-tiny.bin"; do
        if [ -f "$search_dir/$candidate" ]; then
            echo "$search_dir/$candidate"
            return 0
        fi
    done
    return 1
}

MODEL_PATH="$(find_model "$DEFAULT_MODELS_DIR" || true)"
if [ -z "$MODEL_PATH" ] && [ "$MODEL_DIR" != "$DEFAULT_MODELS_DIR" ]; then
    MODEL_PATH="$(find_model "$MODEL_DIR" || true)"
fi
if [ -z "$MODEL_PATH" ]; then
    echo -e "${YELLOW}Downloading Whisper model (first time setup)...${NC}"
    if ! VOICETERM_MODEL_DIR="$MODEL_DIR" ./scripts/setup.sh models --base; then
        echo -e "${RED}Model download failed. Please check the error above.${NC}"
        exit 1
    fi
    MODEL_PATH="$(find_model "$MODEL_DIR" || true)"
fi

if [ -z "$MODEL_PATH" ]; then
    echo -e "${RED}Whisper model not found. Run: ./scripts/setup.sh models --base${NC}"
    exit 1
fi
MODEL_PATH_ABS="$MODEL_PATH"

if [ -z "$OVERLAY_BIN" ]; then
    echo -e "${RED}Overlay binary not found. Please run ./scripts/install.sh or build src.${NC}"
    exit 1
fi
EXTRA_ARGS=()
if [ $HAS_WHISPER_ARG -eq 0 ]; then
    EXTRA_ARGS+=(--whisper-model-path "$MODEL_PATH_ABS")
fi
"$OVERLAY_BIN" "${EXTRA_ARGS[@]}" "$@"
