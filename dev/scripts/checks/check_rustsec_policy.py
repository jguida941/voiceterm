#!/usr/bin/env python3
"""Enforce RustSec policy thresholds from cargo-audit JSON output."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


SEVERITY_SCORES = {
    "critical": 9.0,
    "high": 7.0,
    "medium": 4.0,
    "low": 1.0,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Apply policy checks to cargo-audit JSON output. "
            "Fails on high/critical advisories and configured warning kinds."
        )
    )
    parser.add_argument("--input", required=True, help="Path to cargo-audit JSON output")
    parser.add_argument(
        "--min-cvss",
        type=float,
        default=7.0,
        help="Minimum CVSS score that fails the policy (default: 7.0)",
    )
    parser.add_argument(
        "--fail-on-kind",
        action="append",
        default=[],
        help=(
            "warning kind that should fail the policy (repeatable); "
            "defaults to yanked and unsound if omitted"
        ),
    )
    parser.add_argument(
        "--allow-advisory",
        action="append",
        default=[],
        help="Advisory ID to allowlist (repeatable)",
    )
    parser.add_argument(
        "--allowlist-file",
        help="Path to a newline-delimited advisory allowlist (# comments supported)",
    )
    parser.add_argument(
        "--allow-unknown-severity",
        action="store_true",
        help="Do not fail advisories that have no CVSS/severity metadata",
    )
    return parser.parse_args()


def load_payload(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"Input file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc


def advisory_from_item(item: object) -> dict:
    if not isinstance(item, dict):
        return {}
    advisory = item.get("advisory")
    if isinstance(advisory, dict):
        return advisory
    return item


def advisory_id(advisory: dict) -> str:
    value = advisory.get("id") or advisory.get("advisory_id") or "UNKNOWN"
    return str(value)


def package_name(item: object) -> str:
    if not isinstance(item, dict):
        return "unknown"
    package = item.get("package")
    if isinstance(package, dict):
        name = package.get("name")
        version = package.get("version")
        if name and version:
            return f"{name}@{version}"
        if name:
            return str(name)
    return "unknown"


def parse_cvss(advisory: dict) -> float | None:
    raw = advisory.get("cvss")
    if raw is None:
        raw = advisory.get("cvss_score")
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return None
        try:
            return float(text)
        except ValueError:
            match = re.search(r"([0-9]+(?:\.[0-9]+)?)", text)
            if match:
                return float(match.group(1))
    return None


def parse_severity(advisory: dict) -> float | None:
    severity = advisory.get("severity")
    if not isinstance(severity, str):
        return None
    return SEVERITY_SCORES.get(severity.strip().lower())


def warning_kind(item: object) -> str:
    if not isinstance(item, dict):
        return ""
    value = item.get("kind") or item.get("warning")
    if value is None:
        return ""
    return str(value).strip().lower()


def main() -> int:
    args = parse_args()
    payload = load_payload(Path(args.input))

    fail_kinds = {kind.strip().lower() for kind in args.fail_on_kind if kind.strip()}
    if not fail_kinds:
        fail_kinds = {"yanked", "unsound"}

    allowlist = {item.strip().upper() for item in args.allow_advisory if item.strip()}
    if args.allowlist_file:
        allowlist_path = Path(args.allowlist_file)
        try:
            for line in allowlist_path.read_text(encoding="utf-8").splitlines():
                line = line.split("#", 1)[0].strip()
                if line:
                    allowlist.add(line.upper())
        except FileNotFoundError as exc:
            raise SystemExit(f"Allowlist file not found: {allowlist_path}") from exc
    vulnerabilities = payload.get("vulnerabilities", {})
    vuln_list = vulnerabilities.get("list", [])
    warnings = payload.get("warnings", [])

    if not isinstance(vuln_list, list):
        raise SystemExit("cargo-audit JSON did not contain a vulnerabilities.list array")
    warning_items: list[object] = []
    if isinstance(warnings, list):
        warning_items = warnings
    elif isinstance(warnings, dict):
        for value in warnings.values():
            if isinstance(value, list):
                warning_items.extend(value)
    else:
        raise SystemExit("cargo-audit JSON did not contain a supported warnings structure")

    high_hits: list[str] = []
    warning_hits: list[str] = []

    for item in vuln_list:
        advisory = advisory_from_item(item)
        adv_id = advisory_id(advisory).upper()
        if adv_id in allowlist:
            continue

        cvss = parse_cvss(advisory)
        severity_score = cvss if cvss is not None else parse_severity(advisory)
        if severity_score is None and args.allow_unknown_severity:
            continue
        if severity_score is None or severity_score >= args.min_cvss:
            high_hits.append(
                f"{advisory_id(advisory)} ({package_name(item)}; score={severity_score})"
            )

    for item in warning_items:
        kind = warning_kind(item)
        if kind not in fail_kinds:
            continue
        advisory = advisory_from_item(item)
        adv_id = advisory_id(advisory).upper()
        if adv_id in allowlist:
            continue
        warning_hits.append(f"{kind}: {advisory_id(advisory)} ({package_name(item)})")

    print(
        "RustSec policy summary: "
        f"total_vulnerabilities={len(vuln_list)} "
        f"total_warnings={len(warning_items)} "
        f"high_or_unknown={len(high_hits)} "
        f"failing_warnings={len(warning_hits)}"
    )

    if high_hits:
        print(f"Failing vulnerabilities (threshold >= {args.min_cvss}):")
        for hit in high_hits:
            print(f"- {hit}")
    if warning_hits:
        print("Failing warning kinds:")
        for hit in warning_hits:
            print(f"- {hit}")

    if high_hits or warning_hits:
        return 1

    print("RustSec policy passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
