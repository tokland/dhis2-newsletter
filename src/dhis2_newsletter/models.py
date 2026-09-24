from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class Item(BaseModel):
    source: str
    title: str
    url: str
    published_at: datetime
    author: str | None = None
    body: str = ""
    extra: dict = Field(default_factory=dict)
