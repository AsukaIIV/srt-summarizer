import re

from srt_summarizer.processing.input_models import CourseContext, LessonInput


COURSE_NAME_RE = re.compile(r"课程名称\s*\|\s*([^|\n]+)")


def guess_course_name(transcript: str, lesson: LessonInput, context: CourseContext) -> str:
    if lesson.course_name.strip():
        return lesson.course_name.strip()
    if context.course_name.strip():
        return context.course_name.strip()
    match = COURSE_NAME_RE.search(transcript)
    if match:
        return match.group(1).strip()
    return lesson.source_label.strip() or "未命名课程"


def build_user_prompt(
    transcript: str,
    lesson: LessonInput,
    context: CourseContext,
    image_markdown_lines: list[str],
) -> str:
    sections: list[str] = []
    sections.append(
        "请严格遵守系统给出的课堂总结结构，不要改变五段结构，不要省略信息，不要臆造不确定内容。"
        "整理目标是输出一份高质量、可直接复习的 Markdown 课堂笔记。"
    )
    sections.append(
        "请默认面向第一次学习本节内容的学生写作："
        "在关键定义、公式、推导跳步处补足最必要的解释，"
        "适度点出易混淆处与理解门槛，但不要把整篇写成教学口语稿，也不要加入过多额外提示。"
    )
    if image_markdown_lines:
        sections.append(
            f"本次最多可使用 {len(image_markdown_lines)} 个插图锚点。"
            "如需建议插图位置，只能在正文中输出形如 [[插图1]] 的锚点。"
            "不要直接输出图片 Markdown，不要把锚点集中堆到文末，也不要为帮助不大的图片强行放锚点。"
        )
    if context.course_name.strip():
        sections.append(f"## 课程名\n{context.course_name.strip()}")
    if context.requirements_text.strip():
        sections.append(f"## 课程总体要求\n{context.requirements_text.strip()}")
    if context.prior_notes:
        prior_blocks = []
        for name, content in context.prior_notes:
            prior_blocks.append(f"### 往期笔记：{name}\n{content}")
        sections.append("## 往期课程笔记\n请结合这些笔记保持课程连续性，但不要重复抄写同一内容。\n\n" + "\n\n".join(prior_blocks))
    if lesson.video_path:
        if image_markdown_lines:
            sections.append(
                "## 课堂截图\n"
                "用户提供了对应视频，以下是已抽取的课堂截图。请把截图当作辅助理解的教学材料，而不是装饰。"
                "优先在以下场景自然引用：板书推导、公式变形、图示、例题步骤、定义对比、教师特别强调的关键页。"
                "如果某张截图能明显降低理解门槛，请在对应知识点附近输出对应锚点，不要全部堆到文末。"
                "如果截图较少，更要优先服务于最难理解、最需要视觉支撑的内容。"
                "如果图片帮助不大，可以不放锚点，但不要为了插图而插图。"
                "每张图最多使用一次锚点，锚点编号必须与下方截图编号一致。\n\n"
                + "\n".join(image_markdown_lines)
            )
    sections.append(f"## 当前课堂转录\n{transcript.strip()}")
    return "\n\n".join(section for section in sections if section.strip())
