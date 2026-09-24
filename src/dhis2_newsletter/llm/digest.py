from __future__ import annotations

import json
import logging
from collections import defaultdict

from openai import OpenAI

from ..config import LLMConfig
from ..models import Item
from .prompts import DIGEST_SYSTEM_PROMPT, SECTION_NAMES

log = logging.getLogger(__name__)

BODY_CHAR_LIMIT = 2000


def _group_payload(items: list[Item]) -> list[dict]:
    grouped: dict[str, list[Item]] = defaultdict(list)
    for item in items:
        grouped[item.source].append(item)

    return [
        {
            "source": source,
            "section_name": SECTION_NAMES.get(source, source),
            "items": [
                {
                    "title": it.title,
                    "url": it.url,
                    "author": it.author,
                    "published_at": it.published_at.isoformat(),
                    "body": it.body[:BODY_CHAR_LIMIT],
                    "reported_by_eyeseetea": it.extra.get("is_eyeseetea", False),
                }
                for it in its
            ],
        }
        for source, its in grouped.items()
    ]


def build_digest(items: list[Item], client: OpenAI, llm_config: LLMConfig) -> dict:
    if not items:
        return {"intro": "No notable DHIS2 activity this period.", "sections": []}

    payload = _group_payload(items)

    response = client.chat.completions.create(
        model=llm_config.model,
        max_tokens=llm_config.max_tokens,
        messages=[
            {"role": "system", "content": DIGEST_SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(payload, indent=2)},
        ],
        response_format={"type": "json_object"},
    )
    choice = response.choices[0]
    raw = choice.message.content
    usage = response.usage
    log.info(
        "LLM digest call: finish_reason=%s prompt_tokens=%s completion_tokens=%s",
        choice.finish_reason,
        getattr(usage, "prompt_tokens", None),
        getattr(usage, "completion_tokens", None),
    )
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        log.error(
            "LLM returned invalid/truncated JSON (finish_reason=%s, %d chars). "
            "Try raising llm.max_tokens in config.yaml.",
            choice.finish_reason,
            len(raw or ""),
        )
        raise
