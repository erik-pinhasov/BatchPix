"""
Theme configuration for the application.
Centralized colors, fonts, and style settings.
"""


class Theme:
    """Application theme with colors, fonts, and dimensions."""
    
    # Color palette (Light, Dark) tuples for CustomTkinter
    COLORS = {
        'bg': ("#ffffff", "#0f0f15"),
        'card': ("#f3f4f6", "#1a1a24"),
        'accent': ("#8b5cf6", "#8b5cf6"),     # Violet
        'accent_hover': ("#7c3aed", "#7c3aed"),
        'text': ("#1f2937", "#ffffff"),
        'text_dim': ("#6b7280", "#9ca3af"),
        'border': ("#e5e7eb", "#27272a"),
        'input': ("#ffffff", "#27272a"),
        'input_border': ("#d1d5db", "#3f3f46"),
        'success': ("#22c55e", "#22c55e"),    # Green
        'error': ("#ef4444", "#ef4444"),      # Red
        'button': ("#e5e7eb", "#3f3f46"),
        'button_hover': ("#d1d5db", "#52525b"),
    }
    
    # Modern font settings (Bigger sizes)
    # CTk uses (Required_Font_Family, Size, Weight) tuple
    FONTS = {
        'heading': ('Segoe UI', 16, 'bold'),
        'body': ('Segoe UI', 13),
        'small': ('Segoe UI', 11),
        'button': ('Segoe UI', 13, 'bold'),
        'button_large': ('Segoe UI', 16, 'bold'),
        'mono': ('Consolas', 12),
    }
    
    # Dimensions (Rounded styling)
    DIMENSIONS = {
        'corner_radius': 10,
        'btn_radius_small': 6,
        'btn_radius': 8,
        'padding': 15,
        'gap': 10
    }
    
    # Window settings
    WINDOW = {
        'min_width': 520,  # ~10% narrower
        'min_height': 785,
        'logs_width': 450,
    }
    
    @classmethod
    def get_color(cls, name: str) -> tuple:
        """Get a color tuple (light, dark)."""
        return cls.COLORS.get(name, ("#ffffff", "#0f0f15"))
    
    @classmethod
    def get_font(cls, name: str) -> tuple:
        """Get a font tuple."""
        return cls.FONTS.get(name, ('Segoe UI', 13))
