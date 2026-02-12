"""
Custom widget factories for consistent styling.
"""

import tkinter as tk
from tkinter import ttk
from .theme import Theme


def create_entry(parent, textvariable, width=25):
    """Create a styled text entry field."""
    return tk.Entry(
        parent,
        textvariable=textvariable,
        width=width,
        font=Theme.get_font('body'),
        bg=Theme.get_color('input'),
        fg=Theme.get_color('text'),
        insertbackground='white',
        relief='flat',
        highlightthickness=2,
        bd=0,
        highlightbackground=Theme.get_color('input_border'),
        highlightcolor=Theme.get_color('accent')
    )


def create_button(parent, text, command, small=False):
    """Create a styled button."""
    if small:
        font = Theme.get_font('button')
        padx, pady = Theme.PADDING['button']
    else:
        font = Theme.get_font('button_large')
        padx, pady = Theme.PADDING['button_large']
    
    return tk.Button(
        parent,
        text=text,
        font=font,
        bg=Theme.get_color('button'),
        fg=Theme.get_color('text'),
        relief='flat',
        padx=padx,
        pady=pady,
        cursor='hand2',
        bd=0,
        activebackground=Theme.get_color('button_hover'),
        command=command
    )


def create_accent_button(parent, text, command):
    """Create a prominent accent-colored button."""
    return tk.Button(
        parent,
        text=text,
        font=Theme.get_font('button_large'),
        bg=Theme.get_color('accent'),
        fg=Theme.get_color('text'),
        relief='flat',
        pady=12,
        cursor='hand2',
        bd=0,
        activebackground=Theme.get_color('accent_hover'),
        command=command
    )


def create_spinbox(parent, variable, from_=0, to=100, width=5):
    """Create a custom spinbox with visible increment/decrement buttons."""
    frame = tk.Frame(parent, bg=Theme.get_color('card'))
    
    entry = tk.Entry(
        frame,
        textvariable=variable,
        width=width,
        font=Theme.get_font('body'),
        bg=Theme.get_color('input'),
        fg=Theme.get_color('text'),
        insertbackground='white',
        relief='flat',
        justify='center',
        bd=0,
        highlightthickness=1,
        highlightbackground=Theme.get_color('input_border')
    )
    entry.pack(side='left')
    
    btn_frame = tk.Frame(frame, bg=Theme.get_color('input'))
    btn_frame.pack(side='left', fill='y')
    
    def increment():
        try:
            val = variable.get()
            if val < to:
                variable.set(val + 1)
        except (tk.TclError, ValueError):
            pass
    
    def decrement():
        try:
            val = variable.get()
            if val > from_:
                variable.set(val - 1)
        except (tk.TclError, ValueError):
            pass
    
    tk.Button(
        btn_frame, text="▲", font=('Segoe UI', 6),
        bg=Theme.get_color('button'), fg='white',
        relief='flat', bd=0, padx=3, pady=0,
        command=increment
    ).pack(fill='x')
    
    tk.Button(
        btn_frame, text="▼", font=('Segoe UI', 6),
        bg=Theme.get_color('button'), fg='white',
        relief='flat', bd=0, padx=3, pady=0,
        command=decrement
    ).pack(fill='x')
    
    return frame


def create_combobox(parent, variable, values, width=10):
    """Create a styled combobox."""
    style = ttk.Style()
    style.theme_use('clam')
    style.configure(
        'Modern.TCombobox',
        fieldbackground=Theme.get_color('input'),
        background=Theme.get_color('input'),
        foreground='white',
        arrowcolor='white',
        bordercolor=Theme.get_color('input_border'),
        selectbackground=Theme.get_color('accent'),
        selectforeground='white',
        padding=6
    )
    style.map(
        'Modern.TCombobox',
        fieldbackground=[('readonly', Theme.get_color('input'))],
        background=[('readonly', Theme.get_color('input'))],
        foreground=[('readonly', 'white')]
    )
    
    return ttk.Combobox(
        parent,
        textvariable=variable,
        values=values,
        state="readonly",
        width=width,
        font=Theme.get_font('small'),
        style='Modern.TCombobox'
    )


def create_checkbox(parent, text, variable, bold=False):
    """Create a styled checkbox."""
    font = Theme.get_font('body')
    if bold:
        font = (font[0], font[1], 'bold')
    
    return tk.Checkbutton(
        parent,
        text=text,
        variable=variable,
        font=font,
        bg=Theme.get_color('card'),
        fg=Theme.get_color('text'),
        selectcolor=Theme.get_color('input'),
        activebackground=Theme.get_color('card')
    )


def create_label(parent, text, dim=False):
    """Create a styled label."""
    return tk.Label(
        parent,
        text=text,
        font=Theme.get_font('small'),
        bg=Theme.get_color('card'),
        fg=Theme.get_color('text_dim') if dim else Theme.get_color('text')
    )


def create_radiobutton(parent, text, variable, value, command=None):
    """Create a styled radiobutton."""
    return tk.Radiobutton(
        parent,
        text=text,
        variable=variable,
        value=value,
        font=Theme.get_font('body'),
        bg=Theme.get_color('card'),
        fg=Theme.get_color('text'),
        selectcolor=Theme.get_color('input'),
        activebackground=Theme.get_color('card'),
        command=command
    )
