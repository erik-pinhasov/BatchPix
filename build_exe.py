"""
Build script for BatchPix.
Creates a standalone .exe with all required files.

Usage:
    python build_exe.py

Output:
    dist/BatchPix/
        BatchPix.exe
        realesrgan/
        assets/
"""

import subprocess
import sys
import os
import shutil


def main():
    print("=" * 50)
    print("Building BatchPix")
    print("=" * 50)
    
    # Check PyInstaller
    try:
        import PyInstaller
        print("✓ PyInstaller found")
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # Build command (onedir for easier distribution with assets)
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onedir",
        "--windowed",
        "--clean",
        "--name", "BatchPix",
    ]
    
    # Add hidden imports for lazy-loaded modules
    cmd.extend([
        "--hidden-import", "PIL",
        "--hidden-import", "cairosvg",
        "--hidden-import", "core.enhancer",
        "--hidden-import", "core.resizer",
        "--hidden-import", "core.metadata_stripper",
        "--hidden-import", "core.smart_crop",
        "--hidden-import", "core.copyrights",
        "--hidden-import", "core.renamer",
    ])
    
    cmd.append("main.py")
    
    print("\nBuilding exe... (this may take a few minutes)")
    result = subprocess.run(cmd)
    
    if result.returncode != 0:
        print("\n✗ Build failed")
        return 1
    
    # Copy required folders to dist
    dist_dir = os.path.join("dist", "BatchPix")
    
    # Copy realesrgan folder
    if os.path.exists("realesrgan"):
        dst = os.path.join(dist_dir, "realesrgan")
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.copytree("realesrgan", dst)
        print("✓ Copied realesrgan/")
    else:
        print("⚠ Warning: realesrgan/ folder not found")
    
    print("\n" + "=" * 50)
    print("✓ BUILD SUCCESSFUL!")
    print("=" * 50)
    print(f"\nOutput: {os.path.abspath(dist_dir)}/")
    
    # Build installer with Inno Setup (if available)
    iss_file = "installer.iss"
    iscc_paths = [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
    ]
    
    iscc = None
    for path in iscc_paths:
        if os.path.exists(path):
            iscc = path
            break
    
    if os.path.exists(iss_file) and iscc:
        print("\n" + "=" * 50)
        print("Building Windows Installer...")
        print("=" * 50)
        result = subprocess.run([iscc, iss_file])
        if result.returncode == 0:
            print("✓ Installer created in installer_output/")
        else:
            print("✗ Installer build failed")
    elif os.path.exists(iss_file):
        print("\n⚠ Inno Setup not found — skipping installer build.")
        print("  Install from: https://jrsoftware.org/isinfo.php")
    
    print("\nTo distribute: Upload the installer from installer_output/")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
