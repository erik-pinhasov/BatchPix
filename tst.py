from PIL import Image, ImageEnhance
import sys
from pathlib import Path

SUPPORTED = {'.png', '.jpg', '.jpeg', '.webp'}


def process(src, canvas_size=200, padding=2):
    img = Image.open(src).convert('RGBA')

    # Crop to content (trim transparent edges)
    bbox = img.split()[3].getbbox()
    if bbox:
        img = img.crop(bbox)

    # Scale to max fit within canvas minus padding
    target = canvas_size - padding * 2
    w, h = img.size
    scale = target / max(w, h)
    nw, nh = int(w * scale), int(h * scale)
    img = img.resize((nw, nh), Image.LANCZOS)

    # Center on transparent canvas
    canvas = Image.new('RGBA', (canvas_size, canvas_size), (0, 0, 0, 0))
    canvas.paste(img, ((canvas_size - nw) // 2, (canvas_size - nh) // 2), img)
    return canvas


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Resize and center icons on square canvas')
    parser.add_argument('input_folder')
    parser.add_argument('--size', type=int, default=200, help='Canvas size px (default: 200)')
    parser.add_argument('--padding', type=int, default=8, help='Padding around icon px (default: 8)')
    parser.add_argument('--format', type=str, default='webp', choices=['webp', 'png'])
    parser.add_argument('--quality', type=int, default=90)
    args = parser.parse_args()

    input_dir = Path(args.input_folder)
    output_dir = input_dir / 'processed'
    output_dir.mkdir(exist_ok=True)

    files = sorted(f for f in input_dir.iterdir() if f.suffix.lower() in SUPPORTED)
    if not files:
        print(f"No images found in {input_dir}")
        sys.exit(1)

    print(f"Processing {len(files)} images -> {output_dir}")

    for f in files:
        try:
            result = process(f, args.size, args.padding)
            out = output_dir / f"{f.stem}.{args.format}"
            if args.format == 'webp':
                result.save(out, 'WEBP', quality=args.quality, method=6)
            else:
                result.save(out, 'PNG', optimize=True)
            print(f"  OK  {f.name}")
        except Exception as e:
            print(f"  ERR {f.name}: {e}")

    print("Done!")

if __name__ == '__main__':
    main()