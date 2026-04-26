import json
from collections.abc import Callable
from typing import Any

import requests

from srt_summarizer.config import SYSTEM_PROMPT
from srt_summarizer.services.config_store import RuntimeConfig
from srt_summarizer.services.provider_registry import get_provider


ANTHROPIC_VERSION = "2023-06-01"


def _get_provider(runtime_config: RuntimeConfig):
    return get_provider(runtime_config.provider)


def _build_openai_payload(user_prompt: str, model: str, stream: bool = True, max_tokens: int = 8192) -> dict[str, Any]:
    return {
        "model": model,
        "stream": stream,
        "temperature": 0.3,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    }


def _build_anthropic_payload(user_prompt: str, model: str, stream: bool = True, max_tokens: int = 8192) -> dict[str, Any]:
    return {
        "model": model,
        "stream": stream,
        "system": SYSTEM_PROMPT,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": [{"type": "text", "text": user_prompt}]}],
    }


def _build_test_payload(runtime_config: RuntimeConfig) -> dict[str, Any]:
    provider = _get_provider(runtime_config)
    if provider.api_style == "anthropic_messages":
        return {
            "model": runtime_config.model,
            "stream": False,
            "max_tokens": 16,
            "system": "You are a connectivity test.",
            "messages": [{"role": "user", "content": [{"type": "text", "text": "Reply with ok."}]}],
        }
    return {
        "model": runtime_config.model,
        "stream": False,
        "max_tokens": 16,
        "messages": [
            {"role": "system", "content": "You are a connectivity test."},
            {"role": "user", "content": "Reply with ok."},
        ],
    }


def _build_headers(runtime_config: RuntimeConfig) -> dict[str, str]:
    provider = _get_provider(runtime_config)
    if provider.api_style == "anthropic_messages":
        return {
            "x-api-key": runtime_config.api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "Content-Type": "application/json",
        }
    return {
        "Authorization": f"Bearer {runtime_config.api_key}",
        "Content-Type": "application/json",
    }


def _extract_openai_delta(line: str) -> str:
    if line.startswith("data:"):
        line = line[5:].strip()
    if line == "[DONE]":
        return ""
    chunk = json.loads(line)
    return chunk["choices"][0]["delta"].get("content", "")


def _extract_anthropic_delta(line: str) -> str:
    if line.startswith("event:"):
        return ""
    if not line.startswith("data:"):
        return ""
    payload = line[5:].strip()
    if not payload:
        return ""
    chunk = json.loads(payload)
    if chunk.get("type") == "content_block_delta":
        delta = chunk.get("delta", {})
        if isinstance(delta, dict):
            return str(delta.get("text", ""))
    return ""


def _extract_openai_content(data: dict[str, Any]) -> str:
    message = data.get("choices", [{}])[0].get("message", {})
    content = message.get("content", "")
    if isinstance(content, list):
        content = "".join(str(item.get("text", "")) for item in content if isinstance(item, dict))
    return str(content).strip()


def _extract_anthropic_content(data: dict[str, Any]) -> str:
    content = data.get("content", [])
    if not isinstance(content, list):
        return ""
    parts: list[str] = []
    for item in content:
        if not isinstance(item, dict):
            continue
        if item.get("type") == "text":
            parts.append(str(item.get("text", "")))
    return "".join(parts).strip()


def _format_request_error(error: Exception) -> str:
    if isinstance(error, requests.HTTPError) and error.response is not None:
        status = error.response.status_code
        if status in {401, 403}:
            return "API 认证失败，请检查 API Key"
        if status == 429:
            return "请求过于频繁，请稍后重试"
        return f"模型请求失败（HTTP {status}）"
    if isinstance(error, requests.Timeout):
        return "请求超时，请稍后重试"
    if isinstance(error, requests.RequestException):
        return f"网络请求失败：{error}"
    return str(error)


def test_runtime_config(runtime_config: RuntimeConfig) -> tuple[bool, str]:
    try:
        resp = requests.post(
            runtime_config.base_url,
            headers=_build_headers(runtime_config),
            json=_build_test_payload(runtime_config),
            timeout=30,
        )
        resp.raise_for_status()
        return True, "配置可用"
    except Exception as e:
        return False, _format_request_error(e)


def stream_completion(
    runtime_config: RuntimeConfig,
    user_prompt: str,
    on_token: Callable[[str], None],
    on_done: Callable[[str], None],
    on_error: Callable[[str], None],
) -> None:
    """流式调用 LLM，通过回调返回结果。

    支持 OpenAI Chat 和 Anthropic Messages 两种 API 风格。
    - on_token: 每收到一个 text delta 时调用
    - on_done: 完整内容组装完成后调用
    - on_error: 发生错误时调用
    """
    if not user_prompt:
        on_error("输入内容为空")
        return

    provider = _get_provider(runtime_config)
    payload = (
        _build_anthropic_payload(user_prompt, runtime_config.model, stream=True, max_tokens=8192)
        if provider.api_style == "anthropic_messages"
        else _build_openai_payload(user_prompt, runtime_config.model, stream=True, max_tokens=8192)
    )
    delta_parser = _extract_anthropic_delta if provider.api_style == "anthropic_messages" else _extract_openai_delta
    try:
        with requests.post(
            runtime_config.base_url,
            headers=_build_headers(runtime_config),
            json=payload,
            stream=True,
            timeout=180,
        ) as resp:
            resp.raise_for_status()
            full: list[str] = []
            parse_error = False
            for raw_line in resp.iter_lines():
                if not raw_line:
                    continue
                line = raw_line.decode("utf-8") if isinstance(raw_line, bytes) else raw_line
                if provider.api_style != "anthropic_messages" and line.startswith("data:") and line[5:].strip() == "[DONE]":
                    break
                try:
                    delta = delta_parser(line)
                except (json.JSONDecodeError, KeyError, IndexError):
                    parse_error = True
                    continue
                if delta:
                    full.append(delta)
                    on_token(delta)
            full_text = "".join(full)
            if not full_text:
                if parse_error:
                    on_error("模型返回了无法解析的流式响应")
                    return
                on_error("模型未返回有效内容")
                return
            on_done(full_text)
    except Exception as e:
        on_error(_format_request_error(e))
