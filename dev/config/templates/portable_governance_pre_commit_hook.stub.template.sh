#!/usr/bin/env bash
set -euo pipefail

# Generated starter hook for the {{repo_pack_id}} repo-pack.
python3 dev/scripts/devctl.py check --profile ci
python3 dev/scripts/devctl.py docs-check --strict-tooling
