import subprocess
import sys
import os
import shutil


def create_spec_file():
    """Create BatchPix.spec file with proper configuration."""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

datas = [
    ('app/assets/icon.ico', 'app/assets'),
    ('app/assets', 'app/assets'),
]

hiddenimports = [
    'PIL._tkinter_finder',
    'customtkinter',
    'PIL',
    'cairosvg',
    'core.enhancer',
    'core.resizer',
    'core.metadata_stripper',
    'core.smart_crop',
    'core.copyrights',
    'core.renamer',
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='BatchPix',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='app/assets/icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='BatchPix',
)
'''
    
    with open('BatchPix.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    print("✓ Created BatchPix.spec")


def copy_extra_folders():
    """Copy folders that PyInstaller doesn't include automatically."""
    dist_dir = os.path.join("dist", "BatchPix")
    
    folders_to_copy = [
        ('realesrgan', 'realesrgan'),
        ('app/assets', 'app/assets'),
    ]
    
    for src_folder, dst_name in folders_to_copy:
        if os.path.exists(src_folder):
            dst = os.path.join(dist_dir, dst_name)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree(src_folder, dst)
            print(f"✓ Copied {src_folder}/ to dist/BatchPix/{dst_name}/")
        else:
            print(f"⚠ Warning: {src_folder}/ not found, skipping")


def verify_build(dist_dir):
    """Verify the build output."""
    print("\n" + "=" * 50)
    print("Verifying build contents...")
    print("=" * 50)
    
    required_files = [
        'BatchPix.exe',
        '_internal',
    ]
    
    optional_folders = [
        'realesrgan',
        'app/assets',
    ]
    
    all_good = True
    
    for item in required_files:
        path = os.path.join(dist_dir, item)
        if os.path.exists(path):
            print(f"✓ Found: {item}")
        else:
            print(f"✗ MISSING: {item}")
            all_good = False
    
    for item in optional_folders:
        path = os.path.join(dist_dir, item)
        if os.path.exists(path):
            print(f"✓ Found: {item}")
        else:
            print(f"⚠ Optional missing: {item}")
    
    return all_good


def main():
    print("=" * 50)
    print("Building BatchPix")
    print("=" * 50)
    
    try:
        import PyInstaller
        print("✓ PyInstaller found")
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    print("\nCleaning previous builds...")
    for folder in ["build", "dist"]:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            print(f"✓ Removed {folder}/")
    
    if os.path.exists("BatchPix.spec"):
        os.remove("BatchPix.spec")
        print("✓ Removed old BatchPix.spec")

    create_spec_file()

    print("\nBuilding exe... (this may take a few minutes)")
    cmd = [sys.executable, "-m", "PyInstaller", "--clean", "BatchPix.spec"]
    result = subprocess.run(cmd)
    
    if result.returncode != 0:
        print("\n✗ Build failed")
        return 1
    
    dist_dir = os.path.join("dist", "BatchPix")
    if not os.path.exists(dist_dir):
        print(f"\n✗ Build failed: {dist_dir} not found")
        return 1
    
    exe_path = os.path.join(dist_dir, "BatchPix.exe")
    if not os.path.exists(exe_path):
        print(f"\n✗ BatchPix.exe not found at {exe_path}")
        return 1
    
    print("\nCopying additional folders...")
    copy_extra_folders()
    
    if not verify_build(dist_dir):
        print("\n⚠ Build verification found some issues")
    
    print("\n" + "=" * 50)
    print("✓ BUILD SUCCESSFUL!")
    print("=" * 50)
    print(f"\nOutput: {os.path.abspath(dist_dir)}/")
    print(f"Executable: {os.path.abspath(exe_path)}")
    
    iss_file = "installer.iss"
    iscc_paths = [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
        r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
        r"C:\Program Files\Inno Setup 5\ISCC.exe",
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
        
        os.makedirs("installer_output", exist_ok=True)
        
        result = subprocess.run([iscc, iss_file])
        if result.returncode == 0:
            print("\n✓ Installer created successfully!")
            
            installer_dir = "installer_output"
            if os.path.exists(installer_dir):
                installers = [f for f in os.listdir(installer_dir) if f.endswith('.exe')]
                if installers:
                    installer_path = os.path.join(installer_dir, installers[0])
                    print(f"✓ Installer: {os.path.abspath(installer_path)}")
                    print(f"   Size: {os.path.getsize(installer_path) / (1024*1024):.1f} MB")
        else:
            print("✗ Installer build failed")
    elif os.path.exists(iss_file):
        print("\n⚠ Inno Setup not found — skipping installer build.")
        print("  Install from: https://jrsoftware.org/isinfo.php")
    else:
        print(f"\n⚠ {iss_file} not found — skipping installer build.")
    
    print("\n" + "=" * 50)
    print("DISTRIBUTION")
    print("=" * 50)
    print("To distribute:")
    print("  • Upload the installer from installer_output/")
    print("  • Or zip the entire dist/BatchPix/ folder")
    print("\nDone!")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())