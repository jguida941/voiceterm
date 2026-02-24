"""Shared release guard helpers for distribution commands."""

from __future__ import annotations

import json
import subprocess
from typing import Dict, Tuple

from ..config import REPO_ROOT
from ..script_catalog import check_script_cmd


def check_release_version_parity(expected_version: str) -> Tuple[bool, Dict]:
    """Validate release metadata parity and match it against an expected version."""
    cmd = check_script_cmd("release_version_parity", "--format", "json")
    result = subprocess.run(cmd, cwd=REPO_ROOT, text=True, capture_output=True)

    raw = (result.stdout or "").strip() or (result.stderr or "").strip()
    try:
        report = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        return (
            False,
            {
                "reason": "failed to parse release version parity output",
                "exit_code": result.returncode,
            },
        )

    versions = report.get("versions_present") or []
    missing = report.get("missing") or []
    if result.returncode != 0 or not report.get("ok"):
        return (
            False,
            {
                "reason": "release version parity check failed",
                "versions_present": ",".join(str(v) for v in versions) or "none",
                "missing": ",".join(str(v) for v in missing) or "none",
            },
        )

    if len(versions) != 1 or versions[0] != expected_version:
        return (
            False,
            {
                "reason": "requested version does not match release metadata",
                "requested": expected_version,
                "detected": ",".join(str(v) for v in versions) or "none",
            },
        )

    return True, {"version": expected_version}
