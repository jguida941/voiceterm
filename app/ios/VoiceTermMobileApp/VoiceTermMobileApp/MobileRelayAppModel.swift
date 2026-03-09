import Combine
import Foundation
import VoiceTermMobileCore

@MainActor
final class MobileRelayAppModel: ObservableObject {
    @Published private(set) var bundle: MobileRelayProjectionBundle
    @Published private(set) var sourceTitle: String
    @Published private(set) var sourceDetail: String
    @Published private(set) var lastError: String?

    private var importedBundleURL: URL?

    private static let bookmarkKey = "VoiceTermMobile.importedBundleBookmark"

    init() {
        self.bundle = MobileRelayPreviewData.sampleBundle()
        self.sourceTitle = "Sample Bundle"
        self.sourceDetail = "Built-in preview data"
        self.lastError = nil
        if !restoreImportedBundleIfPresent() {
            _ = restoreLiveBundleIfPresent()
        }
    }

    var hasImportedBundle: Bool {
        importedBundleURL != nil
    }

    var hasLiveBundle: Bool {
        liveBundleDirectoryURL != nil
    }

    var canReload: Bool {
        hasImportedBundle || hasLiveBundle
    }

    @discardableResult
    func importBundle(from selectionURL: URL) -> Bool {
        do {
            let loadedBundle = try loadBundle(from: selectionURL)
            bundle = loadedBundle
            importedBundleURL = normalizedImportedURL(for: selectionURL)
            sourceTitle = "Imported Bundle"
            sourceDetail = importedBundleURL?.lastPathComponent ?? selectionURL.lastPathComponent
            lastError = nil
            try saveBookmark(for: importedBundleURL ?? selectionURL)
            return true
        } catch {
            lastError = error.localizedDescription
            return false
        }
    }

    @discardableResult
    func reload() -> Bool {
        if let importedBundleURL {
            return importBundle(from: importedBundleURL)
        }
        if hasLiveBundle {
            return useLiveBundle()
        }
        lastError = "No imported or live bundle is available yet."
        return false
    }

    @discardableResult
    func useSampleBundle() -> Bool {
        bundle = MobileRelayPreviewData.sampleBundle()
        importedBundleURL = nil
        sourceTitle = "Sample Bundle"
        sourceDetail = "Built-in preview data"
        lastError = nil
        UserDefaults.standard.removeObject(forKey: Self.bookmarkKey)
        return true
    }

    @discardableResult
    func useLiveBundle() -> Bool {
        guard let liveBundleDirectoryURL else {
            lastError = "No live repo bundle has been synced into the app yet."
            return false
        }
        do {
            bundle = try MobileRelayStore.loadBundle(from: liveBundleDirectoryURL)
            importedBundleURL = nil
            sourceTitle = "Live Repo Bundle"
            sourceDetail = liveBundleDirectoryURL.lastPathComponent
            lastError = nil
            return true
        } catch {
            lastError = error.localizedDescription
            return false
        }
    }

    func recordImportError(_ error: Error) {
        lastError = error.localizedDescription
    }

    private func restoreImportedBundleIfPresent() -> Bool {
        guard let importedBundleURL = resolvedBookmarkURL() else {
            return false
        }
        do {
            let loadedBundle = try loadBundle(from: importedBundleURL)
            bundle = loadedBundle
            self.importedBundleURL = normalizedImportedURL(for: importedBundleURL)
            sourceTitle = "Imported Bundle"
            sourceDetail = self.importedBundleURL?.lastPathComponent ?? importedBundleURL.lastPathComponent
            lastError = nil
            return true
        } catch {
            lastError = error.localizedDescription
            return false
        }
    }

    @discardableResult
    private func restoreLiveBundleIfPresent() -> Bool {
        guard let liveBundleDirectoryURL else {
            return false
        }
        do {
            bundle = try MobileRelayStore.loadBundle(from: liveBundleDirectoryURL)
            importedBundleURL = nil
            sourceTitle = "Live Repo Bundle"
            sourceDetail = liveBundleDirectoryURL.lastPathComponent
            lastError = nil
            return true
        } catch {
            lastError = error.localizedDescription
            return false
        }
    }

    private func loadBundle(from selectionURL: URL) throws -> MobileRelayProjectionBundle {
        let didAccess = selectionURL.startAccessingSecurityScopedResource()
        defer {
            if didAccess {
                selectionURL.stopAccessingSecurityScopedResource()
            }
        }
        return try MobileRelayStore.loadBundleSelection(from: selectionURL)
    }

    private func normalizedImportedURL(for selectionURL: URL) -> URL {
        if selectionURL.hasDirectoryPath {
            return selectionURL
        }
        return selectionURL.lastPathComponent == "full.json"
            ? selectionURL.deletingLastPathComponent()
            : selectionURL
    }

    private var liveBundleDirectoryURL: URL? {
        guard let documentsURL = FileManager.default.urls(
            for: .documentDirectory,
            in: .userDomainMask
        ).first else {
            return nil
        }
        let bundleURL = documentsURL.appendingPathComponent("LiveBundle", isDirectory: true)
        let fullJSONURL = bundleURL.appendingPathComponent("full.json")
        return FileManager.default.fileExists(atPath: fullJSONURL.path) ? bundleURL : nil
    }

    private func saveBookmark(for directoryURL: URL) throws {
        let bookmark = try directoryURL.bookmarkData()
        UserDefaults.standard.set(bookmark, forKey: Self.bookmarkKey)
    }

    private func resolvedBookmarkURL() -> URL? {
        guard let bookmark = UserDefaults.standard.data(forKey: Self.bookmarkKey) else {
            return nil
        }
        var isStale = false
        #if os(macOS)
        let bookmarkOptions: URL.BookmarkResolutionOptions = [.withoutUI, .withSecurityScope]
        #else
        let bookmarkOptions: URL.BookmarkResolutionOptions = []
        #endif
        guard let url = try? URL(
            resolvingBookmarkData: bookmark,
            options: bookmarkOptions,
            relativeTo: nil,
            bookmarkDataIsStale: &isStale
        ) else {
            return nil
        }
        if isStale {
            try? saveBookmark(for: url)
        }
        return url
    }
}
