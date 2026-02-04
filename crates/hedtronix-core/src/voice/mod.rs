//! Voice recognition module
//!
//! Implements push-to-talk voice input with Vosk STT.

mod recorder;
mod recognizer;

pub use recorder::AudioRecorder;
pub use recognizer::VoiceRecognizer;
