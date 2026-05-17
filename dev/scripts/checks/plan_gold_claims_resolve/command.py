"""Validate GOLD/proof promotion claims against code and registry symbols."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence

try:
    from check_bootstrap import REPO_ROOT, utc_timestamp
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT, utc_timestamp

try:
    from .symbol_index import DEFAULT_CODE_ROOTS, SymbolIndex, build_symbol_index
except ImportError:
    from symbol_index import DEFAULT_CODE_ROOTS, SymbolIndex, build_symbol_index


COMMAND = "check_plan_gold_claims_resolve"
DEFAULT_TEXT_SOURCES: tuple[str, ...] = (
    "dev/active/MASTER_PLAN.md",
    "dev/state/plan_index.jsonl",
)

_POSITIVE_GOLD_RE = re.compile(
    r"\b(?:VERIFIED\s+GOLD|GOLD-STANDARD|GOLD\s+MODEL\s+CITIZENS?|"
    r"GOLD\s+PROMOTIONS?|PROMOTED\s+TO\s+GOLD)\b",
    re.IGNORECASE,
)
_CLAIM_WINDOW_STOP_RE = re.compile(
    r"\b(?:FAIL|DEMOTE|NEEDS-EVIDENCE|PATTERN|RECOMMEND|CUMULATIVE|"
    r"NEVER-IMPLEMENT|FAKE-PROOF|FILE\s+MISSING|MISSING|FALSIFIED|"
    r"RETRACTION|WRONG|PHANTOM)\b",
    re.IGNORECASE,
)
_CAMEL_SYMBOL_RE = re.compile(r"\b[A-Z][a-z0-9]+(?:[A-Z][A-Za-z0-9]*)+\b")
_CONSTANT_SYMBOL_RE = re.compile(r"\b[A-Z][A-Z0-9]+(?:_[A-Z0-9]+)+\b")
_PATH_TOKEN_RE = re.compile(
    r"(?<![\w/.-])(?:[A-Za-z0-9_.-]+/)*[A-Za-z0-9_.-]+"
    r"\.(?:py|md|json|jsonl|yml|yaml|toml|sh|rs)\b"
)
_IGNORED_SYMBOLS = {
    "GOLD",
    "GOLD-STANDARD",
    "CODEX",
    "CLAUDE",
    "HEAD",
    "REAL",
    "PASS",
    "MP",
}


@dataclass(frozen=True)
class TextRecord:
    source_path: str
    line: int
    field: str
    text: str


@dataclass(frozen=True)
class ClaimReference:
    source_path: str
    line: int
    field: str
    token: str
    token_kind: str
    text: str


@dataclass(frozen=True)
class PlanGoldClaimViolation:
    source_path: str
    line: int
    field: str
    token: str
    token_kind: str
    detail: str
    text: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def collect_gold_claim_references(
    repo_root: Path = REPO_ROOT,
    *,
    text_sources: Sequence[str] = DEFAULT_TEXT_SOURCES,
) -> list[ClaimReference]:
    references: list[ClaimReference] = []
    for record in _iter_text_records(repo_root, text_sources):
        for window in _positive_claim_windows(record.text):
            references.extend(_references_from_window(record, window))
    return references


def evaluate_plan_gold_claims_resolve(
    *,
    repo_root: Path = REPO_ROOT,
    text_sources: Sequence[str] = DEFAULT_TEXT_SOURCES,
    code_roots: Sequence[str] = DEFAULT_CODE_ROOTS,
) -> dict[str, object]:
    index = build_symbol_index(repo_root, code_roots=code_roots)
    references = collect_gold_claim_references(repo_root, text_sources=text_sources)
    violations: list[PlanGoldClaimViolation] = []
    for reference in references:
        violation_detail = _reference_violation_detail(reference, index)
        if not violation_detail:
            continue
        violations.append(
            PlanGoldClaimViolation(
                source_path=reference.source_path,
                line=reference.line,
                field=reference.field,
                token=reference.token,
                token_kind=reference.token_kind,
                detail=violation_detail,
                text=reference.text,
            )
        )

    return {
        "command": COMMAND,
        "timestamp": utc_timestamp(),
        "ok": not violations,
        "source_count": len(text_sources),
        "claim_reference_count": len(references),
        "symbol_count": len(index.symbols),
        "shipped_symbol_count": len(index.shipped_symbols),
        "proposal_stub_symbol_count": len(index.proposal_stub_symbols),
        "path_count": len(index.exact_paths),
        "violations": [violation.to_dict() for violation in violations],
    }


def render_markdown(report: dict[str, object]) -> str:
    violations = report.get("violations", [])
    violation_count = len(violations) if isinstance(violations, list) else 0
    lines = [f"# {COMMAND}", ""]
    lines.append(f"- ok: {report.get('ok', False)}")
    lines.append(f"- source_count: {report.get('source_count', 0)}")
    lines.append(f"- claim_reference_count: {report.get('claim_reference_count', 0)}")
    lines.append(f"- symbol_count: {report.get('symbol_count', 0)}")
    lines.append(f"- shipped_symbol_count: {report.get('shipped_symbol_count', 0)}")
    lines.append(
        f"- proposal_stub_symbol_count: "
        f"{report.get('proposal_stub_symbol_count', 0)}"
    )
    lines.append(f"- path_count: {report.get('path_count', 0)}")
    lines.append(f"- violations: {violation_count}")
    if isinstance(violations, list) and violations:
        lines.extend(("", "## Violations"))
        for violation in violations[:50]:
            if not isinstance(violation, dict):
                continue
            lines.append(
                "- "
                f"`{violation.get('source_path')}:{violation.get('line')}` "
                f"{violation.get('field')} unresolved "
                f"{violation.get('token_kind')} `{violation.get('token')}`"
            )
    return "\n".join(lines)


def _iter_text_records(repo_root: Path, text_sources: Sequence[str]) -> Iterable[TextRecord]:
    for source in text_sources:
        path = repo_root / source
        if not path.exists():
            continue
        if path.suffix == ".jsonl" or path.name.endswith(".ndjson"):
            for line_number, row in _iter_jsonl_rows(path):
                for field in ("title", "summary", "body"):
                    value = row.get(field)
                    if isinstance(value, str) and value:
                        yield TextRecord(source, line_number, field, value)
            continue
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            yield TextRecord(source, line_number, "line", line)


def _iter_jsonl_rows(path: Path) -> Iterable[tuple[int, dict[str, object]]]:
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            yield line_number, row


def _positive_claim_windows(text: str) -> Iterable[str]:
    for match in _POSITIVE_GOLD_RE.finditer(text):
        start = match.start()
        stop_match = _CLAIM_WINDOW_STOP_RE.search(text, match.end())
        end = min(stop_match.start() if stop_match else len(text), match.end() + 800)
        window = text[start:end]
        if _CLAIM_WINDOW_STOP_RE.search(window):
            continue
        yield window


def _references_from_window(record: TextRecord, window: str) -> list[ClaimReference]:
    references: dict[tuple[str, str], ClaimReference] = {}
    for token in _CAMEL_SYMBOL_RE.findall(window):
        if token in _IGNORED_SYMBOLS:
            continue
        references[(token, "symbol")] = ClaimReference(
            source_path=record.source_path,
            line=record.line,
            field=record.field,
            token=token,
            token_kind="symbol",
            text=window.strip(),
        )
    for token in _CONSTANT_SYMBOL_RE.findall(window):
        if token in _IGNORED_SYMBOLS:
            continue
        references[(token, "symbol")] = ClaimReference(
            source_path=record.source_path,
            line=record.line,
            field=record.field,
            token=token,
            token_kind="symbol",
            text=window.strip(),
        )
    for token in _PATH_TOKEN_RE.findall(window):
        references[(token, "path")] = ClaimReference(
            source_path=record.source_path,
            line=record.line,
            field=record.field,
            token=token,
            token_kind="path",
            text=window.strip(),
        )
    return list(references.values())


def _reference_violation_detail(
    reference: ClaimReference,
    index: SymbolIndex,
) -> str:
    if reference.token_kind == "path":
        token = reference.token
        if token in index.exact_paths or Path(token).name in index.basenames:
            return ""
        return "GOLD/proof promotion path does not resolve to a repository file."
    if reference.token in index.shipped_symbols:
        return ""
    if reference.token in index.proposal_stub_symbols:
        return (
            "GOLD/proof promotion symbol resolves only to a proposal-stub "
            "contract, not shipped substrate."
        )
    return (
        "GOLD/proof promotion symbol does not resolve to a shipped code symbol "
        "or registered non-proposal contract."
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("md", "json"), default="md")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    report = evaluate_plan_gold_claims_resolve()
    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(render_markdown(report))
    return 0 if report["ok"] else 1
