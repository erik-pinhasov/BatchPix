"""
Theme configuration for the application.
Centralized colors, fonts, and style settings.
"""


class Theme:
    """Application theme with colors, fonts, and dimensions."""
    
    # Color palette
    COLORS = {
        'bg': '#0f0f15',
        'card': '#1a1a24',
        'accent': '#8b5cf6',
        'accent_hover': '#a78bfa',
        'text': '#ffffff',
        'text_dim': '#9ca3af',
        'border': '#27272a',
        'input': '#27272a',
        'input_border': '#3f3f46',
        'success': '#22c55e',
        'error': '#ef4444',
        'button': '#3f3f46',
        'button_hover': '#52525b',
    }
    
    # Font settings
    FONTS = {
        'heading': ('Segoe UI', 12, 'bold'),
        'body': ('Segoe UI', 11),
        'small': ('Segoe UI', 10),
        'button': ('Segoe UI', 10, 'bold'),
        'button_large': ('Segoe UI', 14, 'bold'),
        'mono': ('Consolas', 10),
    }
    
    # Dimensions
    PADDING = {
        'card': (16, 12),
        'button': (12, 4),
        'button_large': (16, 8),
    }
    
    # Window settings
    WINDOW = {
        'min_width': 580,
        'min_height': 850,
        'logs_width': 380,
    }
    
    @classmethod
    def get_color(cls, name: str) -> str:
        """Get a color by name."""
        return cls.COLORS.get(name, '#ffffff')
    
    @classmethod
    def get_font(cls, name: str) -> tuple:
        """Get a font by name."""
        return cls.FONTS.get(name, ('Segoe UI', 11))
