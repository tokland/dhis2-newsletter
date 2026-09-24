from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Secrets(BaseSettings):
    model_config = SettingsConfigDict(env_file=PROJECT_ROOT / ".env", extra="ignore")

    github_token: str = ""
    jira_email: str = ""
    jira_api_token: str = ""
    youtube_api_key: str = ""
    openrouter_api_key: str = ""
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""


class LLMConfig(BaseModel):
    base_url: str
    model: str
    max_tokens: int = 8000


class SourceConfig(BaseModel):
    enabled: bool = True
    model_config = {"extra": "allow"}


class Config(BaseModel):
    recipients: list[str]
    llm: LLMConfig
    sources: dict[str, SourceConfig]


def load_config(path: Path | str = PROJECT_ROOT / "config.yaml") -> Config:
    with open(path) as f:
        raw = yaml.safe_load(f)
    return Config.model_validate(raw)


def load_secrets() -> Secrets:
    return Secrets()
