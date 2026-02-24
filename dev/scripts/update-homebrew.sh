#!/usr/bin/env bash
#
# Update Homebrew tap for VoiceTerm
# Usage: ./dev/scripts/update-homebrew.sh <version>
# Example: ./dev/scripts/update-homebrew.sh X.Y.Z
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

if [[ "${VOICETERM_DEVCTL_INTERNAL:-0}" != "1" ]]; then
    VERSION="${1:-}"
    if [[ "$VERSION" == "--help" || "$VERSION" == "-h" ]]; then
        echo "Usage: ./dev/scripts/update-homebrew.sh <version> [--yes] [--allow-ci] [--dry-run]"
        echo "Canonical: python3 dev/scripts/devctl.py homebrew --version <version>"
        exit 0
    fi
    if [[ -z "$VERSION" ]]; then
        echo "Usage: ./dev/scripts/update-homebrew.sh <version> [--yes] [--allow-ci] [--dry-run]"
        echo "Canonical: python3 dev/scripts/devctl.py homebrew --version <version>"
        exit 1
    fi
    shift || true
    exec python3 "$REPO_ROOT/dev/scripts/devctl.py" homebrew --version "$VERSION" "$@"
fi

VERSION="${1:-}"
if [[ -z "$VERSION" ]]; then
    echo "Usage: $0 <version>"
    echo "Example: $0 X.Y.Z"
    exit 1
fi

TAG="v$VERSION"
HOMEBREW_TAP_BRANCH="${HOMEBREW_TAP_BRANCH:-main}"
FORMULA_DESC="Voice-first terminal overlay for Codex and Claude with local Whisper STT"
TMP_TARBALL=""

cleanup_tmp_tarball() {
    if [[ -n "$TMP_TARBALL" && -f "$TMP_TARBALL" ]]; then
        rm -f "$TMP_TARBALL"
    fi
}

trap cleanup_tmp_tarball EXIT

# Portable in-place sed (BSD/macOS and GNU/Linux).
sedi() {
    local expression="$1"
    local file="$2"
    if [[ "$(uname -s)" == "Darwin" ]]; then
        sed -i '' "$expression" "$file"
    else
        sed -i "$expression" "$file"
    fi
}

# Resolve the tap repo path (env override -> brew repo -> fallback path).
resolve_homebrew_repo() {
    if [[ -n "${HOMEBREW_VOICETERM_PATH:-}" ]]; then
        echo "$HOMEBREW_VOICETERM_PATH"
        return 0
    fi

    if command -v brew >/dev/null 2>&1; then
        local repo
        repo="$(brew --repo jguida941/voiceterm 2>/dev/null || true)"
        if [[ -n "$repo" && -d "$repo" ]]; then
            echo "$repo"
            return 0
        fi

        repo="$(brew --repo jguida941/homebrew-voiceterm 2>/dev/null || true)"
        if [[ -n "$repo" && -d "$repo" ]]; then
            echo "$repo"
            return 0
        fi
    fi

    # Last-resort fallback for local dev setups.
    echo "$HOME/testing_upgrade/homebrew-voiceterm"
}

HOMEBREW_REPO="$(resolve_homebrew_repo)"
FORMULA="$HOMEBREW_REPO/Formula/voiceterm.rb"
README="$HOMEBREW_REPO/README.md"

echo "=== Updating Homebrew tap for $TAG ==="

# Check Homebrew repo exists
if [[ ! -d "$HOMEBREW_REPO" ]]; then
    echo "Error: Homebrew repo not found at $HOMEBREW_REPO"
    echo "Set HOMEBREW_VOICETERM_PATH or clone the repo first."
    exit 1
fi

# Get SHA256 of release tarball
TARBALL_URL="https://github.com/jguida941/voiceterm/archive/refs/tags/$TAG.tar.gz"
echo "Fetching SHA256 for $TARBALL_URL..."
TMP_TARBALL="$(mktemp "${TMPDIR:-/tmp}/voiceterm-homebrew-${VERSION}-XXXXXX.tar.gz")"
curl -fsSL \
    --retry 5 \
    --retry-delay 2 \
    --retry-connrefused \
    "$TARBALL_URL" \
    -o "$TMP_TARBALL"

if ! tar -tzf "$TMP_TARBALL" >/dev/null 2>&1; then
    echo "Error: downloaded tarball is invalid for $TAG"
    exit 1
fi

SHA256=$(shasum -a 256 "$TMP_TARBALL" | awk '{print $1}')

if [[ -z "$SHA256" || "$SHA256" == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855" ]]; then
    echo "Error: Failed to get SHA256 (empty tarball or tag doesn't exist)"
    echo "Make sure tag $TAG exists on GitHub."
    exit 1
fi

echo "SHA256: $SHA256"

# Update formula (URL, version, checksum).
echo "Updating $FORMULA..."
cd "$HOMEBREW_REPO"

# Update version
sedi "s|url \"https://github.com/jguida941/voiceterm/archive/refs/tags/v[0-9.]*\.tar\.gz\"|url \"$TARBALL_URL\"|" "$FORMULA"
sedi "s|version \"[0-9.]*\"|version \"$VERSION\"|" "$FORMULA"
sedi "s|sha256 \"[a-f0-9]*\"|sha256 \"$SHA256\"|" "$FORMULA"
if grep -q '^[[:space:]]*desc "' "$FORMULA"; then
    sedi "s|^[[:space:]]*desc \".*\"|  desc \"$FORMULA_DESC\"|" "$FORMULA"
else
    echo "Warning: Formula desc line not found; skipping desc sync."
fi

# Keep tap README intentionally minimal and canonical.
# The main repo hosts full docs; the tap repo should only cover brew-specific entrypoints.
if [[ -f "$README" ]]; then
    cat > "$README" <<EOF
# homebrew-voiceterm

Homebrew tap for [VoiceTerm](https://github.com/jguida941/voiceterm).
Voice-first terminal overlay for Codex and Claude with local Whisper STT.

This repository only contains Homebrew formula and release metadata.
For full product docs, use the main VoiceTerm repository.

## Documentation

| Topic | Link |
|---|---|
| Main repo | https://github.com/jguida941/voiceterm |
| Install guide | https://github.com/jguida941/voiceterm/blob/master/guides/INSTALL.md |
| Usage guide | https://github.com/jguida941/voiceterm/blob/master/guides/USAGE.md |
| CLI flags | https://github.com/jguida941/voiceterm/blob/master/guides/CLI_FLAGS.md |
| Troubleshooting | https://github.com/jguida941/voiceterm/blob/master/guides/TROUBLESHOOTING.md |
| Changelog | https://github.com/jguida941/voiceterm/blob/master/dev/CHANGELOG.md |

## Install

\`\`\`bash
brew tap jguida941/voiceterm
brew install voiceterm
\`\`\`

## Upgrade

\`\`\`bash
brew update
brew upgrade voiceterm
\`\`\`

## Version

Current: v$VERSION
EOF
fi

# Show diff
echo ""
echo "Changes:"
if [[ -f "$README" ]]; then
    git diff "$FORMULA" "$README"
else
    git diff "$FORMULA"
fi
echo ""

if [[ -f "$README" ]]; then
    git diff --quiet "$FORMULA" "$README" && {
        echo "No changes needed. Formula is already up to date."
        exit 0
    }
else
    git diff --quiet "$FORMULA" && {
        echo "No changes needed. Formula is already up to date."
        exit 0
    }
fi

# Commit and push
ASSUME_YES="${VOICETERM_DEVCTL_ASSUME_YES:-0}"
if [[ "$ASSUME_YES" == "1" ]]; then
    REPLY="y"
    echo "Commit and push these changes? (y/n) y"
else
    read -p "Commit and push these changes? (y/n) " -n 1 -r
    echo
fi

if [[ $REPLY =~ ^[Yy]$ ]]; then
    if ! git config user.name >/dev/null; then
        git config user.name "${HOMEBREW_GIT_USER_NAME:-github-actions[bot]}"
    fi
    if ! git config user.email >/dev/null; then
        git config user.email "${HOMEBREW_GIT_USER_EMAIL:-41898282+github-actions[bot]@users.noreply.github.com}"
    fi

    if [[ -f "$README" ]]; then
        git add "$FORMULA" "$README"
    else
        git add "$FORMULA"
    fi
    git commit -m "Update to v$VERSION"
    git push origin "$HOMEBREW_TAP_BRANCH"
    echo ""
    echo "=== Homebrew tap updated ==="
    echo "Users can now run: brew update && brew upgrade voiceterm"
else
    echo "Changes not committed. Run manually:"
    echo "  cd $HOMEBREW_REPO"
    echo "  git add Formula/voiceterm.rb"
    echo "  git commit -m 'Update to v$VERSION'"
    echo "  git push origin $HOMEBREW_TAP_BRANCH"
fi
