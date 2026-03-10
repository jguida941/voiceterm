"""devctl mobile-app command implementation."""

from __future__ import annotations

import json
from typing import Any

from ..common import emit_output, pipe_output, run_cmd, write_output
from ..mobile_app_support import (
    DEVICE_DERIVED_DATA_PATH,
    IOS_APP_BUNDLE_ID,
    IOS_PROJECT,
    IOS_SCHEME,
    SIMULATOR_DEMO_SCRIPT,
    list_available_simulators,
    list_physical_devices,
    project_relative_path,
    resolve_development_team,
    select_physical_device,
    select_simulator,
)
from ..time_utils import utc_timestamp


def _base_report(args) -> dict[str, Any]:
    return {
        "command": "mobile-app",
        "timestamp": utc_timestamp(),
        "ok": False,
        "action": str(args.action),
        "result": {},
        "warnings": [],
        "errors": [],
    }


def _render_markdown(report: dict[str, Any]) -> str:
    lines = ["# devctl mobile-app", ""]
    lines.append(f"- ok: {report.get('ok')}")
    lines.append(f"- action: {report.get('action')}")
    result = report.get("result", {})
    if isinstance(result, dict):
        selected = result.get("selected_device_id")
        if selected:
            lines.append(f"- selected_device_id: {selected}")
        if "live_review" in result:
            lines.append(f"- live_review: {result.get('live_review')}")
        team = result.get("development_team")
        if team:
            lines.append(f"- development_team: {team}")
        project = result.get("project")
        if project:
            lines.append(f"- project: {project}")
    warnings = report.get("warnings") or []
    errors = report.get("errors") or []
    if warnings:
        lines.append("")
        lines.append("## Warnings")
        lines.append("")
        for row in warnings:
            lines.append(f"- {row}")
    if errors:
        lines.append("")
        lines.append("## Errors")
        lines.append("")
        for row in errors:
            lines.append(f"- {row}")
    steps = result.get("wizard_steps") if isinstance(result, dict) else None
    if isinstance(steps, list) and steps:
        lines.append("")
        lines.append("## Wizard Steps")
        lines.append("")
        for index, step in enumerate(steps, start=1):
            lines.append(f"{index}. {step}")
    devices = result.get("devices") if isinstance(result, dict) else None
    if isinstance(devices, list) and devices:
        lines.append("")
        lines.append("## Devices")
        lines.append("")
        for row in devices:
            if not isinstance(row, dict):
                continue
            lines.append(
                f"- {row.get('name')} ({row.get('runtime')}) `{row.get('identifier')}`"
            )
    return "\n".join(lines)


def _list_devices(report: dict[str, Any]) -> None:
    report["result"] = {
        "simulators": list_available_simulators(),
        "devices": list_physical_devices(),
    }
    report["ok"] = True


def _simulator_demo(report: dict[str, Any], args) -> None:
    selected_device = select_simulator(getattr(args, "device_id", None))
    if not selected_device:
        report["errors"].append("no simulator device available")
        return
    live_review = bool(getattr(args, "live_review", False))
    review_status_result: dict[str, Any] | None = None
    if live_review:
        review_status_result = run_cmd(
            "mobile-app-review-status",
            [
                "python3",
                "dev/scripts/devctl.py",
                "review-channel",
                "--action",
                "status",
                "--terminal",
                "none",
                "--format",
                "md",
            ],
            dry_run=bool(args.dry_run),
        )
        if review_status_result.get("returncode") != 0:
            report["errors"].append(
                review_status_result.get("error")
                or "unable to refresh review-channel status for live-review mode"
            )
            report["result"] = {
                "selected_device_id": selected_device,
                "live_review": live_review,
                "review_status_result": review_status_result,
            }
            return
    cmd = [str(SIMULATOR_DEMO_SCRIPT)]
    if getattr(args, "device_id", None):
        cmd.append(str(args.device_id))
    env = None
    if live_review:
        env = {"VOICETERM_MOBILE_LIVE_REVIEW": "1"}
    result = run_cmd(
        "mobile-app-simulator-demo",
        cmd,
        env=env,
        dry_run=bool(args.dry_run),
    )
    report["result"] = {
        "selected_device_id": selected_device,
        "live_review": live_review,
        "review_status_result": review_status_result,
        "script": project_relative_path(SIMULATOR_DEMO_SCRIPT),
        "project": project_relative_path(IOS_PROJECT),
        "command_result": result,
    }
    if result.get("returncode") == 0:
        report["ok"] = True
        return
    report["errors"].append(result.get("error") or "simulator demo failed")


def _device_wizard(report: dict[str, Any], args) -> None:
    devices = list_physical_devices()
    selected_device = select_physical_device(getattr(args, "device_id", None), devices)
    development_team = resolve_development_team(getattr(args, "development_team", None))
    report["result"] = {
        "devices": devices,
        "selected_device_id": selected_device,
        "development_team": development_team,
        "project": project_relative_path(IOS_PROJECT),
        "wizard_steps": [
            "Plug in and trust the iPhone or iPad on this Mac.",
            "Open the Xcode project and select the physical device target.",
            "Set your Apple Development Team for VoiceTermMobileApp if it is still blank.",
            "Run `devctl mobile-app --action device-install --development-team <TEAM>` for a scripted build/install/launch, or press Run in Xcode.",
            "Use Import Bundle to load a real emitted mobile-status bundle from Files.",
        ],
    }
    if not devices:
        report["warnings"].append("no connected physical iPhone/iPad detected")
    if bool(args.open_xcode):
        open_result = run_cmd(
            "mobile-app-open-xcode",
            ["open", str(IOS_PROJECT)],
            dry_run=bool(args.dry_run),
        )
        report["result"]["open_xcode_result"] = open_result
        if open_result.get("returncode") != 0:
            report["errors"].append(open_result.get("error") or "unable to open Xcode project")
            return
    report["ok"] = True


def _device_install(report: dict[str, Any], args) -> None:
    devices = list_physical_devices()
    selected_device = select_physical_device(getattr(args, "device_id", None), devices)
    development_team = resolve_development_team(getattr(args, "development_team", None))
    result: dict[str, Any] = {
        "devices": devices,
        "selected_device_id": selected_device,
        "development_team": development_team,
        "project": project_relative_path(IOS_PROJECT),
        "derived_data_path": str(DEVICE_DERIVED_DATA_PATH),
        "wizard_steps": [
            "Plug in and trust the device.",
            "Provide an Apple Development Team ID via --development-team or VOICETERM_IOS_DEVELOPMENT_TEAM.",
            "Let devctl build a signed iphoneos app, install it with devicectl, and launch it on-device.",
            "Use the in-app Tutorial button and Import Bundle to load real repo data.",
        ],
    }
    report["result"] = result
    if not selected_device:
        report["errors"].append("no connected physical iPhone/iPad detected")
        return
    if not development_team:
        report["errors"].append(
            "no Apple Development Team configured; pass --development-team or set VOICETERM_IOS_DEVELOPMENT_TEAM"
        )
        return

    build_cmd = [
        "xcodebuild",
        "-project",
        str(IOS_PROJECT),
        "-scheme",
        IOS_SCHEME,
        "-configuration",
        "Debug",
        "-destination",
        f"id={selected_device}",
        "-derivedDataPath",
        str(DEVICE_DERIVED_DATA_PATH),
    ]
    if bool(getattr(args, "allow_provisioning_updates", False)):
        build_cmd.append("-allowProvisioningUpdates")
    build_cmd.extend(
        [
            f"DEVELOPMENT_TEAM={development_team}",
            "build",
        ]
    )
    build_result = run_cmd(
        "mobile-app-device-build",
        build_cmd,
        dry_run=bool(args.dry_run),
    )
    result["build_result"] = build_result
    if build_result.get("returncode") != 0:
        report["errors"].append(build_result.get("error") or "device build failed")
        return

    app_path = (
        DEVICE_DERIVED_DATA_PATH
        / "Build/Products/Debug-iphoneos/VoiceTermMobileApp.app"
    )
    install_result = run_cmd(
        "mobile-app-device-install",
        [
            "xcrun",
            "devicectl",
            "device",
            "install",
            "app",
            "--device",
            selected_device,
            str(app_path),
        ],
        dry_run=bool(args.dry_run),
    )
    result["app_path"] = str(app_path)
    result["install_result"] = install_result
    if install_result.get("returncode") != 0:
        report["errors"].append(install_result.get("error") or "device install failed")
        return

    launch_result = run_cmd(
        "mobile-app-device-launch",
        [
            "xcrun",
            "devicectl",
            "device",
            "process",
            "launch",
            "--device",
            selected_device,
            "--terminate-existing",
            IOS_APP_BUNDLE_ID,
        ],
        dry_run=bool(args.dry_run),
    )
    result["launch_result"] = launch_result
    if launch_result.get("returncode") != 0:
        report["errors"].append(launch_result.get("error") or "device launch failed")
        return
    report["ok"] = True


def run(args) -> int:
    """Run the iPhone app simulator demo or device install wizard."""
    report = _base_report(args)
    action = str(args.action)
    if action == "list-devices":
        _list_devices(report)
    elif action == "simulator-demo":
        _simulator_demo(report, args)
    elif action == "device-wizard":
        _device_wizard(report, args)
    elif action == "device-install":
        _device_install(report, args)
    else:
        report["errors"].append(f"unsupported action: {action}")

    json_payload = json.dumps(report, indent=2)
    output = json_payload if args.format == "json" else _render_markdown(report)
    pipe_code = emit_output(
        output,
        output_path=args.output,
        pipe_command=args.pipe_command,
        pipe_args=args.pipe_args,
        additional_outputs=[(json_payload, args.json_output)] if args.json_output else None,
        writer=write_output,
        piper=pipe_output,
    )
    if pipe_code != 0:
        return pipe_code
    return 0 if report.get("ok") else 1
