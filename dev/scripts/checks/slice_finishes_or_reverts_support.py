"""Support helpers for ``check_slice_finishes_or_reverts``."""

from __future__ import annotations

import json
import subprocess
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path

try:
    from check_bootstrap import REPO_ROOT
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT


class SliceGuardSupport:
    """Filesystem, git, receipt, and rendering helpers for the slice guard."""

    @staticmethod
    def find_plan_row(path: Path, row_id: str) -> dict[str, object]:
        for row in SliceGuardSupport.iter_jsonl(path):
            if row.get("contract_id") == "PlanRow" and row.get("row_id") == row_id:
                return dict(row)
        return {}

    @staticmethod
    def has_closure_receipt(path: Path, row_id: str) -> bool:
        for receipt in SliceGuardSupport.iter_jsonl(path):
            if receipt.get("contract_id") != "PlanRowClosureReceipt":
                continue
            if receipt.get("plan_row_id") == row_id and bool(receipt.get("closure_succeeded")):
                return True
        return False

    @staticmethod
    def has_abort_receipt(path: Path, row_id: str) -> bool:
        for receipt in SliceGuardSupport.iter_jsonl(path):
            if str(receipt.get("plan_row_id") or receipt.get("row_id")) != row_id:
                continue
            contract_id = str(receipt.get("contract_id", ""))
            status = str(receipt.get("status") or receipt.get("outcome") or "").lower()
            if contract_id in {"SliceAbortReceipt", "SliceBlockedReceipt"}:
                return True
            if status in {"slice_aborted", "blocked", "aborted"}:
                return True
        return False

    @staticmethod
    def has_proven_feature_proof(root: Path, row_id: str) -> bool:
        if not root.exists():
            return False
        for path in sorted(root.glob("*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if not isinstance(payload, Mapping):
                continue
            if payload.get("contract_id") != "FeatureProofReceipt":
                continue
            if payload.get("real_life_test_status") != "proven_passed":
                continue
            if not SliceGuardSupport.feature_proof_refs_row(payload, row_id):
                continue
            if SliceGuardSupport.sequence(payload.get("tests_run")):
                return True
        return False

    @staticmethod
    def feature_proof_refs_row(payload: Mapping[str, object], row_id: str) -> bool:
        direct_refs = (
            payload.get("plan_row_id"),
            payload.get("row_id"),
            payload.get("feature_id"),
            payload.get("target_ref"),
        )
        if any(str(ref) == row_id for ref in direct_refs):
            return True
        for field in (
            "plan_row_ids",
            "plan_refs",
            "evidence_artifacts",
            "role_review_receipt_refs",
            "bypass_audit_trail_refs",
        ):
            if any(row_id in str(item) for item in SliceGuardSupport.sequence(payload.get(field))):
                return True
        return False

    @staticmethod
    def iter_jsonl(path: Path) -> Iterable[Mapping[str, object]]:
        if not path.exists():
            return ()

        def rows() -> Iterable[Mapping[str, object]]:
            for line in path.read_text(encoding="utf-8").splitlines():
                text = line.strip()
                if not text:
                    continue
                try:
                    payload = json.loads(text)
                except json.JSONDecodeError:
                    continue
                if isinstance(payload, Mapping):
                    yield payload

        return rows()

    @staticmethod
    def git_status_output(warnings: list[str]) -> str:
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain", "--untracked-files=all"],
                cwd=REPO_ROOT,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except OSError as exc:
            warnings.append(f"git status failed: {exc}")
            return ""
        if result.returncode:
            warnings.append(f"git status returned {result.returncode}: {result.stderr.strip()}")
        return result.stdout

    @staticmethod
    def parse_git_status(output: str) -> tuple[str, ...]:
        paths: list[str] = []
        for line in output.splitlines():
            if not line.strip():
                continue
            path = line[3:] if len(line) > 3 else line.strip()
            if " -> " in path:
                path = path.split(" -> ", 1)[1]
            path = path.strip()
            if path:
                paths.append(path)
        return tuple(paths)

    @staticmethod
    def sequence(value: object) -> tuple[object, ...]:
        if isinstance(value, (list, tuple)):
            return tuple(value)
        return ()

    @staticmethod
    def repo_relative(path: Path) -> Path:
        try:
            return path.resolve().relative_to(REPO_ROOT)
        except (OSError, ValueError):
            return path

    @staticmethod
    def render_markdown(report: Mapping[str, object], command: str) -> str:
        lines = [f"# {command}", ""]
        lines.append(f"- ok: {report.get('ok')}")
        lines.append(f"- row_id: `{report.get('row_id')}`")
        lines.append(f"- dirty_file_count: {report.get('dirty_file_count')}")
        lines.append(f"- has_closure_receipt: {report.get('has_closure_receipt')}")
        lines.append(
            "- has_proven_feature_proof_receipt: "
            f"{report.get('has_proven_feature_proof_receipt')}"
        )
        lines.append(
            "- has_slice_abort_or_block_receipt: "
            f"{report.get('has_slice_abort_or_block_receipt')}"
        )
        lines.append(f"- violation_count: {report.get('violation_count')}")
        if report.get("display_text"):
            lines.extend(("", str(report["display_text"])))
        violations = report.get("violations")
        if isinstance(violations, Sequence) and not isinstance(violations, (str, bytes)):
            lines.extend(("", "## Violations", ""))
            for violation in violations:
                if isinstance(violation, Mapping):
                    lines.append(
                        f"- {violation.get('reason')}: {violation.get('detail')} "
                        f"Remediation: {violation.get('remediation')}"
                    )
        return "\n".join(lines)
