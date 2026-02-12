"""
Logs panel component - expandable side panel for processing logs.
"""

import tkinter as tk
from .theme import Theme


class LogsPanel(tk.Frame):
    """Expandable side panel for displaying processing logs."""
    
    def __init__(self, parent):
        super().__init__(
            parent,
            bg='#0a0a0f',
            width=Theme.WINDOW['logs_width']
        )
        
        self._build_header()
        self._build_text_area()
    
    def _build_header(self):
        """Build the panel header."""
        tk.Label(
            self,
            text="Processing Logs",
            font=Theme.get_font('heading'),
            bg='#0a0a0f',
            fg=Theme.get_color('accent')
        ).pack(anchor='w', padx=12, pady=(12, 6))
    
    def _build_text_area(self):
        """Build the scrollable text area."""
        self.text = tk.Text(
            self,
            bg='#0a0a0f',
            fg=Theme.get_color('success'),
            font=Theme.get_font('mono'),
            wrap='word',
            bd=0,
            width=44
        )
        self.text.pack(fill='both', expand=True, padx=12, pady=(0, 12))
        self.text.config(state='disabled')
    
    def log(self, message):
        """Add a message to the log."""
        self.text.config(state='normal')
        self.text.insert(tk.END, str(message) + "\n")
        self.text.see(tk.END)
        self.text.config(state='disabled')
    
    def clear(self):
        """Clear all log messages."""
        self.text.config(state='normal')
        self.text.delete('1.0', tk.END)
        self.text.config(state='disabled')
