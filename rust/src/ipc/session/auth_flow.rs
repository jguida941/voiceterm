use crate::auth;

use super::Provider;

#[cfg(any(test, feature = "mutants"))]
use std::sync::{Mutex, OnceLock};

pub(super) type AuthResult = auth::AuthResult;

#[cfg(any(test, feature = "mutants"))]
pub(super) type AuthFlowHook =
    Box<dyn Fn(Provider, &str, &str) -> AuthResult + Send + Sync + 'static>;

#[cfg(any(test, feature = "mutants"))]
static AUTH_FLOW_HOOK: OnceLock<Mutex<Option<AuthFlowHook>>> = OnceLock::new();

#[cfg(any(test, feature = "mutants"))]
#[allow(dead_code)]
pub(super) fn set_auth_flow_hook(hook: Option<AuthFlowHook>) {
    let storage = AUTH_FLOW_HOOK.get_or_init(|| Mutex::new(None));
    *storage.lock().unwrap_or_else(|e| e.into_inner()) = hook;
}

pub(super) fn run_auth_flow(provider: Provider, codex_cmd: &str, claude_cmd: &str) -> AuthResult {
    #[cfg(any(test, feature = "mutants"))]
    if let Some(storage) = AUTH_FLOW_HOOK.get() {
        if let Ok(guard) = storage.lock() {
            if let Some(hook) = guard.as_ref() {
                return hook(provider, codex_cmd, claude_cmd);
            }
        }
    }
    let command = match provider {
        Provider::Codex => codex_cmd,
        Provider::Claude => claude_cmd,
    };
    auth::run_login_command(command)
        .map_err(|err| format!("{} auth failed: {}", provider.as_str(), err))
}
