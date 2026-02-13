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
from PIL import Image, PngImagePlugin


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
            # Add XPTitle/XPComment too? Maybe overkill but standard.
            
        if artist_name:
            exif_dict["0th"][piexif.ImageIFD.Artist] = artist_name.encode('utf-8')
            # Windows XPAuthor (0x9c9d) - strict UTF-16LE without BOM, null terminated (2 bytes)
            # piexif expects bytes for XP tags properly encoded.
            # Convert string to utf-16le bytes.
            xp_author = artist_name.encode('utf-16le') + b'\x00\x00'
            exif_dict["0th"][0x9c9d] = xp_author

        return piexif.dump(exif_dict)
    
    def _build_xmp_bytes(self, copyright_text, artist_name):
        """Build minimal XMP packet with dc:creator and dc:rights."""
        # Simple string formatting is safer than xml.etree for XMP specifics
        xmp_template = (
            '<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="BatchPix">'
            '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
            '<rdf:Description rdf:about="" xmlns:dc="http://purl.org/dc/elements/1.1/">'
            '{creators}'
            '{rights}'
            '</rdf:Description>'
            '</rdf:RDF>'
            '</x:xmpmeta>'
        )
        
        creators = ""
        if artist_name:
            creators = (
                '<dc:creator><rdf:Seq><rdf:li>{0}</rdf:li></rdf:Seq></dc:creator>'
            ).format(artist_name)
            
        rights = ""
        if copyright_text:
            rights = (
                '<dc:rights><rdf:Alt><rdf:li xml:lang="x-default">{0}</rdf:li></rdf:Alt></dc:rights>'
            ).format(copyright_text)
            
        data = xmp_template.format(creators=creators, rights=rights)
        return data.encode('utf-8')

    def _tag_jpeg(self, input_path, output_path, exif_bytes):
        """Tag JPEG losslessly using piexif.insert (no re-encoding)."""
        if os.path.abspath(input_path) != os.path.abspath(output_path):
            shutil.copy2(input_path, output_path)
        
        piexif.insert(exif_bytes, output_path)
        return True, "Tagged JPEG (lossless)"
    
    def _create_text_chunk(self, keyword, text):
        """Create a tEXt chunk data (keyword + null + text). Encoded as Latin-1."""
        # PNG tEXt supports Latin-1. 'utf-8' might work in some viewers but valid spec is Latin-1.
        # We'll use 'ignore' to prevent crashes on unsupported chars.
        k = keyword.encode('latin-1', 'ignore')
        t = text.encode('latin-1', 'ignore')
        data = k + b'\0' + t
        return b'tEXt', data

    def _tag_png(self, input_path, output_path, exif_bytes, copyright_text=None, artist_name=None):
        """
        Tag PNG using Pillow's PngInfo for maximum compatibility.
        """
        try:
            with Image.open(input_path) as img:
                metadata = PngImagePlugin.PngInfo()
                
                # Add our tags to standard PNG text chunks
                # Use multiple keys for maximum compatibility
                if copyright_text:
                    metadata.add_text("Copyright", copyright_text)
                    metadata.add_text("Source", copyright_text)
                
                if artist_name:
                    metadata.add_text("Author", artist_name)
                    metadata.add_text("Artist", artist_name) # Unofficial but common
                    metadata.add_text("Description", f"By {artist_name}") # Windows sometimes shows this
                    metadata.add_text("Software", "BatchPix")
                
                # Add XMP packet (Standard for modern Windows Explorer)
                xmp_data = self._build_xmp_bytes(copyright_text, artist_name)
                # XML:com.adobe.xmp is the standard key for XMP in PNG iTXt
                metadata.add_itxt("XML:com.adobe.xmp", xmp_data.decode('utf-8'))

                # Save with metadata and EXIF
                # Pillow's PNG writer puts 'exif' bytes directly into 'eXIf' chunk.
                # The eXIf chunk expects raw TIFF data (II/MM...), but piexif.dump() adds 'Exif\x00\x00'.
                # We MUST strip this header for PNGs, otherwise Windows ignores the chunk.
                png_exif = exif_bytes
                if png_exif.startswith(b'Exif\x00\x00'):
                    png_exif = png_exif[6:]
                
                img.save(output_path, "png", pnginfo=metadata, exif=png_exif)
                
            return True, "Tagged PNG"
        
        except Exception as e:
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
                ok, msg = self._tag_png(input_path, output_path, exif_bytes, copyright_text, artist_name)
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