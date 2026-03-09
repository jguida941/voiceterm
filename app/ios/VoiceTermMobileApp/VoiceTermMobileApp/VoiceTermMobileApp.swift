import SwiftUI

@main
struct VoiceTermMobileApp: App {
    @StateObject private var model = MobileRelayAppModel()

    var body: some Scene {
        WindowGroup {
            MobileRelayAppRootView(model: model)
        }
    }
}
