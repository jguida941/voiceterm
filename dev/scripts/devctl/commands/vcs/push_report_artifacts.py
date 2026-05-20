"""Artifact helpers for push report payloads and rendering."""

from __future__ import annotations

from typing import Any


def build_push_report_artifacts(
    *,
    push_report_path: str,
    git_mutation_proof_receipt_path: str,
) -> dict[str, str]:
    artifacts: dict[str, str] = {}
    if push_report_path:
        artifacts["push_report_json"] = push_report_path
        artifacts["latest_json"] = push_report_path
    if git_mutation_proof_receipt_path:
        artifacts["git_mutation_proof_receipts"] = git_mutation_proof_receipt_path
    return artifacts


def append_push_report_artifact_lines(
    lines: list[str],
    artifacts: dict[str, Any],
) -> None:
    push_report_json = artifacts.get("push_report_json") or artifacts.get("latest_json")
    if push_report_json:
        lines.append(f"- push_report_json: {push_report_json}")
    git_mutation_proof = artifacts.get("git_mutation_proof_receipts")
    if git_mutation_proof:
        lines.append(f"- git_mutation_proof_receipts: {git_mutation_proof}")
