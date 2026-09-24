#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p logs
./.venv/bin/python -m dhis2_newsletter.main --days 7 >> logs/weekly.log 2>&1
