# Scripts

## User Scripts

Scripts for end users.

| Script | Purpose | Usage |
|--------|---------|-------|
| `setup.sh` | Download Whisper models and setup | `./scripts/setup.sh models --base` |
| `voxterm.py` | Python fallback STT pipeline | Used automatically when native Whisper fails |

### setup.sh

Downloads Whisper models and performs initial setup.

```bash
# Download base English model (recommended)
./scripts/setup.sh models --base

# Download small model (default, larger)
./scripts/setup.sh models --small

# Show help
./scripts/setup.sh --help
```

### voxterm.py

Python fallback pipeline for speech-to-text. Used automatically when:
- Native Whisper model is not available
- Audio device issues occur

Requires: `python3`, `ffmpeg`, `whisper` CLI on PATH.

---

## Developer Scripts

Scripts in `scripts/dev/` are for development and releases.

| Script | Purpose | Usage |
|--------|---------|-------|
| `dev/release.sh` | Create GitHub release tag | `./scripts/dev/release.sh 1.0.33` |
| `dev/update-homebrew.sh` | Update Homebrew tap formula | `./scripts/dev/update-homebrew.sh 1.0.33` |
| `dev/check_mutation_score.py` | Verify mutation test score | Used by CI |
| `dev/tests/` | Test scripts and fixtures | Used by CI and local testing |

### dev/release.sh

Creates a Git tag for a new release. Validates version format and checks for uncommitted changes.

```bash
# Create release v1.0.33
./scripts/dev/release.sh 1.0.33
```

**Prerequisites:**
- Must be on `master` branch
- No uncommitted changes
- `rust_tui/Cargo.toml` version must match
- `docs/CHANGELOG.md` should have entry for version

### dev/update-homebrew.sh

Updates the Homebrew tap with new version and SHA256.

```bash
# Update tap to v1.0.33
./scripts/dev/update-homebrew.sh 1.0.33
```

**Prerequisites:**
- Release tag must exist on GitHub
- Homebrew repo must be cloned (default: `~/testing_upgrade/homebrew-voxterm`)
- Set `HOMEBREW_VOXTERM_PATH` to override location

### dev/check_mutation_score.py

Parses mutation testing results and checks against threshold.

```bash
# Check mutation score (used by CI)
python3 scripts/dev/check_mutation_score.py --path mutants.out/outcomes.json --threshold 0.80
```

### dev/tests/

Test scripts and fixtures used by CI workflows and local testing.

---

## Release Workflow

Full release process:

```bash
# 1. Update version in rust_tui/Cargo.toml
# 2. Update docs/CHANGELOG.md
# 3. Commit all changes
git add -A && git commit -m "Release v1.0.33"

# 4. Create GitHub tag
./scripts/dev/release.sh 1.0.33

# 5. Create GitHub release
gh release create v1.0.33 --title "v1.0.33" --notes "See CHANGELOG.md"

# 6. Update Homebrew tap
./scripts/dev/update-homebrew.sh 1.0.33

# 7. Verify
brew update && brew upgrade voxterm
voxterm --version
```
