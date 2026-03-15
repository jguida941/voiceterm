import Foundation

public enum MobileRelayPreviewData {
    public static func sampleBundle() -> MobileRelayProjectionBundle {
        let snapshot = MobileRelaySnapshot(
            schemaVersion: 1,
            command: "mobile-status",
            timestamp: "2026-03-09T09:01:32Z",
            approvalPolicy: ApprovalPolicy(
                mode: "balanced",
                summary: "Auto-allow safe local work and escalate dangerous actions.",
                autoAllowed: [
                    "repo reads",
                    "status/report commands",
                    "local non-destructive checks"
                ],
                requiresConfirmation: [
                    "rm / destructive deletes",
                    "git push / publish / release",
                    "GitHub write operations"
                ]
            ),
            // Paths must match dev/scripts/devctl/repo_packs/voiceterm.py::RepoPathConfig
            sources: Sources(
                phoneInputPath: "dev/reports/autonomy/queue/phone/latest.json",
                reviewChannelPath: "dev/active/review_channel.md",
                bridgePath: "code_audit.md",
                reviewStatusDir: "dev/reports/review_channel/latest"
            ),
            controllerPayload: ControllerPayload(
                phase: "blocked",
                reason: "review_follow_up_required",
                controller: ControllerState(
                    planID: "MP-340",
                    controllerRunID: "run-123",
                    branchBase: "develop",
                    modeEffective: "report-only",
                    resolved: false,
                    roundsCompleted: 2,
                    maxRounds: 6,
                    tasksCompleted: 3,
                    maxTasks: 9,
                    latestWorkingBranch: "feature/mobile-status"
                ),
                loop: LoopState(
                    unresolvedCount: 3,
                    risk: "high",
                    nextActions: [
                        "Refresh review-channel status",
                        "Send a bounded fix slice",
                    ]
                ),
                sourceRun: SourceRun(
                    runID: 99,
                    runSHA: "deadbeef",
                    runURL: "https://example.invalid/runs/99"
                ),
                ralph: RalphSection(
                    available: true,
                    phase: "running",
                    attempt: 2,
                    maxAttempts: 5,
                    fixRatePct: 66.7,
                    totalFindings: 12,
                    fixedCount: 8,
                    unresolvedCount: 4,
                    branch: "feature/ralph-guardrail",
                    lastRun: "2026-03-09T08:45:00Z"
                ),
                warnings: [],
                errors: []
            ),
            reviewPayload: ReviewPayload(
                schemaVersion: 1,
                command: "review-channel",
                action: "status",
                timestamp: "2026-03-09T09:01:20Z",
                ok: true,
                bridgeLiveness: BridgeLiveness(
                    overallState: "stale",
                    codexPollState: "stale",
                    lastCodexPollUTC: "2026-03-09T04:12:49Z",
                    lastCodexPollAgeSeconds: 600,
                    nextActionPresent: true,
                    openFindingsPresent: true,
                    claudeStatusPresent: true,
                    claudeAckPresent: true
                ),
                reviewState: ReviewState(
                    schemaVersion: 1,
                    command: "review-channel",
                    projectID: "sha256:test",
                    timestamp: "2026-03-09T09:01:20Z",
                    ok: true,
                    review: ReviewMeta(
                        planID: "MP-355",
                        controllerRunID: nil,
                        sessionID: "markdown-bridge",
                        surfaceMode: "markdown-bridge",
                        activeLane: "review"
                    ),
                    agents: [
                        ReviewAgent(
                            agentID: "codex",
                            displayName: "Codex",
                            role: "reviewer",
                            status: "stale",
                            lane: "codex"
                        ),
                        ReviewAgent(
                            agentID: "claude",
                            displayName: "Claude",
                            role: "implementer",
                            status: "active",
                            lane: "claude"
                        ),
                        ReviewAgent(
                            agentID: "operator",
                            displayName: "Operator",
                            role: "approver",
                            status: "warning",
                            lane: "operator"
                        ),
                    ],
                    queue: ReviewQueue(
                        pendingTotal: 2,
                        stalePacketCount: 0
                    ),
                    bridge: ReviewBridge(
                        lastCodexPollUTC: "2026-03-09T04:12:49Z",
                        lastWorktreeHash: "fdc8bee2b634384ac5e1affbe030881c838b4a187267c04772494dce5161cca3",
                        openFindings: "bridge needs rollover-safe handoff",
                        currentInstruction: "keep the next slice bounded",
                        claudeStatus: "implementing the next fix slice",
                        claudeAck: "acknowledged"
                    )
                ),
                agentRegistry: AgentRegistry(
                    schemaVersion: 1,
                    command: "review-channel",
                    timestamp: "2026-03-09T09:01:20Z",
                    agents: [
                        RegistryAgent(
                            agentID: "codex",
                            provider: "codex",
                            displayName: "Codex",
                            currentJob: "review",
                            jobState: "stale",
                            waitingOn: nil,
                            scriptProfile: "markdown-bridge-conductor",
                            lane: "codex",
                            laneTitle: "Codex architecture review",
                            branch: "feature/a1",
                            worktree: "../codex-voice-wt-a1"
                        ),
                        RegistryAgent(
                            agentID: "claude",
                            provider: "claude",
                            displayName: "Claude",
                            currentJob: "implement",
                            jobState: "assigned",
                            waitingOn: nil,
                            scriptProfile: "markdown-bridge-conductor",
                            lane: "claude",
                            laneTitle: "Claude implementation fixes",
                            branch: "feature/a9",
                            worktree: "../codex-voice-wt-a9"
                        ),
                        RegistryAgent(
                            agentID: "operator",
                            provider: "human",
                            displayName: "Operator",
                            currentJob: "approval",
                            jobState: "active",
                            waitingOn: nil,
                            scriptProfile: "markdown-bridge-conductor",
                            lane: "operator",
                            laneTitle: "Operator supervision",
                            branch: "develop",
                            worktree: "."
                        ),
                    ]
                ),
                warnings: [],
                errors: []
            )
        )

        let compact = MobileCompactProjection(
            schemaVersion: 1,
            view: "compact",
            headline: "BLOCKED | review stale | unresolved 3",
            controllerPhase: "blocked",
            controllerReason: "review_follow_up_required",
            controllerRisk: "high",
            planID: "MP-340",
            controllerRunID: "run-123",
            reviewBridgeState: "stale",
            codexPollState: "stale",
            codexLastPollUTC: "2026-03-09T04:12:49Z",
            lastWorktreeHash: "fdc8bee2b634384ac5e1affbe030881c838b4a187267c04772494dce5161cca3",
            pendingTotal: 2,
            unresolvedCount: 3,
            currentInstruction: "keep the next slice bounded",
            openFindings: "bridge needs rollover-safe handoff",
            codexStatus: "stale",
            claudeLaneStatus: "assigned",
            operatorStatus: "active",
            sourceRunURL: "https://example.invalid/runs/99",
            approvalMode: "balanced",
            approvalSummary: "Auto-allow safe local work and escalate dangerous actions.",
            nextActions: [
                "Refresh review-channel status",
                "Send a bounded fix slice",
            ]
        )

        let actions = MobileActionsProjection(
            schemaVersion: 1,
            view: "actions",
            summary: "BLOCKED | review stale | unresolved 3",
            approvalMode: "balanced",
            approvalSummary: "Auto-allow safe local work and escalate dangerous actions.",
            nextActions: [
                "Refresh review-channel status",
                "Send a bounded fix slice",
            ],
            operatorActions: [
                MobileOperatorAction(
                    name: "refresh-mobile-status",
                    command: "python3 dev/scripts/devctl.py mobile-status --view compact --format md",
                    kind: "read",
                    guardText: nil
                ),
                MobileOperatorAction(
                    name: "review-status",
                    command: "python3 dev/scripts/devctl.py review-channel --action status --terminal none --format md",
                    kind: "read",
                    guardText: nil
                ),
                MobileOperatorAction(
                    name: "phone-trace",
                    command: "python3 dev/scripts/devctl.py phone-status --view trace --format md",
                    kind: "read",
                    guardText: nil
                ),
                MobileOperatorAction(
                    name: "dispatch-report-only",
                    command: "python3 dev/scripts/devctl.py controller-action --action dispatch-report-only --branch develop --dry-run --format md",
                    kind: "write",
                    guardText: "policy-gated"
                ),
                MobileOperatorAction(
                    name: "pause-loop",
                    command: "python3 dev/scripts/devctl.py controller-action --action pause-loop --dry-run --format md",
                    kind: "write",
                    guardText: "policy-gated"
                ),
                MobileOperatorAction(
                    name: "resume-loop",
                    command: "python3 dev/scripts/devctl.py controller-action --action resume-loop --dry-run --format md",
                    kind: "write",
                    guardText: "policy-gated"
                ),
            ]
        )

        return MobileRelayProjectionBundle(
            snapshot: snapshot,
            compact: compact,
            alert: nil,
            actions: actions
        )
    }
}
