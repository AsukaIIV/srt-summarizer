# -*- coding: utf-8 -*-
"""
SRT 课堂录音总结工具 - DeepSeek 流式输出版
双击 start.bat 启动（需安装 Python 3 + requests）
"""

import os, re, threading, json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from datetime import datetime
import requests

# ══════════════════════════════════════════════
#  ★ 在此填写你的 DeepSeek API Key ★
API_KEY = "sk-xxxxxxxxxxxxxxxx"
#  模型：deepseek-chat / deepseek-reasoner
MODEL   = "deepseek-reasoner"
# ══════════════════════════════════════════════

DEEPSEEK_URL  = "https://api.deepseek.com/v1/chat/completions"
SYSTEM_PROMPT = """你是一位专业的课堂录音总结专家，拥有丰富的学术笔记整理经验。你的任务是将课堂录音转录文本加工成一份「可以替代听课」的完整 Markdown 笔记——即一位没有上过这节课的同学，单靠你的笔记就能完全掌握本节课所有知识点。

---

## 核心原则

1. **零遗漏原则**：教师讲授的每一个知识点、每一条规律、每一个例子都必须出现在笔记中，不得以「详见课本」「略」等理由省略。
2. **还原讲解逻辑**：不只是列结论，要还原教师的推导过程、类比说明、举例论证，让读者理解「为什么」。
3. **强调内容置顶**：凡教师明确强调（「要记住」「考试会考」「必须掌握」「大家注意」「一定要」「这很重要」「反复强调」等）的内容，除在正文中完整保留外，还须在第三节单独汇总。
4. **过滤噪音**：学生闲聊、课间杂音、点名签到、与课程内容无关的寒暄一律忽略；但学生提问引发的教师延伸讲解必须完整保留。
5. **多节课分隔**：若文件包含多节课内容，每节课独立输出完整的五段结构，节与节之间用 `---` 分隔。

---

## 输出结构（严格按序，不得遗漏）

### 一、课程概要

用表格形式呈现：

| 项目 | 内容 |
|------|------|
| 上课日期 | （从内容推断，无法确定则填「未知」） |
| 课程名称 | |
| 本节范围 | （章节编号 + 主题，如「第2章 2.1～2.3节：光学基础」） |
| 主讲教师 | （若提及） |
| 本节课导言 | （1～2句话，说明本节课在整门课程中的位置与意义） |

---

### 二、正文内容

按教师讲课的自然顺序，将内容划分为若干「部分」：

- 每部分使用 `## 第X部分：标题` 作为二级标题
- 部分内按独立知识点使用 `### 序号. 知识点名称` 作为三级标题
- 知识点内的子话题使用 `#### 序号.子序号 子话题名` 作为四级标题

**每个知识点必须包含以下要素（有则写，无则省略该要素）：**
- **定义／概念**：精确表述，不得用模糊语言替代
- **公式／定律**：用行内代码呈现，如 `n₁sinθ₁ = n₂sinθ₂`；并说明各符号含义
- **推导过程**：还原教师的推导步骤，哪怕只是简略推导
- **物理意义／直觉解释**：教师用来帮助理解的类比、比喻、生活例子
- **适用条件／注意事项**：边界条件、常见误区
- **典型例题**：若教师现场讲解了例题，完整呈现题目+解题过程+结论
- **与前后知识点的联系**：教师提到的承上启下关系

**专业术语规范：**
- 首次出现时标注英文全称，如：全内反射（TIR, Total Internal Reflection）
- 缩写词在括号内说明，如：数值孔径（NA）

---

### 三、教师强调重点 ⚠️

逐条列出所有被教师明确强调的内容，格式如下：

> **【强调】** `所属知识点` — 具体内容，用 **加粗** 标注关键词或公式

要求：
- 不得仅写「很重要」，必须写出完整内容
- 若教师给出了记忆口诀或记忆技巧，一并列出
- 若教师说明了「为什么重要」（如考试必考、工程应用广泛），注明原因

---

### 四、作业与考试重点

#### 4.1 作业题目
逐题列出，保留原始题号，并注明涉及的知识点：
- 题号：题目描述 → 涉及知识点：xxx

#### 4.2 必考公式汇总

| 公式名称 | 表达式 | 各符号含义 | 使用场景 |
|----------|--------|------------|----------|

#### 4.3 必记概念清单
- 逐条列出，每条附简短说明（不超过2句）

#### 4.4 答题规范与技巧
- 教师提到的任何答题要求（如「必须写公式推导过程」「要画图辅助说明」「单位换算要写清楚」等）

---

### 五、课程总结

- 用 5～8 句话完整概括本节课的知识脉络与核心收获
- 指出本节课的重难点所在
- 若教师提及下节课内容，单独一行：**下节课预告：**……

---

## 格式规范

- 标题层级：`##`（部分）→ `###`（知识点）→ `####`（子话题），不使用 `#`
- 公式：行内代码 `` `公式` ``，下标用 Unicode 如 ₁₂，上标用 ⁻¹ 等
- 强调：`**加粗**` 用于关键词，`> 引用块` 用于教师原话
- 中文标点全角：「」、。，：；？！《》
- 转录不清晰处标注 `[unclear]`，不猜测不脑补
- 表格对齐，列表缩进统一使用 2 个空格
"""

# ─────────────────────────────────────────────
#  配色系统
# ─────────────────────────────────────────────
C = dict(
    bg       = "#0d1117",
    surface  = "#161b22",
    surface2 = "#1c2128",
    border   = "#30363d",
    border2  = "#21262d",
    accent   = "#2f81f7",
    accent_h = "#1f6feb",
    accent_d = "#388bfd",
    green    = "#3fb950",
    green_h  = "#2ea043",
    red      = "#f85149",
    yellow   = "#d29922",
    fg       = "#e6edf3",
    fg2      = "#8b949e",
    fg3      = "#484f58",
    code_bg  = "#0d1117",
    sel      = "#264f78",
)

# ─────────────────────────────────────────────
#  文件解析（支持 .srt / .txt / .md）
# ─────────────────────────────────────────────
SUPPORTED_EXT = (".srt", ".txt", ".md")

def parse_file(filepath):
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        raw = f.read()
    return raw.strip()

# ─────────────────────────────────────────────
#  DeepSeek 流式调用
# ─────────────────────────────────────────────
def stream_deepseek(transcript, on_token, on_done, on_error):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type":  "application/json",
    }
    payload = {
        "model":       MODEL,
        "stream":      True,
        "temperature": 0.3,
        "max_tokens":  8192,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": f"请总结以下课堂录音内容：\n\n{transcript}"},
        ],
    }
    try:
        with requests.post(DEEPSEEK_URL, headers=headers,
                           json=payload, stream=True, timeout=180) as resp:
            resp.raise_for_status()
            full = []
            for raw_line in resp.iter_lines():
                if not raw_line:
                    continue
                line = raw_line.decode("utf-8") if isinstance(raw_line, bytes) else raw_line
                if line.startswith("data:"):
                    line = line[5:].strip()
                if line == "[DONE]":
                    break
                try:
                    chunk = json.loads(line)
                    delta = chunk["choices"][0]["delta"].get("content", "")
                    if delta:
                        full.append(delta)
                        on_token(delta)
                except Exception:
                    pass
            on_done("".join(full))
    except Exception as e:
        on_error(str(e))

# ─────────────────────────────────────────────
#  自定义控件（全部基于 tk.Button，避免 Canvas 命名冲突）
# ─────────────────────────────────────────────
class PrimaryButton(tk.Button):
    """实心主操作按钮，hover 变色"""
    def __init__(self, parent, text, command,
                 bg_normal=C["accent"], bg_hover=C["accent_h"],
                 fg=C["fg"], font_size=10, bold=True, **kw):
        self._bg_n = bg_normal
        self._bg_h = bg_hover
        self._enabled = True
        super().__init__(
            parent,
            text=text,
            command=command,
            bg=bg_normal,
            fg=fg,
            activebackground=bg_hover,
            activeforeground=fg,
            relief="flat",
            bd=0,
            padx=16,
            pady=8,
            cursor="hand2",
            font=("Segoe UI", font_size, "bold" if bold else "normal"),
            **kw
        )
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_enter(self, _):
        if self._enabled:
            self.config(bg=self._bg_h)

    def _on_leave(self, _):
        if self._enabled:
            self.config(bg=self._bg_n)

    def set_enabled(self, enabled: bool):
        self._enabled = enabled
        if enabled:
            self.config(state="normal", bg=self._bg_n,
                        fg=C["fg"], cursor="hand2")
        else:
            self.config(state="disabled", bg=C["border"],
                        fg=C["fg3"], cursor="arrow")


class GhostButton(tk.Button):
    """描边幽灵按钮，hover 时文字和边框变蓝"""
    def __init__(self, parent, text, command,
                 font_size=9, **kw):
        super().__init__(
            parent,
            text=text,
            command=command,
            bg=C["surface"],
            fg=C["fg2"],
            activebackground=C["surface2"],
            activeforeground=C["accent"],
            relief="solid",
            bd=1,
            padx=10,
            pady=6,
            cursor="hand2",
            highlightthickness=0,
            font=("Segoe UI", font_size),
            **kw
        )
        self.config(highlightbackground=C["border"])
        self.bind("<Enter>", lambda _: self.config(
            fg=C["accent"], bg=C["surface2"]))
        self.bind("<Leave>", lambda _: self.config(
            fg=C["fg2"], bg=C["surface"]))


class Divider(tk.Frame):
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=C["border2"], height=1, **kw)


# ─────────────────────────────────────────────
#  主界面
# ─────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SRT 课堂总结工具")
        self.geometry("1020x820")
        self.minsize(820, 640)
        self.configure(bg=C["bg"])
        self.resizable(True, True)
        self.state("zoomed")  # 默认最大化

        self._srt_files   = []
        self._running     = False
        self._cur_summary = ""
        self._save_to_src = tk.BooleanVar(value=False)

        self._build_style()
        self._build_ui()

    def _build_style(self):
        s = ttk.Style(self)
        s.theme_use("clam")

        s.configure("Treeview",
                    background=C["surface2"],
                    fieldbackground=C["surface2"],
                    foreground=C["fg"],
                    font=("Segoe UI", 9),
                    borderwidth=0,
                    relief="flat",
                    rowheight=28)
        s.configure("Treeview.Heading",
                    background=C["surface"],
                    foreground=C["fg2"],
                    font=("Segoe UI", 9),
                    relief="flat",
                    borderwidth=0)
        s.map("Treeview",
              background=[("selected", C["sel"])],
              foreground=[("selected", C["fg"])])

        s.configure("TProgressbar",
                    troughcolor=C["border2"],
                    background=C["accent"],
                    bordercolor=C["bg"],
                    lightcolor=C["accent"],
                    darkcolor=C["accent"],
                    thickness=4)

        s.configure("Vertical.TScrollbar",
                    background=C["surface2"],
                    troughcolor=C["surface"],
                    bordercolor=C["surface"],
                    arrowcolor=C["fg3"],
                    width=8)
        s.map("Vertical.TScrollbar",
              background=[("active", C["border"])])

    def _build_ui(self):
        # ── 顶部导航栏 ─────────────────────────
        nav = tk.Frame(self, bg=C["surface"], height=52)
        nav.pack(fill="x")
        nav.pack_propagate(False)
        Divider(self).pack(fill="x")

        nav_inner = tk.Frame(nav, bg=C["surface"])
        nav_inner.pack(fill="both", expand=True, padx=20)

        logo_f = tk.Frame(nav_inner, bg=C["surface"])
        logo_f.pack(side="left", fill="y")
        tk.Label(logo_f, text="🎓", bg=C["surface"],
                 font=("Segoe UI", 16)).pack(side="left", pady=10)
        tk.Label(logo_f, text=" SRT 课堂总结",
                 bg=C["surface"], fg=C["fg"],
                 font=("Segoe UI", 13, "bold")).pack(side="left")
        tk.Label(logo_f, text=" · DeepSeek",
                 bg=C["surface"], fg=C["fg2"],
                 font=("Segoe UI", 11)).pack(side="left")

        right_nav = tk.Frame(nav_inner, bg=C["surface"])
        right_nav.pack(side="right", fill="y", pady=12)

        key_ok    = bool(API_KEY) and not API_KEY.startswith("sk-xxx")
        dot_color = C["green"] if key_ok else C["red"]
        dot_text  = "● 已连接" if key_ok else "● 未配置 API Key"
        tk.Label(right_nav, text=dot_text,
                 bg=C["surface"], fg=dot_color,
                 font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 14))

        model_wrap = tk.Frame(right_nav, bg=C["surface2"],
                              highlightthickness=1,
                              highlightbackground=C["border"])
        model_wrap.pack(side="left")
        tk.Label(model_wrap, text=f"  {MODEL}  ",
                 bg=C["surface2"], fg=C["fg2"],
                 font=("Consolas", 9)).pack(pady=4)

        # ── 输出目录栏 ─────────────────────────
        toolbar = tk.Frame(self, bg=C["bg"])
        toolbar.pack(fill="x", padx=20, pady=(14, 0))

        dir_row = tk.Frame(toolbar, bg=C["bg"])
        dir_row.pack(fill="x")

        tk.Label(dir_row, text="输出目录",
                 bg=C["bg"], fg=C["fg2"],
                 font=("Segoe UI", 9)).pack(side="left")

        out_wrap = tk.Frame(dir_row, bg=C["surface2"],
                            highlightthickness=1,
                            highlightbackground=C["border"])
        out_wrap.pack(side="left", fill="x", expand=True, padx=(8, 8))

        self._out_var = tk.StringVar(
            value=os.path.join(os.path.expanduser("~"), "Desktop"))
        tk.Entry(out_wrap, textvariable=self._out_var,
                 bg=C["surface2"], fg=C["fg"],
                 insertbackground=C["fg"],
                 relief="flat", font=("Segoe UI", 10),
                 bd=6).pack(fill="x")

        GhostButton(dir_row, "浏览", self._pick_output,
                    font_size=9).pack(side="left")

        Divider(toolbar).pack(fill="x", pady=(12, 0))

        # ── 中间主体：左栏 + 文件列表 ───────────
        content = tk.Frame(self, bg=C["bg"])
        content.pack(fill="x", padx=20, pady=(12, 0))

        # 左栏
        sidebar = tk.Frame(content, bg=C["bg"], width=188)
        sidebar.pack(side="left", fill="y", padx=(0, 12))
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="扫描目录",
                 bg=C["bg"], fg=C["fg2"],
                 font=("Segoe UI", 9)).pack(anchor="w")

        dir_ew = tk.Frame(sidebar, bg=C["surface2"],
                          highlightthickness=1,
                          highlightbackground=C["border"])
        dir_ew.pack(fill="x", pady=(4, 10))
        self._dir_var = tk.StringVar()
        tk.Entry(dir_ew, textvariable=self._dir_var,
                 bg=C["surface2"], fg=C["fg2"],
                 insertbackground=C["fg"],
                 relief="flat", font=("Segoe UI", 9),
                 bd=5).pack(fill="x")

        self._scan_btn = PrimaryButton(
            sidebar, "📂  选择并扫描", self._pick_dir,
            bg_normal=C["accent"], bg_hover=C["accent_h"],
            font_size=10, bold=True)
        self._scan_btn.pack(fill="x", ipady=2)

        # 分隔线 + 或
        or_row = tk.Frame(sidebar, bg=C["bg"])
        or_row.pack(fill="x", pady=(8, 0))
        tk.Frame(or_row, bg=C["border2"], height=1).pack(
            side="left", fill="x", expand=True, pady=6)
        tk.Label(or_row, text=" 或 ", bg=C["bg"], fg=C["fg3"],
                 font=("Segoe UI", 8)).pack(side="left")
        tk.Frame(or_row, bg=C["border2"], height=1).pack(
            side="left", fill="x", expand=True, pady=6)

        GhostButton(sidebar, "📄  选择单个文件", self._pick_files,
                    font_size=9).pack(fill="x", ipady=2, pady=(4, 0))

        # 统计卡片
        stat_card = tk.Frame(sidebar, bg=C["surface"],
                             highlightthickness=1,
                             highlightbackground=C["border2"])
        stat_card.pack(fill="x", pady=(14, 0))
        stat_inner = tk.Frame(stat_card, bg=C["surface"], padx=12, pady=10)
        stat_inner.pack(fill="x")

        tk.Label(stat_inner, text="FILE COUNT",
                 bg=C["surface"], fg=C["fg3"],
                 font=("Segoe UI", 7, "bold")).pack(anchor="w")
        self._stat_var = tk.StringVar(value="—")
        tk.Label(stat_inner, textvariable=self._stat_var,
                 bg=C["surface"], fg=C["fg"],
                 font=("Segoe UI", 26, "bold")).pack(anchor="w", pady=(2, 0))
        tk.Label(stat_inner, text="个 .srt 文件",
                 bg=C["surface"], fg=C["fg2"],
                 font=("Segoe UI", 9)).pack(anchor="w")

        # 文件列表
        file_panel = tk.Frame(content, bg=C["surface"],
                              highlightthickness=1,
                              highlightbackground=C["border"])
        file_panel.pack(side="left", fill="both", expand=True)

        list_hdr = tk.Frame(file_panel, bg=C["surface"], pady=8, padx=12)
        list_hdr.pack(fill="x")
        tk.Label(list_hdr, text="文件列表",
                 bg=C["surface"], fg=C["fg2"],
                 font=("Segoe UI", 9, "bold")).pack(side="left")
        self._list_count_var = tk.StringVar(value="")
        tk.Label(list_hdr, textvariable=self._list_count_var,
                 bg=C["surface"], fg=C["fg3"],
                 font=("Segoe UI", 9)).pack(side="left", padx=6)
        GhostButton(list_hdr, "移除所选", self._remove_selected,
                    font_size=8).pack(side="right")
        Divider(file_panel).pack(fill="x")

        tree_frame = tk.Frame(file_panel, bg=C["surface2"])
        tree_frame.pack(fill="both", expand=True)

        cols = ("filename", "size", "status")
        self._tree = ttk.Treeview(tree_frame, columns=cols,
                                   show="headings", height=7)
        self._tree.heading("filename", text="文件名")
        self._tree.heading("size",     text="大小")
        self._tree.heading("status",   text="状态")
        self._tree.column("filename", width=360, stretch=True)
        self._tree.column("size",     width=72,  stretch=False, anchor="e")
        self._tree.column("status",   width=100, stretch=False, anchor="center")

        vsb = ttk.Scrollbar(tree_frame, orient="vertical",
                             command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        self._tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self._tree.tag_configure("done",  foreground=C["green"])
        self._tree.tag_configure("fail",  foreground=C["red"])
        self._tree.tag_configure("doing", foreground=C["yellow"])

        # ── 进度区 ─────────────────────────────
        prog_outer = tk.Frame(self, bg=C["bg"])
        prog_outer.pack(fill="x", padx=20, pady=(10, 0))

        prog_info = tk.Frame(prog_outer, bg=C["bg"])
        prog_info.pack(fill="x", pady=(0, 4))

        self._prog_label = tk.StringVar(value="就绪")
        tk.Label(prog_info, textvariable=self._prog_label,
                 bg=C["bg"], fg=C["fg2"],
                 font=("Segoe UI", 9)).pack(side="left")

        self._prog_pct = tk.StringVar(value="")
        tk.Label(prog_info, textvariable=self._prog_pct,
                 bg=C["bg"], fg=C["accent"],
                 font=("Consolas", 9, "bold")).pack(side="right")

        self._prog_var = tk.DoubleVar(value=0)
        ttk.Progressbar(prog_outer, variable=self._prog_var,
                        maximum=100).pack(fill="x")

        # ── 底部操作栏 ─────────────────────────
        Divider(self).pack(fill="x", pady=(10, 0))
        bottom = tk.Frame(self, bg=C["surface"], pady=12)
        bottom.pack(fill="x")

        btn_row = tk.Frame(bottom, bg=C["surface"])
        btn_row.pack(padx=20, fill="x")

        self._run_btn = PrimaryButton(
            btn_row, "▶  开始总结", self._start,
            bg_normal=C["green"], bg_hover=C["green_h"],
            font_size=11, bold=True)
        self._run_btn.pack(side="left", ipady=4)

        GhostButton(btn_row, "清空输出", self._clear_out,
                    font_size=9).pack(side="left", padx=(10, 0))

        self._src_btn = tk.Button(
            btn_row, text="📁  输出到源目录：关",
            command=self._toggle_save_to_src,
            bg=C["surface2"], fg=C["fg2"],
            activebackground=C["surface2"], activeforeground=C["green"],
            relief="flat", bd=1,
            highlightthickness=1, highlightbackground=C["border"],
            cursor="hand2", font=("Segoe UI", 9),
            padx=10, pady=6)
        self._src_btn.pack(side="left", padx=(10, 0))

        self._status_var = tk.StringVar(value="就绪，请选择目录")
        tk.Label(btn_row, textvariable=self._status_var,
                 bg=C["surface"], fg=C["fg3"],
                 font=("Segoe UI", 9)).pack(side="right")

        # ── 实时输出区 ─────────────────────────
        out_panel = tk.Frame(self, bg=C["surface"],
                             highlightthickness=1,
                             highlightbackground=C["border"])
        out_panel.pack(fill="both", expand=True, padx=20, pady=(10, 0))

        out_hdr = tk.Frame(out_panel, bg=C["surface"], pady=8, padx=12)
        out_hdr.pack(fill="x")

        tk.Label(out_hdr, text="实时输出",
                 bg=C["surface"], fg=C["fg2"],
                 font=("Segoe UI", 9, "bold")).pack(side="left")

        self._pulse_var = tk.StringVar(value="")
        tk.Label(out_hdr, textvariable=self._pulse_var,
                 bg=C["surface"], fg=C["green"],
                 font=("Segoe UI", 11)).pack(side="left", padx=6)

        self._cur_file_var = tk.StringVar(value="")
        tk.Label(out_hdr, textvariable=self._cur_file_var,
                 bg=C["surface"], fg=C["accent"],
                 font=("Segoe UI", 9)).pack(side="left")

        self._token_var = tk.StringVar(value="")
        tk.Label(out_hdr, textvariable=self._token_var,
                 bg=C["surface"], fg=C["fg3"],
                 font=("Consolas", 9)).pack(side="right")

        Divider(out_panel).pack(fill="x")

        self._out_text = scrolledtext.ScrolledText(
            out_panel,
            bg=C["code_bg"], fg="#adbac7",
            insertbackground=C["fg"],
            font=("Consolas", 10),
            relief="flat", wrap="word",
            state="disabled",
            padx=14, pady=12)
        self._out_text.pack(fill="both", expand=True)

        self._out_text.tag_config("h1",      foreground="#79c0ff",
                                  font=("Consolas", 12, "bold"))
        self._out_text.tag_config("h2",      foreground="#79c0ff",
                                  font=("Consolas", 11, "bold"))
        self._out_text.tag_config("bold",    foreground="#ffa657",
                                  font=("Consolas", 10, "bold"))
        self._out_text.tag_config("normal",  foreground="#adbac7")
        self._out_text.tag_config("dim",     foreground="#444c56")
        self._out_text.tag_config("success", foreground=C["green"])
        self._out_text.tag_config("error",   foreground=C["red"])



    # ─────────────────────────────────────────
    #  目录选择
    # ─────────────────────────────────────────
    def _pick_dir(self):
        d = filedialog.askdirectory(title="选择包含 .srt / .txt / .md 文件的目录")
        if not d:
            return
        self._dir_var.set(d)
        self._srt_files.clear()
        for root, _, files in os.walk(d):
            for fn in sorted(files):
                if fn.lower().endswith(SUPPORTED_EXT):
                    self._srt_files.append(os.path.join(root, fn))

        for item in self._tree.get_children():
            self._tree.delete(item)
        for fp in self._srt_files:
            sz  = os.path.getsize(fp)
            szs = f"{sz/1024:.1f} KB" if sz < 1_048_576 else f"{sz/1_048_576:.1f} MB"
            self._tree.insert("", "end", iid=fp,
                              values=(os.path.basename(fp), szs, "待处理"))

        n = len(self._srt_files)
        self._stat_var.set(str(n) if n else "0")
        self._list_count_var.set(f"({n} 个)" if n else "")
        self._prog_label.set("扫描完成，可以开始总结")
        self._out_append(
            f"» 扫描完成  {d}\n» 发现 {n} 个文件 (.srt / .txt / .md)\n\n", "dim")

    def _remove_selected(self):
        selected = self._tree.selection()
        if not selected:
            return
        for iid in selected:
            self._tree.delete(iid)
            if iid in self._srt_files:
                self._srt_files.remove(iid)
        n = len(self._srt_files)
        self._stat_var.set(str(n) if n else "—")
        self._list_count_var.set(f"({n} 个)" if n else "")

    def _pick_files(self):
        files = filedialog.askopenfilenames(
            title="选择 .srt / .txt / .md 文件",
            filetypes=[
                ("支持的文件", "*.srt *.txt *.md"),
                ("SRT 字幕", "*.srt"),
                ("文本文件", "*.txt"),
                ("Markdown", "*.md"),
                ("所有文件", "*.*"),
            ]
        )
        if not files:
            return
        self._srt_files.clear()
        self._srt_files.extend(files)
        self._dir_var.set("")

        for item in self._tree.get_children():
            self._tree.delete(item)
        for fp in self._srt_files:
            sz  = os.path.getsize(fp)
            szs = f"{sz/1024:.1f} KB" if sz < 1_048_576 else f"{sz/1_048_576:.1f} MB"
            self._tree.insert("", "end", iid=fp,
                              values=(os.path.basename(fp), szs, "待处理"))

        n = len(self._srt_files)
        self._stat_var.set(str(n) if n else "0")
        self._list_count_var.set(f"({n} 个)" if n else "")
        self._prog_label.set("文件已选择，可以开始总结")
        self._out_append(f"» 已选择 {n} 个文件\n\n", "dim")

    def _toggle_save_to_src(self):
        val = not self._save_to_src.get()
        self._save_to_src.set(val)
        if val:
            self._src_btn.config(
                text="📁  输出到源目录：开",
                fg=C["green"], highlightbackground=C["green"])
        else:
            self._src_btn.config(
                text="📁  输出到源目录：关",
                fg=C["fg2"], highlightbackground=C["border"])

    def _pick_output(self):
        d = filedialog.askdirectory(title="选择输出目录")
        if d:
            self._out_var.set(d)

    # ─────────────────────────────────────────
    #  开始处理
    # ─────────────────────────────────────────
    def _start(self):
        if self._running:
            return
        if not self._srt_files:
            messagebox.showwarning("提示", "请先选择目录并扫描 .srt 文件")
            return
        if not API_KEY or API_KEY.startswith("sk-xxx"):
            messagebox.showerror("错误",
                "请先在脚本顶部填写有效的 API_KEY，然后重新运行程序")
            return
        self._running = True
        self._run_btn.set_enabled(False)
        self._run_btn.config(text="⏳  处理中…")
        self._prog_var.set(0)
        threading.Thread(target=self._run_all, daemon=True).start()
        self._animate_pulse()

    def _animate_pulse(self):
        if not self._running:
            self._pulse_var.set("")
            return
        self._pulse_var.set("" if self._pulse_var.get() == "●" else "●")
        self.after(600, self._animate_pulse)

    def _run_all(self):
        total   = len(self._srt_files)
        out_dir = self._out_var.get().strip() or os.getcwd()
        os.makedirs(out_dir, exist_ok=True)
        ok = fail = 0

        for idx, fp in enumerate(self._srt_files):
            name = os.path.basename(fp)
            self._set_row(fp, "解析中…", "doing")
            self._ui(self._prog_label.set,   f"[{idx+1}/{total}]  {name}")
            self._ui(self._cur_file_var.set,  name)
            self._ui(self._token_var.set,     "")
            self._ui(self._status_var.set,    f"处理 {idx+1}/{total}")

            sep = "─" * 60
            self._out_append(f"\n{sep}\n  [{idx+1}/{total}]  {name}\n{sep}\n", "dim")

            try:
                text = parse_file(fp)
                if not text.strip():
                    raise ValueError("SRT 文件内容为空")

                self._set_row(fp, "生成中…", "doing")
                self._cur_summary = ""
                token_count = [0]
                done_evt    = threading.Event()
                result_box, err_box = [None], [None]

                def on_token(delta):
                    self._cur_summary += delta
                    token_count[0]    += len(delta)
                    self._out_stream(delta)
                    self._ui(self._token_var.set, f"{token_count[0]:,} chars")

                def on_done(full):
                    result_box[0] = full
                    done_evt.set()

                def on_error(msg):
                    err_box[0] = msg
                    done_evt.set()

                stream_deepseek(text, on_token, on_done, on_error)
                done_evt.wait()

                if err_box[0]:
                    raise RuntimeError(err_box[0])

                stem     = os.path.splitext(name)[0]
                ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
                save_dir = os.path.dirname(fp) if self._save_to_src.get() else out_dir
                out_path = os.path.join(save_dir, f"{stem}_总结_{ts}.md")
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(f"# {stem} 课堂总结\n\n")
                    f.write(
                        f"> 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  \n"
                        f"> 源文件：`{fp}`\n\n---\n\n")
                    f.write(result_box[0] or "")

                self._set_row(fp, "✓ 完成", "done")
                self._out_append(
                    f"\n» 已保存 → {os.path.basename(out_path)}\n", "success")
                ok += 1

            except Exception as e:
                self._set_row(fp, "✗ 失败", "fail")
                self._out_append(f"\n» 失败：{e}\n", "error")
                fail += 1

            self._ui(self._prog_var.set,  (idx + 1) / total * 100)
            self._ui(self._prog_pct.set,  f"{int((idx+1)/total*100)}%")

        self._running = False
        self.after(0, lambda: (
            self._run_btn.set_enabled(True),
            self._run_btn.config(text="▶  开始总结"),
        ))
        self._ui(self._status_var.set,
                 f"完成 — 成功 {ok} 个 / 失败 {fail} 个")
        self._ui(self._prog_label.set,
                 f"全部完成：成功 {ok} 个，失败 {fail} 个")
        self._out_append(
            f"\n{'═'*60}\n"
            f"  全部完成  成功 {ok} 个  失败 {fail} 个\n"
            f"  输出目录：{out_dir}\n", "dim")
        if ok:
            messagebox.showinfo("完成",
                f"总结完成！\n成功 {ok} 个文件\n\n输出目录：\n{out_dir}")

    # ─────────────────────────────────────────
    #  线程安全 UI 工具
    # ─────────────────────────────────────────
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
            self._out_text.config(state="normal")
            self._out_text.insert("end", text, tag)
            self._out_text.see("end")
            self._out_text.config(state="disabled")
        self.after(0, _do)

    def _out_stream(self, delta):
        def _do():
            self._out_text.config(state="normal")
            stripped = delta.lstrip()
            if stripped.startswith("## "):
                tag = "h2"
            elif stripped.startswith("# "):
                tag = "h1"
            elif "**" in delta:
                tag = "bold"
            else:
                tag = "normal"
            self._out_text.insert("end", delta, tag)
            self._out_text.see("end")
            self._out_text.config(state="disabled")
        self.after(0, _do)

    def _clear_out(self):
        self._out_text.config(state="normal")
        self._out_text.delete("1.0", "end")
        self._out_text.config(state="disabled")
        self._prog_var.set(0)
        self._prog_pct.set("")
        self._prog_label.set("已清空")


if __name__ == "__main__":
    app = App()
    app.mainloop()