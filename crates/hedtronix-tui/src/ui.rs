//! UI rendering
//!
//! Implements the terminal UI with conversation view, input area, and status bar.

use hedtronix_core::models::Role;
use ratatui::{
    prelude::*,
    widgets::{Block, Borders, Paragraph, Wrap},
};

use crate::app::{App, InputMode};

/// Main render function
pub fn render(frame: &mut Frame, app: &App) {
    let theme = &app.theme;

    // Create main layout
    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Length(3), // Header
            Constraint::Min(3),    // Conversation
            Constraint::Length(3), // Input
            Constraint::Length(1), // Status
        ])
        .split(frame.area());

    // Render header
    render_header(frame, chunks[0], app);

    // Render conversation
    render_conversation(frame, chunks[1], app);

    // Render input
    render_input(frame, chunks[2], app);

    // Render status bar
    render_status(frame, chunks[3], app);
}

/// Render the header
fn render_header(frame: &mut Frame, area: Rect, app: &App) {
    let theme = &app.theme;

    let title = format!(
        " HEDTRONIX {} ",
        if app.theme.is_dark { "◐" } else { "◑" }
    );

    let block = Block::default()
        .title(title)
        .title_style(Style::default().fg(theme.accent).bold())
        .borders(Borders::ALL)
        .border_style(Style::default().fg(theme.border))
        .style(Style::default().bg(theme.bg_secondary));

    let msg_count = app.conversation.len();
    let content = format!(
        "Messages: {} │ Press Tab to toggle theme │ Ctrl+Q to quit",
        msg_count
    );

    let paragraph = Paragraph::new(content)
        .block(block)
        .style(Style::default().fg(theme.text_secondary));

    frame.render_widget(paragraph, area);
}

/// Render the conversation area
fn render_conversation(frame: &mut Frame, area: Rect, app: &App) {
    let theme = &app.theme;

    let block = Block::default()
        .title(" Conversation ")
        .title_style(Style::default().fg(theme.text_secondary))
        .borders(Borders::ALL)
        .border_style(Style::default().fg(theme.border))
        .style(Style::default().bg(theme.bg_primary));

    // Build conversation text
    let mut lines: Vec<Line> = Vec::new();

    if app.conversation.is_empty() {
        lines.push(Line::from(Span::styled(
            "Start a conversation by pressing Enter and typing your message.",
            Style::default().fg(theme.text_tertiary).italic(),
        )));
    } else {
        for message in app.conversation.messages.iter() {
            let (prefix, style) = match message.role {
                Role::User => (
                    "You: ",
                    Style::default().fg(theme.accent).bold(),
                ),
                Role::Assistant => (
                    "AI: ",
                    Style::default().fg(theme.success).bold(),
                ),
                Role::System => (
                    "System: ",
                    Style::default().fg(theme.warning).italic(),
                ),
            };

            // Add role prefix
            lines.push(Line::from(Span::styled(prefix, style)));

            // Add message content
            for line in message.content.lines() {
                lines.push(Line::from(Span::styled(
                    format!("  {}", line),
                    Style::default().fg(theme.text_primary),
                )));
            }

            // Add spacing
            lines.push(Line::from(""));
        }
    }

    // Handle processing state
    if app.is_processing {
        lines.push(Line::from(Span::styled(
            "AI is thinking...",
            Style::default().fg(theme.info).italic(),
        )));
    }

    let paragraph = Paragraph::new(lines)
        .block(block)
        .wrap(Wrap { trim: false })
        .scroll((app.scroll_offset as u16, 0));

    frame.render_widget(paragraph, area);
}

/// Render the input area
fn render_input(frame: &mut Frame, area: Rect, app: &App) {
    let theme = &app.theme;

    let (border_color, title) = match app.input_mode {
        InputMode::Normal => (theme.border, " Input [Press Enter] "),
        InputMode::Editing => (theme.border_focused, " Input [Typing...] "),
    };

    let block = Block::default()
        .title(title)
        .title_style(Style::default().fg(if app.input_mode == InputMode::Editing {
            theme.accent
        } else {
            theme.text_secondary
        }))
        .borders(Borders::ALL)
        .border_style(Style::default().fg(border_color))
        .style(Style::default().bg(theme.surface_primary));

    let input_text = if app.input.is_empty() && app.input_mode == InputMode::Normal {
        "Press Enter to type..."
    } else {
        &app.input
    };

    let style = if app.input.is_empty() && app.input_mode == InputMode::Normal {
        Style::default().fg(theme.text_disabled).italic()
    } else {
        Style::default().fg(theme.text_primary)
    };

    let paragraph = Paragraph::new(input_text)
        .block(block)
        .style(style);

    frame.render_widget(paragraph, area);

    // Show cursor when in editing mode
    if app.input_mode == InputMode::Editing {
        frame.set_cursor_position(Position::new(
            area.x + 1 + app.cursor_position as u16,
            area.y + 1,
        ));
    }
}

/// Render the status bar
fn render_status(frame: &mut Frame, area: Rect, app: &App) {
    let theme = &app.theme;

    let mode_indicator = match app.input_mode {
        InputMode::Normal => "NORMAL",
        InputMode::Editing => "INSERT",
    };

    let recording_indicator = if app.is_recording {
        "🔴 REC"
    } else {
        ""
    };

    let text = format!(" {} │ {} │ {} ", mode_indicator, app.status, recording_indicator);

    let style = Style::default()
        .bg(theme.surface_secondary)
        .fg(theme.text_secondary);

    let paragraph = Paragraph::new(text).style(style);
    frame.render_widget(paragraph, area);
}
