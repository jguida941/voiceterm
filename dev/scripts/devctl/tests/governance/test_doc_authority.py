"""Tests for `devctl.governance.doc_authority` scanner and report."""

from __future__ import annotations

from pathlib import Path

import pytest

from dev.scripts.devctl.governance.doc_authority import (
    DocRecord,
    DocRegistryReport,
    GovernedDocLayout,
    build_doc_authority_report,
    check_budget,
    classify_doc,
    detect_authority_overlaps,
    detect_consolidation_candidates,
    parse_index_registry,
    parse_metadata_header,
    render_doc_authority_md,
)


# --- parse_metadata_header ---


def test_parse_metadata_header_bold_format() -> None:
    text = (
        "# My Plan\n\n"
        "**Status**: active  |  **Last updated**: 2026-03-20 | **Owner:** tooling/governance\n"
    )
    meta = parse_metadata_header(text)
    assert "active" in meta["status"]
    assert "2026-03-20" in meta["updated"]
    assert "tooling/governance" in meta["owner"]


def test_parse_metadata_header_plain_format() -> None:
    text = (
        "# Review Channel\n\n"
        "Status: execution mirrored in MASTER_PLAN.md (MP-355)\n"
    )
    meta = parse_metadata_header(text)
    assert "execution" in meta["status"].lower() or "mirrored" in meta["status"].lower()


def test_parse_metadata_header_missing() -> None:
    text = "# Just a Title\n\nSome body text without metadata.\n"
    meta = parse_metadata_header(text)
    assert meta == {}


# --- classify_doc ---


def test_classify_doc_spec(tmp_path: Path) -> None:
    doc = tmp_path / "plan.md"
    doc.write_text(
        "# Plan\n## Scope\nStuff\n## Execution Checklist\n- [ ] item\n\n## Session Resume\n- resume\n"
    )
    result = classify_doc(doc, doc.read_text(), in_active=True)
    assert result == "spec"


def test_classify_doc_guide(tmp_path: Path) -> None:
    doc = tmp_path / "dev" / "guides" / "GUIDE.md"
    doc.parent.mkdir(parents=True)
    doc.write_text("# Guide\nReference content.\n")
    result = classify_doc(doc, doc.read_text(), in_active=False)
    assert result == "guide"


def test_classify_doc_reference_small(tmp_path: Path) -> None:
    doc = tmp_path / "stub.md"
    doc.write_text("# Stub\nBridge to elsewhere.\n")
    result = classify_doc(doc, doc.read_text(), in_active=True)
    assert result == "reference"


def test_classify_doc_index(tmp_path: Path) -> None:
    doc = tmp_path / "INDEX.md"
    doc.write_text("# Index\n| col |\n")
    result = classify_doc(doc, doc.read_text(), in_active=True)
    assert result == "reference"


def test_classify_doc_master_plan(tmp_path: Path) -> None:
    doc = tmp_path / "MASTER_PLAN.md"
    doc.write_text("# Master Plan\n## Status\nStuff\n")
    layout = GovernedDocLayout(
        repo_root=tmp_path,
        active_docs_root="dev/active",
        guides_root="dev/guides",
        governed_doc_roots=("dev/active", "dev/guides"),
        index_path="dev/active/INDEX.md",
        tracker_path="MASTER_PLAN.md",
        docs_authority_path="AGENTS.md",
        bridge_path="bridge.md",
        root_files=(),
    )
    result = classify_doc(
        doc,
        doc.read_text(),
        in_active=True,
        rel="MASTER_PLAN.md",
        layout=layout,
    )
    assert result == "tracker"


def test_classify_doc_root_guide_is_guide(tmp_path: Path) -> None:
    doc = tmp_path / "ROOT_GUIDE.md"
    doc.write_text("# Root Guide\n")
    layout = GovernedDocLayout(
        repo_root=tmp_path,
        active_docs_root="dev/active",
        guides_root="dev/guides",
        governed_doc_roots=("dev/active", "dev/guides"),
        index_path="dev/active/INDEX.md",
        tracker_path="dev/active/MASTER_PLAN.md",
        docs_authority_path="AGENTS.md",
        bridge_path="bridge.md",
        root_files=("ROOT_GUIDE.md",),
    )
    result = classify_doc(
        doc,
        doc.read_text(),
        in_active=False,
        rel="ROOT_GUIDE.md",
        layout=layout,
    )
    assert result == "guide"


# --- check_budget ---


def test_check_budget_ok() -> None:
    status, limit = check_budget(500, "spec")
    assert status == "ok"


def test_check_budget_warning() -> None:
    status, limit = check_budget(1500, "spec")
    assert status == "warning"
    assert limit == 1200


def test_check_budget_exceeded() -> None:
    status, limit = check_budget(2500, "spec")
    assert status == "exceeded"
    assert limit == 2000


def test_check_budget_no_limit() -> None:
    status, _ = check_budget(10000, "tracker")
    assert status == "ok"


# --- parse_index_registry ---


def test_parse_index_registry(tmp_path: Path) -> None:
    index = tmp_path / "INDEX.md"
    index.write_text(
        "| Doc | Role | Authority | Scope | When |\n"
        "|---|---|---|---|---|\n"
        "| `plan.md` | `spec` | `mirrored` | MP-377 | when editing platform |\n"
    )
    reg = parse_index_registry(index)
    assert "plan.md" in reg
    assert reg["plan.md"]["role"] == "spec"
    assert reg["plan.md"]["authority"] == "mirrored"


def test_parse_index_registry_missing_file(tmp_path: Path) -> None:
    reg = parse_index_registry(tmp_path / "nonexistent.md")
    assert reg == {}


# --- detect_authority_overlaps ---


def _make_record(**kwargs) -> DocRecord:
    defaults = {
        "path": "test.md",
        "doc_class": "spec",
        "owner": "",
        "authority": "",
        "lifecycle": "active",
        "scope": "",
        "canonical_consumer": "",
        "line_count": 100,
        "budget_status": "ok",
        "budget_limit": 1200,
        "has_metadata_header": True,
        "has_required_sections": True,
        "missing_sections": (),
        "registry_managed": True,
        "in_index": True,
        "issues": (),
        "consolidation_signals": (),
    }
    defaults.update(kwargs)
    return DocRecord(**defaults)


def test_detect_overlaps_same_mp() -> None:
    records = [
        _make_record(path="a.md", scope="MP-377 platform"),
        _make_record(path="b.md", scope="MP-377 authority loop"),
    ]
    overlaps = detect_authority_overlaps(records)
    assert len(overlaps) == 1
    assert overlaps[0]["mp"] == "MP-377"
    assert set(overlaps[0]["docs"]) == {"a.md", "b.md"}


def test_detect_overlaps_no_overlap() -> None:
    records = [
        _make_record(path="a.md", scope="MP-376"),
        _make_record(path="b.md", scope="MP-377"),
    ]
    overlaps = detect_authority_overlaps(records)
    assert overlaps == []


# --- detect_consolidation_candidates ---


def test_detect_consolidation_complete_lifecycle() -> None:
    records = [
        _make_record(
            path="done.md",
            lifecycle="complete",
            consolidation_signals=("lifecycle complete — candidate for archive",),
        ),
    ]
    candidates = detect_consolidation_candidates(records)
    assert len(candidates) == 1
    assert candidates[0]["path"] == "done.md"


def test_detect_consolidation_tiny_reference() -> None:
    records = [
        _make_record(
            path="stub.md",
            doc_class="reference",
            line_count=20,
            consolidation_signals=("tiny reference doc — consider inlining",),
        ),
    ]
    candidates = detect_consolidation_candidates(records)
    assert len(candidates) == 1


def test_detect_consolidation_no_signals() -> None:
    records = [_make_record(path="healthy.md")]
    candidates = detect_consolidation_candidates(records)
    assert candidates == []


# --- build_doc_authority_report ---


def test_build_report_on_empty_repo(tmp_path: Path) -> None:
    report = build_doc_authority_report(tmp_path)
    assert report.command == "doc-authority"
    assert report.total_governed_docs == 0
    assert report.total_lines == 0
    assert report.registry_counts["managed_active_docs"] == 0


def test_build_report_with_active_docs(tmp_path: Path) -> None:
    active = tmp_path / "dev" / "active"
    active.mkdir(parents=True)
    (active / "INDEX.md").write_text(
        "# Index\n\n"
        "| Path | Role | Execution authority | MP scope | When agents read |\n"
        "|---|---|---|---|---|\n"
        "| `dev/active/plan.md` | `spec` | `mirrored` | `MP-377` | when editing platform |\n"
    )
    plan = active / "plan.md"
    plan.write_text(
        "# Plan\n\n"
        "**Status**: active  |  **Last updated**: 2026-03-20 | **Owner:** tooling/governance\n\n"
        "## Scope\nDo things.\n\n"
        "## Execution Checklist\n- [ ] item\n\n"
        "## Progress Log\nNone yet.\n\n"
        "## Session Resume\n- resume\n\n"
        "## Audit Evidence\nNone yet.\n"
    )
    report = build_doc_authority_report(tmp_path)
    assert report.total_governed_docs >= 2
    assert report.command == "doc-authority"
    assert isinstance(report.timestamp_utc, str)
    plan_record = next(record for record in report.records if record.path == "dev/active/plan.md")
    assert plan_record.doc_class == "spec"
    assert report.registry_counts["managed_active_docs"] == 1
    assert report.registry_counts["registered_active_docs"] == 1
    assert report.registry_coverage == 1.0


def test_build_report_uses_index_role_for_runbook(tmp_path: Path) -> None:
    active = tmp_path / "dev" / "active"
    active.mkdir(parents=True)
    (active / "INDEX.md").write_text(
        "# Index\n\n"
        "| Path | Role | Execution authority | MP scope | When agents read |\n"
        "|---|---|---|---|---|\n"
        "| `dev/active/loop_chat_bridge.md` | `runbook` | `supporting` | `MP-338` | when coordinating bridge flow |\n"
    )
    (active / "loop_chat_bridge.md").write_text(
        "# Loop Chat Bridge\n\n"
        "Status: execution mirrored in MASTER_PLAN.md (MP-338)\n\n"
        "## Scope\nBridge.\n\n"
        "## Execution Checklist\n- [ ] step\n\n"
        "## Progress Log\n- none\n\n"
        "## Session Resume\n- resume\n\n"
        "## Audit Evidence\n- none\n"
    )
    report = build_doc_authority_report(tmp_path)
    record = next(
        entry for entry in report.records if entry.path == "dev/active/loop_chat_bridge.md"
    )
    assert record.doc_class == "runbook"


def test_build_report_registry_counts_only_active_subset(tmp_path: Path) -> None:
    active = tmp_path / "dev" / "active"
    guides = tmp_path / "dev" / "guides"
    active.mkdir(parents=True)
    guides.mkdir(parents=True)
    (active / "INDEX.md").write_text(
        "# Index\n\n"
        "| Path | Role | Execution authority | MP scope | When agents read |\n"
        "|---|---|---|---|---|\n"
        "| `dev/active/registered.md` | `spec` | `mirrored` | `MP-377` | when editing platform |\n"
    )
    (active / "registered.md").write_text(
        "# Registered\n\n## Scope\nText\n\n## Execution Checklist\n- [ ] item\n\n## Progress Log\n- none\n\n## Session Resume\n- resume\n\n## Audit Evidence\n- none\n"
    )
    (active / "missing.md").write_text(
        "# Missing\n\n## Scope\nText\n\n## Execution Checklist\n- [ ] item\n\n## Progress Log\n- none\n\n## Session Resume\n- resume\n\n## Audit Evidence\n- none\n"
    )
    (guides / "GUIDE.md").write_text("# Guide\n")
    report = build_doc_authority_report(tmp_path)
    assert report.registry_counts == {
        "managed_active_docs": 2,
        "registered_active_docs": 1,
        "missing_active_docs": 1,
        "non_index_governed_docs": 2,
    }
    assert report.registry_coverage == 0.5


def test_build_report_classifies_agents_as_guide(tmp_path: Path) -> None:
    (tmp_path / "AGENTS.md").write_text("# Agents\n")
    report = build_doc_authority_report(tmp_path)
    record = next(entry for entry in report.records if entry.path == "AGENTS.md")
    assert record.doc_class == "guide"


def test_build_report_classifies_code_audit_as_generated_report(tmp_path: Path) -> None:
    (tmp_path / "bridge.md").write_text("# Audit\n")
    report = build_doc_authority_report(tmp_path)
    record = next(entry for entry in report.records if entry.path == "bridge.md")
    assert record.doc_class == "generated_report"


# --- report output shapes ---


def test_report_json_shape(tmp_path: Path) -> None:
    report = build_doc_authority_report(tmp_path)
    payload = report.to_dict()
    assert payload["command"] == "doc-authority"
    assert "total_governed_docs" in payload
    assert "total_lines" in payload
    assert "by_class" in payload
    assert "by_lifecycle" in payload
    assert "registry_coverage" in payload
    assert "registry_counts" in payload
    assert "budget_violations" in payload
    assert "authority_overlaps" in payload
    assert "consolidation_candidates" in payload
    assert "records" in payload


def test_report_md_renders(tmp_path: Path) -> None:
    report = build_doc_authority_report(tmp_path)
    md = render_doc_authority_md(report)
    assert "# doc-authority" in md
    assert "## Summary" in md
    assert "## By Class" in md
    assert "## Doc Registry" in md
    assert "Registered" in md


# --- CLI integration ---


def test_cli_parser_registration() -> None:
    from dev.scripts.devctl.cli import build_parser

    parser = build_parser()
    args = parser.parse_args(
        ["doc-authority", "--format", "json", "--quality-policy", "policy.json"]
    )
    assert getattr(args, "format", None) == "json"
    assert getattr(args, "quality_policy", None) == "policy.json"


def test_listing_includes_doc_authority() -> None:
    from dev.scripts.devctl.commands.listing import COMMANDS

    assert "doc-authority" in COMMANDS
