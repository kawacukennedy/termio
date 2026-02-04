//! Application state and logic

use hedtronix_core::models::{Conversation, Message};
use hedtronix_core::memory::RingBuffer;

use crate::theme::Theme;

/// Application input mode
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum InputMode {
    /// Normal mode - navigation only
    Normal,
    /// Editing mode - typing input
    Editing,
}

/// Main application state
pub struct App {
    /// Current theme
    pub theme: Theme,

    /// Current conversation
    pub conversation: Conversation,

    /// Recent conversations (ring buffer)
    pub history: RingBuffer<Conversation>,

    /// Current input text
    pub input: String,

    /// Cursor position in input
    pub cursor_position: usize,

    /// Current input mode
    pub input_mode: InputMode,

    /// Scroll offset for conversation view
    pub scroll_offset: usize,

    /// Status message to display
    pub status: String,

    /// Whether AI is processing
    pub is_processing: bool,

    /// Whether voice is recording
    pub is_recording: bool,
}

impl App {
    /// Create a new application instance
    pub fn new(theme: Theme) -> Self {
        Self {
            theme,
            conversation: Conversation::default(),
            history: RingBuffer::new(100),
            input: String::new(),
            cursor_position: 0,
            input_mode: InputMode::Normal,
            scroll_offset: 0,
            status: "Welcome to HEDTRONIX! Press Enter to start typing.".to_string(),
            is_processing: false,
            is_recording: false,
        }
    }

    /// Toggle voice recording
    pub fn toggle_recording(&mut self) {
        self.is_recording = !self.is_recording;
        if self.is_recording {
            self.status = "Recording voice... (Press Space to stop)".to_string();
            // TODO: Start audio recording via hedtronix-core
        } else {
            self.status = "Processing voice...".to_string();
            self.is_processing = true;
            // TODO: Stop recording and transcribe
            
            // Mock completion
            self.is_processing = false;
            self.status = "Voice transcription not verified (Mock)".to_string();
        }
    }

    /// Check if in input mode
    pub fn is_in_input_mode(&self) -> bool {
        self.input_mode == InputMode::Editing
    }

    /// Enter input mode
    pub fn enter_input_mode(&mut self) {
        self.input_mode = InputMode::Editing;
        self.status = "Type your message and press Enter to send".to_string();
    }

    /// Exit input mode
    pub fn exit_input_mode(&mut self) {
        self.input_mode = InputMode::Normal;
        self.status = "Press Enter to start typing, Ctrl+Q to quit".to_string();
    }

    /// Handle a character input
    pub fn handle_char(&mut self, c: char) {
        self.input.insert(self.cursor_position, c);
        self.cursor_position += 1;
    }

    /// Handle backspace
    pub fn handle_backspace(&mut self) {
        if self.cursor_position > 0 {
            self.cursor_position -= 1;
            self.input.remove(self.cursor_position);
        }
    }

    /// Submit the current input
    pub async fn submit_input(&mut self) {
        if self.input.is_empty() {
            return;
        }

        // Create user message
        let user_msg = Message::user(&self.input);
        self.conversation.add_message(user_msg);

        // Clear input
        let user_input = std::mem::take(&mut self.input);
        self.cursor_position = 0;

        // Set processing state
        self.is_processing = true;
        self.status = "Thinking...".to_string();

        // Generate response (placeholder - would call AI service)
        let response = self.generate_response(&user_input).await;

        // Add assistant response
        let assistant_msg = Message::assistant(response);
        self.conversation.add_message(assistant_msg);

        // Reset state
        self.is_processing = false;
        self.status = "Type your message and press Enter to send".to_string();

        // Scroll to bottom
        self.scroll_to_bottom();
    }

    /// Generate a response (placeholder for AI integration)
    async fn generate_response(&self, input: &str) -> String {
        // Simulate processing delay
        tokio::time::sleep(std::time::Duration::from_millis(500)).await;

        // Simple echo response for now
        format!(
            "I received your message: \"{}\"\n\n\
            I'm HEDTRONIX, your terminal-native AI assistant. \
            The AI inference service is not connected yet. \
            Configure the AI service to enable real responses.",
            input
        )
    }

    /// Scroll up in conversation
    pub fn scroll_up(&mut self) {
        self.scroll_offset = self.scroll_offset.saturating_add(1);
    }

    /// Scroll down in conversation
    pub fn scroll_down(&mut self) {
        self.scroll_offset = self.scroll_offset.saturating_sub(1);
    }

    /// Scroll to bottom of conversation
    pub fn scroll_to_bottom(&mut self) {
        self.scroll_offset = 0;
    }

    /// Toggle between dark and light theme
    pub fn toggle_theme(&mut self) {
        self.theme = if self.theme.is_dark {
            Theme::light()
        } else {
            Theme::dark()
        };
        self.status = format!(
            "Theme: {}",
            if self.theme.is_dark { "Dark" } else { "Light" }
        );
    }
}
