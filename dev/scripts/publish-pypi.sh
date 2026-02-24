#!/usr/bin/env bash
#
# Build and optionally publish the VoiceTerm PyPI package.
# Usage:
#   ./dev/scripts/publish-pypi.sh
#   ./dev/scripts/publish-pypi.sh --upload
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

if [[ "${VOICETERM_DEVCTL_INTERNAL:-0}" != "1" ]]; then
    if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
        echo "Usage: ./dev/scripts/publish-pypi.sh [--upload] [--yes] [--allow-ci] [--dry-run]"
        echo "Canonical: python3 dev/scripts/devctl.py pypi [--upload]"
        exit 0
    fi
    exec python3 "$REPO_ROOT/dev/scripts/devctl.py" pypi "$@"
fi

UPLOAD=0
if [[ "${1:-}" == "--upload" ]]; then
    UPLOAD=1
fi

PYPI_DIR="$REPO_ROOT/pypi"
DIST_DIR="$PYPI_DIR/dist"
CARGO_TOML="$REPO_ROOT/rust/Cargo.toml"
PYPROJECT="$PYPI_DIR/pyproject.toml"

if [[ ! -f "$PYPROJECT" ]]; then
    echo "Error: missing $PYPROJECT"
    exit 1
fi

if [[ ! -f "$CARGO_TOML" ]]; then
    echo "Error: missing $CARGO_TOML"
    exit 1
fi

CARGO_VERSION="$(grep '^version = ' "$CARGO_TOML" | head -1 | sed 's/version = "\(.*\)"/\1/')"
PYPI_VERSION="$(grep '^version = ' "$PYPROJECT" | head -1 | sed 's/version = "\(.*\)"/\1/')"

if [[ "$CARGO_VERSION" != "$PYPI_VERSION" ]]; then
    echo "Error: version mismatch"
    echo "  rust/Cargo.toml: $CARGO_VERSION"
    echo "  pypi/pyproject.toml: $PYPI_VERSION"
    exit 1
fi

INIT_PY="$PYPI_DIR/src/voiceterm/__init__.py"
if [[ -f "$INIT_PY" ]]; then
    INIT_VERSION="$(awk -F'"' '/^__version__[[:space:]]*=[[:space:]]*"/{print $2; exit}' "$INIT_PY")"
    if [[ -z "$INIT_VERSION" ]]; then
        echo "Error: missing __version__ assignment in $INIT_PY"
        exit 1
    fi
    if [[ "$INIT_VERSION" != "$PYPI_VERSION" ]]; then
        echo "Auto-syncing __init__.py version: $INIT_VERSION -> $PYPI_VERSION"
        python3 - "$INIT_PY" "$PYPI_VERSION" <<'PY'
import pathlib
import re
import sys

path = pathlib.Path(sys.argv[1])
version = sys.argv[2]
text = path.read_text(encoding="utf-8")
updated, count = re.subn(
    r'^__version__\s*=\s*"[^"]+"',
    f'__version__ = "{version}"',
    text,
    count=1,
    flags=re.MULTILINE,
)
if count != 1:
    raise SystemExit(f"Error: expected one __version__ assignment in {path}")
path.write_text(updated, encoding="utf-8")
PY
    fi
fi

echo "Building PyPI package for VoiceTerm v$PYPI_VERSION"
cd "$PYPI_DIR"
rm -rf "$DIST_DIR"

python3 -m build
python3 -m twine check dist/*

if [[ $UPLOAD -eq 1 ]]; then
    if [[ -n "${PYPI_API_TOKEN:-}" && -z "${TWINE_PASSWORD:-}" ]]; then
        export TWINE_USERNAME="${TWINE_USERNAME:-__token__}"
        export TWINE_PASSWORD="$PYPI_API_TOKEN"
    fi

    if [[ -z "${TWINE_PASSWORD:-}" && -z "${TWINE_CONFIG_FILE:-}" && ! -f "${HOME}/.pypirc" ]]; then
        echo "Error: missing PyPI credentials for non-interactive upload."
        echo "Set PYPI_API_TOKEN (recommended) or TWINE_USERNAME/TWINE_PASSWORD, or configure ~/.pypirc."
        exit 1
    fi

    echo "Uploading to PyPI (non-interactive)..."
    python3 -m twine upload --non-interactive dist/*
    echo "Upload complete."
else
    echo "Build complete. Artifacts:"
    ls -lh dist
    echo ""
    echo "To publish: ./dev/scripts/publish-pypi.sh --upload"
fi
