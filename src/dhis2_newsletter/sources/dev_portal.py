from __future__ import annotations

from datetime import datetime, timezone
from time import mktime

import feedparser

from ..config import Secrets, SourceConfig
from ..models import Item


def fetch(start: datetime, end: datetime, config: SourceConfig, secrets: Secrets) -> list[Item]:
    feed_url = config.model_extra.get(
        "feed_url", "https://developers.dhis2.org/blog/rss.xml"
    )

    feed = feedparser.parse(feed_url)
    items: list[Item] = []
    for entry in feed.entries:
        if not getattr(entry, "published_parsed", None):
            continue
        published = datetime.fromtimestamp(mktime(entry.published_parsed), tz=timezone.utc)
        if not (start <= published <= end):
            continue
        items.append(
            Item(
                source="dev_portal",
                title=entry.title,
                url=entry.link,
                published_at=published,
                body=getattr(entry, "summary", ""),
            )
        )
    return items
