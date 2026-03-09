import Foundation

public enum MobileAudienceMode: String, CaseIterable, Codable, Sendable {
    case simple
    case technical

    public var label: String {
        switch self {
        case .simple:
            return "Simple"
        case .technical:
            return "Technical"
        }
    }
}

public enum MobileRelaySection: String, CaseIterable, Codable, Hashable, Sendable, Identifiable {
    case overview
    case instruction
    case findings
    case agents
    case actions
    case technical

    public var id: String { rawValue }

    public var title: String {
        switch self {
        case .overview:
            return "Overview"
        case .instruction:
            return "Current Plan"
        case .findings:
            return "Open Findings"
        case .agents:
            return "Agent Lanes"
        case .actions:
            return "Safe Actions"
        case .technical:
            return "Technical"
        }
    }
}

public struct MobileRelayDashboardModel: Equatable, Sendable {
    public struct SidebarItem: Equatable, Sendable, Identifiable {
        public let section: MobileRelaySection
        public let title: String
        public let caption: String
        public let badge: String?

        public var id: String { section.id }
    }

    public struct MetricCard: Equatable, Sendable, Identifiable {
        public let id: String
        public let title: String
        public let value: String
        public let detail: String
    }

    public struct NarrativeCard: Equatable, Sendable, Identifiable {
        public let id: String
        public let title: String
        public let simpleBody: String
        public let technicalBody: String
        public let footnote: String?
    }

    public struct LaneCard: Equatable, Sendable, Identifiable {
        public let id: String
        public let title: String
        public let subtitle: String
        public let status: String
        public let provider: String?
        public let branch: String?
        public let worktree: String?
    }

    public struct SafeActionCard: Equatable, Sendable, Identifiable {
        public let id: String
        public let title: String
        public let summary: String
        public let command: String
        public let kind: String
        public let guardText: String
    }

    public struct TechnicalFact: Equatable, Sendable, Identifiable {
        public let id: String
        public let label: String
        public let value: String
    }

    public let headline: String
    public let subheadline: String
    public let sections: [SidebarItem]
    public let metrics: [MetricCard]
    public let instruction: NarrativeCard
    public let findings: NarrativeCard
    public let actionsNarrative: NarrativeCard
    public let lanes: [LaneCard]
    public let actions: [SafeActionCard]
    public let nextActions: [String]
    public let technicalFacts: [TechnicalFact]
    public let sourceRunURL: String
}

public enum MobileRelayPresenter {
    public static func buildDashboard(
        from bundle: MobileRelayProjectionBundle
    ) -> MobileRelayDashboardModel {
        buildDashboard(
            snapshot: bundle.snapshot,
            compact: bundle.compact,
            alert: bundle.alert,
            actions: bundle.actions
        )
    }

    public static func buildDashboard(
        from snapshot: MobileRelaySnapshot
    ) -> MobileRelayDashboardModel {
        buildDashboard(snapshot: snapshot, compact: nil, alert: nil, actions: nil)
    }

    private static func buildDashboard(
        snapshot: MobileRelaySnapshot,
        compact: MobileCompactProjection?,
        alert: MobileAlertProjection?,
        actions: MobileActionsProjection?
    ) -> MobileRelayDashboardModel {
        let phase = snapshot.controllerPayload.phase?.trimmedOrUnknown ?? "unknown"
        let reason = snapshot.controllerPayload.reason?.trimmedOrUnknown ?? "unknown"
        let risk = snapshot.controllerPayload.loop?.risk?.trimmedOrUnknown ?? "unknown"
        let bridgeState = snapshot.reviewPayload.bridgeLiveness?.overallState?.trimmedOrUnknown ?? "unknown"
        let unresolvedCount = compact?.unresolvedCount ?? snapshot.controllerPayload.loop?.unresolvedCount ?? 0
        let pendingCount = compact?.pendingTotal ?? snapshot.reviewPayload.reviewState?.queue?.pendingTotal ?? 0
        let planID = snapshot.controllerPayload.controller?.planID?.trimmedNonEmpty
            ?? snapshot.reviewPayload.reviewState?.review?.planID?.trimmedNonEmpty
            ?? "Unknown"
        let runID = snapshot.controllerPayload.controller?.controllerRunID?.trimmedNonEmpty ?? "Unknown"
        let worktreeHash = compact?.lastWorktreeHash?.trimmedNonEmpty
            ?? snapshot.reviewPayload.reviewState?.bridge?.lastWorktreeHash?.trimmedNonEmpty
            ?? "Unknown"
        let sourceRunURL = compact?.sourceRunURL?.trimmedNonEmpty
            ?? snapshot.controllerPayload.sourceRun?.runURL?.trimmedNonEmpty
            ?? ""
        let lastPollUTC = compact?.codexLastPollUTC?.trimmedNonEmpty
            ?? snapshot.reviewPayload.bridgeLiveness?.lastCodexPollUTC?.trimmedNonEmpty
            ?? "Unknown"
        let currentInstruction = compact?.currentInstruction?.trimmedNonEmpty
            ?? snapshot.reviewPayload.reviewState?.bridge?.currentInstruction?.trimmedNonEmpty
            ?? "No current instruction recorded."
        let openFindings = compact?.openFindings?.trimmedNonEmpty
            ?? snapshot.reviewPayload.reviewState?.bridge?.openFindings?.trimmedNonEmpty
            ?? "No open findings recorded."
        let nextActions = (
            compact?.nextActions
            ?? actions?.nextActions
            ?? snapshot.controllerPayload.loop?.nextActions
            ?? []
        ).compactMap(\.trimmedNonEmpty)
        let lanes = laneCards(from: snapshot)
        let safeActions = actionCards(from: actions)

        let sections = [
            MobileRelayDashboardModel.SidebarItem(
                section: .overview,
                title: "Overview",
                caption: "What is happening right now",
                badge: "\(unresolvedCount)"
            ),
            MobileRelayDashboardModel.SidebarItem(
                section: .instruction,
                title: "Current Plan",
                caption: "What the team should do next",
                badge: nextActions.isEmpty ? nil : "\(min(nextActions.count, 9))"
            ),
            MobileRelayDashboardModel.SidebarItem(
                section: .findings,
                title: "Findings",
                caption: "Why the run is blocked or risky",
                badge: pendingCount > 0 ? "\(pendingCount)" : nil
            ),
            MobileRelayDashboardModel.SidebarItem(
                section: .agents,
                title: "Agents",
                caption: "Codex, Claude, and operator lanes",
                badge: "\(lanes.count)"
            ),
            MobileRelayDashboardModel.SidebarItem(
                section: .actions,
                title: "Safe Actions",
                caption: "Repo-owned commands only",
                badge: safeActions.isEmpty ? nil : "\(safeActions.count)"
            ),
            MobileRelayDashboardModel.SidebarItem(
                section: .technical,
                title: "Technical",
                caption: "IDs, hashes, and bridge timing",
                badge: bridgeState.uppercased()
            ),
        ]

        let metrics = [
            MobileRelayDashboardModel.MetricCard(
                id: "phase",
                title: "Phase",
                value: phase.capitalized,
                detail: reason.replacingOccurrences(of: "_", with: " ")
            ),
            MobileRelayDashboardModel.MetricCard(
                id: "risk",
                title: "Risk",
                value: risk.capitalized,
                detail: "\(unresolvedCount) unresolved items"
            ),
            MobileRelayDashboardModel.MetricCard(
                id: "bridge",
                title: "Bridge",
                value: bridgeState.capitalized,
                detail: "Last Codex poll: \(lastPollUTC)"
            ),
            MobileRelayDashboardModel.MetricCard(
                id: "lanes",
                title: "Lanes",
                value: "\(lanes.count)",
                detail: "\(pendingCount) pending review packets"
            ),
        ]

        let instructionCard = MobileRelayDashboardModel.NarrativeCard(
            id: "instruction",
            title: "Current Plan",
            simpleBody: simplifyInstruction(
                currentInstruction,
                phase: phase,
                bridgeState: bridgeState
            ),
            technicalBody: currentInstruction,
            footnote: nextActions.isEmpty ? nil : "Next actions are taken directly from the mobile relay projection."
        )
        let findingsCard = MobileRelayDashboardModel.NarrativeCard(
            id: "findings",
            title: "Open Findings",
            simpleBody: simplifyFindings(
                openFindings,
                unresolvedCount: unresolvedCount,
                pendingCount: pendingCount
            ),
            technicalBody: openFindings,
            footnote: alert?.summary?.trimmedNonEmpty
        )
        let actionsNarrative = MobileRelayDashboardModel.NarrativeCard(
            id: "actions",
            title: "Safe Actions",
            simpleBody: safeActions.isEmpty
                ? "No safe actions were emitted yet. Refresh the mobile bundle first."
                : "These buttons are repo-owned command previews. They stay bounded and policy-aware.",
            technicalBody: actions?.summary?.trimmedNonEmpty
                ?? "Actions come from `devctl mobile-status` projection output and remain read-first by default.",
            footnote: alert?.commands?.first
        )

        let technicalFacts = [
            MobileRelayDashboardModel.TechnicalFact(id: "plan", label: "Plan ID", value: planID),
            MobileRelayDashboardModel.TechnicalFact(id: "run", label: "Run ID", value: runID),
            MobileRelayDashboardModel.TechnicalFact(id: "hash", label: "Worktree Hash", value: worktreeHash),
            MobileRelayDashboardModel.TechnicalFact(id: "poll", label: "Last Codex Poll", value: lastPollUTC),
            MobileRelayDashboardModel.TechnicalFact(id: "bridge", label: "Bridge State", value: bridgeState),
            MobileRelayDashboardModel.TechnicalFact(id: "url", label: "Source Run URL", value: sourceRunURL.isEmpty ? "Unavailable" : sourceRunURL),
        ]

        return MobileRelayDashboardModel(
            headline: compact?.headline?.trimmedNonEmpty ?? "\(phase.capitalized) | review \(bridgeState) | risk \(risk)",
            subheadline: "Shared mobile relay bundle used by the PyQt console and phone client.",
            sections: sections,
            metrics: metrics,
            instruction: instructionCard,
            findings: findingsCard,
            actionsNarrative: actionsNarrative,
            lanes: lanes,
            actions: safeActions,
            nextActions: nextActions,
            technicalFacts: technicalFacts,
            sourceRunURL: sourceRunURL
        )
    }

    private static func laneCards(from snapshot: MobileRelaySnapshot) -> [MobileRelayDashboardModel.LaneCard] {
        let registryAgents = snapshot.reviewPayload.agentRegistry?.agents ?? []
        if !registryAgents.isEmpty {
            return registryAgents.map {
                MobileRelayDashboardModel.LaneCard(
                    id: $0.agentID?.trimmedNonEmpty ?? UUID().uuidString,
                    title: $0.displayName?.trimmedNonEmpty ?? $0.agentID?.trimmedNonEmpty ?? "Agent",
                    subtitle: $0.laneTitle?.trimmedNonEmpty
                        ?? $0.currentJob?.trimmedNonEmpty
                        ?? $0.provider?.trimmedNonEmpty
                        ?? "Unassigned",
                    status: $0.jobState?.trimmedNonEmpty ?? "unknown",
                    provider: $0.provider?.trimmedNonEmpty,
                    branch: $0.branch?.trimmedNonEmpty,
                    worktree: $0.worktree?.trimmedNonEmpty
                )
            }
        }
        let reviewAgents = snapshot.reviewPayload.reviewState?.agents ?? []
        return reviewAgents.map {
            MobileRelayDashboardModel.LaneCard(
                id: $0.agentID?.trimmedNonEmpty ?? UUID().uuidString,
                title: $0.displayName?.trimmedNonEmpty ?? $0.agentID?.trimmedNonEmpty ?? "Agent",
                subtitle: $0.role?.trimmedNonEmpty ?? $0.lane?.trimmedNonEmpty ?? "Lane",
                status: $0.status?.trimmedNonEmpty ?? "unknown",
                provider: nil,
                branch: nil,
                worktree: nil
            )
        }
    }

    private static func actionCards(
        from actions: MobileActionsProjection?
    ) -> [MobileRelayDashboardModel.SafeActionCard] {
        let rows = actions?.operatorActions ?? []
        return rows.compactMap { row in
            guard let title = row.name?.trimmedNonEmpty,
                  let command = row.command?.trimmedNonEmpty else {
                return nil
            }
            return MobileRelayDashboardModel.SafeActionCard(
                id: row.id,
                title: title,
                summary: actionSummary(for: title, kind: row.kind?.trimmedNonEmpty),
                command: command,
                kind: row.kind?.trimmedNonEmpty ?? "unknown",
                guardText: row.guardText?.trimmedNonEmpty ?? "repo-owned"
            )
        }
    }

    private static func actionSummary(for title: String, kind: String?) -> String {
        switch title {
        case "refresh-mobile-status":
            return "Refresh the shared phone + review snapshot without mutating repo state."
        case "review-status":
            return "Inspect the current review bridge packet and lane state."
        case "phone-trace":
            return "Open the raw controller trace when the simple view is not enough."
        default:
            return kind == "write"
                ? "Guarded repo action. Review the command preview before running it."
                : "Read-only repo action exposed through the shared mobile bundle."
        }
    }

    private static func simplifyInstruction(
        _ instruction: String,
        phase: String,
        bridgeState: String
    ) -> String {
        "The run is \(phase). Review bridge is \(bridgeState). Next step: \(instruction)"
    }

    private static func simplifyFindings(
        _ findings: String,
        unresolvedCount: Int,
        pendingCount: Int
    ) -> String {
        "There are \(unresolvedCount) unresolved items and \(pendingCount) pending review packets. Main issue: \(findings)"
    }
}

private extension String {
    var trimmedNonEmpty: String? {
        let value = trimmingCharacters(in: .whitespacesAndNewlines)
        return value.isEmpty ? nil : value
    }

    var trimmedOrUnknown: String {
        trimmedNonEmpty ?? "unknown"
    }
}
