# Security Policy

## Reporting a Vulnerability

Please report security issues via GitHub Security Advisories (preferred). If that is not possible,
open an issue with minimal details and clearly mark it as a security concern.

## Supported Versions

Only the latest release is supported.

## Disclosure

We will triage reports as quickly as possible and coordinate a fix before public disclosure.

## Threat Model and Trust Boundaries

- VoiceTerm is local-first and runs backend CLIs (`codex`/`claude`) on the same machine as the user.
- Backend subprocesses inherit the invoking user's OS privileges. VoiceTerm does not sandbox them.
- The repository/workspace you run against is part of the trust boundary. Untrusted repos are high risk.
- Network/API behavior and tool execution permissions are primarily enforced by the backend CLI being used.

## Risky Runtime Flags

### `--claude-skip-permissions`

This flag maps to Claude's `--dangerously-skip-permissions` in IPC mode.

- Default is **off**.
- Enabling it removes Claude's permission confirmation prompts.
- Use only in isolated/trusted environments (for example disposable containers/sandboxes).
- Do **not** use against untrusted repositories or with credentials/secrets available in the environment.

## Supply-Chain Policy Gate

The `Security Guard` CI lane (`.github/workflows/security_guard.yml`) enforces RustSec policy by:

- failing on high/critical advisories (CVSS >= 7.0),
- failing on `yanked` and `unsound` warning kinds,
- using a temporary exception list in `dev/security/rustsec_allowlist.md` for known transitive blockers,
- publishing the audit report as a workflow artifact for review.
