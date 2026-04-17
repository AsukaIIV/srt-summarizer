import os
from datetime import datetime


def _sanitize_name_part(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in str(value).strip())
    cleaned = cleaned.strip("._-")
    return cleaned or "未命名课程"


def _is_same_content(candidate: dict, selected_candidates: list[dict]) -> bool:
    return _is_similar_frame(candidate["preview"], [item["preview"] for item in selected_candidates])


def _build_candidate_positions(frame_count: int, candidate_count: int) -> list[int]:
    if frame_count <= 0:
        return []
    start = max(int(frame_count * 0.05), 0)
    end = min(int(frame_count * 0.95), max(frame_count - 1, 0))
    if end <= start:
        start, end = 0, max(frame_count - 1, 0)
    if candidate_count <= 1 or end <= start:
        return [start]
    step = (end - start) / max(candidate_count - 1, 1)
    positions: list[int] = []
    seen: set[int] = set()
    for index in range(candidate_count):
        pos = min(max(int(round(start + index * step)), 0), max(frame_count - 1, 0))
        if pos in seen:
            continue
        seen.add(pos)
        positions.append(pos)
    return positions


def _build_subtitle_positions(segments: list[dict], fps: float, frame_count: int, max_frames: int) -> list[int]:
    if not segments or fps <= 0:
        return []
    picked: list[int] = []
    seen: set[int] = set()
    sorted_segments = sorted(
        (
            segment for segment in segments
            if isinstance(segment.get("text"), str)
            and len(str(segment.get("text", "")).strip()) >= 6
            and float(segment.get("end_seconds", 0)) > float(segment.get("start_seconds", 0))
        ),
        key=lambda item: float(item.get("start_seconds", 0)),
    )
    if not sorted_segments:
        return []
    stride = max(len(sorted_segments) // max(max_frames * 3, 1), 1)
    for index, segment in enumerate(sorted_segments[::stride]):
        if len(picked) >= max(max_frames * 6, 18):
            break
        start_seconds = float(segment["start_seconds"])
        end_seconds = float(segment["end_seconds"])
        midpoint = start_seconds + (end_seconds - start_seconds) / 2
        position = min(max(int(round(midpoint * fps)), 0), max(frame_count - 1, 0))
        if position in seen:
            continue
        seen.add(position)
        picked.append(position)
    return picked


def _build_planned_positions(planned_moments: list[float], fps: float, frame_count: int) -> list[int]:
    if not planned_moments or fps <= 0 or frame_count <= 0:
        return []
    positions: list[int] = []
    seen: set[int] = set()
    for seconds in planned_moments:
        try:
            moment = float(seconds)
        except (TypeError, ValueError):
            continue
        if moment < 0:
            continue
        position = min(max(int(round(moment * fps)), 0), max(frame_count - 1, 0))
        if position in seen:
            continue
        seen.add(position)
        positions.append(position)
    return positions


def _score_frame(cv2, frame) -> tuple[float, dict[str, float], object]:
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    brightness = float(gray.mean())
    blur = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    edges = cv2.Canny(gray, 80, 160)
    edge_density = float((edges > 0).mean())
    downsampled = cv2.resize(gray, (64, 36))

    score = 0.0
    if 25 <= brightness <= 235:
        score += 2.0
    elif 15 <= brightness <= 245:
        score += 1.0
    score += min(blur / 120.0, 3.0)
    score += min(edge_density * 12.0, 3.0)
    return score, {
        "brightness": brightness,
        "blur": blur,
        "edge_density": edge_density,
    }, downsampled


def _is_similar_frame(candidate_preview, selected_previews: list[object]) -> bool:
    for preview in selected_previews:
        diff = abs(candidate_preview.astype("float32") - preview.astype("float32")).mean()
        if diff < 12.0:
            return True
    return False


def _select_best_candidates(candidates: list[dict], max_frames: int, allow_low_quality: bool = False) -> list[dict]:
    selected: list[dict] = []
    for candidate in sorted(candidates, key=lambda item: item["score"], reverse=True):
        metrics = candidate["metrics"]
        if not allow_low_quality:
            if metrics["brightness"] < 20 or metrics["brightness"] > 240:
                continue
            if metrics["blur"] < 40:
                continue
            if metrics["edge_density"] < 0.01:
                continue
        if _is_same_content(candidate, selected):
            continue
        selected.append(candidate)
        if len(selected) >= max_frames:
            break
    return sorted(selected, key=lambda item: item["position"])


def _build_image_filename(course_name: str, sequence: int, identifier: str, now: datetime | None = None) -> str:
    dt = now or datetime.now()
    date_part = dt.strftime("%Y%m%d")
    course_part = _sanitize_name_part(course_name)
    id_part = _sanitize_name_part(identifier)
    return f"{date_part}_{course_part}_{sequence:03d}_{id_part}.png"


def _write_image(cv2, out_path: str, frame) -> bool:
    ext = os.path.splitext(out_path)[1] or ".png"
    ok, encoded = cv2.imencode(ext, frame)
    if not ok:
        return False
    try:
        encoded.tofile(out_path)
    except OSError:
        return False
    return True


def _save_selected_frames(cv2, image_dir: str, candidates: list[dict], course_name: str = "") -> list[str]:
    os.makedirs(image_dir, exist_ok=True)
    saved: list[str] = []
    for index, candidate in enumerate(candidates, start=1):
        identifier = candidate.get("timestamp_id") or f"frame-{candidate.get('position', index)}"
        out_path = os.path.join(image_dir, _build_image_filename(course_name, index, str(identifier)))
        if _write_image(cv2, out_path, candidate["frame"]):
            saved.append(out_path)
    return saved


def _fallback_uniform_frames(cv2, cap, frame_count: int, image_dir: str, max_frames: int, course_name: str = "") -> list[str]:
    step = max(frame_count // max_frames, 1)
    candidates: list[dict] = []
    for index in range(max_frames):
        position = min(index * step, max(frame_count - 1, 0))
        cap.set(cv2.CAP_PROP_POS_FRAMES, position)
        ok, frame = cap.read()
        if not ok:
            continue
        candidates.append(
            {
                "position": position,
                "frame": frame,
                "preview": _score_frame(cv2, frame)[2],
                "timestamp_id": f"frame-{position}",
            }
        )
    unique_candidates: list[dict] = []
    for candidate in candidates:
        if _is_same_content(candidate, unique_candidates):
            continue
        unique_candidates.append(candidate)
        if len(unique_candidates) >= max_frames:
            break
    return _save_selected_frames(cv2, image_dir, unique_candidates, course_name=course_name)


def _format_seconds(seconds: float) -> str:
    total_ms = max(int(round(seconds * 1000)), 0)
    hours = total_ms // 3600000
    minutes = (total_ms % 3600000) // 60000
    secs = (total_ms % 60000) // 1000
    millis = total_ms % 1000
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"


def _find_related_segment(segments: list[dict], seconds: float) -> dict | None:
    if not segments:
        return None
    best_segment = None
    best_distance = None
    for segment in segments:
        start_seconds = float(segment.get("start_seconds", 0))
        end_seconds = float(segment.get("end_seconds", 0))
        if start_seconds <= seconds <= end_seconds:
            return segment
        midpoint = start_seconds + max(end_seconds - start_seconds, 0) / 2
        distance = abs(midpoint - seconds)
        if best_distance is None or distance < best_distance:
            best_distance = distance
            best_segment = segment
    return best_segment


def _build_frame_items(saved_paths: list[str], selected: list[dict], fps: float, subtitle_segments: list[dict]) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for path, candidate in zip(saved_paths, selected):
        seconds = candidate["position"] / fps if fps > 0 else 0.0
        segment = _find_related_segment(subtitle_segments, seconds)
        snippet = ""
        if segment:
            snippet = str(segment.get("text", "")).strip().replace("\n", " ")[:80]
        items.append(
            {
                "path": path,
                "timestamp": _format_seconds(seconds),
                "snippet": snippet,
            }
        )
    return items


def extract_video_frame_items(
    video_path: str,
    image_dir: str,
    max_frames: int = 8,
    subtitle_segments: list[dict] | None = None,
    course_name: str = "",
    planned_moments: list[float] | None = None,
) -> list[dict[str, str]]:
    if not video_path:
        return []
    try:
        import cv2
    except ImportError as e:
        raise RuntimeError("缺少 opencv-python，无法处理视频截图") from e

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"无法打开视频：{video_path}")

    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    if frame_count <= 0:
        cap.release()
        return []

    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
    max_frames = max(1, min(max_frames, 20))
    candidate_count = min(max(max_frames * 8, 24), 120)
    candidates: list[dict] = []
    normalized_segments = subtitle_segments or []
    positions = _build_planned_positions(planned_moments or [], fps, frame_count)
    subtitle_positions = _build_subtitle_positions(normalized_segments, fps, frame_count, max_frames)
    seen_positions = set(positions)
    for position in subtitle_positions:
        if position in seen_positions:
            continue
        positions.append(position)
        seen_positions.add(position)
    if len(positions) < candidate_count:
        extra_positions = _build_candidate_positions(frame_count, candidate_count)
        for position in extra_positions:
            if position in seen_positions:
                continue
            positions.append(position)
            seen_positions.add(position)
    for position in positions:
        cap.set(cv2.CAP_PROP_POS_FRAMES, position)
        ok, frame = cap.read()
        if not ok:
            continue
        score, metrics, preview = _score_frame(cv2, frame)
        candidates.append(
            {
                "position": position,
                "frame": frame,
                "score": score,
                "metrics": metrics,
                "preview": preview,
                "timestamp_id": _format_seconds(position / fps if fps > 0 else 0.0).replace(":", "-").replace(".", "-"),
            }
        )

    if not candidates:
        cap.release()
        raise RuntimeError("无法提取截图：未能从视频读取到任何帧")

    selected = _select_best_candidates(candidates, max_frames)
    if len(selected) < max_frames:
        seen_positions = {item["position"] for item in selected}
        relaxed_pool = [item for item in candidates if item["position"] not in seen_positions]
        selected.extend(_select_best_candidates(relaxed_pool, max_frames - len(selected), allow_low_quality=True))
        selected = sorted(selected, key=lambda item: item["position"])

    if not selected:
        cap.release()
        raise RuntimeError("无法提取有效截图：读取到了视频帧，但都未通过有效性筛选")

    saved = _save_selected_frames(cv2, image_dir, selected, course_name=course_name)
    if len(saved) < max_frames:
        fallback_saved = _fallback_uniform_frames(cv2, cap, frame_count, image_dir, max_frames, course_name=course_name)
        if len(fallback_saved) > len(saved):
            saved = fallback_saved
            selected = [
                {"position": min(index * max(frame_count // max_frames, 1), max(frame_count - 1, 0))}
                for index in range(len(saved))
            ]

    cap.release()
    return _build_frame_items(saved, selected, fps, normalized_segments)


def extract_video_frames(
    video_path: str,
    image_dir: str,
    max_frames: int = 8,
    subtitle_segments: list[dict] | None = None,
    course_name: str = "",
    planned_moments: list[float] | None = None,
) -> list[str]:
    return [
        item["path"]
        for item in extract_video_frame_items(
            video_path,
            image_dir,
            max_frames=max_frames,
            subtitle_segments=subtitle_segments,
            course_name=course_name,
            planned_moments=planned_moments,
        )
    ]
