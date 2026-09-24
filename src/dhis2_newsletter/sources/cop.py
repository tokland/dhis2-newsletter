from __future__ import annotations

from datetime import datetime, timezone

import httpx

from ..config import Secrets, SourceConfig
from ..models import Item


def fetch(start: datetime, end: datetime, config: SourceConfig, secrets: Secrets) -> list[Item]:
    base_url = config.model_extra.get("base_url", "https://community.dhis2.org")
    items: list[Item] = []
    page = 0
    with httpx.Client(timeout=20) as client:
        while page < 10:  # safety cap
            resp = client.get(f"{base_url}/latest.json", params={"page": page})
            resp.raise_for_status()
            topics = resp.json()["topic_list"]["topics"]
            if not topics:
                break

            stop = False
            for t in topics:
                created_at = datetime.fromisoformat(t["created_at"].replace("Z", "+00:00"))
                if created_at < start:
                    stop = True
                    continue
                if created_at > end:
                    continue
                items.append(
                    Item(
                        source="cop",
                        title=t["title"],
                        url=f"{base_url}/t/{t['slug']}/{t['id']}",
                        published_at=created_at,
                        author=t.get("last_poster_username"),
                        body=t.get("excerpt", ""),
                        extra={
                            "reply_count": t.get("reply_count"),
                            "like_count": t.get("like_count"),
                            "views": t.get("views"),
                        },
                    )
                )
            if stop:
                break
            page += 1
    return items
