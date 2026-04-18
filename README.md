# Geographic Market Intelligence — Eli Lilly Demo

A Streamlit Databricks App that demonstrates an end-to-end workflow:

1. **📊 Dashboard** — KPIs, top-state chart, and a sample patient table from
   `eli_lilly_demo.gold_claims.patient_summary` and
   `eli_lilly_demo.silver_claims.diagnosis`.
2. **🗺️ Build Territory** — form that writes user-defined territories to
   `eli_lilly_demo.app_data.territory_definitions`.
3. **📋 View Territories** — shared, multi-user view of every saved territory
   with filters, CSV export, delete, and a patient-per-territory rollup.

## Project layout

```
geo_market_intel/
  app.py                       # Streamlit entry, 3 tabs
  app.yaml                     # Databricks Apps deployment config
  requirements.txt             # Python deps
  lib/
    db.py                      # databricks-sql-connector helpers (OBO + SP)
    queries.py                 # All SQL strings used by the app
  scripts/
    bootstrap_schema.sql       # CREATE SCHEMA + CREATE TABLE territory_definitions
```

## One-time setup

### 1. Authenticate

```bash
databricks auth login \
  --host https://dbc-c294909e-40e9.cloud.databricks.com \
  --profile dbrx_free
databricks current-user me --profile dbrx_free
```

### 2. Bootstrap the Delta storage schema

Run `scripts/bootstrap_schema.sql` against the workspace once. Either via
the Databricks SQL editor or:

```bash
python -c "
import os, time
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState
os.environ['DATABRICKS_CONFIG_PROFILE']='dbrx_free'
w = WorkspaceClient()
sql = open('scripts/bootstrap_schema.sql').read()
for stmt in [s.strip() for s in sql.split(';') if s.strip()]:
    r = w.statement_execution.execute_statement(
        statement=stmt, warehouse_id='5a0ae21a29c598a3', wait_timeout='30s')
    while r.status.state in (StatementState.PENDING, StatementState.RUNNING):
        time.sleep(1); r = w.statement_execution.get_statement(r.statement_id)
    print(stmt[:60], '->', r.status.state)
"
```

## Run locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
DATABRICKS_CONFIG_PROFILE=dbrx_free \
DATABRICKS_WAREHOUSE_ID=5a0ae21a29c598a3 \
streamlit run app.py
```

The connection helper in `lib/db.py` will:

- Use the `dbrx_free` CLI profile when running locally (no OBO header).
- Use the `X-Forwarded-Access-Token` header when running on the Databricks
  Apps platform so `current_user()` reflects the actual viewer.

## Deploy

```bash
# Create the app once
databricks apps create geo-market-intel --profile dbrx_free

# Sync source to a workspace folder, then deploy
USER_EMAIL=$(databricks current-user me --profile dbrx_free | jq -r '.userName')
SRC=/Workspace/Users/${USER_EMAIL}/geo-market-intel
databricks sync --watch=false . "$SRC" --profile dbrx_free
databricks apps deploy geo-market-intel \
  --source-code-path "$SRC" --profile dbrx_free
```

After deploy completes, `databricks apps get geo-market-intel` returns the
public URL.

The app's service principal needs the following grants (the deploy command
prompts for them; if you skip, run them via SQL):

```sql
GRANT USE CATALOG ON CATALOG eli_lilly_demo TO `<app-sp>`;
GRANT USE SCHEMA, SELECT ON SCHEMA eli_lilly_demo.gold_claims TO `<app-sp>`;
GRANT USE SCHEMA, SELECT ON SCHEMA eli_lilly_demo.silver_claims TO `<app-sp>`;
GRANT USE SCHEMA, SELECT, MODIFY ON SCHEMA eli_lilly_demo.app_data TO `<app-sp>`;
```

## Reference

- Catalog: `eli_lilly_demo`
- Source tables: `gold_claims.patient_summary` (1,485 rows),
  `silver_claims.diagnosis`
- App-owned table: `app_data.territory_definitions`
- SQL Warehouse: `5a0ae21a29c598a3` (Serverless Starter, 2X-Small PRO)
