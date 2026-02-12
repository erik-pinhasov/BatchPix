"""
Card components for the application UI.
Each card represents a major section of the interface.
"""

import json
import os
import tkinter as tk
from .theme import Theme
from .widgets import (
    create_entry, create_button, create_checkbox, create_label,
    create_radiobutton, create_combobox, create_spinbox
)


class Card(tk.Frame):
    """Base card component with consistent styling."""
    
    def __init__(self, parent, title=None):
        super().__init__(
            parent,
            bg=Theme.get_color('card'),
            padx=Theme.PADDING['card'][0],
            pady=Theme.PADDING['card'][1],
            highlightbackground=Theme.get_color('border'),
            highlightthickness=1
        )
        
        if title:
            tk.Label(
                self,
                text=title,
                font=Theme.get_font('heading'),
                bg=Theme.get_color('card'),
                fg=Theme.get_color('accent')
            ).pack(anchor='w', pady=(0, 8))


class InputCard(Card):
    """Input selection card with folder/files options."""
    
    def __init__(self, parent, callbacks):
        super().__init__(parent, "📁 INPUT")
        
        self.callbacks = callbacks
        self._build_folder_row()
        self._build_files_row()
    
    def _build_folder_row(self):
        row = tk.Frame(self, bg=Theme.get_color('card'))
        row.pack(fill='x', pady=3)
        
        self.input_mode = tk.StringVar(value="folder")
        create_radiobutton(
            row, "Folder", self.input_mode, "folder",
            self.callbacks.get('on_mode_change')
        ).pack(side='left')
        
        self.folder_var = tk.StringVar()
        self.folder_var.trace_add('write', self.callbacks.get('on_folder_change', lambda *a: None))
        
        self.folder_entry = create_entry(row, self.folder_var, 28)
        self.folder_entry.pack(side='left', padx=8, fill='x', expand=True)
        
        self.folder_btn = create_button(row, "Browse", self.callbacks.get('browse_folder'), small=True)
        self.folder_btn.pack(side='left')
    
    def _build_files_row(self):
        row = tk.Frame(self, bg=Theme.get_color('card'))
        row.pack(fill='x', pady=3)
        
        create_radiobutton(
            row, "Files", self.input_mode, "files",
            self.callbacks.get('on_mode_change')
        ).pack(side='left')
        
        self.files_label = create_label(row, "None", dim=True)
        self.files_label.pack(side='left', padx=8)
        
        self.files_btn = create_button(row, "Select", self.callbacks.get('browse_files'), small=True)
        self.files_btn.config(state='disabled')
        self.files_btn.pack(side='left')
    
    def update_mode(self):
        """Update widget states based on input mode."""
        if self.input_mode.get() == "folder":
            self.folder_entry.config(state='normal')
            self.folder_btn.config(state='normal')
            self.files_btn.config(state='disabled')
        else:
            self.folder_entry.config(state='disabled')
            self.folder_btn.config(state='disabled')
            self.files_btn.config(state='normal')
    
    def set_files_count(self, count):
        """Update the files count label."""
        self.files_label.config(text=f"{count} files" if count else "None")


class OutputCard(Card):
    """Output folder selection card."""
    
    def __init__(self, parent, callbacks):
        super().__init__(parent, "💾 OUTPUT")
        
        row = tk.Frame(self, bg=Theme.get_color('card'))
        row.pack(fill='x')
        
        create_label(row, "Save to:").pack(side='left')
        
        self.output_var = tk.StringVar()
        create_entry(row, self.output_var, 28).pack(side='left', padx=8, fill='x', expand=True)
        
        create_button(row, "Browse", callbacks.get('browse_output'), small=True).pack(side='left')


RESIZE_DESCRIPTIONS = {
    "thumbnail": "150px", "small": "480px", "medium": "800px",
    "large": "1200px", "hd": "1920px", "4k": "3840px", "custom": "Custom"
}


class ActionsCard(Card):
    """Actions selection card with all processing options."""
    
    def __init__(self, parent, callbacks):
        super().__init__(parent, "⚡ ACTIONS")
        
        self.callbacks = callbacks
        self._config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.copyright_config.json')
        self._saved_config = self._load_config()
        self._build_controls()
        self._build_separator()
        self._build_actions()
    
    def _build_controls(self):
        """Build select/deselect all buttons."""
        row = tk.Frame(self, bg=Theme.get_color('card'))
        row.pack(fill='x', pady=(0, 6))
        
        create_button(row, "Select All", self._select_all, small=True).pack(side='left')
        create_button(row, "Deselect All", self._deselect_all, small=True).pack(side='left', padx=10)
    
    def _build_separator(self):
        tk.Frame(self, bg=Theme.get_color('border'), height=1).pack(fill='x', pady=8)
    
    def _build_actions(self):
        """Build all action checkboxes with options."""
        # Action variables (all checked by default)
        self.var_enhance = tk.BooleanVar(value=True)
        self.var_resize = tk.BooleanVar(value=True)
        self.var_crop = tk.BooleanVar(value=True)
        self.var_webp = tk.BooleanVar(value=True)
        self.var_strip = tk.BooleanVar(value=True)
        self.var_rename = tk.BooleanVar(value=True)
        self.var_copyright = tk.BooleanVar(value=True)
        
        self.action_vars = [
            self.var_enhance, self.var_resize, self.var_crop, self.var_webp,
            self.var_strip, self.var_rename, self.var_copyright
        ]
        
        # 1. Enhance
        row = tk.Frame(self, bg=Theme.get_color('card'))
        row.pack(fill='x', pady=2)
        create_checkbox(row, "Enhance", self.var_enhance).pack(side='left')
        self.model_var = tk.StringVar(value="x4-quality")
        create_combobox(row, self.model_var, ["x4-quality", "x4-fast", "x2-quality"]).pack(side='left', padx=6)
        create_label(row, "AI upscale", dim=True).pack(side='left')
        
        # 2. Resize
        row = tk.Frame(self, bg=Theme.get_color('card'))
        row.pack(fill='x', pady=2)
        create_checkbox(row, "Resize", self.var_resize).pack(side='left')
        self.preset_var = tk.StringVar(value="large")
        combo = create_combobox(row, self.preset_var, list(RESIZE_DESCRIPTIONS.keys()))
        combo.pack(side='left', padx=6)
        combo.bind("<<ComboboxSelected>>", self._on_resize_change)
        self.resize_label = create_label(row, "1200px", dim=True)
        self.resize_label.pack(side='left')
        self.aspect_var = tk.BooleanVar(value=True)
        create_checkbox(row, "Aspect ratio", self.aspect_var).pack(side='left', padx=8)
        
        # Custom size frame
        self.custom_frame = tk.Frame(self, bg=Theme.get_color('card'))
        self.width_var = tk.IntVar(value=1200)
        self.height_var = tk.IntVar(value=1200)
        create_label(self.custom_frame, "W:").pack(side='left')
        create_spinbox(self.custom_frame, self.width_var, 100, 8000, 6).pack(side='left', padx=2)
        create_label(self.custom_frame, "H:").pack(side='left', padx=(8, 0))
        create_spinbox(self.custom_frame, self.height_var, 100, 8000, 6).pack(side='left', padx=2)
        
        # 3. Smart Crop
        row = tk.Frame(self, bg=Theme.get_color('card'))
        row.pack(fill='x', pady=2)
        create_checkbox(row, "Smart Crop", self.var_crop).pack(side='left')
        create_label(row, "Remove empty borders", dim=True).pack(side='left', padx=6)
        
        # 4. WebP
        create_checkbox(self, "Convert to WebP", self.var_webp).pack(anchor='w', pady=2)
        
        # 5. Strip Metadata
        row = tk.Frame(self, bg=Theme.get_color('card'))
        row.pack(fill='x', pady=2)
        create_checkbox(row, "Strip Metadata", self.var_strip).pack(side='left')
        create_label(row, "Remove GPS & camera info", dim=True).pack(side='left', padx=6)
        
        # 7. AI Rename
        row = tk.Frame(self, bg=Theme.get_color('card'))
        row.pack(fill='x', pady=2)
        create_checkbox(row, "AI Rename", self.var_rename).pack(side='left')
        create_label(row, "SEO-friendly filenames", dim=True).pack(side='left', padx=6)
        
        # 8. Copyright
        row = tk.Frame(self, bg=Theme.get_color('card'))
        row.pack(fill='x', pady=2)
        create_checkbox(row, "Copyright", self.var_copyright).pack(side='left')
        create_label(row, "Embed metadata", dim=True).pack(side='left', padx=6)
        
        # Copyright inputs
        row = tk.Frame(self, bg=Theme.get_color('card'))
        row.pack(fill='x', pady=(4, 0), padx=(20, 0))
        create_label(row, "Notice:").pack(side='left')
        self.copyright_var = tk.StringVar(value=self._saved_config.get('copyright_text', '© 2026 Your Name'))
        self.copyright_var.trace_add('write', lambda *_: self._save_config())
        create_entry(row, self.copyright_var, 20).pack(side='left', padx=6)
        create_label(row, "Artist:").pack(side='left', padx=(8, 0))
        self.artist_var = tk.StringVar(value=self._saved_config.get('artist', 'Your Name'))
        self.artist_var.trace_add('write', lambda *_: self._save_config())
        create_entry(row, self.artist_var, 14).pack(side='left', padx=6)
    
    def _on_resize_change(self, event=None):
        """Handle resize preset change."""
        preset = self.preset_var.get()
        self.resize_label.config(text=RESIZE_DESCRIPTIONS.get(preset, ""))
        if preset == "custom":
            self.custom_frame.pack(fill='x', pady=2, padx=(20, 0))
        else:
            self.custom_frame.pack_forget()
    
    def _select_all(self):
        for var in self.action_vars:
            var.set(True)
    
    def _deselect_all(self):
        for var in self.action_vars:
            var.set(False)
    
    def _load_config(self):
        """Load saved copyright/artist from config file."""
        try:
            if os.path.exists(self._config_path):
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return {}
    
    def _save_config(self):
        """Save copyright/artist to config file."""
        try:
            data = {
                'copyright_text': self.copyright_var.get(),
                'artist': self.artist_var.get(),
            }
            with open(self._config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False)
        except Exception:
            pass
    
    def get_options(self):
        """Get all action options as a dictionary."""
        return {
            'enhance': self.var_enhance.get(),
            'model': self.model_var.get(),
            'resize': self.var_resize.get(),
            'preset': self.preset_var.get(),
            'width': self.width_var.get(),
            'height': self.height_var.get(),
            'aspect': self.aspect_var.get(),
            'crop': self.var_crop.get(),
            'webp': self.var_webp.get(),
            'strip': self.var_strip.get(),
            'rename': self.var_rename.get(),
            'copyright': self.var_copyright.get(),
            'copyright_text': self.copyright_var.get(),
            'artist': self.artist_var.get(),
        }
