//! TERMIO Terminal UI
//!
//! A next-generation AI assistant with a beautiful terminal interface.
//!
//! # Overview
//!
//! The TERMIO TUI provides a rich terminal interface with:
//! - 70/30 split: Conversation panel (70%) + Context panel (30%)
//! - Sidebar: Conversation history navigation
//! - Help overlay: Keyboard shortcuts reference
//! - Command palette: Quick command execution
//! - Plugin manager: Manage WASM plugins
//!
//! # Keyboard Shortcuts
//!
//! | Shortcut | Action |
//! |---------|--------|
//! | Enter | Start typing / Send message |
//! | Escape | Stop typing / Close overlay |
//! | Ctrl+N | New conversation |
//! | Ctrl+V | Toggle voice recording |
//! | Ctrl+S | Trigger sync |
//! | Ctrl+H | Toggle help |
//! | Ctrl+P | Plugin manager |
//! | Ctrl+B | Toggle sidebar |
//! | Ctrl+K | Command palette |
//! | Ctrl+T | Toggle theme |
//! | Tab | Switch panel focus |
//! | Ctrl+Q | Quit |
//!
//! # Running
//!
//! ```bash
//! cargo run -p termio-tui
//! ```

mod app;
mod theme;
mod ui;

use anyhow::Result;
use crossterm::{
    event::{self, DisableMouseCapture, EnableMouseCapture, Event, KeyCode, KeyEventKind},
    execute,
    terminal::{disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen},
};
use ratatui::prelude::*;
use std::io;
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

use app::App;
use theme::Theme;

/// Initialize logging
///
/// Sets up tracing with environment-based filtering.
/// Log level can be controlled via RUST_LOG environment variable.
fn init_logging() {
    tracing_subscriber::registry()
        .with(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "termio=info".into()),
        )
        .with(tracing_subscriber::fmt::layer().with_target(false))
        .init();
}

/// Main entry point
///
/// Sets up the terminal and runs the application event loop.
#[tokio::main]
async fn main() -> Result<()> {
    // Initialize logging
    init_logging();
    tracing::info!("Starting TERMIO...");

    // Setup terminal for raw mode (no line buffering)
    enable_raw_mode()?;
    let mut stdout = io::stdout();
    // Enter alternate screen buffer for full-screen TUI
    execute!(stdout, EnterAlternateScreen, EnableMouseCapture)?;
    let backend = CrosstermBackend::new(stdout);
    let mut terminal = Terminal::new(backend)?;

    // Create app with dark theme
    let theme = Theme::dark();
    let mut app = App::new(theme);

    // Run the main event loop
    let res = run_app(&mut terminal, &mut app).await;

    // Restore terminal to original state
    disable_raw_mode()?;
    execute!(
        terminal.backend_mut(),
        LeaveAlternateScreen,
        DisableMouseCapture
    )?;
    terminal.show_cursor()?;

    // Handle any errors
    if let Err(err) = res {
        tracing::error!("Application error: {:?}", err);
        return Err(err);
    }

    tracing::info!("TERMIO shutdown complete");
    Ok(())
}

/// Run the main application loop
///
/// Handles keyboard events and renders the UI.
async fn run_app<B: Backend>(terminal: &mut Terminal<B>, app: &mut App) -> Result<()> {
    loop {
        // Step 1: Draw the UI
        terminal.draw(|f| ui::render(f, app))?;

        // Step 2: Check for quit signal
        if app.status == "__QUIT__" {
            return Ok(());
        }

        // Step 3: Handle events
        if event::poll(std::time::Duration::from_millis(100))? {
            if let Event::Key(key) = event::read()? {
                // Only handle key press events (not release)
                if key.kind == KeyEventKind::Press {
                    // ==========================================
                    // Global: Ctrl+Q always quits
                    // ==========================================
                    if key.code == KeyCode::Char('q')
                        && key.modifiers.contains(event::KeyModifiers::CONTROL)
                    {
                        return Ok(());
                    }

                    // ==========================================
                    // Command Palette Mode
                    // ==========================================
                    if app.show_command_palette {
                        match key.code {
                            KeyCode::Esc => app.dismiss_overlay(),
                            KeyCode::Enter => app.execute_command(),
                            KeyCode::Backspace => app.command_palette_backspace(),
                            KeyCode::Char(c) => app.command_palette_char(c),
                            _ => {}
                        }
                        continue;
                    }

                    // ==========================================
                    // Help Overlay Mode
                    // ==========================================
                    if app.show_help {
                        match key.code {
                            KeyCode::Esc => app.dismiss_overlay(),
                            KeyCode::Char('h')
                                if key.modifiers.contains(event::KeyModifiers::CONTROL) =>
                            {
                                app.toggle_help()
                            }
                            _ => {}
                        }
                        continue;
                    }

                    // ==========================================
                    // Plugin Manager Mode
                    // ==========================================
                    if app.show_plugin_manager {
                        match key.code {
                            KeyCode::Esc => {
                                app.show_plugin_manager = false;
                            }
                            KeyCode::Char('p')
                                if key.modifiers.contains(event::KeyModifiers::CONTROL) =>
                            {
                                app.toggle_plugin_manager()
                            }
                            _ => {}
                        }
                        continue;
                    }

                    // ==========================================
                    // Global Shortcuts (Ctrl + key)
                    // ==========================================
                    if key.modifiers.contains(event::KeyModifiers::CONTROL) {
                        match key.code {
                            KeyCode::Char('n') => {
                                app.new_conversation();
                                continue;
                            }
                            KeyCode::Char('v') => {
                                // Ctrl+V = toggle voice per spec
                                app.toggle_recording();
                                continue;
                            }
                            KeyCode::Char('s') => {
                                // Ctrl+S = sync now per spec
                                app.trigger_sync();
                                continue;
                            }
                            KeyCode::Char('p') => {
                                // Ctrl+P = plugin manager per spec
                                app.toggle_plugin_manager();
                                continue;
                            }
                            KeyCode::Char('b') => {
                                // Ctrl+B = toggle sidebar
                                app.toggle_sidebar();
                                continue;
                            }
                            KeyCode::Char('h') => {
                                app.toggle_help();
                                continue;
                            }
                            KeyCode::Char('k') => {
                                // Ctrl+K = command palette
                                app.toggle_command_palette();
                                continue;
                            }
                            KeyCode::Char('t') => {
                                // Ctrl+T = toggle theme
                                app.toggle_theme();
                                continue;
                            }
                            _ => {}
                        }
                    }

                    // ==========================================
                    // Normal Mode Key Handling
                    // ==========================================
                    match key.code {
                        KeyCode::Esc => {
                            if app.is_in_input_mode() {
                                app.exit_input_mode();
                            } else {
                                return Ok(());
                            }
                        }
                        KeyCode::Enter => {
                            if app.is_in_input_mode() {
                                app.submit_input().await;
                            } else {
                                app.enter_input_mode();
                            }
                        }
                        KeyCode::Char(c) => {
                            if app.is_in_input_mode() {
                                app.handle_char(c);
                            }
                        }
                        KeyCode::Backspace => {
                            if app.is_in_input_mode() {
                                app.handle_backspace();
                            }
                        }
                        KeyCode::Up => {
                            if app.show_sidebar && !app.is_in_input_mode() {
                                app.sidebar_up();
                            } else {
                                app.scroll_up();
                            }
                        }
                        KeyCode::Down => {
                            if app.show_sidebar && !app.is_in_input_mode() {
                                app.sidebar_down();
                            } else {
                                app.scroll_down();
                            }
                        }
                        KeyCode::Tab => {
                            // Tab = switch panel focus per spec
                            app.switch_panel_focus();
                        }
                        KeyCode::Right => {
                            if app.show_sidebar && !app.is_in_input_mode() {
                                app.load_selected_conversation();
                            }
                        }
                        _ => {}
                    }
                }
            }
        }
    }
}
