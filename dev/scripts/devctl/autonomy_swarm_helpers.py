"""Planning/render helpers for `devctl autonomy-swarm`."""

from __future__ import annotations

import math
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .autonomy_swarm_render import render_swarm_markdown
from .config import REPO_ROOT

KEYWORDS = (
    "refactor",
    "migration",
    "architecture",
    "unsafe",
    "workspace",
    "concurrency",
    "parser",
    "security",
    "release",
    "performance",
)


def iso_z(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def slug(value: str, *, fallback: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip()).strip("-._")
    return (normalized or fallback)[:80]


def resolve_path(raw_path: str) -> Path:
    path = Path(raw_path).expanduser()
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _question_text(
    question: str | None, question_file: str | None
) -> tuple[str, list[str]]:
    warnings: list[str] = []
    text = str(question or "").strip()
    file_path = str(question_file or "").strip()
    if file_path:
        path = resolve_path(file_path)
        try:
            text = path.read_text(encoding="utf-8").strip()
        except OSError as exc:
            warnings.append(f"question file read failed ({path}): {exc}")
    return text, warnings


def _diff_stats(
    diff_ref: str | None, target_paths: list[str]
) -> tuple[int, int, int, list[str]]:
    warnings: list[str] = []
    ranges: list[list[str]] = []

    if diff_ref:
        ranges.append(["git", "diff", "--numstat", f"{diff_ref}...HEAD"])
    ranges.append(["git", "diff", "--numstat", "HEAD"])

    for index, command in enumerate(ranges):
        full_command = list(command)
        if target_paths:
            full_command.extend(["--", *target_paths])
        result = subprocess.run(
            full_command, cwd=REPO_ROOT, text=True, capture_output=True, check=False
        )
        if result.returncode != 0:
            warning = (result.stderr or result.stdout or "git diff failed").strip()
            warnings.append(f"{' '.join(command[:3])}: {warning}")
            continue

        files = 0
        added = 0
        deleted = 0
        for line in result.stdout.splitlines():
            row = line.strip()
            if not row:
                continue
            parts = row.split("\t")
            if len(parts) < 3:
                continue
            files += 1
            add_text, del_text = parts[0], parts[1]
            if add_text.isdigit():
                added += int(add_text)
            if del_text.isdigit():
                deleted += int(del_text)
        # If commit-range diff is empty, fall back to working-tree diff so active
        # in-flight refactors still influence swarm sizing.
        if files > 0 or added > 0 or deleted > 0 or index == len(ranges) - 1:
            return files, added, deleted, warnings

    return 0, 0, 0, warnings


def collect_refactor_metadata(args) -> tuple[dict[str, Any], list[str]]:
    question_text, question_warnings = _question_text(args.question, args.question_file)
    files, added, deleted, diff_warnings = _diff_stats(
        args.diff_ref, list(args.target_paths or [])
    )

    hits = []
    lower_question = question_text.lower()
    for keyword in KEYWORDS:
        if keyword in lower_question:
            hits.append(keyword)

    question_chars = len(question_text)
    question_words = len([row for row in re.split(r"\s+", question_text) if row])
    estimated_prompt_tokens = max(1, question_chars // 4) if question_chars else 0
    prompt_tokens = _safe_int(args.prompt_tokens, default=estimated_prompt_tokens)
    if prompt_tokens <= 0:
        prompt_tokens = estimated_prompt_tokens

    metadata = {
        "question_chars": question_chars,
        "question_words": question_words,
        "prompt_tokens": prompt_tokens,
        "difficulty_hits": hits,
        "files_changed": files,
        "lines_added": added,
        "lines_deleted": deleted,
        "lines_changed": added + deleted,
        "target_paths": list(args.target_paths or []),
        "diff_ref": str(args.diff_ref or ""),
    }
    warnings = question_warnings + diff_warnings
    return metadata, warnings


def recommend_agent_count(
    metadata: dict[str, Any], args
) -> tuple[int, list[str], dict[str, float | int | None]]:
    min_agents = max(1, _safe_int(args.min_agents, default=1))
    max_agents = max(min_agents, _safe_int(args.max_agents, default=20))

    if args.agents is not None:
        explicit = max(
            min_agents, min(max_agents, _safe_int(args.agents, default=min_agents))
        )
        rationale = [f"explicit --agents={explicit} override"]
        components = {
            "base": 1.0,
            "lines_factor": 0.0,
            "files_factor": 0.0,
            "difficulty_factor": 0.0,
            "prompt_factor": 0.0,
            "raw_score": float(explicit),
            "token_cap": None,
        }
        return explicit, rationale, components

    if not bool(args.adaptive):
        rationale = ["adaptive mode disabled; using minimum agents"]
        components = {
            "base": 1.0,
            "lines_factor": 0.0,
            "files_factor": 0.0,
            "difficulty_factor": 0.0,
            "prompt_factor": 0.0,
            "raw_score": float(min_agents),
            "token_cap": None,
        }
        return min_agents, rationale, components

    lines_changed = _safe_int(metadata.get("lines_changed"), default=0)
    files_changed = _safe_int(metadata.get("files_changed"), default=0)
    difficulty_hits = (
        metadata.get("difficulty_hits")
        if isinstance(metadata.get("difficulty_hits"), list)
        else []
    )
    prompt_tokens = _safe_int(metadata.get("prompt_tokens"), default=0)

    lines_factor = min(6.0, lines_changed / 1200.0)
    files_factor = min(4.0, files_changed / 10.0)
    difficulty_factor = min(3.0, len(difficulty_hits) * 0.7)
    prompt_factor = min(4.0, prompt_tokens / 7000.0)
    raw_score = 1.0 + lines_factor + files_factor + difficulty_factor + prompt_factor

    recommended = int(math.ceil(raw_score))
    token_cap: int | None = None
    token_budget = _safe_int(args.token_budget, default=0)
    per_agent_cost = max(1, _safe_int(args.per_agent_token_cost, default=12000))
    if token_budget > 0:
        token_cap = max(min_agents, token_budget // per_agent_cost)
        recommended = min(recommended, token_cap)

    recommended = max(min_agents, min(max_agents, recommended))

    rationale = [
        f"lines_changed={lines_changed} -> +{round(lines_factor, 2)}",
        f"files_changed={files_changed} -> +{round(files_factor, 2)}",
        f"difficulty_hits={len(difficulty_hits)} -> +{round(difficulty_factor, 2)}",
        f"prompt_tokens={prompt_tokens} -> +{round(prompt_factor, 2)}",
        f"raw_score={round(raw_score, 2)} => recommended={recommended}",
    ]
    if token_cap is not None:
        rationale.append(
            f"token_budget={token_budget}, per_agent_token_cost={per_agent_cost}, token_cap={token_cap}"
        )

    components = {
        "base": 1.0,
        "lines_factor": round(lines_factor, 4),
        "files_factor": round(files_factor, 4),
        "difficulty_factor": round(difficulty_factor, 4),
        "prompt_factor": round(prompt_factor, 4),
        "raw_score": round(raw_score, 4),
        "token_cap": token_cap,
    }
    return recommended, rationale, components


def build_swarm_charts(
    report: dict[str, Any], chart_dir: Path
) -> tuple[list[str], str | None]:
    try:
        import matplotlib.pyplot as plt  # type: ignore
    except Exception as exc:
        return [], f"matplotlib unavailable: {exc}"

    chart_dir.mkdir(parents=True, exist_ok=True)
    chart_paths: list[str] = []

    agents = report.get("agents") if isinstance(report.get("agents"), list) else []
    if agents:
        labels = [str(row.get("agent") or "?") for row in agents]
        ok_values = [1 if bool(row.get("ok")) else 0 for row in agents]
        resolved_values = [1 if bool(row.get("resolved")) else 0 for row in agents]

        status_chart = chart_dir / "swarm_agent_status.png"
        figure = plt.figure(figsize=(10, 4.8))
        axis = figure.add_subplot(111)
        positions = list(range(len(labels)))
        axis.bar(positions, ok_values, width=0.45, label="ok")
        axis.bar(
            [idx + 0.45 for idx in positions],
            resolved_values,
            width=0.45,
            label="resolved",
        )
        axis.set_title("Autonomy Swarm Agent Status")
        axis.set_ylim(0, 1.1)
        axis.set_xticks(
            [idx + 0.225 for idx in positions], labels, rotation=45, ha="right"
        )
        axis.legend()
        figure.tight_layout()
        figure.savefig(status_chart, dpi=150)
        plt.close(figure)
        chart_paths.append(str(status_chart))

    summary_chart = chart_dir / "swarm_summary.png"
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    labels = ["requested", "selected", "ok", "resolved"]
    values = [
        _safe_int(summary.get("requested_agents"), default=0),
        _safe_int(summary.get("selected_agents"), default=0),
        _safe_int(summary.get("ok_count"), default=0),
        _safe_int(summary.get("resolved_count"), default=0),
    ]
    figure = plt.figure(figsize=(8, 4.5))
    axis = figure.add_subplot(111)
    axis.bar(labels, values, color=["#0369a1", "#1d4ed8", "#16a34a", "#15803d"])
    axis.set_title("Swarm Summary")
    axis.set_ylabel("Count")
    figure.tight_layout()
    figure.savefig(summary_chart, dpi=150)
    plt.close(figure)
    chart_paths.append(str(summary_chart))

    return chart_paths, None
