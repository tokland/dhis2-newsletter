from __future__ import annotations

from datetime import datetime

import httpx
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

from ..config import Secrets, SourceConfig
from ..models import Item

TRANSCRIPT_CHAR_LIMIT = 8000


def _uploads_playlist_id(client: httpx.Client, channel_id: str, api_key: str) -> str:
    resp = client.get(
        "https://www.googleapis.com/youtube/v3/channels",
        params={"part": "contentDetails", "id": channel_id, "key": api_key},
    )
    resp.raise_for_status()
    return resp.json()["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]


def _fetch_transcript(video_id: str) -> str:
    try:
        api = YouTubeTranscriptApi()
        transcript = api.fetch(video_id)
        text = " ".join(snippet.text for snippet in transcript)
        return text[:TRANSCRIPT_CHAR_LIMIT]
    except (TranscriptsDisabled, NoTranscriptFound, Exception):
        return ""


def fetch(start: datetime, end: datetime, config: SourceConfig, secrets: Secrets) -> list[Item]:
    channel_id = config.model_extra["channel_id"]
    api_key = secrets.youtube_api_key

    items: list[Item] = []
    with httpx.Client(timeout=20) as client:
        playlist_id = _uploads_playlist_id(client, channel_id, api_key)

        page_token = None
        videos = []
        while True:
            params = {
                "part": "snippet",
                "playlistId": playlist_id,
                "maxResults": 50,
                "key": api_key,
            }
            if page_token:
                params["pageToken"] = page_token
            resp = client.get(
                "https://www.googleapis.com/youtube/v3/playlistItems", params=params
            )
            resp.raise_for_status()
            data = resp.json()

            stop = False
            for entry in data.get("items", []):
                snippet = entry["snippet"]
                published_at = datetime.fromisoformat(snippet["publishedAt"].replace("Z", "+00:00"))
                if published_at < start:
                    stop = True
                    continue
                if published_at > end:
                    continue
                videos.append((snippet, published_at))

            page_token = data.get("nextPageToken")
            if stop or not page_token:
                break

    for snippet, published_at in videos:
        video_id = snippet["resourceId"]["videoId"]
        transcript = _fetch_transcript(video_id)
        body = snippet.get("description", "")
        if transcript:
            body += f"\n\nTranscript excerpt:\n{transcript}"
        items.append(
            Item(
                source="youtube",
                title=snippet["title"],
                url=f"https://www.youtube.com/watch?v={video_id}",
                published_at=published_at,
                body=body,
                extra={"has_transcript": bool(transcript)},
            )
        )
    return items
