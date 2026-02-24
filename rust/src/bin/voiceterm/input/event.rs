//! Semantic input events so the event loop does not depend on raw key bytes.

#[derive(Debug, PartialEq, Eq)]
pub(crate) enum InputEvent {
    Bytes(Vec<u8>),
    VoiceTrigger,
    ImageCaptureTrigger,
    SendStagedText,
    ToggleAutoVoice,
    ToggleSendMode,
    IncreaseSensitivity,
    DecreaseSensitivity,
    HelpToggle,
    ThemePicker,
    QuickThemeCycle,
    SettingsToggle,
    DevPanelToggle,
    ToggleHudStyle,
    TranscriptHistoryToggle,
    ToastHistoryToggle,
    EnterKey,
    Exit,
    /// Mouse click at (x, y) coordinates (1-based, like terminal reports)
    MouseClick {
        x: u16,
        y: u16,
    },
}
