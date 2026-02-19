//! Audio recording with cpal
//!
//! Cross-platform audio input capture for voice recognition.

use std::sync::{Arc, Mutex};
use tokio::sync::mpsc;

/// Audio sample format
pub type AudioSample = i16;

/// Audio buffer for recording
#[derive(Debug, Clone)]
pub struct AudioBuffer {
    pub samples: Vec<AudioSample>,
    pub sample_rate: u32,
    pub channels: u16,
}

impl AudioBuffer {
    pub fn new(sample_rate: u32, channels: u16) -> Self {
        Self {
            samples: Vec::new(),
            sample_rate,
            channels,
        }
    }

    pub fn duration_secs(&self) -> f32 {
        self.samples.len() as f32 / (self.sample_rate as f32 * self.channels as f32)
    }

    pub fn to_mono(&self) -> Vec<AudioSample> {
        if self.channels == 1 {
            return self.samples.clone();
        }

        self.samples
            .chunks(self.channels as usize)
            .map(|chunk| {
                let sum: i32 = chunk.iter().map(|&s| s as i32).sum();
                (sum / self.channels as i32) as AudioSample
            })
            .collect()
    }
}

/// Recording state
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum RecordingState {
    Idle,
    Recording,
    Processing,
}

/// Audio recorder for push-to-talk
pub struct AudioRecorder {
    state: Arc<Mutex<RecordingState>>,
    buffer: Arc<Mutex<AudioBuffer>>,
    sample_rate: u32,
}

impl AudioRecorder {
    /// Create a new audio recorder
    pub fn new() -> Self {
        Self {
            state: Arc::new(Mutex::new(RecordingState::Idle)),
            buffer: Arc::new(Mutex::new(AudioBuffer::new(16000, 1))),
            sample_rate: 16000,
        }
    }

    /// Get current recording state
    pub fn state(&self) -> RecordingState {
        *self.state.lock().unwrap()
    }

    /// Start recording
    pub fn start_recording(&self) -> crate::error::Result<()> {
        let mut state = self.state.lock().unwrap();
        if *state != RecordingState::Idle {
            return Ok(());
        }

        // Clear buffer
        {
            let mut buffer = self.buffer.lock().unwrap();
            buffer.samples.clear();
        }

        *state = RecordingState::Recording;
        tracing::info!("Started audio recording");

        // Note: Actual cpal stream would be started here
        // For now, we implement a mock that can be replaced
        // when vosk integration is available

        Ok(())
    }

    /// Stop recording and return the audio buffer
    pub fn stop_recording(&self) -> crate::error::Result<AudioBuffer> {
        let mut state = self.state.lock().unwrap();
        *state = RecordingState::Processing;

        let buffer = self.buffer.lock().unwrap().clone();
        tracing::info!(
            "Stopped recording: {} samples ({:.2}s)",
            buffer.samples.len(),
            buffer.duration_secs()
        );

        *state = RecordingState::Idle;
        Ok(buffer)
    }

    /// Check if currently recording
    pub fn is_recording(&self) -> bool {
        *self.state.lock().unwrap() == RecordingState::Recording
    }

    /// Add samples to buffer (used by audio callback)
    pub fn add_samples(&self, samples: &[AudioSample]) {
        if *self.state.lock().unwrap() == RecordingState::Recording {
            let mut buffer = self.buffer.lock().unwrap();
            buffer.samples.extend_from_slice(samples);
        }
    }
}

impl Default for AudioRecorder {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_recorder_state() {
        let recorder = AudioRecorder::new();
        assert_eq!(recorder.state(), RecordingState::Idle);

        recorder.start_recording().unwrap();
        assert_eq!(recorder.state(), RecordingState::Recording);

        recorder.stop_recording().unwrap();
        assert_eq!(recorder.state(), RecordingState::Idle);
    }

    #[test]
    fn test_audio_buffer() {
        let mut buffer = AudioBuffer::new(16000, 2);
        buffer.samples = vec![100, 200, 300, 400]; // 2 frames, stereo

        let mono = buffer.to_mono();
        assert_eq!(mono.len(), 2);
        assert_eq!(mono[0], 150); // avg of 100, 200
        assert_eq!(mono[1], 350); // avg of 300, 400
    }
}
