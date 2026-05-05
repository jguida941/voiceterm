from __future__ import annotations

import json
from pathlib import Path

from dev.scripts.checks.memory_authority.checks import run_all_checks
from dev.scripts.checks.memory_authority.command import render_markdown


def _write_clean_repo(root: Path) -> None:
    (root / "dev" / "config").mkdir(parents=True)
    (root / "dev" / "active").mkdir(parents=True)
    (root / "dev" / "guides").mkdir(parents=True)
    (root / "AGENTS.md").write_text(
        "Memory files are short-term continuity only.\n",
        encoding="utf-8",
    )
    (root / "dev" / "config" / "devctl_repo_policy.json").write_text(
        json.dumps({
            "surfaces": [{
                "output_path": "dev/generated/surface.md",
                "template_path": "dev/templates/surface.template.md",
            }],
        }),
        encoding="utf-8",
    )


def test_memory_not_authority_accepts_repo_owned_sources(tmp_path: Path) -> None:
    _write_clean_repo(tmp_path)

    assert run_all_checks(tmp_path) == []


def test_memory_not_authority_rejects_policy_memory_output(tmp_path: Path) -> None:
    _write_clean_repo(tmp_path)
    policy_path = tmp_path / "dev" / "config" / "devctl_repo_policy.json"
    policy_path.write_text(
        json.dumps({"surfaces": [{"output_path": ".claude/projects/memory/rule.md"}]}),
        encoding="utf-8",
    )

    violations = run_all_checks(tmp_path)

    assert [violation["kind"] for violation in violations] == [
        "policy_points_at_memory",
    ]
    assert violations[0]["key"] == "output_path"


def test_memory_not_authority_rejects_memory_docs_as_rules(tmp_path: Path) -> None:
    _write_clean_repo(tmp_path)
    (tmp_path / "dev" / "guides" / "DEVELOPMENT.md").write_text(
        "Architecture rule lives in `memory/runtime-proof.md`.\n",
        encoding="utf-8",
    )

    violations = run_all_checks(tmp_path)

    assert [violation["kind"] for violation in violations] == [
        "doc_cites_memory_as_authority",
    ]
    assert "memory/runtime-proof.md" in str(violations[0]["match"])


def test_memory_not_authority_markdown_names_violations() -> None:
    rendered = render_markdown({
        "ok": False,
        "violations": [{
            "file": "dev/active/plan.md",
            "line": 7,
            "kind": "doc_cites_memory_as_authority",
            "match": "memory/foo.md",
            "hint": "move durable rule into AGENTS.md",
        }],
    })

    assert "# check_memory_not_authority" in rendered
    assert "doc_cites_memory_as_authority" in rendered
    assert "dev/active/plan.md:7" in rendered
