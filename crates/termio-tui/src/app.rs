//! Application state and logic

use termio_core::memory::RingBuffer;
use termio_core::models::{Conversation, Message};

use crate::theme::Theme;

/// Application input mode
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum InputMode {
    Normal,
    Editing,
}

/// Which panel currently has focus
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ActivePanel {
    Conversation,
    Context,
}

/// Main application state
pub struct App {
    pub theme: Theme,
    pub conversation: Conversation,
    pub history: RingBuffer<Conversation>,
    pub input: String,
    pub cursor_position: usize,
    pub input_mode: InputMode,
    pub scroll_offset: usize,
    pub status: String,
    pub is_processing: bool,
    pub is_recording: bool,
    pub show_sidebar: bool,
    pub show_help: bool,
    pub show_command_palette: bool,
    pub command_input: String,
    pub sidebar_selected: usize,

    // -- New spec fields --
    /// Active panel for Tab focus switching
    pub active_panel: ActivePanel,
    /// Whether context panel is visible
    pub show_context_panel: bool,
    /// Current AI model name
    pub ai_model: String,
    /// Recent memory items for context panel
    pub context_memory_items: Vec<String>,
    /// Sync status indicator
    pub sync_status: String,
    /// Unread notification count
    pub notification_count: usize,
    /// Whether plugin manager view is active
    pub show_plugin_manager: bool,
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
            status: "Welcome to TERMIO! Press Enter to start typing.".to_string(),
            is_processing: false,
            is_recording: false,
            show_sidebar: false,
            show_help: false,
            show_command_palette: false,
            command_input: String::new(),
            sidebar_selected: 0,
            active_panel: ActivePanel::Conversation,
            show_context_panel: true,
            ai_model: "LLaMA 3.1 8B (local)".to_string(),
            context_memory_items: vec![
                "User prefers dark mode".to_string(),
                "Last topic: system architecture".to_string(),
            ],
            sync_status: "Synced".to_string(),
            notification_count: 0,
            show_plugin_manager: false,
        }
    }

    /// Toggle voice recording
    pub fn toggle_recording(&mut self) {
        self.is_recording = !self.is_recording;
        if self.is_recording {
            self.status = "Recording voice... (Press Space to stop)".to_string();
        } else {
            self.status = "Processing voice...".to_string();
            self.is_processing = true;

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

        // Generate response (calls AI service or uses fallback)
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

    /// Generate a response — tries the server API, falls back to echo
    async fn generate_response(&self, input: &str) -> String {
        // Try to call the server API
        let client = reqwest::Client::new();
        let result = client
            .post("http://127.0.0.1:8080/api/ai/chat")
            .header("Authorization", "Bearer dev-token")
            .json(&serde_json::json!({
                "message": input,
            }))
            .timeout(std::time::Duration::from_secs(30))
            .send()
            .await;

        match result {
            Ok(resp) if resp.status().is_success() => {
                if let Ok(body) = resp.json::<serde_json::Value>().await {
                    if let Some(text) = body["response"].as_str() {
                        return text.to_string();
                    }
                }
                // Fallback if parsing fails
                self.fallback_response(input)
            }
            _ => {
                // Server unavailable — use fallback
                self.fallback_response(input)
            }
        }
    }

    /// Fallback echo response when server is unavailable
    fn fallback_response(&self, input: &str) -> String {
        format!(
            "I received your message: \"{}\"\n\n\
            I'm TERMIO, your terminal-native AI assistant. \
            The AI inference service is not connected yet. \
            Start the server with: cargo run -p termio-server",
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

    /// Toggle sidebar visibility
    pub fn toggle_sidebar(&mut self) {
        self.show_sidebar = !self.show_sidebar;
    }

    /// Toggle help overlay
    pub fn toggle_help(&mut self) {
        self.show_help = !self.show_help;
    }

    /// Toggle command palette
    pub fn toggle_command_palette(&mut self) {
        self.show_command_palette = !self.show_command_palette;
        if self.show_command_palette {
            self.command_input.clear();
        }
    }

    /// Toggle context panel visibility
    pub fn toggle_context_panel(&mut self) {
        self.show_context_panel = !self.show_context_panel;
    }

    /// Switch focus between panels (Tab key)
    pub fn switch_panel_focus(&mut self) {
        self.active_panel = match self.active_panel {
            ActivePanel::Conversation => ActivePanel::Context,
            ActivePanel::Context => ActivePanel::Conversation,
        };
    }

    /// Toggle plugin manager view
    pub fn toggle_plugin_manager(&mut self) {
        self.show_plugin_manager = !self.show_plugin_manager;
    }

    /// Trigger sync (Ctrl+S per spec)
    pub fn trigger_sync(&mut self) {
        self.sync_status = "Syncing...".to_string();
        self.status = "Sync triggered".to_string();
        // In a real implementation, this would kick off the sync engine
        // For now, mock completion:
        self.sync_status = "Synced".to_string();
    }

    /// Start a new conversation
    pub fn new_conversation(&mut self) {
        // Save current conversation to history (if it has messages)
        if !self.conversation.is_empty() {
            self.history.push(self.conversation.clone());
        }

        // Create fresh conversation
        self.conversation = Conversation::default();
        self.scroll_offset = 0;
        self.status = "New conversation started".to_string();
    }

    /// Check if any overlay is active
    pub fn has_overlay(&self) -> bool {
        self.show_help || self.show_command_palette
    }

    /// Dismiss any active overlay
    pub fn dismiss_overlay(&mut self) {
        self.show_help = false;
        self.show_command_palette = false;
    }

    /// Handle command palette character input
    pub fn command_palette_char(&mut self, c: char) {
        self.command_input.push(c);
    }

    /// Handle command palette backspace
    pub fn command_palette_backspace(&mut self) {
        self.command_input.pop();
    }

    /// Execute command from palette
    pub fn execute_command(&mut self) {
        let cmd = self.command_input.to_lowercase();
        self.show_command_palette = false;

        match cmd.trim() {
            "new" | "new conversation" => self.new_conversation(),
            "theme" | "toggle theme" => self.toggle_theme(),
            "sidebar" | "toggle sidebar" => self.toggle_sidebar(),
            "help" => self.toggle_help(),
            "quit" | "exit" => {
                // Signal quit via status (handled in main loop)
                self.status = "__QUIT__".to_string();
            }
            _ => {
                self.status = format!("Unknown command: {}", cmd);
            }
        }
        self.command_input.clear();
    }

    /// Navigate sidebar up
    pub fn sidebar_up(&mut self) {
        self.sidebar_selected = self.sidebar_selected.saturating_sub(1);
    }

    /// Navigate sidebar down
    pub fn sidebar_down(&mut self) {
        let max = self.history.len().saturating_sub(1);
        if self.sidebar_selected < max {
            self.sidebar_selected += 1;
        }
    }

    /// Load selected conversation from sidebar
    pub fn load_selected_conversation(&mut self) {
        let selected_conv = self.history.get(self.sidebar_selected).cloned();
        if let Some(conv) = selected_conv {
            // Save current conversation first if non-empty
            if !self.conversation.is_empty() {
                self.history.push(self.conversation.clone());
            }
            self.conversation = conv;
            self.scroll_offset = 0;
            self.status = "Loaded conversation from history".to_string();
        }
    }
}
