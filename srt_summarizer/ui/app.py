import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from srt_summarizer.config import (
    DEFAULT_COURSE_NAME,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_SAVE_TO_SOURCE,
    get_config_errors,
    get_runtime_config,
)
from srt_summarizer.constants import C, COMPACT_BREAKPOINT, DEFAULT_MIN_SIZE, DEFAULT_WINDOW_SIZE, UI_METRICS
from srt_summarizer.processing.course_context import build_course_context
from srt_summarizer.processing.diagram_renderer import get_last_font_source, render_diagram_entries
from srt_summarizer.processing.diagram_specs import extract_diagram_specs
from srt_summarizer.processing.file_loader import parse_file, parse_srt_segments
from srt_summarizer.processing.file_scanner import normalize_selected_files, scan_supported_files, scan_video_files
from srt_summarizer.processing.lesson_pairing import normalize_video_files, pair_lessons
from srt_summarizer.processing.output_writer import build_output_paths, resolve_output_dir, write_summary_markdown
from srt_summarizer.processing.video_frames import extract_video_frame_items
from srt_summarizer.services.config_store import RuntimeConfig, load_provider_runtime_state, save_runtime_config
from srt_summarizer.services.dependency_check import (
    check_video_dependencies,
    describe_ffmpeg_source,
    ensure_runtime_dependencies,
    has_ffmpeg,
    resolve_ffmpeg_executable,
)
from srt_summarizer.services.llm_client import stream_completion, test_runtime_config
from srt_summarizer.services.prompt_builder import build_user_prompt, guess_course_name
from srt_summarizer.services.provider_registry import get_provider, get_provider_labels
from srt_summarizer.ui.pages.config_page import ConfigPage
from srt_summarizer.ui.pages.course_page import CoursePage
from srt_summarizer.ui.pages.run_page import RunPage
from srt_summarizer.ui.pages.status_page import StatusPage
from srt_summarizer.ui.theme import build_ttk_style, set_tree_density
from srt_summarizer.ui.widgets import Divider, StatusChip
from srt_summarizer.utils.markdown import choose_stream_tag


FONT = UI_METRICS["font"]
SPACE = UI_METRICS["space"]


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SRT-SUMMARIZER")
        self.configure(bg=C["bg"])
        self.resizable(True, True)

        self._transcript_files: list[str] = []
        self._video_files: list[str] = []
        self._prior_note_files: list[str] = []
        self._running = False
        self._compact_mode = False
        self._default_output_dir = self._resolve_default_output_dir()
        self._config_tested_ok = False
        self._testing_config = False
        self._provider_labels = get_provider_labels()
        self._video_dependency_status = check_video_dependencies()
        self._suspend_provider_memory_sync = False

        self._apply_window_geometry()
        build_ttk_style(self)
        self._load_initial_config()
        for var in (self._model_var, self._base_url_var, self._api_key_var):
            var.trace_add("write", self._on_config_field_changed)
        self._out_var.trace_add("write", self._on_output_dir_changed)
        self._prog_var = tk.DoubleVar(value=0)
        self._build_ui()
        self._refresh_provider_view()
        self._refresh_tree()
        self._update_source_button()
        self._update_output_controls()
        self._set_output_placeholder(True)
        self.after(0, self._resize_tree_columns)
        self.after(300, self._auto_validate_config_on_startup)
        self.bind("<Configure>", self._on_root_resize)

    def _load_initial_config(self):
        config = get_runtime_config()
        provider_models, provider_urls, provider_api_keys = load_provider_runtime_state()
        self._provider_var = tk.StringVar(value=config.provider)
        self._model_var = tk.StringVar(value=config.model)
        self._base_url_var = tk.StringVar(value=config.base_url)
        self._api_key_var = tk.StringVar(value=config.api_key)
        self._course_name_var = tk.StringVar(value=config.course_name or DEFAULT_COURSE_NAME)
        self._out_var = tk.StringVar(value=config.output_dir or DEFAULT_OUTPUT_DIR or self._default_output_dir)
        self._output_hint_var = tk.StringVar(value="")
        self._config_validation_msg_var = tk.StringVar(value="")
        self._dir_var = tk.StringVar()
        self._save_to_src = tk.BooleanVar(value=config.save_to_source if config.output_dir or config.course_name or config.api_key else DEFAULT_SAVE_TO_SOURCE)
        self._stat_var = tk.StringVar(value="0")
        self._extra_stat_var = tk.StringVar(value="字幕 0 / 视频 0 / 往期笔记 0")
        self._list_count_var = tk.StringVar(value="")
        self._status_var = tk.StringVar(value="就绪，请选择字幕文件或扫描目录")
        self._prog_label = tk.StringVar(value="就绪")
        self._prog_pct = tk.StringVar(value="")
        self._token_var = tk.StringVar(value="")
        self._cur_file_var = tk.StringVar(value="")
        self._pulse_var = tk.StringVar(value="")
        self._provider_model_memory: dict[str, str] = provider_models or {}
        self._provider_url_memory: dict[str, str] = provider_urls or {}
        self._provider_api_key_memory: dict[str, str] = provider_api_keys or {}
        if config.provider:
            self._provider_model_memory[config.provider] = config.model.strip()
            self._provider_url_memory[config.provider] = config.base_url.strip()
            self._provider_api_key_memory[config.provider] = config.api_key.strip()

    def _build_ui(self):
        nav = tk.Frame(self, bg=C["surface"], height=UI_METRICS["nav_height"] + 4)
        nav.pack(fill="x")
        nav.pack_propagate(False)
        nav.columnconfigure(0, weight=1)
        nav.columnconfigure(1, weight=0)

        self._title_block = tk.Frame(nav, bg=C["surface"])
        self._title_block.grid(row=0, column=0, sticky="w", padx=(SPACE["outer"], SPACE["section"]), pady=(6, 4))
        self._brand_row = tk.Frame(self._title_block, bg=C["surface"])
        self._brand_row.pack(anchor="w", pady=(2, 0))
        self._brand_mark = tk.Label(self._brand_row, text="✦", bg=C["surface"], fg="#8FC8FF", font=("Segoe UI", FONT["hero"] + 2, "bold"))
        self._brand_mark.pack(side="left")
        self._brand_label = tk.Label(self._brand_row, text="  SRT-SUMMARIZER", bg=C["surface"], fg="#CFE6FB", font=("Segoe UI", FONT["title"] + 1, "bold"))
        self._brand_label.pack(side="left")
        self._title_label = tk.Label(self._brand_row, text="  课堂资料整理", bg=C["surface"], fg="#FFFFFF", font=("Segoe UI", FONT["title"], "bold"))
        self._title_label.pack(side="left")

        self._right_nav = tk.Frame(nav, bg=C["surface"])
        self._right_nav.grid(row=0, column=1, sticky="e", padx=(SPACE["section"], SPACE["outer"]), pady=(6, 4))
        self._badge_row = tk.Frame(self._right_nav, bg=C["surface"])
        self._badge_row.pack(anchor="e", pady=(2, 0))
        self._config_chip = StatusChip(self._badge_row, "未配置", "error")
        self._config_chip.pack(side="left", padx=(0, SPACE["inline"]))
        self._provider_badge = StatusChip(self._badge_row, "", "info")
        self._provider_badge.pack(side="left")

        Divider(self).pack(fill="x")

        notebook_wrap = tk.Frame(self, bg=C["bg"])
        notebook_wrap.pack(fill="both", expand=True)
        self._notebook = ttk.Notebook(notebook_wrap)
        self._notebook.pack(fill="both", expand=True, padx=SPACE["outer"], pady=SPACE["section"])

        self._run_page = RunPage(self._notebook, self)
        self._course_page = CoursePage(self._notebook, self)
        self._status_page = StatusPage(self._notebook, self)
        self._config_page = ConfigPage(self._notebook, self)
        self._notebook.add(self._run_page, text="选择文件")
        self._notebook.add(self._course_page, text="课程设置")
        self._notebook.add(self._status_page, text="开始运行")
        self._notebook.add(self._config_page, text="API设置")

    def _resolve_default_output_dir(self) -> str:
        for path in [os.path.join(os.path.expanduser("~"), "Desktop"), os.path.expanduser("~"), os.getcwd()]:
            if os.path.isdir(path):
                return path
        return os.getcwd()

    def _apply_window_geometry(self):
        self.minsize(*DEFAULT_MIN_SIZE)
        screen_w = max(self.winfo_screenwidth(), DEFAULT_MIN_SIZE[0])
        screen_h = max(self.winfo_screenheight(), DEFAULT_MIN_SIZE[1])
        max_w = max(screen_w - 60, DEFAULT_MIN_SIZE[0])
        max_h = max(screen_h - 80, DEFAULT_MIN_SIZE[1])
        target_w = min(max(int(screen_w * 0.84), DEFAULT_WINDOW_SIZE[0]), max_w)
        target_h = min(max(int(screen_h * 0.82), DEFAULT_WINDOW_SIZE[1]), max_h)
        self.geometry(f"{target_w}x{target_h}")
        if screen_w >= 1600 and screen_h >= 900:
            try:
                self.state("zoomed")
            except tk.TclError:
                self.attributes("-zoomed", True)

    def _current_runtime_config(self) -> RuntimeConfig:
        return RuntimeConfig(
            provider=self._provider_var.get().strip(),
            model=self._model_var.get().strip(),
            base_url=self._base_url_var.get().strip(),
            api_key=self._api_key_var.get().strip(),
            output_dir=self._out_var.get().strip(),
            save_to_source=self._save_to_src.get(),
            course_name=self._course_name_var.get().strip(),
        )

    def _set_config_state_chip(self, text: str, tone: str):
        self._config_chip.set(text, tone)

    def _set_config_validation_message(self, message: str):
        self._config_validation_msg_var.set(message)

    def _refresh_provider_view(self):
        config = self._current_runtime_config()
        errors = get_config_errors(config)
        if errors:
            self._set_config_state_chip("未配置", "error")
        elif self._config_tested_ok:
            self._set_config_state_chip("已验证可用", "success")
        else:
            self._set_config_state_chip("已配置", "warn")
        provider = get_provider(config.provider)
        self._provider_badge.set(f"{provider.label} · {config.model}", "info")
        if hasattr(self, "_config_validation_msg_var") and not self._config_validation_msg_var.get().strip() and provider.config_help_text:
            self._set_config_validation_message(provider.config_help_text)

    def _refresh_tree(self):
        self._run_page.refresh_tree()

    def _update_source_button(self):
        self._src_btn.set_active(self._save_to_src.get(), text=f"输出到源目录：{'开' if self._save_to_src.get() else '关'}")

    def _update_output_controls(self):
        use_source_dir = self._save_to_src.get()
        if hasattr(self, "_out_entry"):
            self._out_entry.config(state="disabled" if use_source_dir else "normal")
        if hasattr(self, "_out_shell"):
            self._out_shell.config(bg=C["border2"] if use_source_dir else C["field"], highlightbackground=C["border"] if use_source_dir else C["border_subtle"])
        if hasattr(self, "_pick_output_btn"):
            self._pick_output_btn.set_enabled(not use_source_dir)
        hint = "已开启输出到源目录，当前输出目录不会生效" if use_source_dir else ""
        self._output_hint_var.set(hint)

    def _set_output_placeholder(self, visible: bool):
        self._out_placeholder_visible = visible
        self._out_placeholder.config(text="等待任务开始\n\n这里会显示模型实时输出、进度提示和生成结果摘要。")
        if visible:
            self._out_placeholder.place(relx=0.5, rely=0.45, anchor="center")
        else:
            self._out_placeholder.place_forget()

    def _on_provider_selected(self, _event=None):
        reverse = {label: key for key, label in self._provider_labels.items()}
        previous_provider = get_provider(self._provider_var.get())
        previous_provider_key = self._provider_var.get().strip()
        provider_key = reverse.get(self._provider_combo.get(), "deepseek")
        provider = get_provider(provider_key)
        old_model = self._model_var.get().strip()
        old_url = self._base_url_var.get().strip()
        old_api_key = self._api_key_var.get().strip()
        if previous_provider_key:
            self._provider_model_memory[previous_provider_key] = old_model or previous_provider.default_model
            self._provider_url_memory[previous_provider_key] = old_url or previous_provider.base_url
            self._provider_api_key_memory[previous_provider_key] = old_api_key

        remembered_url = self._provider_url_memory.get(provider.key, "").strip()
        next_url = remembered_url or provider.base_url
        remembered_model = self._provider_model_memory.get(provider.key, "").strip()
        next_model = remembered_model or provider.default_model
        next_api_key = self._provider_api_key_memory.get(provider.key, "").strip()

        self._suspend_provider_memory_sync = True
        try:
            self._provider_var.set(provider.key)
            self._base_url_var.set(next_url)
            self._model_var.set(next_model)
            self._api_key_var.set(next_api_key)
        finally:
            self._suspend_provider_memory_sync = False

        self._provider_model_memory[provider.key] = next_model
        self._provider_url_memory[provider.key] = next_url
        self._provider_api_key_memory[provider.key] = next_api_key
        self._status_var.set(f"已恢复 {provider.label} 的专属配置")
        self._config_tested_ok = False
        self._set_config_validation_message("")
        self._refresh_provider_view()

    def _on_config_field_changed(self, *_args):
        if getattr(self, "_suspend_provider_memory_sync", False):
            return
        provider_key = self._provider_var.get().strip()
        if provider_key:
            self._provider_model_memory[provider_key] = self._model_var.get().strip()
            self._provider_url_memory[provider_key] = self._base_url_var.get().strip()
            self._provider_api_key_memory[provider_key] = self._api_key_var.get().strip()
        self._config_tested_ok = False
        self._set_config_validation_message("")
        self._refresh_provider_view()

    def _on_output_dir_changed(self, *_args):
        if self._save_to_src.get():
            return
        out_dir = self._out_var.get().strip()
        if out_dir:
            self._status_var.set(f"输出将保存到：{out_dir}")

    def _save_config(self):
        config = self._current_runtime_config()
        errors = get_config_errors(config)
        if errors:
            messagebox.showerror("错误", "；".join(errors))
            return
        save_runtime_config(config)
        self._config_tested_ok = False
        self._set_config_validation_message("")
        self._refresh_provider_view()
        messagebox.showinfo("完成", "配置已保存")

    def _classify_config_error(self, msg: str) -> str:
        lower_msg = msg.lower()
        if "认证失败" in msg:
            return "认证失败"
        if "请求过于频繁" in msg:
            return "触发限流"
        if "超时" in msg:
            return "请求超时"
        if "网络请求失败" in msg or "name or service not known" in lower_msg or "failed to establish" in lower_msg:
            return "网络异常"
        return "配置测试失败"

    def _auto_validate_config_on_startup(self):
        if self._testing_config:
            return
        config = self._current_runtime_config()
        errors = get_config_errors(config)
        if errors:
            self._config_tested_ok = False
            self._set_config_validation_message("请先补全配置：" + "；".join(errors))
            self._refresh_provider_view()
            self._status_var.set("API 配置不完整，请先补全")
            self._notebook.select(self._config_page)
            return
        self._start_config_validation(config, mode="startup")

    def _test_config(self):
        if self._testing_config:
            return
        config = self._current_runtime_config()
        errors = get_config_errors(config)
        if errors:
            messagebox.showerror("错误", "；".join(errors))
            self._config_tested_ok = False
            self._set_config_validation_message("")
            self._refresh_provider_view()
            return
        self._start_config_validation(config, mode="manual")

    def _start_config_validation(self, config: RuntimeConfig, *, mode: str):
        if self._testing_config:
            return
        self._testing_config = True
        self._test_btn.set_enabled(False)
        self._config_tested_ok = False
        if mode == "startup":
            self._status_var.set("正在自动验证 API 配置…")
            self._set_config_validation_message("正在自动验证当前配置…")
        else:
            self._status_var.set("正在测试配置连通性…")
            self._set_config_validation_message("")
        self._set_config_state_chip("测试中", "info")
        threading.Thread(target=self._run_config_validation, args=(config, mode), daemon=True).start()

    def _run_config_validation(self, config: RuntimeConfig, mode: str):
        ok, msg = test_runtime_config(config)
        self.after(0, lambda: self._finish_config_validation(ok, msg, mode))

    def _finish_config_validation(self, ok: bool, msg: str, mode: str):
        self._testing_config = False
        self._test_btn.set_enabled(True)
        self._config_tested_ok = ok
        self._refresh_provider_view()
        if ok:
            self._set_config_validation_message("")
            self._status_var.set("配置已通过连通性测试" if mode == "manual" else "API 配置可用")
            if mode == "manual":
                messagebox.showinfo("测试结果", msg)
            return
        category = self._classify_config_error(msg)
        self._status_var.set(f"{category}，请检查提示")
        if mode == "startup":
            self._set_config_validation_message(f"{category}：{msg}")
            self._notebook.select(self._config_page)
            return
        self._set_config_validation_message("")
        messagebox.showerror("测试结果", f"{category}\n\n{msg}")

    def _build_run_context(self):
        config = self._current_runtime_config()
        errors = get_config_errors(config)
        if errors:
            raise ValueError("；".join(errors))
        if not self._transcript_files:
            raise ValueError("请先选择字幕文件")

        checked_transcripts: list[str] = []
        for path in self._transcript_files:
            if not os.path.exists(path):
                raise ValueError(f"字幕文件不存在：{path}")
            if not os.path.isfile(path):
                raise ValueError(f"字幕路径不是文件：{path}")
            checked_transcripts.append(path)

        checked_videos: list[str] = []
        for path in self._video_files:
            if not os.path.exists(path):
                raise ValueError(f"视频文件不存在：{path}")
            if not os.path.isfile(path):
                raise ValueError(f"视频路径不是文件：{path}")
            checked_videos.append(path)

        checked_notes: list[str] = []
        for path in self._prior_note_files:
            if not os.path.exists(path):
                raise ValueError(f"往期笔记不存在：{path}")
            if not os.path.isfile(path):
                raise ValueError(f"往期笔记路径不是文件：{path}")
            checked_notes.append(path)

        out_dir = self._out_var.get().strip() or self._default_output_dir
        if self._save_to_src.get():
            for path in checked_transcripts:
                source_dir = os.path.dirname(path)
                if not os.path.isdir(source_dir):
                    raise ValueError(f"源文件目录不存在：{source_dir}")
        else:
            if os.path.exists(out_dir) and not os.path.isdir(out_dir):
                raise ValueError("输出路径必须是文件夹，不能是已有文件")
            try:
                os.makedirs(out_dir, exist_ok=True)
            except OSError as e:
                raise ValueError(f"无法创建输出目录：{out_dir}（{e}）") from e

        self._transcript_files = checked_transcripts
        self._video_files = checked_videos
        self._prior_note_files = checked_notes
        return config, out_dir

    def _pick_dir(self):
        directory = filedialog.askdirectory(title="选择视频资料目录")
        if not directory:
            return
        self._dir_var.set(directory)
        self._transcript_files = scan_supported_files(directory)
        self._video_files = scan_video_files(directory)
        self._refresh_tree()
        lessons = pair_lessons(self._transcript_files, self._video_files)
        matched_count = sum(1 for lesson in lessons if lesson.video_path)
        unmatched_count = len(lessons) - matched_count
        self._prog_label.set("扫描完成，可以开始整理" if lessons else "扫描完成，未发现支持的字幕文件")
        tag = "dim" if lessons else "error"
        self._out_append(f"» 扫描完成  {directory}\n", tag)
        self._out_append(f"» 发现 {len(self._transcript_files)} 个字幕/文本文件\n", tag)
        self._out_append(f"» 发现 {len(self._video_files)} 个视频文件\n", tag)
        if lessons:
            self._out_append(f"» 自动匹配 {matched_count} 个任务\n", tag)
            self._out_append(f"» 未匹配视频的字幕 {unmatched_count} 个\n\n", tag)
        else:
            self._out_append("\n", tag)

    def _pick_files(self):
        files = filedialog.askopenfilenames(title="选择字幕/文本文件", filetypes=[("支持的文件", "*.srt *.txt *.md"), ("所有文件", "*.*")])
        if not files:
            return
        normalized = normalize_selected_files(files)
        skipped = len(files) - len(normalized)
        self._transcript_files = normalized
        self._refresh_tree()
        self._out_append(f"» 已选择 {len(normalized)} 个字幕/文本文件\n", "dim")
        if skipped:
            self._out_append(f"» 已忽略 {skipped} 个不支持或重复的文件\n", "error")
        self._out_append("\n", "dim")

    def _pick_videos(self):
        files = filedialog.askopenfilenames(title="选择视频文件", filetypes=[("视频文件", "*.mp4 *.mkv *.mov *.avi *.m4v"), ("所有文件", "*.*")])
        if not files:
            return
        self._video_files = normalize_video_files(files)
        self._refresh_tree()
        self._out_append(f"» 已选择 {len(self._video_files)} 个视频文件\n\n", "dim")

    def _pick_prior_notes(self):
        files = filedialog.askopenfilenames(title="选择往期笔记", filetypes=[("Markdown", "*.md"), ("文本文件", "*.txt"), ("所有文件", "*.*")])
        if not files:
            return
        self._prior_note_files = list(files)
        self._refresh_tree()
        self._out_append(f"» 已选择 {len(self._prior_note_files)} 份往期笔记\n\n", "dim")

    def _remove_selected(self):
        selected = self._tree.selection()
        if not selected:
            return
        for iid in selected:
            if iid in self._transcript_files:
                self._transcript_files.remove(iid)
        self._refresh_tree()

    def _toggle_save_to_src(self):
        val = not self._save_to_src.get()
        self._save_to_src.set(val)
        self._update_source_button()
        self._update_output_controls()
        self._status_var.set("输出将保存到各源文件所在目录" if val else "输出将保存到所选输出目录")

    def _pick_output(self):
        directory = filedialog.askdirectory(title="选择输出目录")
        if directory:
            self._save_to_src.set(False)
            self._update_source_button()
            self._update_output_controls()
            self._out_var.set(directory)

    def _start(self):
        if self._running:
            return
        try:
            config, out_dir = self._build_run_context()
        except ValueError as e:
            messagebox.showerror("错误", str(e))
            return
        self._running = True
        self._run_btn.set_enabled(False)
        self._run_btn.config(text="⏳  处理中…")
        self._prog_var.set(0)
        self._refresh_provider_view()
        self._notebook.select(self._status_page)
        threading.Thread(target=self._run_all, args=(config, out_dir), daemon=True).start()
        self._animate_pulse()

    def _animate_pulse(self):
        if not self._running:
            self._pulse_var.set("")
            return
        self._pulse_var.set("" if self._pulse_var.get() == "●" else "●")
        self.after(600, self._animate_pulse)

    def _run_all(self, runtime_config: RuntimeConfig, out_dir: str):
        installed = ensure_runtime_dependencies()
        if installed:
            self._out_append(f"» 已自动安装依赖：{', '.join(installed)}\n", "success")
        if self._video_files:
            ffmpeg_path = resolve_ffmpeg_executable()
            ffmpeg_source = describe_ffmpeg_source()
            if ffmpeg_path and ffmpeg_source == "bundled":
                self._out_append(f"» 已检测到内置 ffmpeg：{ffmpeg_path}\n", "dim")
            elif ffmpeg_path and ffmpeg_source == "system":
                self._out_append(f"» 已检测到系统 ffmpeg：{ffmpeg_path}\n", "dim")
            elif not has_ffmpeg():
                self._out_append("» 未检测到 ffmpeg，当前使用 OpenCV 规则抽帧\n", "dim")

        lessons = pair_lessons(self._transcript_files, self._video_files)
        total = len(lessons)
        ok = fail = 0
        requirements_text = self._requirements_text.get("1.0", "end").strip()
        context = build_course_context(self._course_name_var.get(), requirements_text, self._prior_note_files)

        for idx, lesson in enumerate(lessons):
            name = os.path.basename(lesson.transcript_path)
            mode_label = "图文混排" if lesson.video_path else "纯字幕"
            mode_result_label = mode_label
            self._set_row(lesson.transcript_path, "解析中…", "doing")
            self._ui(self._prog_label.set, f"[{idx+1}/{total}]  {name}")
            self._ui(self._cur_file_var.set, name)
            self._ui(self._token_var.set, "")
            self._ui(self._status_var.set, f"处理 {idx+1}/{total} · {mode_label}")
            self._out_append(f"\n{'─' * 60}\n  [{idx+1}/{total}]  {name} · {mode_label}\n{'─' * 60}\n", "dim")
            try:
                transcript = parse_file(lesson.transcript_path)
                course_name = guess_course_name(transcript, lesson, context)
                save_dir = resolve_output_dir(lesson.transcript_path, out_dir, self._save_to_src.get())
                bundle_dir, image_dir, note_path = build_output_paths(lesson.transcript_path, save_dir, course_name)
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
                        course_name=course_name,
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
                        f"- 截图 {index}: ![课堂截图 {index}]({entry['relative_path']})"
                        + (f"（时间：{entry['timestamp']}；内容提示：{entry['snippet']}）" if entry.get("snippet") else f"（时间：{entry['timestamp']}）")
                        for index, entry in enumerate(image_entries, start=1)
                    ]
                    self._out_append(f"» 已提取 {len(image_paths)} 张课堂截图，将按图文混排生成\n", "dim")
                prompt = build_user_prompt(transcript, lesson, context, image_markdown_lines)
                self._set_row(lesson.transcript_path, "生成中…", "doing")
                token_count = [0]
                done_evt = threading.Event()
                result_box, err_box = [None], [None]

                def on_token(delta):
                    token_count[0] += len(delta)
                    self._out_stream(delta)
                    self._ui(self._token_var.set, f"{token_count[0]:,} chars")

                def on_done(full):
                    result_box[0] = full
                    done_evt.set()

                def on_error(msg):
                    err_box[0] = msg
                    done_evt.set()

                stream_completion(runtime_config, prompt, on_token, on_done, on_error)
                done_evt.wait()
                if err_box[0]:
                    raise RuntimeError(err_box[0])
                clean_result, diagram_specs, diagram_parse_warnings = extract_diagram_specs(result_box[0] or "")
                for warning in diagram_parse_warnings:
                    self._out_append(f"» {warning}\n", "dim")
                diagram_entries, diagram_render_warnings = render_diagram_entries(diagram_specs, image_dir)
                if diagram_entries:
                    self._out_append(f"» 已生成 {len(diagram_entries)} 张结构化图示\n", "dim")
                    self._out_append(f"» 图示字体：{get_last_font_source()}\n", "dim")
                for warning in diagram_render_warnings:
                    self._out_append(f"» {warning}\n", "dim")
                all_image_entries = image_entries + diagram_entries
                write_summary_markdown(
                    note_path,
                    lesson.transcript_path,
                    clean_result,
                    image_entries=all_image_entries,
                    provider_label=get_provider(runtime_config.provider).label,
                    model_name=runtime_config.model,
                )
                self._set_row(lesson.transcript_path, "✓ 完成", "done")
                self._ui(self._tree.set, lesson.transcript_path, "mode", mode_result_label)
                self._out_append(f"» 输出目录：{bundle_dir}\n», 已保存：{note_path}\n", "success")
                ok += 1
            except Exception as e:
                self._set_row(lesson.transcript_path, "✗ 失败", "fail")
                self._out_append(f"\n» 失败：{e}\n", "error")
                fail += 1
            self._ui(self._prog_var.set, (idx + 1) / total * 100)
            self._ui(self._prog_pct.set, f"{int((idx + 1) / total * 100)}%")

        self._running = False
        save_runtime_config(self._current_runtime_config())
        self.after(0, lambda: (self._run_btn.set_enabled(True), self._run_btn.config(text="▶  开始整理")))
        output_summary = "各源文件所在目录" if self._save_to_src.get() else out_dir
        self._ui(self._cur_file_var.set, "")
        self._ui(self._token_var.set, "")
        self._ui(self._pulse_var.set, "")
        self._ui(self._status_var.set, f"完成 — 成功 {ok} 个 / 失败 {fail} 个")
        self._ui(self._prog_label.set, f"全部完成：成功 {ok} 个，失败 {fail} 个")
        self._out_append(f"\n{'═' * 60}\n  全部完成  成功 {ok} 个  失败 {fail} 个\n  输出位置：{output_summary}\n", "dim")
        if ok:
            messagebox.showinfo("完成", f"整理完成！\n成功 {ok} 个任务\n\n输出位置：\n{output_summary}")

    def _ui(self, fn, *args):
        self.after(0, lambda: fn(*args))

    def _set_row(self, iid, status, tag=""):
        def _do():
            if self._tree.exists(iid):
                self._tree.set(iid, "status", status)
                if tag:
                    self._tree.item(iid, tags=(tag,))
        self.after(0, _do)

    def _out_append(self, text, tag="normal"):
        def _do():
            self._set_output_placeholder(False)
            self._out_text.config(state="normal")
            self._out_text.insert("end", text, tag)
            self._out_text.see("end")
            self._out_text.config(state="disabled")
        self.after(0, _do)

    def _out_stream(self, delta):
        def _do():
            self._set_output_placeholder(False)
            self._out_text.config(state="normal")
            self._out_text.insert("end", delta, choose_stream_tag(delta))
            self._out_text.see("end")
            self._out_text.config(state="disabled")
        self.after(0, _do)

    def _clear_out(self):
        self._out_text.config(state="normal")
        self._out_text.delete("1.0", "end")
        self._out_text.config(state="disabled")
        self._set_output_placeholder(True)
        self._prog_var.set(0)
        self._prog_pct.set("")
        self._prog_label.set("已清空")
        self._cur_file_var.set("")
        self._token_var.set("")
        self._pulse_var.set("")

    def _on_tree_resize(self, event):
        self._resize_tree_columns(event.width)

    def _resize_tree_columns(self, width: int | None = None):
        self._run_page.resize_tree_columns(width)

    def _apply_layout_mode(self):
        width = self.winfo_width() or DEFAULT_WINDOW_SIZE[0]
        height = self.winfo_height() or DEFAULT_WINDOW_SIZE[1]
        compact = width <= COMPACT_BREAKPOINT["width"] or height <= COMPACT_BREAKPOINT["height"]
        if compact == self._compact_mode:
            return
        self._compact_mode = compact
        set_tree_density(self, compact)
        self._run_page.apply_layout_mode(compact)
        self._status_page.apply_layout_mode(compact)
        self._config_page.apply_layout_mode(compact)
        self._title_block.grid_configure(sticky="w", padx=(SPACE["outer"], SPACE["section"]))
        if compact:
            self._right_nav.grid_configure(sticky="e", padx=(SPACE["compact"], SPACE["outer"]), pady=(6, 4))
            self._badge_row.pack_configure(anchor="e", pady=(0, 0))
        else:
            self._right_nav.grid_configure(sticky="e", padx=(SPACE["section"], SPACE["outer"]), pady=(6, 4))
            self._badge_row.pack_configure(anchor="e", pady=(2, 0))
        self.after_idle(self._resize_tree_columns)

    def _on_root_resize(self, event):
        if event.widget is not self:
            return
        self.after_idle(self._apply_layout_mode)
        self.after_idle(self._resize_tree_columns)
