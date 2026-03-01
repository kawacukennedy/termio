//! Voice recognition module
//!
//! Implements push-to-talk voice input with Vosk STT.
//!
//! # Components
//!
//! ## Audio Recorder
//!
//! Cross-platform audio capture using cpal:
//! - Supports multiple sample rates (default: 16kHz)
//! - Mono/stereo capture
//! - Push-to-talk model (start/stop)
//!
//! ## Voice Recognizer
//!
//! Offline speech-to-text using Vosk models:
//! - No network required
//! - Low latency
//! - Multiple language support
//!
//! # Usage
//!
//! ```rust
//! use termio_core::voice::{AudioRecorder, VoiceRecognizer};
//!
//! // Recording
//! let recorder = AudioRecorder::new();
//! recorder.start_recording()?;
//! // ... user speaks ...
//! let audio = recorder.stop_recording()?;
//!
//! // Recognition
//! let mut recognizer = VoiceRecognizer::with_model("/path/to/vosk-model");
//! let result = recognizer.recognize(&audio).await?;
//! println!("Text: {}", result.text);
//! ```

mod recorder;
mod recognizer;

pub use recorder::AudioRecorder;
pub use recognizer::VoiceRecognizer;
