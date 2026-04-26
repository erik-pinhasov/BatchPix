"""
Smart image resizer — resizes by width or height while preserving aspect ratio and metadata.
"""

import os
from PIL import Image


class ImageResizer:
    def __init__(self, log_callback=print):
        self.log = log_callback

    def process_file(self, input_path, output_path, target_size=1200, dimension='width',
                     lossless_intermediate=False):
        """
        Resize image by fixing one dimension and scaling the other to maintain aspect ratio.
        Preserves EXIF metadata (copyright, author, etc.).

        Args:
            input_path:            Source image path
            output_path:           Destination path
            target_size:           Target size in pixels for the chosen dimension
            dimension:             Which dimension to fix — 'width' or 'height'
            lossless_intermediate: When True and the source is a lossy format (JPEG),
                                   save as PNG instead to avoid double lossy encode.
                                   The caller receives the actual output path in return.

        Returns:
            tuple: (success, message, actual_output_path)
        """
        try:
            img = Image.open(input_path)
            original_format = img.format or 'JPEG'
            width, height = img.size

            # Preserve EXIF metadata
            exif_data = img.info.get('exif')

            # Calculate new dimensions
            if dimension == 'width':
                new_width = target_size
                new_height = int(height * (target_size / width))
            else:  # height
                new_height = target_size
                new_width = int(width * (target_size / height))

            resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            lossy_source = original_format.upper() in ('JPEG', 'JPG')
            use_png_intermediate = lossless_intermediate and lossy_source

            if use_png_intermediate:
                save_format = 'PNG'
                actual_output = os.path.splitext(output_path)[0] + '.png'
            else:
                save_format = original_format.upper()
                actual_output = output_path

            save_kwargs = {}

            # Preserve EXIF only for formats that support it
            if exif_data and save_format in ('JPEG', 'WEBP'):
                save_kwargs['exif'] = exif_data

            # Format-specific save params
            if save_format == 'JPEG':
                save_kwargs.update(quality=82, optimize=True)
                resized.save(actual_output, save_format, **save_kwargs)
            elif save_format == 'WEBP':

                save_kwargs.update(quality=82, method=6, alpha_quality=80,
                                   exact=False, lossless=False)
                resized.save(actual_output, save_format, **save_kwargs)
            elif save_format == 'PNG':
                if use_png_intermediate:

                    resized.save(actual_output, 'PNG', optimize=True)
                else:
                    try:
                        import imagequant
                        src = resized.convert('RGBA') if resized.mode != 'RGBA' else resized
                        quantized = imagequant.quantize_pil_image(
                            src, dithering_level=1.0, max_colors=256,
                            min_quality=65, max_quality=85,
                        )
                        quantized.save(actual_output, format='PNG')
                    except ImportError:
                        resized.save(actual_output, 'PNG', optimize=True)
            else:
                resized.save(actual_output, save_format, **save_kwargs)

            if actual_output != input_path and os.path.exists(input_path):
                os.remove(input_path)

            img.close()
            return True, f"{width}x{height} → {new_width}x{new_height}", actual_output

        except Exception as e:
            return False, str(e), output_path