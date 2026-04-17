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
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def load_runtime_config() -> RuntimeConfig:
    settings = _read_json(SETTINGS_PATH)
    secrets = _read_json(SECRETS_PATH)
    provider_key = str(settings.get("provider") or DEFAULT_PROVIDER).strip() or DEFAULT_PROVIDER
    provider = get_provider(provider_key)
    return RuntimeConfig(
        provider=provider.key,
        model=str(settings.get("model") or provider.default_model).strip() or provider.default_model,
        base_url=str(settings.get("base_url") or provider.base_url).strip() or provider.base_url,
        api_key=str(secrets.get("api_key") or "").strip(),
        output_dir=str(settings.get("output_dir") or "").strip(),
        save_to_source=bool(settings.get("save_to_source", False)),
        course_name=str(settings.get("course_name") or "").strip(),
    )


def save_runtime_config(config: RuntimeConfig) -> None:
    _ensure_config_dir()
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(
            {
                "provider": config.provider,
                "model": config.model,
                "base_url": config.base_url,
                "output_dir": config.output_dir,
                "save_to_source": config.save_to_source,
                "course_name": config.course_name,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
    with open(SECRETS_PATH, "w", encoding="utf-8") as f:
        json.dump({"api_key": config.api_key}, f, ensure_ascii=False, indent=2)
