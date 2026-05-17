from __future__ import annotations

from pathlib import Path

from dev.scripts.checks.typed_enum_connectivity.command import build_report


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_policy_dict_keys_and_comparisons_connect_enum_members(tmp_path: Path) -> None:
    _write(
        tmp_path / "dev/scripts/devctl/runtime/demo_modes.py",
        """
from enum import Enum


class DemoMode(str, Enum):
    LOCAL = "local"
    REMOTE = "remote"


MODE_POLICY = {
    DemoMode.LOCAL.value: "local-policy",
    "remote": "remote-policy",
}
""",
    )

    report = build_report(
        repo_root=tmp_path,
        scan_roots=("dev/scripts/devctl",),
    )

    assert report.ok
    assert report.member_count == 2
    assert report.connected_count == 2
    assert report.disconnected_count == 0


def test_disconnected_enum_members_warn_by_default_and_can_fail(
    tmp_path: Path,
) -> None:
    _write(
        tmp_path / "dev/scripts/devctl/runtime/demo_status.py",
        """
from enum import Enum


class DemoStatus(str, Enum):
    ACTIVE = "active"
    STALE = "stale"


def is_active(raw: str) -> bool:
    return raw == "active"
""",
    )

    warning_report = build_report(
        repo_root=tmp_path,
        scan_roots=("dev/scripts/devctl",),
    )
    blocking_report = build_report(
        repo_root=tmp_path,
        scan_roots=("dev/scripts/devctl",),
        fail_on_disconnected=True,
    )

    assert warning_report.ok
    assert warning_report.mode == "warning_only"
    assert [member.member_name for member in warning_report.disconnected_members] == [
        "STALE"
    ]
    assert not blocking_report.ok
    assert blocking_report.mode == "blocking"
