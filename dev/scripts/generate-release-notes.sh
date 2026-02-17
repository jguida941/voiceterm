#!/usr/bin/env bash
#
# Generate markdown release notes from git diff/commit history.
# Usage:
#   ./dev/scripts/generate-release-notes.sh <version>
#   ./dev/scripts/generate-release-notes.sh <version> --output /tmp/voiceterm-v1.0.70.md
#   ./dev/scripts/generate-release-notes.sh <version> --end-ref v1.0.70 --previous-tag v1.0.69
#
set -euo pipefail

VERSION="${1:-}"
if [[ -z "$VERSION" ]]; then
    echo "Usage: $0 <version> [--output <path>] [--end-ref <ref>] [--previous-tag <tag>]"
    exit 1
fi
shift

if ! [[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "Error: version must be in format X.Y.Z"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TAG="v$VERSION"

OUTPUT=""
END_REF=""
PREVIOUS_TAG=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --output)
            OUTPUT="${2:-}"
            shift 2
            ;;
        --end-ref)
            END_REF="${2:-}"
            shift 2
            ;;
        --previous-tag)
            PREVIOUS_TAG="${2:-}"
            shift 2
            ;;
        *)
            echo "Unknown argument: $1"
            exit 1
            ;;
    esac
done

if [[ -z "$OUTPUT" ]]; then
    OUTPUT="/tmp/voiceterm-release-$TAG.md"
fi

cd "$REPO_ROOT"

if [[ -z "$END_REF" ]]; then
    if git rev-parse --verify --quiet "$TAG" >/dev/null; then
        END_REF="$TAG"
    else
        END_REF="HEAD"
    fi
fi

if ! git rev-parse --verify --quiet "$END_REF" >/dev/null; then
    echo "Error: end ref '$END_REF' not found"
    exit 1
fi

if [[ -z "$PREVIOUS_TAG" ]]; then
    while IFS= read -r candidate; do
        [[ -z "$candidate" ]] && continue
        if [[ "$candidate" != "$TAG" && "$candidate" != "$END_REF" ]]; then
            PREVIOUS_TAG="$candidate"
            break
        fi
    done < <(git tag --list 'v[0-9]*' --sort=-version:refname)
fi

DIFF_FROM=""
RANGE_LABEL=""
LOG_RANGE=""
COMPARE_HINT=""

if [[ -n "$PREVIOUS_TAG" ]]; then
    if ! git rev-parse --verify --quiet "$PREVIOUS_TAG" >/dev/null; then
        echo "Error: previous tag '$PREVIOUS_TAG' not found"
        exit 1
    fi
    DIFF_FROM="$PREVIOUS_TAG"
    RANGE_LABEL="$PREVIOUS_TAG..$END_REF"
    LOG_RANGE="$RANGE_LABEL"
    COMPARE_HINT="$PREVIOUS_TAG...$END_REF"
else
    DIFF_FROM="$(git hash-object -t tree /dev/null)"
    RANGE_LABEL="(initial)..$END_REF"
    LOG_RANGE="$END_REF"
    COMPARE_HINT=""
fi

REMOTE_URL="$(git config --get remote.origin.url || true)"
REPO_SLUG="$(echo "$REMOTE_URL" | sed -E 's#^git@github.com:##; s#^https://github.com/##; s#\.git$##')"
COMPARE_URL=""
if [[ -n "$COMPARE_HINT" && "$REPO_SLUG" == */* ]]; then
    COMPARE_URL="https://github.com/$REPO_SLUG/compare/$COMPARE_HINT"
fi

read -r FILE_COUNT INSERTIONS DELETIONS <<<"$(
    git diff --numstat "$DIFF_FROM" "$END_REF" | awk '
        BEGIN { files=0; ins=0; del=0 }
        {
            files += 1
            if ($1 ~ /^[0-9]+$/) ins += $1
            if ($2 ~ /^[0-9]+$/) del += $2
        }
        END { printf("%d %d %d\n", files, ins, del) }
    '
)"

COMMIT_COUNT="$(git rev-list --count "$LOG_RANGE")"

CHANGELOG_FILE="$REPO_ROOT/dev/CHANGELOG.md"
CHANGELOG_SECTION=""
if [[ -f "$CHANGELOG_FILE" ]]; then
    CHANGELOG_SECTION="$(
        awk -v version="$VERSION" '
            $0 ~ "^## \\[" version "\\]" { capture=1; next }
            capture && $0 ~ "^## \\[" { exit }
            capture { print }
        ' "$CHANGELOG_FILE"
    )"
fi

mkdir -p "$(dirname "$OUTPUT")"

{
    echo "# Release $TAG"
    echo ""
    echo "_Generated: $(date -u +"%Y-%m-%d %H:%M:%S UTC")_"
    echo ""
    echo "## Range"
    if [[ -n "$PREVIOUS_TAG" ]]; then
        echo "- Previous tag: \`$PREVIOUS_TAG\`"
    else
        echo "- Previous tag: _(none found)_"
    fi
    echo "- End ref: \`$END_REF\`"
    echo "- Commit range: \`$RANGE_LABEL\`"
    if [[ -n "$COMPARE_URL" ]]; then
        echo "- Compare URL: $COMPARE_URL"
    fi
    echo ""
    echo "## Diff Summary"
    echo "- Commits: $COMMIT_COUNT"
    echo "- Files changed: $FILE_COUNT"
    echo "- Insertions: +$INSERTIONS"
    echo "- Deletions: -$DELETIONS"
    echo ""
    echo "## Changelog Section"
    if [[ -n "$CHANGELOG_SECTION" ]]; then
        echo "$CHANGELOG_SECTION"
    else
        echo "_No version-matched section found in \`dev/CHANGELOG.md\`._"
    fi
    echo ""
    echo "## Commits"
    if [[ "$COMMIT_COUNT" -gt 0 ]]; then
        git log --no-merges --pretty='- `%h` %s (%an)' "$LOG_RANGE"
    else
        echo "- _(no commits in range)_"
    fi
    echo ""
    echo "## Changed Files (numstat)"
    if [[ "$FILE_COUNT" -gt 0 ]]; then
        echo "| File | + | - |"
        echo "|---|---:|---:|"
        git diff --numstat "$DIFF_FROM" "$END_REF" | while IFS=$'\t' read -r add del path; do
            add_display="$add"
            del_display="$del"
            if [[ "$add_display" == "-" ]]; then
                add_display="binary"
            fi
            if [[ "$del_display" == "-" ]]; then
                del_display="binary"
            fi
            echo "| \`$path\` | $add_display | $del_display |"
        done
    else
        echo "- _(no file changes in range)_"
    fi
    echo ""
    echo "## Raw Diffstat"
    echo '```text'
    git diff --stat "$DIFF_FROM" "$END_REF"
    echo '```'
} > "$OUTPUT"

echo "Generated release notes: $OUTPUT"
