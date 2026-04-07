# 🎓 SRT 课堂总结工具

> 将课堂录音字幕文件自动总结为结构化 Markdown 笔记，由 DeepSeek AI 驱动，实时流式输出。

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![Platform](https://img.shields.io/badge/Platform-Windows%2011-blue?logo=windows)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 📸 界面预览

> 双击 `start.bat` 即可启动，无需任何配置界面

![screenshot](/img/screenshot.png)

---

## ✨ 功能特性

- **📂 批量处理** — 递归扫描目录，一次处理所有文件
- **📄 单文件选取** — 支持直接选择单个或多个文件，无需指定目录
- **🗑️ 文件列表管理** — 支持在处理前从列表中移除不需要的文件
- **🤖 AI 总结** — 由 DeepSeek 生成结构化课堂笔记，覆盖概要、知识点、强调重点、作业与考点
- **⚡ 实时流式输出** — 逐字符实时显示 AI 生成内容，无需等待
- **🎨 Markdown 语法着色** — 输出面板实时对标题（蓝色）和粗体内容（橙色）高亮渲染
- **🔢 实时字符计数** — 输出面板实时显示已生成字符数，直观追踪进度
- **🔵 处理状态动画** — 处理期间顶部显示脉冲 `●` 指示器，醒目提示运行状态
- **📊 API 连接状态** — 导航栏实时显示 API Key 配置状态（绿色已连接 / 红色未配置）与当前使用模型名称
- **📄 多格式支持** — 支持 `.srt`、`.txt`、`.md` 文件输入
- **📁 灵活输出路径** — 可输出到指定目录，或直接输出到源文件所在目录
- **🎨 深色主题 UI** — 基于 Tkinter 的深色界面，文件状态实时着色（黄色处理中 / 绿色完成 / 红色失败）
- **🖥️ 开箱即用** — 双击 `start.bat` 自动检查依赖并启动，窗口默认最大化，无需手动配置环境

---

## 📦 安装与使用

### 前置条件

- Windows 10 / 11
- [Python 3.10+](https://www.python.org/downloads/)（安装时务必勾选 **Add Python to PATH** 和 **tcl/tk and IDLE**）

### 快速开始

**1. 下载项目**

```bash
git clone https://github.com/AsukaIIV/srt-summarizer.git
cd srt-summarizer
```

或直接下载 ZIP 解压。

**2. 填写 API Key**

用文本编辑器打开 `srt_summarizer.py`，找到第 15 行：

```python
API_KEY = "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

替换为你的 [DeepSeek API Key](https://platform.deepseek.com/)。

**3. 启动程序**

双击 `start.bat`，程序将自动：
- 检测 Python 环境及 tkinter 是否可用
- 安装所需依赖（`requests`）
- 以最大化窗口启动图形界面

---

## 🖱️ 使用说明

| 步骤 | 操作 |
|------|------|
| ① | 点击「📂 选择并扫描」选择包含字幕文件的文件夹（递归扫描），**或**点击「📄 选择单个文件」直接选取一个或多个文件 |
| ② | 在文件列表中确认要处理的文件；如需排除某些文件，选中后点击「移除所选」 |
| ③ | 设置输出目录（默认为桌面），或开启「输出到源目录」 |
| ④ | 点击「▶ 开始总结」，实时输出面板将逐字显示 AI 生成内容，标题以蓝色高亮，重点加粗以橙色显示 |
| ⑤ | 处理完成后，Markdown 文件自动保存至目标目录，弹窗提示结果统计 |

### 两种文件选取方式

| 方式 | 适用场景 |
|------|----------|
| 📂 选择并扫描目录 | 一次处理整个课程目录下的所有字幕文件 |
| 📄 选择单个文件 | 只处理特定的几个文件，精确控制处理范围 |

### 输出到源目录

底部「📁 输出到源目录」按钮默认关闭。开启后，每个文件的总结 Markdown 将保存在**与源文件相同的文件夹**中，方便按课程目录管理笔记。

---

## ⚙️ 配置说明

打开 `srt_summarizer.py`，顶部可修改以下配置：

```python
# ══════════════════════════════════════════════
#  ★ 在此填写你的 DeepSeek API Key ★
API_KEY = "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
#  模型：deepseek-chat / deepseek-reasoner
MODEL   = "deepseek-chat"
# ══════════════════════════════════════════════
```

| 配置项 | 说明 |
|--------|------|
| `API_KEY` | DeepSeek 平台的 API Key；配置后导航栏显示绿色「● 已连接」 |
| `MODEL` | `deepseek-chat`（快速，推荐）或 `deepseek-reasoner`（深度推理，较慢）；当前模型名称会显示在导航栏右侧 |

---

## 📝 输出格式示例

每个文件生成一份 `原文件名_总结_时间戳.md`，结构如下：

```markdown
# 课堂名称 课堂总结

> 生成时间：2026-03-09 14:32:01
> 源文件：`C:\Users\...\lecture01.srt`

---

## 一、课程概要
| 项目 | 内容 |
| 上课日期 | 2026-03-09 |
| 课程名称 | 光纤通信 |
...

## 第一部分：xxx
### 1. 知识点
#### 1.1 子话题
...

## 三、教师强调重点 ⚠️
> 【强调】所属知识点 — 具体内容

## 四、作业与考试重点
...

## 五、课程总结
...
```

---

## 🗂️ 项目结构

```
srt-summarizer/
├── srt_summarizer.py   # 主程序
├── start.bat           # Windows 一键启动脚本
├── README.md           # 项目说明
└── img/                # 配图
```

---

## 🔧 依赖

| 库 | 用途 | 安装方式 |
|----|------|----------|
| `requests` | 调用 DeepSeek API | `pip install requests`（start.bat 自动安装） |
| `tkinter` | 图形界面 | Python 内置，安装 Python 时勾选 tcl/tk and IDLE |

---

## 📄 License

本项目采用 [MIT License](LICENSE) 开源协议。