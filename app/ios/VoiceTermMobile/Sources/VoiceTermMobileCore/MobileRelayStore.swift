import Foundation

public enum MobileRelayStoreError: Error, LocalizedError, Equatable {
    case fileNotFound(String)
    case invalidPayload(String)

    public var errorDescription: String? {
        switch self {
        case .fileNotFound(let path):
            return "Mobile relay file not found: \(path)"
        case .invalidPayload(let message):
            return "Invalid mobile relay payload: \(message)"
        }
    }
}

public enum MobileRelayStore {
    public static func loadSnapshot(from fileURL: URL) throws -> MobileRelaySnapshot {
        guard FileManager.default.fileExists(atPath: fileURL.path) else {
            throw MobileRelayStoreError.fileNotFound(fileURL.path)
        }
        let data = try Data(contentsOf: fileURL)
        do {
            return try JSONDecoder().decode(MobileRelaySnapshot.self, from: data)
        } catch {
            throw MobileRelayStoreError.invalidPayload(error.localizedDescription)
        }
    }

    public static func loadBundle(from directoryURL: URL) throws -> MobileRelayProjectionBundle {
        let snapshot = try loadSnapshot(from: directoryURL.appendingPathComponent("full.json"))
        let compact = try loadOptionalProjection(
            MobileCompactProjection.self,
            from: directoryURL.appendingPathComponent("compact.json")
        )
        let alert = try loadOptionalProjection(
            MobileAlertProjection.self,
            from: directoryURL.appendingPathComponent("alert.json")
        )
        let actions = try loadOptionalProjection(
            MobileActionsProjection.self,
            from: directoryURL.appendingPathComponent("actions.json")
        )
        return MobileRelayProjectionBundle(
            snapshot: snapshot,
            compact: compact,
            alert: alert,
            actions: actions
        )
    }

    private static func loadOptionalProjection<T: Decodable>(
        _ type: T.Type,
        from fileURL: URL
    ) throws -> T? {
        guard FileManager.default.fileExists(atPath: fileURL.path) else {
            return nil
        }
        let data = try Data(contentsOf: fileURL)
        do {
            return try JSONDecoder().decode(type, from: data)
        } catch {
            throw MobileRelayStoreError.invalidPayload(
                "\(fileURL.lastPathComponent): \(error.localizedDescription)"
            )
        }
    }
}
