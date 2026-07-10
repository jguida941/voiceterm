#if canImport(SwiftUI)
import SwiftUI

public struct VoiceTermMobileDashboardView: View {
    @State private var audienceMode: MobileAudienceMode
    @State private var selectedSection: MobileRelaySection
    @State private var columnVisibility: NavigationSplitViewVisibility = .all
    @State private var consoleLayout: ConsoleLayout = .split

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
                    Text("VoiceTerm Control")
                        .font(.system(size: 26, weight: .bold, design: .rounded))
                    Text(model.subheadline)
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                    Text("PHONE CONSOLE")
                        .font(.system(.caption2, design: .monospaced).weight(.bold))
                        .tracking(1.4)
                        .foregroundStyle(.white.opacity(0.55))
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
            HStack(alignment: .top) {
                VStack(alignment: .leading, spacing: 6) {
                    Text("CONTROL PANEL")
                        .font(.system(.caption, design: .monospaced).weight(.bold))
                        .tracking(1.8)
                        .foregroundStyle(.white.opacity(0.60))
                    Text(model.headline)
                        .font(.system(size: 28, weight: .bold, design: .rounded))
                }
                Spacer()
                statusChip("Approval", value: model.approvalMode.capitalized)
            }
            Text(audienceMode == .simple ? model.instruction.simpleBody : model.instruction.technicalBody)
                .font(.body)
                .foregroundStyle(.secondary)
            controlRail
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
            if let firstRestricted = model.approvalRequiresConfirmation.first {
                Text("Still requires confirmation: \(firstRestricted)")
                    .font(.caption)
                    .foregroundStyle(.white.opacity(0.72))
            }
        }
        .padding(22)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(heroBackground)
    }

    private var controlRail: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 10) {
                statusChip("Bridge", value: metricValue(for: "Bridge"))
                statusChip("Risk", value: metricValue(for: "Risk"))
                statusChip("Phase", value: metricValue(for: "Phase"))
                statusChip("Lanes", value: metricValue(for: "Lanes"))
            }
        }
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
        case .console:
            consoleBoard
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
            approvalPanel
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

    private var approvalPanel: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Text("Approval Policy")
                    .font(.subheadline.weight(.semibold))
                Spacer()
                statusChip("Mode", value: model.approvalMode.capitalized)
            }
            Text(model.approvalSummary)
                .font(.subheadline)
                .foregroundStyle(.secondary)
            if !model.approvalRequiresConfirmation.isEmpty {
                VStack(alignment: .leading, spacing: 6) {
                    ForEach(model.approvalRequiresConfirmation.prefix(4), id: \.self) { item in
                        Label(item, systemImage: "hand.raised.fill")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }
            }
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(.white.opacity(0.04))
        .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
    }

    private var consoleBoard: some View {
        VStack(alignment: .leading, spacing: 14) {
            HStack(alignment: .center) {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Lane Console")
                        .font(.headline)
                    Text("Read-only terminal-style view over the live review-channel bundle.")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                Spacer()
                Picker("Layout", selection: $consoleLayout) {
                    ForEach(ConsoleLayout.allCases, id: \.self) { layout in
                        Text(layout.label).tag(layout)
                    }
                }
                .pickerStyle(.segmented)
                .frame(maxWidth: 190)
            }

            if model.consolePanes.isEmpty {
                emptyState("No lane console data is present in the current bundle.")
            } else if consoleLayout == .combined {
                combinedConsoleCard
            } else {
                ForEach(model.consolePanes) { pane in
                    consoleCard(pane)
                }
            }
        }
        .padding(20)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(cardBackground)
    }

    private var combinedConsoleCard: some View {
        let combinedText = model.consolePanes.map { pane in
            """
            [\(pane.title.lowercased())]
            \(audienceMode == .simple ? pane.simpleBody : pane.technicalBody)
            """
        }.joined(separator: "\n\n")

        return VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("Combined View")
                    .font(.subheadline.weight(.semibold))
                Spacer()
                Text("\(model.consolePanes.count) lanes")
                    .font(.caption.weight(.bold))
                    .padding(.horizontal, 10)
                    .padding(.vertical, 5)
                    .background(.white.opacity(0.08))
                    .clipShape(Capsule())
            }
            consoleText(combinedText)
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(consoleBackground)
        .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
    }

    private func consoleCard(_ pane: MobileRelayDashboardModel.ConsolePane) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                VStack(alignment: .leading, spacing: 3) {
                    Text(pane.title)
                        .font(.subheadline.weight(.semibold))
                    Text(pane.subtitle)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                Spacer()
                Text(pane.status.capitalized)
                    .font(.caption.weight(.bold))
                    .padding(.horizontal, 10)
                    .padding(.vertical, 5)
                    .background(.white.opacity(0.08))
                    .clipShape(Capsule())
            }
            consoleText(audienceMode == .simple ? pane.simpleBody : pane.technicalBody)
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(consoleBackground)
        .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
    }

    private func consoleText(_ value: String) -> some View {
        Text(value)
            .font(.system(.caption, design: .monospaced))
            .foregroundStyle(.white.opacity(0.88))
            .frame(maxWidth: .infinity, alignment: .leading)
            .textSelection(.enabled)
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

    private func metricValue(for title: String) -> String {
        model.metrics.first(where: { $0.title == title })?.value ?? "n/a"
    }

    private func statusChip(_ title: String, value: String) -> some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(title.uppercased())
                .font(.system(.caption2, design: .monospaced).weight(.bold))
                .foregroundStyle(.white.opacity(0.56))
            Text(value)
                .font(.caption.weight(.semibold))
                .foregroundStyle(.white)
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 9)
        .background(.white.opacity(0.08))
        .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
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
                        Color(red: 0.14, green: 0.22, blue: 0.42),
                        Color(red: 0.08, green: 0.14, blue: 0.24),
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

private enum ConsoleLayout: String, CaseIterable {
    case split
    case combined

    var label: String {
        switch self {
        case .split:
            return "Split"
        case .combined:
            return "Combined"
        }
    }
}

private extension VoiceTermMobileDashboardView {
    var consoleBackground: some View {
        RoundedRectangle(cornerRadius: 22, style: .continuous)
            .fill(
                LinearGradient(
                    colors: [
                        Color(red: 0.05, green: 0.07, blue: 0.11),
                        Color(red: 0.02, green: 0.03, blue: 0.06),
                    ],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
            )
            .overlay(
                RoundedRectangle(cornerRadius: 22, style: .continuous)
                    .stroke(.white.opacity(0.08), lineWidth: 1)
            )
    }
}
#endif
