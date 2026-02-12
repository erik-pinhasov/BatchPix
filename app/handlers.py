"""
Event handlers and image processing pipeline.
"""

import os
import shutil
import threading

IMAGE_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp', '.gif',
    '.ico', '.avif', '.svg', '.tga',
}


class ProcessingHandler:
    """Handles image processing operations."""
    
    def __init__(self, app):
        self.app = app
        self._init_processors()
    
    def _init_processors(self):
        """Initialize image processors with lazy loading."""
        from core.enhancer import ImageEnhancer
        from core.resizer import ImageResizer
        from core.metadata_stripper import MetadataStripper
        from core.smart_crop import SmartCropper
        from core.copyrights import CopyrightTagger
        
        self.enhancer = ImageEnhancer(self.app.log)
        self.resizer = ImageResizer(self.app.log)
        self.stripper = MetadataStripper(self.app.log)
        self.cropper = SmartCropper(self.app.log)
        self.copyright_tagger = CopyrightTagger(self.app.log)
        self.renamer = None  # Lazy loaded due to heavy dependencies
    
    def process(self, files, output_dir, options):
        """Process images in a background thread."""
        thread = threading.Thread(
            target=self._process_images,
            args=(files, output_dir, options)
        )
        thread.daemon = True
        thread.start()
    
    def _process_images(self, files, output_dir, options):
        """Main processing logic."""
        try:
            from PIL import Image
            Image.MAX_IMAGE_PIXELS = None
            
            os.makedirs(output_dir, exist_ok=True)
            
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
                self.app.log("=== ENHANCE ===")
                for i, path in enumerate(working):
                    self.app.log(f"[{i+1}/{total}] {os.path.basename(path)}")
                    tmp = path + ".tmp" + os.path.splitext(path)[1]
                    ok, msg = self.enhancer.process_image(path, tmp, options['model'])
                    if ok and os.path.exists(tmp):
                        os.remove(path)
                        os.rename(tmp, path)
                        self.app.log("  ✓ Enhanced")
                    else:
                        self.app.log(f"  ✗ {msg}")
            
            # 2. Resize
            if options.get('resize'):
                self.app.log("=== RESIZE ===")
                custom = max(options['width'], options['height']) if options['preset'] == 'custom' else None
                for i, path in enumerate(working):
                    self.app.log(f"[{i+1}/{total}] {os.path.basename(path)}")
                    ok, msg = self.resizer.process_file(path, path, preset=options['preset'], custom_size=custom)
                    self.app.log("  ✓ Resized" if ok else f"  ✗ {msg}")
            
            # 3. Smart Crop
            if options.get('crop'):
                self.app.log("=== CROP ===")
                for i, path in enumerate(working):
                    self.app.log(f"[{i+1}/{total}] {os.path.basename(path)}")
                    ok, msg = self.cropper.process_file(path, path)
                    self.app.log("  ✓ Cropped" if ok else f"  ✗ {msg}")
            
            # 4. Convert to WebP
            if options.get('webp'):
                self.app.log("=== CONVERT TO WEBP ===")
                new_working = []
                for i, path in enumerate(working):
                    self.app.log(f"[{i+1}/{total}] {os.path.basename(path)}")
                    ext = os.path.splitext(path)[1].lower()
                    if ext != '.webp':
                        try:
                            img = Image.open(path)
                            if img.mode in ('RGBA', 'LA', 'PA', 'P'):
                                img = img.convert('RGBA')
                            webp_path = os.path.splitext(path)[0] + ".webp"
                            img.save(webp_path, "webp", quality=95)
                            img.close()
                            os.remove(path)
                            new_working.append(webp_path)
                            self.app.log("  ✓ Converted")
                        except Exception as e:
                            new_working.append(path)
                            self.app.log(f"  ✗ {e}")
                    else:
                        new_working.append(path)
                        self.app.log("  - Already WebP")
                working = new_working
            
            # 5. Strip Metadata
            if options.get('strip'):
                self.app.log("=== STRIP METADATA ===")
                for i, path in enumerate(working):
                    self.app.log(f"[{i+1}/{total}] {os.path.basename(path)}")
                    ok, msg = self.stripper.process_file(path, path)
                    self.app.log("  ✓ Stripped" if ok else f"  ✗ {msg}")
            
            # 6. AI Rename
            if options.get('rename'):
                self.app.log("=== AI RENAME ===")
                if self.renamer is None:
                    self.app.log("Loading AI model...")
                    from core.renamer import AutoRenamer
                    self.renamer = AutoRenamer(self.app.log)
                
                new_working = []
                for i, path in enumerate(working):
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
                self.app.log("=== COPYRIGHT ===")
                for i, path in enumerate(working):
                    self.app.log(f"[{i+1}/{total}] {os.path.basename(path)}")
                    ok, msg = self.copyright_tagger.process_file(
                        path, path, options['copyright_text'], options['artist']
                    )
                    self.app.log(f"  ✓ {msg}" if ok else f"  ✗ {msg}")
            
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
