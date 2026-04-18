# Geographic Market Intelligence — Databricks Demo

A Streamlit app on Databricks with 3 tabs:
1. An embedded AI/BI dashboard
2. A form to define geographic territories
3. A shared view of everyone's territories with filters + analytics

## What's in this repo

```
data_pipeline/  # Notebook: creates the source Delta tables
dashboard/      # AI/BI dashboard JSON (embedded on Tab 1)
app/            # The Streamlit app + deploy script
```

## Setup (≈15 min)

You need: a Databricks workspace and a running SQL Warehouse.

**1. Log in.**
```bash
databricks auth login --host https://<your-workspace-host>
```

**2. Create the source tables.**
Import `data_pipeline/healthcare_claims_medallion_pipeline.ipynb` into your
workspace and run it. It creates the `eli_lilly_demo` catalog with sample
patient and claims data.

**3. Import the dashboard.**
Workspace → **AI/BI Dashboards → Import dashboard**, upload
`dashboard/population_health_executive_dashboard.lvdash.json`, attach your
warehouse, **Publish with "Embed credentials" ticked**. Copy the dashboard
ID from the URL.

**4. Create the app's table.**
Paste `app/scripts/1_create_table.sql` into the SQL Editor and run it.

**5. Fill in `app/app.yaml`.**
Replace `<YOUR_WAREHOUSE_ID>` and `<YOUR_DASHBOARD_ID>`.

**6. Deploy.**
```bash
cd app
./deploy.sh <your-app-name>
```

The script creates the app, prints the service principal grants for you to
run, syncs the code, and deploys. The final URL is printed at the end.

## Run locally (optional)

```bash
cd app
pip install -r requirements.txt
export DATABRICKS_CONFIG_PROFILE=DEFAULT          # or your profile name
export DATABRICKS_WAREHOUSE_ID=<your-warehouse-id>
streamlit run app.py
```

## Using a different catalog?

Defaults assume `eli_lilly_demo.{silver_claims,gold_claims,app_data}`. To
point at your own catalog/schemas, set `APP_CATALOG`, `APP_SILVER_SCHEMA`,
`APP_GOLD_SCHEMA`, `APP_SCHEMA` in `app/app.yaml`. Full list in
`app/lib/config.py`.
