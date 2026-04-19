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

## Setup

You need: a Databricks workspace and a running SQL Warehouse.

**1. Log in.**
```bash
databricks auth login --host https://<your-workspace-host> --profile <your-profile>
```

**2. Create the source tables.**
Import `data_pipeline/healthcare_claims_medallion_pipeline.ipynb` into your
workspace and run it. It creates the `eli_lilly_demo` catalog with sample
patient and claims data.

**3. Import the dashboard.**
Workspace → **AI/BI Dashboards → Import dashboard**, upload
`dashboard/population_health_executive_dashboard.lvdash.json`, attach your
warehouse, **Publish with "Embed credentials" ticked**.

**4. Create the app's table.**
Paste `app/scripts/1_create_table.sql` into the SQL Editor and run it.

**5. Deploy.**
```bash
cd app
./deploy.sh <your-app-name> <your-profile>
```

On the first run the script asks for your warehouse id and dashboard id,
writes them into `app.yaml`, creates the app, and prints the SQL to run to
grant the app access. Run that SQL, then run `./deploy.sh` again — that
second run syncs the code, deploys, and prints the app URL.

> If you already set `DATABRICKS_CONFIG_PROFILE` in your shell you can skip
> the `<your-profile>` argument.

## Run locally (optional)

```bash
cd app
pip install -r requirements.txt
export DATABRICKS_CONFIG_PROFILE=<your-profile>
export DATABRICKS_WAREHOUSE_ID=<your-warehouse-id>
streamlit run app.py
```

## Using a different catalog?

Defaults assume `eli_lilly_demo.{silver_claims,gold_claims,app_data}`. To
point at your own catalog/schemas, uncomment the `APP_CATALOG` /
`APP_*_SCHEMA` entries in `app/app.yaml`. Full list in `app/lib/config.py`.
