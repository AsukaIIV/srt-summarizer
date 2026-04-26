import os
import re


SRT_TIME_RE = re.compile(
    r"(?P<start>\d{2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*(?P<end>\d{2}:\d{2}:\d{2}[,.]\d{3})"
)


def _parse_srt_timestamp(value: str) -> float:
    hours, minutes, seconds = re.split(r":", value.replace(",", "."))
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def parse_file(filepath: str) -> str:
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            raw = f.read()
    except OSError as e:
        raise ValueError(f"读取文件失败：{e}") from e

    content = raw.strip()
    if not content:
        raise ValueError("输入文件内容为空")
    return content


def parse_srt_segments(filepath: str) -> list[dict[str, float | str]]:
    """解析 .srt 文件，提取字幕段。

    每段返回 start_seconds、end_seconds、text。
    跳过序号行、无效时间戳、空文本段。
    非 .srt 文件返回空列表。
    """
    if not filepath.lower().endswith(".srt"):
        return []
    content = parse_file(filepath)
    blocks = re.split(r"\n\s*\n", content)
    segments: list[dict[str, float | str]] = []
    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        time_line = next((line for line in lines if "-->" in line), "")
        match = SRT_TIME_RE.search(time_line)
        if not match:
            continue
        text_lines = [line for line in lines if line != time_line and not line.isdigit()]
        text = " ".join(text_lines).strip()
        if not text:
            continue
        start_seconds = _parse_srt_timestamp(match.group("start"))
        end_seconds = _parse_srt_timestamp(match.group("end"))
        if end_seconds <= start_seconds:
            continue
        segments.append(
            {
                "start_seconds": start_seconds,
                "end_seconds": end_seconds,
                "text": text,
            }
        )
    return segments
