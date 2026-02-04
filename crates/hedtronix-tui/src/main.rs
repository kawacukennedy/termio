//! HEDTRONIX Terminal UI
//!
//! A next-generation AI assistant with a beautiful terminal interface.

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
fn init_logging() {
    tracing_subscriber::registry()
        .with(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "hedtronix=info".into()),
        )
        .with(tracing_subscriber::fmt::layer().with_target(false))
        .init();
}

/// Main entry point
#[tokio::main]
async fn main() -> Result<()> {
    init_logging();
    tracing::info!("Starting HEDTRONIX...");

    // Setup terminal
    enable_raw_mode()?;
    let mut stdout = io::stdout();
    execute!(stdout, EnterAlternateScreen, EnableMouseCapture)?;
    let backend = CrosstermBackend::new(stdout);
    let mut terminal = Terminal::new(backend)?;

    // Create app
    let theme = Theme::dark();
    let mut app = App::new(theme);

    // Run app
    let res = run_app(&mut terminal, &mut app).await;

    // Restore terminal
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

    tracing::info!("HEDTRONIX shutdown complete");
    Ok(())
}

/// Run the main application loop
async fn run_app<B: Backend>(terminal: &mut Terminal<B>, app: &mut App) -> Result<()> {
    loop {
        // Draw UI
        terminal.draw(|f| ui::render(f, app))?;

        // Handle events
        if event::poll(std::time::Duration::from_millis(100))? {
            if let Event::Key(key) = event::read()? {
                if key.kind == KeyEventKind::Press {
                    match key.code {
                        KeyCode::Char('q') if key.modifiers.contains(event::KeyModifiers::CONTROL) => {
                            return Ok(());
                        }
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
                        KeyCode::Char(' ') => {
                             if !app.is_in_input_mode() {
                                 app.toggle_recording();
                             } else {
                                 app.handle_char(' ');
                             }
                        }
                        KeyCode::Up => app.scroll_up(),
                        KeyCode::Down => app.scroll_down(),
                        KeyCode::Tab => app.toggle_theme(),
                        _ => {}
                    }
                }
            }
        }
    }
}
