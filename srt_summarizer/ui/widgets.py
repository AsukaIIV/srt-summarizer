import tkinter as tk
from tkinter import ttk

from srt_summarizer.constants import C, UI_METRICS


FONT = UI_METRICS["font"]
SPACE = UI_METRICS["space"]
CHIP = UI_METRICS["chip"]
CARD = UI_METRICS["card"]
INPUT = UI_METRICS["input"]


class PrimaryButton(tk.Button):
    def __init__(self, parent, text, command, bg_normal=C["chip"], bg_hover=C["purple_soft"], fg=C["fg2"], font_size=None, bold=True, **kw):
        self._bg_n = bg_normal
        self._bg_h = bg_hover
        self._fg_n = fg
        self._enabled = True
        resolved_font_size = FONT["button"] if font_size is None else font_size
        super().__init__(
            parent,
            text=text,
            command=command,
            bg=bg_normal,
            fg=fg,
            activebackground=bg_hover,
            activeforeground=fg,
            relief="flat",
            bd=0,
            padx=SPACE["button_x"],
            pady=SPACE["button_y"],
            cursor="hand2",
            font=("Segoe UI", resolved_font_size, "bold" if bold else "normal"),
            highlightthickness=1,
            highlightbackground=C["border_subtle"],
            highlightcolor=C["border_subtle"],
            **kw,
        )
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.config(activebackground=self._bg_h, activeforeground=self._fg_n)

    def _on_enter(self, _):
        if self._enabled:
            hover_fg = C["fg"] if self._fg_n != C["panel"] else C["panel"]
            hover_border = C["border_subtle"] if self._fg_n != C["panel"] else self._bg_h
            self.config(bg=self._bg_h, fg=hover_fg, highlightbackground=hover_border)

    def _on_leave(self, _):
        if self._enabled:
            leave_border = C["border_subtle"] if self._fg_n != C["panel"] else self._bg_n
            self.config(bg=self._bg_n, fg=self._fg_n, highlightbackground=leave_border)

    def set_enabled(self, enabled: bool):
        self._enabled = enabled
        if enabled:
            border = C["border_subtle"] if self._fg_n != C["panel"] else self._bg_n
            self.config(state="normal", bg=self._bg_n, fg=self._fg_n, cursor="hand2", highlightbackground=border)
        else:
            self.config(state="disabled", bg=C["border_subtle"], fg=C["fg3"], cursor="arrow", highlightbackground=C["border_subtle"])


class GhostButton(tk.Button):
    def __init__(self, parent, text, command, font_size=None, bg_normal=C["chip"], bg_hover=C["purple_soft"], fg=C["fg2"], border_color=C["border_subtle"], hover_fg=C["fg"], **kw):
        self._enabled = True
        self._bg_n = bg_normal
        self._bg_h = bg_hover
        self._fg_n = fg
        self._fg_h = hover_fg
        self._border = border_color
        resolved_font_size = FONT["button"] if font_size is None else font_size
        super().__init__(
            parent,
            text=text,
            command=command,
            bg=self._bg_n,
            fg=self._fg_n,
            activebackground=self._bg_h,
            activeforeground=self._fg_h,
            relief="flat",
            bd=0,
            padx=SPACE["button_x"],
            pady=SPACE["button_y"],
            cursor="hand2",
            highlightthickness=1,
            highlightbackground=self._border,
            highlightcolor=self._border,
            font=("Segoe UI", resolved_font_size),
            **kw,
        )
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_enter(self, _):
        if self._enabled:
            self.config(fg=self._fg_h, bg=self._bg_h, highlightbackground=self._border)

    def _on_leave(self, _):
        if self._enabled:
            self.config(fg=self._fg_n, bg=self._bg_n, highlightbackground=self._border)

    def set_enabled(self, enabled: bool):
        self._enabled = enabled
        if enabled:
            self.config(state="normal", bg=self._bg_n, fg=self._fg_n, cursor="hand2", highlightbackground=self._border)
        else:
            self.config(state="disabled", bg=C["border2"], fg=C["fg3"], cursor="arrow", highlightbackground=C["border2"])


class ToggleChipButton(tk.Button):
    def __init__(self, parent, text, command, active=False, **kw):
        self._base_text = text
        self._active = active
        super().__init__(
            parent,
            text=text,
            command=command,
            relief="flat",
            bd=0,
            cursor="hand2",
            font=("Segoe UI", FONT["button"]),
            padx=CHIP["pad_x"],
            pady=CHIP["pad_y"],
            highlightthickness=1,
            **kw,
        )
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.set_active(active)

    def _resolve_colors(self):
        if self._active:
            return {
                "bg": C["chip_ok"],
                "fg": C["green"],
                "border": C["green_h"],
                "hover": C["green_soft"],
            }
        return {
            "bg": C["chip"],
            "fg": C["fg2"],
            "border": C["border_subtle"],
            "hover": C["purple_soft"],
        }

    def _apply_colors(self, hovered=False):
        colors = self._resolve_colors()
        self.config(
            bg=colors["hover"] if hovered else colors["bg"],
            fg=colors["fg"],
            activebackground=colors["hover"],
            activeforeground=colors["fg"],
            highlightbackground=colors["border"],
            highlightcolor=colors["border"],
        )

    def _on_enter(self, _):
        self._apply_colors(hovered=True)

    def _on_leave(self, _):
        self._apply_colors(hovered=False)

    def set_active(self, active: bool, text: str | None = None):
        self._active = active
        self.config(text=self._base_text if text is None else text)
        self._apply_colors(hovered=False)


class Divider(tk.Frame):
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=C["border2"], height=1, **kw)


class SectionCard(tk.Frame):
    def __init__(self, parent, title: str, subtitle: str = "", **kw):
        super().__init__(parent, bg=C["panel"], highlightthickness=1, highlightbackground=C["border_subtle"], **kw)
        header = tk.Frame(self, bg=C["panel"], padx=CARD["header_x"], pady=CARD["header_y"])
        header.pack(fill="x")
        tk.Label(header, text=title, bg=C["panel"], fg=C["fg"], font=("Segoe UI", FONT["label"], "bold")).pack(anchor="w")
        if subtitle:
            tk.Label(header, text=subtitle, bg=C["panel"], fg=C["fg3"], font=("Segoe UI", FONT["meta"])).pack(anchor="w", pady=(1, 0))
        Divider(self).pack(fill="x")
        self.body = tk.Frame(self, bg=C["panel"], padx=CARD["pad_x"], pady=CARD["pad_y"])
        self.body.pack(fill="both", expand=True)


class StatusChip(tk.Frame):
    _TONES = {
        "error": (C["chip_error"], C["red"]),
        "success": (C["chip_ok"], C["green"]),
        "warn": (C["chip_warn"], C["yellow"]),
        "info": (C["chip"], C["accent_d"]),
    }

    def __init__(self, parent, text="", tone="info", **kw):
        bg, fg = self._TONES[tone]
        super().__init__(parent, bg=bg, highlightthickness=1, highlightbackground=bg, **kw)
        self._label = tk.Label(self, text=text, bg=bg, fg=fg, font=("Segoe UI", FONT["meta"], "bold"))
        self._label.pack(padx=CHIP["pad_x"], pady=CHIP["pad_y"])
        self.set(text, tone)

    def set(self, text: str, tone: str = "info"):
        bg, fg = self._TONES.get(tone, self._TONES["info"])
        self.config(bg=bg, highlightbackground=bg)
        self._label.config(text=text, bg=bg, fg=fg)


class NotebookPage(ttk.Frame):
    def __init__(self, parent, **kw):
        super().__init__(parent, **kw)
        self.configure(style="Page.TFrame")


class ScrollableFrame(tk.Frame):
    _registry: dict[str, "ScrollableFrame"] = {}

    def __init__(self, parent, bg=C["bg"], **kw):
        super().__init__(parent, bg=bg, **kw)
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.content = tk.Frame(self.canvas, bg=bg)
        self._window_id = self.canvas.create_window((0, 0), window=self.content, anchor="nw")
        self.content.bind("<Configure>", self._on_content_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self._mousewheel_registered = False
        self._suspended = False
        self.register_mousewheel_targets(self, self.canvas, self.content)

    def register_mousewheel_targets(self, *widgets):
        for widget in widgets:
            widget.bind("<Enter>", self._bind_mousewheel, add="+")
            widget.bind("<Leave>", self._unbind_mousewheel, add="+")

    def suspend_mousewheel_targets(self, *widgets):
        for widget in widgets:
            widget.bind("<Enter>", self._suspend_mousewheel, add="+")
            widget.bind("<Leave>", self._resume_mousewheel, add="+")

    def _on_content_configure(self, _event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfigure(self._window_id, width=event.width)

    def _bind_mousewheel(self, _event=None):
        if self._mousewheel_registered:
            return
        root = self.winfo_toplevel()
        key = str(root)
        active = ScrollableFrame._registry.get(key)
        if active and active is not self:
            active._mousewheel_registered = False
        ScrollableFrame._registry[key] = self
        root.bind_all("<MouseWheel>", self._on_mousewheel, add="+")
        root.bind_all("<Button-4>", self._on_mousewheel, add="+")
        root.bind_all("<Button-5>", self._on_mousewheel, add="+")
        self._mousewheel_registered = True

    def _unbind_mousewheel(self, _event=None):
        if self._mouse_over_self():
            return
        self._mousewheel_registered = False
        self._suspended = False
        root = self.winfo_toplevel()
        key = str(root)
        if ScrollableFrame._registry.get(key) is self:
            ScrollableFrame._registry.pop(key, None)

    def _suspend_mousewheel(self, _event=None):
        self._suspended = True

    def _resume_mousewheel(self, _event=None):
        self._suspended = False

    def _mouse_over_self(self) -> bool:
        pointer_widget = self.winfo_containing(self.winfo_pointerx(), self.winfo_pointery())
        while pointer_widget is not None:
            if pointer_widget is self:
                return True
            pointer_widget = pointer_widget.master
        return False

    def _on_mousewheel(self, event):
        key = str(self.winfo_toplevel())
        if ScrollableFrame._registry.get(key) is not self or self._suspended:
            return
        if event.delta:
            step = -1 * int(event.delta / 120) if event.delta else 0
        elif getattr(event, "num", None) == 4:
            step = -1
        elif getattr(event, "num", None) == 5:
            step = 1
        else:
            step = 0
        if step:
            self.canvas.yview_scroll(step, "units")
