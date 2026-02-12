"""
Smart image resizer with presets and custom dimensions.
"""

import os
from PIL import Image

RESIZE_PRESETS = {
    "thumbnail": {"max_size": 150, "desc": "Thumbnail (150px)"},
    "small": {"max_size": 480, "desc": "Small (480px)"},
    "medium": {"max_size": 800, "desc": "Medium (800px)"},
    "large": {"max_size": 1200, "desc": "Large (1200px)"},
    "hd": {"max_size": 1920, "desc": "HD (1920px)"},
    "4k": {"max_size": 3840, "desc": "4K (3840px)"},
    "custom": {"max_size": None, "desc": "Custom..."},
}


class ImageResizer:
    def __init__(self, log_callback=print):
        self.log = log_callback

    def get_preset_names(self):
        return list(RESIZE_PRESETS.keys())

    def get_preset_descriptions(self):
        return [RESIZE_PRESETS[k]["desc"] for k in RESIZE_PRESETS]

    def process_file(self, input_path, output_path, preset=None, custom_size=None, upscale=False):
        """
        Resize image while maintaining aspect ratio.
        
        Args:
            input_path: Source image
            output_path: Destination
            preset: Preset name (thumbnail, small, medium, large, hd, 4k, custom)
            custom_size: Manual max dimension (used when preset='custom')
            upscale: If False, skip images smaller than target
            
        Returns:
            tuple: (success, message)
        """
        if preset == "custom":
            if not custom_size:
                return False, "Custom size not specified"
            target_size = custom_size
        elif preset and preset in RESIZE_PRESETS:
            target_size = RESIZE_PRESETS[preset]["max_size"]
        else:
            return False, "Invalid preset"

        try:
            img = Image.open(input_path)
            original_format = img.format
            width, height = img.size
            max_dim = max(width, height)

            if max_dim <= target_size and not upscale:
                img.save(output_path)
                return True, f"Skipped ({width}x{height})"

            if width > height:
                new_width = target_size
                new_height = int(height * (target_size / width))
            else:
                new_height = target_size
                new_width = int(width * (target_size / height))

            resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            save_format = original_format or "JPEG"
            
            # Optimization flags
            if save_format == "JPEG":
                resized.save(output_path, save_format, quality=85, optimize=True)
            elif save_format == "WEBP":
                resized.save(output_path, save_format, quality=85, method=6)
            elif save_format == "PNG":
                resized.save(output_path, save_format, optimize=True)
            else:
                resized.save(output_path, save_format)

            img.close()
            return True, f"{width}x{height} → {new_width}x{new_height}"

        except Exception as e:
            return False, str(e)
