from __future__ import annotations

from pydantic import BaseModel, Field


class ProviderInfo(BaseModel):
    key: str
    label: str
    base_url: str
    default_model: str
    api_style: str = "openai_chat"
    config_help_text: str = ""


class ConfigResponse(BaseModel):
    provider: str
    model: str
    base_url: str
    api_key: str = ""
    masked_api_key: str = ""
    output_dir: str = ""
    save_to_source: bool = False
    course_name: str = ""
    provider_labels: dict[str, str] = Field(default_factory=dict)
    provider_models: dict[str, str] = Field(default_factory=dict)
    provider_urls: dict[str, str] = Field(default_factory=dict)
    provider_api_keys_present: dict[str, bool] = Field(default_factory=dict)
    provider_masked_keys: dict[str, str] = Field(default_factory=dict)


class ConfigSaveRequest(BaseModel):
    provider: str
    model: str
    base_url: str
    api_key: str = ""
    output_dir: str = ""
    save_to_source: bool = False
    course_name: str = ""


class ConfigTestResponse(BaseModel):
    ok: bool
    message: str


class ScanRequest(BaseModel):
    directory: str


class FilePathsRequest(BaseModel):
    paths: list[str]


class BrowseResponse(BaseModel):
    parent: str
    entries: list[dict]


class FileTreeResponse(BaseModel):
    transcripts: list[str]
    videos: list[str]
    notes: list[str]
    lessons: list[dict]
    stat: int
    extra_stat: str


class RunStartRequest(BaseModel):
    course_name: str = ""
    requirements_text: str = ""
    output_dir: str = ""
    save_to_source: bool = False


class RunStartResponse(BaseModel):
    run_id: str


class RunStatusResponse(BaseModel):
    running: bool
    progress: float = 0.0
    current_file: str = ""
    status_text: str = ""
    token_count: str = ""
