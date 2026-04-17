C = dict(
    bg="#E8EAED",
    surface="#024873",
    surface2="#F7F8FA",
    panel="#FFFFFF",
    panel_alt="#F7F8FA",
    field="#FFFFFF",
    field_focus="#036399",
    border="#D1D5DB",
    border2="#E1E5EA",
    border_subtle="#D9DEE5",
    border_strong="#B8C2CC",
    accent="#024873",
    accent_h="#036399",
    accent_d="#024873",
    accent_soft="#E8F1F7",
    purple="#024873",
    purple_soft="#E8F1F7",
    green="#28A745",
    green_h="#218838",
    green_soft="#EAF7EE",
    red="#DC3545",
    red_soft="#FCEBEC",
    yellow="#D39E00",
    yellow_soft="#FFF8E1",
    fg="#212529",
    fg2="#4B5563",
    fg3="#6C757D",
    code_bg="#0F1720",
    sel="#DCEAF6",
    chip="#F2F4FA",
    chip_ok="#EAF7EE",
    chip_warn="#FFF8E1",
    chip_error="#FCEBEC",
    console_bg="#0F1720",
    console_fg="#D9E2EC",
    console_muted="#94A3B8",
    console_border="#223041",
    console_accent="#62B0FF",
)

SUPPORTED_EXT = (".srt", ".txt", ".md")
SUPPORTED_VIDEO_EXT = (".mp4", ".mkv", ".mov", ".avi", ".m4v")

UI_METRICS = {
    "font": {
        "label": 10,
        "body": 10,
        "button": 10,
        "title": 15,
        "hero": 15,
        "stats": 24,
        "tiny": 8,
        "meta": 9,
        "mono": 10,
        "mono_small": 9,
        "output": 10,
    },
    "space": {
        "outer": 12,
        "section": 10,
        "compact": 6,
        "inline": 4,
        "button_x": 14,
        "button_y": 7,
    },
    "card": {
        "pad_x": 14,
        "pad_y": 10,
        "header_x": 14,
        "header_y": 9,
        "gap": 10,
    },
    "input": {
        "pad_x": 10,
        "pad_y": 7,
    },
    "chip": {
        "pad_x": 9,
        "pad_y": 4,
    },
    "nav_height": 64,
    "requirements_height": 8,
    "tree": {
        "rowheight": 34,
        "compact_rowheight": 28,
        "fixed": {
            "mode": 104,
            "status": 118,
        },
        "minimum": {
            "lesson": 260,
            "folder": 150,
            "video": 150,
        },
    },
    "progress_thickness": 10,
    "scrollbar_width": 12,
    "output_padding": {
        "x": 14,
        "y": 12,
    },
    "notebook": {
        "tab_pad_x": 16,
        "tab_pad_y": 9,
    },
}

COMPACT_BREAKPOINT = {
    "width": 1320,
    "height": 820,
}

DEFAULT_WINDOW_SIZE = (1260, 820)
DEFAULT_MIN_SIZE = (980, 640)
