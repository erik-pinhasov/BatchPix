"""
Main application class.
Orchestrates UI components and processing handlers.
"""

import os
import sys
import customtkinter as ctk
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


class LoadingScreen(ctk.CTkToplevel):
    """Loading animation shown during startup."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.overrideredirect(True)
        self.configure(fg_color='#0f0f15')
        
        width, height = 320, 110
        x = (self.winfo_screenwidth() - width) // 2
        y = (self.winfo_screenheight() - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")
        
        ctk.CTkLabel(
            self, text="BatchPix",
            font=('Segoe UI', 24, 'bold'),
            fg_color='#0f0f15', text_color='white'
        ).pack(pady=(25, 5))
        
        self.status_label = ctk.CTkLabel(
            self, text="Loading...",
            font=('Segoe UI', 13),
            fg_color='#0f0f15', text_color='#8b5cf6'
        )
        self.status_label.pack()
        
        self._dots = 0
        self._animate()
    
    def _animate(self):
        self._dots = (self._dots + 1) % 4
        self.status_label.configure(text="Loading" + "." * self._dots)
        self.after(300, self._animate)
    
    def update_status(self, text):
        self.status_label.configure(text=text)
        self.update()


class App(ctk.CTk):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.withdraw()
        
        # Setup CustomTkinter
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        
        # Configure window
        self.title("BatchPix")
        self.resizable(False, False)
        
        # Show loading screen
        self.loading = LoadingScreen(self)
        self.loading.update()
        
        # Initialize after a brief delay
        self.after(100, self._initialize)
    
    def _initialize(self):
        """Initialize the application."""
        # Set AppUserModelID for proper taskbar icon handling on Windows
        try:
            import ctypes
            myappid = 'batchpix.app.1.0'  # unique ID
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception:
            pass

        self.loading.update_status("Loading modules...")
        
        # State
        self.selected_files = []
        self.logs_visible = False
        self.is_processing = False
        
        # Initialize processor
        self.handler = ProcessingHandler(self)
        
        self.loading.update_status("Building UI...")
        self._build_ui()
        
        # Set window size and position (Center Left)
        target_width = Theme.WINDOW['min_width']
        target_height = Theme.WINDOW['min_height']
        x = 50  # Left side
        y = (self.winfo_screenheight() - target_height) // 2
        self.geometry(f"{target_width}x{target_height}+{x}+{y}")
        
        # Show window
        self.loading.destroy()
        self.deiconify()
    
    def _build_ui(self):
        """Build the main UI."""
        # Main content frame
        self.main_frame = ctk.CTkFrame(
            self,
            fg_color=Theme.get_color('bg'),
            corner_radius=0
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
    
    def _build_output_card(self):
        """Build output folder card."""
        callbacks = {
            'browse_output': self._browse_output,
        }
        self.output_card = OutputCard(self.main_frame, callbacks)
    
    def _build_actions_card(self):
        """Build actions selection card."""
        self.actions_card = ActionsCard(self.main_frame, {})
    
    def _build_start_button(self):
        """Build the start processing button."""
        self.start_btn = create_accent_button(
            self.main_frame, "▶  START BATCH", self._start_processing
        )
        # 70% width approx = large padding
        self.start_btn.pack(fill='x', padx=80, pady=(15, 10))

    def _build_status_bar(self):
        """Build the status bar."""
        self.status_frame = ctk.CTkFrame(
            self.main_frame,
            fg_color=Theme.get_color('card'),
            height=40,
            corner_radius=Theme.DIMENSIONS['corner_radius'],
            border_width=1,
            border_color=Theme.get_color('border')
        )
        self.status_frame.pack(fill='x', padx=15, pady=(0, 15))
        
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Ready",
            font=Theme.get_font('small'),
            text_color=Theme.get_color('success')
        )
        self.status_label.pack(side='left', padx=15)
        
        create_button(
            self.status_frame, "📋 Logs", self._toggle_logs, small=True
        ).pack(side='right', padx=10, pady=5)

    def _update_window_size(self):
        """Update window size while preserving position."""
        target_width = Theme.WINDOW['min_width']
        if self.logs_visible:
            target_width += Theme.WINDOW['logs_width']
        target_height = Theme.WINDOW['min_height']
        
        x = self.winfo_x()
        y = self.winfo_y()
        self.geometry(f"{target_width}x{target_height}+{x}+{y}")


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
            # Hiding
            self.logs_panel.pack_forget()
            self.logs_visible = False
            
            # Unlock main frame
            self.main_frame.pack_propagate(True)
            self.main_frame.configure(width=0) # Reset fixed width
            self.main_frame.pack_configure(expand=True, fill='both')
            
            self._update_window_size()
        else:
            # Showing
            # 1. Lock main frame to current size to prevent squishing
            current_width = self.main_frame.winfo_width()
            self.main_frame.pack_propagate(False)
            self.main_frame.configure(width=current_width)
            self.main_frame.pack_configure(expand=False, fill='y') # Fill Y only, fixed X
            
            # 2. Update window size (expand right)
            self.logs_visible = True
            self._update_window_size()
            
            # 3. Show logs
            self.logs_panel.pack(side='right', fill='both', expand=True)
    
    def _start_processing(self):
        """Start or stop image processing."""
        if self.is_processing:
            self._stop_processing()
            return
        
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
    
    def _stop_processing(self):
        """Stop the current processing."""
        self.handler.cancel()
    
    def _set_processing_state(self, processing):
        """Update UI based on processing state."""
        self.is_processing = processing
        if processing:
            self.start_btn.configure(
                text="■  STOP", fg_color=Theme.get_color('error'),
                hover_color='#dc2626'
            )
        else:
            self.start_btn.configure(
                text="▶  START BATCH", fg_color=Theme.get_color('accent'),
                hover_color=Theme.get_color('accent_hover')
            )
    
    def on_processing_complete(self):
        """Called when processing is complete."""
        self.after(0, lambda: self._set_processing_state(False))
    
    def log(self, message):
        """Log a message to the logs panel and status bar."""
        def _update():
            self.logs_panel.log(message)
            self.status_label.configure(text=str(message)[:60])
        self.after(0, _update)