# SRT-SUMMARIZER v2.0

AI 驱动的课堂录播整理工具，把字幕、转录文本和视频整理成结构化 Markdown 笔记。

## 下载

[srt-summarizer-v2.0.exe](https://github.com/AsukaIIV/srt-summarizer/releases/download/v2.0/srt-summarizer-v2.0.exe)（84 MB）

开箱即用，内嵌 ffmpeg 和中文字体，无需安装 Python 或任何依赖。

## v2.0 更新内容

### 全新 Web 界面

使用 Material Design 3 设计语言重新构建，响应式布局，浏览器访问。

### 功能改进

- 按平台分别记住模型、接口地址和 API Key，切换平台自动恢复
- 已保存的 API Key 显示脱敏占位（如 `sk-x****ejsr`），一眼可知已配置状态
- 测试连接通过后才保存配置，避免写入无效配置
- Console 输出自动滚动到最新内容
- 状态指示器固定宽度，布局更稳定
- 新增关于页面

### 打包

- 单文件 EXE，内嵌 ffmpeg.exe 和 HarmonyOS Sans SC 中文字体
- 双击启动，终端显示运行日志，浏览器自动打开
- 关闭终端窗口即可退出

## 使用方法

1. 下载 `srt-summarizer-v2.0.exe` 并双击运行
2. 浏览器自动打开 `http://127.0.0.1:8099`
3. 在 **API设置** 填写平台、模型、接口地址和 API Key
4. 在 **选择文件** 中添加字幕和视频
5. 切换到 **开始运行** 开始整理

## 注意事项

- 首次使用建议先用一节较短课程测试
- 如果浏览器没有自动打开，手动访问 `http://127.0.0.1:8099`
- 关闭终端窗口即可完全退出程序
