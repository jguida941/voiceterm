//! OpenCode backend definition so OpenCode can run via the common launcher path.

use super::{command_with_args, AiBackend};

/// Backend for OpenCode CLI.
pub struct OpenCodeBackend {
    command: Vec<String>,
}

impl Default for OpenCodeBackend {
    fn default() -> Self {
        Self::new()
    }
}

impl OpenCodeBackend {
    /// Create a new OpenCode backend with default settings.
    #[must_use]
    pub fn new() -> Self {
        Self {
            command: command_with_args("opencode", Vec::new()),
        }
    }

    /// Create an OpenCode backend with additional arguments.
    #[must_use]
    pub fn with_args(args: Vec<String>) -> Self {
        Self {
            command: command_with_args("opencode", args),
        }
    }
}

impl AiBackend for OpenCodeBackend {
    fn name(&self) -> &str {
        "opencode"
    }

    fn display_name(&self) -> &str {
        "OpenCode"
    }

    fn command(&self) -> Vec<String> {
        self.command.clone()
    }

    fn prompt_pattern(&self) -> &str {
        // OpenCode prompt pattern
        r"(?i)^(opencode>|>\s*)$"
    }

    fn thinking_pattern(&self) -> Option<&str> {
        Some(r"(?i)(thinking|processing|\.\.\.)")
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_opencode_backend() {
        let backend = OpenCodeBackend::new();
        assert_eq!(backend.name(), "opencode");
        assert_eq!(backend.display_name(), "OpenCode");
        assert_eq!(backend.command(), vec!["opencode"]);
        assert!(!backend.prompt_pattern().is_empty());
        assert!(backend.thinking_pattern().is_some());
    }

    #[test]
    fn test_opencode_with_args() {
        let backend = OpenCodeBackend::with_args(vec!["--verbose".to_string()]);
        assert_eq!(backend.command(), vec!["opencode", "--verbose"]);
    }
}
