import tkinter as tk
from tkinter import scrolledtext, ttk

from srt_summarizer.constants import C, UI_METRICS
from srt_summarizer.ui.widgets import GhostButton, PrimaryButton, ScrollableFrame, SectionCard, StatusChip


FONT = UI_METRICS["font"]
SPACE = UI_METRICS["space"]
OUTPUT_PADDING = UI_METRICS["output_padding"]


class StatusPage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, style="Page.TFrame")
        self.app = app
        self._build_ui()

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
        tk.Label(header, text="开始运行", bg=C["bg"], fg=C["fg"], font=("Segoe UI", FONT["title"], "bold")).pack(anchor="w")

        progress_card = SectionCard(body, "进度总览")
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

        live_card = SectionCard(body, "Console")
        live_card.grid(row=2, column=0, sticky="nsew", padx=SPACE["outer"], pady=(SPACE["section"], SPACE["section"]))
        console_toolbar = tk.Frame(live_card.body, bg=C["panel"])
        console_toolbar.pack(fill="x")
        tk.Label(console_toolbar, text="LIVE OUTPUT", bg=C["panel"], fg=C["accent"], font=("Consolas", FONT["mono_small"], "bold")).pack(side="left")
        tk.Label(console_toolbar, textvariable=self.app._cur_file_var, bg=C["panel"], fg=C["fg2"], font=("Segoe UI", FONT["label"])).pack(side="right")

        out_shell = tk.Frame(live_card.body, bg=C["console_bg"], highlightthickness=1, highlightbackground=C["console_border"], height=360)
        out_shell.pack(fill="both", expand=True, pady=(SPACE["compact"], 0))
        out_shell.pack_propagate(False)
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
        self.app._out_text.pack(fill="both", expand=True)
        self.app._out_placeholder = tk.Label(out_shell, bg=C["console_bg"], fg=C["console_accent"], justify="center", font=("Segoe UI", FONT["body"]), text="")
        self.app._out_text.tag_config("h1", foreground=C["console_accent"], font=("Consolas", FONT["output"] + 2, "bold"))
        self.app._out_text.tag_config("h2", foreground=C["console_accent"], font=("Consolas", FONT["output"] + 1, "bold"))
        self.app._out_text.tag_config("bold", foreground="#F8D66D", font=("Consolas", FONT["output"], "bold"))
        self.app._out_text.tag_config("normal", foreground=C["console_fg"])
        self.app._out_text.tag_config("dim", foreground=C["console_muted"])
        self.app._out_text.tag_config("success", foreground=C["green"])
        self.app._out_text.tag_config("error", foreground=C["red"])
        self._scroll.register_mousewheel_targets(
            header,
            progress_card,
            progress_card.body,
            controls,
            left_controls,
            strip,
            live_card,
            live_card.body,
            console_toolbar,
            out_shell,
            self.app._out_text,
        )
        self._scroll.suspend_mousewheel_targets(self.app._out_text)

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
