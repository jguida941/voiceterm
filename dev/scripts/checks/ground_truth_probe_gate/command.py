"""Enforce ground-truth probe receipts for authority/proof design changes."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from check_bootstrap import REPO_ROOT
except ModuleNotFoundError:  # pragma: no cover
    from dev.scripts.checks.check_bootstrap import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dev.scripts.devctl.collect import collect_git_status
from dev.scripts.devctl.runtime.ground_truth_probe_receipt import (
    GroundTruthProbeRunReceipt,
    detect_ground_truth_trigger_paths,
    latest_ground_truth_probe_receipt,
    trigger_paths_digest,
)
from dev.scripts.devctl.time_utils import utc_timestamp


def build_report(
    *,
    since_ref: str | None = None,
    head_ref: str = "HEAD",
    receipt_path: str | Path | None = None,
) -> dict[str, object]:
    """Return guard status for current proof/authority trigger paths."""
    git_info = collect_git_status(since_ref, head_ref, repo_root=REPO_ROOT)
    changed_paths = _changed_paths(git_info)
    trigger_paths = detect_ground_truth_trigger_paths(
        repo_root=REPO_ROOT,
        changed_paths=changed_paths,
    )
    receipt = latest_ground_truth_probe_receipt(
        repo_root=REPO_ROOT,
        receipt_path=receipt_path,
    )
    violations = _violations(trigger_paths=trigger_paths, receipt=receipt)
    return {
        "command": "check_ground_truth_probe_gate",
        "timestamp": utc_timestamp(),
        "ok": not violations,
        "since_ref": since_ref,
        "head_ref": head_ref,
        "changed_path_count": len(changed_paths),
        "trigger_paths": list(trigger_paths),
        "trigger_paths_digest": trigger_paths_digest(trigger_paths),
        "receipt": receipt.to_dict() if receipt is not None else None,
        "violations": violations,
    }


def render_markdown(report: dict[str, object]) -> str:
    lines = [
        "# check_ground_truth_probe_gate",
        "",
        f"- ok: {report['ok']}",
        f"- trigger_paths: {len(report['trigger_paths'])}",
        f"- trigger_paths_digest: {report['trigger_paths_digest']}",
    ]
    receipt = report.get("receipt")
    if isinstance(receipt, dict):
        lines.append(f"- receipt_verdict: {receipt.get('verdict')}")
        lines.append(f"- receipt_created_at_utc: {receipt.get('created_at_utc')}")
    else:
        lines.append("- receipt_verdict: missing")
    if report["trigger_paths"]:
        lines.extend(["", "## Trigger Paths"])
        for path in report["trigger_paths"]:
            lines.append(f"- {path}")
    if report["violations"]:
        lines.extend(["", "## Violations"])
        for violation in report["violations"]:
            lines.append(f"- {violation}")
    return "\n".join(lines)


def _violations(
    *,
    trigger_paths: tuple[str, ...],
    receipt: GroundTruthProbeRunReceipt | None,
) -> list[str]:
    if not trigger_paths:
        return []
    if receipt is None:
        return ["missing_ground_truth_probe_receipt"]
    violations: list[str] = []
    expected_digest = trigger_paths_digest(trigger_paths)
    if receipt.changed_paths_digest != expected_digest:
        violations.append("stale_ground_truth_probe_receipt")
    if receipt.verdict != "satisfied":
        violations.append(f"receipt_not_satisfied:{receipt.verdict}")
    missing = [
        probe_id
        for probe_id in receipt.required_probe_ids
        if probe_id not in set(receipt.observed_probe_ids)
    ]
    for probe_id in missing:
        violations.append(f"missing_required_probe:{probe_id}")
    return violations


def _changed_paths(git_info: dict[str, object]) -> tuple[str, ...]:
    rows = git_info.get("changes")
    if not isinstance(rows, list):
        return ()
    paths: list[str] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        path = str(row.get("path") or "").strip()
        if path:
            paths.append(path)
    return tuple(sorted(dict.fromkeys(paths)))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__ or "")
    parser.add_argument("--since-ref", default=None)
    parser.add_argument("--head-ref", default="HEAD")
    parser.add_argument("--receipt-path", default="")
    parser.add_argument("--format", choices=("md", "json"), default="md")
    args = parser.parse_args()
    report = build_report(
        since_ref=args.since_ref,
        head_ref=args.head_ref,
        receipt_path=args.receipt_path or None,
    )
    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(render_markdown(report))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
