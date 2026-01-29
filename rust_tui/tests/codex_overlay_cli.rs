use std::process::Command;

fn combined_output(output: &std::process::Output) -> String {
    let mut combined = String::new();
    combined.push_str(&String::from_utf8_lossy(&output.stdout));
    combined.push_str(&String::from_utf8_lossy(&output.stderr));
    combined
}

fn codex_voice_bin() -> &'static str {
    option_env!("CARGO_BIN_EXE_codex-voice")
        .or(option_env!("CARGO_BIN_EXE_codex_voice"))
        .expect("codex-voice test binary not built")
}

#[test]
fn codex_voice_help_mentions_name() {
    let output = Command::new(codex_voice_bin())
        .arg("--help")
        .output()
        .expect("run codex-voice --help");
    assert!(output.status.success());
    let combined = combined_output(&output);
    assert!(combined.contains("Codex Voice"));
}

#[test]
fn codex_voice_list_input_devices_prints_message() {
    let output = Command::new(codex_voice_bin())
        .arg("--list-input-devices")
        .output()
        .expect("run codex-voice --list-input-devices");
    assert!(output.status.success());
    let combined = combined_output(&output);
    assert!(
        combined.contains("audio input devices")
            || combined.contains("Failed to list audio input devices")
    );
}
