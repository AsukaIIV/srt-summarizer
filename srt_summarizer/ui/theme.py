from tkinter import ttk

from srt_summarizer.constants import C, UI_METRICS


FONT = UI_METRICS["font"]
TREE = UI_METRICS["tree"]
NOTEBOOK = UI_METRICS["notebook"]


def build_ttk_style(root):
    style = ttk.Style(root)
    style.theme_use("clam")

    style.configure("Page.TFrame", background=C["bg"])
    style.configure("TNotebook", background=C["bg"], borderwidth=0, tabmargins=(0, 0, 0, 0))
    style.configure(
        "TNotebook.Tab",
        background=C["surface2"],
        foreground=C["fg2"],
        padding=(NOTEBOOK["tab_pad_x"], NOTEBOOK["tab_pad_y"]),
        borderwidth=0,
        font=("Segoe UI", FONT["label"], "bold"),
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", C["bg"]), ("active", C["surface2"])],
        foreground=[("selected", C["accent"]), ("active", C["accent_h"])],
    )

    style.configure(
        "Treeview",
        background=C["panel"],
        fieldbackground=C["panel"],
        foreground=C["fg"],
        font=("Segoe UI", FONT["body"]),
        borderwidth=0,
        relief="flat",
        rowheight=TREE["rowheight"],
    )
    style.configure(
        "Treeview.Heading",
        background=C["surface2"],
        foreground=C["fg2"],
        font=("Segoe UI", FONT["label"], "bold"),
        relief="flat",
        borderwidth=0,
        padding=(8, 6),
    )
    style.map(
        "Treeview",
        background=[("selected", C["sel"])],
        foreground=[("selected", C["fg"])],
    )
    style.map(
        "Treeview.Heading",
        background=[("active", C["accent_soft"])],
        foreground=[("active", C["accent_d"])],
    )

    style.configure(
        "TProgressbar",
        troughcolor=C["border2"],
        background=C["accent"],
        bordercolor=C["border2"],
        lightcolor=C["accent_h"],
        darkcolor=C["accent"],
        thickness=UI_METRICS["progress_thickness"],
    )

    scrollbar_common = {
        "background": C["surface2"],
        "troughcolor": C["panel_alt"],
        "bordercolor": C["panel_alt"],
        "arrowcolor": C["accent_d"],
        "width": UI_METRICS["scrollbar_width"],
        "relief": "flat",
    }
    style.configure("Vertical.TScrollbar", **scrollbar_common)
    style.configure("Horizontal.TScrollbar", **scrollbar_common)
    style.map("Vertical.TScrollbar", background=[("active", C["border_strong"]), ("pressed", C["border_strong"])])
    style.map("Horizontal.TScrollbar", background=[("active", C["border_strong"]), ("pressed", C["border_strong"])])


def set_tree_density(root, compact: bool):
    style = ttk.Style(root)
    style.configure("Treeview", rowheight=TREE["compact_rowheight"] if compact else TREE["rowheight"])
