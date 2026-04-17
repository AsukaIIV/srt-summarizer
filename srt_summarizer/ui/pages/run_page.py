import os
import tkinter as tk
from tkinter import ttk

from srt_summarizer.constants import C, UI_METRICS
from srt_summarizer.processing.lesson_pairing import pair_lessons
from srt_summarizer.ui.widgets import GhostButton, PrimaryButton, ScrollableFrame, SectionCard, ToggleChipButton


FONT = UI_METRICS["font"]
SPACE = UI_METRICS["space"]
CARD = UI_METRICS["card"]
TREE_METRICS = UI_METRICS["tree"]


class RunPage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, style="Page.TFrame")
        self.app = app
        self.configure(padding=0)
        self._build_ui()

    def _on_tree_mousewheel(self, event):
        if event.delta:
            step = -1 * int(event.delta / 120) if event.delta else 0
        elif getattr(event, "num", None) == 4:
            step = -1
        elif getattr(event, "num", None) == 5:
            step = 1
        else:
            step = 0
        if step:
            self.app._tree.yview_scroll(step, "units")
            return "break"
        return None

    def _make_entry_shell(self, parent, textvariable, *, show=None, fg=None):
        shell = tk.Frame(parent, bg=C["field"], highlightthickness=1, highlightbackground=C["border_subtle"], highlightcolor=C["field_focus"])
        entry = tk.Entry(
            shell,
            textvariable=textvariable,
            show=show,
            bg=C["field"],
            fg=fg or C["fg"],
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
        body.rowconfigure(2, weight=1)

        header = tk.Frame(body, bg=C["bg"])
        header.grid(row=0, column=0, sticky="ew", padx=SPACE["outer"], pady=(SPACE["section"], 0))
        tk.Label(header, text="选择文件", bg=C["bg"], fg=C["fg"], font=("Segoe UI", FONT["title"], "bold")).pack(anchor="w")

        source_card = SectionCard(body, "文件与输出")
        source_card.grid(row=1, column=0, sticky="ew", padx=SPACE["outer"], pady=(SPACE["section"], 0))
        source_card.body.columnconfigure(0, weight=1)

        path_group = tk.Frame(source_card.body, bg=C["panel_alt"], highlightthickness=1, highlightbackground=C["border"])
        path_group.grid(row=0, column=0, sticky="ew")
        path_inner = tk.Frame(path_group, bg=C["panel_alt"], padx=CARD["pad_x"], pady=CARD["pad_y"])
        path_inner.pack(fill="x")
        path_inner.columnconfigure(1, weight=1)
        tk.Label(path_inner, text="当前工作目录", bg=C["panel_alt"], fg=C["fg2"], font=("Segoe UI", FONT["label"])).grid(row=0, column=0, sticky="w")
        dir_shell, _ = self._make_entry_shell(path_inner, self.app._dir_var, fg=C["fg2"])
        dir_shell.grid(row=0, column=1, columnspan=2, sticky="ew", padx=(SPACE["inline"], 0))
        tk.Label(path_inner, text="输出目录", bg=C["panel_alt"], fg=C["fg2"], font=("Segoe UI", FONT["label"])).grid(row=1, column=0, sticky="w", pady=(SPACE["section"], 0))
        out_shell, out_entry = self._make_entry_shell(path_inner, self.app._out_var)
        out_shell.grid(row=1, column=1, columnspan=2, sticky="ew", padx=(SPACE["inline"], 0), pady=(SPACE["section"], 0))
        output_actions = tk.Frame(path_inner, bg=C["panel_alt"])
        output_actions.grid(row=2, column=1, columnspan=2, sticky="w", pady=(2, 0))
        self.app._pick_output_btn = GhostButton(output_actions, "浏览", self.app._pick_output)
        self.app._pick_output_btn.pack(side="left")
        self.app._src_btn = ToggleChipButton(output_actions, "输出到源目录：关", self.app._toggle_save_to_src, active=self.app._save_to_src.get())
        self.app._src_btn.pack(side="left", padx=(SPACE["compact"], 0))
        self.app._output_hint_label = tk.Label(output_actions, textvariable=self.app._output_hint_var, bg=C["panel_alt"], fg=C["fg3"], font=("Segoe UI", FONT["meta"]))
        self.app._output_hint_label.pack(side="left", padx=(SPACE["compact"], 0))
        self.app._out_shell = out_shell
        self.app._out_entry = out_entry

        self._source_actions = tk.Frame(source_card.body, bg=C["panel"])
        self._source_actions.grid(row=1, column=0, sticky="ew", pady=(SPACE["section"], 0))

        self._scan_group = tk.Frame(self._source_actions, bg=C["panel"], highlightthickness=1, highlightbackground=C["border_subtle"])
        self._scan_group.pack(side="left")
        scan_group_inner = tk.Frame(self._scan_group, bg=C["panel"], padx=10, pady=8)
        scan_group_inner.pack(fill="both", expand=True)
        self._scan_btn = PrimaryButton(scan_group_inner, "扫描视频资料目录", self.app._pick_dir, bg_normal=C["accent"], bg_hover=C["accent_h"], fg=C["panel"], bold=True, font_size=FONT["button"] + 1)
        self._scan_btn.pack(side="left")
        self._scan_hint = tk.Label(scan_group_inner, text="自动配对字幕与视频", bg=C["panel"], fg=C["fg3"], font=("Segoe UI", FONT["meta"]))
        self._scan_hint.pack(side="left", padx=(SPACE["compact"], 0))

        self._pick_files_group = tk.Frame(self._source_actions, bg=C["panel"], highlightthickness=0, highlightbackground=C["border_subtle"])
        self._pick_files_group.pack(side="left", padx=(SPACE["compact"], 0))
        GhostButton(self._pick_files_group, "选择字幕文件", self.app._pick_files).pack(side="left")

        self._pick_videos_group = tk.Frame(self._source_actions, bg=C["panel"], highlightthickness=0, highlightbackground=C["border_subtle"])
        self._pick_videos_group.pack(side="left", padx=(SPACE["compact"], 0))
        GhostButton(self._pick_videos_group, "选择视频文件", self.app._pick_videos).pack(side="left")

        self._pick_notes_group = tk.Frame(self._source_actions, bg=C["panel"], highlightthickness=0, highlightbackground=C["border_subtle"])
        self._pick_notes_group.pack(side="left", padx=(SPACE["compact"], 0))
        GhostButton(self._pick_notes_group, "选择往期笔记", self.app._pick_prior_notes).pack(side="left")

        self._overview = tk.Frame(source_card.body, bg=C["panel"])
        self._overview.grid(row=2, column=0, sticky="ew", pady=(SPACE["section"], 0))
        self._overview.columnconfigure(0, weight=1)
        self._stat_card = tk.Frame(self._overview, bg=C["panel_alt"], highlightthickness=1, highlightbackground=C["border"])
        self._stat_card.grid(row=0, column=0, sticky="ew")
        stat_inner = tk.Frame(self._stat_card, bg=C["panel_alt"], padx=CARD["pad_x"], pady=CARD["pad_y"])
        stat_inner.pack(fill="x")
        tk.Label(stat_inner, text="任务概览", bg=C["panel_alt"], fg=C["fg2"], font=("Segoe UI", FONT["label"], "bold")).pack(anchor="w")
        tk.Label(stat_inner, textvariable=self.app._stat_var, bg=C["panel_alt"], fg=C["accent"], font=("Segoe UI", FONT["stats"], "bold")).pack(anchor="w", pady=(1, 0))
        tk.Label(stat_inner, textvariable=self.app._extra_stat_var, bg=C["panel_alt"], fg=C["fg2"], font=("Segoe UI", FONT["label"])).pack(anchor="w", pady=(0, SPACE["inline"]))

        queue_card = SectionCard(body, "课程任务列表")
        queue_card.grid(row=2, column=0, sticky="nsew", padx=SPACE["outer"], pady=(SPACE["section"], SPACE["section"]))
        header_actions = tk.Frame(queue_card.body, bg=C["panel"])
        header_actions.pack(fill="x")
        tk.Label(header_actions, textvariable=self.app._list_count_var, bg=C["panel"], fg=C["fg3"], font=("Segoe UI", FONT["meta"])).pack(side="left")
        self._action_links = tk.Frame(header_actions, bg=C["panel"])
        self._action_links.pack(side="right")
        GhostButton(
            self._action_links,
            "移除所选字幕",
            self.app._remove_selected,
            font_size=FONT["label"],
            bg_normal=C["red_soft"],
            bg_hover="#F8DCDD",
            fg=C["red"],
            border_color="#F1B7BC",
            hover_fg="#C62839",
        ).pack(side="left")

        tree_shell = tk.Frame(queue_card.body, bg=C["panel_alt"], highlightthickness=1, highlightbackground=C["border"], height=280)
        tree_shell.pack(fill="both", expand=True, pady=(SPACE["compact"], 0))
        tree_shell.pack_propagate(False)
        tree_frame = tk.Frame(tree_shell, bg=C["panel_alt"])
        tree_frame.pack(fill="both", expand=True, padx=1, pady=1)
        cols = ("lesson", "folder", "video", "mode", "status")
        self.app._tree = ttk.Treeview(tree_frame, columns=cols, show="headings")
        self.app._tree.heading("lesson", text="字幕")
        self.app._tree.heading("folder", text="来源目录")
        self.app._tree.heading("video", text="视频")
        self.app._tree.heading("mode", text="模式")
        self.app._tree.heading("status", text="状态")
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.app._tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.app._tree.xview)
        self.app._tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        self.app._tree.pack(side="left", fill="both", expand=True)
        self.app._tree.bind("<MouseWheel>", self._on_tree_mousewheel, add="+")
        self.app._tree.bind("<Button-4>", self._on_tree_mousewheel, add="+")
        self.app._tree.bind("<Button-5>", self._on_tree_mousewheel, add="+")
        tree_frame.bind("<Configure>", self.app._on_tree_resize)
        self.app._tree.tag_configure("done", foreground=C["green"])
        self.app._tree.tag_configure("fail", foreground=C["red"])
        self.app._tree.tag_configure("doing", foreground=C["yellow"])
        self.app._tree.tag_configure("dim", foreground=C["fg2"])

        self._scroll.register_mousewheel_targets(
            header,
            source_card,
            source_card.body,
            path_group,
            path_inner,
            dir_shell,
            self._source_actions,
            self._scan_group,
            scan_group_inner,
            self._pick_files_group,
            self._pick_videos_group,
            self._pick_notes_group,
            self._overview,
            self._stat_card,
            out_shell,
            queue_card,
            queue_card.body,
            header_actions,
            self._action_links,
            tree_shell,
            tree_frame,
        )
        self._scroll.suspend_mousewheel_targets(self.app._tree)

    def apply_layout_mode(self, compact: bool):
        buttons = [self._pick_files_group, self._pick_videos_group, self._pick_notes_group]
        for child in self._source_actions.winfo_children():
            child.pack_forget()
        self._scan_group.pack(side="left")
        for index, child in enumerate(buttons):
            child.pack(side="left", padx=(SPACE["compact"], 0))

        action_links = self._action_links.winfo_children()
        for child in action_links:
            child.pack_forget()
        for index, child in enumerate(action_links):
            if compact:
                child.pack(fill="x", pady=(0 if index == 0 else SPACE["compact"], 0))
            else:
                child.pack(side="left", padx=(0 if index == 0 else SPACE["compact"], 0))

        if compact:
            self._scan_hint.configure(text="自动配对字幕与视频", anchor="w")
        else:
            self._scan_hint.configure(text="自动配对字幕与视频", anchor="center")

    def resize_tree_columns(self, width: int | None = None):
        tree_width = width or self.app._tree.winfo_width()
        if tree_width <= 1:
            return
        fixed = TREE_METRICS["fixed"]
        minimum = TREE_METRICS["minimum"]
        fixed_total = fixed["mode"] + fixed["status"]
        usable_width = max(tree_width - fixed_total - 24, 0)
        total_minimum = sum(minimum.values())
        if usable_width <= total_minimum:
            lesson_width = minimum["lesson"]
            folder_width = minimum["folder"]
            video_width = minimum["video"]
        else:
            extra = usable_width - total_minimum
            lesson_width = minimum["lesson"] + int(extra * 0.46)
            folder_width = minimum["folder"] + int(extra * 0.24)
            video_width = minimum["video"] + (extra - int(extra * 0.46) - int(extra * 0.24))
        self.app._tree.column("lesson", width=lesson_width, stretch=False)
        self.app._tree.column("folder", width=folder_width, stretch=False)
        self.app._tree.column("video", width=video_width, stretch=False)
        self.app._tree.column("mode", width=fixed["mode"], stretch=False, anchor="center")
        self.app._tree.column("status", width=fixed["status"], stretch=False, anchor="center")

    def refresh_tree(self):
        for item in self.app._tree.get_children():
            self.app._tree.delete(item)
        lessons = pair_lessons(self.app._transcript_files, self.app._video_files)
        matched_count = 0
        for lesson in lessons:
            video_name = os.path.basename(lesson.video_path) if lesson.video_path else "—"
            folder_name = os.path.basename(os.path.dirname(lesson.transcript_path)) or "—"
            if lesson.video_path:
                matched_count += 1
            mode = "图文混排" if lesson.video_path else "纯字幕"
            self.app._tree.insert("", "end", iid=lesson.transcript_path, values=(os.path.basename(lesson.transcript_path), folder_name, video_name, mode, "待处理"))
        lesson_count = len(lessons)
        self.app._stat_var.set(str(lesson_count))
        self.app._list_count_var.set(f"({lesson_count} 个)" if lessons else "")
        self.app._extra_stat_var.set(f"字幕 {len(self.app._transcript_files)} / 视频 {len(self.app._video_files)} / 往期笔记 {len(self.app._prior_note_files)}")
        if not lessons:
            self.app._status_var.set("就绪，请选择字幕文件或扫描目录")
        elif matched_count == lesson_count:
            self.app._status_var.set("就绪，可开始图文整理")
        elif matched_count > 0:
            self.app._status_var.set("就绪，可开始混合整理")
        else:
            self.app._status_var.set("就绪，可开始字幕整理")
