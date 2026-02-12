"""
Metadata stripper for privacy — removes EXIF, GPS, and camera info.

Supports lossless stripping for JPEG (piexif), PNG and WebP (binary chunk removal).
Falls back to Pillow re-encoding for other formats.
"""

import os
import struct
import shutil
import piexif
from PIL import Image


# PNG chunks that contain metadata (non-critical, safe to strip)
_PNG_METADATA_CHUNKS = {
    b'tEXt', b'zTXt', b'iTXt', b'eXIf',
    b'tIME', b'pHYs', b'oFFs', b'sCAL',
    b'fRAc', b'gIFg', b'gIFx',
}

# WebP chunks that contain metadata
_WEBP_METADATA_CHUNKS = {b'EXIF', b'ICCP', b'XMP '}

# Format-specific save parameters for Pillow fallback
_FORMAT_SAVE_PARAMS = {
    '.jpg':  {'format': 'JPEG', 'quality': 95, 'optimize': True},
    '.jpeg': {'format': 'JPEG', 'quality': 95, 'optimize': True},
    '.webp': {'format': 'WEBP', 'quality': 95, 'optimize': True},
    '.png':  {'format': 'PNG', 'optimize': True},
    '.tiff': {'format': 'TIFF'},
    '.tif':  {'format': 'TIFF'},
    '.avif': {'format': 'AVIF'},
    '.bmp':  {'format': 'BMP'},
    '.ico':  {'format': 'ICO'},
    '.tga':  {'format': 'TGA'},
}


class MetadataStripper:
    """Remove all metadata from images for privacy."""

    def __init__(self, log_callback=print):
        self.log = log_callback

    def _strip_png(self, input_path, output_path):
        """
        Strip metadata chunks from PNG at the binary level.

        Preserves all critical chunks (IHDR, PLTE, IDAT, IEND)
        and transparency (tRNS). Only removes metadata chunks.
        """
        same_file = os.path.abspath(input_path) == os.path.abspath(output_path)
        temp_output = output_path + ".tmp" if same_file else output_path

        try:
            with open(input_path, 'rb') as f_in, open(temp_output, 'wb') as f_out:
                signature = f_in.read(8)
                if signature != b'\x89PNG\r\n\x1a\n':
                    return False, "Not a valid PNG"
                f_out.write(signature)

                while True:
                    length_bytes = f_in.read(4)
                    if not length_bytes:
                        break

                    length = struct.unpack('>I', length_bytes)[0]
                    chunk_type = f_in.read(4)
                    chunk_data = f_in.read(length)
                    crc = f_in.read(4)

                    if chunk_type in _PNG_METADATA_CHUNKS:
                        continue

                    f_out.write(length_bytes)
                    f_out.write(chunk_type)
                    f_out.write(chunk_data)
                    f_out.write(crc)

                    if chunk_type == b'IEND':
                        break

            if same_file:
                shutil.move(temp_output, output_path)

            return True, "Metadata stripped (lossless)"

        except Exception as e:
            if os.path.exists(temp_output) and same_file:
                os.remove(temp_output)
            return False, str(e)

    def _strip_webp(self, input_path, output_path):
        """
        Strip metadata chunks from WebP at the binary level.

        Removes EXIF, ICCP, and XMP chunks while preserving
        image data (VP8/VP8L) and features (alpha, animation).
        Updates VP8X flags to reflect removed metadata.
        """
        same_file = os.path.abspath(input_path) == os.path.abspath(output_path)
        temp_output = output_path + ".tmp" if same_file else output_path

        try:
            with open(input_path, 'rb') as f_in, open(temp_output, 'wb') as f_out:
                riff_sig = f_in.read(4)
                if riff_sig != b'RIFF':
                    return False, "Not a valid RIFF/WebP file"

                file_size_bytes = f_in.read(4)
                webp_sig = f_in.read(4)
                if webp_sig != b'WEBP':
                    return False, "Not a valid WebP file"

                # Write header (file size patched later)
                f_out.write(riff_sig)
                f_out.write(file_size_bytes)
                f_out.write(webp_sig)

                new_file_size = 4  # WEBP signature

                while True:
                    chunk_type = f_in.read(4)
                    if not chunk_type:
                        break

                    chunk_size_bytes = f_in.read(4)
                    chunk_size = struct.unpack('<I', chunk_size_bytes)[0]
                    chunk_data = f_in.read(chunk_size)

                    # RIFF chunks are padded to even size
                    padding = f_in.read(1) if chunk_size % 2 != 0 else b''

                    if chunk_type in _WEBP_METADATA_CHUNKS:
                        continue

                    # Clear metadata flags from VP8X extended header
                    if chunk_type == b'VP8X':
                        flags = chunk_data[0]
                        flags &= ~0x20  # Clear ICC Profile
                        flags &= ~0x08  # Clear EXIF
                        flags &= ~0x04  # Clear XMP
                        chunk_data = bytes([flags]) + chunk_data[1:]

                    f_out.write(chunk_type)
                    f_out.write(chunk_size_bytes)
                    f_out.write(chunk_data)
                    f_out.write(padding)

                    new_file_size += 8 + len(chunk_data) + len(padding)

                # Patch the RIFF file size
                f_out.seek(4)
                f_out.write(struct.pack('<I', new_file_size))

            if same_file:
                shutil.move(temp_output, output_path)

            return True, "Metadata stripped (lossless)"

        except Exception as e:
            if os.path.exists(temp_output) and same_file:
                os.remove(temp_output)
            return False, str(e)

    def _strip_fallback(self, input_path, output_path, ext):
        """
        Fallback: strip metadata by re-encoding with Pillow.

        Copies pixel data to a clean image, discarding all metadata.
        Preserves transparency info if present.
        """
        with Image.open(input_path) as img:
            clean_img = img.copy()

            # Preserve transparency, discard everything else
            old_info = clean_img.info.copy()
            clean_img.info.clear()
            if 'transparency' in old_info:
                clean_img.info['transparency'] = old_info['transparency']

            save_kwargs = _FORMAT_SAVE_PARAMS.get(ext, {})
            clean_img.save(output_path, **save_kwargs)
            clean_img.close()

    def process_file(self, input_path, output_path):
        """
        Remove all metadata from an image file.

        Strategy:
            1. JPEG → lossless via piexif.remove()
            2. PNG  → lossless binary chunk stripping
            3. WebP → lossless binary chunk stripping
            4. All others → Pillow re-encoding fallback

        Args:
            input_path: Source image path.
            output_path: Destination path.

        Returns:
            tuple: (success, message)
        """
        try:
            ext = os.path.splitext(output_path)[1].lower()

            # JPEG: lossless via piexif
            if ext in ('.jpg', '.jpeg'):
                try:
                    if os.path.abspath(input_path) != os.path.abspath(output_path):
                        shutil.copy2(input_path, output_path)
                    piexif.remove(output_path)
                    return True, "Metadata removed (lossless)"
                except Exception as e:
                    self.log(f"piexif failed ({e}), falling back to re-encoding...")

            # PNG: lossless chunk stripping
            elif ext == '.png':
                ok, msg = self._strip_png(input_path, output_path)
                if ok:
                    return ok, msg
                self.log(f"PNG strip failed ({msg}), falling back to re-encoding...")

            # WebP: lossless chunk stripping
            elif ext == '.webp':
                ok, msg = self._strip_webp(input_path, output_path)
                if ok:
                    return ok, msg
                self.log(f"WebP strip failed ({msg}), falling back to re-encoding...")

            # Fallback for all formats (also reached if lossless methods fail)
            self._strip_fallback(input_path, output_path, ext)
            return True, "Metadata removed"

        except Exception as e:
            return False, str(e)
