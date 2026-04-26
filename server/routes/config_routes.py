from __future__ import annotations

import asyncio
import os
from fastapi import APIRouter

from srt_summarizer.config import (
    _invalidate_config_cache,
    get_config_errors,
    get_runtime_config,
    is_valid_api_key,
)
from srt_summarizer.services.config_store import (
    RuntimeConfig,
    load_provider_runtime_state,
    save_runtime_config,
)
from srt_summarizer.services.llm_client import test_runtime_config
from srt_summarizer.services.provider_registry import PROVIDERS

from server.models.schemas import (
    ConfigResponse,
    ConfigSaveRequest,
    ConfigTestResponse,
    ProviderInfo,
)
from server.session import get_session

router = APIRouter(prefix="/api", tags=["config"])


def _mask_api_key(key: str) -> str:
    if not key or len(key) <= 8:
        return "" if not key else "*" * len(key)
    return key[:4] + "*" * (len(key) - 8) + key[-4:]


def _default_output_dir() -> str:
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    return desktop if os.path.isdir(desktop) else os.path.expanduser("~")


def _resolve_output_dir(config_output_dir: str) -> str:
    if config_output_dir and os.path.isdir(config_output_dir):
        return config_output_dir
    return _default_output_dir()


@router.get("/config", response_model=ConfigResponse)
async def get_config():
    config = get_runtime_config()
    provider_labels = {key: p.label for key, p in PROVIDERS.items()}
    provider_models, provider_urls, provider_api_keys = load_provider_runtime_state()
    api_keys_present = {key: bool(v) for key, v in provider_api_keys.items()}
    masked_keys = {key: _mask_api_key(v) for key, v in provider_api_keys.items()}
    return ConfigResponse(
        provider=config.provider,
        model=config.model,
        base_url=config.base_url,
        api_key="",
        masked_api_key=_mask_api_key(config.api_key),
        output_dir=_resolve_output_dir(config.output_dir),
        save_to_source=config.save_to_source,
        course_name=config.course_name,
        provider_labels=provider_labels,
        provider_models=provider_models,
        provider_urls=provider_urls,
        provider_api_keys_present=api_keys_present,
        provider_masked_keys=masked_keys,
    )


@router.post("/config")
async def save_config(body: ConfigSaveRequest):
    def _save():
        provider_models, provider_urls, provider_api_keys = load_provider_runtime_state()

        # Restore from provider memory when fields are empty (matches frontend behavior)
        model = body.model if body.model else provider_models.get(body.provider, "")
        base_url = body.base_url if body.base_url else provider_urls.get(body.provider, "")
        api_key = body.api_key if body.api_key else provider_api_keys.get(body.provider, "")

        if model:
            provider_models[body.provider] = model
        if base_url:
            provider_urls[body.provider] = base_url
        if api_key:
            provider_api_keys[body.provider] = api_key

        config = RuntimeConfig(
            provider=body.provider,
            model=model,
            base_url=base_url,
            api_key=api_key,
            output_dir=body.output_dir,
            save_to_source=body.save_to_source,
            course_name=body.course_name,
        )
        save_runtime_config(config)
        _invalidate_config_cache()
        session = get_session()
        session.output_dir = body.output_dir
        session.save_to_source = body.save_to_source
        session.course_name = body.course_name
        return {"ok": True}

    return await asyncio.to_thread(_save)


@router.post("/config/test", response_model=ConfigTestResponse)
async def test_config(body: ConfigSaveRequest):
    provider_models, provider_urls, provider_api_keys = load_provider_runtime_state()

    model = body.model if body.model else provider_models.get(body.provider, "")
    base_url = body.base_url if body.base_url else provider_urls.get(body.provider, "")
    api_key = body.api_key if body.api_key else provider_api_keys.get(body.provider, "")

    config = RuntimeConfig(
        provider=body.provider,
        model=model,
        base_url=base_url,
        api_key=api_key,
    )
    errors = get_config_errors(config)
    if errors:
        return ConfigTestResponse(ok=False, message="；".join(errors))
    ok, message = await asyncio.to_thread(test_runtime_config, config)
    return ConfigTestResponse(ok=ok, message=message)


@router.get("/providers", response_model=list[ProviderInfo])
async def list_providers():
    return [
        ProviderInfo(
            key=p.key,
            label=p.label,
            base_url=p.base_url,
            default_model=p.default_model,
            api_style=p.api_style,
            config_help_text=p.config_help_text,
        )
        for p in PROVIDERS.values()
    ]


@router.get("/config/status")
async def config_status():
    config = get_runtime_config()
    errors = get_config_errors(config)
    if not errors:
        return {"status": "ok", "label": "已验证可用" if is_valid_api_key(config.api_key) else "已配置"}
    return {"status": "error", "label": "未配置"}
