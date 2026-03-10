"""Shared utility helpers for `devctl autonomy-benchmark`."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .swarm_helpers import fallback_repo_from_origin, resolve_path, slug
from ..common import display_path
from ..config import REPO_ROOT
from ..numeric import to_int

SUPPORTED_TACTICS = ("uniform", "specialized", "research-first", "test-first")


def repo_relative(path: Path) -> str:
    return display_path(path, repo_root=REPO_ROOT)


def parse_swarm_counts(raw: str) -> list[int]:
    counts: list[int] = []
    for part in str(raw or "").split(","):
        text = part.strip()
        if not text:
            continue
        value = to_int(text, default=0)
        if value > 0:
            counts.append(value)
    return sorted(set(counts))


def parse_tactics(raw: str) -> tuple[list[str], list[str]]:
    warnings: list[str] = []
    rows: list[str] = []
    for part in str(raw or "").split(","):
        text = part.strip().lower()
        if not text:
            continue
        if text in SUPPORTED_TACTICS:
            rows.append(text)
        else:
            warnings.append(f"unsupported tactic ignored: {text}")
    return sorted(set(rows)), warnings


def explicit_question(args) -> str:
    question = str(args.question or "").strip()
    question_file = str(args.question_file or "").strip()
    if question_file:
        path = resolve_path(question_file)
        try:
            question = path.read_text(encoding="utf-8").strip()
        except OSError:
            return question
    return question


def validate_plan_scope(
    *, plan_doc: Path, index_doc: Path, master_plan_doc: Path, mp_scope: str
) -> tuple[str, str, str, list[str], list[str]]:
    plan_text = plan_doc.read_text(encoding="utf-8")
    index_text = index_doc.read_text(encoding="utf-8")
    master_text = master_plan_doc.read_text(encoding="utf-8")
    plan_rel = repo_relative(plan_doc)

    warnings: list[str] = []
    errors: list[str] = []
    plan_tokens = {plan_rel, str(plan_doc), plan_doc.name}
    if not any(token and token in index_text for token in plan_tokens):
        errors.append(f"active index does not reference plan doc path: {plan_rel}")
    if mp_scope not in master_text:
        errors.append(f"MASTER_PLAN does not contain scope token: {mp_scope}")
    if mp_scope not in index_text:
        warnings.append(f"INDEX does not explicitly mention scope token: {mp_scope}")
    return plan_text, index_text, plan_rel, warnings, errors


def load_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None
