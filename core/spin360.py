"""
360° Spin View generator — creates sprite sheets and interactive HTML viewers
from a set of multi-angle product images.
"""

import os
import io
import math
import json
import threading
from PIL import Image

from .spin_viewer import generate_viewer_html


class Spin360Generator:
    """Generates 360° spin view sprite sheets and self-contained HTML viewers."""

    def __init__(self, log_callback=print):
        self.log = log_callback
        self._rembg_session = None

    def generate(self, image_paths, output_dir, frame_size=512,
                 remove_bg=True, cancel_event=None):
        """
        Generate a 360° spin view from a list of image paths.

        Args:
            image_paths: List of image file paths (sorted by angle)
            output_dir: Directory to write output files into
            frame_size: Size of each frame in pixels (square)
            remove_bg: Whether to run AI background removal
            cancel_event: threading.Event to check for cancellation

        Returns:
            tuple: (success: bool, message: str)
        """
        if not image_paths:
            return False, "No images provided"

        cancel = cancel_event or threading.Event()

        # Sort images by filename for consistent angle ordering
        image_paths = sorted(image_paths, key=lambda p: os.path.basename(p).lower())
        total = len(image_paths)

        # --- 1. Process each frame ---
        self.log(f"Processing {total} frames...")
        processed_frames = []

        for idx, path in enumerate(image_paths):
            if cancel.is_set():
                return False, "Cancelled"

            filename = os.path.basename(path)
            self.log(f"  [{idx + 1}/{total}] {filename}")

            try:
                frame = self._process_frame(path, frame_size, remove_bg)
                processed_frames.append(frame)
            except Exception as e:
                self.log(f"    ✗ Failed: {e}")
                # Continue with remaining frames

        if not processed_frames:
            return False, "All frames failed to process"

        if cancel.is_set():
            return False, "Cancelled"

        # --- 2. Build sprite sheet ---
        total_frames = len(processed_frames)
        cols = int(math.ceil(math.sqrt(total_frames)))
        rows = int(math.ceil(total_frames / cols))

        self.log(f"Stitching sprite sheet: {cols}×{rows} ({total_frames} frames)")

        sheet_width = cols * frame_size
        sheet_height = rows * frame_size
        sprite_sheet = Image.new('RGBA', (sheet_width, sheet_height), (0, 0, 0, 0))

        for i, frame in enumerate(processed_frames):
            col = i % cols
            row = i // cols
            sprite_sheet.paste(frame, (col * frame_size, row * frame_size))

        # --- 3. Save sprite sheet ---
        spin_dir = os.path.join(output_dir, "360_view")
        os.makedirs(spin_dir, exist_ok=True)

        sprite_name = "product_sprite.webp"
        sprite_path = os.path.join(spin_dir, sprite_name)
        sprite_sheet.save(sprite_path, 'webp', quality=80, method=6, alpha_quality=85, exact=False)
        self.log(f"Sprite sheet saved: {sprite_name}")

        # --- 3b. Save animated GIF ---
        gif_name = "product_360.gif"
        gif_path = os.path.join(spin_dir, gif_name)
        # Composite RGBA frames onto white background (GIF has 1-bit alpha only)
        gif_frames = []
        for frame in processed_frames:
            bg = Image.new('RGB', (frame_size, frame_size), (255, 255, 255))
            bg.paste(frame, (0, 0), frame)
            gif_frames.append(bg)
        
        if gif_frames:
            gif_frames[0].save(
                gif_path, save_all=True, append_images=gif_frames[1:],
                duration=80, loop=0, optimize=True,
            )
            self.log(f"Animated GIF saved: {gif_name}")

        # --- 4. Save config.json ---
        config_data = {
            "spriteSheetName": sprite_name,
            "totalFrames": total_frames,
            "cols": cols,
            "frameSizePx": frame_size,
        }

        config_path = os.path.join(spin_dir, "config.json")
        with open(config_path, 'w') as f:
            json.dump(config_data, f, indent=4)

        # --- 5. Generate self-contained HTML viewer ---
        html_content = generate_viewer_html(config_data, sprite_name)
        html_path = os.path.join(spin_dir, "360_viewer.html")
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        self.log("Viewer HTML generated: 360_viewer.html")

        return True, f"{total_frames} frames → {spin_dir}"

    def _process_frame(self, image_path, frame_size, remove_bg):
        """
        Process a single frame: optionally remove background,
        resize and center on a square canvas.

        Returns:
            PIL.Image: Processed frame (RGBA, frame_size × frame_size)
        """
        if remove_bg:
            # Lazy-load rembg session for performance
            if self._rembg_session is None:
                from rembg import new_session
                self._rembg_session = new_session("u2net")

            from rembg import remove
            with open(image_path, 'rb') as f:
                img_data = f.read()

            output_data = remove(img_data, session=self._rembg_session)
            img = Image.open(io.BytesIO(output_data)).convert('RGBA')
        else:
            img = Image.open(image_path).convert('RGBA')

        # Resize preserving aspect ratio
        img.thumbnail((frame_size, frame_size), Image.Resampling.LANCZOS)

        # Center on square transparent canvas
        canvas = Image.new('RGBA', (frame_size, frame_size), (0, 0, 0, 0))
        offset_x = (frame_size - img.width) // 2
        offset_y = (frame_size - img.height) // 2
        canvas.paste(img, (offset_x, offset_y), img)

        return canvas
