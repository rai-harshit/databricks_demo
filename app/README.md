# Geographic Market Intelligence — Streamlit App

A Databricks App that shows three tabs for the Eli Lilly demo:

1. **📊 Dashboard** — embeds the published AI/BI dashboard
   `Population Health Executive Dashboard - Eli Lilly`
   (`dashboard_id = 01f13ac6dda01c0da0fc8039401cd345`) via an iframe.
2. **🗺️ Build Territory** — form that writes user-defined geographic
   territories to `eli_lilly_demo.app_data.territory_definitions`.
3. **📋 View Territories** — shared, multi-user view of every saved territory
   with filters, CSV export, delete, and a patient-per-territory rollup.

## Repository layout

The app lives inside the `app/` sub-folder of the repo. Relative to the
repo root:

```
.
├── app/                              # <- you are here; Databricks App source
│   ├── app.py                        # Streamlit entry, 3 tabs
│   ├── app.yaml                      # Databricks Apps deployment config
│   ├── requirements.txt              # Python deps
│   ├── lib/
│   │   ├── db.py                     # databricks-sql-connector helpers (OBO + SP)
│   │   └── queries.py                # All SQL strings used by the app
│   └── scripts/
│       └── bootstrap_schema.sql      # CREATE SCHEMA + CREATE TABLE
├── data_pipeline/                    # Medallion notebook for the source tables
│   └── healthcare_claims_medallion_pipeline.ipynb
└── dashboard/                        # Exported AI/BI dashboard definition
    └── population_health_executive_dashboard.lvdash.json
```

All commands in this README assume you are running them from the **`app/`**
directory (the one containing `app.yaml`).

## One-time workspace setup

### 1. Authenticate

```bash
databricks auth login \
  --host https://dbc-c294909e-40e9.cloud.databricks.com \
  --profile dbrx_free
databricks current-user me --profile dbrx_free
```

### 2. Import the source tables

Import `../data_pipeline/healthcare_claims_medallion_pipeline.ipynb` into your
workspace and run it once. It populates:

- `eli_lilly_demo.silver_claims.*` (diagnosis, medical_claim, ...)
- `eli_lilly_demo.gold_claims.patient_summary` (1,485 rows)
- `eli_lilly_demo.gold_claims.claims_analytics`

### 3. Import the dashboard (optional — the app iframes the published version)

Upload `../dashboard/population_health_executive_dashboard.lvdash.json` to
the workspace via **AI/BI Dashboards → Import dashboard**, attach warehouse
`5a0ae21a29c598a3`, then click **Publish → Embed credentials**.

### 4. Bootstrap the app-owned Delta storage

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
# From the repo root
python -m venv .venv && source .venv/bin/activate
pip install -r app/requirements.txt

# From the app/ directory
cd app
DATABRICKS_CONFIG_PROFILE=dbrx_free \
DATABRICKS_WAREHOUSE_ID=5a0ae21a29c598a3 \
streamlit run app.py
```

The connection helper in `lib/db.py` will:

- Use the `dbrx_free` CLI profile when running locally (no OBO header).
- Use the `X-Forwarded-Access-Token` header when running on the Databricks
  Apps platform so `current_user()` reflects the actual viewer.

## Deploy to Databricks Apps

```bash
# One-time: create the app (only if it doesn't exist yet)
databricks apps create geo-market-intel --profile dbrx_free

# Grant the app service principal access (one-time)
SP=$(databricks apps get geo-market-intel --profile dbrx_free \
       | python -c "import json,sys; print(json.load(sys.stdin)['service_principal_client_id'])")
for STMT in \
  "GRANT USE CATALOG ON CATALOG eli_lilly_demo TO \`$SP\`" \
  "GRANT USE SCHEMA, SELECT ON SCHEMA eli_lilly_demo.gold_claims TO \`$SP\`" \
  "GRANT USE SCHEMA, SELECT ON SCHEMA eli_lilly_demo.silver_claims TO \`$SP\`" \
  "GRANT USE SCHEMA, SELECT, MODIFY ON SCHEMA eli_lilly_demo.app_data TO \`$SP\`"; do
  databricks sql-statements execute --warehouse-id 5a0ae21a29c598a3 \
    --statement "$STMT" --profile dbrx_free
done

# Sync just the app/ directory to the workspace, then deploy
USER_EMAIL=$(databricks current-user me --profile dbrx_free \
              | python -c "import json,sys; print(json.load(sys.stdin)['userName'])")
SRC="/Workspace/Users/${USER_EMAIL}/geo-market-intel"

# Run from the repo root so only app/ contents get uploaded:
databricks sync --watch=false \
  --exclude '.venv/**' --exclude '__pycache__/**' --exclude '*.pyc' \
  app "$SRC" --profile dbrx_free

databricks apps deploy geo-market-intel \
  --source-code-path "$SRC" --profile dbrx_free
```

After deploy completes, `databricks apps get geo-market-intel` returns the
public URL. The current deployment is at
<https://geo-market-intel-7474656071514307.aws.databricksapps.com>.

## Reference

- Catalog: `eli_lilly_demo`
- Source tables: `gold_claims.patient_summary` (1,485 rows),
  `gold_claims.claims_analytics`, `silver_claims.diagnosis`
- App-owned table: `app_data.territory_definitions`
- SQL Warehouse: `5a0ae21a29c598a3` (Serverless Starter, 2X-Small PRO)
- Dashboard: `01f13ac6dda01c0da0fc8039401cd345`
  (`Population Health Executive Dashboard - Eli Lilly`, published with
  `embed_credentials: true` so the iframe renders without a per-viewer login)
