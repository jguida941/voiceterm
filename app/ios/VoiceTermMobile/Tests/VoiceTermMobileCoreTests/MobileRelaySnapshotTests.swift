import Foundation
import Testing
@testable import VoiceTermMobileCore

@Test
func decodesMergedMobileRelaySnapshot() throws {
    let data = sampleFullPayload.data(using: .utf8)!
    let snapshot = try JSONDecoder().decode(MobileRelaySnapshot.self, from: data)

    #expect(snapshot.controllerPayload.phase == "blocked")
    #expect(snapshot.reviewPayload.bridgeLiveness?.overallState == "stale")
    #expect(snapshot.reviewPayload.agentRegistry?.agents?.count == 3)
}

@Test
func buildsDashboardFromProjectionBundle() throws {
    let bundle = MobileRelayProjectionBundle(
        snapshot: try JSONDecoder().decode(
            MobileRelaySnapshot.self,
            from: sampleFullPayload.data(using: .utf8)!
        ),
        compact: try JSONDecoder().decode(
            MobileCompactProjection.self,
            from: sampleCompactPayload.data(using: .utf8)!
        ),
        alert: nil,
        actions: try JSONDecoder().decode(
            MobileActionsProjection.self,
            from: sampleActionsPayload.data(using: .utf8)!
        )
    )

    let dashboard = MobileRelayPresenter.buildDashboard(from: bundle)

    #expect(dashboard.headline.contains("BLOCKED"))
    #expect(dashboard.sections.count == 6)
    #expect(dashboard.metrics.count == 4)
    #expect(dashboard.lanes.count == 3)
    #expect(dashboard.actions.count == 3)
    #expect(dashboard.actions.first?.title == "refresh-mobile-status")
    #expect(dashboard.technicalFacts.first?.value == "MP-340")
}

@Test
func loadsProjectionBundleFromDirectory() throws {
    let directoryURL = URL(fileURLWithPath: NSTemporaryDirectory())
        .appendingPathComponent(UUID().uuidString, isDirectory: true)
    try FileManager.default.createDirectory(
        at: directoryURL,
        withIntermediateDirectories: true
    )
    defer { try? FileManager.default.removeItem(at: directoryURL) }

    try sampleFullPayload.write(
        to: directoryURL.appendingPathComponent("full.json"),
        atomically: true,
        encoding: .utf8
    )
    try sampleCompactPayload.write(
        to: directoryURL.appendingPathComponent("compact.json"),
        atomically: true,
        encoding: .utf8
    )
    try sampleActionsPayload.write(
        to: directoryURL.appendingPathComponent("actions.json"),
        atomically: true,
        encoding: .utf8
    )

    let bundle = try MobileRelayStore.loadBundle(from: directoryURL)

    #expect(bundle.snapshot.controllerPayload.controller?.controllerRunID == "run-123")
    #expect(bundle.compact?.reviewBridgeState == "stale")
    #expect(bundle.actions?.operatorActions?.count == 3)
}

@Test
func previewDataProvidesUsableDashboardBundle() {
    let bundle = MobileRelayPreviewData.sampleBundle()
    let dashboard = MobileRelayPresenter.buildDashboard(from: bundle)

    #expect(dashboard.sections.count == 6)
    #expect(dashboard.lanes.count == 3)
    #expect(dashboard.actions.count == 3)
    #expect(dashboard.sourceRunURL == "https://example.invalid/runs/99")
}

private let sampleCompactPayload = """
{
  "schema_version": 1,
  "view": "compact",
  "headline": "BLOCKED | review stale | unresolved 3",
  "controller_phase": "blocked",
  "controller_reason": "review_follow_up_required",
  "controller_risk": "high",
  "plan_id": "MP-340",
  "controller_run_id": "run-123",
  "review_bridge_state": "stale",
  "codex_poll_state": "stale",
  "codex_last_poll_utc": "2026-03-09T04:12:49Z",
  "last_worktree_hash": "fdc8bee2b634384ac5e1affbe030881c838b4a187267c04772494dce5161cca3",
  "pending_total": 2,
  "unresolved_count": 3,
  "current_instruction": "keep the next slice bounded",
  "open_findings": "bridge needs rollover-safe handoff",
  "codex_status": "stale",
  "claude_lane_status": "assigned",
  "operator_status": "active",
  "source_run_url": "https://example.invalid/runs/99",
  "next_actions": [
    "Refresh review-channel status",
    "Send a bounded fix slice"
  ]
}
"""

private let sampleActionsPayload = """
{
  "schema_version": 1,
  "view": "actions",
  "summary": "BLOCKED | review stale | unresolved 3",
  "next_actions": [
    "Refresh review-channel status",
    "Send a bounded fix slice"
  ],
  "operator_actions": [
    {
      "name": "refresh-mobile-status",
      "command": "python3 dev/scripts/devctl.py mobile-status --view compact --format md",
      "kind": "read"
    },
    {
      "name": "review-status",
      "command": "python3 dev/scripts/devctl.py review-channel --action status --terminal none --format md",
      "kind": "read"
    },
    {
      "name": "phone-trace",
      "command": "python3 dev/scripts/devctl.py phone-status --view trace --format md",
      "kind": "read"
    }
  ]
}
"""

private let sampleFullPayload = """
{
  "schema_version": 1,
  "command": "mobile-status",
  "timestamp": "2026-03-09T09:01:32Z",
  "sources": {
    "phone_input_path": "dev/reports/autonomy/queue/phone/latest.json",
    "review_channel_path": "dev/active/review_channel.md",
    "bridge_path": "code_audit.md",
    "review_status_dir": "dev/reports/review_channel/latest"
  },
  "controller_payload": {
    "phase": "blocked",
    "reason": "review_follow_up_required",
    "controller": {
      "plan_id": "MP-340",
      "controller_run_id": "run-123",
      "branch_base": "develop",
      "mode_effective": "report-only",
      "resolved": false,
      "rounds_completed": 2,
      "max_rounds": 6,
      "tasks_completed": 3,
      "max_tasks": 9,
      "latest_working_branch": "feature/mobile-status"
    },
    "loop": {
      "unresolved_count": 3,
      "risk": "high",
      "next_actions": [
        "Refresh review-channel status",
        "Send a bounded fix slice"
      ]
    },
    "source_run": {
      "run_id": 99,
      "run_sha": "deadbeef",
      "run_url": "https://example.invalid/runs/99"
    },
    "warnings": [],
    "errors": []
  },
  "review_payload": {
    "schema_version": 1,
    "command": "review-channel",
    "action": "status",
    "timestamp": "2026-03-09T09:01:20Z",
    "ok": true,
    "bridge_liveness": {
      "overall_state": "stale",
      "codex_poll_state": "stale",
      "last_codex_poll_utc": "2026-03-09T04:12:49Z",
      "last_codex_poll_age_seconds": 600
    },
    "review_state": {
      "schema_version": 1,
      "command": "review-channel",
      "project_id": "sha256:test",
      "timestamp": "2026-03-09T09:01:20Z",
      "ok": true,
      "review": {
        "plan_id": "MP-355",
        "controller_run_id": null,
        "session_id": "markdown-bridge",
        "surface_mode": "markdown-bridge",
        "active_lane": "review"
      },
      "agents": [
        {"agent_id": "codex", "display_name": "Codex", "role": "reviewer", "status": "stale", "lane": "codex"},
        {"agent_id": "claude", "display_name": "Claude", "role": "implementer", "status": "active", "lane": "claude"},
        {"agent_id": "operator", "display_name": "Operator", "role": "approver", "status": "warning", "lane": "operator"}
      ],
      "queue": {
        "pending_total": 2,
        "stale_packet_count": 0
      },
      "bridge": {
        "last_codex_poll_utc": "2026-03-09T04:12:49Z",
        "last_worktree_hash": "fdc8bee2b634384ac5e1affbe030881c838b4a187267c04772494dce5161cca3",
        "open_findings": "bridge needs rollover-safe handoff",
        "current_instruction": "keep the next slice bounded",
        "claude_status": "implementing the next fix slice",
        "claude_ack": "acknowledged"
      }
    },
    "agent_registry": {
      "schema_version": 1,
      "command": "review-channel",
      "timestamp": "2026-03-09T09:01:20Z",
      "agents": [
        {"agent_id": "codex", "provider": "codex", "display_name": "Codex", "current_job": "review", "job_state": "stale", "lane": "codex", "lane_title": "Codex architecture review", "branch": "feature/a1", "worktree": "../codex-voice-wt-a1"},
        {"agent_id": "claude", "provider": "claude", "display_name": "Claude", "current_job": "implement", "job_state": "assigned", "lane": "claude", "lane_title": "Claude implementation fixes", "branch": "feature/a9", "worktree": "../codex-voice-wt-a9"},
        {"agent_id": "operator", "provider": "human", "display_name": "Operator", "current_job": "approval", "job_state": "active", "lane": "operator", "lane_title": "Operator supervision", "branch": "develop", "worktree": "."}
      ]
    },
    "warnings": [],
    "errors": []
  }
}
"""
