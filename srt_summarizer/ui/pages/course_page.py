import tkinter as tk
from tkinter import ttk

from srt_summarizer.constants import C, UI_METRICS
from srt_summarizer.ui.widgets import ScrollableFrame, SectionCard


FONT = UI_METRICS["font"]
SPACE = UI_METRICS["space"]


class CoursePage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, style="Page.TFrame")
        self.app = app
        self._build_ui()

    def _on_requirements_mousewheel(self, event):
        if event.delta:
            step = -1 * int(event.delta / 120) if event.delta else 0
        elif getattr(event, "num", None) == 4:
            step = -1
        elif getattr(event, "num", None) == 5:
            step = 1
        else:
            step = 0
        if step:
            self.app._requirements_text.yview_scroll(step, "units")
            return "break"
        return None

    def _make_entry_shell(self, parent, textvariable):
        shell = tk.Frame(parent, bg=C["field"], highlightthickness=1, highlightbackground=C["border_subtle"], highlightcolor=C["field_focus"])
        entry = tk.Entry(
            shell,
            textvariable=textvariable,
            bg=C["field"],
            fg=C["fg"],
            insertbackground=C["fg"],
            relief="flat",
            bd=0,
            font=("Segoe UI", FONT["body"]),
        )
        entry.pack(fill="both", expand=True, padx=UI_METRICS["input"]["pad_x"], pady=UI_METRICS["input"]["pad_y"])
        entry.bind("<FocusIn>", lambda _event, target=shell: target.config(highlightbackground=C["field_focus"]))
        entry.bind("<FocusOut>", lambda _event, target=shell: target.config(highlightbackground=C["border_subtle"]))
        return shell, entry

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        scroll = ScrollableFrame(self, bg=C["bg"])
        scroll.grid(row=0, column=0, sticky="nsew")
        self._scroll = scroll
        body = scroll.content
        body.columnconfigure(0, weight=1)

        header = tk.Frame(body, bg=C["bg"])
        header.grid(row=0, column=0, sticky="ew", padx=SPACE["outer"], pady=(SPACE["section"], 0))
        tk.Label(header, text="课程设置", bg=C["bg"], fg=C["fg"], font=("Segoe UI", FONT["title"], "bold")).pack(anchor="w")

        course_card = SectionCard(body, "课程整理设置")
        course_card.grid(row=1, column=0, sticky="nsew", padx=SPACE["outer"], pady=(SPACE["section"], SPACE["section"]))
        course_card.body.columnconfigure(0, weight=1)
        tk.Label(course_card.body, text="课程名称", bg=C["panel"], fg=C["fg2"], font=("Segoe UI", FONT["label"])).grid(row=0, column=0, sticky="w")
        course_name_shell, course_name_entry = self._make_entry_shell(course_card.body, self.app._course_name_var)
        course_name_shell.grid(row=1, column=0, sticky="ew", pady=(SPACE["inline"], 0))
        tk.Label(course_card.body, text="留空也可以，不影响生成结构", bg=C["panel"], fg=C["fg3"], font=("Segoe UI", FONT["meta"])).grid(row=2, column=0, sticky="w", pady=(SPACE["compact"], 0))
        tk.Label(course_card.body, text="课程总体要求", bg=C["panel"], fg=C["fg2"], font=("Segoe UI", FONT["label"])).grid(row=3, column=0, sticky="w", pady=(SPACE["section"], 0))
        req_shell = tk.Frame(course_card.body, bg=C["field"], highlightthickness=1, highlightbackground=C["border_subtle"])
        req_shell.grid(row=4, column=0, sticky="nsew", pady=(SPACE["inline"], 0))
        course_card.body.rowconfigure(4, weight=1)
        self.app._requirements_text = tk.Text(req_shell, height=14, bg=C["field"], fg=C["fg"], insertbackground=C["fg"], relief="flat", bd=0, font=("Segoe UI", FONT["body"]), wrap="word")
        self.app._requirements_text.pack(fill="both", expand=True, padx=UI_METRICS["input"]["pad_x"], pady=UI_METRICS["input"]["pad_y"])
        self.app._requirements_text.bind("<MouseWheel>", self._on_requirements_mousewheel, add="+")
        self.app._requirements_text.bind("<Button-4>", self._on_requirements_mousewheel, add="+")
        self.app._requirements_text.bind("<Button-5>", self._on_requirements_mousewheel, add="+")
        tk.Label(course_card.body, text="可留空，主要用于补充课程背景或你希望强调的整理重点", bg=C["panel"], fg=C["fg3"], font=("Segoe UI", FONT["meta"])).grid(row=5, column=0, sticky="w", pady=(SPACE["compact"], 0))

        self._scroll.register_mousewheel_targets(
            header,
            course_card,
            course_card.body,
            course_name_shell,
            course_name_entry,
            req_shell,
            self.app._requirements_text,
        )
        self._scroll.suspend_mousewheel_targets(self.app._requirements_text)

    def apply_layout_mode(self, compact: bool):
        self.app._requirements_text.configure(font=("Segoe UI", FONT["body"] - 1 if compact else FONT["body"]))
