from __future__ import annotations

from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

TEMPLATE_DIR = Path(__file__).parent


def render_html(digest: dict, start: datetime, end: datetime) -> str:
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template("template.html.j2")
    return template.render(digest=digest, start=start.date(), end=end.date())


def render_plain(digest: dict, start: datetime, end: datetime) -> str:
    lines = [f"DHIS2 Weekly Digest — {start.date()} to {end.date()}", "", digest["intro"], ""]
    for section in digest["sections"]:
        lines.append(section["name"].upper())
        lines.append("-" * len(section["name"]))
        for item in section["items"]:
            prefix = "- [EyeSeeTea] " if item.get("highlight") else "- "
            lines.append(f"{prefix}{item['title']}")
            lines.append(f"  {item['url']}")
            lines.append(f"  {item['summary']}")
        lines.append("")
    return "\n".join(lines)
