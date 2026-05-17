"""Three narrow checks that enforce the memory-not-authority contract.

Public API:
  - run_all_checks(repo_root): returns the violation list aggregated across
    policy, AGENTS.md, and dev/active+dev/guides docs.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

POLICY_PATH = "dev/config/devctl_repo_policy.json"
AGENTS_PATH = "AGENTS.md"
DOC_SCAN_DIRS = ("dev/active", "dev/guides")
POLICY_PATH_KEYS = ("output_path", "template_path", "source_authority")
MEMORY_PATH_TOKENS = ("/.claude/projects/", ".claude/projects/", "/memory/", "claude/memory/")
AUTHORITY_TOKENS = ("architecture", "policy", "rule", "rules", "contract", "contracts")
MEMORY_REF_PATTERN = re.compile(r"`?(?:[\w./-]*?/)?memory/[\w./-]+\.md`?", re.IGNORECASE)


def _path_for_report(repo_root: Path, path: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def _looks_like_memory_path(value: str) -> bool:
    lowered = value.lower()
    return any(token in lowered for token in MEMORY_PATH_TOKENS)


def _walk_policy_paths(node: object, trail: tuple[str, ...] = ()) -> list[tuple[str, str, str]]:
    """Yield (key, dotted-trail, value) for every memory-pointing policy key."""
    hits: list[tuple[str, str, str]] = []
    if isinstance(node, dict):
        for key, value in node.items():
            child_trail = trail + (str(key),)
            if key in POLICY_PATH_KEYS and isinstance(value, str) and _looks_like_memory_path(value):
                hits.append((key, ".".join(child_trail), value))
            hits.extend(_walk_policy_paths(value, child_trail))
    elif isinstance(node, list):
        for index, item in enumerate(node):
            hits.extend(_walk_policy_paths(item, trail + (f"[{index}]",)))
    return hits


def _check_policy(repo_root: Path) -> list[dict[str, object]]:
    path = repo_root / POLICY_PATH
    if not path.exists():
        return [{"file": POLICY_PATH, "kind": "policy_missing", "hint": "policy file not found"}]
    try:
        policy = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [{"file": POLICY_PATH, "kind": "policy_unreadable", "hint": str(exc)}]
    return [
        {
            "file": POLICY_PATH,
            "kind": "policy_points_at_memory",
            "key": key,
            "trail": trail,
            "value": value,
            "hint": (
                f"{key} at {trail} resolves under operator memory; "
                "memory must not be a tracked output or template source."
            ),
        }
        for key, trail, value in _walk_policy_paths(policy)
    ]


def _check_agents_rule(repo_root: Path) -> list[dict[str, object]]:
    path = repo_root / AGENTS_PATH
    if not path.exists():
        return [{"file": AGENTS_PATH, "kind": "agents_missing", "hint": "AGENTS.md not found"}]
    text = path.read_text(encoding="utf-8").lower()
    if "memory" in text and ("continuity" in text or "short-term" in text):
        return []
    return [{
        "file": AGENTS_PATH,
        "kind": "agents_rule_missing",
        "hint": "AGENTS.md missing canonical 'memory is short-term continuity' rule.",
    }]


def _scan_doc(repo_root: Path, md_path: Path) -> list[dict[str, object]]:
    try:
        lines = md_path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return [{
            "file": _path_for_report(repo_root, md_path), "line": 0,
            "kind": "doc_unreadable", "hint": str(exc),
        }]
    out: list[dict[str, object]] = []
    for lineno, line in enumerate(lines, start=1):
        lowered = line.lower()
        if not any(token in lowered for token in AUTHORITY_TOKENS):
            continue
        for match in MEMORY_REF_PATTERN.finditer(line):
            out.append({
                "file": _path_for_report(repo_root, md_path),
                "line": lineno,
                "kind": "doc_cites_memory_as_authority",
                "match": match.group(0),
                "hint": (
                    "memory/*.md cited alongside authority token; "
                    "move durable rule into AGENTS.md or repo-owned doc."
                ),
            })
    return out


def _check_docs(repo_root: Path) -> list[dict[str, object]]:
    violations: list[dict[str, object]] = []
    for relative in DOC_SCAN_DIRS:
        root = repo_root / relative
        if not root.exists():
            continue
        for md_path in sorted(root.rglob("*.md")):
            violations.extend(_scan_doc(repo_root, md_path))
    return violations


def run_all_checks(repo_root: Path) -> list[dict[str, object]]:
    """Aggregate violations from policy, AGENTS, and docs scans."""
    return [
        *_check_policy(repo_root),
        *_check_agents_rule(repo_root),
        *_check_docs(repo_root),
    ]
