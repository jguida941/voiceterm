"""Guard launch authority ordering against projection-first regressions."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

try:
    from check_bootstrap import REPO_ROOT
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


@dataclass(frozen=True)
class Violation:
    rule: str
    path: str
    detail: str


def _read(root: Path, rel_path: str) -> str:
    return (root / rel_path).read_text(encoding="utf-8")


def _position(text: str, marker: str) -> int:
    return text.find(marker)


def _requires_before(
    *,
    text: str,
    path: str,
    earlier: str,
    later: str,
    rule: str,
) -> list[Violation]:
    earlier_pos = _position(text, earlier)
    later_pos = _position(text, later)
    if earlier_pos < 0 or later_pos < 0 or earlier_pos > later_pos:
        return [
            Violation(
                rule=rule,
                path=path,
                detail=f"`{earlier}` must appear before `{later}`.",
            )
        ]
    return []


def _requires_markers(
    *,
    text: str,
    path: str,
    markers: tuple[str, ...],
    rule: str,
) -> list[Violation]:
    missing = [marker for marker in markers if marker not in text]
    if not missing:
        return []
    return [
        Violation(
            rule=rule,
            path=path,
            detail="Missing markers: " + ", ".join(f"`{marker}`" for marker in missing),
        )
    ]


def _build_report(root: Path = REPO_ROOT) -> dict[str, object]:
    violations: list[Violation] = []
    helper_path = "dev/scripts/devctl/review_channel/launch_authority_ordering.py"
    bridge_handler_path = "dev/scripts/devctl/commands/review_channel/bridge_handler.py"
    bridge_support_path = "dev/scripts/devctl/commands/review_channel/bridge_support.py"
    bridge_prepare_path = (
        "dev/scripts/devctl/commands/review_channel/bridge_action_prepare.py"
    )
    event_handler_path = "dev/scripts/devctl/commands/review_channel/event_handler.py"
    success_report_path = (
        "dev/scripts/devctl/commands/review_channel/bridge_success_report.py"
    )
    error_model_path = "dev/scripts/devctl/commands/review_channel_command/models.py"

    for rel_path in (
        helper_path,
        bridge_handler_path,
        bridge_support_path,
        bridge_prepare_path,
        event_handler_path,
        success_report_path,
        error_model_path,
    ):
        if not (root / rel_path).exists():
            violations.append(
                Violation(
                    rule="required_authority_ordering_file_missing",
                    path=rel_path,
                    detail=(
                        "Required Phase 0.4-Bootstrap authority-ordering file "
                        "is missing."
                    ),
                )
            )
    if violations:
        return _report(violations)

    bridge_handler = _read(root, bridge_handler_path)
    violations.extend(
        _requires_before(
            text=bridge_handler,
            path=bridge_handler_path,
            earlier="launch_authority_report = require_valid_launch_bypass_if_requested(",
            later="validate_live_launch_conflicts(",
            rule="launch_bypass_must_precede_projection_conflict_gates",
        )
    )
    violations.extend(
        _requires_before(
            text=bridge_handler,
            path=bridge_handler_path,
            earlier="launch_authority_report = require_valid_launch_bypass_if_requested(",
            later="preparation = prepare_bridge_action(",
            rule="launch_bypass_must_precede_bridge_preparation",
        )
    )

    bridge_prepare = _read(root, bridge_prepare_path)
    violations.extend(
        _requires_before(
            text=bridge_prepare,
            path=bridge_prepare_path,
            earlier="if not launch_bridge_gate_bypassed",
            later="enforce_bridge_launch_attention(",
            rule="bridge_bypass_check_must_precede_attention_gate",
        )
    )
    bridge_support = _read(root, bridge_support_path)
    violations.extend(
        _requires_before(
            text=bridge_support,
            path=bridge_support_path,
            earlier="if launch_bridge_gate_bypassed(launch_authority_report):",
            later="launch_state_errors = validate_launch_bridge_state",
            rule="bridge_bypass_check_must_precede_live_bridge_validation",
        )
    )

    event_handler = _read(root, event_handler_path)
    violations.extend(
        _requires_before(
            text=event_handler,
            path=event_handler_path,
            earlier="if _operator_post_authority(args):",
            later="report = evaluate_control_decision_obedience",
            rule="operator_source_must_precede_obedience_gate",
        )
    )

    required_fields = (
        "bypass_receipt_id",
        "bypass_receipt_validated",
        "bridge_gate_bypassed",
        "bypass_scope",
        "rejected_reason",
    )
    violations.extend(
        _requires_markers(
            text=_read(root, success_report_path),
            path=success_report_path,
            markers=("launch_authority_report_fields",),
            rule="launch_success_report_missing_structured_bypass_fields",
        )
    )
    violations.extend(
        _requires_markers(
            text=_read(root, error_model_path),
            path=error_model_path,
            markers=required_fields,
            rule="launch_error_report_missing_structured_bypass_fields",
        )
    )
    return _report(violations)


def _report(violations: list[Violation]) -> dict[str, object]:
    return {
        "command": "check_launcher_authority_ordering",
        "ok": not violations,
        "violation_count": len(violations),
        "violations": [asdict(violation) for violation in violations],
    }


def _render_markdown(report: dict[str, object]) -> str:
    lines = ["# check_launcher_authority_ordering", ""]
    lines.append(f"- ok: {report['ok']}")
    lines.append(f"- violation_count: {report['violation_count']}")
    violations = report.get("violations")
    if isinstance(violations, list) and violations:
        lines.append("")
        lines.append("## Violations")
        for violation in violations:
            if not isinstance(violation, dict):
                continue
            lines.append(
                f"- {violation.get('path')}: {violation.get('rule')} - "
                f"{violation.get('detail')}"
            )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("json", "md"), default="json")
    args = parser.parse_args(argv)
    report = _build_report()
    if args.format == "md":
        print(_render_markdown(report))
    else:
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
