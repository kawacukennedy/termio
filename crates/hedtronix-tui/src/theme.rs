//! Theme configuration
//!
//! Implements the iOS 26 design system colors from the specification.

use ratatui::style::Color;

/// Theme configuration with colors from iOS 26 design system
#[derive(Debug, Clone)]
pub struct Theme {
    /// Whether this is a dark theme
    pub is_dark: bool,

    /// Background colors
    pub bg_primary: Color,
    pub bg_secondary: Color,
    pub bg_tertiary: Color,

    /// Surface colors
    pub surface_primary: Color,
    pub surface_secondary: Color,
    pub surface_tertiary: Color,

    /// Text colors
    pub text_primary: Color,
    pub text_secondary: Color,
    pub text_tertiary: Color,
    pub text_disabled: Color,

    /// Accent colors
    pub accent: Color,
    pub accent_dim: Color,

    /// Functional colors
    pub success: Color,
    pub warning: Color,
    pub error: Color,
    pub info: Color,

    /// Border colors
    pub border: Color,
    pub border_focused: Color,
}

impl Theme {
    /// Create a dark theme (iOS 26 dark mode)
    pub fn dark() -> Self {
        Self {
            is_dark: true,
            // Background
            bg_primary: Color::Rgb(12, 12, 12),    // #0C0C0C
            bg_secondary: Color::Rgb(23, 23, 23),  // #171717
            bg_tertiary: Color::Rgb(38, 38, 38),   // #262626

            // Surface
            surface_primary: Color::Rgb(23, 23, 23),   // #171717
            surface_secondary: Color::Rgb(38, 38, 38), // #262626
            surface_tertiary: Color::Rgb(64, 64, 64),  // #404040

            // Text
            text_primary: Color::Rgb(250, 250, 250),  // #FAFAFA
            text_secondary: Color::Rgb(212, 212, 212), // #D4D4D4
            text_tertiary: Color::Rgb(163, 163, 163),  // #A3A3A3
            text_disabled: Color::Rgb(82, 82, 82),     // #525252

            // Accent (primary.500)
            accent: Color::Rgb(14, 165, 233),     // #0EA5E9
            accent_dim: Color::Rgb(3, 105, 161),  // #0369A1

            // Functional
            success: Color::Rgb(16, 185, 129),  // #10B981
            warning: Color::Rgb(245, 158, 11),  // #F59E0B
            error: Color::Rgb(239, 68, 68),     // #EF4444
            info: Color::Rgb(59, 130, 246),     // #3B82F6

            // Border
            border: Color::Rgb(64, 64, 64),         // neutral.700
            border_focused: Color::Rgb(14, 165, 233), // primary.500
        }
    }

    /// Create a light theme (iOS 26 light mode)
    pub fn light() -> Self {
        Self {
            is_dark: false,
            // Background
            bg_primary: Color::Rgb(255, 255, 255),   // #FFFFFF
            bg_secondary: Color::Rgb(245, 245, 245), // #F5F5F5
            bg_tertiary: Color::Rgb(229, 229, 229),  // #E5E5E5

            // Surface
            surface_primary: Color::Rgb(255, 255, 255),   // #FFFFFF
            surface_secondary: Color::Rgb(250, 250, 250), // #FAFAFA
            surface_tertiary: Color::Rgb(245, 245, 245),  // #F5F5F5

            // Text
            text_primary: Color::Rgb(23, 23, 23),      // #171717
            text_secondary: Color::Rgb(82, 82, 82),    // #525252
            text_tertiary: Color::Rgb(163, 163, 163),  // #A3A3A3
            text_disabled: Color::Rgb(212, 212, 212),  // #D4D4D4

            // Accent (primary.500)
            accent: Color::Rgb(14, 165, 233),     // #0EA5E9
            accent_dim: Color::Rgb(2, 132, 199),  // #0284C7

            // Functional
            success: Color::Rgb(16, 185, 129),  // #10B981
            warning: Color::Rgb(245, 158, 11),  // #F59E0B
            error: Color::Rgb(239, 68, 68),     // #EF4444
            info: Color::Rgb(59, 130, 246),     // #3B82F6

            // Border
            border: Color::Rgb(229, 229, 229),      // neutral.200
            border_focused: Color::Rgb(14, 165, 233), // primary.500
        }
    }
}

impl Default for Theme {
    fn default() -> Self {
        Self::dark()
    }
}
