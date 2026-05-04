"""Guard coverage and remediation receipts for check-router."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class CheckRouterGuardCoverageReceipt:
    schema_version: int
    contract_id: str
    bundle: str
    risk_addons: list[str]
    planned_command_count: int
    executed_command_count: int
    materialized_step_count: int
    skipped_command_count: int
    failed_command_count: int
    unexecuted_command_count: int
    all_planned_commands_materialized: bool
    all_planned_commands_executed: bool
    dry_run: bool
    failed_steps: list[dict[str, object]]
    unexecuted_commands: list[dict[str, object]]
    source_counts: dict[str, int]


@dataclass(frozen=True)
class GuardRemediationAction:
    schema_version: int
    contract_id: str
    action_id: str
    source: str
    router_command: str
    reason: str
    required_paths: list[str]
    remediation: str
    auto_executable: bool


def build_guard_coverage_receipt(
    *,
    planned_rows: list[dict[str, str]],
    steps: list[dict],
    execute: bool,
    dry_run: bool,
    bundle_name: str,
    risk_addons: list[dict],
) -> dict[str, object]:
    failed_steps = [step for step in steps if int(step.get("returncode") or 0) != 0]
    skipped_steps = [step for step in steps if bool(step.get("skipped"))]
    unexecuted_rows = planned_rows[len(steps) :]
    receipt = CheckRouterGuardCoverageReceipt(
        schema_version=1,
        contract_id="CheckRouterGuardCoverageReceipt",
        bundle=bundle_name,
        risk_addons=[str(addon.get("id") or "") for addon in risk_addons],
        planned_command_count=len(planned_rows),
        executed_command_count=len(steps) - len(skipped_steps),
        materialized_step_count=len(steps),
        skipped_command_count=len(skipped_steps),
        failed_command_count=len(failed_steps),
        unexecuted_command_count=len(unexecuted_rows),
        all_planned_commands_materialized=len(steps) == len(planned_rows),
        all_planned_commands_executed=(
            bool(execute)
            and not dry_run
            and len(steps) == len(planned_rows)
            and not skipped_steps
        ),
        dry_run=dry_run,
        failed_steps=[_failed_step_row(step) for step in failed_steps],
        unexecuted_commands=[_unexecuted_command_row(row) for row in unexecuted_rows],
        source_counts=_source_counts(planned_rows),
    )
    return asdict(receipt)


def build_remediation_actions(steps: list[dict]) -> list[dict[str, object]]:
    actions: list[dict[str, object]] = []
    for step in steps:
        if int(step.get("returncode") or 0) == 0:
            continue
        output = str(step.get("failure_output") or "")
        action = GuardRemediationAction(
            schema_version=1,
            contract_id="GuardRemediationAction",
            action_id="guard-remediation:" + str(step.get("name") or "step"),
            source=str(step.get("source") or ""),
            router_command=str(step.get("router_command") or ""),
            reason=_classify_failure_reason(output),
            required_paths=_required_paths_from_failure(output),
            remediation=_remediation_text(output),
            auto_executable=False,
        )
        actions.append(asdict(action))
    return actions


def _failed_step_row(step: dict) -> dict[str, object]:
    return {
        "name": str(step.get("name") or ""),
        "source": str(step.get("source") or ""),
        "returncode": int(step.get("returncode") or 0),
        "router_command": str(step.get("router_command") or ""),
    }


def _unexecuted_command_row(row: dict[str, str]) -> dict[str, object]:
    return {
        "source": str(row.get("source") or ""),
        "command": str(row.get("command") or ""),
    }


def _source_counts(planned_rows: list[dict[str, str]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in planned_rows:
        source = str(row.get("source") or "unknown")
        counts[source] = counts.get(source, 0) + 1
    return counts


def _classify_failure_reason(output: str) -> str:
    if "timed out after" in output or "route budget exhausted" in output:
        return "guard_execution_timed_out"
    if "Strict tooling docs mode requires maintainer docs" in output:
        return "strict_tooling_maintainer_docs_missing"
    if "Engineering evolution log is required" in output:
        return "engineering_evolution_log_missing"
    if "Active-plan sync gate failed" in output:
        return "active_plan_sync_failed"
    return "guard_failed"


def _required_paths_from_failure(output: str) -> list[str]:
    paths: list[str] = []
    for marker in (
        "Update missing maintainer docs:",
        "Strict tooling docs mode requires maintainer docs; missing:",
    ):
        if marker not in output:
            continue
        tail = output.split(marker, 1)[1].splitlines()[0].strip()
        if tail.endswith("."):
            tail = tail[:-1]
        paths.extend(_split_required_paths(tail))
    if "Engineering evolution log is required" in output:
        paths.append("dev/history/ENGINEERING_EVOLUTION.md")
    return sorted(dict.fromkeys(path for path in paths if path))


def _split_required_paths(raw: str) -> list[str]:
    return [
        item.strip().strip("`")
        for item in raw.replace(" and ", ",").split(",")
        if item.strip()
    ]


def _remediation_text(output: str) -> str:
    if "timed out after" in output or "route budget exhausted" in output:
        return (
            "Inspect the timed-out guard for a hang, narrow its scan scope, "
            "or raise its typed execution policy only with measured evidence."
        )
    required_paths = _required_paths_from_failure(output)
    if required_paths:
        return "Update required paths: " + ", ".join(required_paths)
    return "Inspect the failed guard output and fix the reported violations."
