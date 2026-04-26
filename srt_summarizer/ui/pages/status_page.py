import tkinter as tk
from tkinter import scrolledtext, ttk

from srt_summarizer.constants import C, UI_METRICS
from srt_summarizer.ui.widgets import GhostButton, PrimaryButton, SectionCard, StatusChip


FONT = UI_METRICS["font"]
SPACE = UI_METRICS["space"]
OUTPUT_PADDING = UI_METRICS["output_padding"]
CONSOLE_MIN_HEIGHT = 200


class StatusPage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, style="Page.TFrame")
        self.app = app
        self._build_ui()

    def _build_ui(self):
        # 整个页面分为两行：
        # row 0: 顶部控件（header + 进度卡片）— 自然高度，不可滚动
        # row 1: Console — 撑满剩余空间，保留最低高度
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1, minsize=CONSOLE_MIN_HEIGHT)

        # ── row 0: 顶部区域 ──
        top_frame = tk.Frame(self, bg=C["bg"])
        top_frame.grid(row=0, column=0, sticky="ew")
        top_frame.columnconfigure(0, weight=1)

        header = tk.Frame(top_frame, bg=C["bg"])
        header.grid(row=0, column=0, sticky="ew", padx=SPACE["outer"], pady=(SPACE["section"], 0))
        tk.Label(header, text="开始运行", bg=C["bg"], fg=C["fg"], font=("Segoe UI", FONT["title"], "bold")).pack(anchor="w")

        progress_card = SectionCard(top_frame, "进度总览")
        progress_card.grid(row=1, column=0, sticky="ew", padx=SPACE["outer"], pady=(SPACE["section"], 0))
        controls = tk.Frame(progress_card.body, bg=C["panel"])
        controls.pack(fill="x")
        left_controls = tk.Frame(controls, bg=C["panel"])
        left_controls.pack(side="left")
        self.app._run_btn = PrimaryButton(left_controls, "开始整理", self.app._start, bg_normal=C["accent"], bg_hover=C["accent_h"], fg=C["panel"], font_size=FONT["button"] + 1, bold=True)
        self.app._run_btn.pack(side="left")
        GhostButton(left_controls, "清空输出", self.app._clear_out).pack(side="left", padx=(SPACE["compact"], 0))
        tk.Label(controls, textvariable=self.app._status_var, bg=C["panel"], fg=C["fg2"], font=("Segoe UI", FONT["label"])).pack(side="right")

        strip = tk.Frame(progress_card.body, bg=C["panel"])
        strip.pack(fill="x", pady=(SPACE["section"], SPACE["inline"]))
        self._current_chip = StatusChip(strip, "等待任务", "info")
        self._current_chip.pack(side="left")
        self._token_chip = StatusChip(strip, "chars 0", "warn")
        self._token_chip.pack(side="left", padx=(SPACE["compact"], 0))
        self._pulse_chip = StatusChip(strip, "idle", "success")
        self._pulse_chip.pack(side="left", padx=(SPACE["compact"], 0))
        tk.Label(strip, textvariable=self.app._prog_pct, bg=C["panel"], fg=C["accent"], font=("Consolas", FONT["mono_small"], "bold")).pack(side="right")
        tk.Label(strip, textvariable=self.app._prog_label, bg=C["panel"], fg=C["fg2"], font=("Segoe UI", FONT["label"])).pack(side="right", padx=(0, SPACE["section"]))
        ttk.Progressbar(progress_card.body, variable=self.app._prog_var, maximum=100).pack(fill="x")

        # ── row 1: Console 区域 ──
        live_card = SectionCard(self, "Console")
        live_card.grid(row=1, column=0, sticky="nsew", padx=SPACE["outer"], pady=(SPACE["section"], SPACE["section"]))
        live_card.body.columnconfigure(0, weight=1)
        live_card.body.rowconfigure(0, weight=0)
        live_card.body.rowconfigure(1, weight=1)

        console_toolbar = tk.Frame(live_card.body, bg=C["panel"])
        console_toolbar.grid(row=0, column=0, sticky="ew")
        tk.Label(console_toolbar, text="LIVE OUTPUT", bg=C["panel"], fg=C["accent"], font=("Consolas", FONT["mono_small"], "bold")).pack(side="left")
        tk.Label(console_toolbar, textvariable=self.app._cur_file_var, bg=C["panel"], fg=C["fg2"], font=("Segoe UI", FONT["label"])).pack(side="right")

        out_shell = tk.Frame(live_card.body, bg=C["console_bg"], highlightthickness=1, highlightbackground=C["console_border"])
        out_shell.grid(row=1, column=0, sticky="nsew", pady=(SPACE["compact"], 0))
        out_shell.columnconfigure(0, weight=1)
        out_shell.rowconfigure(0, weight=1)

        self.app._out_text = scrolledtext.ScrolledText(
            out_shell,
            bg=C["console_bg"],
            fg=C["console_fg"],
            insertbackground=C["console_fg"],
            font=("Consolas", FONT["output"]),
            relief="flat",
            bd=0,
            wrap="word",
            state="disabled",
            padx=OUTPUT_PADDING["x"],
            pady=OUTPUT_PADDING["y"],
        )
        self.app._out_text.grid(row=0, column=0, sticky="nsew")
        self.app._out_placeholder = tk.Label(out_shell, bg=C["console_bg"], fg=C["console_accent"], justify="center", font=("Segoe UI", FONT["body"]), text="")
        self.app._out_text.tag_config("h1", foreground=C["console_accent"], font=("Consolas", FONT["output"] + 2, "bold"))
        self.app._out_text.tag_config("h2", foreground=C["console_accent"], font=("Consolas", FONT["output"] + 1, "bold"))
        self.app._out_text.tag_config("bold", foreground="#F8D66D", font=("Consolas", FONT["output"], "bold"))
        self.app._out_text.tag_config("normal", foreground=C["console_fg"])
        self.app._out_text.tag_config("dim", foreground=C["console_muted"])
        self.app._out_text.tag_config("success", foreground=C["green"])
        self.app._out_text.tag_config("error", foreground=C["red"])

        self.app._cur_file_var.trace_add("write", self._refresh_chips)
        self.app._token_var.trace_add("write", self._refresh_chips)
        self.app._pulse_var.trace_add("write", self._refresh_chips)
        self._refresh_chips()

    def _refresh_chips(self, *_args):
        current = self.app._cur_file_var.get().strip() or "等待任务"
        token_text = self.app._token_var.get().strip() or "chars 0"
        pulse_text = "running" if self.app._pulse_var.get().strip() else "idle"
        self._current_chip.set(current, "info")
        self._token_chip.set(token_text, "warn")
        self._pulse_chip.set(pulse_text, "success" if pulse_text == "running" else "warn")

    def apply_layout_mode(self, compact: bool):
        self.app._out_text.configure(font=("Consolas", FONT["output"] - 1 if compact else FONT["output"]))
        self.app._out_placeholder.configure(font=("Segoe UI", FONT["body"] - 1 if compact else FONT["body"]))
