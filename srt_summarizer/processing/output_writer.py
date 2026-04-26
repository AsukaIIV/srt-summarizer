import os
import re
from datetime import datetime


IMAGE_SECTION_RE = re.compile(r"(^##\s+第[一二三四五六七八九十0-9]+部分.*?$)", re.MULTILINE)
SUBSECTION_RE = re.compile(r"^###\s+.*?$|^####\s+.*?$", re.MULTILINE)
ANCHOR_RE = re.compile(r"\[\[插图(\d+)\]\]")
TOKEN_RE = re.compile(r"[A-Za-z0-9\u4e00-\u9fff]{2,}")


def resolve_output_dir(source_file: str, chosen_output_dir: str, save_to_source: bool) -> str:
    return os.path.dirname(source_file) if save_to_source else chosen_output_dir


def sanitize_path_part(value: str) -> str:
    cleaned = re.sub(r'[\\/:*?"<>|]+', '_', value).strip().strip('.')
    return cleaned or '未命名课程'


def build_output_bundle_dir(source_file: str, save_dir: str, course_name: str) -> str:
    stem = os.path.splitext(os.path.basename(source_file))[0]
    parent = os.path.basename(os.path.dirname(source_file)).strip()
    suffix = f"_{sanitize_path_part(parent)}" if parent else ""
    bundle_name = f"{sanitize_path_part(stem)}{suffix}_{sanitize_path_part(course_name)}"
    return os.path.join(save_dir, bundle_name)


def build_note_filename(source_file: str, course_name: str) -> str:
    stem = sanitize_path_part(os.path.splitext(os.path.basename(source_file))[0])
    course = sanitize_path_part(course_name)
    if course and course != '未命名课程':
        return f"{stem}_{course}_课堂总结.md"
    return f"{stem}_课堂总结.md"


def build_output_paths(source_file: str, save_dir: str, course_name: str) -> tuple[str, str, str]:
    bundle_dir = build_output_bundle_dir(source_file, save_dir, course_name)
    img_dir = os.path.join(bundle_dir, "imgs")
    note_path = os.path.join(bundle_dir, build_note_filename(source_file, course_name))
    return bundle_dir, img_dir, note_path


def normalize_markdown_content(content: str) -> str:
    lines = [line.rstrip() for line in content.replace("\r\n", "\n").split("\n")]
    cleaned: list[str] = []
    blank_run = 0
    for line in lines:
        if not line.strip():
            blank_run += 1
            if blank_run > 1:
                continue
            cleaned.append("")
            continue
        blank_run = 0
        cleaned.append(line)
    text = "\n".join(cleaned).strip()
    return text + "\n" if text else ""


def _normalize_match_text(text: str) -> str:
    text = re.sub(r"[（()）【】\[\]、，。；：！？,.!?:;\-_/]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.lower().strip()


def _extract_tokens(text: str) -> list[str]:
    return TOKEN_RE.findall(_normalize_match_text(text))


def _split_markdown_sections(normalized: str) -> tuple[str, list[dict[str, str]]]:
    matches = list(IMAGE_SECTION_RE.finditer(normalized))
    if not matches:
        return normalized, []
    prefix = normalized[:matches[0].start()]
    sections: list[dict[str, str]] = []
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(normalized)
        block = normalized[start:end].strip()
        lines = block.splitlines()
        heading = lines[0].strip() if lines else ""
        body = "\n".join(lines[1:]).strip()
        subsection_lines = SUBSECTION_RE.findall(block)
        excerpt = body[:400]
        sections.append(
            {
                "heading": heading,
                "body": body,
                "block": block,
                "subsections": "\n".join(line.strip() for line in subsection_lines),
                "excerpt": excerpt,
            }
        )
    return prefix, sections


def _score_entry_against_section(entry: dict[str, str], section: dict[str, str], section_index: int, total_sections: int) -> float:
    snippet = str(entry.get("snippet", "")).strip()
    if not snippet:
        return 0.2 / max(abs(section_index), 1)
    snippet_tokens = _extract_tokens(snippet)
    if not snippet_tokens:
        return 0.0
    heading_text = _normalize_match_text(section["heading"])
    subsection_text = _normalize_match_text(section["subsections"])
    excerpt_text = _normalize_match_text(section["excerpt"])
    score = 0.0
    for token in snippet_tokens:
        if token in heading_text:
            score += 4.0
        if token in subsection_text:
            score += 3.0
        if token in excerpt_text:
            score += 1.2
    unique_count = len(set(snippet_tokens))
    if unique_count:
        score += min(unique_count * 0.1, 0.8)
    if total_sections > 1:
        expected_index = min(max(int(round((len(snippet_tokens) % total_sections))), 0), total_sections - 1)
        score += max(0.0, 0.3 - abs(section_index - expected_index) * 0.08)
    return score


def _render_image_block(entry: dict[str, str], image_number: int, confidence: float) -> str:
    rel_path = str(entry.get("relative_path", "")).replace('\\', '/')
    if not rel_path:
        return ""
    if str(entry.get("kind", "")).strip() == "diagram":
        title = str(entry.get("title", "")).strip()
        caption = str(entry.get("caption", "")).strip()
        alt = title or f"结构化图示 {image_number}"
        lines = [f"![{alt}]({rel_path})"]
        if caption:
            lines.append(f"> 图示说明：{caption}")
        return "\n".join(lines)
    lines = [f"![课堂截图 {image_number}]({rel_path})"]
    snippet = str(entry.get("snippet", "")).strip()
    timestamp = str(entry.get("timestamp", "")).strip()
    if confidence >= 4.5 and timestamp and not snippet:
        lines.append(f"> 看图提示：截图时间 {timestamp}")
    elif confidence >= 3.5 and snippet:
        helper = snippet.replace("\n", " ").strip()
        if len(helper) > 36:
            helper = helper[:36].rstrip() + "…"
        prefix = f"{timestamp} · " if timestamp else ""
        lines.append(f"> 看图提示：{prefix}{helper}")
    return "\n".join(lines)


def _build_appendix_block(entries: list[dict[str, str]], start_index: int) -> str:
    title = "## 结构化图示补充" if entries and str(entries[0].get("kind", "")).strip() == "diagram" else "## 课堂截图补充"
    lines = [title, ""]
    for image_number, entry in enumerate(entries, start=start_index):
        lines.append(_render_image_block(entry, image_number, confidence=0.0))
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def _split_entry_kinds(entries: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    screenshots: list[dict[str, str]] = []
    diagrams: list[dict[str, str]] = []
    for entry in entries:
        if str(entry.get("kind", "")).strip() == "diagram":
            diagrams.append(entry)
        else:
            screenshots.append(entry)
    return screenshots, diagrams


def _replace_image_anchors(content: str, image_entries: list[dict[str, str]]) -> tuple[str, list[dict[str, str]], int]:
    used_indices: set[int] = set()
    next_image_number = 1

    def repl(match: re.Match[str]) -> str:
        nonlocal next_image_number
        entry_index = int(match.group(1)) - 1
        if entry_index < 0 or entry_index >= len(image_entries):
            return ""
        if entry_index in used_indices:
            return ""
        rendered = _render_image_block(image_entries[entry_index], next_image_number, confidence=5.0)
        if not rendered:
            return ""
        used_indices.add(entry_index)
        next_image_number += 1
        return f"\n\n{rendered}\n\n"

    replaced = ANCHOR_RE.sub(repl, content)
    remaining_entries = [entry for index, entry in enumerate(image_entries) if index not in used_indices]
    return normalize_markdown_content(replaced), remaining_entries, next_image_number


def inject_images_into_markdown(content: str, image_entries: list[dict[str, str]]) -> str:
    """将截图和结构化图示注入 Markdown。

    流程：
    1. 先替换 LLM 生成的 [[插图N]] 锚点（精确位置）
    2. 剩余截图按语义评分（_score_entry_against_section）分配到各章节
    3. 结构化图示追加到文末
    4. 每个章节最多 2 张截图，最低评分阈值 2.6
    """
    if not image_entries:
        return content
    screenshot_entries, diagram_entries = _split_entry_kinds(image_entries)
    anchored = normalize_markdown_content(content)
    next_image_number = 1
    if screenshot_entries:
        anchored, remaining_entries, next_image_number = _replace_image_anchors(content, screenshot_entries)
        if remaining_entries:
            normalized = normalize_markdown_content(anchored)
            prefix, sections = _split_markdown_sections(normalized)
            if not sections:
                appendix = _build_appendix_block(remaining_entries, next_image_number)
                anchored = normalize_markdown_content(f"{normalized}\n{appendix}")
            else:
                candidates: list[dict] = []
                for entry_index, entry in enumerate(remaining_entries):
                    for section_index, section in enumerate(sections):
                        score = _score_entry_against_section(entry, section, section_index, len(sections))
                        if score <= 0:
                            continue
                        candidates.append(
                            {
                                "entry_index": entry_index,
                                "section_index": section_index,
                                "score": score,
                            }
                        )
                candidates.sort(key=lambda item: item["score"], reverse=True)

                max_per_section = 1 if len(remaining_entries) <= len(sections) else 2
                assigned_entries: set[int] = set()
                section_counts = [0] * len(sections)
                section_images: list[list[tuple[int, dict[str, str], float]]] = [[] for _ in sections]
                appendix_entries: list[dict[str, str]] = []

                for candidate in candidates:
                    entry_index = candidate["entry_index"]
                    section_index = candidate["section_index"]
                    score = candidate["score"]
                    if entry_index in assigned_entries:
                        continue
                    if score < 2.6:
                        continue
                    if section_counts[section_index] >= max_per_section:
                        continue
                    section_images[section_index].append((entry_index, remaining_entries[entry_index], score))
                    section_counts[section_index] += 1
                    assigned_entries.add(entry_index)

                strong_fallback_sections = sorted(
                    range(len(sections)),
                    key=lambda idx: len(_extract_tokens(sections[idx]["heading"] + " " + sections[idx]["subsections"] + " " + sections[idx]["excerpt"])),
                    reverse=True,
                )
                for entry_index, entry in enumerate(remaining_entries):
                    if entry_index in assigned_entries:
                        continue
                    placed = False
                    for section_index in strong_fallback_sections:
                        if section_counts[section_index] >= max_per_section:
                            continue
                        if len(remaining_entries) <= len(sections):
                            break
                        section_images[section_index].append((entry_index, entry, 0.0))
                        section_counts[section_index] += 1
                        assigned_entries.add(entry_index)
                        placed = True
                        break
                    if not placed:
                        appendix_entries.append(entry)

                built: list[str] = []
                if prefix.strip():
                    built.append(prefix.rstrip() + "\n\n")
                image_number = next_image_number
                for section_index, section in enumerate(sections):
                    built.append(section["block"].rstrip() + "\n")
                    if section_images[section_index]:
                        for _entry_index, entry, score in sorted(section_images[section_index], key=lambda item: item[0]):
                            built.append("\n" + _render_image_block(entry, image_number, score) + "\n")
                            image_number += 1
                if appendix_entries:
                    built.append("\n" + _build_appendix_block(appendix_entries, image_number))
                anchored = normalize_markdown_content("".join(built))
                next_image_number = image_number
    if diagram_entries:
        diagram_block = _build_appendix_block(diagram_entries, next_image_number)
        anchored = normalize_markdown_content(f"{anchored}\n{diagram_block}")
    return anchored


def write_summary_markdown(
    out_path: str,
    source_path: str,
    content: str,
    image_entries: list[dict[str, str]] | None = None,
    provider_label: str = "",
    model_name: str = "",
    now: datetime | None = None,
) -> None:
    dt = now or datetime.now()
    stem = os.path.splitext(os.path.basename(source_path))[0]
    normalized = inject_images_into_markdown(content or "", image_entries or [])
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"# {stem} 课堂总结\n\n")
        f.write(
            f"> 生成时间：{dt.strftime('%Y-%m-%d %H:%M:%S')}  \n"
            f"> 源文件：`{source_path}`  \n"
            f"> 模型平台：{provider_label or '未标注'}  \n"
            f"> 模型名称：{model_name or '未标注'}\n\n---\n\n"
        )
        f.write(normalized)
