# DHIS2 Newsletter

Weekly digest of DHIS2 activity (CoP, JIRA, GitHub, YouTube, releases, dev
portal, official newsletter), filtered and summarized by an LLM, sent by email.

## Setup

```
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Credentials go in `.env` (see `.env.example`). Copy `config.example.yaml` to `config.yaml` and edit it.

## Run

```
source .venv/bin/activate
python -m dhis2_newsletter.main --days 7
```

Sends the digest email to the recipients in `config.yaml`.

Useful flags:
- `--days N` — look back N days (default 7)
- `--start YYYY-MM-DD` / `--end YYYY-MM-DD` — explicit date range instead of `--days`
- `--dry-run` — print the digest instead of emailing it
- `--skip-llm` — print raw fetched items only (no LLM call, no email) — quick way to check the sources are pulling data

## Config

Edit `config.yaml` to change recipients, enable/disable a source, or the LLM model.

JIRA issues reported by an EyeSeeTea teammate (matched by name against
`sources.jira.eyeseetea_team` in `config.yaml`) are always kept and marked
with a ⭐ EyeSeeTea badge in the email, even if the LLM would otherwise have
filtered them out as minor.

## Schedule

Runs automatically every Sunday at 22:00 (`crontab -l` to check, `crontab -e`
to change) via `scripts/run_weekly.sh`. Logs to `logs/weekly.log`.

## Cost

One weekly run ≈ $0.16 in LLM usage (`anthropic/claude-sonnet-5` via
OpenRouter, ~40k input / ~8k output tokens) — about $0.65/month.
