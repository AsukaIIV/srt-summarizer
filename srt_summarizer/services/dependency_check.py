import importlib.util
import shutil
import subprocess
import sys


REQUIRED_PACKAGES = (
    ("requests", "requests"),
    ("cv2", "opencv-python"),
    ("ffmpeg", "ffmpeg-python"),
)


def has_python_module(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def ensure_python_package(module_name: str, package_name: str) -> None:
    if has_python_module(module_name):
        return
    subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])


def ensure_runtime_dependencies() -> list[str]:
    installed: list[str] = []
    for module_name, package_name in REQUIRED_PACKAGES:
        if not has_python_module(module_name):
            ensure_python_package(module_name, package_name)
            installed.append(package_name)
    return installed


def has_opencv() -> bool:
    return has_python_module("cv2")


def has_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None


def check_video_dependencies() -> dict[str, bool]:
    return {
        "opencv": has_opencv(),
        "ffmpeg": has_ffmpeg(),
    }
