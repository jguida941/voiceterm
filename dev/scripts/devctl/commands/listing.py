"""devctl list command implementation."""

import json

from ..common import emit_output, write_output
from ..time_utils import utc_timestamp

COMMANDS = [
    "check",
    "check-router",
    "mutants",
    "mutation-score",
    "docs-check",
    "hygiene",
    "publication-sync",
    "push",
    "review-channel",
    "sync",
    "integrations-sync",
    "integrations-import",
    "release",
    "release-gates",
    "ship",
    "release-notes",
    "homebrew",
    "pypi",
    "status",
    "orchestrate-status",
    "orchestrate-watch",
    "report",
    "process-cleanup",
    "process-audit",
    "process-watch",
    "guard-run",
    "compat-matrix",
    "mcp",
    "data-science",
    "quality-policy",
    "launcher-check",
    "launcher-probes",
    "launcher-policy",
    "tandem-validate",
    "render-surfaces",
    "context-graph",
    "startup-context",
    "platform-contracts",
    "doc-authority",
    "governance-draft",
    "governance-export",
    "governance-bootstrap",
    "governance-import-findings",
    "governance-quality-feedback",
    "governance-review",
    "probe-report",
    "triage",
    "triage-loop",
    "loop-packet",
    "autonomy-loop",
    "autonomy-benchmark",
    "swarm_run",
    "autonomy-report",
    "phone-status",
    "mobile-status",
    "mobile-app",
    "controller-action",
    "ralph-status",
    "autonomy-swarm",
    "mutation-loop",
    "failure-cleanup",
    "reports-cleanup",
    "audit-scaffold",
    "cihub-setup",
    "security",
    "path-audit",
    "path-rewrite",
    "list",
]

PROFILES = [
    "ci",
    "prepush",
    "release",
    "maintainer-lint",
    "pedantic",
    "quick",
    "fast",
    "ai-guard",
]


def run(args) -> int:
    """List devctl commands and profiles."""
    payload = {
        "command": "list",
        "timestamp": utc_timestamp(),
        "commands": COMMANDS,
        "profiles": PROFILES,
    }
    if args.format == "json":
        output = json.dumps(payload, indent=2)
    else:
        lines = ["# devctl list", "", "Commands:"]
        for name in COMMANDS:
            lines.append(f"- {name}")
        lines.append("")
        lines.append("Profiles:")
        for name in PROFILES:
            lines.append(f"- {name}")
        output = "\n".join(lines)
    emit_output(
        output,
        output_path=args.output,
        pipe_command=getattr(args, "pipe_command", None),
        pipe_args=getattr(args, "pipe_args", None),
        writer=write_output,
    )
    return 0
