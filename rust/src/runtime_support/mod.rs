//! Runtime helpers shared by the VoiceTerm overlay and speech pipeline.

mod logging;
mod pipeline;
#[cfg(test)]
mod tests;

#[cfg(test)]
pub(crate) use logging::set_logging_for_tests;
pub use logging::{
    crash_log_path, init_logging, log_debug, log_debug_content, log_file_path, log_panic,
};
#[cfg(test)]
pub(crate) use pipeline::PipelineMetrics;
pub(crate) use pipeline::{run_python_transcription, PipelineJsonResult};
