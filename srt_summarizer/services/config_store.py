import json
import os
from dataclasses import dataclass

from srt_summarizer.services.provider_registry import get_provider


CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".srt_summarizer")
SETTINGS_PATH = os.path.join(CONFIG_DIR, "settings.json")
SECRETS_PATH = os.path.join(CONFIG_DIR, "secrets.json")


@dataclass
class RuntimeConfig:
    provider: str
    model: str
    base_url: str
    api_key: str
    output_dir: str = ""
    save_to_source: bool = False
    course_name: str = ""


DEFAULT_PROVIDER = "deepseek"


def _ensure_config_dir() -> None:
    os.makedirs(CONFIG_DIR, exist_ok=True)


def _read_json(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        # 保留文件但内容损坏时返回空字典，不覆盖文件
        return {}
    except OSError:
        return {}
    return data if isinstance(data, dict) else {}


def _load_provider_values(settings: dict, field_name: str) -> dict[str, str]:
    raw_values = settings.get(field_name)
    if not isinstance(raw_values, dict):
        return {}
    provider_values: dict[str, str] = {}
    for key, value in raw_values.items():
        provider_key = str(key).strip()
        field_value = str(value).strip()
        if provider_key and field_value:
            provider_values[provider_key] = field_value
    return provider_values


def _load_provider_models(settings: dict) -> dict[str, str]:
    return _load_provider_values(settings, "provider_models")


def _load_provider_urls(settings: dict) -> dict[str, str]:
    return _load_provider_values(settings, "provider_urls")


def _load_provider_keys(secrets: dict) -> dict[str, str]:
    return _load_provider_values(secrets, "provider_api_keys")


def load_provider_runtime_state() -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    settings = _read_json(SETTINGS_PATH)
    secrets = _read_json(SECRETS_PATH)
    return _load_provider_models(settings), _load_provider_urls(settings), _load_provider_keys(secrets)


def load_runtime_config() -> RuntimeConfig:
    settings = _read_json(SETTINGS_PATH)
    secrets = _read_json(SECRETS_PATH)
    provider_key = str(settings.get("provider") or DEFAULT_PROVIDER).strip() or DEFAULT_PROVIDER
    provider = get_provider(provider_key)
    provider_models = _load_provider_models(settings)
    provider_urls = _load_provider_urls(settings)
    provider_keys = _load_provider_keys(secrets)
    return RuntimeConfig(
        provider=provider.key,
        model=provider_models.get(provider.key) or str(settings.get("model") or provider.default_model).strip() or provider.default_model,
        base_url=provider_urls.get(provider.key) or str(settings.get("base_url") or provider.base_url).strip() or provider.base_url,
        api_key=provider_keys.get(provider.key) or str(secrets.get("api_key") or "").strip(),
        output_dir=str(settings.get("output_dir") or "").strip(),
        save_to_source=bool(settings.get("save_to_source", False)),
        course_name=str(settings.get("course_name") or "").strip(),
    )


def save_runtime_config(config: RuntimeConfig) -> None:
    _ensure_config_dir()
    settings = _read_json(SETTINGS_PATH)
    secrets = _read_json(SECRETS_PATH)
    provider_models = _load_provider_models(settings)
    provider_urls = _load_provider_urls(settings)
    provider_keys = _load_provider_keys(secrets)
    provider_models[config.provider] = config.model.strip()
    provider_urls[config.provider] = config.base_url.strip()
    provider_keys[config.provider] = config.api_key.strip()
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(
            {
                "provider": config.provider,
                "model": config.model,
                "provider_models": provider_models,
                "base_url": config.base_url,
                "provider_urls": provider_urls,
                "output_dir": config.output_dir,
                "save_to_source": config.save_to_source,
                "course_name": config.course_name,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
    with open(SECRETS_PATH, "w", encoding="utf-8") as f:
        json.dump(
            {
                "api_key": config.api_key,
                "provider_api_keys": provider_keys,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
