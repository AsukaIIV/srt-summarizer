from collections.abc import Callable

from srt_summarizer.services.config_store import load_runtime_config
from srt_summarizer.services.llm_client import stream_completion


def stream_deepseek(
    transcript: str,
    on_token: Callable[[str], None],
    on_done: Callable[[str], None],
    on_error: Callable[[str], None],
) -> None:
    config = load_runtime_config()
    stream_completion(config, f"请总结以下课堂录音内容：\n\n{transcript}", on_token, on_done, on_error)
