import Combine
import Foundation
import VoiceTermMobileCore

@MainActor
final class MobileRelayAppModel: ObservableObject {
    @Published private(set) var bundle: MobileRelayProjectionBundle
    @Published private(set) var sourceTitle: String
    @Published private(set) var sourceDetail: String
    @Published private(set) var lastError: String?

    private var importedDirectoryURL: URL?

    private static let bookmarkKey = "VoiceTermMobile.importedBundleBookmark"

    init() {
        self.bundle = MobileRelayPreviewData.sampleBundle()
        self.sourceTitle = "Sample Bundle"
        self.sourceDetail = "Built-in preview data"
        self.lastError = nil
        restoreImportedBundleIfPresent()
    }

    var hasImportedBundle: Bool {
        importedDirectoryURL != nil
    }

    func importBundle(from directoryURL: URL) {
        do {
            let loadedBundle = try loadBundle(from: directoryURL)
            bundle = loadedBundle
            importedDirectoryURL = directoryURL
            sourceTitle = "Imported Bundle"
            sourceDetail = directoryURL.lastPathComponent
            lastError = nil
            try saveBookmark(for: directoryURL)
        } catch {
            lastError = error.localizedDescription
        }
    }

    func reload() {
        guard let importedDirectoryURL else {
            lastError = "No imported bundle is available yet."
            return
        }
        importBundle(from: importedDirectoryURL)
    }

    func useSampleBundle() {
        bundle = MobileRelayPreviewData.sampleBundle()
        importedDirectoryURL = nil
        sourceTitle = "Sample Bundle"
        sourceDetail = "Built-in preview data"
        lastError = nil
        UserDefaults.standard.removeObject(forKey: Self.bookmarkKey)
    }

    func recordImportError(_ error: Error) {
        lastError = error.localizedDescription
    }

    private func restoreImportedBundleIfPresent() {
        guard let directoryURL = resolvedBookmarkURL() else {
            return
        }
        do {
            let loadedBundle = try loadBundle(from: directoryURL)
            bundle = loadedBundle
            importedDirectoryURL = directoryURL
            sourceTitle = "Imported Bundle"
            sourceDetail = directoryURL.lastPathComponent
            lastError = nil
        } catch {
            lastError = error.localizedDescription
        }
    }

    private func loadBundle(from directoryURL: URL) throws -> MobileRelayProjectionBundle {
        let didAccess = directoryURL.startAccessingSecurityScopedResource()
        defer {
            if didAccess {
                directoryURL.stopAccessingSecurityScopedResource()
            }
        }
        return try MobileRelayStore.loadBundle(from: directoryURL)
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
