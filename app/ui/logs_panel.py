"""
Logs panel component - expandable side panel for processing logs.
"""

import customtkinter as ctk
import tkinter as tk
from .theme import Theme


class LogsPanel(ctk.CTkFrame):
    """Expandable side panel for displaying processing logs."""
    
    def __init__(self, parent):
        super().__init__(
            parent,
            fg_color='#0a0a0f',
            width=Theme.WINDOW['logs_width'],
            corner_radius=0  # Flat on the side
        )
        
        self._build_header()
        self._build_text_area()
    
    def _build_header(self):
        """Build the panel header."""
        ctk.CTkLabel(
            self,
            text="Processing Logs",
            font=Theme.get_font('heading'),
            text_color=Theme.get_color('accent')
        ).pack(anchor='w', padx=20, pady=(20, 10))
    
    def _build_text_area(self):
        """Build the scrollable text area."""
        self.text = ctk.CTkTextbox(
            self,
            fg_color='#0a0a0f',
            text_color=Theme.get_color('success'),
            font=Theme.get_font('mono'),
            wrap='word',
            border_width=0,
            width=400,
            corner_radius=0
        )
        self.text.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        self.text.configure(state='disabled')
    
    def log(self, message):
        """Add a message to the log."""
        self.text.configure(state='normal')
        self.text.insert(tk.END, str(message) + "\n")
        self.text.see(tk.END)
        self.text.configure(state='disabled')
    
    def clear(self):
        """Clear all log messages."""
        self.text.configure(state='normal')
        self.text.delete('1.0', tk.END)
        self.text.configure(state='disabled')



