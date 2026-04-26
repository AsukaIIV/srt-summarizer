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
APP_NAME = f"srt-summarizer-v{APP_VERSION}"

# ---- bundled assets --------------------------------------------------------
FFMPEG_SOURCE = ROOT / "vendor" / "ffmpeg" / "win64" / "ffmpeg.exe"
FONT_SOURCE = ROOT / "HarmonyOS_Sans_SC_Medium.ttf"

if not FFMPEG_SOURCE.is_file():
    raise FileNotFoundError(f"Bundled ffmpeg not found: {FFMPEG_SOURCE}")
if not FONT_SOURCE.is_file():
    raise FileNotFoundError(f"Bundled font not found: {FONT_SOURCE}")

# ---- OpenCV hooks ----------------------------------------------------------
cv2_hiddenimports = collect_submodules("cv2")
cv2_binaries = collect_dynamic_libs("cv2")
cv2_datas = collect_data_files("cv2")

# ---- collect all bundled data ----------------------------------------------
datas = []
datas += cv2_datas
datas += [(str(FFMPEG_SOURCE), "ffmpeg")]
datas += [(str(FONT_SOURCE), ".")]
# Jinja2 templates & static assets
datas += [(str(ROOT / "templates"), "templates")]
datas += [(str(ROOT / "static"), "static")]
# System prompt shipped next to config.py
prompts_dir = ROOT / "srt_summarizer" / "prompts"
datas += [(str(prompts_dir), "srt_summarizer/prompts")]

# ---- hidden imports (web stack) --------------------------------------------
web_hiddenimports = [
    "server",
    "server.app",
    "server.session",
    "server.models",
    "server.models.schemas",
    "server.routes",
    "server.routes.config_routes",
    "server.routes.file_routes",
    "server.routes.run_routes",
    "uvicorn.loops.auto",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.logging",
    "uvicorn.lifespan.on",
    "jinja2.ext",
    "starlette",
    "fastapi",
    "aiofiles",
]

hiddenimports = cv2_hiddenimports + web_hiddenimports

# ---- analysis --------------------------------------------------------------
a = Analysis(
    [str(ROOT / "web_main.py")],
    pathex=[str(ROOT)],
    binaries=cv2_binaries,
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

# ---- single-file executable ------------------------------------------------
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
    console=True,
    disable_windowed_traceback=False,
    version=str(ROOT / "build" / "windows" / "file_version_info.txt"),
)
