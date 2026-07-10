// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "VoiceTermMobile",
    platforms: [
        .iOS(.v17),
        .macOS(.v14),
    ],
    products: [
        .library(
            name: "VoiceTermMobileCore",
            targets: ["VoiceTermMobileCore"]
        ),
    ],
    targets: [
        .target(
            name: "VoiceTermMobileCore",
            path: "Sources/VoiceTermMobileCore"
        ),
        .testTarget(
            name: "VoiceTermMobileCoreTests",
            dependencies: ["VoiceTermMobileCore"],
            path: "Tests/VoiceTermMobileCoreTests"
        ),
    ]
)
