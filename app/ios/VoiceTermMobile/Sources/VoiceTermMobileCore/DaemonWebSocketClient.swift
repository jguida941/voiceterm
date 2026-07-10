import Foundation

/// Real-time WebSocket client for the VoiceTerm daemon hub.
///
/// Connects to the daemon's WebSocket bridge (default port 9876) for live
/// agent output streaming, spawn commands, and status queries. Replaces
/// static snapshot-based mobile relay with a persistent event stream.
///
/// Protocol: JSON-lines over WebSocket text frames.
/// - Send: ``DaemonCommand`` objects (``{"cmd":"spawn_agent", ...}``)
/// - Receive: ``DaemonEvent`` objects (``{"event":"agent_output", ...}``)
@MainActor
public final class DaemonWebSocketClient: ObservableObject {

    // MARK: - Published state

    @Published public private(set) var connectionState: ConnectionState = .disconnected
    @Published public private(set) var lastEvent: DaemonEvent?
    @Published public private(set) var agents: [AgentSnapshot] = []
    @Published public private(set) var daemonVersion: String?

    // MARK: - Configuration

    public let host: String
    public let port: UInt16

    // MARK: - Private

    private var webSocketTask: URLSessionWebSocketTask?
    private var urlSession: URLSession?
    private var eventHandlers: [(DaemonEvent) -> Void] = []

    // MARK: - Types

    public enum ConnectionState: Sendable {
        case disconnected
        case connecting
        case connected
        case failed(String)
    }

    public struct DaemonEvent: Codable, Sendable, Equatable {
        public let event: String
        public let sessionId: String?
        public let text: String?
        public let version: String?
        public let socketPath: String?
        public let wsPort: UInt16?
        public let wsURL: String?
        public let lifecycle: String?
        public let primaryAttach: String?
        public let provider: String?
        public let label: String?
        public let workingDir: String?
        public let pid: Int32?
        public let startedAtUnixMs: UInt64?
        public let memoryMode: String?
        public let exitCode: Int32?
        public let activeAgents: Int?
        public let connectedClients: Int?
        public let uptimeSecs: Double?
        public let message: String?
        public let agents: [AgentSnapshot]?

        enum CodingKeys: String, CodingKey {
            case event
            case sessionId = "session_id"
            case text
            case version
            case socketPath = "socket_path"
            case wsPort = "ws_port"
            case wsURL = "ws_url"
            case lifecycle
            case primaryAttach = "primary_attach"
            case provider
            case label
            case workingDir = "working_dir"
            case pid
            case startedAtUnixMs = "started_at_unix_ms"
            case memoryMode = "memory_mode"
            case exitCode = "exit_code"
            case activeAgents = "active_agents"
            case connectedClients = "connected_clients"
            case uptimeSecs = "uptime_secs"
            case message
            case agents
        }

        public var isOutput: Bool { event == "agent_output" }
        public var isError: Bool { event == "error" }
    }

    public struct AgentSnapshot: Codable, Sendable, Equatable, Identifiable {
        public let sessionId: String
        public let provider: String
        public let label: String
        public let workingDir: String
        public let pid: Int32
        public let isAlive: Bool

        public var id: String { sessionId }

        enum CodingKeys: String, CodingKey {
            case sessionId = "session_id"
            case provider
            case label
            case workingDir = "working_dir"
            case pid
            case isAlive = "is_alive"
        }
    }

    // MARK: - Init

    public init(host: String = "localhost", port: UInt16 = 9876) {
        self.host = host
        self.port = port
    }

    // MARK: - Connection

    public func connect() {
        guard case .disconnected = connectionState else { return }
        connectionState = .connecting

        let url = URL(string: "ws://\(host):\(port)")!
        let session = URLSession(configuration: .default)
        let task = session.webSocketTask(with: url)
        self.urlSession = session
        self.webSocketTask = task
        task.resume()
        connectionState = .connected
        receiveLoop()
    }

    public func disconnect() {
        webSocketTask?.cancel(with: .normalClosure, reason: nil)
        webSocketTask = nil
        urlSession?.invalidateAndCancel()
        urlSession = nil
        connectionState = .disconnected
    }

    // MARK: - Commands

    public func spawnAgent(
        provider: String,
        workingDir: String? = nil,
        label: String? = nil,
        initialPrompt: String? = nil
    ) {
        var cmd: [String: Any] = ["cmd": "spawn_agent", "provider": provider]
        if let wd = workingDir { cmd["working_dir"] = wd }
        if let lbl = label { cmd["label"] = lbl }
        if let prompt = initialPrompt { cmd["initial_prompt"] = prompt }
        sendCommand(cmd)
    }

    public func sendToAgent(sessionId: String, text: String) {
        sendCommand(["cmd": "send_to_agent", "session_id": sessionId, "text": text])
    }

    public func killAgent(sessionId: String) {
        sendCommand(["cmd": "kill_agent", "session_id": sessionId])
    }

    public func listAgents() {
        sendCommand(["cmd": "list_agents"])
    }

    public func getStatus() {
        sendCommand(["cmd": "get_status"])
    }

    public func requestShutdown() {
        sendCommand(["cmd": "shutdown"])
    }

    // MARK: - Event observation

    public func onEvent(_ handler: @escaping (DaemonEvent) -> Void) {
        eventHandlers.append(handler)
    }

    // MARK: - Private

    private func sendCommand(_ dict: [String: Any]) {
        guard let data = try? JSONSerialization.data(withJSONObject: dict),
              let text = String(data: data, encoding: .utf8) else {
            return
        }
        webSocketTask?.send(.string(text)) { error in
            if let error {
                Task { @MainActor in
                    self.connectionState = .failed(error.localizedDescription)
                }
            }
        }
    }

    private func receiveLoop() {
        webSocketTask?.receive { [weak self] result in
            Task { @MainActor in
                guard let self else { return }
                switch result {
                case .success(let message):
                    self.handleMessage(message)
                    self.receiveLoop()
                case .failure(let error):
                    self.connectionState = .failed(error.localizedDescription)
                }
            }
        }
    }

    private func handleMessage(_ message: URLSessionWebSocketTask.Message) {
        guard case .string(let text) = message else { return }
        let decoder = JSONDecoder()
        guard let data = text.data(using: .utf8),
              let event = try? decoder.decode(DaemonEvent.self, from: data) else {
            return
        }

        lastEvent = event
        applyEvent(event)

        for handler in eventHandlers {
            handler(event)
        }
    }

    private func applyEvent(_ event: DaemonEvent) {
        switch event.event {
        case "daemon_ready":
            daemonVersion = event.version
        case "agent_spawned":
            if let sid = event.sessionId,
               let provider = event.provider,
               let label = event.label {
                let snapshot = AgentSnapshot(
                    sessionId: sid,
                    provider: provider,
                    label: label,
                    workingDir: event.workingDir ?? ".",
                    pid: event.pid ?? 0,
                    isAlive: true
                )
                agents.append(snapshot)
            }
        case "agent_exited", "agent_killed":
            if let sid = event.sessionId {
                agents.removeAll { $0.sessionId == sid }
            }
        case "agent_list":
            if let list = event.agents {
                agents = list
            }
        case "daemon_shutdown":
            agents.removeAll()
            connectionState = .disconnected
        default:
            break
        }
    }
}
