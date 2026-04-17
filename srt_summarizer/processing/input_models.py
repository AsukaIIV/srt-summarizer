from dataclasses import dataclass, field


@dataclass
class CourseContext:
    course_name: str = ""
    requirements_text: str = ""
    prior_notes: list[tuple[str, str]] = field(default_factory=list)


@dataclass
class LessonInput:
    lesson_id: str
    transcript_path: str
    video_path: str = ""
    source_label: str = ""
    course_name: str = ""
    requirements_text: str = ""
    prior_note_paths: list[str] = field(default_factory=list)
