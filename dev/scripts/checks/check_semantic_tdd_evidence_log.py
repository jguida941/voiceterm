#!/usr/bin/env python3
"""Warn when semantic-TDD canonical surfaces change without an evidence.md entry.

Forcing function so the per-slice receipt discipline doesn't decay over
time. Runs fail-OPEN by default: never blocks a commit, but emits a
visible warning when a slice ships without a new case in `evidence.md`.

Trigger surfaces (matching either substring or directory):
  - dev/scripts/devctl/tests/scenarios/test_live_state_invariants.py
  - dev/scripts/devctl/runtime/semantic_tdd_role.py
  - dev/scripts/devctl/runtime/role_profile.py
  - any production file whose path contains `topology` or `reviewer_mode`
    or `authority_snapshot` under `dev/scripts/devctl/`
  - any test under `dev/scripts/devctl/tests/scenarios/` whose name
    starts with `test_topology_` or `test_role_` or `test_reviewer_`

If any of those changed in the staged diff (or in the most recent
commit, when run post-commit), the guard checks:
  1. `evidence.md` was also staged/touched in the same window.
  2. The number of `## Case <N>` headings increased (or a `### Slice`
     subsection was added under an existing case).

Failure mode is configurable:
  --mode warn   (default; fail-OPEN with prominent warning, exit 0)
  --mode strict (fail-CLOSED; exit 1 when evidence is missing)
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

try:
    from check_bootstrap import REPO_ROOT, utc_timestamp
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT, utc_timestamp


_EVIDENCE_PATH = REPO_ROOT / "evidence.md"
_CASE_HEADING_RE = re.compile(r"^## Case \d+", re.MULTILINE)
_SUBSLICE_HEADING_RE = re.compile(r"^### Slice [A-Z]\.\d+", re.MULTILINE)


_TRIGGER_EXACT_PATHS = frozenset({
    "dev/scripts/devctl/tests/scenarios/test_live_state_invariants.py",
    "dev/scripts/devctl/runtime/semantic_tdd_role.py",
    "dev/scripts/devctl/runtime/role_profile.py",
    "evidence.md",
})

_TRIGGER_SUBSTRINGS_RUNTIME = (
    "/runtime/control_topology",
    "/runtime/reviewer_mode",
    "/runtime/reviewer_gate",
    "/runtime/authority_snapshot",
    "/runtime/push_authorization",
    "/runtime/role_customization",
    "/runtime/work_intake_models",
    "/runtime/topology_authority_facts",
    "/runtime/commit_permission",
    "/runtime/control_plane_daemons",
    "/runtime/operator_context",
    "/review_channel/collaboration_session_status",
    "/review_channel/follow_controller",
    "/review_channel/collaboration_registry",
    "/review_channel/coordination_state_projection",
    "/platform/coordination_snapshot",
    "/platform/system_picture",
    "/platform/planning_ir",
)

_TRIGGER_TEST_PREFIXES = (
    "dev/scripts/devctl/tests/scenarios/test_topology_",
    "dev/scripts/devctl/tests/scenarios/test_role_",
    "dev/scripts/devctl/tests/scenarios/test_reviewer_",
    "dev/scripts/devctl/tests/scenarios/test_live_state_invariants",
)


@dataclass(frozen=True)
class ChangedSurfaces:
    staged: tuple[str, ...] = field(default_factory=tuple)
    last_commit: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class GuardReport:
    contract_id: str = "SemanticTddEvidenceGuardReport"
    schema_version: int = 1
    ok: bool = True
    mode: str = "warn"
    timestamp_utc: str = ""
    triggering_surfaces: tuple[str, ...] = field(default_factory=tuple)
    evidence_present: bool = True
    evidence_path: str = "evidence.md"
    case_count_current: int = 0
    case_count_committed: int = 0
    case_count_delta: int = 0
    slice_subheading_count_delta: int = 0
    evidence_in_diff: bool = False
    warnings: tuple[str, ...] = field(default_factory=tuple)
    hints: tuple[str, ...] = field(default_factory=tuple)


def _run_git(*args: str) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(REPO_ROOT), *args],
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return ""
    if result.returncode != 0:
        return ""
    return result.stdout


def _staged_paths() -> tuple[str, ...]:
    raw = _run_git("diff", "--cached", "--name-only")
    return tuple(line.strip() for line in raw.splitlines() if line.strip())


def _last_commit_paths() -> tuple[str, ...]:
    raw = _run_git("show", "--name-only", "--pretty=", "HEAD")
    return tuple(line.strip() for line in raw.splitlines() if line.strip())


def _is_trigger_surface(path: str) -> bool:
    path = path.strip()
    if not path:
        return False
    if path in _TRIGGER_EXACT_PATHS:
        return True
    for substr in _TRIGGER_SUBSTRINGS_RUNTIME:
        if substr in path:
            return True
    for prefix in _TRIGGER_TEST_PREFIXES:
        if path.startswith(prefix):
            return True
    return False


def _filter_triggers(paths: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(p for p in paths if _is_trigger_surface(p))


def _count_case_headings(text: str) -> int:
    return len(_CASE_HEADING_RE.findall(text))


def _count_slice_subheadings(text: str) -> int:
    return len(_SUBSLICE_HEADING_RE.findall(text))


def _read_committed_evidence() -> str:
    return _run_git("show", "HEAD:evidence.md")


def build_report(*, mode: str, scope: str) -> GuardReport:
    staged = _staged_paths()
    last_commit = _last_commit_paths()

    if scope == "staged":
        scan_paths = staged
    elif scope == "last_commit":
        scan_paths = last_commit
    else:
        scan_paths = staged + last_commit

    triggers = _filter_triggers(scan_paths)
    evidence_in_diff = (
        "evidence.md" in staged
        or "evidence.md" in last_commit
    )

    current_text = _EVIDENCE_PATH.read_text(encoding="utf-8") if _EVIDENCE_PATH.exists() else ""
    committed_text = _read_committed_evidence()

    case_current = _count_case_headings(current_text)
    case_committed = _count_case_headings(committed_text)
    case_delta = case_current - case_committed
    slice_delta = _count_slice_subheadings(current_text) - _count_slice_subheadings(committed_text)

    warnings: list[str] = []
    hints: list[str] = []
    ok = True

    if not triggers:
        return GuardReport(
            ok=True,
            mode=mode,
            timestamp_utc=utc_timestamp(),
            triggering_surfaces=(),
            evidence_present=_EVIDENCE_PATH.exists(),
            evidence_path="evidence.md",
            case_count_current=case_current,
            case_count_committed=case_committed,
            case_count_delta=case_delta,
            slice_subheading_count_delta=slice_delta,
            evidence_in_diff=evidence_in_diff,
            warnings=(),
            hints=("No semantic-TDD trigger surfaces touched; guard not required.",),
        )

    if not _EVIDENCE_PATH.exists():
        warnings.append(
            "evidence.md is missing entirely. Create it with a `## Case <N>` "
            "heading documenting the architectural insight surfaced by this "
            "slice (template lives in dev/active/semantic_tdd_lane.md)."
        )
        ok = False
    elif not evidence_in_diff:
        warnings.append(
            "Semantic-TDD trigger surfaces changed but evidence.md was NOT "
            "staged or touched in the same window. Add a new case (or extend "
            "an existing one) so future contributors can see WHAT the slice "
            "caught and WHY the discipline pays off."
        )
        ok = False
    elif case_delta <= 0 and slice_delta <= 0:
        warnings.append(
            "evidence.md is in the diff but no new `## Case <N>` heading "
            "was added and no new `### Slice <id>` sub-section appeared. "
            "Document the slice's win concretely or the discipline decays."
        )
        ok = False

    if triggers:
        hints.append(
            f"Trigger surfaces detected ({len(triggers)} file(s)): "
            + ", ".join(triggers[:6])
            + (f" (+{len(triggers) - 6} more)" if len(triggers) > 6 else "")
        )
    hints.append(
        f"Evidence cases: current={case_current} committed={case_committed} "
        f"delta=+{case_delta} | slice sub-sections delta=+{slice_delta}"
    )
    hints.append(
        "Template per case (in evidence.md): What semantic-TDD caught / "
        "How it was caught / The actual code (before) / The RED assertion / "
        "Why this is non-obvious without the discipline / Outcome."
    )

    return GuardReport(
        ok=ok if mode == "strict" else True,
        mode=mode,
        timestamp_utc=utc_timestamp(),
        triggering_surfaces=triggers,
        evidence_present=_EVIDENCE_PATH.exists(),
        evidence_path="evidence.md",
        case_count_current=case_current,
        case_count_committed=case_committed,
        case_count_delta=case_delta,
        slice_subheading_count_delta=slice_delta,
        evidence_in_diff=evidence_in_diff,
        warnings=tuple(warnings),
        hints=tuple(hints),
    )


def _render_md(report: GuardReport) -> str:
    lines = [
        "# check_semantic_tdd_evidence_log",
        "",
        f"- ok: **{report.ok}**",
        f"- mode: {report.mode}",
        f"- timestamp: {report.timestamp_utc}",
        f"- evidence.md present: {report.evidence_present}",
        f"- evidence in diff: {report.evidence_in_diff}",
        f"- case count: current={report.case_count_current} "
        f"committed={report.case_count_committed} delta=+{report.case_count_delta}",
        f"- slice sub-section delta: +{report.slice_subheading_count_delta}",
        "",
    ]
    if report.triggering_surfaces:
        lines.append("## Trigger surfaces")
        for surface in report.triggering_surfaces:
            lines.append(f"- {surface}")
        lines.append("")
    if report.warnings:
        lines.append("## WARNINGS (evidence-log gap)")
        for w in report.warnings:
            lines.append(f"- {w}")
        lines.append("")
    if report.hints:
        lines.append("## Hints")
        for h in report.hints:
            lines.append(f"- {h}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Forcing function so semantic-TDD slices log to evidence.md."
    )
    parser.add_argument(
        "--mode",
        choices=("warn", "strict"),
        default="warn",
        help="warn = fail-open (exit 0 even on gap); strict = fail-closed",
    )
    parser.add_argument(
        "--scope",
        choices=("staged", "last_commit", "both"),
        default="staged",
        help="Which diff window to scan",
    )
    parser.add_argument(
        "--format",
        choices=("json", "md"),
        default="md",
        help="Output format",
    )
    args = parser.parse_args(argv)

    report = build_report(mode=args.mode, scope=args.scope)

    if args.format == "json":
        sys.stdout.write(json.dumps(asdict(report), indent=2, default=str))
        sys.stdout.write("\n")
    else:
        sys.stdout.write(_render_md(report))
        sys.stdout.write("\n")

    if not report.ok and args.mode == "strict":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
