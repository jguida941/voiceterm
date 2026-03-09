import SwiftUI
import UniformTypeIdentifiers
import VoiceTermMobileCore

struct MobileRelayAppRootView: View {
    @ObservedObject var model: MobileRelayAppModel
    @State private var showingImporter = false

    var body: some View {
        VoiceTermMobileDashboardView(bundle: model.bundle)
            .safeAreaInset(edge: .top, spacing: 0) {
                controlStrip
            }
            .fileImporter(
                isPresented: $showingImporter,
                allowedContentTypes: [.folder],
                allowsMultipleSelection: false,
                onCompletion: handleImport
            )
    }

    private var controlStrip: some View {
        VStack(spacing: 0) {
            HStack(spacing: 12) {
                VStack(alignment: .leading, spacing: 3) {
                    Text(model.sourceTitle)
                        .font(.caption.weight(.bold))
                        .foregroundStyle(.white.opacity(0.85))
                    Text(model.sourceDetail)
                        .font(.caption2)
                        .foregroundStyle(.white.opacity(0.70))
                        .lineLimit(1)
                }
                Spacer()
                Button("Import Bundle") {
                    showingImporter = true
                }
                .buttonStyle(.borderedProminent)

                Button("Reload") {
                    model.reload()
                }
                .buttonStyle(.bordered)
                .disabled(!model.hasImportedBundle)

                Button("Use Sample") {
                    model.useSampleBundle()
                }
                .buttonStyle(.bordered)
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 12)
            .background(.ultraThinMaterial)

            if let lastError = model.lastError, !lastError.isEmpty {
                HStack(spacing: 10) {
                    Image(systemName: "exclamationmark.triangle.fill")
                    Text(lastError)
                        .font(.caption)
                        .multilineTextAlignment(.leading)
                    Spacer()
                }
                .padding(.horizontal, 16)
                .padding(.vertical, 10)
                .background(Color(red: 0.44, green: 0.17, blue: 0.17))
                .foregroundStyle(.white)
            }
        }
    }

    private func handleImport(_ result: Result<[URL], Error>) {
        switch result {
        case .success(let urls):
            guard let url = urls.first else {
                return
            }
            model.importBundle(from: url)
        case .failure(let error):
            model.recordImportError(error)
        }
    }
}
