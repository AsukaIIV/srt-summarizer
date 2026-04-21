# -*- mode: python ; coding: utf-8 -*-
import re
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_submodules

ROOT = Path(SPECPATH)
VERSION_INFO_PATH = ROOT / "build" / "windows" / "version_info.txt"
version_info_text = VERSION_INFO_PATH.read_text(encoding="utf-8")
version_match = re.search(r"APP_VERSION\s*=\s*['\"]([^'\"]+)['\"]", version_info_text)
if not version_match:
    raise ValueError(f"APP_VERSION not found in {VERSION_INFO_PATH}")
APP_VERSION = version_match.group(1)
APP_NAME = f"SRT-SUMMARIZER-v{APP_VERSION}"
FFMPEG_SOURCE = ROOT / "vendor" / "ffmpeg" / "win64" / "ffmpeg.exe"
FONT_SOURCE = ROOT / "HarmonyOS_Sans_SC_Medium.ttf"
if not FFMPEG_SOURCE.is_file():
    raise FileNotFoundError(f"Bundled ffmpeg not found: {FFMPEG_SOURCE}")
if not FONT_SOURCE.is_file():
    raise FileNotFoundError(f"Bundled font not found: {FONT_SOURCE}")

hiddenimports = collect_submodules("cv2")
binaries = collect_dynamic_libs("cv2")
datas = collect_data_files("cv2")
datas += [(str(FFMPEG_SOURCE), "ffmpeg")]
datas += [(str(FONT_SOURCE), ".")]


a = Analysis(
    [str(ROOT / "app.py")],
    pathex=[str(ROOT)],
    binaries=binaries,
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
    a.binaries,
    a.datas,
    [],
    exclude_binaries=False,
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    version=str(ROOT / "build" / "windows" / "version_info.txt"),
)
