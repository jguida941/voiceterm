from __future__ import annotations

from pathlib import Path

from dev.scripts.checks.check_action_result_status_domain import (
    evaluate_action_result_status_domain,
)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_status_domain_scans_only_action_result_envelopes(tmp_path: Path) -> None:
    _write(
        tmp_path / "dev/scripts/devctl/runtime/sample.py",
        "\n".join(
            (
                "def helper():",
                "    return dict(status='blocked')",
                "result = ActionResult(",
                "    schema_version=1,",
                "    contract_id='ActionResult',",
                "    action_id='demo',",
                "    ok=False,",
                "    status='blocked',",
                ")",
            )
        ),
    )

    report = evaluate_action_result_status_domain(repo_root=tmp_path)

    assert report.violation_count == 1
    assert report.violations[0]["literal"] == "blocked"


def test_status_domain_accepts_action_result_fields_domain_value(
    tmp_path: Path,
) -> None:
    _write(
        tmp_path / "dev/scripts/devctl/runtime/sample.py",
        "fields = ActionResultFields(action_id='demo', ok=True, status='pass', reason='ok')\n",
    )

    report = evaluate_action_result_status_domain(repo_root=tmp_path)

    assert report.violation_count == 0

