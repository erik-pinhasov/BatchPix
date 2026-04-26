"""
Event handlers and image processing pipeline.
"""

import os
import shutil
import threading

def _save_png(img, path):
    """
    Save a PIL image as PNG using imagequant (lossy palette reduction, same engine
    as pngquant) when available. Falls back to Pillow's lossless optimize if not.
    imagequant typically produces 60-80% smaller files than Pillow alone.
    Install: pip install imagequant
    """
    try:
        import imagequant
        # imagequant requires RGBA mode
        src = img.convert('RGBA') if img.mode != 'RGBA' else img
        quantized = imagequant.quantize_pil_image(
            src,
            dithering_level=1.0,
            max_colors=256,
            min_quality=65,
            max_quality=85,
        )
        quantized.save(path, format='PNG')
    except ImportError:
        img.save(path, format='PNG', optimize=True)


IMAGE_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp', '.gif',
    '.ico', '.avif', '.svg', '.tga',
}

# Format-specific save parameters
FORMAT_SAVE_PARAMS = {
    'WEBP':  {'format': 'WEBP', 'quality': 82, 'method': 6, 'alpha_quality': 80, 'exact': False, 'lossless': False},
    'PNG':   {'format': 'PNG', 'optimize': True},
    'JPEG':  {'format': 'JPEG', 'quality': 82, 'optimize': True},
    'BMP':   {'format': 'BMP'},
    'TIFF':  {'format': 'TIFF'},
}

# File extensions for each output format
FORMAT_EXTENSIONS = {
    'WEBP': '.webp', 'PNG': '.png', 'JPEG': '.jpg',
    'BMP': '.bmp', 'TIFF': '.tiff',
}


class ProcessingHandler:
    """Handles image processing operations."""
    
    def __init__(self, app):
        self.app = app
        self._cancel_event = threading.Event()
        self._current_output_dir = None
        self._init_processors()
    
    def _init_processors(self):
        """Initialize image processors with lazy loading."""
        from core.enhancer import ImageEnhancer
        from core.resizer import ImageResizer
        from core.metadata_stripper import MetadataStripper
        from core.smart_crop import SmartCropper
        from core.copyrights import CopyrightTagger
        from core.bg_fill import BgFiller
        from core.canvas_fit import CanvasFitter

        self.enhancer = ImageEnhancer(self.app.log)
        self.resizer = ImageResizer(self.app.log)
        self.stripper = MetadataStripper(self.app.log)
        self.cropper = SmartCropper(self.app.log)
        self.copyright_tagger = CopyrightTagger(self.app.log)
        self.bg_filler = BgFiller(self.app.log)
        self.canvas_fitter = CanvasFitter(self.app.log)
        self.renamer = None  # Lazy loaded due to heavy dependencies
        self.spin360 = None  # Lazy loaded due to heavy dependencies (rembg)
    
    def process(self, files, output_dir, options):
        """Process images in a background thread."""
        self._cancel_event.clear()
        self._current_output_dir = None
        thread = threading.Thread(
            target=self._process_images,
            args=(files, output_dir, options)
        )
        thread.daemon = True
        thread.start()
    
    def cancel(self):
        """Cancel the current processing and delete output."""
        self._cancel_event.set()
    
    def _cancelled(self):
        """Check if processing was cancelled. If so, clean up and return True."""
        if self._cancel_event.is_set():
            self.app.log("\n✗ CANCELLED")
            if self._current_output_dir and os.path.exists(self._current_output_dir):
                try:
                    shutil.rmtree(self._current_output_dir)
                    self.app.log(f"Cleaned up: {self._current_output_dir}")
                except Exception as e:
                    self.app.log(f"Cleanup error: {e}")
            self.app.on_processing_complete()
            return True
        return False
    
    def _get_unique_output_dir(self, base_path):
        """Return a unique output directory, appending _1, _2, etc. if it already has files."""
        if not os.path.exists(base_path) or not os.listdir(base_path):
            return base_path
        
        counter = 1
        while True:
            candidate = f"{base_path}_{counter}"
            if not os.path.exists(candidate) or not os.listdir(candidate):
                return candidate
            counter += 1

    def _process_images(self, files, output_dir, options):
        """Main processing logic."""
        try:
            from PIL import Image
            Image.MAX_IMAGE_PIXELS = None
            
            # Auto-increment output folder if it already has files
            output_dir = self._get_unique_output_dir(output_dir)
            self._current_output_dir = output_dir
            os.makedirs(output_dir, exist_ok=True)
            self.app.log(f"Output: {output_dir}")
            
            # Copy files to output directory
            working = []
            for f in files:
                dst = os.path.join(output_dir, os.path.basename(f))
                shutil.copy2(f, dst)
                working.append(dst)
            
            total = len(working)
            
            # 0. Rasterize SVGs to PNG (before any processing)
            new_working = []
            for path in working:
                if path.lower().endswith('.svg'):
                    try:
                        import cairosvg
                        png_path = os.path.splitext(path)[0] + '.png'
                        cairosvg.svg2png(url=path, write_to=png_path, output_width=2048)
                        os.remove(path)
                        new_working.append(png_path)
                        self.app.log(f"  SVG → PNG: {os.path.basename(png_path)}")
                    except Exception as e:
                        self.app.log(f"  ✗ SVG convert failed: {e}")
                        new_working.append(path)
                else:
                    new_working.append(path)
            working = new_working
            
            # 1. Enhance
            if options.get('enhance'):
                if self._cancelled(): return
                self.app.log("=== ENHANCE ===")
                for i, path in enumerate(working):
                    if self._cancelled(): return
                    self.app.log(f"[{i+1}/{total}] {os.path.basename(path)}")
                    tmp = path + ".tmp" + os.path.splitext(path)[1]
                    ok, msg = self.enhancer.process_image(path, tmp, options['model'])
                    if ok and os.path.exists(tmp):
                        os.remove(path)
                        os.rename(tmp, path)
                        self.app.log("  ✓ Enhanced")
                    else:
                        self.app.log(f"  ✗ {msg}")
            
            # 2. Smart Crop (run before resize so we resize the trimmed content)
            if options.get('crop'):
                if self._cancelled(): return
                self.app.log("=== CROP ===")
                for i, path in enumerate(working):
                    if self._cancelled(): return
                    self.app.log(f"[{i+1}/{total}] {os.path.basename(path)}")
                    ok, msg = self.cropper.process_file(path, path)
                    self.app.log("  ✓ Cropped" if ok else f"  ✗ {msg}")

            # 3. Resize
            if options.get('resize'):
                if self._cancelled(): return
                self.app.log("=== RESIZE ===")
                # When a convert step follows, save as lossless PNG intermediate
                # to avoid double lossy encode (e.g. JPEG→resize at q=85→convert to WebP at q=82).
                use_lossless_intermediate = options.get('convert', False)
                new_working = []
                for i, path in enumerate(working):
                    if self._cancelled(): return
                    self.app.log(f"[{i+1}/{total}] {os.path.basename(path)}")
                    ok, msg, out_path = self.resizer.process_file(
                        path, path,
                        target_size=options['custom_size'],
                        dimension=options['resize_dimension'],
                        lossless_intermediate=use_lossless_intermediate,
                    )
                    self.app.log("  ✓ Resized" if ok else f"  ✗ {msg}")
                    new_working.append(out_path if ok else path)
                working = new_working

            # 3.25. Fit to Canvas
            if options.get('canvas_fit'):
                if self._cancelled(): return
                self.app.log("=== FIT TO CANVAS ===")
                for i, path in enumerate(working):
                    if self._cancelled(): return
                    self.app.log(f"[{i+1}/{total}] {os.path.basename(path)}")
                    ok, msg = self.canvas_fitter.process_file(
                        path, path,
                        canvas_size=options.get('canvas_size', 200),
                        padding=options.get('canvas_padding', 8),
                    )
                    self.app.log(f"  ✓ {msg}" if ok else f"  ✗ {msg}")

            # 3.5. Add Background
            if options.get('bg'):
                if self._cancelled(): return
                self.app.log("=== ADD BACKGROUND ===")
                for i, path in enumerate(working):
                    if self._cancelled(): return
                    self.app.log(f"[{i+1}/{total}] {os.path.basename(path)}")
                    ok, msg = self.bg_filler.process_file(
                        path, path,
                        bg_type=options.get('bg_type', 'color'),
                        bg_color=options.get('bg_color', '#ffffff'),
                        bg_image_path=options.get('bg_image', ''),
                    )
                    self.app.log(f"  ✓ {msg}" if ok else f"  ✗ {msg}")

            # 4. Convert Format
            target_fmt = options.get('convert_format', 'WEBP')
            target_ext = FORMAT_EXTENSIONS.get(target_fmt, '.webp')
            if options.get('convert'):
                if self._cancelled(): return
                self.app.log(f"=== CONVERT TO {target_fmt} ===")
                new_working = []
                for i, path in enumerate(working):
                    if self._cancelled(): return
                    self.app.log(f"[{i+1}/{total}] {os.path.basename(path)}")
                    ext = os.path.splitext(path)[1].lower()
                    if ext != target_ext:
                        try:
                            img = Image.open(path)
                            # Handle transparency for formats that don't support it
                            if target_fmt == 'JPEG' and img.mode in ('RGBA', 'LA', 'PA', 'P'):
                                img = img.convert('RGB')
                            elif img.mode in ('RGBA', 'LA', 'PA', 'P'):
                                img = img.convert('RGBA')
                            new_path = os.path.splitext(path)[0] + target_ext
                            if target_fmt == 'PNG':
                                _save_png(img, new_path)
                            else:
                                save_params = FORMAT_SAVE_PARAMS.get(target_fmt, {})
                                img.save(new_path, **save_params)
                            img.close()
                            os.remove(path)
                            new_working.append(new_path)
                            self.app.log(f"  ✓ → {target_fmt}")
                        except Exception as e:
                            new_working.append(path)
                            self.app.log(f"  ✗ {e}")
                    else:
                        # Same format: re-encode in-place to apply current save params
                        try:
                            img = Image.open(path)
                            if target_fmt == 'JPEG' and img.mode in ('RGBA', 'LA', 'PA', 'P'):
                                img = img.convert('RGB')
                            elif img.mode in ('RGBA', 'LA', 'PA', 'P'):
                                img = img.convert('RGBA')
                            if target_fmt == 'PNG':
                                _save_png(img, path)
                            else:
                                save_params = FORMAT_SAVE_PARAMS.get(target_fmt, {})
                                img.save(path, **save_params)
                            img.close()
                            new_working.append(path)
                            self.app.log(f"  ✓ Re-compressed {target_fmt}")
                        except Exception as e:
                            new_working.append(path)
                            self.app.log(f"  ✗ {e}")
                working = new_working
            
            # 5. Strip Metadata
            if options.get('strip'):
                if self._cancelled(): return
                self.app.log("=== STRIP METADATA ===")
                for i, path in enumerate(working):
                    if self._cancelled(): return
                    self.app.log(f"[{i+1}/{total}] {os.path.basename(path)}")
                    ok, msg = self.stripper.process_file(path, path)
                    self.app.log("  ✓ Stripped" if ok else f"  ✗ {msg}")
            
            # 6. AI Rename
            if options.get('rename'):
                if self._cancelled(): return
                self.app.log("=== AI RENAME ===")
                if self.renamer is None:
                    self.app.log("Loading AI model...")
                    from core.renamer import AutoRenamer
                    self.renamer = AutoRenamer(self.app.log)
                
                new_working = []
                for i, path in enumerate(working):
                    if self._cancelled(): return
                    self.app.log(f"[{i+1}/{total}] {os.path.basename(path)}")
                    ok, new_name, caption = self.renamer.process_file(path)
                    if ok:
                        self.app.log(f"  ✓ → {new_name}")
                        new_path = os.path.join(os.path.dirname(path), new_name)
                        new_working.append(new_path)
                    else:
                        self.app.log(f"  ✗ {new_name}")
                        new_working.append(path)
                working = new_working
            
            # 7. Copyright
            if options.get('copyright'):
                if self._cancelled(): return
                self.app.log("=== COPYRIGHT ===")
                for i, path in enumerate(working):
                    if self._cancelled(): return
                    self.app.log(f"[{i+1}/{total}] {os.path.basename(path)}")
                    ok, msg = self.copyright_tagger.process_file(
                        path, path, options['copyright_text'], options['artist']
                    )
                    self.app.log(f"  ✓ {msg}" if ok else f"  ✗ {msg}")
            
            # 8. 360° Spin View
            if options.get('spin360'):
                if self._cancelled(): return
                self.app.log("=== 360° SPIN VIEW ===")
                if self.spin360 is None:
                    self.app.log("Loading background removal model...")
                    from core.spin360 import Spin360Generator
                    self.spin360 = Spin360Generator(self.app.log)
                
                ok, msg = self.spin360.generate(
                    image_paths=working,
                    output_dir=output_dir,
                    frame_size=options.get('spin360_frame_size', 512),
                    remove_bg=options.get('spin360_rembg', True),
                    cancel_event=self._cancel_event,
                )
                if ok:
                    self.app.log(f"  ✓ {msg}")
                else:
                    self.app.log(f"  ✗ {msg}")
            
            if self._cancelled(): return
            self.app.log(f"\n✓ DONE! {total} files saved to {output_dir}")
            
        except Exception as e:
            self.app.log(f"Error: {e}")
        
        self.app.on_processing_complete()


def get_image_files(folder):
    """Get all image files from a folder."""
    return [
        os.path.join(folder, f) for f in os.listdir(folder)
        if os.path.splitext(f)[1].lower() in IMAGE_EXTENSIONS
    ]