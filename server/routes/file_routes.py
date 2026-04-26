from __future__ import annotations

import asyncio
import os
from fastapi import APIRouter, HTTPException

from srt_summarizer.processing.file_scanner import (
    normalize_selected_files,
    scan_supported_files,
    scan_video_files,
)
from srt_summarizer.processing.lesson_pairing import (
    normalize_video_files,
    pair_lessons,
)

from server.models.schemas import BrowseResponse, FilePathsRequest, FileTreeResponse, ScanRequest
from server.session import get_session

router = APIRouter(prefix="/api", tags=["files"])


def _open_native_folder_picker(initial_dir: str) -> str:
    """Open the native Windows folder picker dialog and return the selected path."""
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    try:
        path = filedialog.askdirectory(initialdir=initial_dir, title="选择目录")
    finally:
        root.destroy()
    return path if path else ""


def _open_native_file_picker(initial_dir: str, title: str, exts: list[str]) -> list[str]:
    """Open the native Windows file picker dialog and return selected file paths."""
    import tkinter as tk
    from tkinter import filedialog

    ft = [(f"{title} ({' '.join(exts)})", " ".join(exts)), ("所有文件", "*.*")] if exts else [("所有文件", "*.*")]

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    try:
        paths = filedialog.askopenfilenames(initialdir=initial_dir, title=title, filetypes=ft)
    finally:
        root.destroy()
    return list(paths) if paths else []


@router.post("/pick/folder")
async def pick_folder(initial_dir: str = ""):
    if not initial_dir or not os.path.isdir(initial_dir):
        initial_dir = os.path.join(os.path.expanduser("~"), "Desktop")
        if not os.path.isdir(initial_dir):
            initial_dir = os.path.expanduser("~")
    # Tkinter MUST run on the main thread — cannot use asyncio.to_thread
    path = _open_native_folder_picker(initial_dir)
    return {"path": path}


@router.post("/pick/files")
async def pick_files(file_type: str = "transcripts", initial_dir: str = ""):
    if not initial_dir or not os.path.isdir(initial_dir):
        initial_dir = os.path.join(os.path.expanduser("~"), "Desktop")
        if not os.path.isdir(initial_dir):
            initial_dir = os.path.expanduser("~")

    if file_type == "videos":
        title = "选择视频文件"
        exts = ["*.mp4", "*.mkv", "*.avi", "*.mov", "*.webm", "*.flv", "*.wmv"]
    elif file_type == "notes":
        title = "选择往期笔记"
        exts = ["*.md", "*.txt"]
    else:
        title = "选择字幕文件"
        exts = ["*.srt", "*.txt", "*.md"]

    # Tkinter MUST run on the main thread — cannot use asyncio.to_thread
    paths = _open_native_file_picker(initial_dir, title, exts)
    return {"paths": paths}


@router.post("/files/scan")
async def scan_directory(body: ScanRequest):
    directory = body.directory.strip()
    if not directory or not os.path.isdir(directory):
        raise HTTPException(400, "目录不存在或不可访问")

    session = get_session()
    session.reset_files()

    def _scan():
        session.transcript_files = scan_supported_files(directory)
        session.video_files = scan_video_files(directory)
        return pair_lessons(session.transcript_files, session.video_files)

    lessons = await asyncio.to_thread(_scan)
    return {
        "transcript_count": len(session.transcript_files),
        "video_count": len(session.video_files),
        "lesson_count": len(lessons),
        "matched_count": sum(1 for l in lessons if l.video_path),
    }


@router.get("/files/tree", response_model=FileTreeResponse)
async def get_file_tree():
    session = get_session()

    def _build():
        lessons = pair_lessons(session.transcript_files, session.video_files)
        lesson_dicts = []
        for lesson in lessons:
            lesson_dicts.append({
                "transcript_path": lesson.transcript_path,
                "video_path": lesson.video_path or "",
                "source_label": lesson.source_label or "",
                "status": "待处理",
            })
        return FileTreeResponse(
            transcripts=session.transcript_files,
            videos=session.video_files,
            notes=session.prior_note_files,
            lessons=lesson_dicts,
            stat=len(lesson_dicts),
            extra_stat=f"字幕 {len(session.transcript_files)} / 视频 {len(session.video_files)} / 往期笔记 {len(session.prior_note_files)}",
        )

    return await asyncio.to_thread(_build)


@router.post("/files/transcripts")
async def add_transcripts(body: FilePathsRequest):
    session = get_session()
    normalized = normalize_selected_files(body.paths)
    for path in normalized:
        if path not in session.transcript_files:
            session.transcript_files.append(path)
    return {"added": len(normalized), "skipped": len(body.paths) - len(normalized)}


@router.post("/files/videos")
async def add_videos(body: FilePathsRequest):
    session = get_session()
    normalized = normalize_video_files(body.paths)
    for path in normalized:
        if path not in session.video_files:
            session.video_files.append(path)
    return {"added": len(normalized)}


@router.post("/files/notes")
async def add_notes(body: FilePathsRequest):
    session = get_session()
    added = 0
    for path in body.paths:
        if os.path.isfile(path) and path not in session.prior_note_files:
            session.prior_note_files.append(path)
            added += 1
    return {"added": added}


@router.delete("/files/transcripts")
async def remove_transcripts(body: FilePathsRequest):
    session = get_session()
    removed = 0
    for path in body.paths:
        if path in session.transcript_files:
            session.transcript_files.remove(path)
            removed += 1
    return {"removed": removed}


@router.get("/files/browse", response_model=BrowseResponse)
async def browse_directory(path: str = ""):
    def _browse():
        p = path
        if not p or not os.path.exists(p):
            p = "C:\\" if os.name == "nt" else "/"
        if not os.path.isdir(p):
            p = os.path.dirname(p) or p

        entries = []
        try:
            for name in sorted(os.listdir(p)):
                full = os.path.join(p, name)
                is_dir = os.path.isdir(full)
                try:
                    size = os.path.getsize(full) if not is_dir else 0
                except OSError:
                    size = 0
                entries.append({
                    "name": name,
                    "path": full,
                    "is_dir": is_dir,
                    "size": size,
                })
        except PermissionError:
            pass
        return BrowseResponse(parent=p, entries=entries)

    return await asyncio.to_thread(_browse)
