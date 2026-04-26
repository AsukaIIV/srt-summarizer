import os
import re

from srt_summarizer.constants import SUPPORTED_VIDEO_EXT
from srt_summarizer.processing.input_models import LessonInput


NOISE_TOKENS = {"1080p", "720p", "2160p", "avc", "hevc", "x264", "x265", "h264", "h265", "字幕", "subtitle", "sub", "chs", "cht", "eng", "aac"}


def normalize_video_files(paths) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for path in paths:
        if not path.lower().endswith(SUPPORTED_VIDEO_EXT):
            continue
        if path in seen:
            continue
        seen.add(path)
        normalized.append(path)
    return normalized


def _normalize_name(path: str) -> str:
    stem = os.path.splitext(os.path.basename(path))[0].lower()
    stem = re.sub(r"[\[\](){}._\-]+", " ", stem)
    stem = re.sub(r"\s+", " ", stem).strip()
    tokens = [token for token in stem.split() if token and token not in NOISE_TOKENS]
    return " ".join(tokens)


def _score_match(transcript_path: str, video_path: str) -> float:
    transcript_tokens = set(_normalize_name(transcript_path).split())
    video_tokens = set(_normalize_name(video_path).split())
    if not transcript_tokens or not video_tokens:
        return 0.0
    overlap = transcript_tokens & video_tokens
    union = transcript_tokens | video_tokens
    score = len(overlap) / max(len(union), 1)
    transcript_stem = os.path.splitext(os.path.basename(transcript_path))[0].lower()
    video_stem = os.path.splitext(os.path.basename(video_path))[0].lower()
    if transcript_stem in video_stem or video_stem in transcript_stem:
        score += 0.2
    return score


def _match_video(transcript_path: str, video_paths: list[str], exact_map: dict[str, str], normalized_map: dict[str, str]) -> str:
    stem = os.path.splitext(os.path.basename(transcript_path))[0]
    exact = exact_map.get(stem.lower(), "")
    if exact:
        return exact
    normalized_name = _normalize_name(transcript_path)
    normalized = normalized_map.get(normalized_name, "")
    if normalized:
        return normalized
    scored = sorted(((path, _score_match(transcript_path, path)) for path in video_paths), key=lambda item: item[1], reverse=True)
    if not scored:
        return ""
    best_path, best_score = scored[0]
    second_score = scored[1][1] if len(scored) > 1 else 0.0
    if best_score >= 0.45 and best_score - second_score >= 0.1:
        return best_path
    return ""


def pair_lessons(transcript_paths: list[str], video_paths: list[str]) -> list[LessonInput]:
    """将字幕路径与视频路径一一配对，返回课程输入列表。

    配对策略：
    1. 精确文件名匹配（去后缀、忽略大小写）
    2. 标准化名称匹配（去除分辨率/编码标签）
    3. Jaccard 相似度评分（阈值 >= 0.45，分差 >= 0.1）
    """
    videos_by_stem = {
        os.path.splitext(os.path.basename(path))[0].lower(): path for path in video_paths
    }
    videos_by_normalized = {
        _normalize_name(path): path for path in video_paths if _normalize_name(path)
    }
    lessons: list[LessonInput] = []
    for transcript_path in transcript_paths:
        stem = os.path.splitext(os.path.basename(transcript_path))[0]
        lessons.append(
            LessonInput(
                lesson_id=transcript_path,
                transcript_path=transcript_path,
                video_path=_match_video(transcript_path, video_paths, videos_by_stem, videos_by_normalized),
                source_label=stem,
            )
        )
    return lessons
