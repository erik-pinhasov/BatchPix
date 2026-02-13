"""
Card components for the application UI using CustomTkinter.
Each card represents a major section of the interface.
"""

import json
import os
import sys
import customtkinter as ctk
from tkinter import filedialog, messagebox
from .theme import Theme
from .widgets import (
    create_entry, create_button, create_checkbox, create_label,
    create_radiobutton, create_combobox, create_spinbox
)


def _get_base_path():
    """Get project root — works for both dev and frozen exe."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


CONVERT_FORMATS = ['WebP', 'PNG', 'JPEG', 'BMP', 'TIFF']


class Card(ctk.CTkFrame):
    """Base card component with consistent styling."""
    
    def __init__(self, parent, title=None):
        super().__init__(
            parent,
            fg_color=Theme.get_color('card'),
            corner_radius=Theme.DIMENSIONS['corner_radius'],
            border_width=1,
            border_color=Theme.get_color('border')
        )
        self.pack(fill='x', pady=(0, Theme.DIMENSIONS['gap']))
        
        # Inner padding frame to handle content spacing
        self.inner = ctk.CTkFrame(self, fg_color="transparent")
        self.inner.pack(fill='both', expand=True, padx=Theme.DIMENSIONS['padding'], pady=Theme.DIMENSIONS['padding'])
        
        if title:
            ctk.CTkLabel(
                self.inner,
                text=title,
                font=Theme.get_font('heading'),
                text_color=Theme.get_color('accent')
            ).pack(anchor='w', pady=(0, 10))


class InputCard(Card):
    """Input selection card with folder/files options."""
    
    def __init__(self, parent, callbacks):
        super().__init__(parent, "📁 INPUT")
        
        self.callbacks = callbacks
        self._build_folder_row()
        self._build_files_row()
    
    def _build_folder_row(self):
        row = ctk.CTkFrame(self.inner, fg_color="transparent")
        row.pack(fill='x', pady=5)
        
        self.input_mode = ctk.StringVar(value="folder")
        create_radiobutton(
            row, "Folder", self.input_mode, "folder",
            self.callbacks.get('on_mode_change')
        ).pack(side='left')
        
        self.folder_var = ctk.StringVar()
        self.folder_var.trace_add('write', self.callbacks.get('on_folder_change', lambda *a: None))
        
        self.folder_entry = create_entry(row, self.folder_var, 300)
        self.folder_entry.pack(side='left', padx=10, fill='x', expand=True)
        
        self.folder_btn = create_button(row, "Browse", self.callbacks.get('browse_folder'), small=True)
        self.folder_btn.pack(side='left')
    
    def _build_files_row(self):
        row = ctk.CTkFrame(self.inner, fg_color="transparent")
        row.pack(fill='x', pady=5)
        
        create_radiobutton(
            row, "Files", self.input_mode, "files",
            self.callbacks.get('on_mode_change')
        ).pack(side='left')
        
        self.files_label = create_label(row, "0 files selected", dim=True)
        self.files_label.pack(side='left', padx=10)
        
        self.files_btn = create_button(row, "Select", self.callbacks.get('browse_files'), small=True)
        self.files_btn.configure(state='disabled')
        self.files_btn.pack(side='left')
    
    def update_mode(self):
        """Update widget states based on input mode."""
        if self.input_mode.get() == "folder":
            self.folder_entry.configure(state='normal')
            self.folder_btn.configure(state='normal')
            self.files_btn.configure(state='disabled')
        else:
            self.folder_entry.configure(state='disabled')
            self.folder_btn.configure(state='disabled')
            self.files_btn.configure(state='normal')
    
    def set_files_count(self, count):
        """Update the files count label."""
        self.files_label.configure(text=f"{count} files" if count else "None")


class OutputCard(Card):
    """Output folder selection card."""
    
    def __init__(self, parent, callbacks):
        super().__init__(parent, "💾 OUTPUT")
        
        row = ctk.CTkFrame(self.inner, fg_color="transparent")
        row.pack(fill='x')
        
        create_label(row, "Save to:").pack(side='left')
        
        self.output_var = ctk.StringVar()
        create_entry(row, self.output_var, 300).pack(side='left', padx=10, fill='x', expand=True)
        
        create_button(row, "Browse", callbacks.get('browse_output'), small=True).pack(side='left')


RESIZE_DESCRIPTIONS = {
    "thumbnail": "150px", "small": "480px", "medium": "800px",
    "large": "1200px", "hd": "1920px", "4k": "3840px", "custom": "Custom"
}


class TermMapDialog(ctk.CTkToplevel):
    """Modal dialog for editing AI rename term mappings."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Edit Rename Map")
        self.geometry("500x500")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        # Determine colors for consistent look
        bg_color = Theme.get_color('bg')
        self.configure(fg_color=bg_color)

        self._map_path = os.path.join(_get_base_path(), 'term_mappings.json')

        # Header
        ctk.CTkLabel(
            self, text="Term Mappings",
            font=Theme.get_font('heading'),
            text_color=Theme.get_color('accent')
        ).pack(anchor='w', padx=20, pady=(20, 5))

        ctk.CTkLabel(
            self, text='Map generic AI captions to specific terms (JSON format)',
            font=Theme.get_font('small'),
            text_color=Theme.get_color('text_dim')
        ).pack(anchor='w', padx=20)

        # Text editor (CTkTextbox)
        self.text = ctk.CTkTextbox(
            self, width=460, height=300,
            font=Theme.get_font('mono'),
            fg_color=Theme.get_color('input'),
            text_color=Theme.get_color('text'),
            border_width=1,
            border_color=Theme.get_color('input_border'),
            corner_radius=Theme.DIMENSIONS['corner_radius']
        )
        self.text.pack(padx=20, pady=15, fill='both', expand=True)

        # Load current mappings
        self._load()

        # Buttons
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill='x', padx=20, pady=(0, 20))
        create_button(btn_row, "Save", self._save, small=True).pack(side='right', padx=(10, 0))
        create_button(btn_row, "Cancel", self.destroy, small=True).pack(side='right')

    def _load(self):
        try:
            if os.path.exists(self._map_path):
                with open(self._map_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {}
            self.text.insert('1.0', json.dumps(data, indent=4, ensure_ascii=False))
        except Exception:
            self.text.insert('1.0', '{}')

    def _save(self):
        try:
            data = json.loads(self.text.get('1.0', 'end-1c'))
            with open(self._map_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            self.destroy()
        except json.JSONDecodeError as e:
            messagebox.showerror("Invalid JSON", f"Fix the JSON syntax:\n{e}", parent=self)


class ActionsCard(Card):
    """Actions selection card with all processing options."""
    
    def __init__(self, parent, callbacks):
        super().__init__(parent, "⚡ ACTIONS")
        
        self.callbacks = callbacks
        self._config_path = os.path.join(_get_base_path(), '.copyright_config.json')
        self._saved_config = self._load_config()
        self._build_controls()
        self._build_separator()
        self._build_actions()
    
    def _build_controls(self):
        """Build select/deselect all buttons."""
        row = ctk.CTkFrame(self.inner, fg_color="transparent")
        row.pack(fill='x', pady=(0, 10))
        
        create_button(row, "Select All", self._select_all, small=True).pack(side='left')
        create_button(row, "Deselect All", self._deselect_all, small=True).pack(side='left', padx=10)
    
    def _build_separator(self):
        ctk.CTkFrame(self.inner, height=1, fg_color=Theme.get_color('border')).pack(fill='x', pady=10)
    
    def _build_actions(self):
        """Build all action checkboxes with options."""
        # Action variables (all checked by default)
        self.var_enhance = ctk.BooleanVar(value=True)
        self.var_resize = ctk.BooleanVar(value=True)
        self.var_crop = ctk.BooleanVar(value=True)
        self.var_convert = ctk.BooleanVar(value=True)
        self.var_strip = ctk.BooleanVar(value=True)
        self.var_rename = ctk.BooleanVar(value=True)
        self.var_copyright = ctk.BooleanVar(value=True)
        
        self.action_vars = [
            self.var_enhance, self.var_resize, self.var_crop, self.var_convert,
            self.var_strip, self.var_rename, self.var_copyright
        ]
        
        # 1. Enhance
        row = ctk.CTkFrame(self.inner, fg_color="transparent")
        row.pack(fill='x', pady=2)
        create_checkbox(row, "Enhance", self.var_enhance).pack(side='left')
        self.model_var = ctk.StringVar(value="x4-quality")
        create_combobox(row, self.model_var, ["x4-quality", "x4-fast", "x2-quality"], width=110).pack(side='left', padx=10)
        create_label(row, "AI upscale", dim=True).pack(side='left')
        
        # 2. Resize
        row = ctk.CTkFrame(self.inner, fg_color="transparent")
        row.pack(fill='x', pady=2)
        create_checkbox(row, "Resize", self.var_resize).pack(side='left')
        self.preset_var = ctk.StringVar(value="large")
        combo = create_combobox(row, self.preset_var, list(RESIZE_DESCRIPTIONS.keys()), width=110)
        combo.pack(side='left', padx=10)
        combo.configure(command=self._on_resize_change)
        
        # Dynamic Options Frame (Inline)
        self.resize_options_frame = ctk.CTkFrame(row, fg_color="transparent")
        self.resize_options_frame.pack(side='left')
        
        # Option A: Preset Info + Aspect Ratio
        self.preset_info_frame = ctk.CTkFrame(self.resize_options_frame, fg_color="transparent")
        self.resize_label = create_label(self.preset_info_frame, "1200px", dim=True)
        self.resize_label.pack(side='left')
        self.aspect_var = ctk.BooleanVar(value=True)
        create_checkbox(self.preset_info_frame, "Aspect ratio", self.aspect_var).pack(side='left', padx=15)
        
        # Option B: Custom W/H
        self.custom_size_frame = ctk.CTkFrame(self.resize_options_frame, fg_color="transparent")
        self.width_var = ctk.IntVar(value=1200)
        self.height_var = ctk.IntVar(value=1200)
        create_label(self.custom_size_frame, "W:").pack(side='left')
        create_spinbox(self.custom_size_frame, self.width_var, 100, 8000, 70).pack(side='left', padx=5)
        create_label(self.custom_size_frame, "H:").pack(side='left', padx=(10, 0))
        create_spinbox(self.custom_size_frame, self.height_var, 100, 8000, 70).pack(side='left', padx=5)
        
        # Initial State
        self.preset_info_frame.pack(side='left', fill='both')

        # 3. Smart Crop
        row = ctk.CTkFrame(self.inner, fg_color="transparent")
        row.pack(fill='x', pady=2)
        create_checkbox(row, "Smart Crop", self.var_crop).pack(side='left')
        create_label(row, "Remove empty borders", dim=True).pack(side='left', padx=10)
        
        # 4. Convert Format
        row = ctk.CTkFrame(self.inner, fg_color="transparent")
        row.pack(fill='x', pady=2)
        create_checkbox(row, "Convert Format", self.var_convert).pack(side='left')
        self.format_var = ctk.StringVar(value="WebP")
        create_combobox(row, self.format_var, CONVERT_FORMATS).pack(side='left', padx=10)
        
        # 5. Strip Metadata
        row = ctk.CTkFrame(self.inner, fg_color="transparent")
        row.pack(fill='x', pady=2)
        create_checkbox(row, "Strip Metadata", self.var_strip).pack(side='left')
        create_label(row, "Remove GPS & camera info", dim=True).pack(side='left', padx=10)
        
        # 6. AI Rename
        row = ctk.CTkFrame(self.inner, fg_color="transparent")
        row.pack(fill='x', pady=2)
        create_checkbox(row, "AI Rename", self.var_rename).pack(side='left')
        create_label(row, "SEO-friendly filenames", dim=True).pack(side='left', padx=10)
        create_button(row, "Edit Map", self._open_term_map, small=True).pack(side='left', padx=10)
        
        # 7. Copyright
        row = ctk.CTkFrame(self.inner, fg_color="transparent")
        row.pack(fill='x', pady=2)
        create_checkbox(row, "Copyright", self.var_copyright).pack(side='left')
        
        # Consolidated Copyright Input
        self.copyright_text_var = ctk.StringVar(value=self._saved_config.get('copyright_holder', 'Your Name'))
        self.copyright_text_var.trace_add('write', lambda *_: self._save_config())
        
        create_entry(row, self.copyright_text_var, 200).pack(side='left', padx=10)
        create_label(row, "(Holder Name)", dim=True).pack(side='left')
        
    def _on_resize_change(self, choice=None):
        """Handle resize preset change."""
        preset = self.preset_var.get()
        if preset == "custom":
            self.preset_info_frame.pack_forget()
            self.custom_size_frame.pack(side='left', fill='both', padx=(5, 0))
        else:
            self.custom_size_frame.pack_forget()
            self.preset_info_frame.pack(side='left', fill='both')
            self.resize_label.configure(text=RESIZE_DESCRIPTIONS.get(preset, ""))

    def _select_all(self):
        for var in self.action_vars:
            var.set(True)

    def _deselect_all(self):
        for var in self.action_vars:
            var.set(False)

    def _open_term_map(self):
        TermMapDialog(self.winfo_toplevel())

    def _load_config(self):
        try:
            if os.path.exists(self._config_path):
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return {}

    def _save_config(self):
        try:
            data = {
                'copyright_holder': self.copyright_text_var.get(),
            }
            with open(self._config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False)
        except:
            pass
    
    def get_options(self):
        """Get all action options as a dictionary."""
        holder = self.copyright_text_var.get().strip()
        from datetime import datetime
        year = datetime.now().year
        
        return {
            'enhance': self.var_enhance.get(),
            'model': self.model_var.get(),
            'resize': self.var_resize.get(),
            'preset': self.preset_var.get(),
            'width': self.width_var.get(),
            'height': self.height_var.get(),
            'aspect': self.aspect_var.get(),
            'crop': self.var_crop.get(),
            'convert': self.var_convert.get(),
            'convert_format': self.format_var.get().upper(),
            'strip': self.var_strip.get(),
            'rename': self.var_rename.get(),
            'copyright': self.var_copyright.get(),
            'copyright_text': f"© {year} {holder}" if holder else "",
            'artist': holder,
        }


