# Geographic Market Intelligence — Databricks Demo

A Streamlit app on Databricks with 3 tabs:
1. An embedded AI/BI dashboard
2. A form to define geographic territories
3. A shared view of everyone's territories with filters + analytics

## What's in this repo

```
data_pipeline/  # Notebook: creates the source Delta tables
dashboard/      # AI/BI dashboard JSON (embedded on Tab 1)
genie_spaces/   # Exported Genie Space JSON + import/export notebook
app/            # The Streamlit app + deploy script
```

## Setup

You need: a Databricks workspace and a running SQL Warehouse. The user
running `deploy.sh` must have MANAGE (or ownership) on the target
catalog/schemas so it can create the app's schema+table and grant the
app's service principal access.

**1. Log in.**
```bash
databricks auth login --host https://<your-workspace-host> --profile <your-profile>
```

**2. Create the source tables.**
Import `data_pipeline/healthcare_claims_medallion_pipeline.ipynb` into
your workspace and run it. It creates the `eli_lilly_demo` catalog with
sample patient and claims data.

**3. Import the dashboard.**
Workspace → **AI/BI Dashboards → Import dashboard**, upload
`dashboard/population_health_executive_dashboard.lvdash.json`, attach
your warehouse, **Publish with "Embed credentials" ticked**.

**4. (Optional) Import the Genie Space.**
Gives stakeholders a natural-language chat interface over the same claims
data. Import `genie_spaces/Import Export Genie Space.ipynb` into your
workspace, open the second cell ("Import Genie Space from JSON"), point
`IMPORT_FILE` at `genie_spaces/genie_space_export.json` (upload it to
`/Workspace/...` first) and set `TARGET_WAREHOUSE_ID` to your warehouse,
then run the cell. See [`genie_spaces/README.md`](genie_spaces/README.md)
for details. The app itself does not depend on this step.

**5. Edit `app/app.yaml`.**
Set these two per-workspace values (the rest already have sensible
defaults):
- `resources.sql_warehouse.id` — your SQL Warehouse id.
- `env.APP_DASHBOARD_ID` — the id from the dashboard's published URL
  (`.../dashboardsv3/<THIS_PART>/published`).

**6. Deploy.**
```bash
cd app
./deploy.sh <your-app-name> <your-profile>
```

`deploy.sh` does everything end-to-end:
1. Creates the app (if missing), syncs code, and deploys.
2. Applies `app/scripts/1_create_table.sql` (creates the app schema + the
   `territory_definitions` table).
3. Applies `app/scripts/2_grant_sp_access.sql` (grants the app SP access
   to the source + app schemas).

Both `.sql` files are the source of truth — `deploy.sh` just renders
`{{CATALOG}}` / `{{APP_SCHEMA}}` / `{{SP}}` / etc. from `app.yaml` and
the app's service principal before running them. Every step is
idempotent — re-run any time you change code or config.

## Run locally (optional)

```bash
cd app
pip install -r requirements.txt
export DATABRICKS_CONFIG_PROFILE=<your-profile>
export DATABRICKS_WAREHOUSE_ID=<your-warehouse-id>
streamlit run app.py
```

## Using a different catalog?

Defaults are `eli_lilly_demo.{silver_claims, gold_claims, app_data}`, set
in `app/app.yaml` under `env` (`APP_CATALOG`, `APP_SILVER_SCHEMA`,
`APP_GOLD_SCHEMA`, `APP_SCHEMA`). Edit those values and re-run
`./deploy.sh` — both the app (at runtime) and the bootstrap SQL in
`deploy.sh` read from the same place, so they stay in sync. The source
catalog itself must already exist; `deploy.sh` does not create catalogs.
