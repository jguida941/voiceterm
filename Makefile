# VoiceTerm Developer Makefile
# Run `make help` to see available commands

.PHONY: help build run doctor fmt fmt-check lint check test test-bin test-perf test-mem test-mem-loop parser-fuzz security-audit bench ci prepush mutants mutants-all mutants-audio mutants-config mutants-voice mutants-pty mutants-results mutants-raw dev-check dev-ci dev-prepush dev-mutants dev-mutants-results dev-mutation-score dev-docs-check dev-hygiene dev-list dev-status dev-report release release-notes homebrew pypi ship model-base model-small model-tiny clean clean-tests

# Default target
help:
	@echo "VoiceTerm Developer Commands"
	@echo ""
	@echo "Building:"
	@echo "  make build        Build release binary"
	@echo "  make run          Build and run voiceterm"
	@echo "  make doctor       Run voiceterm --doctor diagnostics"
	@echo ""
	@echo "Code Quality:"
	@echo "  make fmt          Format code"
	@echo "  make lint         Run clippy linter"
	@echo "  make test         Run all tests"
	@echo "  make check        Format + lint (no tests)"
	@echo ""
	@echo "CI / Pre-push:"
	@echo "  make ci           Core CI check (fmt + lint + test)"
	@echo "  make prepush      All push/PR checks (ci + perf + memory guard)"
	@echo "  make security-audit RustSec policy check (high/critical + yanked/unsound)"
	@echo ""
	@echo "Mutation Testing:"
	@echo "  make mutants           Interactive module selection"
	@echo "  make mutants-all       Test all modules (slow)"
	@echo "  make mutants-audio     Test audio module only"
	@echo "  make mutants-results   Show last results"
	@echo ""
	@echo "Dev CLI:"
	@echo "  make dev-check         Run devctl check"
	@echo "  make dev-ci            Run devctl check --ci"
	@echo "  make dev-prepush       Run devctl check --prepush"
	@echo "  make dev-mutants       Run devctl mutants"
	@echo "  make dev-mutants-results Show devctl mutants results"
	@echo "  make dev-mutation-score  Run devctl mutation-score"
	@echo "  make dev-docs-check    Run devctl docs-check --user-facing"
	@echo "  make dev-hygiene      Run devctl hygiene audit"
	@echo "  make dev-list          List devctl commands/profiles"
	@echo "  make dev-status        Run devctl status"
	@echo "  make dev-report        Run devctl report"
	@echo ""
	@echo "Testing:"
	@echo "  make test-bin     Test overlay binary only"
	@echo "  make test-perf    Run perf smoke test + metrics verification"
	@echo "  make test-mem     Run memory guard test once"
	@echo "  make test-mem-loop Run memory guard loop (CI parity)"
	@echo "  make parser-fuzz  Run parser property-fuzz tests"
	@echo "  make bench        Run voice benchmark"
	@echo ""
	@echo "Release:"
	@echo "  make release V=X.Y.Z   Create/push release tag + notes via devctl"
	@echo "  make release-notes V=X.Y.Z  Generate release notes markdown via devctl"
	@echo "  make homebrew V=X.Y.Z  Update Homebrew formula via devctl"
	@echo "  make pypi               Build/check PyPI package via devctl"
	@echo "  make ship V=X.Y.Z      Full release control-plane flow via devctl ship"
	@echo ""
	@echo "Models:"
	@echo "  make model-base   Download base.en model (recommended)"
	@echo "  make model-small  Download small.en model"
	@echo "  make model-tiny   Download tiny.en model (fastest)"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean        Remove build artifacts"
	@echo ""

# =============================================================================
# Building
# =============================================================================

build:
	cd src && cargo build --release --bin voiceterm

run: build
	./src/target/release/voiceterm

doctor: build
	./src/target/release/voiceterm --doctor

# =============================================================================
# Code Quality
# =============================================================================

fmt:
	cd src && cargo fmt --all

fmt-check:
	cd src && cargo fmt --all -- --check

lint:
	cd src && cargo clippy --workspace --all-features -- -D warnings

check: fmt-check lint

# =============================================================================
# Testing
# =============================================================================

test:
	cd src && cargo test --workspace --all-features

test-bin:
	cd src && cargo test --bin voiceterm

test-perf:
	cd src && cargo test --no-default-features legacy_tui::tests::perf_smoke_emits_voice_metrics -- --nocapture
	@LOG_PATH=$$(python3 -c "import os, tempfile; print(os.path.join(tempfile.gettempdir(), 'voiceterm_tui.log'))"); \
	echo "Inspecting $$LOG_PATH"; \
	if ! grep -q "voice_metrics|" "$$LOG_PATH"; then \
		echo "voice_metrics log missing from log" >&2; \
		exit 1; \
	fi; \
	python3 .github/scripts/verify_perf_metrics.py "$$LOG_PATH"

test-mem:
	cd src && cargo test --no-default-features legacy_tui::tests::memory_guard_backend_threads_drop -- --nocapture

test-mem-loop:
	@set -eu; \
	cd src; \
	for i in $$(seq 1 20); do \
		echo "Iteration $$i"; \
		cargo test --no-default-features legacy_tui::tests::memory_guard_backend_threads_drop -- --nocapture; \
	done

parser-fuzz:
	cd src && cargo test pty_session::tests::prop_find_csi_sequence_respects_bounds -- --nocapture
	cd src && cargo test pty_session::tests::prop_find_osc_terminator_respects_bounds -- --nocapture
	cd src && cargo test pty_session::tests::prop_split_incomplete_escape_preserves_original_bytes -- --nocapture

security-audit:
	cargo install cargo-audit --locked
	cd src && (cargo audit --json > ../rustsec-audit.json || true)
	python3 dev/scripts/check_rustsec_policy.py --input rustsec-audit.json --min-cvss 7.0 --fail-on-kind yanked --fail-on-kind unsound --allowlist-file dev/security/rustsec_allowlist.md

# Voice benchmark
bench:
	./dev/scripts/tests/benchmark_voice.sh

# Full CI check (matches GitHub Actions)
ci: fmt-check lint test
	@echo ""
	@echo "✓ CI checks passed!"

# Run all push/PR checks locally (rust_ci + perf_smoke + memory_guard)
prepush: ci test-perf test-mem-loop
	@echo ""
	@echo "✓ Pre-push checks passed!"

# =============================================================================
# Mutation Testing
# =============================================================================

# Interactive module selection
mutants:
	python3 dev/scripts/mutants.py

# Test all modules (slow)
mutants-all:
	python3 dev/scripts/mutants.py --all

# Test specific modules
mutants-audio:
	python3 dev/scripts/mutants.py --module audio

mutants-config:
	python3 dev/scripts/mutants.py --module config

mutants-voice:
	python3 dev/scripts/mutants.py --module voice

mutants-pty:
	python3 dev/scripts/mutants.py --module pty

# Show last mutation test results
mutants-results:
	python3 dev/scripts/mutants.py --results-only

# Legacy: run cargo mutants directly
mutants-raw:
	cd src && cargo mutants --timeout 300 -o mutants.out
	python3 dev/scripts/check_mutation_score.py --path src/mutants.out/outcomes.json --threshold 0.80

# =============================================================================
# Dev CLI (devctl)
# =============================================================================

dev-check:
	python3 dev/scripts/devctl.py check

dev-ci:
	python3 dev/scripts/devctl.py check --ci

dev-prepush:
	python3 dev/scripts/devctl.py check --prepush

dev-mutants:
	python3 dev/scripts/devctl.py mutants

dev-mutants-results:
	python3 dev/scripts/devctl.py mutants --results-only

dev-mutation-score:
	python3 dev/scripts/devctl.py mutation-score

dev-docs-check:
	python3 dev/scripts/devctl.py docs-check --user-facing

dev-hygiene:
	python3 dev/scripts/devctl.py hygiene --format md

dev-list:
	python3 dev/scripts/devctl.py list

dev-status:
	python3 dev/scripts/devctl.py status --format md

dev-report:
	python3 dev/scripts/devctl.py report --format md

# =============================================================================
# Release
# =============================================================================

# Usage: make release V=X.Y.Z
release:
ifndef V
	$(error Version required. Usage: make release V=X.Y.Z)
endif
	python3 dev/scripts/devctl.py release --version $(V)

# Usage: make release-notes V=X.Y.Z
release-notes:
ifndef V
	$(error Version required. Usage: make release-notes V=X.Y.Z)
endif
	python3 dev/scripts/devctl.py release-notes --version $(V)

# Usage: make homebrew V=X.Y.Z
homebrew:
ifndef V
	$(error Version required. Usage: make homebrew V=X.Y.Z)
endif
	python3 dev/scripts/devctl.py homebrew --version $(V)

pypi:
	python3 dev/scripts/devctl.py pypi

# Usage: make ship V=X.Y.Z
ship:
ifndef V
	$(error Version required. Usage: make ship V=X.Y.Z)
endif
	python3 dev/scripts/devctl.py ship --version $(V) --verify --tag --notes --github --pypi --homebrew --verify-pypi

# =============================================================================
# Model Management
# =============================================================================

model-base:
	./scripts/setup.sh models --base

model-small:
	./scripts/setup.sh models --small

model-tiny:
	./scripts/setup.sh models --tiny

# =============================================================================
# Cleanup
# =============================================================================

clean:
	cd src && cargo clean
	rm -rf src/mutants.out

# Remove test scripts clutter
clean-tests:
	@echo "Removing one-off test scripts..."
	find dev/scripts/tests -maxdepth 1 -type f \
		! -name 'benchmark_voice.sh' \
		! -name 'integration_test.sh' \
		! -name 'measure_latency.sh' \
		-exec rm -f {} +
	@echo "Done. Kept: benchmark_voice.sh, measure_latency.sh, integration_test.sh"
