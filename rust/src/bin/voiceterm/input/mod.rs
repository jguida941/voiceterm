//! Input subsystem wiring that turns raw terminal bytes into overlay events.

mod event;
mod mouse;
mod parser;
mod spawn;

pub(crate) use event::InputEvent;
#[cfg(test)]
pub(crate) use parser::InputParser;
pub(crate) use spawn::spawn_input_thread;
