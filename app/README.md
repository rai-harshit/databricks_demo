# app/

Streamlit source for the demo. Full setup lives in the
[top-level README](../README.md).

```
app.py              Streamlit UI (3 tabs)
app.yaml            Databricks Apps deployment config — single source of
                    truth for catalog/schema names (APP_CATALOG, APP_*_SCHEMA)
requirements.txt    Python deps
deploy.sh           One-command deploy: app + schema/table + SP grants
lib/
  config.py         Reads env vars set by app.yaml (catalog, dashboard id, …)
  db.py             SQL connector helpers
  queries.py        Every SQL statement the app runs
scripts/
  1_create_table.sql       Source of truth for app schema + table DDL.
                           deploy.sh renders {{PLACEHOLDERS}} and applies it.
  2_grant_sp_access.sql    Source of truth for UC grants to the app SP.
                           deploy.sh renders {{PLACEHOLDERS}} and applies it.
```

## Troubleshooting

- `DATABRICKS_WAREHOUSE_ID is not set` → edit `app.yaml` and put a real
  warehouse id in place of `<YOUR_WAREHOUSE_ID>`.
- Tab 1 shows a login screen → re-publish the dashboard with **Embed
  credentials** enabled.
- `PERMISSION_DENIED` on any table → re-run `./deploy.sh` — grants are
  idempotent and will be re-applied. Only hand-run
  `scripts/2_grant_sp_access.sql` if you need to fix grants without
  redeploying the app.
- Deploy fails with `Catalog not found` → the catalog in `APP_CATALOG`
  must already exist. `deploy.sh` does not create catalogs (requires
  metastore-admin privileges).
- Deploy fails with `PERMISSION_DENIED` on `CREATE SCHEMA` or `GRANT` →
  the profile running `deploy.sh` needs MANAGE/ownership on the
  catalog and schemas referenced in `app.yaml`.
