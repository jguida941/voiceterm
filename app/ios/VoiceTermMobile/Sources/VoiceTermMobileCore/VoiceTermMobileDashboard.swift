#if canImport(SwiftUI)
import SwiftUI

public struct VoiceTermMobileDashboardView: View {
    @State private var audienceMode: MobileAudienceMode
    @State private var selectedSection: MobileRelaySection
    @State private var columnVisibility: NavigationSplitViewVisibility = .all

    private let model: MobileRelayDashboardModel

    public init(
        snapshot: MobileRelaySnapshot,
        audienceMode: MobileAudienceMode = .simple,
        selectedSection: MobileRelaySection = .overview
    ) {
        self._audienceMode = State(initialValue: audienceMode)
        self._selectedSection = State(initialValue: selectedSection)
        self.model = MobileRelayPresenter.buildDashboard(from: snapshot)
    }

    public init(
        bundle: MobileRelayProjectionBundle,
        audienceMode: MobileAudienceMode = .simple,
        selectedSection: MobileRelaySection = .overview
    ) {
        self._audienceMode = State(initialValue: audienceMode)
        self._selectedSection = State(initialValue: selectedSection)
        self.model = MobileRelayPresenter.buildDashboard(from: bundle)
    }

    public var body: some View {
        NavigationSplitView(columnVisibility: $columnVisibility) {
            sidebar
        } detail: {
            detailContent
        }
        .navigationSplitViewStyle(.balanced)
        .background(appBackground)
    }

    private var sidebar: some View {
        List {
            Section {
                VStack(alignment: .leading, spacing: 10) {
                    Text("VoiceTerm Mobile")
                        .font(.system(size: 26, weight: .bold, design: .rounded))
                    Text(model.subheadline)
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                }
                .padding(.vertical, 8)
                .listRowBackground(Color.clear)
            }

            Section("Workspace") {
                ForEach(model.sections) { item in
                    Button {
                        selectedSection = item.section
                    } label: {
                        sidebarRow(item)
                    }
                    .buttonStyle(.plain)
                    .listRowBackground(
                        item.section == selectedSection
                            ? Color.white.opacity(0.08)
                            : Color.clear
                    )
                }
            }

            Section("Read Mode") {
                Picker("Read mode", selection: $audienceMode) {
                    ForEach(MobileAudienceMode.allCases, id: \.self) { mode in
                        Text(mode.label).tag(mode)
                    }
                }
                .pickerStyle(.segmented)
                .listRowInsets(EdgeInsets(top: 10, leading: 12, bottom: 10, trailing: 12))
            }
        }
        .scrollContentBackground(.hidden)
        .background(appBackground)
    }

    private var detailContent: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                heroCard
                metricsGrid
                sectionView(for: selectedSection)
            }
            .padding(20)
        }
        .background(appBackground.ignoresSafeArea())
    }

    private func sidebarRow(_ item: MobileRelayDashboardModel.SidebarItem) -> some View {
        HStack(alignment: .top, spacing: 12) {
            VStack(alignment: .leading, spacing: 3) {
                Text(item.title)
                    .font(.subheadline.weight(item.section == selectedSection ? .bold : .semibold))
                Text(item.caption)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            Spacer()
            if let badge = item.badge, !badge.isEmpty {
                Text(badge)
                    .font(.caption.weight(.bold))
                    .padding(.horizontal, 10)
                    .padding(.vertical, 5)
                    .background(.white.opacity(0.10))
                    .clipShape(Capsule())
            }
        }
        .padding(.vertical, 6)
    }

    private var heroCard: some View {
        VStack(alignment: .leading, spacing: 14) {
            Text(model.headline)
                .font(.system(size: 28, weight: .bold, design: .rounded))
            Text(audienceMode == .simple ? model.instruction.simpleBody : model.instruction.technicalBody)
                .font(.body)
                .foregroundStyle(.secondary)
            if !model.nextActions.isEmpty {
                VStack(alignment: .leading, spacing: 8) {
                    Text("Next Actions")
                        .font(.caption.weight(.semibold))
                        .foregroundStyle(.secondary)
                    ForEach(model.nextActions.prefix(4), id: \.self) { action in
                        Label(action, systemImage: "arrow.forward.circle.fill")
                            .font(.subheadline)
                    }
                }
            }
        }
        .padding(22)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(heroBackground)
    }

    private var metricsGrid: some View {
        LazyVGrid(
            columns: [
                GridItem(.adaptive(minimum: 140), spacing: 12),
            ],
            spacing: 12
        ) {
            ForEach(model.metrics) { metric in
                VStack(alignment: .leading, spacing: 8) {
                    Text(metric.title.uppercased())
                        .font(.caption2.weight(.bold))
                        .foregroundStyle(.secondary)
                    Text(metric.value)
                        .font(.title3.weight(.semibold))
                    Text(metric.detail)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                .padding(16)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(cardBackground)
            }
        }
    }

    @ViewBuilder
    private func sectionView(for section: MobileRelaySection) -> some View {
        switch section {
        case .overview:
            VStack(alignment: .leading, spacing: 16) {
                narrativeCard(model.instruction)
                narrativeCard(model.findings)
            }
        case .instruction:
            narrativeCard(model.instruction)
        case .findings:
            narrativeCard(model.findings)
        case .agents:
            lanesBoard
        case .actions:
            VStack(alignment: .leading, spacing: 16) {
                narrativeCard(model.actionsNarrative)
                actionsBoard
            }
        case .technical:
            technicalBoard
        }
    }

    private func narrativeCard(_ card: MobileRelayDashboardModel.NarrativeCard) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(card.title)
                .font(.headline)
            Text(audienceMode == .simple ? card.simpleBody : card.technicalBody)
                .foregroundStyle(.secondary)
            if let footnote = card.footnote, !footnote.isEmpty {
                Divider().overlay(.white.opacity(0.08))
                Text(footnote)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .padding(20)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(cardBackground)
    }

    private var lanesBoard: some View {
        VStack(alignment: .leading, spacing: 14) {
            Text("Agent Lanes")
                .font(.headline)
            if model.lanes.isEmpty {
                emptyState("No agent lanes are present in the current bundle.")
            } else {
                ForEach(model.lanes) { lane in
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            VStack(alignment: .leading, spacing: 3) {
                                Text(lane.title)
                                    .font(.subheadline.weight(.semibold))
                                Text(lane.subtitle)
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                            Spacer()
                            Text(lane.status.capitalized)
                                .font(.caption.weight(.bold))
                                .padding(.horizontal, 10)
                                .padding(.vertical, 5)
                                .background(.white.opacity(0.08))
                                .clipShape(Capsule())
                        }
                        if audienceMode == .technical {
                            if let provider = lane.provider, !provider.isEmpty {
                                Text("Provider: \(provider)")
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                            if let branch = lane.branch, !branch.isEmpty {
                                Text("Branch: \(branch)")
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                            if let worktree = lane.worktree, !worktree.isEmpty {
                                Text("Worktree: \(worktree)")
                                    .font(.caption2)
                                    .foregroundStyle(.secondary)
                            }
                        }
                    }
                    .padding(16)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .background(.white.opacity(0.04))
                    .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
                }
            }
        }
        .padding(20)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(cardBackground)
    }

    private var actionsBoard: some View {
        VStack(alignment: .leading, spacing: 14) {
            Text("Safe Actions")
                .font(.headline)
            if model.actions.isEmpty {
                emptyState("No safe action cards were emitted for this bundle yet.")
            } else {
                ForEach(model.actions) { action in
                    VStack(alignment: .leading, spacing: 10) {
                        HStack {
                            Text(action.title)
                                .font(.subheadline.weight(.semibold))
                            Spacer()
                            Text(action.kind.capitalized)
                                .font(.caption.weight(.bold))
                                .padding(.horizontal, 10)
                                .padding(.vertical, 5)
                                .background(.white.opacity(0.08))
                                .clipShape(Capsule())
                        }
                        Text(action.summary)
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                        Text(action.command)
                            .font(.system(.caption, design: .monospaced))
                            .foregroundStyle(.secondary)
                            .textSelection(.enabled)
                        Text("Guard: \(action.guardText)")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                    .padding(16)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .background(.white.opacity(0.04))
                    .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
                }
            }
        }
        .padding(20)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(cardBackground)
    }

    private var technicalBoard: some View {
        VStack(alignment: .leading, spacing: 14) {
            Text("Technical")
                .font(.headline)
            ForEach(model.technicalFacts) { fact in
                HStack(alignment: .top) {
                    Text(fact.label)
                        .font(.caption.weight(.bold))
                        .foregroundStyle(.secondary)
                        .frame(width: 120, alignment: .leading)
                    Text(fact.value)
                        .font(.system(.caption, design: .monospaced))
                        .textSelection(.enabled)
                }
            }
        }
        .padding(20)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(cardBackground)
    }

    private func emptyState(_ message: String) -> some View {
        Text(message)
            .font(.subheadline)
            .foregroundStyle(.secondary)
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(16)
            .background(.white.opacity(0.04))
            .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
    }

    private var appBackground: some View {
        LinearGradient(
            colors: [
                Color(red: 0.05, green: 0.06, blue: 0.10),
                Color(red: 0.08, green: 0.10, blue: 0.16),
            ],
            startPoint: .topLeading,
            endPoint: .bottomTrailing
        )
    }

    private var heroBackground: some View {
        RoundedRectangle(cornerRadius: 30, style: .continuous)
            .fill(
                LinearGradient(
                    colors: [
                        Color(red: 0.17, green: 0.26, blue: 0.46),
                        Color(red: 0.10, green: 0.15, blue: 0.28),
                    ],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
            )
            .overlay(
                RoundedRectangle(cornerRadius: 30, style: .continuous)
                    .stroke(.white.opacity(0.10), lineWidth: 1)
            )
    }

    private var cardBackground: some View {
        RoundedRectangle(cornerRadius: 26, style: .continuous)
            .fill(.white.opacity(0.08))
            .overlay(
                RoundedRectangle(cornerRadius: 26, style: .continuous)
                    .stroke(.white.opacity(0.08), lineWidth: 1)
            )
    }
}
#endif
