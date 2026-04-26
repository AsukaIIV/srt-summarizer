from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderDefinition:
    key: str
    label: str
    base_url: str
    default_model: str
    api_style: str = "openai_chat"
    config_help_text: str = ""


PROVIDERS: dict[str, ProviderDefinition] = {
    "deepseek": ProviderDefinition(
        key="deepseek",
        label="DeepSeek",
        base_url="https://api.deepseek.com/v1/chat/completions",
        default_model="deepseek-v4-flash",
        api_style="openai_chat",
        config_help_text="使用 DeepSeek 官方接口。",
    ),
    "openai_compatible": ProviderDefinition(
        key="openai_compatible",
        label="OpenAI Compatible",
        base_url="https://api.openai.com/v1/chat/completions",
        default_model="gpt-4o-mini",
        api_style="openai_chat",
        config_help_text="适用于兼容 OpenAI Chat Completions 的接口。",
    ),
    "siliconflow": ProviderDefinition(
        key="siliconflow",
        label="硅基流动",
        base_url="https://api.siliconflow.cn/v1/chat/completions",
        default_model="Qwen/Qwen2.5-7B-Instruct",
        api_style="openai_chat",
        config_help_text="默认使用硅基流动 OpenAI 兼容接口。",
    ),
    "qwen": ProviderDefinition(
        key="qwen",
        label="千问",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        default_model="qwen-plus",
        api_style="openai_chat",
        config_help_text="默认使用千问兼容 OpenAI 的接口地址。",
    ),
    "kimi": ProviderDefinition(
        key="kimi",
        label="Kimi",
        base_url="https://api.moonshot.cn/v1/chat/completions",
        default_model="moonshot-v1-8k",
        api_style="openai_chat",
        config_help_text="默认使用 Kimi 的 OpenAI 兼容接口。",
    ),
    "claude": ProviderDefinition(
        key="claude",
        label="Claude",
        base_url="https://api.anthropic.com/v1/messages",
        default_model="claude-sonnet-4-5",
        api_style="anthropic_messages",
        config_help_text="默认使用 Claude 原生 Anthropic Messages 接口。",
    ),
}


def get_provider(provider_key: str) -> ProviderDefinition:
    return PROVIDERS.get(provider_key, PROVIDERS["deepseek"])


def get_provider_labels() -> dict[str, str]:
    return {key: provider.label for key, provider in PROVIDERS.items()}
