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

from app.app import App


def main():
    """Launch the application."""
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()