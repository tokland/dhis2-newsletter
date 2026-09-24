from __future__ import annotations

from openai import OpenAI

from ..config import LLMConfig, Secrets


def make_client(llm_config: LLMConfig, secrets: Secrets) -> OpenAI:
    return OpenAI(base_url=llm_config.base_url, api_key=secrets.openrouter_api_key)
