"""
Canvas fitter — scales each image down to fit inside a square canvas with
even padding on all sides, centring the content on a transparent canvas.
"""

import os
from PIL import Image


class CanvasFitter:
    def __init__(self, log_callback=print):
        self.log = log_callback

    def process_file(self, input_path, output_path, canvas_size=200, padding=8):
        """
        Fit input image into a square canvas of `canvas_size` px with `padding`
        px of empty space on every side.

        - If the source has an alpha channel, transparent borders are trimmed
          first so padding is measured from the visible content.
        - The resized dimensions are forced to share parity with the canvas
          size, guaranteeing identical margins left/right and top/bottom
          (so the content stays exactly centred — no 1 px drift).

        Args:
            input_path:  Source image
            output_path: Destination (may be the same as input)
            canvas_size: Square canvas side length in pixels
            padding:     Empty space around the content on every side, in px

        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            canvas_size = int(canvas_size)
            padding = int(padding)
            if canvas_size <= 0:
                return False, "Canvas size must be positive"
            if padding < 0:
                return False, "Padding must be non-negative"
            if padding * 2 >= canvas_size:
                return False, "Padding too large for canvas size"

            src = Image.open(input_path)
            original_format = (src.format or 'PNG').upper()
            exif = src.info.get('exif')

            img = src.convert('RGBA')

            # Trim transparent borders so padding hugs the visible content
            alpha_bbox = img.split()[3].getbbox()
            if alpha_bbox:
                img = img.crop(alpha_bbox)

            target = canvas_size - padding * 2
            w, h = img.size
            scale = target / max(w, h)
            nw = max(1, int(round(w * scale)))
            nh = max(1, int(round(h * scale)))

            # Clamp to the available space (rounding can push us 1 px over)
            nw = min(nw, target)
            nh = min(nh, target)

            # Force parity match so (canvas_size - n) is even on both axes —
            # this guarantees pad_left == pad_right and pad_top == pad_bottom.
            if (canvas_size - nw) % 2 != 0:
                nw = max(1, nw - 1)
            if (canvas_size - nh) % 2 != 0:
                nh = max(1, nh - 1)

            resized = img.resize((nw, nh), Image.Resampling.LANCZOS)

            canvas = Image.new('RGBA', (canvas_size, canvas_size), (0, 0, 0, 0))
            offset = ((canvas_size - nw) // 2, (canvas_size - nh) // 2)
            canvas.paste(resized, offset, resized)

            ext = os.path.splitext(output_path)[1].lower()
            save_kwargs = {}
            if exif and ext in ('.jpg', '.jpeg', '.webp'):
                save_kwargs['exif'] = exif

            if ext in ('.jpg', '.jpeg'):
                # JPEG can't hold transparency — flatten on white
                flat = Image.new('RGB', canvas.size, (255, 255, 255))
                flat.paste(canvas, mask=canvas.split()[3])
                flat.save(output_path, 'JPEG', quality=90, optimize=True, **save_kwargs)
            elif ext == '.webp':
                canvas.save(output_path, 'WEBP', quality=90, method=6,
                            alpha_quality=90, exact=False, **save_kwargs)
            elif ext == '.png':
                canvas.save(output_path, 'PNG', optimize=True)
            else:
                # Best-effort fall-through using detected source format
                if original_format == 'JPEG':
                    flat = Image.new('RGB', canvas.size, (255, 255, 255))
                    flat.paste(canvas, mask=canvas.split()[3])
                    flat.save(output_path, original_format, **save_kwargs)
                else:
                    canvas.save(output_path, original_format, **save_kwargs)

            src.close()
            return True, f"{canvas_size}x{canvas_size} (pad {padding})"

        except Exception as e:
            return False, str(e)
