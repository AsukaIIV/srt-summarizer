from __future__ import annotations

import asyncio
import json
import os
import threading
import uuid

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from srt_summarizer.config import _invalidate_config_cache, get_runtime_config
from srt_summarizer.processing.course_context import build_course_context
from srt_summarizer.processing.diagram_renderer import get_last_font_source, render_diagram_entries
from srt_summarizer.processing.diagram_specs import extract_diagram_specs
from srt_summarizer.processing.file_loader import parse_file, parse_srt_segments
from srt_summarizer.processing.lesson_pairing import pair_lessons
from srt_summarizer.processing.output_writer import build_output_paths, resolve_output_dir, write_summary_markdown
from srt_summarizer.processing.video_frames import extract_video_frame_items
from srt_summarizer.services.config_store import save_runtime_config, RuntimeConfig
from srt_summarizer.services.dependency_check import (
    describe_ffmpeg_source,
    ensure_runtime_dependencies,
    has_ffmpeg,
    resolve_ffmpeg_executable,
)
from srt_summarizer.services.llm_client import stream_completion
from srt_summarizer.services.prompt_builder import build_user_prompt, guess_course_name
from srt_summarizer.services.provider_registry import get_provider

from server.models.schemas import RunStartRequest, RunStartResponse, RunStatusResponse
from server.session import RunState, get_session

router = APIRouter(prefix="/api", tags=["run"])

# SSE streaming endpoint also handled by this router


@router.post("/run/start", response_model=RunStartResponse)
async def start_run(body: RunStartRequest):
    session = get_session()
    if session.current_run and session.current_run.running:
        raise HTTPException(409, "已有任务正在运行")

    if not session.transcript_files:
        raise HTTPException(400, "请先添加至少一个字幕文件")

    config = get_runtime_config()
    output_dir = body.output_dir.strip() if body.output_dir else ""
    save_to_source = body.save_to_source

    # Validate
    if save_to_source:
        for path in session.transcript_files:
            source_dir = os.path.dirname(path)
            if not os.path.isdir(source_dir):
                raise HTTPException(400, f"源文件目录不存在：{source_dir}")
    else:
        if not output_dir:
            raise HTTPException(400, "请设置输出目录或启用输出到源目录")

    session.output_dir = output_dir
    session.save_to_source = save_to_source
    session.course_name = body.course_name
    session.requirements_text = body.requirements_text

    run_id = uuid.uuid4().hex[:12]
    queue = asyncio.Queue()
    cancel_evt = asyncio.Event()
    run_state = RunState(run_id=run_id, queue=queue, cancel_event=cancel_evt)
    session.current_run = run_state

    # Launch pipeline in background
    asyncio.create_task(_run_pipeline_async(
        config, output_dir, body.course_name, body.requirements_text,
        session, run_state,
    ))

    return RunStartResponse(run_id=run_id)


@router.post("/run/cancel")
async def cancel_run():
    session = get_session()
    if session.current_run:
        session.current_run.cancel_event.set()
        session.current_run.running = False
    return {"ok": True}


@router.get("/run/status", response_model=RunStatusResponse)
async def run_status():
    session = get_session()
    run = session.current_run
    if not run or not run.running:
        return RunStatusResponse(running=False)
    return RunStatusResponse(running=True, progress=0.0)


@router.get("/stream/output")
async def stream_output(run_id: str = Query(...)):
    session = get_session()
    run = session.current_run
    if not run or run.run_id != run_id:
        raise HTTPException(404, "未找到对应的运行任务")

    async def event_generator():
        while True:
            msg = await run.queue.get()
            if msg is None:
                break
            event_type = msg["event"]
            data = msg["data"]
            yield f"event: {event_type}\ndata: {data}\n\n"
            if event_type in ("complete",):
                break

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def _run_pipeline_async(config, output_dir, course_name, requirements_text, session, run_state):
    loop = asyncio.get_running_loop()

    def push(event_type, data):
        asyncio.run_coroutine_threadsafe(
            run_state.queue.put({"event": event_type, "data": json.dumps(data, ensure_ascii=False)}),
            loop,
        )

    def push_done():
        asyncio.run_coroutine_threadsafe(
            run_state.queue.put(None),  # Sentinel
            loop,
        )

    def sync_run():
        try:
            _sync_run_all(config, output_dir, course_name, requirements_text, session, run_state, push)
        finally:
            push_done()

    await asyncio.to_thread(sync_run)


def _sync_run_all(config, output_dir, course_name, requirements_text, session, run_state, push):
    """Ported from srt_summarizer/ui/app.py App._run_all (lines 532-674)."""

    installed = ensure_runtime_dependencies()
    if installed:
        push("log", {"text": f"» 已自动安装依赖：{', '.join(installed)}\n", "tag": "success"})

    if session.video_files:
        ffmpeg_path = resolve_ffmpeg_executable()
        ffmpeg_source = describe_ffmpeg_source()
        if ffmpeg_path and ffmpeg_source == "bundled":
            push("log", {"text": f"» 已检测到内置 ffmpeg：{ffmpeg_path}\n", "tag": "dim"})
        elif ffmpeg_path and ffmpeg_source == "system":
            push("log", {"text": f"» 已检测到系统 ffmpeg：{ffmpeg_path}\n", "tag": "dim"})
        elif not has_ffmpeg():
            push("log", {"text": "» 未检测到 ffmpeg，当前使用 OpenCV 规则抽帧\n", "tag": "dim"})

    lessons = pair_lessons(session.transcript_files, session.video_files)
    total = len(lessons)
    ok = fail = 0
    context = build_course_context(course_name, requirements_text, session.prior_note_files)

    for idx, lesson in enumerate(lessons):
        if run_state.cancel_event.is_set():
            push("log", {"text": "\n» 任务已取消\n", "tag": "dim"})
            break

        name = os.path.basename(lesson.transcript_path)
        mode_label = "图文混排" if lesson.video_path else "纯字幕"
        mode_result_label = mode_label

        push("tree_update", {
            "path": lesson.transcript_path,
            "status": "解析中…",
            "tag": "doing",
            "mode": "",
        })
        push("progress", {
            "current": idx + 1,
            "total": total,
            "percentage": 0,
            "filename": name,
            "mode": mode_label,
        })
        push("status", {"message": f"处理 {idx+1}/{total} · {mode_label}"})
        push("log", {"text": f"\n{'─' * 60}\n  [{idx+1}/{total}]  {name} · {mode_label}\n{'─' * 60}\n", "tag": "dim"})

        try:
            transcript = parse_file(lesson.transcript_path)
            course_name_guessed = guess_course_name(transcript, lesson, context)
            save_dir = resolve_output_dir(lesson.transcript_path, output_dir, session.save_to_source)
            bundle_dir, image_dir, note_path = build_output_paths(
                lesson.transcript_path, save_dir, course_name_guessed
            )
            os.makedirs(bundle_dir, exist_ok=True)
            image_paths = []
            image_markdown_lines = []
            image_entries = []

            if lesson.video_path:
                subtitle_segments = parse_srt_segments(lesson.transcript_path)
                frame_items = extract_video_frame_items(
                    lesson.video_path,
                    image_dir,
                    max_frames=8,
                    subtitle_segments=subtitle_segments,
                    course_name=course_name_guessed,
                )
                image_paths = [item["path"] for item in frame_items]
                if not image_paths:
                    raise RuntimeError("视频任务未生成有效截图，无法进行图文混排")
                image_entries = [
                    {
                        "relative_path": f"imgs/{os.path.basename(item['path'])}",
                        "timestamp": item.get("timestamp", ""),
                        "snippet": item.get("snippet", ""),
                    }
                    for item in frame_items
                ]
                image_markdown_lines = [
                    f"- 截图 {i}: ![课堂截图 {i}]({entry['relative_path']})"
                    + (f"（时间：{entry['timestamp']}；内容提示：{entry['snippet']}）" if entry.get("snippet") else f"（时间：{entry['timestamp']}）")
                    for i, entry in enumerate(image_entries, start=1)
                ]
                push("log", {"text": f"» 已提取 {len(image_paths)} 张课堂截图，将按图文混排生成\n", "tag": "dim"})

            prompt = build_user_prompt(transcript, lesson, context, image_markdown_lines)
            push("tree_update", {
                "path": lesson.transcript_path,
                "status": "生成中…",
                "tag": "doing",
                "mode": "",
            })

            token_count = [0]
            done_evt = threading.Event()
            result_box = [None]
            err_box = [None]

            def on_token(delta):
                token_count[0] += len(delta)
                push("token", {"delta": delta, "total_chars": token_count[0]})

            def on_done(full):
                result_box[0] = full
                done_evt.set()

            def on_error(msg):
                err_box[0] = msg
                done_evt.set()

            stream_completion(config, prompt, on_token, on_done, on_error)
            done_evt.wait()

            if err_box[0]:
                raise RuntimeError(err_box[0])

            clean_result, diagram_specs, diagram_parse_warnings = extract_diagram_specs(result_box[0] or "")
            for warning in diagram_parse_warnings:
                push("log", {"text": f"» {warning}\n", "tag": "dim"})
            diagram_entries, diagram_render_warnings = render_diagram_entries(diagram_specs, image_dir)
            if diagram_entries:
                push("log", {"text": f"» 已生成 {len(diagram_entries)} 张结构化图示\n", "tag": "dim"})
                push("log", {"text": f"» 图示字体：{get_last_font_source()}\n", "tag": "dim"})
            for warning in diagram_render_warnings:
                push("log", {"text": f"» {warning}\n", "tag": "dim"})

            all_image_entries = image_entries + diagram_entries
            write_summary_markdown(
                note_path,
                lesson.transcript_path,
                clean_result,
                image_entries=all_image_entries,
                provider_label=get_provider(config.provider).label,
                model_name=config.model,
            )
            push("tree_update", {
                "path": lesson.transcript_path,
                "status": "✓ 完成",
                "tag": "done",
                "mode": mode_result_label,
            })
            push("log", {"text": f"» 输出目录：{bundle_dir}\n» 已保存：{note_path}\n", "tag": "success"})
            ok += 1
        except BaseException as e:
            if isinstance(e, (KeyboardInterrupt, SystemExit)):
                raise
            push("tree_update", {
                "path": lesson.transcript_path,
                "status": "✗ 失败",
                "tag": "fail",
                "mode": "",
            })
            push("log", {"text": f"\n» 失败：{e}\n", "tag": "error"})
            fail += 1

        pct = int((idx + 1) / total * 100)
        push("progress", {
            "current": idx + 1,
            "total": total,
            "percentage": pct,
            "filename": name,
            "mode": mode_label,
        })

    run_state.running = False
    save_runtime_config(config)
    _invalidate_config_cache()
    output_summary = "各源文件所在目录" if session.save_to_source else (output_dir or "未指定")
    push("complete", {
        "success_count": ok,
        "fail_count": fail,
        "output_summary": output_summary,
    })
