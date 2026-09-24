from __future__ import annotations

from datetime import datetime

import httpx

from ..config import Secrets, SourceConfig
from ..models import Item


def fetch(start: datetime, end: datetime, config: SourceConfig, secrets: Secrets) -> list[Item]:
    org = config.model_extra.get("org", "dhis2")
    headers = {}
    if secrets.github_token:
        headers["Authorization"] = f"token {secrets.github_token}"

    items: list[Item] = []
    page = 1
    with httpx.Client(timeout=20, headers=headers) as client:
        while page <= 10:  # safety cap
            resp = client.get(
                f"https://api.github.com/orgs/{org}/repos",
                params={"sort": "created", "direction": "desc", "per_page": 50, "page": page},
            )
            resp.raise_for_status()
            repos = resp.json()
            if not repos:
                break

            stop = False
            for repo in repos:
                created_at = datetime.fromisoformat(repo["created_at"].replace("Z", "+00:00"))
                if created_at < start:
                    stop = True
                    continue
                if created_at > end:
                    continue
                items.append(
                    Item(
                        source="github",
                        title=f"New repo: {repo['full_name']}",
                        url=repo["html_url"],
                        published_at=created_at,
                        body=repo.get("description") or "",
                        extra={"language": repo.get("language")},
                    )
                )
            if stop:
                break
            page += 1
    return items
