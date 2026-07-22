# Contributing

Thanks for contributing to VoiceTerm. Bug reports, documentation fixes, tests,
and focused code changes are welcome.

## Development setup

Install the prerequisites from [the install guide](../guides/INSTALL.md), then
build and test the project:

```bash
make build
make ci
```

Useful focused commands:

```bash
make check
make test-bin
make integration
make parser-fuzz
python3 -m unittest discover -s pypi/tests
```

## Changes

- Keep changes focused and add or update tests for behavior changes.
- Run `cargo fmt`; CI treats Clippy warnings as errors.
- Update `CHANGELOG.md` for user-facing fixes and features.
- Update screenshots, controls tables, and guides when the UI or CLI changes.
- Use imperative commit subjects such as `Fix Cursor overlay redraw`.

## Pull requests

Explain the problem, the approach, and the verification you ran. Include the
terminal host and wrapped backend for terminal-specific changes (for example,
Cursor + Codex or JetBrains + Claude).

Be respectful and constructive. See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
and [SECURITY.md](SECURITY.md).
