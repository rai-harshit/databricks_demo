#!/usr/bin/env bash
# Deploy this Streamlit app to Databricks Apps.
#
#   ./deploy.sh <app-name> [profile]
#
# On first run it asks for your warehouse id + dashboard id, writes them
# into app.yaml, creates the app, and prints the SQL you need to run to
# grant it access. After you run that SQL, re-run ./deploy.sh to deploy.
# Subsequent runs just sync + redeploy.
#
# Profile resolution (first match wins):
#   1. $2 argument
#   2. $DATABRICKS_CONFIG_PROFILE env var
#   3. CLI default (the [DEFAULT] section of ~/.databrickscfg)

set -euo pipefail

APP_NAME="${1:-}"
PROFILE="${2:-${DATABRICKS_CONFIG_PROFILE:-}}"

if [[ -z "$APP_NAME" ]]; then
  echo "Usage: ./deploy.sh <app-name> [profile]"
  exit 1
fi

cd "$(dirname "$0")"

# --profile flag — empty means "let the CLI pick from env or DEFAULT".
PFLAG=()
if [[ -n "$PROFILE" ]]; then PFLAG=(--profile "$PROFILE"); fi

# ---------- fill in placeholders in app.yaml on first run ----------

if grep -q '<YOUR_WAREHOUSE_ID>' app.yaml; then
  echo "SQL Warehouses in this workspace:"
  databricks warehouses list "${PFLAG[@]}" -o json \
    | python3 -c "import json,sys;[print(f\"  {w['id']}  {w['name']}\") for w in json.load(sys.stdin)]"
  echo
  read -rp "Paste the warehouse id to use: " WH_ID
  [[ -z "$WH_ID" ]] && { echo "no warehouse id given, aborting"; exit 1; }
  sed -i.bak "s|<YOUR_WAREHOUSE_ID>|$WH_ID|" app.yaml && rm -f app.yaml.bak
fi

if grep -q '<YOUR_DASHBOARD_ID>' app.yaml; then
  echo
  echo "Find the dashboard id in the URL of the published dashboard:"
  echo "  https://.../dashboardsv3/<THIS_PART>/published"
  read -rp "Paste the dashboard id: " DASH_ID
  [[ -z "$DASH_ID" ]] && { echo "no dashboard id given, aborting"; exit 1; }
  sed -i.bak "s|<YOUR_DASHBOARD_ID>|$DASH_ID|" app.yaml && rm -f app.yaml.bak
fi

# ---------- create app if needed, then hand off grants to the user ----------

if ! databricks apps get "$APP_NAME" "${PFLAG[@]}" >/dev/null 2>&1; then
  echo ">> Creating app '$APP_NAME'…"
  databricks apps create "$APP_NAME" "${PFLAG[@]}" >/dev/null

  SP=$(databricks apps get "$APP_NAME" "${PFLAG[@]}" \
       | python3 -c "import json,sys;print(json.load(sys.stdin)['service_principal_client_id'])")

  echo
  echo "App created. Service principal id:"
  echo "  $SP"
  echo
  echo "Next step:"
  echo "  1. Open scripts/2_grant_sp_access.sql in the SQL Editor."
  echo "  2. Find+Replace <SP> → $SP"
  echo "  3. Run it."
  echo "  4. Re-run ./deploy.sh $APP_NAME${PROFILE:+ $PROFILE}"
  exit 0
fi

# ---------- sync + deploy ----------

USER_EMAIL=$(databricks current-user me "${PFLAG[@]}" \
             | python3 -c "import json,sys;print(json.load(sys.stdin)['userName'])")
SRC="/Workspace/Users/${USER_EMAIL}/${APP_NAME}"

echo ">> Syncing code to $SRC…"
databricks sync --watch=false \
  --exclude '.venv/**' --exclude '__pycache__/**' --exclude '*.pyc' \
  --exclude '.env*' \
  . "$SRC" "${PFLAG[@]}"

echo ">> Deploying…"
databricks apps deploy "$APP_NAME" \
  --source-code-path "$SRC" "${PFLAG[@]}" >/dev/null

URL=$(databricks apps get "$APP_NAME" "${PFLAG[@]}" \
      | python3 -c "import json,sys;print(json.load(sys.stdin).get('url',''))")

echo
echo "Done. App URL: ${URL:-run 'databricks apps get $APP_NAME' to see it}"
