import json
import re
from typing import Any

DIAGRAM_BLOCK_RE = re.compile(
    r"\n*##\s*结构化图示输出\s*\n+```json\s*(\{[\s\S]*?\})\s*```\s*$",
    re.MULTILINE,
)
ALLOWED_TYPES = {"comparison", "flow", "formula_map"}
MAX_DIAGRAMS = 2
MAX_ITEMS = 8
MAX_TEXT_LEN = 80


def _clean_text(value: Any, limit: int = MAX_TEXT_LEN) -> str:
    text = str(value or "").strip()
    text = re.sub(r"\s+", " ", text)
    return text[:limit].strip()


def _clean_string_list(values: Any, limit: int = MAX_ITEMS) -> list[str]:
    if not isinstance(values, list):
        return []
    items: list[str] = []
    for value in values[:limit]:
        text = _clean_text(value)
        if text:
            items.append(text)
    return items


def _normalize_spec(raw: Any) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    diagram_type = _clean_text(raw.get("type"), limit=24).lower()
    if diagram_type not in ALLOWED_TYPES:
        return None
    title = _clean_text(raw.get("title"))
    if not title:
        return None
    summary = _clean_text(raw.get("summary"), limit=120)
    placement_hint = _clean_text(raw.get("placement_hint"), limit=120)
    spec: dict[str, Any] = {
        "type": diagram_type,
        "title": title,
        "summary": summary,
        "placement_hint": placement_hint,
    }
    if diagram_type == "comparison":
        left_title = _clean_text(raw.get("left_title"))
        right_title = _clean_text(raw.get("right_title"))
        left_items = _clean_string_list(raw.get("left_items"))
        right_items = _clean_string_list(raw.get("right_items"))
        if not left_title or not right_title or (not left_items and not right_items):
            return None
        spec.update(
            {
                "left_title": left_title,
                "right_title": right_title,
                "left_items": left_items,
                "right_items": right_items,
            }
        )
        return spec
    if diagram_type == "flow":
        steps = _clean_string_list(raw.get("steps"))
        if len(steps) < 2:
            return None
        spec["steps"] = steps
        return spec
    central_formula = _clean_text(raw.get("central_formula"), limit=120)
    branches = _clean_string_list(raw.get("branches"))
    if not central_formula or not branches:
        return None
    spec.update(
        {
            "central_formula": central_formula,
            "branches": branches,
        }
    )
    return spec


def extract_diagram_specs(content: str) -> tuple[str, list[dict[str, Any]], list[str]]:
    text = (content or "").strip()
    if not text:
        return "", [], []
    match = DIAGRAM_BLOCK_RE.search(text)
    if not match:
        return text, [], []
    markdown_body = text[:match.start()].rstrip()
    warnings: list[str] = []
    try:
        payload = json.loads(match.group(1))
    except json.JSONDecodeError:
        return markdown_body, [], ["结构化图示 JSON 解析失败，已跳过图示生成"]
    raw_specs = payload.get("diagrams") if isinstance(payload, dict) else None
    if not isinstance(raw_specs, list):
        return markdown_body, [], ["结构化图示格式无效，已跳过图示生成"]
    specs: list[dict[str, Any]] = []
    for index, raw_spec in enumerate(raw_specs[:MAX_DIAGRAMS], start=1):
        normalized = _normalize_spec(raw_spec)
        if normalized is None:
            warnings.append(f"第 {index} 个结构化图示格式无效，已跳过")
            continue
        specs.append(normalized)
    return markdown_body, specs, warnings
