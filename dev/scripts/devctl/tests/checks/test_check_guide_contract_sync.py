"""Tests for the guide-contract sync guard."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from dev.scripts.checks.guide_contract_sync import command as guide_contract_sync


def test_guide_contract_sync_passes_current_repo_policy() -> None:
    report = guide_contract_sync.build_report()
    assert report["ok"] is True
    assert report["violations"] == []


def test_guide_contract_sync_flags_missing_required_tokens(tmp_path: Path) -> None:
    guide_path = tmp_path / "guide.md"
    guide_path.write_text("# guide\n", encoding="utf-8")
    policy_payload = {
        "guide_contract_rules": [
            {
                "id": "guide-rule",
                "doc_path": "guide.md",
                "required_contains": ["quality-policy", "platform-contracts"],
            }
        ]
    }
    with (
        patch.object(guide_contract_sync, "REPO_ROOT", tmp_path),
        patch.object(
            guide_contract_sync,
            "load_repo_governance_section",
            return_value=(policy_payload, [], tmp_path / "policy.json"),
        ),
        patch.object(
            guide_contract_sync,
            "display_path",
            side_effect=lambda path, repo_root: Path(path).name,
        ),
    ):
        report = guide_contract_sync.build_report()

    assert report["ok"] is False
    assert report["violations"][0]["rule_id"] == "guide-rule"
    assert report["violations"][0]["missing_contains"] == [
        "quality-policy",
        "platform-contracts",
    ]
    assert report["violations"][0]["section_violations"] == []


def test_guide_contract_sync_flags_missing_section_tokens(tmp_path: Path) -> None:
    guide_path = tmp_path / "guide.md"
    guide_path.write_text(
        "## System Coverage Map\n\n- quality-policy\n",
        encoding="utf-8",
    )
    policy_payload = {
        "guide_contract_rules": [
            {
                "id": "guide-rule",
                "doc_path": "guide.md",
                "required_contains": ["## System Coverage Map"],
                "required_sections": [
                    {
                        "heading": "System Coverage Map",
                        "required_contains": ["quality-policy", "review-channel"],
                    }
                ],
            }
        ]
    }
    with (
        patch.object(guide_contract_sync, "REPO_ROOT", tmp_path),
        patch.object(
            guide_contract_sync,
            "load_repo_governance_section",
            return_value=(policy_payload, [], tmp_path / "policy.json"),
        ),
        patch.object(
            guide_contract_sync,
            "display_path",
            side_effect=lambda path, repo_root: Path(path).name,
        ),
    ):
        report = guide_contract_sync.build_report()

    assert report["ok"] is False
    assert report["violations"][0]["missing_contains"] == []
    assert report["violations"][0]["section_violations"] == [
        {
            "heading": "System Coverage Map",
            "missing_contains": ["review-channel"],
            "error": None,
        }
    ]


def test_guide_contract_sync_flags_missing_section_heading(tmp_path: Path) -> None:
    guide_path = tmp_path / "guide.md"
    guide_path.write_text("# guide\n", encoding="utf-8")
    policy_payload = {
        "guide_contract_rules": [
            {
                "id": "guide-rule",
                "doc_path": "guide.md",
                "required_contains": [],
                "required_sections": [
                    {
                        "heading": "System Coverage Map",
                        "required_contains": ["quality-policy"],
                    }
                ],
            }
        ]
    }
    with (
        patch.object(guide_contract_sync, "REPO_ROOT", tmp_path),
        patch.object(
            guide_contract_sync,
            "load_repo_governance_section",
            return_value=(policy_payload, [], tmp_path / "policy.json"),
        ),
        patch.object(
            guide_contract_sync,
            "display_path",
            side_effect=lambda path, repo_root: Path(path).name,
        ),
    ):
        report = guide_contract_sync.build_report()

    assert report["ok"] is False
    assert report["violations"][0]["section_violations"] == [
        {
            "heading": "System Coverage Map",
            "missing_contains": ["quality-policy"],
            "error": "missing heading",
        }
    ]


def test_guide_contract_sync_markdown_lists_missing_tokens() -> None:
    output = guide_contract_sync.render_md(
        {
            "command": "check_guide_contract_sync",
            "ok": False,
            "policy_path": "policy.json",
            "checked_rule_count": 1,
            "warnings": [],
            "violations": [
                {
                    "rule_id": "guide-rule",
                    "doc_path": "dev/guides/DEVCTL_AUTOGUIDE.md",
                    "missing_contains": ["quality-policy"],
                    "section_violations": [
                        {
                            "heading": "System Coverage Map",
                            "missing_contains": ["review-channel"],
                            "error": None,
                        }
                    ],
                }
            ],
        }
    )
    assert "# check_guide_contract_sync" in output
    assert "quality-policy" in output
    assert "System Coverage Map" in output
    assert "review-channel" in output
