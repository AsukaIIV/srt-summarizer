import os

from srt_summarizer.constants import SUPPORTED_EXT, SUPPORTED_VIDEO_EXT


def _scan_files_by_extensions(directory: str, extensions: tuple[str, ...]) -> list[str]:
    files_found: list[str] = []
    seen: set[str] = set()
    for root, _, files in os.walk(directory):
        for fn in sorted(files):
            path = os.path.join(root, fn)
            if not fn.lower().endswith(extensions):
                continue
            if path in seen:
                continue
            seen.add(path)
            files_found.append(path)
    return files_found


def scan_supported_files(directory: str) -> list[str]:
    return _scan_files_by_extensions(directory, SUPPORTED_EXT)


def scan_video_files(directory: str) -> list[str]:
    return _scan_files_by_extensions(directory, SUPPORTED_VIDEO_EXT)


def normalize_selected_files(paths) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for path in paths:
        if not path.lower().endswith(SUPPORTED_EXT):
            continue
        if path in seen:
            continue
        seen.add(path)
        normalized.append(path)
    return normalized


def format_file_size(path: str) -> str:
    try:
        size = os.path.getsize(path)
    except OSError:
        return "读取失败"
    if size < 1_048_576:
        return f"{size/1024:.1f} KB"
    return f"{size/1_048_576:.1f} MB"
