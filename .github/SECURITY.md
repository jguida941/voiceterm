# Security Policy

## Reporting a Vulnerability

Please report security issues via GitHub Security Advisories (preferred). If that is not possible,
open an issue with minimal details and clearly mark it as a security concern.

**Do NOT open a public GitHub issue for security vulnerabilities.** Use the
private advisory process so we can coordinate a fix before disclosure.

We aim to acknowledge reports within 48 hours and provide an initial assessment
within 7 days.

### What to include in your report

- Description of the vulnerability
- Steps to reproduce
- Impact (what an attacker could do)
- Affected versions

## Supported Versions

| Version | Supported |
|---------|-----------|
| Latest release | Yes |
| Previous minor | Best-effort |
| Older | No |

## Severity Rating

We use CVSS (Common Vulnerability Scoring System) to rate severity from 0 to 10.
Higher scores indicate more serious vulnerabilities.

## Disclosure

We will triage reports as quickly as possible and coordinate a fix before public disclosure.

## Threat Model and Trust Boundaries

- VoiceTerm is local-first and runs backend CLIs (`codex`/`claude`) on the same machine as the user.
- Backend subprocesses inherit the invoking user's OS privileges. VoiceTerm does not sandbox them.
- The repository/workspace you run against is part of the trust boundary. Untrusted repos are high risk.
- Network/API behavior and tool execution permissions are primarily enforced by the backend CLI being used.

## Supply-Chain Policy Gate

The `Security Guard` CI lane (`.github/workflows/security_guard.yml`) installs
the locked `cargo-audit` and `cargo-deny` tools, runs `cargo audit` and
`cargo deny check` against the checked-in Rust dependency metadata, and runs
CodeQL analysis for the Python packaging and release helpers.
