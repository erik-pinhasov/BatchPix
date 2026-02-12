"""
Smart image cropper - removes empty borders (transparency or solid color).
"""

import os
from PIL import Image, ImageChops


class SmartCropper:
    def __init__(self, log_callback=print):
        self.log = log_callback

    def process_file(self, input_path, output_path, tolerance=10):
        """
        Crop empty/transparent borders from image.
        
        Args:
            input_path: Source image
            output_path: Destination
            
        Returns:
            tuple: (success, message)
        """
        try:
            img = Image.open(input_path)
            original_size = img.size
            if 'exif' in img.info:
                exif = img.info['exif']
            else:
                exif = b""
            
            bbox = None
            
            # 1. Determine Bounding Box (Non-destructive)
            if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                # Use alpha channel to find content
                # Convert a COPY to RGBA to find alpha bounds
                temp_img = img.convert('RGBA')
                alpha = temp_img.split()[-1]
                bbox = alpha.getbbox()
                # temp_img is discarded, original 'img' is untouched (e.g. kept as P-mode)
            else:
                # For non-transparent images, detect solid color borders
                bg = Image.new(img.mode, img.size, img.getpixel((0, 0)))
                diff = ImageChops.difference(img, bg)
                
                if tolerance > 0:
                    diff = diff.point(lambda x: 0 if x < tolerance else 255)
                
                bbox = diff.getbbox()
            
            if bbox:
                # Crop the ORIGINAL image (preserving P-mode/Palette)
                cropped = img.crop(bbox)
                new_size = cropped.size
                
                # Save with Optimization
                ext = os.path.splitext(output_path)[1].lower()
                save_kwargs = {}
                if exif:
                    save_kwargs['exif'] = exif
                
                if ext in ['.jpg', '.jpeg']:
                    if cropped.mode == 'RGBA':
                        cropped = cropped.convert('RGB')
                    # Use 85 quality + optimize (balance size/quality)
                    cropped.save(output_path, 'JPEG', quality=85, optimize=True, **save_kwargs)
                    
                elif ext == '.webp':
                    # Use 85 quality + method 6 (best compression)
                    cropped.save(output_path, 'WEBP', quality=85, method=6, **save_kwargs)
                    
                elif ext == '.png':
                    # Optimize PNG (P-mode preserved automatically if cropped.mode == 'P')
                    cropped.save(output_path, 'PNG', optimize=True, **save_kwargs)
                    
                else:
                    cropped.save(output_path, **save_kwargs)
                
                img.close()
                
                if original_size != new_size:
                    return True, f"{original_size[0]}x{original_size[1]} → {new_size[0]}x{new_size[1]}"
                else:
                    return True, "No empty borders"
            else:
                # Image is entirely empty/solid
                img.save(output_path)
                img.close()
                return True, "No content found"
                
        except Exception as e:
            return False, str(e)
