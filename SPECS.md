# DHIS2 Newsletter Bot — SPECS

Script that, for a date range, pulls DHIS2 ecosystem activity, uses an LLM
to filter/rank/summarize it, and emails a digest.

## Sources

- **CoP** — community.dhis2.org (Discourse JSON API), forum posts/announcements.
- **JIRA** — dhis2.atlassian.net, bugs/releases via REST API + JQL.
- **DHIS2 Newsletter** — monthly email from `newsletter@dhis2.org`, read via IMAP on the user's Gmail (same creds as SMTP).
- **Release pages** — releases.dhis2.org + GitHub Releases, what shipped.
- **Developer Portal** — developers.dhis2.org blog/docs updates.
- **GitHub** — dhis2 org: new repos only for now (API).
- **YouTube** — official channel: meetups, Academy, webinars (Data API v3).
- **Social (X/Twitter)** — skipped for v1 (API paywalled, scraping unreliable/against ToS).

## Architecture

connectors (parallel, fail-soft) → normalize/dedupe → LLM stage
(filter → categorize → rank → summarize → intro) → render template → send email.

## Data model

`Item(source, title, url, published_at, author, body, extra)`

## Config

`config.yaml`: date range, per-source toggles/settings, recipients, LLM
model. Secrets via env vars (`OPENROUTER_API_KEY`, `GITHUB_TOKEN`,
`JIRA_API_TOKEN`, `YOUTUBE_API_KEY`, `SMTP_*`).

## Stack

Python, `httpx`, `feedparser`, `openai` SDK pointed at OpenRouter
(`base_url=https://openrouter.ai/api/v1`), `jinja2`, `pydantic`.

## Layout

```
src/dhis2_newsletter/
  main.py, models.py, config.py
  sources/   (cop, jira, newsletter, releases, dev_portal, github, youtube)
  llm/       (client, prompts, digest)
  compose/   (template, render)
  send/      (email)
```

## Credentials

Stored in `.env` (gitignored), template in `.env.example`.

- [x] `GITHUB_TOKEN` — classic PAT, no scopes (public read, 5000 req/hr).
- [x] `JIRA_API_TOKEN` / `JIRA_EMAIL`
- [x] `YOUTUBE_API_KEY` — verified working; official channel `UC7lT6wGX_IXkfguh2DvcrSA` (@dhis2org)
- [x] `OPENROUTER_API_KEY` — LLM provider, model `anthropic/claude-sonnet-5`
- [x] `SMTP_*` — Gmail SMTP (smtp.gmail.com:587), app password, from `pyarnau@gmail.com`.
  Same creds double as IMAP (imap.gmail.com:993) for reading the newsletter source.

Cadence: weekly.

## Status

v1 implemented, tested end-to-end, and sending real emails (`src/`, run via
`python -m dhis2_newsletter.main`). See README.md for user-facing usage.

- All 7 connectors verified live; JIRA returns ~220-230 raw items/week,
  LLM stage filters to a real digest.
- YouTube source pulls the transcript of new videos (`youtube-transcript-api`)
  and feeds it to the LLM for a detail-rich summary, not just title/description.
- JIRA issues reported by an EyeSeeTea teammate are always kept and
  flagged (⭐), matched by name (`sources.jira.eyeseetea_team` in
  config.yaml) since JIRA's API hides reporter emails for non-admin tokens.
  Enforced deterministically after the LLM call, not just via prompt
  instruction, so it can't silently get dropped.
- Cost: ~$0.16/run (~40k input / ~8k output tokens, `claude-sonnet-5`).
- Fixed: initial `max_tokens=8000` was too low and truncated the LLM's
  JSON output mid-digest; raised to 16000.
