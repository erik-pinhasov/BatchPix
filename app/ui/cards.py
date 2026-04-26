"""
Card components for the application UI using CustomTkinter.
Each card represents a major section of the interface.
"""

import json
import os
import sys
import customtkinter as ctk
from tkinter import filedialog, messagebox, colorchooser
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
    """Actions card with mode toggle: Batch Process or 360° Spin View."""
    
    def __init__(self, parent, callbacks):
        super().__init__(parent)
        
        self.callbacks = callbacks
        self._config_path = os.path.join(_get_base_path(), '.copyright_config.json')
        self._saved_config = self._load_config()
        
        self.mode_var = ctk.StringVar(value="batch")
        
        self._build_mode_toggle()
        self._build_batch_panel()
        self._build_spin360_panel()
        self._on_mode_change()
    
    def _build_mode_toggle(self):
        """Build the mode selector at the top of the card."""
        self.mode_frame = ctk.CTkFrame(self.inner, fg_color="transparent")
        self.mode_frame.pack(fill='x', pady=(0, 10))
        
        self.mode_toggle = ctk.CTkSegmentedButton(
            self.mode_frame,
            values=["⚡ Batch Process", "🔄 360° Spin View"],
            command=self._on_mode_toggle,
            font=Theme.get_font('body'),
            selected_color=Theme.get_color('accent'),
            selected_hover_color=Theme.get_color('accent_hover'),
            unselected_color=Theme.get_color('input'),
            unselected_hover_color=Theme.get_color('input_border'),
            text_color="white",
            corner_radius=8,
            height=36,
        )
        self.mode_toggle.set("⚡ Batch Process")
        self.mode_toggle.pack(fill='x')
    
    def _on_mode_toggle(self, value):
        """Handle segmented button toggle."""
        self.mode_var.set("batch" if "Batch" in value else "spin360")
        self._on_mode_change()
    
    def _on_mode_change(self):
        """Show/hide panels based on mode."""
        if self.mode_var.get() == "batch":
            self.spin360_frame.pack_forget()
            self.batch_frame.pack(fill='x', after=self.mode_frame)
        else:
            self.batch_frame.pack_forget()
            self.spin360_frame.pack(fill='x', after=self.mode_frame)
        
        # Notify parent (app.py) so it can update the START button text
        on_mode = self.callbacks.get('on_mode_change')
        if on_mode:
            on_mode(self.mode_var.get())
    
    def _build_batch_panel(self):
        """Build the batch processing actions panel."""
        self.batch_frame = ctk.CTkFrame(self.inner, fg_color="transparent")
        
        # Select/Deselect All
        row = ctk.CTkFrame(self.batch_frame, fg_color="transparent")
        row.pack(fill='x', pady=(0, 10))
        create_button(row, "Select All", self._select_all, small=True).pack(side='left')
        create_button(row, "Deselect All", self._deselect_all, small=True).pack(side='left', padx=10)
        
        # Separator
        ctk.CTkFrame(self.batch_frame, height=1, fg_color=Theme.get_color('border')).pack(fill='x', pady=10)
        
        # Action variables (all checked by default)
        self.var_enhance = ctk.BooleanVar(value=True)
        self.var_crop = ctk.BooleanVar(value=True)
        self.var_resize = ctk.BooleanVar(value=True)
        self.var_canvas_fit = ctk.BooleanVar(value=False)
        self.var_bg = ctk.BooleanVar(value=False)
        self.var_convert = ctk.BooleanVar(value=True)
        self.var_strip = ctk.BooleanVar(value=True)
        self.var_rename = ctk.BooleanVar(value=True)
        self.var_copyright = ctk.BooleanVar(value=True)

        self.action_vars = [
            self.var_enhance, self.var_crop, self.var_resize, self.var_canvas_fit,
            self.var_bg, self.var_convert, self.var_strip, self.var_rename,
            self.var_copyright,
        ]

        # 1. Enhance
        row = ctk.CTkFrame(self.batch_frame, fg_color="transparent")
        row.pack(fill='x', pady=2)
        create_checkbox(row, "Enhance", self.var_enhance).pack(side='left')
        self.model_var = ctk.StringVar(value="x4-quality")
        create_combobox(row, self.model_var, ["x4-quality", "x4-fast", "x2-quality"], width=110).pack(side='left', padx=10)
        create_label(row, "AI upscale", dim=True).pack(side='left')

        # 2. Smart Crop (runs before resize so we adjust size on the trimmed content)
        row = ctk.CTkFrame(self.batch_frame, fg_color="transparent")
        row.pack(fill='x', pady=2)
        create_checkbox(row, "Smart Crop", self.var_crop).pack(side='left')
        create_label(row, "Remove empty borders", dim=True).pack(side='left', padx=10)

        # 3. Resize
        row = ctk.CTkFrame(self.batch_frame, fg_color="transparent")
        row.pack(fill='x', pady=2)
        create_checkbox(row, "Resize", self.var_resize).pack(side='left')
        self.resize_dim_var = ctk.StringVar(value="Width")
        create_combobox(row, self.resize_dim_var, ["Width", "Height"], width=90).pack(side='left', padx=10)
        self.custom_size_var = ctk.StringVar(value="1200")
        create_spinbox(row, self.custom_size_var, 100, 8000, 80).pack(side='left')
        create_label(row, "px  (aspect ratio kept)", dim=True).pack(side='left', padx=(5, 0))

        # 3.25. Fit to Canvas (square canvas + even padding, content centred)
        row = ctk.CTkFrame(self.batch_frame, fg_color="transparent")
        row.pack(fill='x', pady=2)
        create_checkbox(row, "Fit to Canvas", self.var_canvas_fit).pack(side='left')
        self.canvas_size_var = ctk.StringVar(value="200")
        create_spinbox(row, self.canvas_size_var, 16, 8000, 80).pack(side='left', padx=(10, 4))
        create_label(row, "px  Padding", dim=True).pack(side='left')
        self.canvas_padding_var = ctk.StringVar(value="8")
        create_spinbox(row, self.canvas_padding_var, 0, 2000, 70).pack(side='left', padx=(4, 4))
        create_label(row, "px", dim=True).pack(side='left')

        # 3.5. Add Background
        self._build_bg_row()

        # 4. Convert Format
        row = ctk.CTkFrame(self.batch_frame, fg_color="transparent")
        row.pack(fill='x', pady=2)
        create_checkbox(row, "Convert Format", self.var_convert).pack(side='left')
        self.format_var = ctk.StringVar(value="WebP")
        create_combobox(row, self.format_var, CONVERT_FORMATS).pack(side='left', padx=10)
        
        # 5. Strip Metadata
        row = ctk.CTkFrame(self.batch_frame, fg_color="transparent")
        row.pack(fill='x', pady=2)
        create_checkbox(row, "Strip Metadata", self.var_strip).pack(side='left')
        create_label(row, "Remove GPS & camera info", dim=True).pack(side='left', padx=10)
        
        # 6. AI Rename
        row = ctk.CTkFrame(self.batch_frame, fg_color="transparent")
        row.pack(fill='x', pady=2)
        create_checkbox(row, "AI Rename", self.var_rename).pack(side='left')
        create_label(row, "SEO-friendly filenames", dim=True).pack(side='left', padx=10)
        create_button(row, "Edit Map", self._open_term_map, small=True).pack(side='left', padx=10)
        
        # 7. Copyright
        row = ctk.CTkFrame(self.batch_frame, fg_color="transparent")
        row.pack(fill='x', pady=2)
        create_checkbox(row, "Copyright", self.var_copyright).pack(side='left')
        
        self.copyright_text_var = ctk.StringVar(value=self._saved_config.get('copyright_holder', 'Your Name'))
        self.copyright_text_var.trace_add('write', lambda *_: self._save_config())
        
        create_entry(row, self.copyright_text_var, 200).pack(side='left', padx=10)
        create_label(row, "(Holder Name)", dim=True).pack(side='left')
    
    def _build_bg_row(self):
        """Build the Add Background row with color/image sub-controls."""
        # Persistent container — always packed in batch_frame, holds all bg widgets
        bg_container = ctk.CTkFrame(self.batch_frame, fg_color="transparent")
        bg_container.pack(fill='x', pady=2)

        # -- Main row: checkbox + radio buttons --
        top_row = ctk.CTkFrame(bg_container, fg_color="transparent")
        top_row.pack(fill='x')

        create_checkbox(top_row, "Add Background", self.var_bg).pack(side='left')

        self.bg_type_var = ctk.StringVar(value="color")

        ctk.CTkRadioButton(
            top_row, text="Color",
            variable=self.bg_type_var, value="color",
            font=Theme.get_font('small'),
            fg_color=Theme.get_color('accent'),
            hover_color=Theme.get_color('accent_hover'),
            text_color=Theme.get_color('text'),
            command=self._on_bg_type_change,
        ).pack(side='left', padx=(12, 6))

        ctk.CTkRadioButton(
            top_row, text="Image",
            variable=self.bg_type_var, value="image",
            font=Theme.get_font('small'),
            fg_color=Theme.get_color('accent'),
            hover_color=Theme.get_color('accent_hover'),
            text_color=Theme.get_color('text'),
            command=self._on_bg_type_change,
        ).pack(side='left', padx=(0, 6))

        # -- Color sub-row (inside container) --
        self.bg_color_row = ctk.CTkFrame(bg_container, fg_color="transparent")

        self.bg_color_var = ctk.StringVar(value="#ffffff")
        self.bg_swatch = ctk.CTkButton(
            self.bg_color_row,
            text="",
            width=28, height=28,
            fg_color="#ffffff",
            hover_color="#ffffff",
            border_width=1,
            border_color=Theme.get_color('input_border'),
            corner_radius=6,
            command=self._pick_color,
            cursor='hand2',
        )
        self.bg_swatch.pack(side='left', padx=(0, 8))

        self.bg_hex_entry = create_entry(self.bg_color_row, self.bg_color_var, width=100)
        self.bg_hex_entry.pack(side='left')
        create_label(self.bg_color_row, "hex color", dim=True).pack(side='left', padx=(6, 0))
        self.bg_color_var.trace_add('write', self._on_hex_typed)

        # -- Image sub-row (inside container) --
        self.bg_image_row = ctk.CTkFrame(bg_container, fg_color="transparent")

        self.bg_image_var = ctk.StringVar()
        create_entry(self.bg_image_row, self.bg_image_var, width=260).pack(side='left', fill='x', expand=True)
        create_button(
            self.bg_image_row, "Browse",
            lambda: self._browse_bg_image(), small=True
        ).pack(side='left', padx=(8, 0))

        # Default: show color sub-row
        self._on_bg_type_change()

    def _on_bg_type_change(self):
        """Show the relevant sub-row based on the selected background type."""
        if self.bg_type_var.get() == "color":
            self.bg_image_row.pack_forget()
            self.bg_color_row.pack(fill='x', padx=(28, 0), pady=(2, 0))
        else:
            self.bg_color_row.pack_forget()
            self.bg_image_row.pack(fill='x', padx=(28, 0), pady=(2, 0))

    def _pick_color(self):
        """Open the system color picker and update swatch + hex entry."""
        initial = self.bg_color_var.get() or "#ffffff"
        result = colorchooser.askcolor(color=initial, title="Choose Background Color")
        if result and result[1]:
            hex_color = result[1]  # e.g. '#ff0000'
            self.bg_color_var.set(hex_color)
            self._update_swatch(hex_color)

    def _on_hex_typed(self, *_):
        """Update swatch when a valid hex is typed into the entry."""
        val = self.bg_color_var.get().strip()
        if not val.startswith('#'):
            val = '#' + val
        # Only update if the hex is valid (3 or 6 chars after #)
        stripped = val.lstrip('#')
        if len(stripped) in (3, 6) and all(c in '0123456789abcdefABCDEF' for c in stripped):
            self._update_swatch(val)

    def _update_swatch(self, hex_color: str):
        """Set the swatch fg_color to reflect the chosen color."""
        try:
            self.bg_swatch.configure(fg_color=hex_color, hover_color=hex_color)
        except Exception:
            pass

    def _browse_bg_image(self):
        """Open file dialog to choose a background image."""
        path = filedialog.askopenfilename(
            title="Select Background Image",
            filetypes=[("Images", "*.jpg *.jpeg *.png *.webp *.bmp *.tiff *.tif")]
        )
        if path:
            self.bg_image_var.set(path)

    def _build_spin360_panel(self):
        """Build the 360° Spin View settings panel."""
        self.spin360_frame = ctk.CTkFrame(self.inner, fg_color="transparent")
        
        # Description
        desc = ctk.CTkLabel(
            self.spin360_frame,
            text="Generate interactive 360° product views from multi-angle photos",
            font=Theme.get_font('small'),
            text_color=Theme.get_color('text_dim'),
        )
        desc.pack(anchor='w', pady=(0, 15))
        
        # Frame size
        row = ctk.CTkFrame(self.spin360_frame, fg_color="transparent")
        row.pack(fill='x', pady=5)
        create_label(row, "Frame Size:").pack(side='left')
        self.spin360_frame_size_var = ctk.StringVar(value="512")
        create_spinbox(row, self.spin360_frame_size_var, 128, 2048, 80).pack(side='left', padx=10)
        create_label(row, "px  (each frame is resized to this square)", dim=True).pack(side='left')
        
        # Remove background
        row = ctk.CTkFrame(self.spin360_frame, fg_color="transparent")
        row.pack(fill='x', pady=5)
        self.var_spin360_rembg = ctk.BooleanVar(value=True)
        create_checkbox(row, "Remove Background", self.var_spin360_rembg).pack(side='left')
        create_label(row, "AI-powered (uses rembg)", dim=True).pack(side='left', padx=10)
        
        # Info note
        info = ctk.CTkLabel(
            self.spin360_frame,
            text="💡 Tip: Name your images in order (01.jpg, 02.jpg, ...) for correct rotation sequence.",
            font=Theme.get_font('small'),
            text_color=Theme.get_color('accent'),
            wraplength=450,
            justify='left',
        )
        info.pack(anchor='w', pady=(15, 0))

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
    
    @staticmethod
    def _safe_int(var, default):
        """Safely get an int from a StringVar, returning default if empty/invalid."""
        try:
            return int(var.get())
        except (ValueError, Exception):
            return default

    def get_options(self):
        """Get all action options as a dictionary."""
        holder = self.copyright_text_var.get().strip()
        from datetime import datetime
        year = datetime.now().year
        
        is_spin360 = self.mode_var.get() == "spin360"
        
        # Normalise hex (ensure it starts with #)
        raw_hex = self.bg_color_var.get().strip()
        bg_hex = raw_hex if raw_hex.startswith('#') else f'#{raw_hex}'

        return {
            'mode': self.mode_var.get(),
            'enhance': False if is_spin360 else self.var_enhance.get(),
            'model': self.model_var.get(),
            'resize': False if is_spin360 else self.var_resize.get(),
            'custom_size': self._safe_int(self.custom_size_var, 1200),
            'resize_dimension': self.resize_dim_var.get().lower(),
            'crop': False if is_spin360 else self.var_crop.get(),
            'canvas_fit': False if is_spin360 else self.var_canvas_fit.get(),
            'canvas_size': self._safe_int(self.canvas_size_var, 200),
            'canvas_padding': self._safe_int(self.canvas_padding_var, 8),
            'bg': False if is_spin360 else self.var_bg.get(),
            'bg_type': self.bg_type_var.get(),
            'bg_color': bg_hex,
            'bg_image': self.bg_image_var.get(),
            'convert': False if is_spin360 else self.var_convert.get(),
            'convert_format': self.format_var.get().upper(),
            'strip': False if is_spin360 else self.var_strip.get(),
            'rename': False if is_spin360 else self.var_rename.get(),
            'copyright': False if is_spin360 else self.var_copyright.get(),
            'copyright_text': f"© {year} {holder}" if holder else "",
            'artist': holder,
            'spin360': is_spin360,
            'spin360_frame_size': self._safe_int(self.spin360_frame_size_var, 512),
            'spin360_rembg': self.var_spin360_rembg.get(),
        }
