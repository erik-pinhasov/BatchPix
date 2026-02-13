"""
BatchPix - Entry Point

Batch process images for web optimization with:
- AI Enhancement (Real-ESRGAN)
- Smart Resize & Crop
- Format Conversion (WebP, PNG, JPEG, BMP, TIFF)
- Metadata Management
- AI-powered Renaming
- Copyright Tagging

Author: E.P.
"""

import ctypes
try:
    # Per-Monitor DPI awareness — must be set before any window is created
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

from app.app import App


def main():
    """Launch the application."""
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()