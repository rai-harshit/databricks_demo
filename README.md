# Geographic Market Intelligence — Databricks Demo

End-to-end Databricks demo with three pieces:

| Folder | Contents |
| --- | --- |
| [`app/`](app) | Streamlit Databricks App (3 tabs: embedded dashboard, territory builder, territory viewer). See [`app/README.md`](app/README.md) for setup and deploy. |
| [`data_pipeline/`](data_pipeline) | Healthcare Claims Medallion pipeline notebook that produces the Bronze/Silver/Gold tables the app reads. |
| [`dashboard/`](dashboard) | Exported AI/BI dashboard definition (`.lvdash.json`) that the app embeds on Tab 1. |

## What you get

1. **Import the pipeline notebook** — populates a `*.silver_claims` and
   `*.gold_claims` set of Delta tables (defaults to the `eli_lilly_demo`
   catalog; configurable).
2. **Import the dashboard** — a published AI/BI dashboard rendering patient
   and claims analytics off those tables.
3. **Deploy the app** — a Streamlit Databricks App that embeds the dashboard
   and lets users define, share, and analyze custom geographic territories
   on top of the same data.

## Getting started

Everything workspace-specific (host, warehouse id, catalog, dashboard id) is
driven by environment variables — you do not need to edit Python. Walk through
[`app/README.md`](app/README.md) for the full setup.

The only workspace identifiers you need to supply are:

- your workspace host (e.g. `https://<workspace>.cloud.databricks.com`)
- a SQL Warehouse ID
- (optional) the published AI/BI dashboard ID you want to embed

Defaults assume the `eli_lilly_demo` catalog with `silver_claims`,
`gold_claims`, and `app_data` schemas; override via `APP_CATALOG`,
`APP_*_SCHEMA`, etc. if yours differ.
