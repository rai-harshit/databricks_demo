#!/usr/bin/env bash
# Deploy this Streamlit app to Databricks Apps.
#
#   ./deploy.sh <app-name> [profile]
#
# First run: creates the app, prints the SQL you need to run to grant it
# access, then exits. Run the SQL, then re-run this script to deploy.
# Every run after that just syncs the code and redeploys.

set -euo pipefail

APP_NAME="${1:-}"
PROFILE="${2:-DEFAULT}"

if [[ -z "$APP_NAME" ]]; then
  echo "Usage: ./deploy.sh <app-name> [profile]"
  exit 1
fi

cd "$(dirname "$0")"

if grep -q '<YOUR_WAREHOUSE_ID>\|<YOUR_DASHBOARD_ID>' app.yaml; then
  echo "ERROR: edit app.yaml first — replace <YOUR_WAREHOUSE_ID> and <YOUR_DASHBOARD_ID>."
  exit 1
fi

if ! databricks apps get "$APP_NAME" --profile "$PROFILE" >/dev/null 2>&1; then
  echo ">> Creating app '$APP_NAME'…"
  databricks apps create "$APP_NAME" --profile "$PROFILE" >/dev/null

  SP=$(databricks apps get "$APP_NAME" --profile "$PROFILE" \
       | python3 -c "import json,sys;print(json.load(sys.stdin)['service_principal_client_id'])")

  echo
  echo "App created. Service principal id:"
  echo "  $SP"
  echo
  echo "Next: open scripts/2_grant_sp_access.sql in the SQL Editor,"
  echo "replace <SP> with the id above, run it, then re-run ./deploy.sh."
  exit 0
fi

USER_EMAIL=$(databricks current-user me --profile "$PROFILE" \
             | python3 -c "import json,sys;print(json.load(sys.stdin)['userName'])")
SRC="/Workspace/Users/${USER_EMAIL}/${APP_NAME}"

echo ">> Syncing code to $SRC…"
databricks sync --watch=false \
  --exclude '.venv/**' --exclude '__pycache__/**' --exclude '*.pyc' \
  --exclude '.env*' \
  . "$SRC" --profile "$PROFILE"

echo ">> Deploying…"
databricks apps deploy "$APP_NAME" \
  --source-code-path "$SRC" --profile "$PROFILE" >/dev/null

URL=$(databricks apps get "$APP_NAME" --profile "$PROFILE" \
      | python3 -c "import json,sys;print(json.load(sys.stdin).get('url',''))")

echo
echo "Done. App URL: ${URL:-run 'databricks apps get $APP_NAME' to see it}"
