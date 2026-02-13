"""
Custom widget factories using CustomTkinter for modern styling.
"""

import customtkinter as ctk
from .theme import Theme


def create_entry(parent, textvariable, width=200):
    """Create a styled rounded entry field."""
    return ctk.CTkEntry(
        parent,
        textvariable=textvariable,
        width=width,
        font=Theme.get_font('body'),
        fg_color=Theme.get_color('input'),
        text_color=Theme.get_color('text'),
        border_color=Theme.get_color('input_border'),
        border_width=1,
        corner_radius=Theme.DIMENSIONS['corner_radius']
    )


def create_button(parent, text, command, small=False):
    """Create a styled rounded button."""
    if small:
        font = Theme.get_font('button')
        height = 32
        corner_radius = Theme.DIMENSIONS['btn_radius_small']
    else:
        font = Theme.get_font('button_large')
        height = 40
        corner_radius = Theme.DIMENSIONS['btn_radius']
    
    return ctk.CTkButton(
        parent,
        text=text,
        command=command,
        font=font,
        fg_color=Theme.get_color('button'),
        text_color=Theme.get_color('text'),
        hover_color=Theme.get_color('button_hover'),
        corner_radius=corner_radius,
        height=height,
        cursor='hand2'
    )


def create_accent_button(parent, text, command):
    """Create a prominent accent-colored rounded button (START)."""
    return ctk.CTkButton(
        parent,
        text=text,
        command=command,
        font=Theme.get_font('button_large'),
        fg_color=Theme.get_color('accent'),
        text_color='white',
        hover_color=Theme.get_color('accent_hover'),
        corner_radius=Theme.DIMENSIONS['btn_radius'],
        height=50,  # Taller for main action
        cursor='hand2'
    )


def create_spinbox(parent, variable, from_=0, to=100, width=60):
    """Create a modern spinbox (Entry + Buttons)."""
    # CTk doesn't have a native Spinbox, so we build one.
    frame = ctk.CTkFrame(parent, fg_color="transparent")
    
    entry = ctk.CTkEntry(
        frame,
        textvariable=variable,
        width=width,
        height=24,  # Compact height
        font=Theme.get_font('body'),
        fg_color=Theme.get_color('input'),
        text_color=Theme.get_color('text'),
        border_color=Theme.get_color('input_border'),
        justify='center',
        corner_radius=Theme.DIMENSIONS['corner_radius']
    )
    entry.pack(side='left', padx=(0, 3))
    
    # Helper to validate input
    def validate(val):
        try:
            return from_ <= int(val) <= to
        except:
            return False

    def increment():
        try:
            val = int(variable.get())
            if val < to:
                variable.set(val + 1)
        except:
            variable.set(from_)

    def decrement():
        try:
            val = int(variable.get())
            if val > from_:
                variable.set(val - 1)
        except:
            variable.set(from_)
            
    # Buttons container
    btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
    btn_frame.pack(side='left')
    
    # Mini buttons
    # We use small height buttons
    btn_up = ctk.CTkButton(
        btn_frame, text="▲", width=20, height=12,
        font=('Arial', 6),
        fg_color=Theme.get_color('button'),
        hover_color=Theme.get_color('button_hover'),
        command=increment,
        corner_radius=3
    )
    btn_up.pack(pady=(0, 0)) # No gap
    
    btn_down = ctk.CTkButton(
        btn_frame, text="▼", width=20, height=12,
        font=('Arial', 6),
        fg_color=Theme.get_color('button'),
        hover_color=Theme.get_color('button_hover'),
        command=decrement,
        corner_radius=3
    )
    btn_down.pack()
    
    return frame


def create_combobox(parent, variable, values, width=150):
    """Create a modern rounded combobox."""
    return ctk.CTkComboBox(
        parent,
        variable=variable,
        values=values,
        width=width,
        font=Theme.get_font('body'),
        fg_color=Theme.get_color('input'),
        text_color=Theme.get_color('text'),
        border_color=Theme.get_color('input_border'),
        button_color=Theme.get_color('button'),
        button_hover_color=Theme.get_color('button_hover'),
        dropdown_fg_color=Theme.get_color('card'),
        dropdown_text_color=Theme.get_color('text'),
        dropdown_hover_color=Theme.get_color('button'),
        corner_radius=Theme.DIMENSIONS['corner_radius'],
        state="readonly" 
    )


def create_checkbox(parent, text, variable, bold=False):
    """Create a modern rounded checkbox."""
    font = Theme.get_font('body')
    if bold:
        font = (font[0], font[1], 'bold')
    
    return ctk.CTkCheckBox(
        parent,
        text=text,
        variable=variable,
        font=font,
        fg_color=Theme.get_color('accent'),
        hover_color=Theme.get_color('accent_hover'),
        text_color=Theme.get_color('text'),
        border_color=Theme.get_color('input_border'),
        corner_radius=4,
        border_width=2
    )


def create_label(parent, text, dim=False):
    """Create a styled label."""
    return ctk.CTkLabel(
        parent,
        text=text,
        font=Theme.get_font('small'),
        text_color=Theme.get_color('text_dim') if dim else Theme.get_color('text')
    )


def create_radiobutton(parent, text, variable, value, command=None):
    """Create a modern radiobutton."""
    return ctk.CTkRadioButton(
        parent,
        text=text,
        variable=variable,
        value=value,
        font=Theme.get_font('body'),
        fg_color=Theme.get_color('accent'),
        hover_color=Theme.get_color('accent_hover'),
        text_color=Theme.get_color('text'),
        command=command
    )

