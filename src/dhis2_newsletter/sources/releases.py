from __future__ import annotations

from datetime import datetime, timezone

import httpx

from ..config import Secrets, SourceConfig
from ..models import Item


def fetch(start: datetime, end: datetime, config: SourceConfig, secrets: Secrets) -> list[Item]:
    versions_url = config.model_extra.get(
        "versions_url", "https://releases.dhis2.org/v1/versions/stable.json"
    )

    items: list[Item] = []
    with httpx.Client(timeout=20) as client:
        resp = client.get(versions_url)
        resp.raise_for_status()
        data = resp.json()

    for version in data.get("versions", []):
        for patch in version.get("patchVersions", []):
            release_date = datetime.fromisoformat(patch["releaseDate"]).replace(
                tzinfo=timezone.utc
            )
            if not (start <= release_date <= end):
                continue
            kind = "hotfix" if patch.get("hotfix") else "patch"
            items.append(
                Item(
                    source="releases",
                    title=f"DHIS2 {patch['displayName']} released ({kind})",
                    url=patch["url"],
                    published_at=release_date,
                    body=f"DHIS2 core {patch['displayName']}, file size {patch.get('fileSize', 'n/a')}",
                    extra={"major": version["name"], "hotfix": patch.get("hotfix", False)},
                )
            )
    return items
