#!/usr/bin/env python3
"""GuardIR v4.44 (rev_pkt_4723) — no-prose-authority-promotion guard.

Fails when maintained docs promote generated markdown, active markdown,
bridge/dashboard text, or chat above typed state. The GuardIR v4.37+
packet-as-evidence rule says projections and offline evidence are NEVER
durable authority; durable authority lives in typed state (PlanRow,
contracts, receipts, guards). This guard scans hand-maintained docs for
phrases that contradict that invariant.

Maintained doc scope (initial; can be extended via repo policy):
- ``dev/guides/DEVELOPMENT.md``
- ``dev/guides/SYSTEM_MAP.md``
- ``dev/active/INDEX.md``

Disallowed phrases (case-sensitive substring match):
- ``Canonical prose authority``
- ``canonical execution state``
- ``AGENTS.md is workflow authority``
- ``MASTER_PLAN.md is canonical``
- ``This file is the canonical registry``

The guard exits 0 when no disallowed phrases are present; exits 1 with a
typed JSON or markdown payload otherwise so CI can surface the violation.

Usage:
    python3 dev/scripts/checks/check_no_prose_authority_promotion.py --format md
    python3 dev/scripts/checks/check_no_prose_authority_promotion.py --format json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


#: Hand-maintained docs scanned by this guard. Generated docs (AGENTS.md,
#: CLAUDE.md, bridge.md) are NOT in this list — fixing those requires updating
#: the typed renderer inputs, per codex's v4.44 directive
#: "Do not hand-edit generated boot cards as the fix."
_MAINTAINED_DOC_PATHS: tuple[str, ...] = (
    "dev/guides/DEVELOPMENT.md",
    "dev/guides/SYSTEM_MAP.md",
    "dev/active/INDEX.md",
    "dev/active/MASTER_PLAN.md",
    "dev/active/ai_governance_platform.md",
    "dev/active/platform_authority_loop.md",
    "dev/guides/PLATFORM_GUIDE.md",
    "dev/guides/AI_GOVERNANCE_PLATFORM.md",
)

#: Phrases that promote prose above typed state. Case-sensitive substring
#: match. Each entry is the literal disallowed phrase plus a short reason
#: rendered in the failure output.
_DISALLOWED_PHRASES: tuple[tuple[str, str], ...] = (
    (
        "Canonical prose authority",
        "Prose surfaces are projections, not durable authority (v4.37+).",
    ),
    (
        "canonical execution state",
        "Execution state is typed (PlanRow / receipts), not prose (v4.37+).",
    ),
    (
        "AGENTS.md is workflow authority",
        "AGENTS.md is a generated boot card / projection, not workflow authority.",
    ),
    (
        "MASTER_PLAN.md is canonical",
        "MASTER_PLAN.md is a tracker projection over `dev/state/plan_index.jsonl`.",
    ),
    (
        "This file is the canonical registry",
        "Canonical registry is `dev/state/plan_index.jsonl`; this file is a "
        "maintained pointer index.",
    ),
)

#: v4.44.1 (rev_pkt_4725): broadened contextual scan. A line is flagged when
#: it co-mentions a protected doc reference AND a dangerous authority term,
#: UNLESS the same line contains a qualifying projection/typed-state term.
#: Codex's reproduction caught lines like
#:   ``AGENTS.md stays the source of truth for policy/branch workflow``
#:   ``canonical bootstrap order in AGENTS.md:235-242``
#:   ``MASTER_PLAN.md ... canonical tracker``
#: All have a protected-doc ref + a dangerous term on the same line and
#: NO projection/typed-state qualifier.
_PROTECTED_DOC_REFS: tuple[str, ...] = (
    "AGENTS.md",
    "CLAUDE.md",
    "MASTER_PLAN.md",
    "dev/active/INDEX.md",
)

#: Authority-promoting terms. Case-insensitive match on the line as a whole.
#: v4.44.3 (rev_pkt_4728) expanded this set after codex's sidecar audit caught
#: live authority-promoting language in owner-spec docs and platform guide
#: surfaces — places agents read for routing/scope decisions. Examples codex
#: surfaced (line counts at audit time):
#:   MASTER_PLAN.md:5  "single active plan for strategy, execution, and release tracking"
#:   ai_governance_platform.md:7  "MASTER_PLAN stays the repo-wide tracker authority"
#:   SYSTEM_MAP.md:559  "MASTER_PLAN.md — execution authority / tracker"
#:   DEVELOPMENT.md:46  "canonical findings + execution checklist"
#:   PLATFORM_GUIDE.md:337  "read the active authority docs for your scope"
#:   AI_GOVERNANCE_PLATFORM.md:222  "executable source of truth for the shared layer model"
_DANGEROUS_AUTHORITY_TERMS: tuple[str, ...] = (
    "source of truth",
    "source-of-truth",
    "canonical bootstrap",
    "canonical tracker",
    "canonical registry",
    "canonical spec",
    "canonical owner",
    "canonical active",
    "canonical findings",
    "bootstrap order",
    "execution authority",
    "execution state authority",
    "tracker authority",
    "router authority",
    "active authority docs",
    "active authority doc",
    "only main active plan",
    "single active plan",
    "execution-owner set",
    "executable source of truth",
    "markdown becomes structured authority",
)

#: Qualifying terms that, when present on the SAME LINE as a dangerous combo,
#: mean the line correctly frames the doc as a projection / pointer / evidence
#: rather than durable authority. Case-insensitive substring match.
#:
#: v4.44.3 (rev_pkt_4728) expanded this set so lines that USE the dangerous
#: terms in correct typed-framing (positive: "typed PlanRow rows"; negative:
#: "without treating X as execution authority"; ingestion: "markdown is
#: ingestion/projection, not durable execution authority") are correctly
#: exempted, while bare authority claims still fail. Codex's directive:
#: "Allow these terms only when the same line clearly frames typed state,
#: PlanRows, contracts, receipts, guards, projections, pointers, or
#: reference-only material as the durable authority."
_PROJECTION_QUALIFIERS: tuple[str, ...] = (
    # Positive typed-framing
    "projection",
    "generated",
    "pointer index",
    "pointer over",
    "over typed",
    "plan_index.jsonl",
    "maintained projection",
    "tracker_projection",
    "tracker projection",
    "typed planrow",
    "typed `planrow`",
    "typed plan_row",
    "typed `plan_row`",
    "typed planrows",
    "planrow rows",
    "typed state",
    "typed action",
    # v4.45.1 (rev_pkt_4735): broad single-word qualifiers like ``contracts``,
    # ``receipts``, and ``reducer`` were too permissive — they exempted whole
    # lines just because the word appeared anywhere, even in unrelated clauses
    # like ``contracts may disagree``. Compound forms below require typed-
    # framing intent (preposition or ``typed`` prefix).
    "typed contracts",
    "in contracts",
    "via contracts",
    "by contracts",
    "the contracts",
    "typed receipts",
    "in receipts",
    "via receipts",
    "by receipts",
    "the receipts",
    "guard results",
    "reference-only",
    "reference only",
    "owner spec",
    "owner doc",
    "ingestion/projection",
    "scope-preserving ingestion",
    "bounded projection",
    # Negation / non-promotion markers
    "without treating",
    "without pretending",
    "without claiming",
    "without regex",
    "not durable authority",
    "not durable execution authority",
    "not authority",
    "not the source",
    "not source-of-truth",
    "rather than",
    "instead of",
    "stops claiming",
    "stops being",
    "stops outranking",
    "supposed to be",
    "must never become",
    "do not make",
    "must not",
    "are supposed to",
    "compile execution authority",
    # Historical changelog commentary referencing packet decisions
    "rev_pkt_",
    # Typed-completion markers — task lines bound to typed PlanRow IDs
    "- [x]",
    "- [ ]",
    "[x] mp",
    "[ ] mp",
    "[x] `mp",
    "[ ] `mp",
    "phase_id=mp",
    "phase metadata:",
    "owner_doc=`dev/active",
    "owner_doc:",
    "acceptance_criteria:",
    "depends_on:",
    "status: `done`",
    "status=in_progress",
    "status: in_progress",
    "summary=",
    "scope: preserve",
    "scope: collapse",
    # Common negation patterns that flip dangerous terms into non-promotion
    "do not treat",
    "do not make",
    "do not let",
    "do not keep",
    "not standalone",
    "not durable",
    "not advisory",
    "supporting context, not",
    "not a replacement",
    "not a second",
    "not a peer",
    "second source of truth",  # "not a second source of truth"
    # Backend / typed registry references that carry the actual authority
    "findingbacklog",
    "packetplanintegration",
    "planregistry",
    "plan_registry",
    "ingestionprovenance",
    "ingestion source",
    "ingestion/projection",
    "machine-readable",
    # Structural markers for projection-only docs
    "describes each doc",
    "describes the",
    "column below",
    "authority projection",
    "router projection",
    "navigation surface",
    "supplementary navigation",
    # Additional typed-state qualifiers
    "typed bootstrap",
    "typed phase",
    "typed phase task",
    "review_state",
    "event log",
    # v4.45.1 (rev_pkt_4735): ``reducer`` alone was too broad. Require
    # compound forms that demonstrate typed-framing intent.
    "reducer state",
    "by the reducer",
    "in the reducer",
    "via reducer",
    "from reducer",
    "typed reducer",
    "agent_sync",
    "cli-first",
    "bundle as",
    "bundle_registry",
    "bounded source",
    "bounded ai assist",
    # Descriptive metadata patterns
    "must preserve",
    "must name its",
    "must stay consistent",
    "must never become",
    "what counts as",
    "(must preserve)",
)


def _line_has_authority_promotion(line: str) -> tuple[bool, str]:
    """Return (is_violation, reason) for a single line.

    A line violates the broadened guard when:
    1. It contains one of ``_DANGEROUS_AUTHORITY_TERMS`` as a substring
       (case-insensitive), AND
    2. The same line does NOT contain a qualifying projection term from
       ``_PROJECTION_QUALIFIERS``.

    The v4.44.3 (rev_pkt_4728) refactor collapses the two-pass design
    (standalone + doc-ref combo) into a single standalone-terms scan,
    because codex's sidecar audit surfaced authority-promotion language that
    uses self-references ("this file") instead of explicit doc paths. A
    self-claim like ``treat this file as the only main active plan`` should
    be flagged whether or not another doc is named on the same line — the
    phrase itself elevates a maintained surface to durable authority.

    Returns ``(False, "")`` when not a violation.
    """
    line_lower = line.lower()
    if any(q in line_lower for q in _PROJECTION_QUALIFIERS):
        return (False, "")
    for term in _DANGEROUS_AUTHORITY_TERMS:
        if term in line_lower:
            return (
                True,
                f"Phrase ``{term}`` promotes a maintained surface to durable "
                "authority. Reframe as a projection / pointer over typed "
                "state (``dev/state/plan_index.jsonl``, contracts, receipts, "
                "or guards), or add a projection qualifier on the line.",
            )
    return (False, "")


def _scan_file(path: Path) -> list[dict[str, object]]:
    """Return one row per disallowed phrase / contextual violation in ``path``.

    Two scan passes:
    1. **Legacy substring pass**: looks for the original v4.44 phrases (e.g.
       ``Canonical prose authority``).
    2. **v4.44.1 contextual pass**: per-line check for protected doc refs
       co-occurring with dangerous authority terms unless qualified by
       projection / typed-state language.
    """
    if not path.exists():
        return []
    try:
        content = path.read_text(encoding="utf-8")
    except OSError:
        return []
    violations: list[dict[str, object]] = []
    # Pass 1: legacy substring scan
    for phrase, reason in _DISALLOWED_PHRASES:
        start = 0
        while True:
            idx = content.find(phrase, start)
            if idx == -1:
                break
            line_no = content.count("\n", 0, idx) + 1
            violations.append(
                {
                    "doc_path": str(path),
                    "phrase": phrase,
                    "line_number": line_no,
                    "reason": reason,
                }
            )
            start = idx + len(phrase)
    # Pass 2: v4.44.1 contextual scan
    for line_idx, line in enumerate(content.splitlines(), start=1):
        is_violation, reason = _line_has_authority_promotion(line)
        if is_violation:
            violations.append(
                {
                    "doc_path": str(path),
                    "phrase": line.strip()[:120],
                    "line_number": line_idx,
                    "reason": reason,
                }
            )
    return violations


def _scan_all(repo_root: Path) -> list[dict[str, object]]:
    """Scan every maintained doc and aggregate violations."""
    all_violations: list[dict[str, object]] = []
    for rel in _MAINTAINED_DOC_PATHS:
        all_violations.extend(_scan_file(repo_root / rel))
    return all_violations


def _render_md(violations: list[dict[str, object]]) -> str:
    if not violations:
        return (
            "# check_no_prose_authority_promotion\n\n"
            "- ok: True\n"
            "- violation_count: 0\n"
            f"- maintained_doc_count: {len(_MAINTAINED_DOC_PATHS)}\n"
        )
    lines = [
        "# check_no_prose_authority_promotion",
        "",
        "- ok: False",
        f"- violation_count: {len(violations)}",
        f"- maintained_doc_count: {len(_MAINTAINED_DOC_PATHS)}",
        "",
        "## Violations",
        "",
    ]
    for v in violations:
        lines.append(
            f"- `{v['doc_path']}:{v['line_number']}`: "
            f"phrase {v['phrase']!r} — {v['reason']}"
        )
    return "\n".join(lines) + "\n"


def _render_json(violations: list[dict[str, object]]) -> str:
    return json.dumps(
        {
            "contract_id": "ProseAuthorityPromotionCheck",
            "schema_version": 1,
            "ok": not violations,
            "violation_count": len(violations),
            "maintained_doc_count": len(_MAINTAINED_DOC_PATHS),
            "maintained_doc_paths": list(_MAINTAINED_DOC_PATHS),
            "disallowed_phrases": [
                {"phrase": p, "reason": r} for p, r in _DISALLOWED_PHRASES
            ],
            "violations": violations,
        },
        indent=2,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "GuardIR v4.44 (rev_pkt_4723): fail when maintained docs promote "
            "prose surfaces (AGENTS.md, MASTER_PLAN.md, INDEX.md, etc.) "
            "above typed state."
        ),
    )
    parser.add_argument(
        "--format",
        choices=("md", "json"),
        default="md",
        help="Output format (default: md).",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help=(
            "Repo root to scan (default: 4 levels up from this script, the "
            "repo root)."
        ),
    )
    args = parser.parse_args(argv)
    repo_root = args.repo_root or Path(__file__).resolve().parents[3]
    violations = _scan_all(repo_root)
    output = _render_json(violations) if args.format == "json" else _render_md(violations)
    print(output)
    return 0 if not violations else 1


if __name__ == "__main__":
    sys.exit(main())
