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


def summarize_content_density(segments: list[dict[str, float | str]]) -> dict[str, float | int | list[dict[str, float]]]:
    if not segments:
        return {
            "duration_seconds": 0.0,
            "segment_count": 0,
            "total_chars": 0,
            "avg_chars_per_minute": 0.0,
            "peak_chars_per_minute": 0.0,
            "dense_ranges": [],
        }
    ordered = sorted(segments, key=lambda item: float(item.get("start_seconds", 0)))
    duration_seconds = max(float(ordered[-1].get("end_seconds", 0)) - float(ordered[0].get("start_seconds", 0)), 0.0)
    total_chars = sum(len(str(item.get("text", "")).strip()) for item in ordered)
    avg_chars_per_minute = total_chars / max(duration_seconds / 60, 1e-6)
    windows: list[dict[str, float]] = []
    peak_chars_per_minute = 0.0
    for segment in ordered:
        start = float(segment.get("start_seconds", 0))
        window_end = start + 60.0
        chars = 0
        for other in ordered:
            other_start = float(other.get("start_seconds", 0))
            if start <= other_start < window_end:
                chars += len(str(other.get("text", "")).strip())
        peak_chars_per_minute = max(peak_chars_per_minute, float(chars))
        windows.append({"start": start, "end": min(window_end, float(ordered[-1].get("end_seconds", 0))), "chars": float(chars)})
    dense_ranges = [
        {"start": window["start"], "end": window["end"], "chars": window["chars"]}
        for window in sorted(windows, key=lambda item: item["chars"], reverse=True)[:5]
        if window["chars"] > 0
    ]
    return {
        "duration_seconds": round(duration_seconds, 2),
        "segment_count": len(ordered),
        "total_chars": total_chars,
        "avg_chars_per_minute": round(avg_chars_per_minute, 2),
        "peak_chars_per_minute": round(peak_chars_per_minute, 2),
        "dense_ranges": dense_ranges,
    }
