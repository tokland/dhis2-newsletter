from __future__ import annotations

import unicodedata
from datetime import datetime

import httpx

from ..config import Secrets, SourceConfig
from ..models import Item


def _name_tokens(name: str) -> set[str]:
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return set(ascii_name.lower().split())


def _is_team_member(reporter_name: str, roster: list[str]) -> bool:
    reporter_tokens = _name_tokens(reporter_name)
    return any(len(reporter_tokens & _name_tokens(full_name)) >= 2 for full_name in roster)


def fetch(start: datetime, end: datetime, config: SourceConfig, secrets: Secrets) -> list[Item]:
    base_url = config.model_extra.get("base_url", "https://dhis2.atlassian.net")
    project = config.model_extra.get("project", "DHIS2")
    eyeseetea_team = config.model_extra.get("eyeseetea_team", [])

    jql = (
        f'project = {project} AND updated >= "{start:%Y-%m-%d %H:%M}" '
        f'AND updated <= "{end:%Y-%m-%d %H:%M}" ORDER BY updated DESC'
    )

    items: list[Item] = []
    auth = httpx.BasicAuth(secrets.jira_email, secrets.jira_api_token)
    with httpx.Client(timeout=20, auth=auth) as client:
        next_token = None
        while True:
            params = {
                "jql": jql,
                "maxResults": 100,
                "fields": "summary,status,updated,fixVersions,priority,issuetype,reporter",
            }
            if next_token:
                params["nextPageToken"] = next_token
            resp = client.get(f"{base_url}/rest/api/3/search/jql", params=params)
            resp.raise_for_status()
            data = resp.json()

            for issue in data.get("issues", []):
                fields = issue["fields"]
                reporter_name = (fields.get("reporter") or {}).get("displayName", "")
                is_eyeseetea = bool(eyeseetea_team) and _is_team_member(
                    reporter_name, eyeseetea_team
                )
                items.append(
                    Item(
                        source="jira",
                        title=f"{issue['key']}: {fields['summary']}",
                        url=f"{base_url}/browse/{issue['key']}",
                        published_at=datetime.fromisoformat(fields["updated"]),
                        author=reporter_name,
                        body=fields["status"]["name"],
                        extra={
                            "status": fields["status"]["name"],
                            "priority": (fields.get("priority") or {}).get("name"),
                            "issue_type": (fields.get("issuetype") or {}).get("name"),
                            "fix_versions": [v["name"] for v in fields.get("fixVersions", [])],
                            "reporter": reporter_name,
                            "is_eyeseetea": is_eyeseetea,
                        },
                    )
                )

            next_token = data.get("nextPageToken")
            if not next_token:
                break
    return items
