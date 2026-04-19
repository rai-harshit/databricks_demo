#!/usr/bin/env bash
# Usage: ./deploy.sh <app-name> <profile>
set -eo pipefail

APP="${1:?Usage: ./deploy.sh <app-name> <profile>}"
PROFILE="${2:?Usage: ./deploy.sh <app-name> <profile>}"
cd "$(dirname "$0")"

WID=$(grep -E '^\s+id:' app.yaml | head -1 | sed -E 's/.*"(.*)".*/\1/')
[[ -z "$WID" || "$WID" == "<YOUR_WAREHOUSE_ID>" ]] && { echo "Edit app.yaml: replace <YOUR_WAREHOUSE_ID>."; exit 1; }

databricks apps get "$APP" --profile "$PROFILE" >/dev/null 2>&1 \
  || databricks apps create "$APP" --profile "$PROFILE" >/dev/null

databricks apps update "$APP" --profile "$PROFILE" --json \
  "{\"name\":\"$APP\",\"resources\":[{\"name\":\"sql_warehouse\",\"sql_warehouse\":{\"id\":\"$WID\",\"permission\":\"CAN_USE\"}}]}" >/dev/null

EMAIL=$(databricks current-user me --profile "$PROFILE" | grep -o '"userName":"[^"]*"' | cut -d'"' -f4)
SRC="/Workspace/Users/$EMAIL/$APP"

databricks sync --watch=false --exclude '.venv/**' --exclude '__pycache__/**' . "$SRC" --profile "$PROFILE"
databricks apps deploy "$APP" --source-code-path "$SRC" --profile "$PROFILE"
