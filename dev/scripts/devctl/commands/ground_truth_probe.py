"""Thin ``ground-truth-probe`` CLI surface.

Owns ONE responsibility: run an optional pytest target, then hand its
exit code + report digest into the EXISTING
``runtime/ground_truth_probe_receipt.py:build_ground_truth_probe_receipt()``
reducer so the existing final-response gate can consume the receipt.

This command does NOT define a parallel receipt builder. It does NOT own
typed responsibility contracts, finding routing, render-surfaces, or
context-graph wiring. Those are Phase 2+ per the durable
live-state-semantic-TDD plan's "E2-MINIMAL — current slice" boundary.

Usage:
    python3 dev/scripts/devctl.py ground-truth-probe \\
        --record \\
        --pytest-target dev/scripts/devctl/tests/scenarios/test_live_state_invariants.py \\
        --format json

Verdict mapping:
    pytest exit 0       → GroundTruthProbeRunReceipt.verdict = "satisfied"
    pytest exit nonzero → GroundTruthProbeRunReceipt.verdict = "unsatisfied"

The final-response gate already reads the receipt ledger at
``dev/state/ground_truth_probe_receipts.jsonl`` and blocks completion
when the latest receipt's verdict is not "satisfied". No new gate added.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

from ..common import emit_output, write_output
from ..runtime.ground_truth_probe_receipt import (
    GroundTruthProbeRunInput,
    GroundTruthProbeRunReceipt,
    append_ground_truth_probe_receipt,
    build_ground_truth_probe_receipt,
)

_REPO_ROOT = Path(__file__).resolve().parents[4]

_LIVE_STATE_INVARIANT_PROBE_ID = "live_state_invariants_v1"

_DEFAULT_LIVE_STATE_PYTEST_TARGET = (
    "dev/scripts/devctl/tests/scenarios/test_live_state_invariants.py"
)

_ARTIFACT_WRITES_ENV = "DEVCTL_NO_ARTIFACT_WRITES"


def _text(value: object) -> str:
    """Coerce subprocess output (which may be bytes on some platforms) to str."""
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def _artifact_writes_suppressed() -> bool:
    """True when the repo-wide no-write env var is set."""
    return os.environ.get(_ARTIFACT_WRITES_ENV) == "1"


def add_parser(sub) -> None:
    """Register the ``ground-truth-probe`` subcommand."""
    from ..common import add_standard_output_arguments

    cmd = sub.add_parser(
        "ground-truth-probe",
        help=(
            "Run an optional pytest target and record the result as a "
            "GroundTruthProbeRunReceipt (existing receipt path; no parallel "
            "lifecycle)."
        ),
    )
    add_standard_output_arguments(cmd, format_choices=("json", "md"))
    cmd.add_argument(
        "--record",
        action="store_true",
        help="Append the receipt to dev/state/ground_truth_probe_receipts.jsonl.",
    )
    cmd.add_argument(
        "--pytest-target",
        default=_DEFAULT_LIVE_STATE_PYTEST_TARGET,
        help=(
            "Pytest path to execute. Defaults to the live-state invariant "
            "suite so the final-response gate's default invocation produces "
            "a real receipt. Use --skip-pytest to record trigger evidence "
            "only."
        ),
    )
    cmd.add_argument(
        "--skip-pytest",
        action="store_true",
        help=(
            "Do not run pytest. Records a NON-SATISFYING receipt "
            "(verdict=missing) — debug/smoke only. Will NOT unblock the "
            "final-response gate."
        ),
    )
    cmd.add_argument(
        "--strict",
        action="store_true",
        help=(
            "Return nonzero exit code when the pytest-backed receipt verdict "
            "is unsatisfied. Off by default so the receipt is always written "
            "AND readable by the calling agent. Use --strict in CI."
        ),
    )
    cmd.add_argument(
        "--base-ref",
        default="",
        help="Optional git base ref recorded on the receipt.",
    )
    cmd.add_argument(
        "--head-ref",
        default="HEAD",
        help="Git head ref recorded on the receipt (default: HEAD).",
    )
    cmd.add_argument(
        "--probe-id",
        default=_LIVE_STATE_INVARIANT_PROBE_ID,
        help=(
            "Probe id stamped on the receipt's observed_probe_ids when "
            "pytest passes (default: live_state_invariants_v1)."
        ),
    )


def run(args) -> int:
    """Run the pytest target (if any), build the receipt, optionally record."""
    pytest_target = str(getattr(args, "pytest_target", "") or "").strip()
    skip_pytest = bool(getattr(args, "skip_pytest", False))
    base_ref = str(getattr(args, "base_ref", "") or "").strip()
    head_ref = str(getattr(args, "head_ref", "HEAD") or "HEAD").strip() or "HEAD"
    probe_id = str(getattr(args, "probe_id", _LIVE_STATE_INVARIANT_PROBE_ID) or _LIVE_STATE_INVARIANT_PROBE_ID).strip()
    record = bool(getattr(args, "record", False))

    pytest_outcome = (
        _run_pytest_target(pytest_target)
        if (pytest_target and not skip_pytest)
        else None
    )

    trigger_paths = (pytest_target,) if pytest_target else ()
    if pytest_outcome is not None and pytest_outcome["exit_code"] == 0:
        observed_probe_ids = (probe_id,)
        warnings: tuple[str, ...] = ()
    elif pytest_outcome is not None:
        observed_probe_ids = ()
        warnings = (
            f"pytest_target_failed:{pytest_target}",
            f"pytest_exit_code:{pytest_outcome['exit_code']}",
            f"pytest_failure_summary:{pytest_outcome['summary']}",
        )
    else:
        observed_probe_ids = ()
        warnings = ()

    required_probe_ids = (probe_id,) if pytest_target else ()

    receipt: GroundTruthProbeRunReceipt = build_ground_truth_probe_receipt(
        GroundTruthProbeRunInput(
            trigger_paths=trigger_paths,
            design_ids=("ground-truth-probe",),
            required_probe_ids=required_probe_ids,
            observed_probe_ids=observed_probe_ids,
            base_ref=base_ref,
            head_ref=head_ref,
            probe_report_path=(pytest_outcome or {}).get("report_path", ""),
            probe_report_sha256=(pytest_outcome or {}).get("report_sha256", ""),
            warnings=warnings,
        )
    )

    # Override builder's verdict when pytest evidence is authoritative.
    # The existing builder only emits satisfied/missing based on probe id
    # presence; pytest gives a stronger signal (the actual run executed
    # and either honored or violated the live-state contract), so it maps
    # directly to "satisfied" / "unsatisfied" per the live-state semantic
    # TDD plan's verdict semantics.
    receipt = _adjust_verdict_for_pytest(receipt, pytest_outcome)

    receipt_path = ""
    if record and not _artifact_writes_suppressed():
        receipt_path = (
            append_ground_truth_probe_receipt(receipt, repo_root=_REPO_ROOT)
            .relative_to(_REPO_ROOT)
            .as_posix()
        )

    payload = {
        "command": "ground-truth-probe",
        "pytest_target": pytest_target,
        "pytest_exit_code": (pytest_outcome or {}).get("exit_code"),
        "pytest_summary": (pytest_outcome or {}).get("summary", ""),
        "receipt_recorded": bool(receipt_path),
        "receipt_path": receipt_path,
        "receipt": receipt.to_dict(),
    }

    if getattr(args, "format", "json") == "json":
        output = json.dumps(payload, indent=2)
    else:
        output = _markdown_summary(payload)

    emit_output(
        output,
        output_path=getattr(args, "output", None),
        pipe_command=getattr(args, "pipe_command", None),
        pipe_args=getattr(args, "pipe_args", None),
        writer=write_output,
    )

    # Default: exit 0 even when the receipt's verdict is "unsatisfied".
    # Rationale: the receipt IS the proof artifact. If the caller (agent or
    # gate) sees a nonzero exit code, it may treat the whole command as
    # failed and never inspect the receipt — defeating the proof chain.
    # Use --strict in CI when a nonzero signal is desired.
    if bool(getattr(args, "strict", False)):
        if pytest_outcome is not None and pytest_outcome["exit_code"] != 0:
            return 1
    return 0


def _run_pytest_target(target: str) -> dict[str, object]:
    """Run pytest against ``target`` and capture exit code + report digest.

    Returns:
        dict with keys: exit_code (int), summary (str), report_path (str),
        report_sha256 (str). The report file lives under
        ``dev/reports/ground_truth_probe_pytest/<digest>.txt`` and contains
        the captured pytest stdout — sufficient MVP evidence (not universal
        audit evidence) without requiring the optional pytest-json-report
        plugin.

    Failure modes that produce a typed receipt rather than crashing:
      - Target path does not exist or escapes the repo → exit_code 127
      - subprocess.run raises TimeoutExpired → exit_code 124
      - subprocess.run raises OSError (e.g. ENOENT for the interpreter)
        → exit_code 127
    """
    # Path validation — refuse junk paths so the receipt records a real
    # reason rather than pytest's own confusing "no tests collected" code.
    # Strip pytest node id suffix (after ::) for path checks; pytest itself
    # accepts node ids like ``path/to/test.py::test_name`` and the suffix
    # is NOT part of the filesystem path.
    target_path_text = target.split("::", 1)[0]
    candidate = (_REPO_ROOT / target_path_text).resolve()
    try:
        candidate.relative_to(_REPO_ROOT)
    except ValueError:
        return _failure_outcome(
            exit_code=127,
            summary=f"pytest target escapes repo: {target}",
            raw_output=f"REFUSED: target path resolves outside repo root: {candidate}",
        )
    if not candidate.exists():
        return _failure_outcome(
            exit_code=127,
            summary=f"pytest target not found: {target}",
            raw_output=f"REFUSED: target path does not exist: {candidate}",
        )

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", target, "-v", "--tb=short", "-rN"],
            cwd=str(_REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=600,
        )
    except subprocess.TimeoutExpired as exc:
        # exc.stdout / exc.stderr may be bytes depending on platform —
        # coerce defensively so string concatenation never crashes.
        raw_output = (
            _text(exc.stdout)
            + ("\n--- stderr ---\n" + _text(exc.stderr) if exc.stderr else "")
            + f"\n--- timeout ---\npytest timed out after {exc.timeout}s"
        )
        return _failure_outcome(
            exit_code=124,
            summary=f"pytest timed out after {exc.timeout}s",
            raw_output=raw_output,
        )
    except OSError as exc:
        return _failure_outcome(
            exit_code=127,
            summary=f"pytest execution failed: {type(exc).__name__}: {exc}",
            raw_output=f"OSError invoking pytest: {exc!r}",
        )

    raw_output = result.stdout + ("\n--- stderr ---\n" + result.stderr if result.stderr else "")
    summary_line = _extract_summary_line(raw_output)
    return _persist_pytest_report(
        exit_code=int(result.returncode),
        summary=summary_line,
        raw_output=raw_output,
    )


def _persist_pytest_report(
    *,
    exit_code: int,
    summary: str,
    raw_output: str,
) -> dict[str, object]:
    """Hash-pin raw pytest output to disk; return the report descriptor.

    When ``DEVCTL_NO_ARTIFACT_WRITES=1`` is set, the report file is NOT
    written. The sha256 is still computed (so callers see deterministic
    content fingerprints) but ``report_path`` is the empty string —
    signalling no on-disk artifact was produced.
    """
    report_sha = "sha256:" + hashlib.sha256(raw_output.encode("utf-8")).hexdigest()
    if _artifact_writes_suppressed():
        return {
            "exit_code": exit_code,
            "summary": summary,
            "report_path": "",
            "report_sha256": report_sha,
        }
    report_dir = _REPO_ROOT / "dev/reports/ground_truth_probe_pytest"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_file = report_dir / f"{report_sha[7:23]}.txt"
    report_file.write_text(raw_output, encoding="utf-8")
    return {
        "exit_code": exit_code,
        "summary": summary,
        "report_path": report_file.relative_to(_REPO_ROOT).as_posix(),
        "report_sha256": report_sha,
    }


def _failure_outcome(
    *,
    exit_code: int,
    summary: str,
    raw_output: str,
) -> dict[str, object]:
    """Build a failure outcome that still persists captured evidence."""
    return _persist_pytest_report(
        exit_code=exit_code,
        summary=summary,
        raw_output=raw_output,
    )


def _extract_summary_line(stdout: str) -> str:
    """Return pytest's terminal summary line (e.g. '2 passed, 1 xfailed in 5s')."""
    for line in reversed(stdout.splitlines()):
        stripped = line.strip().strip("=").strip()
        if not stripped:
            continue
        if any(token in stripped for token in ("passed", "failed", "error", "xfailed", "skipped")):
            return stripped
    return ""


_PYTEST_PASSED_PATTERN = re.compile(r"(\d+)\s+passed\b")


def _real_pass_count(summary: str) -> int:
    """Extract the actual ``N passed`` count from pytest's terminal summary.

    ``passed`` is the ONLY pytest outcome that constitutes real evidence.
    xfailed / skipped / xpassed / deselected are debt-acknowledgement or
    non-execution states and must not certify the suite as "satisfied".
    """
    match = _PYTEST_PASSED_PATTERN.search(summary or "")
    return int(match.group(1)) if match else 0


def _adjust_verdict_for_pytest(
    receipt: GroundTruthProbeRunReceipt,
    pytest_outcome: dict[str, object] | None,
) -> GroundTruthProbeRunReceipt:
    """Override receipt.verdict when pytest evidence is decisive.

    Verdict rules (oracle-integrity policy):

      satisfied:
        pytest exit code 0 AND at least one test actually PASSED (not just
        xfail/skipped/xpassed). An empty suite, an all-xfail suite, or an
        all-skipped suite cannot satisfy the gate — those states prove
        nothing.

      unsatisfied:
        pytest exit code nonzero (test failure, collection error, target
        missing, timeout, OSError) — OR pytest exit 0 with zero real
        passes (no actual evidence produced).

    This guards against the hidden lie "exit 0 ⇒ proof": an agent could
    point the probe at an empty or xfail-only file and pretend the gate
    is happy. The writer refuses.
    """
    if pytest_outcome is None:
        return receipt
    exit_code = int(pytest_outcome["exit_code"])
    summary = str(pytest_outcome.get("summary") or "")
    real_passes = _real_pass_count(summary)
    if exit_code == 0 and real_passes >= 1:
        new_verdict = "satisfied"
        extra_warnings: tuple[str, ...] = ()
    else:
        new_verdict = "unsatisfied"
        extra_warnings = ()
        if exit_code == 0 and real_passes == 0:
            extra_warnings = (
                f"pytest_exit_0_but_no_real_passes:{summary!r}",
                "verdict_downgraded_to_unsatisfied:empty_or_xfail_only_suite_is_not_proof",
            )
    if receipt.verdict == new_verdict and not extra_warnings:
        return receipt
    data = asdict(receipt)
    data["verdict"] = new_verdict
    data["trigger_paths"] = tuple(receipt.trigger_paths)
    data["design_ids"] = tuple(receipt.design_ids)
    data["required_probe_ids"] = tuple(receipt.required_probe_ids)
    data["observed_probe_ids"] = tuple(receipt.observed_probe_ids)
    data["warnings"] = tuple(receipt.warnings) + extra_warnings
    return GroundTruthProbeRunReceipt(**data)


def _markdown_summary(payload: dict[str, object]) -> str:
    receipt = payload.get("receipt") or {}
    lines = [
        "# Ground-Truth Probe Receipt",
        "",
        f"- contract_id: `{receipt.get('contract_id', '')}`",
        f"- schema_version: `{receipt.get('schema_version', '')}`",
        f"- verdict: **{receipt.get('verdict', '')}**",
        f"- created_at_utc: `{receipt.get('created_at_utc', '')}`",
        f"- head_ref: `{receipt.get('head_ref', '')}`",
        f"- pytest_target: `{payload.get('pytest_target', '')}`",
        f"- pytest_exit_code: `{payload.get('pytest_exit_code')}`",
        f"- pytest_summary: `{payload.get('pytest_summary', '')}`",
        f"- probe_report_path: `{receipt.get('probe_report_path', '')}`",
        f"- probe_report_sha256: `{receipt.get('probe_report_sha256', '')}`",
        f"- receipt_recorded: `{payload.get('receipt_recorded')}`",
        f"- receipt_path: `{payload.get('receipt_path', '')}`",
    ]
    warnings = receipt.get("warnings") or []
    if warnings:
        lines.append("")
        lines.append("## Warnings")
        for warning in warnings:
            lines.append(f"- `{warning}`")
    return "\n".join(lines)
