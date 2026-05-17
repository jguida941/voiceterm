import json
from pathlib import Path

from dev.scripts.checks.repo_portability import build_report


def _write_policy(tmp_path: Path, target_path: str) -> Path:
    path = tmp_path / "dev/config/devctl_repo_policy.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "repo_governance": {
                    "repo_portability": {
                        "target_paths": [target_path],
                        "ignore_paths": ["__pycache__"],
                        "project_name_literals": ["VoiceTerm"],
                        "operator_identity_literals": ["jguida941"],
                        "allowed_literals": {},
                    }
                },
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return path


def test_repo_portability_guard_flags_packet_and_timestamp_literals(
    tmp_path: Path,
) -> None:
    source = tmp_path / "dev/scripts/checks/example_guard.py"
    source.parent.mkdir(parents=True)
    source.write_text(
        'MANDATE_PACKET_ID = "rev_pkt_4017"\n'
        'MANDATE_OBSERVED_AT_UTC = "2026-05-14T15:37:25Z"\n',
        encoding="utf-8",
    )
    _write_policy(tmp_path, "dev/scripts/checks/example_guard.py")

    report = build_report(repo_root=tmp_path)

    assert report["ok"] is False
    assert report["finding_count"] == 2
    assert report["category_counts"] == {
        "packet_id_literal": 1,
        "session_timestamp_literal": 1,
    }


def test_repo_portability_guard_accepts_policy_lookup(
    tmp_path: Path,
) -> None:
    source = tmp_path / "dev/scripts/checks/example_guard.py"
    source.parent.mkdir(parents=True)
    source.write_text(
        "from dev.scripts.devctl.runtime.repo_portability import resolve_guard_mandate\n"
        'mandate = resolve_guard_mandate("check_example", repo_root=repo_root)\n',
        encoding="utf-8",
    )
    _write_policy(tmp_path, "dev/scripts/checks/example_guard.py")

    report = build_report(repo_root=tmp_path)

    assert report["ok"] is True
    assert report["finding_count"] == 0


def test_repo_portability_guard_flags_project_name_literals(
    tmp_path: Path,
) -> None:
    source = tmp_path / "dev/scripts/checks/example_guard.py"
    source.parent.mkdir(parents=True)
    source.write_text('PRODUCT_NAME = "VoiceTerm"\n', encoding="utf-8")
    _write_policy(tmp_path, "dev/scripts/checks/example_guard.py")

    report = build_report(repo_root=tmp_path)

    assert report["ok"] is False
    assert report["category_counts"] == {"project_name_literal": 1}
