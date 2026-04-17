import os

from srt_summarizer.processing.file_loader import parse_file
from srt_summarizer.processing.input_models import CourseContext


def build_course_context(course_name: str, requirements_text: str, prior_note_paths: list[str]) -> CourseContext:
    notes: list[tuple[str, str]] = []
    for path in prior_note_paths:
        content = parse_file(path)
        notes.append((os.path.basename(path), content))
    return CourseContext(
        course_name=course_name.strip(),
        requirements_text=requirements_text.strip(),
        prior_notes=notes,
    )
