import Foundation
import Testing
@testable import VoiceTermMobileCore

@Test
func decodesDaemonReadyLifecycleMetadata() throws {
    let payload = """
    {
      "event": "daemon_ready",
      "version": "1.1.1",
      "socket_path": "/tmp/voiceterm.sock",
      "ws_port": 9876,
      "ws_url": "ws://127.0.0.1:9876",
      "lifecycle": "running",
      "primary_attach": "web_socket",
      "pid": 4242,
      "started_at_unix_ms": 123456,
      "working_dir": "/tmp/repo",
      "memory_mode": "assist"
    }
    """

    let event = try JSONDecoder().decode(
        DaemonWebSocketClient.DaemonEvent.self,
        from: Data(payload.utf8)
    )

    #expect(event.event == "daemon_ready")
    #expect(event.version == "1.1.1")
    #expect(event.socketPath == "/tmp/voiceterm.sock")
    #expect(event.wsPort == 9876)
    #expect(event.wsURL == "ws://127.0.0.1:9876")
    #expect(event.lifecycle == "running")
    #expect(event.primaryAttach == "web_socket")
    #expect(event.pid == 4242)
    #expect(event.startedAtUnixMs == 123456)
    #expect(event.workingDir == "/tmp/repo")
    #expect(event.memoryMode == "assist")
}

@Test
func decodesDaemonStatusLifecycleMetadata() throws {
    let payload = """
    {
      "event": "daemon_status",
      "version": "1.1.1",
      "active_agents": 2,
      "connected_clients": 3,
      "uptime_secs": 42.5,
      "socket_path": "/tmp/voiceterm.sock",
      "ws_port": 9876,
      "ws_url": "ws://127.0.0.1:9876",
      "lifecycle": "running",
      "primary_attach": "web_socket",
      "pid": 4242,
      "started_at_unix_ms": 123456,
      "working_dir": "/tmp/repo",
      "memory_mode": "assist"
    }
    """

    let event = try JSONDecoder().decode(
        DaemonWebSocketClient.DaemonEvent.self,
        from: Data(payload.utf8)
    )

    #expect(event.event == "daemon_status")
    #expect(event.activeAgents == 2)
    #expect(event.connectedClients == 3)
    #expect(event.uptimeSecs == 42.5)
    #expect(event.wsURL == "ws://127.0.0.1:9876")
    #expect(event.lifecycle == "running")
    #expect(event.primaryAttach == "web_socket")
    #expect(event.memoryMode == "assist")
}
