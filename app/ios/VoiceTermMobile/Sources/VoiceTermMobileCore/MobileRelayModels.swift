import Foundation

public struct MobileRelaySnapshot: Codable, Equatable, Sendable {
    public let schemaVersion: Int?
    public let command: String?
    public let timestamp: String?
    public let sources: Sources?
    public let controllerPayload: ControllerPayload
    public let reviewPayload: ReviewPayload

    enum CodingKeys: String, CodingKey {
        case schemaVersion = "schema_version"
        case command
        case timestamp
        case sources
        case controllerPayload = "controller_payload"
        case reviewPayload = "review_payload"
    }
}

public struct Sources: Codable, Equatable, Sendable {
    public let phoneInputPath: String?
    public let reviewChannelPath: String?
    public let bridgePath: String?
    public let reviewStatusDir: String?

    enum CodingKeys: String, CodingKey {
        case phoneInputPath = "phone_input_path"
        case reviewChannelPath = "review_channel_path"
        case bridgePath = "bridge_path"
        case reviewStatusDir = "review_status_dir"
    }
}

public struct ControllerPayload: Codable, Equatable, Sendable {
    public let phase: String?
    public let reason: String?
    public let controller: ControllerState?
    public let loop: LoopState?
    public let sourceRun: SourceRun?
    public let warnings: [String]?
    public let errors: [String]?

    enum CodingKeys: String, CodingKey {
        case phase
        case reason
        case controller
        case loop
        case sourceRun = "source_run"
        case warnings
        case errors
    }
}

public struct ControllerState: Codable, Equatable, Sendable {
    public let planID: String?
    public let controllerRunID: String?
    public let branchBase: String?
    public let modeEffective: String?
    public let resolved: Bool?
    public let roundsCompleted: Int?
    public let maxRounds: Int?
    public let tasksCompleted: Int?
    public let maxTasks: Int?
    public let latestWorkingBranch: String?

    enum CodingKeys: String, CodingKey {
        case planID = "plan_id"
        case controllerRunID = "controller_run_id"
        case branchBase = "branch_base"
        case modeEffective = "mode_effective"
        case resolved
        case roundsCompleted = "rounds_completed"
        case maxRounds = "max_rounds"
        case tasksCompleted = "tasks_completed"
        case maxTasks = "max_tasks"
        case latestWorkingBranch = "latest_working_branch"
    }
}

public struct LoopState: Codable, Equatable, Sendable {
    public let unresolvedCount: Int?
    public let risk: String?
    public let nextActions: [String]?

    enum CodingKeys: String, CodingKey {
        case unresolvedCount = "unresolved_count"
        case risk
        case nextActions = "next_actions"
    }
}

public struct SourceRun: Codable, Equatable, Sendable {
    public let runID: Int?
    public let runSHA: String?
    public let runURL: String?

    enum CodingKeys: String, CodingKey {
        case runID = "run_id"
        case runSHA = "run_sha"
        case runURL = "run_url"
    }
}

public struct ReviewPayload: Codable, Equatable, Sendable {
    public let schemaVersion: Int?
    public let command: String?
    public let action: String?
    public let timestamp: String?
    public let ok: Bool?
    public let bridgeLiveness: BridgeLiveness?
    public let reviewState: ReviewState?
    public let agentRegistry: AgentRegistry?
    public let warnings: [String]?
    public let errors: [String]?

    enum CodingKeys: String, CodingKey {
        case schemaVersion = "schema_version"
        case command
        case action
        case timestamp
        case ok
        case bridgeLiveness = "bridge_liveness"
        case reviewState = "review_state"
        case agentRegistry = "agent_registry"
        case warnings
        case errors
    }
}

public struct BridgeLiveness: Codable, Equatable, Sendable {
    public let overallState: String?
    public let codexPollState: String?
    public let lastCodexPollUTC: String?
    public let lastCodexPollAgeSeconds: Int?
    public let nextActionPresent: Bool?
    public let openFindingsPresent: Bool?
    public let claudeStatusPresent: Bool?
    public let claudeAckPresent: Bool?

    enum CodingKeys: String, CodingKey {
        case overallState = "overall_state"
        case codexPollState = "codex_poll_state"
        case lastCodexPollUTC = "last_codex_poll_utc"
        case lastCodexPollAgeSeconds = "last_codex_poll_age_seconds"
        case nextActionPresent = "next_action_present"
        case openFindingsPresent = "open_findings_present"
        case claudeStatusPresent = "claude_status_present"
        case claudeAckPresent = "claude_ack_present"
    }
}

public struct ReviewState: Codable, Equatable, Sendable {
    public let schemaVersion: Int?
    public let command: String?
    public let projectID: String?
    public let timestamp: String?
    public let ok: Bool?
    public let review: ReviewMeta?
    public let agents: [ReviewAgent]?
    public let queue: ReviewQueue?
    public let bridge: ReviewBridge?

    enum CodingKeys: String, CodingKey {
        case schemaVersion = "schema_version"
        case command
        case projectID = "project_id"
        case timestamp
        case ok
        case review
        case agents
        case queue
        case bridge
    }
}

public struct ReviewMeta: Codable, Equatable, Sendable {
    public let planID: String?
    public let controllerRunID: String?
    public let sessionID: String?
    public let surfaceMode: String?
    public let activeLane: String?

    enum CodingKeys: String, CodingKey {
        case planID = "plan_id"
        case controllerRunID = "controller_run_id"
        case sessionID = "session_id"
        case surfaceMode = "surface_mode"
        case activeLane = "active_lane"
    }
}

public struct ReviewAgent: Codable, Equatable, Sendable {
    public let agentID: String?
    public let displayName: String?
    public let role: String?
    public let status: String?
    public let lane: String?

    enum CodingKeys: String, CodingKey {
        case agentID = "agent_id"
        case displayName = "display_name"
        case role
        case status
        case lane
    }
}

public struct ReviewQueue: Codable, Equatable, Sendable {
    public let pendingTotal: Int?
    public let stalePacketCount: Int?

    enum CodingKeys: String, CodingKey {
        case pendingTotal = "pending_total"
        case stalePacketCount = "stale_packet_count"
    }
}

public struct ReviewBridge: Codable, Equatable, Sendable {
    public let lastCodexPollUTC: String?
    public let lastWorktreeHash: String?
    public let openFindings: String?
    public let currentInstruction: String?
    public let claudeStatus: String?
    public let claudeAck: String?

    enum CodingKeys: String, CodingKey {
        case lastCodexPollUTC = "last_codex_poll_utc"
        case lastWorktreeHash = "last_worktree_hash"
        case openFindings = "open_findings"
        case currentInstruction = "current_instruction"
        case claudeStatus = "claude_status"
        case claudeAck = "claude_ack"
    }
}

public struct AgentRegistry: Codable, Equatable, Sendable {
    public let schemaVersion: Int?
    public let command: String?
    public let timestamp: String?
    public let agents: [RegistryAgent]?

    enum CodingKeys: String, CodingKey {
        case schemaVersion = "schema_version"
        case command
        case timestamp
        case agents
    }
}

public struct MobileCompactProjection: Codable, Equatable, Sendable {
    public let schemaVersion: Int?
    public let view: String?
    public let headline: String?
    public let controllerPhase: String?
    public let controllerReason: String?
    public let controllerRisk: String?
    public let planID: String?
    public let controllerRunID: String?
    public let reviewBridgeState: String?
    public let codexPollState: String?
    public let codexLastPollUTC: String?
    public let lastWorktreeHash: String?
    public let pendingTotal: Int?
    public let unresolvedCount: Int?
    public let currentInstruction: String?
    public let openFindings: String?
    public let codexStatus: String?
    public let claudeLaneStatus: String?
    public let operatorStatus: String?
    public let sourceRunURL: String?
    public let nextActions: [String]?

    enum CodingKeys: String, CodingKey {
        case schemaVersion = "schema_version"
        case view
        case headline
        case controllerPhase = "controller_phase"
        case controllerReason = "controller_reason"
        case controllerRisk = "controller_risk"
        case planID = "plan_id"
        case controllerRunID = "controller_run_id"
        case reviewBridgeState = "review_bridge_state"
        case codexPollState = "codex_poll_state"
        case codexLastPollUTC = "codex_last_poll_utc"
        case lastWorktreeHash = "last_worktree_hash"
        case pendingTotal = "pending_total"
        case unresolvedCount = "unresolved_count"
        case currentInstruction = "current_instruction"
        case openFindings = "open_findings"
        case codexStatus = "codex_status"
        case claudeLaneStatus = "claude_lane_status"
        case operatorStatus = "operator_status"
        case sourceRunURL = "source_run_url"
        case nextActions = "next_actions"
    }
}

public struct MobileAlertProjection: Codable, Equatable, Sendable {
    public let schemaVersion: Int?
    public let view: String?
    public let severity: String?
    public let summary: String?
    public let why: [String]?
    public let currentInstruction: String?
    public let nextActions: [String]?
    public let commands: [String]?

    enum CodingKeys: String, CodingKey {
        case schemaVersion = "schema_version"
        case view
        case severity
        case summary
        case why
        case currentInstruction = "current_instruction"
        case nextActions = "next_actions"
        case commands
    }
}

public struct MobileActionsProjection: Codable, Equatable, Sendable {
    public let schemaVersion: Int?
    public let view: String?
    public let summary: String?
    public let nextActions: [String]?
    public let operatorActions: [MobileOperatorAction]?

    enum CodingKeys: String, CodingKey {
        case schemaVersion = "schema_version"
        case view
        case summary
        case nextActions = "next_actions"
        case operatorActions = "operator_actions"
    }
}

public struct MobileOperatorAction: Codable, Equatable, Sendable, Identifiable {
    public let name: String?
    public let command: String?
    public let kind: String?
    public let guardText: String?

    public var id: String {
        let base = name?.trimmingCharacters(in: .whitespacesAndNewlines)
        return (base?.isEmpty == false ? base : command) ?? UUID().uuidString
    }

    enum CodingKeys: String, CodingKey {
        case name
        case command
        case kind
        case guardText = "guard"
    }
}

public struct MobileRelayProjectionBundle: Equatable, Sendable {
    public let snapshot: MobileRelaySnapshot
    public let compact: MobileCompactProjection?
    public let alert: MobileAlertProjection?
    public let actions: MobileActionsProjection?
}

public struct RegistryAgent: Codable, Equatable, Sendable, Identifiable {
    public let agentID: String?
    public let provider: String?
    public let displayName: String?
    public let currentJob: String?
    public let jobState: String?
    public let waitingOn: String?
    public let scriptProfile: String?
    public let lane: String?
    public let laneTitle: String?
    public let branch: String?
    public let worktree: String?

    public var id: String { agentID ?? UUID().uuidString }

    enum CodingKeys: String, CodingKey {
        case agentID = "agent_id"
        case provider
        case displayName = "display_name"
        case currentJob = "current_job"
        case jobState = "job_state"
        case waitingOn = "waiting_on"
        case scriptProfile = "script_profile"
        case lane
        case laneTitle = "lane_title"
        case branch
        case worktree
    }
}
