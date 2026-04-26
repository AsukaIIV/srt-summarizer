import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path


REQUIRED_PACKAGES = (
    ("requests", "requests"),
    ("cv2", "opencv-python"),
    ("ffmpeg", "ffmpeg-python"),
)


_FFMPEG_ENV_VARS = (
    "SRT_SUMMARIZER_FFMPEG",
    "FFMPEG_PATH",
)


def is_frozen_app() -> bool:
    return bool(getattr(sys, "frozen", False))


def get_resource_base_dir() -> Path:
    if is_frozen_app():
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    return Path(__file__).resolve().parents[1]


def get_app_base_dir() -> Path:
    if is_frozen_app():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def get_bundled_ffmpeg_path() -> str | None:
    candidate = get_resource_base_dir() / "ffmpeg" / "ffmpeg.exe"
    if candidate.is_file():
        return str(candidate)
    return None


def resolve_ffmpeg_executable() -> str | None:
    bundled = get_bundled_ffmpeg_path()
    if bundled:
        return bundled
    for env_name in _FFMPEG_ENV_VARS:
        env_value = os.environ.get(env_name, "").strip()
        if env_value and Path(env_value).is_file():
            return env_value
    return shutil.which("ffmpeg")


def describe_ffmpeg_source() -> str:
    path = resolve_ffmpeg_executable()
    if not path:
        return "missing"
    bundled = get_bundled_ffmpeg_path()
    if bundled and Path(path).resolve() == Path(bundled).resolve():
        return "bundled"
    return "system"


def has_python_module(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def ensure_python_package(module_name: str, package_name: str) -> None:
    if has_python_module(module_name):
        return
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
    except (subprocess.CalledProcessError, OSError) as e:
        raise RuntimeError(f"自动安装依赖《{package_name}》失败：{e}。请手动执行：pip install {package_name}") from e


def ensure_runtime_dependencies() -> list[str]:
    installed: list[str] = []
    missing: list[str] = []
    for module_name, package_name in REQUIRED_PACKAGES:
        if has_python_module(module_name):
            continue
        if is_frozen_app():
            missing.append(package_name)
            continue
        ensure_python_package(module_name, package_name)
        installed.append(package_name)
    if missing:
        raise RuntimeError(f"打包版缺少运行依赖：{', '.join(missing)}")
    return installed


def has_opencv() -> bool:
    return has_python_module("cv2")


def has_ffmpeg() -> bool:
    return resolve_ffmpeg_executable() is not None


def check_video_dependencies() -> dict[str, bool]:
    return {
        "opencv": has_opencv(),
        "ffmpeg": has_ffmpeg(),
    }
