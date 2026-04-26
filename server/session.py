from __future__ import annotations

import asyncio
from dataclasses import dataclass, field


@dataclass
class RunState:
    run_id: str
    queue: asyncio.Queue
    cancel_event: asyncio.Event = field(default_factory=asyncio.Event)
    running: bool = True


class SessionStore:
    """Server-side equivalent of the Tkinter App instance variables."""

    def __init__(self):
        self.transcript_files: list[str] = []
        self.video_files: list[str] = []
        self.prior_note_files: list[str] = []
        self.output_dir: str = ""
        self.save_to_source: bool = False
        self.course_name: str = ""
        self.requirements_text: str = ""
        self.current_run: RunState | None = None

    def reset_files(self):
        self.transcript_files = []
        self.video_files = []
        self.prior_note_files = []


_session_store: SessionStore | None = None


def get_session() -> SessionStore:
    global _session_store
    if _session_store is None:
        _session_store = SessionStore()
    return _session_store
