"""
AI-powered image renaming using BLIP captioning.

Generates SEO-friendly filenames from image content using
Salesforce's BLIP model. Supports custom term mappings
via a JSON configuration file.
"""

import os
import re
import sys
import io
import json
import logging
from PIL import Image

# Fix for transformers isatty error in GUI apps
if not hasattr(sys.stdout, 'isatty'):
    sys.stdout = io.StringIO()
if not hasattr(sys.stderr, 'isatty'):
    sys.stderr = io.StringIO()

# Suppress HuggingFace / transformers warnings
import warnings
warnings.filterwarnings("ignore")
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)

from transformers import BlipProcessor, BlipForConditionalGeneration

# Term mapping config file
TERM_MAP_FILE = "term_mappings.json"


class AutoRenamer:
    """AI-powered image renamer using BLIP captioning."""

    def __init__(self, log_callback=print):
        self.log = log_callback
        self.processor = None
        self.model = None
        self._model_loaded = False
        self.term_map = self._load_term_map()

    def _get_base_path(self):
        """Get project root — works for both dev and frozen exe."""
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def _load_term_map(self):
        """
        Load custom term mappings from JSON file.

        Looks for 'term_mappings.json' in the project root.
        Falls back to DEFAULT_TERM_MAP if file doesn't exist.

        JSON format:
            {
                "generic_term": "replacement_term",
                "cup": "kiddush-cup",
                "candle": "shabbat-candles"
            }
        """
        config_path = os.path.join(self._get_base_path(), TERM_MAP_FILE)
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    custom_map = json.load(f)
                self.log(f"Loaded {len(custom_map)} custom term mappings")
                return custom_map
        except (json.JSONDecodeError, OSError) as e:
            self.log(f"Warning: Could not load {TERM_MAP_FILE}: {e}")
        return {}

    def _get_model_path(self):
        """Get model path — use local bundled model if available, else HF hub."""
        local_path = os.path.join(self._get_base_path(), 'models', 'blip-captioning')
        if os.path.isdir(local_path):
            return local_path
        return "Salesforce/blip-image-captioning-base"

    def load_model(self):
        """Download and load the BLIP captioning model."""
        if self._model_loaded:
            return True

        try:
            model_path = self._get_model_path()
            is_local = not model_path.startswith("Salesforce/")
            self.log(f"Loading BLIP model{'(local)' if is_local else ''}...")

            self.processor = BlipProcessor.from_pretrained(
                model_path, use_fast=True
            )
            self.model = BlipForConditionalGeneration.from_pretrained(
                model_path
            )
            self._model_loaded = True
            self.log("Model loaded!")
            return True
        except Exception as e:
            self.log(f"Failed to load model: {e}")
            return False

    def clean_filename(self, text):
        """Convert a caption into a clean, SEO-friendly filename."""
        text = text.lower()

        # Apply custom term mappings
        for generic, specific in self.term_map.items():
            if generic in text:
                text = text.replace(generic, specific)

        # Remove common stopwords
        stopwords = {
            "a", "an", "the", "and", "with", "on", "of", "in", "it",
            "is", "are", "wearing", "carrying", "set", "colored",
            "includes", "pattern", "design", "background", "white",
        }

        words = re.findall(r'[a-z0-9]+', text)
        unique = []
        seen = set()

        for w in words:
            if w not in stopwords and w not in seen and len(w) > 1:
                unique.append(w)
                seen.add(w)

        return "-".join(unique[:8]) or "image"

    def process_file(self, file_path):
        """
        Generate an AI caption and rename the file.

        Returns:
            tuple: (success, new_filename, caption)
        """
        if not self.load_model():
            return False, "Model failed to load", ""

        try:
            with Image.open(file_path) as img:
                image = img.convert('RGB')
                inputs = self.processor(image, return_tensors="pt")
                out = self.model.generate(**inputs, max_new_tokens=30)
                caption = self.processor.decode(out[0], skip_special_tokens=True)

            new_base = self.clean_filename(caption)
            dir_name = os.path.dirname(file_path)
            ext = os.path.splitext(file_path)[1]

            new_name = f"{new_base}{ext}"
            new_path = os.path.join(dir_name, new_name)

            # Handle duplicate filenames
            counter = 1
            while os.path.exists(new_path) and new_path != file_path:
                new_name = f"{new_base}-{counter}{ext}"
                new_path = os.path.join(dir_name, new_name)
                counter += 1

            if new_path != file_path:
                os.rename(file_path, new_path)

            return True, new_name, caption

        except Exception as e:
            self.log(f"Rename error: {e}")
            return False, str(e), ""
