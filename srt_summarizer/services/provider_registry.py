from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderDefinition:
    key: str
    label: str
    base_url: str
    default_model: str


PROVIDERS: dict[str, ProviderDefinition] = {
    "deepseek": ProviderDefinition(
        key="deepseek",
        label="DeepSeek",
        base_url="https://api.deepseek.com/v1/chat/completions",
        default_model="deepseek-reasoner",
    ),
    "openai_compatible": ProviderDefinition(
        key="openai_compatible",
        label="OpenAI Compatible",
        base_url="https://api.openai.com/v1/chat/completions",
        default_model="gpt-4o-mini",
    ),
}


def get_provider(provider_key: str) -> ProviderDefinition:
    return PROVIDERS.get(provider_key, PROVIDERS["deepseek"])


def get_provider_labels() -> dict[str, str]:
    return {key: provider.label for key, provider in PROVIDERS.items()}
