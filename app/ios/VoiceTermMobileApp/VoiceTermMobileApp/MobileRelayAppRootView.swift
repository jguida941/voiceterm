import SwiftUI
import UniformTypeIdentifiers
import VoiceTermMobileCore

struct MobileRelayAppRootView: View {
    @ObservedObject var model: MobileRelayAppModel
    @AppStorage("VoiceTermMobile.showTutorial") private var shouldShowTutorial = true
    @State private var showingImporter = false
    @State private var showingTutorial = false
    @State private var controlsExpanded = true

    var body: some View {
        VoiceTermMobileDashboardView(bundle: model.bundle)
            .safeAreaInset(edge: .top, spacing: 0) {
                controlStrip
            }
            .sheet(isPresented: $showingTutorial) {
                tutorialSheet
            }
            .fileImporter(
                isPresented: $showingImporter,
                allowedContentTypes: [.folder, .json],
                allowsMultipleSelection: false,
                onCompletion: handleImport
            )
            .onAppear {
                if shouldShowTutorial {
                    showingTutorial = true
                }
            }
    }

    private var controlStrip: some View {
        VStack(spacing: 0) {
            if controlsExpanded {
                expandedControlStrip
            } else {
                collapsedControlStrip
            }

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

    private var expandedControlStrip: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(alignment: .top, spacing: 12) {
                VStack(alignment: .leading, spacing: 3) {
                    Text("OPERATOR DECK")
                        .font(.system(.caption2, design: .monospaced).weight(.bold))
                        .tracking(1.4)
                        .foregroundStyle(.white.opacity(0.58))
                    Text(model.sourceTitle)
                        .font(.caption.weight(.bold))
                        .foregroundStyle(.white.opacity(0.85))
                    Text(model.sourceDetail)
                        .font(.caption2)
                        .foregroundStyle(.white.opacity(0.70))
                        .lineLimit(1)
                    Text("Import a bundle folder or the full.json file from mobile-status output.")
                        .font(.caption2)
                        .foregroundStyle(.white.opacity(0.56))
                        .fixedSize(horizontal: false, vertical: true)
                }
                Spacer()
                Button {
                    withAnimation(.easeInOut(duration: 0.18)) {
                        controlsExpanded = false
                    }
                } label: {
                    Image(systemName: "chevron.up")
                        .font(.caption.weight(.bold))
                }
                .buttonStyle(.bordered)
                .accessibilityLabel("Hide Controls")
            }

            HStack(spacing: 10) {
                Button("Import Bundle") {
                    showingImporter = true
                }
                .buttonStyle(.borderedProminent)
                .frame(maxWidth: .infinity)

                Button("Reload") {
                    if model.reload() {
                        collapseControls()
                    }
                }
                .buttonStyle(.bordered)
                .frame(maxWidth: .infinity)
                .disabled(!model.canReload)
            }

            HStack(spacing: 10) {
                Button("Tutorial") {
                    showingTutorial = true
                }
                .buttonStyle(.bordered)
                .frame(maxWidth: .infinity)

                Button("Use Live Repo Bundle") {
                    if model.useLiveBundle() {
                        collapseControls()
                    }
                }
                .buttonStyle(.bordered)
                .frame(maxWidth: .infinity)
                .disabled(!model.hasLiveBundle)

                Button("Use Sample Bundle") {
                    if model.useSampleBundle() {
                        collapseControls()
                    }
                }
                .buttonStyle(.bordered)
                .frame(maxWidth: .infinity)
            }

            Text("Phone shell mirrors the shared control bundle. Use live repo data when possible; sample mode is only a fallback.")
                .font(.caption2)
                .foregroundStyle(.white.opacity(0.56))
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 12)
        .background(.ultraThinMaterial)
    }

    private var collapsedControlStrip: some View {
        HStack(spacing: 10) {
            VStack(alignment: .leading, spacing: 2) {
                Text("CONTROL")
                    .font(.system(.caption2, design: .monospaced).weight(.bold))
                    .foregroundStyle(.white.opacity(0.55))
                Text(model.sourceTitle)
                    .font(.caption.weight(.bold))
                    .foregroundStyle(.white.opacity(0.85))
                Text(model.sourceDetail)
                    .font(.caption2)
                    .foregroundStyle(.white.opacity(0.60))
                    .lineLimit(1)
            }
            Spacer()
            if model.canReload {
                Button {
                    _ = model.reload()
                } label: {
                    Image(systemName: "arrow.clockwise")
                        .font(.caption.weight(.bold))
                }
                .buttonStyle(.bordered)
                .accessibilityLabel("Reload Live Data")
            }
            Button {
                withAnimation(.easeInOut(duration: 0.18)) {
                    controlsExpanded = true
                }
            } label: {
                Label("Controls", systemImage: "slider.horizontal.3")
                    .font(.caption.weight(.semibold))
            }
            .buttonStyle(.borderedProminent)
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 10)
        .background(.ultraThinMaterial)
    }

    private func handleImport(_ result: Result<[URL], Error>) {
        switch result {
        case .success(let urls):
            guard let url = urls.first else {
                return
            }
            if model.importBundle(from: url) {
                collapseControls()
            }
        case .failure(let error):
            model.recordImportError(error)
        }
    }

    private func collapseControls() {
        withAnimation(.easeInOut(duration: 0.18)) {
            controlsExpanded = false
        }
    }

    private var tutorialSheet: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 18) {
                    tutorialBlock(
                        title: "1. Real Data First",
                        body: "When a synced LiveBundle exists, the app now prefers it automatically instead of falling back to sample data."
                    )
                    tutorialBlock(
                        title: "2. If You Need To Load Data Manually",
                        body: "Use Import Bundle and choose the emitted mobile-status bundle folder or its full.json file."
                    )
                    tutorialBlock(
                        title: "3. What To Check",
                        body: "Overview should show the current plan and findings, Actions should show typed controller previews, and Terminal should show Codex, Claude, and Operator lane views."
                    )
                    tutorialBlock(
                        title: "4. Honesty Boundary",
                        body: "The app shows real repo-backed action previews, but execution still belongs to repo-owned devctl commands on the host machine."
                    )
                    tutorialBlock(
                        title: "5. Approval Mode",
                        body: "The mobile bundle now carries the shared approval policy. Safe local work can stay automatic, but destructive or publish-class actions still require approval."
                    )
                }
                .padding(20)
            }
            .navigationTitle("VoiceTerm Mobile")
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") {
                        shouldShowTutorial = false
                        showingTutorial = false
                    }
                }
            }
        }
    }

    private func tutorialBlock(title: String, body: String) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(title)
                .font(.headline)
            Text(body)
                .font(.body)
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(16)
        .background(.white.opacity(0.05))
        .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
    }
}
