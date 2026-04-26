"""
Background filler — composites a solid color or image behind each source image.
Works with RGBA sources (transparent PNGs, WebPs) and flat RGB images alike.
"""

from PIL import Image


def _parse_hex(hex_color: str) -> tuple:
    """Parse a hex color string (with or without #) into an (R, G, B, 255) tuple."""
    hex_color = hex_color.strip().lstrip('#')
    if len(hex_color) == 3:
        hex_color = ''.join(c * 2 for c in hex_color)
    if len(hex_color) != 6:
        raise ValueError(f"Invalid hex color: #{hex_color}")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return (r, g, b, 255)


def _scale_to_fill(bg: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """
    Scale bg image to cover target dimensions (scale-to-fill / crop strategy).
    The background image is scaled so that it completely covers the target size,
    then centre-cropped to exact dimensions. No letterboxing.
    """
    bg_w, bg_h = bg.size
    scale = max(target_w / bg_w, target_h / bg_h)
    new_w = int(bg_w * scale)
    new_h = int(bg_h * scale)
    bg = bg.resize((new_w, new_h), Image.Resampling.LANCZOS)

    # Center crop
    left = (new_w - target_w) // 2
    top  = (new_h - target_h) // 2
    bg = bg.crop((left, top, left + target_w, top + target_h))
    return bg


class BgFiller:
    """Composites a background (color or image) behind each source image."""

    def __init__(self, log_callback=print):
        self.log = log_callback

    def process_file(
        self,
        input_path: str,
        output_path: str,
        bg_type: str = "color",
        bg_color: str = "#ffffff",
        bg_image_path: str = "",
    ) -> tuple:
        """
        Add a background to input_path and save to output_path.

        Args:
            input_path:    Source image path.
            output_path:   Destination image path (can be same as input for in-place).
            bg_type:       "color" or "image".
            bg_color:      Hex color string used when bg_type == "color".
            bg_image_path: Path to background image used when bg_type == "image".

        Returns:
            (success: bool, message: str)
        """
        try:
            src = Image.open(input_path)
            original_format = src.format or "PNG"

            # Always work in RGBA so transparency compositing is correct
            src_rgba = src.convert("RGBA")
            w, h = src_rgba.size

            # Build the background canvas (always RGBA)
            if bg_type == "image":
                if not bg_image_path:
                    return False, "No background image path provided"
                try:
                    bg_raw = Image.open(bg_image_path).convert("RGBA")
                except Exception as e:
                    return False, f"Cannot open background image: {e}"
                canvas = _scale_to_fill(bg_raw, w, h)
            else:
                # Color mode
                try:
                    color = _parse_hex(bg_color)
                except ValueError as e:
                    return False, str(e)
                canvas = Image.new("RGBA", (w, h), color)

            # Composite: paste source (with its alpha as mask) over the canvas
            canvas.paste(src_rgba, (0, 0), mask=src_rgba)

            # Convert back to original color mode for saving
            # If the original was RGBA/LA keep RGBA; otherwise flatten to RGB
            if original_format in ("PNG", "WEBP") and src.mode in ("RGBA", "LA", "PA"):
                result = canvas  # keep transparency channel (bg is now opaque anyway)
            else:
                result = canvas.convert("RGB")

            # Preserve EXIF if present
            save_kwargs = {}
            exif = src.info.get("exif")
            if exif:
                save_kwargs["exif"] = exif

            result.save(output_path, original_format, **save_kwargs)
            src.close()
            return True, f"Background added ({bg_type})"

        except Exception as e:
            return False, str(e)
