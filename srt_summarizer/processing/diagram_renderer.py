import os
import sys
from typing import Any

from PIL import Image, ImageDraw, ImageFont

CANVAS_WIDTH = 1400
CANVAS_HEIGHT = 920
BG = "#F8FAFC"
TEXT = "#0F172A"
MUTED = "#475569"
BORDER = "#CBD5E1"
PRIMARY = "#DBEAFE"
SECONDARY = "#E0F2FE"
ACCENT = "#FEF3C7"
WHITE = "#FFFFFF"
MAX_DIAGRAMS = 2
FONT_FILENAME = "HarmonyOS_Sans_SC_Medium.ttf"
_LAST_FONT_SOURCE = "未初始化"


def _resource_path(filename: str) -> str:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, filename)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", filename))


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    global _LAST_FONT_SOURCE
    bundled_font = _resource_path(FONT_FILENAME)
    candidates = [(bundled_font, "项目内字体")]
    if bold:
        candidates.extend(
            [
                ("C:/Windows/Fonts/msyhbd.ttc", "系统字体"),
                ("C:/Windows/Fonts/simhei.ttf", "系统字体"),
                ("C:/Windows/Fonts/arialbd.ttf", "系统字体"),
            ]
        )
    candidates.extend(
        [
            ("C:/Windows/Fonts/msyh.ttc", "系统字体"),
            ("C:/Windows/Fonts/msyhbd.ttc", "系统字体"),
            ("C:/Windows/Fonts/simhei.ttf", "系统字体"),
            ("C:/Windows/Fonts/arial.ttf", "系统字体"),
        ]
    )
    for path, source_label in candidates:
        if os.path.exists(path):
            try:
                _LAST_FONT_SOURCE = f"{source_label}：{os.path.basename(path)}"
                return ImageFont.truetype(path, size=size)
            except OSError:
                continue
    _LAST_FONT_SOURCE = "Pillow 默认字体"
    return ImageFont.load_default()


def get_last_font_source() -> str:
    return _LAST_FONT_SOURCE


def _measure_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    left, top, right, bottom = draw.multiline_textbbox((0, 0), text, font=font, spacing=6)
    return right - left, bottom - top


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> str:
    words = [segment for segment in text.replace("\n", " ").split(" ") if segment]
    if not words:
        return ""
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        trial = f"{current} {word}".strip()
        width, _ = _measure_text(draw, trial, font)
        if width <= max_width:
            current = trial
            continue
        lines.append(current)
        current = word
    lines.append(current)
    return "\n".join(lines)


def _wrap_cjk_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> str:
    if " " in text:
        return _wrap_text(draw, text, font, max_width)
    lines: list[str] = []
    current = ""
    for char in text:
        trial = current + char
        width, _ = _measure_text(draw, trial, font)
        if current and width > max_width:
            lines.append(current)
            current = char
        else:
            current = trial
    if current:
        lines.append(current)
    return "\n".join(lines)


def _fit_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> str:
    text = str(text or "").strip()
    if not text:
        return ""
    if any("\u4e00" <= ch <= "\u9fff" for ch in text) and " " not in text:
        return _wrap_cjk_text(draw, text, font, max_width)
    return _wrap_text(draw, text, font, max_width)


def _draw_title(draw: ImageDraw.ImageDraw, title: str, subtitle: str) -> None:
    title_font = _load_font(42, bold=True)
    subtitle_font = _load_font(24)
    draw.text((70, 42), title, fill=TEXT, font=title_font)
    if subtitle:
        subtitle_text = _fit_text(draw, subtitle, subtitle_font, CANVAS_WIDTH - 140)
        draw.multiline_text((70, 102), subtitle_text, fill=MUTED, font=subtitle_font, spacing=6)


def _draw_box(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], title: str, items: list[str], fill: str) -> None:
    title_font = _load_font(28, bold=True)
    body_font = _load_font(23)
    draw.rounded_rectangle(box, radius=24, fill=fill, outline=BORDER, width=3)
    x1, y1, x2, y2 = box
    draw.text((x1 + 28, y1 + 22), title, fill=TEXT, font=title_font)
    cursor_y = y1 + 78
    for item in items:
        wrapped = _fit_text(draw, f"• {item}", body_font, x2 - x1 - 56)
        _, height = _measure_text(draw, wrapped, body_font)
        draw.multiline_text((x1 + 28, cursor_y), wrapped, fill=TEXT, font=body_font, spacing=6)
        cursor_y += height + 14
        if cursor_y > y2 - 40:
            break


def _draw_arrow(draw: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int]) -> None:
    draw.line([start, end], fill=MUTED, width=8)
    ex, ey = end
    draw.polygon([(ex, ey), (ex - 26, ey - 14), (ex - 26, ey + 14)], fill=MUTED)


def _render_comparison(spec: dict[str, Any], out_path: str) -> dict[str, str]:
    image = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), BG)
    draw = ImageDraw.Draw(image)
    _draw_title(draw, spec["title"], spec.get("summary", ""))
    left_box = (70, 180, 660, 820)
    right_box = (740, 180, 1330, 820)
    _draw_box(draw, left_box, spec["left_title"], spec.get("left_items", []), PRIMARY)
    _draw_box(draw, right_box, spec["right_title"], spec.get("right_items", []), SECONDARY)
    image.save(out_path)
    return {
        "kind": "diagram",
        "relative_path": f"imgs/{os.path.basename(out_path)}",
        "title": spec["title"],
        "caption": spec.get("summary", "") or f"对比图：{spec['left_title']} 与 {spec['right_title']}",
        "snippet": spec.get("placement_hint", "") or spec["title"],
        "timestamp": "",
    }


def _render_flow(spec: dict[str, Any], out_path: str) -> dict[str, str]:
    image = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), BG)
    draw = ImageDraw.Draw(image)
    _draw_title(draw, spec["title"], spec.get("summary", ""))
    steps = spec.get("steps", [])[:6]
    title_font = _load_font(25, bold=True)
    body_font = _load_font(22)
    box_width = 1180
    box_height = 90
    start_x = 110
    start_y = 200
    gap = 26
    for index, step in enumerate(steps, start=1):
        y1 = start_y + (index - 1) * (box_height + gap)
        y2 = y1 + box_height
        draw.rounded_rectangle((start_x, y1, start_x + box_width, y2), radius=22, fill=WHITE, outline=BORDER, width=3)
        badge_x1 = start_x + 24
        badge_x2 = badge_x1 + 74
        draw.rounded_rectangle((badge_x1, y1 + 18, badge_x2, y1 + 62), radius=18, fill=ACCENT, outline=None)
        draw.text((badge_x1 + 23, y1 + 20), str(index), fill=TEXT, font=title_font)
        wrapped = _fit_text(draw, step, body_font, box_width - 160)
        draw.multiline_text((badge_x2 + 24, y1 + 20), wrapped, fill=TEXT, font=body_font, spacing=6)
        if index < len(steps):
            _draw_arrow(draw, (CANVAS_WIDTH // 2, y2 + 4), (CANVAS_WIDTH // 2, y2 + gap - 6))
    image.save(out_path)
    return {
        "kind": "diagram",
        "relative_path": f"imgs/{os.path.basename(out_path)}",
        "title": spec["title"],
        "caption": spec.get("summary", "") or "流程图：按步骤梳理课堂中的判断或答题路径",
        "snippet": spec.get("placement_hint", "") or spec["title"],
        "timestamp": "",
    }


def _render_formula_map(spec: dict[str, Any], out_path: str) -> dict[str, str]:
    image = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), BG)
    draw = ImageDraw.Draw(image)
    _draw_title(draw, spec["title"], spec.get("summary", ""))
    center_box = (360, 250, 1040, 430)
    formula_font = _load_font(34, bold=True)
    note_font = _load_font(22)
    draw.rounded_rectangle(center_box, radius=26, fill=ACCENT, outline=BORDER, width=3)
    formula_text = _fit_text(draw, spec["central_formula"], formula_font, 600)
    fw, fh = _measure_text(draw, formula_text, formula_font)
    draw.multiline_text((700 - fw / 2, 290), formula_text, fill=TEXT, font=formula_font, spacing=8)
    branches = spec.get("branches", [])[:4]
    branch_boxes = [
        (70, 560, 620, 790),
        (780, 560, 1330, 790),
        (70, 450, 620, 540),
        (780, 450, 1330, 540),
    ]
    for branch, box in zip(branches, branch_boxes, strict=False):
        draw.rounded_rectangle(box, radius=22, fill=WHITE, outline=BORDER, width=3)
        wrapped = _fit_text(draw, branch, note_font, box[2] - box[0] - 40)
        _, bh = _measure_text(draw, wrapped, note_font)
        draw.multiline_text((box[0] + 20, box[1] + (box[3] - box[1] - bh) / 2), wrapped, fill=TEXT, font=note_font, spacing=6)
        target_x = (box[0] + box[2]) // 2
        target_y = box[1]
        source_y = center_box[3]
        source_x = 700 if target_x < 700 else 700
        _draw_arrow(draw, (source_x, source_y + 8), (target_x, target_y - 10))
    image.save(out_path)
    return {
        "kind": "diagram",
        "relative_path": f"imgs/{os.path.basename(out_path)}",
        "title": spec["title"],
        "caption": spec.get("summary", "") or "公式关系图：梳理核心公式与适用点、易错点之间的关系",
        "snippet": spec.get("placement_hint", "") or spec["title"],
        "timestamp": "",
    }


def render_diagram_entries(diagram_specs: list[dict[str, Any]], image_dir: str) -> tuple[list[dict[str, str]], list[str]]:
    if not diagram_specs:
        return [], []
    os.makedirs(image_dir, exist_ok=True)
    entries: list[dict[str, str]] = []
    warnings: list[str] = []
    for index, spec in enumerate(diagram_specs[:MAX_DIAGRAMS], start=1):
        out_path = os.path.join(image_dir, f"diagram_{index:02d}_{spec['type']}.png")
        try:
            if spec["type"] == "comparison":
                entry = _render_comparison(spec, out_path)
            elif spec["type"] == "flow":
                entry = _render_flow(spec, out_path)
            else:
                entry = _render_formula_map(spec, out_path)
            entries.append(entry)
        except (OSError, KeyError, ValueError) as exc:
            warnings.append(f"结构化图示《{spec.get('title', index)}》生成失败：{exc}")
    return entries, warnings
