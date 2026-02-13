# BatchPix

A desktop application for batch processing images — enhance, resize, crop, convert, strip metadata, rename, and tag copyright in a single pipeline.

<div align="center">

![Python](https://img.shields.io/badge/Python-3.9+-blue)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)
![License](https://img.shields.io/badge/License-MIT-green)

```markdown
The UI was created entirely using Google Antigravity with the Gemini 3 Pro model.
```

<img src="screenshot.png" alt="screenshot" width="450"/>

</div>

## Features

| Feature | Description |
|---------|-------------|
| **AI Enhancement** | Upscale images 2×/4× using Real-ESRGAN neural network |
| **Smart Resize** | Presets: thumbnail, small, medium, large, HD, 4K, or custom dimensions |
| **Smart Crop** | Automatically detect and remove empty, transparent, or solid-color borders |
| **WebP Conversion** | Convert to WebP format for significantly smaller file sizes |
| **Metadata Strip** | Remove GPS coordinates, EXIF tags, and camera data for privacy |
| **AI Rename** | Generate descriptive, SEO-friendly filenames using BLIP image captioning |
| **Copyright Tag** | Embed copyright and artist metadata into image EXIF data (lossless) |

### Supported Formats

`JPG` · `PNG` · `WebP` · `AVIF` · `TIFF` · `BMP` · `GIF` · `ICO` · `TGA` · `SVG`

> SVG files are automatically rasterized to high-resolution PNG (2048px) before processing.

---

## Installation

### Option 1: Windows Installer (Recommended)

Download `BatchPix_Setup.exe` from the [Releases](../../releases) page and run it.  
No Python, dependencies, or configuration required — everything is bundled into the installer.

### Option 2: Run from Source

**Prerequisites:** Python 3.9+ and pip.

```bash
# Clone the repository
git clone https://github.com/erik-pinhasov/BatchPix.git
cd BatchPix

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Launch
python main.py
```

### External Dependencies

| Dependency | Required For | How to Get |
|-----------|-------------|------------|
| [Real-ESRGAN portable](https://github.com/xinntao/Real-ESRGAN/releases/tag/v0.2.5.0) | AI Enhancement only | Download the Windows binary and extract into a `realesrgan/` folder in the project root |
| [GTK3 Runtime](https://github.com/nickvdp/gtk3-win/releases) | SVG support only | Required by CairoSVG on Windows — install if processing SVG files |

> **Note:** FFmpeg is **not** required. All image processing uses Pillow and native binaries.

---

## Usage

1. **Select Input** — Choose a folder or pick individual files
2. **Set Output** — Specify where processed images should be saved
3. **Choose Actions** — Check the processing steps you want to apply
4. **Configure** — Adjust settings for each action (resize preset, enhancement model, etc.)
5. **Click Start** — The pipeline runs, and progress is shown in the log panel

### Processing Pipeline

When multiple actions are selected, they always execute in this fixed order:

```
Enhance → Resize → Smart Crop → WebP Convert → Strip Metadata → AI Rename → Copyright
```

Each step receives the output of the previous step. For example, if you select Enhance + Resize + WebP, the image is upscaled first, then resized, then converted to WebP.

---

## AI Models

### BLIP — Image Captioning (AI Rename)

- **Model:** [`Salesforce/blip-image-captioning-base`](https://huggingface.co/Salesforce/blip-image-captioning-base)
- **Purpose:** Generates natural-language descriptions of images, which are then cleaned into SEO-friendly filenames
- **Size:** ~990 MB (downloaded automatically on first use)
- **Runs on:** CPU (no GPU required)

### Real-ESRGAN — Image Upscaling (AI Enhancement)

- **Models:** [`realesrgan-x4plus`](https://github.com/xinntao/Real-ESRGAN) (quality), [`realesrgan-x4plus-anime`](https://github.com/xinntao/Real-ESRGAN) (fast/anime)
- **Purpose:** Neural network super-resolution — upscales images 2× or 4× while preserving detail
- **Runs via:** Vulkan GPU compute (the portable binary handles this automatically)

---

## Configuration

### Custom Term Mappings (AI Rename)

The AI renamer replaces generic terms detected by BLIP with domain-specific names. Create a `term_mappings.json` file in the project root:

```json
{
    "cup": "kiddush-cup",
    "candle": "shabbat-candles",
    "scroll": "megillah",
    "book": "siddur"
}
```

If no `term_mappings.json` exists, no term replacements are applied. The renamer still generates clean filenames from BLIP captions — the mappings just let you customize vocabulary.

### Copyright Settings

Copyright and artist fields are saved automatically to `.copyright_config.json` and persist between sessions.

---

## Building from Source

### Step 1: Build the Executable

```bash
python build_exe.py
```

This uses [PyInstaller](https://pyinstaller.org/) to bundle Python, all pip dependencies, assets, and the Real-ESRGAN engine into a standalone folder at `dist/BatchPix/`.

### Step 2: Build the Installer (optional)

Install [Inno Setup 6](https://jrsoftware.org/isdl.php) (free), then either:

- Run `python build_exe.py` again — it auto-detects Inno Setup and compiles the installer
- Or open `installer.iss` in Inno Setup and press **Compile** (F9)

Output: `installer_output/BatchPix_Setup.exe`

The installer registers the app in Windows Add/Remove Programs, creates Start Menu shortcuts, and optionally adds a desktop shortcut.

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `torch` | ≥ 2.6 | PyTorch — tensor computation for BLIP model |
| `torchvision` | ≥ 0.21 | Image transforms for BLIP preprocessing |
| `transformers` | ≥ 4.36 | Hugging Face — loads BLIP model |
| `Pillow` | ≥ 10.0 | Core image I/O, resize, crop, format conversion |
| `piexif` | ≥ 1.1 | Lossless EXIF read/write for copyright tagging |
| `opencv-contrib-python` | ≥ 4.8 | Smart crop border detection |
| `numpy` | ≥ 1.22 | Array operations for image processing |
| `requests` | ≥ 2.28 | Model download from Hugging Face Hub |
| `cairosvg` | ≥ 2.5 | SVG → PNG rasterization |

## License

MIT License — see [LICENSE](LICENSE)