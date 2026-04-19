#!/usr/bin/env bash
# Usage: ./deploy.sh <app-name> <profile>
#
# Reads the warehouse id from app.yaml, attaches it to the app as a SQL
# warehouse resource, syncs the code, and deploys. Idempotent.

set -eo pipefail

APP_NAME="${1:?Usage: ./deploy.sh <app-name> <profile>}"
PROFILE="${2:?Usage: ./deploy.sh <app-name> <profile>}"

cd "$(dirname "$0")"

WAREHOUSE_ID=$(grep -E '^[[:space:]]+id:' app.yaml | head -1 | sed -E 's/.*id:[[:space:]]*"?([^"[:space:]]+)"?.*/\1/')

if [[ -z "$WAREHOUSE_ID" || "$WAREHOUSE_ID" == "<YOUR_WAREHOUSE_ID>" ]]; then
  echo "ERROR: app.yaml has no valid warehouse id under resources.sql_warehouse.id."
  echo "Edit app.yaml and replace <YOUR_WAREHOUSE_ID> with a real warehouse id."
  exit 1
fi

if ! databricks apps get "$APP_NAME" --profile "$PROFILE" >/dev/null 2>&1; then
  echo ">> Creating app '$APP_NAME'..."
  databricks apps create "$APP_NAME" --profile "$PROFILE" >/dev/null
fi

echo ">> Binding SQL warehouse $WAREHOUSE_ID to the app..."
UPDATE_JSON=$(mktemp)
trap 'rm -f "$UPDATE_JSON"' EXIT
cat > "$UPDATE_JSON" <<JSON
{
  "name": "$APP_NAME",
  "resources": [
    {
      "name": "sql_warehouse",
      "description": "SQL warehouse used by the app",
      "sql_warehouse": {"id": "$WAREHOUSE_ID", "permission": "CAN_USE"}
    }
  ]
}
JSON
databricks apps update "$APP_NAME" --profile "$PROFILE" --json @"$UPDATE_JSON" >/dev/null

SP=$(databricks apps get "$APP_NAME" --profile "$PROFILE" \
     | python3 -c "import json,sys;print(json.load(sys.stdin)['service_principal_client_id'])")
echo "App service principal: $SP"
echo "(If the app cannot read your tables, grant this SP access via scripts/2_grant_sp_access.sql.)"

USER_EMAIL=$(databricks current-user me --profile "$PROFILE" \
             | python3 -c "import json,sys;print(json.load(sys.stdin)['userName'])")
SRC="/Workspace/Users/${USER_EMAIL}/${APP_NAME}"

echo ">> Syncing code to $SRC..."
databricks sync --watch=false \
  --exclude '.venv/**' --exclude '__pycache__/**' --exclude '*.pyc' \
  . "$SRC" --profile "$PROFILE"

echo ">> Deploying..."
databricks apps deploy "$APP_NAME" \
  --source-code-path "$SRC" --profile "$PROFILE" >/dev/null

URL=$(databricks apps get "$APP_NAME" --profile "$PROFILE" \
      | python3 -c "import json,sys;print(json.load(sys.stdin).get('url',''))")

echo
if [[ -n "$URL" ]]; then
  echo "Done. App URL: $URL"
else
  echo "Done. Run: databricks apps get $APP_NAME --profile $PROFILE"
fi
