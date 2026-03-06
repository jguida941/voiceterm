//! Prompt-regex resolution so custom and backend defaults validate consistently.

use anyhow::{Context, Result};
use regex::Regex;
use std::env;

use crate::config::OverlayConfig;

pub(crate) struct PromptRegexConfig {
    pub(crate) regex: Option<Regex>,
    pub(crate) allow_auto_learn: bool,
}

pub(crate) fn resolve_prompt_regex(
    config: &OverlayConfig,
    backend_fallback: Option<&str>,
) -> Result<PromptRegexConfig> {
    let user_override = config
        .prompt_regex
        .clone()
        .or_else(|| env::var("VOICETERM_PROMPT_REGEX").ok());
    if let Some(raw) = user_override {
        let regex = Regex::new(&raw).with_context(|| format!("invalid prompt regex: {raw}"))?;
        return Ok(PromptRegexConfig {
            regex: Some(regex),
            allow_auto_learn: false,
        });
    }

    if let Some(raw) = backend_fallback
        .map(str::trim)
        .filter(|pattern| !pattern.is_empty())
    {
        let regex = Regex::new(raw).with_context(|| format!("invalid prompt regex: {raw}"))?;
        return Ok(PromptRegexConfig {
            regex: Some(regex),
            allow_auto_learn: true,
        });
    }

    Ok(PromptRegexConfig {
        regex: None,
        allow_auto_learn: true,
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::config::OverlayConfig;
    use crate::test_env::default_overlay_config;

    fn make_default_config(prompt_regex: Option<&str>) -> OverlayConfig {
        let mut config = default_overlay_config();
        config.prompt_regex = prompt_regex.map(str::to_string);
        config
    }

    #[test]
    fn resolve_prompt_regex_honors_config() {
        let config = make_default_config(Some("^codex> $"));
        let resolved = resolve_prompt_regex(&config, None).expect("regex should compile");
        assert!(resolved.regex.is_some());
        assert!(!resolved.allow_auto_learn);
    }

    #[test]
    fn resolve_prompt_regex_rejects_invalid() {
        let config = make_default_config(Some("["));
        assert!(resolve_prompt_regex(&config, None).is_err());
    }
}
