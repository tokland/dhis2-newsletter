from __future__ import annotations

import argparse
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone

from .compose.render import render_html, render_plain
from .config import load_config, load_secrets
from .llm.client import make_client
from .llm.digest import build_digest
from .llm.prompts import SECTION_NAMES
from .models import Item
from .send.email import send_email
from .sources import REGISTRY

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger("dhis2_newsletter")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="DHIS2 weekly digest")
    parser.add_argument("--days", type=int, default=7, help="Look back this many days (default 7)")
    parser.add_argument("--start", type=str, help="Start date YYYY-MM-DD (overrides --days)")
    parser.add_argument("--end", type=str, help="End date YYYY-MM-DD (default: now)")
    parser.add_argument("--dry-run", action="store_true", help="Print digest instead of emailing")
    parser.add_argument(
        "--skip-llm", action="store_true", help="Skip the LLM stage and just list raw items"
    )
    return parser.parse_args()


def dedupe(items: list[Item]) -> list[Item]:
    seen: set[str] = set()
    deduped = []
    for item in items:
        key = item.title.strip().lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def enforce_eyeseetea_highlights(digest: dict, items: list[Item]) -> dict:
    """Guarantee EyeSeeTea-reported JIRA issues survive and are flagged,
    regardless of what the LLM did with them."""
    eyeseetea_items = {it.url: it for it in items if it.extra.get("is_eyeseetea") and it.url}
    if not eyeseetea_items:
        return digest

    seen_urls = set()
    for section in digest.get("sections", []):
        for entry in section.get("items", []):
            seen_urls.add(entry.get("url"))
            if entry.get("url") in eyeseetea_items:
                entry["highlight"] = True

    missing = [it for url, it in eyeseetea_items.items() if url not in seen_urls]
    if missing:
        section_name = SECTION_NAMES["jira"]
        target = next((s for s in digest["sections"] if s["name"] == section_name), None)
        if target is None:
            target = {"name": section_name, "items": []}
            digest["sections"].append(target)
        for it in missing:
            target["items"].insert(
                0,
                {
                    "title": it.title,
                    "url": it.url,
                    "summary": (
                        f"Reported by EyeSeeTea team member {it.extra.get('reporter', '')}. "
                        f"Status: {it.extra.get('status', '')}."
                    ),
                    "highlight": True,
                },
            )
    return digest


def fetch_all(start: datetime, end: datetime, config, secrets) -> list[Item]:
    items: list[Item] = []
    with ThreadPoolExecutor(max_workers=len(REGISTRY)) as pool:
        futures = {}
        for name, fetch_fn in REGISTRY.items():
            source_config = config.sources.get(name)
            if source_config is None or not source_config.enabled:
                continue
            futures[pool.submit(fetch_fn, start, end, source_config, secrets)] = name

        for future in as_completed(futures):
            name = futures[future]
            try:
                source_items = future.result()
                log.info("%s: %d items", name, len(source_items))
                items.extend(source_items)
            except Exception:
                log.exception("Source %s failed, skipping", name)
    return items


def main() -> None:
    args = parse_args()

    end = datetime.fromisoformat(args.end).replace(tzinfo=timezone.utc) if args.end else datetime.now(timezone.utc)
    start = (
        datetime.fromisoformat(args.start).replace(tzinfo=timezone.utc)
        if args.start
        else end - timedelta(days=args.days)
    )

    config = load_config()
    secrets = load_secrets()

    log.info("Fetching items from %s to %s", start, end)
    items = dedupe(fetch_all(start, end, config, secrets))
    log.info("Total items fetched (deduped): %d", len(items))

    if args.skip_llm:
        for item in items:
            print(f"[{item.source}] {item.title} — {item.url}")
        return

    client = make_client(config.llm, secrets)
    digest = build_digest(items, client, config.llm)
    digest = enforce_eyeseetea_highlights(digest, items)

    html_body = render_html(digest, start, end)
    plain_body = render_plain(digest, start, end)
    subject = f"DHIS2 Weekly Digest — {start.date()} to {end.date()}"

    if args.dry_run:
        print(plain_body)
        return

    send_email(subject, html_body, plain_body, config.recipients, secrets)
    log.info("Digest sent to %s", config.recipients)


if __name__ == "__main__":
    main()
