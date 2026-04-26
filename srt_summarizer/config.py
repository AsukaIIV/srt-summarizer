import os
from pathlib import Path
from urllib.parse import urlparse

from srt_summarizer.services.config_store import RuntimeConfig, load_runtime_config
from srt_summarizer.services.provider_registry import get_provider

PLACEHOLDER_API_KEYS = {"", "sk-xxxxxxxxxxxxxxxx", "sk-xxx"}

# 惰性初始化的配置缓存，避免模块导入时 I/O 失败导致应用崩溃
_CONFIG_CACHE: RuntimeConfig | None = None


def _get_cached_config() -> RuntimeConfig:
    global _CONFIG_CACHE
    if _CONFIG_CACHE is None:
        try:
            _CONFIG_CACHE = load_runtime_config()
        except Exception:
            provider = get_provider("deepseek")
            _CONFIG_CACHE = RuntimeConfig(
                provider="deepseek",
                model=provider.default_model,
                base_url=provider.base_url,
                api_key="",
            )
    return _CONFIG_CACHE


def _invalidate_config_cache() -> None:
    global _CONFIG_CACHE
    _CONFIG_CACHE = None


DEFAULT_OUTPUT_DIR = ""
DEFAULT_SAVE_TO_SOURCE = False
DEFAULT_COURSE_NAME = ""


def _clean_env(name: str, default: str) -> str:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip()


def is_valid_api_key(value: str) -> bool:
    candidate = value.strip()
    return candidate not in PLACEHOLDER_API_KEYS and len(candidate) >= 10


def is_valid_model(value: str) -> bool:
    return bool(value.strip())


def is_valid_url(value: str) -> bool:
    candidate = value.strip()
    if not candidate:
        return False
    parsed = urlparse(candidate)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def get_runtime_config() -> RuntimeConfig:
    cached = _get_cached_config()
    provider = _clean_env("LLM_PROVIDER", cached.provider)
    provider_def = get_provider(provider)
    return RuntimeConfig(
        provider=provider_def.key,
        model=_clean_env("LLM_MODEL", cached.model or provider_def.default_model),
        base_url=_clean_env("LLM_BASE_URL", cached.base_url or provider_def.base_url),
        api_key=_clean_env("LLM_API_KEY", cached.api_key),
        output_dir=cached.output_dir,
        save_to_source=cached.save_to_source,
        course_name=cached.course_name,
    )


def get_config_errors(config: RuntimeConfig | None = None) -> list[str]:
    current = config or get_runtime_config()
    errors: list[str] = []
    if not is_valid_api_key(current.api_key):
        errors.append("请先配置有效的 API Key")
    if not is_valid_model(current.model):
        errors.append("模型名称不能为空")
    if not is_valid_url(current.base_url):
        errors.append("接口地址无效")
    return errors


_SYSTEM_PROMPT_CACHE: str | None = None


def get_system_prompt() -> str:
    """从独立文件加载系统提示词，避免硬编码在 Python 源码中。"""
    global _SYSTEM_PROMPT_CACHE
    if _SYSTEM_PROMPT_CACHE is not None:
        return _SYSTEM_PROMPT_CACHE
    prompt_path = Path(__file__).resolve().parent / "prompts" / "system.md"
    try:
        _SYSTEM_PROMPT_CACHE = prompt_path.read_text(encoding="utf-8")
        return _SYSTEM_PROMPT_CACHE
    except (OSError, UnicodeDecodeError) as e:
        raise RuntimeError(f"加载系统提示词文件失败：{prompt_path} — {e}") from e


SYSTEM_PROMPT = get_system_prompt()
