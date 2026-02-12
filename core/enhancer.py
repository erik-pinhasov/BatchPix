"""
Image enhancement using Real-ESRGAN.
"""

import os
import subprocess
import sys
from pathlib import Path

MODELS_CONFIG = {
    "x4-quality": {
        "algo": "realesrgan-x4plus",
        "scale": 4,
        "desc": "Best Quality (4x)"
    },
    "x4-fast": {
        "algo": "realesrgan-x4plus-anime",
        "scale": 4,
        "desc": "Fast (4x)"
    },
    "x2-quality": {
        "algo": "realesrgan-x4plus",
        "scale": 2,
        "desc": "Quality (2x)"
    },
}


def get_base_path():
    """Get base path for resources - works for both dev and exe."""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent.parent


class ImageEnhancer:
    def __init__(self, log_callback=print):
        self.log = log_callback
        self.base_path = get_base_path()
        self.realesrgan_bin = self.base_path / "realesrgan" / "realesrgan-ncnn-vulkan.exe"

    def get_model_names(self):
        return list(MODELS_CONFIG.keys())

    def get_model_descriptions(self):
        return {k: v["desc"] for k, v in MODELS_CONFIG.items()}

    def process_image(self, input_path, output_path, model_key):
        """Upscale image using Real-ESRGAN."""
        conf = MODELS_CONFIG.get(model_key)
        if not conf:
            return False, f"Unknown model: {model_key}"

        # Check if exe exists
        if not self.realesrgan_bin.exists():
            self.log(f"Real-ESRGAN not found at: {self.realesrgan_bin}")
            return False, "Real-ESRGAN not found"

        cmd = [
            str(self.realesrgan_bin),
            "-i", str(input_path),
            "-o", str(output_path),
            "-n", conf["algo"],
            "-s", str(conf["scale"]),
            "-g", "0",
            "-t", "256",
            "-j", "2:2:2"
        ]

        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        try:
            self.log(f"Running: {os.path.basename(input_path)}")
            result = subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                startupinfo=startupinfo,
                cwd=str(self.realesrgan_bin.parent)  # Run from realesrgan folder
            )
            if os.path.exists(output_path):
                return True, "Success"
            else:
                return False, "Output file not created"
        except FileNotFoundError:
            return False, "Real-ESRGAN executable not found"
        except subprocess.CalledProcessError as e:
            err = e.stderr.decode(errors='ignore') if e.stderr else str(e)
            self.log(f"Error: {err}")
            return False, err