//! UI rendering
//!
//! Implements the terminal UI with 70/30 layout split, context panel,
//! conversation view, input area, status bar, sidebar, help overlay,
//! command palette, and basic markdown rendering per spec.

use termio_core::models::Role;
use ratatui::{
    prelude::*,
    widgets::{Block, Borders, Clear, List, ListItem, Paragraph, Wrap},
};

use crate::app::{ActivePanel, App, InputMode};

/// Main render function
pub fn render(frame: &mut Frame, app: &App) {
    // Top-level: optionally split for sidebar
    if app.show_sidebar {
        let horizontal = Layout::default()
            .direction(Direction::Horizontal)
            .constraints([
                Constraint::Percentage(25), // Sidebar
                Constraint::Percentage(75), // Main
            ])
            .split(frame.size());

        render_sidebar(frame, horizontal[0], app);
        render_main(frame, horizontal[1], app);
    } else {
        render_main(frame, frame.size(), app);
    }

    // Overlays (drawn on top)
    if app.show_help {
        render_help_overlay(frame, app);
    }

    if app.show_command_palette {
        render_command_palette(frame, app);
    }

    if app.show_plugin_manager {
        render_plugin_manager(frame, app);
    }
}

/// Render the main content area with 70/30 split for context panel
fn render_main(frame: &mut Frame, area: Rect, app: &App) {
    if app.show_context_panel {
        // 70/30 horizontal split per spec
        let h_split = Layout::default()
            .direction(Direction::Horizontal)
            .constraints([
                Constraint::Percentage(70), // Conversation area
                Constraint::Percentage(30), // Context panel
            ])
            .split(area);

        render_conversation_area(frame, h_split[0], app);
        render_context_panel(frame, h_split[1], app);
    } else {
        render_conversation_area(frame, area, app);
    }
}

/// Render the conversation area (header + messages + input + status bar)
fn render_conversation_area(frame: &mut Frame, area: Rect, app: &App) {
    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Length(3), // Header
            Constraint::Min(3),   // Conversation
            Constraint::Length(3), // Input
            Constraint::Length(1), // Status bar
        ])
        .split(area);

    render_header(frame, chunks[0], app);
    render_conversation(frame, chunks[1], app);
    render_input(frame, chunks[2], app);
    render_status_bar(frame, chunks[3], app);
}

/// Render the context panel (right 30%) — model, memory, graph connections
fn render_context_panel(frame: &mut Frame, area: Rect, app: &App) {
    let theme = &app.theme;

    let is_focused = app.active_panel == ActivePanel::Context;
    let border_color = if is_focused { theme.border_focused } else { theme.border };

    let block = Block::default()
        .title(" Context ")
        .title_style(Style::default().fg(if is_focused { theme.accent } else { theme.text_secondary }).bold())
        .borders(Borders::ALL)
        .border_style(Style::default().fg(border_color))
        .style(Style::default().bg(theme.bg_secondary));

    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .margin(1)
        .constraints([
            Constraint::Length(4), // Model info
            Constraint::Length(1), // Separator
            Constraint::Min(3),   // Memory items
            Constraint::Length(1), // Separator
            Constraint::Length(4), // Graph connections
        ])
        .split(block.inner(area));

    frame.render_widget(block, area);

    // Model info section
    let model_lines = vec![
        Line::from(Span::styled("  Model", Style::default().fg(theme.accent).bold())),
        Line::from(Span::styled(
            format!("  {}", app.ai_model),
            Style::default().fg(theme.text_primary),
        )),
        Line::from(Span::styled(
            "  Status: Ready",
            Style::default().fg(theme.success),
        )),
    ];
    frame.render_widget(Paragraph::new(model_lines), chunks[0]);

    // Separator
    frame.render_widget(
        Paragraph::new(Line::from(Span::styled(
            "  ─────────────────",
            Style::default().fg(theme.surface_tertiary),
        ))),
        chunks[1],
    );

    // Memory items section
    let mut memory_lines = vec![
        Line::from(Span::styled("  Recent Memory", Style::default().fg(theme.accent).bold())),
    ];
    if app.context_memory_items.is_empty() {
        memory_lines.push(Line::from(Span::styled(
            "  No memory items yet",
            Style::default().fg(theme.text_tertiary).italic(),
        )));
    } else {
        for item in &app.context_memory_items {
            memory_lines.push(Line::from(Span::styled(
                format!("  • {}", item),
                Style::default().fg(theme.text_secondary),
            )));
        }
    }
    frame.render_widget(Paragraph::new(memory_lines).wrap(Wrap { trim: false }), chunks[2]);

    // Separator
    frame.render_widget(
        Paragraph::new(Line::from(Span::styled(
            "  ─────────────────",
            Style::default().fg(theme.surface_tertiary),
        ))),
        chunks[3],
    );

    // Graph connections section
    let graph_lines = vec![
        Line::from(Span::styled("  Graph", Style::default().fg(theme.accent).bold())),
        Line::from(Span::styled(
            "  0 nodes │ 0 edges",
            Style::default().fg(theme.text_tertiary),
        )),
    ];
    frame.render_widget(Paragraph::new(graph_lines), chunks[4]);
}

/// Render the sidebar with conversation history
fn render_sidebar(frame: &mut Frame, area: Rect, app: &App) {
    let theme = &app.theme;

    let block = Block::default()
        .title(" History ")
        .title_style(Style::default().fg(theme.accent).bold())
        .borders(Borders::ALL)
        .border_style(Style::default().fg(theme.border))
        .style(Style::default().bg(theme.bg_secondary));

    let items: Vec<ListItem> = if app.history.is_empty() {
        vec![ListItem::new(Span::styled(
            "No conversations yet",
            Style::default().fg(theme.text_tertiary).italic(),
        ))]
    } else {
        app.history
            .iter()
            .enumerate()
            .map(|(i, conv)| {
                let first_msg = conv
                    .messages
                    .first()
                    .map(|m| {
                        let preview: String = m.content.chars().take(30).collect();
                        if m.content.len() > 30 {
                            format!("{}...", preview)
                        } else {
                            preview
                        }
                    })
                    .unwrap_or_else(|| "Empty".to_string());

                let style = if i == app.sidebar_selected {
                    Style::default().fg(theme.accent).bold().bg(theme.surface_primary)
                } else {
                    Style::default().fg(theme.text_primary)
                };

                ListItem::new(Span::styled(
                    format!(" {} │ {}", conv.messages.len(), first_msg),
                    style,
                ))
            })
            .collect()
    };

    let list = List::new(items).block(block);
    frame.render_widget(list, area);
}

/// Render the header
fn render_header(frame: &mut Frame, area: Rect, app: &App) {
    let theme = &app.theme;

    let title = format!(
        " TERMIO {} ",
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
        "Messages: {} │ Ctrl+V voice │ Ctrl+S sync │ Ctrl+H help │ Ctrl+P plugins │ Tab panels",
        msg_count
    );

    let paragraph = Paragraph::new(content)
        .block(block)
        .style(Style::default().fg(theme.text_secondary));

    frame.render_widget(paragraph, area);
}

/// Render the conversation area with basic markdown support
fn render_conversation(frame: &mut Frame, area: Rect, app: &App) {
    let theme = &app.theme;

    let is_focused = app.active_panel == ActivePanel::Conversation;
    let border_color = if is_focused { theme.border_focused } else { theme.border };

    let block = Block::default()
        .title(" Conversation ")
        .title_style(Style::default().fg(theme.text_secondary))
        .borders(Borders::ALL)
        .border_style(Style::default().fg(border_color))
        .style(Style::default().bg(theme.bg_primary));

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

            lines.push(Line::from(Span::styled(prefix, style)));

            // Basic markdown rendering
            let mut in_code_block = false;
            for line in message.content.lines() {
                if line.starts_with("```") {
                    in_code_block = !in_code_block;
                    if in_code_block {
                        lines.push(Line::from(Span::styled(
                            "  ┌─ code ──────────────",
                            Style::default().fg(theme.surface_tertiary),
                        )));
                    } else {
                        lines.push(Line::from(Span::styled(
                            "  └────────────────────",
                            Style::default().fg(theme.surface_tertiary),
                        )));
                    }
                } else if in_code_block {
                    lines.push(Line::from(Span::styled(
                        format!("  │ {}", line),
                        Style::default().fg(theme.warning).bg(theme.bg_tertiary),
                    )));
                } else {
                    // Basic inline markdown: **bold**, *italic*, `code`
                    let rendered = render_markdown_line(line, theme);
                    lines.push(rendered);
                }
            }

            lines.push(Line::from(""));
        }
    }

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

/// Render a single line with basic markdown: **bold**, *italic*, `code`
fn render_markdown_line<'a>(line: &str, theme: &crate::theme::Theme) -> Line<'a> {
    let mut spans: Vec<Span<'a>> = Vec::new();
    spans.push(Span::raw("  ".to_string()));

    let mut chars = line.chars().peekable();
    let mut current = String::new();

    while let Some(c) = chars.next() {
        match c {
            '`' => {
                // Flush current text
                if !current.is_empty() {
                    spans.push(Span::styled(current.clone(), Style::default().fg(theme.text_primary)));
                    current.clear();
                }
                // Collect until closing `
                let mut code = String::new();
                while let Some(&next) = chars.peek() {
                    if next == '`' {
                        chars.next();
                        break;
                    }
                    code.push(chars.next().unwrap());
                }
                spans.push(Span::styled(code, Style::default().fg(theme.warning).bg(theme.bg_tertiary)));
            }
            '*' if chars.peek() == Some(&'*') => {
                chars.next(); // consume second *
                if !current.is_empty() {
                    spans.push(Span::styled(current.clone(), Style::default().fg(theme.text_primary)));
                    current.clear();
                }
                let mut bold = String::new();
                while let Some(&next) = chars.peek() {
                    if next == '*' {
                        chars.next();
                        if chars.peek() == Some(&'*') {
                            chars.next();
                            break;
                        }
                        bold.push('*');
                    } else {
                        bold.push(chars.next().unwrap());
                    }
                }
                spans.push(Span::styled(bold, Style::default().fg(theme.text_primary).bold()));
            }
            '*' => {
                if !current.is_empty() {
                    spans.push(Span::styled(current.clone(), Style::default().fg(theme.text_primary)));
                    current.clear();
                }
                let mut italic = String::new();
                while let Some(&next) = chars.peek() {
                    if next == '*' {
                        chars.next();
                        break;
                    }
                    italic.push(chars.next().unwrap());
                }
                spans.push(Span::styled(italic, Style::default().fg(theme.text_primary).italic()));
            }
            _ => current.push(c),
        }
    }

    if !current.is_empty() {
        spans.push(Span::styled(current, Style::default().fg(theme.text_primary)));
    }

    Line::from(spans)
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

    let paragraph = Paragraph::new(input_text).block(block).style(style);

    frame.render_widget(paragraph, area);

    if app.input_mode == InputMode::Editing {
        frame.set_cursor(
            area.x + 1 + app.cursor_position as u16,
            area.y + 1,
        );
    }
}

/// Render the status bar with sync, notifications, model indicator per spec
fn render_status_bar(frame: &mut Frame, area: Rect, app: &App) {
    let theme = &app.theme;

    let mode = match app.input_mode {
        InputMode::Normal => "NORMAL",
        InputMode::Editing => "INSERT",
    };

    let recording = if app.is_recording { " 🔴 REC │" } else { "" };

    let sync_icon = match app.sync_status.as_str() {
        "Synced" => "✓",
        "Syncing..." => "⟳",
        _ => "?",
    };

    let notif = if app.notification_count > 0 {
        format!(" 🔔{}", app.notification_count)
    } else {
        String::new()
    };

    let panel = match app.active_panel {
        ActivePanel::Conversation => "CONV",
        ActivePanel::Context => "CTX",
    };

    let text = format!(
        " {} │{} {} │ {} {} │ {} │ {} ",
        mode, recording, app.status, sync_icon, app.sync_status, notif, panel
    );

    let style = Style::default()
        .bg(theme.surface_secondary)
        .fg(theme.text_secondary);

    let paragraph = Paragraph::new(text).style(style);
    frame.render_widget(paragraph, area);
}

/// Render the help overlay
fn render_help_overlay(frame: &mut Frame, app: &App) {
    let theme = &app.theme;
    let area = centered_rect(60, 70, frame.size());

    frame.render_widget(Clear, area);

    let block = Block::default()
        .title(" Help — Keyboard Shortcuts ")
        .title_style(Style::default().fg(theme.accent).bold())
        .borders(Borders::ALL)
        .border_style(Style::default().fg(theme.accent))
        .style(Style::default().bg(theme.bg_secondary));

    let help_text = vec![
        Line::from(Span::styled("  Navigation", Style::default().fg(theme.accent).bold())),
        Line::from(Span::styled("  Enter        Start typing / Send message", Style::default().fg(theme.text_primary))),
        Line::from(Span::styled("  Esc          Stop typing / Close overlay", Style::default().fg(theme.text_primary))),
        Line::from(Span::styled("  Up / Down    Scroll conversation", Style::default().fg(theme.text_primary))),
        Line::from(""),
        Line::from(Span::styled("  Features", Style::default().fg(theme.accent).bold())),
        Line::from(Span::styled("  Ctrl+N       New conversation", Style::default().fg(theme.text_primary))),
        Line::from(Span::styled("  Ctrl+V       Toggle voice recording", Style::default().fg(theme.text_primary))),
        Line::from(Span::styled("  Ctrl+S       Trigger sync", Style::default().fg(theme.text_primary))),
        Line::from(Span::styled("  Ctrl+H       Toggle this help", Style::default().fg(theme.text_primary))),
        Line::from(Span::styled("  Ctrl+P       Plugin manager", Style::default().fg(theme.text_primary))),
        Line::from(Span::styled("  Ctrl+B       Toggle sidebar", Style::default().fg(theme.text_primary))),
        Line::from(Span::styled("  Ctrl+K       Command palette", Style::default().fg(theme.text_primary))),
        Line::from(Span::styled("  Tab          Switch panel focus", Style::default().fg(theme.text_primary))),
        Line::from(Span::styled("  Ctrl+T       Toggle theme", Style::default().fg(theme.text_primary))),
        Line::from(Span::styled("  Space        Toggle voice (Normal mode)", Style::default().fg(theme.text_primary))),
        Line::from(""),
        Line::from(Span::styled("  System", Style::default().fg(theme.accent).bold())),
        Line::from(Span::styled("  Ctrl+Q       Quit", Style::default().fg(theme.text_primary))),
        Line::from(""),
        Line::from(Span::styled("  Press Esc to close", Style::default().fg(theme.text_tertiary).italic())),
    ];

    let paragraph = Paragraph::new(help_text)
        .block(block)
        .wrap(Wrap { trim: false });

    frame.render_widget(paragraph, area);
}

/// Render the command palette
fn render_command_palette(frame: &mut Frame, app: &App) {
    let theme = &app.theme;
    let area = centered_rect(50, 20, frame.size());

    frame.render_widget(Clear, area);

    let block = Block::default()
        .title(" Command Palette ")
        .title_style(Style::default().fg(theme.accent).bold())
        .borders(Borders::ALL)
        .border_style(Style::default().fg(theme.accent))
        .style(Style::default().bg(theme.bg_secondary));

    let prompt = if app.command_input.is_empty() {
        "Type a command: new, theme, sidebar, help, sync, quit"
    } else {
        &app.command_input
    };

    let style = if app.command_input.is_empty() {
        Style::default().fg(theme.text_tertiary).italic()
    } else {
        Style::default().fg(theme.text_primary)
    };

    let paragraph = Paragraph::new(prompt).block(block).style(style);

    frame.render_widget(paragraph, area);

    frame.set_cursor(
        area.x + 1 + app.command_input.len() as u16,
        area.y + 1,
    );
}

/// Render the plugin manager overlay
fn render_plugin_manager(frame: &mut Frame, app: &App) {
    let theme = &app.theme;
    let area = centered_rect(70, 60, frame.size());

    frame.render_widget(Clear, area);

    let block = Block::default()
        .title(" Plugin Manager ")
        .title_style(Style::default().fg(theme.accent).bold())
        .borders(Borders::ALL)
        .border_style(Style::default().fg(theme.accent))
        .style(Style::default().bg(theme.bg_secondary));

    let lines = vec![
        Line::from(Span::styled("  Installed Plugins", Style::default().fg(theme.accent).bold())),
        Line::from(""),
        Line::from(Span::styled("  No plugins installed yet.", Style::default().fg(theme.text_tertiary).italic())),
        Line::from(""),
        Line::from(Span::styled("  Plugin Directory: ~/.termio/plugins", Style::default().fg(theme.text_secondary))),
        Line::from(Span::styled("  Registry: Not connected", Style::default().fg(theme.text_tertiary))),
        Line::from(""),
        Line::from(Span::styled("  Press Esc to close", Style::default().fg(theme.text_tertiary).italic())),
    ];

    let paragraph = Paragraph::new(lines)
        .block(block)
        .wrap(Wrap { trim: false });

    frame.render_widget(paragraph, area);
}

/// Helper: create a centered rectangle
fn centered_rect(percent_x: u16, percent_y: u16, r: Rect) -> Rect {
    let popup_layout = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Percentage((100 - percent_y) / 2),
            Constraint::Percentage(percent_y),
            Constraint::Percentage((100 - percent_y) / 2),
        ])
        .split(r);

    Layout::default()
        .direction(Direction::Horizontal)
        .constraints([
            Constraint::Percentage((100 - percent_x) / 2),
            Constraint::Percentage(percent_x),
            Constraint::Percentage((100 - percent_x) / 2),
        ])
        .split(popup_layout[1])[1]
}
