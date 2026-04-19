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

# ---------------------------------------------------------------------------
# Bootstrap Unity Catalog objects the app depends on:
#   1. Create the app's schema + `territory_definitions` table (Tabs 2/3).
#   2. Grant the app's service principal access to the source + app schemas
#      so SQL queries issued by the app (running as the SP) succeed.
# Both steps are idempotent (CREATE ... IF NOT EXISTS / GRANT).
# ---------------------------------------------------------------------------
SP=$(databricks apps get "$APP" --profile "$PROFILE" | jq -r '.service_principal_client_id')
if [[ -z "$SP" || "$SP" == "null" ]]; then
  echo "Could not resolve app service principal id from 'databricks apps get'." >&2
  exit 1
fi

# Read env var value from app.yaml (name: <k> / value: "<v>" pair). Falls
# back to $2 if the var isn't declared. Keeps app.yaml as the single source
# of truth for catalog/schema names.
yaml_env() {
  awk -v k="$1" -v d="$2" '
    /^[[:space:]]*-[[:space:]]*name:[[:space:]]*/ {
      n=$0; sub(/^[^:]*:[[:space:]]*/, "", n); gsub(/[[:space:]]/, "", n); next
    }
    /^[[:space:]]*value:[[:space:]]*/ && n==k {
      v=$0; sub(/^[^:]*:[[:space:]]*/, "", v); gsub(/^"|"$/, "", v); print v; found=1; exit
    }
    END { if (!found) print d }
  ' app.yaml
}

CAT=$(yaml_env APP_CATALOG        eli_lilly_demo)
SILVER=$(yaml_env APP_SILVER_SCHEMA silver_claims)
GOLD=$(yaml_env APP_GOLD_SCHEMA     gold_claims)
APP_SCH=$(yaml_env APP_SCHEMA       app_data)

run_sql() {
  local stmt="$1"
  local payload
  payload=$(jq -Rn --arg s "$stmt" --arg w "$WID" \
    '{warehouse_id:$w, statement:$s, wait_timeout:"30s", on_wait_timeout:"CANCEL"}')
  local resp
  resp=$(databricks api post /api/2.0/sql/statements --profile "$PROFILE" --json "$payload")
  local state
  state=$(echo "$resp" | jq -r '.status.state // "UNKNOWN"')
  if [[ "$state" != "SUCCEEDED" ]]; then
    echo "SQL failed ($state): $stmt" >&2
    echo "$resp" | jq '.status.error // .' >&2
    exit 1
  fi
}

# Render {{PLACEHOLDERS}} from app.yaml/SP, strip SQL comments + blank lines,
# split on ';' and run each statement via run_sql. Assumes no ';' inside
# string literals (fine for this app's DDL + GRANTs).
run_sql_file() {
  local file="$1"
  local rendered
  rendered=$(sed \
    -e "s|{{CATALOG}}|$CAT|g" \
    -e "s|{{SILVER_SCHEMA}}|$SILVER|g" \
    -e "s|{{GOLD_SCHEMA}}|$GOLD|g" \
    -e "s|{{APP_SCHEMA}}|$APP_SCH|g" \
    -e "s|{{SP}}|$SP|g" \
    -e '/^[[:space:]]*--/d' \
    -e '/^[[:space:]]*$/d' \
    "$file")
  while IFS= read -r stmt; do
    stmt=$(echo "$stmt" | awk '{$1=$1;print}')
    [[ -z "$stmt" ]] && continue
    run_sql "$stmt"
  done < <(echo "$rendered" | tr '\n' ' ' | tr ';' '\n')
}

echo "Applying scripts/1_create_table.sql…"
run_sql_file scripts/1_create_table.sql

echo "Applying scripts/2_grant_sp_access.sql for SP $SP…"
run_sql_file scripts/2_grant_sp_access.sql

echo "Bootstrap complete."
