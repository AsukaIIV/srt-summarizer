<div align="center">

# SRT-SUMMARIZER

### AI 驱动的课堂录播整理工具

把字幕、转录文本和视频整理成结构化 Markdown 课堂笔记

![软件界面截图](img/screenshot.png)

</div>

---

## 软件简介

SRT-SUMMARIZER 是一个面向学生和日常学习场景的课堂资料整理工具。

它可以把课堂字幕（`.srt`）、转录文本（`.txt` / `.md`）、视频截图、往期笔记，借助 LLM 整理成结构清晰、方便复习的 Markdown 课程笔记。

**v2.0 提供两种使用方式：**

- **Web 界面**（推荐）：浏览器访问，Material Design 3 风格，响应式布局
- **单文件 EXE**：开箱即用，内嵌 ffmpeg 和中文字体，无需安装任何依赖

---

## 主要功能

- 整理 `.srt` / `.txt` / `.md` 为结构化课程笔记
- 配对视频并自动抽取课堂截图，图文混排
- 批量扫描资料目录，自动配对字幕与视频
- 导入往期笔记，增强课程上下文连续性
- 流式实时显示模型输出和生成进度
- 按平台分别记住模型、接口地址和 API Key
- 启动时自动校验 API 配置
- 生成结构化图示（概念对比、流程图、公式关系图）
- 输出到固定目录或源文件所在目录
- 已保存的 API Key 显示脱敏占位，切换平台不丢失

---

## 支持平台

| 平台 | 接口风格 |
|------|----------|
| DeepSeek | OpenAI Compatible |
| OpenAI Compatible | OpenAI Compatible |
| 硅基流动 | OpenAI Compatible |
| 千问 | OpenAI Compatible |
| Kimi | OpenAI Compatible |
| Claude | Anthropic Messages |

---

## 快速开始（Windows.exe）

### 使用预编译版本

1. 从 [Releases](https://github.com/AsukaIIV/srt-summarizer/releases) 下载 `srt-summarizer-v2.0.exe`
2. 双击运行，终端窗口显示启动日志
3. 浏览器自动打开 `http://127.0.0.1:8099`
4. 在 **API设置** 中填写你的 API 配置并保存
5. 在 **选择文件** 中添加字幕、视频或扫描目录
6. 切换到 **开始运行** 开始整理

**无需安装 Python、ffmpeg 或任何依赖。**

### 从源码运行

```bash
git clone https://github.com/AsukaIIV/srt-summarizer.git
cd srt-summarizer
pip install -r requirements_web.txt
python web_main.py
```

浏览器访问 `http://127.0.0.1:8099`。

---

## API 配置

在 **API设置** 页面填写：

- **API 平台**：从下拉列表选择
- **模型**：平台对应的模型名称
- **接口地址**：API Base URL（切换平台会自动带入默认值）
- **密钥**：API Key

平台会分别记住各自的配置，切换平台时自动恢复。已保存的密钥会显示为脱敏格式（如 `sk-x****ejsr`），无需重新输入即可看到已保存状态。

测试连接通过后才会保存配置，避免写入无效配置。

---

## 界面概览

界面包含四个功能页面和一个关于页面：

| 页面 | 功能 |
|------|------|
| **选择文件** | 浏览/扫描工作目录，管理字幕、视频、往期笔记任务列表 |
| **课程设置** | 填写课程名称和总体要求 |
| **开始运行** | 实时进度、Console 输出、字符计数、任务状态 |
| **API设置** | 平台选择、模型/接口/密钥配置、连接测试 |
| **关于** | 作者信息与项目链接 |

---

## 输出结构

每个任务生成一个独立课程目录：

```text
某节课_来源目录_课程名/
├── 某节课_课程名_课堂总结.md
└── imgs/
    ├── 001.png
    ├── 002.png
    └── ...
```

- `课堂总结.md`：最终整理结果，包含生成时间、源文件路径、模型信息
- `imgs/`：课堂截图和结构化图示
- 纯字幕任务：不生成截图
- 视频任务必须有有效截图，否则任务失败，不降级为纯文本

---

## 从源码打包

```bat
cd build\windows
build.bat
```

输出 `dist\srt-summarizer-v2.0.exe`（约 84 MB）。

打包内容：
- Python 运行时
- 全部业务代码（FastAPI + Jinja2 模板 + 静态资源）
- ffmpeg（视频抽帧）
- HarmonyOS Sans SC 中文字体（图表渲染）
- OpenCV（图像处理）

---

## 配置保存位置

```text
~/.srt_summarizer/settings.json
~/.srt_summarizer/secrets.json
```

---

## 运行环境

- **预编译版**：Windows 10 / 11
- **源码运行**：Python 3.10+，跨平台

---

## 常见问题

**API 连接失败**
- 检查 API Key、接口地址、模型名称是否正确
- 使用 **测试配置** 按钮验证连接
- Claude 平台需确认接口地址为 `https://api.anthropic.com/v1/messages`

**视频任务失败**
- 确认视频文件可正常播放
- 检查是否提取到有效截图

**浏览器没有自动打开**
- 手动访问 `http://127.0.0.1:8099`
- 检查终端窗口是否有错误日志
- 确认端口 8099 未被占用

---

## 提示

首次使用建议先用一节较短课程测试，确认 API 可用、能正常生成 Markdown 后，再批量整理整门课资料。
