"""
Main application class.
Orchestrates UI components and processing handlers.
"""

import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox

from .ui.theme import Theme
from .ui.widgets import create_button, create_accent_button
from .ui.cards import InputCard, OutputCard, ActionsCard
from .ui.logs_panel import LogsPanel
from .handlers import ProcessingHandler, get_image_files


def get_base_path():
    """Get base path for resources (works with PyInstaller)."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class LoadingScreen(tk.Toplevel):
    """Loading animation shown during startup."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.overrideredirect(True)
        self.configure(bg='#0f0f15')
        
        width, height = 320, 110
        x = (self.winfo_screenwidth() - width) // 2
        y = (self.winfo_screenheight() - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")
        
        tk.Label(
            self, text="BatchPix",
            font=('Segoe UI', 16, 'bold'),
            bg='#0f0f15', fg='white'
        ).pack(pady=(20, 8))
        
        self.status_label = tk.Label(
            self, text="Loading...",
            font=('Segoe UI', 11),
            bg='#0f0f15', fg='#8b5cf6'
        )
        self.status_label.pack()
        
        self._dots = 0
        self._animate()
    
    def _animate(self):
        self._dots = (self._dots + 1) % 4
        self.status_label.config(text="Loading" + "." * self._dots)
        self.after(300, self._animate)
    
    def update_status(self, text):
        self.status_label.config(text=text)
        self.update()


class App(tk.Tk):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.withdraw()
        
        # Show loading screen
        self.loading = LoadingScreen(self)
        self.loading.update()
        
        # Configure window
        self.title("BatchPix")
        self.configure(bg=Theme.get_color('bg'))
        self.resizable(False, False)
        
        # Initialize after a brief delay
        self.after(100, self._initialize)
    
    def _initialize(self):
        """Initialize the application."""
        self.loading.update_status("Loading modules...")
        
        # State
        self.selected_files = []
        self.logs_visible = False
        
        # Initialize processor
        self.handler = ProcessingHandler(self)
        
        self.loading.update_status("Building UI...")
        self._set_icon()
        self._build_ui()
        
        # Set window size
        self._update_window_size()
        
        # Show window
        self.loading.destroy()
        self.deiconify()
    
    def _set_icon(self):
        """Set the application icon."""
        base = get_base_path()
        ico_path = os.path.join(base, 'assets', 'icon.ico')
        if os.path.exists(ico_path):
            try:
                self.iconbitmap(default=ico_path)
            except tk.TclError:
                pass
    
    def _build_ui(self):
        """Build the main UI."""
        # Main content frame
        self.main_frame = tk.Frame(
            self,
            bg=Theme.get_color('bg'),
            padx=18, pady=14
        )
        self.main_frame.pack(side='left', fill='both', expand=True)
        
        # Logs panel (hidden by default)
        self.logs_panel = LogsPanel(self)
        
        # Build UI sections
        self._build_input_card()
        self._build_output_card()
        self._build_actions_card()
        self._build_start_button()
        self._build_status_bar()
    
    def _build_input_card(self):
        """Build input selection card."""
        callbacks = {
            'on_mode_change': self._on_mode_change,
            'on_folder_change': self._on_folder_change,
            'browse_folder': self._browse_folder,
            'browse_files': self._browse_files,
        }
        self.input_card = InputCard(self.main_frame, callbacks)
        self.input_card.pack(fill='x', pady=(0, 10))
    
    def _build_output_card(self):
        """Build output folder card."""
        callbacks = {
            'browse_output': self._browse_output,
        }
        self.output_card = OutputCard(self.main_frame, callbacks)
        self.output_card.pack(fill='x', pady=(0, 10))
    
    def _build_actions_card(self):
        """Build actions selection card."""
        self.actions_card = ActionsCard(self.main_frame, {})
        self.actions_card.pack(fill='x', pady=(0, 10))
    
    def _build_start_button(self):
        """Build the start processing button."""
        self.start_btn = create_accent_button(
            self.main_frame, "▶  START", self._start_processing
        )
        self.start_btn.pack(fill='x', pady=(10, 8))
    
    def _build_status_bar(self):
        """Build the status bar."""
        status_frame = tk.Frame(
            self.main_frame,
            bg=Theme.get_color('card'),
            pady=8, padx=12,
            highlightbackground=Theme.get_color('border'),
            highlightthickness=1
        )
        status_frame.pack(fill='x')
        
        self.status_label = tk.Label(
            status_frame,
            text="Ready",
            font=Theme.get_font('small'),
            bg=Theme.get_color('card'),
            fg=Theme.get_color('success')
        )
        self.status_label.pack(side='left')
        
        create_button(
            status_frame, "📋 Logs", self._toggle_logs, small=True
        ).pack(side='right')
    
    def _update_window_size(self):
        """Update window size and position based on logs visibility."""
        width = Theme.WINDOW['min_width']
        if self.logs_visible:
            width += Theme.WINDOW['logs_width']
        height = Theme.WINDOW['min_height']
        
        # Center horizontally, position near top of screen
        screen_w = self.winfo_screenwidth()
        x = (screen_w - width) // 2
        y = 20
        self.geometry(f"{width}x{height}+{x}+{y}")
    
    # Event handlers
    def _on_mode_change(self):
        """Handle input mode change."""
        self.input_card.update_mode()
    
    def _on_folder_change(self, *args):
        """Handle folder path change."""
        folder = self.input_card.folder_var.get().replace('\\', '/')
        if folder:
            self.output_card.output_var.set(folder + "/output")
    
    def _browse_folder(self):
        """Open folder browser dialog."""
        folder = filedialog.askdirectory()
        if folder:
            self.input_card.folder_var.set(folder.replace('\\', '/'))
    
    def _browse_files(self):
        """Open file browser dialog."""
        files = filedialog.askopenfilenames(
            filetypes=[("Images", "*.jpg *.jpeg *.png *.webp *.bmp *.gif *.tiff *.tif *.ico *.avif *.svg *.tga")]
        )
        if files:
            self.selected_files = list(files)
            self.input_card.set_files_count(len(files))
            self.output_card.output_var.set(
                os.path.dirname(files[0]).replace('\\', '/') + "/output"
            )
    
    def _browse_output(self):
        """Open output folder browser dialog."""
        folder = filedialog.askdirectory()
        if folder:
            self.output_card.output_var.set(folder.replace('\\', '/'))
    
    def _toggle_logs(self):
        """Toggle logs panel visibility."""
        if self.logs_visible:
            self.logs_panel.pack_forget()
            self.logs_visible = False
        else:
            self.logs_panel.pack(side='right', fill='both')
            self.logs_visible = True
        self._update_window_size()
    
    def _start_processing(self):
        """Start image processing."""
        # Get input files
        if self.input_card.input_mode.get() == "folder":
            folder = self.input_card.folder_var.get()
            if not folder or not os.path.isdir(folder):
                messagebox.showerror("Error", "Select a valid folder")
                return
            files = get_image_files(folder)
        else:
            files = self.selected_files
        
        if not files:
            messagebox.showerror("Error", "No images found")
            return
        
        # Get output folder
        output = self.output_card.output_var.get()
        if not output:
            messagebox.showerror("Error", "Select output folder")
            return
        
        # Get processing options
        options = self.actions_card.get_options()
        
        # Update UI
        self.log(f"Processing {len(files)} images...")
        self._set_processing_state(True)
        
        # Start processing
        self.handler.process(files, output, options)
    
    def _set_processing_state(self, processing):
        """Update UI based on processing state."""
        if processing:
            self.start_btn.config(state='disabled', bg=Theme.get_color('button'))
        else:
            self.start_btn.config(state='normal', bg=Theme.get_color('accent'))
    
    def on_processing_complete(self):
        """Called when processing is complete."""
        self.after(0, lambda: self._set_processing_state(False))
    
    def log(self, message):
        """Log a message to the logs panel and status bar."""
        def _update():
            self.logs_panel.log(message)
            self.status_label.config(text=str(message)[:60])
        self.after(0, _update)
