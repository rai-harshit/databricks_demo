-- Source of truth for the app SP's Unity Catalog grants.
-- Applied automatically by `./deploy.sh` — placeholders are substituted
-- from `app.yaml` and from `databricks apps get <app>`. To run manually,
-- replace every {{...}} token first.

GRANT USE CATALOG ON CATALOG {{CATALOG}}                              TO `{{SP}}`;
GRANT USE SCHEMA, SELECT ON SCHEMA {{CATALOG}}.{{GOLD_SCHEMA}}         TO `{{SP}}`;
GRANT USE SCHEMA, SELECT ON SCHEMA {{CATALOG}}.{{SILVER_SCHEMA}}       TO `{{SP}}`;
GRANT USE SCHEMA, SELECT, MODIFY ON SCHEMA {{CATALOG}}.{{APP_SCHEMA}}  TO `{{SP}}`;
