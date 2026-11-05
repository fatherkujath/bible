#!/usr/bin/env bash
# Builds the whole site from scratch. Cloudflare Pages runs this on every push.
#   1. Fetch the pinned sources, build and validate the reference database,
#      and export the per-chapter data files (data-pipeline/).
#   2. Build the static web app into app/out/.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== Data pipeline"
(cd data-pipeline && python3 -m sic_pipeline all)

echo "== Web app"
(cd app && npm ci --no-audit --no-fund && npm run build)

echo "== Done: app/out is ready to publish"
