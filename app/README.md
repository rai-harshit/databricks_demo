# Geographic Market Intelligence — Streamlit App

A Databricks App that shows three tabs:

1. **Dashboard** — embeds a published AI/BI dashboard via iframe.
2. **Build Territory** — form that writes user-defined geographic territories
   to a Delta table.
3. **View Territories** — shared, multi-user view of every saved territory
   with filters, CSV export, delete, and a patient-per-territory rollup.

The repo ships with the Eli Lilly demo defaults, but **every workspace-specific
value is configurable via environment variables** — you do not need to edit
any Python to run it against your own catalog, warehouse, or dashboard.

## Repository layout

```
.
├── app/                              # <- you are here; Databricks App source
│   ├── app.py                        # Streamlit entry, 3 tabs
│   ├── app.yaml                      # Databricks Apps deployment config
│   ├── requirements.txt              # Python deps
│   ├── .env.example                  # Template for local env vars
│   ├── lib/
│   │   ├── config.py                 # All env-driven config (catalog, dashboard, …)
│   │   ├── db.py                     # SQL connector helpers (OBO + SP)
│   │   └── queries.py                # All SQL strings used by the app
│   └── scripts/
│       ├── bootstrap_schema.sql      # CREATE SCHEMA + CREATE TABLE
│       └── grant_sp_access.sql       # Grants for the app service principal
├── data_pipeline/                    # Medallion notebook for the source tables
│   └── healthcare_claims_medallion_pipeline.ipynb
└── dashboard/                        # Exported AI/BI dashboard definition
    └── population_health_executive_dashboard.lvdash.json
```

All commands below assume you are running them from the **`app/`** directory
(the one containing `app.yaml`).

## Configuration reference

| Setting | Env var | Default | Where it's used |
| --- | --- | --- | --- |
| Workspace host | (CLI profile) | — | `databricks auth login --host …` |
| CLI profile name | `DATABRICKS_CONFIG_PROFILE` | — | Local auth |
| SQL Warehouse ID | `DATABRICKS_WAREHOUSE_ID` | — | Every query the app runs |
| Unity Catalog | `APP_CATALOG` | `eli_lilly_demo` | `lib/config.py` |
| Silver schema | `APP_SILVER_SCHEMA` | `silver_claims` | Source `diagnosis` table |
| Gold schema | `APP_GOLD_SCHEMA` | `gold_claims` | Source `patient_summary` table |
| App schema | `APP_SCHEMA` | `app_data` | Territory Delta table |
| Dashboard ID | `APP_DASHBOARD_ID` | (demo dashboard) | Tab 1 iframe |
| Dashboard name | `APP_DASHBOARD_NAME` | `Population Health Executive Dashboard` | Tab 1 title |

> **Pick your values now and keep them handy** — you'll plug them into the CLI
> commands, `app.yaml`, and the SQL scripts below.

## One-time workspace setup

### 1. Authenticate the CLI

```bash
databricks auth login \
  --host https://<YOUR_WORKSPACE_HOST> \
  --profile <YOUR_PROFILE_NAME>

databricks current-user me --profile <YOUR_PROFILE_NAME>
```

### 2. Load the source tables

Import `../data_pipeline/healthcare_claims_medallion_pipeline.ipynb` into your
workspace and run it once. Out of the box it writes to:

- `eli_lilly_demo.silver_claims.*` (`diagnosis`, `medical_claim`, …)
- `eli_lilly_demo.gold_claims.patient_summary`
- `eli_lilly_demo.gold_claims.claims_analytics`

If you want different names, edit the notebook constants **and** set the
matching `APP_*` env vars in step 5.

### 3. Import the dashboard (optional)

Only needed if you want the Tab 1 iframe to show the sample dashboard:

1. Workspace → **AI/BI Dashboards → Import dashboard**.
2. Upload `../dashboard/population_health_executive_dashboard.lvdash.json`.
3. Attach your SQL warehouse.
4. Click **Publish**, tick **Embed credentials** (required for the iframe to
   render without a per-viewer login).
5. Copy the dashboard ID from the URL — that's the value you'll use for
   `APP_DASHBOARD_ID`.

Already have your own published dashboard? Just use its ID.

### 4. Create the app's Delta storage

Open `scripts/bootstrap_schema.sql` in the **Databricks SQL Editor** (or any
notebook attached to your warehouse) and click **Run**. The script is
idempotent, so it's safe to re-run any time.

If your catalog / schema names differ from the defaults, edit the two
identifiers at the top of the file before running.

### 5. (Optional) Point the app at different objects

Only needed if your catalog, schemas, or dashboard don't match the defaults
in the table above. Either export the env vars locally, or uncomment them in
`app.yaml` before deploying.

## Run locally

```bash
# From the repo root
python -m venv .venv && source .venv/bin/activate
pip install -r app/requirements.txt

# Copy the env template and fill it in
cp app/.env.example app/.env
# (edit app/.env with your profile + warehouse id)

# From the app/ directory
cd app
set -a && source .env && set +a   # export every var in .env
streamlit run app.py
```

What the connection helper (`lib/db.py`) does:

- **Local**: uses your CLI profile. `current_user()` resolves to the logged-in
  user — useful for demoing the audit trail on Tab 3.
- **On Databricks Apps**: uses the `X-Forwarded-Access-Token` header (OBO) so
  `current_user()` reflects the actual viewer, not the app service principal.

## Deploy to Databricks Apps

### 1. Edit `app.yaml`

Open `app.yaml` and replace `<YOUR_WAREHOUSE_ID>` with the real warehouse ID.
Optionally uncomment the `APP_*` env overrides if your catalog / dashboard
names differ from the defaults.

### 2. Create the app

```bash
databricks apps create <YOUR_APP_NAME> --profile <YOUR_PROFILE_NAME>
```

### 3. Grant the app service principal access

```bash
# Print the service principal client id — you'll paste it into the SQL script.
databricks apps get <YOUR_APP_NAME> --profile <YOUR_PROFILE_NAME> \
  | python -c "import json,sys; print(json.load(sys.stdin)['service_principal_client_id'])"
```

Open `scripts/grant_sp_access.sql` in the **Databricks SQL Editor**, replace
`<APP_SERVICE_PRINCIPAL_CLIENT_ID>` with the value printed above, and run it.

### 4. Sync source & deploy

```bash
# Destination path inside the workspace for the app's source code.
USER_EMAIL=$(databricks current-user me --profile <YOUR_PROFILE_NAME> \
             | python -c "import json,sys; print(json.load(sys.stdin)['userName'])")
SRC="/Workspace/Users/${USER_EMAIL}/<YOUR_APP_NAME>"

# Run from the repo root so only the app/ folder is uploaded.
databricks sync --watch=false \
  --exclude '.venv/**' --exclude '__pycache__/**' --exclude '*.pyc' \
  --exclude '.env' --exclude '.env.*' \
  app "$SRC" --profile <YOUR_PROFILE_NAME>

databricks apps deploy <YOUR_APP_NAME> \
  --source-code-path "$SRC" --profile <YOUR_PROFILE_NAME>
```

After deploy finishes, the app's URL is in:

```bash
databricks apps get <YOUR_APP_NAME> --profile <YOUR_PROFILE_NAME>
```

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| `DATABRICKS_WAREHOUSE_ID is not set` on startup | Export it locally (via `.env`) or ensure `app.yaml` has a valid warehouse id for `sql_warehouse`. |
| Tab 1 shows a host-resolution error | Set `DATABRICKS_HOST` or make sure `DATABRICKS_CONFIG_PROFILE` points to a profile with a valid host. |
| Tab 1 iframe loads a login screen | Re-publish the dashboard with **Embed credentials** enabled, or update `APP_DASHBOARD_ID`. |
| `PERMISSION_DENIED` on any table | Re-run `scripts/grant_sp_access.sql` with the correct service principal. |
| `current_user()` returns the SP client id on Tab 2 | The OBO header wasn't forwarded. Make sure you're visiting the deployed app URL (not a direct warehouse query). |

## What's where in the code

- `lib/config.py` — read once at startup; every catalog / schema / table name
  the app uses is built here.
- `lib/queries.py` — every SQL statement the app runs, parameterized.
- `lib/db.py` — connection helpers; auto-picks OBO token vs CLI profile.
- `app.py` — Streamlit UI for the three tabs.
