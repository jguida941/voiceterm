//! ANSI/control stripping so prompt matching runs on stable plain-text buffers.

pub(super) fn strip_ansi_preserve_controls(bytes: &[u8]) -> Vec<u8> {
    crate::ansi::strip_ansi_preserve_controls(bytes)
}
