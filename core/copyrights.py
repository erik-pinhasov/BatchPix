"""
Add copyright and artist metadata to images.

Supports lossless EXIF insertion for JPEG, WebP, TIFF, and AVIF
via piexif, and binary-level eXIf chunk insertion for PNG.
"""

import os
import struct
import zlib
import piexif
from PIL import Image
import shutil


class CopyrightTagger:
    
    def __init__(self, log_callback=print):
        self.log = log_callback
    
    def _build_exif_bytes(self, copyright_text, artist_name, existing_exif=None):
        """Build EXIF bytes with copyright/artist, preserving existing EXIF if any."""
        exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}
        
        if existing_exif:
            try:
                existing = piexif.load(existing_exif)
                for key in ("0th", "Exif", "GPS", "1st"):
                    if key in existing and existing[key]:
                        exif_dict[key].update(existing[key])
            except Exception:
                pass
        
        if copyright_text:
            exif_dict["0th"][piexif.ImageIFD.Copyright] = copyright_text.encode('utf-8')
        if artist_name:
            exif_dict["0th"][piexif.ImageIFD.Artist] = artist_name.encode('utf-8')
        
        return piexif.dump(exif_dict)
    
    def _tag_jpeg(self, input_path, output_path, exif_bytes):
        """Tag JPEG losslessly using piexif.insert (no re-encoding)."""
        if os.path.abspath(input_path) != os.path.abspath(output_path):
            shutil.copy2(input_path, output_path)
        
        piexif.insert(exif_bytes, output_path)
        return True, "Tagged JPEG (lossless)"
    
    def _tag_png(self, input_path, output_path, exif_bytes):
        """
        Tag PNG by inserting an eXIf chunk at binary level.
        No image re-encoding — only chunk-level manipulation.
        """
        # eXIf chunk stores raw TIFF data without the 'Exif\x00\x00' prefix
        # piexif.dump() includes that prefix, so strip it
        if exif_bytes[:6] == b'Exif\x00\x00':
            chunk_data = exif_bytes[6:]
        else:
            chunk_data = exif_bytes
        same_file = os.path.abspath(input_path) == os.path.abspath(output_path)
        temp_output = output_path + ".tmp" if same_file else output_path
        
        try:
            with open(input_path, 'rb') as f_in, open(temp_output, 'wb') as f_out:
                # Validate and copy PNG signature
                sig = f_in.read(8)
                if sig != b'\x89PNG\r\n\x1a\n':
                    return False, "Not a valid PNG"
                f_out.write(sig)
                
                exif_written = False
                
                while True:
                    header = f_in.read(8)
                    if len(header) < 8:
                        break
                    
                    length = struct.unpack('>I', header[:4])[0]
                    chunk_type = header[4:8]
                    cdata = f_in.read(length)
                    chunk_crc = f_in.read(4)
                    
                    # Skip any existing eXIf chunk (we'll write our own)
                    if chunk_type == b'eXIf':
                        continue
                    
                    # Insert our eXIf chunk right before IDAT (after all header chunks)
                    if chunk_type == b'IDAT' and not exif_written:
                        self._write_chunk(f_out, b'eXIf', chunk_data)
                        exif_written = True
                    
                    # Copy original chunk as-is
                    f_out.write(header)
                    f_out.write(cdata)
                    f_out.write(chunk_crc)
                    
                    if chunk_type == b'IEND':
                        break
                
                # If no IDAT was found (unlikely), insert before EOF
                if not exif_written:
                    self._write_chunk(f_out, b'eXIf', chunk_data)
            
            if same_file:
                shutil.move(temp_output, output_path)
            
            return True, "Tagged PNG (lossless)"
        
        except Exception as e:
            if os.path.exists(temp_output) and same_file:
                try:
                    os.remove(temp_output)
                except OSError:
                    pass
            return False, f"PNG tag failed: {e}"
    
    def _write_chunk(self, f_out, chunk_type, chunk_data):
        """Write a properly formatted PNG chunk with CRC."""
        f_out.write(struct.pack('>I', len(chunk_data)))
        f_out.write(chunk_type)
        f_out.write(chunk_data)
        crc = zlib.crc32(chunk_type)
        crc = zlib.crc32(chunk_data, crc) & 0xffffffff
        f_out.write(struct.pack('>I', crc))
    
    def _tag_webp(self, input_path, output_path, exif_bytes):
        """Tag WebP losslessly using piexif.insert (no re-encoding)."""
        if os.path.abspath(input_path) != os.path.abspath(output_path):
            shutil.copy2(input_path, output_path)
        
        piexif.insert(exif_bytes, output_path)
        return True, "Tagged WebP (lossless)"
    
    def process_file(self, input_path, output_path, copyright_text, artist_name):
        """Add copyright/artist metadata to an image file."""
        if not copyright_text and not artist_name:
            return False, "No text provided"
        
        ext = os.path.splitext(input_path)[1].lower()
        supported = {'.jpg', '.jpeg', '.webp', '.png', '.tiff', '.tif', '.avif'}
        
        if ext not in supported:
            return False, f"Unsupported format: {ext}"
        
        try:
            # Load existing EXIF if any
            existing_exif = None
            try:
                with Image.open(input_path) as img:
                    existing_exif = img.info.get('exif')
            except Exception:
                pass
            
            # Build EXIF with copyright data
            exif_bytes = self._build_exif_bytes(copyright_text, artist_name, existing_exif)
            
            # Tag based on format
            if ext in ('.jpg', '.jpeg'):
                ok, msg = self._tag_jpeg(input_path, output_path, exif_bytes)
            elif ext == '.png':
                ok, msg = self._tag_png(input_path, output_path, exif_bytes)
            elif ext in ('.webp', '.tiff', '.tif', '.avif'):
                ok, msg = self._tag_webp(input_path, output_path, exif_bytes)
            else:
                return False, "Unsupported"
            
            if not ok:
                return False, msg
            
            # Verify the tag was written
            try:
                with Image.open(output_path) as verify:
                    if 'exif' in verify.info:
                        v = piexif.load(verify.info['exif'])
                        v_copy = v["0th"].get(piexif.ImageIFD.Copyright, b"").decode('utf-8', 'ignore')
                        if v_copy == copyright_text:
                            return True, msg
                    return False, "Verification failed - tag not readable"
            except Exception as e:
                return False, f"Verification error: {e}"
            
        except Exception as e:
            return False, str(e)
    
    def process_folder(self, input_folder, copyright_text, artist_name, output_folder=None):
        if output_folder is None:
            output_folder = os.path.join(input_folder, "tagged_images")
        
        os.makedirs(output_folder, exist_ok=True)
        count = 0
        
        self.log(f"Starting copyright tagging in: {input_folder}")
        
        for root, dirs, files in os.walk(input_folder):
            if output_folder in root:
                continue
            
            for filename in files:
                ext = os.path.splitext(filename)[1].lower()
                if ext in {'.jpg', '.jpeg', '.webp', '.png', '.tiff', '.tif', '.avif'}:
                    f_in = os.path.join(root, filename)
                    f_out = os.path.join(output_folder, filename)
                    
                    ok, msg = self.process_file(f_in, f_out, copyright_text, artist_name)
                    if ok:
                        self.log(f"✓ Tagged: {filename}")
                        count += 1
                    else:
                        self.log(f"✗ Error {filename}: {msg}")
        
        self.log(f"Done! Processed {count} images.")
        return count