# VoiceTerm developer commands. Run `make help` for the short command list.

.PHONY: help build run doctor fmt fmt-check lint check test test-bin test-perf test-mem parser-fuzz bench integration ci prepush security pypi release-check release-notes release homebrew model-base model-small model-tiny clean

ifeq ($(shell uname),Darwin)
ifneq ($(wildcard /Library/Developer/CommandLineTools/usr/lib/libclang.dylib),)
export LIBCLANG_PATH ?= /Library/Developer/CommandLineTools/usr/lib
endif
endif

help:
	@echo "VoiceTerm commands"
	@echo "  make build                 Build the optimized binary"
	@echo "  make run                   Build and run VoiceTerm"
	@echo "  make doctor                Run environment diagnostics"
	@echo "  make check                 Run rustfmt and Clippy"
	@echo "  make test                  Run the complete Rust test suite"
	@echo "  make ci                    Run formatting, linting, and tests"
	@echo "  make prepush               Run CI plus runtime smoke tests"
	@echo "  make pypi                  Build and validate PyPI artifacts"
	@echo "  make release-check V=X.Y.Z Verify release version and notes"
	@echo "  make release V=X.Y.Z       Publish a GitHub release"
	@echo "  make homebrew V=X.Y.Z TAP=/path/to/tap"

build:
	cd rust && cargo build --release --bin voiceterm

run: build
	./scripts/start.sh

doctor: build
	./rust/target/release/voiceterm --doctor

fmt:
	cd rust && cargo fmt --all

fmt-check:
	cd rust && cargo fmt --all -- --check

lint:
	cd rust && cargo clippy --workspace --all-targets --all-features -- -D warnings

check: fmt-check lint

test:
	cd rust && cargo test --workspace --all-features

test-bin:
	cd rust && cargo test --bin voiceterm

test-perf:
	@LOG_PATH=$$(python3 -c "import os,tempfile; print(os.path.join(tempfile.gettempdir(), 'voiceterm_perf_test.log'))"); \
	rm -f "$$LOG_PATH"; \
	(cd rust && VOICETERM_LOG_PATH="$$LOG_PATH" cargo test --no-default-features runtime_support::tests::perf_smoke_emits_voice_metrics -- --nocapture); \
	python3 .github/scripts/verify_perf_metrics.py "$$LOG_PATH"; \
	rm -f "$$LOG_PATH"

test-mem:
	cd rust && cargo test --no-default-features agent_runtime::tests::backend_threads_return_to_baseline -- --nocapture

parser-fuzz:
	cd rust && cargo test pty_session::tests::prop_find_csi_sequence_respects_bounds -- --nocapture
	cd rust && cargo test pty_session::tests::prop_find_osc_terminator_respects_bounds -- --nocapture
	cd rust && cargo test pty_session::tests::prop_split_incomplete_escape_preserves_original_bytes -- --nocapture

bench:
	./scripts/tests/benchmark_voice.sh

integration: build
	./scripts/tests/integration_test.sh

ci: fmt-check lint test

prepush: ci test-perf test-mem parser-fuzz

security:
	cd rust && cargo audit
	cd rust && cargo deny check

pypi:
	python3 -m build pypi
	python3 -m twine check pypi/dist/*

release-check:
ifndef V
	$(error Version required. Usage: make release-check V=X.Y.Z)
endif
	python3 scripts/release/check_version.py --expected $(V)
	python3 scripts/release/release_notes.py $(V) >/dev/null

release-notes:
ifndef V
	$(error Version required. Usage: make release-notes V=X.Y.Z)
endif
	python3 scripts/release/release_notes.py $(V)

release: release-check
	@NOTES=$$(mktemp); \
	python3 scripts/release/release_notes.py $(V) >"$$NOTES"; \
	gh release create v$(V) --target master --title "VoiceTerm v$(V)" --notes-file "$$NOTES"; \
	rm -f "$$NOTES"

homebrew:
ifndef V
	$(error Version required. Usage: make homebrew V=X.Y.Z TAP=/path/to/homebrew-voiceterm)
endif
ifndef TAP
	$(error Tap path required. Usage: make homebrew V=X.Y.Z TAP=/path/to/homebrew-voiceterm)
endif
	python3 scripts/release/update_homebrew.py --version $(V) --formula "$(TAP)/Formula/voiceterm.rb" --readme "$(TAP)/README.md"

model-base:
	./scripts/setup.sh models --base

model-small:
	./scripts/setup.sh models --small

model-tiny:
	./scripts/setup.sh models --tiny

clean:
	cd rust && cargo clean
