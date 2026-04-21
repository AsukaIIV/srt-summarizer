import tkinter as tk
from tkinter import ttk

from srt_summarizer.constants import C, UI_METRICS
from srt_summarizer.ui.widgets import GhostButton, ScrollableFrame, SectionCard


FONT = UI_METRICS["font"]
SPACE = UI_METRICS["space"]


class ConfigPage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, style="Page.TFrame")
        self.app = app
        self._build_ui()

    def _make_entry_shell(self, parent, textvariable, *, show=None):
        shell = tk.Frame(parent, bg=C["field"], highlightthickness=1, highlightbackground=C["border_subtle"], highlightcolor=C["field_focus"])
        entry = tk.Entry(
            shell,
            textvariable=textvariable,
            show=show,
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
        tk.Label(header, text="API配置", bg=C["bg"], fg=C["fg"], font=("Segoe UI", FONT["title"], "bold")).pack(anchor="w")

        api_card = SectionCard(body, "模型与接口")
        api_card.grid(row=1, column=0, sticky="ew", padx=SPACE["outer"], pady=(SPACE["section"], SPACE["section"]))
        api_card.body.columnconfigure(1, weight=1)
        api_card.body.columnconfigure(3, weight=1)
        tk.Label(api_card.body, text="API 平台", bg=C["panel"], fg=C["fg2"], font=("Segoe UI", FONT["label"])).grid(row=0, column=0, sticky="w")
        provider_values = [self.app._provider_labels[key] for key in self.app._provider_labels]
        self.app._provider_combo = ttk.Combobox(api_card.body, state="readonly", values=provider_values, width=18)
        self.app._provider_combo.grid(row=0, column=1, sticky="ew", padx=(SPACE["inline"], SPACE["section"]))
        self.app._provider_combo.set(self.app._provider_labels[self.app._provider_var.get()])
        self.app._provider_combo.bind("<<ComboboxSelected>>", self.app._on_provider_selected)
        tk.Label(api_card.body, text="模型", bg=C["panel"], fg=C["fg2"], font=("Segoe UI", FONT["label"])).grid(row=0, column=2, sticky="w")
        model_shell, model_entry = self._make_entry_shell(api_card.body, self.app._model_var)
        model_shell.grid(row=0, column=3, sticky="ew", padx=(SPACE["inline"], 0))
        tk.Label(api_card.body, text="接口地址", bg=C["panel"], fg=C["fg2"], font=("Segoe UI", FONT["label"])).grid(row=1, column=0, sticky="w", pady=(SPACE["section"], 0))
        base_url_shell, base_url_entry = self._make_entry_shell(api_card.body, self.app._base_url_var)
        base_url_shell.grid(row=1, column=1, columnspan=3, sticky="ew", padx=(SPACE["inline"], 0), pady=(SPACE["section"], 0))
        tk.Label(api_card.body, text="密钥", bg=C["panel"], fg=C["fg2"], font=("Segoe UI", FONT["label"])).grid(row=2, column=0, sticky="w", pady=(SPACE["section"], 0))
        api_key_shell, api_key_entry = self._make_entry_shell(api_card.body, self.app._api_key_var, show="*")
        api_key_shell.grid(row=2, column=1, columnspan=3, sticky="ew", padx=(SPACE["inline"], 0), pady=(SPACE["section"], 0))

        tk.Label(
            api_card.body,
            text="当前平台会分别记住自己的模型、接口地址和 API Key。",
            bg=C["panel"],
            fg=C["fg2"],
            font=("Segoe UI", FONT["meta"]),
            justify="left",
        ).grid(row=3, column=0, columnspan=4, sticky="w", pady=(SPACE["compact"], 0))

        action_row = tk.Frame(api_card.body, bg=C["panel"])
        action_row.grid(row=4, column=0, columnspan=4, sticky="ew", pady=(SPACE["section"], 0))
        GhostButton(action_row, "保存配置", self.app._save_config).pack(side="left")
        self.app._test_btn = GhostButton(action_row, "测试配置", self.app._test_config)
        self.app._test_btn.pack(side="left", padx=(SPACE["compact"], 0))
        self.app._config_chip_host = tk.Frame(action_row, bg=C["panel"])
        self.app._config_chip_host.pack(side="right")

        self.app._config_validation_msg_label = tk.Label(
            api_card.body,
            textvariable=self.app._config_validation_msg_var,
            bg=C["panel"],
            fg=C["red"],
            font=("Segoe UI", FONT["meta"]),
            justify="left",
            wraplength=760,
        )
        self.app._config_validation_msg_label.grid(row=5, column=0, columnspan=4, sticky="ew", pady=(SPACE["compact"], 0))

        self._scroll.register_mousewheel_targets(
            header,
            api_card,
            api_card.body,
            action_row,
            self.app._config_chip_host,
            self.app._config_validation_msg_label,
            model_shell,
            model_entry,
            base_url_shell,
            base_url_entry,
            api_key_shell,
            api_key_entry,
            self.app._provider_combo,
        )

    def apply_layout_mode(self, compact: bool):
        combo_width = 14 if compact else 18
        self.app._provider_combo.configure(width=combo_width)
        self.app._config_validation_msg_label.configure(wraplength=560 if compact else 760)
