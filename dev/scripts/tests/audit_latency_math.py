#!/usr/bin/env python3
"""Audit VoiceTerm latency math against logged latency_audit fields.

Reads `latency_audit|...` lines, recomputes expected values, and reports:
- `display_ms` consistency with `stt_ms`
- `rtf` consistency with `stt_ms/speech_ms`
- `math` field consistency
- `badge` consistency for the selected latency display mode
"""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class Mismatch:
    line_no: int
    field: str
    expected: str
    actual: str


def default_log_path() -> Path:
    tmpdir = os.environ.get("TMPDIR") or "/tmp"
    return Path(tmpdir) / "voiceterm_tui.log"


def parse_optional_u32(value: str) -> Optional[int]:
    if value == "na":
        return None
    try:
        parsed = int(value)
    except ValueError:
        return None
    if parsed < 0:
        return None
    return parsed


def parse_optional_float(value: str) -> Optional[float]:
    if value == "na":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def expected_badge(mode: str, stt_ms: Optional[int], rtf: Optional[float]) -> str:
    if stt_ms is None:
        return "na"
    if mode == "off":
        return "off"
    if mode == "short":
        return f"{stt_ms}ms"
    if mode == "label":
        return f"Latency:{stt_ms}ms"
    if mode == "rtf":
        if rtf is None:
            return f"{stt_ms}ms"
        return f"{rtf:.2f}x"
    if mode == "both":
        if rtf is None:
            return f"{stt_ms}ms"
        return f"{stt_ms}ms+{rtf:.2f}x"
    return "na"


def parse_latency_audit_fields(line: str) -> Optional[dict[str, str]]:
    marker = "latency_audit|"
    if marker not in line:
        return None
    payload = line.split(marker, 1)[1].strip()
    fields: dict[str, str] = {}
    for part in payload.split("|"):
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        fields[key] = value
    return fields


def expected_math(stt_ms: Optional[int], speech_ms: Optional[int]) -> str:
    if stt_ms is None or speech_ms is None or speech_ms <= 0:
        return "na"
    return f"{stt_ms}/{speech_ms}={stt_ms / speech_ms:.3f}"


def audit_file(log_path: Path, rtf_tolerance: float, max_report: int) -> tuple[int, list[Mismatch]]:
    lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    mismatches: list[Mismatch] = []
    latency_line_count = 0

    for line_no, line in enumerate(lines, start=1):
        fields = parse_latency_audit_fields(line)
        if fields is None:
            continue
        latency_line_count += 1

        stt_ms = parse_optional_u32(fields.get("stt_ms", "na"))
        speech_ms = parse_optional_u32(fields.get("speech_ms", "na"))
        display_ms = parse_optional_u32(fields.get("display_ms", "na"))
        rtf_logged = parse_optional_float(fields.get("rtf", "na"))
        mode = fields.get("mode", "na")
        badge = fields.get("badge", "na")
        math_field = fields.get("math", "na")
        source = fields.get("source", "na")
        pipeline = fields.get("pipeline", "na")

        expected_display = "na" if stt_ms is None else str(stt_ms)
        if fields.get("display_ms", "na") != expected_display:
            mismatches.append(
                Mismatch(
                    line_no=line_no,
                    field="display_ms",
                    expected=expected_display,
                    actual=fields.get("display_ms", "na"),
                )
            )

        expected_source = "na" if stt_ms is None else "stt"
        if source != expected_source:
            mismatches.append(
                Mismatch(
                    line_no=line_no,
                    field="source",
                    expected=expected_source,
                    actual=source,
                )
            )

        if pipeline not in {"rust", "python"}:
            mismatches.append(
                Mismatch(
                    line_no=line_no,
                    field="pipeline",
                    expected="rust|python",
                    actual=pipeline,
                )
            )

        rtf_expected: Optional[float] = None
        if stt_ms is not None and speech_ms is not None and speech_ms > 0:
            rtf_expected = stt_ms / speech_ms

        if rtf_expected is None:
            if fields.get("rtf", "na") != "na":
                mismatches.append(
                    Mismatch(
                        line_no=line_no,
                        field="rtf",
                        expected="na",
                        actual=fields.get("rtf", "na"),
                    )
                )
        else:
            if rtf_logged is None:
                mismatches.append(
                    Mismatch(
                        line_no=line_no,
                        field="rtf",
                        expected=f"{rtf_expected:.3f}",
                        actual=fields.get("rtf", "na"),
                    )
                )
            elif abs(rtf_logged - rtf_expected) > rtf_tolerance:
                mismatches.append(
                    Mismatch(
                        line_no=line_no,
                        field="rtf",
                        expected=f"{rtf_expected:.3f}",
                        actual=f"{rtf_logged:.3f}",
                    )
                )

        expected_math_field = expected_math(stt_ms, speech_ms)
        if math_field != expected_math_field:
            mismatches.append(
                Mismatch(
                    line_no=line_no,
                    field="math",
                    expected=expected_math_field,
                    actual=math_field,
                )
            )

        badge_rtf = rtf_logged if rtf_logged is not None else rtf_expected
        expected_badge_text = expected_badge(mode, stt_ms, badge_rtf)
        if badge != expected_badge_text:
            mismatches.append(
                Mismatch(
                    line_no=line_no,
                    field="badge",
                    expected=expected_badge_text,
                    actual=badge,
                )
            )

        if display_ms is None and stt_ms is not None:
            mismatches.append(
                Mismatch(
                    line_no=line_no,
                    field="display_ms_parse",
                    expected=str(stt_ms),
                    actual=fields.get("display_ms", "na"),
                )
            )

    if len(mismatches) > max_report:
        mismatches = mismatches[:max_report]
    return latency_line_count, mismatches


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate latency_audit log math and display fields."
    )
    parser.add_argument(
        "--log-path",
        type=Path,
        default=default_log_path(),
        help="Path to voiceterm log file (default: $TMPDIR/voiceterm_tui.log or /tmp/voiceterm_tui.log).",
    )
    parser.add_argument(
        "--rtf-tolerance",
        type=float,
        default=0.002,
        help="Allowed absolute delta between logged rtf and stt_ms/speech_ms.",
    )
    parser.add_argument(
        "--max-report",
        type=int,
        default=20,
        help="Maximum mismatch rows to print.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.log_path.exists():
        print(f"error: log file not found: {args.log_path}")
        return 2

    latency_lines, mismatches = audit_file(
        log_path=args.log_path,
        rtf_tolerance=args.rtf_tolerance,
        max_report=args.max_report,
    )

    if latency_lines == 0:
        print(f"error: no latency_audit lines found in {args.log_path}")
        return 2

    print(f"audited latency_audit lines: {latency_lines}")
    if mismatches:
        print(f"mismatches: {len(mismatches)}")
        for item in mismatches:
            print(
                f"line {item.line_no}: {item.field} expected={item.expected} actual={item.actual}"
            )
        return 1

    print("mismatches: 0")
    print("latency math and badge rendering are internally consistent with logged fields.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
