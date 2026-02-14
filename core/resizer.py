"""
Smart image resizer — resizes by width or height while preserving aspect ratio and metadata.
"""

import os
from PIL import Image


class ImageResizer:
    def __init__(self, log_callback=print):
        self.log = log_callback

    def process_file(self, input_path, output_path, target_size=1200, dimension='width'):
        """
        Resize image by fixing one dimension and scaling the other to maintain aspect ratio.
        Preserves EXIF metadata (copyright, author, etc.).
        
        Args:
            input_path: Source image path
            output_path: Destination path
            target_size: Target size in pixels for the chosen dimension
            dimension: Which dimension to fix — 'width' or 'height'
            
        Returns:
            tuple: (success, message)
        """
        try:
            img = Image.open(input_path)
            original_format = img.format
            width, height = img.size

            # Preserve EXIF metadata
            exif_data = img.info.get('exif')

            # Calculate new dimensions based on selected dimension
            if dimension == 'width':
                new_width = target_size
                new_height = int(height * (target_size / width))
            else:  # height
                new_height = target_size
                new_width = int(width * (target_size / height))

            resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            save_format = original_format or "JPEG"
            save_kwargs = {}

            # Preserve EXIF if available
            if exif_data:
                save_kwargs['exif'] = exif_data

            # Optimization flags per format
            if save_format == "JPEG":
                save_kwargs.update(quality=85, optimize=True)
            elif save_format == "WEBP":
                save_kwargs.update(quality=85, method=6)
            elif save_format == "PNG":
                save_kwargs.update(optimize=True)

            resized.save(output_path, save_format, **save_kwargs)
            img.close()
            return True, f"{width}x{height} → {new_width}x{new_height}"

        except Exception as e:
            return False, str(e)
