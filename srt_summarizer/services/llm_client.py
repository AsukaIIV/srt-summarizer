import json
import re
from collections.abc import Callable
from typing import Any

import requests

from srt_summarizer.config import SYSTEM_PROMPT
from srt_summarizer.services.config_store import RuntimeConfig


JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*(\{[\s\S]*\})\s*```|(?P<plain>\{[\s\S]*\})")


def _build_payload(user_prompt: str, model: str, stream: bool = True, max_tokens: int = 8192) -> dict[str, Any]:
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


def _extract_delta(line: str) -> str:
    if line.startswith("data:"):
        line = line[5:].strip()
    if line == "[DONE]":
        return ""
    chunk = json.loads(line)
    return chunk["choices"][0]["delta"].get("content", "")


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
    headers = {
        "Authorization": f"Bearer {runtime_config.api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": runtime_config.model,
        "stream": False,
        "max_tokens": 16,
        "messages": [
            {"role": "system", "content": "You are a connectivity test."},
            {"role": "user", "content": "Reply with ok."},
        ],
    }
    try:
        resp = requests.post(runtime_config.base_url, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        return True, "配置可用"
    except Exception as e:
        return False, _format_request_error(e)


def completion(runtime_config: RuntimeConfig, user_prompt: str, max_tokens: int = 1200) -> str:
    user_prompt = user_prompt.strip()
    if not user_prompt:
        raise ValueError("输入内容为空")
    headers = {
        "Authorization": f"Bearer {runtime_config.api_key}",
        "Content-Type": "application/json",
    }
    try:
        resp = requests.post(
            runtime_config.base_url,
            headers=headers,
            json=_build_payload(user_prompt, runtime_config.model, stream=False, max_tokens=max_tokens),
            timeout=180,
        )
        resp.raise_for_status()
        data = resp.json()
        message = data.get("choices", [{}])[0].get("message", {})
        content = message.get("content", "")
        if isinstance(content, list):
            content = "".join(str(item.get("text", "")) for item in content if isinstance(item, dict))
        content = str(content).strip()
        if not content:
            raise ValueError("模型未返回有效内容")
        return content
    except Exception as e:
        raise RuntimeError(_format_request_error(e)) from e


def _parse_json_block(text: str) -> dict[str, Any]:
    match = JSON_BLOCK_RE.search(text.strip())
    if not match:
        raise ValueError("截图规划结果不是有效 JSON")
    block = match.group(1) or match.group("plain") or ""
    payload = json.loads(block)
    if not isinstance(payload, dict):
        raise ValueError("截图规划结果格式错误")
    return payload


def stream_completion(
    runtime_config: RuntimeConfig,
    user_prompt: str,
    on_token: Callable[[str], None],
    on_done: Callable[[str], None],
    on_error: Callable[[str], None],
) -> None:
    user_prompt = user_prompt.strip()
    if not user_prompt:
        on_error("输入内容为空")
        return

    headers = {
        "Authorization": f"Bearer {runtime_config.api_key}",
        "Content-Type": "application/json",
    }
    try:
        with requests.post(
            runtime_config.base_url,
            headers=headers,
            json=_build_payload(user_prompt, runtime_config.model, stream=True, max_tokens=8192),
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
                if line.startswith("data:") and line[5:].strip() == "[DONE]":
                    break
                try:
                    delta = _extract_delta(line)
                except Exception:
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
