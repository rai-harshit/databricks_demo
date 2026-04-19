#!/usr/bin/env bash
# Usage: ./deploy.sh <app-name> <profile>
#
# Assumes you've already edited app.yaml with a real warehouse id and
# dashboard id. Creates the app if it doesn't exist, syncs the code, and
# deploys. Safe to run any number of times.

set -eo pipefail

APP_NAME="${1:?Usage: ./deploy.sh <app-name> <profile>}"
PROFILE="${2:?Usage: ./deploy.sh <app-name> <profile>}"

cd "$(dirname "$0")"

if ! databricks apps get "$APP_NAME" --profile "$PROFILE" >/dev/null 2>&1; then
  echo ">> Creating app '$APP_NAME'…"
  databricks apps create "$APP_NAME" --profile "$PROFILE" >/dev/null
fi

SP=$(databricks apps get "$APP_NAME" --profile "$PROFILE" \
     | python3 -c "import json,sys;print(json.load(sys.stdin)['service_principal_client_id'])")
echo "App service principal: $SP"
echo "(If the app can't read your tables, grant this SP access via scripts/2_grant_sp_access.sql.)"

USER_EMAIL=$(databricks current-user me --profile "$PROFILE" \
             | python3 -c "import json,sys;print(json.load(sys.stdin)['userName'])")
SRC="/Workspace/Users/${USER_EMAIL}/${APP_NAME}"

echo ">> Syncing code to $SRC…"
databricks sync --watch=false \
  --exclude '.venv/**' --exclude '__pycache__/**' --exclude '*.pyc' \
  . "$SRC" --profile "$PROFILE"

echo ">> Deploying…"
databricks apps deploy "$APP_NAME" \
  --source-code-path "$SRC" --profile "$PROFILE" >/dev/null

URL=$(databricks apps get "$APP_NAME" --profile "$PROFILE" \
      | python3 -c "import json,sys;print(json.load(sys.stdin).get('url',''))")

echo
echo "Done. App URL: ${URL:-run 'databricks apps get $APP_NAME --profile $PROFILE' to see it}"
