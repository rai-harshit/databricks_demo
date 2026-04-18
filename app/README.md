# app/

Streamlit source for the demo. Full setup lives in the
[top-level README](../README.md).

```
app.py              Streamlit UI (3 tabs)
app.yaml            Databricks Apps deployment config
requirements.txt    Python deps
deploy.sh           One-command deploy
lib/
  config.py         All env-driven settings (catalog, dashboard id, …)
  db.py             SQL connector helpers
  queries.py        Every SQL statement the app runs
scripts/
  1_create_table.sql       Run once in SQL Editor before first deploy
  2_grant_sp_access.sql    Run after `deploy.sh` creates the app
```

## Troubleshooting

- `DATABRICKS_WAREHOUSE_ID is not set` → edit `app.yaml` and put a real
  warehouse id in place of `<YOUR_WAREHOUSE_ID>`.
- Tab 1 shows a login screen → re-publish the dashboard with **Embed
  credentials** enabled.
- `PERMISSION_DENIED` on any table → re-run `scripts/2_grant_sp_access.sql`
  with the app's service principal id (printed by `deploy.sh`).
